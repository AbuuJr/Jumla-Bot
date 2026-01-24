"""
OpenAI GPT adapter implementation.
"""

import time
import logging
from typing import Optional

from ..types import LLMConfig, LLMResponse, LLMProvider
from ..exceptions import CircuitBreakerOpenError, ProviderAPIError
from .base import LLMProviderAdapter

logger = logging.getLogger(__name__)


class OpenAIAdapter(LLMProviderAdapter):
    """OpenAI GPT-4 adapter"""
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        
        if not self.circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError("OpenAI circuit breaker is open")
        
        start_time = time.time()
        
        try:
            # Build messages array
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare request payload
            payload = {
                "model": self.config.openai_model,
                "messages": messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
            }
            
            # Add JSON mode for extraction requests
            if "extract" in prompt.lower() or "json" in prompt.lower():
                payload["response_format"] = {"type": "json_object"}
            
            # Make API request
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=True, latency_ms=latency_ms)
            
            logger.info(
                f"OpenAI request succeeded: "
                f"latency={latency_ms:.0f}ms, "
                f"tokens={data['usage']['total_tokens']}"
            )
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                provider=LLMProvider.OPENAI,
                model=self.config.openai_model,
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"],
                latency_ms=latency_ms,
                metadata={"finish_reason": data["choices"][0]["finish_reason"]},
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            error_msg = str(e)
            status_code = getattr(e, 'status_code', None)
            
            logger.error(
                f"OpenAI request failed: {error_msg} "
                f"(status={status_code}, latency={latency_ms:.0f}ms)"
            )
            
            raise ProviderAPIError(
                provider="OpenAI",
                message=error_msg,
                status_code=status_code,
            ) from e