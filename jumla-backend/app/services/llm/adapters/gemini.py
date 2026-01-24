"""
Google Gemini adapter using official google-generativeai SDK.
"""
import time
import logging
from typing import Optional

import google.generativeai as genai
from google.generativeai import types
from ..types import LLMConfig, LLMResponse, LLMProvider
from ..exceptions import CircuitBreakerOpenError, ProviderAPIError
from .base import LLMProviderAdapter

logger = logging.getLogger(__name__)


class GeminiAdapter(LLMProviderAdapter):
    """Google Gemini adapter using native SDK"""
    
    def __init__(self, config: LLMConfig):
        """Initialize Gemini adapter with native SDK"""
        super().__init__(config)
        
        # Initialize Gemini client
        try:
            self.gemini_client = genai.Client(api_key=config.gemini_api_key)
            logger.info("Gemini SDK client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.gemini_client = None
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        
        if not self.gemini_client:
            raise ProviderAPIError(
                provider="Gemini",
                message="Gemini client not initialized",
                status_code=None,
            )
        
        if not self.circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError("Gemini circuit breaker is open")
        
        start_time = time.time()
        
        try:
            # Build the full prompt (Gemini doesn't have separate system prompt in generate_content)
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Configure generation
            config_dict = {
                "temperature": temperature or self.config.temperature,
                "max_output_tokens": max_tokens or self.config.max_tokens,
            }
            
            # Make the API call using SDK
            response = self.gemini_client.models.generate_content(
                model=self.config.gemini_model,
                contents=full_prompt,
                config=types.GenerateContentConfig(**config_dict)
            )
            
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=True, latency_ms=latency_ms)
            
            # Extract content
            content = response.text
            
            # Get usage metadata if available
            usage = response.usage_metadata
            prompt_tokens = usage.prompt_token_count if usage else 0
            completion_tokens = usage.candidates_token_count if usage else 0
            
            logger.info(
                f"Gemini request succeeded: "
                f"latency={latency_ms:.0f}ms, "
                f"tokens={prompt_tokens + completion_tokens}"
            )
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.GEMINI,
                model=self.config.gemini_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                metadata={"finish_reason": "complete"},
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_metrics(success=False, latency_ms=latency_ms)
            
            error_msg = str(e)
            
            # Extract status code if it's a rate limit or quota error
            status_code = None
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                status_code = 429
                logger.warning(f"Gemini rate limit hit - consider upgrading API quota")
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                status_code = 401
            elif "400" in error_msg:
                status_code = 400
            
            logger.error(
                f"Gemini request failed: {error_msg} "
                f"(status={status_code}, latency={latency_ms:.0f}ms)"
            )
            
            raise ProviderAPIError(
                provider="Gemini",
                message=error_msg,
                status_code=status_code,
            ) from e
    
    async def close(self):
        """Cleanup Gemini client resources"""
        # Gemini SDK doesn't require explicit cleanup, but we call parent
        await super().close()
        logger.info("GeminiAdapter closed")