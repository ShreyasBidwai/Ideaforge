import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from tests.test_s6_02_approvals import create_approved_solution

# TEST 1: Parse "Resets in: 4 hours 23 minutes"
def test_parse_resets_in():
    from app.services.build_orchestrator import BuildOrchestrator
    orch = BuildOrchestrator(db=None)
    output = "You've reached your usage limit. Resets in: 4 hours 23 minutes"
    reset_time = orch.parse_rate_limit_reset(output)
    assert reset_time is not None
    expected_min = datetime.utcnow() + timedelta(hours=4, minutes=22)
    expected_max = datetime.utcnow() + timedelta(hours=4, minutes=24)
    assert expected_min <= reset_time <= expected_max

# TEST 2: Parse "Your limit will reset at 7pm"
def test_parse_reset_at_time():
    from app.services.build_orchestrator import BuildOrchestrator
    orch = BuildOrchestrator(db=None)
    output = "Claude usage limit reached. Your limit will reset at 7:00 PM"
    reset_time = orch.parse_rate_limit_reset(output)
    assert reset_time is not None

# TEST 3: No rate limit returns None
def test_parse_no_rate_limit():
    from app.services.build_orchestrator import BuildOrchestrator
    orch = BuildOrchestrator(db=None)
    output = "Successfully created the file backend/app/main.py"
    reset_time = orch.parse_rate_limit_reset(output)
    assert reset_time is None

# TEST 4: Retry prompt includes original and errors
def test_retry_prompt_content():
    from app.services.build_orchestrator import BuildOrchestrator
    orch = BuildOrchestrator(db=None)
    retry = orch.build_retry_prompt("Create auth system", "AssertionError: expected 200 got 401")
    assert "Create auth system" in retry
    assert "AssertionError" in retry
    assert "fix" in retry.lower()

# TEST 5: Retry prompt tells not to modify tests
def test_retry_preserves_tests():
    from app.services.build_orchestrator import BuildOrchestrator
    orch = BuildOrchestrator(db=None)
    retry = orch.build_retry_prompt("Original task", "Test failed")
    assert "do not modify the test" in retry.lower() or "don't modify test" in retry.lower() or "fix the source" in retry.lower()

# TEST 6: Test output parsing
@patch("subprocess.run")
def test_parse_test_output(mock_run):
    from app.services.build_orchestrator import BuildOrchestrator
    orch = BuildOrchestrator(db=None)
    mock_run.return_value = MagicMock(
        stdout="tests/test_auth.py::test_login PASSED\ntests/test_auth.py::test_register PASSED\ntests/test_auth.py::test_bad_login FAILED\n================ 2 passed, 1 failed ================",
        stderr="",
        returncode=1
    )
    passed, failed, output = orch.run_tests("pytest", "/tmp")
    assert passed == 2
    assert failed == 1

# TEST 7: CronService schedules and cancels
async def test_cron_schedule():
    from app.services.cron_service import CronService
    import uuid
    project_id = uuid.uuid4()
    callback_called = False
    async def callback(pid):
        nonlocal callback_called
        callback_called = True
    
    resume_at = datetime.utcnow() + timedelta(seconds=1)
    await CronService.schedule_resume(project_id, resume_at, callback)
    assert str(project_id) in CronService._scheduled_jobs
    
    # Cancel before it fires
    await CronService.cancel_job(project_id)
    assert str(project_id) not in CronService._scheduled_jobs

# TEST 8: Build status endpoint
async def test_build_status(client, auth_headers, mock_gemini):
    """GET /build/status should return current build state"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    response = await client.get(f"/api/v1/projects/{proj_id}/build/status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "current_task" in data or "progress" in data

# TEST 9: Build logs endpoint
async def test_build_logs(client, auth_headers, mock_gemini):
    """GET /build/logs should return build log entries"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    response = await client.get(f"/api/v1/projects/{proj_id}/build/logs", headers=auth_headers)
    assert response.status_code == 200
