import json
import re
from typing import Tuple
from langchain_core.prompts import ChatPromptTemplate
from app.llm.gateway import get_llm_gateway
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.decision.models.decision import (
    DecisionRecommendation, CaseStrength, ConfidenceAssessment, RiskAssessment, DecisionExplanation
)
from app.decision.models.factors import TokenUsage, DeadlineRisk, OperationalCostBreakdown
from decimal import Decimal

SYSTEM_PROMPT = """You are an Explanation Generator.
The decision has already been deterministically calculated.
Do not change:
- action
- confidence
- success likelihood
- expected recovery
- operational cost
- NEV
- risk classification

Do not introduce new evidence or policy sources.
Explain the supplied decision artifact clearly.

Your output MUST be a valid JSON object matching this schema exactly:
{{
  "summary": "...",
  "why_we_believe_we_can_win": ["..."],
  "supporting_evidence": [{{"evidence_id": "...", "reason": "..."}}],
  "contradicting_evidence": [],
  "risks": ["..."],
  "economic_summary": "...",
  "deadline_summary": "...",
  "next_action": "...",
  "sources": ["EV-..."]
}}
Do not output markdown code blocks. Just output the JSON.
"""

def generate_explanation(
    case: CanonicalCase, 
    assessment: EvidenceAssessment, 
    recommendation: DecisionRecommendation,
    case_strength: CaseStrength,
    confidence: ConfidenceAssessment,
    risk: RiskAssessment,
    deadline_risk: DeadlineRisk,
    cost_breakdown: OperationalCostBreakdown,
    policy_context: list
) -> Tuple[DecisionExplanation, TokenUsage]:
    
    llm = get_llm_gateway()
    from langchain_core.output_parsers import JsonOutputParser
    
    parser = JsonOutputParser(pydantic_object=DecisionExplanation)
    
    human_msg = f"""
    DISPUTE ID: {case.dispute.dispute_id}
    DETERMINISTIC RECOMMENDATION: {recommendation.action}
    CONFIDENCE: {recommendation.confidence}
    SUCCESS LIKELIHOOD: {recommendation.success_likelihood}
    EXPECTED RECOVERY: {recommendation.expected_recovery}
    OPERATIONAL COST: {recommendation.operational_cost}
    NET EXPECTED VALUE: {recommendation.net_expected_value}
    
    DEADLINE RISK: {deadline_risk.risk} ({deadline_risk.time_remaining_hours}h)
    
    CASE STRENGTH: {case_strength.model_dump()}
    CONFIDENCE: {confidence.model_dump()}
    RISK: {risk.model_dump()}
    
    EVIDENCE FINDINGS: {[f.model_dump() for f in assessment.evidence_findings]}
    POLICY FINDINGS: {assessment.policy_findings}
    
    Generate the explanation based ONLY on the provided data.
    
    {parser.get_format_instructions()}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{human_msg}")
    ])
    
    try:
        # Invoke LLM directly to get AIMessage with usage_metadata
        formatted = prompt.format_messages(human_msg=human_msg)
        ai_msg = llm.invoke(formatted)
        parsed_dict = parser.invoke(ai_msg)
        parsed = DecisionExplanation(**parsed_dict)
        
        # Grounding Validation
        valid_evidence_ids = {f.evidence_id for f in assessment.evidence_findings}
        valid_policy_ids = {p.policy_id for p in policy_context} if policy_context else set()
        valid_policy_chunks = set()
        if policy_context:
            for p in policy_context:
                if hasattr(p, 'chunks'):
                    for c in p.chunks:
                        valid_policy_chunks.add(c.chunk_id)
                        
        allowed_sources = valid_evidence_ids.union(set(assessment.policy_findings))
        
        if parsed:
            invalid_sources = [src for src in parsed.sources if src not in allowed_sources]
            if invalid_sources:
                raise ValueError(f"Explanation Validation FAILED: Unknown or manufactured sources detected: {invalid_sources}")
        else:
            raise ValueError("Failed to parse DecisionExplanation from LLM output.")
        
        # Extract real token usage from Gemini response metadata
        meta = getattr(ai_msg, "usage_metadata", None) or {}
        from app.config.settings import settings
        usage = TokenUsage(
            input_tokens=meta.get("input_tokens", 0),
            output_tokens=meta.get("output_tokens", 0),
            total_tokens=meta.get("total_tokens", 0),
            model=settings.llm_model
        )
        
        return parsed, usage
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e
