from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.evaluation import RubricResponse, RubricSchema, ComparisonResult, FullEvaluationResponse
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

@router.post("/problem-statements/{problem_id}/evaluation/disqualify", response_model=dict)
async def disqualify_gate(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    service = EvaluationService(ai_provider, db)
    return await service.run_disqualifier_gate(problem_id, current_user.id)

@router.post("/problem-statements/{problem_id}/evaluation/score", response_model=dict)
async def score_survivors(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    service = EvaluationService(ai_provider, db)
    return await service.run_scoring(problem_id, current_user.id)

@router.get("/problem-statements/{problem_id}/evaluation/scores", response_model=dict)
async def get_scores(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = EvaluationService(None, db)
    return await service.get_scores(problem_id, current_user.id)

@router.post("/problem-statements/{problem_id}/evaluation/attack", response_model=dict)
async def devils_advocate(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    service = EvaluationService(ai_provider, db)
    return await service.run_devils_advocate(problem_id, current_user.id)

@router.post("/problem-statements/{problem_id}/evaluation/ach", response_model=dict)
async def ach_analysis(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    service = EvaluationService(ai_provider, db)
    return await service.run_ach_analysis(problem_id, current_user.id)

@router.get("/problem-statements/{problem_id}/evaluation/attacks", response_model=dict)
async def get_attacks(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = EvaluationService(None, db)
    return await service.get_attacks(problem_id, current_user.id)

@router.get("/problem-statements/{problem_id}/evaluation/ach", response_model=dict)
async def get_ach(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = EvaluationService(None, db)
    return await service.get_ach(problem_id, current_user.id)

@router.post("/problem-statements/{problem_id}/evaluation/compare", response_model=ComparisonResult)
async def generate_comparison(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = EvaluationService(None, db)
    return await service.generate_comparison(problem_id, current_user.id)

@router.get("/problem-statements/{problem_id}/evaluation", response_model=FullEvaluationResponse)
async def get_full_evaluation(
    problem_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = EvaluationService(None, db)
    return await service.get_full_evaluation(problem_id, current_user.id)



