from typing import TypedDict, Optional, Annotated
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.decision.models.decision import (
    CaseStrength, ConfidenceAssessment, RiskAssessment, DecisionRecommendation, DecisionExplanation
)
from app.decision.models.factors import DeadlineRisk, TokenUsage, OperationalCostBreakdown
from app.decision.models.human_review import WorkflowStatus
from decimal import Decimal

class DecisionState(TypedDict):
    dispute_id: str
    
    canonical_case: CanonicalCase
    evidence_assessment: EvidenceAssessment
    policy_context: list # list of policy documents

    case_strength: Optional[CaseStrength]
    confidence: Optional[ConfidenceAssessment]
    risk_assessment: Optional[RiskAssessment]

    success_likelihood: Optional[float]

    recoverable_amount: Optional[Decimal]
    expected_recovery: Optional[Decimal]
    operational_cost: Optional[Decimal]          # Phase 5 only cost (for observability)
    net_expected_value: Optional[Decimal]

    token_usage: Annotated[TokenUsage, lambda a, b: TokenUsage(
        input_tokens=(a.input_tokens if a else 0) + (b.input_tokens if b else 0),
        output_tokens=(a.output_tokens if a else 0) + (b.output_tokens if b else 0),
        total_tokens=(a.total_tokens if a else 0) + (b.total_tokens if b else 0),
        model=b.model if b and b.model else (a.model if a else None)
    )]
    operational_cost_breakdown: Optional[OperationalCostBreakdown]

    # Cross-phase (Phases 1-5) cumulative token usage passed in from caller
    cumulative_token_usage: Optional[TokenUsage]
    cumulative_operational_cost: Optional[Decimal]   # used as NEV cost input

    deadline_risk: Optional[DeadlineRisk]

    ai_recommendation: Optional[DecisionRecommendation]
    explanation: Optional[DecisionExplanation]

    workflow_status: WorkflowStatus
    decision_artifact_id: Optional[str]
