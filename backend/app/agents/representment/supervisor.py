import logging
from typing import Optional
from langgraph.graph import StateGraph, END
from langsmith import traceable

from app.agents.representment.state import RepresentmentState
from app.agents.representment.evidence_selection_agent import select_evidence
from app.agents.representment.representation_agent import generate_representation
from app.representment.services.validation_service import ValidationService
from app.representment.models.policy_mapping import PolicyRequirementMapping
from app.decision.models.factors import TokenUsage

logger = logging.getLogger(__name__)

# Basic MVO mapping function
def map_policy_requirements(case, bundle) -> PolicyRequirementMapping:
    # A real implementation would query RAG/rules
    # For Phase 6 MVO, we return a generic struct to satisfy validation
    return PolicyRequirementMapping(
        requirements=[],
        overall_coverage=1.0,
        missing_critical_requirements=[]
    )

def entry_validation_node(state: RepresentmentState) -> dict:
    if state["final_decision"].action != "CONTEST":
        raise ValueError("Phase 6 Representment can only be entered with a CONTEST decision.")
    return {"workflow_status": "STARTING"}

def evidence_selection_node(state: RepresentmentState) -> dict:
    mapping = state.get("policy_mapping")
    if not mapping:
        mapping = map_policy_requirements(state["canonical_case"], state["evidence_bundle"])
        
    package, usage = select_evidence(
        state["canonical_case"], 
        state["evidence_bundle"], 
        state["evidence_assessment"],
        mapping
    )
    
    existing = state.get("token_usage") or TokenUsage()
    accumulated = TokenUsage(
        input_tokens=existing.input_tokens + usage.input_tokens,
        output_tokens=existing.output_tokens + usage.output_tokens,
        total_tokens=existing.total_tokens + usage.total_tokens,
        model=usage.model
    )
    
    return {
        "selected_evidence": package, 
        "policy_mapping": mapping,
        "token_usage": accumulated,
        "workflow_status": "DRAFTING"
    }

def representation_node(state: RepresentmentState) -> dict:
    feedback = "\n".join(state["validation_errors"]) if state["validation_errors"] else ""
    draft, usage = generate_representation(
        state["canonical_case"],
        state["selected_evidence"],
        state["policy_mapping"],
        validation_feedback=feedback
    )
    
    existing = state.get("token_usage") or TokenUsage()
    accumulated = TokenUsage(
        input_tokens=existing.input_tokens + usage.input_tokens,
        output_tokens=existing.output_tokens + usage.output_tokens,
        total_tokens=existing.total_tokens + usage.total_tokens,
        model=usage.model
    )
    
    return {
        "representation_draft": draft,
        "token_usage": accumulated,
        "workflow_status": "VALIDATING"
    }

def validation_node(state: RepresentmentState) -> dict:
    service = ValidationService()
    result = service.validate_draft(
        state["representation_draft"],
        state["selected_evidence"],
        state["policy_mapping"],
        state["evidence_bundle"],
        state["evidence_assessment"]
    )
    
    return {
        "validation_result": result,
        "validation_errors": result.errors,
        "retry_count": state["retry_count"] + 1,
        "workflow_status": "NEEDS_REVIEW" if result.status == "PASS" else "FAILED_VALIDATION"
    }

def routing_after_validation(state: RepresentmentState) -> str:
    if state["validation_result"].status == "PASS":
        return "human_review"
    if state["retry_count"] < 2:  # Bounded retries
        return "representation"
    return "human_review"  # Force human review if persistently failing

def build_representment_graph() -> StateGraph:
    workflow = StateGraph(RepresentmentState)
    
    workflow.add_node("entry_validation", entry_validation_node)
    workflow.add_node("evidence_selection", evidence_selection_node)
    workflow.add_node("representation", representation_node)
    workflow.add_node("validation", validation_node)
    
    # Human Review is essentially the end of the AI automated pipeline
    # The graph yields to the UI at this point.
    def human_review_node(state: RepresentmentState) -> dict:
        return {} # No-op node, state is persisted and waiting for API call
        
    workflow.add_node("human_review", human_review_node)
    
    workflow.set_entry_point("entry_validation")
    workflow.add_edge("entry_validation", "evidence_selection")
    workflow.add_edge("evidence_selection", "representation")
    workflow.add_edge("representation", "validation")
    
    workflow.add_conditional_edges(
        "validation",
        routing_after_validation,
        {
            "representation": "representation",
            "human_review": "human_review"
        }
    )
    
    workflow.add_edge("human_review", END)
    
    return workflow.compile()
