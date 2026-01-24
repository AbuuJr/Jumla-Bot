# ========================================
# app/api/v1/admin.py
# ========================================
"""
Admin-only endpoints for system management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import require_role, hash_password
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.auth import UserCreate, UserResponse
from app.schemas.common import PaginatedResponse

router_admin = APIRouter()


@router_admin.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Create new user (admin only)
    """
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
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router_admin.get("/users", response_model=PaginatedResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    List all users in organization (admin only)
    """
    query = select(User).where(User.organization_id == current_user.organization_id)
    
    if role:
        query = query.where(User.role == role)
    
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
    
    user.is_active = False
    await db.commit()
    
    return {"message": "User deactivated"}


@router_admin.get("/audit-logs", response_model=PaginatedResponse)
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = None,
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
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return PaginatedResponse(
        items=[log.__dict__ for log in logs],
        total=total or 0,
        skip=skip,
        limit=limit
    )


@router_admin.get("/health")
async def system_health(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    System health check (admin only)
    """
    # Check database
    try:
        await db.execute(select(1))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Celery workers
    from app.tasks.celery_app import celery_app
    try:
        inspector = celery_app.control.inspect()
        active_workers = inspector.active()
        celery_status = "healthy" if active_workers else "no workers"
    except Exception as e:
        celery_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" and celery_status == "healthy" else "degraded",
        "database": db_status,
        "celery": celery_status,
        "timestamp": datetime.utcnow().isoformat()
    }


from datetime import datetime