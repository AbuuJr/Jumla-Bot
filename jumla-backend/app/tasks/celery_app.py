"""
app/tasks/celery_app.py and task definitions
Celery configuration and background task implementations
"""
from celery import Celery
from celery.utils.log import get_task_logger
from typing import Dict, Any
from uuid import UUID
import asyncio

from app.config import settings

logger = get_task_logger(__name__)

# Create Celery app
celery_app = Celery(
    "jumla-bot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


# Helper to run async functions in Celery
def run_async(coro):
    """Run async coroutine in sync Celery task"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ========== app/tasks/enrichment_tasks.py ==========
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def enrich_lead_task(self, lead_id: str):
    """
    Enrich lead with external data sources
    
    Idempotency: Uses lead_id as unique identifier.
    Safe to retry - will update existing enrichment data.
    """
    from app.services.enrichment_service import enrichment_service
    from app.core.database import get_db_context
    from app.models.lead import Lead
    from sqlalchemy import select
    
    try:
        logger.info(f"Starting enrichment for lead {lead_id}")
        
        async def do_enrichment():
            async with get_db_context() as db:
                # Fetch lead
                result = await db.execute(
                    select(Lead).where(Lead.id == UUID(lead_id))
                )
                lead = result.scalar_one_or_none()
                
                if not lead:
                    raise ValueError(f"Lead {lead_id} not found")
                
                # Enrich property data
                enriched_data = await enrichment_service.enrich_property(
                    address=lead.enriched_data.get("property_address"),
                    city=lead.enriched_data.get("city"),
                    state=lead.enriched_data.get("state"),
                    zip_code=lead.enriched_data.get("zip"),
                )
                
                # Update lead
                lead.enriched_data.update(enriched_data)
                await db.commit()
                
                logger.info(f"Successfully enriched lead {lead_id}")
                return enriched_data
        
        return run_async(do_enrichment())
    
    except Exception as exc:
        logger.error(f"Enrichment failed for lead {lead_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def score_lead_task(self, lead_id: str):
    """
    Calculate and update lead score
    
    Idempotency: Overwrites existing score with new calculation.
    """
    from app.services.scoring_engine import scoring_engine
    from app.core.database import get_db_context
    from app.models.lead import Lead
    from app.models.lead_score import LeadScore
    from app.models.conversation import Conversation
    from sqlalchemy import select
    
    try:
        logger.info(f"Scoring lead {lead_id}")
        
        async def do_scoring():
            async with get_db_context() as db:
                # Fetch lead and conversations
                lead_result = await db.execute(
                    select(Lead).where(Lead.id == UUID(lead_id))
                )
                lead = lead_result.scalar_one_or_none()
                
                if not lead:
                    raise ValueError(f"Lead {lead_id} not found")
                
                conv_result = await db.execute(
                    select(Conversation).where(Conversation.lead_id == UUID(lead_id))
                )
                conversations = conv_result.scalars().all()
                
                # Calculate score
                score_breakdown = scoring_engine.score_lead(
                    lead=lead,
                    conversations=conversations,
                    property_data=lead.enriched_data
                )
                
                # Update or create score record
                score_result = await db.execute(
                    select(LeadScore).where(LeadScore.lead_id == UUID(lead_id))
                )
                score_record = score_result.scalar_one_or_none()
                
                if score_record:
                    score_record.total_score = score_breakdown.total_score
                    score_record.urgency_score = score_breakdown.urgency_score
                    score_record.motivation_score = score_breakdown.motivation_score
                    score_record.property_score = score_breakdown.property_score
                    score_record.response_score = score_breakdown.response_score
                    score_record.financial_score = score_breakdown.financial_score
                    score_record.factors = score_breakdown.factors
                else:
                    score_record = LeadScore(
                        lead_id=UUID(lead_id),
                        total_score=score_breakdown.total_score,
                        urgency_score=score_breakdown.urgency_score,
                        motivation_score=score_breakdown.motivation_score,
                        property_score=score_breakdown.property_score,
                        response_score=score_breakdown.response_score,
                        financial_score=score_breakdown.financial_score,
                        factors=score_breakdown.factors,
                    )
                    db.add(score_record)
                
                # Update lead temperature
                lead.temperature = score_breakdown.temperature.value
                
                await db.commit()
                logger.info(f"Scored lead {lead_id}: {score_breakdown.total_score} ({score_breakdown.temperature})")
                
                return {
                    "score": float(score_breakdown.total_score),
                    "temperature": score_breakdown.temperature.value
                }
        
        return run_async(do_scoring())
    
    except Exception as exc:
        logger.error(f"Scoring failed for lead {lead_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True)
def send_followup_task(self, lead_id: str, message: str, channel: str = "sms"):
    """
    Send automated followup message
    
    Idempotency: Should be called with unique followup_log_id to prevent duplicates.
    """
    from app.services.twilio_adapter import twilio_adapter
    from app.services.sendgrid_adapter import sendgrid_adapter
    from app.core.database import get_db_context
    from app.models.lead import Lead
    from sqlalchemy import select
    
    try:
        logger.info(f"Sending followup to lead {lead_id} via {channel}")
        
        async def do_send():
            async with get_db_context() as db:
                result = await db.execute(
                    select(Lead).where(Lead.id == UUID(lead_id))
                )
                lead = result.scalar_one_or_none()
                
                if not lead:
                    raise ValueError(f"Lead {lead_id} not found")
                
                if channel == "sms":
                    return await twilio_adapter.send_sms(lead.phone, message)
                elif channel == "email":
                    return await sendgrid_adapter.send_email(
                        to_email=lead.email,
                        subject="Following up on your property",
                        body=message
                    )
        
        return run_async(do_send())
    
    except Exception as exc:
        logger.error(f"Followup failed for lead {lead_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def send_blast_task(lead_ids: list[str], message: str, channel: str = "sms"):
    """
    Send bulk message to multiple leads
    
    Idempotency: Each lead gets unique message delivery.
    """
    results = []
    for lead_id in lead_ids:
        try:
            result = send_followup_task.delay(lead_id, message, channel)
            results.append({"lead_id": lead_id, "task_id": result.id})
        except Exception as e:
            logger.error(f"Failed to queue blast for {lead_id}: {e}")
            results.append({"lead_id": lead_id, "error": str(e)})
    
    return results