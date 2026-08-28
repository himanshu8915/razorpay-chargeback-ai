"""
Log formatters — shared between technical and progress log output.
"""

import json
import logging
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Emits log records as single-line JSON for structured log parsing."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
