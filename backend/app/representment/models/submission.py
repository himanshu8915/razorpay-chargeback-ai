from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.representment.models.evidence_package import EvidencePackage
from app.representment.models.policy_mapping import PolicyRequirementMapping
from app.representment.models.representation import FinalRepresentation
from app.representment.models.validation import ValidationResult

class AuditLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str = Field(description="Action taken (e.g., 'AI_DRAFT_GENERATED', 'HUMAN_EDITED', 'EVIDENCE_REMOVED', 'VALIDATION_FAILED', 'APPROVED')")
    actor: str = Field(description="'AI', 'SYSTEM', or reviewer_id")
    details: Optional[str] = None

class SubmissionPackage(BaseModel):
    dispute_id: str
    decision: str = Field(description="The confirmed FinalDecision (must be CONTEST).")
    
    representation: FinalRepresentation
    evidence: EvidencePackage
    policy_mapping: PolicyRequirementMapping
    validation_status: ValidationResult
    
    human_approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    status: str = Field(description="'DRAFT', 'STALE', 'READY_FOR_SUBMISSION'")
    audit_history: List[AuditLogEntry] = Field(default_factory=list)
