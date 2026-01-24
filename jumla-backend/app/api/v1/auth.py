"""
app/api/v1/auth.py
Enhanced authentication endpoints with session management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    LogoutRequest
)
from app.services.auth_service import auth_service

router = APIRouter()


def get_client_info(request: Request) -> tuple:
    """Extract client information from request"""
    user_agent = request.headers.get("user-agent")
    # Get real IP, considering proxy headers
    ip_address = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
        request.headers.get("x-real-ip") or
        request.client.host if request.client else None
    )
    return user_agent, ip_address


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens
    
    Creates a session for refresh token tracking.
    
    Returns:
        - access_token: Short-lived token for API requests (15 min)
        - refresh_token: Long-lived token for refreshing access (7 days)
    """
    # Authenticate user
    user = await auth_service.authenticate_user(
        db=db,
        email=credentials.email,
        password=credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Get client info
    user_agent, ip_address = get_client_info(request)
    
    # Create tokens and session
    access_token, refresh_token = await auth_service.create_tokens(
        db=db,
        user=user,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    from app.config import settings
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    Implements token rotation: old refresh token is revoked,
    new access and refresh tokens are issued.
    """
    user_agent, ip_address = get_client_info(request)
    
    try:
        access_token, refresh_token = await auth_service.refresh_tokens(
            db=db,
            refresh_token=refresh_request.refresh_token,
            user_agent=user_agent,
            ip_address=ip_address
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    from app.config import settings
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user info
    """
    return current_user


@router.post("/logout")
async def logout(
    logout_request: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout user by revoking refresh token session
    
    Client should also delete tokens from storage.
    """
    if logout_request.refresh_token:
        revoked = await auth_service.logout(
            db=db,
            refresh_token=logout_request.refresh_token
        )
        
        if revoked:
            return {"message": "Logged out successfully", "session_revoked": True}
        else:
            return {"message": "Logged out", "session_revoked": False}
    
    return {"message": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout from all devices by revoking all user sessions
    """
    await auth_service.revoke_all_user_sessions(
        db=db,
        user_id=str(current_user.id)
    )
    
    return {"message": "Logged out from all devices"}