from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class MappedRequirement(BaseModel):
    requirement_name: str = Field(description="E.g. 'DELIVERY_CONFIRMATION', 'ORDER_FULFILLMENT'")
    description: str = Field(description="Description of what needs to be proven.")
    status: Literal["COVERED", "MISSING", "PARTIAL"] = Field(description="Status of the evidence mapping.")
    supporting_evidence_ids: List[str] = Field(
        default_factory=list,
        description="List of evidence IDs that support this requirement."
    )
    policy_source_ids: List[str] = Field(
        default_factory=list,
        description="List of policy document/chunk IDs defining this requirement."
    )
    is_critical: bool = Field(default=True, description="Whether this requirement is strictly required to contest.")

class PolicyRequirementMapping(BaseModel):
    requirements: List[MappedRequirement] = Field(default_factory=list)
    overall_coverage: float = Field(ge=0.0, le=1.0, description="Percentage of critical requirements covered.")
    missing_critical_requirements: List[str] = Field(default_factory=list, description="Names of missing critical requirements.")
