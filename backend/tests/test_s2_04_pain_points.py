import pytest
import json
from unittest.mock import AsyncMock, patch

# ─── Prompt Template Tests ───

# TEST 1: Prompt template generates valid prompts
def test_prompt_template_generates():
    """build_pain_point_prompt should return (system_prompt, user_prompt) strings"""
    from app.ai.prompts.pain_points import build_pain_point_prompt
    from app.core.maturity import get_maturity_config, MaturityLevel
    config = get_maturity_config(MaturityLevel.MVP)
    system, user = build_pain_point_prompt("Healthcare", "Mumbai, India", config)
    assert isinstance(system, str)
    assert isinstance(user, str)
    assert "Healthcare" in user
    assert "Mumbai" in user
    assert "JSON" in system

# TEST 2: Prompt includes correct pain point count from maturity
def test_prompt_respects_maturity_count():
    """POC prompt should ask for fewer pain points than production"""
    from app.ai.prompts.pain_points import build_pain_point_prompt
    from app.core.maturity import get_maturity_config, MaturityLevel
    poc_sys, _ = build_pain_point_prompt("Fintech", "India", get_maturity_config(MaturityLevel.POC))
    prod_sys, _ = build_pain_point_prompt("Fintech", "India", get_maturity_config(MaturityLevel.PRODUCTION))
    assert "3" in poc_sys  # min count for POC
    assert "8" in prod_sys or "10" in prod_sys  # higher count for production

# TEST 3: Prompt enforces JSON-only output
def test_prompt_enforces_json():
    """System prompt must explicitly demand JSON-only output"""
    from app.ai.prompts.pain_points import build_pain_point_prompt
    from app.core.maturity import get_maturity_config, MaturityLevel
    system, _ = build_pain_point_prompt("EdTech", "India", get_maturity_config(MaturityLevel.MVP))
    assert "JSON" in system
    assert "no markdown" in system.lower() or "only valid json" in system.lower() or "only json" in system.lower()

# ─── Schema Validation Tests ───

# TEST 4: Valid pain point parses correctly
def test_valid_pain_point_schema():
    """PainPointSchema should accept valid data"""
    from app.schemas.pain_point import PainPointSchema
    pp = PainPointSchema(
        name="High patient wait times",
        description="Patients wait 3+ hours in urban hospitals.",
        severity=8,
        affected_stakeholders=["Patients", "Hospital administrators"],
        evidence="NITI Aayog reports show average OPD wait of 3.2 hours."
    )
    assert pp.severity == 8

# TEST 5: Invalid severity rejected
def test_invalid_severity_rejected():
    """Severity outside 1-10 should be rejected"""
    from app.schemas.pain_point import PainPointSchema
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PainPointSchema(name="Test", description="Test", severity=15, affected_stakeholders=[], evidence="Test")

# ─── Service Tests (Mocked AI) ───

# TEST 6: Service calls AI and returns parsed pain points
@pytest.mark.anyio
async def test_discover_pain_points_success(client, auth_headers, mock_gemini):
    """POST /sessions/{id}/discover should call AI and return pain points"""
    # Create session first
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "Mumbai, India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    
    # Mock AI response
    mock_gemini.return_value = json.dumps({
        "pain_points": [
            {
                "name": "Long patient wait times",
                "description": "Urban hospitals have 3+ hour wait times for OPD.",
                "severity": 8,
                "affected_stakeholders": ["Patients", "Doctors"],
                "evidence": "Government reports confirm this."
            },
            {
                "name": "Paper-based record keeping",
                "description": "90% of clinics still use paper records.",
                "severity": 7,
                "affected_stakeholders": ["Clinic staff", "Patients"],
                "evidence": "WHO India digital health survey."
            }
        ]
    })
    
    response = await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "pain_points" in data
    assert len(data["pain_points"]) >= 2

# TEST 7: Discovery updates session status
@pytest.mark.anyio
async def test_discover_updates_session_status(client, auth_headers, mock_gemini):
    """After discovery, session status should update to problem_generation"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Fintech", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    
    await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    session_response = await client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert session_response.json()["status"] == "problem_generation"

# TEST 8: GET pain points returns cached data
@pytest.mark.anyio
async def test_get_cached_pain_points(client, auth_headers, mock_gemini):
    """GET /sessions/{id}/pain-points should return stored data without AI call"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "EdTech", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    
    await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    mock_gemini.reset_mock()
    
    response = await client.get(f"/api/v1/sessions/{session_id}/pain-points", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["pain_points"]) >= 1
    mock_gemini.assert_not_called()  # Should NOT call AI again

# TEST 9: Discovery requires session ownership
@pytest.mark.anyio
async def test_discover_requires_ownership(client, auth_headers, other_auth_headers, mock_gemini):
    """Cannot discover on another user's session"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Gaming", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    response = await client.post(f"/api/v1/sessions/{session_id}/discover", headers=other_auth_headers)
    assert response.status_code == 403
