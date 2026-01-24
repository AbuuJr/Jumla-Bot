"""
# app/models/lead_score.py
"""
from sqlalchemy import ForeignKey, JSON, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from . import Base

class LeadScore(Base):
    """Lead score model - scoring metrics for prioritization"""
    __tablename__ = "lead_scores"
    
    lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, index=True)
    urgency_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    motivation_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    property_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    response_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    financial_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    factors: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="score")

