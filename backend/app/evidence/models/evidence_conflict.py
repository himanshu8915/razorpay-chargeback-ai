from pydantic import BaseModel, Field
from typing import Literal, List

class EvidenceConflict(BaseModel):
    evidence_ids: List[str] = Field(description="The IDs of the conflicting evidence items.")
    topic: str = Field(description="The topic or factual aspect where the conflict occurs (e.g., 'fulfillment_status').")
    description: str = Field(description="A concise description of the factual contradiction.")
    severity: Literal["low", "medium", "high"] = Field(description="Deterministic severity of the conflict.")
