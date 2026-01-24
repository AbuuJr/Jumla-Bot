"""
app/schemas/auth.py
Enhanced Pydantic schemas for authentication
"""
from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional
from datetime import datetime
from enum import Enum


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


class LogoutRequest(BaseModel):
    """Logout request with optional refresh token"""
    refresh_token: Optional[str] = None


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr
    new_password: str = Field(..., min_length=8)


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


class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: UUID4
    email: str
    full_name: Optional[str]
    role: str
    organization_id: Optional[UUID4]  # Null for system owner
    is_active: bool
    is_system_owner: bool = False
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Session response schema"""
    id: UUID4
    user_id: UUID4
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, session):
        """Custom validation to handle is_valid property"""
        data = {
            "id": session.id,
            "user_id": session.user_id,
            "user_agent": session.user_agent,
            "ip_address": session.ip_address,
            "created_at": session.created_at,
            "last_used_at": session.last_used_at,
            "expires_at": session.expires_at,
            "is_active": session.is_valid
        }
        return cls(**data)