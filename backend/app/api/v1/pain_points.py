from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.pain_point import PainPointResponse
from app.services.pain_point_service import PainPointService
from app.ai.provider import get_ai_provider, AIProvider
from app.core.maturity import MaturityLevel
from app.services.session_service import get_session

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/sessions/{session_id}/discover", response_model=PainPointResponse)
async def discover_session_pain_points(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    # Verify ownership
    session = await get_session(db, session_id, current_user.id)
    
    service = PainPointService(ai_provider, db)
    pain_points = await service.discover_pain_points(
        session_id=session.id,
        industry=session.industry,
        location=session.location,
        maturity_level=MaturityLevel(session.maturity_level)
    )
    return {"pain_points": pain_points}

@router.get("/sessions/{session_id}/pain-points", response_model=PainPointResponse)
async def get_session_pain_points(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    session = await get_session(db, session_id, current_user.id)
    return {"pain_points": session.pain_points or []}
