import pytest
from app.agents.decision.explanation_agent import generate_explanation
from unittest.mock import patch, MagicMock

@pytest.fixture
def base_args():
    # Setup some basic mocks for the arguments
    case = MagicMock()
    case.dispute.dispute_id = "DSP-1"
    
    assessment = MagicMock()
    # Mock finding with a valid evidence ID
    finding = MagicMock()
    finding.evidence_id = "EV-123"
    assessment.evidence_findings = [finding]
    assessment.policy_findings = ["POL-123"]
    
    recommendation = MagicMock()
    recommendation.action = "CONTEST"
    recommendation.confidence = 0.9
    recommendation.success_likelihood = 0.9
    recommendation.expected_recovery = 100.0
    recommendation.operational_cost = 0.0
    recommendation.net_expected_value = 100.0
    
    case_strength = MagicMock()
    confidence = MagicMock()
    risk = MagicMock()
    deadline_risk = MagicMock()
    cost_breakdown = MagicMock()
    
    return {
        "case": case,
        "assessment": assessment,
        "recommendation": recommendation,
        "case_strength": case_strength,
        "confidence": confidence,
        "risk": risk,
        "deadline_risk": deadline_risk,
        "cost_breakdown": cost_breakdown,
        "policy_context": []
    }

def test_explanation_valid_sources(base_args):
    args = base_args.copy()
    
    mock_llm_res = MagicMock()
    mock_llm_res.content = '{"summary": "Test", "why_we_believe_we_can_win": [], "supporting_evidence": [], "contradicting_evidence": [], "risks": [], "economic_summary": "test", "deadline_summary": "test", "next_action": "test", "sources": ["EV-123", "POL-123"]}'
    mock_llm_res.usage_metadata = {"input_tokens": 10, "output_tokens": 10, "total_tokens": 20}
    mock_llm_res.response_metadata = {"model_name": "test-model"}
    
    with patch("app.agents.decision.explanation_agent.get_llm_gateway") as mock_gateway:
        mock_gateway.return_value.invoke.return_value = mock_llm_res
        
        explanation, usage = generate_explanation(**args)
        assert explanation.summary == "Test"

def test_explanation_invalid_sources(base_args):
    args = base_args.copy()
    
    mock_llm_res = MagicMock()
    # "MANUFACTURED-456" is not in the assessment's evidence findings
    mock_llm_res.content = '{"summary": "Test", "sources": ["EV-123", "MANUFACTURED-456"]}'
    mock_llm_res.usage_metadata = {"input_tokens": 10, "output_tokens": 10, "total_tokens": 20}
    mock_llm_res.response_metadata = {"model_name": "test-model"}
    
    with patch("app.agents.decision.explanation_agent.get_llm_gateway") as mock_gateway:
        mock_gateway.return_value.invoke.return_value = mock_llm_res
        
        with pytest.raises(ValueError, match="Explanation Validation FAILED: Unknown or manufactured sources detected"):
            generate_explanation(**args)
