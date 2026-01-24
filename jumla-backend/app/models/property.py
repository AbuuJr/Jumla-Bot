"""
app/models/property.py
Property SQLAlchemy models
"""
from sqlalchemy import String, ForeignKey, JSON, Text, Integer, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from enum import Enum
from decimal import Decimal

from . import Base


class LeadStage(str, Enum):
    """Lead stage enumeration"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    OFFER_MADE = "offer_made"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Temperature(str, Enum):
    """Lead temperature enumeration"""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class Property(Base):
    """Property model - associated with lead"""
    __tablename__ = "properties"
    
    lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    address_full: Mapped[Optional[str]] = mapped_column(Text)
    address_street: Mapped[Optional[str]] = mapped_column(String(255))
    address_city: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    address_state: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    address_zip: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    property_type: Mapped[Optional[str]] = mapped_column(String(100))
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 1))
    sqft: Mapped[Optional[int]] = mapped_column(Integer)
    lot_size: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    condition: Mapped[Optional[str]] = mapped_column(String(50))
    estimated_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    estimated_arv: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    estimated_repair_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    zoning: Mapped[Optional[str]] = mapped_column(String(100))
    tax_assessed_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    last_sale_date: Mapped[Optional[date]] = mapped_column(Date)
    last_sale_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(
    "metadata",  # actual DB column name
    JSON,
    default=dict
    )

    
    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="properties")
    offers: Mapped[List["Offer"]] = relationship(back_populates="property")
    
    def __repr__(self) -> str:
        return f"<Property {self.address_full or 'Unknown Address'}>"