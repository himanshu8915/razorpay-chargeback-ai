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
    
    SUPPORTING EVIDENCE IDs: {assessment.supporting_evidence}
    CONTRADICTING EVIDENCE IDs: {assessment.contradicting_evidence}
    CONFLICTS: {[c.model_dump() for c in assessment.conflicts]}
    
    Evaluate the case strength.
    
    {parser.get_format_instructions()}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{human_msg}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        parsed_dict = chain.invoke({"human_msg": human_msg})
        parsed = CaseStrength(**parsed_dict)
        
        usage = TokenUsage(
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            model="unknown"
        )
        
        return parsed, usage
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e
