"""
app/services/scoring_engine.py
Deterministic lead scoring engine

CRITICAL: 100% deterministic scoring based on explicit rules.
NO LLM involvement. All scores are reproducible and auditable.
"""
from typing import Dict, Any, Optional, List
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from app.config import settings
from app.models.lead import Lead, Temperature

logger = logging.getLogger(__name__)


@dataclass
class LeadScoreBreakdown:
    """Detailed score breakdown"""
    total_score: Decimal
    urgency_score: Decimal
    motivation_score: Decimal
    property_score: Decimal
    response_score: Decimal
    financial_score: Decimal
    temperature: Temperature
    factors: Dict[str, Any]


class ScoringEngine:
    """
    Deterministic lead scoring engine
    
    Scoring categories (0-100 each):
    1. Urgency (0-20 points): How quickly they need to sell
    2. Motivation (0-20 points): Why they're selling
    3. Property (0-20 points): Property characteristics
    4. Response (0-20 points): Engagement and responsiveness
    5. Financial (0-20 points): Financial indicators
    
    Total: 0-100 points
    - Hot: 80-100
    - Warm: 50-79
    - Cold: 0-49
    """
    
    # Urgency keywords and scores
    URGENCY_KEYWORDS = {
        "immediate": 20,
        "asap": 20,
        "urgent": 18,
        "soon": 15,
        "quickly": 15,
        "this week": 18,
        "this month": 15,
        "foreclosure": 20,
        "flexible": 5,
        "no rush": 2,
    }
    
    # Motivation keywords and scores
    MOTIVATION_KEYWORDS = {
        "financial": 18,
        "debt": 20,
        "divorce": 18,
        "inheritance": 15,
        "relocation": 16,
        "job": 14,
        "downsize": 12,
        "upgrade": 8,
        "tax": 17,
        "behind on payments": 20,
    }
    
    # Property condition impact
    CONDITION_SCORES = {
        "poor": 18,      # More attractive (bigger discount opportunity)
        "fair": 15,
        "good": 10,
        "excellent": 5,  # Less attractive (lower margin)
    }
    
    def score_lead(
        self,
        lead: Lead,
        conversations: List[Any],
        property_data: Optional[Dict[str, Any]] = None
    ) -> LeadScoreBreakdown:
        """
        Calculate comprehensive lead score
        
        Args:
            lead: Lead model instance
            conversations: List of conversations with lead
            property_data: Enriched property data
        
        Returns:
            LeadScoreBreakdown with detailed scoring
        """
        factors = {}
        
        # 1. Urgency Score (0-20)
        urgency_score, urgency_factors = self._score_urgency(
            lead.raw_data,
            lead.enriched_data,
            conversations
        )
        factors["urgency"] = urgency_factors
        
        # 2. Motivation Score (0-20)
        motivation_score, motivation_factors = self._score_motivation(
            lead.raw_data,
            lead.enriched_data,
            conversations
        )
        factors["motivation"] = motivation_factors
        
        # 3. Property Score (0-20)
        property_score, property_factors = self._score_property(
            property_data or lead.enriched_data
        )
        factors["property"] = property_factors
        
        # 4. Response Score (0-20)
        response_score, response_factors = self._score_responsiveness(
            conversations,
            lead.created_at
        )
        factors["response"] = response_factors
        
        # 5. Financial Score (0-20)
        financial_score, financial_factors = self._score_financial(
            lead.enriched_data,
            property_data or {}
        )
        factors["financial"] = financial_factors
        
        # Calculate total score
        total_score = (
            urgency_score +
            motivation_score +
            property_score +
            response_score +
            financial_score
        )
        
        # Determine temperature
        if total_score >= Decimal(settings.HOT_LEAD_SCORE_THRESHOLD):
            temperature = Temperature.HOT
        elif total_score >= Decimal(settings.WARM_LEAD_SCORE_THRESHOLD):
            temperature = Temperature.WARM
        else:
            temperature = Temperature.COLD
        
        return LeadScoreBreakdown(
            total_score=total_score,
            urgency_score=urgency_score,
            motivation_score=motivation_score,
            property_score=property_score,
            response_score=response_score,
            financial_score=financial_score,
            temperature=temperature,
            factors=factors
        )
    
    def _score_urgency(
        self,
        raw_data: Dict[str, Any],
        enriched_data: Dict[str, Any],
        conversations: List[Any]
    ) -> tuple[Decimal, Dict[str, Any]]:
        """Score urgency to sell (0-20)"""
        score = Decimal("0")
        factors = {}
        
        # Check for urgency keywords in conversations
        all_text = " ".join([
            c.message_body.lower() for c in conversations if c.message_body
        ])
        
        matched_keywords = []
        for keyword, points in self.URGENCY_KEYWORDS.items():
            if keyword in all_text:
                score += Decimal(points)
                matched_keywords.append(keyword)
        
        # Cap at 20
        score = min(score, Decimal("20"))
        
        # Check extracted urgency field
        urgency = enriched_data.get("urgency")
        if urgency == "immediate":
            score = Decimal("20")
        elif urgency == "soon":
            score = max(score, Decimal("15"))
        
        factors["matched_keywords"] = matched_keywords
        factors["extracted_urgency"] = urgency
        
        return score, factors
    
    def _score_motivation(
        self,
        raw_data: Dict[str, Any],
        enriched_data: Dict[str, Any],
        conversations: List[Any]
    ) -> tuple[Decimal, Dict[str, Any]]:
        """Score motivation to sell (0-20)"""
        score = Decimal("0")
        factors = {}
        
        # Check for motivation keywords
        all_text = " ".join([
            c.message_body.lower() for c in conversations if c.message_body
        ])
        
        matched_keywords = []
        for keyword, points in self.MOTIVATION_KEYWORDS.items():
            if keyword in all_text:
                score += Decimal(points)
                matched_keywords.append(keyword)
        
        # Cap at 20
        score = min(score, Decimal("20"))
        
        # Check extracted motivation
        motivation = enriched_data.get("motivation")
        if motivation in ["financial", "debt"]:
            score = Decimal("20")
        elif motivation in ["divorce", "relocation"]:
            score = max(score, Decimal("16"))
        
        factors["matched_keywords"] = matched_keywords
        factors["extracted_motivation"] = motivation
        
        return score, factors
    
    def _score_property(
        self,
        property_data: Dict[str, Any]
    ) -> tuple[Decimal, Dict[str, Any]]:
        """Score property characteristics (0-20)"""
        score = Decimal("10")  # Base score
        factors = {}
        
        # Condition score (worse condition = higher score = better deal)
        condition = property_data.get("condition", "").lower()
        if condition in self.CONDITION_SCORES:
            condition_score = Decimal(self.CONDITION_SCORES[condition])
            score = condition_score
            factors["condition"] = condition
        
        # Has complete address (indicates data quality)
        if property_data.get("property_address") or property_data.get("address_full"):
            score += Decimal("2")
            factors["has_address"] = True
        
        # Property value in good range
        estimated_value = property_data.get("estimated_value")
        if estimated_value:
            value = Decimal(str(estimated_value))
            if Decimal(50000) <= value <= Decimal(500000):
                score += Decimal("3")
                factors["value_in_range"] = True
        
        # Cap at 20
        score = min(score, Decimal("20"))
        
        return score, factors
    
    def _score_responsiveness(
        self,
        conversations: List[Any],
        lead_created_at: datetime
    ) -> tuple[Decimal, Dict[str, Any]]:
        """Score engagement and response time (0-20)"""
        score = Decimal("0")
        factors = {}
        
        if not conversations:
            return Decimal("5"), {"message": "No conversations yet"}
        
        # Number of exchanges
        exchange_count = len([c for c in conversations if c.direction == "inbound"])
        if exchange_count >= 5:
            score += Decimal("10")
        elif exchange_count >= 3:
            score += Decimal("7")
        elif exchange_count >= 1:
            score += Decimal("5")
        
        factors["exchange_count"] = exchange_count
        
        # Response time (how quickly they respond)
        inbound_messages = [c for c in conversations if c.direction == "inbound"]
        if len(inbound_messages) >= 2:
            avg_response_minutes = self._calculate_avg_response_time(inbound_messages)
            if avg_response_minutes < 60:  # Under 1 hour
                score += Decimal("10")
            elif avg_response_minutes < 240:  # Under 4 hours
                score += Decimal("7")
            elif avg_response_minutes < 1440:  # Under 24 hours
                score += Decimal("5")
            
            factors["avg_response_minutes"] = avg_response_minutes
        
        # Recent activity (responded in last 24 hours)
        if conversations and (datetime.utcnow() - conversations[-1].created_at) < timedelta(hours=24):
            score += Decimal("5")
            factors["recent_activity"] = True
        
        # Cap at 20
        score = min(score, Decimal("20"))
        
        return score, factors
    
    def _score_financial(
        self,
        enriched_data: Dict[str, Any],
        property_data: Dict[str, Any]
    ) -> tuple[Decimal, Dict[str, Any]]:
        """Score financial indicators (0-20)"""
        score = Decimal("10")  # Base score
        factors = {}
        
        # Has price expectation
        price_expectation = enriched_data.get("price_expectation")
        if price_expectation:
            factors["has_price_expectation"] = True
            
            # Check if expectation is realistic
            estimated_value = property_data.get("estimated_value")
            if estimated_value:
                expectation_ratio = Decimal(str(price_expectation)) / Decimal(str(estimated_value))
                if Decimal("0.6") <= expectation_ratio <= Decimal("0.9"):
                    score += Decimal("10")  # Realistic expectation
                    factors["realistic_expectation"] = True
                elif expectation_ratio < Decimal("0.6"):
                    score += Decimal("5")  # Low expectation (good for us)
                    factors["low_expectation"] = True
        
        # Property has equity
        estimated_value = property_data.get("estimated_value")
        last_sale_price = property_data.get("last_sale_price")
        if estimated_value and last_sale_price:
            equity_ratio = (Decimal(str(estimated_value)) - Decimal(str(last_sale_price))) / Decimal(str(estimated_value))
            if equity_ratio > Decimal("0.3"):
                score += Decimal("5")
                factors["has_equity"] = True
        
        # Cap at 20
        score = min(score, Decimal("20"))
        
        return score, factors
    
    def _calculate_avg_response_time(self, messages: List[Any]) -> float:
        """Calculate average response time in minutes"""
        if len(messages) < 2:
            return 0
        
        response_times = []
        for i in range(1, len(messages)):
            time_diff = (messages[i].created_at - messages[i-1].created_at).total_seconds() / 60
            response_times.append(time_diff)
        
        return sum(response_times) / len(response_times) if response_times else 0


# Singleton instance
scoring_engine = ScoringEngine()