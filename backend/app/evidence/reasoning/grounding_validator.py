from typing import List, Tuple
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.agents.evidence_reasoning.schemas import AgentEvidenceAssessment

class GroundingError(Exception):
    pass

def validate_grounding(assessment: AgentEvidenceAssessment, bundle: EvidenceBundle) -> Tuple[bool, List[str]]:
    """
    Validates that every finding in the LLM's assessment is grounded in actual evidence.
    Returns (is_valid, list_of_errors).
    """
    valid_evidence_ids = {item.evidence_id for item in bundle.structured_evidence}
    valid_policy_ids = {item.evidence_id for item in bundle.policy_evidence}
    
    errors = []
    
    for finding in assessment.evidence_findings:
        if finding.evidence_id not in valid_evidence_ids:
            errors.append(f"Ungrounded factual evidence ID: {finding.evidence_id}")
            
        for policy_ref in finding.policy_basis:
            if policy_ref not in valid_policy_ids:
                errors.append(f"Ungrounded policy reference ID: {policy_ref}")
                
    is_valid = len(errors) == 0
    return is_valid, errors
