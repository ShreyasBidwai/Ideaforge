from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User, Solution, ProblemStatement, Session as SessionModel, Evaluation
from app.schemas.approval import ApprovedSolutionResponse

router = APIRouter(prefix="/approvals", dependencies=[Depends(get_current_user)])

@router.get("", response_model=list[ApprovedSolutionResponse])
async def get_approved_solutions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Solution)
        .join(ProblemStatement, Solution.problem_id == ProblemStatement.id)
        .join(SessionModel, ProblemStatement.session_id == SessionModel.id)
        .outerjoin(Evaluation, Solution.id == Evaluation.solution_id)
        .options(
            joinedload(Solution.problem_statement).joinedload(ProblemStatement.session),
            joinedload(Solution.evaluation)
        )
        .where(SessionModel.user_id == current_user.id)
        .where(Solution.status == "approved")
        .order_by(Solution.updated_at.desc())
    )
    result = await db.execute(query)
    solutions = result.scalars().all()
    return list(solutions)
