import uuid
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    solution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("solutions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    industry = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    maturity_level = Column(String(50), nullable=False)
    tech_stack = Column(JSON, nullable=False)
    status = Column(String(50), default="doc_generation", nullable=False)
    project_dir = Column(String(1000), nullable=True)
    pause_on_failure = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    solution = relationship("Solution", back_populates="project")
    documents = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    sprints = relationship(
        "Sprint",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    setup_steps = relationship(
        "SetupStep",
        back_populates="project",
        cascade="all, delete-orphan",
    )

