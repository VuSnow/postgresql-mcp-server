"""
Phase 10.14 — Single Statement + Supported SQL Shapes tests.
"""

import pytest

from postgresql_mcp.guardrails.statement_guard import check_statement


# ═══════════════════════════════════════════════════════════════════════════
# Multiple statements
# ═══════════════════════════════════════════════════════════════════════════


class TestMultipleStatements:
    """Only one statement per query."""

    def test_two_selects(self):
        sql = "SELECT 1; SELECT 2"
        r = check_statement(sql)
        assert r.is_blocked is True
        assert "one SQL statement" in r.reason

    def test_select_then_drop(self):
        sql = "SELECT id FROM users; DROP TABLE users"
        r = check_statement(sql)
        assert r.is_blocked is True

    def test_three_statements(self):
        sql = "SELECT 1; SELECT 2; SELECT 3"
        r = check_statement(sql)
        assert r.is_blocked is True

    def test_single_statement_ok(self):
        sql = "SELECT id, name FROM users WHERE id = 1"
        r = check_statement(sql)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Blocked statement types
# ═══════════════════════════════════════════════════════════════════════════


class TestBlockedStatementTypes:
    """COPY, DO, CALL are blocked."""

    def test_copy_to(self):
        sql = "COPY users TO '/tmp/users.csv'"
        r = check_statement(sql)
        assert r.is_blocked is True
        assert "COPY" in r.reason

    def test_copy_from(self):
        sql = "COPY users FROM '/tmp/users.csv'"
        r = check_statement(sql)
        assert r.is_blocked is True

    def test_do_block(self):
        sql = "DO $$ BEGIN RAISE NOTICE 'hello'; END $$"
        r = check_statement(sql)
        assert r.is_blocked is True
        assert "COMMAND" in r.reason

    def test_call_procedure(self):
        sql = "CALL my_procedure(1, 'abc')"
        r = check_statement(sql)
        assert r.is_blocked is True


# ═══════════════════════════════════════════════════════════════════════════
# SELECT INTO
# ═══════════════════════════════════════════════════════════════════════════


class TestSelectInto:
    """SELECT INTO creates a table — blocked."""

    def test_select_into(self):
        sql = "SELECT id, name INTO new_users FROM users WHERE active = true"
        r = check_statement(sql)
        assert r.is_blocked is True
        assert "SELECT INTO" in r.reason

    def test_select_into_temp(self):
        sql = "SELECT id INTO TEMP temp_table FROM users"
        r = check_statement(sql)
        assert r.is_blocked is True

    def test_normal_select_ok(self):
        sql = "SELECT id, name FROM users WHERE id = 1"
        r = check_statement(sql)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# LATERAL
# ═══════════════════════════════════════════════════════════════════════════


class TestLateral:
    """LATERAL joins are blocked."""

    def test_lateral_subquery(self):
        sql = """
        SELECT u.id, t.total
        FROM users u,
        LATERAL (SELECT SUM(amount) AS total FROM orders WHERE user_id = u.id) t
        """
        r = check_statement(sql)
        assert r.is_blocked is True
        assert "LATERAL" in r.reason

    def test_lateral_join(self):
        sql = """
        SELECT u.id, l.val
        FROM users u
        CROSS JOIN LATERAL unnest(u.tags) AS l(val)
        """
        r = check_statement(sql)
        assert r.is_blocked is True

    def test_normal_join_ok(self):
        sql = "SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id WHERE u.id = 1"
        r = check_statement(sql)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Valid queries pass
# ═══════════════════════════════════════════════════════════════════════════


class TestValidQueries:
    """Normal SELECT queries pass statement guard."""

    def test_simple_select(self):
        r = check_statement("SELECT id, name FROM users WHERE id = 1")
        assert r.is_blocked is False

    def test_join(self):
        sql = "SELECT u.id FROM users u JOIN orders o ON u.id = o.user_id LIMIT 10"
        r = check_statement(sql)
        assert r.is_blocked is False

    def test_aggregate(self):
        r = check_statement("SELECT COUNT(*) FROM users")
        assert r.is_blocked is False

    def test_with_limit_offset(self):
        r = check_statement("SELECT id FROM users ORDER BY id LIMIT 10 OFFSET 5")
        assert r.is_blocked is False

    def test_parse_error_passes(self):
        """Unparseable SQL not blocked by statement guard."""
        r = check_statement("THIS IS NOT SQL")
        assert r.is_blocked is False

    def test_where_clause(self):
        r = check_statement("SELECT id, email FROM users WHERE active = true AND age > 18 LIMIT 50")
        assert r.is_blocked is False
