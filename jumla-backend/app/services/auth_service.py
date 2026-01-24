"""
app/services/auth_service.py
Authentication business logic
"""
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.user import User
from app.core.security import verify_password, create_access_token, create_refresh_token


class AuthService:
    """Authentication service with business logic"""
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user by email and password
        
        Returns:
            User if authenticated, None otherwise
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        return user
    
    def create_tokens(self, user: User) -> Tuple[str, str]:
        """
        Create access and refresh tokens for user
        
        Returns:
            Tuple of (access_token, refresh_token)
        """
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "org_id": str(user.organization_id),
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return access_token, refresh_token


# Singleton instance
auth_service = AuthService()


