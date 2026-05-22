"""
MCP Tools — DELETE and TRUNCATE operations.

Tools: delete, truncate_table
"""

import logging
from typing import Any

from postgresql_mcp.server import mcp, delete_service

logger = logging.getLogger(__name__)


@mcp.tool()
async def delete(
    table_name: str,
    where_clause: str,
    where_values: list[Any] | None = None,
    schema: str = "public",
) -> dict:
    """Delete rows from a table matching a WHERE condition.

    WHERE clause is mandatory — full-table deletes are not allowed.
    Use truncate_table instead if you need to remove all rows.

    Args:
        table_name: Name of the table to delete from.
        where_clause: WHERE expression with positional params ($1, $2, ...).
                      Example: "id = $1" or "status = $1 AND created_at < $2"
        where_values: Values for WHERE clause params. Example: [42]
        schema: Schema containing the table. Defaults to 'public'.

    Requires READ_ONLY=false and ALLOW_DESTRUCTIVE=true.
    Table must be in WRITE_ALLOWLIST if configured.
    """
    try:
        return {"result": await delete_service.delete(
            table_name, where_clause, where_values, schema
        )}
    except Exception as e:
        logger.error(f"[tool] delete error: {e}")
        return {"error": str(e)}


@mcp.tool()
async def truncate_table(
    table_name: str,
    schema: str = "public",
) -> dict:
    """Truncate a table — removes ALL rows and resets identity sequences.

    This is a destructive operation and cannot be easily undone.

    Args:
        table_name: Name of the table to truncate.
        schema: Schema containing the table. Defaults to 'public'.

    Requires READ_ONLY=false and ALLOW_DESTRUCTIVE=true.
    Table must be in WRITE_ALLOWLIST if configured.
    """
    try:
        return {"result": await delete_service.truncate_table(table_name, schema)}
    except Exception as e:
        logger.error(f"[tool] truncate_table error: {e}")
        return {"error": str(e)}
