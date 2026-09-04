from typing import List
from app.evidence.models.evidence_conflict import EvidenceConflict
from app.agents.evidence_reasoning.schemas import AgentEvidenceAssessment

def calculate_confidence(
    assessment: AgentEvidenceAssessment, 
    completeness_status: str, 
    conflicts: List[EvidenceConflict],
    has_grounding_failure: bool = False
) -> float:
    """
    Deterministically calculates the final reasoning confidence.
    Inputs:
    - completeness_status: "complete", "partial", or "insufficient"
    - conflicts: list of detected factual conflicts
    - has_grounding_failure: if validation failed after max retries
    - assessment.evidence_findings: to aggregate base confidence of findings
    """
    
    # Base confidence from LLM reasoning extraction
    if not assessment.evidence_findings:
        base_conf = 0.5
    else:
        base_conf = sum(f.confidence for f in assessment.evidence_findings) / len(assessment.evidence_findings)
        
    # Completeness penalty
    if completeness_status == "insufficient":
        base_conf -= 0.4
    elif completeness_status == "partial":
        base_conf -= 0.15
        
    # Conflict penalty
    for conflict in conflicts:
        if conflict.severity == "high":
            base_conf -= 0.2
        elif conflict.severity == "medium":
            base_conf -= 0.1
        else:
            base_conf -= 0.05
            
    # Policy penalty (if findings claim support/contradiction but have no policy basis)
    unsupported_findings = [f for f in assessment.evidence_findings if f.relationship != "does_not_address" and not f.policy_basis]
    if unsupported_findings:
        base_conf -= 0.05 * len(unsupported_findings)
        
    # Grounding failure penalty
    if has_grounding_failure:
        base_conf -= 0.30
        
    # Ensure bounds
    return max(0.0, min(1.0, round(base_conf, 2)))
