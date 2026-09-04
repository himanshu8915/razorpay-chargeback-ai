import os
import json
import logging
from datetime import datetime, timezone
from app.representment.models.submission import SubmissionPackage, AuditLogEntry

logger = logging.getLogger(__name__)

class SubmissionService:
    def __init__(self, results_dir: str = "results/disputes"):
        self.results_dir = results_dir

    def persist_submission_package(self, package: SubmissionPackage):
        """
        Persists the immutable submission package to disk for evaluation/audit.
        This provides the final artifact of Phase 6.
        """
        dispute_dir = os.path.join(self.results_dir, package.dispute_id)
        os.makedirs(dispute_dir, exist_ok=True)
        
        # We assume CanonicalCase, FinalDecision, EvidenceBundle are already 
        # serialized by their respective phases, but we write Phase 6 artifacts here.
        
        representation_path = os.path.join(dispute_dir, "representation.json")
        with open(representation_path, "w") as f:
            f.write(package.representation.model_dump_json(indent=2))
            
        evidence_path = os.path.join(dispute_dir, "selected_evidence.json")
        with open(evidence_path, "w") as f:
            f.write(package.evidence.model_dump_json(indent=2))
            
        policy_path = os.path.join(dispute_dir, "policy_mapping.json")
        with open(policy_path, "w") as f:
            f.write(package.policy_mapping.model_dump_json(indent=2))
            
        validation_path = os.path.join(dispute_dir, "validation.json")
        with open(validation_path, "w") as f:
            f.write(package.validation_status.model_dump_json(indent=2))
            
        package_path = os.path.join(dispute_dir, "submission_package.json")
        with open(package_path, "w") as f:
            f.write(package.model_dump_json(indent=2))
            
        logger.info(f"Successfully persisted Submission Package for {package.dispute_id} to {dispute_dir}")

    def append_audit_log(self, package: SubmissionPackage, action: str, actor: str, details: str = None) -> SubmissionPackage:
        """
        Appends an audit log entry to the package.
        """
        log = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            action=action,
            actor=actor,
            details=details
        )
        package.audit_history.append(log)
        return package
