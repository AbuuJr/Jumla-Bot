"""
# app/models/followup_log.py
"""
from sqlalchemy import String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from . import Base

class FollowupStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FollowupLog(Base):
    """Followup log model - tracks scheduled followups"""
    __tablename__ = "followup_logs"
    
    lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default=FollowupStatus.PENDING, index=True)
    result: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="followup_logs")

