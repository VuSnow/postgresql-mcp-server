"""
MCP Tools — INSERT operations.

Tools: insert_one, insert_many
"""

import logging
from typing import Any

from postgresql_mcp.server import mcp, create_service

logger = logging.getLogger(__name__)


@mcp.tool()
async def insert_one(
    table_name: str,
    data: dict[str, Any],
    schema: str = "public",
) -> dict:
    """Insert a single row into a table.

    Args:
        table_name: Name of the table to insert into.
        data: Column-value mapping. Example: {"name": "Alice", "age": 30}
        schema: Schema containing the table. Defaults to 'public'.

    Requires READ_ONLY=false. Table must be in WRITE_ALLOWLIST if configured.
    Uses parameterized queries — safe from SQL injection.
    """
    try:
        return {"result": await create_service.insert_one(table_name, data, schema)}
    except Exception as e:
        logger.error(f"[tool] insert_one error: {e}")
        return {"error": str(e)}


@mcp.tool()
async def insert_many(
    table_name: str,
    columns: list[str],
    rows: list[list[Any]],
    schema: str = "public",
) -> dict:
    """Insert multiple rows into a table in a single transaction.

    Args:
        table_name: Name of the table to insert into.
        columns: List of column names. Example: ["name", "age"]
        rows: List of value lists. Example: [["Alice", 30], ["Bob", 25]]
        schema: Schema containing the table. Defaults to 'public'.

    Requires READ_ONLY=false. Table must be in WRITE_ALLOWLIST if configured.
    Uses parameterized queries — safe from SQL injection.
    """
    try:
        return {"result": await create_service.insert_many(table_name, columns, rows, schema)}
    except Exception as e:
        logger.error(f"[tool] insert_many error: {e}")
        return {"error": str(e)}
