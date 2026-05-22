"""
MCP Tools — Database metadata exploration.

All tools return LLM-friendly formatted strings.
"""

import logging

from postgresql_mcp.server import mcp, metadata_service

logger = logging.getLogger(__name__)


@mcp.tool()
async def list_schemas() -> str:
    """List all non-system schemas in the database.

    Returns schema names with count. Use this to discover what schemas
    are available before exploring tables.
    """
    try:
        return await metadata_service.list_schemas()
    except Exception as e:
        logger.error(f"[tool] list_schemas error: {e}")
        return f"Error: {e}"


@mcp.tool()
async def list_tables(schema: str = "public") -> str:
    """List all tables in a schema with their type and estimated row count.

    Args:
        schema: Schema name to list tables from. Defaults to 'public'.

    Returns table names, types (BASE TABLE/VIEW), and estimated row counts.
    """
    try:
        return await metadata_service.list_tables(schema)
    except Exception as e:
        logger.error(f"[tool] list_tables error: {e}")
        return f"Error: {e}"


@mcp.tool()
async def get_table_schema(table_name: str, schema: str = "public") -> str:
    """Get the column definitions for a table.

    Args:
        table_name: Name of the table to inspect.
        schema: Schema containing the table. Defaults to 'public'.

    Returns column names, data types, nullability, and defaults.
    Use this to understand table structure before writing queries.
    """
    try:
        return await metadata_service.get_table_schema(table_name, schema)
    except Exception as e:
        logger.error(f"[tool] get_table_schema error: {e}")
        return f"Error: {e}"


@mcp.tool()
async def get_indexes(table_name: str, schema: str = "public") -> str:
    """List all indexes on a table.

    Args:
        table_name: Name of the table.
        schema: Schema containing the table. Defaults to 'public'.

    Returns index names, types (btree/hash/gin/gist), columns, and flags (PRIMARY, UNIQUE).
    Useful for understanding query performance characteristics.
    """
    try:
        return await metadata_service.get_indexes(table_name, schema)
    except Exception as e:
        logger.error(f"[tool] get_indexes error: {e}")
        return f"Error: {e}"


@mcp.tool()
async def get_constraints(table_name: str, schema: str = "public") -> str:
    """List all constraints on a table (PK, FK, UNIQUE, CHECK).

    Args:
        table_name: Name of the table.
        schema: Schema containing the table. Defaults to 'public'.

    Returns constraint names, types, columns, and foreign key references.
    Useful for understanding table relationships.
    """
    try:
        return await metadata_service.get_constraints(table_name, schema)
    except Exception as e:
        logger.error(f"[tool] get_constraints error: {e}")
        return f"Error: {e}"


@mcp.tool()
async def get_column_values(
    table_name: str,
    column: str,
    schema: str = "public",
    limit: int = 50,
) -> str:
    """Get distinct non-null values for a column.

    Args:
        table_name: Name of the table.
        column: Column name to sample values from.
        schema: Schema containing the table. Defaults to 'public'.
        limit: Maximum number of distinct values to return. Defaults to 50.

    Useful for understanding column cardinality, data patterns, and valid
    filter values before writing queries.
    """
    try:
        return await metadata_service.get_column_values(table_name, column, schema, limit)
    except Exception as e:
        logger.error(f"[tool] get_column_values error: {e}")
        return f"Error: {e}"
