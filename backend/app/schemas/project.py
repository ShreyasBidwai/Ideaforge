from datetime import datetime
from uuid import UUID
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    id: UUID
    project_id: UUID
    doc_type: str
    title: str
    content: str
    version: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    solution_id: UUID
    name: str
    description: str | None = None
    industry: str
    location: str
    maturity_level: str
    tech_stack: list | dict | None = None
    status: str
    project_dir: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
