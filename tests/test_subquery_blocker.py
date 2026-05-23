"""
Phase 10.9 — Subquery / CTE / Set Operation Blocker tests.

Tests structural shape enforcement for subqueries, CTEs, and set operations.
"""

import pytest

from postgresql_mcp.guardrails.subquery_blocker import check_query_structure


# ═══════════════════════════════════════════════════════════════════════════
# Subqueries
# ═══════════════════════════════════════════════════════════════════════════


class TestSubqueryBlocked:
    """BLOCK_SUBQUERIES=true (default) rejects nested SELECT."""

    def test_subquery_in_where(self):
        sql = "SELECT id FROM users WHERE id IN (SELECT user_id FROM admins)"
        r = check_query_structure(sql, block_subqueries=True)
        assert r.is_blocked is True
        assert "Subqueries" in r.reason

    def test_subquery_in_from(self):
        sql = "SELECT t.id FROM (SELECT id FROM users) AS t"
        r = check_query_structure(sql, block_subqueries=True)
        assert r.is_blocked is True

    def test_subquery_in_select_list(self):
        sql = "SELECT id, (SELECT COUNT(*) FROM orders WHERE orders.user_id = users.id) FROM users"
        r = check_query_structure(sql, block_subqueries=True)
        assert r.is_blocked is True

    def test_exists_subquery(self):
        sql = "SELECT id FROM users WHERE EXISTS (SELECT 1 FROM admins WHERE admins.id = users.id)"
        r = check_query_structure(sql, block_subqueries=True)
        assert r.is_blocked is True

    def test_not_in_subquery(self):
        sql = "SELECT id FROM users WHERE id NOT IN (SELECT blocked_id FROM blocklist)"
        r = check_query_structure(sql, block_subqueries=True)
        assert r.is_blocked is True


class TestSubqueryAllowed:
    """BLOCK_SUBQUERIES=false allows subqueries."""

    def test_subquery_in_where_allowed(self):
        sql = "SELECT id FROM users WHERE id IN (SELECT user_id FROM admins)"
        r = check_query_structure(sql, block_subqueries=False)
        assert r.is_blocked is False

    def test_subquery_in_from_allowed(self):
        sql = "SELECT t.id FROM (SELECT id FROM users) AS t"
        r = check_query_structure(sql, block_subqueries=False)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# CTE (WITH clause)
# ═══════════════════════════════════════════════════════════════════════════


class TestCTEBlocked:
    """ALLOW_CTE=false (default) rejects WITH clauses."""

    def test_simple_cte(self):
        sql = "WITH active AS (SELECT id FROM users WHERE active = true) SELECT id FROM active"
        r = check_query_structure(sql, allow_cte=False)
        assert r.is_blocked is True
        assert "CTE" in r.reason

    def test_multiple_ctes(self):
        sql = """
        WITH a AS (SELECT 1 AS x),
             b AS (SELECT 2 AS y)
        SELECT a.x, b.y FROM a, b
        """
        r = check_query_structure(sql, allow_cte=False)
        assert r.is_blocked is True

    def test_recursive_cte_blocked_even_without_allow_cte(self):
        sql = """
        WITH RECURSIVE tree AS (
            SELECT id, parent_id, name FROM categories WHERE parent_id IS NULL
            UNION ALL
            SELECT c.id, c.parent_id, c.name FROM categories c JOIN tree t ON c.parent_id = t.id
        )
        SELECT * FROM tree
        """
        r = check_query_structure(sql, allow_cte=False, allow_recursive_cte=False)
        assert r.is_blocked is True


class TestCTEAllowed:
    """ALLOW_CTE=true allows WITH clauses."""

    def test_simple_cte_allowed(self):
        sql = "WITH active AS (SELECT id FROM users WHERE active = true) SELECT id FROM active"
        r = check_query_structure(sql, allow_cte=True, block_subqueries=False)
        assert r.is_blocked is False

    def test_multiple_ctes_allowed(self):
        sql = """
        WITH a AS (SELECT 1 AS x),
             b AS (SELECT 2 AS y)
        SELECT a.x, b.y FROM a, b
        """
        r = check_query_structure(sql, allow_cte=True, block_subqueries=False)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Recursive CTE
# ═══════════════════════════════════════════════════════════════════════════


class TestRecursiveCTEBlocked:
    """ALLOW_RECURSIVE_CTE=false (default) blocks recursive CTEs."""

    def test_recursive_cte(self):
        sql = """
        WITH RECURSIVE tree AS (
            SELECT id, parent_id FROM categories WHERE parent_id IS NULL
            UNION ALL
            SELECT c.id, c.parent_id FROM categories c JOIN tree t ON c.parent_id = t.id
        )
        SELECT id FROM tree
        """
        r = check_query_structure(sql, allow_cte=True, allow_recursive_cte=False, block_subqueries=False)
        assert r.is_blocked is True
        assert "Recursive" in r.reason

    def test_recursive_keyword_without_actual_recursion(self):
        """WITH RECURSIVE that doesn't self-reference is still flagged (keyword-level)."""
        sql = """
        WITH RECURSIVE cte AS (
            SELECT 1 AS n
        )
        SELECT n FROM cte
        """
        r = check_query_structure(sql, allow_cte=True, allow_recursive_cte=False, block_subqueries=False)
        assert r.is_blocked is True


class TestRecursiveCTEAllowed:
    """ALLOW_RECURSIVE_CTE=true allows recursive CTEs."""

    def test_recursive_cte_allowed(self):
        sql = """
        WITH RECURSIVE tree AS (
            SELECT id, parent_id FROM categories WHERE parent_id IS NULL
            UNION ALL
            SELECT c.id, c.parent_id FROM categories c JOIN tree t ON c.parent_id = t.id
        )
        SELECT id FROM tree
        """
        r = check_query_structure(
            sql,
            allow_cte=True,
            allow_recursive_cte=True,
            allow_set_operations=True,
            block_subqueries=False,
        )
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Set operations (UNION / INTERSECT / EXCEPT)
# ═══════════════════════════════════════════════════════════════════════════


class TestSetOperationsBlocked:
    """ALLOW_SET_OPERATIONS=false (default) rejects UNION/INTERSECT/EXCEPT."""

    def test_union(self):
        sql = "SELECT id FROM users UNION SELECT id FROM admins"
        r = check_query_structure(sql, allow_set_operations=False)
        assert r.is_blocked is True
        assert "Set operations" in r.reason

    def test_union_all(self):
        sql = "SELECT id FROM users UNION ALL SELECT id FROM admins"
        r = check_query_structure(sql, allow_set_operations=False)
        assert r.is_blocked is True

    def test_intersect(self):
        sql = "SELECT id FROM users INTERSECT SELECT id FROM admins"
        r = check_query_structure(sql, allow_set_operations=False)
        assert r.is_blocked is True

    def test_except(self):
        sql = "SELECT id FROM users EXCEPT SELECT id FROM blocked_users"
        r = check_query_structure(sql, allow_set_operations=False)
        assert r.is_blocked is True


class TestSetOperationsAllowed:
    """ALLOW_SET_OPERATIONS=true allows set operations."""

    def test_union_allowed(self):
        sql = "SELECT id FROM users UNION SELECT id FROM admins"
        r = check_query_structure(sql, allow_set_operations=True)
        assert r.is_blocked is False

    def test_union_all_allowed(self):
        sql = "SELECT id FROM users UNION ALL SELECT id FROM admins"
        r = check_query_structure(sql, allow_set_operations=True)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Simple queries (no shape issues)
# ═══════════════════════════════════════════════════════════════════════════


class TestSimpleQueriesPass:
    """Flat queries pass all structure checks."""

    def test_simple_select(self):
        r = check_query_structure("SELECT id, name FROM users WHERE id = 1")
        assert r.is_blocked is False

    def test_join_not_subquery(self):
        sql = "SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id WHERE u.id = 1"
        r = check_query_structure(sql)
        assert r.is_blocked is False

    def test_aggregate_group_by(self):
        sql = "SELECT department, COUNT(*) FROM employees GROUP BY department"
        r = check_query_structure(sql)
        assert r.is_blocked is False

    def test_order_by_limit(self):
        sql = "SELECT id, name FROM users ORDER BY name LIMIT 10"
        r = check_query_structure(sql)
        assert r.is_blocked is False

    def test_parse_error_passes(self):
        """Unparseable SQL is not blocked by structure checker (other guardrails handle it)."""
        r = check_query_structure("THIS IS NOT SQL AT ALL")
        assert r.is_blocked is False

    def test_having_clause(self):
        sql = "SELECT department, COUNT(*) FROM emp GROUP BY department HAVING COUNT(*) > 5"
        r = check_query_structure(sql)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Combined flags
# ═══════════════════════════════════════════════════════════════════════════


class TestCombinedFlags:
    """Multiple flags interact correctly."""

    def test_cte_with_subquery_both_blocked(self):
        """CTE blocked first (check order: subquery → CTE)."""
        sql = """
        WITH cte AS (SELECT id FROM users WHERE id IN (SELECT user_id FROM admins))
        SELECT id FROM cte
        """
        r = check_query_structure(sql, block_subqueries=True, allow_cte=False)
        assert r.is_blocked is True

    def test_cte_allowed_but_subquery_blocked(self):
        """CTE body containing subquery is still caught."""
        sql = """
        WITH cte AS (SELECT id FROM users WHERE id IN (SELECT user_id FROM admins))
        SELECT id FROM cte
        """
        r = check_query_structure(sql, block_subqueries=True, allow_cte=True)
        assert r.is_blocked is True
        assert "Subqueries" in r.reason

    def test_all_allowed(self):
        """Everything enabled — complex query passes structure check."""
        sql = """
        WITH cte AS (SELECT id FROM users)
        SELECT id FROM cte
        UNION
        SELECT id FROM admins
        """
        r = check_query_structure(
            sql,
            block_subqueries=False,
            allow_cte=True,
            allow_set_operations=True,
        )
        assert r.is_blocked is False
