import pytest

# ─── Registration Tests ───


# TEST 1: Successful registration
async def test_register_success(client):
    """POST /auth/register with valid data should return 201 and user data"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "StrongPass123!",
            "full_name": "Test User",
        },
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "hashed_password" not in data
    assert "password" not in data


# TEST 2: Duplicate email registration
async def test_register_duplicate_email(client):
    """Registering with an existing email should return 409"""
    user_data = {
        "email": "dupe@example.com",
        "password": "StrongPass123!",
        "full_name": "Dupe User",
    }
    await client.post("/api/v1/auth/register", json=user_data)
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 409


# TEST 3: Registration with weak password
async def test_register_weak_password(client):
    """Password under 8 characters should fail validation"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",
            "full_name": "Weak Pass",
        },
    )
    assert response.status_code == 422


# TEST 4: Registration with invalid email
async def test_register_invalid_email(client):
    """Invalid email format should fail validation"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "StrongPass123!",
            "full_name": "Bad Email",
        },
    )
    assert response.status_code == 422


# ─── Login Tests ───


# TEST 5: Successful login
async def test_login_success(client):
    """POST /auth/login with correct credentials should return tokens"""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "StrongPass123!",
            "full_name": "Login User",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


# TEST 6: Login with wrong password
async def test_login_wrong_password(client):
    """Wrong password should return 401"""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpw@example.com",
            "password": "StrongPass123!",
            "full_name": "Wrong PW",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401


# TEST 7: Login with non-existent email
async def test_login_nonexistent_email(client):
    """Non-existent email should return 401"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 401


# ─── Protected Endpoint Tests ───


# TEST 8: Access /me with valid token
async def test_me_with_valid_token(client):
    """GET /auth/me with valid access token should return user data"""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "password": "StrongPass123!",
            "full_name": "Me User",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "StrongPass123!"},
    )
    token = login.json()["access_token"]
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


# TEST 9: Access /me without token
async def test_me_without_token(client):
    """GET /auth/me without token should return 401"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in [401, 403]


# TEST 10: Access /me with invalid token
async def test_me_with_invalid_token(client):
    """GET /auth/me with garbage token should return 401"""
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401


# ─── Token Refresh Tests ───


# TEST 11: Refresh token returns new tokens
async def test_refresh_token_success(client):
    """POST /auth/refresh with valid refresh token should return new token pair"""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "StrongPass123!",
            "full_name": "Refresh User",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "StrongPass123!"},
    )
    refresh_token = login.json()["refresh_token"]
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


# TEST 12: Refresh with access token should fail
async def test_refresh_with_access_token(client):
    """Using access token as refresh token should fail"""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "badrefresh@example.com",
            "password": "StrongPass123!",
            "full_name": "Bad Refresh",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "badrefresh@example.com",
            "password": "StrongPass123!",
        },
    )
    access_token = login.json()["access_token"]
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": access_token}
    )
    assert response.status_code == 401


# ─── Security Tests ───


# TEST 13: Password is hashed in database (not plaintext)
def test_password_hashing():
    """hash_password should return a bcrypt hash, not plaintext"""
    from backend.app.core.security import hash_password, verify_password

    hashed = hash_password("MyPassword123!")
    assert hashed != "MyPassword123!"
    assert hashed.startswith("$2b$")
    assert verify_password("MyPassword123!", hashed) is True
    assert verify_password("WrongPassword", hashed) is False


# TEST 14: Response never contains password
async def test_no_password_in_response(client):
    """No endpoint should ever return password or hashed_password"""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nopw@example.com",
            "password": "StrongPass123!",
            "full_name": "No PW",
        },
    )
    body = resp.text
    assert "hashed_password" not in body
    assert "StrongPass123!" not in body
