import logging
from langgraph.graph import StateGraph, END
from app.agents.decision.state import DecisionState
from app.agents.decision.case_strength_agent import analyze_case_strength
from app.agents.decision.confidence_agent import analyze_confidence
from app.agents.decision.risk_agent import analyze_risk
from app.agents.decision.explanation_agent import generate_explanation
from app.decision.calculators.success_likelihood import calculate_success_likelihood
from app.decision.calculators.expected_recovery import calculate_recoverable_amount, calculate_expected_recovery, calculate_net_expected_value
from app.decision.calculators.operational_cost import calculate_operational_cost
from app.decision.calculators.deadline_risk import calculate_deadline_risk
from app.decision.rules.decision_engine import evaluate_decision
from app.decision.models.decision import DecisionRecommendation
from app.decision.models.factors import TokenUsage
from app.api.v1.endpoints.execution_state import execution_registry

logger = logging.getLogger(__name__)

def add_token_usage(state: DecisionState, usage: TokenUsage):
    pass # Deprecated in favor of Annotated reducer

def case_strength_node(state: DecisionState) -> dict:
    dispute_id = state["canonical_case"].dispute.dispute_id
    logger.info("Running Case Strength Node")
    execution_registry.update_node(dispute_id, "node_case_strength", "Analyzing case strength...")
    strength, usage = analyze_case_strength(state["canonical_case"], state["evidence_assessment"], state["policy_context"])
    return {"case_strength": strength, "token_usage": usage}

def confidence_node(state: DecisionState) -> dict:
    dispute_id = state["canonical_case"].dispute.dispute_id
    logger.info("Running Confidence Node")
    execution_registry.update_node(dispute_id, "node_confidence_decision", "Analyzing decision confidence...")
    conf, usage = analyze_confidence(state["canonical_case"], state["evidence_assessment"], state["policy_context"])
    return {"confidence": conf, "token_usage": usage}

def risk_node(state: DecisionState) -> dict:
    dispute_id = state["canonical_case"].dispute.dispute_id
    logger.info("Running Risk Node")
    execution_registry.update_node(dispute_id, "node_risk", "Analyzing case risk flags...")
    risk, usage = analyze_risk(state["canonical_case"], state["evidence_assessment"], state["policy_context"])
    return {"risk_assessment": risk, "token_usage": usage}

def calculate_success_node(state: DecisionState) -> dict:
    dispute_id = state["canonical_case"].dispute.dispute_id
    logger.info("Running Calculate Success Likelihood Node")
    execution_registry.update_node(dispute_id, "calculate_success", "Calculating success likelihood...")
    p_win = calculate_success_likelihood(
        evidence_assessment=state["evidence_assessment"],
        case_strength=state["case_strength"],
        decision_confidence=state["confidence"].confidence,
        has_critical_conflict=state["risk_assessment"].critical_conflict,
        has_missing_critical=state["risk_assessment"].missing_critical_evidence,
        policy_ambiguity=state["risk_assessment"].policy_ambiguity
    )
    return {"success_likelihood": p_win}

def calculate_economics_node(state: DecisionState) -> dict:
    dispute_id = state["canonical_case"].dispute.dispute_id
    logger.info("Running Economics Node")
    execution_registry.update_node(dispute_id, "calculate_economics", "Calculating economics...")
    recoverable = calculate_recoverable_amount(state["canonical_case"].dispute.dispute_amount)
    expected = calculate_expected_recovery(state["success_likelihood"], recoverable)
    
    # Phase 5 only cost (for observability breakdown)
    cost_breakdown = calculate_operational_cost(state.get("token_usage") or TokenUsage())
    
    # NEV uses cumulative cost (Phases 1-5) if available, otherwise Phase 5 cost
    cumulative_cost = state.get("cumulative_operational_cost")
    if cumulative_cost is None:
        cumulative_cost = cost_breakdown.total_operational_cost
    
    nev = calculate_net_expected_value(expected, cumulative_cost)
    
    return {
        "recoverable_amount": recoverable,
        "expected_recovery": expected,
        "operational_cost": cost_breakdown.total_operational_cost,  # Phase 5 only
        "operational_cost_breakdown": cost_breakdown,
        "net_expected_value": nev
    }

def calculate_deadline_node(state: DecisionState) -> dict:
    dispute_id = state["canonical_case"].dispute.dispute_id
    logger.info("Running Deadline Node")
    execution_registry.update_node(dispute_id, "calculate_deadline", "Calculating deadline risk...")
    deadline_risk = calculate_deadline_risk(state["canonical_case"].deadline)
    return {"deadline_risk": deadline_risk}

def decision_engine_node(state: DecisionState) -> dict:
    dispute_id = state["canonical_case"].dispute.dispute_id
    logger.info("Running Decision Engine Node")
    execution_registry.update_node(dispute_id, "decision_engine", "Evaluating decision engine...")
    action, reasons = evaluate_decision(
        has_critical_conflict=state["risk_assessment"].critical_conflict,
        has_policy_ambiguity=state["risk_assessment"].policy_ambiguity,
        has_missing_critical_evidence=state["risk_assessment"].missing_critical_evidence,
        confidence=state["confidence"].confidence,
        case_strength=state["case_strength"].case_strength,
        success_likelihood=state["success_likelihood"],
        recoverable_amount=state["recoverable_amount"],
        expected_recovery=state["expected_recovery"],
        operational_cost=state["operational_cost"],
        net_expected_value=state["net_expected_value"],
        deadline_risk=state["deadline_risk"]
    )
    
    rec = DecisionRecommendation(
        action=action,
        confidence=state["confidence"].confidence,
        case_strength=state["case_strength"].case_strength,
        success_likelihood=state["success_likelihood"],
        recoverable_amount=state["recoverable_amount"],
        expected_recovery=state["expected_recovery"],
        operational_cost=state["operational_cost"],
        net_expected_value=state["net_expected_value"],
        deadline_risk=state["deadline_risk"].risk,
        reason_codes=reasons,
        decision_factors=[]
    )
    return {"ai_recommendation": rec}

def explanation_node(state: DecisionState) -> dict:
    dispute_id = state["canonical_case"].dispute.dispute_id
    logger.info("Running Explanation Node")
    execution_registry.update_node(dispute_id, "explanation_agent", "Generating merchant explanation...")
    explanation, usage = generate_explanation(
        case=state["canonical_case"],
        assessment=state["evidence_assessment"],
        recommendation=state["ai_recommendation"],
        case_strength=state["case_strength"],
        confidence=state["confidence"],
        risk=state["risk_assessment"],
        deadline_risk=state["deadline_risk"],
        cost_breakdown=state["operational_cost_breakdown"],
        policy_context=state["policy_context"]
    )
    
    # We must construct a temporary usage object representing everything so far + this node
    # so we can calculate the final cost breakdown.
    cumulative_now = TokenUsage(
        input_tokens=(state.get("token_usage").input_tokens if state.get("token_usage") else 0) + usage.input_tokens,
        output_tokens=(state.get("token_usage").output_tokens if state.get("token_usage") else 0) + usage.output_tokens,
        total_tokens=(state.get("token_usage").total_tokens if state.get("token_usage") else 0) + usage.total_tokens,
        model=usage.model
    )
    cost_breakdown = calculate_operational_cost(cumulative_now)
    
    return {
        "explanation": explanation,
        "token_usage": usage,
        "operational_cost": cost_breakdown.total_operational_cost,
        "operational_cost_breakdown": cost_breakdown,
        "workflow_status": "NEEDS_REVIEW"
    }

def build_decision_graph() -> StateGraph:
    workflow = StateGraph(DecisionState)
    
    workflow.add_node("node_case_strength", case_strength_node)
    workflow.add_node("node_confidence", confidence_node)
    workflow.add_node("node_risk", risk_node)
    
    workflow.add_node("calculate_success", calculate_success_node)
    workflow.add_node("calculate_deadline", calculate_deadline_node)
    workflow.add_node("calculate_economics", calculate_economics_node)
    
    workflow.add_node("decision_engine", decision_engine_node)
    workflow.add_node("explanation_agent", explanation_node)
    
    # Entry Point (start parallel)
    def init_node(state): return {"dispute_id": state["dispute_id"]}
    workflow.add_node("init", init_node)
    workflow.set_entry_point("init")
    
    workflow.add_edge("init", "node_case_strength")
    workflow.add_edge("node_case_strength", "node_confidence")
    workflow.add_edge("node_confidence", "node_risk")
    
    # Fan in to calculate_success
    workflow.add_edge("node_risk", "calculate_success")
    
    workflow.add_edge("calculate_success", "calculate_deadline")
    workflow.add_edge("calculate_deadline", "calculate_economics")
    
    workflow.add_edge("calculate_economics", "decision_engine")
    workflow.add_edge("decision_engine", "explanation_agent")
    workflow.add_edge("explanation_agent", END)
    
    return workflow.compile()
