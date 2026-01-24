"""
Anthropic Claude adapter implementation.
"""

import time
import logging
from typing import Optional

from ..types import LLMConfig, LLMResponse, LLMProvider
from ..exceptions import CircuitBreakerOpenError, ProviderAPIError
from .base import LLMProviderAdapter

logger = logging.getLogger(__name__)


class AnthropicAdapter(LLMProviderAdapter):
    """Anthropic Claude adapter"""
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        
        if not self.circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError("Anthropic circuit breaker is open")
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.config.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.anthropic_model,
                    "max_tokens": max_tokens or self.config.max_tokens,
                    "temperature": temperature or self.config.temperature,
                    "system": system_prompt or "",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            
            response.raise_for_status()
            data = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=True, latency_ms=latency_ms)
            
            logger.info(
                f"Anthropic request succeeded: "
                f"latency={latency_ms:.0f}ms, "
                f"tokens={data['usage']['input_tokens'] + data['usage']['output_tokens']}"
            )
            
            return LLMResponse(
                content=data["content"][0]["text"],
                provider=LLMProvider.ANTHROPIC,
                model=self.config.anthropic_model,
                prompt_tokens=data["usage"]["input_tokens"],
                completion_tokens=data["usage"]["output_tokens"],
                latency_ms=latency_ms,
                metadata={"stop_reason": data["stop_reason"]},
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            error_msg = str(e)
            status_code = getattr(e, 'status_code', None)
            
            logger.error(
                f"Anthropic request failed: {error_msg} "
                f"(status={status_code}, latency={latency_ms:.0f}ms)"
            )
            
            raise ProviderAPIError(
                provider="Anthropic",
                message=error_msg,
                status_code=status_code,
            ) from e