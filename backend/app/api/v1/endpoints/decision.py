import asyncio
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from pydantic import BaseModel
from typing import Optional, Set
import traceback
import logging

from app.db.session import AsyncSessionLocal
from app.db.models import DecisionArtifactModel
from app.decision.services.decision_service import DecisionService
from app.decision.services.human_review_service import HumanReviewService
from app.evidence.services.evidence_discovery_service import EvidenceDiscoveryService
from app.evidence.services.evidence_verification_service import EvidenceVerificationService
from app.services.case_service import CaseService
from app.api.v1.endpoints.execution_state import execution_registry

router = APIRouter()
logger = logging.getLogger(__name__)

decision_service = DecisionService()
review_service = HumanReviewService()

decision_service = DecisionService()
review_service = HumanReviewService()

class AnalyzeRequest(BaseModel):
    # In a full app, we would take just the dispute_id and fetch case/bundle/assessment from DB
    pass

class ReviewRequest(BaseModel):
    action: str
    reviewer_id: str
    reason: Optional[str] = None
    edited_decision: Optional[str] = None
    edited_response: Optional[str] = None

async def _do_analysis(dispute_id: str):
    async with AsyncSessionLocal() as db:
        logger.info(f"Starting background analysis for {dispute_id}")
        
        # Phase 3
        execution_registry.update_node(dispute_id, "evidence_discovery", "Running Evidence Discovery (Phase 3)...")
        discovery_service = EvidenceDiscoveryService(db)
        bundle, _ = await discovery_service.discover_evidence(dispute_id)
        canonical_case = await discovery_service.case_service.get_case(dispute_id)
        
        # Phase 4
        execution_registry.update_node(dispute_id, "evidence_verification", "Running Evidence Verification (Phase 4)...")
        verification_service = EvidenceVerificationService()
        assessment, _ = await verification_service.verify_evidence(canonical_case, bundle)
        
        # Phase 5
        execution_registry.update_node(dispute_id, "decision_analysis", "Running Decision Analysis (Phase 5)...")
        ds = DecisionService()
        result = await ds.analyze_dispute(dispute_id, canonical_case, assessment, [])
        logger.info(f"Analysis completed successfully for {dispute_id}")
        return result

async def run_analysis_pipeline(dispute_id: str):
    """Background task running Phase 3 -> 4 -> 5"""
    try:
        # Wrap the whole pipeline in a 60-second timeout
        # Using a separate thread to prevent synchronous LangGraph operations from blocking asyncio.wait_for cancellation
        await asyncio.wait_for(_do_analysis(dispute_id), timeout=60.0)
        execution_registry.complete_analysis(dispute_id)
    except asyncio.TimeoutError:
        logger.error(f"Analysis timed out for {dispute_id}")
        execution_registry.timeout_analysis(dispute_id)
    except Exception as e:
        logger.error(f"Analysis failed for {dispute_id}: {traceback.format_exc()}")
        execution_registry.fail_analysis(dispute_id, str(e))


@router.post("/{dispute_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_dispute_endpoint(dispute_id: str, background_tasks: BackgroundTasks):
    """
    Thin orchestration boundary triggering Phase 3-5 pipeline.
    Idempotent: prevents duplicate or concurrent execution.
    """
    state = execution_registry.get_state(dispute_id)
    if state and state.status == "RUNNING":
        return {"status": "ANALYSIS_IN_PROGRESS", "message": f"Dispute {dispute_id} is currently being analyzed."}
        
    # Check if already analyzed
    decision_art = await decision_service.get_decision(dispute_id)
    if decision_art:
        return {"status": "ALREADY_ANALYZED", "message": f"Dispute {dispute_id} already has a decision artifact."}
        
    async with AsyncSessionLocal() as db:
        # Validate dispute exists
        case_service = CaseService(db)
        case = await case_service.get_case(dispute_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")

    execution_registry.start_analysis(dispute_id, [
        {"id": "evidence_discovery", "label": "Evidence Discovery (Phase 3)"},
        {"id": "case_evidence_planner", "label": "Case Evidence Planner"},
        {"id": "structured_retrieval", "label": "Structured Retrieval"},
        {"id": "policy_evidence_planner", "label": "Policy Evidence Planner"},
        {"id": "hybrid_policy_retrieval", "label": "Hybrid Policy Retrieval"},
        
        {"id": "evidence_verification", "label": "Evidence Verification (Phase 4)"},
        {"id": "node_reasoning", "label": "Evidence Reasoning Agent"},
        {"id": "node_validation", "label": "Grounding Validator"},
        {"id": "node_completeness", "label": "Completeness Check"},
        {"id": "node_conflict", "label": "Conflict Detector"},
        {"id": "node_confidence_verification", "label": "Verification Confidence"},
        {"id": "node_build", "label": "Assessment Builder"},
        
        {"id": "decision_analysis", "label": "Decision Analysis (Phase 5)"},
        {"id": "node_case_strength", "label": "Case Strength Agent"},
        {"id": "node_confidence_decision", "label": "Decision Confidence Agent"},
        {"id": "node_risk", "label": "Risk Assessment Agent"},
        {"id": "calculate_success", "label": "Success Likelihood Calculator"},
        {"id": "calculate_deadline", "label": "Deadline Risk Calculator"},
        {"id": "calculate_economics", "label": "Economics Calculator"},
        {"id": "decision_engine", "label": "Decision Engine"},
        {"id": "explanation_agent", "label": "Explanation Agent"}
    ])
    background_tasks.add_task(run_analysis_pipeline, dispute_id)
    
    return {"status": "ANALYSIS_STARTED", "message": f"Background analysis started for {dispute_id}."}

@router.get("/{dispute_id}/progress")
async def get_analysis_progress(dispute_id: str):
    state = execution_registry.get_state(dispute_id)
    if not state:
        return {"status": "NOT_STARTED", "dispute_id": dispute_id}
    return state.model_dump()


@router.get("/{dispute_id}/decision")
async def get_decision_endpoint(dispute_id: str):
    """
    Get the decision brief for the frontend.
    """
    decision = await decision_service.get_decision(dispute_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision artifact not found")
    return decision

@router.post("/{dispute_id}/review")
async def review_decision_endpoint(dispute_id: str, request: ReviewRequest):
    """
    Process Human-in-the-loop action.
    """
    try:
        result = await review_service.process_review(
            dispute_id=dispute_id,
            action=request.action,
            reviewer_id=request.reviewer_id,
            reason=request.reason,
            edited_decision=request.edited_decision,
            edited_response=request.edited_response
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing review: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")
