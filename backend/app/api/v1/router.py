from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.maturity import router as maturity_router
from app.api.v1.tech_stacks import router as tech_stacks_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.pain_points import router as pain_points_router
from app.api.v1.problem_statements import router as problem_statements_router
from app.api.v1.solutions import router as solutions_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.projects import router as projects_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(maturity_router, tags=["maturity"])
router.include_router(tech_stacks_router, prefix="/tech-stacks", tags=["tech-stacks"])
router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
router.include_router(pain_points_router, tags=["pain-points"])
router.include_router(problem_statements_router, tags=["problem-statements"])
router.include_router(solutions_router, tags=["solutions"])
router.include_router(evaluations_router, tags=["evaluations"])
router.include_router(dashboard_router, tags=["dashboard"])
router.include_router(approvals_router, tags=["approvals"])
router.include_router(projects_router, tags=["projects"])




