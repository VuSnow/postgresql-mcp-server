"""
Phase 10.15 — Metadata Tools Policy Filter.

When metadata filtering is active (text2sql/sensitive profile or strict mode):
- list_tables: only tables present in column policy
- get_table_schema: only allowed_columns for the table
- get_indexes/get_constraints: only for tables in policy
- get_column_values: only for sampleable_columns (NOT allowed_columns)

In general profile (permissive mode): no filtering applied.
"""

from typing import Optional

from postgresql_mcp.guardrails.models import ColumnPolicyConfig, TablePolicy, GuardrailResult


class MetadataFilter:
    """Filters metadata results based on column policy."""

    def __init__(self, policy: Optional[ColumnPolicyConfig], filtering_enabled: bool):
        """
        Args:
            policy: Column policy config (may be None if not configured).
            filtering_enabled: Whether to apply filtering (from effective_metadata_filtering).
        """
        self._policy = policy
        self._enabled = filtering_enabled

    @property
    def is_active(self) -> bool:
        """Whether metadata filtering is active."""
        return self._enabled and self._policy is not None

    def _get_table_policy(self, table_name: str, schema: str = "public") -> Optional[TablePolicy]:
        """Look up policy for a table."""
        if not self._policy:
            return None
        # Try schema.table then just table
        key = f"{schema}.{table_name}"
        if key in self._policy.policies:
            return self._policy.policies[key]
        if table_name in self._policy.policies:
            return self._policy.policies[table_name]
        return None

    def filter_tables(self, tables: list[dict], schema: str = "public") -> list[dict]:
        """
        Filter list_tables results to only tables present in policy.

        Args:
            tables: List of table dicts with 'table_name' key.
            schema: Schema name.

        Returns:
            Filtered list (or original if filtering not active).
        """
        if not self.is_active:
            return tables

        result = []
        for t in tables:
            name = t.get("table_name", "")
            if self._get_table_policy(name, schema) is not None:
                result.append(t)
        return result

    def check_table_access(self, table_name: str, schema: str = "public") -> GuardrailResult:
        """
        Check if a table is accessible for metadata operations.

        Returns:
            GuardrailResult — blocked if table not in policy (strict mode).
        """
        if not self.is_active:
            return GuardrailResult(is_blocked=False)

        if self._get_table_policy(table_name, schema) is None:
            return GuardrailResult(
                is_blocked=True,
                reason=(
                    f"Table '{schema}.{table_name}' is not in the column policy. "
                    f"Metadata access is restricted to configured tables."
                ),
            )
        return GuardrailResult(is_blocked=False)

    def filter_columns(self, columns: list[dict], table_name: str, schema: str = "public") -> list[dict]:
        """
        Filter get_table_schema results to only allowed_columns.

        Args:
            columns: List of column dicts with 'column_name' key.
            table_name: Table name.
            schema: Schema name.

        Returns:
            Filtered list (or original if filtering not active).
        """
        if not self.is_active:
            return columns

        policy = self._get_table_policy(table_name, schema)
        if policy is None:
            return []  # Table not in policy → no columns visible

        if not policy.allowed_columns:
            return columns  # No column restriction

        allowed = set(policy.allowed_columns)
        return [c for c in columns if c.get("column_name", "") in allowed]

    def check_column_values_access(
        self, table_name: str, column: str, schema: str = "public"
    ) -> GuardrailResult:
        """
        Check if get_column_values is allowed for this table.column.

        Only sampleable_columns can be enumerated (NOT allowed_columns).

        Returns:
            GuardrailResult — blocked if column not in sampleable_columns.
        """
        if not self.is_active:
            return GuardrailResult(is_blocked=False)

        policy = self._get_table_policy(table_name, schema)
        if policy is None:
            return GuardrailResult(
                is_blocked=True,
                reason=(
                    f"Table '{schema}.{table_name}' is not in the column policy. "
                    f"Column value sampling is not allowed."
                ),
            )

        if not policy.sampleable_columns:
            return GuardrailResult(
                is_blocked=True,
                reason=(
                    f"Table '{schema}.{table_name}' has no sampleable_columns configured. "
                    f"Column value sampling is not allowed for this table."
                ),
            )

        if column not in policy.sampleable_columns:
            return GuardrailResult(
                is_blocked=True,
                reason=(
                    f"Column '{column}' is not in sampleable_columns for "
                    f"'{schema}.{table_name}'. "
                    f"Only these columns can be sampled: {policy.sampleable_columns}"
                ),
            )

        return GuardrailResult(is_blocked=False)
