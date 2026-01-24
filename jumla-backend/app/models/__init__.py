"""
app/models/__init__.py
SQLAlchemy base configuration and imports
"""
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import MetaData
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional


# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models"""
    metadata = metadata
    
    # Common fields for most models
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# Import all models for Alembic auto-detection
from .organization import Organization
from .user import User
from .lead import Lead
from .property import Property
from .conversation import Conversation
from .buyer import Buyer
from .offer import Offer
from .lead_score import LeadScore
from .followup_log import FollowupLog
from .audit_log import AuditLog

__all__ = [
    "Base",
    "Organization",
    "User",
    "Lead",
    "Property",
    "Conversation",
    "Buyer",
    "Offer",
    "LeadScore",
    "FollowupLog",
    "AuditLog",
]