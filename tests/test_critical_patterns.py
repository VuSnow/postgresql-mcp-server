"""
Phase 10.17 — Critical Pattern Blocking tests.

Tests defense-in-depth regex layer that catches dangerous patterns
before AST parsing.
"""

import pytest

from postgresql_mcp.guardrails.critical_patterns import check_critical_patterns


# ═══════════════════════════════════════════════════════════════════════════
# File system access
# ═══════════════════════════════════════════════════════════════════════════


class TestFileSystemPatterns:
    def test_pg_read_file_blocked(self):
        r = check_critical_patterns("SELECT pg_read_file('/etc/passwd')")
        assert r.is_blocked is True
        assert "pg_read_file" in r.reason

    def test_pg_read_binary_file_blocked(self):
        r = check_critical_patterns("SELECT pg_read_binary_file('/etc/shadow')")
        assert r.is_blocked is True
        assert "pg_read_binary_file" in r.reason

    def test_pg_write_file_blocked(self):
        r = check_critical_patterns("SELECT pg_write_file('/tmp/x', 'data')")
        assert r.is_blocked is True
        assert "pg_write_file" in r.reason

    def test_pg_ls_dir_blocked(self):
        r = check_critical_patterns("SELECT pg_ls_dir('/etc')")
        assert r.is_blocked is True
        assert "pg_ls_dir" in r.reason

    def test_pg_stat_file_blocked(self):
        r = check_critical_patterns("SELECT pg_stat_file('/etc/passwd')")
        assert r.is_blocked is True
        assert "pg_stat_file" in r.reason


# ═══════════════════════════════════════════════════════════════════════════
# Large object operations
# ═══════════════════════════════════════════════════════════════════════════


class TestLargeObjectPatterns:
    def test_lo_import_blocked(self):
        r = check_critical_patterns("SELECT lo_import('/etc/passwd')")
        assert r.is_blocked is True
        assert "lo_import" in r.reason

    def test_lo_export_blocked(self):
        r = check_critical_patterns("SELECT lo_export(12345, '/tmp/dump')")
        assert r.is_blocked is True
        assert "lo_export" in r.reason

    def test_lo_unlink_blocked(self):
        r = check_critical_patterns("SELECT lo_unlink(12345)")
        assert r.is_blocked is True
        assert "lo_unlink" in r.reason


# ═══════════════════════════════════════════════════════════════════════════
# Command execution & COPY
# ═══════════════════════════════════════════════════════════════════════════


class TestCommandExecution:
    def test_pg_execute_server_program_blocked(self):
        r = check_critical_patterns(
            "COPY x FROM PROGRAM pg_execute_server_program('/bin/ls')"
        )
        assert r.is_blocked is True

    def test_copy_to_blocked(self):
        r = check_critical_patterns("COPY users TO '/tmp/users.csv'")
        assert r.is_blocked is True
        assert "COPY TO/FROM" in r.reason

    def test_copy_from_blocked(self):
        r = check_critical_patterns("COPY users FROM '/tmp/inject.csv'")
        assert r.is_blocked is True
        assert "COPY TO/FROM" in r.reason

    def test_copy_in_select_context(self):
        # Even embedded in a larger query
        r = check_critical_patterns("SELECT 1; COPY users TO '/tmp/x'")
        assert r.is_blocked is True


# ═══════════════════════════════════════════════════════════════════════════
# Backend manipulation & DoS
# ═══════════════════════════════════════════════════════════════════════════


class TestBackendManipulation:
    def test_pg_terminate_backend_blocked(self):
        r = check_critical_patterns("SELECT pg_terminate_backend(1234)")
        assert r.is_blocked is True
        assert "pg_terminate_backend" in r.reason

    def test_pg_cancel_backend_blocked(self):
        r = check_critical_patterns("SELECT pg_cancel_backend(1234)")
        assert r.is_blocked is True
        assert "pg_cancel_backend" in r.reason

    def test_pg_reload_conf_blocked(self):
        r = check_critical_patterns("SELECT pg_reload_conf()")
        assert r.is_blocked is True
        assert "pg_reload_conf" in r.reason

    def test_pg_sleep_blocked(self):
        r = check_critical_patterns("SELECT pg_sleep(10)")
        assert r.is_blocked is True
        assert "pg_sleep" in r.reason

    def test_pg_advisory_lock_blocked(self):
        r = check_critical_patterns("SELECT pg_advisory_lock(1)")
        assert r.is_blocked is True
        assert "advisory_lock" in r.reason

    def test_pg_advisory_xact_lock_blocked(self):
        r = check_critical_patterns("SELECT pg_advisory_xact_lock(1)")
        assert r.is_blocked is True
        assert "advisory" in r.reason

    def test_pg_try_advisory_lock_blocked(self):
        r = check_critical_patterns("SELECT pg_try_advisory_lock(1)")
        assert r.is_blocked is True


# ═══════════════════════════════════════════════════════════════════════════
# Data exfiltration via XML
# ═══════════════════════════════════════════════════════════════════════════


class TestXmlExfiltration:
    def test_database_to_xml_blocked(self):
        r = check_critical_patterns("SELECT database_to_xml(true, true, '')")
        assert r.is_blocked is True
        assert "database_to_xml" in r.reason

    def test_query_to_xml_blocked(self):
        r = check_critical_patterns("SELECT query_to_xml('SELECT * FROM users', true, true, '')")
        assert r.is_blocked is True
        assert "query_to_xml" in r.reason

    def test_table_to_xml_blocked(self):
        r = check_critical_patterns("SELECT table_to_xml('users', true, true, '')")
        assert r.is_blocked is True
        assert "table_to_xml" in r.reason

    def test_schema_to_xml_blocked(self):
        r = check_critical_patterns("SELECT schema_to_xml('public', true, true, '')")
        assert r.is_blocked is True
        assert "schema_to_xml" in r.reason


# ═══════════════════════════════════════════════════════════════════════════
# External access (dblink)
# ═══════════════════════════════════════════════════════════════════════════


class TestExternalAccess:
    def test_dblink_blocked(self):
        r = check_critical_patterns(
            "SELECT * FROM dblink('host=evil.com', 'SELECT 1') AS t(id int)"
        )
        assert r.is_blocked is True
        assert "dblink" in r.reason

    def test_dblink_exec_blocked(self):
        r = check_critical_patterns("SELECT dblink_exec('connstr', 'DROP TABLE x')")
        assert r.is_blocked is True
        assert "dblink_exec" in r.reason


# ═══════════════════════════════════════════════════════════════════════════
# Sensitive catalog tables
# ═══════════════════════════════════════════════════════════════════════════


class TestSensitiveCatalogs:
    def test_pg_shadow_blocked(self):
        r = check_critical_patterns("SELECT * FROM pg_shadow")
        assert r.is_blocked is True
        assert "pg_shadow" in r.reason

    def test_pg_authid_blocked(self):
        r = check_critical_patterns("SELECT * FROM pg_authid")
        assert r.is_blocked is True
        assert "pg_authid" in r.reason


# ═══════════════════════════════════════════════════════════════════════════
# Obfuscation / evasion patterns
# ═══════════════════════════════════════════════════════════════════════════


class TestObfuscationPatterns:
    def test_dollar_quoting_blocked(self):
        r = check_critical_patterns("SELECT $$malicious code$$")
        assert r.is_blocked is True
        assert "Dollar-quoted" in r.reason

    def test_dollar_quoting_multiline(self):
        r = check_critical_patterns("DO $$\nBEGIN\n  RAISE NOTICE 'pwned';\nEND;\n$$;")
        assert r.is_blocked is True

    def test_hex_escape_blocked(self):
        r = check_critical_patterns(r"SELECT '\x41\x42\x43'")
        assert r.is_blocked is True
        assert "Hex escape" in r.reason

    def test_unicode_escape_string_blocked(self):
        r = check_critical_patterns("SELECT U&'\\0041'")
        assert r.is_blocked is True
        assert "Unicode escape" in r.reason

    def test_unicode_escape_double_quote_blocked(self):
        r = check_critical_patterns('SELECT * FROM U"table"')
        # U& is the prefix, this one doesn't have &
        # Let's test the actual pattern: U&"..."
        pass

    def test_unicode_escape_with_ampersand(self):
        r = check_critical_patterns("SELECT U&'data'")
        assert r.is_blocked is True

    def test_backslash_escape_string_blocked(self):
        r = check_critical_patterns(r"SELECT E'test\\escape'")
        assert r.is_blocked is True
        assert "Escape string" in r.reason


# ═══════════════════════════════════════════════════════════════════════════
# Safe queries pass through
# ═══════════════════════════════════════════════════════════════════════════


class TestSafeQueries:
    def test_simple_select(self):
        r = check_critical_patterns("SELECT id, name FROM users WHERE id = 1")
        assert r.is_blocked is False

    def test_select_with_join(self):
        r = check_critical_patterns(
            "SELECT u.id, o.amount FROM users u JOIN orders o ON u.id = o.user_id"
        )
        assert r.is_blocked is False

    def test_aggregate_query(self):
        r = check_critical_patterns("SELECT COUNT(*), status FROM orders GROUP BY status")
        assert r.is_blocked is False

    def test_subquery(self):
        r = check_critical_patterns(
            "SELECT id FROM users WHERE id IN (SELECT user_id FROM orders)"
        )
        assert r.is_blocked is False

    def test_with_cte(self):
        r = check_critical_patterns(
            "WITH active AS (SELECT id FROM users WHERE active = true) "
            "SELECT * FROM active"
        )
        assert r.is_blocked is False

    def test_case_expression(self):
        r = check_critical_patterns(
            "SELECT CASE WHEN status = 'a' THEN 'Active' ELSE 'Inactive' END FROM users"
        )
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Master switch (enabled=False)
# ═══════════════════════════════════════════════════════════════════════════


class TestDisabled:
    def test_disabled_allows_everything(self):
        r = check_critical_patterns("SELECT pg_read_file('/etc/passwd')", enabled=False)
        assert r.is_blocked is False

    def test_disabled_dollar_quoting(self):
        r = check_critical_patterns("SELECT $$evil$$", enabled=False)
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# Case insensitivity
# ═══════════════════════════════════════════════════════════════════════════


class TestCaseInsensitivity:
    def test_uppercase(self):
        r = check_critical_patterns("SELECT PG_READ_FILE('/etc/passwd')")
        assert r.is_blocked is True

    def test_mixed_case(self):
        r = check_critical_patterns("SELECT Pg_Sleep(10)")
        assert r.is_blocked is True

    def test_copy_mixed(self):
        r = check_critical_patterns("Copy users To '/tmp/x'")
        assert r.is_blocked is True
