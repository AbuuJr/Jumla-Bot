"""
app/models/lead.py
Lead SQLAlchemy model with nullable contact fields for chat leads
"""
from sqlalchemy import String, ForeignKey, text, JSON, ARRAY, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Dict, Any
from uuid import UUID

from enum import Enum

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


class Lead(Base):
    """
    Lead model - represents potential seller
    
    Contact fields (phone, email, name) are NULLABLE to support:
    1. Chat-initiated leads (contact info extracted later by AI)
    2. Partial lead data from various sources
    
    At least ONE contact method should eventually be provided for follow-up.
    """
    __tablename__ = "leads"
    
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Contact Information - ALL NULLABLE for chat leads
    phone: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Lead Metadata
    source: Mapped[str] = mapped_column(String(100), default="web_form")
    stage: Mapped[str] = mapped_column(String(50), default=LeadStage.NEW, index=True)
    temperature: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    
    # Data Storage
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    enriched_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    tags: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default=text("'{}'")
    )    
    # Assignment
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), 
        index=True
    )
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="leads")
    assigned_agent: Mapped[Optional["User"]] = relationship(
        back_populates="assigned_leads", 
        foreign_keys=[assigned_to]
    )
    properties: Mapped[List["Property"]] = relationship(
        back_populates="lead", 
        cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        back_populates="lead", 
        cascade="all, delete-orphan"
    )
    offers: Mapped[List["Offer"]] = relationship(
        back_populates="lead", 
        cascade="all, delete-orphan"
    )
    score: Mapped[Optional["LeadScore"]] = relationship(
        back_populates="lead", 
        uselist=False
    )
    followup_logs: Mapped[List["FollowupLog"]] = relationship(
        back_populates="lead", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        identifier = self.name or self.email or self.phone or f"Lead-{self.id}"
        return f"<Lead {identifier} ({self.stage})>"
    
    @property
    def display_name(self) -> str:
        """Get best available display name for the lead"""
        return self.name or self.email or self.phone or f"Anonymous Lead"
    
    @property
    def has_contact_info(self) -> bool:
        """Check if lead has at least one contact method"""
        return bool(self.phone or self.email)