"""
Phase 10.9 — Subquery / CTE / Set Operation Blocker.

Blocks structural query shapes based on config:
- BLOCK_SUBQUERIES (default: true) — reject nested SELECT in FROM/WHERE/HAVING/SELECT list
- ALLOW_CTE (default: false) — reject WITH clauses unless explicitly allowed
- ALLOW_SET_OPERATIONS (default: false) — reject UNION/INTERSECT/EXCEPT
- ALLOW_RECURSIVE_CTE (default: false) — reject recursive CTEs even if CTE allowed
"""

from postgresql_mcp.guardrails.models import GuardrailResult
from postgresql_mcp.guardrails.sql_parser import parse_query, ParsedQuery


def check_query_structure(
    sql: str,
    block_subqueries: bool = True,
    allow_cte: bool = False,
    allow_set_operations: bool = False,
    allow_recursive_cte: bool = False,
    default_schema: str = "public",
) -> GuardrailResult:
    """
    Validate query structural shape against policy.

    Args:
        sql: Raw SQL query.
        block_subqueries: If True, reject subqueries in SELECT/FROM/WHERE/HAVING.
        allow_cte: If False, reject WITH (CTE) clauses.
        allow_set_operations: If False, reject UNION/INTERSECT/EXCEPT.
        allow_recursive_cte: If False, reject recursive CTEs (even if CTE allowed).
        default_schema: Default schema for parsing.

    Returns:
        GuardrailResult — blocked if disallowed structure is found.
    """
    parsed = parse_query(sql, default_schema)
    if parsed.parse_error:
        # Can't validate structure — let other guardrails handle parse errors
        return GuardrailResult(is_blocked=False)

    return _check_parsed_structure(
        parsed,
        block_subqueries=block_subqueries,
        allow_cte=allow_cte,
        allow_set_operations=allow_set_operations,
        allow_recursive_cte=allow_recursive_cte,
    )


def _check_parsed_structure(
    parsed: ParsedQuery,
    block_subqueries: bool,
    allow_cte: bool,
    allow_set_operations: bool,
    allow_recursive_cte: bool,
) -> GuardrailResult:
    """Check parsed query shape against policy flags."""

    # Subquery check
    if block_subqueries and parsed.has_subquery:
        return GuardrailResult(
            is_blocked=True,
            reason=(
                "Subqueries are not allowed (BLOCK_SUBQUERIES=true). "
                "Rewrite as a JOIN or separate queries."
            ),
        )

    # CTE check
    if parsed.has_cte and not allow_cte:
        return GuardrailResult(
            is_blocked=True,
            reason=(
                "CTE (WITH clause) is not allowed (ALLOW_CTE=false). "
                "Rewrite without WITH or enable CTE support."
            ),
        )

    # Recursive CTE check (even if CTE allowed, recursive may not be)
    if parsed.has_recursive_cte and not allow_recursive_cte:
        return GuardrailResult(
            is_blocked=True,
            reason=(
                "Recursive CTE (WITH RECURSIVE) is not allowed (ALLOW_RECURSIVE_CTE=false). "
                "Recursive queries can cause unbounded execution."
            ),
        )

    # Set operations check
    if parsed.has_set_operation and not allow_set_operations:
        return GuardrailResult(
            is_blocked=True,
            reason=(
                "Set operations (UNION/INTERSECT/EXCEPT) are not allowed "
                "(ALLOW_SET_OPERATIONS=false). Rewrite as separate queries."
            ),
        )

    return GuardrailResult(is_blocked=False)


# Backward-compatible alias
StructureCheckResult = GuardrailResult
