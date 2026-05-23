"""
SELECT * blocking.

Prevents queries using wildcard column selection (SELECT *, table.*, alias.*).
Forces agents to explicitly list columns, enabling column policy enforcement.

COUNT(*) and other aggregate functions using * are NOT blocked.
"""

from postgresql_mcp.guardrails.models import GuardrailResult
from postgresql_mcp.guardrails.sql_parser import parse_query

# Backward-compatible alias
StarCheckResult = GuardrailResult


def check_select_star(sql: str, default_schema: str = "public") -> StarCheckResult:
    """
    Check if a SQL query uses SELECT * or table.* wildcard.

    Does NOT block COUNT(*), SUM(*), or other aggregate functions.

    Args:
        sql: Raw SQL query string.
        default_schema: Default schema for table normalization.

    Returns:
        StarCheckResult indicating whether the query is blocked.
    """
    parsed = parse_query(sql, default_schema)

    if parsed.parse_error:
        return StarCheckResult(is_blocked=False)

    if parsed.has_star:
        return StarCheckResult(
            is_blocked=True,
            reason=(
                "SELECT * is not allowed. Please list columns explicitly "
                "(e.g. SELECT id, name FROM table)."
            ),
        )

    return StarCheckResult(is_blocked=False)
