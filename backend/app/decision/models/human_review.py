from pydantic import BaseModel, Field
from typing import Literal, Optional, Any, Dict
from datetime import datetime

WorkflowStatus = Literal[
    "ANALYZING", 
    "DECISION_READY", 
    "EXPLANATION_READY", 
    "NEEDS_REVIEW", 
    "APPROVED", 
    "EDITED", 
    "NEEDS_EVIDENCE", 
    "ESCALATED", 
    "FINAL_DECISION"
]

HumanAction = Literal["APPROVE", "EDIT", "REQUEST_EVIDENCE", "ESCALATE", "REJECT"]

class HumanReview(BaseModel):
    review_id: str
    decision_artifact_id: str
    dispute_id: str
    
    ai_recommendation: Dict[str, Any]
    ai_confidence: float
    ai_explanation: Dict[str, Any]
    
    human_action: HumanAction
    human_reason: Optional[str] = None
    
    edited_decision: Optional[str] = None
    edited_response: Optional[str] = None
    
    reviewer_id: str
    review_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    previous_state: WorkflowStatus
    new_state: WorkflowStatus
