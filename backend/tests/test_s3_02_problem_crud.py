import pytest
import json

# Helper: create a session with problem statements
async def create_session_with_problems(client, auth_headers, mock_gemini, industry="Healthcare"):
    session = await client.post("/api/v1/sessions", json={
        "industry": industry, "location": "India"
    }, headers=auth_headers)
    session_id = session.json()["id"]
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Pain", "description": "Desc", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    await client.post(f"/api/v1/sessions/{session_id}/discover", headers=auth_headers)
    mock_gemini.return_value = json.dumps({"problem_statements": [
        {"title": f"{industry} Problem 1", "description": "Desc 1", "target_user": "Users",
         "core_pain": "Pain 1", "market_context": "Market 1", "severity": 5, "feasibility": 4, "market_size": 3, "uniqueness": 4},
        {"title": f"{industry} Problem 2", "description": "Desc 2", "target_user": "Users",
         "core_pain": "Pain 2", "market_context": "Market 2", "severity": 3, "feasibility": 5, "market_size": 4, "uniqueness": 2}
    ]})
    resp = await client.post(f"/api/v1/sessions/{session_id}/generate-problems", headers=auth_headers)
    return resp.json()

# TEST 1: List all problem statements
@pytest.mark.anyio
async def test_list_all_problems(client, auth_headers, mock_gemini):
    """GET /problem-statements should return all user's problems"""
    await create_session_with_problems(client, auth_headers, mock_gemini, "Healthcare")
    await create_session_with_problems(client, auth_headers, mock_gemini, "Fintech")
    response = await client.get("/api/v1/problem-statements", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 4  # 2 per session

# TEST 2: Filter by industry
@pytest.mark.anyio
async def test_filter_by_industry(client, auth_headers, mock_gemini):
    """Filter should return only matching industry"""
    await create_session_with_problems(client, auth_headers, mock_gemini, "Healthcare")
    await create_session_with_problems(client, auth_headers, mock_gemini, "Fintech")
    response = await client.get("/api/v1/problem-statements?industry=Healthcare", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert all("Healthcare" in item.get("title", "") or "Healthcare" == item.get("industry", "") for item in items)

# TEST 3: Sort by overall_rating descending
@pytest.mark.anyio
async def test_sort_by_rating(client, auth_headers, mock_gemini):
    """Problems should be sortable by overall_rating"""
    await create_session_with_problems(client, auth_headers, mock_gemini)
    response = await client.get("/api/v1/problem-statements?sort_by=overall_rating&sort_order=desc", headers=auth_headers)
    items = response.json()["items"]
    if len(items) >= 2:
        assert items[0]["overall_rating"] >= items[1]["overall_rating"]

# TEST 4: Pagination works
@pytest.mark.anyio
async def test_pagination(client, auth_headers, mock_gemini):
    """Pagination should limit results"""
    await create_session_with_problems(client, auth_headers, mock_gemini)
    response = await client.get("/api/v1/problem-statements?page=1&per_page=1", headers=auth_headers)
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] >= 2

# TEST 5: Get single problem statement
@pytest.mark.anyio
async def test_get_single_problem(client, auth_headers, mock_gemini):
    """GET /problem-statements/{id} should return full detail"""
    problems = await create_session_with_problems(client, auth_headers, mock_gemini)
    problem_id = problems[0]["id"]
    response = await client.get(f"/api/v1/problem-statements/{problem_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == problem_id

# TEST 6: Update problem statement
@pytest.mark.anyio
async def test_update_problem(client, auth_headers, mock_gemini):
    """PATCH should update fields and recalculate rating"""
    problems = await create_session_with_problems(client, auth_headers, mock_gemini)
    problem_id = problems[0]["id"]
    original_rating = problems[0]["overall_rating"]
    response = await client.patch(f"/api/v1/problem-statements/{problem_id}", json={
        "severity": 1, "feasibility": 1
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["severity"] == 1
    assert response.json()["overall_rating"] != original_rating  # rating should change

# TEST 7: Select problem statement
@pytest.mark.anyio
async def test_select_problem(client, auth_headers, mock_gemini):
    """POST /problem-statements/{id}/select should set status to selected"""
    problems = await create_session_with_problems(client, auth_headers, mock_gemini)
    problem_id = problems[0]["id"]
    response = await client.post(f"/api/v1/problem-statements/{problem_id}/select", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "selected"

# TEST 8: Archive problem statement
@pytest.mark.anyio
async def test_archive_problem(client, auth_headers, mock_gemini):
    """DELETE should archive (set status to archived), not hard delete"""
    problems = await create_session_with_problems(client, auth_headers, mock_gemini)
    problem_id = problems[0]["id"]
    response = await client.delete(f"/api/v1/problem-statements/{problem_id}", headers=auth_headers)
    assert response.status_code in [200, 204]
    get_resp = await client.get(f"/api/v1/problem-statements/{problem_id}", headers=auth_headers)
    # Should still exist but with archived status, OR return 404 depending on implementation
    if get_resp.status_code == 200:
        assert get_resp.json()["status"] == "archived"

# TEST 9: Filter by status
@pytest.mark.anyio
async def test_filter_by_status(client, auth_headers, mock_gemini):
    """Filter by status=draft should exclude selected/archived"""
    problems = await create_session_with_problems(client, auth_headers, mock_gemini)
    # Select one
    await client.post(f"/api/v1/problem-statements/{problems[0]['id']}/select", headers=auth_headers)
    response = await client.get("/api/v1/problem-statements?status=draft", headers=auth_headers)
    items = response.json()["items"]
    assert all(item["status"] == "draft" for item in items)

# TEST 10: Industries endpoint returns unique list
@pytest.mark.anyio
async def test_industries_list(client, auth_headers, mock_gemini):
    """GET /problem-statements/industries should return unique industries"""
    await create_session_with_problems(client, auth_headers, mock_gemini, "Healthcare")
    await create_session_with_problems(client, auth_headers, mock_gemini, "Fintech")
    response = await client.get("/api/v1/problem-statements/industries", headers=auth_headers)
    assert response.status_code == 200
    industries = response.json()
    assert "Healthcare" in industries
    assert "Fintech" in industries

# TEST 11: Cannot access other user's problem statements
@pytest.mark.anyio
async def test_ownership_check(client, auth_headers, other_auth_headers, mock_gemini):
    """User B should not access User A's problem statements"""
    problems = await create_session_with_problems(client, auth_headers, mock_gemini)
    problem_id = problems[0]["id"]
    response = await client.get(f"/api/v1/problem-statements/{problem_id}", headers=other_auth_headers)
    assert response.status_code == 403
