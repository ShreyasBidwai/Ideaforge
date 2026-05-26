from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.api.deps import get_current_user, get_cache
from app.core.database import get_db
from app.models import User, ProblemStatement
from app.schemas.problem_statement import (
    ProblemStatementResponse,
    ProblemStatementListResponse,
    ProblemStatementUpdate
)
from app.services.problem_statement_service import ProblemStatementService
from app.ai.provider import get_ai_provider, AIProvider
from app.core.cache import CacheService

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/sessions/{session_id}/generate-problems", response_model=list[ProblemStatementResponse])
async def generate_problems(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
    cache: CacheService | None = Depends(get_cache)
):
    service = ProblemStatementService(ai_provider, db, cache)
    problems = await service.generate_problem_statements(session_id, current_user.id)
    return problems

@router.get("/sessions/{session_id}/problem-statements", response_model=list[ProblemStatementResponse])
async def get_session_problems(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ProblemStatementService(None, db, None)
    problems = await service.get_problem_statements_by_session(session_id, current_user.id)
    return problems

@router.get("/problem-statements", response_model=ProblemStatementListResponse)
async def list_problems(
    industry: str | None = Query(None),
    status: str | None = Query(None),
    sort_by: str = Query("overall_rating"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ProblemStatementService(None, db, None)
    result = await service.get_all_problem_statements(
        user_id=current_user.id,
        industry=industry,
        status_filter=status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page
    )
    return result

@router.get("/problem-statements/{id}", response_model=ProblemStatementResponse)
async def get_single_problem(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ProblemStatement)
        .options(joinedload(ProblemStatement.session))
        .where(ProblemStatement.id == id)
    )
    ps = result.scalar_one_or_none()
    if ps is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem statement not found"
        )
    if ps.session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this problem statement"
        )
    return ps

@router.patch("/problem-statements/{id}", response_model=ProblemStatementResponse)
async def update_problem(
    id: UUID,
    data: ProblemStatementUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ProblemStatementService(None, db, None)
    ps = await service.update_problem_statement(id, current_user.id, data)
    return ps

@router.post("/problem-statements/{id}/select", response_model=ProblemStatementResponse)
async def select_problem(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ProblemStatementService(None, db, None)
    ps = await service.select_problem_statement(id, current_user.id)
    return ps
