"""
Shared data models for the guardrails module.

Contains:
- GuardrailResult: unified check result for all blockers/validators
- TablePolicy / ColumnPolicyConfig: per-table column access policy
- AuditEntry: structured audit log entry
"""

import time
from dataclasses import dataclass, field
from typing import Any


MAX_QUERY_LOG_LENGTH = 500


# ─── Unified Check Result ────────────────────────────────────────────────────


@dataclass
class GuardrailResult:
    """
    Unified result for all guardrail checks (blockers, validators, policy).

    Replaces: StarCheckResult, CatalogCheckResult, PolicyCheckResult, ValidationResult.
    """

    is_blocked: bool
    reason: str = ""
    blocked_table: str = ""  # optional: which table triggered the block


# ─── Column Policy Models ────────────────────────────────────────────────────


@dataclass
class TablePolicy:
    """Policy for a single table."""

    allowed_columns: list[str] = field(default_factory=list)
    sampleable_columns: list[str] = field(default_factory=list)
    required_filter_columns: list[str] = field(default_factory=list)
    allow_aggregates_without_filter: bool = False
    group_by_columns: list[str] = field(default_factory=list)
    max_rows: int | None = None


@dataclass
class ColumnPolicyConfig:
    """Full column policy configuration."""

    policies: dict[str, TablePolicy] = field(default_factory=dict)
    mode: str = "permissive"  # "permissive" or "strict"
    default_schema: str = "public"


# ─── Audit Entry ─────────────────────────────────────────────────────────────


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
