import pytest
from decimal import Decimal
from app.decision.rules.decision_engine import evaluate_decision
from app.decision.models.factors import DeadlineRisk

@pytest.fixture
def base_args():
    return {
        "has_critical_conflict": False,
        "has_policy_ambiguity": False,
        "has_missing_critical_evidence": False,
        "confidence": 0.90,
        "case_strength": 0.85,
        "success_likelihood": 0.85,
        "recoverable_amount": Decimal("1000.00"),
        "expected_recovery": Decimal("850.00"),
        "operational_cost": Decimal("0.00"),
        "net_expected_value": Decimal("850.00"),
        "deadline_risk": DeadlineRisk(time_remaining_hours=100, risk="SAFE", urgency="NORMAL")
    }

def test_rule_4_confidence_boundary(base_args):
    args = base_args.copy()
    from app.config.settings import settings
    args["confidence"] = settings.decision_confidence_threshold - 0.01
    action, reasons = evaluate_decision(**args)
    assert action == "ESCALATE"
    assert "INSUFFICIENT_CONFIDENCE" in reasons
    
    args["confidence"] = settings.decision_confidence_threshold
    action, reasons = evaluate_decision(**args)
    assert action == "CONTEST"

def test_rule_5_nev_boundary(base_args):
    args = base_args.copy()
    from app.config.settings import settings
    args["net_expected_value"] = Decimal(str(settings.decision_min_nev))
    action, reasons = evaluate_decision(**args)
    assert action == "ACCEPT"
    assert "NEGATIVE_OR_LOW_EXPECTED_VALUE" in reasons
    
    args["net_expected_value"] = Decimal(str(settings.decision_min_nev)) + Decimal("0.01")
    action, reasons = evaluate_decision(**args)
    assert action == "CONTEST"

def test_rule_1_critical_conflict(base_args):
    args = base_args.copy()
    args["has_critical_conflict"] = True
    action, reasons = evaluate_decision(**args)
    assert action == "ESCALATE"
    assert "CRITICAL_CONFLICT" in reasons

def test_rule_2_policy_ambiguity(base_args):
    args = base_args.copy()
    args["has_policy_ambiguity"] = True
    action, reasons = evaluate_decision(**args)
    assert action == "ESCALATE"
    assert "POLICY_AMBIGUITY" in reasons

def test_rule_3_missing_evidence(base_args):
    args = base_args.copy()
    args["has_missing_critical_evidence"] = True
    action, reasons = evaluate_decision(**args)
    assert action == "NEEDS_EVIDENCE"
    assert "MISSING_CRITICAL_EVIDENCE" in reasons

def test_rule_4_low_confidence(base_args):
    args = base_args.copy()
    args["confidence"] = 0.50 # Below threshold
    action, reasons = evaluate_decision(**args)
    assert action == "ESCALATE"
    assert "INSUFFICIENT_CONFIDENCE" in reasons

def test_rule_5_positive_nev(base_args):
    args = base_args.copy()
    action, reasons = evaluate_decision(**args)
    assert action == "CONTEST"
    assert "POSITIVE_EXPECTED_VALUE" in reasons

def test_rule_6_negative_nev(base_args):
    args = base_args.copy()
    args["net_expected_value"] = Decimal("-50.00")
    action, reasons = evaluate_decision(**args)
    assert action == "ACCEPT"
    assert "NEGATIVE_OR_LOW_EXPECTED_VALUE" in reasons

def test_priority_ordering(base_args):
    # Missing evidence vs low confidence -> missing evidence has priority (Rule 3 > 4)
    args = base_args.copy()
    args["has_missing_critical_evidence"] = True
    args["confidence"] = 0.10
    action, reasons = evaluate_decision(**args)
    assert action == "NEEDS_EVIDENCE"

    # Critical conflict vs missing evidence -> critical conflict has priority (Rule 1 > 3)
    args["has_critical_conflict"] = True
    action, reasons = evaluate_decision(**args)
    assert action == "ESCALATE"
    assert "CRITICAL_CONFLICT" in reasons
