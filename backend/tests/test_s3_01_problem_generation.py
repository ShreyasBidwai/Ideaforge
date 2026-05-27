import pytest
import json

# ─── Rating Computation Tests ───

# TEST 1: Overall rating computation is correct
def test_overall_rating_computation():
    """Weighted average: (sev*2 + feas*2 + mkt*1.5 + uniq*1) / 6.5"""
    from app.services.problem_statement_service import ProblemStatementService
    rating = ProblemStatementService.compute_overall_rating(5, 4, 3, 2)
    expected = round((5*2 + 4*2 + 3*1.5 + 2*1) / 6.5, 2)
    assert rating == expected

# TEST 2: Rating with all 5s equals 5.0
def test_perfect_rating():
    """All 5s should produce rating of 5.0"""
    from app.services.problem_statement_service import ProblemStatementService
    rating = ProblemStatementService.compute_overall_rating(5, 5, 5, 5)
    assert rating == 5.0

# TEST 3: Rating with all 1s equals 1.0
def test_minimum_rating():
    """All 1s should produce rating of 1.0"""
    from app.services.problem_statement_service import ProblemStatementService
    rating = ProblemStatementService.compute_overall_rating(1, 1, 1, 1)
    assert rating == 1.0

# TEST 4: Severity and feasibility weigh more than uniqueness
def test_severity_weighs_more():
    """Changing severity should affect rating more than changing uniqueness"""
    from app.services.problem_statement_service import ProblemStatementService
    rating_high_sev = ProblemStatementService.compute_overall_rating(5, 3, 3, 3)
    rating_high_uniq = ProblemStatementService.compute_overall_rating(3, 3, 3, 5)
    assert rating_high_sev > rating_high_uniq

# ─── Prompt Template Tests ───

# TEST 5: Prompt includes pain points
def test_prompt_includes_pain_points():
    """User prompt should contain pain point data"""
    from app.ai.prompts.problem_statements import build_problem_statement_prompt
    from app.core.maturity import get_maturity_config, MaturityLevel
    pain_points = [
        {"name": "Long wait times", "severity": 8, "description": "Patients wait 3+ hours"},
        {"name": "Paper records", "severity": 7, "description": "90% clinics use paper"}
    ]
    config = get_maturity_config(MaturityLevel.MVP)
    system, user = build_problem_statement_prompt(pain_points, "Healthcare", "India", config)
    assert "Long wait times" in user
    assert "Paper records" in user
    assert "Healthcare" in user

# TEST 6: Prompt requests correct count based on maturity
def test_prompt_count_matches_maturity():
    """POC should request 2, production should request 3"""
    from app.ai.prompts.problem_statements import build_problem_statement_prompt
    from app.core.maturity import get_maturity_config, MaturityLevel
    pain_points = [{"name": "Test", "severity": 5, "description": "Test"}]
    poc_sys, _ = build_problem_statement_prompt(pain_points, "Fintech", "India", get_maturity_config(MaturityLevel.POC))
    prod_sys, _ = build_problem_statement_prompt(pain_points, "Fintech", "India", get_maturity_config(MaturityLevel.PRODUCTION))
    assert "2" in poc_sys
    assert "3" in prod_sys

# ─── Schema Validation Tests ───

# TEST 7: Valid problem statement schema
def test_valid_problem_statement_schema():
    """ProblemStatementCreate should accept valid data"""
    from app.schemas.problem_statement import ProblemStatementCreate
    ps = ProblemStatementCreate(
        title="Digital patient queue management",
        description="Hospitals need a digital queue system to reduce wait times.",
        target_user="Hospital administrators and outpatients",
        core_pain="3+ hour wait times causing patient dropout",
        market_context="India's hospital market is $100B+, digital health is growing 30% YoY",
        severity=4, feasibility=5, market_size=4, uniqueness=3
    )
    assert ps.severity == 4

# TEST 8: Ratings outside 1-5 rejected
def test_invalid_rating_rejected():
    """Ratings outside 1-5 should fail validation"""
    from app.schemas.problem_statement import ProblemStatementCreate
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ProblemStatementCreate(
            title="Test", description="Test", target_user="Test",
            core_pain="Test", market_context="Test",
            severity=6, feasibility=3, market_size=3, uniqueness=3
        )

# ─── API Tests (Mocked AI) ───

# TEST 9: Generate problem statements from session
@pytest.mark.anyio
async def test_generate_problem_statements(client, auth_headers, mock_gemini):
    """POST /sessions/{id}/generate-problems should return problem statements"""
    # Create session with pain points
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "Mumbai, India", "maturity_level": "mvp"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    
    # First discover pain points
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Wait times", "description": "Long waits", "severity": 8, "affected_stakeholders": ["Patients"], "evidence": "Data"},
        {"name": "Paper records", "description": "No digital records", "severity": 7, "affected_stakeholders": ["Doctors"], "evidence": "Data"}
    ]})
    await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    
    # Now generate problem statements
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {
            "title": "Digital Patient Queue System",
            "description": "Build a digital queue management system for hospitals.",
            "target_user": "Hospital administrators",
            "core_pain": "3+ hour patient wait times",
            "market_context": "India healthcare market growing rapidly.",
            "severity": 4, "feasibility": 5, "market_size": 4, "uniqueness": 3
        },
        {
            "title": "Electronic Health Records for Clinics",
            "description": "Cloud-based EHR for small/medium clinics.",
            "target_user": "Clinic owners and doctors",
            "core_pain": "Paper-based records cause errors and delays",
            "market_context": "90% of Indian clinics lack digital records.",
            "severity": 4, "feasibility": 4, "market_size": 5, "uniqueness": 2
        }
    ]})
    
    response = await client.post(f"/api/v1/sessions/{session_id}/generate-problems", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert all("overall_rating" in ps for ps in data)
    assert all(ps["overall_rating"] > 0 for ps in data)

# TEST 10: Generated problem statements are persisted
@pytest.mark.anyio
async def test_problem_statements_persisted(client, auth_headers, mock_gemini):
    """GET /sessions/{id}/problem-statements should return stored problems"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Fintech", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "Test Problem", "description": "Test desc", "target_user": "Users",
         "core_pain": "Pain", "market_context": "Market", "severity": 3, "feasibility": 4, "market_size": 3, "uniqueness": 3}
    ]})
    await client.post(f"/api/v1/sessions/{session_id}/generate-problems", headers=auth_headers)
    
    response = await client.get(f"/api/v1/sessions/{session_id}/problem-statements", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1

# TEST 11: Session status updates after generation
@pytest.mark.anyio
async def test_session_status_updates(client, auth_headers, mock_gemini):
    """Session status should change to solution_generation after problem generation"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "EdTech", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "Test", "description": "Test", "target_user": "Users",
         "core_pain": "Pain", "market_context": "Mkt", "severity": 3, "feasibility": 3, "market_size": 3, "uniqueness": 3}
    ]})
    await client.post(f"/api/v1/sessions/{session_id}/generate-problems", headers=auth_headers)
    
    session_resp = await client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert session_resp.json()["status"] == "solution_generation"

# TEST 12: Cannot generate without pain points
@pytest.mark.anyio
async def test_generate_without_pain_points_fails(client, auth_headers):
    """Generating problems without discovering pain points first should fail"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Gaming", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    response = await client.post(f"/api/v1/sessions/{session_id}/generate-problems", headers=auth_headers)
    assert response.status_code in [400, 422]
