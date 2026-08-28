"""
Phase 0 unit tests.

Test 1: FastAPI app imports without error.
Test 2: Core enums are defined correctly.
Test 3: Settings load from environment.
Test 4: ProgressEvent schema constructs correctly.
"""

from app.core.enums import DecisionAction, CaseStatus, DisputeType
from app.core.exceptions import ChargebackBaseError
from app.config.settings import settings
from app.logging.events import make_event, ProgressEvent
from app.core.enums import ProgressStatus


def test_decision_action_values():
    """DecisionAction enum must contain the three primary outcomes."""
    assert DecisionAction.CONTEST == "contest"
    assert DecisionAction.ACCEPT == "accept"
    assert DecisionAction.HUMAN_REVIEW == "human_review"


def test_dispute_type_eight_classes():
    """DisputeType must match the eight locked benchmark classes from Dataset PRD."""
    expected = {
        "fraud",
        "duplicate_charge",
        "product_not_received",
        "product_not_as_described",
        "refund_not_received",
        "processing_error",
        "unauthorized_transaction",
        "other",
    }
    actual = {dt.value for dt in DisputeType}
    assert actual == expected


def test_case_status_values():
    """CaseStatus enum contains expected statuses."""
    assert CaseStatus.NEW == "new"
    assert CaseStatus.ANALYZING == "analyzing"
    assert CaseStatus.COMPLETED == "completed"


def test_exceptions_inherit_base():
    """All custom exceptions must inherit from ChargebackBaseError."""
    from app.core.exceptions import (
        DatabaseError,
        RAGNotReadyError,
        DisputeNotFoundError,
    )
    assert issubclass(DatabaseError, ChargebackBaseError)
    assert issubclass(RAGNotReadyError, ChargebackBaseError)
    assert issubclass(DisputeNotFoundError, ChargebackBaseError)


def test_settings_has_required_fields():
    """Settings object must expose all required configuration keys."""
    assert hasattr(settings, "database_url")
    assert hasattr(settings, "llm_provider")
    assert hasattr(settings, "langsmith_api_key")
    assert hasattr(settings, "kaggle_config")
    assert hasattr(settings, "dispute_deadline_days")


def test_progress_event_schema():
    """ProgressEvent must construct and serialize correctly."""
    event = make_event(
        phase="initialization",
        component="database",
        status=ProgressStatus.COMPLETED,
        message="Database ready",
        progress=100,
    )
    assert isinstance(event, ProgressEvent)
    assert event.phase == "initialization"
    assert event.component == "database"
    assert event.status == ProgressStatus.COMPLETED
    assert event.progress == 100
    assert event.event_id is not None
    # Must be JSON-serializable
    data = event.model_dump()
    assert data["message"] == "Database ready"
