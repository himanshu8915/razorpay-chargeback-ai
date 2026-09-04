import pytest
from pydantic import ValidationError
from app.evidence.models.evidence_finding import EvidenceFinding
from app.evidence.models.evidence_conflict import EvidenceConflict
from app.evidence.models.evidence_assessment import EvidenceAssessment

def test_evidence_finding_valid():
    finding = EvidenceFinding(
        evidence_id="DEL_123",
        relationship="contradicts",
        claim_aspect="product_received",
        finding="Delivery record marks the order as delivered.",
        policy_basis=["POL-001"],
        confidence=0.9
    )
    assert finding.evidence_id == "DEL_123"
    assert finding.relationship == "contradicts"

def test_evidence_finding_invalid_relationship():
    with pytest.raises(ValidationError):
        EvidenceFinding(
            evidence_id="DEL_123",
            relationship="proves_merchant_right", # invalid enum
            claim_aspect="product_received",
            finding="Delivery record marks the order as delivered.",
            policy_basis=["POL-001"],
            confidence=0.9
        )

def test_evidence_finding_invalid_confidence():
    with pytest.raises(ValidationError):
        EvidenceFinding(
            evidence_id="DEL_123",
            relationship="supports",
            claim_aspect="product_received",
            finding="Delivery record marks the order as delivered.",
            policy_basis=["POL-001"],
            confidence=1.5 # invalid confidence > 1.0
        )

def test_evidence_conflict_valid():
    conflict = EvidenceConflict(
        evidence_ids=["ORD_1", "DEL_1"],
        topic="fulfillment",
        description="Order cancelled but marked delivered.",
        severity="high"
    )
    assert conflict.severity == "high"
    assert len(conflict.evidence_ids) == 2

def test_evidence_assessment_valid():
    assessment = EvidenceAssessment(
        dispute_id="DSP_123",
        evidence_findings=[],
        supporting_evidence=[],
        contradicting_evidence=[],
        non_probative_evidence=[],
        missing_evidence=[],
        conflicts=[],
        policy_findings=[],
        completeness="complete",
        overall_assessment="All good.",
        confidence=0.95,
        risk_flags=[]
    )
    assert assessment.completeness == "complete"
    assert assessment.confidence == 0.95
