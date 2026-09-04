import logging
from typing import List, Dict, Any
from app.representment.models.representation import RepresentationDraft
from app.representment.models.evidence_package import EvidencePackage
from app.representment.models.policy_mapping import PolicyRequirementMapping
from app.representment.models.validation import ValidationResult, ValidationChecks
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.evidence.models.evidence_assessment import EvidenceAssessment
from app.representment.rules import validation_rules

logger = logging.getLogger(__name__)

class ValidationService:
    def validate_draft(
        self,
        draft: RepresentationDraft,
        package: EvidencePackage,
        mapping: PolicyRequirementMapping,
        bundle: EvidenceBundle,
        assessment: EvidenceAssessment,
        max_length: int = 5000
    ) -> ValidationResult:
        logger.info("Executing deterministic validation on Representation Draft")
        
        checks = ValidationChecks()
        all_errors = []
        all_warnings = []
        
        # 1. Evidence Reference Validity
        ok_refs, ref_errs = validation_rules.validate_evidence_references(draft, bundle)
        checks.evidence_references = "PASS" if ok_refs else "FAIL"
        all_errors.extend(ref_errs)
        
        # 2. Unsupported Claim Detection
        ok_unsup, unsup_errs = validation_rules.validate_unsupported_claims(draft)
        checks.unsupported_claims = "PASS" if ok_unsup else "FAIL"
        all_errors.extend(unsup_errs)
        
        # 3. Evidence Consistency (Structured)
        ok_cons, cons_errs = validation_rules.validate_evidence_consistency(draft, bundle)
        checks.evidence_consistency = "PASS" if ok_cons else "FAIL"
        all_errors.extend(cons_errs)
        
        # 4. Policy Consistency
        ok_pol, pol_errs = validation_rules.validate_policy_consistency(draft, mapping)
        checks.policy_consistency = "PASS" if ok_pol else "FAIL"
        all_errors.extend(pol_errs)
        
        # 5. Contradiction Check
        # If the EvidenceAssessment flagged a critical conflict, we warn/fail if the 
        # draft makes claims around that conflict without nuance. 
        # For a deterministic check: we ensure no claim uses contradicting evidence blindly.
        con_errs = []
        contradicting_ids = set(assessment.contradicting_evidence)
        for arg in draft.factual_arguments:
            overlap = set(arg.evidence_ids).intersection(contradicting_ids)
            if overlap:
                con_errs.append(f"Factual argument uses known contradicting evidence {overlap} without resolving conflict.")
        
        checks.contradiction_check = "PASS" if not con_errs else "FAIL"
        all_errors.extend(con_errs)
        
        # 6. Required Evidence Coverage
        ok_req, req_errs = validation_rules.validate_required_coverage(package, mapping)
        checks.required_evidence = "PASS" if ok_req else "FAIL"
        all_errors.extend(req_errs)
        
        # 7. Format / Length
        ok_fmt, fmt_errs = validation_rules.validate_format(draft, max_length)
        checks.format = "PASS" if ok_fmt else "FAIL"
        all_errors.extend(fmt_errs)
        
        # Final status
        overall_status = "PASS" if not all_errors else "FAIL"
        
        return ValidationResult(
            status=overall_status,
            checks=checks,
            errors=all_errors,
            warnings=all_warnings
        )
        
    def mark_stale(self, previous_result: ValidationResult) -> ValidationResult:
        """
        Invalidates a previous validation result, marking it STALE 
        due to a human edit to evidence or text.
        """
        logger.info("Marking validation result as STALE.")
        stale_checks = ValidationChecks(
            evidence_references="STALE",
            unsupported_claims="STALE",
            evidence_consistency="STALE",
            policy_consistency="STALE",
            contradiction_check="STALE",
            required_evidence="STALE",
            format="STALE"
        )
        return ValidationResult(
            status="STALE",
            checks=stale_checks,
            errors=["Validation is stale due to manual edits. Re-validation required."],
            warnings=[]
        )
