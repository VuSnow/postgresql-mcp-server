"""
MCP Tools — SQL query execution with guardrails.

Tools: execute_query, dry_run_query, explain_query
"""

import logging

from typing import Optional

from postgresql_mcp.server import mcp, read_service

logger = logging.getLogger(__name__)


@mcp.tool()
async def execute_query(query: str, user_id: Optional[str] = None) -> dict:
    """Execute a SQL query and return results.

    The query passes through a security pipeline:
    - Rate limiting (sliding window)
    - Security validation (injection detection, forbidden keywords)
    - Auto LIMIT injection (capped to server max)
    - PII masking on results
    - Audit logging

    Args:
        query: SQL SELECT query to execute.
        user_id: Optional user identifier for Row-Level Security (RLS).
                 Only used when USER_CONTEXT_VARIABLE is configured.

    Returns formatted results with column headers and row data.
    Only SELECT queries are allowed in read-only mode.
    """
    try:
        return {"result": await read_service.execute_query(query, user_id=user_id)}
    except Exception as e:
        logger.error(f"[tool] execute_query error: {e}")
        return {"error": str(e)}


@mcp.tool()
async def dry_run_query(query: str) -> dict:
    """Validate a SQL query without executing it.

    Runs security checks only — no rate limit consumed, no data returned.
    Use this to verify a query is safe before executing.

    Args:
        query: SQL query to validate.

    Returns whether the query passes security validation.
    """
    try:
        return {"result": await read_service.dry_run_query(query)}
    except Exception as e:
        logger.error(f"[tool] dry_run_query error: {e}")
        return {"error": str(e)}


@mcp.tool()
async def explain_query(
    query: str,
    analyze: bool = False,
    format: str = "text",
) -> dict:
    """Get the execution plan for a SQL query.

    Args:
        query: SQL query to explain.
        analyze: If True, actually executes the query to get real timing
                 (use with caution on write queries). Defaults to False.
        format: Output format — 'text', 'json', 'xml', or 'yaml'.
                Defaults to 'text'.

    Returns the EXPLAIN output showing how PostgreSQL will execute the query.
    Useful for optimizing slow queries.
    """
    try:
        return {"result": await read_service.explain_query(query, analyze=analyze, format=format)}
    except Exception as e:
        logger.error(f"[tool] explain_query error: {e}")
        return {"error": str(e)}
