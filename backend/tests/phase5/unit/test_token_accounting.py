"""
Cross-phase LLM token accounting tests.

Tests:
  1. Zero pricing — tokens counted, cost zero
  2. Future pricing — cost driven purely by configuration
  3. Multi-phase aggregation
  4. Retry accounting (multiple records for same phase)
  5. Multi-run / cross-dispute isolation
  6. Expected recovery unchanged
  7. NEV uses cumulative cost, not Phase 5 cost alone
  8. Open-source pricing: tokens > 0, cost == 0
  9. Future price config changes economics without code change
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.decision.models.factors import TokenUsage, OperationalCostBreakdown
from app.usage.dispute_token_tracker import (
    aggregate_usage_records,
    build_phase_usage_record,
    price_token_usage,
)
from app.decision.calculators.expected_recovery import (
    calculate_recoverable_amount,
    calculate_expected_recovery,
    calculate_net_expected_value,
)
from app.decision.calculators.operational_cost import calculate_operational_cost


# ---------------------------------------------------------------------------
# Test 1: Zero pricing — tokens are recorded, cost is zero
# ---------------------------------------------------------------------------
def test_zero_pricing_tokens_counted_cost_zero():
    usage = TokenUsage(input_tokens=10_000, output_tokens=2_000, total_tokens=12_000, model="test")
    with patch("app.decision.calculators.operational_cost.settings") as mock_settings:
        mock_settings.llm_input_price_per_1k = 0.0
        mock_settings.llm_output_price_per_1k = 0.0
        breakdown = calculate_operational_cost(usage)

    assert breakdown.input_tokens == 10_000
    assert breakdown.output_tokens == 2_000
    assert breakdown.total_tokens == 12_000
    assert breakdown.total_operational_cost == Decimal("0.00")


# ---------------------------------------------------------------------------
# Test 2: Future pricing — cost is purely configuration-driven
# ---------------------------------------------------------------------------
def test_future_pricing_is_config_driven():
    usage = TokenUsage(input_tokens=1_000, output_tokens=500, total_tokens=1_500, model="test")

    with patch("app.decision.calculators.operational_cost.settings") as mock_settings:
        mock_settings.llm_input_price_per_1k = 1.0   # ₹1 per 1k input tokens
        mock_settings.llm_output_price_per_1k = 2.0  # ₹2 per 1k output tokens
        breakdown = calculate_operational_cost(usage)

    assert breakdown.input_cost == Decimal("1.00")    # 1000/1000 * 1.0
    assert breakdown.output_cost == Decimal("1.00")   # 500/1000 * 2.0
    assert breakdown.total_operational_cost == Decimal("2.00")


# ---------------------------------------------------------------------------
# Test 3: Multi-phase aggregation
# ---------------------------------------------------------------------------
def test_multi_phase_aggregation():
    records = [
        {"dispute_id": "DSP-1", "phase": "phase3", "input_tokens": 8_000, "output_tokens": 2_000, "total_tokens": 10_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
        {"dispute_id": "DSP-1", "phase": "phase3", "input_tokens": 7_000, "output_tokens": 1_000, "total_tokens": 8_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
        {"dispute_id": "DSP-1", "phase": "phase4", "input_tokens": 14_000, "output_tokens": 1_000, "total_tokens": 15_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
        {"dispute_id": "DSP-1", "phase": "phase5", "input_tokens": 20_000, "output_tokens": 5_000, "total_tokens": 25_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
        # phase1, phase2 with known values
        {"dispute_id": "DSP-1", "phase": "phase1", "input_tokens": 9_000, "output_tokens": 1_000, "total_tokens": 10_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
        {"dispute_id": "DSP-1", "phase": "phase2", "input_tokens": 18_000, "output_tokens": 2_000, "total_tokens": 20_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
    ]
    cumulative = aggregate_usage_records(records)

    # Phase 3 = 10k + 8k = 18k total tokens
    assert cumulative.phases["phase3"].total_tokens == 18_000
    # Phase 4 = 15k
    assert cumulative.phases["phase4"].total_tokens == 15_000
    # Phase 5 = 25k
    assert cumulative.phases["phase5"].total_tokens == 25_000
    # Phase 1 = 10k, Phase 2 = 20k
    assert cumulative.phases["phase1"].total_tokens == 10_000
    assert cumulative.phases["phase2"].total_tokens == 20_000
    # Total = 10k+8k+15k+25k+10k+20k = 88k
    assert cumulative.total_tokens == 88_000


# ---------------------------------------------------------------------------
# Test 4: Retry accounting — multiple phase4 records must all count
# ---------------------------------------------------------------------------
def test_retry_accounting():
    records = [
        {"dispute_id": "DSP-1", "phase": "phase4", "input_tokens": 5_000, "output_tokens": 0, "total_tokens": 5_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
        {"dispute_id": "DSP-1", "phase": "phase4", "input_tokens": 5_000, "output_tokens": 0, "total_tokens": 5_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
        {"dispute_id": "DSP-1", "phase": "phase4", "input_tokens": 5_000, "output_tokens": 0, "total_tokens": 5_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
    ]
    cumulative = aggregate_usage_records(records)
    # All three attempts must be counted
    assert cumulative.phases["phase4"].total_tokens == 15_000
    assert cumulative.total_tokens == 15_000


# ---------------------------------------------------------------------------
# Test 5: Multiple runs for one dispute aggregate; no cross-dispute leakage
# ---------------------------------------------------------------------------
def test_multi_run_per_dispute_no_cross_leakage():
    dsp1_records = [
        {"dispute_id": "DSP-1", "phase": "phase5", "input_tokens": 20_000, "output_tokens": 0, "total_tokens": 20_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
        {"dispute_id": "DSP-1", "phase": "phase5", "input_tokens": 30_000, "output_tokens": 0, "total_tokens": 30_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
    ]
    dsp2_records = [
        {"dispute_id": "DSP-2", "phase": "phase5", "input_tokens": 50_000, "output_tokens": 0, "total_tokens": 50_000, "input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
    ]

    c1 = aggregate_usage_records(dsp1_records)
    c2 = aggregate_usage_records(dsp2_records)

    assert c1.total_tokens == 50_000   # run-A + run-B
    assert c2.total_tokens == 50_000   # DSP-2 only
    assert c1.dispute_id == "DSP-1"
    assert c2.dispute_id == "DSP-2"


# ---------------------------------------------------------------------------
# Test 6: Expected recovery formula is unchanged
# ---------------------------------------------------------------------------
def test_expected_recovery_unchanged():
    total_dispute_amount = 1249.0
    p_win = 0.87

    recoverable = calculate_recoverable_amount(total_dispute_amount)
    expected = calculate_expected_recovery(p_win, recoverable)

    assert float(recoverable) == pytest.approx(1249.0)
    assert float(expected) == pytest.approx(1086.63, abs=0.01)


# ---------------------------------------------------------------------------
# Test 7: NEV uses cumulative cost, NOT only Phase 5 cost
# ---------------------------------------------------------------------------
def test_nev_uses_cumulative_cost():
    expected_recovery = Decimal("1000.00")

    phase5_cost = Decimal("20.00")
    prior_phases_cost = Decimal("150.00")
    cumulative_cost = phase5_cost + prior_phases_cost   # ₹170

    nev = calculate_net_expected_value(expected_recovery, cumulative_cost)

    assert nev == Decimal("830.00")   # NOT ₹980 (which would use Phase5 cost alone)


# ---------------------------------------------------------------------------
# Test 8: Open-source pricing — tokens > 0, cost == 0
# ---------------------------------------------------------------------------
def test_open_source_pricing_tokens_nonzero_cost_zero():
    usage = TokenUsage(input_tokens=25_000, output_tokens=5_000, total_tokens=30_000, model="open-source")
    with patch("app.decision.calculators.operational_cost.settings") as mock_settings:
        mock_settings.llm_input_price_per_1k = 0.0
        mock_settings.llm_output_price_per_1k = 0.0
        breakdown = calculate_operational_cost(usage)

    assert breakdown.total_tokens == 30_000
    assert breakdown.total_operational_cost == Decimal("0.00")
    # Tokens are real — not fabricated
    assert breakdown.input_tokens == 25_000
    assert breakdown.output_tokens == 5_000


# ---------------------------------------------------------------------------
# Test 9: Future price config changes economics — no code-path change needed
# ---------------------------------------------------------------------------
def test_future_price_config_changes_economics():
    """
    Same token usage, same code, different config → different economics.
    """
    usage = TokenUsage(input_tokens=10_000, output_tokens=2_000, total_tokens=12_000, model="test")

    # Current: price=0
    with patch("app.decision.calculators.operational_cost.settings") as mock_settings:
        mock_settings.llm_input_price_per_1k = 0.0
        mock_settings.llm_output_price_per_1k = 0.0
        cost_now = calculate_operational_cost(usage).total_operational_cost

    # Future: price configured
    with patch("app.decision.calculators.operational_cost.settings") as mock_settings:
        mock_settings.llm_input_price_per_1k = 2.0
        mock_settings.llm_output_price_per_1k = 4.0
        cost_future = calculate_operational_cost(usage).total_operational_cost

    assert cost_now == Decimal("0.00")
    # 10000/1000*2 + 2000/1000*4 = 20 + 8 = 28
    assert cost_future == Decimal("28.00")
    # Token counts are identical in both
    with patch("app.decision.calculators.operational_cost.settings") as mock_settings:
        mock_settings.llm_input_price_per_1k = 2.0
        mock_settings.llm_output_price_per_1k = 4.0
        b = calculate_operational_cost(usage)
    assert b.total_tokens == 12_000


# ---------------------------------------------------------------------------
# Test: build_phase_usage_record helper
# ---------------------------------------------------------------------------
def test_build_phase_usage_record_zero_pricing():
    usage = TokenUsage(input_tokens=5_000, output_tokens=1_000, total_tokens=6_000, model="test")
    with patch("app.decision.calculators.operational_cost.settings") as mock_settings:
        mock_settings.llm_input_price_per_1k = 0.0
        mock_settings.llm_output_price_per_1k = 0.0
        rec = build_phase_usage_record("DSP-1", "phase3", usage, node="case_planner")

    assert rec["dispute_id"] == "DSP-1"
    assert rec["phase"] == "phase3"
    assert rec["node"] == "case_planner"
    assert rec["input_tokens"] == 5_000
    assert rec["total_tokens"] == 6_000
    assert rec["total_cost"] == 0.0
