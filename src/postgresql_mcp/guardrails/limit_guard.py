"""
Phase 10.11 — LIMIT / OFFSET Enforcement.

Rules:
- No LIMIT → reject in text2sql/sensitive; pass in general (rewriter injects DEFAULT_LIMIT)
- LIMIT > MAX_LIMIT → reject
- OFFSET > MAX_OFFSET → reject
- Pure aggregates (COUNT, SUM, etc. with no GROUP BY) exempt from LIMIT requirement

Config-driven: uses MAX_LIMIT, MAX_OFFSET, DEFAULT_LIMIT, security_profile.
"""

from typing import Optional

from postgresql_mcp.guardrails.models import GuardrailResult
from postgresql_mcp.guardrails.sql_parser import parse_query, is_pure_aggregate


def check_limit_offset(
    sql: str,
    max_limit: int = 1000,
    max_offset: int = 10000,
    require_limit: bool = False,
    default_schema: str = "public",
) -> GuardrailResult:
    """
    Validate LIMIT and OFFSET values in a SQL query.

    Args:
        sql: Raw SQL query.
        max_limit: Maximum allowed LIMIT value.
        max_offset: Maximum allowed OFFSET value.
        require_limit: If True, queries without LIMIT are rejected
                       (except pure aggregates).
        default_schema: Default schema for parsing.

    Returns:
        GuardrailResult — blocked if LIMIT/OFFSET violates policy.
    """
    parsed = parse_query(sql, default_schema)
    if parsed.parse_error:
        return GuardrailResult(is_blocked=False)

    # Pure aggregate queries don't need LIMIT (single-row result)
    import sqlglot
    from sqlglot import exp
    stmts = sqlglot.parse(sql, dialect="postgres")
    stmt = stmts[0] if stmts else None

    # Only enforce LIMIT/OFFSET on SELECT statements
    if stmt is not None and not isinstance(stmt, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        return GuardrailResult(is_blocked=False)

    pure_agg = is_pure_aggregate(stmt) if stmt else False

    # ── LIMIT checks ─────────────────────────────────────────────────────

    if parsed.limit is None:
        if require_limit and not pure_agg:
            return GuardrailResult(
                is_blocked=True,
                reason=(
                    "Query must include a LIMIT clause. "
                    "Add LIMIT to bound the result set."
                ),
            )
    else:
        if parsed.limit > max_limit:
            return GuardrailResult(
                is_blocked=True,
                reason=(
                    f"LIMIT {parsed.limit} exceeds maximum allowed value of {max_limit}. "
                    f"Reduce LIMIT to at most {max_limit}."
                ),
            )
        if parsed.limit < 0:
            return GuardrailResult(
                is_blocked=True,
                reason="LIMIT must not be negative.",
            )

    # ── OFFSET checks ────────────────────────────────────────────────────

    if parsed.offset is not None:
        if parsed.offset > max_offset:
            return GuardrailResult(
                is_blocked=True,
                reason=(
                    f"OFFSET {parsed.offset} exceeds maximum allowed value of {max_offset}. "
                    f"Use keyset/cursor pagination instead of large OFFSET."
                ),
            )
        if parsed.offset < 0:
            return GuardrailResult(
                is_blocked=True,
                reason="OFFSET must not be negative.",
            )

    return GuardrailResult(is_blocked=False)
