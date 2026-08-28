"""
Structured logger for technical/system logs.
Writes to logs/ directory and stdout.
"""

import logging
import logging.handlers
import os
from pathlib import Path

from app.config.settings import settings


def _ensure_log_dir(subdir: str) -> Path:
    path = Path(settings.log_dir) / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logger(name: str, subdir: str = "application") -> logging.Logger:
    """
    Return a named logger that writes to both stdout and a rotating file.
    All loggers share the same level from settings.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured — avoid duplicate handlers
        return logger

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Stdout handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Rotating file handler
    log_dir = _ensure_log_dir(subdir)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / f"{name.replace('.', '_')}.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
