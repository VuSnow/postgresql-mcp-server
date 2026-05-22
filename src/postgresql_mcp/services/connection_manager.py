"""
Connection Manager — singleton lifecycle management for PostgreSQLClient.

State machine: disconnected → connecting → connected → error
Supports lazy pool creation, health check, and reconnect.
"""

import logging
from enum import Enum

from postgresql_mcp.clients import PostgreSQLClient
from postgresql_mcp.configs import ServerConfigs

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class ConnectionManager:
    """Singleton-style manager that owns the PostgreSQLClient lifecycle."""

    def __init__(self, configs: ServerConfigs):
        self._configs = configs
        self._client = PostgreSQLClient()
        self._state = ConnectionState.DISCONNECTED
        self._last_error: str | None = None

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def client(self) -> PostgreSQLClient:
        """Access underlying client. Raises if not connected."""
        if self._state != ConnectionState.CONNECTED:
            raise RuntimeError(
                f"Cannot use client in state '{self._state.value}'. Call connect() first."
            )
        return self._client

    @property
    def last_error(self) -> str | None:
        return self._last_error

    async def connect(self) -> None:
        """Create connection pool. Transitions: disconnected/error → connecting → connected."""
        if self._state == ConnectionState.CONNECTED:
            logger.debug("[conn_mgr] Already connected, skipping.")
            return

        self._state = ConnectionState.CONNECTING
        self._last_error = None

        try:
            await self._client.connect(self._configs.connection_string)
            self._state = ConnectionState.CONNECTED
            logger.info("[conn_mgr] Connected to PostgreSQL.")
        except Exception as e:
            self._state = ConnectionState.ERROR
            self._last_error = str(e)
            logger.error(f"[conn_mgr] Connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection pool. Transitions: any → disconnected."""
        if self._state == ConnectionState.DISCONNECTED:
            return

        try:
            await self._client.close()
        except Exception as e:
            logger.warning(f"[conn_mgr] Error during disconnect: {e}")
        finally:
            self._state = ConnectionState.DISCONNECTED
            self._last_error = None
            logger.info("[conn_mgr] Disconnected.")

    async def ensure_connected(self) -> None:
        """Lazy connect — only creates pool if not already connected."""
        if self._state == ConnectionState.CONNECTED:
            return
        await self.connect()

    async def health_check(self) -> bool:
        """Ping the database. Returns False and transitions to ERROR on failure."""
        if self._state != ConnectionState.CONNECTED:
            return False

        healthy = await self._client.ping()
        if not healthy:
            self._state = ConnectionState.ERROR
            self._last_error = "Health check failed"
            logger.warning("[conn_mgr] Health check failed, state → error.")
        return healthy

    async def reconnect(self) -> None:
        """Force reconnect: disconnect then connect."""
        await self.disconnect()
        await self.connect()

    def get_status(self) -> dict:
        """Return current status for the get_status tool."""
        return {
            "state": self._state.value,
            "last_error": self._last_error,
        }
