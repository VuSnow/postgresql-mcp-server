"""
Phase 10.14 — Single Statement + Supported SQL Shapes.

Rules:
- Only ONE statement per query (no stacked queries via `;`)
- Block unsupported statement types: COPY, DO, CALL, Command
- Block SELECT INTO (writes data)
- Block LATERAL (complex join pattern)
- CTE/set-ops delegated to subquery_blocker (Phase 10.9)
"""

import sqlglot
from sqlglot import exp
from typing import Optional

from postgresql_mcp.guardrails.models import GuardrailResult
from postgresql_mcp.guardrails.sql_parser import parse_query

# Statement types that are always blocked
_BLOCKED_STATEMENT_TYPES = (
    exp.Copy,
    exp.Command,  # DO $$...$$, CALL, and other unsupported statements
)


def check_statement(
    sql: str,
    default_schema: str = "public",
) -> GuardrailResult:
    """
    Validate statement shape: single statement, supported type, no dangerous patterns.

    Args:
        sql: Raw SQL query.
        default_schema: Default schema for parsing.

    Returns:
        GuardrailResult — blocked if statement is multi-statement or unsupported type.
    """
    parsed = parse_query(sql, default_schema)

    # Parse error — let other guardrails handle
    if parsed.parse_error:
        return GuardrailResult(is_blocked=False)

    # ── Multiple statements ──────────────────────────────────────────────

    if parsed.statement_count > 1:
        return GuardrailResult(
            is_blocked=True,
            reason=(
                "Only one SQL statement per query is allowed. "
                "Remove ';' separators and send one statement at a time."
            ),
        )

    # ── Parse statement for type checking ────────────────────────────────

    stmts = sqlglot.parse(sql, dialect="postgres")
    if not stmts:
        return GuardrailResult(is_blocked=False)

    stmt = stmts[0]

    # ── Blocked statement types ──────────────────────────────────────────

    if isinstance(stmt, _BLOCKED_STATEMENT_TYPES):
        stmt_type = type(stmt).__name__.upper()
        return GuardrailResult(
            is_blocked=True,
            reason=(
                f"Statement type '{stmt_type}' is not allowed. "
                f"Only SELECT queries are supported."
            ),
        )

    # ── SELECT INTO ──────────────────────────────────────────────────────

    if stmt.find(exp.Into) is not None:
        return GuardrailResult(
            is_blocked=True,
            reason=(
                "SELECT INTO is not allowed (creates a table). "
                "Use a plain SELECT query instead."
            ),
        )

    # ── LATERAL ──────────────────────────────────────────────────────────

    if parsed.has_lateral:
        return GuardrailResult(
            is_blocked=True,
            reason=(
                "LATERAL joins are not allowed. "
                "Rewrite as a standard JOIN or correlated subquery."
            ),
        )

    return GuardrailResult(is_blocked=False)
