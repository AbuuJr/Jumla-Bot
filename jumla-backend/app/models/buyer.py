"""
# app/models/buyer.py
"""
from sqlalchemy import String, ForeignKey, JSON, Text, Numeric, Boolean, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal


from . import Base

class Buyer(Base):
    """Buyer model - represents potential buyers/investors"""
    __tablename__ = "buyers"
    
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    criteria: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    preferred_markets: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    min_deal_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    max_deal_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="buyers")
    offers: Mapped[List["Offer"]] = relationship(back_populates="buyer")


