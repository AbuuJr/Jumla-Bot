"""
Redis-based rate limiter using token bucket algorithm.
Enforces per-organization and global rate limits for LLM calls.
"""

import time
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10  # Allow short bursts


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter with Redis backend.
    
    Features:
    - Sliding window rate limiting
    - Per-organization quotas
    - Multiple time windows (minute, hour, day)
    - Graceful degradation (fails open if Redis unavailable)
    - Usage tracking for analytics
    
    Usage:
        limiter = TokenBucketRateLimiter(redis_client, config)
        allowed, retry_after = await limiter.check_rate_limit(org_id)
        if not allowed:
            raise HTTPException(429, f"Retry after {retry_after}s")
    """
    
    def __init__(self, redis_client, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis/aioredis client (or None to disable)
            config: Rate limit configuration
        """
        self.redis = redis_client
        self.config = config or RateLimitConfig()
        self.enabled = redis_client is not None
        
        if not self.enabled:
            logger.warning(
                "⚠️  Rate limiter initialized without Redis - limits DISABLED. "
                "All requests will be allowed."
            )
        else:
            logger.info(
                f"Rate limiter initialized: "
                f"{self.config.requests_per_minute}/min, "
                f"{self.config.requests_per_hour}/hour, "
                f"{self.config.requests_per_day}/day"
            )
    
    async def check_rate_limit(
        self,
        org_id: str,
        operation: str = "llm_call",
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed under rate limits.
        
        Args:
            org_id: Organization identifier
            operation: Type of operation (for separate limits)
        
        Returns:
            (allowed, retry_after_seconds)
            - allowed: True if request should proceed
            - retry_after: Seconds to wait before retry (if not allowed)
        """
        if not self.enabled:
            return True, None
        
        try:
            # Check per-minute limit (strictest)
            allowed, retry_after = await self._check_limit(
                key=f"ratelimit:{org_id}:{operation}:minute",
                limit=self.config.requests_per_minute,
                window_seconds=60,
            )
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for org={org_id}: "
                    f"{self.config.requests_per_minute}/minute"
                )
                return False, retry_after
            
            # Check per-hour limit
            allowed, retry_after = await self._check_limit(
                key=f"ratelimit:{org_id}:{operation}:hour",
                limit=self.config.requests_per_hour,
                window_seconds=3600,
            )
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for org={org_id}: "
                    f"{self.config.requests_per_hour}/hour"
                )
                return False, retry_after
            
            # Check per-day limit
            allowed, retry_after = await self._check_limit(
                key=f"ratelimit:{org_id}:{operation}:day",
                limit=self.config.requests_per_day,
                window_seconds=86400,
            )
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for org={org_id}: "
                    f"{self.config.requests_per_day}/day"
                )
                return False, retry_after
            
            return True, None
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}", exc_info=True)
            # Fail open - allow request if Redis is down
            # This prevents Redis outages from blocking all traffic
            return True, None
    
    async def _check_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, Optional[int]]:
        """
        Check single rate limit using sliding window.
        
        Implementation uses Redis sorted sets where:
        - Score = timestamp
        - Member = unique request ID
        
        Args:
            key: Redis key for this limit
            limit: Maximum requests in window
            window_seconds: Time window in seconds
        
        Returns:
            (allowed, retry_after_seconds)
        """
        try:
            now = time.time()
            window_start = now - window_seconds
            
            # Remove entries older than window
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            current_count = await self.redis.zcard(key)
            
            if current_count >= limit:
                # Rate limit exceeded - calculate retry time
                oldest_entries = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest_entries:
                    oldest_time = oldest_entries[0][1]
                    retry_after = int(oldest_time + window_seconds - now)
                    return False, max(1, retry_after)
                return False, window_seconds
            
            # Add current request to window
            request_id = f"{now}:{id(self)}"  # Unique ID
            await self.redis.zadd(key, {request_id: now})
            
            # Set expiry on key (cleanup)
            await self.redis.expire(key, window_seconds + 60)
            
            return True, None
            
        except Exception as e:
            logger.error(f"Rate limit check error for {key}: {str(e)}")
            # Fail open
            return True, None
    
    async def record_request(
        self,
        org_id: str,
        operation: str = "llm_call",
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        provider: Optional[str] = None,
    ):
        """
        Record a request for monitoring and analytics.
        
        This does NOT enforce limits - it only tracks usage.
        Call this after successful requests to maintain statistics.
        
        Args:
            org_id: Organization identifier
            operation: Type of operation
            tokens_used: Number of tokens consumed
            cost_usd: Estimated cost in USD
            provider: LLM provider used
        """
        if not self.enabled:
            return
        
        try:
            timestamp = int(time.time())
            date_key = time.strftime("%Y-%m-%d", time.gmtime())
            
            # Increment request counter
            await self.redis.hincrby(
                f"usage:{org_id}:{operation}:requests",
                date_key,
                1,
            )
            
            # Track tokens
            if tokens_used > 0:
                await self.redis.hincrby(
                    f"usage:{org_id}:{operation}:tokens",
                    date_key,
                    tokens_used,
                )
            
            # Track cost
            if cost_usd > 0:
                await self.redis.hincrbyfloat(
                    f"usage:{org_id}:{operation}:cost",
                    date_key,
                    cost_usd,
                )
            
            # Track by provider
            if provider:
                await self.redis.hincrby(
                    f"usage:{org_id}:provider:{provider}",
                    date_key,
                    1,
                )
            
            # Set expiry (keep 90 days)
            for key in [
                f"usage:{org_id}:{operation}:requests",
                f"usage:{org_id}:{operation}:tokens",
                f"usage:{org_id}:{operation}:cost",
                f"usage:{org_id}:provider:{provider}" if provider else None,
            ]:
                if key:
                    await self.redis.expire(key, 86400 * 90)
            
        except Exception as e:
            logger.error(f"Failed to record request: {str(e)}")
            # Non-critical - don't raise
    
    async def get_usage_stats(
        self,
        org_id: str,
        operation: str = "llm_call",
        days: int = 7,
    ) -> dict:
        """
        Get usage statistics for an organization.
        
        Args:
            org_id: Organization identifier
            operation: Type of operation
            days: Number of days to include
        
        Returns:
            Dictionary with usage stats by date
        """
        if not self.enabled:
            return {"error": "Rate limiter not enabled"}
        
        try:
            stats = {
                "org_id": org_id,
                "operation": operation,
                "period_days": days,
                "requests": {},
                "tokens": {},
                "cost_usd": {},
            }
            
            # Get data for last N days
            for i in range(days):
                date = time.strftime(
                    "%Y-%m-%d",
                    time.gmtime(time.time() - (i * 86400))
                )
                
                # Get requests
                requests = await self.redis.hget(
                    f"usage:{org_id}:{operation}:requests",
                    date,
                )
                stats["requests"][date] = int(requests) if requests else 0
                
                # Get tokens
                tokens = await self.redis.hget(
                    f"usage:{org_id}:{operation}:tokens",
                    date,
                )
                stats["tokens"][date] = int(tokens) if tokens else 0
                
                # Get cost
                cost = await self.redis.hget(
                    f"usage:{org_id}:{operation}:cost",
                    date,
                )
                stats["cost_usd"][date] = float(cost) if cost else 0.0
            
            # Calculate totals
            stats["total_requests"] = sum(stats["requests"].values())
            stats["total_tokens"] = sum(stats["tokens"].values())
            stats["total_cost_usd"] = sum(stats["cost_usd"].values())
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {str(e)}")
            return {"error": str(e)}
    
    async def get_current_usage(
        self,
        org_id: str,
        operation: str = "llm_call",
    ) -> dict:
        """
        Get current usage counts for all time windows.
        
        Args:
            org_id: Organization identifier
            operation: Type of operation
        
        Returns:
            Dict with current counts for each time window
        """
        if not self.enabled:
            return {"error": "Rate limiter not enabled"}
        
        try:
            now = time.time()
            
            # Count requests in each window
            minute_count = await self._get_window_count(
                f"ratelimit:{org_id}:{operation}:minute",
                now - 60,
                now,
            )
            
            hour_count = await self._get_window_count(
                f"ratelimit:{org_id}:{operation}:hour",
                now - 3600,
                now,
            )
            
            day_count = await self._get_window_count(
                f"ratelimit:{org_id}:{operation}:day",
                now - 86400,
                now,
            )
            
            return {
                "minute": {
                    "current": minute_count,
                    "limit": self.config.requests_per_minute,
                    "remaining": max(0, self.config.requests_per_minute - minute_count),
                },
                "hour": {
                    "current": hour_count,
                    "limit": self.config.requests_per_hour,
                    "remaining": max(0, self.config.requests_per_hour - hour_count),
                },
                "day": {
                    "current": day_count,
                    "limit": self.config.requests_per_day,
                    "remaining": max(0, self.config.requests_per_day - day_count),
                },
            }
            
        except Exception as e:
            logger.error(f"Failed to get current usage: {str(e)}")
            return {"error": str(e)}
    
    async def _get_window_count(
        self,
        key: str,
        start: float,
        end: float,
    ) -> int:
        """Get count of requests in time window"""
        try:
            return await self.redis.zcount(key, start, end)
        except Exception:
            return 0
    
    async def reset_limits(
        self,
        org_id: str,
        operation: str = "llm_call",
    ):
        """
        Reset rate limits for an organization (admin operation).
        
        Args:
            org_id: Organization identifier
            operation: Type of operation
        """
        if not self.enabled:
            return
        
        try:
            keys_to_delete = [
                f"ratelimit:{org_id}:{operation}:minute",
                f"ratelimit:{org_id}:{operation}:hour",
                f"ratelimit:{org_id}:{operation}:day",
            ]
            
            for key in keys_to_delete:
                await self.redis.delete(key)
            
            logger.info(f"✓ Reset rate limits for org={org_id}, operation={operation}")
            
        except Exception as e:
            logger.error(f"Failed to reset limits: {str(e)}")