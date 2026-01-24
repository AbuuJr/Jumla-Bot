"""
Abstract base adapter for LLM providers.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from ..types import LLMConfig, LLMResponse
from ..circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class LLMProviderAdapter(ABC):
    """
    Abstract base class for LLM provider adapters.
    
    All provider implementations must inherit from this class
    and implement the complete() method.
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize adapter.
        
        Args:
            config: LLM configuration
        """
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout_seconds,
            follow_redirects=True,
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.failure_threshold,
            recovery_timeout=config.recovery_timeout,
        )
        
        logger.info(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Execute completion request.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
        
        Returns:
            LLMResponse with completion
        
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            ProviderAPIError: If API request fails
        """
        pass
    
    async def close(self):
        """Cleanup resources"""
        await self.client.aclose()
        logger.info(f"{self.__class__.__name__} closed")
    
    def _record_metrics(self, success: bool, latency_ms: float):
        """
        Record metrics for monitoring.
        
        Args:
            success: Whether the request succeeded
            latency_ms: Request latency in milliseconds
        """
        if success:
            self.circuit_breaker.record_success()
        else:
            self.circuit_breaker.record_failure()