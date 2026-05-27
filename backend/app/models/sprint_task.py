import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SprintTask(Base):
    __tablename__ = "sprint_tasks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    sprint_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sprints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_number = Column(Integer, nullable=False)
    name = Column(String(500), nullable=False)
    prompt = Column(Text, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    test_command = Column(String(500), nullable=True)
    test_count = Column(Integer, default=0, nullable=False)
    tests_passed = Column(Integer, default=0, nullable=False)
    tests_failed = Column(Integer, default=0, nullable=False)
    claude_output = Column(Text, nullable=True)
    error_output = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    rate_limit_reset_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    sprint = relationship("Sprint", back_populates="tasks")
