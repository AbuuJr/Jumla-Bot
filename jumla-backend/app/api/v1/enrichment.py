# ========================================
# app/api/v1/enrichment.py
# ========================================
"""
Enrichment trigger and status endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.lead import Lead

router_enrichment = APIRouter()


@router_enrichment.post("/trigger/{lead_id}")
async def trigger_enrichment(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger enrichment for a lead
    """
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id
        )
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Queue enrichment task
    from app.tasks.celery_app import enrich_lead_task
    task = enrich_lead_task.delay(str(lead_id))
    
    return {
        "message": "Enrichment task queued",
        "task_id": task.id,
        "lead_id": str(lead_id)
    }


@router_enrichment.get("/status/{task_id}")
async def get_enrichment_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check status of enrichment task
    """
    from app.tasks.celery_app import celery_app
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }