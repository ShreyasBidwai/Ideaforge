import pytest
import json

# TEST 1: SSE formatter produces correct format
def test_sse_format():
    """SSE events should be properly formatted"""
    from app.core.streaming import format_sse_event
    event = format_sse_event("progress", {"status": "starting", "message": "Hello"})
    assert "event: progress" in event
    assert "data: " in event
    assert event.endswith("\n\n")

# TEST 2: SSE event data is valid JSON
def test_sse_data_is_json():
    """SSE data field should be parseable JSON"""
    from app.core.streaming import format_sse_event
    import json
    event = format_sse_event("data", {"key": "value"})
    data_line = [l for l in event.split("\n") if l.startswith("data: ")][0]
    json_str = data_line.replace("data: ", "")
    parsed = json.loads(json_str)
    assert parsed["key"] == "value"

# TEST 3: Stream endpoint returns correct content type
@pytest.mark.anyio
async def test_stream_content_type(client, auth_headers, mock_gemini):
    """Stream endpoint should return text/event-stream"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    response = await client.post(f"/api/v1/sessions/{session_id}/discover/stream", headers=auth_headers)
    assert response.headers.get("content-type", "").startswith("text/event-stream")

# TEST 4: Stream emits complete event with data
@pytest.mark.anyio
async def test_stream_emits_complete(client, auth_headers, mock_gemini):
    """Stream should end with a complete event containing pain points"""
    session = await client.post("/api/v1/sessions", json={
        "industry": "Fintech", "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "KYC Friction", "description": "KYC takes too long", "severity": 7, "affected_stakeholders": ["Users"], "evidence": "RBI data"}
    ]})
    response = await client.post(f"/api/v1/sessions/{session_id}/discover/stream", headers=auth_headers)
    body = response.text if hasattr(response, 'text') else (await response.aread()).decode()
    assert "complete" in body
