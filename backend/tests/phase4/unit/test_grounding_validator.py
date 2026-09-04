import pytest
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.evidence.models.evidence_item import EvidenceItem
from app.agents.evidence_reasoning.schemas import AgentEvidenceAssessment
from app.evidence.models.evidence_finding import EvidenceFinding
from app.evidence.reasoning.grounding_validator import validate_grounding

def test_grounding_valid():
    bundle = EvidenceBundle(
        dispute_id="DSP_1",
        structured_evidence=[
            EvidenceItem(
                evidence_id="EV-123",
                evidence_type="field_status",
                source_type="postgresql",
                source_id="1",
                content={"status": "delivered"},
                relevance_score=1.0,
                timestamp="2026-08-29T10:00:00Z",
                provenance={}
            )
        ],
        policy_evidence=[
            EvidenceItem(
                evidence_id="EV-POL-123",
                evidence_type="policy_chunk",
                source_type="postgresql",
                source_id="chunk-c821a",
                content={"text": "Delivery required", "policy_id": "POL-DISPUTE-001"},
                relevance_score=1.0,
                timestamp="2026-08-29T10:00:00Z",
                provenance={
                    "document_id": "POL-DISPUTE-001",
                    "chunk_id": "chunk-c821a",
                    "section": "Dispute Resolution Policy",
                    "version": "1.0"
                }
            )
        ],
        missing_evidence=[],
        retrieval_metadata={}
    )
    
    assessment = AgentEvidenceAssessment(
        evidence_findings=[
            EvidenceFinding(
                evidence_id="EV-123",
                relationship="contradicts",
                claim_aspect="delivery",
                finding="Delivery confirmed",
                policy_basis=["EV-POL-123"],
                confidence=0.9
            )
        ],
        overall_assessment="Testing"
    )
    
    is_valid, errors = validate_grounding(assessment, bundle)
    assert is_valid is True
    assert len(errors) == 0

def test_grounding_namespace_mismatch():
    """
    Given a policy EvidenceItem with evidence_id=EV-POL-123 and document_id=POL-DISPUTE-001,
    if the finding uses policy_basis=["POL-DISPUTE-001"], it MUST fail grounding.
    """
    bundle = EvidenceBundle(
        dispute_id="DSP_1",
        structured_evidence=[
            EvidenceItem(
                evidence_id="EV-123",
                evidence_type="field_status",
                source_type="postgresql",
                source_id="1",
                content={"status": "delivered"},
                relevance_score=1.0,
                timestamp="2026-08-29T10:00:00Z",
                provenance={}
            )
        ],
        policy_evidence=[
            EvidenceItem(
                evidence_id="EV-POL-123",
                evidence_type="policy_chunk",
                source_type="postgresql",
                source_id="chunk-c821a",
                content={"text": "Delivery required", "policy_id": "POL-DISPUTE-001"},
                relevance_score=1.0,
                timestamp="2026-08-29T10:00:00Z",
                provenance={
                    "document_id": "POL-DISPUTE-001",
                    "chunk_id": "chunk-c821a"
                }
            )
        ],
        missing_evidence=[],
        retrieval_metadata={}
    )
    
    assessment = AgentEvidenceAssessment(
        evidence_findings=[
            EvidenceFinding(
                evidence_id="EV-123",
                relationship="contradicts",
                claim_aspect="delivery",
                finding="Delivery confirmed",
                policy_basis=["POL-DISPUTE-001"], # Fails! Must be EV-POL-123
                confidence=0.9
            )
        ],
        overall_assessment="Testing"
    )
    
    is_valid, errors = validate_grounding(assessment, bundle)
    assert is_valid is False
    assert len(errors) == 1
    assert "Ungrounded policy reference ID: POL-DISPUTE-001" in errors[0]

def test_grounding_invalid_evidence():
    bundle = EvidenceBundle(
        dispute_id="DSP_1",
        structured_evidence=[],
        policy_evidence=[],
        missing_evidence=[],
        retrieval_metadata={}
    )
    
    assessment = AgentEvidenceAssessment(
        evidence_findings=[
            EvidenceFinding(
                evidence_id="FAKE-123",
                relationship="contradicts",
                claim_aspect="delivery",
                finding="I hallucinated this",
                policy_basis=["FAKE-POL"],
                confidence=0.9
            )
        ],
        overall_assessment="Testing"
    )
    
    is_valid, errors = validate_grounding(assessment, bundle)
    assert is_valid is False
    assert len(errors) == 2
    assert "Ungrounded factual evidence ID: FAKE-123" in errors[0]
    assert "Ungrounded policy reference ID: FAKE-POL" in errors[1]

def test_intended_provenance_chain():
    """
    Verify the intended provenance chain from policy_basis to the exact retrieved policy source.
    """
    bundle = EvidenceBundle(
        dispute_id="DSP_1",
        structured_evidence=[],
        policy_evidence=[
            EvidenceItem(
                evidence_id="EV-POL-123",
                evidence_type="policy_chunk",
                source_type="postgresql",
                source_id="chunk-c821a",
                content={"text": "Delivery required", "policy_id": "POL-DISPUTE-001"},
                relevance_score=1.0,
                timestamp="2026-08-29T10:00:00Z",
                provenance={
                    "document_id": "POL-DISPUTE-001",
                    "chunk_id": "chunk-c821a",
                    "section": "Dispute Resolution Policy",
                    "version": "1.0"
                }
            )
        ],
        missing_evidence=[],
        retrieval_metadata={}
    )
    
    finding = EvidenceFinding(
        evidence_id="EV-STRUCT-456",
        relationship="supports",
        claim_aspect="delivery",
        finding="Finding text",
        policy_basis=["EV-POL-123"],
        confidence=0.9
    )
    
    # Trace the chain
    retrieved_chunk_id = finding.policy_basis[0]
    
    # 1. Match retrieved chunk in bundle
    matched_item = next((item for item in bundle.policy_evidence if item.evidence_id == retrieved_chunk_id), None)
    assert matched_item is not None
    
    # 2. Extract document and chunk provenance
    assert matched_item.provenance["document_id"] == "POL-DISPUTE-001"
    assert matched_item.provenance["chunk_id"] == "chunk-c821a"
    assert matched_item.source_id == "chunk-c821a"
