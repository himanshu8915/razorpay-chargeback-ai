"""
Dispute-scoped LLM token tracker.

Provides:
  - record_usage()    : persist one LLM invocation row for a dispute
  - aggregate_usage() : deterministic aggregation → cumulative totals + phase breakdown
  - build_cumulative_cost() : price the aggregate using settings

This is the single source of truth for cross-phase operational cost.
It reuses the existing TokenUsage model and OperationalCostBreakdown calculator.
No new pricing logic is introduced; it delegates to calculate_operational_cost().
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional

from app.decision.models.factors import TokenUsage, OperationalCostBreakdown
from app.decision.calculators.operational_cost import calculate_operational_cost

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lightweight in-memory record (no DB dependency in pure logic)
# ---------------------------------------------------------------------------

@dataclass
class PhaseUsage:
    phase: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    input_cost: Decimal = Decimal("0.00")
    output_cost: Decimal = Decimal("0.00")
    total_cost: Decimal = Decimal("0.00")


@dataclass
class CumulativeUsage:
    dispute_id: str
    phases: Dict[str, PhaseUsage] = field(default_factory=dict)

    # Aggregated totals
    @property
    def total_input_tokens(self) -> int:
        return sum(p.input_tokens for p in self.phases.values())

    @property
    def total_output_tokens(self) -> int:
        return sum(p.output_tokens for p in self.phases.values())

    @property
    def total_tokens(self) -> int:
        return sum(p.total_tokens for p in self.phases.values())

    @property
    def cumulative_input_cost(self) -> Decimal:
        return sum((p.input_cost for p in self.phases.values()), Decimal("0.00"))

    @property
    def cumulative_output_cost(self) -> Decimal:
        return sum((p.output_cost for p in self.phases.values()), Decimal("0.00"))

    @property
    def cumulative_operational_cost(self) -> Decimal:
        return sum((p.total_cost for p in self.phases.values()), Decimal("0.00"))

    def to_dict(self) -> dict:
        return {
            "dispute_id": self.dispute_id,
            "phases": {
                phase: {
                    "input_tokens": p.input_tokens,
                    "output_tokens": p.output_tokens,
                    "total_tokens": p.total_tokens,
                    "input_cost": float(p.input_cost),
                    "output_cost": float(p.output_cost),
                    "total_cost": float(p.total_cost),
                }
                for phase, p in self.phases.items()
            },
            "totals": {
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_tokens": self.total_tokens,
                "cumulative_input_cost": float(self.cumulative_input_cost),
                "cumulative_output_cost": float(self.cumulative_output_cost),
                "cumulative_operational_cost": float(self.cumulative_operational_cost),
            },
        }


# ---------------------------------------------------------------------------
# Pure accounting helpers (no DB, fully deterministic)
# ---------------------------------------------------------------------------

def price_token_usage(usage: TokenUsage) -> OperationalCostBreakdown:
    """
    Convert a TokenUsage into an OperationalCostBreakdown using configured pricing.
    Delegates entirely to the existing calculator — no duplicate logic.
    """
    return calculate_operational_cost(usage)


def aggregate_usage_records(records: List[dict]) -> CumulativeUsage:
    """
    Given a list of raw usage dicts (from DB rows or in-memory),
    return a CumulativeUsage grouped by phase.

    Each dict must have:
        dispute_id, phase, input_tokens, output_tokens, total_tokens,
        input_cost, output_cost, total_cost
    """
    if not records:
        return CumulativeUsage(dispute_id="unknown")

    dispute_id = records[0]["dispute_id"]
    cumulative = CumulativeUsage(dispute_id=dispute_id)

    for row in records:
        phase = row["phase"]
        if phase not in cumulative.phases:
            cumulative.phases[phase] = PhaseUsage(phase=phase)
        p = cumulative.phases[phase]
        p.input_tokens += row.get("input_tokens", 0)
        p.output_tokens += row.get("output_tokens", 0)
        p.total_tokens += row.get("total_tokens", 0)
        p.input_cost += Decimal(str(row.get("input_cost", 0.0)))
        p.output_cost += Decimal(str(row.get("output_cost", 0.0)))
        p.total_cost += Decimal(str(row.get("total_cost", 0.0)))

    return cumulative


def build_phase_usage_record(
    dispute_id: str,
    phase: str,
    token_usage: TokenUsage,
    node: Optional[str] = None,
) -> dict:
    """
    Compute pricing for one TokenUsage and return a dict
    ready for DB persistence or in-memory accumulation.
    """
    cost_breakdown = price_token_usage(token_usage)
    return {
        "dispute_id": dispute_id,
        "phase": phase,
        "node": node,
        "model": token_usage.model,
        "input_tokens": token_usage.input_tokens,
        "output_tokens": token_usage.output_tokens,
        "total_tokens": token_usage.total_tokens,
        "input_cost": float(cost_breakdown.input_cost),
        "output_cost": float(cost_breakdown.output_cost),
        "total_cost": float(cost_breakdown.total_operational_cost),
    }


# ---------------------------------------------------------------------------
# DB persistence (async — keeps service layer clean)
# ---------------------------------------------------------------------------

async def persist_usage_record(db, dispute_id: str, phase: str, token_usage: TokenUsage, node: Optional[str] = None) -> None:
    """
    Persist one LLM usage record to the DB asynchronously.
    `db` must be an active AsyncSession.
    Failures are logged but do not propagate — accounting must not break the pipeline.
    """
    from app.db.models import LlmUsageRecordModel  # local import to avoid circular
    try:
        rec = build_phase_usage_record(dispute_id, phase, token_usage, node)
        row = LlmUsageRecordModel(**rec)
        db.add(row)
        await db.flush()  # don't commit here; let the caller manage the transaction
        logger.debug(f"LLM usage persisted: dispute={dispute_id} phase={phase} tokens={token_usage.total_tokens}")
    except Exception as e:
        logger.warning(f"Failed to persist LLM usage record (non-fatal): {e}")


async def fetch_cumulative_usage(db, dispute_id: str) -> CumulativeUsage:
    """
    Fetch all LLM usage records for a dispute from DB and return aggregated CumulativeUsage.
    """
    from sqlalchemy import select
    from app.db.models import LlmUsageRecordModel
    try:
        result = await db.execute(
            select(LlmUsageRecordModel).where(LlmUsageRecordModel.dispute_id == dispute_id)
        )
        rows = result.scalars().all()
        records = [
            {
                "dispute_id": r.dispute_id,
                "phase": r.phase,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "total_tokens": r.total_tokens,
                "input_cost": r.input_cost,
                "output_cost": r.output_cost,
                "total_cost": r.total_cost,
            }
            for r in rows
        ]
        return aggregate_usage_records(records)
    except Exception as e:
        logger.warning(f"Failed to fetch cumulative usage (returning empty): {e}")
        return CumulativeUsage(dispute_id=dispute_id)
