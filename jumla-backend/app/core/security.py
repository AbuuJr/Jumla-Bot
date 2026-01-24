"""
app/core/security.py
JWT authentication, password hashing, and RBAC utilities
ENHANCED: Added refresh token hashing and system owner support
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.config import settings
from app.models.user import User
from app.core.database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token scheme
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)  # For optional auth


def hash_password(password: str) -> str:
    """Hash a plain password (bcrypt max 72 bytes)"""
    password_bytes = password.encode("utf-8")[:72]
    return pwd_context.hash(password_bytes)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(
        plain_password.encode("utf-8")[:72],
        hashed_password
    )


# NEW: Hash refresh token for secure storage
def hash_refresh_token(token: str) -> str:
    """
    Hash refresh token for secure storage using SHA-256
    Uses SHA-256 for fast comparison (not bcrypt which is slow)
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire, 
        "type": "access",
        "iat": datetime.utcnow()  # NEW: Add issued at time
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token with longer expiry and unique ID"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire, 
        "type": "refresh",
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(32)  # NEW: JWT ID for uniqueness
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    Raises 401 if not authenticated.
    
    Usage:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, otherwise return None.
    Used for endpoints that allow both public and authenticated access.
    
    Usage:
        @router.post("/leads")
        async def create_lead(
            current_user: Optional[User] = Depends(get_current_user_optional)
        ):
            if current_user:
                # Authenticated request
                org_id = current_user.organization_id
            else:
                # Public request
                org_id = settings.DEFAULT_ORGANIZATION_ID
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        if payload.get("type") != "access":
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Fetch user from database
        result = await db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if user is None or not user.is_active:
            return None
        
        return user
    except Exception:
        # If token is invalid, just return None instead of raising error
        return None


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control.
    ENHANCED: System owner bypasses role checks
    
    Usage:
        @router.post("/admin/users")
        async def create_user(
            current_user: User = Depends(require_role("admin"))
        ):
            ...
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # NEW: System owner bypasses all role checks
        if hasattr(current_user, 'is_system_owner') and current_user.is_system_owner:
            return current_user
            
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


def require_permission(permission: str):
    """
    Dependency factory for permission-based access control.
    
    Usage:
        @router.get("/leads")
        async def get_leads(
            current_user: User = Depends(require_permission("read:leads"))
        ):
            ...
    """
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}"
            )
        return current_user
    
    return permission_checker


# NEW: System owner dependency
def require_system_owner():
    """
    Dependency to require system owner access.
    
    Usage:
        @router.post("/system/organizations")
        async def create_org(
            current_user: User = Depends(require_system_owner())
        ):
            ...
    """
    async def system_owner_checker(current_user: User = Depends(get_current_user)) -> User:
        if not hasattr(current_user, 'is_system_owner') or not current_user.is_system_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System owner access required"
            )
        return current_user
    
    return system_owner_checker