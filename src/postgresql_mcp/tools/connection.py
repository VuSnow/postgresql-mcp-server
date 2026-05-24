"""
MCP Tools — Connection lifecycle management.

Tools: connect, disconnect, get_status
"""

import logging

from postgresql_mcp.server import mcp, connection_manager

logger = logging.getLogger(__name__)


@mcp.tool()
async def connect() -> dict:
    """Connect to the PostgreSQL database.

    Establishes connection pool. Safe to call multiple times —
    will skip if already connected.
    """
    try:
        await connection_manager.connect()
        return {"result": "Connected to PostgreSQL."}
    except Exception as e:
        logger.error(f"[tool] connect error: {e}")
        return {"error": f"Connection failed: {e}"}


@mcp.tool()
async def disconnect() -> dict:
    """Disconnect from the PostgreSQL database.

    Closes the connection pool. Safe to call if already disconnected.
    """
    try:
        await connection_manager.disconnect()
        return {"result": "Disconnected."}
    except Exception as e:
        logger.error(f"[tool] disconnect error: {e}")
        return {"error": f"Disconnect failed: {e}"}


@mcp.tool()
async def get_status() -> dict:
    """Get the current connection status.

    Returns state (disconnected/connecting/connected/error),
    last error message if any, and database health (ping result).
    """
    status = connection_manager.get_status()
    result = {"state": status["state"]}
    if status["last_error"]:
        result["last_error"] = status["last_error"]

    # If connected, perform a real health check
    if status["state"] == "connected":
        try:
            healthy = await connection_manager.health_check()
            result["healthy"] = healthy
        except Exception:
            result["healthy"] = False

    return {"result": result}
