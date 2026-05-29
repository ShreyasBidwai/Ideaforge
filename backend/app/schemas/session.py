from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any, List, Optional
from app.core.maturity import MaturityLevel, MaturityConfig

class MaturityLevelInfo(BaseModel):
    level: MaturityLevel
    label: str
    description: str
    pain_point_count: tuple[int, int]
    problem_statement_count: int
    solution_candidate_count: int
    evaluation_steps: List[str]

class SessionCreate(BaseModel):
    industry: str
    location: str
    maturity_level: MaturityLevel = MaturityLevel.MVP
    tech_stack_preferences: Optional[List[str]] = None
    guidance: Optional[str] = None

    @field_validator("guidance", mode="before")
    @classmethod
    def validate_guidance(cls, v):
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("guidance must be a string")
        v = v.strip()
        if len(v) > 1000:
            raise ValueError("guidance cannot exceed 1000 characters")
        return v

class SessionUpdate(BaseModel):
    maturity_level: Optional[MaturityLevel] = None
    tech_stack_preferences: Optional[List[str]] = None
    status: Optional[str] = None

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    industry: str
    location: str
    guidance: Optional[str] = None
    pain_points: Optional[List[Any]] = None
    maturity_level: MaturityLevel
    tech_stack_preferences: Optional[List[str]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    maturity_config: MaturityConfig

    model_config = ConfigDict(from_attributes=True)

class SessionListResponse(BaseModel):
    items: List[SessionResponse]
    total: int
    page: int
    per_page: int
