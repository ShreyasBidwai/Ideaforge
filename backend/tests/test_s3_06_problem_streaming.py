import pytest
import json

# TEST 1: Stream endpoint returns SSE content type
async def test_problem_stream_content_type(client, auth_headers, mock_gemini):
    """Stream endpoint should return text/event-stream"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India"
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
    response = await client.post(f"/api/v1/sessions/{session_id}/generate-problems/stream", headers=auth_headers)
    assert response.headers.get("content-type", "").startswith("text/event-stream")

# TEST 2: Stream emits complete event with problem statements
async def test_problem_stream_complete(client, auth_headers, mock_gemini):
    """Stream should end with complete event containing problem statements"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Fintech", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": "KYC Solution", "description": "Streamline KYC", "target_user": "Banks",
         "core_pain": "Slow KYC", "market_context": "Indian banking", "severity": 4, "feasibility": 4, "market_size": 5, "uniqueness": 3}
    ]})
    response = await client.post(f"/api/v1/sessions/{session_id}/generate-problems/stream", headers=auth_headers)
    body = response.text if hasattr(response, 'text') else (await response.aread()).decode()
    assert "complete" in body
    assert "KYC Solution" in body

# TEST 3: Stream requires pain points to exist
async def test_problem_stream_requires_pain_points(client, auth_headers):
    """Stream should fail if no pain points discovered yet"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Gaming", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    response = await client.post(f"/api/v1/sessions/{session_id}/generate-problems/stream", headers=auth_headers)
    assert response.status_code in [400, 422]
