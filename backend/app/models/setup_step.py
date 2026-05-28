import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SetupStep(Base):
    __tablename__ = "setup_steps"

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
    step_type = Column(String(50), nullable=False)   # enum: api_key, env_var, external_account, oauth_config, system_install, manual_action
    title = Column(String(500), nullable=False)      # e.g. "Add your Stripe secret key"
    description = Column(Text, nullable=True)        # what to do and where
    target_file = Column(String(500), nullable=True)  # e.g. ".env" if it's an env var
    env_key = Column(String(255), nullable=True)      # e.g. "STRIPE_SECRET_KEY"
    is_required = Column(Boolean, default=True, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)   # user marks done (or we detect for env vars)
    doc_url = Column(String(1000), nullable=True)     # link to where to get the key/account
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship to project
    project = relationship("Project", back_populates="setup_steps")
