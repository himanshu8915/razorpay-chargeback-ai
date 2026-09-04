from pydantic import BaseModel, Field
from typing import List, Dict, Literal

class ValidationChecks(BaseModel):
    evidence_references: Literal["PASS", "FAIL", "STALE", "PENDING"] = "PENDING"
    unsupported_claims: Literal["PASS", "FAIL", "STALE", "PENDING"] = "PENDING"
    evidence_consistency: Literal["PASS", "FAIL", "STALE", "PENDING"] = "PENDING"
    policy_consistency: Literal["PASS", "FAIL", "STALE", "PENDING"] = "PENDING"
    contradiction_check: Literal["PASS", "FAIL", "STALE", "PENDING"] = "PENDING"
    required_evidence: Literal["PASS", "FAIL", "STALE", "PENDING"] = "PENDING"
    format: Literal["PASS", "FAIL", "STALE", "PENDING"] = "PENDING"

class ValidationResult(BaseModel):
    status: Literal["PASS", "FAIL", "STALE", "PENDING"] = Field(
        description="Overall status. 'STALE' means the representation or evidence was edited and requires re-validation."
    )
    checks: ValidationChecks = Field(default_factory=ValidationChecks)
    errors: List[str] = Field(default_factory=list, description="List of hard validation failures.")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings.")
