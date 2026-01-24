"""
# app/models/conversation.py
"""
from sqlalchemy import String, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any
from uuid import UUID
from enum import Enum

from . import Base

class ConversationChannel(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    VOICE = "voice"


class ConversationDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Conversation(Base):
    """Conversation model - tracks all messages with leads"""
    __tablename__ = "conversations"
    
    lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    from_number: Mapped[Optional[str]] = mapped_column(String(50))
    to_number: Mapped[Optional[str]] = mapped_column(String(50))
    message_body: Mapped[Optional[str]] = mapped_column(Text)
    extracted_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    llm_response: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="delivered")
    external_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(
    "metadata",  # actual DB column name
    JSON,
    default=dict
    )

    
    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="conversations")


