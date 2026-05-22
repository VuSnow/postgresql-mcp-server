"""
MCP Tools — UPDATE operations.

Tools: update
"""

import logging
from typing import Any

from postgresql_mcp.server import mcp, update_service

logger = logging.getLogger(__name__)


@mcp.tool()
async def update(
    table_name: str,
    set_data: dict[str, Any],
    where_clause: str,
    where_values: list[Any] | None = None,
    schema: str = "public",
) -> dict:
    """Update rows in a table matching a WHERE condition.

    WHERE clause is mandatory — full-table updates are not allowed.

    Args:
        table_name: Name of the table to update.
        set_data: Column-value mapping for SET. Example: {"status": "active"}
        where_clause: WHERE expression with positional params.
                      Params start at $(N+1) where N = number of SET columns.
                      Example: "id = $3" (if set_data has 2 columns)
        where_values: Values for WHERE clause params. Example: [42]
        schema: Schema containing the table. Defaults to 'public'.

    Requires READ_ONLY=false. Table must be in WRITE_ALLOWLIST if configured.
    Uses parameterized queries — safe from SQL injection.
    """
    try:
        return {"result": await update_service.update(
            table_name, set_data, where_clause, where_values, schema
        )}
    except Exception as e:
        logger.error(f"[tool] update error: {e}")
        return {"error": str(e)}
