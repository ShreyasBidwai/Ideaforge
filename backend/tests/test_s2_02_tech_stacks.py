import pytest

# TEST 1: Registry contains all major categories
def test_registry_categories():
    """Registry should have frontend, backend, database, infrastructure, ai_ml"""
    from app.core.tech_stacks import TECH_STACK_REGISTRY
    assert "frontend" in TECH_STACK_REGISTRY
    assert "backend" in TECH_STACK_REGISTRY
    assert "database" in TECH_STACK_REGISTRY
    assert "infrastructure" in TECH_STACK_REGISTRY
    assert "ai_ml" in TECH_STACK_REGISTRY

# TEST 2: Each category has subcategories with items
def test_registry_has_items():
    """Each category should have at least one subcategory with at least one item"""
    from app.core.tech_stacks import TECH_STACK_REGISTRY
    for category, subcats in TECH_STACK_REGISTRY.items():
        assert len(subcats) > 0, f"{category} has no subcategories"
        for subcat, items in subcats.items():
            assert len(items) > 0, f"{category}.{subcat} has no items"

# TEST 3: GET /tech-stacks returns full registry
@pytest.mark.anyio
async def test_get_full_registry(client, auth_headers):
    """GET /api/v1/tech-stacks should return the complete registry"""
    response = await client.get("/api/v1/tech-stacks", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "frontend" in data
    assert "backend" in data

# TEST 4: Search finds matching technologies
@pytest.mark.anyio
async def test_search_tech_stacks(client, auth_headers):
    """Search should return matching technologies across categories"""
    response = await client.get("/api/v1/tech-stacks/search?q=react", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    names = [item["name"].lower() for item in data]
    assert any("react" in name for name in names)

# TEST 5: Search is case-insensitive
@pytest.mark.anyio
async def test_search_case_insensitive(client, auth_headers):
    """Search should be case-insensitive"""
    r1 = await client.get("/api/v1/tech-stacks/search?q=PYTHON", headers=auth_headers)
    r2 = await client.get("/api/v1/tech-stacks/search?q=python", headers=auth_headers)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert len(r1.json()) == len(r2.json())

# TEST 6: Search with no match returns empty
@pytest.mark.anyio
async def test_search_no_match(client, auth_headers):
    """Search with gibberish should return empty array"""
    response = await client.get("/api/v1/tech-stacks/search?q=xyznonexistent", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0

# TEST 7: Categories endpoint returns structure
@pytest.mark.anyio
async def test_get_categories(client, auth_headers):
    """GET /api/v1/tech-stacks/categories should return category/subcategory names"""
    response = await client.get("/api/v1/tech-stacks/categories", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict) or isinstance(data, list)
