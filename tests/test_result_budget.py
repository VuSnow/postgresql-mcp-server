"""
Phase 10.16 — Result Budget tests.

Tests pre-execute column count check and post-execute result truncation.
"""

import pytest

from postgresql_mcp.guardrails.result_budget import check_column_count, ResultBudget


# ═══════════════════════════════════════════════════════════════════════════
# Pre-execute: check_column_count
# ═══════════════════════════════════════════════════════════════════════════


class TestCheckColumnCount:
    def test_within_limit(self):
        sql = "SELECT id, name, email FROM users WHERE id = 1"
        r = check_column_count(sql, max_columns=50)
        assert r.is_blocked is False

    def test_at_limit(self):
        cols = ", ".join(f"col{i}" for i in range(50))
        sql = f"SELECT {cols} FROM wide_table WHERE id = 1"
        r = check_column_count(sql, max_columns=50)
        assert r.is_blocked is False

    def test_over_limit(self):
        cols = ", ".join(f"col{i}" for i in range(51))
        sql = f"SELECT {cols} FROM wide_table WHERE id = 1"
        r = check_column_count(sql, max_columns=50)
        assert r.is_blocked is True
        assert "51" in r.reason
        assert "50" in r.reason

    def test_small_limit(self):
        sql = "SELECT a, b, c, d, e FROM t WHERE id = 1"
        r = check_column_count(sql, max_columns=3)
        assert r.is_blocked is True

    def test_single_column(self):
        sql = "SELECT id FROM users WHERE id = 1"
        r = check_column_count(sql, max_columns=50)
        assert r.is_blocked is False

    def test_parse_error_passes(self):
        r = check_column_count("NOT SQL AT ALL", max_columns=5)
        assert r.is_blocked is False

    def test_non_select_passes(self):
        sql = "INSERT INTO t (a, b, c) VALUES (1, 2, 3)"
        r = check_column_count(sql, max_columns=2)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Post-execute: ResultBudget — row truncation
# ═══════════════════════════════════════════════════════════════════════════


class TestRowTruncation:
    def test_within_limit(self):
        budget = ResultBudget(max_rows=10)
        rows = [{"id": i} for i in range(5)]
        result_rows, cols, warnings = budget.enforce(rows, ["id"])
        assert len(result_rows) == 5
        assert warnings == []

    def test_at_limit(self):
        budget = ResultBudget(max_rows=10)
        rows = [{"id": i} for i in range(10)]
        result_rows, cols, warnings = budget.enforce(rows, ["id"])
        assert len(result_rows) == 10
        assert warnings == []

    def test_over_limit(self):
        budget = ResultBudget(max_rows=5)
        rows = [{"id": i} for i in range(20)]
        result_rows, cols, warnings = budget.enforce(rows, ["id"])
        assert len(result_rows) == 5
        assert any("truncated" in w.lower() for w in warnings)
        assert any("5 of 20" in w for w in warnings)

    def test_empty_rows(self):
        budget = ResultBudget(max_rows=10)
        result_rows, cols, warnings = budget.enforce([], ["id"])
        assert result_rows == []
        assert warnings == []


# ═══════════════════════════════════════════════════════════════════════════
# Post-execute: ResultBudget — cell truncation
# ═══════════════════════════════════════════════════════════════════════════


class TestCellTruncation:
    def test_short_cells_unchanged(self):
        budget = ResultBudget(max_cell_length=100)
        rows = [{"name": "Alice", "bio": "Short text"}]
        result_rows, _, warnings = budget.enforce(rows, ["name", "bio"])
        assert result_rows[0]["name"] == "Alice"
        assert result_rows[0]["bio"] == "Short text"
        assert warnings == []

    def test_long_cell_truncated(self):
        budget = ResultBudget(max_cell_length=10)
        rows = [{"data": "A" * 100}]
        result_rows, _, warnings = budget.enforce(rows, ["data"])
        assert result_rows[0]["data"] == "A" * 10 + "...[truncated]"
        assert any("truncated" in w.lower() for w in warnings)

    def test_non_string_not_truncated(self):
        budget = ResultBudget(max_cell_length=5)
        rows = [{"id": 123456789, "amount": 99.99}]
        result_rows, _, warnings = budget.enforce(rows, ["id", "amount"])
        assert result_rows[0]["id"] == 123456789
        assert result_rows[0]["amount"] == 99.99
        assert warnings == []

    def test_multiple_cells_truncated(self):
        budget = ResultBudget(max_cell_length=5)
        rows = [
            {"a": "long string here", "b": "another long one"},
            {"a": "short", "b": "x" * 20},
        ]
        result_rows, _, warnings = budget.enforce(rows, ["a", "b"])
        assert "...[truncated]" in result_rows[0]["a"]
        assert "...[truncated]" in result_rows[0]["b"]
        # "short" is exactly 5 chars — not truncated
        assert result_rows[1]["a"] == "short"
        assert "...[truncated]" in result_rows[1]["b"]
        assert any("3 cell(s)" in w for w in warnings)


# ═══════════════════════════════════════════════════════════════════════════
# Post-execute: ResultBudget — byte budget
# ═══════════════════════════════════════════════════════════════════════════


class TestByteBudget:
    def test_within_byte_limit(self):
        budget = ResultBudget(max_bytes=10000)
        rows = [{"id": i, "name": f"user_{i}"} for i in range(10)]
        result_rows, _, warnings = budget.enforce(rows, ["id", "name"])
        assert len(result_rows) == 10
        assert not any("size limit" in w for w in warnings)

    def test_exceeds_byte_limit(self):
        budget = ResultBudget(max_bytes=100, max_rows=1000)
        # Each row is roughly ~30-40 bytes in JSON
        rows = [{"id": i, "data": "x" * 50} for i in range(100)]
        result_rows, _, warnings = budget.enforce(rows, ["id", "data"])
        assert len(result_rows) < 100
        assert any("size limit" in w for w in warnings)

    def test_single_huge_row_still_returned(self):
        """First row is always returned even if it exceeds budget."""
        budget = ResultBudget(max_bytes=10)
        rows = [{"data": "x" * 1000}]
        result_rows, _, warnings = budget.enforce(rows, ["data"])
        # First row is always included
        assert len(result_rows) == 1


# ═══════════════════════════════════════════════════════════════════════════
# Combined enforcement
# ═══════════════════════════════════════════════════════════════════════════


class TestCombined:
    def test_cell_and_row_truncation(self):
        budget = ResultBudget(max_rows=3, max_cell_length=10)
        rows = [{"text": "A" * 100} for _ in range(10)]
        result_rows, _, warnings = budget.enforce(rows, ["text"])
        assert len(result_rows) == 3
        assert all("...[truncated]" in r["text"] for r in result_rows)
        assert len(warnings) == 2  # cell + row warnings

    def test_all_within_budget(self):
        budget = ResultBudget(max_rows=100, max_bytes=1_000_000, max_cell_length=4096)
        rows = [{"id": i, "name": f"user_{i}"} for i in range(10)]
        result_rows, cols, warnings = budget.enforce(rows, ["id", "name"])
        assert len(result_rows) == 10
        assert cols == ["id", "name"]
        assert warnings == []
