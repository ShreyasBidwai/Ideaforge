from app.core.config import settings
from app.services.search.tavily_provider import TavilyProvider

def get_search_provider():
    """Factory — swap providers here. Default Tavily."""
    provider = getattr(settings, "SEARCH_PROVIDER", "tavily")
    if provider == "tavily":
        return TavilyProvider()
    raise ValueError(f"Unknown search provider: {provider}")
