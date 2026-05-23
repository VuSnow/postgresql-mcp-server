"""
Phase 10.16 — Result Budget Enforcement.

Two layers:
1. Pre-execute: reject queries selecting too many columns (MAX_COLUMNS_RETURNED)
2. Post-execute: truncate results exceeding row/byte/cell limits

Configs: MAX_RESULT_ROWS, MAX_RESULT_BYTES, MAX_CELL_LENGTH, MAX_COLUMNS_RETURNED
"""

import json
from typing import Any

from postgresql_mcp.guardrails.models import GuardrailResult
from postgresql_mcp.guardrails.sql_parser import parse_query


# ═══════════════════════════════════════════════════════════════════════════
# Pre-execute: column count check
# ═══════════════════════════════════════════════════════════════════════════


def check_column_count(
    sql: str,
    max_columns: int = 50,
    default_schema: str = "public",
) -> GuardrailResult:
    """
    Reject queries selecting more than max_columns columns.

    Args:
        sql: Raw SQL query.
        max_columns: Maximum allowed columns in SELECT.
        default_schema: Default schema for parsing.

    Returns:
        GuardrailResult — blocked if column count exceeds limit.
    """
    parsed = parse_query(sql, default_schema)
    if parsed.parse_error:
        return GuardrailResult(is_blocked=False)

    # parsed.columns contains the extracted column references
    # But for SELECT *, we can't count — that's handled by star_blocker
    # Count explicit columns from the AST
    import sqlglot
    from sqlglot import exp

    stmts = sqlglot.parse(sql, dialect="postgres")
    if not stmts:
        return GuardrailResult(is_blocked=False)

    stmt = stmts[0]
    select = stmt.find(exp.Select)
    if select is None:
        return GuardrailResult(is_blocked=False)

    col_count = len(select.expressions)
    if col_count > max_columns:
        return GuardrailResult(
            is_blocked=True,
            reason=(
                f"Query selects {col_count} columns, exceeding the maximum of {max_columns}. "
                f"Reduce the number of columns in your SELECT clause."
            ),
        )

    return GuardrailResult(is_blocked=False)


# ═══════════════════════════════════════════════════════════════════════════
# Post-execute: result truncation
# ═══════════════════════════════════════════════════════════════════════════


class ResultBudget:
    """Post-execute result size enforcement."""

    def __init__(
        self,
        max_rows: int = 100,
        max_bytes: int = 1_048_576,
        max_cell_length: int = 4096,
    ):
        self._max_rows = max_rows
        self._max_bytes = max_bytes
        self._max_cell_length = max_cell_length

    def enforce(
        self, rows: list[dict[str, Any]], columns: list[str]
    ) -> tuple[list[dict[str, Any]], list[str], list[str]]:
        """
        Enforce result budget on query results.

        Args:
            rows: Query result rows.
            columns: Column names.

        Returns:
            Tuple of (truncated_rows, columns, warnings).
            Warnings describe what was truncated.
        """
        warnings: list[str] = []

        # 1. Truncate cells
        rows = self._truncate_cells(rows, warnings)

        # 2. Truncate rows
        if len(rows) > self._max_rows:
            original_count = len(rows)
            rows = rows[: self._max_rows]
            warnings.append(
                f"Results truncated: returned {self._max_rows} of {original_count} rows "
                f"(MAX_RESULT_ROWS={self._max_rows})."
            )

        # 3. Check byte budget
        rows, byte_warning = self._truncate_by_bytes(rows)
        if byte_warning:
            warnings.append(byte_warning)

        return rows, columns, warnings

    def _truncate_cells(
        self, rows: list[dict[str, Any]], warnings: list[str]
    ) -> list[dict[str, Any]]:
        """Truncate individual cell values exceeding max_cell_length."""
        truncated_count = 0
        result = []
        for row in rows:
            new_row = {}
            for key, value in row.items():
                if isinstance(value, str) and len(value) > self._max_cell_length:
                    new_row[key] = value[: self._max_cell_length] + "...[truncated]"
                    truncated_count += 1
                else:
                    new_row[key] = value
            result.append(new_row)

        if truncated_count > 0:
            warnings.append(
                f"{truncated_count} cell(s) truncated to {self._max_cell_length} characters "
                f"(MAX_CELL_LENGTH={self._max_cell_length})."
            )
        return result

    def _truncate_by_bytes(
        self, rows: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], str]:
        """Truncate rows to stay within byte budget."""
        total_bytes = 0
        kept_rows: list[dict[str, Any]] = []

        for row in rows:
            # Estimate row size via JSON serialization
            row_bytes = len(json.dumps(row, default=str).encode("utf-8"))
            if total_bytes + row_bytes > self._max_bytes and kept_rows:
                return kept_rows, (
                    f"Results truncated: returned {len(kept_rows)} of {len(rows)} rows "
                    f"due to size limit (MAX_RESULT_BYTES={self._max_bytes})."
                )
            total_bytes += row_bytes
            kept_rows.append(row)

        return kept_rows, ""
