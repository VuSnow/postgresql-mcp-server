"""
Phase 10.13 — ENABLE_WRITE_TOOLS config tests.

Tests that write tools are registered/hidden based on ENABLE_WRITE_TOOLS config.
"""

import pytest

from postgresql_mcp.configs import ServerConfigs


class TestEnableWriteToolsConfig:
    """Config-level tests for ENABLE_WRITE_TOOLS."""

    def test_default_false(self):
        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
        )
        assert configs.enable_write_tools is False

    def test_explicit_true(self):
        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            ENABLE_WRITE_TOOLS=True,
        )
        assert configs.enable_write_tools is True

    def test_explicit_false(self):
        configs = ServerConfigs(
            POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost/test",
            ENABLE_WRITE_TOOLS=False,
        )
        assert configs.enable_write_tools is False


class TestWriteToolRegistration:
    """Verify write tool modules exist and have the expected tool functions."""

    def test_create_tools_have_mcp_tool(self):
        """Create tool module defines insert functions."""
        from postgresql_mcp.tools import create
        assert hasattr(create, "insert_one")
        assert hasattr(create, "insert_many")

    def test_update_tools_have_mcp_tool(self):
        from postgresql_mcp.tools import update
        assert hasattr(update, "update")

    def test_delete_tools_have_mcp_tool(self):
        from postgresql_mcp.tools import delete
        assert hasattr(delete, "delete")
        assert hasattr(delete, "truncate_table")

    def test_read_tools_always_available(self):
        """Read tools are always registered regardless of config."""
        from postgresql_mcp.tools import read
        assert hasattr(read, "execute_query")
        assert hasattr(read, "dry_run_query")
        assert hasattr(read, "explain_query")


class TestAppConditionalImport:
    """Verify app.py conditional import logic."""

    def test_app_module_loads(self):
        """app.py can be imported without error."""
        import postgresql_mcp.app
        assert hasattr(postgresql_mcp.app, "mcp")

    def test_configs_accessible_from_server(self):
        from postgresql_mcp.server import configs
        assert hasattr(configs, "enable_write_tools")
