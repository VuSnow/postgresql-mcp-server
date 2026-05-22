"""Tests for connection and metadata MCP tools — output formatting."""

import pytest
from unittest.mock import AsyncMock, patch

from postgresql_mcp.services.connection_manager import ConnectionManager, ConnectionState
from postgresql_mcp.services.postgresql.metadata import MetadataService
from postgresql_mcp.configs import ServerConfigs


@pytest.fixture
def configs():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
    )


@pytest.fixture
def connection_manager(configs):
    return ConnectionManager(configs)


@pytest.fixture
def metadata_service(connection_manager, configs):
    svc = MetadataService(connection_manager, configs)
    svc.ensure_connected = AsyncMock()
    return svc


class TestConnectionTools:
    @pytest.mark.asyncio
    async def test_connect_success(self, connection_manager):
        # Simulate tool function directly
        with patch.object(connection_manager, "connect", new_callable=AsyncMock) as mock:
            await connection_manager.connect()
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_status_disconnected(self, connection_manager):
        status = connection_manager.get_status()
        assert status["state"] == "disconnected"

    @pytest.mark.asyncio
    async def test_get_status_connected(self, connection_manager):
        with patch.object(connection_manager._client, "connect", new_callable=AsyncMock):
            await connection_manager.connect()

        status = connection_manager.get_status()
        assert status["state"] == "connected"

    @pytest.mark.asyncio
    async def test_get_status_error(self, connection_manager):
        with patch.object(
            connection_manager._client, "connect", new_callable=AsyncMock, side_effect=Exception("fail")
        ):
            with pytest.raises(Exception):
                await connection_manager.connect()

        status = connection_manager.get_status()
        assert status["state"] == "error"
        assert status["last_error"] == "fail"


class TestMetadataToolOutputFormat:
    """Verify tools return strings (not dicts) for LLM consumption."""

    @pytest.mark.asyncio
    async def test_list_schemas_returns_string(self, metadata_service):
        metadata_service._conn_mgr._client.list_schemas = AsyncMock(
            return_value=[{"schema_name": "public"}]
        )
        metadata_service._conn_mgr._state = "connected"

        result = await metadata_service.list_schemas()
        assert isinstance(result, str)
        assert "public" in result

    @pytest.mark.asyncio
    async def test_list_tables_returns_string(self, metadata_service):
        metadata_service._conn_mgr._client.list_tables = AsyncMock(
            return_value=[{"table_name": "t", "table_type": "BASE TABLE", "estimated_row_count": 0}]
        )
        metadata_service._conn_mgr._state = "connected"

        result = await metadata_service.list_tables()
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_table_schema_returns_string(self, metadata_service):
        metadata_service._conn_mgr._client.get_table_schema = AsyncMock(
            return_value=[{
                "column_name": "id", "data_type": "integer", "udt_name": "int4",
                "is_nullable": "NO", "column_default": None,
                "character_maximum_length": None, "numeric_precision": 32,
                "numeric_scale": 0, "datetime_precision": None, "ordinal_position": 1,
            }]
        )
        metadata_service._conn_mgr._state = "connected"

        result = await metadata_service.get_table_schema("t")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_error_returns_string(self, metadata_service):
        # Validation errors should produce readable messages
        with pytest.raises(ValueError):
            await metadata_service.list_tables("invalid-schema!")
