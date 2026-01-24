"""
Prometheus metrics collection for AI services.
Tracks LLM calls, latency, errors, and costs.
"""

import time
import logging
from typing import Dict, Optional
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Centralized metrics collection for AI services.
    
    Tracks:
    - Request counts per provider
    - Latency histograms
    - Error rates
    - Token usage
    - Cost estimates
    - Circuit breaker states
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize metrics collector.
        
        Args:
            registry: Optional Prometheus registry (uses default if None)
        """
        self.registry = registry
        
        # LLM Request Metrics
        self.llm_requests = Counter(
            'llm_requests_total',
            'Total LLM API requests',
            ['provider', 'operation', 'status'],
            registry=registry,
        )
        
        self.llm_latency = Histogram(
            'llm_request_duration_seconds',
            'LLM request latency',
            ['provider', 'operation'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=registry,
        )
        
        self.llm_tokens = Counter(
            'llm_tokens_total',
            'Total tokens used',
            ['provider', 'token_type'],  # token_type: prompt, completion
            registry=registry,
        )
        
        self.llm_cost = Counter(
            'llm_cost_usd_total',
            'Estimated LLM cost in USD',
            ['provider'],
            registry=registry,
        )
        
        # Circuit Breaker Metrics
        self.circuit_breaker_state = Gauge(
            'circuit_breaker_state',
            'Circuit breaker state (0=healthy, 1=degraded, 2=failed)',
            ['provider'],
            registry=registry,
        )
        
        self.circuit_breaker_failures = Counter(
            'circuit_breaker_failures_total',
            'Circuit breaker failure count',
            ['provider'],
            registry=registry,
        )
        
        # Extraction Metrics
        self.extraction_validation = Counter(
            'extraction_validation_total',
            'Extraction validation results',
            ['status'],  # status: success, failed
            registry=registry,
        )
        
        # Rate Limit Metrics
        self.rate_limit_exceeded = Counter(
            'rate_limit_exceeded_total',
            'Rate limit exceeded events',
            ['org_id', 'operation'],
            registry=registry,
        )
        
        # Cache Metrics
        self.cache_operations = Counter(
            'cache_operations_total',
            'Cache operations',
            ['operation', 'status'],  # operation: hit, miss, write
            registry=registry,
        )
        
        logger.info("Metrics collector initialized")
    
    def record_llm_request(
        self,
        provider: str,
        operation: str,
        status: str,  # success, error, fallback
        latency_seconds: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ):
        """Record LLM request metrics"""
        try:
            self.llm_requests.labels(
                provider=provider,
                operation=operation,
                status=status,
            ).inc()
            
            self.llm_latency.labels(
                provider=provider,
                operation=operation,
            ).observe(latency_seconds)
            
            if prompt_tokens > 0:
                self.llm_tokens.labels(
                    provider=provider,
                    token_type='prompt',
                ).inc(prompt_tokens)
            
            if completion_tokens > 0:
                self.llm_tokens.labels(
                    provider=provider,
                    token_type='completion',
                ).inc(completion_tokens)
            
            # Estimate cost (rough approximation)
            cost = self._estimate_cost(provider, prompt_tokens, completion_tokens)
            if cost > 0:
                self.llm_cost.labels(provider=provider).inc(cost)
                
        except Exception as e:
            logger.error(f"Failed to record LLM metrics: {str(e)}")
    
    def record_circuit_breaker_state(self, provider: str, state: str):
        """Record circuit breaker state"""
        try:
            state_value = {
                'healthy': 0,
                'degraded': 1,
                'failed': 2,
            }.get(state, 0)
            
            self.circuit_breaker_state.labels(provider=provider).set(state_value)
            
        except Exception as e:
            logger.error(f"Failed to record circuit breaker state: {str(e)}")
    
    def record_circuit_breaker_failure(self, provider: str):
        """Record circuit breaker failure"""
        try:
            self.circuit_breaker_failures.labels(provider=provider).inc()
        except Exception as e:
            logger.error(f"Failed to record circuit breaker failure: {str(e)}")
    
    def record_extraction_validation(self, is_valid: bool):
        """Record extraction validation result"""
        try:
            status = 'success' if is_valid else 'failed'
            self.extraction_validation.labels(status=status).inc()
        except Exception as e:
            logger.error(f"Failed to record validation metric: {str(e)}")
    
    def record_rate_limit_exceeded(self, org_id: str, operation: str):
        """Record rate limit exceeded event"""
        try:
            self.rate_limit_exceeded.labels(
                org_id=org_id,
                operation=operation,
            ).inc()
        except Exception as e:
            logger.error(f"Failed to record rate limit metric: {str(e)}")
    
    def record_cache_operation(self, operation: str, status: str):
        """Record cache operation (hit, miss, write)"""
        try:
            self.cache_operations.labels(
                operation=operation,
                status=status,
            ).inc()
        except Exception as e:
            logger.error(f"Failed to record cache metric: {str(e)}")
    
    def _estimate_cost(
        self,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Estimate API cost in USD.
        
        Pricing (as of 2024 - update as needed):
        - GPT-4 Turbo: $0.01/1K prompt, $0.03/1K completion
        - Claude Sonnet: $0.003/1K prompt, $0.015/1K completion
        - Gemini Pro: $0.00025/1K prompt, $0.00075/1K completion
        """
        pricing = {
            'openai': (0.01, 0.03),
            'anthropic': (0.003, 0.015),
            'gemini': (0.00025, 0.00075),
        }
        
        prompt_cost_per_1k, completion_cost_per_1k = pricing.get(
            provider.lower(),
            (0.01, 0.03),  # Default to GPT-4 pricing
        )
        
        prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
        completion_cost = (completion_tokens / 1000) * completion_cost_per_1k
        
        return prompt_cost + completion_cost


# Global metrics collector instance
metrics_collector = MetricsCollector()