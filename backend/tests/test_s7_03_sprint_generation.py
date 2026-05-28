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

def make_gemini_side_effect(fail_sprints=False):
    def gemini_side_effect(prompt, system_prompt, response_schema=None, *args, **kwargs):
        if response_schema:
            properties = response_schema.get("properties", {})
            if "sprints" in properties:
                if fail_sprints:
                    raise RuntimeError("All free-tier Gemini models exhausted")
                return json.dumps(MOCK_SPRINTS)
            if "prompt" in properties:
                import re
                sprint_match = re.search(r"Current Sprint:\s*(\d+)", prompt)
                task_match = re.search(r"Current Task Number:\s*(\d+)", prompt)
                sprint_num = int(sprint_match.group(1)) if sprint_match else 1
                task_num = int(task_match.group(1)) if task_match else 1
                
                target_sprint = next((s for s in MOCK_SPRINTS["sprints"] if s["sprint_number"] == sprint_num), None)
                if target_sprint:
                    target_task = next((t for t in target_sprint["tasks"] if t["task_number"] == task_num), None)
                    if target_task:
                        return json.dumps({
                            "prompt": target_task["prompt"],
                            "test_command": target_task["test_command"],
                            "expected_test_count": target_task["expected_test_count"]
                        })
                return json.dumps({
                    "prompt": "Default task instruction prompt detailing files and test command.",
                    "test_command": "cd backend && python -m pytest tests/test_health.py -v",
                    "expected_test_count": 2
                })
            if "pain_points" in properties:
                return json.dumps({"pain_points": [
                    {"name": "P", "description": "D", "severity": 5, "affected_stakeholders": ["U"], "evidence": "E"}
                ]})
            if "problem_statements" in properties:
                return json.dumps({"problem_statements": [
                    {"title": "Problem", "description": "D", "target_user": "U", "core_pain": "P", "market_context": "M",
                     "severity": 4, "feasibility": 4, "market_size": 4, "uniqueness": 3}
                ]})
            if "solutions" in properties:
                return json.dumps({"solutions": [
                    {"title": "Approved Sol", "description": "D", "mechanism": "M", "tech_stack": ["React"],
                     "target_user": "Users", "revenue_model": "SaaS $99/mo", "is_unconventional": False}
                ]})
        return "# Doc content"
    return gemini_side_effect

# TEST 1: Generate sprints creates sprint records (mock GeminiProvider)
async def test_generate_sprints(client, auth_headers, mock_gemini):
    """POST /projects/{id}/generate-sprints should create sprints with tasks via Gemini"""
    mock_gemini.side_effect = make_gemini_side_effect()
    
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    
    response = await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    assert response.status_code == 200
    
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    assert len(sprints.json()) >= 2

# TEST 2: Each task has a self-contained prompt
async def test_tasks_have_detailed_prompts(client, auth_headers, mock_gemini):
    mock_gemini.side_effect = make_gemini_side_effect()
    
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    for sprint in sprints.json():
        tasks_resp = await client.get(f"/api/v1/projects/{proj_id}/sprints/{sprint['id']}/tasks", headers=auth_headers)
        for task in tasks_resp.json():
            assert len(task["prompt"]) > 50
            assert task["test_command"] is not None

# TEST 3: Tasks ordered correctly
async def test_tasks_ordered(client, auth_headers, mock_gemini):
    mock_gemini.side_effect = make_gemini_side_effect()
    
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    sprint_numbers = [s["sprint_number"] for s in sprints.json()]
    assert sprint_numbers == sorted(sprint_numbers)

# TEST 4: Handles Gemini rate limit gracefully
async def test_handles_rate_limit(client, auth_headers, mock_gemini):
    mock_gemini.side_effect = make_gemini_side_effect(fail_sprints=True)
    
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    
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
async def test_prompt_requests_scaffold_first(client, auth_headers, mock_gemini):
    """The prompt sent to Gemini should require Sprint 1 Task 1 to be a scaffold"""
    prompts_captured = []
    def capturing_side_effect(prompt, system_prompt, response_schema=None, *args, **kwargs):
        prompts_captured.append(prompt)
        side_effect = make_gemini_side_effect()
        return side_effect(prompt, system_prompt, response_schema, *args, **kwargs)
    
    mock_gemini.side_effect = capturing_side_effect
    
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    # Find the prompt that was sent to generate sprints
    sprint_prompt = next((p for p in prompts_captured if "sprints" in p.lower() or "sprint" in p.lower()), "")
    assert "scaffold" in sprint_prompt.lower() or "empty directory" in sprint_prompt.lower() or "sprint 1, task 1" in sprint_prompt.lower()

# TEST 7: Database and runnable on localhost directives in sprint/roadmap prompts
def test_sprint_generation_prompts_db_and_localhost_directives():
    """Verify database and runnable on localhost directives in sprint/roadmap prompt generation."""
    from app.services.sprint_generation_service import SprintGenerationService
    from app.models.project import Project
    
    project = Project(
        maturity_level="mvp",
        documents=[]
    )
    context = {
        "solution": {"title": "App", "tech_stack": ["Python"]},
        "session": {"industry": "Health", "location": "US", "maturity_level": "mvp"}
    }
    
    service = SprintGenerationService(db=None)
    roadmap_prompt = service._build_roadmap_prompt(project, context)
    assert "SQLite" in roadmap_prompt
    assert "app.db" in roadmap_prompt

    task_prompt = service._build_task_detail_prompt(
        project, context, {"sprints": []}, 1, 1, "Task", "Desc"
    )
    assert "SQLite" in task_prompt
    assert "RUNNABLE ON LOCALHOST DIRECTIVE" in task_prompt
