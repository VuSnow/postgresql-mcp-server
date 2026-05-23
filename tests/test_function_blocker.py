"""
Phase 10.8 — Function Allowlist/Blocklist tests.

Tests for function enforcement in both allowlist and blacklist modes.
"""

import pytest

from postgresql_mcp.guardrails.function_blocker import (
    check_functions,
    load_allowed_functions,
    DEFAULT_ALLOWED_FUNCTIONS,
    DANGEROUS_FUNCTIONS,
)


# ─── load_allowed_functions ──────────────────────────────────────────────────


class TestLoadAllowedFunctions:
    def test_parse_json_array(self):
        result = load_allowed_functions('["count", "sum", "avg"]')
        assert result == frozenset(["count", "sum", "avg"])

    def test_case_normalized(self):
        result = load_allowed_functions('["COUNT", "SUM"]')
        assert "count" in result
        assert "sum" in result

    def test_none_returns_none(self):
        assert load_allowed_functions(None) is None

    def test_empty_string_returns_none(self):
        assert load_allowed_functions("") is None


# ─── Allowlist mode — blocked ────────────────────────────────────────────────


class TestAllowlistBlocked:
    """Functions not in allowlist are rejected."""

    def test_pg_sleep_blocked(self):
        result = check_functions("SELECT pg_sleep(5)", mode="allowlist")
        assert result.is_blocked is True
        assert "pg_sleep" in result.reason

    def test_dblink_blocked(self):
        result = check_functions("SELECT dblink('host=evil', 'SELECT 1')", mode="allowlist")
        assert result.is_blocked is True
        assert "dblink" in result.reason

    def test_lo_export_blocked(self):
        result = check_functions("SELECT lo_export(12345, '/tmp/out')", mode="allowlist")
        assert result.is_blocked is True

    def test_current_setting_blocked(self):
        result = check_functions("SELECT current_setting('data_directory')", mode="allowlist")
        assert result.is_blocked is True

    def test_set_config_blocked(self):
        result = check_functions("SELECT set_config('log_statement', 'all', false)", mode="allowlist")
        assert result.is_blocked is True

    def test_custom_function_blocked(self):
        """User-defined functions not in allowlist are blocked."""
        result = check_functions("SELECT my_custom_func(1)", mode="allowlist")
        assert result.is_blocked is True
        assert "my_custom_func" in result.reason


# ─── Allowlist mode — allowed ────────────────────────────────────────────────


class TestAllowlistAllowed:
    """Safe functions in the default allowlist pass."""

    def test_count(self):
        result = check_functions("SELECT COUNT(*) FROM users", mode="allowlist")
        assert result.is_blocked is False

    def test_aggregates(self):
        result = check_functions("SELECT SUM(amount), AVG(amount), MIN(amount), MAX(amount) FROM t", mode="allowlist")
        assert result.is_blocked is False

    def test_string_functions(self):
        result = check_functions("SELECT LOWER(name), UPPER(name), LENGTH(name) FROM t WHERE id=1", mode="allowlist")
        assert result.is_blocked is False

    def test_date_functions(self):
        result = check_functions("SELECT date_trunc('month', created_at), NOW() FROM t WHERE id=1", mode="allowlist")
        assert result.is_blocked is False

    def test_math_functions(self):
        result = check_functions("SELECT ROUND(amount, 2), ABS(balance), FLOOR(rate) FROM t WHERE id=1", mode="allowlist")
        assert result.is_blocked is False

    def test_coalesce(self):
        result = check_functions("SELECT COALESCE(name, 'Unknown') FROM t WHERE id=1", mode="allowlist")
        assert result.is_blocked is False

    def test_json_agg(self):
        result = check_functions("SELECT json_agg(row_to_json(t)) FROM t", mode="allowlist")
        assert result.is_blocked is False

    def test_window_function(self):
        result = check_functions("SELECT ROW_NUMBER() OVER (ORDER BY id) FROM t", mode="allowlist")
        assert result.is_blocked is False

    def test_no_functions_passes(self):
        result = check_functions("SELECT id, name FROM users WHERE id = 1", mode="allowlist")
        assert result.is_blocked is False

    def test_extract(self):
        result = check_functions("SELECT EXTRACT(year FROM created_at) FROM t WHERE id=1", mode="allowlist")
        assert result.is_blocked is False


# ─── Custom allowlist ────────────────────────────────────────────────────────


class TestCustomAllowlist:
    """User-provided ALLOWED_FUNCTIONS overrides default."""

    def test_custom_allows_specific(self):
        custom = frozenset(["count", "sum"])
        result = check_functions("SELECT COUNT(*) FROM users", mode="allowlist", allowed_functions=custom)
        assert result.is_blocked is False

    def test_custom_blocks_unlisted(self):
        custom = frozenset(["count", "sum"])
        result = check_functions("SELECT LOWER(name) FROM users WHERE id=1", mode="allowlist", allowed_functions=custom)
        assert result.is_blocked is True
        assert "lower" in result.reason


# ─── Blacklist mode — blocked ────────────────────────────────────────────────


class TestBlacklistBlocked:
    """Dangerous functions blocked in blacklist mode."""

    def test_pg_sleep(self):
        result = check_functions("SELECT pg_sleep(10)", mode="blacklist")
        assert result.is_blocked is True

    def test_pg_read_file(self):
        result = check_functions("SELECT pg_read_file('/etc/passwd')", mode="blacklist")
        assert result.is_blocked is True

    def test_lo_export(self):
        result = check_functions("SELECT lo_export(1234, '/tmp/dump')", mode="blacklist")
        assert result.is_blocked is True


# ─── Blacklist mode — allowed ────────────────────────────────────────────────


class TestBlacklistAllowed:
    """Non-dangerous functions pass in blacklist mode."""

    def test_custom_function_allowed(self):
        """User-defined functions are allowed in blacklist mode."""
        result = check_functions("SELECT my_custom_func(1)", mode="blacklist")
        assert result.is_blocked is False

    def test_safe_functions(self):
        result = check_functions("SELECT LOWER(name), COUNT(*) FROM t WHERE id=1", mode="blacklist")
        assert result.is_blocked is False

    def test_no_functions(self):
        result = check_functions("SELECT id FROM users WHERE id = 1", mode="blacklist")
        assert result.is_blocked is False
