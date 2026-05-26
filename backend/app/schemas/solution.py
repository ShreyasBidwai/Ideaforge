from datetime import datetime
from uuid import UUID
from typing import Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

class SolutionCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    mechanism: str | None = None
    tech_stack: list[str] | None = None
    target_user: str | None = None
    revenue_model: str | None = None
    is_unconventional: bool = False

class EvaluationResponse(BaseModel):
    id: UUID
    solution_id: UUID
    rubric: dict | list | None = None
    scores: dict | list | None = None
    weighted_avg: float | None = None
    min_score: float | None = None
    attack_summary: str | None = None
    attack_survives: bool | None = None
    inconsistencies: dict | list | None = None
    inconsistency_count: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SolutionResponse(BaseModel):
    id: UUID
    problem_id: UUID
    title: str
    description: str
    mechanism: str | None = None
    tech_stack: list[str] | None = None
    target_user: str | None = None
    revenue_model: str | None = None
    is_unconventional: bool
    status: str
    created_at: datetime
    updated_at: datetime
    evaluation: EvaluationResponse | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_evaluation_context(cls, data: Any) -> Any:
        if hasattr(data, "__dict__"):
            if "evaluation" not in data.__dict__:
                object.__setattr__(data, "evaluation", None)
        elif isinstance(data, dict):
            if "evaluation" not in data:
                data["evaluation"] = None
        return data

class SolutionListResponse(BaseModel):
    items: list[SolutionResponse]
    total: int

class SolutionStatusUpdate(BaseModel):
    status: str

class SolutionUpdate(BaseModel):
    tech_stack: list[str] | None = None
    title: str | None = None
    description: str | None = None
    mechanism: str | None = None
    target_user: str | None = None
    revenue_model: str | None = None

