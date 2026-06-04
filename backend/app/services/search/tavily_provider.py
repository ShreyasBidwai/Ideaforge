import httpx
from app.services.search.base import SearchProvider, SearchResult
from app.core.config import settings

class TavilyProvider(SearchProvider):
    """Tavily search — AI-optimized results. Free tier: 1000 credits/month."""
    BASE_URL = "https://api.tavily.com/search"

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not settings.TAVILY_API_KEY:
            raise RuntimeError("TAVILY_API_KEY not configured")
        payload = {
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",   # basic = faster/cheaper; advanced costs more credits
            "include_answer": False,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.BASE_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=r.get("score"),
            )
            for r in data.get("results", [])
        ]
