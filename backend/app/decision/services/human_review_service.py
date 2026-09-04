import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import DecisionArtifactModel, HumanReviewModel
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

class HumanReviewService:
    async def process_review(
        self,
        dispute_id: str,
        action: str,
        reviewer_id: str,
        edited_decision: Optional[str] = None,
        edited_response: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a human review action.
        """
        
        logger.info(f"Processing Human Review for {dispute_id}: {action}")
        
        db = AsyncSessionLocal()
        try:
            
            result = await db.execute(
                select(DecisionArtifactModel)
                .filter(DecisionArtifactModel.dispute_id == dispute_id)
                .order_by(DecisionArtifactModel.created_at.desc())
            )
            artifact = result.scalar_one_or_none()
            
            if not artifact:
                raise ValueError(f"No decision artifact found for dispute {dispute_id}")
                
            previous_state = artifact.workflow_status
            
            # Allowable transitions from NEEDS_REVIEW
            if previous_state not in ["NEEDS_REVIEW", "EXPLANATION_READY"]:
                raise ValueError(f"Invalid workflow state for review: {previous_state}")
            
            # Determine new state based on action
            if action == "APPROVE":
                new_state = "FINAL_DECISION"
                # If AI recommended ACCEPT, final is ACCEPT. If CONTEST, final is CONTEST
                # Usually captured downstream or explicitly in edited_decision if we want to store it here
            elif action == "EDIT":
                new_state = "FINAL_DECISION"
            elif action == "REQUEST_EVIDENCE":
                new_state = "NEEDS_EVIDENCE"
            elif action == "ESCALATE":
                new_state = "ESCALATED"
                edited_decision = "ESCALATE"
            elif action == "REJECT":
                new_state = "FINAL_DECISION"
            else:
                raise ValueError(f"Unknown action: {action}")
                
            # Create HumanReview record
            review_id = f"HR-{uuid.uuid4().hex[:12].upper()}"
            
            review = HumanReviewModel(
                review_id=review_id,
                decision_artifact_id=artifact.decision_artifact_id,
                dispute_id=dispute_id,
                ai_recommendation={"action": artifact.decision},
                ai_confidence=artifact.confidence,
                ai_explanation={"summary": artifact.rationale},
                human_action=action,
                human_reason=reason,
                edited_decision=edited_decision,
                edited_response=edited_response,
                reviewer_id=reviewer_id,
                review_timestamp=datetime.now(timezone.utc),
                previous_state=previous_state,
                new_state=new_state
            )
            
            # Update Artifact state and decision if modified
            artifact.workflow_status = new_state
            if edited_decision and edited_decision in ["CONTEST", "ACCEPT"]:
                artifact.decision = edited_decision
            
            db.add(review)
            await db.commit()
            await db.refresh(review)
            
            logger.info(f"Human review persisted for {dispute_id}. New state: {new_state}")
            
            return {
                "review_id": review_id,
                "dispute_id": dispute_id,
                "action": action,
                "new_state": new_state
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to process human review: {e}")
            raise
        finally:
            await db.close()
