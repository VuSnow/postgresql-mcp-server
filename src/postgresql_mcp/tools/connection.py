"""
MCP Tools — Connection lifecycle management.

Tools: connect, disconnect, get_status
"""

import logging

from postgresql_mcp.server import mcp, connection_manager

logger = logging.getLogger(__name__)


@mcp.tool()
async def connect() -> str:
    """Connect to the PostgreSQL database.

    Establishes connection pool. Safe to call multiple times —
    will skip if already connected.
    """
    try:
        await connection_manager.connect()
        return "Connected to PostgreSQL."
    except Exception as e:
        logger.error(f"[tool] connect error: {e}")
        return f"Connection failed: {e}"


@mcp.tool()
async def disconnect() -> str:
    """Disconnect from the PostgreSQL database.

    Closes the connection pool. Safe to call if already disconnected.
    """
    try:
        await connection_manager.disconnect()
        return "Disconnected."
    except Exception as e:
        logger.error(f"[tool] disconnect error: {e}")
        return f"Disconnect failed: {e}"


@mcp.tool()
async def get_status() -> str:
    """Get the current connection status.

    Returns state (disconnected/connecting/connected/error) and
    last error message if any.
    """
    status = connection_manager.get_status()
    lines = [
        f"State: {status['state']}",
    ]
    if status["last_error"]:
        lines.append(f"Last error: {status['last_error']}")
    return "\n".join(lines)
