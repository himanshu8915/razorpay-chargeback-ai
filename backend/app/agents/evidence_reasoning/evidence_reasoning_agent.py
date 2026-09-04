import json
import re
from typing import Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from app.llm.gateway import get_llm_gateway
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.agents.evidence_reasoning.schemas import AgentEvidenceAssessment
from app.agents.evidence_reasoning.prompts import EVIDENCE_REASONING_SYSTEM
from app.decision.models.factors import TokenUsage

def reason_evidence(case: CanonicalCase, bundle: EvidenceBundle) -> Tuple[AgentEvidenceAssessment, TokenUsage]:
    """
    Evaluates evidence against the dispute claim and policy.
    Uses regex + json.loads to extract the AgentEvidenceAssessment structure robustly.
    Returns (AgentEvidenceAssessment, TokenUsage) for cross-phase accounting.
    """
    llm = get_llm_gateway()

    evidence_text = []
    for item in bundle.policy_evidence:
        evidence_text.append(f"POLICY CHUNK [{item.evidence_id}]: {json.dumps(item.content, default=str)}")
    for item in bundle.structured_evidence:
        evidence_text.append(f"FACTUAL EVIDENCE [{item.evidence_id}]: {json.dumps(item.content, default=str)}")
            
    human_msg = f"""
    DISPUTE CLAIM: {case.dispute.claim}
    DISPUTE TYPE: {case.dispute.dispute_type}
    DISPUTE REASON: {case.dispute.dispute_reason}
    
    EVIDENCE BUNDLE:
    {chr(10).join(evidence_text)}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", EVIDENCE_REASONING_SYSTEM),
        ("human", "{human_msg}")
    ])
    
    for attempt in range(3):
        try:
            res = llm.invoke(prompt.format_messages(human_msg=human_msg))
            
            text = res.content
            if isinstance(text, list):
                # Handle list of blocks from some models
                text = "".join(
                    block["text"] if isinstance(block, dict) and "text" in block else str(block) 
                    for block in text
                )
                
            # Extract JSON robustly
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if not match:
                raise ValueError(f"Could not extract JSON from reasoning agent output: {text}")
                
            json_str = match.group(0)
            data = json.loads(json_str)
            
            usage = TokenUsage(
                input_tokens=res.usage_metadata.get("input_tokens", 0) if res.usage_metadata else 0,
                output_tokens=res.usage_metadata.get("output_tokens", 0) if res.usage_metadata else 0,
                total_tokens=res.usage_metadata.get("total_tokens", 0) if res.usage_metadata else 0,
                model=res.response_metadata.get("model_name", "unknown") if getattr(res, "response_metadata", None) else "unknown"
            )
            return AgentEvidenceAssessment(**data), usage
        except Exception as e:
            if attempt == 2:
                raise e
            import logging
            logging.getLogger(__name__).warning(f"JSON Parse/Validation error on attempt {attempt+1}: {e}. Retrying...")

