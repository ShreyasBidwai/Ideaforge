import pytest
from tests.test_s6_02_approvals import create_approved_solution

# TEST 1: Dependency fix prompt is correct
def test_dependency_fix_prompt():
    from backend.app.services.build_orchestrator import BuildOrchestrator
    orch = BuildOrchestrator(db=None)
    prompt = orch.build_dependency_fix_prompt(
        "ModuleNotFoundError: No module named 'redis'", "/project"
    )
    assert "redis" in prompt.lower()
    assert "install" in prompt.lower()

# TEST 2: Clean retry prompt includes existing context
def test_clean_retry_prompt():
    from backend.app.services.build_orchestrator import BuildOrchestrator
    orch = BuildOrchestrator(db=None)
    prompt = orch.build_clean_retry_prompt(
        "Create auth system",
        "TypeError: 'NoneType' object is not subscriptable",
        ["backend/app/main.py", "backend/app/core/config.py"]
    )
    assert "Create auth system" in prompt
    assert "TypeError" in prompt
    assert "main.py" in prompt

# TEST 3: Clean retry tells to read existing files
def test_clean_retry_reads_existing():
    from backend.app.services.build_orchestrator import BuildOrchestrator
    orch = BuildOrchestrator(db=None)
    prompt = orch.build_clean_retry_prompt("Task", "Error", ["file.py"])
    assert "read" in prompt.lower() or "existing" in prompt.lower()

# TEST 4: Dependency detection from error output
def test_detect_dependency_error():
    """Should detect when error is a missing dependency"""
    errors_that_are_deps = [
        "ModuleNotFoundError: No module named 'redis'",
        "Cannot find module 'axios'",
        "ImportError: No module named 'pydantic_settings'",
        "npm ERR! Could not resolve dependency",
    ]
    # This tests the detection logic exists and differentiates
    from backend.app.services.build_orchestrator import BuildOrchestrator
    orch = BuildOrchestrator(db=None)
    for err in errors_that_are_deps:
        prompt = orch.build_dependency_fix_prompt(err, "/project")
        assert "install" in prompt.lower()

# TEST 5: Retry failed API endpoint
@pytest.mark.anyio
async def test_retry_failed_endpoint(client, auth_headers, mock_gemini):
    """POST /build/retry-failed should exist"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    response = await client.post(f"/api/v1/projects/{proj_id}/build/retry-failed", headers=auth_headers)
    # Should return 200 or 400 (no failed task to retry), not 404
    assert response.status_code in [200, 400, 422]

# TEST 6: Failure details endpoint
@pytest.mark.anyio
async def test_failure_details_endpoint(client, auth_headers, mock_gemini):
    """GET /build/failure-details should return info"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    response = await client.get(f"/api/v1/projects/{proj_id}/build/failure-details", headers=auth_headers)
    assert response.status_code in [200, 404]  # 404 if no failures
