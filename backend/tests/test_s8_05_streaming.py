import pytest
import json

# Helper to create an approved solution for API endpoint tests
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

# TEST 1: Doc generation stream returns SSE
@pytest.mark.anyio
async def test_doc_stream_content_type(client, auth_headers, mock_gemini):
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc content"
    response = await client.post(f"/api/v1/projects/{proj_id}/generate-docs/stream", headers=auth_headers)
    assert response.headers.get("content-type", "").startswith("text/event-stream")

# TEST 2: Doc stream emits complete event
@pytest.mark.anyio
async def test_doc_stream_complete(client, auth_headers, mock_gemini):
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    mock_gemini.return_value = "# Doc content"
    response = await client.post(f"/api/v1/projects/{proj_id}/generate-docs/stream", headers=auth_headers)
    body = response.text if hasattr(response, 'text') else (await response.aread()).decode()
    assert "complete" in body

# TEST 3: Build log stream endpoint exists
@pytest.mark.anyio
async def test_build_log_stream(client, auth_headers, mock_gemini):
    sol_id = await create_approved_solution(client, auth_headers, mock_gemini)
    project = await client.post(f"/api/v1/solutions/{sol_id}/create-project", headers=auth_headers)
    proj_id = project.json()["id"]
    response = await client.get(f"/api/v1/projects/{proj_id}/build/logs/stream", headers=auth_headers)
    assert response.headers.get("content-type", "").startswith("text/event-stream")
