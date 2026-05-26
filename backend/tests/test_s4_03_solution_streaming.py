import pytest
import json

MOCK_SOLUTIONS = {"solutions": [
    {"title": "Sol 1", "description": "D", "mechanism": "M unique 1", "tech_stack": ["React"],
     "target_user": "Users", "revenue_model": "SaaS", "is_unconventional": False},
    {"title": "Sol 2", "description": "D", "mechanism": "M unique 2", "tech_stack": ["Vue"],
     "target_user": "Users", "revenue_model": "Marketplace", "is_unconventional": False},
    {"title": "Sol 3", "description": "D", "mechanism": "M unique 3", "tech_stack": ["Angular"],
     "target_user": "Users", "revenue_model": "API", "is_unconventional": True},
]}

async def setup_selected_problem(client, auth_headers, mock_gemini):
    """Helper: create session → discover → generate problems → select"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India", "maturity_level": "poc"
    }, headers=auth_headers)
    sid = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "P", "description": "D", "severity": 5, "affected_stakeholders": ["U"], "evidence": "E"}
    ]})
    await client.post(f"/api/v1/sessions/{sid}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "T", "description": "D", "target_user": "U", "core_pain": "P", "market_context": "M",
         "severity": 3, "feasibility": 3, "market_size": 3, "uniqueness": 3}
    ]})
    problems = await client.post(f"/api/v1/sessions/{sid}/generate-problems", headers=auth_headers)
    pid = problems.json()[0]["id"]
    await client.post(f"/api/v1/problem-statements/{pid}/select", headers=auth_headers)
    return pid

# TEST 1: Stream returns correct content type
async def test_solution_stream_type(client, auth_headers, mock_gemini):
    pid = await setup_selected_problem(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(MOCK_SOLUTIONS)
    response = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions/stream", headers=auth_headers)
    assert response.headers.get("content-type", "").startswith("text/event-stream")

# TEST 2: Stream emits complete with solutions
async def test_solution_stream_complete(client, auth_headers, mock_gemini):
    pid = await setup_selected_problem(client, auth_headers, mock_gemini)
    mock_gemini.return_value = json.dumps(MOCK_SOLUTIONS)
    response = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions/stream", headers=auth_headers)
    body = response.text if hasattr(response, 'text') else (await response.aread()).decode()
    assert "complete" in body
    assert "Sol 1" in body

# TEST 3: Stream fails without selected problem
async def test_solution_stream_requires_selected(client, auth_headers, mock_gemini):
    session = await client.post("/api/v1/sessions", json={"industry": "Gaming", "location": "India"}, headers=auth_headers)
    sid = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "P", "description": "D", "severity": 5, "affected_stakeholders": ["U"], "evidence": "E"}
    ]})
    await client.post(f"/api/v1/sessions/{sid}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "T", "description": "D", "target_user": "U", "core_pain": "P", "market_context": "M",
         "severity": 3, "feasibility": 3, "market_size": 3, "uniqueness": 3}
    ]})
    problems = await client.post(f"/api/v1/sessions/{sid}/generate-problems", headers=auth_headers)
    pid = problems.json()[0]["id"]
    # NOT selecting
    response = await client.post(f"/api/v1/problem-statements/{pid}/generate-solutions/stream", headers=auth_headers)
    assert response.status_code in [400, 422]
