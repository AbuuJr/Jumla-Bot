"""
app/models/organization.py
Organization SQLAlchemy models
"""
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Dict, Any
from . import Base

class Organization(Base):
    """Organization model"""
    __tablename__ = "organizations"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    leads: Mapped[List["Lead"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    buyers: Mapped[List["Buyer"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="organization")
    
    def __repr__(self) -> str:
        return f"<Organization {self.name} ({self.slug})>"