"""
Phase 10.2 — System Catalog Blocking tests.

Tests for AST-based table extraction and system catalog access prevention.
"""

import pytest
from postgresql_mcp.guardrails.sql_parser import parse_query, extract_tables, ParsedQuery
from postgresql_mcp.guardrails.catalog_blocker import (
    check_system_catalog_access,
    CatalogCheckResult,
    BLOCKED_SYSTEM_TABLES,
    BLOCKED_SCHEMAS,
)


# ─── AST Parser: Table Extraction ───────────────────────────────────────────


class TestTableExtraction:
    """extract_tables correctly identifies all table references."""

    def test_simple_select(self):
        tables = parse_query("SELECT id FROM users").tables
        assert tables == ["public.users"]

    def test_qualified_table(self):
        tables = parse_query("SELECT id FROM public.users").tables
        assert tables == ["public.users"]

    def test_schema_qualified(self):
        tables = parse_query("SELECT id FROM analytics.events").tables
        assert tables == ["analytics.events"]

    def test_join_extracts_both_tables(self):
        sql = "SELECT u.id FROM users u JOIN orders o ON u.id = o.user_id"
        tables = parse_query(sql).tables
        assert "public.users" in tables
        assert "public.orders" in tables

    def test_multiple_joins(self):
        sql = """
            SELECT u.id
            FROM users u
            JOIN orders o ON u.id = o.user_id
            JOIN products p ON o.product_id = p.id
        """
        tables = parse_query(sql).tables
        assert len(tables) == 3
        assert "public.users" in tables
        assert "public.orders" in tables
        assert "public.products" in tables

    def test_subquery_table(self):
        sql = "SELECT * FROM (SELECT id FROM users) sub"
        tables = parse_query(sql).tables
        assert "public.users" in tables

    def test_pg_catalog_qualified(self):
        sql = "SELECT * FROM pg_catalog.pg_shadow"
        tables = parse_query(sql).tables
        assert "pg_catalog.pg_shadow" in tables

    def test_unqualified_pg_tables_get_default_schema(self):
        """Unqualified pg_shadow → public.pg_shadow (not pg_catalog)."""
        sql = "SELECT * FROM pg_shadow"
        tables = parse_query(sql).tables
        # sqlglot treats unqualified as default schema
        assert "public.pg_shadow" in tables

    def test_custom_default_schema(self):
        tables = parse_query("SELECT id FROM users", default_schema="myschema").tables
        assert tables == ["myschema.users"]

    def test_cte_source_tables(self):
        sql = "WITH cte AS (SELECT id FROM users) SELECT * FROM cte"
        tables = parse_query(sql).tables
        assert "public.users" in tables

    def test_case_insensitive(self):
        tables = parse_query("SELECT id FROM PUBLIC.Users").tables
        assert "public.users" in tables


# ─── AST Parser: Query Shape Detection ──────────────────────────────────────


class TestQueryShapeDetection:
    """Detect CTE, subquery, set operations, star select."""

    def test_detect_star(self):
        assert parse_query("SELECT * FROM users").has_star is True

    def test_count_star_not_detected_as_star(self):
        assert parse_query("SELECT COUNT(*) FROM users").has_star is False

    def test_table_star(self):
        assert parse_query("SELECT users.* FROM users").has_star is True

    def test_detect_cte(self):
        sql = "WITH cte AS (SELECT 1) SELECT * FROM cte"
        assert parse_query(sql).has_cte is True

    def test_no_cte(self):
        assert parse_query("SELECT 1").has_cte is False

    def test_detect_recursive_cte(self):
        sql = "WITH RECURSIVE cte AS (SELECT 1 UNION ALL SELECT 1) SELECT * FROM cte"
        assert parse_query(sql).has_recursive_cte is True

    def test_detect_union(self):
        sql = "SELECT 1 UNION SELECT 2"
        assert parse_query(sql).has_set_operation is True

    def test_detect_intersect(self):
        sql = "SELECT 1 INTERSECT SELECT 1"
        assert parse_query(sql).has_set_operation is True

    def test_detect_except(self):
        sql = "SELECT 1 EXCEPT SELECT 2"
        assert parse_query(sql).has_set_operation is True

    def test_no_set_operation(self):
        assert parse_query("SELECT 1 FROM users").has_set_operation is False

    def test_statement_count_single(self):
        assert parse_query("SELECT 1").statement_count == 1

    def test_statement_count_multiple(self):
        assert parse_query("SELECT 1; SELECT 2").statement_count == 2

    def test_detect_limit(self):
        assert parse_query("SELECT id FROM users LIMIT 10").limit == 10

    def test_detect_offset(self):
        assert parse_query("SELECT id FROM users LIMIT 10 OFFSET 20").offset == 20

    def test_no_limit(self):
        assert parse_query("SELECT id FROM users").limit is None

    def test_parse_error(self):
        result = parse_query("NOT VALID SQL ???")
        # sqlglot is lenient — may not error. Test that it doesn't crash.
        assert isinstance(result, ParsedQuery)


# ─── System Catalog Blocking ────────────────────────────────────────────────


class TestSystemCatalogBlocking:
    """check_system_catalog_access blocks dangerous system tables."""

    def test_block_pg_shadow(self):
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_shadow")
        assert result.is_blocked is True
        assert "pg_shadow" in result.blocked_table

    def test_block_pg_authid(self):
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_authid")
        assert result.is_blocked is True

    def test_block_pg_roles(self):
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_roles")
        assert result.is_blocked is True

    def test_block_pg_user(self):
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_user")
        assert result.is_blocked is True

    def test_block_pg_stat_activity(self):
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_stat_activity")
        assert result.is_blocked is True

    def test_block_pg_stat_statements(self):
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_stat_statements")
        assert result.is_blocked is True

    def test_block_pg_settings(self):
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_settings")
        assert result.is_blocked is True

    def test_block_any_pg_catalog_table(self):
        """Any table under pg_catalog schema is blocked."""
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_class")
        assert result.is_blocked is True
        assert "pg_catalog" in result.reason

    def test_block_in_join(self):
        """System catalog referenced in JOIN is also blocked."""
        sql = "SELECT u.id FROM users u JOIN pg_catalog.pg_roles r ON true"
        result = check_system_catalog_access(sql)
        assert result.is_blocked is True

    def test_block_in_subquery(self):
        """System catalog in subquery is blocked."""
        sql = "SELECT * FROM (SELECT * FROM pg_catalog.pg_shadow) sub"
        result = check_system_catalog_access(sql)
        assert result.is_blocked is True

    def test_allow_regular_table(self):
        """Normal tables are not blocked."""
        result = check_system_catalog_access("SELECT id FROM users")
        assert result.is_blocked is False

    def test_allow_information_schema(self):
        """information_schema is NOT blocked (metadata tools use it)."""
        result = check_system_catalog_access(
            "SELECT * FROM information_schema.tables"
        )
        assert result.is_blocked is False

    def test_allow_qualified_user_table(self):
        result = check_system_catalog_access("SELECT id FROM public.users")
        assert result.is_blocked is False

    def test_allow_analytics_schema(self):
        result = check_system_catalog_access("SELECT id FROM analytics.events")
        assert result.is_blocked is False

    def test_block_pg_file_settings(self):
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_file_settings")
        assert result.is_blocked is True

    def test_block_pg_hba_file_rules(self):
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_hba_file_rules")
        assert result.is_blocked is True

    def test_block_case_insensitive(self):
        """Blocking works regardless of case."""
        result = check_system_catalog_access("SELECT * FROM PG_CATALOG.PG_SHADOW")
        assert result.is_blocked is True

    def test_multiple_tables_one_blocked(self):
        """If any table is blocked, the query is blocked."""
        sql = "SELECT * FROM users, pg_catalog.pg_authid"
        result = check_system_catalog_access(sql)
        assert result.is_blocked is True

    def test_result_includes_reason(self):
        result = check_system_catalog_access("SELECT * FROM pg_catalog.pg_shadow")
        assert result.reason != ""
        assert result.blocked_table != ""
