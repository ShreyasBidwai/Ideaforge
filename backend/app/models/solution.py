import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Solution(Base):
    __tablename__ = "solutions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    problem_id = Column(
        UUID(as_uuid=True),
        ForeignKey("problem_statements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    mechanism = Column(Text, nullable=True)
    tech_stack = Column(JSON, nullable=True)
    target_user = Column(String(500), nullable=True)
    revenue_model = Column(String(500), nullable=True)
    is_unconventional = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="candidate", nullable=False)
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
    problem_statement = relationship("ProblemStatement", back_populates="solutions")
    evaluation = relationship(
        "Evaluation",
        back_populates="solution",
        uselist=False,
        cascade="all, delete-orphan",
    )
