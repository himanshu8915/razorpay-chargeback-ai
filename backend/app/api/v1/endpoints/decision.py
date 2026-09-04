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

router = APIRouter()
logger = logging.getLogger(__name__)

decision_service = DecisionService()
review_service = HumanReviewService()

# In-memory lock to prevent duplicate concurrent analyses
ANALYZING_DISPUTES: Set[str] = set()

class AnalyzeRequest(BaseModel):
    # In a full app, we would take just the dispute_id and fetch case/bundle/assessment from DB
    pass

class ReviewRequest(BaseModel):
    action: str
    reviewer_id: str
    reason: Optional[str] = None
    edited_decision: Optional[str] = None
    edited_response: Optional[str] = None

async def run_analysis_pipeline(dispute_id: str):
    """Background task running Phase 3 -> 4 -> 5"""
    try:
        async with AsyncSessionLocal() as db:
            logger.info(f"Starting background analysis for {dispute_id}")
            
            # Phase 3
            discovery_service = EvidenceDiscoveryService(db)
            bundle, _ = await discovery_service.discover_evidence(dispute_id)
            canonical_case = await discovery_service.case_service.get_case(dispute_id)
            
            # Phase 4
            verification_service = EvidenceVerificationService()
            assessment, _ = await verification_service.verify_evidence(canonical_case, bundle)
            
            # Phase 5
            ds = DecisionService()
            result = await ds.analyze_dispute(dispute_id, canonical_case, assessment, [])
            logger.info(f"Analysis completed successfully for {dispute_id}")
            
    except Exception as e:
        logger.error(f"Analysis failed for {dispute_id}: {traceback.format_exc()}")
    finally:
        ANALYZING_DISPUTES.discard(dispute_id)


@router.post("/{dispute_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_dispute_endpoint(dispute_id: str, background_tasks: BackgroundTasks):
    """
    Thin orchestration boundary triggering Phase 3-5 pipeline.
    Idempotent: prevents duplicate or concurrent execution.
    """
    if dispute_id in ANALYZING_DISPUTES:
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

    ANALYZING_DISPUTES.add(dispute_id)
    background_tasks.add_task(run_analysis_pipeline, dispute_id)
    
    return {"status": "ANALYSIS_STARTED", "message": f"Background analysis started for {dispute_id}."}


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
