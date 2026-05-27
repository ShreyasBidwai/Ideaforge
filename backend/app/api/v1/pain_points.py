from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_cache
from app.core.database import get_db
from app.models import User
from app.schemas.pain_point import PainPointResponse
from app.services.pain_point_service import PainPointService
from app.ai.provider import get_ai_provider, AIProvider
from app.core.maturity import MaturityLevel
from app.services.session_service import get_session
from app.core.streaming import format_sse_event
from app.core.cache import CacheService

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/sessions/{session_id}/discover", response_model=PainPointResponse)
async def discover_session_pain_points(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
    cache: CacheService = Depends(get_cache)
):
    # Verify ownership
    session = await get_session(db, session_id, current_user.id)
    
    service = PainPointService(ai_provider, db, cache)
    pain_points = await service.discover_pain_points(
        session_id=session.id,
        industry=session.industry,
        location=session.location,
        maturity_level=MaturityLevel(session.maturity_level)
    )
    return {"pain_points": pain_points}

@router.post("/sessions/{session_id}/discover/stream")
async def discover_session_pain_points_stream(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
    cache: CacheService = Depends(get_cache)
):
    # Verify ownership
    session = await get_session(db, session_id, current_user.id)

    async def event_generator():
        service = PainPointService(ai_provider, db, cache)
        try:
            async for step in service.discover_pain_points_stream(
                session_id=session.id,
                industry=session.industry,
                location=session.location,
                maturity_level=MaturityLevel(session.maturity_level)
            ):
                event_type = step["status"]
                if event_type in ("starting", "calling_ai", "parsing"):
                    sse_type = "progress"
                elif event_type == "complete":
                    sse_type = "complete"
                else:
                    sse_type = "progress"
                yield format_sse_event(sse_type, step)
        except Exception as e:
            yield format_sse_event("error", {"status": "error", "message": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/sessions/{session_id}/pain-points", response_model=PainPointResponse)
async def get_session_pain_points(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    session = await get_session(db, session_id, current_user.id)
    return {"pain_points": session.pain_points or []}
