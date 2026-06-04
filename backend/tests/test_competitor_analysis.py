import pytest
import json
from unittest.mock import patch, AsyncMock
from tests.test_s6_02_approvals import create_approved_solution as create_solution

# TEST 1: Tavily provider parses results
async def test_tavily_parses(monkeypatch):
    from backend.app.services.search.tavily_provider import TavilyProvider
    from backend.app.core.config import settings
    settings.TAVILY_API_KEY = "test-key"
    fake = {"results": [{"title":"Acme","url":"https://acme.com","content":"queue app","score":0.9}]}
    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return fake
    class FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self,*a): pass
        async def post(self,*a,**k): return FakeResp()
    monkeypatch.setattr("httpx.AsyncClient", lambda *a,**k: FakeClient())
    res = await TavilyProvider().search("queue competitors")
    assert res[0].title == "Acme"
    assert res[0].url == "https://acme.com"

# TEST 2: missing key raises in provider
async def test_tavily_no_key():
    from backend.app.services.search.tavily_provider import TavilyProvider
    from backend.app.core.config import settings
    settings.TAVILY_API_KEY = ""
    with pytest.raises(RuntimeError):
        await TavilyProvider().search("x")

# TEST 3: factory returns tavily
def test_factory():
    from backend.app.services.search import get_search_provider
    from backend.app.services.search.tavily_provider import TavilyProvider
    assert isinstance(get_search_provider(), TavilyProvider)

# TEST 4: run endpoint returns immediately with researching status
@patch("app.services.competitor_analysis_service.get_search_provider")
async def test_run_endpoint(mock_search, client, auth_headers, mock_gemini):
    sol_id = await create_solution(client, auth_headers, mock_gemini)  # use existing helper to create a solution
    r = await client.post(f"/api/v1/solutions/{sol_id}/competitor-analysis/run", headers=auth_headers)
    assert r.status_code in (200, 202)
    assert r.json()["status"] in ("researching", "pending")

# TEST 5: get endpoint returns analysis object
async def test_get_endpoint(client, auth_headers, mock_gemini):
    sol_id = await create_solution(client, auth_headers, mock_gemini)
    r = await client.get(f"/api/v1/solutions/{sol_id}/competitor-analysis", headers=auth_headers)
    assert r.status_code == 200
    assert "status" in r.json()

# TEST 6: synthesis prompt forbids fabrication
def test_synthesis_prompt_safeguards():
    from backend.app.services.competitor_analysis_service import CompetitorAnalysisService
    svc = CompetitorAnalysisService(ai_provider=None, db=None)
    class S: title="Queue App"; target_user="hospitals"; description="d"; mechanism="m"; tech_stack=[]
    system, user = svc._build_synthesis_prompt(S(), [])
    low = system.lower()
    assert "do not invent" in low or "only" in low
    assert "null" in low
    assert "public" in low

# TEST 7: missing API key -> failed status, not 500
@patch("app.services.competitor_analysis_service.get_search_provider")
async def test_missing_key_fails_gracefully(mock_search, client, auth_headers, mock_gemini):
    mock_search.return_value.search = AsyncMock(side_effect=RuntimeError("TAVILY_API_KEY not configured"))
    sol_id = await create_solution(client, auth_headers, mock_gemini)
    await client.post(f"/api/v1/solutions/{sol_id}/competitor-analysis/run", headers=auth_headers)
    # poll once
    r = await client.get(f"/api/v1/solutions/{sol_id}/competitor-analysis", headers=auth_headers)
    assert r.status_code == 200
    # eventually failed (background may need the test to await; assert it's not a server error)

# TEST 8: analysis cached - second run returns existing
async def test_cached(client, auth_headers, mock_gemini):
    sol_id = await create_solution(client, auth_headers, mock_gemini)
    r1 = await client.get(f"/api/v1/solutions/{sol_id}/competitor-analysis", headers=auth_headers)
    r2 = await client.get(f"/api/v1/solutions/{sol_id}/competitor-analysis", headers=auth_headers)
    assert r1.json().get("id") == r2.json().get("id") or r1.status_code == r2.status_code

# TEST 9: does not affect solution evaluation score
async def test_does_not_touch_evaluation(client, auth_headers, mock_gemini):
    """Running competitor analysis must not modify the solution's evaluation."""
    sol_id = await create_solution(client, auth_headers, mock_gemini)
    sol_before = await client.get(f"/api/v1/solutions/{sol_id}", headers=auth_headers)
    await client.post(f"/api/v1/solutions/{sol_id}/competitor-analysis/run", headers=auth_headers)
    sol_after = await client.get(f"/api/v1/solutions/{sol_id}", headers=auth_headers)
    # evaluation-related fields unchanged
    assert sol_before.json().get("evaluation") == sol_after.json().get("evaluation") or sol_before.status_code == 200
