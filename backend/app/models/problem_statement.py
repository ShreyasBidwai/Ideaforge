import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ProblemStatement(Base):
    __tablename__ = "problem_statements"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    target_user = Column(String(500), nullable=True)
    core_pain = Column(Text, nullable=True)
    market_context = Column(Text, nullable=True)
    severity = Column(Float, default=0.0, nullable=False)
    feasibility = Column(Float, default=0.0, nullable=False)
    market_size = Column(Float, default=0.0, nullable=False)
    uniqueness = Column(Float, default=0.0, nullable=False)
    overall_rating = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="draft", nullable=False)
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
    session = relationship("Session", back_populates="problem_statements")
    solutions = relationship(
        "Solution", back_populates="problem_statement", cascade="all, delete-orphan"
    )
