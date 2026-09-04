from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from app.schemas.canonical_case import CanonicalCase
from app.decision.services.decision_service import DecisionService
# In a real app we'd fetch these from a database/repository layer
# For Phase 6 MVO we mock the fetch to demonstrate the workflow.
from app.agents.representment.supervisor import build_representment_graph
from app.agents.representment.state import RepresentmentState
from app.representment.services.representment_review_service import RepresentmentReviewService
from app.representment.services.validation_service import ValidationService

router = APIRouter()
logger = logging.getLogger(__name__)

decision_service = DecisionService()
validation_service = ValidationService()
review_service = RepresentmentReviewService(validation_service)
graph = build_representment_graph()

class RepresentmentReviewRequest(BaseModel):
    action: str
    reviewer_id: str
    edited_text: Optional[str] = None

# Mock in-memory state store for Phase 6 MVO
# A real implementation persists RepresentmentState to DB
_representment_store: Dict[str, RepresentmentState] = {}

@router.post("/{dispute_id}/representment")
def start_representment(dispute_id: str):
    """Starts the Phase 6 workflow."""
    # 1. Fetch Decision, Assessment, Bundle, Case (Mocked)
    decision = decision_service.get_decision(dispute_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found.")
        
    # We pretend to fetch the rest...
    # if decision.action != "CONTEST":
    #    raise HTTPException(status_code=400, detail="Only CONTEST decisions can enter Phase 6.")
    
    # In full integration, we build initial state and run graph.invoke()
    # For now, we return 501 until full DB integration
    raise HTTPException(status_code=501, detail="Implement db fetch of case/bundle to start Phase 6")

@router.get("/{dispute_id}/representment")
def get_representment_state(dispute_id: str):
    state = _representment_store.get(dispute_id)
    if not state:
        raise HTTPException(status_code=404, detail="Representment state not found.")
    return state

@router.post("/{dispute_id}/representment/review")
def review_representment(dispute_id: str, request: RepresentmentReviewRequest):
    state = _representment_store.get(dispute_id)
    if not state or not state.get("submission_package"):
        raise HTTPException(status_code=404, detail="No submission package ready for review.")
        
    try:
        package = state["submission_package"]
        updated_package = review_service.process_review(
            package=package,
            action=request.action,
            reviewer_id=request.reviewer_id,
            edited_text=request.edited_text
        )
        state["submission_package"] = updated_package
        return {"status": "success", "package_status": updated_package.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing representment review: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
