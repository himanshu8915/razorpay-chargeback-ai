import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from app.decision.calculators.expected_recovery import calculate_expected_recovery, calculate_recoverable_amount, calculate_net_expected_value
from app.decision.calculators.deadline_risk import calculate_deadline_risk
from app.decision.calculators.operational_cost import calculate_operational_cost
from app.decision.models.factors import TokenUsage

def test_recoverable_amount():
    assert calculate_recoverable_amount(1249.00) == Decimal("1249.0")
    assert calculate_recoverable_amount(0.0) == Decimal("0.0")

def test_expected_recovery():
    # P=0
    assert calculate_expected_recovery(0.0, Decimal("1000")) == Decimal("0.00")
    # P=1
    assert calculate_expected_recovery(1.0, Decimal("1000")) == Decimal("1000.00")
    # P=0.87
    assert calculate_expected_recovery(0.87, Decimal("1249")) == Decimal("1086.63")

def test_net_expected_value():
    assert calculate_net_expected_value(Decimal("1086.63"), Decimal("0.00")) == Decimal("1086.63")
    assert calculate_net_expected_value(Decimal("1086.63"), Decimal("120.00")) == Decimal("966.63")
    assert calculate_net_expected_value(Decimal("100.00"), Decimal("200.00")) == Decimal("-100.00")

def test_deadline_risk():
    now = datetime.now(timezone.utc)
    
    # Safe
    safe_deadline = now + timedelta(days=5)
    risk = calculate_deadline_risk(safe_deadline, now)
    assert risk.risk == "SAFE"
    assert risk.urgency == "NORMAL"
    
    # Approaching
    approaching = now + timedelta(hours=70)
    risk = calculate_deadline_risk(approaching, now)
    assert risk.risk == "APPROACHING"
    assert risk.urgency == "HIGH"
    
    # Urgent
    urgent = now + timedelta(hours=20)
    risk = calculate_deadline_risk(urgent, now)
    assert risk.risk == "CRITICAL"
    assert risk.urgency == "URGENT"
    
    # Expired
    expired = now - timedelta(hours=1)
    risk = calculate_deadline_risk(expired, now)
    assert risk.risk == "CRITICAL"
    assert risk.urgency == "EXPIRED"

def test_operational_cost_zero_pricing():
    # Using default zero-priced open source model config
    usage = TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500, model="default")
    cost = calculate_operational_cost(usage)
    assert cost.input_cost == Decimal("0.00")
    assert cost.output_cost == Decimal("0.00")
    assert cost.total_operational_cost == Decimal("0.00")
