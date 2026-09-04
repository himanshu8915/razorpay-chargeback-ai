import json
import re
import logging
from typing import Tuple
from langchain_core.prompts import ChatPromptTemplate
from app.llm.gateway import get_llm_gateway
from app.decision.models.factors import TokenUsage
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.representment.models.evidence_package import EvidencePackage, SelectedEvidenceItem
from app.representment.models.policy_mapping import PolicyRequirementMapping

logger = logging.getLogger(__name__)

EVIDENCE_SELECTION_SYSTEM = """
You are an expert Chargeback Representment Evidence Selector.
Your job is to identify which pieces of verified evidence are actually useful for the submission.

RULES:
1. DO NOT invent evidence. You must only select evidence IDs provided in the EvidenceBundle.
2. Optimize for quality and relevance over quantity.
3. Remove redundant evidence unless corroboration is critical.
4. Ensure critical requirements are met if evidence exists.
5. Provide a relevance score (0.0 to 1.0) and a role for each selected item.

Output strictly as JSON matching this schema:
{
  "selected_evidence": [
    {
      "evidence_id": "string",
      "role": "direct_support | corroboration | policy_reference | context",
      "relevance": float,
      "reason": "string"
    }
  ]
}
"""

def select_evidence(
    case: CanonicalCase, 
    bundle: EvidenceBundle, 
    assessment: EvidenceAssessment,
    mapping: PolicyRequirementMapping
) -> Tuple[EvidencePackage, TokenUsage]:
    """
    Invokes the LLM to select the most relevant evidence, 
    ensuring it does not fabricate IDs.
    """
    logger.info(f"Selecting evidence for dispute {case.dispute.dispute_id}")
    llm = get_llm_gateway()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", EVIDENCE_SELECTION_SYSTEM),
        ("human", "Dispute:\n{dispute_json}\n\nEvidence Bundle:\n{bundle_json}\n\nPolicy Mapping:\n{mapping_json}\n\nAssessment:\n{assessment_json}")
    ])
    
    chain = prompt | llm
    
    # Strip down payload to avoid max context length
    bundle_data = [{"evidence_id": e.evidence_id, "type": e.type, "summary": e.content} for e in bundle.structured_evidence]
    
    res = chain.invoke({
        "dispute_json": case.dispute.model_dump_json(include={'dispute_id', 'dispute_type', 'dispute_reason', 'claim'}),
        "bundle_json": json.dumps(bundle_data),
        "mapping_json": mapping.model_dump_json(),
        "assessment_json": assessment.model_dump_json(include={'supporting_evidence', 'contradicting_evidence'})
    })
    
    text = res.content
    if isinstance(text, list):
        text = "".join(block["text"] if isinstance(block, dict) and "text" in block else str(block) for block in text)
        
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)
        
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from Evidence Selector: {text}")
        data = {"selected_evidence": []}
        
    usage = TokenUsage(
        input_tokens=res.usage_metadata.get("input_tokens", 0) if res.usage_metadata else 0,
        output_tokens=res.usage_metadata.get("output_tokens", 0) if res.usage_metadata else 0,
        total_tokens=res.usage_metadata.get("total_tokens", 0) if res.usage_metadata else 0,
        model=res.response_metadata.get("model_name", "unknown") if getattr(res, "response_metadata", None) else "unknown"
    )
    
    # Deterministic guardrail: filter out any IDs that were not in the bundle
    valid_ids = {e.evidence_id for e in bundle.structured_evidence} | {e.evidence_id for e in bundle.policy_evidence}
    
    cleaned_items = []
    for item in data.get("selected_evidence", []):
        eid = item.get("evidence_id")
        if eid in valid_ids:
            try:
                cleaned_items.append(SelectedEvidenceItem(**item))
            except Exception as e:
                logger.warning(f"Validation error for evidence item {eid}: {e}")
        else:
            logger.warning(f"LLM hallucinated evidence ID {eid}. Discarding.")
            
    package = EvidencePackage(selected_evidence=cleaned_items)
    return package, usage
