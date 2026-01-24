"""
app/schemas/conversation.py
Pydantic schemas for conversations
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ConversationChannel(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    VOICE = "voice"


class ConversationDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ConversationCreate(BaseModel):
    """Conversation creation schema"""
    lead_id: UUID4
    channel: ConversationChannel
    direction: ConversationDirection
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    message_body: Optional[str] = None
    status: Optional[str] = "delivered"
    external_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    """Full conversation record"""
    id: UUID4
    lead_id: UUID4
    channel: str
    direction: str
    message_body: str
    status: str
    extracted_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class ConversationListResponse(BaseModel):
    """Paginated conversation list"""
    items: List[ConversationResponse]
    total: int
    skip: int
    limit: int


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation"""
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    attachments: Optional[List[str]] = Field(None, description="List of attachment URLs/IDs")



class MessageResponse(BaseModel):
    """Single message in a conversation"""
    id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    attachments: Optional[List[str]] = None



class SendMessageResponse(BaseModel):
    """Response after sending a message - includes user message and bot response"""
    user_message: MessageResponse
    bot_message: MessageResponse
    extracted_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted seller/property info from the message"
    )





