"""
Phase 10.0 — Security Profile tests.

Tests for SECURITY_PROFILE config, effective property resolution,
and profile-based validation constraints.
"""

import os
import pytest
from postgresql_mcp.configs import ServerConfigs, SecurityProfile


# ─── Helper ─────────────────────────────────────────────────────────────────


def make_configs(**overrides):
    """Create ServerConfigs with test defaults + overrides."""
    env = {
        "POSTGRESQL_CONNECTION_STRING": "postgresql://test:test@localhost:5432/testdb",
        **overrides,
    }
    return ServerConfigs(**env)


# ─── Security Profile Enum ──────────────────────────────────────────────────


class TestSecurityProfileEnum:
    """SecurityProfile enum values and parsing."""

    def test_general_profile(self):
        assert SecurityProfile("general") == SecurityProfile.GENERAL

    def test_text2sql_profile(self):
        assert SecurityProfile("text2sql") == SecurityProfile.TEXT2SQL

    def test_sensitive_profile(self):
        assert SecurityProfile("sensitive") == SecurityProfile.SENSITIVE

    def test_invalid_profile_raises(self):
        with pytest.raises(ValueError):
            SecurityProfile("invalid")


# ─── Profile Defaults ───────────────────────────────────────────────────────


class TestProfileDefaults:
    """Default config values for each profile."""

    def test_general_profile_defaults(self):
        cfg = make_configs(SECURITY_PROFILE="general")
        assert cfg.security_profile == SecurityProfile.GENERAL
        assert cfg.effective_column_policy_mode == "permissive"
        assert cfg.effective_metadata_filtering is False
        assert cfg.effective_function_control == "blacklist"

    def test_text2sql_profile_defaults(self):
        cfg = make_configs(SECURITY_PROFILE="text2sql")
        assert cfg.security_profile == SecurityProfile.TEXT2SQL
        assert cfg.effective_column_policy_mode == "strict"
        assert cfg.effective_metadata_filtering is True
        assert cfg.effective_function_control == "allowlist"

    def test_sensitive_profile_defaults(self):
        cfg = make_configs(
            SECURITY_PROFILE="sensitive",
            COLUMN_POLICY='{"public.users": {"allowed_columns": ["id"]}}',
        )
        assert cfg.security_profile == SecurityProfile.SENSITIVE
        assert cfg.effective_column_policy_mode == "strict"
        assert cfg.effective_metadata_filtering is True
        assert cfg.effective_function_control == "allowlist"

    def test_default_profile_is_general(self):
        cfg = make_configs()
        assert cfg.security_profile == SecurityProfile.GENERAL


# ─── Sensitive Profile Validation ────────────────────────────────────────────


class TestSensitiveProfileValidation:
    """Sensitive profile requires policy file."""

    def test_sensitive_without_policy_raises(self):
        with pytest.raises(ValueError, match="requires COLUMN_POLICY"):
            make_configs(SECURITY_PROFILE="sensitive")

    def test_sensitive_with_column_policy_ok(self):
        cfg = make_configs(
            SECURITY_PROFILE="sensitive",
            COLUMN_POLICY='{"public.users": {"allowed_columns": ["id"]}}',
        )
        assert cfg.security_profile == SecurityProfile.SENSITIVE

    def test_sensitive_with_policy_file_ok(self):
        cfg = make_configs(
            SECURITY_PROFILE="sensitive",
            COLUMN_POLICY_FILE="/etc/mcp/policy.json",
        )
        assert cfg.security_profile == SecurityProfile.SENSITIVE

    def test_text2sql_without_policy_ok(self):
        """text2sql recommends but does not require policy."""
        cfg = make_configs(SECURITY_PROFILE="text2sql")
        assert cfg.security_profile == SecurityProfile.TEXT2SQL


# ─── Explicit Override ───────────────────────────────────────────────────────


class TestExplicitOverride:
    """Explicit config overrides profile defaults."""

    def test_override_column_policy_mode(self):
        """Explicit COLUMN_POLICY_MODE overrides profile default."""
        cfg = make_configs(
            SECURITY_PROFILE="general",
            COLUMN_POLICY_MODE="strict",
        )
        assert cfg.effective_column_policy_mode == "strict"

    def test_override_strict_to_permissive(self):
        """Can override text2sql strict to permissive."""
        cfg = make_configs(
            SECURITY_PROFILE="text2sql",
            COLUMN_POLICY_MODE="permissive",
        )
        assert cfg.effective_column_policy_mode == "permissive"

    def test_explicit_allowed_functions_forces_allowlist(self):
        """Setting ALLOWED_FUNCTIONS forces allowlist regardless of profile."""
        cfg = make_configs(
            SECURITY_PROFILE="general",
            ALLOWED_FUNCTIONS='["count","sum"]',
        )
        assert cfg.effective_function_control == "allowlist"


# ─── New Config Fields ───────────────────────────────────────────────────────


class TestNewConfigFields:
    """Phase 10 config fields have correct defaults."""

    def test_block_select_star_default(self):
        cfg = make_configs()
        assert cfg.block_select_star is True

    def test_block_subqueries_default(self):
        cfg = make_configs()
        assert cfg.block_subqueries is True

    def test_allow_cte_default(self):
        cfg = make_configs()
        assert cfg.allow_cte is False

    def test_allow_set_operations_default(self):
        cfg = make_configs()
        assert cfg.allow_set_operations is False

    def test_allow_recursive_cte_default(self):
        cfg = make_configs()
        assert cfg.allow_recursive_cte is False

    def test_enable_write_tools_default(self):
        cfg = make_configs()
        assert cfg.enable_write_tools is False

    def test_max_offset_default(self):
        cfg = make_configs()
        assert cfg.max_offset == 10000

    def test_max_result_rows_default(self):
        cfg = make_configs()
        assert cfg.max_result_rows == 100

    def test_max_result_bytes_default(self):
        cfg = make_configs()
        assert cfg.max_result_bytes == 1048576

    def test_max_cell_length_default(self):
        cfg = make_configs()
        assert cfg.max_cell_length == 4096

    def test_max_columns_returned_default(self):
        cfg = make_configs()
        assert cfg.max_columns_returned == 50

    def test_default_schema(self):
        cfg = make_configs()
        assert cfg.default_schema == "public"

    def test_user_context_variable_default(self):
        cfg = make_configs()
        assert cfg.user_context_variable is None

    def test_custom_max_offset(self):
        cfg = make_configs(MAX_OFFSET="5000")
        assert cfg.max_offset == 5000

    def test_custom_security_fields(self):
        cfg = make_configs(
            BLOCK_SELECT_STAR="false",
            BLOCK_SUBQUERIES="false",
            ALLOW_CTE="true",
            MAX_RESULT_ROWS="50",
            DEFAULT_SCHEMA="analytics",
        )
        assert cfg.block_select_star is False
        assert cfg.block_subqueries is False
        assert cfg.allow_cte is True
        assert cfg.max_result_rows == 50
        assert cfg.default_schema == "analytics"
