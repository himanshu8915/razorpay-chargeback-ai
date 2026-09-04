import json
import re
from typing import Tuple
from langchain_core.prompts import ChatPromptTemplate
from app.llm.gateway import get_llm_gateway
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.decision.models.decision import RiskAssessment
from app.decision.models.factors import TokenUsage

SYSTEM_PROMPT = """You are a Risk Analyst for dispute intelligence.
Identify critical conflicts, missing critical evidence, and policy ambiguity.
"""

def analyze_risk(case: CanonicalCase, assessment: EvidenceAssessment, policy_context: list) -> Tuple[RiskAssessment, TokenUsage]:
    llm = get_llm_gateway()
    
    # Use native structured output which enforces JSON at the API level
    from langchain_core.output_parsers import JsonOutputParser
    
    from langchain_core.output_parsers import JsonOutputParser
    parser = JsonOutputParser(pydantic_object=RiskAssessment)

    human_msg = f"""
    DISPUTE ID: {case.dispute.dispute_id}
    CONFLICTS: {[c.model_dump() for c in assessment.conflicts]}
    POLICY AMBIGUITY: {len(policy_context) == 0}
    
    Evaluate the risk.
    
    {parser.get_format_instructions()}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{human_msg}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        parsed_dict = chain.invoke({"human_msg": human_msg})
        parsed = RiskAssessment(**parsed_dict)
        
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
