"""
QueryRewriter — auto-injects LIMIT, caps existing LIMIT.

Rules:
- If query has no LIMIT → append LIMIT {default_limit}
- If query has LIMIT > max_limit → rewrite to max_limit
- Skip rewriting for pure aggregate queries (COUNT, SUM, AVG, MIN, MAX without GROUP BY... that return single row)
- CTE-aware: only inject LIMIT on the final SELECT, not inside WITH clauses
"""

import logging
import re

logger = logging.getLogger(__name__)

# Matches LIMIT clause with a number
_LIMIT_RE = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)

# Matches OFFSET clause (we preserve it)
_OFFSET_RE = re.compile(r"\bOFFSET\s+\d+\b", re.IGNORECASE)

# Pure aggregate detection — SELECT with only aggregate functions and no GROUP BY
_AGGREGATE_FUNCS = re.compile(
    r"\bSELECT\s+(?:(?:COUNT|SUM|AVG|MIN|MAX|BOOL_AND|BOOL_OR|ARRAY_AGG|STRING_AGG)\s*\()",
    re.IGNORECASE,
)
_GROUP_BY_RE = re.compile(r"\bGROUP\s+BY\b", re.IGNORECASE)

# Detect CTE (WITH ... AS (...) SELECT ...)
_CTE_RE = re.compile(r"\bWITH\b", re.IGNORECASE)

# Find the final SELECT in a CTE query (naive but effective for most cases)
_FINAL_SELECT_RE = re.compile(r"\)\s*SELECT\b", re.IGNORECASE)


def _is_pure_aggregate(sql: str) -> bool:
    """Check if query is a pure aggregate (single-row result, no GROUP BY)."""
    if _GROUP_BY_RE.search(sql):
        return False
    return bool(_AGGREGATE_FUNCS.search(sql))


def _find_final_statement_start(sql: str) -> int:
    """
    Find the start of the final SELECT statement.
    For CTE queries, this is after the last `) SELECT`.
    For simple queries, this is 0.
    """
    if not _CTE_RE.match(sql.strip()):
        return 0

    # Find the last `) SELECT` pattern
    matches = list(_FINAL_SELECT_RE.finditer(sql))
    if matches:
        # Return position of SELECT (after the `)`)
        last_match = matches[-1]
        return last_match.start() + 1  # skip the `)`

    return 0


class QueryRewriter:
    """Rewrites queries to enforce LIMIT constraints."""

    def __init__(self, default_limit: int = 100, max_limit: int = 1000):
        self._default_limit = default_limit
        self._max_limit = max_limit

    def rewrite(self, query: str) -> str:
        """
        Apply LIMIT rewriting rules to a query.
        Returns the (possibly modified) query.
        """
        # Skip pure aggregates — they return one row
        if _is_pure_aggregate(query):
            logger.debug("[rewriter] Skipping aggregate query.")
            return query

        # Find the final statement portion to analyze
        final_start = _find_final_statement_start(query)
        final_portion = query[final_start:]

        # Check for existing LIMIT in the final statement
        limit_match = _LIMIT_RE.search(final_portion)

        if limit_match:
            # Cap existing LIMIT if it exceeds max
            existing_limit = int(limit_match.group(1))
            if existing_limit > self._max_limit:
                logger.debug(
                    f"[rewriter] Capping LIMIT {existing_limit} → {self._max_limit}"
                )
                # Replace in the original query at the correct position
                abs_start = final_start + limit_match.start()
                abs_end = final_start + limit_match.end()
                query = (
                    query[:abs_start]
                    + f"LIMIT {self._max_limit}"
                    + query[abs_end:]
                )
            return query

        # No LIMIT found — inject default
        # Strip trailing semicolons/whitespace, append LIMIT, re-add semicolons
        stripped = query.rstrip()
        has_semicolon = stripped.endswith(";")
        if has_semicolon:
            stripped = stripped[:-1].rstrip()

        new_query = f"{stripped}\nLIMIT {self._default_limit}"
        if has_semicolon:
            new_query += ";"

        logger.debug(f"[rewriter] Injected LIMIT {self._default_limit}")
        return new_query
