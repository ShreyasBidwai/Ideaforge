from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.evaluation import RubricResponse, RubricSchema
from app.services.evaluation_service import EvaluationService
from app.ai.provider import get_ai_provider, AIProvider

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/problem-statements/{problem_id}/evaluation/rubric", response_model=RubricResponse)
async def generate_rubric(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    service = EvaluationService(ai_provider, db)
    return await service.generate_rubric(problem_id, current_user.id)

@router.get("/problem-statements/{problem_id}/evaluation/rubric", response_model=RubricResponse)
async def get_rubric(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = EvaluationService(None, db)
    return await service.get_rubric(problem_id, current_user.id)

@router.patch("/problem-statements/{problem_id}/evaluation/rubric", response_model=RubricResponse)
async def edit_rubric(
    problem_id: UUID,
    data: RubricSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = EvaluationService(None, db)
    return await service.update_rubric(problem_id, current_user.id, data.model_dump())

@router.post("/problem-statements/{problem_id}/evaluation/rubric/lock", response_model=RubricResponse)
async def lock_rubric(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = EvaluationService(None, db)
    return await service.lock_rubric(problem_id, current_user.id)
