"""
app/services/auth_service.py
Enhanced authentication service with session management and improved error messages
"""
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from fastapi import HTTPException, status


from app.models.user import User
from app.models.session import Session
from app.models.audit_log import AuditLog
from app.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    decode_token
)
from app.config import settings




class AuthService:
    """Authentication service with session management, audit logging, and improved error messages"""
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        email: str,
        password: str
    ) -> User:
        """
        Authenticate user by email and password with specific error messages
        
        Returns:
            User if authenticated
            
        Raises:
            HTTPException with specific error messages for different failure cases:
            - 401: User not found
            - 401: Wrong password
            - 403: Account inactive
        """
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # IMPROVED: Specific error for non-existent users
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No account found with this email address. Please contact your system administrator to request access."
            )
        
        # Check if account is active
        if not user.is_active:
            # IMPROVED: Specific error for inactive accounts
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact your system administrator for assistance."
            )
        
        # Verify password
        if not verify_password(password, user.password_hash):
            # IMPROVED: More helpful error for wrong password
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password. Please try again or contact your administrator if you've forgotten your password."
            )
        
        return user
    
    async def create_tokens(
        self, 
        db: AsyncSession, 
        user: User,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Create access and refresh tokens with session persistence
        Updates last_login timestamp
        
        Returns:
            Tuple of (access_token, refresh_token)
        """
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "org_id": str(user.organization_id) if user.organization_id else None,
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Hash and store refresh token
        refresh_hash = hash_refresh_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        session = Session(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            last_used_at=datetime.utcnow()
        )
        
        db.add(session)
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        
        await db.commit()
        
        return access_token, refresh_token
    
    async def refresh_tokens(
        self,
        db: AsyncSession,
        refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Refresh access token using refresh token
        Implements token rotation: old refresh token is revoked, new one issued
        
        Returns:
            Tuple of (new_access_token, new_refresh_token)
        """
        # Decode refresh token
        payload = decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Find and validate session
        refresh_hash = hash_refresh_token(refresh_token)
        result = await db.execute(
            select(Session).where(
                Session.refresh_token_hash == refresh_hash,
                Session.user_id == user_id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        if not session.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or revoked"
            )
        
        # Get user
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Revoke old session (token rotation)
        session.revoke()
        
        # Create new tokens and session
        new_access_token, new_refresh_token = await self.create_tokens(
            db, user, user_agent, ip_address
        )
        
        return new_access_token, new_refresh_token
    
    async def logout(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> bool:
        """
        Logout user by revoking refresh token session
        
        Returns:
            True if session was revoked, False if not found
        """
        refresh_hash = hash_refresh_token(refresh_token)
        
        result = await db.execute(
            select(Session).where(Session.refresh_token_hash == refresh_hash)
        )
        session = result.scalar_one_or_none()
        
        if session:
            session.revoke()
            await db.commit()
            return True
        
        return False
    
    async def revoke_all_user_sessions(
        self,
        db: AsyncSession,
        user_id: str
    ):
        """Revoke all sessions for a user (e.g., on password change)"""
        result = await db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.revoked_at.is_(None)
            )
        )
        sessions = result.scalars().all()
        
        for session in sessions:
            session.revoke()
        
        await db.commit()
    
    async def reset_password_for_user(
        self,
        db: AsyncSession,
        requestor: User,
        target_email: str,
        new_password: str,
        ip_address: Optional[str] = None
    ) -> User:
        """
        Reset password for a user with proper authorization checks
        
        Rules:
        - System owner can reset anyone's password
        - Admin can reset non-admin users in their org
        - Nobody else can reset passwords
        
        Args:
            requestor: User requesting the password reset
            target_email: Email of user whose password to reset
            new_password: New password (plain text, will be hashed)
            ip_address: IP address of requestor for audit
        
        Returns:
            Updated user
        
        Raises:
            HTTPException if not authorized or user not found
        """
        # Find target user
        result = await db.execute(
            select(User).where(User.email == target_email)
        )
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check authorization
        if not requestor.can_reset_password_for(target_user):
            if target_user.role == "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin passwords can only be reset by System Owner"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to reset this user's password"
                )
        
        # Store before state for audit
        before_state = {
            "email": target_user.email,
            "role": target_user.role,
            "is_active": target_user.is_active
        }
        
        # Update password
        target_user.password_hash = hash_password(new_password)
        
        # Revoke all existing sessions
        await self.revoke_all_user_sessions(db, str(target_user.id))
        
        # Create audit log
        audit_log = AuditLog(
            organization_id=target_user.organization_id,
            user_id=requestor.id if not requestor.is_system_owner else None,
            performed_by=requestor.email,
            entity_type="user",
            entity_id=target_user.id,
            action="reset_password",
            before=before_state,
            after={
                "email": target_user.email,
                "role": target_user.role,
                "is_active": target_user.is_active,
                "password_changed": True
            },
            ip_address=ip_address
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(target_user)
        
        return target_user




# Singleton instance
auth_service = AuthService()



