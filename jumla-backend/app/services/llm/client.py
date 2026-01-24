"""
Main LLM orchestration client with multi-provider fallback.
Handles extraction, response generation, and summarization.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.lead import Lead

from jsonschema import validate, ValidationError as JsonSchemaValidationError

from .types import (
    LLMConfig,
    LLMProvider,
    LLMResponse,
    ExtractionResult,
    ProviderStatus,
)
from .exceptions import (
    AllProvidersFailedError,
    SchemaValidationError,
    CircuitBreakerOpenError,
    ProviderAPIError,
)
from .adapters import (
    LLMProviderAdapter,
    OpenAIAdapter,
    AnthropicAdapter,
    GeminiAdapter,
    MockAdapter,
)

logger = logging.getLogger(__name__)

# System prompt for response generation
SYSTEM_PROMPT = """You are Jumla-bot, a friendly real estate assistant helping sellers get fast cash offers.

Guidelines:
- Be concise (1-2 sentences)
- Ask for ONE piece of missing information at a time
- Be empathetic if seller mentions urgency/distress
- NEVER make offers or discuss pricing
- If user mentions payment terms or wants to negotiate, say you'll connect them with an agent"""


class LLMClient:
    """
    Main LLM orchestration client with multi-provider fallback.
    
    Features:
    - Automatic provider fallback
    - Circuit breaker per provider
    - Schema validation
    - Caching support
    - Comprehensive error handling
    
    Usage:
        client = LLMClient(config, schema, prompts, cache)
        result = await client.extract_lead_info(message, sender)
    """
    
    def __init__(
        self,
        config: LLMConfig,
        schema: Dict[str, Any],
        prompts: Dict[str, str],
        cache_backend: Optional[Any] = None,
    ):
        """
        Initialize LLM client.
        
        Args:
            config: LLM configuration
            schema: JSON schema for validation
            prompts: Prompt templates
            cache_backend: Optional Redis client for caching
        """
        self.config = config
        self.schema = schema
        self.prompts = prompts
        self.cache = cache_backend
        
        # Initialize provider adapters
        self.adapters: Dict[LLMProvider, LLMProviderAdapter] = {}
        self._initialize_adapters()
        
        logger.info(
            f"LLMClient initialized with providers: "
            f"{[p.value for p in config.provider_priority]}"
        )
    
    def _initialize_adapters(self):
        """Initialize provider adapters based on configuration"""
        adapter_map = {
            LLMProvider.OPENAI: OpenAIAdapter,
            LLMProvider.ANTHROPIC: AnthropicAdapter,
            LLMProvider.GEMINI: GeminiAdapter,
            LLMProvider.MOCK: MockAdapter,
        }
        
        for provider in self.config.provider_priority:
            adapter_class = adapter_map.get(provider)
            if adapter_class:
                self.adapters[provider] = adapter_class(self.config)
                logger.info(f"Initialized {provider.value} adapter")


    def _identify_missing_fields(self, extracted_data: Optional[Dict[str, Any]]) -> List[str]:
        """Identify which critical fields are still missing"""
        if not extracted_data:
            return ["address", "property_details", "timeline"]
        
        missing = []
        
        # Check property address
        prop = extracted_data.get("property", {})
        if not prop.get("address") and not (prop.get("city") and prop.get("zip_code")):
            missing.append("address")
        
        # Check property details
        if not prop.get("bedrooms") or not prop.get("condition"):
            missing.append("property_details")
        
        # Check timeline/urgency
        situation = extracted_data.get("situation", {})
        if not situation.get("urgency"):
            missing.append("timeline")
        
        # Check motivation
        if not situation.get("motivation"):
            missing.append("motivation")
        
        return missing
    

    def _check_escalation_triggers(
        self, message: str, extracted_data: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Check if message contains triggers that require human escalation.
        
        Returns:
            Escalation type if triggered, None otherwise
        """
        message_lower = message.lower()
        
        # Payment terms indicators
        payment_keywords = [
            "50%", "percent", "partial payment", "installment",
            "pay half", "split payment", "% now", "% later"
        ]
        if any(keyword in message_lower for keyword in payment_keywords):
            return "payment_terms"
        
        # Negotiation indicators
        negotiation_keywords = [
            "negotiate", "discuss terms", "make a deal",
            "counter offer", "bargain", "legal", "contract"
        ]
        if any(keyword in message_lower for keyword in negotiation_keywords):
            return "negotiation"
        
        # Check extracted data for high price discrepancy
        if extracted_data:
            situation = extracted_data.get("situation", {})
            asking_price = situation.get("asking_price")
            if asking_price and asking_price > 10_000_000:  # Unusually high
                return "price_review"
        
        return None


    def _should_confirm_details(self, extracted_data: Optional[Dict[str, Any]]) -> bool:
        """Check if we have enough info to confirm with user before proceeding"""
        if not extracted_data:
            return False
        
        prop = extracted_data.get("property", {})
        
        # Need at minimum: address + bedrooms + condition
        has_address = bool(prop.get("address") or (prop.get("city") and prop.get("zip_code")))
        has_bedrooms = prop.get("bedrooms") is not None
        has_condition = prop.get("condition") is not None
        
        return has_address and has_bedrooms and has_condition


    def _create_escalation_response(self, escalation_type: str) -> LLMResponse:
        """Create response for escalation scenarios"""
        templates = {
            "payment_terms": (
                "Thanks for that info — I'll pass this to an agent who will "
                "review the payment terms and follow up within 24 hours."
            ),
            "negotiation": (
                "I'll connect you with an agent who can discuss those details. "
                "They'll reach out shortly."
            ),
            "price_review": (
                "Thank you for the information. An agent will review your property details "
                "and reach out to discuss options."
            ),
        }
        
        content = templates.get(escalation_type, templates["negotiation"])
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.OPENAI,  # Placeholder
            model="template",
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=0,
            metadata={"escalation_type": escalation_type},
        )


    def _create_confirmation_response(self, extracted_data: Dict[str, Any]) -> LLMResponse:
        """Create confirmation response when we have key details"""
        prop = extracted_data.get("property", {})
        
        details_parts = []
        
        if prop.get("bedrooms"):
            details_parts.append(f"{prop['bedrooms']} bedrooms")
        
        if prop.get("bathrooms"):
            details_parts.append(f"{prop['bathrooms']} bathrooms")
        
        if prop.get("condition"):
            details_parts.append(f"{prop['condition']} condition")
        
        if prop.get("address"):
            address = prop["address"]
        elif prop.get("city") and prop.get("state"):
            address = f"{prop['city']}, {prop['state']}"
        else:
            address = "the property"
        
        details = ", ".join(details_parts) if details_parts else "the details"
        
        content = (
            f"Let me confirm: {details} at {address}. "
            f"Is this correct? (Reply 'yes' to continue or provide corrections)"
        )
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.OPENAI,
            model="template",
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=0,
            metadata={"type": "confirmation"},
        )


    def _build_info_summary(self, extracted_data: Optional[Dict[str, Any]]) -> str:
        """
        Build human-readable summary of lead information for AI context.
        NOW USES EXTRACTED_DATA WHICH CONTAINS ACCUMULATED INFO
        """
        parts = []
        
        if not extracted_data:
            return "No information gathered yet"
        
        # Contact info
        contact = extracted_data.get("contact", {})
        if contact.get("name"):
            parts.append(f"Name: {contact['name']}")
        if contact.get("phone"):
            parts.append(f"Phone: {contact['phone']}")
        if contact.get("email"):
            parts.append(f"Email: {contact['email']}")
        
        # Property info
        prop = extracted_data.get("property", {})
        if prop.get("address"):
            parts.append(f"Address: {prop['address']}")
        elif prop.get("city"):
            parts.append(f"City: {prop['city']}")
        
        if prop.get("bedrooms"):
            parts.append(f"Bedrooms: {prop['bedrooms']}")
        if prop.get("bathrooms"):
            parts.append(f"Bathrooms: {prop['bathrooms']}")
        if prop.get("condition"):
            parts.append(f"Condition: {prop['condition']}")
        
        # Situation info
        situation = extracted_data.get("situation", {})
        if situation.get("urgency"):
            parts.append(f"Timeline: {situation['urgency']}")
        if situation.get("motivation"):
            parts.append(f"Motivation: {situation['motivation']}")
        
        return "; ".join(parts) if parts else "Limited information provided"

    
    async def close(self):
        """Cleanup all provider connections"""
        logger.info("Closing LLM client and all adapters")
        for adapter in self.adapters.values():
            await adapter.close()
    
    # ========================================================================
    # CORE METHODS
    # ========================================================================
    
    async def extract_lead_info(
        self,
        message: str,
        sender: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        lead_id: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Extract structured lead information from conversation message.
        
        Args:
            message: The latest message from seller
            sender: Identifier for who sent the message
            conversation_history: List of prior messages
            lead_id: Optional lead ID for caching
        
        Returns:
            ExtractionResult with validated data
        """
        # Check cache if lead_id provided
        if lead_id and self.cache:
            cached_result = await self._get_from_cache(lead_id, message)
            if cached_result:
                return cached_result
        
        # Format conversation history
        history_text = self._format_history(conversation_history)
        
        # Build extraction prompt with safe formatting
        prompt = self._safe_format_prompt(
            self.prompts["extract"],
            conversation_history=history_text or "No prior conversation",
            sender=sender,
            message=message,
        )
        
        # Execute with fallback
        try:
            llm_response = await self._complete_with_fallback(
                prompt=prompt,
                temperature=0.1,  # Very deterministic for extraction
            )
        except AllProvidersFailedError as e:
            logger.error(f"Extraction failed - all providers unavailable: {str(e)}")
            return self._create_fallback_extraction(str(e))
        
        # Parse and validate JSON
        data = self._parse_json_safely(llm_response.content)
        
        if not data:
            logger.error("Failed to parse extraction JSON")
            return self._create_fallback_extraction("Invalid JSON response")
        
        # Validate against schema
        is_valid, errors = self._validate_extraction(data)
        
        # Cache valid extractions
        if is_valid and lead_id and self.cache:
            await self._save_to_cache(lead_id, message, data)
        
        return ExtractionResult(
            data=data,
            validated=is_valid,
            validation_errors=errors,
            llm_response=llm_response,
        )
    
    async def generate_response(
        self,
        message: str,
        lead_stage: str,
        info_summary: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Generate a smart, contextual response to the seller.
        
        Now includes:
        - Acknowledgment of what user just said
        - Specific questions for missing fields
        - Escalation detection
        - Confirmation of extracted data
        """
        history_text = self._format_history(conversation_history)
        
        # Analyze what information we have vs what's missing
        missing_fields = self._identify_missing_fields(extracted_data)
        needs_escalation = self._check_escalation_triggers(message, extracted_data)
        
        # If user proposed payment terms or wants to negotiate -> escalate
        if needs_escalation:
            escalation_type = needs_escalation  # "payment_terms" or "negotiation"
            return self._create_escalation_response(escalation_type)
        
        # If we have key info (address + beds + condition), confirm before proceeding
        if self._should_confirm_details(extracted_data):
            return self._create_confirmation_response(extracted_data)
        
        # Build info summary showing what we know
        info_summary = self._build_info_summary(extracted_data)
        
        # Build contextual prompt with ALL possible placeholders
        # Extract property details safely
        prop = extracted_data.get("property", {}) if extracted_data else {}
        situation = extracted_data.get("situation", {}) if extracted_data else {}
        
        prompt_vars = {
            "lead_status": lead_stage,
            "info_summary": info_summary,
            "conversation_history": history_text or "No prior conversation",
            "message": message,
            # Add all possible property fields
            "address": prop.get("address", "not provided"),
            "beds": prop.get("bedrooms", "not provided"),
            "bedrooms": prop.get("bedrooms", "not provided"),
            "baths": prop.get("bathrooms", "not provided"),
            "bathrooms": prop.get("bathrooms", "not provided"),
            "condition": prop.get("condition", "not provided"),
            "property_type": prop.get("property_type", "not provided"),
            "urgency": situation.get("urgency", "not provided"),
            "motivation": situation.get("motivation", "not provided"),
        }
        
        # Safe format with all possible variables
        prompt = self._safe_format_prompt(self.prompts["reply"], **prompt_vars)
        
        # Add system prompt
        system_prompt = self.prompts.get("system", SYSTEM_PROMPT)
        
        # Execute with fallback
        try:
            response = await self._complete_with_fallback(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=300,
            )
        except AllProvidersFailedError:
            # If all providers fail, give intelligent fallback based on extracted data
            return self._create_smart_fallback_response(message, extracted_data, missing_fields)
        
        return response
    
    def _create_smart_fallback_response(
        self, 
        message: str, 
        extracted_data: Optional[Dict[str, Any]], 
        missing_fields: List[str]
    ) -> LLMResponse:
        """Create an intelligent fallback response when LLM is unavailable"""
        
        # If we have the address but LLM failed, acknowledge and ask for next thing
        if extracted_data:
            prop = extracted_data.get("property", {})
            
            if prop.get("address") and "bedrooms" in missing_fields:
                content = "Got it! How many bedrooms does the property have?"
            elif prop.get("bedrooms") and "condition" in missing_fields:
                content = "Thanks! What's the overall condition? (Excellent / Good / Needs TLC / Major repairs)"
            elif "address" in missing_fields:
                content = "Thanks for reaching out! Could you share the property address?"
            else:
                content = "Thanks! When are you looking to sell? (ASAP / 1-3 months / Flexible)"
        else:
            # No extracted data yet
            if "address" in message.lower() or any(char.isdigit() for char in message):
                content = "Thanks! How many bedrooms does the property have?"
            else:
                content = "Thanks for reaching out! Could you share the property address?"
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.OPENAI,
            model="fallback",
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=0,
            metadata={"fallback": True},
        )
    
    def _safe_format_prompt(self, template: str, **kwargs) -> str:
        """
        Safely format prompt template, providing defaults for missing keys.
        This prevents KeyError when prompt template has placeholders we don't provide.
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing prompt variable: {e}. Using safe defaults.")
            # Add the missing key with a default value
            missing_key = str(e).strip("'")
            kwargs[missing_key] = "not provided"
            return template.format(**kwargs)
    
    async def summarize_lead(
        self,
        conversation_history: List[Dict[str, str]],
        extracted_data: Dict[str, Any],
    ) -> str:
        """
        Generate a human-readable summary of the lead for review.
        
        Args:
            conversation_history: Full conversation
            extracted_data: Structured data extracted from conversation
        
        Returns:
            Summary text
        """
        history_text = self._format_history(conversation_history)
        
        prompt = f"""Summarize this real estate lead conversation for the sales team.

CONVERSATION:
{history_text}

EXTRACTED DATA:
{json.dumps(extracted_data, indent=2)}

Provide a 3-4 sentence summary highlighting:
1. Property details and condition
2. Seller's motivation and timeline
3. Key concerns or requirements
4. Recommended next steps

Be concise and factual."""
        
        response = await self._complete_with_fallback(
            prompt=prompt,
            temperature=0.3,
            max_tokens=400,
        )
        
        return response.content
    
    # ========================================================================
    # PROVIDER FALLBACK LOGIC (OPTIMIZED FOR PRIMARY-FIRST)
    # ========================================================================
    
    async def _complete_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Execute completion with automatic provider fallback.
        Tries PRIMARY provider first, only falls back if it fails.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            LLMResponse from first successful provider
        
        Raises:
            AllProvidersFailedError: If all providers fail
        """
        errors = []
        
        for provider in self.config.provider_priority:
            adapter = self.adapters.get(provider)
            if not adapter:
                continue
            
            try:
                logger.info(f"Attempting completion with {provider.value}")
                
                response = await adapter.complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                logger.info(
                    f"✓ Success with {provider.value} "
                    f"(latency: {response.latency_ms:.0f}ms, "
                    f"tokens: {response.prompt_tokens + response.completion_tokens})"
                )
                
                # SUCCESS - return immediately without trying other providers
                return response
                
            except CircuitBreakerOpenError as e:
                logger.warning(
                    f"✗ {provider.value} circuit breaker open, trying next provider"
                )
                errors.append((provider, str(e)))
                continue
                
            except ProviderAPIError as e:
                logger.warning(
                    f"✗ {provider.value} failed: {str(e)}, trying next provider"
                )
                errors.append((provider, str(e)))
                continue
            
            except Exception as e:
                logger.error(
                    f"✗ Unexpected error with {provider.value}: {str(e)}",
                    exc_info=True,
                )
                errors.append((provider, str(e)))
                continue
        
        # All providers failed
        error_summary = "; ".join([f"{p.value}: {e}" for p, e in errors])
        raise AllProvidersFailedError(
            f"All LLM providers failed. Errors: {error_summary}"
        )
    
    # ========================================================================
    # VALIDATION & PARSING
    # ========================================================================
    
    def _validate_extraction(
        self, data: Dict[str, Any]
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate extracted data against JSON schema.
        
        Args:
            data: Extracted data to validate
        
        Returns:
            (is_valid, error_list)
        """
        try:
            validate(instance=data, schema=self.schema)
            return True, None
        except JsonSchemaValidationError as e:
            errors = [str(e.message)]
            # Collect all validation errors
            if e.context:
                errors.extend([str(err.message) for err in e.context])
            logger.warning(f"Schema validation failed: {errors}")
            return False, errors
    
    def _parse_json_safely(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Safely parse JSON from LLM response.
        Handles markdown code blocks and other formatting issues.
        
        Args:
            content: Raw LLM response content
        
        Returns:
            Parsed JSON dict or None if parsing fails
        """
        try:
            # Remove markdown code blocks if present
            content = content.strip()
            
            if content.startswith("```"):
                # Extract content between code fences
                lines = content.split("\n")
                if len(lines) > 2:
                    content = "\n".join(lines[1:-1])
                content = content.replace("```json", "").replace("```", "").strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(
                f"JSON parsing failed: {str(e)}\n"
                f"Content preview: {content[:200]}..."
            )
            return None
    
    # ========================================================================
    # CACHING
    # ========================================================================
    
    async def _get_from_cache(
        self, lead_id: str, message: str
    ) -> Optional[ExtractionResult]:
        """
        Get cached extraction result.
        
        Args:
            lead_id: Lead identifier
            message: Message content (for cache key)
        
        Returns:
            Cached ExtractionResult or None
        """
        if not self.cache:
            return None
        
        try:
            cache_key = f"extraction:{lead_id}:{hash(message)}"
            cached = await self.cache.get(cache_key)
            
            if cached:
                logger.info(f"Cache hit for lead {lead_id}")
                data = json.loads(cached)
                
                return ExtractionResult(
                    data=data,
                    validated=True,
                    validation_errors=None,
                    llm_response=LLMResponse(
                        content=cached,
                        provider=LLMProvider.OPENAI,  # Placeholder
                        model="cached",
                        prompt_tokens=0,
                        completion_tokens=0,
                        latency_ms=0,
                        cached=True,
                    ),
                )
        except Exception as e:
            logger.warning(f"Cache read failed: {str(e)}")
        
        return None
    
    async def _save_to_cache(
        self, lead_id: str, message: str, data: Dict[str, Any]
    ):
        """
        Save extraction result to cache.
        
        Args:
            lead_id: Lead identifier
            message: Message content (for cache key)
            data: Extracted data to cache
        """
        if not self.cache:
            return
        
        try:
            cache_key = f"extraction:{lead_id}:{hash(message)}"
            await self.cache.setex(
                cache_key,
                self.config.cache_ttl_seconds,
                json.dumps(data),
            )
            logger.debug(f"Cached extraction for lead {lead_id}")
        except Exception as e:
            logger.warning(f"Cache write failed: {str(e)}")
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _format_history(
        self, conversation_history: Optional[List[Dict[str, str]]]
    ) -> str:
        """
        Format conversation history for prompts.
        
        Args:
            conversation_history: List of messages
        
        Returns:
            Formatted history string
        """
        if not conversation_history:
            return ""
        
        # Take last N messages to avoid token limits
        recent_history = conversation_history[-10:]
        
        return "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in recent_history
        ])
    
    def _get_empty_extraction_structure(self) -> Dict[str, Any]:
        """
        Return safe empty extraction structure matching schema.
        Used as fallback when extraction completely fails.
        
        Returns:
            Empty but schema-valid extraction dict
        """
        return {
            "contact": {
                "name": None,
                "phone": None,
                "email": None,
                "preferred_contact_method": None,
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
                "condition": None,
            },
            "situation": {
                "motivation": None,
                "urgency": None,
                "occupancy_status": None,
                "mortgage_status": None,
                "asking_price": None,
                "repairs_needed": None,
                "open_to_cash_offer": None,
            },
            "intent": {
                "classification": "unclear",
                "confidence": 0.0,
                "next_action": None,
            },
            "metadata": {
                "language": "en",
                "sentiment": "neutral",
                "contains_pii": False,
                "extraction_notes": "Failed to extract data from message",
            },
        }
    
    def _create_fallback_extraction(self, reason: str) -> ExtractionResult:
        """
        Create fallback extraction result when all providers fail.
        
        Args:
            reason: Reason for fallback
        
        Returns:
            Safe fallback ExtractionResult
        """
        data = self._get_empty_extraction_structure()
        data["metadata"]["extraction_notes"] = f"Extraction failed: {reason}"
        
        return ExtractionResult(
            data=data,
            validated=False,
            validation_errors=[reason],
            llm_response=LLMResponse(
                content=json.dumps(data),
                provider=LLMProvider.OPENAI,  # Placeholder
                model="fallback",
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=0,
            ),
        )
    
    # ========================================================================
    # HEALTH & STATUS
    # ========================================================================
    
    def get_provider_health(self) -> Dict[str, ProviderStatus]:
        """
        Get health status of all providers.
        
        Returns:
            Dict mapping provider name to health status
        """
        return {
            provider.value: adapter.circuit_breaker.get_status()
            for provider, adapter in self.adapters.items()
        }
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers (admin operation)"""
        logger.info("Resetting all circuit breakers")
        for adapter in self.adapters.values():
            adapter.circuit_breaker.reset()