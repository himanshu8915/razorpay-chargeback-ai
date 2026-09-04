from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime
from decimal import Decimal

class CaseStrength(BaseModel):
    case_strength: float = Field(description="Deterministic/scored case strength 0.0 to 1.0", ge=0.0, le=1.0)
    supporting_factors: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    critical_conflicts: List[str] = Field(default_factory=list)

class ConfidenceAssessment(BaseModel):
    confidence: Optional[float] = Field(None, description="Deterministic confidence 0.0 to 1.0", ge=0.0, le=1.0)
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"]
    reasons: List[str] = Field(default_factory=list)

class RiskAssessment(BaseModel):
    critical_conflict: bool = Field(description="True if a critical evidence conflict exists")
    missing_critical_evidence: bool = Field(description="True if mandatory evidence is missing")
    policy_ambiguity: bool = Field(description="True if policy does not clearly cover the scenario")
    risk_level: Literal["HIGH", "MEDIUM", "LOW"]
    reasons: List[str] = Field(default_factory=list)

class DecisionRecommendation(BaseModel):
    action: Literal["CONTEST", "ACCEPT", "ESCALATE", "NEEDS_EVIDENCE"]
    confidence: float = Field(ge=0.0, le=1.0)
    case_strength: float = Field(ge=0.0, le=1.0)
    success_likelihood: float = Field(ge=0.0, le=1.0)
    recoverable_amount: Decimal
    expected_recovery: Decimal
    operational_cost: Decimal
    net_expected_value: Decimal
    deadline_risk: Literal["SAFE", "APPROACHING", "URGENT", "CRITICAL"]
    reason_codes: List[str] = Field(default_factory=list)
    decision_factors: List[str] = Field(default_factory=list)

class DecisionExplanation(BaseModel):
    summary: str
    why_we_believe_we_can_win: List[str] = Field(default_factory=list)
    supporting_evidence: List[dict] = Field(default_factory=list, description="List of dicts with evidence_id and reason")
    contradicting_evidence: List[dict] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    economic_summary: str
    deadline_summary: str
    next_action: str
    sources: List[str] = Field(default_factory=list, description="List of evidence or policy IDs cited")

class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

class TokenCost(BaseModel):
    input_cost: Decimal = Decimal("0.00")
    output_cost: Decimal = Decimal("0.00")
    total_cost: Decimal = Decimal("0.00")

class DecisionArtifact(BaseModel):
    decision: Literal["CONTEST", "ACCEPT", "ESCALATE", "HUMAN_REVIEW_REQUIRED"]
    confidence: float = Field(ge=0.0, le=1.0)
    case_strength: float = Field(ge=0.0, le=1.0)
    success_likelihood: float = Field(ge=0.0, le=1.0)
    expected_recovery: Decimal
    recoverable_amount: Decimal
    estimated_operational_cost: Decimal
    token_usage: TokenUsage
    token_cost: TokenCost
    net_expected_value: Decimal
    reason_codes: List[str] = Field(default_factory=list)
    key_evidence: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    deadline: Optional[str] = None
    deadline_risk: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    next_action: str
    rationale: str

class FinalDecision(BaseModel):
    action: Literal["CONTEST", "ACCEPT", "ESCALATE"]
    reason: Optional[str] = None
    response_payload: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
