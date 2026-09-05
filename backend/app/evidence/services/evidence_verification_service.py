import logging
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langsmith import traceable
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.evidence.models.evidence_conflict import EvidenceConflict
from app.evidence.models.evidence_finding import EvidenceFinding
from app.agents.evidence_reasoning.schemas import AgentEvidenceAssessment
from app.agents.evidence_reasoning.evidence_reasoning_agent import reason_evidence
from app.evidence.reasoning.grounding_validator import validate_grounding
from app.evidence.reasoning.completeness import determine_completeness
from app.evidence.reasoning.conflict_detector import detect_conflicts
from app.evidence.reasoning.confidence import calculate_confidence
from app.decision.models.factors import TokenUsage
from app.api.v1.endpoints.execution_state import execution_registry

logger = logging.getLogger(__name__)

class VerificationState(TypedDict):
    case: CanonicalCase
    bundle: EvidenceBundle
    agent_assessment: Optional[AgentEvidenceAssessment]
    validation_errors: List[str]
    retry_count: int
    completeness: str
    missing_critical: List[str]
    conflicts: List[EvidenceConflict]
    confidence: float
    final_assessment: Optional[EvidenceAssessment]
    # Token usage accumulated across all retry attempts
    token_usage: Optional[TokenUsage]
    usage_attempts: List[TokenUsage]

def reasoning_node(state: VerificationState) -> dict:
    dispute_id = state["case"].dispute.dispute_id
    logger.info("Executing reasoning node")
    execution_registry.update_node(dispute_id, "node_reasoning", "Executing reasoning node...")
    # if we have validation errors from a previous run, the prompt should ideally be stricter.
    # For now we just rerun.
    assessment, usage = reason_evidence(state["case"], state["bundle"])
    # Accumulate usage across all reasoning attempts (retries count!)
    existing = state.get("token_usage") or TokenUsage()
    accumulated = TokenUsage(
        input_tokens=existing.input_tokens + usage.input_tokens,
        output_tokens=existing.output_tokens + usage.output_tokens,
        total_tokens=existing.total_tokens + usage.total_tokens,
        model=usage.model
    )
    usage_attempts = state.get("usage_attempts", []) + [usage]
    return {"agent_assessment": assessment, "token_usage": accumulated, "usage_attempts": usage_attempts}

def validation_node(state: VerificationState) -> dict:
    dispute_id = state["case"].dispute.dispute_id
    logger.info("Executing validation node")
    execution_registry.update_node(dispute_id, "node_validation", "Executing validation node...")
    is_valid, errors = validate_grounding(state["agent_assessment"], state["bundle"])
    return {"validation_errors": errors, "retry_count": state["retry_count"] + 1}

def routing_after_validation(state: VerificationState) -> str:
    if state["validation_errors"]:
        if state["retry_count"] < 2:
            logger.warning(f"Validation failed, retrying. Errors: {state['validation_errors']}")
            return "reasoning"
        else:
            logger.error("Max retries reached for validation.")
            return "completeness" # proceed with what we have, or could fail
    return "completeness"

def completeness_node(state: VerificationState) -> dict:
    dispute_id = state["case"].dispute.dispute_id
    logger.info("Executing completeness node")
    execution_registry.update_node(dispute_id, "node_completeness", "Executing completeness node...")
    comp, missing = determine_completeness(state["bundle"])
    return {"completeness": comp, "missing_critical": missing}

def conflict_node(state: VerificationState) -> dict:
    dispute_id = state["case"].dispute.dispute_id
    logger.info("Executing conflict node")
    execution_registry.update_node(dispute_id, "node_conflict", "Executing conflict node...")
    conflicts = detect_conflicts(state["bundle"])
    return {"conflicts": conflicts}

def confidence_node(state: VerificationState) -> dict:
    dispute_id = state["case"].dispute.dispute_id
    logger.info("Executing confidence node")
    execution_registry.update_node(dispute_id, "node_confidence_verification", "Executing confidence node...")
    conf = calculate_confidence(
        state["agent_assessment"], 
        state["completeness"], 
        state["conflicts"],
        has_grounding_failure=len(state["validation_errors"]) > 0
    )
    return {"confidence": conf}

def build_assessment_node(state: VerificationState) -> dict:
    dispute_id = state["case"].dispute.dispute_id
    logger.info("Executing build assessment node")
    execution_registry.update_node(dispute_id, "node_build", "Executing build assessment node...")
    agent_output = state["agent_assessment"]
    
    # Categorize evidence based on findings
    supporting = [f.evidence_id for f in agent_output.evidence_findings if f.relationship == "supports"]
    contradicting = [f.evidence_id for f in agent_output.evidence_findings if f.relationship == "contradicts"]
    neutral = [f.evidence_id for f in agent_output.evidence_findings if f.relationship == "does_not_address"]
    
    # Risk flags
    risk_flags = []
    if state["completeness"] == "insufficient":
        risk_flags.append("INSUFFICIENT_EVIDENCE")
    if state["conflicts"]:
        risk_flags.append("CONFLICTING_EVIDENCE")
    if state["confidence"] < 0.6:
        risk_flags.append("LOW_REASONING_CONFIDENCE")
    if state["validation_errors"]:
        risk_flags.append("GROUNDING_FAILURE")
        
    assessment = EvidenceAssessment(
        dispute_id=state["case"].dispute.dispute_id,
        evidence_findings=agent_output.evidence_findings,
        supporting_evidence=supporting,
        contradicting_evidence=contradicting,
        non_probative_evidence=neutral,
        missing_evidence=state["missing_critical"],
        conflicts=state["conflicts"],
        policy_findings=list(set(p for f in agent_output.evidence_findings for p in f.policy_basis)),
        completeness=state["completeness"],
        overall_assessment=agent_output.overall_assessment,
        confidence=state["confidence"],
        risk_flags=risk_flags
    )
    return {"final_assessment": assessment}

def build_verification_graph() -> StateGraph:
    workflow = StateGraph(VerificationState)
    
    workflow.add_node("node_reasoning", reasoning_node)
    workflow.add_node("node_validation", validation_node)
    workflow.add_node("node_completeness", completeness_node)
    workflow.add_node("node_conflict", conflict_node)
    workflow.add_node("node_confidence", confidence_node)
    workflow.add_node("node_build", build_assessment_node)
    
    workflow.set_entry_point("node_reasoning")
    
    workflow.add_edge("node_reasoning", "node_validation")
    workflow.add_conditional_edges(
        "node_validation",
        routing_after_validation,
        {
            "reasoning": "node_reasoning",
            "completeness": "node_completeness"
        }
    )
    
    workflow.add_edge("node_completeness", "node_conflict")
    workflow.add_edge("node_conflict", "node_confidence")
    workflow.add_edge("node_confidence", "node_build")
    workflow.add_edge("node_build", END)
    
    return workflow.compile()

from app.db.session import AsyncSessionLocal
from app.usage.dispute_token_tracker import persist_usage_record

class EvidenceVerificationService:
    def __init__(self):
        self.graph = build_verification_graph()
        
    @traceable(name="evidence_verification")
    async def verify_evidence(self, case: CanonicalCase, bundle: EvidenceBundle) -> tuple[EvidenceAssessment, TokenUsage]:
        """
        Verify evidence and return (EvidenceAssessment, TokenUsage).
        TokenUsage accumulates all reasoning retry attempts for Phase 4 cost accounting.
        Persists each attempt iteratively to DB.
        """
        logger.info(f"PHASE_4_STARTED: Starting Evidence Verification for {case.dispute.dispute_id}")
        initial_state = {
            "case": case,
            "bundle": bundle,
            "agent_assessment": None,
            "validation_errors": [],
            "retry_count": 0,
            "completeness": "",
            "missing_critical": [],
            "conflicts": [],
            "confidence": 0.0,
            "final_assessment": None,
            "token_usage": TokenUsage(),  # accumulate across retries
            "usage_attempts": []
        }
        
        import asyncio
        result = await asyncio.to_thread(self.graph.invoke, initial_state)
        final = result["final_assessment"]
        usage = result.get("token_usage") or TokenUsage()
        attempts = result.get("usage_attempts", [])
        
        # Persist each attempt individually
        db = AsyncSessionLocal()
        try:
            for i, attempt in enumerate(attempts):
                await persist_usage_record(db, case.dispute.dispute_id, "phase4", attempt, node=f"reasoning_node_attempt_{i+1}")
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to persist Phase 4 tokens: {e}")
        finally:
            await db.close()
        
        logger.info(f"PHASE_4_COMPLETED: Completeness: {final.completeness}, Confidence: {final.confidence}, Tokens: {usage.total_tokens} across {len(attempts)} attempts")
        return final, usage
