import pytest
from decimal import Decimal
from app.decision.rules.decision_engine import evaluate_decision
from app.decision.models.factors import DeadlineRisk

# Case A: Strong Contest
def test_case_a_strong_contest():
    action, reasons = evaluate_decision(
        has_critical_conflict=False,
        has_policy_ambiguity=False,
        has_missing_critical_evidence=False,
        confidence=0.91,
        case_strength=0.88,
        success_likelihood=0.87,
        recoverable_amount=Decimal("1249.00"),
        expected_recovery=Decimal("1086.63"),
        operational_cost=Decimal("0.00"),
        net_expected_value=Decimal("1086.63"),
        deadline_risk=DeadlineRisk(time_remaining_hours=10, risk="SAFE", urgency="NORMAL")
    )
    assert action == "CONTEST"

# Case B: Weak Case
def test_case_b_weak_case():
    action, reasons = evaluate_decision(
        has_critical_conflict=False,
        has_policy_ambiguity=False,
        has_missing_critical_evidence=False,
        confidence=0.45,
        case_strength=0.30,
        success_likelihood=0.20,
        recoverable_amount=Decimal("1000.00"),
        expected_recovery=Decimal("200.00"),
        operational_cost=Decimal("0.00"),
        net_expected_value=Decimal("200.00"),
        deadline_risk=DeadlineRisk(time_remaining_hours=10, risk="SAFE", urgency="NORMAL")
    )
    # Low confidence -> ESCALATE (per rules)
    assert action == "ESCALATE"

# Case C: Strong But Economically Unattractive
def test_case_c_unprofitable():
    action, reasons = evaluate_decision(
        has_critical_conflict=False,
        has_policy_ambiguity=False,
        has_missing_critical_evidence=False,
        confidence=0.95,
        case_strength=0.95,
        success_likelihood=0.95,
        recoverable_amount=Decimal("50.00"),
        expected_recovery=Decimal("47.50"),
        operational_cost=Decimal("100.00"),
        net_expected_value=Decimal("-52.50"),
        deadline_risk=DeadlineRisk(time_remaining_hours=10, risk="SAFE", urgency="NORMAL")
    )
    assert action == "ACCEPT"

# Case D: Contradictory
def test_case_d_contradictory():
    action, reasons = evaluate_decision(
        has_critical_conflict=True,
        has_policy_ambiguity=False,
        has_missing_critical_evidence=False,
        confidence=0.80,
        case_strength=0.50,
        success_likelihood=0.0,
        recoverable_amount=Decimal("1000.00"),
        expected_recovery=Decimal("0.00"),
        operational_cost=Decimal("0.00"),
        net_expected_value=Decimal("0.00"),
        deadline_risk=DeadlineRisk(time_remaining_hours=10, risk="SAFE", urgency="NORMAL")
    )
    assert action == "ESCALATE"

# Case E: Missing Evidence
def test_case_e_missing_evidence():
    action, reasons = evaluate_decision(
        has_critical_conflict=False,
        has_policy_ambiguity=False,
        has_missing_critical_evidence=True,
        confidence=0.80,
        case_strength=0.50,
        success_likelihood=0.0,
        recoverable_amount=Decimal("1000.00"),
        expected_recovery=Decimal("0.00"),
        operational_cost=Decimal("0.00"),
        net_expected_value=Decimal("0.00"),
        deadline_risk=DeadlineRisk(time_remaining_hours=10, risk="SAFE", urgency="NORMAL")
    )
    assert action == "NEEDS_EVIDENCE"
