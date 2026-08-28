import json
import os
from datetime import datetime

LOG_FILE = "/app/logs/initialization/latest.jsonl"

def init_logger():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    # Clear the previous log file
    with open(LOG_FILE, 'w') as f:
        pass

def log_event(stage: str, status: str, message: str):
    """
    Logs an event in JSONL format.
    Stages: DATABASE, DOWNLOAD, SANITY_CHECK, STRUCTURED_INGESTION, POLICY_EXTRACTION, CHUNKING, EMBEDDING, INDEXING, VERIFICATION, READY
    Status: SUCCESS, FAILED, INFO
    """
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "stage": stage,
        "status": status,
        "message": message
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(event) + '\n')
    print(f"[{event['timestamp']}] [{stage}] [{status}] {message}")
