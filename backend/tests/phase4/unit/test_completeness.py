import pytest
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.evidence.models.evidence_item import EvidenceItem
from app.evidence.reasoning.completeness import determine_completeness

def test_completeness_complete():
    bundle = EvidenceBundle(
        dispute_id="1",
        structured_evidence=[
            EvidenceItem(
                evidence_id="1", evidence_type="test", source_type="db",
                source_id="1", content={}, relevance_score=1.0, timestamp="2026", provenance={}
            )
        ],
        policy_evidence=[],
        missing_evidence=[], # No missing evidence
        retrieval_metadata={}
    )
    status, flags = determine_completeness(bundle)
    assert status == "complete"
    assert len(flags) == 0

def test_completeness_partial():
    bundle = EvidenceBundle(
        dispute_id="1",
        structured_evidence=[
            EvidenceItem(
                evidence_id="1", evidence_type="test", source_type="db",
                source_id="1", content={}, relevance_score=1.0, timestamp="2026", provenance={}
            )
        ],
        policy_evidence=[],
        missing_evidence=["Missing delivery confirmation"],
        retrieval_metadata={}
    )
    status, flags = determine_completeness(bundle)
    assert status == "partial"
    assert len(flags) == 1

def test_completeness_insufficient():
    bundle = EvidenceBundle(
        dispute_id="1",
        structured_evidence=[], # Missing all structured evidence
        policy_evidence=[],
        missing_evidence=["Structured data is entirely missing or null."],
        retrieval_metadata={}
    )
    status, flags = determine_completeness(bundle)
    assert status == "insufficient"
