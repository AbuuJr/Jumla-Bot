"""
Anthropic Claude adapter using official anthropic SDK.
"""
import time
import logging
from typing import Optional

from anthropic import AsyncAnthropic, APIError, RateLimitError, AuthenticationError

from ..types import LLMConfig, LLMResponse, LLMProvider
from ..exceptions import CircuitBreakerOpenError, ProviderAPIError
from .base import LLMProviderAdapter

logger = logging.getLogger(__name__)


class AnthropicAdapter(LLMProviderAdapter):
    """Anthropic Claude adapter using native SDK"""
    
    def __init__(self, config: LLMConfig):
        """Initialize Anthropic adapter with native SDK"""
        super().__init__(config)
        
        # Initialize Anthropic client
        try:
            self.anthropic_client = AsyncAnthropic(
                api_key=config.anthropic_api_key,
                timeout=config.timeout_seconds,
                max_retries=0,  # We handle retries via circuit breaker
            )
            logger.info("Anthropic SDK client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            self.anthropic_client = None
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        
        if not self.anthropic_client:
            raise ProviderAPIError(
                provider="Anthropic",
                message="Anthropic client not initialized",
                status_code=None,
            )
        
        if not self.circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError("Anthropic circuit breaker is open")
        
        start_time = time.time()
        
        try:
            # Make API call using SDK
            response = await self.anthropic_client.messages.create(
                model=self.config.anthropic_model,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
            )
            
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=True, latency_ms=latency_ms)
            
            # Extract content
            content = response.content[0].text
            usage = response.usage
            
            logger.info(
                f"Anthropic request succeeded: "
                f"latency={latency_ms:.0f}ms, "
                f"tokens={usage.input_tokens + usage.output_tokens}"
            )
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.ANTHROPIC,
                model=self.config.anthropic_model,
                prompt_tokens=usage.input_tokens,
                completion_tokens=usage.output_tokens,
                latency_ms=latency_ms,
                metadata={"stop_reason": response.stop_reason},
            )
            
        except AuthenticationError as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            logger.error(f"Anthropic authentication failed - check API key (latency={latency_ms:.0f}ms)")
            
            raise ProviderAPIError(
                provider="Anthropic",
                message="Invalid API key - please check your ANTHROPIC_API_KEY",
                status_code=401,
            ) from e
        
        except RateLimitError as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            logger.warning(f"Anthropic rate limit exceeded (latency={latency_ms:.0f}ms)")
            
            raise ProviderAPIError(
                provider="Anthropic",
                message="Rate limit exceeded - try again in a moment",
                status_code=429,
            ) from e
        
        except APIError as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            logger.error(
                f"Anthropic API error: {str(e)} "
                f"(status={e.status_code}, latency={latency_ms:.0f}ms)"
            )
            
            raise ProviderAPIError(
                provider="Anthropic",
                message=str(e),
                status_code=e.status_code,
            ) from e
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            logger.error(
                f"Anthropic unexpected error: {str(e)} "
                f"(latency={latency_ms:.0f}ms)"
            )
            
            raise ProviderAPIError(
                provider="Anthropic",
                message=str(e),
                status_code=None,
            ) from e
    
    async def close(self):
        """Cleanup Anthropic client resources"""
        if self.anthropic_client:
            await self.anthropic_client.close()
        await super().close()
        logger.info("AnthropicAdapter closed")