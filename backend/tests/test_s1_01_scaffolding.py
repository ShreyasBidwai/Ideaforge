# TEST 1: Health endpoint returns correct response
async def test_health_endpoint(client):
    """GET /api/v1/health should return status healthy and version"""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


# TEST 2: CORS headers are present
async def test_cors_headers(client):
    """OPTIONS request should return CORS headers"""
    response = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


# TEST 3: Config loads with defaults
def test_config_defaults():
    """Config should load with sensible defaults"""
    from backend.app.core.config import get_settings

    settings = get_settings()
    assert settings.APP_ENV == "development"
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert "localhost:5173" in str(settings.CORS_ORIGINS)


# TEST 4: Database engine creates without error
async def test_database_engine():
    """Async engine should be creatable from config"""
    from backend.app.core.database import engine

    assert engine is not None


# TEST 5: AI provider base class is abstract
def test_ai_provider_is_abstract():
    """AIProvider cannot be instantiated directly"""
    import pytest
    from backend.app.ai.provider import AIProvider

    with pytest.raises(TypeError):
        AIProvider()


# TEST 6: GeminiProvider instantiates with API key
def test_gemini_provider_init():
    """GeminiProvider should instantiate with an API key"""
    from backend.app.ai.provider import GeminiProvider

    provider = GeminiProvider(api_key="test-key")
    assert provider is not None
    assert provider.model_name == "gemini-2.5-flash"


# TEST 7: 404 on unknown routes
async def test_unknown_route_returns_404(client):
    """Unknown routes should return 404"""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404


# TEST 8: API router prefix is correct
async def test_api_v1_prefix(client):
    """All API routes should be under /api/v1"""
    response = await client.get("/health")  # without prefix
    assert response.status_code == 404
    response = await client.get("/api/v1/health")  # with prefix
    assert response.status_code == 200
