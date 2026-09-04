import pytest
import asyncio
from app.evidence.services.evidence_discovery_service import EvidenceDiscoveryService
from app.evidence.services.evidence_verification_service import EvidenceVerificationService
from app.db.models import Dispute
from sqlalchemy import select
from unittest.mock import patch
from app.agents.evidence_reasoning.schemas import AgentEvidenceAssessment
from app.evidence.models.evidence_finding import EvidenceFinding

@pytest.mark.asyncio
async def test_end_to_end_verification_pipeline(db_session):
    # Fetch a real dispute
    result = await db_session.execute(select(Dispute.dispute_id).limit(1))
    dispute_id = result.scalar_one_or_none()
    
    if not dispute_id:
        pytest.skip("No disputes found in database to test Phase 4.")
        
    discovery_service = EvidenceDiscoveryService(db_session)
    verification_service = EvidenceVerificationService()
    
    try:
        # 1. Discovery (Phase 3)
        bundle, p3_usage = await discovery_service.discover_evidence(dispute_id)
        assert bundle is not None
        
        case = await discovery_service.case_service.get_case(dispute_id)
        
        # 2. Verification (Phase 4)
        assessment, p4_usage = await verification_service.verify_evidence(case, bundle)
        
        assert assessment is not None
        assert assessment.dispute_id == dispute_id
        assert assessment.completeness in ["complete", "partial", "insufficient"]
        assert 0.0 <= assessment.confidence <= 1.0
        
    except ImportError as e:
        pytest.skip(f"Skipping due to missing dependencies: {e}")

@pytest.mark.asyncio
async def test_verification_grounding_failure_penalty(db_session):
    """
    Verifies that a repeated grounding failure produces a GROUNDING_FAILURE risk flag
    and reduces the final confidence deterministically.
    """
    result = await db_session.execute(select(Dispute.dispute_id).limit(1))
    dispute_id = result.scalar_one_or_none()
    if not dispute_id:
        pytest.skip("No disputes found in database to test Phase 4.")
        
    discovery_service = EvidenceDiscoveryService(db_session)
    from app.evidence.models.evidence_bundle import EvidenceBundle
    from app.decision.models.factors import TokenUsage
    mock_bundle = EvidenceBundle(
        dispute_id=dispute_id,
        structured_evidence=[],
        policy_evidence=[],
        missing_evidence=[],
        retrieval_metadata={}
    )
    with patch.object(discovery_service, "discover_evidence", return_value=(mock_bundle, TokenUsage())):
        bundle, p3_usage = await discovery_service.discover_evidence(dispute_id)
    case = await discovery_service.case_service.get_case(dispute_id)
    
    # Create a mock assessment that will fail grounding
    mock_assessment = AgentEvidenceAssessment(
        evidence_findings=[
            EvidenceFinding(
                evidence_id="FAKE-123", # Fails grounding
                relationship="supports",
                claim_aspect="delivery",
                finding="Fake finding",
                policy_basis=["FAKE-POL-123"], # Fails grounding
                confidence=0.95
            )
        ],
        overall_assessment="Testing"
    )
    
    verification_service = EvidenceVerificationService()
    
    with patch("app.evidence.services.evidence_verification_service.reason_evidence", return_value=(mock_assessment, TokenUsage())):
        assessment, p4_usage = await verification_service.verify_evidence(case, bundle)
        
        assert "GROUNDING_FAILURE" in assessment.risk_flags
        # base confidence is 0.95. Grounding failure gives -0.30 -> 0.65.
        # if there are completeness penalties or conflicts, it might be lower.
        assert assessment.confidence <= 0.65
