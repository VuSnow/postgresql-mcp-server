import logging
import asyncpg
from typing import Any
from utils import validate_identifier

logger = logging.getLogger(__name__)

class MetadataMixin:
    """Pure asyncpg metadata queries. No business logic."""

    pool: asyncpg.Pool

    async def list_schemas(self) -> list[dict[str, Any]]:
        """List all non-system schemas."""
        query = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            AND schema_name NOT LIKE 'pg_temp_%'
            AND schema_name NOT LIKE 'pg_toast_temp_%'
            ORDER BY schema_name
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)

        return [dict(r) for r in rows]

    async def list_tables(self, schema: str = "public") -> list[dict[str, Any]]:
        """List all tables in a schema with estimated row counts."""
        query = """
            SELECT
                t.table_name,
                t.table_type,
                COALESCE(s.n_live_tup, 0) AS estimated_row_count
            FROM information_schema.tables t
            LEFT JOIN pg_stat_user_tables s ON s.schemaname = t.table_schema
            AND s.relname = t.table_name
            WHERE t.table_schema = $1
            ORDER BY t.table_name
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, schema)

        return [dict(r) for r in rows]

    async def get_table_schema(
        self,
        table_name: str,
        schema: str = "public",
    ) -> list[dict[str, Any]]:
        """Get column definitions for a table."""
        query = """
            SELECT 
                c.column_name,
                c.data_type,
                c.udt_name,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                c.datetime_precision,
                c.ordinal_position
            FROM information_schema.columns c
            WHERE c.table_schema = $1
            AND c.table_name = $2
            ORDER BY c.ordinal_position
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, schema, table_name)

        return [dict(r) for r in rows]

    async def get_indexes(
        self,
        table_name: str,
        schema: str = "public",
    ) -> list[dict[str, Any]]:
        """List indexes for a table."""
        query = """
            SELECT 
                i.relname AS index_name,
                ix.indisunique AS is_unique,
                ix.indisprimary AS is_primary,
                am.amname AS index_type,
                array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) FILTER (WHERE a.attname IS NOT NULL) AS columns,
                pg_get_indexdef(i.oid) AS index_definition
            FROM pg_index ix
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_am am ON am.oid = i.relam
            LEFT JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            WHERE n.nspname = $1
            AND t.relname = $2
            GROUP BY i.oid, i.relname, ix.indisunique, ix.indisprimary, am.amname
            ORDER BY i.relname
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, schema, table_name)

        return [dict(r) for r in rows]

    async def get_constraints(
        self,
        table_name: str,
        schema: str = "public",
    ) -> list[dict[str, Any]]:
        """List constraints: primary key, foreign key, unique, check, exclusion."""
        query = """
            SELECT
                c.conname AS constraint_name,
                c.contype AS constraint_type,
                CASE c.contype
                    WHEN 'p' THEN 'PRIMARY KEY'
                    WHEN 'f' THEN 'FOREIGN KEY'
                    WHEN 'u' THEN 'UNIQUE'
                    WHEN 'c' THEN 'CHECK'
                    WHEN 'x' THEN 'EXCLUDE'
                    ELSE c.contype::text
                END AS constraint_type_name,
                array_agg(a.attname ORDER BY array_position(c.conkey, a.attnum)) FILTER (WHERE a.attname IS NOT NULL) AS columns,
                pg_get_constraintdef(c.oid) AS constraint_definition,
                fn.nspname AS foreign_schema,
                ft.relname AS foreign_table,
                (
                    SELECT array_agg(fa.attname ORDER BY array_position(c.confkey, fa.attnum))
                    FROM pg_attribute fa
                    WHERE fa.attrelid = c.confrelid
                    AND fa.attnum = ANY(c.confkey)
                ) AS foreign_columns
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            LEFT JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
            LEFT JOIN pg_class ft ON ft.oid = c.confrelid
            LEFT JOIN pg_namespace fn ON fn.oid = ft.relnamespace
            WHERE n.nspname = $1
            AND t.relname = $2
            GROUP BY  c.oid, c.conname, c.contype, fn.nspname, ft.relname, c.confrelid, c.confkey
            ORDER BY c.contype, c.conname
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, schema, table_name)

        return [dict(r) for r in rows]

    async def get_column_values(
        self,
        table_name: str,
        column: str,
        schema: str = "public",
        limit: int = 50,
    ) -> list[Any]:
        """Get distinct non-null values for a column."""
        schema = validate_identifier(schema)
        table_name = validate_identifier(table_name)
        column = validate_identifier(column)

        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        query = f"""
            SELECT DISTINCT "{column}" AS value
            FROM "{schema}"."{table_name}"
            WHERE "{column}" IS NOT NULL
            ORDER BY "{column}"
            LIMIT $1
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [r["value"] for r in rows]
