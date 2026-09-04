from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc, func
from typing import Dict, Optional
from datetime import datetime, timezone
from app.db.session import get_db
from app.db.models import Dispute, DecisionArtifactModel, Order
from app.services.case_service import CaseService, CaseAssemblyError
from app.services.demo_portfolio_resolver import DemoPortfolioResolver

router = APIRouter(
    prefix="/disputes",
    tags=["Disputes"]
)

@router.get("")
async def list_disputes(
    merchant_id: str,
    decision: str = Query(None, description="CONTEST, REVIEW, or ACCEPT"),
    min_amount: float = Query(None),
    max_amount: float = Query(None),
    sort_by: str = Query(None, description="amount, deadline, net_value"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    base_query = (
        select(Dispute, DecisionArtifactModel)
        .join(Order, Dispute.canonical_order_id == Order.order_id)
        .join(DecisionArtifactModel, Dispute.dispute_id == DecisionArtifactModel.dispute_id)
        .where(Order.merchant_id == merchant_id)
    )
    
    if decision:
        if decision == "REVIEW":
            base_query = base_query.where(
                (DecisionArtifactModel.decision.in_(["REVIEW", "ESCALATE", "HUMAN_REVIEW_REQUIRED", "NEEDS_EVIDENCE"]))
                | (DecisionArtifactModel.workflow_status.in_(["NEEDS_REVIEW", "IN_REVIEW"]))
            )
        else:
            base_query = base_query.where(DecisionArtifactModel.decision == decision)
        
    if min_amount is not None:
        base_query = base_query.where(Dispute.dispute_amount >= min_amount)
    if max_amount is not None:
        base_query = base_query.where(Dispute.dispute_amount <= max_amount)
        
    # Apply ordering
    if sort_by == "amount":
        col = Dispute.dispute_amount
        base_query = base_query.order_by(desc(col) if sort_desc else asc(col))
    elif sort_by == "deadline":
        col = DecisionArtifactModel.deadline
        base_query = base_query.order_by(desc(col) if sort_desc else asc(col))
    elif sort_by == "net_value":
        col = DecisionArtifactModel.net_expected_value
        base_query = base_query.order_by(desc(col) if sort_desc else asc(col))
    else:
        # Default fallback rules
        if decision == "CONTEST":
            base_query = base_query.order_by(desc(DecisionArtifactModel.net_expected_value))
        elif decision == "REVIEW":
            base_query = base_query.order_by(asc(DecisionArtifactModel.deadline))
        else:
            base_query = base_query.order_by(desc(Dispute.dispute_amount))
        
    offset = (page - 1) * size
    query = base_query.offset(offset).limit(size)
    
    result = await db.execute(query)
    rows = result.all()
    
    count_query = select(func.count()).select_from(
        base_query.with_only_columns(Dispute.dispute_id).order_by(None).subquery()
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    items = []
    for dispute, decision_art in rows:
        items.append({
            "dispute_id": dispute.dispute_id,
            "dispute_amount": dispute.dispute_amount,
            "dispute_type": dispute.dispute_type,
            "dispute_opened_at": dispute.dispute_opened_at.isoformat() if dispute.dispute_opened_at else None,
            "decision": decision_art.decision,
            "confidence": decision_art.confidence,
            "case_strength": decision_art.case_strength,
            "net_expected_value": decision_art.net_expected_value,
            "deadline": decision_art.deadline,
            "deadline_risk": decision_art.deadline_risk,
            "workflow_status": decision_art.workflow_status,
            "next_action": decision_art.next_action
        })
        
    return {
        "items": items,
        "total": total,
        "size": size
    }

@router.get("/unanalyzed")
async def list_unanalyzed_disputes(
    merchant_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Dedicated read-only adapter for unanalyzed disputes, ensuring
    we don't change the semantics of the existing analyzed queue.
    """
    live_demo_ids = DemoPortfolioResolver.get_live_demo_case_ids(merchant_id)
    if not live_demo_ids:
        return {"items": [], "total": 0, "size": size}

    base_query = (
        select(Dispute)
        .join(Order, Dispute.canonical_order_id == Order.order_id)
        .outerjoin(DecisionArtifactModel, Dispute.dispute_id == DecisionArtifactModel.dispute_id)
        .where(Order.merchant_id == merchant_id)
        .where(DecisionArtifactModel.dispute_id == None)
        .where(Dispute.dispute_id.in_(live_demo_ids))
        .order_by(desc(Dispute.dispute_opened_at))
    )
    
    offset = (page - 1) * size
    query = base_query.offset(offset).limit(size)
    
    result = await db.execute(query)
    rows = result.scalars().all()
    
    count_query = select(func.count()).select_from(
        base_query.with_only_columns(Dispute.dispute_id).order_by(None).subquery()
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    items = []
    for dispute in rows:
        items.append({
            "dispute_id": dispute.dispute_id,
            "dispute_amount": dispute.dispute_amount,
            "dispute_type": dispute.dispute_type,
            "dispute_opened_at": dispute.dispute_opened_at.isoformat() if dispute.dispute_opened_at else None,
            "workflow_status": "UNANALYZED"
        })
        
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }

from app.decision.services.decision_service import DecisionService
decision_service = DecisionService()

@router.get("/{dispute_id}")
async def get_dispute(dispute_id: str, db: AsyncSession = Depends(get_db)):
    service = CaseService(db)
    
    try:
        case = await service.get_case(dispute_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dispute {dispute_id} not found"
            )
            
        decision_art = await decision_service.get_decision(dispute_id)
        
        return {
            "case": case.model_dump(),
            "decision_artifact": decision_art
        }
    except HTTPException:
        raise
    except CaseAssemblyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Case Assembly Error: {str(e)}"
        )
    except Exception as e:
        # Generic fallback for database unavailability or unexpected errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable or Database Error"
        )
