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


# TEST 10: Toggle pause_on_failure via PATCH API
async def test_patch_project_settings(client, auth_headers, mock_gemini):
    """PATCH /projects/{id} to toggle pause_on_failure"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project_res = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project_res.json()["id"]
    
    # Toggle pause_on_failure to True
    response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"pause_on_failure": True},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["pause_on_failure"] is True
    
    # Toggle pause_on_failure to False
    response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"pause_on_failure": False},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["pause_on_failure"] is False


# TEST 11: Orchestrator pause on failure behaviour
@patch("app.services.build_orchestrator.BuildOrchestrator.execute_task")
async def test_orchestrator_pause_on_failure(mock_execute, client, auth_headers, mock_gemini):
    """If pause_on_failure is enabled, failing tasks should pause the entire project build status"""
    from app.core.database import async_session
    from app.services.build_orchestrator import BuildOrchestrator
    from app.models.project import Project
    from app.models.sprint import Sprint
    from app.models.sprint_task import SprintTask
    from app.models.user import User
    from sqlalchemy.future import select
    from uuid import uuid4

    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project_res = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project_res.json()["id"]
    
    # Enable pause_on_failure
    await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"pause_on_failure": True},
        headers=auth_headers
    )

    async with async_session() as db:
        # Get actual registered user id
        stmt_user = select(User)
        res_user = await db.execute(stmt_user)
        user = res_user.scalars().first()
        user_id = user.id

        # Create a mock sprint and tasks
        sprint = Sprint(id=uuid4(), project_id=proj_id, sprint_number=1, name="Sprint 1")
        task = SprintTask(
            id=uuid4(),
            sprint_id=sprint.id,
            task_number=1,
            name="Task 1",
            prompt="Write hello world",
            status="pending"
        )
        db.add(sprint)
        db.add(task)
        await db.commit()

        # Mock execution failure
        mock_execute.return_value = False

        # Run orchestrator
        orch = BuildOrchestrator(db)
        await orch.start_build(proj_id, user_id)

        # Verify project is paused
        stmt = select(Project).where(Project.id == proj_id)
        res = await db.execute(stmt)
        proj = res.scalars().first()
        assert proj.status == "paused"


# TEST 12: Orchestrator self healing behaviour
@patch("app.services.build_orchestrator.BuildOrchestrator.execute_task")
async def test_orchestrator_continue_with_self_healing(mock_execute, client, auth_headers, mock_gemini):
    """If pause_on_failure is disabled, failing tasks should skip first, then heal at the end"""
    from app.core.database import async_session
    from app.services.build_orchestrator import BuildOrchestrator
    from app.models.project import Project
    from app.models.sprint import Sprint
    from app.models.sprint_task import SprintTask
    from app.models.user import User
    from sqlalchemy.future import select
    from uuid import uuid4

    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project_res = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project_res.json()["id"]
    
    # Ensure pause_on_failure is False
    await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"pause_on_failure": False},
        headers=auth_headers
    )

    async with async_session() as db:
        # Get actual registered user id
        stmt_user = select(User)
        res_user = await db.execute(stmt_user)
        user = res_user.scalars().first()
        user_id = user.id

        # Create a mock sprint and task
        sprint = Sprint(id=uuid4(), project_id=proj_id, sprint_number=1, name="Sprint 1")
        task = SprintTask(
            id=uuid4(),
            sprint_id=sprint.id,
            task_number=1,
            name="Task 1",
            prompt="Write hello world",
            status="pending"
        )
        db.add(sprint)
        db.add(task)
        await db.commit()

        # Mock execution failure on first run, success on self-healing run
        mock_execute.side_effect = [False, True]

        # Run orchestrator
        orch = BuildOrchestrator(db)
        await orch.start_build(proj_id, user_id)

        # Verify task is now passed after self-healing and project status is complete
        stmt = select(Project).where(Project.id == proj_id)
        res = await db.execute(stmt)
        proj = res.scalars().first()
        assert proj.status == "complete"

