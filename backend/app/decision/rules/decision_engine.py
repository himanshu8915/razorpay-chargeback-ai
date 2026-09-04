from decimal import Decimal
from typing import Literal, Tuple, List
from app.decision.models.decision import DecisionRecommendation
from app.decision.models.factors import DeadlineRisk
from app.config.settings import settings

def evaluate_decision(
    has_critical_conflict: bool,
    has_policy_ambiguity: bool,
    has_missing_critical_evidence: bool,
    confidence: float,
    case_strength: float,
    success_likelihood: float,
    recoverable_amount: Decimal,
    expected_recovery: Decimal,
    operational_cost: Decimal,
    net_expected_value: Decimal,
    deadline_risk: DeadlineRisk
) -> Tuple[Literal["CONTEST", "ACCEPT", "ESCALATE", "NEEDS_EVIDENCE"], List[str]]:
    """
    Deterministic Decision Engine evaluating exactly to the architectural rules.
    """
    reasons = []

    # Rule 1 — Critical Conflict
    if has_critical_conflict:
        reasons.append("CRITICAL_CONFLICT")
        return "ESCALATE", reasons

    # Rule 2 — Policy Ambiguity
    if has_policy_ambiguity:
        reasons.append("POLICY_AMBIGUITY")
        return "ESCALATE", reasons

    # Rule 3 — Missing Critical Evidence
    if has_missing_critical_evidence:
        reasons.append("MISSING_CRITICAL_EVIDENCE")
        return "NEEDS_EVIDENCE", reasons

    # Rule 4 — Insufficient Confidence
    if confidence < settings.decision_confidence_threshold:
        reasons.append("INSUFFICIENT_CONFIDENCE")
        return "ESCALATE", reasons

    # Rule 5 — Positive Economics (and sufficient confidence/no conflicts checked above)
    if net_expected_value > Decimal(str(settings.decision_min_nev)):
        reasons.append("POSITIVE_EXPECTED_VALUE")
        if case_strength > 0.7:
            reasons.append("STRONG_CASE")
        return "CONTEST", reasons

    # Rule 6 — Otherwise
    reasons.append("NEGATIVE_OR_LOW_EXPECTED_VALUE")
    return "ACCEPT", reasons
