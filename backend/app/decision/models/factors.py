from pydantic import BaseModel, Field
from typing import Literal, Optional
from decimal import Decimal

class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model: Optional[str] = None
    provider: Optional[str] = None

class OperationalCostBreakdown(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
    input_cost: Decimal
    output_cost: Decimal
    
    human_review_cost: Decimal = Decimal("0.00")
    evidence_cost: Decimal = Decimal("0.00")
    submission_cost: Decimal = Decimal("0.00")
    
    total_operational_cost: Decimal
    
    currency: str
    pricing_source: str
    pricing_version: str

class DeadlineRisk(BaseModel):
    time_remaining_hours: float
    risk: Literal["SAFE", "APPROACHING", "URGENT", "CRITICAL"]
    urgency: Literal["NORMAL", "HIGH", "URGENT", "EXPIRED"]
