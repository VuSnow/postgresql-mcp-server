"""
CreateMixin — parameterized INSERT operations.

All operations use $1, $2, ... placeholders — never string interpolation for values.
Table/column names are validated at the service layer.
"""

import logging
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class CreateMixin:
    """Pure asyncpg INSERT operations. No business logic."""

    pool: asyncpg.Pool  # provided by BasePostgreSQLClient

    async def insert_one(
        self,
        schema: str,
        table: str,
        columns: list[str],
        values: list[Any],
    ) -> dict[str, Any]:
        """
        Insert a single row. Returns the inserted row.

        Uses parameterized query: INSERT INTO schema.table (cols) VALUES ($1, $2, ...) RETURNING *
        """
        placeholders = ", ".join(f"${i + 1}" for i in range(len(values)))
        cols = ", ".join(columns)
        sql = f'INSERT INTO "{schema}"."{table}" ({cols}) VALUES ({placeholders}) RETURNING *'

        logger.debug(f"[client] insert_one: {sql}")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(sql, *values)

        return dict(row) if row else {}

    async def insert_many(
        self,
        schema: str,
        table: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> int:
        """
        Insert multiple rows in a single transaction. Returns count of inserted rows.

        Uses asyncpg's executemany for efficient batch insert.
        """
        placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
        cols = ", ".join(columns)
        sql = f'INSERT INTO "{schema}"."{table}" ({cols}) VALUES ({placeholders})'

        logger.debug(f"[client] insert_many: {sql} ({len(rows)} rows)")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.executemany(sql, rows)

        # executemany doesn't return a count directly, return len(rows)
        return len(rows)
