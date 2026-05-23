"""
Phase 10.12 — User Context for RLS tests.

Tests variable name validation, user_id validation, and SET LOCAL generation.
"""

import pytest

from postgresql_mcp.guardrails.user_context import (
    validate_variable_name,
    validate_user_id,
    build_set_local_sql,
)


# ═══════════════════════════════════════════════════════════════════════════
# Variable name validation
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateVariableName:
    def test_simple_name(self):
        r = validate_variable_name("app.current_user_id")
        assert r.is_blocked is False

    def test_dotted_name(self):
        r = validate_variable_name("myapp.tenant.id")
        assert r.is_blocked is False

    def test_underscore_start(self):
        r = validate_variable_name("_internal_var")
        assert r.is_blocked is False

    def test_no_dots(self):
        r = validate_variable_name("user_id")
        assert r.is_blocked is False

    def test_empty(self):
        r = validate_variable_name("")
        assert r.is_blocked is True

    def test_sql_injection_semicolon(self):
        r = validate_variable_name("app.user'; DROP TABLE users; --")
        assert r.is_blocked is True

    def test_spaces(self):
        r = validate_variable_name("app user")
        assert r.is_blocked is True

    def test_special_chars(self):
        r = validate_variable_name("app@user")
        assert r.is_blocked is True

    def test_starts_with_number(self):
        r = validate_variable_name("1app.user")
        assert r.is_blocked is True

    def test_single_quotes(self):
        r = validate_variable_name("app'user")
        assert r.is_blocked is True


# ═══════════════════════════════════════════════════════════════════════════
# User ID validation
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateUserId:
    def test_numeric_id(self):
        r = validate_user_id("12345")
        assert r.is_blocked is False

    def test_uuid(self):
        r = validate_user_id("550e8400-e29b-41d4-a716-446655440000")
        assert r.is_blocked is False

    def test_alphanumeric(self):
        r = validate_user_id("user_abc_123")
        assert r.is_blocked is False

    def test_empty(self):
        r = validate_user_id("")
        assert r.is_blocked is True

    def test_sql_injection(self):
        r = validate_user_id("1'; DROP TABLE users; --")
        assert r.is_blocked is True

    def test_spaces(self):
        r = validate_user_id("user 123")
        assert r.is_blocked is True

    def test_single_quotes(self):
        r = validate_user_id("user'id")
        assert r.is_blocked is True

    def test_semicolons(self):
        r = validate_user_id("123;456")
        assert r.is_blocked is True

    def test_parentheses(self):
        r = validate_user_id("pg_sleep(5)")
        assert r.is_blocked is True

    def test_backslash(self):
        r = validate_user_id("user\\id")
        assert r.is_blocked is True


# ═══════════════════════════════════════════════════════════════════════════
# SET LOCAL SQL generation
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildSetLocalSql:
    def test_basic(self):
        sql = build_set_local_sql("app.current_user_id", "12345")
        assert sql == """SET LOCAL "app.current_user_id" = '12345'"""

    def test_uuid_value(self):
        sql = build_set_local_sql("app.user_id", "550e8400-e29b-41d4-a716-446655440000")
        assert "550e8400" in sql
        assert "SET LOCAL" in sql

    def test_quoted_variable(self):
        """Variable name is double-quoted to handle dots safely."""
        sql = build_set_local_sql("my.app.tenant", "abc")
        assert '"my.app.tenant"' in sql


# ═══════════════════════════════════════════════════════════════════════════
# Config integration
# ═══════════════════════════════════════════════════════════════════════════


class TestConfigIntegration:
    def test_variable_configured(self):
        from postgresql_mcp.configs import ServerConfigs

        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            USER_CONTEXT_VARIABLE="app.current_user_id",
        )
        assert configs.user_context_variable == "app.current_user_id"

    def test_variable_not_configured(self):
        from postgresql_mcp.configs import ServerConfigs

        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
        )
        assert configs.user_context_variable is None
