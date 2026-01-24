"""
app/api/v1/leads.py
Leads CRUD endpoints with chat support and AI integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional, require_permission
from app.dependencies import get_llm_client, get_rate_limiter
from app.models.user import User
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.schemas.lead import (
    LeadCreate,
    LeadCreateResponse,
    LeadUpdate,
    LeadResponse,
    LeadWithScore,
)
from app.schemas.common import PaginatedResponse
from app.services.llm.client import LLMClient, AllProvidersFailedError
from app.services.rate_limiter import TokenBucketRateLimiter
from app.core.metrics import metrics_collector
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=LeadCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    llm_client: LLMClient = Depends(get_llm_client),
    rate_limiter: TokenBucketRateLimiter = Depends(get_rate_limiter),
):
    """
    Create a new lead.
    
    Supports both PUBLIC and AUTHENTICATED access:
    - PUBLIC: Sellers can create leads via forms/chat without login
    - AUTHENTICATED: Admins can create leads manually
    
    Returns:
        LeadCreateResponse with lead and optional conversation_id
    """
    
    # =================================================================
    # Determine Organization ID
    # =================================================================
    if current_user:
        # Authenticated request (admin creating lead manually)
        organization_id = current_user.organization_id
        is_authenticated = True
        logger.info(
            f"Creating lead (authenticated): org={organization_id}, "
            f"source={lead_data.source}, user={current_user.email}"
        )
    else:
        # Public request (seller submitting form/chat)
        if not settings.DEFAULT_ORGANIZATION_ID:
            logger.error("DEFAULT_ORGANIZATION_ID not configured for public lead creation")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Public lead creation is not configured. Please contact support."
            )
        
        try:
            organization_id = UUID(settings.DEFAULT_ORGANIZATION_ID)
        except (ValueError, TypeError):
            logger.error(f"Invalid DEFAULT_ORGANIZATION_ID: {settings.DEFAULT_ORGANIZATION_ID}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System configuration error. Please contact support."
            )
        
        is_authenticated = False
        logger.info(
            f"Creating lead (public): org={organization_id}, source={lead_data.source}"
        )
    
    org_id = str(organization_id)
    conversation_id = None
    
    try:
        # ====================================================================
        # STEP 1: Check for Existing Lead (Deduplication)
        # ====================================================================
        # Only check for duplicates if we have contact info
        # Chat leads without contact info are always new until AI extracts details
        existing_lead = None
        
        if lead_data.phone:
            result = await db.execute(
                select(Lead).where(
                    Lead.organization_id == organization_id,
                    Lead.phone == lead_data.phone
                )
            )
            existing_lead = result.scalar_one_or_none()
        
        if not existing_lead and lead_data.email:
            result = await db.execute(
                select(Lead).where(
                    Lead.organization_id == organization_id,
                    Lead.email == lead_data.email
                )
            )
            existing_lead = result.scalar_one_or_none()
        
        # For chat leads without contact info, always create new lead
        # The AI will extract contact details and we can merge later if needed
        
        # ====================================================================
        # STEP 2: Create or Update Lead
        # ====================================================================
        if existing_lead:
            logger.info(f"Found existing lead: {existing_lead.id}")
            
            # Update with new data (don't overwrite existing values)
            if lead_data.email and not existing_lead.email:
                existing_lead.email = lead_data.email
            if lead_data.name and not existing_lead.name:
                existing_lead.name = lead_data.name
            if lead_data.phone and not existing_lead.phone:
                existing_lead.phone = lead_data.phone
            if lead_data.tags:
                existing_tags = set(existing_lead.tags or [])
                new_tags = set(lead_data.tags)
                existing_lead.tags = list(existing_tags | new_tags)
            
            lead = existing_lead
        else:
            # Create new lead
            lead = Lead(
                organization_id=organization_id,
                phone=lead_data.phone,
                email=lead_data.email,
                name=lead_data.name,
                source=lead_data.source,
                stage="new",  # Fixed: use 'stage' not 'status'
                raw_data=lead_data.raw_data or {},
                enriched_data={},
                tags=lead_data.tags or [],
            )
            db.add(lead)
            await db.flush()  # Get lead.id without committing
            logger.info(f"Created new lead: {lead.id}")
        
        # ====================================================================
        # STEP 3: Handle Chat-Initiated Lead (AI Processing)
        # ====================================================================
        if lead_data.initial_message and lead_data.source == "chat":
            logger.info(f"Processing chat-initiated lead: {lead.id}")
            
            # Check rate limits
            allowed, retry_after = await rate_limiter.check_rate_limit(
                org_id=org_id,
                operation="chat_lead_creation",
            )
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for org: {org_id}")
                ai_response = "Thank you for reaching out! A team member will respond shortly."
                use_ai = False
            else:
                use_ai = True
            
            # Process with AI if allowed
            extracted_data = None
            
            if use_ai:
                try:
                    # Extract structured data from message
                    extraction_result = await llm_client.extract_lead_info(
                        message=lead_data.initial_message,
                        sender="chat_user",
                        conversation_history=[],
                        lead_id=str(lead.id),
                    )
                    
                    extracted_data = extraction_result.data
                    
                    # Update lead with extracted info
                    if extraction_result.validated:
                        contact = extracted_data.get("contact", {})
                        if contact.get("name") and not lead.name:
                            lead.name = contact["name"]
                        if contact.get("phone") and not lead.phone:
                            lead.phone = contact["phone"]
                        if contact.get("email") and not lead.email:
                            lead.email = contact["email"]
                        
                        # Store in enriched_data
                        if not lead.enriched_data:
                            lead.enriched_data = {}
                        lead.enriched_data["initial_extraction"] = extracted_data
                    
                    # Generate AI response
                    response_result = await llm_client.generate_response(
                        message=lead_data.initial_message,
                        lead_stage=lead.stage,  # Fixed: use 'stage' not 'status'
                        info_summary=lead.name or "New contact",
                        conversation_history=[],
                    )
                    
                    ai_response = response_result.content
                    logger.info(f"AI processing successful for lead: {lead.id}")
                    
                except AllProvidersFailedError as e:
                    logger.error(f"AI processing failed: {str(e)}")
                    ai_response = (
                        "Thank you for reaching out! I'd be happy to help you with your property. "
                        "Can you tell me a bit more about what you're looking for?"
                    )
                except Exception as e:
                    logger.error(f"Unexpected AI error: {str(e)}", exc_info=True)
                    ai_response = "Thank you for your message! How can I help you today?"
            else:
                ai_response = "Thank you for reaching out! A team member will respond shortly."
            
            # Create conversation records
            user_conversation = Conversation(
                lead_id=lead.id,
                channel="chat",
                direction="inbound",
                message_body=lead_data.initial_message,
                status="received",
                extracted_data=extracted_data,
                metadata={
                    "is_initial_message": True,
                    "ai_processed": use_ai,
                    "is_authenticated": is_authenticated,
                },
            )
            db.add(user_conversation)
            await db.flush()
            
            bot_conversation = Conversation(
                lead_id=lead.id,
                channel="chat",
                direction="outbound",
                message_body=ai_response,
                status="sent",
                metadata={
                    "auto_generated": True,
                    "is_authenticated": is_authenticated,
                },
            )
            db.add(bot_conversation)
            
            conversation_id = str(user_conversation.id)
            logger.info(f"Created conversation: {conversation_id}")
        
        # ====================================================================
        # STEP 4: Commit and Return
        # ====================================================================
        await db.commit()
        await db.refresh(lead)
        
        logger.info(
            f"Successfully created/updated lead: {lead.id}, "
            f"authenticated={is_authenticated}"
        )
        
        # Track metrics
        try:
            metrics_collector.track_event(
                event="lead_created",
                properties={
                    "lead_id": str(lead.id),
                    "source": lead_data.source,
                    "organization_id": str(organization_id),
                    "is_authenticated": is_authenticated,
                    "has_chat": bool(conversation_id),
                }
            )
        except Exception as e:
            logger.warning(f"Failed to track metrics: {e}")
        
        # TODO: Trigger background tasks for enrichment and scoring
        # background_tasks.add_task(enrich_lead_task, str(lead.id))
        # background_tasks.add_task(score_lead_task, str(lead.id))
        
        return LeadCreateResponse(
            lead=LeadResponse.model_validate(lead),
            conversation_id=conversation_id,
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create lead: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lead. Please try again."
        )


@router.get("", response_model=PaginatedResponse)
async def list_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    stage: Optional[str] = None,  # Fixed: renamed from 'status' to 'stage'
    temperature: Optional[str] = None,
    assigned_to: Optional[UUID] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("read:leads"))
):
    """
    List leads with filtering and pagination.
    
    REQUIRES AUTHENTICATION - Admin only
    """
    query = select(Lead).where(Lead.organization_id == current_user.organization_id)
    
    # Apply filters
    if stage:  # Fixed: changed from 'status' to 'stage'
        query = query.where(Lead.stage == stage)
    if temperature:
        query = query.where(Lead.temperature == temperature)
    if assigned_to:
        query = query.where(Lead.assigned_to == assigned_to)
    if source:
        query = query.where(Lead.source == source)
    if search:
        query = query.where(
            or_(
                Lead.name.ilike(f"%{search}%"),
                Lead.phone.ilike(f"%{search}%"),
                Lead.email.ilike(f"%{search}%"),
            )
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
    
    # Execute
    result = await db.execute(query)
    leads = result.scalars().all()
    
    return PaginatedResponse(
        items=[LeadResponse.model_validate(lead) for lead in leads],
        total=total or 0,
        skip=skip,
        limit=limit,
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("read:leads"))
):
    """
    Get lead by ID.
    
    REQUIRES AUTHENTICATION - Admin only
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
    
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    lead_data: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("update:leads"))
):
    """
    Update lead.
    
    REQUIRES AUTHENTICATION - Admin only
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
    
    # Update fields
    update_data = lead_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
    
    await db.commit()
    await db.refresh(lead)
    
    logger.info(f"Lead updated: {lead.id} by user {current_user.email}")
    
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("delete:leads"))
):
    """
    Delete lead.
    
    REQUIRES AUTHENTICATION - Admin only
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
    
    await db.delete(lead)
    await db.commit()
    
    logger.info(f"Lead deleted: {lead_id} by user {current_user.email}")
    
    return None