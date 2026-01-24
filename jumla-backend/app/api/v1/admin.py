"""
app/api/v1/admin.py
Enhanced admin endpoints with password reset and session management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import require_role, hash_password
from app.models.user import User
from app.models.session import Session
from app.models.audit_log import AuditLog
from app.schemas.auth import (
    UserCreate, 
    UserResponse, 
    PasswordResetRequest,
    SessionResponse
)
from app.schemas.common import PaginatedResponse
from app.services.auth_service import auth_service

router_admin = APIRouter()


@router_admin.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Create new user within organization (admin only)
    
    Admins can only create users in their own organization.
    """
    # Verify organization match (unless system owner)
    if not current_user.is_system_owner:
        if user_data.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create users in other organizations"
            )
    
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        organization_id=user_data.organization_id,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True
    )
    
    db.add(user)
    await db.flush()
    
    # Audit log
    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=current_user.id,
        performed_by=current_user.email,
        entity_type="user",
        entity_id=user.id,
        action="create",
        before=None,
        after={
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router_admin.get("/users", response_model=PaginatedResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    List all users in organization (admin only)
    """
    query = select(User).where(User.organization_id == current_user.organization_id)
    
    if role:
        query = query.where(User.role == role)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total or 0,
        skip=skip,
        limit=limit
    )


@router_admin.post("/reset-password")
async def reset_user_password(
    reset_data: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Reset password for a user
    
    Authorization:
    - System Owner can reset any password
    - Admin can reset non-admin users in their organization
    - Admin CANNOT reset other admin passwords
    """
    ip_address = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
        request.headers.get("x-real-ip") or
        request.client.host if request.client else None
    )
    
    try:
        updated_user = await auth_service.reset_password_for_user(
            db=db,
            requestor=current_user,
            target_email=reset_data.email,
            new_password=reset_data.new_password,
            ip_address=ip_address
        )
        
        return {
            "message": "Password reset successfully",
            "user_email": updated_user.email,
            "sessions_revoked": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router_admin.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Deactivate user (admin only)
    """
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == current_user.organization_id
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    before_state = {"is_active": user.is_active}
    user.is_active = False
    
    # Revoke all sessions
    await auth_service.revoke_all_user_sessions(db, str(user.id))
    
    # Audit log
    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=current_user.id,
        performed_by=current_user.email,
        entity_type="user",
        entity_id=user.id,
        action="deactivate",
        before=before_state,
        after={"is_active": False}
    )
    db.add(audit)
    
    await db.commit()
    
    return {"message": "User deactivated", "sessions_revoked": True}


@router_admin.get("/sessions", response_model=PaginatedResponse)
async def list_user_sessions(
    user_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    List active sessions for users in organization
    """
    query = select(Session).join(User).where(
        User.organization_id == current_user.organization_id
    )
    
    if user_id:
        query = query.where(Session.user_id == user_id)
    
    # Only active sessions
    query = query.where(Session.revoked_at.is_(None))
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(Session.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return PaginatedResponse(
        items=[SessionResponse.model_validate(s) for s in sessions],
        total=total or 0,
        skip=skip,
        limit=limit
    )


@router_admin.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Revoke a specific session (admin only)
    """
    result = await db.execute(
        select(Session).join(User).where(
            Session.id == session_id,
            User.organization_id == current_user.organization_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    session.revoke()
    await db.commit()
    
    return {"message": "Session revoked"}


@router_admin.get("/audit-logs", response_model=PaginatedResponse)
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Get audit logs (admin only)
    """
    query = select(AuditLog).where(
        AuditLog.organization_id == current_user.organization_id
    )
    
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    
    if action:
        query = query.where(AuditLog.action == action)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return PaginatedResponse(
        items=[{
            "id": str(log.id),
            "performed_by": log.performed_by,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id),
            "action": log.action,
            "before": log.before,
            "after": log.after,
            "created_at": log.created_at.isoformat(),
            "ip_address": log.ip_address
        } for log in logs],
        total=total or 0,
        skip=skip,
        limit=limit
    )