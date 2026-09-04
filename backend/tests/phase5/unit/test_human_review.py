import pytest
from unittest.mock import patch, MagicMock
from app.decision.services.human_review_service import HumanReviewService
from app.db.models import DecisionArtifactModel

import pytest_asyncio
from unittest.mock import AsyncMock

@pytest_asyncio.fixture
def mock_db():
    with patch("app.decision.services.human_review_service.AsyncSessionLocal") as mock:
        session = AsyncMock()
        mock.return_value = session
        yield session

@pytest.fixture
def mock_artifact():
    artifact = DecisionArtifactModel(
        decision_artifact_id="DA-123",
        dispute_id="DSP-1",
        decision="CONTEST",
        confidence=0.9,
        case_strength=0.8,
        success_likelihood=0.85,
        recoverable_amount=100.0,
        expected_recovery=85.0,
        estimated_operational_cost=10.0,
        net_expected_value=75.0,
        token_usage={},
        token_cost={},
        reason_codes=[],
        key_evidence=[],
        supporting_evidence=[],
        contradicting_evidence=[],
        missing_evidence=[],
        risk_flags=[],
        deadline_risk="LOW",
        next_action="CONTEST",
        rationale="test",
        workflow_status="NEEDS_REVIEW"
    )
    return artifact

@pytest.mark.asyncio
async def test_approve_action(mock_db, mock_artifact):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mock_artifact
    mock_db.execute.return_value = result_mock
    
    service = HumanReviewService()
    result = await service.process_review(
        dispute_id="DSP-1",
        action="APPROVE",
        reviewer_id="user1"
    )
    
    assert result["new_state"] == "FINAL_DECISION"
    assert mock_artifact.workflow_status == "FINAL_DECISION"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_escalate_action(mock_db, mock_artifact):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mock_artifact
    mock_db.execute.return_value = result_mock
    
    service = HumanReviewService()
    result = await service.process_review(
        dispute_id="DSP-1",
        action="ESCALATE",
        reviewer_id="user1"
    )
    
    assert result["new_state"] == "ESCALATED"
    assert mock_artifact.workflow_status == "ESCALATED"

@pytest.mark.asyncio
async def test_request_evidence_action(mock_db, mock_artifact):
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mock_artifact
    mock_db.execute.return_value = result_mock
    
    service = HumanReviewService()
    result = await service.process_review(
        dispute_id="DSP-1",
        action="REQUEST_EVIDENCE",
        reviewer_id="user1"
    )
    
    assert result["new_state"] == "NEEDS_EVIDENCE"
    assert mock_artifact.workflow_status == "NEEDS_EVIDENCE"
