import logging
from typing import Any, List, Dict, Tuple

import asyncpg

logger = logging.getLogger(__name__)


class ReadMixin:
    """Pure asyncpg query execution. No business/security logic."""

    pool: asyncpg.Pool  # provided by BasePostgreSQLClient

    async def execute_query(self, query: str, timeout_seconds: int | None = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute a SQL query. Returns (rows, column_names)."""
        async with self.pool.acquire() as conn:
            stmt = await conn.prepare(query, timeout=timeout_seconds)
            columns = [attr.name for attr in stmt.get_attributes()]
            rows = await stmt.fetch(timeout=timeout_seconds)

        return [dict(row) for row in rows], columns

    async def execute_query_with_context(
        self,
        set_local_sql: str,
        query: str,
        timeout_seconds: int | None = None,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute SET LOCAL + query in a single transaction for RLS context."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(set_local_sql)
                stmt = await conn.prepare(query, timeout=timeout_seconds)
                columns = [attr.name for attr in stmt.get_attributes()]
                rows = await stmt.fetch(timeout=timeout_seconds)

        return [dict(row) for row in rows], columns

    async def explain_query(self, query: str, analyze: bool = False, format: str = "text", timeout_seconds: int | None = None) -> str:
        """Run EXPLAIN on a query. Returns the plan as a string."""
        fmt = format.upper()
        options: list[str] = []

        if analyze:
            options.append("ANALYZE true")

        if fmt != "TEXT":
            options.append(f"FORMAT {fmt}")

        explain_sql = (
            f"EXPLAIN ({', '.join(options)}) {query}"
            if options
            else f"EXPLAIN {query}"
        )

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(explain_sql, timeout=timeout_seconds)

        return "\n".join(str(row[0]) for row in rows)
