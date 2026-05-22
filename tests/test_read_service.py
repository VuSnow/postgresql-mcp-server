"""Tests for ReadService — end-to-end pipeline, timeout, error formatting."""

import pytest
from unittest.mock import AsyncMock, patch

from postgresql_mcp.services.postgresql.read import ReadService
from postgresql_mcp.services.connection_manager import ConnectionManager
from postgresql_mcp.guardrails import create_pipeline
from postgresql_mcp.configs import ServerConfigs


@pytest.fixture
def configs():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
        READ_ONLY=True,
        DEFAULT_LIMIT=100,
        MAX_LIMIT=500,
        MAX_QUERY_LENGTH=10000,
        QUERY_TIMEOUT_SECONDS=30,
        RATE_LIMIT_MAX_CALLS=10,
        RATE_LIMIT_WINDOW_SECONDS=3600,
    )


@pytest.fixture
def pipeline(configs):
    return create_pipeline(
        max_calls=configs.rate_limit_max_calls,
        window_seconds=configs.rate_limit_window_seconds,
        max_query_length=configs.max_query_length,
        read_only=configs.read_only,
        default_limit=configs.default_limit,
        max_limit=configs.max_limit,
    )


@pytest.fixture
def service(configs, pipeline):
    manager = ConnectionManager(configs)
    svc = ReadService(manager, configs, pipeline)
    svc.ensure_connected = AsyncMock()
    return svc


class TestExecuteQuery:
    @pytest.mark.asyncio
    async def test_successful_query(self, service):
        service._conn_mgr._client.execute_query = AsyncMock(
            return_value=(
                [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
                ["id", "name"],
            )
        )
        service._conn_mgr._state = "connected"

        result = await service.execute_query("SELECT id, name FROM users")
        assert "2 row(s)" in result
        assert "Alice" in result
        assert "Bob" in result
        assert "id | name" in result

    @pytest.mark.asyncio
    async def test_empty_result(self, service):
        service._conn_mgr._client.execute_query = AsyncMock(
            return_value=([], ["id"])
        )
        service._conn_mgr._state = "connected"

        result = await service.execute_query("SELECT id FROM users WHERE 1=0")
        assert "0 rows" in result

    @pytest.mark.asyncio
    async def test_blocked_by_security(self, service):
        result = await service.execute_query("DROP TABLE users")
        assert "blocked" in result.lower()
        assert "Forbidden keyword" in result

    @pytest.mark.asyncio
    async def test_blocked_by_injection(self, service):
        result = await service.execute_query("SELECT 1; DROP TABLE users")
        assert "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_blocked_by_dangerous_function(self, service):
        result = await service.execute_query("SELECT pg_sleep(10)")
        assert "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_auto_limit_injected(self, service):
        """Verify the rewriter injects LIMIT before execution."""
        captured_query = None

        async def mock_execute(query, timeout_seconds=None):
            nonlocal captured_query
            captured_query = query
            return ([], ["id"])

        service._conn_mgr._client.execute_query = mock_execute
        service._conn_mgr._state = "connected"

        await service.execute_query("SELECT * FROM users")
        assert "LIMIT 100" in captured_query

    @pytest.mark.asyncio
    async def test_limit_capped(self, service):
        captured_query = None

        async def mock_execute(query, timeout_seconds=None):
            nonlocal captured_query
            captured_query = query
            return ([], ["id"])

        service._conn_mgr._client.execute_query = mock_execute
        service._conn_mgr._state = "connected"

        await service.execute_query("SELECT * FROM users LIMIT 9999")
        assert "LIMIT 500" in captured_query

    @pytest.mark.asyncio
    async def test_execution_error_formatted(self, service):
        service._conn_mgr._client.execute_query = AsyncMock(
            side_effect=Exception("relation 'users' does not exist")
        )
        service._conn_mgr._state = "connected"

        result = await service.execute_query("SELECT * FROM users")
        assert "Query error" in result
        assert "does not exist" in result

    @pytest.mark.asyncio
    async def test_rate_limit_blocking(self, configs):
        # Create pipeline with max_calls=2
        pipeline = create_pipeline(
            max_calls=2,
            window_seconds=3600,
            read_only=True,
            default_limit=100,
            max_limit=500,
        )
        manager = ConnectionManager(configs)
        svc = ReadService(manager, configs, pipeline)
        svc.ensure_connected = AsyncMock()
        svc._conn_mgr._client.execute_query = AsyncMock(return_value=([], ["x"]))
        svc._conn_mgr._state = "connected"

        # First 2 calls succeed
        r1 = await svc.execute_query("SELECT 1")
        r2 = await svc.execute_query("SELECT 2")
        assert "blocked" not in r1.lower()
        assert "blocked" not in r2.lower()

        # Third call should be rate limited
        r3 = await svc.execute_query("SELECT 3")
        assert "Rate limit" in r3


class TestPIIMasking:
    @pytest.mark.asyncio
    async def test_pii_columns_masked(self, configs):
        pipeline = create_pipeline(
            max_calls=100,
            read_only=True,
            default_limit=100,
            max_limit=500,
            pii_rules_json='[{"column":"email","method":"hash"}]',
        )
        manager = ConnectionManager(configs)
        svc = ReadService(manager, configs, pipeline)
        svc.ensure_connected = AsyncMock()
        svc._conn_mgr._client.execute_query = AsyncMock(
            return_value=(
                [{"id": 1, "email": "secret@example.com"}],
                ["id", "email"],
            )
        )
        svc._conn_mgr._state = "connected"

        result = await svc.execute_query("SELECT id, email FROM users")
        assert "secret@example.com" not in result
        assert "1" in result  # id preserved


class TestDryRunQuery:
    @pytest.mark.asyncio
    async def test_valid_query(self, service):
        result = await service.dry_run_query("SELECT * FROM users WHERE id = 1")
        assert "valid" in result.lower()

    @pytest.mark.asyncio
    async def test_invalid_query(self, service):
        result = await service.dry_run_query("DROP TABLE users")
        assert "rejected" in result.lower()

    @pytest.mark.asyncio
    async def test_injection_detected(self, service):
        result = await service.dry_run_query("SELECT 1; DELETE FROM users")
        assert "rejected" in result.lower()


class TestExplainQuery:
    @pytest.mark.asyncio
    async def test_explain_success(self, service):
        service._conn_mgr._client.explain_query = AsyncMock(
            return_value="Seq Scan on users  (cost=0.00..1.01 rows=1 width=36)"
        )
        service._conn_mgr._state = "connected"

        result = await service.explain_query("SELECT * FROM users")
        assert "EXPLAIN" in result
        assert "Seq Scan" in result

    @pytest.mark.asyncio
    async def test_explain_analyze(self, service):
        service._conn_mgr._client.explain_query = AsyncMock(
            return_value="Seq Scan on users  (cost=0.00..1.01 rows=1 width=36) (actual time=0.01..0.01 rows=1 loops=1)"
        )
        service._conn_mgr._state = "connected"

        result = await service.explain_query("SELECT * FROM users", analyze=True)
        assert "EXPLAIN ANALYZE" in result

    @pytest.mark.asyncio
    async def test_explain_blocked_dangerous_query(self, service):
        result = await service.explain_query("DROP TABLE users")
        assert "rejected" in result.lower()

    @pytest.mark.asyncio
    async def test_explain_error(self, service):
        service._conn_mgr._client.explain_query = AsyncMock(
            side_effect=Exception("syntax error")
        )
        service._conn_mgr._state = "connected"

        result = await service.explain_query("SELECT bad syntax")
        assert "error" in result.lower()


class TestResultFormatting:
    @pytest.mark.asyncio
    async def test_null_values_displayed(self, service):
        service._conn_mgr._client.execute_query = AsyncMock(
            return_value=(
                [{"id": 1, "name": None}],
                ["id", "name"],
            )
        )
        service._conn_mgr._state = "connected"

        result = await service.execute_query("SELECT id, name FROM users")
        assert "NULL" in result

    @pytest.mark.asyncio
    async def test_long_values_truncated(self, service):
        long_value = "x" * 200
        service._conn_mgr._client.execute_query = AsyncMock(
            return_value=(
                [{"data": long_value}],
                ["data"],
            )
        )
        service._conn_mgr._state = "connected"

        result = await service.execute_query("SELECT data FROM t")
        assert "..." in result
        assert long_value not in result

    @pytest.mark.asyncio
    async def test_many_rows_capped_display(self, service):
        rows = [{"id": i} for i in range(100)]
        service._conn_mgr._client.execute_query = AsyncMock(
            return_value=(rows, ["id"])
        )
        service._conn_mgr._state = "connected"

        result = await service.execute_query("SELECT id FROM t LIMIT 100")
        assert "50 more row(s)" in result
