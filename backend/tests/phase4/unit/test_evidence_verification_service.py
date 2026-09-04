import pytest
from unittest.mock import patch, MagicMock
from app.evidence.services.evidence_verification_service import EvidenceVerificationService
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.evidence.models.evidence_item import EvidenceItem
from app.schemas.canonical_case import CanonicalCase

@pytest.mark.asyncio
@patch('app.evidence.services.evidence_verification_service.reason_evidence')
async def test_verification_service_success(mock_reason):
    # Mock reasoning agent output
    mock_assessment = MagicMock()
    
    from app.evidence.models.evidence_finding import EvidenceFinding
    
    mock_finding = EvidenceFinding(
        evidence_id="EV-1",
        relationship="supports",
        claim_aspect="delivery",
        finding="test",
        policy_basis=[],
        confidence=0.9
    )
    
    mock_assessment.evidence_findings = [mock_finding]
    mock_assessment.overall_assessment = "Looks good"
    # reason_evidence now returns (assessment, TokenUsage) tuple
    from app.decision.models.factors import TokenUsage
    mock_reason.return_value = (mock_assessment, TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15))
    
    case = MagicMock(spec=CanonicalCase)
    case.dispute = MagicMock()
    case.dispute.dispute_id = "DSP_123"
    
    bundle = EvidenceBundle(
        dispute_id="DSP_123",
        structured_evidence=[
            EvidenceItem(
                evidence_id="EV-1", evidence_type="field_status", source_type="db",
                source_id="1", content={"status": "delivered"}, relevance_score=1.0, timestamp="2026", provenance={}
            )
        ],
        policy_evidence=[],
        missing_evidence=[],
        retrieval_metadata={}
    )
    
    service = EvidenceVerificationService()
    # verify_evidence now returns (EvidenceAssessment, TokenUsage)
    final_assessment, usage = await service.verify_evidence(case, bundle)
    
    assert final_assessment.dispute_id == "DSP_123"
    assert final_assessment.completeness == "complete"
    assert "EV-1" in final_assessment.supporting_evidence
    assert final_assessment.confidence > 0.0
    # verify token usage is returned
    assert usage.total_tokens == 15
