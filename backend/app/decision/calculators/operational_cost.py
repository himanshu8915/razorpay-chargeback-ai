from decimal import Decimal
from typing import Dict, Optional
from pydantic import BaseModel
from app.decision.models.factors import TokenUsage, OperationalCostBreakdown

class TokenPricingConfig(BaseModel):
    model: str
    input_cost_per_1k_tokens: Decimal
    output_cost_per_1k_tokens: Decimal
    currency: str = "INR"

from app.config.settings import settings

def get_pricing_config(model_name: Optional[str]) -> TokenPricingConfig:
    # Use global settings for token pricing per the MVO architecture requirements
    return TokenPricingConfig(
        model=model_name or "default",
        input_cost_per_1k_tokens=Decimal(str(settings.llm_input_price_per_1k)),
        output_cost_per_1k_tokens=Decimal(str(settings.llm_output_price_per_1k))
    )

def calculate_operational_cost(
    token_usage: TokenUsage,
    human_review_cost: Decimal = Decimal("0.0"),
    evidence_cost: Decimal = Decimal("0.0"),
    submission_cost: Decimal = Decimal("0.0")
) -> OperationalCostBreakdown:
    
    pricing = get_pricing_config(token_usage.model)
    
    input_cost = (Decimal(token_usage.input_tokens) / Decimal("1000")) * pricing.input_cost_per_1k_tokens
    output_cost = (Decimal(token_usage.output_tokens) / Decimal("1000")) * pricing.output_cost_per_1k_tokens
    
    # Quantize to 2 decimal places
    input_cost = input_cost.quantize(Decimal("0.01"))
    output_cost = output_cost.quantize(Decimal("0.01"))
    
    total_cost = input_cost + output_cost + human_review_cost + evidence_cost + submission_cost
    total_cost = total_cost.quantize(Decimal("0.01"))
    
    return OperationalCostBreakdown(
        input_tokens=token_usage.input_tokens,
        output_tokens=token_usage.output_tokens,
        total_tokens=token_usage.total_tokens,
        input_cost=input_cost,
        output_cost=output_cost,
        human_review_cost=human_review_cost,
        evidence_cost=evidence_cost,
        submission_cost=submission_cost,
        total_operational_cost=total_cost,
        currency=pricing.currency,
        pricing_source="config",
        pricing_version="v1"
    )
