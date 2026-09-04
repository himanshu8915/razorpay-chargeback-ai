from typing import Tuple, List, Literal
from app.evidence.models.evidence_bundle import EvidenceBundle

def determine_completeness(bundle: EvidenceBundle) -> Tuple[Literal["complete", "partial", "insufficient"], List[str]]:
    """
    Determines evidence completeness based on missing evidence.
    Returns (completeness_status, missing_critical_flags)
    """
    if not bundle.structured_evidence:
        return "insufficient", ["NO_STRUCTURED_EVIDENCE"]
        
    # Check if there is missing evidence reported by the bundle
    if not bundle.missing_evidence:
        return "complete", []
        
    critical_missing = []
    status: Literal["complete", "partial", "insufficient"] = "complete"
    
    # In a real system, we'd check criticality against policy.
    # Here, if missing_evidence contains strings about critical fields being missing:
    for missing in bundle.missing_evidence:
        missing_lower = missing.lower()
        if "delivery" in missing_lower or "tracking" in missing_lower or "entirely missing" in missing_lower:
            critical_missing.append(missing)
            
    if len(critical_missing) == len(bundle.missing_evidence) and len(bundle.missing_evidence) > 0:
        # if all missing evidence is critical, and we have multiple missing, it could be insufficient
        if len(critical_missing) > 2 or "entirely missing" in bundle.missing_evidence[0].lower():
            status = "insufficient"
        else:
            status = "partial"
    elif len(critical_missing) > 0:
        status = "partial"
    elif len(bundle.missing_evidence) > 0:
        # non-critical missing
        status = "complete"
        
    return status, critical_missing
