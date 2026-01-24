"""
app/models/user.py 
User SQLAlchemy models
"""
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

from . import Base


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    AGENT = "agent"
    INTEGRATOR = "integrator"
    BOT = "bot"

class User(Base):
    """User model with RBAC"""
    __tablename__ = "users"
    
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="users")
    assigned_leads: Mapped[List["Lead"]] = relationship(back_populates="assigned_agent", foreign_keys="Lead.assigned_to")
    approved_offers: Mapped[List["Offer"]] = relationship(back_populates="approver", foreign_keys="Offer.approved_by")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission based on role"""
        permissions_map = {
            UserRole.ADMIN: ["*"],  # All permissions
            UserRole.AGENT: ["read:leads", "update:leads", "create:conversations", "read:offers"],
            UserRole.INTEGRATOR: ["read:leads", "read:offers", "create:webhooks"],
            UserRole.BOT: ["read:leads", "create:conversations", "update:leads"],
        }
        user_perms = permissions_map.get(self.role, [])
        return "*" in user_perms or permission in user_perms