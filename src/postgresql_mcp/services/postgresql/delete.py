"""
DeleteService — DELETE and TRUNCATE with destructive policy enforcement.

- DELETE requires WHERE clause (no accidental full-table deletes)
- TRUNCATE requires ALLOW_DESTRUCTIVE=true
- Both require READ_ONLY=false and pass WRITE_ALLOWLIST check
"""

import logging
from typing import Any

from postgresql_mcp.services.postgresql.base import BaseService

logger = logging.getLogger(__name__)


class DeleteService(BaseService):
    """Service layer for DELETE/TRUNCATE operations."""

    async def delete(
        self,
        table_name: str,
        where_clause: str,
        where_values: list[Any] | None = None,
        schema: str = "public",
    ) -> str:
        """
        Delete rows matching a WHERE condition.

        Args:
            table_name: Target table.
            where_clause: WHERE expression with positional params ($1, $2, ...).
                          Cannot be empty.
            where_values: Values for WHERE clause params.
            schema: Schema name. Defaults to 'public'.

        Returns:
            Formatted string with count of deleted rows.
        """
        await self.ensure_connected()
        self._validate_table_name(table_name, schema)
        self._check_destructive_allowed()
        self._check_write_target(schema, table_name)

        if not where_clause or not where_clause.strip():
            raise ValueError(
                "WHERE clause is required. "
                "Full-table deletes without WHERE are not allowed. "
                "Use truncate_table for that purpose."
            )

        self._validate_where_clause(where_clause)
        where_vals = where_values or []

        count = await self.client.delete(schema, table_name, where_clause, where_vals)
        return f"Deleted {count} row(s) from '{schema}.{table_name}'."

    async def truncate_table(
        self,
        table_name: str,
        schema: str = "public",
    ) -> str:
        """
        TRUNCATE a table — removes all rows and resets identity sequences.

        Requires ALLOW_DESTRUCTIVE=true.

        Args:
            table_name: Target table.
            schema: Schema name. Defaults to 'public'.

        Returns:
            Confirmation message.
        """
        await self.ensure_connected()
        self._validate_table_name(table_name, schema)
        self._check_destructive_allowed()
        self._check_write_target(schema, table_name)

        await self.client.truncate(schema, table_name)
        return f"Truncated table '{schema}.{table_name}'. All rows removed."
