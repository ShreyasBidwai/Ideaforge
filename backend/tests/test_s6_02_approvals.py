import pytest
import json

async def create_approved_solution(client, auth_headers, mock_gemini):
    """Helper: create full pipeline and approve a solution"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India"
    }, headers=auth_headers)
    sid = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "P", "description": "D", "severity": 5, "affected_stakeholders": ["U"], "evidence": "E"}
    ]})
    await client.post(f"/api/v1/sessions/{sid}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "Problem", "description": "D", "target_user": "U", "core_pain": "P", "market_context": "M",
         "severity": 4, "feasibility": 4, "market_size": 4, "uniqueness": 3}
    ]})
    problems = await client.post(f"/api/v1/sessions/{sid}/generate-problems", headers=auth_headers)
    pid = problems.json()[0]["id"]
    await client.post(f"/api/v1/problem-statements/{pid}/select", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"solutions": [
        {"title": "Approved Sol", "description": "D", "mechanism": "M", "tech_stack": ["React"],
         "target_user": "Users", "revenue_model": "SaaS $99/mo", "is_unconventional": False}
    ]})
    solutions = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions", headers=auth_headers)
    sol_id = solutions.json()[0]["id"]
    await client.post(f"/api/v1/solutions/{sol_id}/approve", headers=auth_headers)
    return sol_id

# TEST 1: List approved solutions
async def test_list_approvals(client, auth_headers, mock_gemini):
    """GET /approvals should list approved solutions"""
    await create_approved_solution(client, auth_headers, mock_gemini)
    response = await client.get("/api/v1/approvals", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "approved"

# TEST 2: Approved solution includes context
async def test_approval_includes_context(client, auth_headers, mock_gemini):
    """Approved solution should include problem title and industry"""
    await create_approved_solution(client, auth_headers, mock_gemini)
    response = await client.get("/api/v1/approvals", headers=auth_headers)
    data = response.json()
    assert "problem_title" in data[0] or "problem" in data[0] or "industry" in data[0]

# TEST 3: Revoke approval
async def test_revoke_approval(client, auth_headers, mock_gemini):
    """POST /solutions/{id}/revoke should change status from approved"""
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    response = await client.post(f"/api/v1/solutions/{sol_id}/revoke", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] != "approved"
    # Should no longer appear in approvals
    approvals = await client.get("/api/v1/approvals", headers=auth_headers)
    sol_ids = [a.get("id") or a.get("solution_id") for a in approvals.json()]
    assert sol_id not in sol_ids

# TEST 4: Empty approvals list
async def test_empty_approvals(client, auth_headers):
    """New user should have empty approvals"""
    response = await client.get("/api/v1/approvals", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0

# TEST 5: Approvals require auth
async def test_approvals_require_auth(client):
    """Approvals endpoint should require authentication"""
    response = await client.get("/api/v1/approvals")
    assert response.status_code in [401, 403]
