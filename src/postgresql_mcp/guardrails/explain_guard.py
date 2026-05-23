"""
Phase 10.10 — EXPLAIN Safety Guard.

Controls:
- BLOCK_EXPLAIN: reject EXPLAIN entirely (default True for sensitive profile)
- BLOCK_EXPLAIN_ANALYZE: reject EXPLAIN ANALYZE (default True — it executes the query)
"""

from postgresql_mcp.guardrails.models import GuardrailResult


def check_explain(
    analyze: bool,
    block_explain: bool = False,
    block_explain_analyze: bool = True,
) -> GuardrailResult:
    """
    Validate whether an EXPLAIN request is allowed.

    Args:
        analyze: Whether EXPLAIN ANALYZE was requested.
        block_explain: If True, block all EXPLAIN requests.
        block_explain_analyze: If True, block EXPLAIN ANALYZE (it executes the query).

    Returns:
        GuardrailResult — blocked if the EXPLAIN variant is disallowed.
    """
    if block_explain:
        return GuardrailResult(
            is_blocked=True,
            reason="EXPLAIN is not allowed in the current security profile.",
        )

    if analyze and block_explain_analyze:
        return GuardrailResult(
            is_blocked=True,
            reason=(
                "EXPLAIN ANALYZE is not allowed (it executes the query). "
                "Use EXPLAIN without ANALYZE to see the plan without execution."
            ),
        )

    return GuardrailResult(is_blocked=False)
