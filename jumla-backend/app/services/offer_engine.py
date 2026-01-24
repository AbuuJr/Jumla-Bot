"""
app/services/offer_engine.py
Deterministic offer calculation engine

CRITICAL: This module contains 100% deterministic business logic.
NO LLM calls. NO probabilistic decisions. All rules are explicit and testable.
"""
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from enum import Enum
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class PropertyCondition(str, Enum):
    """Property condition enumeration"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class OfferStrategy(str, Enum):
    """Offer calculation strategy"""
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"


@dataclass
class OfferCalculation:
    """Offer calculation result"""
    offer_amount: Decimal
    arv: Decimal  # After Repair Value
    repair_cost: Decimal
    margin_percent: Decimal
    confidence_level: str  # "high", "medium", "low"
    factors: Dict[str, Any]
    warnings: list[str]


class OfferEngine:
    """
    Deterministic offer calculation engine
    
    Formula: Offer = (ARV * Margin%) - Repair Cost - Holding Cost
    
    All calculations are explicit, testable, and auditable.
    """
    
    # Condition-based repair cost multipliers (per sqft)
    REPAIR_COST_PER_SQFT = {
        PropertyCondition.EXCELLENT: Decimal("0"),
        PropertyCondition.GOOD: Decimal("15"),
        PropertyCondition.FAIR: Decimal("35"),
        PropertyCondition.POOR: Decimal("60"),
    }
    
    # Holding cost assumptions
    HOLDING_MONTHS = 3
    HOLDING_COST_PERCENT = Decimal("0.02")  # 2% of ARV per quarter
    
    # Strategy-based margin adjustments
    STRATEGY_MARGINS = {
        OfferStrategy.STANDARD: Decimal("0.70"),      # 70% of ARV
        OfferStrategy.AGGRESSIVE: Decimal("0.75"),    # 75% of ARV
        OfferStrategy.CONSERVATIVE: Decimal("0.65"),  # 65% of ARV
    }
    
    def calculate_offer(
        self,
        estimated_value: Decimal,
        sqft: Optional[int] = None,
        condition: Optional[str] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[Decimal] = None,
        year_built: Optional[int] = None,
        strategy: OfferStrategy = OfferStrategy.STANDARD
    ) -> OfferCalculation:
        """
        Calculate cash offer based on property characteristics
        
        Args:
            estimated_value: Estimated market value or ARV
            sqft: Property square footage
            condition: Property condition
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            year_built: Year property was built
            strategy: Offer strategy (standard/aggressive/conservative)
        
        Returns:
            OfferCalculation with offer amount and breakdown
        """
        warnings = []
        confidence = "high"
        
        # Validate inputs
        if estimated_value <= 0:
            raise ValueError("Estimated value must be positive")
        
        if estimated_value < Decimal(settings.MIN_OFFER_AMOUNT):
            raise ValueError(f"Property value below minimum threshold: ${settings.MIN_OFFER_AMOUNT}")
        
        if estimated_value > Decimal(settings.MAX_OFFER_AMOUNT):
            raise ValueError(f"Property value exceeds maximum threshold: ${settings.MAX_OFFER_AMOUNT}")
        
        # Calculate ARV (After Repair Value)
        arv = self._calculate_arv(estimated_value, year_built, bedrooms, bathrooms)
        
        # Calculate repair costs
        repair_cost = self._calculate_repair_cost(
            condition=condition,
            sqft=sqft,
            year_built=year_built
        )
        
        if not sqft or not condition:
            confidence = "medium"
            warnings.append("Missing property details (sqft or condition) - using estimates")
        
        # Calculate holding costs
        holding_cost = arv * self.HOLDING_COST_PERCENT
        
        # Get margin based on strategy
        margin_percent = self.STRATEGY_MARGINS[strategy]
        
        # Calculate offer: (ARV * Margin) - Repair Cost - Holding Cost
        offer_amount = (arv * margin_percent) - repair_cost - holding_cost
        
        # Round to nearest $1000
        offer_amount = self._round_to_thousand(offer_amount)
        
        # Validate offer is within acceptable range
        min_offer = arv * Decimal("0.50")  # Never less than 50% ARV
        max_offer = arv * Decimal("0.85")  # Never more than 85% ARV
        
        if offer_amount < min_offer:
            offer_amount = min_offer
            confidence = "low"
            warnings.append("Offer adjusted to minimum threshold (50% ARV)")
        
        if offer_amount > max_offer:
            offer_amount = max_offer
            confidence = "low"
            warnings.append("Offer adjusted to maximum threshold (85% ARV)")
        
        # Final bounds check
        if offer_amount < Decimal(settings.MIN_OFFER_AMOUNT):
            offer_amount = Decimal(settings.MIN_OFFER_AMOUNT)
            warnings.append(f"Offer set to minimum: ${settings.MIN_OFFER_AMOUNT}")
        
        if offer_amount > Decimal(settings.MAX_OFFER_AMOUNT):
            raise ValueError("Calculated offer exceeds maximum allowed")
        
        return OfferCalculation(
            offer_amount=offer_amount,
            arv=arv,
            repair_cost=repair_cost,
            margin_percent=margin_percent,
            confidence_level=confidence,
            factors={
                "strategy": strategy,
                "holding_cost": float(holding_cost),
                "sqft": sqft,
                "condition": condition,
                "bedrooms": bedrooms,
                "bathrooms": float(bathrooms) if bathrooms else None,
                "year_built": year_built,
            },
            warnings=warnings
        )
    
    def _calculate_arv(
        self,
        estimated_value: Decimal,
        year_built: Optional[int],
        bedrooms: Optional[int],
        bathrooms: Optional[Decimal]
    ) -> Decimal:
        """Calculate After Repair Value with adjustments"""
        arv = estimated_value
        
        # Age adjustment (very old properties may have higher ARV potential)
        if year_built and year_built < 1950:
            arv *= Decimal("1.05")  # 5% premium for historic properties
        
        # Size adjustment (based on bed/bath count)
        if bedrooms and bedrooms >= 4:
            arv *= Decimal("1.03")  # 3% premium for larger homes
        
        return arv
    
    def _calculate_repair_cost(
        self,
        condition: Optional[str],
        sqft: Optional[int],
        year_built: Optional[int]
    ) -> Decimal:
        """Calculate estimated repair costs"""
        # Default to "fair" condition if not provided
        cond = PropertyCondition(condition) if condition else PropertyCondition.FAIR
        
        # Use average sqft if not provided
        sqft = sqft or 1500
        
        # Base repair cost
        repair_cost = self.REPAIR_COST_PER_SQFT[cond] * Decimal(sqft)
        
        # Age adjustment (older homes need more work)
        if year_built:
            age = 2026 - year_built
            if age > 50:
                repair_cost *= Decimal("1.25")  # 25% increase for very old homes
            elif age > 30:
                repair_cost *= Decimal("1.15")  # 15% increase for old homes
        
        return repair_cost
    
    def _round_to_thousand(self, amount: Decimal) -> Decimal:
        """Round amount to nearest $1000"""
        return (amount / 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 1000


# Singleton instance
offer_engine = OfferEngine()