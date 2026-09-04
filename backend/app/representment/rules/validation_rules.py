from typing import List, Dict, Any, Tuple
from app.representment.models.representation import RepresentationDraft
from app.representment.models.evidence_package import EvidencePackage
from app.representment.models.policy_mapping import PolicyRequirementMapping
from app.evidence.models.evidence_bundle import EvidenceBundle

def validate_evidence_references(draft: RepresentationDraft, bundle: EvidenceBundle) -> Tuple[bool, List[str]]:
    """Validator 1 — Evidence reference validity"""
    valid_ids = {item.evidence_id for item in bundle.structured_evidence}
    errors = []
    
    for ref in draft.evidence_references:
        if ref not in valid_ids:
            errors.append(f"Global reference to unknown evidence ID: {ref}")
            
    for arg in draft.factual_arguments:
        for ref in arg.evidence_ids:
            if ref not in valid_ids:
                errors.append(f"Factual argument references unknown evidence ID: {ref}")
                
    return len(errors) == 0, errors

def validate_unsupported_claims(draft: RepresentationDraft) -> Tuple[bool, List[str]]:
    """Validator 2 — Unsupported claim detection"""
    errors = []
    for i, arg in enumerate(draft.factual_arguments):
        if not arg.evidence_ids:
            errors.append(f"Factual argument {i+1} ('{arg.statement[:30]}...') lacks evidence references.")
    return len(errors) == 0, errors

def validate_evidence_consistency(draft: RepresentationDraft, bundle: EvidenceBundle) -> Tuple[bool, List[str]]:
    """Validator 3 — Evidence consistency (Structured Values)"""
    errors = []
    bundle_map = {item.evidence_id: item for item in bundle.structured_evidence}
    
    for arg in draft.factual_arguments:
        for key, structured_val in arg.structured_values.items():
            for ref in arg.evidence_ids:
                if ref in bundle_map:
                    evidence_item = bundle_map[ref]
                    # We look for the exact value in the evidence's parsed value.
                    # String comparison for dates/amounts isn't perfect but provides a deterministic safety net.
                    val_str = str(structured_val.value).lower().strip()
                    evidence_val_str = str(evidence_item.value).lower().strip()
                    
                    if val_str not in evidence_val_str:
                        # Attempt to find it in the content representation if value is complex
                        content_str = str(evidence_item.content).lower().strip()
                        if val_str not in content_str:
                            errors.append(f"Claimed {structured_val.field_type} '{structured_val.value}' not found in Evidence {ref}")
    return len(errors) == 0, errors

def validate_policy_consistency(draft: RepresentationDraft, mapping: PolicyRequirementMapping) -> Tuple[bool, List[str]]:
    """Validator 4 — Policy consistency"""
    errors = []
    valid_policy_ids = set()
    for req in mapping.requirements:
        valid_policy_ids.update(req.policy_source_ids)
        
    for arg in draft.policy_arguments:
        for p_ref in arg.policy_source_ids:
            if p_ref not in valid_policy_ids:
                errors.append(f"Policy argument references unknown policy ID: {p_ref}")
    return len(errors) == 0, errors

def validate_contradiction(draft: RepresentationDraft, bundle: EvidenceBundle) -> Tuple[bool, List[str]]:
    """Validator 5 — Contradiction detection"""
    # Without an LLM, pure deterministic contradiction is hard. 
    # We rely on Phase 4's EvidenceAssessment for known contradictions.
    # We will pass the Phase 4 assessment to the validator service to inject it here.
    return True, [] # Implemented in service layer utilizing Phase 4 findings.

def validate_required_coverage(package: EvidencePackage, mapping: PolicyRequirementMapping) -> Tuple[bool, List[str]]:
    """Validator 6 — Required evidence coverage"""
    errors = []
    selected_ids = {item.evidence_id for item in package.selected_evidence}
    
    for req in mapping.requirements:
        if req.is_critical:
            # Check if any selected evidence satisfies this requirement
            covered = any(ev_id in selected_ids for ev_id in req.supporting_evidence_ids)
            if not covered:
                errors.append(f"Critical requirement '{req.requirement_name}' is not covered by selected evidence.")
    return len(errors) == 0, errors

def validate_format(draft: RepresentationDraft, max_length: int = 5000) -> Tuple[bool, List[str]]:
    """Validator 7 — Length / format"""
    errors = []
    
    # Reconstruct text representation roughly
    full_text = draft.summary + draft.claim_response + draft.conclusion
    for fa in draft.factual_arguments:
        full_text += fa.statement
    for pa in draft.policy_arguments:
        full_text += pa.statement
        
    if len(full_text) > max_length:
        errors.append(f"Representation length ({len(full_text)} chars) exceeds maximum ({max_length} chars).")
        
    if not draft.summary or len(draft.summary.strip()) < 10:
        errors.append("Summary is missing or too short.")
        
    if not draft.claim_response or len(draft.claim_response.strip()) < 10:
        errors.append("Claim response is missing or too short.")
        
    if not draft.conclusion or len(draft.conclusion.strip()) < 10:
        errors.append("Conclusion is missing or too short.")
        
    return len(errors) == 0, errors
