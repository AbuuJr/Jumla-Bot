"""
app/services/llm_client.py
LLM adapter for OpenAI and Anthropic with JSON schema validation
"""
from typing import Dict, Any, Optional, List
from enum import Enum
import json
import logging
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM provider enumeration"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """
    LLM client with fallback support and JSON schema validation
    
    IMPORTANT: LLM is used ONLY for extraction and summarization.
    LLM MUST NEVER make deterministic business decisions (pricing, scoring, offers).
    """
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.primary_provider = LLMProvider(settings.LLM_PRIMARY_PROVIDER)
        self.fallback_provider = LLMProvider(settings.LLM_FALLBACK_PROVIDER) if settings.LLM_FALLBACK_PROVIDER else None
    
    async def extract_lead_info(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured information from lead message
        
        Returns:
            {
                "property_address": str | None,
                "bedrooms": int | None,
                "bathrooms": float | None,
                "condition": str | None,  # "excellent", "good", "fair", "poor"
                "urgency": str | None,    # "immediate", "soon", "flexible"
                "motivation": str | None,  # "financial", "relocation", "inheritance", "other"
                "price_expectation": float | None,
                "timeline": str | None,
                "additional_notes": str | None
            }
        """
        system_prompt = """You are an expert real estate assistant. Extract structured information from seller messages.
        
        Extract ONLY the following fields (return null if not mentioned):
        - property_address: Full address if mentioned
        - bedrooms: Number of bedrooms
        - bathrooms: Number of bathrooms
        - condition: Property condition (excellent/good/fair/poor)
        - urgency: Selling urgency (immediate/soon/flexible)
        - motivation: Reason for selling (financial/relocation/inheritance/other)
        - price_expectation: Expected sale price in dollars
        - timeline: Desired closing timeline
        - additional_notes: Any other relevant information
        
        Return ONLY valid JSON with these exact field names. No markdown, no explanations."""
        
        user_prompt = f"Extract information from this message:\n\n{message}"
        
        if conversation_history:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history[-5:]])
            user_prompt += f"\n\nRecent conversation:\n{context}"
        
        try:
            # Try primary provider
            extracted = await self._call_llm(
                provider=self.primary_provider,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            return self._validate_extraction_schema(extracted)
        
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}")
            
            # Try fallback provider
            if self.fallback_provider:
                try:
                    extracted = await self._call_llm(
                        provider=self.fallback_provider,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt
                    )
                    return self._validate_extraction_schema(extracted)
                except Exception as fallback_error:
                    logger.error(f"Fallback LLM also failed: {fallback_error}")
            
            # Return empty extraction on complete failure
            return self._empty_extraction()
    
    async def generate_response(
        self,
        message: str,
        extracted_data: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate conversational response to lead
        
        This is a simple response generator. LLM does NOT make offers or business decisions.
        """
        system_prompt = """You are a friendly real estate assistant helping sellers. 
        
        Your role:
        - Ask clarifying questions to understand their property and situation
        - Be empathetic and professional
        - Gather information: address, property details, condition, timeline, motivation
        - DO NOT make offers or discuss specific prices
        - DO NOT make promises or commitments
        - Keep responses brief (2-3 sentences)
        
        An agent will review and make an official offer later."""
        
        context = ""
        if conversation_history:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history[-5:]])
        
        user_prompt = f"""Recent conversation:
{context}

Latest message: {message}

Extracted info so far: {json.dumps(extracted_data, indent=2)}

Generate a helpful response."""
        
        try:
            response = await self._call_llm(
                provider=self.primary_provider,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            return response if isinstance(response, str) else response.get("response", "Thank you for the information. An agent will be in touch soon.")
        
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return "Thank you for reaching out. An agent will contact you shortly to discuss your property."
    
    async def _call_llm(
        self,
        provider: LLMProvider,
        system_prompt: str,
        user_prompt: str
    ) -> Any:
        """Call LLM provider with retry logic"""
        for attempt in range(settings.LLM_MAX_RETRIES):
            try:
                if provider == LLMProvider.OPENAI:
                    return await self._call_openai(system_prompt, user_prompt)
                elif provider == LLMProvider.ANTHROPIC:
                    return await self._call_anthropic(system_prompt, user_prompt)
            except Exception as e:
                if attempt == settings.LLM_MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _call_openai(self, system_prompt: str, user_prompt: str) -> Any:
        """Call OpenAI API"""
        response = await asyncio.wait_for(
            self.openai_client.chat.completions.create(
                model=settings.LLM_MODEL_OPENAI,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"} if "JSON" in system_prompt else None
            ),
            timeout=settings.LLM_TIMEOUT_SECONDS
        )
        
        content = response.choices[0].message.content
        
        # Try to parse as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    
    async def _call_anthropic(self, system_prompt: str, user_prompt: str) -> Any:
        """Call Anthropic API"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not configured")
        
        response = await asyncio.wait_for(
            self.anthropic_client.messages.create(
                model=settings.LLM_MODEL_ANTHROPIC,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
            ),
            timeout=settings.LLM_TIMEOUT_SECONDS
        )
        
        content = response.content[0].text
        
        # Try to parse as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    
    def _validate_extraction_schema(self, data: Any) -> Dict[str, Any]:
        """Validate and normalize extracted data"""
        if not isinstance(data, dict):
            return self._empty_extraction()
        
        schema = {
            "property_address": (str, None),
            "bedrooms": (int, None),
            "bathrooms": (float, None),
            "condition": (str, None),
            "urgency": (str, None),
            "motivation": (str, None),
            "price_expectation": (float, None),
            "timeline": (str, None),
            "additional_notes": (str, None),
        }
        
        validated = {}
        for key, (expected_type, default) in schema.items():
            value = data.get(key, default)
            
            # Type coercion and validation
            if value is not None:
                try:
                    if expected_type == int:
                        validated[key] = int(value)
                    elif expected_type == float:
                        validated[key] = float(value)
                    elif expected_type == str:
                        validated[key] = str(value).strip()
                except (ValueError, TypeError):
                    validated[key] = default
            else:
                validated[key] = default
        
        return validated
    
    def _empty_extraction(self) -> Dict[str, Any]:
        """Return empty extraction schema"""
        return {
            "property_address": None,
            "bedrooms": None,
            "bathrooms": None,
            "condition": None,
            "urgency": None,
            "motivation": None,
            "price_expectation": None,
            "timeline": None,
            "additional_notes": None,
        }

# Singleton instance
llm_client = LLMClient()