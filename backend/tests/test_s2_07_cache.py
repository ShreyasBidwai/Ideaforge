import pytest

# TEST 1: Cache key generation is consistent
def test_cache_key_consistent():
    """Same input should always produce same cache key"""
    from app.core.cache import CacheService
    key1 = CacheService.make_pain_point_key("Healthcare", "Mumbai, India", "mvp")
    key2 = CacheService.make_pain_point_key("healthcare", "mumbai, india", "mvp")
    assert key1 == key2  # case-insensitive

# TEST 2: Cache key includes all parameters
def test_cache_key_includes_all_params():
    """Different maturity levels should produce different keys"""
    from app.core.cache import CacheService
    key1 = CacheService.make_pain_point_key("Healthcare", "India", "mvp")
    key2 = CacheService.make_pain_point_key("Healthcare", "India", "production")
    assert key1 != key2

# TEST 3: Cache key normalizes whitespace
def test_cache_key_normalizes():
    """Extra whitespace should not affect cache key"""
    from app.core.cache import CacheService
    key1 = CacheService.make_pain_point_key("Healthcare", "Mumbai, India", "mvp")
    key2 = CacheService.make_pain_point_key("  Healthcare  ", "  Mumbai,  India  ", "mvp")
    assert key1 == key2

# TEST 4: Cache set and get work (requires Redis running or mock)
@pytest.mark.anyio
async def test_cache_set_and_get(cache_service):
    """Set a value and get it back"""
    await cache_service.set("test_key", '{"data": "hello"}', ttl=60)
    result = await cache_service.get("test_key")
    assert result == '{"data": "hello"}'

# TEST 5: Cache returns None for missing key
@pytest.mark.anyio
async def test_cache_miss(cache_service):
    """Get on non-existent key returns None"""
    result = await cache_service.get("nonexistent_key_xyz")
    assert result is None

# TEST 6: Cache delete works
@pytest.mark.anyio
async def test_cache_delete(cache_service):
    """Delete should remove the key"""
    await cache_service.set("delete_me", "value", ttl=60)
    await cache_service.delete("delete_me")
    result = await cache_service.get("delete_me")
    assert result is None

# TEST 7: Second discovery call uses cache (no AI call)
@pytest.mark.anyio
async def test_second_discovery_uses_cache(client, auth_headers, mock_gemini, cache_service):
    """Second identical discovery should not call AI again"""
    import json
    # Create two sessions with same industry/location/maturity
    s1 = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India", "maturity_level": "mvp"
    }, headers=auth_headers)
    s2 = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India", "maturity_level": "mvp"
    }, headers=auth_headers)
    
    mock_gemini.return_value = json.dumps({"pain_points": [
        {"name": "Test", "description": "Test", "severity": 5, "affected_stakeholders": ["Users"], "evidence": "Data"}
    ]})
    
    await client.post(f"/api/v1/sessions/{s1.json()['id']}/discover", headers=auth_headers)
    call_count_after_first = mock_gemini.call_count
    
    await client.post(f"/api/v1/sessions/{s2.json()['id']}/discover", headers=auth_headers)
    assert mock_gemini.call_count == call_count_after_first  # No additional AI call
