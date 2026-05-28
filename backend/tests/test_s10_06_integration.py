import sys
import types
import app

# Register backend.app in sys.modules to support the specific import paths required by the tests
backend_module = types.ModuleType('backend')
backend_module.app = app
sys.modules['backend'] = backend_module

import pytest
import json
from unittest.mock import patch

try:
    from tests.test_s6_02_approvals import create_approved_solution
except ImportError:
    from backend.tests.test_s6_02_approvals import create_approved_solution

# TEST 1: project flow exposes setup manifest + run status + e2e endpoints
@pytest.mark.anyio
async def test_runnable_endpoints_exist(client, auth_headers, mock_gemini):
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    p = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    pid = p.json()["id"]
    assert (await client.get(f"/api/v1/projects/{pid}/setup-manifest", headers=auth_headers)).status_code == 200
    assert (await client.get(f"/api/v1/projects/{pid}/setup-manifest/ready", headers=auth_headers)).status_code == 200
    assert (await client.get(f"/api/v1/projects/{pid}/run/status", headers=auth_headers)).status_code == 200
    assert (await client.get(f"/api/v1/projects/{pid}/e2e", headers=auth_headers)).status_code == 200

# TEST 2: sqlite project needs no required DB step
def test_sqlite_no_required_db():
    """When project maturity is mvp and .env.example has sqlite DATABASE_URL, DB is not a required step"""
    from backend.app.services.setup_manifest_service import SetupManifestService
    svc = SetupManifestService(db=None)
    steps = svc._parse_env_example("DATABASE_URL=sqlite+aiosqlite:///./app.db\nSTRIPE_SECRET_KEY=\n")
    required = [s for s in steps if s["is_required"]]
    keys = {s["env_key"] for s in required}
    assert "DATABASE_URL" not in keys
    assert "STRIPE_SECRET_KEY" in keys

# TEST 3: run gated until required setup complete (covered, re-assert wiring)
@pytest.mark.anyio
async def test_full_gate(client, auth_headers, mock_gemini, monkeypatch):
    from backend.app.services.setup_manifest_service import SetupManifestService
    async def not_ready(self, pid): return False
    monkeypatch.setattr(SetupManifestService, "all_required_complete", not_ready)
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    p = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    pid = p.json()["id"]
    r = await client.post(f"/api/v1/projects/{pid}/run/start", headers=auth_headers)
    assert r.status_code in (400, 409, 422)
