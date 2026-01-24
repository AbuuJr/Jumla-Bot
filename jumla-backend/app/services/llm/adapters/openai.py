"""
OpenAI GPT adapter using official openai SDK.
"""
import time
import logging
from typing import Optional

from openai import AsyncOpenAI
from openai import APIError, RateLimitError, AuthenticationError

from ..types import LLMConfig, LLMResponse, LLMProvider
from ..exceptions import CircuitBreakerOpenError, ProviderAPIError
from .base import LLMProviderAdapter

logger = logging.getLogger(__name__)


class OpenAIAdapter(LLMProviderAdapter):
    """OpenAI GPT adapter using native SDK"""
    
    def __init__(self, config: LLMConfig):
        """Initialize OpenAI adapter with native SDK"""
        super().__init__(config)
        
        # Initialize OpenAI client
        try:
            self.openai_client = AsyncOpenAI(
                api_key=config.openai_api_key,
                timeout=config.timeout_seconds,
                max_retries=0,  # We handle retries via circuit breaker
            )
            logger.info("OpenAI SDK client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        
        if not self.openai_client:
            raise ProviderAPIError(
                provider="OpenAI",
                message="OpenAI client not initialized",
                status_code=None,
            )
        
        if not self.circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError("OpenAI circuit breaker is open")
        
        start_time = time.time()
        
        try:
            # Build messages array
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare request kwargs
            kwargs = {
                "model": self.config.openai_model,
                "messages": messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
            }
            
            # Add JSON mode for extraction requests
            if "extract" in prompt.lower() or "json" in prompt.lower():
                kwargs["response_format"] = {"type": "json_object"}
            
            # Make API call using SDK
            response = await self.openai_client.chat.completions.create(**kwargs)
            
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=True, latency_ms=latency_ms)
            
            # Extract data from response
            content = response.choices[0].message.content
            usage = response.usage
            
            logger.info(
                f"OpenAI request succeeded: "
                f"latency={latency_ms:.0f}ms, "
                f"tokens={usage.total_tokens}"
            )
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.OPENAI,
                model=self.config.openai_model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                latency_ms=latency_ms,
                metadata={"finish_reason": response.choices[0].finish_reason},
            )
            
        except AuthenticationError as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            logger.error(f"OpenAI authentication failed - check API key (latency={latency_ms:.0f}ms)")
            
            raise ProviderAPIError(
                provider="OpenAI",
                message="Invalid API key - please check your OPENAI_API_KEY",
                status_code=401,
            ) from e
        
        except RateLimitError as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            logger.warning(f"OpenAI rate limit exceeded (latency={latency_ms:.0f}ms)")
            
            raise ProviderAPIError(
                provider="OpenAI",
                message="Rate limit exceeded - try again in a moment",
                status_code=429,
            ) from e
        
        except APIError as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            logger.error(
                f"OpenAI API error: {str(e)} "
                f"(status={e.status_code}, latency={latency_ms:.0f}ms)"
            )
            
            raise ProviderAPIError(
                provider="OpenAI",
                message=str(e),
                status_code=e.status_code,
            ) from e
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            logger.error(
                f"OpenAI unexpected error: {str(e)} "
                f"(latency={latency_ms:.0f}ms)"
            )
            
            raise ProviderAPIError(
                provider="OpenAI",
                message=str(e),
                status_code=None,
            ) from e
    
    async def close(self):
        """Cleanup OpenAI client resources"""
        if self.openai_client:
            await self.openai_client.close()
        await super().close()
        logger.info("OpenAIAdapter closed")