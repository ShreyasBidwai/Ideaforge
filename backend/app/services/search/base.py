from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class SearchResult:
    title: str
    url: str
    content: str          # snippet / extracted content
    score: float | None = None

class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        ...
