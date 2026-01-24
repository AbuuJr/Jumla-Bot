"""
app/api/v1/offers.py
Offer management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.lead import Lead
from app.models.property import Property
from app.models.offer import Offer, OfferStatus
from app.services.offer_engine import offer_engine, OfferStrategy
from app.schemas.offer import (
    OfferCreate,
    OfferResponse,
    OfferUpdate,
    OfferApproveRequest,
    OfferListResponse,
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.post("", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    offer_data: OfferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new offer using the deterministic offer engine
    """
    # Verify lead access
    result = await db.execute(
        select(Lead).where(
            Lead.id == offer_data.lead_id,
            Lead.organization_id == current_user.organization_id
        )
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Get property data
    property_data = lead.enriched_data
    
    # Calculate offer using deterministic engine
    try:
        calculation = offer_engine.calculate_offer(
            estimated_value=Decimal(str(property_data.get("estimated_value", 200000))),
            sqft=property_data.get("sqft"),
            condition=property_data.get("condition"),
            bedrooms=property_data.get("bedrooms"),
            bathrooms=Decimal(str(property_data.get("bathrooms"))) if property_data.get("bathrooms") else None,
            year_built=property_data.get("year_built"),
            strategy=offer_data.strategy or OfferStrategy.STANDARD
        )
        
        # Create offer record
        offer = Offer(
            lead_id=offer_data.lead_id,
            property_id=offer_data.property_id,
            buyer_id=offer_data.buyer_id,
            offer_amount=calculation.offer_amount,
            offer_type=offer_data.offer_type or "cash",
            calculation_data={
                "offer_amount": float(calculation.offer_amount),
                "arv": float(calculation.arv),
                "repair_cost": float(calculation.repair_cost),
                "margin_percent": float(calculation.margin_percent),
                "confidence_level": calculation.confidence_level,
                "factors": calculation.factors,
                "warnings": calculation.warnings,
            },
            status=OfferStatus.PENDING,
            notes=offer_data.notes,
        )
        
        db.add(offer)
        await db.commit()
        await db.refresh(offer)
        
        return offer
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=PaginatedResponse)
async def list_offers(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    lead_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List offers with filtering
    """
    query = select(Offer).join(Lead).where(
        Lead.organization_id == current_user.organization_id
    )
    
    if status:
        query = query.where(Offer.status == status)
    if lead_id:
        query = query.where(Offer.lead_id == lead_id)
    
    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Paginate
    query = query.order_by(Offer.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    offers = result.scalars().all()
    
    return PaginatedResponse(
        items=[OfferResponse.model_validate(o) for o in offers],
        total=total or 0,
        skip=skip,
        limit=limit
    )


@router.get("/{offer_id}", response_model=OfferResponse)
async def get_offer(
    offer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get offer by ID
    """
    result = await db.execute(
        select(Offer).join(Lead).where(
            Offer.id == offer_id,
            Lead.organization_id == current_user.organization_id
        )
    )
    offer = result.scalar_one_or_none()
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found"
        )
    
    return offer


@router.post("/{offer_id}/approve", response_model=OfferResponse)
async def approve_offer(
    offer_id: UUID,
    approve_data: OfferApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Approve offer (admin only)
    """
    result = await db.execute(
        select(Offer).join(Lead).where(
            Offer.id == offer_id,
            Lead.organization_id == current_user.organization_id
        )
    )
    offer = result.scalar_one_or_none()
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found"
        )
    
    if offer.status != OfferStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve offer with status: {offer.status}"
        )
    
    offer.status = OfferStatus.APPROVED
    offer.approved_by = current_user.id
    offer.approved_at = datetime.utcnow()
    if approve_data.notes:
        offer.notes = f"{offer.notes}\n\nApproval notes: {approve_data.notes}" if offer.notes else approve_data.notes
    
    await db.commit()
    await db.refresh(offer)
    
    return offer


@router.post("/{offer_id}/send", response_model=OfferResponse)
async def send_offer(
    offer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send approved offer to lead
    """
    result = await db.execute(
        select(Offer).join(Lead).where(
            Offer.id == offer_id,
            Lead.organization_id == current_user.organization_id
        )
    )
    offer = result.scalar_one_or_none()
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found"
        )
    
    if offer.status != OfferStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer must be approved before sending"
        )
    
    # TODO: Send via SMS/email using Twilio/SendGrid
    # from app.services.twilio_adapter import twilio_adapter
    # await twilio_adapter.send_sms(lead.phone, message)
    
    offer.status = OfferStatus.SENT
    offer.sent_at = datetime.utcnow()
    offer.expires_at = datetime.utcnow() + timedelta(days=7)
    
    await db.commit()
    await db.refresh(offer)
    
    return offer


@router.patch("/{offer_id}", response_model=OfferResponse)
async def update_offer(
    offer_id: UUID,
    offer_data: OfferUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update offer
    """
    result = await db.execute(
        select(Offer).join(Lead).where(
            Offer.id == offer_id,
            Lead.organization_id == current_user.organization_id
        )
    )
    offer = result.scalar_one_or_none()
    
    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found"
        )
    
    update_data = offer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(offer, field, value)
    
    await db.commit()
    await db.refresh(offer)
    
    return offer