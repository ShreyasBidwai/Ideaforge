from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Any

class ProblemStatementCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    target_user: str | None = None
    core_pain: str | None = None
    market_context: str | None = None
    severity: float = Field(..., ge=1.0, le=5.0)
    feasibility: float = Field(..., ge=1.0, le=5.0)
    market_size: float = Field(..., ge=1.0, le=5.0)
    uniqueness: float = Field(..., ge=1.0, le=5.0)

class ProblemStatementUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: float | None = Field(None, ge=1.0, le=5.0)
    feasibility: float | None = Field(None, ge=1.0, le=5.0)
    market_size: float | None = Field(None, ge=1.0, le=5.0)
    uniqueness: float | None = Field(None, ge=1.0, le=5.0)
    status: str | None = None

class ProblemStatementResponse(BaseModel):
    id: UUID
    session_id: UUID
    title: str
    description: str
    target_user: str | None = None
    core_pain: str | None = None
    market_context: str | None = None
    severity: float
    feasibility: float
    market_size: float
    uniqueness: float
    overall_rating: float
    status: str
    created_at: datetime
    updated_at: datetime
    
    industry: str | None = None
    location: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_session_context(cls, data: Any) -> Any:
        # Pydantic may pass a dict or an ORM object
        if hasattr(data, "session") and data.session:
            session = data.session
            # We set the attribute on the ORM object dynamically so standard serialization can read it
            object.__setattr__(data, "industry", getattr(session, "industry", None))
            object.__setattr__(data, "location", getattr(session, "location", None))
        elif isinstance(data, dict):
            session = data.get("session")
            if session:
                if isinstance(session, dict):
                    data["industry"] = session.get("industry")
                    data["location"] = session.get("location")
                else:
                    data["industry"] = getattr(session, "industry", None)
                    data["location"] = getattr(session, "location", None)
        return data

class ProblemStatementListResponse(BaseModel):
    items: list[ProblemStatementResponse]
    total: int
    page: int
    per_page: int
