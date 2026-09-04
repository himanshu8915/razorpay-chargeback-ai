import pytest
import os
from datetime import datetime, timedelta
from app.services.deadline_resolver import resolve_deadline

def test_resolve_deadline():
    opened_at = datetime(2026, 1, 1, 12, 0)
    deadline, source, window = resolve_deadline(opened_at)
    
    # Defaults to 30 days based on config
    assert window == 30
    assert deadline == opened_at + timedelta(days=30)
    assert source in ["deadline_rules.json", "fallback"]
