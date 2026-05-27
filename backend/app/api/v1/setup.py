from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.models import User
from app.services.claude_service import ClaudeService, ClaudeStatus

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/claude-status")
async def get_claude_status(current_user: User = Depends(get_current_user)):
    return ClaudeService.check_installation()

@router.post("/claude-test")
async def run_claude_test(prompt: str = "say hello", current_user: User = Depends(get_current_user)):
    result = ClaudeService.run_prompt(prompt, cwd="/tmp")
    return result


@router.get("/ai-status")
async def get_ai_status(current_user: User = Depends(get_current_user)):
    from app.ai.provider import model_rotator
    status = model_rotator.get_status()
    available_count = len([v for v in status.values() if v == "available"])
    return {
        "models": status,
        "remaining_capacity": available_count * 20
    }

