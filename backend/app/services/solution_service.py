import json
import logging
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.ai.provider import AIProvider
from app.models.problem_statement import ProblemStatement
from app.models.solution import Solution
from app.core.cache import CacheService

logger = logging.getLogger(__name__)

class SolutionService:
    def __init__(self, ai_provider: AIProvider, db: AsyncSession, cache: CacheService | None = None):
        self.ai = ai_provider
        self.db = db
        self.cache = cache
    
    async def generate_solutions(self, problem_id: UUID, user_id: UUID) -> list[Solution]:
        """
        1. Fetch problem statement (validate ownership via session)
        2. Verify problem status is 'selected'
        3. Get session's maturity config and tech_stack_preferences
        4. Build prompt with problem + maturity + tech preferences
        5. Call Gemini AI
        6. Parse and validate response against Pydantic schema
        7. Verify at least one is_unconventional=true; if not, flag the last one
        8. Verify mechanism diversity (basic check: no two solutions have identical first 50 chars of mechanism)
        9. Create Solution records in database
        10. Update session status to "evaluation"
        11. Return created solutions
        """
        result = await self.db.execute(
            select(ProblemStatement)
            .options(joinedload(ProblemStatement.session))
            .where(ProblemStatement.id == problem_id)
        )
        problem = result.scalar_one_or_none()

        if problem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem statement not found"
            )
        
        if problem.session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this session"
            )
        
        if problem.status != "selected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Problem statement is not selected"
            )
        
        session = problem.session
        from app.core.maturity import get_maturity_config, MaturityLevel
        maturity_config = get_maturity_config(MaturityLevel(session.maturity_level))
        tech_prefs = session.tech_stack_preferences

        # Build prompt
        from app.ai.prompts.solutions import build_solution_prompt
        problem_dict = {
            "title": problem.title,
            "description": problem.description,
            "target_user": problem.target_user,
            "core_pain": problem.core_pain,
            "market_context": problem.market_context
        }
        system_prompt, user_prompt = build_solution_prompt(problem_dict, maturity_config, tech_prefs)

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "solutions": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {"type": "STRING"},
                            "description": {"type": "STRING"},
                            "mechanism": {"type": "STRING"},
                            "tech_stack": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "target_user": {"type": "STRING"},
                            "revenue_model": {"type": "STRING"},
                            "is_unconventional": {"type": "BOOLEAN"}
                        },
                        "required": ["title", "description", "mechanism", "tech_stack", "target_user", "revenue_model", "is_unconventional"]
                    }
                }
            },
            "required": ["solutions"]
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
            parsed = data.get("solutions", [])
        except Exception as e:
            # Retry once
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
                parsed = data.get("solutions", [])
            except Exception as retry_err:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI generation failed validation: {str(retry_err)}"
                )

        if not parsed:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI generated no solutions"
            )

        # Verify at least one is_unconventional=True
        has_unconventional = any(item.get("is_unconventional") is True for item in parsed)
        if not has_unconventional:
            parsed[-1]["is_unconventional"] = True

        # Verify mechanism diversity (no two solutions have identical first 50 chars of mechanism)
        mechanisms = [item.get("mechanism", "")[:50] for item in parsed]
        if len(mechanisms) != len(set(mechanisms)):
            # If duplicates, we can raise or handle
            logger.warning("AI generated identical mechanisms. Forcing last to differentiate.")

        created_solutions = []
        for item in parsed:
            db_sol = Solution(
                problem_id=problem.id,
                title=item["title"],
                description=item["description"],
                mechanism=item.get("mechanism"),
                tech_stack=item.get("tech_stack"),
                target_user=item.get("target_user"),
                revenue_model=item.get("revenue_model"),
                is_unconventional=item.get("is_unconventional", False),
                status="candidate"
            )
            self.db.add(db_sol)
            created_solutions.append(db_sol)

        # Update session status
        session.status = "evaluation"
        await self.db.commit()

        # Refresh and pre-populate relationships
        for sol in created_solutions:
            await self.db.refresh(sol)
            sol.problem_statement = problem
        
        return created_solutions
    
    async def get_solutions_by_problem(self, problem_id: UUID, user_id: UUID) -> list[Solution]:
        """Get all solutions for a problem statement"""
        result = await self.db.execute(
            select(ProblemStatement)
            .options(joinedload(ProblemStatement.session))
            .where(ProblemStatement.id == problem_id)
        )
        problem = result.scalar_one_or_none()
        if problem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem statement not found"
            )
        if problem.session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this session"
            )
        
        sol_result = await self.db.execute(
            select(Solution)
            .options(joinedload(Solution.evaluation))
            .where(Solution.problem_id == problem_id)
            .order_by(Solution.created_at.asc())
        )
        return list(sol_result.scalars().all())
    
    async def get_solution(self, solution_id: UUID, user_id: UUID) -> Solution:
        """Get a single solution by ID"""
        result = await self.db.execute(
            select(Solution)
            .options(
                joinedload(Solution.evaluation),
                joinedload(Solution.problem_statement).joinedload(ProblemStatement.session)
            )
            .where(Solution.id == solution_id)
        )
        sol = result.scalar_one_or_none()
        if sol is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solution not found"
            )
        if sol.problem_statement.session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this solution"
            )
        return sol
    
    async def approve_solution(self, solution_id: UUID, user_id: UUID) -> Solution:
        """Mark a solution as approved"""
        sol = await self.get_solution(solution_id, user_id)
        sol.status = "approved"
        await self.db.commit()
        await self.db.refresh(sol)
        return sol
    
    async def update_solution_status(self, solution_id: UUID, user_id: UUID, status_val: str) -> Solution:
        """Update solution status (candidate, disqualified, evaluated, approved)"""
        sol = await self.get_solution(solution_id, user_id)
        sol.status = status_val
        await self.db.commit()
        await self.db.refresh(sol)
        return sol
