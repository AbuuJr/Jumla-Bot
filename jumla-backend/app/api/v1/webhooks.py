"""
app/api/v1/webhooks.py
Webhook receivers for Twilio and SendGrid with AI integration
"""
from fastapi import APIRouter, Depends, Request, HTTPException, status, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import hmac
import hashlib
import logging

from app.core.database import get_db
from app.dependencies import get_llm_client, get_rate_limiter
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.organization import Organization
from app.services.llm.client import LLMClient, AllProvidersFailedError
from app.services.rate_limiter import TokenBucketRateLimiter
from app.core.metrics import metrics_collector
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def verify_twilio_signature(signature: str, url: str, params: dict) -> bool:
    """
    Verify Twilio request signature for security.
    
    Args:
        signature: X-Twilio-Signature header value
        url: Full request URL
        params: Form parameters
    
    Returns:
        True if signature is valid
    """
    if not settings.TWILIO_WEBHOOK_SECRET:
        logger.warning("Twilio webhook secret not configured - skipping verification")
        return True
    
    # Build signature string
    data = url
    for key in sorted(params.keys()):
        data += key + params[key]
    
    # Compute signature
    expected_signature = hmac.new(
        settings.TWILIO_WEBHOOK_SECRET.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha1
    ).digest()
    
    import base64
    expected_signature_b64 = base64.b64encode(expected_signature).decode()
    
    return hmac.compare_digest(signature, expected_signature_b64)


async def get_organization_by_phone(db: AsyncSession, phone_number: str) -> Optional[Organization]:
    """
    Get organization by their Twilio phone number.
    
    Args:
        db: Database session
        phone_number: Phone number to lookup
    
    Returns:
        Organization or None
    """
    result = await db.execute(
        select(Organization).where(
            Organization.metadata['twilio_phone_number'].astext == phone_number
        )
    )
    return result.scalar_one_or_none()


async def _get_conversation_history(
    db: AsyncSession,
    lead_id,
    limit: int = 10,
) -> list[dict]:
    """Get recent conversation history for AI context"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.lead_id == lead_id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()
    
    return [
        {
            "role": "user" if conv.direction == "inbound" else "assistant",
            "content": conv.message_body,
            "timestamp": conv.created_at.isoformat(),
        }
        for conv in reversed(history)
        if conv.message_body
    ]


def _build_info_summary(lead: Lead) -> str:
    """Build info summary for AI context"""
    parts = []
    
    if lead.name:
        parts.append(f"Name: {lead.name}")
    if lead.phone:
        parts.append(f"Phone: {lead.phone}")
    
    if lead.enriched_data:
        if lead.enriched_data.get("property_address"):
            parts.append(f"Property: {lead.enriched_data['property_address']}")
        if lead.enriched_data.get("situation_motivation"):
            parts.append(f"Motivation: {lead.enriched_data['situation_motivation']}")
    
    return "; ".join(parts) if parts else "New contact"


def _get_fallback_response() -> str:
    """Fallback response when AI is unavailable"""
    return (
        "Thank you for your message! We've received your information and "
        "a member of our team will get back to you shortly."
    )


async def _update_lead_from_extraction(
    db: AsyncSession,
    lead: Lead,
    extracted_data: dict,
):
    """Update lead with extracted data"""
    try:
        contact = extracted_data.get("contact", {})
        if contact.get("name") and not lead.name:
            lead.name = contact["name"]
        if contact.get("email") and not lead.email:
            lead.email = contact["email"]
        
        property_data = extracted_data.get("property", {})
        situation = extracted_data.get("situation", {})
        
        if not lead.enriched_data:
            lead.enriched_data = {}
        
        for key, value in property_data.items():
            if value is not None:
                lead.enriched_data[f"property_{key}"] = value
        
        for key, value in situation.items():
            if value is not None:
                lead.enriched_data[f"situation_{key}"] = value
        
        intent = extracted_data.get("intent", {})
        if intent.get("classification") == "qualified_lead" and lead.status == "new":
            lead.status = "contacted"
        
        lead.enriched_data["last_ai_extraction"] = extracted_data
        
        await db.commit()
        logger.info(f"Updated lead {lead.id} from webhook extraction")
        
    except Exception as e:
        logger.error(f"Failed to update lead: {str(e)}")
        await db.rollback()


async def _send_sms_response(
    from_number: str,
    to_number: str,
    message: str,
) -> bool:
    """
    Send SMS response via Twilio.
    
    Args:
        from_number: Our Twilio number
        to_number: Recipient number
        message: Message text
    
    Returns:
        True if sent successfully
    """
    try:
        # TODO: Implement actual Twilio sending
        # from app.services.twilio_adapter import twilio_adapter
        # result = await twilio_adapter.send_sms(
        #     from_=from_number,
        #     to=to_number,
        #     body=message,
        # )
        # return result.success
        
        logger.info(f"Would send SMS to {to_number}: {message[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        return False


async def _generate_lead_summary_background(
    lead_id,
    db: AsyncSession,
    llm_client: LLMClient,
):
    """Background task to generate AI summary"""
    try:
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            return
        
        history = await _get_conversation_history(db, lead_id, limit=50)
        if len(history) < 3:
            return
        
        extracted_data = lead.enriched_data.get("last_ai_extraction") if lead.enriched_data else None
        if not extracted_data:
            return
        
        summary = await llm_client.summarize_lead(
            conversation_history=history,
            extracted_data=extracted_data,
        )
        
        if not lead.enriched_data:
            lead.enriched_data = {}
        lead.enriched_data["ai_summary"] = summary
        
        await db.commit()
        logger.info(f"Generated summary for lead {lead_id}")
        
    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}", exc_info=True)


# ============================================================================
# TWILIO WEBHOOK
# ============================================================================

@router.post(
    "/twilio",
    summary="Twilio SMS webhook",
    description="Receives inbound SMS, processes with AI, and sends automated responses"
)
async def twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    NumMedia: str = Form(default="0"),
    db: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
    rate_limiter: TokenBucketRateLimiter = Depends(get_rate_limiter),
):
    """
    Twilio SMS webhook receiver.
    
    Flow:
    1. Verify Twilio signature
    2. Find/create lead
    3. Check rate limits
    4. Extract structured data with AI
    5. Generate AI response
    6. Send response via Twilio
    7. Save all records
    8. Trigger background tasks
    
    Returns TwiML response (empty for now).
    """
    
    logger.info(f"Received SMS from {From} to {To}: {Body[:50]}...")
    
    # ========================================================================
    # STEP 1: Verify Twilio Signature
    # ========================================================================
    
    if settings.TWILIO_WEBHOOK_SECRET:
        signature = request.headers.get("X-Twilio-Signature", "")
        form_data = await request.form()
        
        if not verify_twilio_signature(signature, str(request.url), dict(form_data)):
            logger.error(f"Invalid Twilio signature from {From}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature"
            )
    
    # ========================================================================
    # STEP 2: Determine Organization
    # ========================================================================
    
    organization = await get_organization_by_phone(db, To)
    
    if not organization:
        logger.error(f"No organization found for Twilio number {To}")
        # Use default organization or create one
        result = await db.execute(select(Organization).limit(1))
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No organization configured"
            )
    
    org_id = str(organization.id)
    logger.info(f"Processing SMS for organization {org_id}")
    
    # ========================================================================
    # STEP 3: Rate Limiting
    # ========================================================================
    
    allowed, retry_after = await rate_limiter.check_rate_limit(
        org_id=org_id,
        operation="webhook_sms",
    )
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for org {org_id}")
        # Still process but don't use AI
        metrics_collector.record_rate_limit_exceeded(org_id, "webhook_sms")
        use_ai = False
    else:
        use_ai = True
    
    # ========================================================================
    # STEP 4: Find or Create Lead
    # ========================================================================
    
    result = await db.execute(
        select(Lead).where(
            Lead.phone == From,
            Lead.organization_id == organization.id
        )
    )
    lead = result.scalar_one_or_none()
    
    if not lead:
        logger.info(f"Creating new lead from inbound SMS: {From}")
        lead = Lead(
            phone=From,
            organization_id=organization.id,
            source="sms_inbound",
            status="new",
            enriched_data={},
        )
        db.add(lead)
        await db.flush()  # Get lead.id
    
    # ========================================================================
    # STEP 5: Create Inbound Conversation Record
    # ========================================================================
    
    conversation = Conversation(
        lead_id=lead.id,
        channel="sms",
        direction="inbound",
        from_number=From,
        to_number=To,
        message_body=Body,
        external_id=MessageSid,
        status="received",
        metadata={
            "num_media": NumMedia,
            "ai_enabled": use_ai,
        }
    )
    
    # ========================================================================
    # STEP 6: AI Processing (if rate limit allows)
    # ========================================================================
    
    ai_response_text = None
    
    if use_ai:
        try:
            # Get conversation history
            history = await _get_conversation_history(db, lead.id, limit=10)
            
            # ================================================================
            # 6A: Extract Structured Data
            # ================================================================
            
            logger.info(f"Extracting data from SMS for lead {lead.id}")
            
            extraction_result = await llm_client.extract_lead_info(
                message=Body,
                sender=From,
                conversation_history=history,
                lead_id=str(lead.id),
            )
            
            # Store extraction
            conversation.extracted_data = extraction_result.data
            conversation.metadata["ai_provider"] = extraction_result.llm_response.provider.value
            conversation.metadata["ai_latency_ms"] = extraction_result.llm_response.latency_ms
            conversation.metadata["ai_validated"] = extraction_result.validated
            
            if not extraction_result.validated:
                logger.warning(
                    f"Extraction validation failed: {extraction_result.validation_errors}"
                )
                conversation.metadata["ai_validation_errors"] = extraction_result.validation_errors
            
            # Record metrics
            metrics_collector.record_llm_request(
                provider=extraction_result.llm_response.provider.value,
                operation="webhook_extraction",
                status="success",
                latency_seconds=extraction_result.llm_response.latency_ms / 1000,
                prompt_tokens=extraction_result.llm_response.prompt_tokens,
                completion_tokens=extraction_result.llm_response.completion_tokens,
            )
            
            # Update lead
            if extraction_result.validated:
                await _update_lead_from_extraction(db, lead, extraction_result.data)
            
            # ================================================================
            # 6B: Generate AI Response
            # ================================================================
            
            logger.info(f"Generating AI response for lead {lead.id}")
            
            info_summary = _build_info_summary(lead)
            
            response_result = await llm_client.generate_response(
                message=Body,
                lead_status=lead.status,
                info_summary=info_summary,
                conversation_history=history,
            )
            
            ai_response_text = response_result.content
            conversation.metadata["ai_response_generated"] = True
            conversation.metadata["ai_response_provider"] = response_result.provider.value
            
            # Record metrics
            metrics_collector.record_llm_request(
                provider=response_result.provider.value,
                operation="webhook_response",
                status="success",
                latency_seconds=response_result.latency_ms / 1000,
                prompt_tokens=response_result.prompt_tokens,
                completion_tokens=response_result.completion_tokens,
            )
            
            # Record usage
            await rate_limiter.record_request(
                org_id=org_id,
                operation="webhook_sms",
                tokens_used=(
                    extraction_result.llm_response.prompt_tokens +
                    extraction_result.llm_response.completion_tokens +
                    response_result.prompt_tokens +
                    response_result.completion_tokens
                ),
            )
            
            logger.info(f"AI processing complete for lead {lead.id}")
            
        except AllProvidersFailedError as e:
            logger.error(f"All AI providers failed for webhook: {str(e)}")
            conversation.metadata["ai_error"] = str(e)
            ai_response_text = _get_fallback_response()
            conversation.metadata["ai_response_fallback"] = True
            
        except Exception as e:
            logger.error(
                f"Unexpected error in AI processing: {str(e)}",
                exc_info=True
            )
            conversation.metadata["ai_error"] = str(e)
            ai_response_text = _get_fallback_response()
            conversation.metadata["ai_response_fallback"] = True
    
    else:
        # Rate limited - use fallback
        ai_response_text = _get_fallback_response()
        conversation.metadata["rate_limited"] = True
    
    # ========================================================================
    # STEP 7: Save Inbound Conversation
    # ========================================================================
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    logger.info(f"Saved inbound conversation {conversation.id}")
    
    # ========================================================================
    # STEP 8: Send SMS Response
    # ========================================================================
    
    if ai_response_text:
        # Send via Twilio
        sms_sent = await _send_sms_response(
            from_number=To,
            to_number=From,
            message=ai_response_text,
        )
        
        if sms_sent:
            # Create outbound conversation record
            outbound = Conversation(
                lead_id=lead.id,
                channel="sms",
                direction="outbound",
                from_number=To,
                to_number=From,
                message_body=ai_response_text,
                status="sent",
                metadata={"auto_generated": True}
            )
            db.add(outbound)
            await db.commit()
            
            logger.info(f"Sent AI response to {From}")
        else:
            logger.error(f"Failed to send SMS response to {From}")
    
    # ========================================================================
    # STEP 9: Background Tasks
    # ========================================================================
    
    # Generate lead summary
    if conversation.extracted_data:
        count_result = await db.execute(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.lead_id == lead.id)
        )
        total_conversations = count_result.scalar() or 0
        
        if total_conversations >= 3:
            background_tasks.add_task(
                _generate_lead_summary_background,
                lead_id=lead.id,
                db=db,
                llm_client=llm_client,
            )
    
    # Trigger lead scoring
    # TODO: Implement Celery task
    # from app.tasks.celery_app import score_lead_task
    # if conversation.extracted_data:
    #     score_lead_task.delay(str(lead.id))
    
    # ========================================================================
    # STEP 10: Return TwiML Response
    # ========================================================================
    
    # Return empty TwiML (we already sent response above)
    # If you want Twilio to send the response, return TwiML with <Message>
    
    return {"status": "processed", "lead_id": str(lead.id)}


# ============================================================================
# SENDGRID WEBHOOK
# ============================================================================

@router.post(
    "/sendgrid",
    summary="SendGrid email events webhook"
)
async def sendgrid_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    SendGrid email event webhook.
    
    Handles email delivery events:
    - delivered
    - bounced
    - opened
    - clicked
    - spam_report
    - unsubscribe
    
    Updates conversation status based on event type.
    """
    events = await request.json()
    
    logger.info(f"Received {len(events)} SendGrid events")
    
    processed_count = 0
    
    for event in events:
        try:
            event_type = event.get("event")
            email = event.get("email")
            message_id = event.get("sg_message_id")
            
            if not message_id:
                continue
            
            # Find conversation by external_id
            result = await db.execute(
                select(Conversation).where(
                    Conversation.external_id == message_id
                )
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                logger.warning(f"Conversation not found for message {message_id}")
                continue
            
            # Update status based on event
            status_map = {
                "delivered": "delivered",
                "bounce": "failed",
                "dropped": "failed",
                "deferred": "pending",
                "processed": "sent",
            }
            
            new_status = status_map.get(event_type)
            if new_status:
                conversation.status = new_status
                
                if not conversation.metadata:
                    conversation.metadata = {}
                conversation.metadata[f"sendgrid_{event_type}"] = event
                
                processed_count += 1
            
            # Track engagement events
            if event_type in ["open", "click"]:
                if not conversation.metadata:
                    conversation.metadata = {}
                if "engagement" not in conversation.metadata:
                    conversation.metadata["engagement"] = []
                
                conversation.metadata["engagement"].append({
                    "type": event_type,
                    "timestamp": event.get("timestamp"),
                    "url": event.get("url") if event_type == "click" else None,
                })
                
                processed_count += 1
            
        except Exception as e:
            logger.error(f"Failed to process SendGrid event: {str(e)}")
            continue
    
    if processed_count > 0:
        await db.commit()
    
    logger.info(f"Processed {processed_count}/{len(events)} SendGrid events")
    
    return {
        "status": "processed",
        "events_received": len(events),
        "events_processed": processed_count,
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    summary="Webhook health check"
)
async def webhook_health():
    """
    Health check endpoint for webhook services.
    
    Returns status of:
    - Twilio configuration
    - SendGrid configuration
    - Database connectivity
    """
    health = {
        "status": "healthy",
        "webhooks": {
            "twilio": {
                "configured": bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN),
                "phone_number": settings.TWILIO_PHONE_NUMBER if settings.TWILIO_PHONE_NUMBER else None,
                "signature_verification": bool(settings.TWILIO_WEBHOOK_SECRET),
            },
            "sendgrid": {
                "configured": bool(settings.SENDGRID_API_KEY),
                "from_email": settings.SENDGRID_FROM_EMAIL if settings.SENDGRID_FROM_EMAIL else None,
            }
        }
    }
    
    return health
