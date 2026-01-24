"""
app/api/v1/conversations.py
Conversation management endpoints with AI integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
import logging
from datetime import datetime

from app.core.database import get_db
from app.config import settings
from app.core.security import get_current_user, get_current_user_optional
from app.dependencies import get_llm_client, get_rate_limiter
from app.models.user import User
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    SendMessageRequest,
    SendMessageResponse,
    MessageResponse

)
from app.services.llm.client import LLMClient, AllProvidersFailedError
from app.services.rate_limiter import TokenBucketRateLimiter
from app.core.metrics import metrics_collector

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _get_conversation_history(
    db: AsyncSession,
    lead_id: UUID,
    limit: int = 10,
) -> List[dict]:
    """
    Get recent conversation history for AI context.
    
    Args:
        db: Database session
        lead_id: Lead identifier
        limit: Number of recent messages to fetch
    
    Returns:
        List of conversation messages in chronological order
    """
    result = await db.execute(
        select(Conversation)
        .where(Conversation.lead_id == lead_id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()
    
    # Convert to format expected by LLM
    return [
        {
            "role": "user" if conv.direction == "inbound" else "assistant",
            "content": conv.message_body,
            "timestamp": conv.created_at.isoformat(),
        }
        for conv in reversed(history)
        if conv.message_body
    ]


async def _update_lead_from_extraction(
    db: AsyncSession,
    lead: Lead,
    extracted_data: dict,
):
    """
    Update lead record with extracted information.
    
    Args:
        db: Database session
        lead: Lead model instance
        extracted_data: Extracted data from AI
    """
    try:
        # Update contact information
        contact = extracted_data.get("contact", {})
        if contact.get("name") and not lead.name:
            lead.name = contact["name"]
        if contact.get("phone") and not lead.phone:
            lead.phone = contact["phone"]
        if contact.get("email") and not lead.email:
            lead.email = contact["email"]
        
        # Update property information in enriched_data
        property_data = extracted_data.get("property", {})
        situation = extracted_data.get("situation", {})
        
        # Merge into enriched_data
        if not lead.enriched_data:
            lead.enriched_data = {}
        
        for key, value in property_data.items():
            if value is not None:
                lead.enriched_data[f"property_{key}"] = value
        
        for key, value in situation.items():
            if value is not None:
                lead.enriched_data[f"situation_{key}"] = value
        
        # Update lead status based on intent
        intent = extracted_data.get("intent", {})
        if intent.get("classification") == "qualified_lead":
            if lead.status == "new":
                lead.status = "contacted"
        elif intent.get("classification") == "not_interested":
            lead.status = "disqualified"
        
        # Store full extraction for audit
        lead.enriched_data["last_ai_extraction"] = extracted_data
        
        await db.commit()
        logger.info(f"Updated lead {lead.id} from AI extraction")
        
    except Exception as e:
        logger.error(f"Failed to update lead from extraction: {str(e)}")
        await db.rollback()


def _build_info_summary(lead: Lead, extracted_data: Optional[dict] = None) -> str:
    """
    Build human-readable summary of lead information for AI context.
    
    Args:
        lead: Lead model instance
        extracted_data: Optional extracted data from latest message
    
    Returns:
        Summary string
    """
    parts = []
    
    # From lead record
    if lead.name:
        parts.append(f"Name: {lead.name}")
    if lead.phone:
        parts.append(f"Phone: {lead.phone}")
    
    # From enriched data
    if lead.enriched_data:
        if lead.enriched_data.get("property_address"):
            parts.append(f"Property: {lead.enriched_data['property_address']}")
        if lead.enriched_data.get("situation_motivation"):
            parts.append(f"Motivation: {lead.enriched_data['situation_motivation']}")
    
    # From latest extraction
    if extracted_data:
        property_data = extracted_data.get("property", {})
        if property_data.get("address"):
            parts.append(f"Property: {property_data['address']}")
    
    return "; ".join(parts) if parts else "Limited information available"


def _get_fallback_response(lead_status: str) -> str:
    """
    Get fallback response when AI services are unavailable.
    
    Args:
        lead_status: Current lead status
    
    Returns:
        Safe fallback response text
    """
    fallback_responses = {
        "new": "Thank you for reaching out! A member of our team will get back to you shortly.",
        "contacted": "Thanks for your message. We'll review your information and follow up soon.",
        "qualified": "Thank you for the additional details. Our team will be in touch.",
        "disqualified": "Thank you for your time.",
        "default": "We've received your message and will respond shortly.",
    }
    
    return fallback_responses.get(lead_status, fallback_responses["default"])


async def _generate_lead_summary(
    lead_id: UUID,
    db: AsyncSession,
    llm_client: LLMClient,
):
    """
    Background task to generate AI summary of lead.
    
    Args:
        lead_id: Lead identifier
        db: Database session
        llm_client: LLM client instance
    """
    try:
        # Get lead
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            return
        
        # Get conversation history
        history = await _get_conversation_history(db, lead_id, limit=50)
        if len(history) < 3:  # Need at least 3 messages for summary
            return
        
        # Get latest extraction
        extracted_data = lead.enriched_data.get("last_ai_extraction") if lead.enriched_data else None
        if not extracted_data:
            return
        
        # Generate summary
        summary = await llm_client.summarize_lead(
            conversation_history=history,
            extracted_data=extracted_data,
        )
        
        # Save to lead
        if not lead.enriched_data:
            lead.enriched_data = {}
        lead.enriched_data["ai_summary"] = summary
        lead.enriched_data["ai_summary_generated_at"] = lead.updated_at.isoformat()
        
        await db.commit()
        logger.info(f"Generated AI summary for lead {lead_id}")
        
    except Exception as e:
        logger.error(f"Failed to generate lead summary: {str(e)}", exc_info=True)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conversation with AI processing"
)
async def create_conversation(
    conversation_data: ConversationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm_client: LLMClient = Depends(get_llm_client),
    rate_limiter: TokenBucketRateLimiter = Depends(get_rate_limiter),
):
    """
    Create a new conversation record.
    
    For inbound messages:
    - Extracts structured data using AI
    - Updates lead information
    - Generates AI response (optional)
    - Triggers background summarization
    
    Rate limits apply per organization.
    """
    
    # ========================================================================
    # STEP 1: Rate Limiting (for AI operations)
    # ========================================================================
    
    if conversation_data.direction == "inbound":
        org_id = str(current_user.organization_id)
        allowed, retry_after = await rate_limiter.check_rate_limit(
            org_id=org_id,
            operation="conversation_ai",
        )
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for org {org_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"AI rate limit exceeded. Retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )
    
    # ========================================================================
    # STEP 2: Verify Lead Access
    # ========================================================================
    
    result = await db.execute(
        select(Lead).where(
            Lead.id == conversation_data.lead_id,
            Lead.organization_id == current_user.organization_id
        )
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # ========================================================================
    # STEP 3: Create Conversation Record
    # ========================================================================
    
    conversation = Conversation(
        lead_id=conversation_data.lead_id,
        channel=conversation_data.channel,
        direction=conversation_data.direction,
        from_number=conversation_data.from_number,
        to_number=conversation_data.to_number,
        message_body=conversation_data.message_body,
        status=conversation_data.status or "delivered",
        external_id=conversation_data.external_id,
        metadata=conversation_data.metadata or {},
    )
    
    # ========================================================================
    # STEP 4: AI Processing (for inbound messages only)
    # ========================================================================
    
    ai_response_text = None
    
    if conversation_data.direction == "inbound" and conversation_data.message_body:
        try:
            # Get conversation history
            history = await _get_conversation_history(
                db,
                conversation_data.lead_id,
                limit=10
            )
            
            # ================================================================
            # 4A: Extract Structured Data
            # ================================================================
            
            logger.info(f"Extracting data from inbound message for lead {lead.id}")
            
            extraction_result = await llm_client.extract_lead_info(
                message=conversation_data.message_body,
                sender=conversation_data.from_number or "unknown",
                conversation_history=history,
                lead_id=str(lead.id),
            )
            
            # Store extraction in conversation
            conversation.extracted_data = extraction_result.data
            conversation.metadata["ai_provider"] = extraction_result.llm_response.provider.value
            conversation.metadata["ai_latency_ms"] = extraction_result.llm_response.latency_ms
            conversation.metadata["ai_validated"] = extraction_result.validated
            
            if not extraction_result.validated:
                conversation.metadata["ai_validation_errors"] = extraction_result.validation_errors
                logger.warning(
                    f"Extraction validation failed for lead {lead.id}: "
                    f"{extraction_result.validation_errors}"
                )
            
            # Record metrics
            metrics_collector.record_llm_request(
                provider=extraction_result.llm_response.provider.value,
                operation="extraction",
                status="success",
                latency_seconds=extraction_result.llm_response.latency_ms / 1000,
                prompt_tokens=extraction_result.llm_response.prompt_tokens,
                completion_tokens=extraction_result.llm_response.completion_tokens,
            )
            
            # Update lead with extracted information
            if extraction_result.validated:
                await _update_lead_from_extraction(db, lead, extraction_result.data)
            
            # ================================================================
            # 4B: Generate AI Response (optional - you can disable this)
            # ================================================================
            
            try:
                info_summary = _build_info_summary(lead, extraction_result.data)
                
                response_result = await llm_client.generate_response(
                    message=conversation_data.message_body,
                    lead_stage=lead.status,
                    info_summary=info_summary,
                    conversation_history=history,
                )
                
                ai_response_text = response_result.content
                conversation.metadata["ai_response_generated"] = True
                conversation.metadata["ai_response_provider"] = response_result.provider.value
                
                # Record metrics
                metrics_collector.record_llm_request(
                    provider=response_result.provider.value,
                    operation="response_generation",
                    status="success",
                    latency_seconds=response_result.latency_ms / 1000,
                    prompt_tokens=response_result.prompt_tokens,
                    completion_tokens=response_result.completion_tokens,
                )
                
                logger.info(f"Generated AI response for lead {lead.id}")
                
            except AllProvidersFailedError as e:
                logger.error(f"AI response generation failed: {str(e)}")
                ai_response_text = _get_fallback_response(lead.status)
                conversation.metadata["ai_response_fallback"] = True
            
            # Record usage
            await rate_limiter.record_request(
                org_id=org_id,
                operation="conversation_ai",
                tokens_used=(
                    extraction_result.llm_response.prompt_tokens +
                    extraction_result.llm_response.completion_tokens
                ),
            )
            
        except AllProvidersFailedError as e:
            # All AI providers failed - log but don't fail the request
            logger.error(f"AI extraction failed for lead {lead.id}: {str(e)}")
            conversation.metadata["ai_extraction_failed"] = True
            conversation.metadata["ai_error"] = str(e)
            ai_response_text = _get_fallback_response(lead.status)
            
        except Exception as e:
            # Unexpected error - log but don't fail
            logger.error(
                f"Unexpected error in AI processing for lead {lead.id}: {str(e)}",
                exc_info=True
            )
            conversation.metadata["ai_error"] = str(e)
    
    # ========================================================================
    # STEP 5: Save Conversation
    # ========================================================================
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    logger.info(
        f"Created conversation {conversation.id} for lead {lead.id} "
        f"(direction={conversation.direction}, channel={conversation.channel})"
    )
    
    # ========================================================================
    # STEP 6: Background Tasks
    # ========================================================================
    
    # Trigger lead summarization after multiple messages
    if conversation.extracted_data:
        # Count total conversations
        count_result = await db.execute(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.lead_id == lead.id)
        )
        total_conversations = count_result.scalar() or 0
        
        # Generate summary after 3+ messages
        if total_conversations >= 3:
            background_tasks.add_task(
                _generate_lead_summary,
                lead_id=lead.id,
                db=db,
                llm_client=llm_client,
            )
    
    # TODO: Trigger re-scoring task if data was extracted
    # from app.tasks.celery_app import score_lead_task
    # if conversation.extracted_data:
    #     score_lead_task.delay(str(lead.id))
    
    # ========================================================================
    # STEP 7: Return Response
    # ========================================================================
    
    # Add AI response to metadata for client
    if ai_response_text:
        conversation.metadata["suggested_response"] = ai_response_text
    
    return conversation


@router.get(
    "/lead/{lead_id}",
    response_model=ConversationListResponse,
    summary="Get conversations for a lead"
)
async def get_lead_conversations(
    lead_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all conversations for a specific lead.
    
    Returns conversations in chronological order with extracted data.
    """
    # Verify lead access
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
    
    # Get conversations
    query = (
        select(Conversation)
        .where(Conversation.lead_id == lead_id)
        .order_by(Conversation.created_at.asc())
    )
    
    # Get total count
    count_query = select(func.count()).select_from(Conversation).where(
        Conversation.lead_id == lead_id
    )
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations],
        total=total or 0,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get specific conversation"
)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific conversation by ID.
    
    Includes extracted data and AI metadata.
    """
    result = await db.execute(
        select(Conversation)
        .join(Lead)
        .where(
            Conversation.id == conversation_id,
            Lead.organization_id == current_user.organization_id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation

@router.post(
    "/{lead_id}/message",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message in conversation"
)
async def send_message(
    lead_id: UUID,
    message_data: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),  # Allow public access
    llm_client: LLMClient = Depends(get_llm_client),
    rate_limiter: TokenBucketRateLimiter = Depends(get_rate_limiter),
):
    """
    Send a message in an existing conversation.
    
    For public users (chat widget):
    - No authentication required
    - Uses lead_id from URL
    
    For authenticated users (admin):
    - Can send on behalf of lead
    
    Returns both user message and AI-generated bot response.
    """
    
    # Determine organization ID (same logic as create_lead)
    if current_user:
        organization_id = current_user.organization_id
        is_authenticated = True
    else:
        if not settings.DEFAULT_ORGANIZATION_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Public messaging is not configured"
            )
        try:
            organization_id = UUID(settings.DEFAULT_ORGANIZATION_ID)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System configuration error"
            )
        is_authenticated = False
    
    # ========================================================================
    # STEP 1: Verify Lead Exists and Access
    # ========================================================================
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.organization_id == organization_id
        )
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # ========================================================================
    # STEP 2: Rate Limiting (for public users)
    # ========================================================================
    org_id = str(organization_id)
    
    if not is_authenticated:
        try:
            allowed, retry_after = await rate_limiter.check_rate_limit(
                org_id=org_id,
                operation="chat_message",
            )
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for lead {lead_id}")
                # Don't block, just disable AI
                use_ai = False
            else:
                use_ai = True
        except Exception as e:
            # Redis connection error - continue without rate limiting
            logger.warning(f"Rate limit check failed: {e}")
            use_ai = True
    else:
        use_ai = True  # Admins always get AI
    
    # ========================================================================
    # STEP 3: Get Conversation History
    # ========================================================================
    history_result = await db.execute(
        select(Conversation)
        .where(Conversation.lead_id == lead_id)
        .order_by(Conversation.created_at.desc())
        .limit(10)
    )
    conversations = history_result.scalars().all()
    
    # Build history for AI (newest first, so reverse)
    history = [
        {
            "role": "user" if conv.direction == "inbound" else "assistant",
            "content": conv.message_body,
            "timestamp": conv.created_at.isoformat(),
        }
        for conv in reversed(conversations)
    ]
    
    # ========================================================================
    # STEP 4: Create User Message Record
    # ========================================================================
    user_conversation = Conversation(
        lead_id=lead_id,
        channel="chat",
        direction="inbound",
        message_body=message_data.content,
        status="received",
        metadata={
            "is_authenticated": is_authenticated,
            "has_attachments": bool(message_data.attachments),
        },
    )
    db.add(user_conversation)
    await db.flush()  # Get ID
    
    # ========================================================================
    # STEP 5: AI Processing (Extract Info & Generate Response)
    # ========================================================================
    extracted_data = None
    ai_response_text = None

    if use_ai:
        try:
            # ================================================================
            # 5A: Extract structured data
            # ================================================================
            extraction_result = await llm_client.extract_lead_info(
                message=message_data.content,
                sender="chat_user",
                conversation_history=history,
                lead_id=str(lead_id),
            )
            
            extracted_data = extraction_result.data
            user_conversation.extracted_data = extracted_data
            
            # Update lead with extracted info
            if extraction_result.validated:
                contact = extracted_data.get("contact", {})
                if contact.get("name") and not lead.name:
                    lead.name = contact["name"]
                if contact.get("phone") and not lead.phone:
                    lead.phone = contact["phone"]
                if contact.get("email") and not lead.email:
                    lead.email = contact["email"]
                
                # Update enriched_data
                if not lead.enriched_data:
                    lead.enriched_data = {}
                lead.enriched_data["latest_extraction"] = extracted_data
                lead.enriched_data["extraction_timestamp"] = datetime.utcnow().isoformat()
            
            # Check for escalation signals in extraction notes
            metadata = extracted_data.get("metadata", {})
            extraction_notes = metadata.get("extraction_notes", "")
            if any(signal in extraction_notes for signal in [
                "PAYMENT_TERMS_PROPOSED",
                "NEGOTIATION_REQUESTED", 
                "LEGAL_QUESTION",
                "DISTRESS_SIGNAL"
            ]):
                logger.info(f"Escalation signal detected in extraction: {extraction_notes}")
                user_conversation.metadata["escalation_signal"] = extraction_notes
            
            # ================================================================
            # 5B: Generate AI response (with smart context)
            # ================================================================
            response_result = await llm_client.generate_response(
                message=message_data.content,
                lead_stage=lead.stage,
                info_summary="",  # Will be built by generate_response
                conversation_history=history,
                extracted_data=extracted_data,  # ✅ NOW PASSING EXTRACTED DATA
            )
            
            ai_response_text = response_result.content
            
            # Check if response triggered escalation
            if response_result.metadata and response_result.metadata.get("requires_human"):
                escalation_type = response_result.metadata.get("escalation_type")
                
                # Mark lead for human review
                lead.stage = "awaiting_human_clarification"
                
                # Add escalation metadata
                if not lead.enriched_data:
                    lead.enriched_data = {}
                lead.enriched_data["escalation"] = {
                    "type": escalation_type,
                    "triggered_at": datetime.utcnow().isoformat(),
                    "message": message_data.content[:200],
                }
                
                logger.info(
                    f"Escalation triggered for lead {lead_id}: {escalation_type}"
                )
                
                # TODO: Create notification/task for agent
                # await create_escalation_task(
                #     lead_id=lead_id,
                #     escalation_type=escalation_type,
                #     message=message_data.content
                # )
            
            logger.info(f"AI processing successful for lead: {lead_id}")
            
        except Exception as e:
            logger.error(f"AI processing failed: {str(e)}")
            # Fallback response
            ai_response_text = (
                "Thank you for your message! Could you share the property address "
                "so I can help you better?"
            )
            user_conversation.metadata["ai_fallback"] = True
            user_conversation.metadata["ai_error"] = str(e)
    else:
        # No AI - simple response
        ai_response_text = "Thank you for your message! A team member will respond shortly."
        user_conversation.metadata["ai_disabled"] = True
    
    # ========================================================================
    # STEP 6: Create Bot Response Record
    # ========================================================================
    bot_conversation = Conversation(
        lead_id=lead_id,
        channel="chat",
        direction="outbound",
        message_body=ai_response_text,
        status="sent",
        metadata={
            "auto_generated": True,
            "is_authenticated": is_authenticated,
        },
    )
    db.add(bot_conversation)
    
    # ========================================================================
    # STEP 7: Commit Everything
    # ========================================================================
    await db.commit()
    await db.refresh(user_conversation)
    await db.refresh(bot_conversation)
    await db.refresh(lead)
    
    logger.info(
        f"Message sent for lead {lead_id}: user_msg={user_conversation.id}, "
        f"bot_msg={bot_conversation.id}"
    )
    
    # ========================================================================
    # STEP 8: Return Response
    # ========================================================================
    return SendMessageResponse(
        user_message=MessageResponse(
            id=str(user_conversation.id),
            role="user",
            content=user_conversation.message_body,
            timestamp=user_conversation.created_at.isoformat(),
            metadata={
                "extracted_fields": extracted_data if extracted_data else None,
            },
        ),
        bot_message=MessageResponse(
            id=str(bot_conversation.id),
            role="assistant",
            content=bot_conversation.message_body,
            timestamp=bot_conversation.created_at.isoformat(),
        ),
        extracted_data={
            "seller_info": {
                "name": lead.name,
                "email": lead.email,
                "phone": lead.phone,
            } if any([lead.name, lead.email, lead.phone]) else None,
        },
    )

@router.post(
    "/{conversation_id}/messages",  # ← PLURAL to match frontend
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message using conversation ID"
)
async def send_message_by_conversation_id(
    conversation_id: UUID,
    message_data: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    llm_client: LLMClient = Depends(get_llm_client),
    rate_limiter: TokenBucketRateLimiter = Depends(get_rate_limiter),
):
    """
    Send a message using conversation ID (frontend compatibility).
    
    This endpoint looks up the lead_id from the conversation_id,
    then delegates to the main send_message logic.
    """
    
    # Look up the lead_id from conversation_id
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get the lead_id
    lead_id = conversation.lead_id
    
    # Call the existing send_message function
    return await send_message(
        lead_id=lead_id,
        message_data=message_data,
        background_tasks=background_tasks,
        db=db,
        current_user=current_user,
        llm_client=llm_client,
        rate_limiter=rate_limiter,
    )

@router.get(
    "/health/ai",
    summary="Get AI services health"
)
async def get_ai_health(
    llm_client: LLMClient = Depends(get_llm_client),
    rate_limiter: TokenBucketRateLimiter = Depends(get_rate_limiter),
    current_user: User = Depends(get_current_user),
):
    """
    Get AI services health status.
    
    Shows:
    - Provider health (circuit breaker states)
    - Rate limit usage
    - Overall system status
    """
    org_id = str(current_user.organization_id)
    
    # Get provider health
    provider_health = llm_client.get_provider_health()
    
    # Get rate limit usage
    current_usage = await rate_limiter.get_current_usage(
        org_id=org_id,
        operation="conversation_ai",
    )
    
    # Determine overall status
    healthy_providers = [
        p for p, status in provider_health.items()
        if status == "healthy"
    ]
    
    overall_status = "healthy" if len(healthy_providers) >= 2 else "degraded"
    if not healthy_providers:
        overall_status = "unavailable"
    
    return {
        "status": overall_status,
        "providers": provider_health,
        "rate_limits": current_usage,
        "healthy_provider_count": len(healthy_providers),
    }