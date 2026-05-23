"""
Phase 10.3 — Block SELECT * tests.

Tests for AST-based SELECT * / table.* / alias.* detection.
Critical: COUNT(*) must NOT be blocked.
"""

import pytest
from postgresql_mcp.guardrails.star_blocker import check_select_star


# ─── Must BLOCK ─────────────────────────────────────────────────────────────


class TestSelectStarBlocked:
    """Queries with wildcard column selection are blocked."""

    def test_select_star(self):
        result = check_select_star("SELECT * FROM users")
        assert result.is_blocked is True

    def test_select_star_with_where(self):
        result = check_select_star("SELECT * FROM users WHERE id = 1")
        assert result.is_blocked is True

    def test_select_star_with_limit(self):
        result = check_select_star("SELECT * FROM users LIMIT 10")
        assert result.is_blocked is True

    def test_table_dot_star(self):
        result = check_select_star("SELECT users.* FROM users")
        assert result.is_blocked is True

    def test_alias_dot_star(self):
        result = check_select_star("SELECT u.* FROM users u")
        assert result.is_blocked is True

    def test_star_in_join(self):
        result = check_select_star("SELECT * FROM users u JOIN orders o ON u.id = o.user_id")
        assert result.is_blocked is True

    def test_table_star_in_join(self):
        result = check_select_star(
            "SELECT u.*, o.id FROM users u JOIN orders o ON u.id = o.user_id"
        )
        assert result.is_blocked is True

    def test_star_with_schema(self):
        result = check_select_star("SELECT * FROM public.users")
        assert result.is_blocked is True

    def test_reason_message(self):
        result = check_select_star("SELECT * FROM users")
        assert "list columns explicitly" in result.reason


# ─── Must PASS ──────────────────────────────────────────────────────────────


class TestSelectStarAllowed:
    """Queries without wildcard are allowed. COUNT(*) is not a wildcard."""

    def test_count_star(self):
        result = check_select_star("SELECT COUNT(*) FROM users")
        assert result.is_blocked is False

    def test_count_star_with_alias(self):
        result = check_select_star("SELECT COUNT(*) AS total FROM users")
        assert result.is_blocked is False

    def test_multiple_aggregates_with_star(self):
        result = check_select_star("SELECT COUNT(*), SUM(amount) FROM orders")
        assert result.is_blocked is False

    def test_explicit_columns(self):
        result = check_select_star("SELECT id, name, email FROM users")
        assert result.is_blocked is False

    def test_explicit_columns_with_table(self):
        result = check_select_star("SELECT users.id, users.name FROM users")
        assert result.is_blocked is False

    def test_aggregate_with_group_by(self):
        result = check_select_star(
            "SELECT department, COUNT(*) FROM users GROUP BY department"
        )
        assert result.is_blocked is False

    def test_expression_columns(self):
        result = check_select_star("SELECT id, LOWER(name) AS lower_name FROM users")
        assert result.is_blocked is False

    def test_count_star_and_explicit_column(self):
        result = check_select_star(
            "SELECT department, COUNT(*) FROM users GROUP BY department LIMIT 10"
        )
        assert result.is_blocked is False

    def test_subquery_with_explicit_columns(self):
        """Subquery with explicit columns — not a star."""
        result = check_select_star("SELECT id FROM (SELECT id FROM users) sub")
        assert result.is_blocked is False

    def test_sum_star(self):
        """SUM doesn't take * but just in case."""
        result = check_select_star("SELECT SUM(amount) FROM orders")
        assert result.is_blocked is False
