"""
Circuit breaker pattern implementation for provider health management.
"""

import time
import logging
from typing import Optional

from .types import ProviderStatus

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker for managing provider health.
    
    States:
    - HEALTHY: All operations allowed
    - DEGRADED: Recovery mode, limited operations
    - FAILED: Circuit open, no operations allowed
    
    Automatically transitions between states based on failure/success rates.
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.status = ProviderStatus.HEALTHY
        
        logger.info(
            f"Circuit breaker initialized: "
            f"threshold={failure_threshold}, timeout={recovery_timeout}s"
        )
    
    def record_success(self):
        """Record successful call - resets failure count"""
        if self.failure_count > 0:
            logger.info(
                f"Circuit breaker recovering: "
                f"failures cleared (was {self.failure_count})"
            )
        
        self.failure_count = 0
        self.status = ProviderStatus.HEALTHY
    
    def record_failure(self):
        """Record failed call - may trip circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.status = ProviderStatus.FAILED
            logger.warning(
                f"Circuit breaker OPENED after {self.failure_count} failures"
            )
        else:
            logger.debug(
                f"Circuit breaker failure recorded: "
                f"{self.failure_count}/{self.failure_threshold}"
            )
    
    def can_attempt(self) -> bool:
        """
        Check if we can attempt to call this provider.
        
        Returns:
            True if call is allowed, False if circuit is open
        """
        if self.status == ProviderStatus.HEALTHY:
            return True
        
        if self.status == ProviderStatus.FAILED:
            # Check if enough time has passed for recovery attempt
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info(
                        f"Circuit breaker attempting recovery after {elapsed:.1f}s"
                    )
                    self.status = ProviderStatus.DEGRADED
                    return True
            return False
        
        # DEGRADED state - allow attempts
        return True
    
    def get_status(self) -> ProviderStatus:
        """Get current circuit breaker status"""
        return self.status
    
    def reset(self):
        """Manually reset circuit breaker (admin operation)"""
        logger.info("Circuit breaker manually reset")
        self.failure_count = 0
        self.last_failure_time = None
        self.status = ProviderStatus.HEALTHY