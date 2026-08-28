"""
Shared type aliases used across the application.
"""

from typing import Any

# JSON-serialisable dict
JsonDict = dict[str, Any]

# Dispute identifier
DisputeId = str

# Case identifier (same format as dispute ID for Phase 0)
CaseId = str
