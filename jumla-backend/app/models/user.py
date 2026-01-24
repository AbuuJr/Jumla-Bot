"""
app/models/user.py 
User SQLAlchemy models - Enhanced with system owner support
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
    """User model with RBAC and system owner support"""
    __tablename__ = "users"
    
    # System owner has NULL organization_id
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), 
        nullable=True, 
        index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system_owner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(back_populates="users")
    assigned_leads: Mapped[List["Lead"]] = relationship(
        back_populates="assigned_agent", 
        foreign_keys="Lead.assigned_to"
    )
    approved_offers: Mapped[List["Offer"]] = relationship(
        back_populates="approver", 
        foreign_keys="Offer.approved_by"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")
    sessions: Mapped[List["Session"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        if self.is_system_owner:
            return f"<User {self.email} (SYSTEM_OWNER)>"
        return f"<User {self.email} ({self.role})>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission based on role"""
        # System owner has all permissions
        if self.is_system_owner:
            return True
            
        permissions_map = {
            UserRole.ADMIN: ["*"],  # All permissions within org
            UserRole.AGENT: ["read:leads", "update:leads", "create:conversations", "read:offers"],
            UserRole.INTEGRATOR: ["read:leads", "read:offers", "create:webhooks"],
            UserRole.BOT: ["read:leads", "create:conversations", "update:leads"],
        }
        user_perms = permissions_map.get(self.role, [])
        return "*" in user_perms or permission in user_perms
    
    def can_reset_password_for(self, target_user: "User") -> bool:
        """Check if this user can reset password for target user"""
        # System owner can reset anyone's password
        if self.is_system_owner:
            return True
        
        # Admin can reset non-admin users in their org
        if self.role == UserRole.ADMIN and target_user.role != UserRole.ADMIN:
            return self.organization_id == target_user.organization_id
        
        return False