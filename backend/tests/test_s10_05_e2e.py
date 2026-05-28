import sys
import types
import app

# Register backend.app in sys.modules to support the specific patch paths required by the tests
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

E2E_MOCK = {"tests":[
  {"name":"health check","framework":"pytest-httpx","file_path":"e2e/test_health.py",
   "test_code":"import httpx, os\n\ndef test_health():\n    r=httpx.get(os.environ['BASE_URL']+'/health')\n    assert r.status_code==200"}
]}

# TEST 1: generate writes tests (mock claude)
@pytest.mark.anyio
@patch('backend.app.services.claude_service.ClaudeService.run_prompt')
async def test_generate_e2e(mock_claude, client, auth_headers, mock_gemini):
    mock_claude.return_value = {"success":True,"output":json.dumps(E2E_MOCK),"error":None,
        "is_rate_limited":False,"rate_limit_reset":None,"exit_code":0,"duration_seconds":12.0}
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    p = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    pid = p.json()["id"]
    r = await client.post(f"/api/v1/projects/{pid}/e2e/generate", headers=auth_headers)
    assert r.status_code == 200
    lst = await client.get(f"/api/v1/projects/{pid}/e2e", headers=auth_headers)
    assert len(lst.json()) >= 1

# TEST 2: generate handles rate limit
@pytest.mark.anyio
@patch('backend.app.services.claude_service.ClaudeService.run_prompt')
async def test_e2e_rate_limit(mock_claude, client, auth_headers, mock_gemini):
    mock_claude.return_value = {"success":False,"output":"","error":"rate limit",
        "is_rate_limited":True,"rate_limit_reset":None,"exit_code":1,"duration_seconds":1.0}
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    p = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    pid = p.json()["id"]
    r = await client.post(f"/api/v1/projects/{pid}/e2e/generate", headers=auth_headers)
    assert r.status_code == 429

# TEST 3: run requires running project
@pytest.mark.anyio
async def test_run_requires_running(client, auth_headers, mock_gemini):
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    p = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    pid = p.json()["id"]
    r = await client.post(f"/api/v1/projects/{pid}/e2e/run", headers=auth_headers)
    assert r.status_code in (409, 400)

# TEST 4: list endpoint
@pytest.mark.anyio
async def test_e2e_list(client, auth_headers, mock_gemini):
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    p = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    pid = p.json()["id"]
    r = await client.get(f"/api/v1/projects/{pid}/e2e", headers=auth_headers)
    assert r.status_code == 200
