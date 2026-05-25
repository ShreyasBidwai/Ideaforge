import uuid
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    solution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("solutions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    rubric = Column(JSON, nullable=False)
    scores = Column(JSON, nullable=True)
    weighted_avg = Column(Float, nullable=True)
    min_score = Column(Float, nullable=True)
    attack_summary = Column(Text, nullable=True)
    attack_survives = Column(Boolean, nullable=True)
    inconsistencies = Column(JSON, nullable=True)
    inconsistency_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    solution = relationship("Solution", back_populates="evaluation")
