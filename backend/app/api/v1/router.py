from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.maturity import router as maturity_router
from app.api.v1.tech_stacks import router as tech_stacks_router
from app.api.v1.sessions import router as sessions_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(maturity_router, tags=["maturity"])
router.include_router(tech_stacks_router, prefix="/tech-stacks", tags=["tech-stacks"])
router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])

