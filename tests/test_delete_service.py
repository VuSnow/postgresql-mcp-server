"""Tests for DeleteService — destructive policy, WHERE enforcement, truncate gating."""

import pytest
from unittest.mock import AsyncMock

from postgresql_mcp.services.postgresql.delete import DeleteService
from postgresql_mcp.configs import ServerConfigs


@pytest.fixture
def configs_destructive():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
        READ_ONLY=False,
        ALLOW_DESTRUCTIVE=True,
    )


@pytest.fixture
def configs_write_only():
    """Write enabled but destructive disabled."""
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
        READ_ONLY=False,
        ALLOW_DESTRUCTIVE=False,
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
        ALLOW_DESTRUCTIVE=True,
        WRITE_ALLOWLIST="public.users,public.orders",
    )


def _make_service(configs):
    from postgresql_mcp.services.connection_manager import ConnectionManager
    cm = ConnectionManager(configs)
    svc = DeleteService(cm, configs)
    svc.ensure_connected = AsyncMock()
    cm._state = "connected"
    cm._client.delete = AsyncMock(return_value=5)
    cm._client.truncate = AsyncMock()
    return svc


class TestDeleteServicePolicy:
    @pytest.mark.asyncio
    async def test_delete_blocked_read_only(self, configs_read_only):
        svc = _make_service(configs_read_only)
        with pytest.raises(PermissionError, match="Write operations are disabled"):
            await svc.delete("users", "id = $1", [1])

    @pytest.mark.asyncio
    async def test_delete_blocked_destructive_disabled(self, configs_write_only):
        svc = _make_service(configs_write_only)
        with pytest.raises(PermissionError, match="Destructive operations are disabled"):
            await svc.delete("users", "id = $1", [1])

    @pytest.mark.asyncio
    async def test_delete_blocked_allowlist(self, configs_with_allowlist):
        svc = _make_service(configs_with_allowlist)
        with pytest.raises(PermissionError, match="not allowed"):
            await svc.delete("secret_table", "id = $1", [1])

    @pytest.mark.asyncio
    async def test_delete_allowed_by_allowlist(self, configs_with_allowlist):
        svc = _make_service(configs_with_allowlist)
        result = await svc.delete("users", "id = $1", [1])
        assert "Deleted 5 row(s)" in result

    @pytest.mark.asyncio
    async def test_truncate_blocked_read_only(self, configs_read_only):
        svc = _make_service(configs_read_only)
        with pytest.raises(PermissionError, match="Write operations are disabled"):
            await svc.truncate_table("users")

    @pytest.mark.asyncio
    async def test_truncate_blocked_destructive_disabled(self, configs_write_only):
        svc = _make_service(configs_write_only)
        with pytest.raises(PermissionError, match="Destructive operations are disabled"):
            await svc.truncate_table("users")

    @pytest.mark.asyncio
    async def test_truncate_blocked_allowlist(self, configs_with_allowlist):
        svc = _make_service(configs_with_allowlist)
        with pytest.raises(PermissionError, match="not allowed"):
            await svc.truncate_table("secret_table")

    @pytest.mark.asyncio
    async def test_truncate_allowed(self, configs_destructive):
        svc = _make_service(configs_destructive)
        result = await svc.truncate_table("users")
        assert "Truncated" in result


class TestDeleteServiceValidation:
    @pytest.mark.asyncio
    async def test_empty_where_raises(self, configs_destructive):
        svc = _make_service(configs_destructive)
        with pytest.raises(ValueError, match="WHERE clause is required"):
            await svc.delete("users", "", [])

    @pytest.mark.asyncio
    async def test_whitespace_where_raises(self, configs_destructive):
        svc = _make_service(configs_destructive)
        with pytest.raises(ValueError, match="WHERE clause is required"):
            await svc.delete("users", "   ", [])

    @pytest.mark.asyncio
    async def test_invalid_table_raises(self, configs_destructive):
        svc = _make_service(configs_destructive)
        with pytest.raises(ValueError, match="Invalid table"):
            await svc.delete("bad-table!", "id = $1", [1])

    @pytest.mark.asyncio
    async def test_truncate_invalid_table_raises(self, configs_destructive):
        svc = _make_service(configs_destructive)
        with pytest.raises(ValueError, match="Invalid table"):
            await svc.truncate_table("bad-table!")


class TestDeleteServiceSuccess:
    @pytest.mark.asyncio
    async def test_delete_success(self, configs_destructive):
        svc = _make_service(configs_destructive)
        result = await svc.delete("users", "id = $1", [42])
        assert "Deleted 5 row(s)" in result
        assert "public.users" in result
        svc._conn_mgr._client.delete.assert_called_once_with(
            "public", "users", "id = $1", [42]
        )

    @pytest.mark.asyncio
    async def test_delete_no_where_values(self, configs_destructive):
        svc = _make_service(configs_destructive)
        result = await svc.delete("users", "status = 'inactive'")
        assert "Deleted 5 row(s)" in result
        svc._conn_mgr._client.delete.assert_called_once_with(
            "public", "users", "status = 'inactive'", []
        )

    @pytest.mark.asyncio
    async def test_delete_custom_schema(self, configs_destructive):
        svc = _make_service(configs_destructive)
        result = await svc.delete("users", "id = $1", [1], schema="myschema")
        assert "myschema.users" in result

    @pytest.mark.asyncio
    async def test_truncate_success(self, configs_destructive):
        svc = _make_service(configs_destructive)
        result = await svc.truncate_table("users")
        assert "Truncated table 'public.users'" in result
        svc._conn_mgr._client.truncate.assert_called_once_with("public", "users")

    @pytest.mark.asyncio
    async def test_truncate_custom_schema(self, configs_destructive):
        svc = _make_service(configs_destructive)
        result = await svc.truncate_table("users", schema="archive")
        assert "archive.users" in result
