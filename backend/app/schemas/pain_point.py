from pydantic import BaseModel, Field
from typing import List

class PainPointSchema(BaseModel):
    name: str = Field(..., description="Short title (5-10 words)")
    description: str = Field(..., description="Detailed description of the pain point (2-4 sentences)")
    severity: int = Field(..., ge=1, le=10, description="Severity score between 1 and 10")
    affected_stakeholders: List[str] = Field(..., description="Affected specific roles/entities")
    evidence: str = Field(..., description="Evidence of the pain point")

class PainPointResponse(BaseModel):
    pain_points: List[PainPointSchema]

class DiscoverRequest(BaseModel):
    pass
