import pytest
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.evidence.models.evidence_item import EvidenceItem
from app.evidence.reasoning.conflict_detector import detect_conflicts

def test_detect_order_delivery_conflict():
    bundle = EvidenceBundle(
        dispute_id="1",
        structured_evidence=[
            EvidenceItem(
                evidence_id="ORD-1", evidence_type="field_status", source_type="db",
                source_id="1", content={"order_status": "cancelled"}, relevance_score=1.0, timestamp="2026", provenance={}
            ),
            EvidenceItem(
                evidence_id="DEL-1", evidence_type="field_status", source_type="db",
                source_id="1", content={"delivery_state": "delivered"}, relevance_score=1.0, timestamp="2026", provenance={}
            )
        ],
        policy_evidence=[],
        missing_evidence=[],
        retrieval_metadata={}
    )
    conflicts = detect_conflicts(bundle)
    assert len(conflicts) == 1
    assert conflicts[0].topic == "fulfillment_status"
    assert conflicts[0].severity == "high"
    assert "ORD-1" in conflicts[0].evidence_ids
    assert "DEL-1" in conflicts[0].evidence_ids

def test_detect_no_conflict():
    bundle = EvidenceBundle(
        dispute_id="1",
        structured_evidence=[
            EvidenceItem(
                evidence_id="ORD-1", evidence_type="field_status", source_type="db",
                source_id="1", content={"order_status": "fulfilled"}, relevance_score=1.0, timestamp="2026", provenance={}
            ),
            EvidenceItem(
                evidence_id="DEL-1", evidence_type="field_status", source_type="db",
                source_id="1", content={"delivery_state": "delivered"}, relevance_score=1.0, timestamp="2026", provenance={}
            )
        ],
        policy_evidence=[],
        missing_evidence=[],
        retrieval_metadata={}
    )
    conflicts = detect_conflicts(bundle)
    assert len(conflicts) == 0
