"""
Integration tests for write and delete operations against real PostgreSQL.

Uses a separate test table to avoid interfering with read tests.
"""

import pytest

from postgresql_mcp.configs import ServerConfigs
from postgresql_mcp.services.connection_manager import ConnectionManager
from postgresql_mcp.services.postgresql.create import CreateService
from postgresql_mcp.services.postgresql.update import UpdateService
from postgresql_mcp.services.postgresql.delete import DeleteService


pytestmark = pytest.mark.integration


@pytest.fixture
def write_configs():
    """Configs with write and destructive enabled."""
    import os
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING=os.environ.get(
            "POSTGRESQL_CONNECTION_STRING",
            "postgresql://test:test@localhost:5432/testdb",
        ),
        READ_ONLY=False,
        ALLOW_DESTRUCTIVE=True,
    )


@pytest.fixture
async def write_connection_manager(write_configs, setup_test_schema):
    mgr = ConnectionManager(write_configs)
    await mgr.connect()
    yield mgr
    await mgr.disconnect()


@pytest.fixture
def create_service(write_connection_manager, write_configs):
    return CreateService(write_connection_manager, write_configs)


@pytest.fixture
def update_service(write_connection_manager, write_configs):
    return UpdateService(write_connection_manager, write_configs)


@pytest.fixture
def delete_service(write_connection_manager, write_configs):
    return DeleteService(write_connection_manager, write_configs)


@pytest.fixture(autouse=True)
async def write_test_table(write_connection_manager):
    """Create and clean a test table for each write test."""
    pool = write_connection_manager.client.pool
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_integration.write_test (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                value INTEGER,
                status VARCHAR(20) DEFAULT 'pending'
            );
            TRUNCATE TABLE test_integration.write_test RESTART IDENTITY;
        """)
    yield
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE test_integration.write_test RESTART IDENTITY;")


class TestInsertIntegration:
    async def test_insert_one(self, create_service, write_connection_manager):
        result = await create_service.insert_one(
            "write_test",
            {"name": "Alice", "value": 42},
            schema="test_integration",
        )
        assert "Inserted 1 row" in result
        assert "Alice" in result

        # Verify in DB
        pool = write_connection_manager.client.pool
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM test_integration.write_test WHERE name = $1", "Alice"
            )
        assert row["value"] == 42

    async def test_insert_many(self, create_service, write_connection_manager):
        result = await create_service.insert_many(
            "write_test",
            ["name", "value"],
            [["Bob", 10], ["Charlie", 20], ["Dave", 30]],
            schema="test_integration",
        )
        assert "Inserted 3 row(s)" in result

        pool = write_connection_manager.client.pool
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT count(*) FROM test_integration.write_test"
            )
        assert count == 3

    async def test_insert_with_default(self, create_service, write_connection_manager):
        """Insert without specifying 'status' — should use default."""
        result = await create_service.insert_one(
            "write_test",
            {"name": "Eve", "value": 99},
            schema="test_integration",
        )
        assert "Inserted 1 row" in result

        pool = write_connection_manager.client.pool
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT status FROM test_integration.write_test WHERE name = $1", "Eve"
            )
        assert row["status"] == "pending"


class TestUpdateIntegration:
    async def test_update_single_row(self, create_service, update_service, write_connection_manager):
        await create_service.insert_one(
            "write_test", {"name": "Alice", "value": 1}, schema="test_integration"
        )

        result = await update_service.update(
            "write_test",
            {"value": 100, "status": "done"},
            "name = $3",
            ["Alice"],
            schema="test_integration",
        )
        assert "Updated 1 row(s)" in result

        pool = write_connection_manager.client.pool
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM test_integration.write_test WHERE name = $1", "Alice"
            )
        assert row["value"] == 100
        assert row["status"] == "done"

    async def test_update_multiple_rows(self, create_service, update_service):
        await create_service.insert_many(
            "write_test",
            ["name", "value", "status"],
            [["A", 1, "pending"], ["B", 2, "pending"], ["C", 3, "done"]],
            schema="test_integration",
        )

        result = await update_service.update(
            "write_test",
            {"status": "processed"},
            "status = $2",
            ["pending"],
            schema="test_integration",
        )
        assert "Updated 2 row(s)" in result

    async def test_update_no_match(self, create_service, update_service):
        await create_service.insert_one(
            "write_test", {"name": "X", "value": 1}, schema="test_integration"
        )

        result = await update_service.update(
            "write_test",
            {"value": 999},
            "name = $2",
            ["NonExistent"],
            schema="test_integration",
        )
        assert "Updated 0 row(s)" in result


class TestDeleteIntegration:
    async def test_delete_single_row(self, create_service, delete_service, write_connection_manager):
        await create_service.insert_many(
            "write_test",
            ["name", "value"],
            [["Alice", 1], ["Bob", 2]],
            schema="test_integration",
        )

        result = await delete_service.delete(
            "write_test", "name = $1", ["Alice"], schema="test_integration"
        )
        assert "Deleted 1 row(s)" in result

        pool = write_connection_manager.client.pool
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT count(*) FROM test_integration.write_test"
            )
        assert count == 1

    async def test_delete_multiple_rows(self, create_service, delete_service):
        await create_service.insert_many(
            "write_test",
            ["name", "value", "status"],
            [["A", 1, "old"], ["B", 2, "old"], ["C", 3, "new"]],
            schema="test_integration",
        )

        result = await delete_service.delete(
            "write_test", "status = $1", ["old"], schema="test_integration"
        )
        assert "Deleted 2 row(s)" in result

    async def test_delete_no_match(self, create_service, delete_service):
        await create_service.insert_one(
            "write_test", {"name": "X", "value": 1}, schema="test_integration"
        )

        result = await delete_service.delete(
            "write_test", "name = $1", ["Ghost"], schema="test_integration"
        )
        assert "Deleted 0 row(s)" in result

    async def test_truncate(self, create_service, delete_service, write_connection_manager):
        await create_service.insert_many(
            "write_test",
            ["name", "value"],
            [["A", 1], ["B", 2], ["C", 3]],
            schema="test_integration",
        )

        result = await delete_service.truncate_table(
            "write_test", schema="test_integration"
        )
        assert "Truncated" in result

        pool = write_connection_manager.client.pool
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT count(*) FROM test_integration.write_test"
            )
        assert count == 0
