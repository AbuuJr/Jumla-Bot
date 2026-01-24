"""
# ========== app/schemas/auth.py ==========
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional
from datetime import datetime
from enum import Enum
from app.db.mixins import TimestampMixin


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    AGENT = "agent"
    INTEGRATOR = "integrator"
    BOT = "bot"


class UserCreate(BaseModel):
    """User creation schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: UserRole
    organization_id: UUID4


class UserResponse(BaseModel):
    """User response schema"""
    id: UUID4
    email: str
    full_name: Optional[str]
    role: str
    organization_id: UUID4
    is_active: bool
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True
