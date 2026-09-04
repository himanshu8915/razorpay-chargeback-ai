from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.decision.models.decision import CaseStrength

def calculate_success_likelihood(
    evidence_assessment: EvidenceAssessment,
    case_strength: CaseStrength,
    decision_confidence: float,
    has_critical_conflict: bool,
    has_missing_critical: bool,
    policy_ambiguity: bool
) -> float:
    """
    Deterministic scoring model for MVO.
    0.0 <= P(win) <= 1.0
    """
    if has_critical_conflict or has_missing_critical:
        return 0.0
        
    base_score = 0.4
    
    # Evidence Completeness
    if evidence_assessment.completeness == "complete":
        base_score += 0.2
    elif evidence_assessment.completeness == "partial":
        base_score += 0.05
        
    # Case Strength
    base_score += (case_strength.case_strength * 0.3)
    
    # Policy alignment
    if not policy_ambiguity:
        base_score += 0.1
        
    # Confidence weight
    final_score = base_score * decision_confidence
    
    # Bounding
    return max(0.0, min(1.0, final_score))
