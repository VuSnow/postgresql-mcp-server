"""Tests for CreateService — write policy, validation, delegation."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from postgresql_mcp.services.postgresql.create import CreateService
from postgresql_mcp.configs import ServerConfigs


@pytest.fixture
def configs_write_enabled():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
        READ_ONLY=False,
    )


@pytest.fixture
def configs_read_only():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
        READ_ONLY=True,
    )


@pytest.fixture
def configs_with_allowlist():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
        READ_ONLY=False,
        WRITE_ALLOWLIST="public.users,public.orders",
    )


def _make_service(configs):
    from postgresql_mcp.services.connection_manager import ConnectionManager
    cm = ConnectionManager(configs)
    svc = CreateService(cm, configs)
    svc.ensure_connected = AsyncMock()
    cm._state = "connected"
    cm._client.insert_one = AsyncMock(return_value={"id": 1, "name": "Alice"})
    cm._client.insert_many = AsyncMock(return_value=2)
    return svc


class TestCreateServicePolicy:
    @pytest.mark.asyncio
    async def test_insert_one_blocked_read_only(self, configs_read_only):
        svc = _make_service(configs_read_only)
        with pytest.raises(PermissionError, match="Write operations are disabled"):
            await svc.insert_one("users", {"name": "Alice"})

    @pytest.mark.asyncio
    async def test_insert_one_blocked_allowlist(self, configs_with_allowlist):
        svc = _make_service(configs_with_allowlist)
        with pytest.raises(PermissionError, match="not allowed"):
            await svc.insert_one("secret_table", {"name": "Alice"})

    @pytest.mark.asyncio
    async def test_insert_one_allowed_by_allowlist(self, configs_with_allowlist):
        svc = _make_service(configs_with_allowlist)
        result = await svc.insert_one("users", {"name": "Alice"})
        assert "Inserted 1 row" in result

    @pytest.mark.asyncio
    async def test_insert_many_blocked_read_only(self, configs_read_only):
        svc = _make_service(configs_read_only)
        with pytest.raises(PermissionError):
            await svc.insert_many("users", ["name"], [["Alice"]])


class TestCreateServiceValidation:
    @pytest.mark.asyncio
    async def test_empty_data_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="Data cannot be empty"):
            await svc.insert_one("users", {})

    @pytest.mark.asyncio
    async def test_invalid_column_name_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="Invalid column"):
            await svc.insert_one("users", {"bad-col!": "value"})

    @pytest.mark.asyncio
    async def test_invalid_table_name_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="Invalid table"):
            await svc.insert_one("bad-table!", {"name": "Alice"})

    @pytest.mark.asyncio
    async def test_empty_columns_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="Columns list cannot be empty"):
            await svc.insert_many("users", [], [["Alice"]])

    @pytest.mark.asyncio
    async def test_empty_rows_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="Rows list cannot be empty"):
            await svc.insert_many("users", ["name"], [])

    @pytest.mark.asyncio
    async def test_row_length_mismatch_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="Row 0 has 2 values, expected 1"):
            await svc.insert_many("users", ["name"], [["Alice", "extra"]])


class TestCreateServiceSuccess:
    @pytest.mark.asyncio
    async def test_insert_one_success(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        result = await svc.insert_one("users", {"name": "Alice", "age": 30})
        assert "Inserted 1 row" in result
        assert "id: 1" in result
        svc._conn_mgr._client.insert_one.assert_called_once_with(
            "public", "users", ["name", "age"], ["Alice", 30]
        )

    @pytest.mark.asyncio
    async def test_insert_many_success(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        result = await svc.insert_many("users", ["name", "age"], [["Alice", 30], ["Bob", 25]])
        assert "Inserted 2 row(s)" in result
        svc._conn_mgr._client.insert_many.assert_called_once_with(
            "public", "users", ["name", "age"], [["Alice", 30], ["Bob", 25]]
        )

    @pytest.mark.asyncio
    async def test_insert_one_custom_schema(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        result = await svc.insert_one("users", {"name": "Alice"}, schema="myschema")
        assert "myschema.users" in result
