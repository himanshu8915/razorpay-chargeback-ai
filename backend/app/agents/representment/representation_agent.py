import json
import re
import logging
from typing import Tuple
from langchain_core.prompts import ChatPromptTemplate
from app.llm.gateway import get_llm_gateway
from app.decision.models.factors import TokenUsage
from app.schemas.canonical_case import CanonicalCase
from app.representment.models.evidence_package import EvidencePackage
from app.representment.models.policy_mapping import PolicyRequirementMapping
from app.representment.models.representation import RepresentationDraft

logger = logging.getLogger(__name__)

REPRESENTATION_SYSTEM = """
You are an expert Chargeback Representment Generator.
Your job is to generate the draft representation based strictly on the provided selected evidence and policy context.

RULES:
1. Grounding is absolute. Every factual claim MUST include references to the selected evidence IDs.
2. Structure your output exactly to match the schema below.
3. For factual arguments, extract the atomic structured values (like dates, statuses) exactly as they appear in the evidence, and place them in `structured_values`.
4. Distinguish between Facts, Policy, and Inferences. Do not mix them.
5. If you do not have evidence for a claim, DO NOT MAKE IT.

Output strictly as JSON matching this schema:
{
  "summary": "string",
  "claim_response": "string",
  "factual_arguments": [
    {
      "statement": "string",
      "evidence_ids": ["string"],
      "structured_values": {
        "field_name_1": {
          "field_type": "date|amount|status|identifier",
          "value": "string or number"
        }
      }
    }
  ],
  "policy_arguments": [
    {
      "statement": "string",
      "policy_source_ids": ["string"]
    }
  ],
  "conclusion": "string",
  "evidence_references": ["string"]
}
"""

def generate_representation(
    case: CanonicalCase, 
    package: EvidencePackage,
    mapping: PolicyRequirementMapping,
    validation_feedback: str = ""
) -> Tuple[RepresentationDraft, TokenUsage]:
    """
    Invokes the LLM to generate the RepresentationDraft.
    validation_feedback is used during regeneration to correct prior errors.
    """
    logger.info(f"Generating representation for dispute {case.dispute.dispute_id}")
    llm = get_llm_gateway()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", REPRESENTATION_SYSTEM),
        ("human", "Dispute:\n{dispute_json}\n\nSelected Evidence:\n{package_json}\n\nPolicy Mapping:\n{mapping_json}\n\nValidation Feedback (if retrying):\n{feedback}")
    ])
    
    chain = prompt | llm
    
    res = chain.invoke({
        "dispute_json": case.dispute.model_dump_json(include={'dispute_id', 'dispute_type', 'dispute_reason', 'claim'}),
        "package_json": package.model_dump_json(),
        "mapping_json": mapping.model_dump_json(),
        "feedback": validation_feedback or "None. First attempt."
    })
    
    text = res.content
    if isinstance(text, list):
        text = "".join(block["text"] if isinstance(block, dict) and "text" in block else str(block) for block in text)
        
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)
        
    try:
        data = json.loads(text)
        draft = RepresentationDraft(**data)
    except Exception as e:
        logger.error(f"Failed to parse RepresentationDraft from LLM output: {e}\nRaw output: {text}")
        raise ValueError(f"LLM produced invalid representation format: {e}")
        
    usage = TokenUsage(
        input_tokens=res.usage_metadata.get("input_tokens", 0) if res.usage_metadata else 0,
        output_tokens=res.usage_metadata.get("output_tokens", 0) if res.usage_metadata else 0,
        total_tokens=res.usage_metadata.get("total_tokens", 0) if res.usage_metadata else 0,
        model=res.response_metadata.get("model_name", "unknown") if getattr(res, "response_metadata", None) else "unknown"
    )
    
    return draft, usage
