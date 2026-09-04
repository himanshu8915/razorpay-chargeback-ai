from typing import TypedDict, Optional, List
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.decision.models.decision import FinalDecision
from app.representment.models.evidence_package import EvidencePackage
from app.representment.models.policy_mapping import PolicyRequirementMapping
from app.representment.models.representation import RepresentationDraft, FinalRepresentation
from app.representment.models.validation import ValidationResult
from app.representment.models.submission import SubmissionPackage
from app.decision.models.factors import TokenUsage

class RepresentmentState(TypedDict):
    dispute_id: str
    
    # Inputs
    canonical_case: CanonicalCase
    evidence_bundle: EvidenceBundle
    evidence_assessment: EvidenceAssessment
    final_decision: FinalDecision
    
    # Workflow artifacts
    selected_evidence: Optional[EvidencePackage]
    policy_mapping: Optional[PolicyRequirementMapping]
    representation_draft: Optional[RepresentationDraft]
    validation_result: Optional[ValidationResult]
    final_representation: Optional[FinalRepresentation]
    submission_package: Optional[SubmissionPackage]
    
    # State tracking
    workflow_status: str # e.g. "VALIDATING", "NEEDS_REVIEW", "READY", "FAILED_VALIDATION", "STALE"
    retry_count: int
    validation_errors: List[str]
    
    # Observability
    token_usage: Optional[TokenUsage]
