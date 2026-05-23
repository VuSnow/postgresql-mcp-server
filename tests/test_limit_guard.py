"""
Phase 10.11 — LIMIT / OFFSET Enforcement tests.
"""

import pytest

from postgresql_mcp.guardrails.limit_guard import check_limit_offset


# ═══════════════════════════════════════════════════════════════════════════
# LIMIT enforcement
# ═══════════════════════════════════════════════════════════════════════════


class TestLimitExceeded:
    """Queries with LIMIT exceeding max are rejected."""

    def test_limit_over_max(self):
        sql = "SELECT id FROM users LIMIT 5000"
        r = check_limit_offset(sql, max_limit=1000)
        assert r.is_blocked is True
        assert "5000" in r.reason
        assert "1000" in r.reason

    def test_limit_at_max(self):
        sql = "SELECT id FROM users LIMIT 1000"
        r = check_limit_offset(sql, max_limit=1000)
        assert r.is_blocked is False

    def test_limit_below_max(self):
        sql = "SELECT id FROM users LIMIT 10"
        r = check_limit_offset(sql, max_limit=1000)
        assert r.is_blocked is False

    def test_limit_one(self):
        sql = "SELECT id FROM users LIMIT 1"
        r = check_limit_offset(sql, max_limit=100)
        assert r.is_blocked is False

    def test_limit_zero(self):
        """LIMIT 0 is valid (returns no rows)."""
        sql = "SELECT id FROM users LIMIT 0"
        r = check_limit_offset(sql, max_limit=100)
        assert r.is_blocked is False


class TestLimitRequired:
    """require_limit=True rejects queries without LIMIT."""

    def test_no_limit_rejected(self):
        sql = "SELECT id, name FROM users WHERE active = true"
        r = check_limit_offset(sql, require_limit=True)
        assert r.is_blocked is True
        assert "LIMIT" in r.reason

    def test_no_limit_allowed_by_default(self):
        sql = "SELECT id, name FROM users WHERE active = true"
        r = check_limit_offset(sql, require_limit=False)
        assert r.is_blocked is False

    def test_with_limit_passes(self):
        sql = "SELECT id, name FROM users WHERE active = true LIMIT 50"
        r = check_limit_offset(sql, require_limit=True)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Aggregate exception
# ═══════════════════════════════════════════════════════════════════════════


class TestAggregateException:
    """Pure aggregates don't need LIMIT even when required."""

    def test_count_star_no_limit(self):
        sql = "SELECT COUNT(*) FROM users"
        r = check_limit_offset(sql, require_limit=True)
        assert r.is_blocked is False

    def test_sum_avg_no_limit(self):
        sql = "SELECT SUM(amount), AVG(amount) FROM transactions"
        r = check_limit_offset(sql, require_limit=True)
        assert r.is_blocked is False

    def test_min_max_no_limit(self):
        sql = "SELECT MIN(created_at), MAX(created_at) FROM users"
        r = check_limit_offset(sql, require_limit=True)
        assert r.is_blocked is False

    def test_group_by_needs_limit(self):
        """GROUP BY can produce unbounded rows — LIMIT still required."""
        sql = "SELECT department, COUNT(*) FROM employees GROUP BY department"
        r = check_limit_offset(sql, require_limit=True)
        assert r.is_blocked is True

    def test_group_by_with_limit_passes(self):
        sql = "SELECT department, COUNT(*) FROM employees GROUP BY department LIMIT 20"
        r = check_limit_offset(sql, require_limit=True)
        assert r.is_blocked is False

    def test_non_aggregate_column_needs_limit(self):
        """SELECT with mix of agg and non-agg needs LIMIT."""
        sql = "SELECT name, COUNT(*) FROM users GROUP BY name"
        r = check_limit_offset(sql, require_limit=True)
        assert r.is_blocked is True


# ═══════════════════════════════════════════════════════════════════════════
# OFFSET enforcement
# ═══════════════════════════════════════════════════════════════════════════


class TestOffsetExceeded:
    """Queries with OFFSET exceeding max are rejected."""

    def test_offset_over_max(self):
        sql = "SELECT id FROM users LIMIT 10 OFFSET 20000"
        r = check_limit_offset(sql, max_offset=10000)
        assert r.is_blocked is True
        assert "20000" in r.reason
        assert "10000" in r.reason

    def test_offset_at_max(self):
        sql = "SELECT id FROM users LIMIT 10 OFFSET 10000"
        r = check_limit_offset(sql, max_offset=10000)
        assert r.is_blocked is False

    def test_offset_below_max(self):
        sql = "SELECT id FROM users LIMIT 10 OFFSET 100"
        r = check_limit_offset(sql, max_offset=10000)
        assert r.is_blocked is False

    def test_no_offset_passes(self):
        sql = "SELECT id FROM users LIMIT 10"
        r = check_limit_offset(sql, max_offset=10000)
        assert r.is_blocked is False

    def test_offset_zero(self):
        sql = "SELECT id FROM users LIMIT 10 OFFSET 0"
        r = check_limit_offset(sql, max_offset=10000)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Combined LIMIT + OFFSET
# ═══════════════════════════════════════════════════════════════════════════


class TestCombined:
    """Both LIMIT and OFFSET validated together."""

    def test_both_valid(self):
        sql = "SELECT id FROM users LIMIT 50 OFFSET 500"
        r = check_limit_offset(sql, max_limit=100, max_offset=10000)
        assert r.is_blocked is False

    def test_limit_over_offset_ok(self):
        sql = "SELECT id FROM users LIMIT 5000 OFFSET 500"
        r = check_limit_offset(sql, max_limit=1000, max_offset=10000)
        assert r.is_blocked is True
        assert "LIMIT" in r.reason

    def test_offset_over_limit_ok(self):
        sql = "SELECT id FROM users LIMIT 50 OFFSET 50000"
        r = check_limit_offset(sql, max_limit=1000, max_offset=10000)
        assert r.is_blocked is True
        assert "OFFSET" in r.reason


# ═══════════════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Parse errors and special cases."""

    def test_parse_error_passes(self):
        r = check_limit_offset("NOT VALID SQL AT ALL")
        assert r.is_blocked is False

    def test_insert_no_limit_passes(self):
        """Non-SELECT statements don't have LIMIT — not blocked."""
        r = check_limit_offset("INSERT INTO t (id) VALUES (1)", require_limit=True)
        assert r.is_blocked is False

    def test_small_max_limit(self):
        sql = "SELECT id FROM users LIMIT 5"
        r = check_limit_offset(sql, max_limit=3)
        assert r.is_blocked is True

    def test_very_large_offset(self):
        sql = "SELECT id FROM users LIMIT 10 OFFSET 999999999"
        r = check_limit_offset(sql, max_offset=10000)
        assert r.is_blocked is True
