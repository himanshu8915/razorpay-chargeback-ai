from langchain_core.prompts import ChatPromptTemplate
from app.llm.gateway import get_llm_gateway
from app.agents.evidence_discovery.schemas import PolicyEvidencePlan
from app.agents.evidence_discovery.prompts import POLICY_EVIDENCE_PLANNER_SYSTEM
from app.schemas.canonical_case import CanonicalCase
from app.decision.models.factors import TokenUsage
from typing import Tuple
import json
import re

def plan_policy_evidence(case: CanonicalCase, relevant_case_context: dict) -> Tuple[PolicyEvidencePlan, TokenUsage]:
    """
    Executes the Policy Evidence Planner LLM to determine policy topics
    and search queries based on the case facts.
    Returns (PolicyEvidencePlan, TokenUsage) for cross-phase accounting.
    """
    llm = get_llm_gateway()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", POLICY_EVIDENCE_PLANNER_SYSTEM),
        ("human", "Dispute Allegation:\nType: {dispute_type}\nReason: {dispute_reason}\nClaim: {claim}\n\nSelected Case Context:\n{relevant_case_context}")
    ])
    
    chain = prompt | llm
    
    res = chain.invoke({
        "dispute_type": case.dispute.dispute_type,
        "dispute_reason": case.dispute.dispute_reason,
        "claim": case.dispute.claim,
        "relevant_case_context": str(relevant_case_context)
    })
    
    text = res.content
    if isinstance(text, list):
        # Extract text from list of blocks or list of strings
        text = "".join(
            block["text"] if isinstance(block, dict) and "text" in block else str(block) 
            for block in text
        )
        
    # Clean json block if present
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)
        
    data = json.loads(text)
    usage = TokenUsage(
        input_tokens=res.usage_metadata.get("input_tokens", 0) if res.usage_metadata else 0,
        output_tokens=res.usage_metadata.get("output_tokens", 0) if res.usage_metadata else 0,
        total_tokens=res.usage_metadata.get("total_tokens", 0) if res.usage_metadata else 0,
        model=res.response_metadata.get("model_name", "unknown") if getattr(res, "response_metadata", None) else "unknown"
    )
    return PolicyEvidencePlan(**data), usage
