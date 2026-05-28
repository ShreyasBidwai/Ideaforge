import pytest
import os
import tempfile

try:
    from tests.test_s6_02_approvals import create_approved_solution
except ImportError:
    from backend.tests.test_s6_02_approvals import create_approved_solution

# TEST 1: API_KEY line becomes required api_key step
def test_env_apikey_is_required():
    from app.services.setup_manifest_service import SetupManifestService
    svc = SetupManifestService(db=None)
    steps = svc._parse_env_example("STRIPE_SECRET_KEY=\nDATABASE_URL=sqlite+aiosqlite:///./app.db\n")
    by_key = {s["env_key"]: s for s in steps}
    assert by_key["STRIPE_SECRET_KEY"]["step_type"] == "api_key"
    assert by_key["STRIPE_SECRET_KEY"]["is_required"] is True

# TEST 2: DATABASE_URL with sqlite default is NOT required
def test_sqlite_db_not_required():
    from app.services.setup_manifest_service import SetupManifestService
    svc = SetupManifestService(db=None)
    steps = svc._parse_env_example("DATABASE_URL=sqlite+aiosqlite:///./app.db\n")
    by_key = {s["env_key"]: s for s in steps}
    assert by_key["DATABASE_URL"]["is_required"] is False

# TEST 3: SECRET/TOKEN keys are api_key type
def test_secret_token_detected():
    from app.services.setup_manifest_service import SetupManifestService
    svc = SetupManifestService(db=None)
    steps = svc._parse_env_example("JWT_SECRET=\nAUTH_TOKEN=\n")
    types = {s["env_key"]: s["step_type"] for s in steps}
    assert types["JWT_SECRET"] == "api_key"
    assert types["AUTH_TOKEN"] == "api_key"

# TEST 4: Comments and blank lines ignored
def test_ignores_comments():
    from app.services.setup_manifest_service import SetupManifestService
    svc = SetupManifestService(db=None)
    steps = svc._parse_env_example("# this is a comment\n\nAPI_KEY=\n")
    assert len(steps) == 1
    assert steps[0]["env_key"] == "API_KEY"

# TEST 5: write_env_value rejects unknown keys
def test_write_rejects_unknown_key():
    from app.services.setup_manifest_service import SetupManifestService
    svc = SetupManifestService(db=None)
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, ".env.example"), "w") as f:
            f.write("KNOWN_KEY=\n")
        ok = svc._write_env_line(tmp, "EVIL_KEY", "x", allowed_keys={"KNOWN_KEY"})
        assert ok is False

# TEST 6: write_env_value rejects newline injection
def test_write_rejects_newline():
    from app.services.setup_manifest_service import SetupManifestService
    svc = SetupManifestService(db=None)
    with tempfile.TemporaryDirectory() as tmp:
        ok = svc._write_env_line(tmp, "API_KEY", "abc\nMALICIOUS=1", allowed_keys={"API_KEY"})
        assert ok is False

# TEST 7: write_env_value writes valid key
def test_write_valid_value():
    from app.services.setup_manifest_service import SetupManifestService
    svc = SetupManifestService(db=None)
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, ".env.example"), "w") as f:
            f.write("API_KEY=\n")
        ok = svc._write_env_line(tmp, "API_KEY", "sk-12345", allowed_keys={"API_KEY"})
        assert ok is True
        with open(os.path.join(tmp, ".env")) as f:
            assert "API_KEY=sk-12345" in f.read()

# TEST 8: known service detected from docs
def test_known_service_detected():
    from app.services.setup_manifest_service import SetupManifestService
    svc = SetupManifestService(db=None)
    extra = svc._scan_docs_for_services("The app uses Stripe for payments and SendGrid for email.")
    names = {s["title"].lower() for s in extra}
    assert any("stripe" in n for n in names)
    assert any("sendgrid" in n for n in names)

# TEST 9: manifest endpoint
async def test_manifest_endpoint(client, auth_headers, mock_gemini):
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    
    # Generate manifest first to populate database for listing
    await client.post(f"/api/v1/projects/{proj_id}/setup-manifest/generate", headers=auth_headers)
    
    r = await client.get(f"/api/v1/projects/{proj_id}/setup-manifest", headers=auth_headers)
    assert r.status_code == 200

# TEST 10: ready gate endpoint
async def test_ready_gate(client, auth_headers, mock_gemini):
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    
    # Generate manifest first to populate database for listing
    await client.post(f"/api/v1/projects/{proj_id}/setup-manifest/generate", headers=auth_headers)
    
    r = await client.get(f"/api/v1/projects/{proj_id}/setup-manifest/ready", headers=auth_headers)
    assert r.status_code == 200
    assert "ready" in r.json()
