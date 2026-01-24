"""
app/schemas/buyer.py
Pydantic schemas for buyers
"""
from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


class BuyerCreate(BaseModel):
    """Buyer creation schema"""
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = Field(default_factory=dict)
    preferred_markets: Optional[List[str]] = None
    min_deal_size: Optional[Decimal] = None
    max_deal_size: Optional[Decimal] = None
    notes: Optional[str] = None


class BuyerUpdate(BaseModel):
    """Buyer update schema"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    preferred_markets: Optional[List[str]] = None
    min_deal_size: Optional[Decimal] = None
    max_deal_size: Optional[Decimal] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class BuyerResponse(BaseModel):
    """Buyer response schema"""
    id: UUID4
    organization_id: UUID4
    name: str
    email: Optional[str]
    phone: Optional[str]
    criteria: Dict[str, Any]
    preferred_markets: Optional[List[str]]
    min_deal_size: Optional[Decimal]
    max_deal_size: Optional[Decimal]
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BuyerListResponse(BaseModel):
    """Paginated buyer list"""
    items: List[BuyerResponse]
    total: int
    skip: int
    limit: int