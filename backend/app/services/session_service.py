from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.session import Session
from app.schemas.session import SessionCreate, SessionUpdate

async def create_session(db: AsyncSession, user_id: UUID, data: SessionCreate) -> Session:
    db_session = Session(
        user_id=user_id,
        industry=data.industry,
        location=data.location,
        guidance=data.guidance,
        maturity_level=data.maturity_level.value,
        tech_stack_preferences=data.tech_stack_preferences,
        status="discovery"
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def get_session(db: AsyncSession, session_id: UUID, user_id: UUID) -> Session:
    result = await db.execute(select(Session).where(Session.id == session_id))
    db_session = result.scalar_one_or_none()
    
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if db_session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this session"
        )
    
    return db_session

async def get_user_sessions(db: AsyncSession, user_id: UUID, page: int, per_page: int) -> dict:
    total_result = await db.execute(
        select(func.count()).select_from(Session).where(Session.user_id == user_id)
    )
    total = total_result.scalar() or 0
    
    offset = (page - 1) * per_page
    items_result = await db.execute(
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(Session.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    items = items_result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page
    }

async def update_session(db: AsyncSession, session_id: UUID, user_id: UUID, data: SessionUpdate) -> Session:
    db_session = await get_session(db, session_id, user_id)
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "maturity_level" and value is not None:
            setattr(db_session, field, value.value)
        elif value is not None:
            setattr(db_session, field, value)
            
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def delete_session(db: AsyncSession, session_id: UUID, user_id: UUID) -> None:
    db_session = await get_session(db, session_id, user_id)
    await db.delete(db_session)
    await db.commit()
