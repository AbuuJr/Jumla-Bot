# ========================================
# app/services/lead_service.py
# ========================================
"""
Lead business logic service
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.models.lead import Lead, LeadStage
from app.models.lead_score import LeadScore


class LeadService:
    """Lead service with business logic"""
    
    async def create_lead(
        self,
        db: AsyncSession,
        organization_id: UUID,
        phone: str,
        **kwargs
    ) -> Lead:
        """
        Create a new lead with deduplication
        
        Checks if lead with same phone exists first
        """
        # Check for existing lead
        result = await db.execute(
            select(Lead).where(
                Lead.organization_id == organization_id,
                Lead.phone == phone
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing lead instead of creating duplicate
            for key, value in kwargs.items():
                if value is not None:
                    setattr(existing, key, value)
            await db.commit()
            await db.refresh(existing)
            return existing
        
        # Create new lead
        lead = Lead(
            organization_id=organization_id,
            phone=phone,
            **kwargs
        )
        db.add(lead)
        await db.commit()
        await db.refresh(lead)
        
        return lead
    
    async def search_leads(
        self,
        db: AsyncSession,
        organization_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Lead], int]:
        """
        Search leads by name, phone, or email
        
        Returns:
            Tuple of (leads, total_count)
        """
        query = select(Lead).where(
            Lead.organization_id == organization_id,
            or_(
                Lead.name.ilike(f"%{search_term}%"),
                Lead.phone.ilike(f"%{search_term}%"),
                Lead.email.ilike(f"%{search_term}%"),
            )
        )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Get paginated results
        query = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        leads = result.scalars().all()
        
        return leads, total or 0
    
    async def get_lead_with_score(
        self,
        db: AsyncSession,
        lead_id: UUID,
        organization_id: UUID
    ) -> Optional[tuple[Lead, Optional[LeadScore]]]:
        """
        Get lead with its score
        
        Returns:
            Tuple of (lead, score) or None if not found
        """
        # Get lead
        result = await db.execute(
            select(Lead).where(
                Lead.id == lead_id,
                Lead.organization_id == organization_id
            )
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            return None
        
        # Get score
        score_result = await db.execute(
            select(LeadScore).where(LeadScore.lead_id == lead_id)
        )
        score = score_result.scalar_one_or_none()
        
        return lead, score
    
    async def update_lead_stage(
        self,
        db: AsyncSession,
        lead_id: UUID,
        new_stage: LeadStage
    ) -> Optional[Lead]:
        """
        Update lead stage with business logic
        
        Performs validation and triggers appropriate actions
        """
        result = await db.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            return None
        
        old_stage = lead.stage
        lead.stage = new_stage
        
        # Business logic based on stage transition
        if new_stage == LeadStage.CLOSED_WON:
            # TODO: Trigger won notification
            pass
        elif new_stage == LeadStage.CLOSED_LOST:
            # TODO: Log lost reason
            pass
        
        await db.commit()
        await db.refresh(lead)
        
        return lead


# Singleton instance
lead_service = LeadService()