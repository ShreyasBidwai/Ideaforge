import json
from uuid import UUID
from typing import AsyncGenerator
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.ai.provider import AIProvider
from app.ai.prompts.pain_points import build_pain_point_prompt
from app.core.maturity import get_maturity_config, MaturityLevel
from app.models.session import Session
from app.schemas.pain_point import PainPointSchema, PainPointResponse

class PainPointService:
    def __init__(self, ai_provider: AIProvider, db: AsyncSession):
        self.ai = ai_provider
        self.db = db

    async def discover_pain_points(
        self,
        session_id: UUID,
        industry: str,
        location: str,
        maturity_level: MaturityLevel
    ) -> list[PainPointSchema]:
        """
        1. Get maturity config
        2. Build prompt from template
        3. Call Gemini AI with structured JSON output
        4. Parse and validate response against Pydantic schema
        5. If validation fails, retry once with error context
        6. Store pain points in session.pain_points (JSON field)
        7. Update session status to "problem_generation"
        8. Return parsed pain points
        """
        maturity_config = get_maturity_config(maturity_level)
        system_prompt, user_prompt = build_pain_point_prompt(industry, location, maturity_config)

        # Gemini-compatible JSON schema
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "pain_points": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "description": {"type": "STRING"},
                            "severity": {"type": "INTEGER"},
                            "affected_stakeholders": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "evidence": {"type": "STRING"}
                        },
                        "required": ["name", "description", "severity", "affected_stakeholders", "evidence"]
                    }
                }
            },
            "required": ["pain_points"]
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
            parsed = PainPointResponse.model_validate(data)
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
                parsed = PainPointResponse.model_validate(data)
            except Exception as retry_err:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI generation failed validation: {str(retry_err)}"
                )

        # Update session
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session.pain_points = [pp.model_dump() for pp in parsed.pain_points]
        session.status = "problem_generation"
        
        await self.db.commit()
        await self.db.refresh(session)

        return parsed.pain_points

    async def discover_pain_points_stream(
        self,
        session_id: UUID,
        industry: str,
        location: str,
        maturity_level: MaturityLevel
    ) -> AsyncGenerator[dict, None]:
        # Step 1: starting
        yield {
            "status": "starting",
            "message": f"Analyzing {industry} industry in {location}..."
        }

        # Step 2: calling_ai
        yield {
            "status": "calling_ai",
            "message": "Consulting AI for pain point analysis..."
        }

        maturity_config = get_maturity_config(maturity_level)
        system_prompt, user_prompt = build_pain_point_prompt(industry, location, maturity_config)

        # Gemini-compatible JSON schema
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "pain_points": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "description": {"type": "STRING"},
                            "severity": {"type": "INTEGER"},
                            "affected_stakeholders": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "evidence": {"type": "STRING"}
                        },
                        "required": ["name", "description", "severity", "affected_stakeholders", "evidence"]
                    }
                }
            },
            "required": ["pain_points"]
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
            parsed = PainPointResponse.model_validate(data)
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
                parsed = PainPointResponse.model_validate(data)
            except Exception as retry_err:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI generation failed validation: {str(retry_err)}"
                )

        # Step 3: parsing
        yield {
            "status": "parsing",
            "message": "Processing discovered pain points..."
        }

        # Update session
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session.pain_points = [pp.model_dump() for pp in parsed.pain_points]
        session.status = "problem_generation"
        
        await self.db.commit()
        await self.db.refresh(session)

        # Step 4: complete
        yield {
            "status": "complete",
            "data": {
                "pain_points": [pp.model_dump() for pp in parsed.pain_points]
            }
        }

