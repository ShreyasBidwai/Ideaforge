import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

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
    doc_type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="draft", nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="documents")
