import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.representment.models.submission import SubmissionPackage, AuditLogEntry
from app.representment.models.representation import FinalRepresentation, RepresentationDraft
from app.representment.services.validation_service import ValidationService

logger = logging.getLogger(__name__)

class RepresentmentReviewService:
    def __init__(self, validation_service: ValidationService):
        self.validation_service = validation_service

    def process_review(
        self,
        package: SubmissionPackage,
        action: str,
        reviewer_id: str,
        edited_text: Optional[str] = None
    ) -> SubmissionPackage:
        """
        Process human review action on the submission package.
        Valid actions: APPROVE, EDIT, REJECT, REGENERATE
        """
        logger.info(f"Processing Representment Review: {action} by {reviewer_id} for {package.dispute_id}")
        
        if package.status == "READY_FOR_SUBMISSION" and action != "REJECT":
            raise ValueError("Package is already approved and ready for submission.")
            
        if action == "APPROVE":
            if package.validation_status.status != "PASS":
                raise ValueError("Cannot approve a package that has not passed validation.")
            
            package.human_approved = True
            package.approved_by = reviewer_id
            package.approved_at = datetime.now(timezone.utc)
            package.status = "READY_FOR_SUBMISSION"
            
            # Finalize representation payload
            rep = package.representation
            draft_to_use = rep.human_edited_draft if rep.is_human_edited else rep.original_ai_draft
            # A simple flattening for submission payload
            rep.final_text_payload = self._flatten_draft(draft_to_use)
            
            self._audit(package, "APPROVED", reviewer_id, "Package approved for submission.")
            
        elif action == "EDIT":
            if not edited_text:
                raise ValueError("EDIT action requires edited_text.")
                
            # Parse edited text into a new Draft (simplified for MVO)
            # In a real UI, this might be a JSON patch or structured form update.
            # Here we just override the claim_response.
            edited_draft = package.representation.original_ai_draft.model_copy(deep=True)
            edited_draft.claim_response = edited_text
            
            package.representation.human_edited_draft = edited_draft
            package.representation.is_human_edited = True
            
            # STALE State
            package.validation_status = self.validation_service.mark_stale(package.validation_status)
            package.status = "STALE"
            
            self._audit(package, "HUMAN_EDITED", reviewer_id, "Human edited the representation draft. Re-validation required.")
            
        elif action == "REGENERATE":
            package.status = "REGENERATION_REQUESTED"
            self._audit(package, "REGENERATION_REQUESTED", reviewer_id, "Human requested regeneration.")
            
        elif action == "REJECT":
            package.status = "REJECTED"
            self._audit(package, "REJECTED", reviewer_id, "Human rejected the representment package.")
            
        else:
            raise ValueError(f"Unknown action: {action}")
            
        return package

    def _flatten_draft(self, draft: RepresentationDraft) -> str:
        lines = [draft.summary, "", draft.claim_response, ""]
        lines.append("Factual Arguments:")
        for arg in draft.factual_arguments:
            lines.append(f"- {arg.statement} (Evidence: {', '.join(arg.evidence_ids)})")
        lines.append("")
        lines.append("Policy Arguments:")
        for arg in draft.policy_arguments:
            lines.append(f"- {arg.statement} (Policy: {', '.join(arg.policy_source_ids)})")
        lines.append("")
        lines.append(draft.conclusion)
        return "\n".join(lines)
        
    def _audit(self, package: SubmissionPackage, action: str, actor: str, details: str):
        log = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            action=action,
            actor=actor,
            details=details
        )
        package.audit_history.append(log)
