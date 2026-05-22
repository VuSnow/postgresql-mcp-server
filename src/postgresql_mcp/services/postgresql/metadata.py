"""
MetadataService — formats client metadata results for LLM consumption.

Delegates to PostgreSQLClient for raw data, then formats into
readable strings optimized for agent output.
"""

import logging
from typing import Any

from postgresql_mcp.services.postgresql.base import BaseService

logger = logging.getLogger(__name__)


class MetadataService(BaseService):
    """Service layer for database metadata operations."""

    async def list_schemas(self) -> str:
        """List all non-system schemas. Returns formatted string."""
        await self.ensure_connected()
        rows = await self.client.list_schemas()

        if not rows:
            return "No user schemas found."

        schemas = [r["schema_name"] for r in rows]
        lines = ["Schemas:", ""]
        for s in schemas:
            lines.append(f"  • {s}")
        lines.append(f"\nTotal: {len(schemas)} schema(s)")
        return "\n".join(lines)

    async def list_tables(self, schema: str = "public") -> str:
        """List all tables in a schema. Returns formatted string."""
        await self.ensure_connected()
        self._validate_identifier(schema, "schema")

        rows = await self.client.list_tables(schema)

        if not rows:
            return f"No tables found in schema '{schema}'."

        lines = [f"Tables in '{schema}':", ""]
        lines.append(f"{'Table':<40} {'Type':<15} {'Est. Rows':<12}")
        lines.append("-" * 67)
        for r in rows:
            lines.append(
                f"{r['table_name']:<40} {r['table_type']:<15} {r['estimated_row_count']:<12}"
            )
        lines.append(f"\nTotal: {len(rows)} table(s)")
        return "\n".join(lines)

    async def get_table_schema(self, table_name: str, schema: str = "public") -> str:
        """Get column definitions for a table. Returns formatted string."""
        await self.ensure_connected()
        self._validate_table_name(table_name, schema)

        rows = await self.client.get_table_schema(table_name, schema)

        if not rows:
            return f"Table '{schema}.{table_name}' not found or has no columns."

        lines = [f"Columns for '{schema}.{table_name}':", ""]
        lines.append(f"{'#':<4} {'Column':<30} {'Type':<20} {'Nullable':<10} {'Default'}")
        lines.append("-" * 90)
        for r in rows:
            col_type = r["udt_name"]
            if r["character_maximum_length"]:
                col_type += f"({r['character_maximum_length']})"
            elif r["numeric_precision"]:
                col_type += f"({r['numeric_precision']}"
                if r["numeric_scale"]:
                    col_type += f",{r['numeric_scale']}"
                col_type += ")"

            nullable = "YES" if r["is_nullable"] == "YES" else "NO"
            default = r["column_default"] or ""
            lines.append(
                f"{r['ordinal_position']:<4} {r['column_name']:<30} {col_type:<20} {nullable:<10} {default}"
            )

        lines.append(f"\nTotal: {len(rows)} column(s)")
        return "\n".join(lines)

    async def get_indexes(self, table_name: str, schema: str = "public") -> str:
        """List indexes for a table. Returns formatted string."""
        await self.ensure_connected()
        self._validate_table_name(table_name, schema)

        rows = await self.client.get_indexes(table_name, schema)

        if not rows:
            return f"No indexes found for '{schema}.{table_name}'."

        lines = [f"Indexes for '{schema}.{table_name}':", ""]
        for r in rows:
            flags = []
            if r.get("is_primary"):
                flags.append("PRIMARY")
            if r.get("is_unique"):
                flags.append("UNIQUE")
            flags_str = f" [{', '.join(flags)}]" if flags else ""

            columns = ", ".join(r.get("columns") or [])
            lines.append(f"  • {r['index_name']}{flags_str}")
            lines.append(f"    Type: {r['index_type']}, Columns: ({columns})")
            lines.append("")

        lines.append(f"Total: {len(rows)} index(es)")
        return "\n".join(lines)

    async def get_constraints(self, table_name: str, schema: str = "public") -> str:
        """List constraints for a table. Returns formatted string."""
        await self.ensure_connected()
        self._validate_table_name(table_name, schema)

        rows = await self.client.get_constraints(table_name, schema)

        if not rows:
            return f"No constraints found for '{schema}.{table_name}'."

        lines = [f"Constraints for '{schema}.{table_name}':", ""]
        for r in rows:
            columns = ", ".join(r.get("columns") or [])
            lines.append(f"  • {r['constraint_name']} ({r['constraint_type_name']})")
            lines.append(f"    Columns: ({columns})")
            if r.get("foreign_table"):
                fk_cols = ", ".join(r.get("foreign_columns") or [])
                lines.append(
                    f"    References: {r['foreign_schema']}.{r['foreign_table']} ({fk_cols})"
                )
            lines.append("")

        lines.append(f"Total: {len(rows)} constraint(s)")
        return "\n".join(lines)

    async def get_column_values(
        self,
        table_name: str,
        column: str,
        schema: str = "public",
        limit: int = 50,
    ) -> str:
        """Get distinct values for a column. Returns formatted string."""
        await self.ensure_connected()
        self._validate_table_name(table_name, schema)
        self._validate_identifier(column, "column")

        values = await self.client.get_column_values(table_name, column, schema, limit)

        if not values:
            return f"No non-null values found for '{schema}.{table_name}.{column}'."

        lines = [f"Distinct values for '{schema}.{table_name}.{column}' (limit {limit}):", ""]
        for v in values:
            lines.append(f"  • {v}")

        lines.append(f"\nTotal: {len(values)} value(s)")
        if len(values) == limit:
            lines.append("(results may be truncated)")
        return "\n".join(lines)
