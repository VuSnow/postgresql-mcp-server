"""Tests for ConnectionManager — state transitions and lifecycle."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from postgresql_mcp.services.connection_manager import ConnectionManager, ConnectionState
from postgresql_mcp.configs import ServerConfigs


@pytest.fixture
def configs():
    """Minimal configs for testing."""
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
    )


@pytest.fixture
def manager(configs):
    return ConnectionManager(configs)


class TestConnectionManagerInit:
    def test_initial_state_is_disconnected(self, manager):
        assert manager.state == ConnectionState.DISCONNECTED

    def test_initial_last_error_is_none(self, manager):
        assert manager.last_error is None

    def test_client_raises_when_disconnected(self, manager):
        with pytest.raises(RuntimeError, match="Cannot use client"):
            _ = manager.client


class TestConnectionManagerConnect:
    @pytest.mark.asyncio
    async def test_connect_success(self, manager):
        with patch.object(manager._client, "connect", new_callable=AsyncMock) as mock_connect:
            await manager.connect()

        assert manager.state == ConnectionState.CONNECTED
        assert manager.last_error is None
        mock_connect.assert_called_once_with(
            "postgresql://test:test@localhost:5432/testdb",
            min_size=1,
            max_size=10,
        )

    @pytest.mark.asyncio
    async def test_connect_failure_transitions_to_error(self, manager):
        with patch.object(
            manager._client, "connect", new_callable=AsyncMock, side_effect=Exception("connection refused")
        ):
            with pytest.raises(Exception, match="connection refused"):
                await manager.connect()

        assert manager.state == ConnectionState.ERROR
        assert manager.last_error == "connection refused"

    @pytest.mark.asyncio
    async def test_connect_skips_if_already_connected(self, manager):
        with patch.object(manager._client, "connect", new_callable=AsyncMock) as mock_connect:
            await manager.connect()
            await manager.connect()  # second call should skip

        mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_retries_after_error(self, manager):
        # First call fails
        with patch.object(
            manager._client, "connect", new_callable=AsyncMock, side_effect=Exception("fail")
        ):
            with pytest.raises(Exception):
                await manager.connect()

        assert manager.state == ConnectionState.ERROR

        # Second call succeeds
        with patch.object(manager._client, "connect", new_callable=AsyncMock):
            await manager.connect()

        assert manager.state == ConnectionState.CONNECTED


class TestConnectionManagerDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_from_connected(self, manager):
        with patch.object(manager._client, "connect", new_callable=AsyncMock):
            await manager.connect()

        with patch.object(manager._client, "close", new_callable=AsyncMock) as mock_close:
            await manager.disconnect()

        assert manager.state == ConnectionState.DISCONNECTED
        mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_when_already_disconnected(self, manager):
        await manager.disconnect()  # no-op, should not raise
        assert manager.state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_disconnect_handles_close_error_gracefully(self, manager):
        with patch.object(manager._client, "connect", new_callable=AsyncMock):
            await manager.connect()

        with patch.object(
            manager._client, "close", new_callable=AsyncMock, side_effect=Exception("close error")
        ):
            await manager.disconnect()  # should not raise

        assert manager.state == ConnectionState.DISCONNECTED


class TestConnectionManagerEnsureConnected:
    @pytest.mark.asyncio
    async def test_ensure_connected_creates_connection(self, manager):
        with patch.object(manager._client, "connect", new_callable=AsyncMock) as mock_connect:
            await manager.ensure_connected()

        mock_connect.assert_called_once()
        assert manager.state == ConnectionState.CONNECTED

    @pytest.mark.asyncio
    async def test_ensure_connected_skips_if_connected(self, manager):
        with patch.object(manager._client, "connect", new_callable=AsyncMock) as mock_connect:
            await manager.connect()
            await manager.ensure_connected()

        mock_connect.assert_called_once()


class TestConnectionManagerHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(self, manager):
        with patch.object(manager._client, "connect", new_callable=AsyncMock):
            await manager.connect()

        with patch.object(manager._client, "ping", new_callable=AsyncMock, return_value=True):
            result = await manager.health_check()

        assert result is True
        assert manager.state == ConnectionState.CONNECTED

    @pytest.mark.asyncio
    async def test_health_check_returns_false_and_sets_error(self, manager):
        with patch.object(manager._client, "connect", new_callable=AsyncMock):
            await manager.connect()

        with patch.object(manager._client, "ping", new_callable=AsyncMock, return_value=False):
            result = await manager.health_check()

        assert result is False
        assert manager.state == ConnectionState.ERROR
        assert manager.last_error == "Health check failed"

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_not_connected(self, manager):
        result = await manager.health_check()
        assert result is False


class TestConnectionManagerReconnect:
    @pytest.mark.asyncio
    async def test_reconnect(self, manager):
        with patch.object(manager._client, "connect", new_callable=AsyncMock):
            await manager.connect()

        with patch.object(manager._client, "close", new_callable=AsyncMock):
            with patch.object(manager._client, "connect", new_callable=AsyncMock) as mock_connect:
                await manager.reconnect()

        assert manager.state == ConnectionState.CONNECTED


class TestConnectionManagerGetStatus:
    def test_status_disconnected(self, manager):
        status = manager.get_status()
        assert status == {"state": "disconnected", "last_error": None}

    @pytest.mark.asyncio
    async def test_status_connected(self, manager):
        with patch.object(manager._client, "connect", new_callable=AsyncMock):
            await manager.connect()

        status = manager.get_status()
        assert status == {"state": "connected", "last_error": None}
