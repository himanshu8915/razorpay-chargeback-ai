import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.agents.decision.supervisor import build_decision_graph
from app.db.models import DecisionArtifactModel
from app.db.session import AsyncSessionLocal
from app.decision.models.factors import TokenUsage
from app.config.settings import settings
from app.usage.dispute_token_tracker import (
    build_phase_usage_record,
    aggregate_usage_records,
    fetch_cumulative_usage,
    persist_usage_record,
    price_token_usage,
)

logger = logging.getLogger(__name__)


class DecisionService:
    def __init__(self):
        self.graph = build_decision_graph()

    async def analyze_dispute(
        self,
        dispute_id: str,
        canonical_case: CanonicalCase,
        evidence_assessment: EvidenceAssessment,
        policy_context: list,
        prior_phases_usage: Optional[TokenUsage] = None,  # Phase 3 + 4 tokens from caller
    ) -> dict:
        """
        Run Phase 5 decision analysis.

        prior_phases_usage: combined token usage from Phase 3 and Phase 4 already
        calculated by the caller. Used to compute cumulative_operational_cost for NEV.
        """
        logger.info(f"PHASE_5_STARTED: Starting Decision Analysis for {dispute_id}")

        # Calculate cumulative cost from prior phases so NEV uses the full picture
        prior_cost = Decimal("0.00")
        if prior_phases_usage:
            prior_breakdown = price_token_usage(prior_phases_usage)
            prior_cost = prior_breakdown.total_operational_cost

        initial_state = {
            "dispute_id": dispute_id,
            "canonical_case": canonical_case,
            "evidence_assessment": evidence_assessment,
            "policy_context": policy_context,
            "cumulative_token_usage": prior_phases_usage,
            "cumulative_operational_cost": prior_cost,
        }

        # Invoke LangGraph Phase 5 Supervisor
        import asyncio
        result = await asyncio.to_thread(self.graph.invoke, initial_state)

        # Phase 5 token usage from all specialist agents
        phase5_usage = result.get("token_usage") or TokenUsage()

        # Build full cumulative usage = prior phases + phase5
        total_cumulative = TokenUsage(
            input_tokens=(prior_phases_usage.input_tokens if prior_phases_usage else 0) + phase5_usage.input_tokens,
            output_tokens=(prior_phases_usage.output_tokens if prior_phases_usage else 0) + phase5_usage.output_tokens,
            total_tokens=(prior_phases_usage.total_tokens if prior_phases_usage else 0) + phase5_usage.total_tokens,
            model=phase5_usage.model,
        )
        total_cumulative_breakdown = price_token_usage(total_cumulative)

        # Persist Phase 5 usage record
        artifact_id = f"DA-{uuid.uuid4().hex[:12].upper()}"
        
        def _json_safe(obj):
            if isinstance(obj, dict):
                return {k: _json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_json_safe(v) for v in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj

        db = AsyncSessionLocal()
        try:
            # Persist Phase 5 token usage
            await persist_usage_record(db, dispute_id, "phase5", phase5_usage, node="supervisor")

            ai_rec = result.get("ai_recommendation")
            evidence = result.get("evidence_assessment")
            explanation = result.get("explanation")
            
            # Map evidence list correctly
            key_evidence = explanation.sources if explanation and explanation.sources else evidence.supporting_evidence
            
            decision_artifact = DecisionArtifactModel(
                decision_artifact_id=artifact_id,
                dispute_id=dispute_id,
                
                decision=ai_rec.action if ai_rec else "HUMAN_REVIEW_REQUIRED",
                confidence=result.get("confidence", {}).confidence if result.get("confidence") else 0.0,
                case_strength=result.get("case_strength", {}).case_strength if result.get("case_strength") else 0.0,
                success_likelihood=result.get("success_likelihood", 0.0),
                
                recoverable_amount=float(result.get("recoverable_amount", 0.0)),
                expected_recovery=float(result.get("expected_recovery", 0.0)),
                estimated_operational_cost=float(result.get("operational_cost", 0.0)),
                net_expected_value=float(result.get("net_expected_value", 0.0)),
                
                token_usage={
                    "input_tokens": total_cumulative.input_tokens,
                    "output_tokens": total_cumulative.output_tokens,
                    "total_tokens": total_cumulative.total_tokens
                },
                token_cost={
                    "input_cost": float(total_cumulative_breakdown.input_cost),
                    "output_cost": float(total_cumulative_breakdown.output_cost),
                    "total_cost": float(total_cumulative_breakdown.total_operational_cost)
                },
                
                reason_codes=ai_rec.reason_codes if ai_rec else [],
                key_evidence=key_evidence,
                supporting_evidence=evidence.supporting_evidence if evidence else [],
                contradicting_evidence=evidence.contradicting_evidence if evidence else [],
                missing_evidence=evidence.missing_evidence if evidence else [],
                risk_flags=evidence.risk_flags if evidence else [],
                
                deadline=result.get("canonical_case").deadline.isoformat() if result.get("canonical_case") and result.get("canonical_case").deadline else None,
                deadline_risk=result.get("deadline_risk").risk if result.get("deadline_risk") else "MEDIUM",
                next_action=explanation.next_action if explanation else "HUMAN_REVIEW",
                rationale=explanation.summary if explanation else "",
                
                workflow_status=result.get("workflow_status", "NEEDS_REVIEW"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(decision_artifact)
            await db.commit()
            await db.refresh(decision_artifact)
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to persist decision artifact: {e}")
            raise
        finally:
            await db.close()

        logger.info(
            f"PHASE_5_COMPLETED: Analysis complete for {dispute_id}. "
            f"Workflow: {result['workflow_status']}. "
            f"Phase5 tokens: {phase5_usage.total_tokens}. "
            f"Cumulative tokens: {total_cumulative.total_tokens}."
        )

        return {
            "decision_artifact_id": artifact_id,
            "dispute_id": dispute_id,
            "workflow_status": result["workflow_status"],
            "ai_recommendation": result["ai_recommendation"].model_dump(),
            "phase5_token_usage": {
                "input_tokens": phase5_usage.input_tokens,
                "output_tokens": phase5_usage.output_tokens,
                "total_tokens": phase5_usage.total_tokens,
            },
            "cumulative_token_usage": {
                "input_tokens": total_cumulative.input_tokens,
                "output_tokens": total_cumulative.output_tokens,
                "total_tokens": total_cumulative.total_tokens,
            },
        }

    async def get_decision(self, dispute_id: str) -> Optional[dict]:
        db = AsyncSessionLocal()
        try:
            result = await db.execute(
                select(DecisionArtifactModel)
                .filter(DecisionArtifactModel.dispute_id == dispute_id)
                .order_by(DecisionArtifactModel.created_at.desc())
                .limit(1)
            )
            artifact = result.scalar_one_or_none()

            if not artifact:
                return None

            # Return directly mapping to the authoritative DecisionArtifact schema
            return {
                "decision": artifact.decision,
                "confidence": artifact.confidence,
                "case_strength": artifact.case_strength,
                "success_likelihood": artifact.success_likelihood,
                
                "recoverable_amount": artifact.recoverable_amount,
                "expected_recovery": artifact.expected_recovery,
                "estimated_operational_cost": artifact.estimated_operational_cost,
                "net_expected_value": artifact.net_expected_value,
                
                "token_usage": artifact.token_usage,
                "token_cost": artifact.token_cost,
                
                "reason_codes": artifact.reason_codes,
                "key_evidence": artifact.key_evidence,
                "supporting_evidence": artifact.supporting_evidence,
                "contradicting_evidence": artifact.contradicting_evidence,
                "missing_evidence": artifact.missing_evidence,
                "risk_flags": artifact.risk_flags,
                
                "deadline": artifact.deadline,
                "deadline_risk": artifact.deadline_risk,
                "next_action": artifact.next_action,
                "rationale": artifact.rationale,

                # Also returning ID and workflow status for metadata
                "decision_artifact_id": artifact.decision_artifact_id,
                "dispute_id": artifact.dispute_id,
                "workflow_status": artifact.workflow_status,
                "created_at": artifact.created_at.isoformat(),
                "updated_at": artifact.updated_at.isoformat(),
                "llm_model": settings.llm_model,
            }
        finally:
            await db.close()

    async def append_token_usage(self, dispute_id: str, additional_usage: TokenUsage) -> None:
        """
        Append additional token usage (e.g., from Phase 6) to the decision artifact,
        recalculate the cost, and update Net Expected Value.
        """
        db = AsyncSessionLocal()
        try:
            result = await db.execute(
                select(DecisionArtifactModel)
                .filter(DecisionArtifactModel.dispute_id == dispute_id)
                .order_by(DecisionArtifactModel.created_at.desc())
                .limit(1)
            )
            artifact = result.scalar_one_or_none()
            if not artifact:
                return
            
            # Combine usage
            current_usage = artifact.token_usage or {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            new_input = current_usage.get("input_tokens", 0) + additional_usage.input_tokens
            new_output = current_usage.get("output_tokens", 0) + additional_usage.output_tokens
            new_total = current_usage.get("total_tokens", 0) + additional_usage.total_tokens
            
            combined_usage = TokenUsage(
                input_tokens=new_input,
                output_tokens=new_output,
                total_tokens=new_total,
                model=additional_usage.model
            )
            
            # Recalculate cost
            from app.decision.calculators.operational_cost import calculate_operational_cost
            cost_breakdown = calculate_operational_cost(combined_usage)
            
            # Update fields
            artifact.token_usage = {
                "input_tokens": combined_usage.input_tokens,
                "output_tokens": combined_usage.output_tokens,
                "total_tokens": combined_usage.total_tokens
            }
            artifact.token_cost = {
                "input_cost": float(cost_breakdown.input_cost),
                "output_cost": float(cost_breakdown.output_cost),
                "total_cost": float(cost_breakdown.total_operational_cost)
            }
            artifact.estimated_operational_cost = float(cost_breakdown.total_operational_cost)
            artifact.net_expected_value = float(artifact.expected_recovery) - artifact.estimated_operational_cost
            artifact.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to append token usage: {e}")
            raise
        finally:
            await db.close()
