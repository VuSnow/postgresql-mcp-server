"""
AuditLogger — structured logging for all query executions.

Logs:
- Query text (truncated)
- Rows returned
- Execution duration
- Blocked reason (if rejected by guardrails)
- Timestamp
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("postgresql_mcp.audit")

MAX_QUERY_LOG_LENGTH = 500


@dataclass
class AuditEntry:
    """A single audit log entry."""
    query: str
    duration_ms: float | None = None
    rows_returned: int | None = None
    blocked: bool = False
    blocked_reason: str | None = None
    error: str | None = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for structured logging."""
        d = {
            "query": self.query[:MAX_QUERY_LOG_LENGTH],
            "timestamp": self.timestamp,
            "blocked": self.blocked,
        }
        if self.duration_ms is not None:
            d["duration_ms"] = round(self.duration_ms, 2)
        if self.rows_returned is not None:
            d["rows_returned"] = self.rows_returned
        if self.blocked_reason:
            d["blocked_reason"] = self.blocked_reason
        if self.error:
            d["error"] = self.error
        return d


class AuditLogger:
    """Records and logs audit entries for query executions."""

    def __init__(self):
        self._entries: list[AuditEntry] = []

    def log_execution(
        self,
        query: str,
        duration_ms: float,
        rows_returned: int,
    ) -> None:
        """Log a successful query execution."""
        entry = AuditEntry(
            query=query,
            duration_ms=duration_ms,
            rows_returned=rows_returned,
        )
        self._entries.append(entry)
        logger.info(
            "Query executed",
            extra={"audit": entry.to_dict()},
        )

    def log_blocked(self, query: str, reason: str) -> None:
        """Log a blocked query."""
        entry = AuditEntry(
            query=query,
            blocked=True,
            blocked_reason=reason,
        )
        self._entries.append(entry)
        logger.warning(
            f"Query blocked: {reason}",
            extra={"audit": entry.to_dict()},
        )

    def log_error(self, query: str, error: str, duration_ms: float | None = None) -> None:
        """Log a query that resulted in an error."""
        entry = AuditEntry(
            query=query,
            error=error,
            duration_ms=duration_ms,
        )
        self._entries.append(entry)
        logger.error(
            f"Query error: {error}",
            extra={"audit": entry.to_dict()},
        )

    @property
    def entries(self) -> list[AuditEntry]:
        """Access logged entries (for testing/inspection)."""
        return self._entries

    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
