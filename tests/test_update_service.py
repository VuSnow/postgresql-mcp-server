"""Tests for UpdateService — write policy, validation, WHERE enforcement."""

import pytest
from unittest.mock import AsyncMock

from postgresql_mcp.services.postgresql.update import UpdateService
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
        WRITE_ALLOWLIST="public.users",
    )


def _make_service(configs):
    from postgresql_mcp.services.connection_manager import ConnectionManager
    cm = ConnectionManager(configs)
    svc = UpdateService(cm, configs)
    svc.ensure_connected = AsyncMock()
    cm._state = "connected"
    cm._client.update = AsyncMock(return_value=3)
    return svc


class TestUpdateServicePolicy:
    @pytest.mark.asyncio
    async def test_update_blocked_read_only(self, configs_read_only):
        svc = _make_service(configs_read_only)
        with pytest.raises(PermissionError, match="Write operations are disabled"):
            await svc.update("users", {"status": "active"}, "id = $2", [1])

    @pytest.mark.asyncio
    async def test_update_blocked_allowlist(self, configs_with_allowlist):
        svc = _make_service(configs_with_allowlist)
        with pytest.raises(PermissionError, match="not allowed"):
            await svc.update("secret_table", {"x": 1}, "id = $2", [1])

    @pytest.mark.asyncio
    async def test_update_allowed_by_allowlist(self, configs_with_allowlist):
        svc = _make_service(configs_with_allowlist)
        result = await svc.update("users", {"status": "active"}, "id = $2", [1])
        assert "Updated 3 row(s)" in result


class TestUpdateServiceValidation:
    @pytest.mark.asyncio
    async def test_empty_set_data_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="SET data cannot be empty"):
            await svc.update("users", {}, "id = $1", [1])

    @pytest.mark.asyncio
    async def test_empty_where_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="WHERE clause is required"):
            await svc.update("users", {"status": "active"}, "", [])

    @pytest.mark.asyncio
    async def test_whitespace_where_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="WHERE clause is required"):
            await svc.update("users", {"status": "active"}, "   ", [])

    @pytest.mark.asyncio
    async def test_invalid_column_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="Invalid column"):
            await svc.update("users", {"bad-col!": "x"}, "id = $2", [1])

    @pytest.mark.asyncio
    async def test_invalid_table_raises(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        with pytest.raises(ValueError, match="Invalid table"):
            await svc.update("bad-table!", {"x": 1}, "id = $2", [1])


class TestUpdateServiceSuccess:
    @pytest.mark.asyncio
    async def test_update_success(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        result = await svc.update("users", {"name": "Bob", "age": 30}, "id = $3", [42])
        assert "Updated 3 row(s)" in result
        svc._conn_mgr._client.update.assert_called_once_with(
            "public", "users", ["name", "age"], ["Bob", 30], "id = $3", [42]
        )

    @pytest.mark.asyncio
    async def test_update_no_where_values(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        result = await svc.update("users", {"active": True}, "status = 'pending'")
        assert "Updated 3 row(s)" in result
        svc._conn_mgr._client.update.assert_called_once_with(
            "public", "users", ["active"], [True], "status = 'pending'", []
        )

    @pytest.mark.asyncio
    async def test_update_custom_schema(self, configs_write_enabled):
        svc = _make_service(configs_write_enabled)
        result = await svc.update("users", {"x": 1}, "id = $2", [1], schema="myschema")
        assert "myschema.users" in result
