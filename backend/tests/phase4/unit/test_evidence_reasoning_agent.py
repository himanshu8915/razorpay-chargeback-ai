import pytest
from unittest.mock import patch, MagicMock
from app.schemas.canonical_case import CanonicalCase
from app.evidence.models.evidence_bundle import EvidenceBundle
from app.evidence.models.evidence_item import EvidenceItem
from app.agents.evidence_reasoning.evidence_reasoning_agent import reason_evidence

@patch('app.agents.evidence_reasoning.evidence_reasoning_agent.get_llm_gateway')
def test_reason_evidence_agent(mock_get_llm):
    # Mock LLM response
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '''
    {
      "evidence_findings": [
        {
          "evidence_id": "EV-123",
          "relationship": "contradicts",
          "claim_aspect": "delivery",
          "finding": "Delivery confirmed.",
          "policy_basis": [],
          "confidence": 0.95
        }
      ],
      "overall_assessment": "Delivery confirmed."
    }
    '''
    mock_response.usage_metadata = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    mock_response.response_metadata = {"model_name": "test-model"}
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm

    # Setup inputs
    case = MagicMock()
    case.claim = "Not received"
    case.dispute_type = "fraud"
    case.dispute_reason = "product_not_received"

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
        policy_evidence=[],
        missing_evidence=[],
        retrieval_metadata={}
    )

    assessment, usage = reason_evidence(case, bundle)
    
    assert assessment.overall_assessment == "Delivery confirmed."
    assert len(assessment.evidence_findings) == 1
    assert assessment.evidence_findings[0].evidence_id == "EV-123"
    assert assessment.evidence_findings[0].relationship == "contradicts"
    # Verify token usage is returned
    assert usage.total_tokens == 15
    assert usage.input_tokens == 10
