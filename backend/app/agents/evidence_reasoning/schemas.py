from pydantic import BaseModel, Field
from typing import List
from app.evidence.models.evidence_finding import EvidenceFinding

class AgentEvidenceAssessment(BaseModel):
    """
    The structured output expected from the Evidence Reasoning Agent.
    """
    evidence_findings: List[EvidenceFinding] = Field(
        description="List of atomic findings mapping evidence items to claim aspects."
    )
    overall_assessment: str = Field(
        description="A concise human-readable summary of the evidence state (what supports, what contradicts, what's missing), without any decision leakage."
    )
