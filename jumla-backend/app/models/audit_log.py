"""
app/models/audit_log.py
Enhanced audit log model with before/after snapshots
"""
from sqlalchemy import String, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import INET
from typing import Optional, Dict, Any
from uuid import UUID

from . import Base


class AuditLog(Base):
    """Audit log model - tracks all system actions with before/after state"""
    __tablename__ = "audit_logs"
    
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), 
        index=True
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), 
        index=True
    )
    performed_by: Mapped[Optional[str]] = mapped_column(
        String(255), 
        index=True,
        comment="Email of user or 'system_owner_script'"
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # State snapshots
    before: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        comment="State before action"
    )
    after: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        comment="State after action"
    )
    
    # Legacy field (kept for backward compatibility)
    changes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(back_populates="audit_logs")
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id} by {self.performed_by}>"