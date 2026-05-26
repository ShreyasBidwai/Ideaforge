from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_cache
from app.core.database import get_db
from app.models import User
from app.schemas.solution import (
    SolutionResponse,
    SolutionStatusUpdate
)
from app.services.solution_service import SolutionService
from app.ai.provider import get_ai_provider, AIProvider
from app.core.cache import CacheService
from app.core.streaming import format_sse_event

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/problem-statements/{problem_id}/generate-solutions", response_model=list[SolutionResponse])
async def generate_solutions(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
    cache: CacheService | None = Depends(get_cache)
):
    service = SolutionService(ai_provider, db, cache)
    solutions = await service.generate_solutions(problem_id, current_user.id)
    return solutions

@router.post("/problem-statements/{problem_id}/generate-solutions/stream")
async def generate_solutions_stream(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
    cache: CacheService | None = Depends(get_cache)
):
    service = SolutionService(ai_provider, db, cache)
    await service.validate_problem_for_generation(problem_id, current_user.id)

    async def event_generator():
        try:
            async for step in service.generate_solutions_stream(problem_id, current_user.id):
                event_type = step["status"]
                if event_type in ("preparing", "generating", "validating", "saving"):
                    sse_type = "progress"
                elif event_type == "complete":
                    sse_type = "complete"
                else:
                    sse_type = "progress"
                yield format_sse_event(sse_type, step)
        except Exception as e:
            yield format_sse_event("error", {"status": "error", "message": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/problem-statements/{problem_id}/solutions", response_model=list[SolutionResponse])
async def get_problem_solutions(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SolutionService(None, db)
    solutions = await service.get_solutions_by_problem(problem_id, current_user.id)
    return solutions

@router.get("/solutions/{id}", response_model=SolutionResponse)
async def get_solution(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SolutionService(None, db)
    solution = await service.get_solution(id, current_user.id)
    return solution

@router.post("/solutions/{id}/approve", response_model=SolutionResponse)
async def approve_solution(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SolutionService(None, db)
    solution = await service.approve_solution(id, current_user.id)
    return solution

@router.patch("/solutions/{id}/status", response_model=SolutionResponse)
async def update_solution_status(
    id: UUID,
    data: SolutionStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SolutionService(None, db)
    solution = await service.update_solution_status(id, current_user.id, data.status)
    return solution
