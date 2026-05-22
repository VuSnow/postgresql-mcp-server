"""
Shared application state — MCP instance and bootstrapped services.

Both app.py and tools/*.py import from here to avoid circular imports.
"""

from fastmcp import FastMCP

from postgresql_mcp.configs import ServerConfigs
from postgresql_mcp.guardrails import create_pipeline
from postgresql_mcp.services.connection_manager import ConnectionManager
from postgresql_mcp.services.postgresql.metadata import MetadataService
from postgresql_mcp.services.postgresql.read import ReadService
from postgresql_mcp.services.postgresql.create import CreateService
from postgresql_mcp.services.postgresql.update import UpdateService

mcp = FastMCP(
    name="PostgreSQL MCP Server",
    instructions=(
        "You are a PostgreSQL assistant. Use the available tools to help users "
        "interact with their PostgreSQL databases — querying data, inspecting "
        "schema structure, and managing database operations."
    ),
)

# ─── Bootstrap services ─────────────────────────────────────────────────────

configs = ServerConfigs()
connection_manager = ConnectionManager(configs)
metadata_service = MetadataService(connection_manager, configs)

pipeline = create_pipeline(
    max_calls=configs.rate_limit_max_calls,
    window_seconds=configs.rate_limit_window_seconds,
    max_query_length=configs.max_query_length,
    read_only=configs.read_only,
    allow_destructive=configs.allow_destructive,
    default_limit=configs.default_limit,
    max_limit=configs.max_limit,
    pii_rules_json=configs.pii_rules,
)
read_service = ReadService(connection_manager, configs, pipeline)
create_service = CreateService(connection_manager, configs)
update_service = UpdateService(connection_manager, configs)
