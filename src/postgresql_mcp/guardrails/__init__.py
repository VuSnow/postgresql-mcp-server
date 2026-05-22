"""
GuardrailsPipeline — orchestrates the pre-execute and post-execute pipeline.

Pipeline flow:
  PRE-EXECUTE:
    1. RateLimiter.check()
    2. SecurityValidator.validate()
    3. QueryRewriter.rewrite()

  EXECUTE:
    → caller executes the (possibly rewritten) query

  POST-EXECUTE:
    4. PIIMasker.mask_rows()
    5. AuditLogger.log_execution()
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

from postgresql_mcp.guardrails.audit_logger import AuditLogger
from postgresql_mcp.guardrails.pii_masker import PIIMasker, PIIRule, parse_pii_rules
from postgresql_mcp.guardrails.query_rewriter import QueryRewriter
from postgresql_mcp.guardrails.rate_limiter import RateLimiter
from postgresql_mcp.guardrails.security_validator import SecurityValidator

logger = logging.getLogger(__name__)


@dataclass
class PreExecuteResult:
    """Result of pre-execute pipeline."""
    allowed: bool
    rewritten_query: str | None = None
    blocked_reason: str | None = None


@dataclass
class PostExecuteResult:
    """Result of post-execute pipeline."""
    rows: list[dict[str, Any]]
    columns: list[str]
    duration_ms: float


class GuardrailsPipeline:
    """Orchestrates all guardrail modules in sequence."""

    def __init__(
        self,
        rate_limiter: RateLimiter,
        security_validator: SecurityValidator,
        query_rewriter: QueryRewriter,
        pii_masker: PIIMasker,
        audit_logger: AuditLogger,
    ):
        self._rate_limiter = rate_limiter
        self._security_validator = security_validator
        self._query_rewriter = query_rewriter
        self._pii_masker = pii_masker
        self._audit_logger = audit_logger

    @property
    def audit_logger(self) -> AuditLogger:
        return self._audit_logger

    def pre_execute(self, query: str) -> PreExecuteResult:
        """
        Run pre-execute checks:
        1. Rate limit
        2. Security validation
        3. Query rewrite (LIMIT injection)

        Returns PreExecuteResult with allowed=False if blocked.
        """
        # 1. Rate limit check
        if not self._rate_limiter.check():
            reason = "Rate limit exceeded. Try again later."
            self._audit_logger.log_blocked(query, reason)
            return PreExecuteResult(allowed=False, blocked_reason=reason)

        # 2. Security validation
        validation = self._security_validator.validate(query)
        if not validation.is_valid:
            self._audit_logger.log_blocked(query, validation.reason)
            return PreExecuteResult(allowed=False, blocked_reason=validation.reason)

        # 3. Query rewrite
        rewritten = self._query_rewriter.rewrite(query)

        return PreExecuteResult(allowed=True, rewritten_query=rewritten)

    def post_execute(
        self,
        query: str,
        rows: list[dict[str, Any]],
        columns: list[str],
        duration_ms: float,
    ) -> PostExecuteResult:
        """
        Run post-execute processing:
        4. PII masking
        5. Audit logging

        Records the rate limit call on success.
        """
        # Record successful call in rate limiter
        self._rate_limiter.record()

        # 4. PII masking
        masked_rows = self._pii_masker.mask_rows(rows, columns)

        # 5. Audit log
        self._audit_logger.log_execution(query, duration_ms, len(rows))

        return PostExecuteResult(
            rows=masked_rows,
            columns=columns,
            duration_ms=duration_ms,
        )

    def log_error(self, query: str, error: str, duration_ms: float | None = None) -> None:
        """Log a query execution error."""
        self._audit_logger.log_error(query, error, duration_ms)


def create_pipeline(
    max_calls: int = 100,
    window_seconds: int = 3600,
    max_query_length: int = 10000,
    read_only: bool = True,
    allow_destructive: bool = False,
    default_limit: int = 100,
    max_limit: int = 1000,
    pii_rules_json: str | None = None,
) -> GuardrailsPipeline:
    """Factory function to create a fully configured pipeline."""
    return GuardrailsPipeline(
        rate_limiter=RateLimiter(max_calls=max_calls, window_seconds=window_seconds),
        security_validator=SecurityValidator(
            max_query_length=max_query_length,
            read_only=read_only,
            allow_destructive=allow_destructive,
        ),
        query_rewriter=QueryRewriter(default_limit=default_limit, max_limit=max_limit),
        pii_masker=PIIMasker(rules=parse_pii_rules(pii_rules_json)),
        audit_logger=AuditLogger(),
    )
