"""
Mock adapter for testing.
"""

import asyncio
import json
import logging
from typing import Optional, Dict

from ..types import LLMConfig, LLMResponse, LLMProvider
from .base import LLMProviderAdapter

logger = logging.getLogger(__name__)


class MockAdapter(LLMProviderAdapter):
    """Mock adapter for testing - returns predefined responses"""
    
    def __init__(self, config: LLMConfig, mock_responses: Optional[Dict[str, str]] = None):
        """
        Initialize mock adapter.
        
        Args:
            config: LLM configuration
            mock_responses: Optional dict mapping keywords to responses
        """
        super().__init__(config)
        self.mock_responses = mock_responses or {}
        self.call_count = 0
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        
        self.call_count += 1
        await asyncio.sleep(0.05)  # Simulate API latency
        
        logger.debug(f"MockAdapter call #{self.call_count}")
        
        # Check for custom mock responses
        for keyword, response in self.mock_responses.items():
            if keyword.lower() in prompt.lower():
                return self._build_response(response)
        
        # Default responses
        if "extract" in prompt.lower():
            return self._build_response(self._get_default_extraction())
        
        return self._build_response(
            "Thank you for reaching out! I'd be happy to help. "
            "Can you tell me more about your property?"
        )
    
    def _build_response(self, content: str) -> LLMResponse:
        """Build mock LLM response"""
        return LLMResponse(
            content=content,
            provider=LLMProvider.MOCK,
            model="mock-model-v1",
            prompt_tokens=100,
            completion_tokens=len(content.split()) * 2,
            latency_ms=50.0,
        )
    
    def _get_default_extraction(self) -> str:
        """Get default extraction JSON"""
        return json.dumps({
            "contact": {
                "name": None,
                "phone": None,
                "email": None,
                "preferred_contact_method": None
            },
            "property": {
                "address": None,
                "city": None,
                "state": None,
                "zip_code": None,
                "property_type": None,
                "bedrooms": None,
                "bathrooms": None,
                "square_feet": None,
                "year_built": None,
                "condition": None
            },
            "situation": {
                "motivation": None,
                "urgency": None,
                "occupancy_status": None,
                "mortgage_status": None,
                "asking_price": None,
                "repairs_needed": None,
                "open_to_cash_offer": None
            },
            "intent": {
                "classification": "needs_more_info",
                "confidence": 0.5,
                "next_action": "follow_up"
            },
            "metadata": {
                "language": "en",
                "sentiment": "neutral",
                "contains_pii": False,
                "extraction_notes": None
            }
        })