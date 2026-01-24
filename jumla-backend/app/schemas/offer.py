# ========================================
# app/schemas/offer.py
# ========================================
"""
Pydantic schemas for offers
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OfferStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OfferStrategy(str, Enum):
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"


class OfferCreate(BaseModel):
    """Offer creation schema"""
    lead_id: UUID4
    property_id: Optional[UUID4] = None
    buyer_id: Optional[UUID4] = None
    strategy: Optional[OfferStrategy] = OfferStrategy.STANDARD
    offer_type: Optional[str] = "cash"
    notes: Optional[str] = None


class OfferUpdate(BaseModel):
    """Offer update schema"""
    status: Optional[OfferStatus] = None
    buyer_id: Optional[UUID4] = None
    notes: Optional[str] = None


class OfferApproveRequest(BaseModel):
    """Offer approval request"""
    notes: Optional[str] = None


class OfferResponse(BaseModel):
    """Offer response schema"""
    id: UUID4
    lead_id: UUID4
    property_id: Optional[UUID4]
    buyer_id: Optional[UUID4]
    offer_amount: Decimal
    offer_type: str
    calculation_data: Dict[str, Any]
    status: str
    approved_by: Optional[UUID4]
    approved_at: Optional[datetime]
    sent_at: Optional[datetime]
    expires_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class OfferListResponse(BaseModel):
    """Paginated offer list"""
    items: List[OfferResponse]
    total: int
    skip: int
    limit: int