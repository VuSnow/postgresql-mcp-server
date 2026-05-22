"""Tests for BaseService — input validation and write policy enforcement."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from postgresql_mcp.services.postgresql.base import BaseService
from postgresql_mcp.services.connection_manager import ConnectionManager, ConnectionState
from postgresql_mcp.configs import ServerConfigs


@pytest.fixture
def configs_read_only():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
        READ_ONLY=True,
    )


@pytest.fixture
def configs_write_enabled():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
        READ_ONLY=False,
    )


@pytest.fixture
def configs_destructive_enabled():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
        READ_ONLY=False,
        ALLOW_DESTRUCTIVE=True,
    )


@pytest.fixture
def configs_with_allowlist():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
        READ_ONLY=False,
        WRITE_ALLOWLIST="public.users, analytics.*",
    )


def make_service(configs):
    manager = ConnectionManager(configs)
    return BaseService(manager, configs)


class TestValidateIdentifier:
    def test_valid_identifiers(self, configs_read_only):
        svc = make_service(configs_read_only)
        assert svc._validate_identifier("users", "table") == "users"
        assert svc._validate_identifier("_private", "column") == "_private"
        assert svc._validate_identifier("Table_123", "table") == "Table_123"

    def test_invalid_identifiers(self, configs_read_only):
        svc = make_service(configs_read_only)
        with pytest.raises(ValueError, match="Invalid table"):
            svc._validate_identifier("123abc", "table")

        with pytest.raises(ValueError, match="Invalid column"):
            svc._validate_identifier("has space", "column")

        with pytest.raises(ValueError, match="Invalid schema"):
            svc._validate_identifier("drop;--", "schema")

        with pytest.raises(ValueError, match="Invalid table"):
            svc._validate_identifier("", "table")

    def test_sql_injection_attempts(self, configs_read_only):
        svc = make_service(configs_read_only)
        with pytest.raises(ValueError):
            svc._validate_identifier("users; DROP TABLE users;--", "table")

        with pytest.raises(ValueError):
            svc._validate_identifier("table.name", "table")


class TestValidateTableName:
    def test_valid_table_name(self, configs_read_only):
        svc = make_service(configs_read_only)
        schema, table = svc._validate_table_name("orders", "public")
        assert schema == "public"
        assert table == "orders"

    def test_invalid_table_raises(self, configs_read_only):
        svc = make_service(configs_read_only)
        with pytest.raises(ValueError, match="Invalid table name"):
            svc._validate_table_name("bad table!", "public")

    def test_invalid_schema_raises(self, configs_read_only):
        svc = make_service(configs_read_only)
        with pytest.raises(ValueError, match="Invalid schema"):
            svc._validate_table_name("users", "bad-schema")


class TestCheckWriteAllowed:
    def test_raises_when_read_only(self, configs_read_only):
        svc = make_service(configs_read_only)
        with pytest.raises(PermissionError, match="Write operations are disabled"):
            svc._check_write_allowed()

    def test_passes_when_write_enabled(self, configs_write_enabled):
        svc = make_service(configs_write_enabled)
        svc._check_write_allowed()  # should not raise


class TestCheckDestructiveAllowed:
    def test_raises_when_read_only(self, configs_read_only):
        svc = make_service(configs_read_only)
        with pytest.raises(PermissionError, match="Write operations are disabled"):
            svc._check_destructive_allowed()

    def test_raises_when_destructive_disabled(self, configs_write_enabled):
        svc = make_service(configs_write_enabled)
        with pytest.raises(PermissionError, match="Destructive operations are disabled"):
            svc._check_destructive_allowed()

    def test_passes_when_destructive_enabled(self, configs_destructive_enabled):
        svc = make_service(configs_destructive_enabled)
        svc._check_destructive_allowed()  # should not raise


class TestCheckWriteTarget:
    def test_no_allowlist_allows_all(self, configs_write_enabled):
        svc = make_service(configs_write_enabled)
        svc._check_write_target("public", "anything")  # should not raise

    def test_exact_match(self, configs_with_allowlist):
        svc = make_service(configs_with_allowlist)
        svc._check_write_target("public", "users")  # should not raise

    def test_wildcard_schema_match(self, configs_with_allowlist):
        svc = make_service(configs_with_allowlist)
        svc._check_write_target("analytics", "events")  # matches analytics.*

    def test_denied_when_not_in_allowlist(self, configs_with_allowlist):
        svc = make_service(configs_with_allowlist)
        with pytest.raises(PermissionError, match="not allowed"):
            svc._check_write_target("public", "orders")

    def test_star_allows_all(self, configs_write_enabled):
        configs_write_enabled.write_allowlist = "*"
        svc = make_service(configs_write_enabled)
        svc._check_write_target("any_schema", "any_table")  # should not raise

    def test_raises_when_read_only_regardless_of_allowlist(self, configs_read_only):
        configs_read_only.write_allowlist = "public.*"
        svc = make_service(configs_read_only)
        with pytest.raises(PermissionError, match="Write operations are disabled"):
            svc._check_write_target("public", "users")


class TestEnsureConnected:
    @pytest.mark.asyncio
    async def test_delegates_to_connection_manager(self, configs_read_only):
        svc = make_service(configs_read_only)
        with patch.object(svc._conn_mgr, "ensure_connected", new_callable=AsyncMock) as mock:
            await svc.ensure_connected()
        mock.assert_called_once()
