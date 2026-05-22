"""Tests for QueryRewriter — LIMIT injection and capping."""

import pytest
from postgresql_mcp.guardrails.query_rewriter import QueryRewriter


@pytest.fixture
def rewriter():
    return QueryRewriter(default_limit=100, max_limit=1000)


class TestLimitInjection:
    def test_injects_limit_when_missing(self, rewriter):
        result = rewriter.rewrite("SELECT * FROM users")
        assert "LIMIT 100" in result

    def test_injects_limit_with_semicolon(self, rewriter):
        result = rewriter.rewrite("SELECT * FROM users;")
        assert "LIMIT 100" in result
        assert result.endswith(";")

    def test_preserves_existing_limit(self, rewriter):
        query = "SELECT * FROM users LIMIT 50"
        result = rewriter.rewrite(query)
        assert "LIMIT 50" in result
        assert "LIMIT 100" not in result

    def test_caps_excessive_limit(self, rewriter):
        query = "SELECT * FROM users LIMIT 5000"
        result = rewriter.rewrite(query)
        assert "LIMIT 1000" in result
        assert "LIMIT 5000" not in result

    def test_preserves_limit_at_max(self, rewriter):
        query = "SELECT * FROM users LIMIT 1000"
        result = rewriter.rewrite(query)
        assert "LIMIT 1000" in result

    def test_preserves_offset(self, rewriter):
        query = "SELECT * FROM users LIMIT 50 OFFSET 10"
        result = rewriter.rewrite(query)
        assert "OFFSET 10" in result


class TestAggregateSkip:
    def test_skips_count(self, rewriter):
        query = "SELECT COUNT(*) FROM users"
        result = rewriter.rewrite(query)
        assert "LIMIT" not in result

    def test_skips_sum(self, rewriter):
        query = "SELECT SUM(amount) FROM orders"
        result = rewriter.rewrite(query)
        assert "LIMIT" not in result

    def test_skips_avg(self, rewriter):
        query = "SELECT AVG(age) FROM users"
        result = rewriter.rewrite(query)
        assert "LIMIT" not in result

    def test_does_not_skip_with_group_by(self, rewriter):
        query = "SELECT status, COUNT(*) FROM orders GROUP BY status"
        result = rewriter.rewrite(query)
        assert "LIMIT 100" in result

    def test_does_not_skip_non_aggregate(self, rewriter):
        query = "SELECT name, age FROM users"
        result = rewriter.rewrite(query)
        assert "LIMIT 100" in result


class TestCTEHandling:
    def test_injects_limit_on_final_select(self, rewriter):
        query = """WITH active AS (
            SELECT * FROM users WHERE active = true
        )
        SELECT * FROM active"""
        result = rewriter.rewrite(query)
        assert "LIMIT 100" in result

    def test_does_not_inject_inside_cte(self, rewriter):
        query = """WITH active AS (
            SELECT * FROM users WHERE active = true LIMIT 10
        )
        SELECT * FROM active"""
        result = rewriter.rewrite(query)
        # The CTE's inner LIMIT 10 should remain
        assert "LIMIT 10" in result

    def test_caps_limit_on_final_select(self, rewriter):
        query = """WITH data AS (
            SELECT * FROM big_table
        )
        SELECT * FROM data LIMIT 9999"""
        result = rewriter.rewrite(query)
        assert "LIMIT 1000" in result


class TestEdgeCases:
    def test_empty_query(self, rewriter):
        result = rewriter.rewrite("")
        # Empty becomes empty + LIMIT (it's the rewriter's job, not validator's)
        assert "LIMIT" in result

    def test_custom_limits(self):
        rw = QueryRewriter(default_limit=10, max_limit=50)
        result = rw.rewrite("SELECT * FROM t")
        assert "LIMIT 10" in result

        result = rw.rewrite("SELECT * FROM t LIMIT 100")
        assert "LIMIT 50" in result

    def test_multiline_query(self, rewriter):
        query = """SELECT 
            id,
            name
        FROM users
        WHERE active = true"""
        result = rewriter.rewrite(query)
        assert "LIMIT 100" in result
