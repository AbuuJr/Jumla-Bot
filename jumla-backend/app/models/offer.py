"""
# app/models/offer.py
"""
from sqlalchemy import String, ForeignKey, JSON, Text, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum

from . import Base

class OfferStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Offer(Base):
    """Offer model - represents cash offers to sellers"""
    __tablename__ = "offers"
    
    lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("properties.id", ondelete="SET NULL"), index=True)
    buyer_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("buyers.id", ondelete="SET NULL"), index=True)
    offer_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    offer_type: Mapped[str] = mapped_column(String(50), default="cash")
    calculation_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default=OfferStatus.PENDING, index=True)
    approved_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="offers")
    property: Mapped[Optional["Property"]] = relationship(back_populates="offers")
    buyer: Mapped[Optional["Buyer"]] = relationship(back_populates="offers")
    approver: Mapped[Optional["User"]] = relationship(back_populates="approved_offers", foreign_keys=[approved_by])



