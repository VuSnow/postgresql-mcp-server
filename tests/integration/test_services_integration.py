"""
Integration tests for MetadataService and ReadService — real DB.

Tests the service layer output formatting with actual PostgreSQL data.
"""

import pytest

pytestmark = pytest.mark.integration


class TestMetadataServiceIntegration:
    @pytest.mark.asyncio
    async def test_list_schemas_output(self, metadata_service):
        result = await metadata_service.list_schemas()
        assert "test_integration" in result
        assert "schema(s)" in result

    @pytest.mark.asyncio
    async def test_list_tables_output(self, metadata_service):
        result = await metadata_service.list_tables("test_integration")
        assert "users" in result
        assert "orders" in result
        assert "table(s)" in result
        assert "BASE TABLE" in result

    @pytest.mark.asyncio
    async def test_get_table_schema_output(self, metadata_service):
        result = await metadata_service.get_table_schema("users", "test_integration")
        assert "id" in result
        assert "name" in result
        assert "email" in result
        assert "varchar" in result
        assert "int4" in result
        assert "column(s)" in result

    @pytest.mark.asyncio
    async def test_get_indexes_output(self, metadata_service):
        result = await metadata_service.get_indexes("orders", "test_integration")
        assert "idx_orders_user_id" in result
        assert "btree" in result
        assert "index(es)" in result

    @pytest.mark.asyncio
    async def test_get_constraints_output(self, metadata_service):
        result = await metadata_service.get_constraints("orders", "test_integration")
        assert "PRIMARY KEY" in result
        assert "FOREIGN KEY" in result
        assert "References:" in result
        assert "test_integration.users" in result

    @pytest.mark.asyncio
    async def test_get_column_values_output(self, metadata_service):
        result = await metadata_service.get_column_values(
            "users", "status", "test_integration"
        )
        assert "active" in result
        assert "inactive" in result
        assert "value(s)" in result


class TestReadServiceIntegration:
    @pytest.mark.asyncio
    async def test_execute_select(self, read_service):
        result = await read_service.execute_query(
            "SELECT id, name FROM test_integration.users ORDER BY id"
        )
        assert "3 row(s)" in result
        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result

    @pytest.mark.asyncio
    async def test_execute_with_where(self, read_service):
        result = await read_service.execute_query(
            "SELECT name FROM test_integration.users WHERE status = 'active'"
        )
        assert "2 row(s)" in result
        assert "Alice" in result
        assert "Charlie" not in result

    @pytest.mark.asyncio
    async def test_execute_aggregation(self, read_service):
        result = await read_service.execute_query(
            "SELECT COUNT(*) as total FROM test_integration.orders"
        )
        assert "3" in result

    @pytest.mark.asyncio
    async def test_execute_join(self, read_service):
        result = await read_service.execute_query("""
            SELECT u.name, o.amount
            FROM test_integration.users u
            JOIN test_integration.orders o ON o.user_id = u.id
            ORDER BY o.amount DESC
        """)
        assert "row(s)" in result
        assert "Alice" in result

    @pytest.mark.asyncio
    async def test_blocked_ddl(self, read_service):
        result = await read_service.execute_query("DROP TABLE test_integration.users")
        assert "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_blocked_injection(self, read_service):
        result = await read_service.execute_query(
            "SELECT 1; DELETE FROM test_integration.users"
        )
        assert "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_auto_limit_applied(self, read_service):
        """Query without LIMIT should still work (auto-injected)."""
        result = await read_service.execute_query(
            "SELECT * FROM test_integration.users"
        )
        assert "row(s)" in result

    @pytest.mark.asyncio
    async def test_dry_run_valid(self, read_service):
        result = await read_service.dry_run_query(
            "SELECT * FROM test_integration.users WHERE id = 1"
        )
        assert "valid" in result.lower()

    @pytest.mark.asyncio
    async def test_dry_run_invalid(self, read_service):
        result = await read_service.dry_run_query("DROP TABLE users")
        assert "rejected" in result.lower()

    @pytest.mark.asyncio
    async def test_explain(self, read_service):
        result = await read_service.explain_query(
            "SELECT * FROM test_integration.users WHERE id = 1"
        )
        assert "EXPLAIN" in result
        assert "Scan" in result or "Index" in result

    @pytest.mark.asyncio
    async def test_explain_nonexistent_table(self, read_service):
        result = await read_service.explain_query(
            "SELECT * FROM nonexistent_table_xyz"
        )
        assert "error" in result.lower()


class TestPIIMaskingIntegration:
    """Test PII masking with real data."""

    @pytest.mark.asyncio
    async def test_email_masked(self, connection_manager, integration_configs):
        """Verify PII masking works end-to-end with real query results."""
        from postgresql_mcp.guardrails import create_pipeline
        from postgresql_mcp.services.postgresql.read import ReadService

        pipeline = create_pipeline(
            max_calls=100,
            read_only=True,
            default_limit=100,
            max_limit=500,
            pii_rules_json='[{"column":"email","method":"hash"}]',
        )
        svc = ReadService(connection_manager, integration_configs, pipeline)

        result = await svc.execute_query(
            "SELECT name, email FROM test_integration.users ORDER BY id LIMIT 1"
        )
        # Email should be masked (not contain the real value)
        assert "alice@example.com" not in result
        # But name should be visible
        assert "Alice" in result
