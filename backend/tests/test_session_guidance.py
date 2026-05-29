import pytest
import json
from app.ai.prompts.pain_points import build_pain_point_prompt

# TEST 1: create session with guidance persists it
@pytest.mark.asyncio
async def test_create_with_guidance(client, auth_headers):
    r = await client.post("/api/v1/sessions", json={
        "industry": "Healthcare", "location": "India",
        "guidance": "keep the tech stack simple, internal admin tool"
    }, headers=auth_headers)
    assert r.status_code in (200, 201)
    assert "simple" in (r.json().get("guidance") or "").lower()

# TEST 2: guidance is optional
@pytest.mark.asyncio
async def test_create_without_guidance(client, auth_headers):
    r = await client.post("/api/v1/sessions", json={
        "industry": "Retail", "location": "USA"
    }, headers=auth_headers)
    assert r.status_code in (200, 201)
    assert r.json().get("guidance") in (None, "")

# TEST 3: guidance over 1000 chars rejected
@pytest.mark.asyncio
async def test_guidance_too_long(client, auth_headers):
    r = await client.post("/api/v1/sessions", json={
        "industry": "Finance", "location": "UK", "guidance": "x" * 1001
    }, headers=auth_headers)
    assert r.status_code in (400, 422)

# TEST 4: guidance injected into discovery prompt
def test_guidance_in_prompt():
    out = build_pain_point_prompt(industry="Healthcare", location="India",
                                  guidance="internal logging tool, simple stack")
    combined = (out if isinstance(out, str) else " ".join(out))
    assert "logging" in combined.lower()
    assert "guidance" in combined.lower()

# TEST 5: empty guidance does NOT add guidance block
def test_empty_guidance_no_block():
    out = build_pain_point_prompt(industry="Retail", location="USA", guidance="")
    combined = (out if isinstance(out, str) else " ".join(out))
    assert "USER GUIDANCE" not in combined
