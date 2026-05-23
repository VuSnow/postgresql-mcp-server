"""
Phase 10.15 — Metadata Tools Policy Filter tests.
"""

import pytest

from postgresql_mcp.guardrails.metadata_filter import MetadataFilter
from postgresql_mcp.guardrails.models import ColumnPolicyConfig, TablePolicy


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def policy():
    """Sample policy with two tables."""
    return ColumnPolicyConfig(
        policies={
            "users": TablePolicy(
                allowed_columns=["id", "name", "email", "department"],
                sampleable_columns=["department"],
            ),
            "orders": TablePolicy(
                allowed_columns=["id", "user_id", "amount", "status"],
                sampleable_columns=["status"],
            ),
        },
        mode="strict",
    )


@pytest.fixture
def active_filter(policy):
    return MetadataFilter(policy=policy, filtering_enabled=True)


@pytest.fixture
def inactive_filter(policy):
    return MetadataFilter(policy=policy, filtering_enabled=False)


@pytest.fixture
def no_policy_filter():
    return MetadataFilter(policy=None, filtering_enabled=True)


# ═══════════════════════════════════════════════════════════════════════════
# is_active
# ═══════════════════════════════════════════════════════════════════════════


class TestIsActive:
    def test_active_when_enabled_and_policy(self, active_filter):
        assert active_filter.is_active is True

    def test_inactive_when_disabled(self, inactive_filter):
        assert inactive_filter.is_active is False

    def test_inactive_when_no_policy(self, no_policy_filter):
        assert no_policy_filter.is_active is False


# ═══════════════════════════════════════════════════════════════════════════
# filter_tables
# ═══════════════════════════════════════════════════════════════════════════


class TestFilterTables:
    def test_filters_to_policy_tables(self, active_filter):
        tables = [
            {"table_name": "users", "table_type": "BASE TABLE", "estimated_row_count": 100},
            {"table_name": "orders", "table_type": "BASE TABLE", "estimated_row_count": 500},
            {"table_name": "secrets", "table_type": "BASE TABLE", "estimated_row_count": 10},
            {"table_name": "internal_logs", "table_type": "BASE TABLE", "estimated_row_count": 1000},
        ]
        result = active_filter.filter_tables(tables)
        names = [t["table_name"] for t in result]
        assert names == ["users", "orders"]

    def test_no_filter_when_inactive(self, inactive_filter):
        tables = [
            {"table_name": "users"},
            {"table_name": "secrets"},
        ]
        result = inactive_filter.filter_tables(tables)
        assert len(result) == 2

    def test_empty_result_when_no_match(self, active_filter):
        tables = [{"table_name": "unknown_table"}]
        result = active_filter.filter_tables(tables)
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════
# check_table_access
# ═══════════════════════════════════════════════════════════════════════════


class TestCheckTableAccess:
    def test_allowed_table(self, active_filter):
        r = active_filter.check_table_access("users")
        assert r.is_blocked is False

    def test_blocked_table(self, active_filter):
        r = active_filter.check_table_access("secrets")
        assert r.is_blocked is True
        assert "not in the column policy" in r.reason

    def test_no_check_when_inactive(self, inactive_filter):
        r = inactive_filter.check_table_access("secrets")
        assert r.is_blocked is False


# ═══════════════════════════════════════════════════════════════════════════
# filter_columns
# ═══════════════════════════════════════════════════════════════════════════


class TestFilterColumns:
    def test_filters_to_allowed_columns(self, active_filter):
        columns = [
            {"column_name": "id", "udt_name": "int4"},
            {"column_name": "name", "udt_name": "varchar"},
            {"column_name": "password_hash", "udt_name": "varchar"},
            {"column_name": "email", "udt_name": "varchar"},
            {"column_name": "ssn", "udt_name": "varchar"},
            {"column_name": "department", "udt_name": "varchar"},
        ]
        result = active_filter.filter_columns(columns, "users")
        names = [c["column_name"] for c in result]
        assert set(names) == {"id", "name", "email", "department"}

    def test_no_filter_when_inactive(self, inactive_filter):
        columns = [
            {"column_name": "id"},
            {"column_name": "password_hash"},
        ]
        result = inactive_filter.filter_columns(columns, "users")
        assert len(result) == 2

    def test_empty_for_unknown_table(self, active_filter):
        columns = [{"column_name": "id"}]
        result = active_filter.filter_columns(columns, "secrets")
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════
# check_column_values_access
# ═══════════════════════════════════════════════════════════════════════════


class TestCheckColumnValuesAccess:
    def test_sampleable_column_allowed(self, active_filter):
        r = active_filter.check_column_values_access("users", "department")
        assert r.is_blocked is False

    def test_non_sampleable_column_blocked(self, active_filter):
        """email is in allowed_columns but NOT in sampleable_columns."""
        r = active_filter.check_column_values_access("users", "email")
        assert r.is_blocked is True
        assert "sampleable_columns" in r.reason

    def test_unknown_table_blocked(self, active_filter):
        r = active_filter.check_column_values_access("secrets", "id")
        assert r.is_blocked is True

    def test_no_check_when_inactive(self, inactive_filter):
        r = inactive_filter.check_column_values_access("secrets", "password")
        assert r.is_blocked is False

    def test_table_with_no_sampleable_columns(self):
        """Table in policy but no sampleable_columns defined."""
        policy = ColumnPolicyConfig(
            policies={
                "logs": TablePolicy(
                    allowed_columns=["id", "message"],
                    sampleable_columns=[],
                ),
            },
            mode="strict",
        )
        f = MetadataFilter(policy=policy, filtering_enabled=True)
        r = f.check_column_values_access("logs", "message")
        assert r.is_blocked is True
        assert "no sampleable_columns" in r.reason


# ═══════════════════════════════════════════════════════════════════════════
# Schema-qualified table names
# ═══════════════════════════════════════════════════════════════════════════


class TestSchemaQualified:
    def test_schema_qualified_policy_lookup(self):
        policy = ColumnPolicyConfig(
            policies={
                "analytics.events": TablePolicy(
                    allowed_columns=["id", "event_type", "created_at"],
                    sampleable_columns=["event_type"],
                ),
            },
            mode="strict",
        )
        f = MetadataFilter(policy=policy, filtering_enabled=True)

        # Access with schema
        r = f.check_table_access("events", "analytics")
        assert r.is_blocked is False

        # Column values
        r = f.check_column_values_access("events", "event_type", "analytics")
        assert r.is_blocked is False

        # Non-sampleable
        r = f.check_column_values_access("events", "id", "analytics")
        assert r.is_blocked is True


# ═══════════════════════════════════════════════════════════════════════════
# Config integration
# ═══════════════════════════════════════════════════════════════════════════


class TestConfigIntegration:
    def test_text2sql_enables_filtering(self):
        from postgresql_mcp.configs import ServerConfigs

        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            SECURITY_PROFILE="text2sql",
        )
        assert configs.effective_metadata_filtering is True

    def test_sensitive_enables_filtering(self):
        from postgresql_mcp.configs import ServerConfigs

        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            SECURITY_PROFILE="sensitive",
            COLUMN_POLICY='{"users": {"allowed_columns": ["id"]}}',
        )
        assert configs.effective_metadata_filtering is True

    def test_general_disables_filtering(self):
        from postgresql_mcp.configs import ServerConfigs

        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            SECURITY_PROFILE="general",
        )
        assert configs.effective_metadata_filtering is False
