from pydantic import BaseModel, Field
from typing import Literal, List

class EvidenceFinding(BaseModel):
    evidence_id: str = Field(description="The ID of the evidence item from the EvidenceBundle.")
    relationship: Literal["supports", "contradicts", "does_not_address"] = Field(
        description="How this evidence relates to the CUSTOMER'S dispute claim."
    )
    claim_aspect: str = Field(default="general", description="The specific aspect of the claim this evidence addresses (e.g. 'delivery', 'fulfillment').")
    finding: str = Field(default="", description="A concise factual explanation of what the evidence shows.")
    policy_basis: List[str] = Field(default_factory=list, description="List of exact retrieved policy EvidenceItem.evidence_id references (e.g., 'EV-POL-xxx') that apply to this finding. MUST NOT be document IDs.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this specific finding's extraction and relationship.")
