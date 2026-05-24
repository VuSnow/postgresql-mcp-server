"""
Connection Manager — singleton lifecycle management for PostgreSQLClient.

State machine: disconnected → connecting → connected → error
Supports lazy pool creation, health check, reconnect with retry.
"""

import asyncio
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
            await self._client.connect(
                self._configs.connection_string,
                min_size=self._configs.pool_min_size,
                max_size=self._configs.pool_max_size,
            )
            self._state = ConnectionState.CONNECTED
            logger.info("[conn_mgr] Connected to PostgreSQL.")
        except Exception as e:
            self._state = ConnectionState.ERROR
            self._last_error = str(e)
            logger.error("[conn_mgr] Connection failed: %s", e)
            raise

    async def disconnect(self) -> None:
        """Close connection pool. Transitions: any → disconnected."""
        if self._state == ConnectionState.DISCONNECTED:
            return

        try:
            await self._client.close()
        except Exception as e:
            logger.warning("[conn_mgr] Error during disconnect: %s", e)
        finally:
            self._state = ConnectionState.DISCONNECTED
            self._last_error = None
            logger.info("[conn_mgr] Disconnected.")

    async def ensure_connected(self) -> None:
        """Lazy connect with retry — creates pool if not connected, retries on failure."""
        if self._state == ConnectionState.CONNECTED:
            return

        max_retries = self._configs.connect_max_retries
        base_delay = self._configs.connect_base_delay
        max_delay = self._configs.connect_max_delay

        last_exc: Exception | None = None
        delay = base_delay

        for attempt in range(1, max_retries + 1):
            try:
                await self.connect()
                return
            except Exception as e:
                last_exc = e
                if attempt < max_retries:
                    logger.warning(
                        "[conn_mgr] Connect attempt %d/%d failed: %s. Retrying in %.1fs...",
                        attempt, max_retries, e, delay,
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)
                    # Reset state so connect() tries again
                    self._state = ConnectionState.DISCONNECTED

        logger.error("[conn_mgr] All %d connect attempts failed.", max_retries)
        raise last_exc  # type: ignore[misc]

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
