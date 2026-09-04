from pydantic import BaseModel, Field
from typing import List, Literal

class SelectedEvidenceItem(BaseModel):
    evidence_id: str = Field(description="Must exactly match an ID from the Phase 3 EvidenceBundle.")
    role: Literal["direct_support", "corroboration", "policy_reference", "context"] = Field(
        description="The role this evidence plays in the representment."
    )
    relevance: float = Field(ge=0.0, le=1.0, description="Relevance score (0.0 to 1.0).")
    reason: str = Field(description="Explanation of why this evidence was selected.")

class EvidencePackage(BaseModel):
    selected_evidence: List[SelectedEvidenceItem] = Field(
        description="The filtered subset of evidence selected for submission.",
        default_factory=list
    )
