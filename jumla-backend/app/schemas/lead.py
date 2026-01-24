"""
app/schemas/lead.py
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, UUID4, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from app.schemas.common import PaginationParams


class LeadStage(str, Enum):
    """Lead stage enumeration"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    OFFER_MADE = "offer_made"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Temperature(str, Enum):
    """Lead temperature"""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class LeadResponse(BaseModel):
    """Lead response schema"""
    id: UUID4
    organization_id: UUID4
    phone: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    source: str
    stage: str = "new"  
    temperature: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    enriched_data: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    assigned_to: Optional[UUID4] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }


class LeadCreate(BaseModel):
    """Lead creation schema - flexible for chat and manual entry"""
    phone: Optional[str] = Field(None, description="Phone number (optional for chat)")
    email: Optional[EmailStr] = Field(None, description="Email address")
    name: Optional[str] = Field(None, description="Contact name")
    source: str = Field(default="web_form", description="Lead source")
    raw_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    initial_message: Optional[str] = Field(None, description="First message from chat widget")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Normalize phone number with lenient validation"""
        if not v:
            return None
        
        # Remove all non-numeric characters
        cleaned = ''.join(filter(str.isdigit, v))
        
        if not cleaned:
            return None
        
        # For chat widget, accept partial numbers (will be completed later)
        if len(cleaned) < 10:
            return v  # Return as-is for now
        
        # Normalize to E.164 format for complete numbers
        if len(cleaned) == 10:
            # Assume US number
            return f"+1{cleaned}"
        elif len(cleaned) == 11 and cleaned[0] == '1':
            return f"+{cleaned}"
        else:
            return f"+{cleaned}"
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "phone": "+1234567890",
                    "email": "seller@example.com",
                    "name": "John Doe",
                    "source": "website"
                },
                {
                    "source": "chat",
                    "initial_message": "Hi, I want to sell my house"
                }
            ]
        }
    }


class LeadCreateResponse(BaseModel):
    """Response when creating a lead"""
    lead: LeadResponse
    conversation_id: Optional[str] = Field(None, description="Conversation ID if created via chat")
    
    model_config = {
        "from_attributes": True
    }


class LeadUpdate(BaseModel):
    """Lead update schema"""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    stage: Optional[LeadStage] = None
    temperature: Optional[Temperature] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[UUID4] = None
    enriched_data: Optional[Dict[str, Any]] = None


class LeadWithScore(LeadResponse):
    """Lead response with score"""
    score: Optional[float] = None


class LeadListFilter(PaginationParams):
    """Lead list filter parameters"""
    stage: Optional[LeadStage] = None
    temperature: Optional[Temperature] = None
    assigned_to: Optional[UUID4] = None
    source: Optional[str] = None
    search: Optional[str] = None