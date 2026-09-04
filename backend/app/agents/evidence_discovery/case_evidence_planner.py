from langchain_core.prompts import ChatPromptTemplate
from app.llm.gateway import get_llm_gateway
from app.agents.evidence_discovery.schemas import CaseEvidencePlan
from app.agents.evidence_discovery.prompts import CASE_EVIDENCE_PLANNER_SYSTEM
from app.schemas.canonical_case import CanonicalCase
from app.decision.models.factors import TokenUsage
from typing import Tuple
import json
import re

def plan_case_evidence(case: CanonicalCase, allowed_schema: dict) -> Tuple[CaseEvidencePlan, TokenUsage]:
    """
    Executes the Case Evidence Planner LLM to identify relevant factual fields
    based on the CanonicalCase and its embedded dispute allegation.
    Returns (CaseEvidencePlan, TokenUsage) for cross-phase accounting.
    """
    llm = get_llm_gateway()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", CASE_EVIDENCE_PLANNER_SYSTEM),
        ("human", "Dispute Allegation:\nType: {dispute_type}\nReason: {dispute_reason}\nClaim: {claim}\n\nAllowed Schema:\n{allowed_schema}")
    ])
    
    chain = prompt | llm
    
    res = chain.invoke({
        "dispute_type": case.dispute.dispute_type,
        "dispute_reason": case.dispute.dispute_reason,
        "claim": case.dispute.claim,
        "allowed_schema": str(allowed_schema)
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
    return CaseEvidencePlan(**data), usage
