"""
User-facing progress event schema and emitter.
These events feed the frontend progress UI — they are NOT raw technical logs.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import ProgressStatus
from app.core.types import CaseId


class ProgressEvent(BaseModel):
    """
    Structured progress event emitted by every major operation.
    Consumed by the frontend progress panel.
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: CaseId | None = None
    phase: str
    component: str
    status: ProgressStatus
    progress: int = Field(default=0, ge=0, le=100)
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


def make_event(
    phase: str,
    component: str,
    status: ProgressStatus,
    message: str,
    progress: int = 0,
    case_id: CaseId | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProgressEvent:
    """Convenience factory for creating a ProgressEvent."""
    return ProgressEvent(
        phase=phase,
        component=component,
        status=status,
        progress=progress,
        message=message,
        case_id=case_id,
        metadata=metadata or {},
    )
