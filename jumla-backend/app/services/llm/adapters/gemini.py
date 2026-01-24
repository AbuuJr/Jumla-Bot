"""
Google Gemini adapter implementation (fallback only).
"""

import time
import logging
from typing import Optional

from ..types import LLMConfig, LLMResponse, LLMProvider
from ..exceptions import CircuitBreakerOpenError, ProviderAPIError
from .base import LLMProviderAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(LLMProviderAdapter):
    """Google Gemini adapter (fallback provider)"""
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        
        if not self.circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError("Gemini circuit breaker is open")
        
        start_time = time.time()
        
        try:
            # Gemini combines system and user prompts
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = await self.client.post(
                f"https://generativelanguage.googleapis.com/v1/models/{self.config.gemini_model}:generateContent",
                headers={"Content-Type": "application/json"},
                params={"key": self.config.gemini_api_key},
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "temperature": temperature or self.config.temperature,
                        "maxOutputTokens": max_tokens or self.config.max_tokens,
                    },
                },
            )
            
            response.raise_for_status()
            data = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=True, latency_ms=latency_ms)
            
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            
            logger.info(
                f"Gemini request succeeded: "
                f"latency={latency_ms:.0f}ms, "
                f"tokens={usage.get('totalTokenCount', 0)}"
            )
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.GEMINI,
                model=self.config.gemini_model,
                prompt_tokens=usage.get("promptTokenCount", 0),
                completion_tokens=usage.get("candidatesTokenCount", 0),
                latency_ms=latency_ms,
                metadata={"finish_reason": data["candidates"][0].get("finishReason")},
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            error_msg = str(e)
            status_code = getattr(e, 'status_code', None)
            
            logger.error(
                f"Gemini request failed: {error_msg} "
                f"(status={status_code}, latency={latency_ms:.0f}ms)"
            )
            
            raise ProviderAPIError(
                provider="Gemini",
                message=error_msg,
                status_code=status_code,
            ) from e