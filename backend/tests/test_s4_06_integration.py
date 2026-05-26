import pytest
import json

MOCK_SOLUTIONS_5 = {"solutions": [
    {"title": f"Solution {i+1}", "description": f"Desc {i+1}", "mechanism": f"Unique mechanism {i+1} that is different",
     "tech_stack": [f"Tech{i+1}A", f"Tech{i+1}B"], "target_user": f"User {i+1}",
     "revenue_model": f"Model {i+1}", "is_unconventional": i == 4}
    for i in range(5)
]}

async def full_pipeline_to_solutions(client, auth_headers, mock_gemini, industry="Healthcare", maturity="mvp"):
    """Helper: runs full pipeline from session to solutions"""
    session = await client.post("/api/v1/sessions", json={
        "industry": industry, "location": "India", "maturity_level": maturity,
        "tech_stack_preferences": ["React", "FastAPI"]
    }, headers=auth_headers)
    sid = session.json()["id"]
    
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Pain 1", "description": "Desc", "severity": 8, "affected_stakeholders": ["Users"], "evidence": "Data"},
        {"name": "Pain 2", "description": "Desc", "severity": 6, "affected_stakeholders": ["Admins"], "evidence": "Data"}
    ]})
    await client.post(f"/api/v1/sessions/{sid}/discover", headers=auth_headers)
    
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "Problem 1", "description": "Desc", "target_user": "Users",
         "core_pain": "Pain", "market_context": "Market", "severity": 4, "feasibility": 4, "market_size": 4, "uniqueness": 3}
    ]})
    problems = await client.post(f"/api/v1/sessions/{sid}/generate-problems", headers=auth_headers)
    pid = problems.json()[0]["id"]
    await client.post(f"/api/v1/problem-statements/{pid}/select", headers=auth_headers)
    
    mock_gemini.return_value = json.dumps(MOCK_SOLUTIONS_5)
    solutions = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    return sid, pid, solutions.json()

# TEST 1: Full pipeline produces solutions
async def test_full_pipeline(client, auth_headers, mock_gemini):
    """Complete flow from session to solutions should work"""
    sid, pid, solutions = await full_pipeline_to_solutions(client, auth_headers, mock_gemini)
    assert len(solutions) >= 4
    assert any(s["is_unconventional"] for s in solutions)

# TEST 2: Solutions belong to correct problem
async def test_solutions_belong_to_problem(client, auth_headers, mock_gemini):
    """All solutions should reference the correct problem_id"""
    sid, pid, solutions = await full_pipeline_to_solutions(client, auth_headers, mock_gemini)
    for s in solutions:
        assert s["problem_id"] == pid

# TEST 3: Session status is evaluation after solutions
async def test_session_evaluation_status(client, auth_headers, mock_gemini):
    """Session should be in evaluation status"""
    sid, _, _ = await full_pipeline_to_solutions(client, auth_headers, mock_gemini)
    session = await client.get(f"/api/v1/sessions/{sid}", headers=auth_headers)
    assert session.json()["status"] == "evaluation"

# TEST 4: Can approve a solution
async def test_approve_in_pipeline(client, auth_headers, mock_gemini):
    """Should be able to approve a solution from the pipeline"""
    _, _, solutions = await full_pipeline_to_solutions(client, auth_headers, mock_gemini)
    resp = await client.post(f"/api/v1/solutions/{solutions[0]['id']}/approve", headers=auth_headers)
    assert resp.json()["status"] == "approved"

# TEST 5: Tech stack preferences carried through
async def test_tech_prefs_in_pipeline(client, auth_headers, mock_gemini):
    """Session tech preferences should be accessible"""
    sid, _, _ = await full_pipeline_to_solutions(client, auth_headers, mock_gemini)
    session = await client.get(f"/api/v1/sessions/{sid}", headers=auth_headers)
    assert session.json()["tech_stack_preferences"] == ["React", "FastAPI"]

# TEST 6: Multiple problems can have independent solutions
async def test_independent_solution_sets(client, auth_headers, mock_gemini):
    """Two selected problems should have independent solution sets"""
    # First problem's solutions
    _, pid1, sols1 = await full_pipeline_to_solutions(client, auth_headers, mock_gemini, "Healthcare")
    # Second problem (new session)
    _, pid2, sols2 = await full_pipeline_to_solutions(client, auth_headers, mock_gemini, "Fintech")
    
    # Verify independence
    get1 = await client.get(f"/api/v1/problem-statements/{pid1}/solutions", headers=auth_headers)
    get2 = await client.get(f"/api/v1/problem-statements/{pid2}/solutions", headers=auth_headers)
    ids1 = {s["id"] for s in get1.json()}
    ids2 = {s["id"] for s in get2.json()}
    assert ids1.isdisjoint(ids2)  # no overlap
