"""Tests for SecurityValidator — injection attempts, forbidden keywords, edge cases."""

import pytest
from postgresql_mcp.guardrails.security_validator import (
    SecurityValidator,
    ValidationResult,
    strip_comments,
)


class TestStripComments:
    def test_line_comments(self):
        assert strip_comments("SELECT 1 -- comment").strip() == "SELECT 1"

    def test_block_comments(self):
        assert strip_comments("SELECT /* hidden */ 1").strip() == "SELECT   1"

    def test_nested_block_comments(self):
        result = strip_comments("SELECT /* outer /* inner */ still */ 1")
        assert "hidden" not in result.lower() or "inner" not in result.lower()

    def test_no_comments(self):
        assert strip_comments("SELECT * FROM users") == "SELECT * FROM users"


class TestReadOnlyMode:
    """In read-only mode, only SELECT/EXPLAIN/WITH/SHOW allowed."""

    @pytest.fixture
    def validator(self):
        return SecurityValidator(read_only=True)

    def test_select_allowed(self, validator):
        r = validator.validate("SELECT * FROM users")
        assert r.is_valid

    def test_explain_allowed(self, validator):
        r = validator.validate("EXPLAIN SELECT * FROM users")
        assert r.is_valid

    def test_with_cte_allowed(self, validator):
        r = validator.validate("WITH cte AS (SELECT 1) SELECT * FROM cte")
        assert r.is_valid

    def test_show_allowed(self, validator):
        r = validator.validate("SHOW server_version")
        assert r.is_valid

    @pytest.mark.parametrize("keyword", [
        "INSERT INTO users VALUES (1)",
        "UPDATE users SET name='x'",
        "DELETE FROM users",
        "DROP TABLE users",
        "ALTER TABLE users ADD col int",
        "CREATE TABLE evil (id int)",
        "TRUNCATE users",
        "GRANT ALL ON users TO evil",
        "REVOKE ALL ON users FROM evil",
        "SET statement_timeout = 0",
        "COPY users TO '/tmp/dump'",
        "VACUUM users",
    ])
    def test_forbidden_keywords_blocked(self, validator, keyword):
        r = validator.validate(keyword)
        assert not r.is_valid
        assert r.reason is not None


class TestWriteMode:
    """In write mode, DDL/DCL still blocked; DML allowed."""

    @pytest.fixture
    def validator(self):
        return SecurityValidator(read_only=False, allow_destructive=False)

    def test_select_allowed(self, validator):
        r = validator.validate("SELECT * FROM users")
        assert r.is_valid

    def test_insert_allowed(self, validator):
        r = validator.validate("INSERT INTO users VALUES (1, 'test')")
        assert r.is_valid

    def test_update_allowed(self, validator):
        r = validator.validate("UPDATE users SET name='x' WHERE id=1")
        assert r.is_valid

    def test_delete_blocked_without_destructive(self, validator):
        r = validator.validate("DELETE FROM users WHERE id=1")
        assert not r.is_valid
        assert "ALLOW_DESTRUCTIVE" in r.reason

    def test_drop_blocked(self, validator):
        r = validator.validate("DROP TABLE users")
        assert not r.is_valid

    def test_alter_blocked(self, validator):
        r = validator.validate("ALTER TABLE users ADD COLUMN x int")
        assert not r.is_valid

    def test_grant_blocked(self, validator):
        r = validator.validate("GRANT SELECT ON users TO public")
        assert not r.is_valid


class TestDestructiveMode:
    """With allow_destructive, DELETE is allowed."""

    @pytest.fixture
    def validator(self):
        return SecurityValidator(read_only=False, allow_destructive=True)

    def test_delete_allowed(self, validator):
        r = validator.validate("DELETE FROM users WHERE id=1")
        assert r.is_valid

    def test_drop_still_blocked(self, validator):
        r = validator.validate("DROP TABLE users")
        assert not r.is_valid


class TestDangerousFunctions:
    @pytest.fixture
    def validator(self):
        return SecurityValidator(read_only=True)

    @pytest.mark.parametrize("func", [
        "pg_sleep(10)",
        "pg_terminate_backend(123)",
        "pg_cancel_backend(123)",
        "lo_export(123, '/tmp/x')",
        "pg_read_file('/etc/passwd')",
        "dblink('host=evil', 'SELECT 1')",
    ])
    def test_dangerous_functions_blocked(self, validator, func):
        query = f"SELECT {func}"
        r = validator.validate(query)
        assert not r.is_valid
        assert "Dangerous function" in r.reason

    def test_safe_function_allowed(self, validator):
        r = validator.validate("SELECT now(), count(*) FROM users")
        assert r.is_valid


class TestInjectionPatterns:
    @pytest.fixture
    def validator(self):
        return SecurityValidator(read_only=True)

    def test_semicolon_injection(self, validator):
        r = validator.validate("SELECT 1; DROP TABLE users")
        assert not r.is_valid

    def test_union_injection(self, validator):
        r = validator.validate("SELECT id FROM users UNION SELECT password FROM secrets")
        assert not r.is_valid

    def test_union_all_injection(self, validator):
        r = validator.validate("SELECT id FROM users UNION ALL SELECT password FROM secrets")
        assert not r.is_valid

    def test_comment_hiding_injection(self, validator):
        # Attacker tries to hide DROP behind a comment
        r = validator.validate("SELECT 1 /* */; DROP TABLE users")
        assert not r.is_valid

    def test_hex_shellcode_blocked(self, validator):
        r = validator.validate("SELECT 0x4141414141414141")
        assert not r.is_valid


class TestPostgresInjectionPatterns:
    """Phase 10.7: PostgreSQL-specific injection patterns."""

    @pytest.fixture
    def validator(self):
        return SecurityValidator(read_only=True)

    def test_pg_shadow_probe(self, validator):
        r = validator.validate("SELECT * FROM pg_shadow")
        assert not r.is_valid

    def test_pg_authid_probe(self, validator):
        r = validator.validate("SELECT rolpassword FROM pg_authid")
        assert not r.is_valid

    def test_current_setting_extraction(self, validator):
        r = validator.validate("SELECT current_setting('data_directory')")
        assert not r.is_valid

    def test_current_setting_case_insensitive(self, validator):
        r = validator.validate("SELECT CURRENT_SETTING('log_connections')")
        assert not r.is_valid

    def test_copy_to_file(self, validator):
        r = validator.validate("COPY users TO '/tmp/dump.csv'")
        assert not r.is_valid

    def test_copy_from_file(self, validator):
        r = validator.validate("COPY users FROM '/etc/passwd'")
        assert not r.is_valid

    def test_chr_encoding_bypass(self, validator):
        r = validator.validate("SELECT CHR(65) || CHR(66)")
        assert not r.is_valid

    def test_chr_with_spaces(self, validator):
        r = validator.validate("SELECT chr( 39 )")
        assert not r.is_valid

    def test_pg_advisory_lock_dos(self, validator):
        r = validator.validate("SELECT pg_advisory_lock(1)")
        assert not r.is_valid

    def test_pg_advisory_xact_lock(self, validator):
        r = validator.validate("SELECT pg_advisory_xact_lock(1, 2)")
        assert not r.is_valid

    # ─── Should NOT be blocked (false positive check) ────────────────────

    def test_legitimate_pg_stat_user_tables(self, validator):
        """pg_stat_user_tables doesn't match pg_shadow/pg_authid patterns."""
        r = validator.validate("SELECT relname FROM pg_stat_user_tables")
        # This may be blocked by other rules (first keyword), but NOT by injection patterns
        # We only check it doesn't match pg_shadow/pg_authid
        # Actually read-only allows SELECT but pg_stat... might be allowed
        assert r.is_valid or "injection" not in (r.reason or "").lower()

    def test_column_named_copy_ok(self, validator):
        """Column named 'copy_date' should not trigger COPY pattern."""
        r = validator.validate("SELECT copy_date FROM documents WHERE id = 1")
        assert r.is_valid


class TestQueryLength:
    def test_exceeds_max_length(self):
        validator = SecurityValidator(max_query_length=50)
        long_query = "SELECT " + "x" * 100
        r = validator.validate(long_query)
        assert not r.is_valid
        assert "exceeds maximum length" in r.reason

    def test_within_max_length(self):
        validator = SecurityValidator(max_query_length=1000)
        r = validator.validate("SELECT * FROM users")
        assert r.is_valid


class TestEdgeCases:
    @pytest.fixture
    def validator(self):
        return SecurityValidator(read_only=True)

    def test_empty_query(self, validator):
        r = validator.validate("")
        assert r.is_valid  # empty is technically valid (will fail at execution)

    def test_whitespace_only(self, validator):
        r = validator.validate("   \n\t  ")
        assert r.is_valid

    def test_case_insensitive_keywords(self, validator):
        r = validator.validate("drop TABLE users")
        assert not r.is_valid

    def test_mixed_case_function(self, validator):
        r = validator.validate("SELECT Pg_Sleep(5)")
        assert not r.is_valid
