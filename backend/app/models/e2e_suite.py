import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class E2ETest(Base):
    __tablename__ = "e2e_tests"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    framework = Column(String(50), nullable=False)  # "playwright" | "pytest-httpx"
    test_code = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    last_output = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship to project
    project = relationship("Project", back_populates="e2e_tests")
