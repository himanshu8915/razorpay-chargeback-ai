from typing import List, Dict, Any
from pydantic import BaseModel
from app.evidence.models.evidence_item import EvidenceItem

class EvidenceBundle(BaseModel):
    dispute_id: str
    structured_evidence: List[EvidenceItem]
    policy_evidence: List[EvidenceItem]
    missing_evidence: List[str]
    retrieval_metadata: Dict[str, Any]
