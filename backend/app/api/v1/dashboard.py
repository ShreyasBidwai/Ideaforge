from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlalchemy.future import select

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User, Session as SessionModel, ProblemStatement, Solution

router = APIRouter(prefix="/dashboard", dependencies=[Depends(get_current_user)])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sessions_query = select(func.count(SessionModel.id)).where(SessionModel.user_id == current_user.id)
    sessions_count = (await db.execute(sessions_query)).scalar() or 0

    problems_query = select(func.count(ProblemStatement.id))\
        .join(SessionModel, ProblemStatement.session_id == SessionModel.id)\
        .where(SessionModel.user_id == current_user.id)
    problems_count = (await db.execute(problems_query)).scalar() or 0

    evaluated_query = select(func.count(Solution.id))\
        .join(ProblemStatement, Solution.problem_id == ProblemStatement.id)\
        .join(SessionModel, ProblemStatement.session_id == SessionModel.id)\
        .where(SessionModel.user_id == current_user.id)\
        .where(Solution.status.in_(["evaluated", "approved"]))
    evaluated_count = (await db.execute(evaluated_query)).scalar() or 0

    approved_query = select(func.count(Solution.id))\
        .join(ProblemStatement, Solution.problem_id == ProblemStatement.id)\
        .join(SessionModel, ProblemStatement.session_id == SessionModel.id)\
        .where(SessionModel.user_id == current_user.id)\
        .where(Solution.status == "approved")
    approved_count = (await db.execute(approved_query)).scalar() or 0

    return {
        "total_sessions": sessions_count,
        "total_problems": problems_count,
        "solutions_evaluated": evaluated_count,
        "solutions_approved": approved_count
    }
