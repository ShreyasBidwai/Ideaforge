import pytest

# TEST 1: Create session successfully
@pytest.mark.anyio
async def test_create_session(client, auth_headers):
    """POST /sessions with valid data should create session"""
    response = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare",
        "location": "Mumbai, India",
        "maturity_level": "mvp"
    }, headers=auth_headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["industry"] == "Healthcare"
    assert data["location"] == "Mumbai, India"
    assert data["maturity_level"] == "mvp"
    assert data["status"] == "discovery"

# TEST 2: Create session with tech stack preferences
@pytest.mark.anyio
async def test_create_session_with_tech_stack(client, auth_headers):
    """Session should store tech stack preferences"""
    response = await client.post("/api/v1/sessions", json={
        "industry": "Fintech",
        "location": "Bangalore, India",
        "maturity_level": "production",
        "tech_stack_preferences": ["React", "FastAPI", "PostgreSQL"]
    }, headers=auth_headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["tech_stack_preferences"] == ["React", "FastAPI", "PostgreSQL"]

# TEST 3: Create session defaults to MVP
@pytest.mark.anyio
async def test_create_session_default_mvp(client, auth_headers):
    """Session without maturity_level should default to mvp"""
    response = await client.post("/api/v1/sessions", json={
        "industry": "EdTech",
        "location": "Delhi, India"
    }, headers=auth_headers)
    assert response.status_code in [200, 201]
    assert response.json()["maturity_level"] == "mvp"

# TEST 4: List sessions with pagination
@pytest.mark.anyio
async def test_list_sessions(client, auth_headers):
    """GET /sessions should return user's sessions paginated"""
    # Create 3 sessions
    for industry in ["Healthcare", "Fintech", "EdTech"]:
        await client.post("/api/v1/sessions", json={
            "industry": industry, "location": "India"
        }, headers=auth_headers)
    response = await client.get("/api/v1/sessions?page=1&per_page=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) <= 2
    assert "total" in data

# TEST 5: Get session by ID
@pytest.mark.anyio
async def test_get_session_by_id(client, auth_headers):
    """GET /sessions/{id} should return the session"""
    create = await client.post("/api/v1/sessions", json={
        "industry": "Logistics", "location": "India"
    }, headers=auth_headers)
    session_id = create.json()["id"]
    response = await client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == session_id

# TEST 6: Get session returns 404 for non-existent
@pytest.mark.anyio
async def test_get_nonexistent_session(client, auth_headers):
    """GET /sessions/{id} with fake ID should return 404"""
    import uuid
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/sessions/{fake_id}", headers=auth_headers)
    assert response.status_code == 404

# TEST 7: Update session maturity level
@pytest.mark.anyio
async def test_update_session(client, auth_headers):
    """PATCH /sessions/{id} should update fields"""
    create = await client.post("/api/v1/sessions", json={
        "industry": "AgriTech", "location": "India"
    }, headers=auth_headers)
    session_id = create.json()["id"]
    response = await client.patch(f"/api/v1/sessions/{session_id}", json={
        "maturity_level": "production"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["maturity_level"] == "production"

# TEST 8: Delete session
@pytest.mark.anyio
async def test_delete_session(client, auth_headers):
    """DELETE /sessions/{id} should remove session"""
    create = await client.post("/api/v1/sessions", json={
        "industry": "Retail", "location": "India"
    }, headers=auth_headers)
    session_id = create.json()["id"]
    response = await client.delete(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert response.status_code in [200, 204]
    # Verify it's gone
    get_response = await client.get(f"/api/v1/sessions/{session_id}", headers=auth_headers)
    assert get_response.status_code == 404

# TEST 9: Cannot access another user's session
@pytest.mark.anyio
async def test_session_ownership(client, auth_headers, other_auth_headers):
    """User A should not access User B's session"""
    create = await client.post("/api/v1/sessions", json={
        "industry": "Gaming", "location": "India"
    }, headers=auth_headers)
    session_id = create.json()["id"]
    response = await client.get(f"/api/v1/sessions/{session_id}", headers=other_auth_headers)
    assert response.status_code == 403

# TEST 10: Session requires authentication
@pytest.mark.anyio
async def test_session_requires_auth(client):
    """POST /sessions without auth should return 401"""
    response = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India"
    })
    assert response.status_code in [401, 403]

# TEST 11: Sessions ordered by newest first
@pytest.mark.anyio
async def test_sessions_ordered_newest_first(client, auth_headers):
    """GET /sessions should return newest first"""
    await client.post("/api/v1/sessions", json={"industry": "First", "location": "India"}, headers=auth_headers)
    await client.post("/api/v1/sessions", json={"industry": "Second", "location": "India"}, headers=auth_headers)
    response = await client.get("/api/v1/sessions", headers=auth_headers)
    items = response.json()["items"]
    assert items[0]["industry"] == "Second"  # newest first
