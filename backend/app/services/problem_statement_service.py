import json
import logging
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.ai.provider import AIProvider
from app.ai.prompts.problem_statements import build_problem_statement_prompt
from app.core.maturity import get_maturity_config, MaturityLevel
from app.models.session import Session
from app.models.problem_statement import ProblemStatement
from app.schemas.problem_statement import ProblemStatementUpdate, ProblemStatementCreate
from app.core.cache import CacheService

logger = logging.getLogger(__name__)

class ProblemStatementService:
    def __init__(self, ai_provider: AIProvider, db: AsyncSession, cache: CacheService | None = None):
        self.ai = ai_provider
        self.db = db
        self.cache = cache

    async def generate_problem_statements(self, session_id: UUID, user_id: UUID) -> list[ProblemStatement]:
        """
        1. Fetch session (validate ownership)
        2. Get pain points from session.pain_points
        3. Get maturity config from session.maturity_level
        4. Build prompt
        5. Call Gemini AI
        6. Parse and validate response
        7. Compute overall_rating for each: weighted avg (severity*2 + feasibility*2 + market_size*1.5 + uniqueness*1) / 6.5
        8. Create ProblemStatement records in database
        9. Update session status to "solution_generation"
        10. Return created problem statements
        """
        # Fetch session
        result = await self.db.execute(
            select(Session)
            .where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
            
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this session"
            )
            
        if not session.pain_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pain points discovered yet. Discover pain points first."
            )

        # Get maturity config
        maturity_level_enum = MaturityLevel(session.maturity_level)
        maturity_config = get_maturity_config(maturity_level_enum)

        # Build prompt
        system_prompt, user_prompt = build_problem_statement_prompt(
            session.pain_points,
            session.industry,
            session.location,
            maturity_config
        )

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "problem_statements": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {"type": "STRING"},
                            "description": {"type": "STRING"},
                            "target_user": {"type": "STRING"},
                            "core_pain": {"type": "STRING"},
                            "market_context": {"type": "STRING"},
                            "severity": {"type": "INTEGER"},
                            "feasibility": {"type": "INTEGER"},
                            "market_size": {"type": "INTEGER"},
                            "uniqueness": {"type": "INTEGER"}
                        },
                        "required": ["title", "description", "target_user", "core_pain", "market_context", "severity", "feasibility", "market_size", "uniqueness"]
                    }
                }
            },
            "required": ["problem_statements"]
        }

        parsed = None
        try:
            raw_response = await self.ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                temperature=maturity_config.temperature
            )
            data = json.loads(raw_response)
            parsed = data.get("problem_statements", [])
        except Exception as e:
            # Retry once with error context
            retry_prompt = (
                f"{user_prompt}\n\n"
                f"Your previous response failed validation with error: {str(e)}.\n"
                f"Please correct any issues and return ONLY valid JSON matching the schema."
            )
            try:
                raw_response = await self.ai.generate(
                    prompt=retry_prompt,
                    system_prompt=system_prompt,
                    response_schema=response_schema,
                    temperature=maturity_config.temperature
                )
                data = json.loads(raw_response)
                parsed = data.get("problem_statements", [])
            except Exception as retry_err:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI generation failed validation: {str(retry_err)}"
                )

        created_problems = []
        for item in parsed:
            # Validate values ge=1, le=5
            sev = float(max(1, min(5, item["severity"])))
            feas = float(max(1, min(5, item["feasibility"])))
            mkt = float(max(1, min(5, item["market_size"])))
            uniq = float(max(1, min(5, item["uniqueness"])))

            overall = self.compute_overall_rating(sev, feas, mkt, uniq)
            
            db_ps = ProblemStatement(
                session_id=session.id,
                title=item["title"],
                description=item["description"],
                target_user=item.get("target_user"),
                core_pain=item.get("core_pain"),
                market_context=item.get("market_context"),
                severity=sev,
                feasibility=feas,
                market_size=mkt,
                uniqueness=uniq,
                overall_rating=overall,
                status="draft"
            )
            self.db.add(db_ps)
            created_problems.append(db_ps)

        # Update session status
        session.status = "solution_generation"
        await self.db.commit()

        # Refresh objects
        for ps in created_problems:
            await self.db.refresh(ps)
            # Pre-populate relationship object to avoid LazyLoad error on serialization
            ps.session = session

        return created_problems

    async def get_problem_statements_by_session(self, session_id: UUID, user_id: UUID) -> list[ProblemStatement]:
        """Get all problem statements for a session"""
        # Validate session ownership
        result = await self.db.execute(
            select(Session)
            .where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
            
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this session"
            )

        ps_result = await self.db.execute(
            select(ProblemStatement)
            .options(joinedload(ProblemStatement.session))
            .where(ProblemStatement.session_id == session_id)
            .order_by(ProblemStatement.created_at.desc())
        )
        return list(ps_result.scalars().all())

    async def get_all_problem_statements(
        self, user_id: UUID, industry: str | None = None, 
        status_filter: str | None = None, sort_by: str = "overall_rating",
        sort_order: str = "desc", page: int = 1, per_page: int = 20
    ) -> dict:
        """Get all user's problem statements with filtering, sorting, pagination"""
        # Count total
        count_query = select(func.count(ProblemStatement.id)).join(Session).where(Session.user_id == user_id)
        if industry:
            count_query = count_query.where(Session.industry == industry)
        if status_filter:
            count_query = count_query.where(ProblemStatement.status == status_filter)
            
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Fetch page items
        query = select(ProblemStatement).options(joinedload(ProblemStatement.session)).join(Session).where(Session.user_id == user_id)
        if industry:
            query = query.where(Session.industry == industry)
        if status_filter:
            query = query.where(ProblemStatement.status == status_filter)

        sort_col = getattr(ProblemStatement, sort_by, ProblemStatement.overall_rating)
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        items_result = await self.db.execute(query)
        items = list(items_result.scalars().all())

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page
        }

    async def update_problem_statement(self, problem_id: UUID, user_id: UUID, data: ProblemStatementUpdate) -> ProblemStatement:
        """Update a problem statement (edit title, description, ratings, status)"""
        result = await self.db.execute(
            select(ProblemStatement)
            .options(joinedload(ProblemStatement.session))
            .where(ProblemStatement.id == problem_id)
        )
        ps = result.scalar_one_or_none()
        
        if ps is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem statement not found"
            )
            
        if ps.session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this problem statement"
            )

        update_data = data.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(ps, key, val)

        if any(k in update_data for k in ["severity", "feasibility", "market_size", "uniqueness"]):
            ps.overall_rating = self.compute_overall_rating(
                ps.severity, ps.feasibility, ps.market_size, ps.uniqueness
            )

        await self.db.commit()
        await self.db.refresh(ps)
        return ps

    async def select_problem_statement(self, problem_id: UUID, user_id: UUID) -> ProblemStatement:
        """Mark a problem statement as 'selected' for solution generation"""
        result = await self.db.execute(
            select(ProblemStatement)
            .options(joinedload(ProblemStatement.session))
            .where(ProblemStatement.id == problem_id)
        )
        ps = result.scalar_one_or_none()
        
        if ps is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem statement not found"
            )
            
        if ps.session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this problem statement"
            )

        ps.status = "selected"
        await self.db.commit()
        await self.db.refresh(ps)
        return ps

    @staticmethod
    def compute_overall_rating(severity: float, feasibility: float, market_size: float, uniqueness: float) -> float:
        """Weighted average: severity*2 + feasibility*2 + market_size*1.5 + uniqueness*1 / 6.5"""
        return round((severity * 2 + feasibility * 2 + market_size * 1.5 + uniqueness * 1) / 6.5, 2)
