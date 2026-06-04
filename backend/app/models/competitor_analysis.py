import uuid
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class CompetitorAnalysis(Base):
    __tablename__ = "competitor_analyses"

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
        index=True,
    )
    status = Column(String(50), default="pending", nullable=False)   # pending, researching, completed, failed
    competitors = Column(JSON, nullable=True)      # list of {name, description, pricing, funding, strengths, weaknesses, url}
    market_summary = Column(Text, nullable=True)   # overall competitive landscape summary
    differentiation = Column(Text, nullable=True)  # how this solution differs / its gap in the market
    sources = Column(JSON, nullable=True)          # list of {title, url} actually used
    researched_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
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

    # Relationship
    solution = relationship("Solution", back_populates="competitor_analysis")
