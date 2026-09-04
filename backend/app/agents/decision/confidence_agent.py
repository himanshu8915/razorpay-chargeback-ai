import json
import re
from typing import Tuple
from langchain_core.prompts import ChatPromptTemplate
from app.llm.gateway import get_llm_gateway
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.decision.models.decision import ConfidenceAssessment
from app.decision.models.factors import TokenUsage

SYSTEM_PROMPT = """You are a Confidence Analyst for dispute intelligence.
Analyze the canonical case and evidence assessment.
Do not calculate 'confidence' natively, it will be injected later. Only provide categorical levels (HIGH, MEDIUM, LOW) and reasons.
"""

def analyze_confidence(case: CanonicalCase, assessment: EvidenceAssessment, policy_context: list) -> Tuple[ConfidenceAssessment, TokenUsage]:
    llm = get_llm_gateway()
    
    from langchain_core.output_parsers import JsonOutputParser
    parser = JsonOutputParser(pydantic_object=ConfidenceAssessment)

    human_msg = f"""
    DISPUTE ID: {case.dispute.dispute_id}
    PHASE 4 CONFIDENCE SCORE: {assessment.confidence}
    EVIDENCE COMPLETENESS: {assessment.completeness}
    CONFLICTS: {[c.model_dump() for c in assessment.conflicts]}
    
    Evaluate the confidence level qualitatively.
    
    {parser.get_format_instructions()}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{human_msg}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        parsed_dict = chain.invoke({"human_msg": human_msg})
        parsed = ConfidenceAssessment(**parsed_dict)
        
        parsed.confidence = assessment.confidence # Inherit deterministic score
        
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
