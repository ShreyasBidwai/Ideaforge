from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class CompetitorAnalysisResponse(BaseModel):
    id: UUID
    solution_id: UUID
    status: str
    competitors: list[dict] | None = None
    market_summary: str | None = None
    differentiation: str | None = None
    sources: list[dict] | None = None
    researched_at: datetime | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
