import pytest
import json
from unittest.mock import patch, MagicMock
from tests.test_s6_02_approvals import create_approved_solution

MOCK_SPRINTS = {
    "sprints": [
        {
            "sprint_number": 1, "name": "Foundation",
            "description": "Project setup and scaffolding",
            "tasks": [
                {"task_number": 1, "name": "Project scaffold",
                 "prompt": "Create a new project in an empty directory. Initialize with package.json for frontend (React 18 + TypeScript + Vite) and requirements.txt for backend (FastAPI + SQLAlchemy + PostgreSQL). Create directory structure: backend/app/, frontend/src/, backend/tests/, frontend/src/__tests__/. Create backend/app/main.py with FastAPI app and GET /health endpoint returning {status: healthy}. Create backend/tests/test_health.py with test for health endpoint. Run: cd backend && python -m pytest tests/test_health.py -v",
                 "test_command": "cd backend && python -m pytest tests/test_health.py -v",
                 "expected_test_count": 2},
                {"task_number": 2, "name": "Database models",
                 "prompt": "The project has FastAPI in backend/app/main.py. Create SQLAlchemy models in backend/app/models/user.py with User model (id, email, name, created_at). Create backend/app/core/database.py with async engine setup. Create backend/tests/test_models.py with model tests. Run: cd backend && python -m pytest tests/test_models.py -v",
                 "test_command": "cd backend && python -m pytest tests/test_models.py -v",
                 "expected_test_count": 4}
            ]
        },
        {
            "sprint_number": 2, "name": "Core Features",
            "description": "Main application features",
            "tasks": [
                {"task_number": 1, "name": "API endpoints",
                 "prompt": "The project has FastAPI in backend/app/main.py and User model in backend/app/models/user.py. Create REST endpoints in backend/app/api/v1/users.py: POST /users (create), GET /users (list), GET /users/{id} (detail). Create backend/tests/test_users.py with 6 tests. Run: cd backend && python -m pytest tests/test_users.py -v",
                 "test_command": "cd backend && python -m pytest tests/test_users.py -v",
                 "expected_test_count": 6}
            ]
        }
    ],
    "total_tasks": 3, "total_sprints": 2, "estimated_total_tests": 12
}

# TEST 1: Generate sprints creates sprint records (mock ClaudeService)
@patch('app.services.claude_service.ClaudeService.run_prompt')
async def test_generate_sprints(mock_claude, client, auth_headers, mock_gemini):
    """POST /projects/{id}/generate-sprints should create sprints with tasks via Claude Code"""
    mock_claude.return_value = {
        "success": True,
        "output": json.dumps(MOCK_SPRINTS),
        "error": None,
        "is_rate_limited": False,
        "rate_limit_reset": None,
        "exit_code": 0,
        "duration_seconds": 45.2
    }
    
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc content"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    
    response = await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    assert response.status_code == 200
    
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    assert len(sprints.json()) >= 2

# TEST 2: Each task has a self-contained prompt
@patch('app.services.claude_service.ClaudeService.run_prompt')
async def test_tasks_have_detailed_prompts(mock_claude, client, auth_headers, mock_gemini):
    mock_claude.return_value = {
        "success": True, "output": json.dumps(MOCK_SPRINTS),
        "error": None, "is_rate_limited": False, "rate_limit_reset": None,
        "exit_code": 0, "duration_seconds": 30.0
    }
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    for sprint in sprints.json():
        tasks_resp = await client.get(f"/api/v1/projects/{proj_id}/sprints/{sprint['id']}/tasks", headers=auth_headers)
        for task in tasks_resp.json():
            assert len(task["prompt"]) > 50
            assert task["test_command"] is not None

# TEST 3: Tasks ordered correctly
@patch('app.services.claude_service.ClaudeService.run_prompt')
async def test_tasks_ordered(mock_claude, client, auth_headers, mock_gemini):
    mock_claude.return_value = {
        "success": True, "output": json.dumps(MOCK_SPRINTS),
        "error": None, "is_rate_limited": False, "rate_limit_reset": None,
        "exit_code": 0, "duration_seconds": 30.0
    }
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    sprint_numbers = [s["sprint_number"] for s in sprints.json()]
    assert sprint_numbers == sorted(sprint_numbers)

# TEST 4: Handles Claude Code rate limit gracefully
@patch('app.services.claude_service.ClaudeService.run_prompt')
async def test_handles_rate_limit(mock_claude, client, auth_headers, mock_gemini):
    mock_claude.return_value = {
        "success": False, "output": "",
        "error": "Rate limit exceeded",
        "is_rate_limited": True, "rate_limit_reset": "2026-05-27T19:00:00",
        "exit_code": 1, "duration_seconds": 2.0
    }
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    
    response = await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    assert response.status_code == 429

# TEST 5: Parses JSON even with markdown fences
def test_parse_json_with_fences():
    from app.services.sprint_generation_service import SprintGenerationService
    service = SprintGenerationService(db=None)
    output = '```json\n{"sprints": [], "total_tasks": 0, "total_sprints": 0, "estimated_total_tests": 0}\n```'
    result = service._parse_sprint_json(output)
    assert "sprints" in result

# TEST 6: First task is always project scaffold
@patch('app.services.claude_service.ClaudeService.run_prompt')
async def test_prompt_requests_scaffold_first(mock_claude, client, auth_headers, mock_gemini):
    """The prompt sent to Claude Code should require Sprint 1 Task 1 to be a scaffold"""
    mock_claude.return_value = {
        "success": True, "output": json.dumps(MOCK_SPRINTS),
        "error": None, "is_rate_limited": False, "rate_limit_reset": None,
        "exit_code": 0, "duration_seconds": 30.0
    }
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    # Check that Claude was called with a prompt mentioning scaffold
    call_args = mock_claude.call_args
    prompt_sent = call_args[1].get("prompt", "") if call_args[1] else call_args[0][0]
    assert "scaffold" in prompt_sent.lower() or "empty directory" in prompt_sent.lower() or "sprint 1, task 1" in prompt_sent.lower()
