from datetime import datetime, timezone
from app.decision.models.factors import DeadlineRisk
import math

def calculate_deadline_risk(deadline: datetime, current_time: datetime = None) -> DeadlineRisk:
    """
    Calculates time remaining and derives the risk and urgency class.
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)
        
    # Ensure deadline is timezone aware for accurate comparison
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
        
    time_remaining_td = deadline - current_time
    time_remaining_hours = time_remaining_td.total_seconds() / 3600.0
    
    if time_remaining_hours < 0:
        return DeadlineRisk(
            time_remaining_hours=round(time_remaining_hours, 2),
            risk="CRITICAL",
            urgency="EXPIRED"
        )
    elif time_remaining_hours <= 24:
        return DeadlineRisk(
            time_remaining_hours=round(time_remaining_hours, 2),
            risk="CRITICAL",
            urgency="URGENT"
        )
    elif time_remaining_hours <= 72:
        return DeadlineRisk(
            time_remaining_hours=round(time_remaining_hours, 2),
            risk="APPROACHING",
            urgency="HIGH"
        )
    else:
        return DeadlineRisk(
            time_remaining_hours=round(time_remaining_hours, 2),
            risk="SAFE",
            urgency="NORMAL"
        )
