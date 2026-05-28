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
    import asyncio
    result = await asyncio.to_thread(ClaudeService.run_prompt, prompt, cwd="/tmp")
    return result


@router.get("/debug-claude")
async def debug_claude(current_user: User = Depends(get_current_user)):
    """Debug endpoint — runs a simple Claude Code test and returns full diagnostics"""
    import shutil
    import os
    import asyncio
    
    diagnostics = {
        "claude_path_shutil": shutil.which("claude"),
        "claude_path_resolved": ClaudeService._find_claude_binary(),
        "node_path": shutil.which("node"),
        "npm_path": shutil.which("npm"),
        "path_env": os.environ.get("PATH", "NOT SET"),
        "home_dir": os.path.expanduser("~"),
        "npm_global_exists": os.path.isdir(os.path.expanduser("~/.npm-global/bin")),
        "npm_global_contents": [],
        "test_result": None
    }
    
    # Check npm global bin contents
    npm_global = os.path.expanduser("~/.npm-global/bin")
    if os.path.isdir(npm_global):
        diagnostics["npm_global_contents"] = os.listdir(npm_global)
    
    # Try running claude
    try:
        result = await asyncio.to_thread(
            ClaudeService.run_prompt,
            prompt="Respond with exactly: CLAUDE_CODE_WORKING",
            cwd="/tmp",
            timeout=60
        )
        diagnostics["test_result"] = result
    except Exception as e:
        diagnostics["test_result"] = {"error": str(e), "type": type(e).__name__}
    
    return diagnostics


@router.get("/ai-status")
async def get_ai_status(current_user: User = Depends(get_current_user)):
    from app.ai.provider import model_rotator
    status = model_rotator.get_status()
    available_count = len([v for v in status.values() if v == "available"])
    return {
        "models": status,
        "remaining_capacity": available_count * 20
    }

