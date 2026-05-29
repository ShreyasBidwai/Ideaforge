import uuid
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Session(Base):
    __tablename__ = "sessions"

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
    industry = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    guidance = Column(Text, nullable=True)
    pain_points = Column(JSON, nullable=True)
    maturity_level = Column(String(50), default="mvp", nullable=False)
    tech_stack_preferences = Column(JSON, nullable=True)
    status = Column(String(50), default="discovery", nullable=False)
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
    user = relationship("User", back_populates="sessions")
    problem_statements = relationship(
        "ProblemStatement",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    @property
    def maturity_config(self):
        from app.core.maturity import get_maturity_config, MaturityLevel
        return get_maturity_config(MaturityLevel(self.maturity_level))
