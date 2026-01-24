# ========================================
# app/dependencies.py
# ========================================
"""
FastAPI dependencies for dependency injection
"""
import json
import logging
from typing import Optional, Dict, List
from functools import lru_cache

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from redis.asyncio import Redis  # ✅ FIXED

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.config import settings

# Import LLM services
from app.services.llm.client import LLMClient, LLMConfig, LLMProvider
from app.services.rate_limiter import TokenBucketRateLimiter, RateLimitConfig

logger = logging.getLogger(__name__)


# ============================================================================
# USER & ORG DEPENDENCIES
# ============================================================================

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """Fetch user's organization"""
    from sqlalchemy import select

    result = await db.execute(
        select(Organization).where(
            Organization.id == current_user.organization_id
        )
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return organization


async def validate_organization_access(
    organization_id: UUID,
    current_user: User = Depends(get_current_user)
) -> UUID:
    """Ensure user belongs to organization"""
    if current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    return organization_id


async def get_request_id(
    x_request_id: Optional[str] = Header(None)
) -> Optional[str]:
    """Extract request ID from headers"""
    return x_request_id


# ============================================================================
# LLM CONFIG LOADERS
# ============================================================================

@lru_cache()
def _load_llm_schema() -> Dict:
    """Load and cache JSON schema"""
    try:
        with open("ai/schema.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load LLM schema: {e}")
        raise RuntimeError("Could not load AI schema file")


@lru_cache()
def _load_llm_prompts() -> Dict[str, str]:
    """Load and cache prompt templates"""
    try:
        prompts = {}

        with open("ai/prompts/extract_v2.txt", "r", encoding='utf-8') as f:
            prompts["extract"] = f.read()

        with open("ai/prompts/reply_v2.txt", "r", encoding='utf-8') as f:
            prompts["reply"] = f.read()

        return prompts
    except Exception as e:
        logger.error(f"Failed to load LLM prompts: {e}")
        raise RuntimeError("Could not load AI prompt files")


# ============================================================================
# GLOBAL SERVICE INSTANCES
# ============================================================================

_llm_client: Optional[LLMClient] = None
_redis_client: Optional[Redis] = None
_rate_limiter: Optional[TokenBucketRateLimiter] = None


# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

async def initialize_ai_services():
    """Initialize Redis, LLM client, and rate limiter"""
    global _llm_client, _redis_client, _rate_limiter

    try:
        # --- Redis ---
        if settings.REDIS_URL:
            _redis_client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
            logger.info("✓ Redis client initialized")

        # --- Provider priority with primary provider first ---
        provider_list = [
            p.strip().lower()
            for p in settings.LLM_PROVIDER_PRIORITY.split(",")
            if p.strip()
        ]

        # Ensure primary provider is tried first
        primary = settings.LLM_PRIMARY_PROVIDER.lower()
        if primary in provider_list:
            provider_list.remove(primary)  # Remove from current position
        provider_list.insert(0, primary)  # Add to front

        logger.info(f"LLM provider order: {provider_list} (primary: {primary})")


        # --- Provider priority ---
        provider_priority = [
            LLMProvider(p)
            for p in provider_list
            if p in ["openai", "anthropic", "gemini", "mock"]
        ]

        # --- LLM config ---
        llm_config = LLMConfig(
            openai_api_key=settings.OPENAI_API_KEY,
            anthropic_api_key=settings.ANTHROPIC_API_KEY or "",
            gemini_api_key=settings.GEMINI_API_KEY or "",
            provider_priority=provider_priority,
            openai_model=settings.LLM_MODEL_OPENAI,
            anthropic_model=settings.LLM_MODEL_ANTHROPIC,
            gemini_model=settings.LLM_MODEL_GEMINI,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            max_retries=settings.LLM_MAX_RETRIES,
            rate_limit_rpm=settings.LLM_RATE_LIMIT_RPM,
            cache_ttl_seconds=settings.LLM_CACHE_TTL_SECONDS,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            failure_threshold=settings.LLM_CIRCUIT_BREAKER_THRESHOLD,
            recovery_timeout=settings.LLM_CIRCUIT_BREAKER_TIMEOUT,
        )

        # --- Load assets ---
        schema = _load_llm_schema()
        prompts = _load_llm_prompts()

        # --- LLM client ---
        _llm_client = LLMClient(
            config=llm_config,
            schema=schema,
            prompts=prompts,
            cache_backend=_redis_client if settings.ENABLE_LLM_CACHING else None,
        )

        logger.info("✓ LLM client initialized")

        # --- Rate limiter ---
        rate_limit_config = RateLimitConfig(
            requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
            requests_per_hour=getattr(settings, "RATE_LIMIT_PER_HOUR", 1000),
            requests_per_day=getattr(settings, "RATE_LIMIT_PER_DAY", 10000),
        )

        _rate_limiter = TokenBucketRateLimiter(
            redis_client=_redis_client,
            config=rate_limit_config,
        )

        logger.info("✓ Rate limiter initialized")

    except Exception as e:
        logger.error("AI services initialization failed", exc_info=True)
        raise


async def shutdown_ai_services():
    """Shutdown Redis & LLM services"""
    global _llm_client, _redis_client

    logger.info("Shutting down AI services...")

    if _llm_client:
        await _llm_client.close()
        logger.info("✓ LLM client closed")

    if _redis_client:
        await _redis_client.close()
        logger.info("✓ Redis client closed")


# ============================================================================
# DEPENDENCY ACCESSORS
# ============================================================================

def get_llm_client() -> LLMClient:
    if _llm_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI services not initialized"
        )
    return _llm_client


def get_rate_limiter() -> TokenBucketRateLimiter:
    if _rate_limiter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiter not initialized"
        )
    return _rate_limiter


# ============================================================================
# LEGACY IN-MEMORY RATE LIMITER (DEV ONLY)
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter (dev only)"""

    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.cache: Dict[str, List[float]] = {}

    async def __call__(
        self,
        current_user: User = Depends(get_current_user)
    ):
        import time

        user_id = str(current_user.id)
        now = time.time()

        self.cache.setdefault(user_id, [])
        self.cache[user_id] = [
            t for t in self.cache[user_id]
            if now - t < self.period
        ]

        if len(self.cache[user_id]) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.calls}/{self.period}s"
            )

        self.cache[user_id].append(now)
