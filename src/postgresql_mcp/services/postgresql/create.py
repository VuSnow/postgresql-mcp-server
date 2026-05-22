"""
CreateService — insert operations with write policy enforcement.

Validates identifiers, checks write permissions, delegates to client.
"""

import logging
from typing import Any

from postgresql_mcp.services.postgresql.base import BaseService

logger = logging.getLogger(__name__)


class CreateService(BaseService):
    """Service layer for INSERT operations."""

    async def insert_one(
        self,
        table_name: str,
        data: dict[str, Any],
        schema: str = "public",
    ) -> str:
        """
        Insert a single row into a table.

        Args:
            table_name: Target table.
            data: Column-value mapping for the new row.
            schema: Schema name. Defaults to 'public'.

        Returns:
            Formatted string showing the inserted row.
        """
        await self.ensure_connected()
        self._validate_table_name(table_name, schema)
        self._check_write_target(schema, table_name)

        if not data:
            raise ValueError("Data cannot be empty.")

        # Validate all column names
        columns = list(data.keys())
        for col in columns:
            self._validate_identifier(col, "column")

        values = list(data.values())

        row = await self.client.insert_one(schema, table_name, columns, values)

        # Format output
        lines = [f"Inserted 1 row into '{schema}.{table_name}':", ""]
        for k, v in row.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    async def insert_many(
        self,
        table_name: str,
        columns: list[str],
        rows: list[list[Any]],
        schema: str = "public",
    ) -> str:
        """
        Insert multiple rows into a table.

        Args:
            table_name: Target table.
            columns: Column names (same order as values in each row).
            rows: List of value lists — each inner list is one row.
            schema: Schema name. Defaults to 'public'.

        Returns:
            Formatted string with count of inserted rows.
        """
        await self.ensure_connected()
        self._validate_table_name(table_name, schema)
        self._check_write_target(schema, table_name)

        if not columns:
            raise ValueError("Columns list cannot be empty.")
        if not rows:
            raise ValueError("Rows list cannot be empty.")

        # Validate column names
        for col in columns:
            self._validate_identifier(col, "column")

        # Validate row lengths
        expected = len(columns)
        for i, row in enumerate(rows):
            if len(row) != expected:
                raise ValueError(
                    f"Row {i} has {len(row)} values, expected {expected} (columns: {columns})."
                )

        count = await self.client.insert_many(schema, table_name, columns, rows)
        return f"Inserted {count} row(s) into '{schema}.{table_name}'."
