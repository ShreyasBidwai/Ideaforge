import pytest
import os
import tempfile
import json

try:
    from tests.test_s6_02_approvals import create_approved_solution
except ImportError:
    from backend.tests.test_s6_02_approvals import create_approved_solution

# TEST 1: find_free_port returns an int
def test_find_free_port():
    from backend.app.services.project_runner import ProjectRunner
    port = ProjectRunner.find_free_port(8200)
    assert isinstance(port, int)
    assert port >= 8200

# TEST 2: detect python backend
def test_detect_python_backend():
    from backend.app.services.project_runner import ProjectRunner
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "backend", "app"))
        open(os.path.join(tmp, "backend", "requirements.txt"), "w").close()
        open(os.path.join(tmp, "backend", "app", "main.py"), "w").close()
        info = ProjectRunner.detect_stack(tmp)
        assert info["has_backend"] is True

# TEST 3: detect node frontend
def test_detect_node_frontend():
    from backend.app.services.project_runner import ProjectRunner
    with tempfile.TemporaryDirectory() as tmp:
        fe = os.path.join(tmp, "frontend")
        os.makedirs(fe)
        with open(os.path.join(fe, "package.json"), "w") as f:
            json.dump({"scripts": {"dev": "vite"}}, f)
        info = ProjectRunner.detect_stack(tmp)
        assert info["has_frontend"] is True

# TEST 4: no project files → nothing detected
def test_detect_empty():
    from backend.app.services.project_runner import ProjectRunner
    with tempfile.TemporaryDirectory() as tmp:
        info = ProjectRunner.detect_stack(tmp)
        assert info["has_backend"] is False
        assert info["has_frontend"] is False

# TEST 5: status for unknown project
def test_status_unknown():
    from backend.app.services.project_runner import ProjectRunner
    s = ProjectRunner.status("nonexistent-project")
    assert s["status"] in ("stopped", "not_running", "unknown")

# TEST 6: get_logs returns list
def test_get_logs_empty():
    from backend.app.services.project_runner import ProjectRunner
    logs = ProjectRunner.get_logs("nonexistent", "backend")
    assert isinstance(logs, list)

# TEST 7: run is gated on setup manifest
async def test_run_gated_on_manifest(client, auth_headers, mock_gemini, monkeypatch):
    """start should 400 if required setup steps incomplete"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    # Force ready=False
    from app.services.setup_manifest_service import SetupManifestService
    async def fake_ready(self, pid): return False
    monkeypatch.setattr(SetupManifestService, "all_required_complete", fake_ready)
    r = await client.post(f"/api/v1/projects/{proj_id}/run/start", headers=auth_headers)
    assert r.status_code in (400, 409, 422)

# TEST 8: status endpoint reachable
async def test_status_endpoint(client, auth_headers, mock_gemini):
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    r = await client.get(f"/api/v1/projects/{proj_id}/run/status", headers=auth_headers)
    assert r.status_code == 200
    assert "status" in r.json()
