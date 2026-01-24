"""
app/models/session.py
Session model for refresh token management
"""
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from uuid import UUID

from . import Base


class Session(Base):
    """Session model for tracking refresh tokens"""
    __tablename__ = "sessions"
    
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        index=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        index=True
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<Session {self.id} for user {self.user_id}>"
    
    @property
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        now = datetime.utcnow()
        return (
            self.revoked_at is None and 
            self.expires_at > now
        )
    
    def revoke(self):
        """Revoke this session"""
        self.revoked_at = datetime.utcnow()