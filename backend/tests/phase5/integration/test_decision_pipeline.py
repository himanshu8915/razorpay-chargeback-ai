import pytest
import asyncio
from unittest.mock import patch, MagicMock
from sqlalchemy import select
from app.db.models import Dispute, DecisionArtifactModel
from app.evidence.services.evidence_discovery_service import EvidenceDiscoveryService
from app.evidence.services.evidence_verification_service import EvidenceVerificationService
from app.decision.services.decision_service import DecisionService
from app.decision.models.decision import CaseStrength, ConfidenceAssessment, RiskAssessment, DecisionExplanation
from app.decision.models.factors import TokenUsage

@pytest.mark.asyncio(loop_scope="function")
async def test_full_decision_pipeline(db_session):
    # Fetch a real dispute
    result = await db_session.execute(select(Dispute.dispute_id).limit(1))
    dispute_id = result.scalar_one_or_none()
    
    if not dispute_id:
        pytest.skip("No disputes found in database to test Phase 5.")
        
    discovery_service = EvidenceDiscoveryService(db_session)
    verification_service = EvidenceVerificationService()
    decision_service = DecisionService()
    
    # 1. Phase 3: Discovery
    from app.agents.evidence_discovery.schemas import CaseEvidencePlan, PolicyEvidencePlan
    
    with patch("app.evidence.services.evidence_discovery_service.plan_case_evidence") as mock_case, \
         patch("app.evidence.services.evidence_discovery_service.plan_policy_evidence") as mock_policy:
         
        mock_case.return_value = (CaseEvidencePlan(evidence_categories=[], relevant_entities=[], relevant_fields=[], rationale="mock"), TokenUsage())
        mock_policy.return_value = (PolicyEvidencePlan(search_queries=["test"], policy_topics=[], required_policy_context=["mock"]), TokenUsage())
        
        bundle, p3_usage = await discovery_service.discover_evidence(dispute_id)
        case = await discovery_service.case_service.get_case(dispute_id)
    
    # Mock Phase 4 LLM reasoning just to make it fast and deterministic for this test
    with patch("app.evidence.services.evidence_verification_service.reason_evidence") as mock_reason:
        from app.agents.evidence_reasoning.schemas import AgentEvidenceAssessment
        mock_reason.return_value = (AgentEvidenceAssessment(
            evidence_findings=[],
            overall_assessment="Mocked"
        ), TokenUsage())
        assessment, p4_usage = await verification_service.verify_evidence(case, bundle)
        
    # 2. Phase 5: Decision Service with Mocked LLM nodes
    mock_case_strength = CaseStrength(case_strength=0.9, supporting_factors=[], weaknesses=[], critical_conflicts=[])
    mock_confidence = ConfidenceAssessment(confidence=0.9, confidence_level="HIGH", reasons=[])
    mock_risk = RiskAssessment(critical_conflict=False, missing_critical_evidence=False, policy_ambiguity=False, risk_level="LOW", reasons=[])
    mock_explanation = DecisionExplanation(
        summary="Test", why_we_believe_we_can_win=[], supporting_evidence=[],
        contradicting_evidence=[], risks=[], economic_summary="", deadline_summary="",
        next_action="", sources=[]
    )
    mock_usage = TokenUsage(input_tokens=10, output_tokens=10, total_tokens=20, model="mock")
    
    with patch("app.agents.decision.supervisor.analyze_case_strength", return_value=(mock_case_strength, mock_usage)), \
         patch("app.agents.decision.supervisor.analyze_confidence", return_value=(mock_confidence, mock_usage)), \
         patch("app.agents.decision.supervisor.analyze_risk", return_value=(mock_risk, mock_usage)), \
         patch("app.agents.decision.supervisor.generate_explanation", return_value=(mock_explanation, mock_usage)):
         
        result = await decision_service.analyze_dispute(
            dispute_id=dispute_id,
            canonical_case=case,
            evidence_assessment=assessment,
            policy_context=[]
        )
        
        assert result is not None
        assert result["workflow_status"] == "NEEDS_REVIEW"
        assert "ai_recommendation" in result
        
        artifact = await decision_service.get_decision(dispute_id)
        assert artifact is not None
        assert artifact["dispute_id"] == dispute_id
        assert artifact["workflow_status"] == "NEEDS_REVIEW"
