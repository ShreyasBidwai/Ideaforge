import pytest
import json

# TEST 1: Stats endpoint returns correct structure
async def test_dashboard_stats_structure(client, auth_headers):
    """GET /dashboard/stats should return all 4 counts"""
    response = await client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_sessions" in data
    assert "total_problems" in data
    assert "solutions_evaluated" in data
    assert "solutions_approved" in data

# TEST 2: Stats are zero for new user
async def test_dashboard_stats_zero(client, auth_headers):
    """New user should have all zero stats"""
    response = await client.get("/api/v1/dashboard/stats", headers=auth_headers)
    data = response.json()
    assert data["total_sessions"] == 0
    assert data["total_problems"] == 0

# TEST 3: Stats update after creating data
async def test_dashboard_stats_after_data(client, auth_headers, mock_gemini):
    """Stats should reflect created sessions and problems"""
    # Create a session
    await client.post("/api/v1/sessions", json={"industry": "Healthcare", "location": "India"}, headers=auth_headers)
    await client.post("/api/v1/sessions", json={"industry": "Fintech", "location": "India"}, headers=auth_headers)
    response = await client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert response.json()["total_sessions"] == 2

# TEST 4: Stats require authentication
async def test_dashboard_stats_auth(client):
    """Stats endpoint should require auth"""
    response = await client.get("/api/v1/dashboard/stats")
    assert response.status_code in [401, 403]
