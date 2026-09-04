from pydantic import BaseModel, Field
from typing import Literal, List
from app.evidence.models.evidence_finding import EvidenceFinding
from app.evidence.models.evidence_conflict import EvidenceConflict

class EvidenceAssessment(BaseModel):
    dispute_id: str = Field(description="The canonical case dispute ID.")
    evidence_findings: List[EvidenceFinding] = Field(description="The atomic reasoning results for evidence mapping to the claim.")
    supporting_evidence: List[str] = Field(default_factory=list, description="List of evidence IDs that support the claim.")
    contradicting_evidence: List[str] = Field(default_factory=list, description="List of evidence IDs that contradict the claim.")
    non_probative_evidence: List[str] = Field(default_factory=list, description="List of evidence IDs that do not address the claim.")
    missing_evidence: List[str] = Field(default_factory=list, description="List of missing evidence keys.")
    conflicts: List[EvidenceConflict] = Field(default_factory=list, description="Detected factual conflicts.")
    policy_findings: List[str] = Field(default_factory=list, description="Traceable policy references applicable to the dispute.")
    completeness: Literal["complete", "partial", "insufficient"] = Field(description="Deterministic measure of evidence completeness.")
    overall_assessment: str = Field(description="Evidence state explanation without decision leakage.")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall deterministic confidence in the assessment.")
    risk_flags: List[str] = Field(default_factory=list, description="Deterministic risk flags.")
