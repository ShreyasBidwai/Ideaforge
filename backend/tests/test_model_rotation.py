import pytest
from datetime import datetime, timedelta

# TEST 1: Rotator returns first available model
def test_returns_first_model():
    from backend.app.ai.provider import ModelRotator
    rotator = ModelRotator(["model-a", "model-b", "model-c"])
    assert rotator.get_current_model() == "model-a"

# TEST 2: Skips exhausted model
def test_skips_exhausted():
    from backend.app.ai.provider import ModelRotator
    rotator = ModelRotator(["model-a", "model-b", "model-c"])
    rotator.mark_exhausted("model-a")
    assert rotator.get_current_model() == "model-b"

# TEST 3: Rotates through all
def test_rotates_through():
    from backend.app.ai.provider import ModelRotator
    rotator = ModelRotator(["model-a", "model-b", "model-c"])
    rotator.mark_exhausted("model-a")
    rotator.mark_exhausted("model-b")
    assert rotator.get_current_model() == "model-c"

# TEST 4: All exhausted raises error
def test_all_exhausted_raises():
    from backend.app.ai.provider import ModelRotator
    rotator = ModelRotator(["model-a", "model-b"])
    rotator.mark_exhausted("model-a")
    rotator.mark_exhausted("model-b")
    with pytest.raises(Exception, match="exhausted"):
        rotator.get_current_model()

# TEST 5: Resets after 24 hours
def test_resets_after_24h():
    from backend.app.ai.provider import ModelRotator
    rotator = ModelRotator(["model-a", "model-b"])
    rotator.exhausted["model-a"] = datetime.utcnow() - timedelta(hours=25)
    assert rotator.get_current_model() == "model-a"

# TEST 6: Status shows all models
def test_status():
    from backend.app.ai.provider import ModelRotator
    rotator = ModelRotator(["model-a", "model-b"])
    rotator.mark_exhausted("model-a")
    status = rotator.get_status()
    assert status["model-a"] == "exhausted"
    assert status["model-b"] == "available"

# TEST 7: AI status endpoint
@pytest.mark.anyio
async def test_ai_status_endpoint(client, auth_headers):
    response = await client.get("/api/v1/setup/ai-status", headers=auth_headers)
    assert response.status_code == 200
    assert "models" in response.json() or "status" in response.json()
