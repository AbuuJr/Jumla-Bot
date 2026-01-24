"""
app/services/llm/types.py
Type definitions for LLM service.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MOCK = "mock"


class ProviderStatus(str, Enum):
    """Circuit breaker states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    # API Keys
    openai_api_key: str
    anthropic_api_key: str
    gemini_api_key: str
    
    # Provider priority order
    provider_priority: List[LLMProvider]
    
    # Model configurations
    openai_model: str = "gpt-4-turbo-preview"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    gemini_model: str = "gemini-2.5-pro"
    
    # Timeouts and retries
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_multiplier: float = 2.0
    
    # Rate limiting (requests per minute)
    rate_limit_rpm: int = 60
    
    # Circuit breaker
    failure_threshold: int = 5
    recovery_timeout: int = 60
    
    # Caching
    cache_ttl_seconds: int = 300
    
    # Safety
    max_tokens: int = 2000
    temperature: float = 0.1


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    provider: LLMProvider
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    cached: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExtractionResult:
    """Result from lead information extraction"""
    data: Dict[str, Any]
    validated: bool
    validation_errors: Optional[List[str]]
    llm_response: LLMResponse