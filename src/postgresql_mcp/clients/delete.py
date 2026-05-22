"""
DeleteMixin — parameterized DELETE and TRUNCATE operations.

All DELETE operations use $1, $2, ... placeholders.
Table/column names are validated at the service layer.
"""

import logging
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class DeleteMixin:
    """Pure asyncpg DELETE/TRUNCATE operations. No business logic."""

    pool: asyncpg.Pool  # provided by BasePostgreSQLClient

    async def delete(
        self,
        schema: str,
        table: str,
        where_clause: str,
        where_values: list[Any],
    ) -> int:
        """
        Delete rows matching a WHERE clause. Returns count of deleted rows.

        Args:
            schema: Schema name.
            table: Table name.
            where_clause: WHERE expression with positional params ($1, $2, ...).
            where_values: Values for WHERE clause params.
        """
        sql = f'DELETE FROM "{schema}"."{table}" WHERE {where_clause}'

        logger.debug(f"[client] delete: {sql}")

        async with self.pool.acquire() as conn:
            result = await conn.execute(sql, *where_values)

        # result is like "DELETE 5"
        count = int(result.split()[-1]) if result else 0
        return count

    async def truncate(
        self,
        schema: str,
        table: str,
    ) -> None:
        """
        TRUNCATE a table (removes all rows, resets sequences).

        This is a DDL-like operation — cannot be rolled back easily.
        """
        sql = f'TRUNCATE TABLE "{schema}"."{table}" RESTART IDENTITY'

        logger.debug(f"[client] truncate: {sql}")

        async with self.pool.acquire() as conn:
            await conn.execute(sql)
