import json
import re
from typing import Tuple
from langchain_core.prompts import ChatPromptTemplate
from app.llm.gateway import get_llm_gateway
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.decision.models.decision import CaseStrength
from app.decision.models.factors import TokenUsage

SYSTEM_PROMPT = """You are a Case Strength Analyst for dispute intelligence.
Analyze the canonical case and evidence assessment.
Identify supporting factors, weaknesses, and critical conflicts.
Score case strength deterministically on a scale of 0.0 to 1.0.
"""

def analyze_case_strength(case: CanonicalCase, assessment: EvidenceAssessment, policy_context: list) -> Tuple[CaseStrength, TokenUsage]:
    llm = get_llm_gateway()
    
    from langchain_core.output_parsers import JsonOutputParser
    
    # Use standard LLM invoke with JSON output parser to avoid Groq tool-calling errors
    parser = JsonOutputParser(pydantic_object=CaseStrength)
    
    human_msg = f"""
    DISPUTE CLAIM: {case.dispute.claim}
    DISPUTE REASON: {case.dispute.dispute_reason}
    EVIDENCE COMPLETENESS: {assessment.completeness}
    OVERALL ASSESSMENT: {assessment.overall_assessment}
    
    EVIDENCE FINDINGS ({len(assessment.evidence_findings)} items):
    {[{
        "evidence_id": f.evidence_id,
        "relationship": f.relationship,
        "claim_aspect": f.claim_aspect,
        "finding": f.finding,
        "confidence": f.confidence
    } for f in assessment.evidence_findings]}
    
    SUPPORTING EVIDENCE COUNT: {len(assessment.supporting_evidence)}
    CONTRADICTING EVIDENCE COUNT: {len(assessment.contradicting_evidence)}
    CONFLICTS: {[c.model_dump() for c in assessment.conflicts]}
    RISK FLAGS: {assessment.risk_flags}
    
    Based on the evidence findings above, score the merchant's case strength.
    A case is strong when there is substantial supporting evidence, no critical conflicts,
    and the evidence directly addresses the dispute claim.
    
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
        parsed = CaseStrength(**parsed_dict)
        
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
