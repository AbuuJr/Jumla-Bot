"""
app/api/v1/buyers.py
Buyer management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.buyer import Buyer
from app.schemas.buyer import BuyerCreate, BuyerUpdate, BuyerResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.post("", response_model=BuyerResponse, status_code=status.HTTP_201_CREATED)
async def create_buyer(
    buyer_data: BuyerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new buyer"""
    buyer = Buyer(
        organization_id=current_user.organization_id,
        name=buyer_data.name,
        email=buyer_data.email,
        phone=buyer_data.phone,
        criteria=buyer_data.criteria or {},
        preferred_markets=buyer_data.preferred_markets,
        min_deal_size=buyer_data.min_deal_size,
        max_deal_size=buyer_data.max_deal_size,
        notes=buyer_data.notes,
    )
    
    db.add(buyer)
    await db.commit()
    await db.refresh(buyer)
    
    return buyer


@router.get("", response_model=PaginatedResponse)
async def list_buyers(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List buyers"""
    query = select(Buyer).where(
        Buyer.organization_id == current_user.organization_id,
        Buyer.is_active == is_active
    )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(Buyer.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    buyers = result.scalars().all()
    
    return PaginatedResponse(
        items=[BuyerResponse.model_validate(b) for b in buyers],
        total=total or 0,
        skip=skip,
        limit=limit
    )


@router.get("/{buyer_id}", response_model=BuyerResponse)
async def get_buyer(
    buyer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get buyer by ID"""
    result = await db.execute(
        select(Buyer).where(
            Buyer.id == buyer_id,
            Buyer.organization_id == current_user.organization_id
        )
    )
    buyer = result.scalar_one_or_none()
    
    if not buyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found"
        )
    
    return buyer


@router.patch("/{buyer_id}", response_model=BuyerResponse)
async def update_buyer(
    buyer_id: UUID,
    buyer_data: BuyerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update buyer"""
    result = await db.execute(
        select(Buyer).where(
            Buyer.id == buyer_id,
            Buyer.organization_id == current_user.organization_id
        )
    )
    buyer = result.scalar_one_or_none()
    
    if not buyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found"
        )
    
    update_data = buyer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(buyer, field, value)
    
    await db.commit()
    await db.refresh(buyer)
    
    return buyer