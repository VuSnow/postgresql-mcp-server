"""
ReadService — executes queries through the full guardrails pipeline.

Pipeline: RateLimiter → SecurityValidator → QueryRewriter → execute → PIIMasker → AuditLogger
"""

import logging
import time
from typing import Any, Optional

from postgresql_mcp.guardrails import GuardrailsPipeline, create_pipeline
from postgresql_mcp.guardrails.critical_patterns import check_critical_patterns
from postgresql_mcp.guardrails.explain_guard import check_explain
from postgresql_mcp.guardrails.security_validator import SecurityValidator
from postgresql_mcp.guardrails.user_context import validate_user_id, build_set_local_sql
from postgresql_mcp.services.postgresql.base import BaseService

logger = logging.getLogger(__name__)


class ReadService(BaseService):
    """Service layer for query execution with full guardrails."""

    def __init__(self, connection_manager, configs, pipeline: GuardrailsPipeline):
        super().__init__(connection_manager, configs)
        self._pipeline = pipeline
        # Standalone validator for dry_run (no rewrite/PII needed)
        self._security_validator = SecurityValidator(
            max_query_length=configs.max_query_length,
            read_only=configs.read_only,
            allow_destructive=configs.allow_destructive,
        )

    async def execute_query(self, query: str, user_id: Optional[str] = None) -> str:
        """
        Execute a SQL query with full guardrails pipeline.
        Returns LLM-friendly formatted result string.

        If user_id is provided and USER_CONTEXT_VARIABLE is configured,
        SET LOCAL is executed in the same transaction for RLS support.
        """
        await self.ensure_connected()

        # CRITICAL PATTERN CHECK (defense-in-depth, before AST)
        cp_check = check_critical_patterns(query)
        if cp_check.is_blocked:
            return f"Query blocked: {cp_check.reason}"

        # PRE-EXECUTE: rate limit + security + rewrite
        pre = self._pipeline.pre_execute(query)
        if not pre.allowed:
            return f"Query blocked: {pre.blocked_reason}"

        rewritten_query = pre.rewritten_query

        # RLS user context
        set_local_sql = None
        if user_id and self._configs.user_context_variable:
            id_check = validate_user_id(user_id)
            if id_check.is_blocked:
                return f"Query blocked: {id_check.reason}"
            set_local_sql = build_set_local_sql(
                self._configs.user_context_variable, user_id
            )

        # EXECUTE
        start = time.time()
        try:
            if set_local_sql:
                rows, columns = await self.client.execute_query_with_context(
                    set_local_sql,
                    rewritten_query,
                    timeout_seconds=self._configs.query_timeout_seconds,
                )
            else:
                rows, columns = await self.client.execute_query(
                    rewritten_query,
                    timeout_seconds=self._configs.query_timeout_seconds,
                )
            duration_ms = (time.time() - start) * 1000
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            self._pipeline.log_error(query, str(e), duration_ms)
            logger.error(f"[read_service] Query execution error: {e}")
            return f"Query error: {e}"

        # POST-EXECUTE: PII mask + audit log
        post = self._pipeline.post_execute(query, rows, columns, duration_ms)

        # Format output
        return self._format_results(post.rows, post.columns, post.duration_ms)

    async def dry_run_query(self, query: str) -> str:
        """
        Validate a query without executing it (security check only).
        No rewrite, no PII, no rate limit consumed.
        Returns validation result.
        """
        result = self._security_validator.validate(query)
        if result.is_valid:
            return "Query is valid. No security issues detected."
        else:
            return f"Query rejected: {result.reason}"

    async def explain_query(
        self,
        query: str,
        analyze: bool = False,
        format: str = "text",
    ) -> str:
        """
        Run EXPLAIN on a query. Returns the execution plan.
        EXPLAIN ANALYZE actually executes the query (use with caution).
        """
        await self.ensure_connected()

        # EXPLAIN safety guard
        explain_check = check_explain(
            analyze=analyze,
            block_explain=self._configs.effective_block_explain,
            block_explain_analyze=self._configs.block_explain_analyze,
        )
        if explain_check.is_blocked:
            return f"Query blocked: {explain_check.reason}"

        # Critical pattern check on the inner query
        cp_check = check_critical_patterns(query)
        if cp_check.is_blocked:
            return f"Query blocked: {cp_check.reason}"

        # Security check on the inner query
        validation = self._security_validator.validate(query)
        if not validation.is_valid:
            return f"Query rejected: {validation.reason}"

        try:
            plan = await self.client.explain_query(
                query,
                analyze=analyze,
                format=format,
                timeout_seconds=self._configs.query_timeout_seconds,
            )
            header = "EXPLAIN ANALYZE" if analyze else "EXPLAIN"
            return f"{header} ({format.upper()}):\n\n{plan}"
        except Exception as e:
            logger.error(f"[read_service] Explain error: {e}")
            return f"Explain error: {e}"

    def _format_results(
        self,
        rows: list[dict[str, Any]],
        columns: list[str],
        duration_ms: float,
    ) -> str:
        """Format query results as an LLM-friendly string."""
        if not rows:
            return f"Query returned 0 rows. ({duration_ms:.1f}ms)"

        lines = []

        # Header
        lines.append(f"Results: {len(rows)} row(s) in {duration_ms:.1f}ms")
        lines.append("")

        # Column headers
        header = " | ".join(columns)
        lines.append(header)
        lines.append("-" * len(header))

        # Rows (cap display at 50 for readability)
        display_limit = 50
        for row in rows[:display_limit]:
            values = [self._format_value(row.get(col)) for col in columns]
            lines.append(" | ".join(values))

        if len(rows) > display_limit:
            lines.append(f"... and {len(rows) - display_limit} more row(s)")

        return "\n".join(lines)

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a single cell value for display."""
        if value is None:
            return "NULL"
        if isinstance(value, str) and len(value) > 100:
            return value[:100] + "..."
        return str(value)
