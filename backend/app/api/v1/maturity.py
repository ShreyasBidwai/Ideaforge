from fastapi import APIRouter
from app.core.maturity import MATURITY_CONFIGS
from app.schemas.session import MaturityLevelInfo

router = APIRouter()

@router.get("/maturity-levels", response_model=list[MaturityLevelInfo])
async def get_maturity_levels():
    return list(MATURITY_CONFIGS.values())
