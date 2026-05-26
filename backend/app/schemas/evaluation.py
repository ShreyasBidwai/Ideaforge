from datetime import datetime
from uuid import UUID
from typing import Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

class RubricCriterion(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    weight: float = Field(..., ge=0.5, le=5.0)
    scale: dict[str, str]

    @field_validator("scale")
    @classmethod
    def validate_scale_keys(cls, v: dict[str, str]) -> dict[str, str]:
        required_keys = {"1", "3", "5"}
        if set(v.keys()) != required_keys:
            raise ValueError("Scale must define concrete anchors for exactly scores 1, 3, and 5")
        return v

class Disqualifier(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)

class RubricSchema(BaseModel):
    criteria: list[RubricCriterion] = Field(..., min_length=3, max_length=6)
    disqualifiers: list[Disqualifier] = Field(..., min_length=1, max_length=5)

class RubricResponse(BaseModel):
    rubric: RubricSchema
    is_locked: bool
    problem_id: UUID

    model_config = ConfigDict(from_attributes=True)

class EvaluationResponse(BaseModel):
    id: UUID
    solution_id: UUID
    rubric: RubricSchema | dict
    scores: dict | None = None
    weighted_avg: float | None = None
    min_score: float | None = None
    attack_summary: str | None = None
    attack_survives: bool | None = None
    inconsistencies: dict | None = None
    inconsistency_count: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
