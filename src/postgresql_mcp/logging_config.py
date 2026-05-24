"""
Structured JSON logging configuration for production.

Outputs JSON lines to stdout for easy integration with log aggregators
(CloudWatch, ELK, Datadog, etc.).
"""

import json
import logging
import sys
import time
from typing import Any


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include audit data if present
        if hasattr(record, "audit"):
            log_entry["audit"] = record.audit

        # Include exception info
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure root logger with JSON structured output.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # JSON formatter for production
    json_formatter = JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z")

    # Stream handler → stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(json_formatter)
    handler.setLevel(log_level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
