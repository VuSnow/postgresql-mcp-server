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
from typing import Any

from postgresql_mcp.guardrails.models import AuditEntry, MAX_QUERY_LOG_LENGTH

logger = logging.getLogger("postgresql_mcp.audit")


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
