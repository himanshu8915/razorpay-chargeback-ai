import json
import os
from datetime import datetime, timedelta

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/deadline_rules.json")

def resolve_deadline(dispute_opened_at: datetime) -> tuple[datetime, str, int]:
    """
    Calculates the operational deadline based on a configurable response window.
    Returns: (deadline, deadline_source, response_window_days)
    """
    response_window_days = 30 # Fallback
    source = "fallback"
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                rules = json.load(f)
                if "DEFAULT" in rules:
                    response_window_days = rules["DEFAULT"]
                    source = "deadline_rules.json"
        except Exception:
            pass
            
    deadline = dispute_opened_at + timedelta(days=response_window_days)
    return deadline, source, response_window_days
