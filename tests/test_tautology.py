"""
Phase 10.5 — Tautology Detection tests.

Tests that trivial WHERE clauses (1=1, true, id=id) are detected
and blocked when required_filter_columns is configured.
"""

import pytest
import sqlglot

from postgresql_mcp.guardrails.sql_parser import has_tautological_where
from postgresql_mcp.guardrails.column_policy import (
    check_column_policy,
    load_column_policy,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def parse_stmt(sql: str):
    stmts = sqlglot.parse(sql, dialect="postgres")
    return [s for s in stmts if s is not None][0]


POLICY_JSON = """{
    "public.users": {
        "allowed_columns": ["id", "name", "email"],
        "required_filter_columns": ["id", "name"],
        "allow_aggregates_without_filter": true,
        "group_by_columns": ["name"],
        "max_rows": 50
    }
}"""


def make_policy():
    return load_column_policy(policy_json=POLICY_JSON, mode="strict")


# ─── has_tautological_where (unit) ──────────────────────────────────────────


class TestHasTautologicalWhere:
    """Direct tests for the tautology detector."""

    @pytest.mark.parametrize("sql", [
        "SELECT 1 WHERE 1=1",
        "SELECT 1 WHERE '1'='1'",
        "SELECT 1 WHERE 'a'='a'",
        "SELECT 1 WHERE true",
        "SELECT 1 WHERE TRUE",
        "SELECT 1 WHERE NOT false",
        "SELECT 1 WHERE NOT FALSE",
    ])
    def test_detects_tautology(self, sql):
        stmt = parse_stmt(sql)
        assert has_tautological_where(stmt) is True

    def test_detects_self_reference(self):
        stmt = parse_stmt("SELECT id FROM users WHERE id = id")
        assert has_tautological_where(stmt) is True

    def test_detects_qualified_self_reference(self):
        stmt = parse_stmt("SELECT id FROM users WHERE users.id = users.id")
        assert has_tautological_where(stmt) is True

    def test_detects_and_tautology(self):
        """WHERE 1=1 AND true → both parts tautological."""
        stmt = parse_stmt("SELECT 1 WHERE 1=1 AND true")
        assert has_tautological_where(stmt) is True

    def test_detects_or_with_tautology(self):
        """WHERE false OR 1=1 → one part tautological (OR makes whole thing true)."""
        stmt = parse_stmt("SELECT 1 WHERE 0=1 OR 1=1")
        assert has_tautological_where(stmt) is True

    @pytest.mark.parametrize("sql", [
        "SELECT 1 WHERE id = 42",
        "SELECT 1 WHERE name = 'Alice'",
        "SELECT 1 WHERE id > 10",
        "SELECT 1 WHERE id IN (1, 2, 3)",
        "SELECT 1 WHERE id = 1 AND name = 'Bob'",
        "SELECT 1 WHERE 1 = 2",  # always false, not tautology
        "SELECT 1",  # no WHERE at all
    ])
    def test_not_tautology(self, sql):
        stmt = parse_stmt(sql)
        assert has_tautological_where(stmt) is False

    def test_real_filter_with_tautology_in_and(self):
        """WHERE id = 1 AND 1=1 → not fully tautological (AND requires all parts)."""
        stmt = parse_stmt("SELECT 1 WHERE id = 1 AND 1=1")
        # AND is tautological only if BOTH sides are tautologies
        assert has_tautological_where(stmt) is False


# ─── Integration with column_policy ─────────────────────────────────────────


class TestTautologyInPolicy:
    """Tautology check integrated into column policy enforcement."""

    def test_tautology_blocked_with_required_filter(self):
        """WHERE 1=1 is blocked when table has required_filter_columns."""
        policy = make_policy()
        result = check_column_policy(
            "SELECT id FROM users WHERE 1=1 LIMIT 5", policy
        )
        assert result.is_blocked is True
        assert "Tautological" in result.reason

    def test_where_true_blocked(self):
        policy = make_policy()
        result = check_column_policy(
            "SELECT id FROM users WHERE true LIMIT 5", policy
        )
        assert result.is_blocked is True
        assert "Tautological" in result.reason

    def test_self_reference_blocked(self):
        policy = make_policy()
        result = check_column_policy(
            "SELECT id FROM users WHERE id = id LIMIT 5", policy
        )
        assert result.is_blocked is True
        assert "Tautological" in result.reason

    def test_real_filter_passes(self):
        """Legitimate filter passes as before."""
        policy = make_policy()
        result = check_column_policy(
            "SELECT id FROM users WHERE id = 42 LIMIT 5", policy
        )
        assert result.is_blocked is False

    def test_no_required_filter_skips_tautology_check(self):
        """Tables without required_filter_columns don't trigger tautology check."""
        policy = load_column_policy(
            policy_json='{"public.open_table": {"allowed_columns": ["id", "data"]}}',
            mode="strict",
        )
        result = check_column_policy(
            "SELECT id FROM open_table WHERE 1=1", policy
        )
        assert result.is_blocked is False

    def test_aggregate_bypasses_tautology(self):
        """Pure aggregate (COUNT) still passes despite tautological WHERE."""
        policy = make_policy()
        result = check_column_policy("SELECT COUNT(*) FROM users WHERE 1=1", policy)
        # Tautology check fires before aggregate exception — this should be blocked
        # because the intent of the tautology check is to catch LLM mistakes early
        assert result.is_blocked is True
