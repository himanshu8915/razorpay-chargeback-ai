from datetime import datetime
from typing import Any, Optional, Dict
from pydantic import BaseModel

class EvidenceItem(BaseModel):
    evidence_id: str
    evidence_type: str
    source_type: str
    source_id: str
    content: Any
    relevance_score: Optional[float] = None
    timestamp: Optional[datetime] = None
    provenance: Dict[str, Any]
