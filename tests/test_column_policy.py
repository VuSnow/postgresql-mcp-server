"""
Phase 10.4 — Column Policy Enforcement tests.

Tests for per-table column allowlisting, required filters,
aggregate exceptions, GROUP BY validation, strict/permissive modes.
"""

import pytest
from postgresql_mcp.guardrails.column_policy import (
    load_column_policy,
    check_column_policy,
    ColumnPolicyConfig,
    TablePolicy,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────


USERS_POLICY_JSON = """{
    "public.users": {
        "allowed_columns": ["id", "full_name", "department", "created_at"],
        "sampleable_columns": ["department"],
        "required_filter_columns": ["id", "full_name"],
        "allow_aggregates_without_filter": true,
        "group_by_columns": ["department", "created_at"],
        "max_rows": 20
    },
    "public.transactions": {
        "allowed_columns": ["id", "amount", "status", "created_at"],
        "sampleable_columns": ["status"],
        "required_filter_columns": ["id", "account_id"],
        "allow_aggregates_without_filter": true,
        "group_by_columns": ["status", "created_at"],
        "max_rows": 100
    }
}"""


def make_policy(mode: str = "strict") -> ColumnPolicyConfig:
    return load_column_policy(policy_json=USERS_POLICY_JSON, mode=mode)


# ─── Policy Loading ─────────────────────────────────────────────────────────


class TestPolicyLoading:
    """load_column_policy correctly parses JSON."""

    def test_load_from_json(self):
        policy = load_column_policy(policy_json=USERS_POLICY_JSON)
        assert "public.users" in policy.policies
        assert "public.transactions" in policy.policies

    def test_table_policy_fields(self):
        policy = load_column_policy(policy_json=USERS_POLICY_JSON)
        users = policy.policies["public.users"]
        assert users.allowed_columns == ["id", "full_name", "department", "created_at"]
        assert users.sampleable_columns == ["department"]
        assert users.required_filter_columns == ["id", "full_name"]
        assert users.allow_aggregates_without_filter is True
        assert users.group_by_columns == ["department", "created_at"]
        assert users.max_rows == 20

    def test_unqualified_table_normalized(self):
        policy = load_column_policy(policy_json='{"users": {"allowed_columns": ["id"]}}')
        assert "public.users" in policy.policies

    def test_empty_policy(self):
        policy = load_column_policy()
        assert policy.policies == {}

    def test_mode_setting(self):
        policy = load_column_policy(policy_json=USERS_POLICY_JSON, mode="strict")
        assert policy.mode == "strict"


# ─── Column Allowlist (must BLOCK) ──────────────────────────────────────────


class TestColumnBlocked:
    """Queries referencing disallowed columns are blocked."""

    def test_block_sensitive_column(self):
        policy = make_policy()
        result = check_column_policy("SELECT password_hash FROM users WHERE id = 1", policy)
        assert result.is_blocked is True
        assert "password_hash" in result.reason

    def test_block_column_with_alias(self):
        """Aliased column is still checked by source name."""
        policy = make_policy()
        result = check_column_policy(
            "SELECT password_hash AS p FROM users WHERE id = 1", policy
        )
        assert result.is_blocked is True

    def test_block_email_column(self):
        policy = make_policy()
        result = check_column_policy("SELECT email FROM users WHERE id = 1", policy)
        assert result.is_blocked is True

    def test_block_all_disallowed(self):
        policy = make_policy()
        result = check_column_policy(
            "SELECT id, ssn FROM users WHERE id = 1", policy
        )
        assert result.is_blocked is True
        assert "ssn" in result.reason


# ─── Column Allowlist (must PASS) ───────────────────────────────────────────


class TestColumnAllowed:
    """Queries with allowed columns pass."""

    def test_allowed_single_column(self):
        policy = make_policy()
        result = check_column_policy("SELECT id FROM users WHERE id = 1 LIMIT 1", policy)
        assert result.is_blocked is False

    def test_allowed_multiple_columns(self):
        policy = make_policy()
        result = check_column_policy(
            "SELECT id, full_name, department FROM users WHERE id = 1 LIMIT 5", policy
        )
        assert result.is_blocked is False

    def test_allowed_with_table_qualification(self):
        policy = make_policy()
        result = check_column_policy(
            "SELECT users.id, users.full_name FROM users WHERE users.id = 1 LIMIT 1",
            policy,
        )
        assert result.is_blocked is False


# ─── Strict Mode (table not in policy) ──────────────────────────────────────


class TestStrictMode:
    """In strict mode, tables not in policy are rejected."""

    def test_strict_blocks_unknown_table(self):
        policy = make_policy(mode="strict")
        result = check_column_policy("SELECT id FROM secret_table WHERE id = 1", policy)
        assert result.is_blocked is True
        assert "not in the column policy" in result.reason

    def test_permissive_allows_unknown_table(self):
        policy = make_policy(mode="permissive")
        result = check_column_policy("SELECT id FROM secret_table WHERE id = 1", policy)
        assert result.is_blocked is False


# ─── Required Filter Columns ────────────────────────────────────────────────


class TestRequiredFilter:
    """Queries must have WHERE with required filter column."""

    def test_block_no_where(self):
        """Query without WHERE on required filter is blocked."""
        policy = make_policy()
        result = check_column_policy("SELECT id FROM users LIMIT 5", policy)
        assert result.is_blocked is True
        assert "requires a WHERE filter" in result.reason

    def test_block_wrong_filter_column(self):
        """WHERE on non-required column is blocked."""
        policy = make_policy()
        result = check_column_policy(
            "SELECT id FROM users WHERE department = 'eng' LIMIT 5", policy
        )
        assert result.is_blocked is True

    def test_pass_with_id_filter(self):
        policy = make_policy()
        result = check_column_policy(
            "SELECT id, full_name FROM users WHERE id = 42 LIMIT 1", policy
        )
        assert result.is_blocked is False

    def test_pass_with_name_filter(self):
        policy = make_policy()
        result = check_column_policy(
            "SELECT id FROM users WHERE full_name = 'Alice' LIMIT 1", policy
        )
        assert result.is_blocked is False


# ─── Aggregate Exception ────────────────────────────────────────────────────


class TestAggregateException:
    """Pure aggregate queries skip required_filter_columns check."""

    def test_count_star_no_filter_passes(self):
        """COUNT(*) without WHERE passes (pure aggregate)."""
        policy = make_policy()
        result = check_column_policy("SELECT COUNT(*) FROM users", policy)
        assert result.is_blocked is False

    def test_avg_no_filter_passes(self):
        policy = make_policy()
        result = check_column_policy(
            "SELECT AVG(amount) FROM transactions", policy
        )
        assert result.is_blocked is False

    def test_group_by_allowed_dimension(self):
        """GROUP BY on allowed dimension column passes."""
        policy = make_policy()
        result = check_column_policy(
            "SELECT department, COUNT(*) FROM users GROUP BY department LIMIT 20",
            policy,
        )
        assert result.is_blocked is False

    def test_group_by_disallowed_column(self):
        """GROUP BY on non-dimension column is blocked."""
        policy = make_policy()
        result = check_column_policy(
            "SELECT id, COUNT(*) FROM users GROUP BY id LIMIT 20", policy
        )
        assert result.is_blocked is True
        assert "GROUP BY" in result.reason

    def test_non_pure_aggregate_needs_filter(self):
        """SELECT with row-level column + aggregate is not pure aggregate."""
        policy = make_policy()
        result = check_column_policy(
            "SELECT id, COUNT(*) FROM users GROUP BY id LIMIT 20", policy
        )
        assert result.is_blocked is True


# ─── Max Rows ───────────────────────────────────────────────────────────────


class TestMaxRows:
    """Per-table max_rows enforcement."""

    def test_limit_within_max_rows(self):
        policy = make_policy()
        result = check_column_policy(
            "SELECT id FROM users WHERE id = 1 LIMIT 5", policy
        )
        assert result.is_blocked is False

    def test_limit_exceeds_max_rows(self):
        """LIMIT > max_rows is rejected."""
        policy = make_policy()
        result = check_column_policy(
            "SELECT id FROM users WHERE id = 1 LIMIT 100", policy
        )
        assert result.is_blocked is True
        assert "max_rows" in result.reason

    def test_limit_exactly_max_rows(self):
        policy = make_policy()
        result = check_column_policy(
            "SELECT id FROM users WHERE id = 1 LIMIT 20", policy
        )
        assert result.is_blocked is False


# ─── No Policy Configured ───────────────────────────────────────────────────


class TestNoPolicyConfigured:
    """When no policy is set, all queries pass."""

    def test_no_policy_allows_everything(self):
        policy = load_column_policy()
        result = check_column_policy("SELECT * FROM users", policy)
        assert result.is_blocked is False
