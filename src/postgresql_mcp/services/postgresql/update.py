"""
UpdateService — UPDATE operations with write policy enforcement.

WHERE clause is mandatory — no accidental full-table updates.
"""

import logging
from typing import Any

from postgresql_mcp.services.postgresql.base import BaseService

logger = logging.getLogger(__name__)


class UpdateService(BaseService):
    """Service layer for UPDATE operations."""

    async def update(
        self,
        table_name: str,
        set_data: dict[str, Any],
        where_clause: str,
        where_values: list[Any] | None = None,
        schema: str = "public",
    ) -> str:
        """
        Update rows matching a WHERE condition.

        Args:
            table_name: Target table.
            set_data: Column-value mapping for SET clause.
            where_clause: WHERE expression with positional params ($N+1, $N+2, ...).
                          N = number of SET columns. Cannot be empty.
            where_values: Values for WHERE clause params.
            schema: Schema name. Defaults to 'public'.

        Returns:
            Formatted string with count of updated rows.
        """
        await self.ensure_connected()
        self._validate_table_name(table_name, schema)
        self._check_write_target(schema, table_name)

        if not set_data:
            raise ValueError("SET data cannot be empty.")

        if not where_clause or not where_clause.strip():
            raise ValueError(
                "WHERE clause is required. "
                "Full-table updates without WHERE are not allowed."
            )

        self._validate_where_clause(where_clause)

        # Validate column names in SET
        set_columns = list(set_data.keys())
        for col in set_columns:
            self._validate_identifier(col, "column")

        set_values = list(set_data.values())
        where_vals = where_values or []

        count = await self.client.update(
            schema, table_name, set_columns, set_values, where_clause, where_vals
        )

        return f"Updated {count} row(s) in '{schema}.{table_name}'."
