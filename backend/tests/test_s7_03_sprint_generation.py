import pytest
import json
from tests.test_s6_02_approvals import create_approved_solution

MOCK_SPRINTS = {
    "sprints": [
        {
            "sprint_number": 1, "name": "Foundation",
            "description": "Project setup and scaffolding",
            "tasks": [
                {"task_number": 1, "name": "Backend scaffolding",
                 "prompt": "Create a FastAPI project in backend/ with health endpoint...",
                 "test_command": "cd backend && python -m pytest tests/test_scaffolding.py -v",
                 "expected_test_count": 5, "estimated_tokens": 3000},
                {"task_number": 2, "name": "Database models",
                 "prompt": "Create SQLAlchemy models in backend/app/models/...",
                 "test_command": "cd backend && python -m pytest tests/test_models.py -v",
                 "expected_test_count": 6, "estimated_tokens": 4000}
            ]
        },
        {
            "sprint_number": 2, "name": "Core Features",
            "description": "Main application features",
            "tasks": [
                {"task_number": 1, "name": "API endpoints",
                 "prompt": "Create REST endpoints in backend/app/api/...",
                 "test_command": "cd backend && python -m pytest tests/test_api.py -v",
                 "expected_test_count": 8, "estimated_tokens": 5000}
            ]
        }
    ],
    "total_tasks": 3, "total_sprints": 2, "estimated_total_tests": 19
}

# TEST 1: Generate sprints creates sprint records
async def test_generate_sprints(client, auth_headers, mock_gemini):
    """POST /projects/{id}/generate-sprints should create sprints with tasks"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc content"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    
    mock_gemini.return_value = json.dumps(MOCK_SPRINTS)
    response = await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    assert response.status_code == 200
    
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    assert len(sprints.json()) >= 2

# TEST 2: Each task has a non-empty prompt
async def test_tasks_have_prompts(client, auth_headers, mock_gemini):
    """Every sprint task should have a prompt and test command"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_SPRINTS)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    for sprint in sprints.json():
        tasks_resp = await client.get(f"/api/v1/projects/{proj_id}/sprints/{sprint['id']}/tasks", headers=auth_headers)
        for task in tasks_resp.json():
            assert len(task["prompt"]) > 20
            assert task["test_command"] is not None

# TEST 3: Tasks are ordered correctly
async def test_tasks_ordered(client, auth_headers, mock_gemini):
    """Tasks should be in order within each sprint"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_SPRINTS)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    sprints = await client.get(f"/api/v1/projects/{proj_id}/sprints", headers=auth_headers)
    sprint_numbers = [s["sprint_number"] for s in sprints.json()]
    assert sprint_numbers == sorted(sprint_numbers)

# TEST 4: Sprint prompt template enforces self-contained prompts
def test_sprint_prompt_enforces_self_contained():
    """Prompt template should demand self-contained task prompts"""
    from app.ai.prompts.docs.sprint_prompts import build_sprint_prompts_prompt
    context = {"solution": {"title": "Test", "tech_stack": ["React"]}, "session": {"industry": "HC", "location": "IN", "maturity_level": "mvp"}}
    system, _ = build_sprint_prompts_prompt(context, "arch doc", "prd doc", "trd doc")
    assert "self-contained" in system.lower() or "self contained" in system.lower()
    assert "no memory" in system.lower() or "fresh session" in system.lower()

# TEST 5: Project status updates after sprint generation
async def test_project_status_after_sprints(client, auth_headers, mock_gemini):
    """Project status should change to doc_review after sprints generated"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_SPRINTS)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    proj = await client.get(f"/api/v1/projects/{proj_id}", headers=auth_headers)
    assert proj.json()["status"] == "doc_review"


def test_clean_json_response():
    """Verify that clean_json_response successfully cleans raw markdown and wrapping text"""
    from app.services.sprint_generation_service import clean_json_response
    
    # 1. Plain clean JSON
    plain = '{"sprints": []}'
    assert clean_json_response(plain) == plain
    
    # 2. Wrapped in markdown code block
    markdown = '```json\n{"sprints": []}\n```'
    assert clean_json_response(markdown) == plain
    
    # 3. Code block without json language identifier
    markdown_plain = '```\n{"sprints": []}\n```'
    assert clean_json_response(markdown_plain) == plain
    
    # 4. Text prefix and suffix
    text_wrapped = 'Here is the plan: {"sprints": []} Hope it helps!'
    assert clean_json_response(text_wrapped) == plain

    # 5. Absurdly large hallucinated numbers (Gemini bug)
    import json
    huge_num = '{"sprints": [], "total_tasks": ' + '5' * 500 + '}'
    cleaned = clean_json_response(huge_num)
    parsed = json.loads(cleaned)  # must not raise
    assert parsed["total_tasks"] == 0
    assert parsed["sprints"] == []

    # 6. Raw newlines and tabs inside string fields
    raw_newlines = '{"sprints": [], "prompt": "Hello\nWorld\twith\ttabs\rhere"}'
    cleaned_raw = clean_json_response(raw_newlines)
    parsed_raw = json.loads(cleaned_raw)
    assert parsed_raw["prompt"] == "Hello\nWorld\twith\ttabs\rhere"


