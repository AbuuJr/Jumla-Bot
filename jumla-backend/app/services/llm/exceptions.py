"""
Custom exceptions for LLM service.
"""


class LLMError(Exception):
    """Base exception for LLM operations"""
    pass


class AllProvidersFailedError(LLMError):
    """All configured providers failed"""
    pass


class SchemaValidationError(LLMError):
    """JSON schema validation failed"""
    pass


class RateLimitExceededError(LLMError):
    """Rate limit exceeded"""
    pass


class CircuitBreakerOpenError(LLMError):
    """Circuit breaker is open for this provider"""
    pass


class ProviderAPIError(LLMError):
    """Provider API returned an error"""
    
    def __init__(self, provider: str, message: str, status_code: int = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"{provider}: {message}")