"""
UpdateMixin — parameterized UPDATE operations.

All operations use $1, $2, ... placeholders — never string interpolation for values.
Table/column names are validated at the service layer.
"""

import logging
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class UpdateMixin:
    """Pure asyncpg UPDATE operations. No business logic."""

    pool: asyncpg.Pool  # provided by BasePostgreSQLClient

    async def update(
        self,
        schema: str,
        table: str,
        set_columns: list[str],
        set_values: list[Any],
        where_clause: str,
        where_values: list[Any],
    ) -> int:
        """
        Update rows matching a WHERE clause. Returns count of affected rows.

        Parameters are indexed sequentially: SET uses $1..$N, WHERE uses $(N+1)..

        Args:
            schema: Schema name.
            table: Table name.
            set_columns: Columns to update.
            set_values: Values for SET columns (positional params $1..$N).
            where_clause: WHERE expression using positional params starting at $(N+1).
            where_values: Values for WHERE clause params.
        """
        n = len(set_values)
        set_pairs = ", ".join(
            f"{col} = ${i + 1}" for i, col in enumerate(set_columns)
        )
        sql = f'UPDATE "{schema}"."{table}" SET {set_pairs} WHERE {where_clause}'

        all_values = list(set_values) + list(where_values)

        logger.debug(f"[client] update: {sql}")

        async with self.pool.acquire() as conn:
            result = await conn.execute(sql, *all_values)

        # result is like "UPDATE 3"
        count = int(result.split()[-1]) if result else 0
        return count
