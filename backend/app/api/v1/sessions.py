from uuid import UUID
from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse
from app.services import session_service

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await session_service.create_session(db, current_user.id, data)

@router.get("", response_model=SessionListResponse)
async def list_user_sessions(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await session_service.get_user_sessions(db, current_user.id, page, per_page)

@router.get("/{id}", response_model=SessionResponse)
async def get_session_by_id(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await session_service.get_session(db, id, current_user.id)

@router.patch("/{id}", response_model=SessionResponse)
async def update_session_by_id(
    id: UUID,
    data: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await session_service.update_session(db, id, current_user.id, data)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_by_id(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await session_service.delete_session(db, id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
