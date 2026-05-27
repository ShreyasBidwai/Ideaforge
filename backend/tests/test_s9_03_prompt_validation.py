import pytest

# TEST 1: Good prompt passes validation
def test_good_prompt_passes():
    from backend.app.services.prompt_validator import PromptValidator
    prompt = """Create a FastAPI health endpoint.

## Files to Create
### backend/app/api/v1/health.py
- GET /health returns {"status": "healthy"}

## Test Cases
### backend/tests/test_health.py
```python
async def test_health(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
```

## Acceptance Criteria
- GET /health returns 200
- Response contains status field"""
    result = PromptValidator.validate_prompt(prompt)
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0

# TEST 2: Prompt referencing "previous" flagged
def test_references_previous():
    from backend.app.services.prompt_validator import PromptValidator
    prompt = "Using the same pattern as before, create the user service. Continue from the previous task."
    warnings = PromptValidator.check_self_contained(prompt)
    assert len(warnings) > 0

# TEST 3: Prompt without file paths flagged
def test_no_file_paths():
    from backend.app.services.prompt_validator import PromptValidator
    prompt = "Create the authentication system with login and register endpoints. Add proper validation."
    warnings = PromptValidator.check_file_paths(prompt)
    assert len(warnings) > 0

# TEST 4: Prompt without tests flagged
def test_no_tests():
    from backend.app.services.prompt_validator import PromptValidator
    prompt = "Create backend/app/services/auth.py with login and register functions."
    errors = PromptValidator.check_has_tests(prompt)
    assert len(errors) > 0

# TEST 5: Prompt with tests passes
def test_with_tests_passes():
    from backend.app.services.prompt_validator import PromptValidator
    prompt = """Create auth service.
    
### backend/tests/test_auth.py
```python
async def test_login(client):
    assert True
```

Run: cd backend && python -m pytest tests/test_auth.py -v"""
    errors = PromptValidator.check_has_tests(prompt)
    assert len(errors) == 0

# TEST 6: Too short prompt flagged
def test_too_short():
    from backend.app.services.prompt_validator import PromptValidator
    prompt = "Create auth."
    warnings = PromptValidator.check_length(prompt)
    assert len(warnings) > 0

# TEST 7: Too long prompt flagged
def test_too_long():
    from backend.app.services.prompt_validator import PromptValidator
    prompt = "x " * 10000  # 20000 chars
    warnings = PromptValidator.check_length(prompt)
    assert len(warnings) > 0

# TEST 8: Validate all prompts returns summary
def test_validate_all():
    from backend.app.services.prompt_validator import PromptValidator
    tasks = [
        {"name": "Good task", "prompt": "Create backend/app/main.py...\n\n### tests/test.py\n```python\ndef test(): pass\n```\nRun: pytest\n\nAcceptance: works"},
        {"name": "Bad task", "prompt": "Do the thing"},
    ]
    result = PromptValidator.validate_all_prompts(tasks)
    assert result["total_tasks"] == 2
    assert result["valid_tasks"] >= 1
    assert result["tasks_with_errors"] >= 1

# TEST 9: Validation API endpoint
@pytest.mark.anyio
async def test_validate_api(client, auth_headers, mock_gemini):
    """POST /projects/{id}/validate-prompts should return validation results"""
    import json
    from tests.test_s6_02_approvals import create_approved_solution
    from tests.test_s7_03_sprint_generation import MOCK_SPRINTS
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc"
    await client.post(f"/api/v1/projects/{proj_id}/generate-docs", headers=auth_headers)
    mock_gemini.return_value = json.dumps(MOCK_SPRINTS)
    await client.post(f"/api/v1/projects/{proj_id}/generate-sprints", headers=auth_headers)
    
    response = await client.post(f"/api/v1/projects/{proj_id}/validate-prompts", headers=auth_headers)
    assert response.status_code == 200
    assert "total_tasks" in response.json()
    assert "overall_score" in response.json()

# TEST 10: Self-contained check catches common phrases
def test_self_contained_catches_all():
    from backend.app.services.prompt_validator import PromptValidator
    bad_phrases = [
        "as we did before",
        "using the same pattern",
        "continue from the previous",
        "building on what we created",
        "the file we created earlier"
    ]
    for phrase in bad_phrases:
        warnings = PromptValidator.check_self_contained(f"Task: {phrase} create the service")
        assert len(warnings) > 0, f"Failed to catch: {phrase}"
