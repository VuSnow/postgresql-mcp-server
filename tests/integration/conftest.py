"""
Integration test fixtures — real PostgreSQL connection.

Requires env var: POSTGRESQL_CONNECTION_STRING (pointing to a real DB)
All integration tests are marked with @pytest.mark.integration.

Run integration tests:   pytest -m integration
Skip integration tests:  pytest -m "not integration"
"""

import os
import pytest
import asyncpg

from postgresql_mcp.configs import ServerConfigs
from postgresql_mcp.clients import PostgreSQLClient
from postgresql_mcp.services.connection_manager import ConnectionManager
from postgresql_mcp.services.postgresql.metadata import MetadataService
from postgresql_mcp.services.postgresql.read import ReadService
from postgresql_mcp.guardrails import create_pipeline


def get_connection_string() -> str:
    return os.environ.get(
        "POSTGRESQL_CONNECTION_STRING",
        "postgresql://test:test@localhost:5432/testdb",
    )


@pytest.fixture(scope="session")
def integration_configs():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING=get_connection_string(),
        READ_ONLY=True,
        DEFAULT_LIMIT=100,
        MAX_LIMIT=500,
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async fixtures."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool():
    """Session-scoped asyncpg pool. Skips all tests if DB unreachable."""
    conn_str = get_connection_string()
    try:
        pool = await asyncpg.create_pool(dsn=conn_str, min_size=1, max_size=3)
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")
        return

    yield pool
    await pool.close()


@pytest.fixture(scope="session")
async def setup_test_schema(db_pool):
    """Create test tables for integration tests. Cleaned up at session end."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE SCHEMA IF NOT EXISTS test_integration;

            DROP TABLE IF EXISTS test_integration.orders CASCADE;
            DROP TABLE IF EXISTS test_integration.users CASCADE;

            CREATE TABLE test_integration.users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE test_integration.orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES test_integration.users(id),
                amount NUMERIC(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE INDEX idx_orders_user_id ON test_integration.orders(user_id);

            INSERT INTO test_integration.users (name, email, status) VALUES
                ('Alice', 'alice@example.com', 'active'),
                ('Bob', 'bob@example.com', 'active'),
                ('Charlie', 'charlie@example.com', 'inactive');

            INSERT INTO test_integration.orders (user_id, amount) VALUES
                (1, 99.99),
                (1, 149.50),
                (2, 25.00);
        """)

    yield

    # Cleanup
    async with db_pool.acquire() as conn:
        await conn.execute("""
            DROP TABLE IF EXISTS test_integration.orders CASCADE;
            DROP TABLE IF EXISTS test_integration.users CASCADE;
            DROP SCHEMA IF EXISTS test_integration CASCADE;
        """)


@pytest.fixture
async def client(integration_configs, setup_test_schema):
    """A connected PostgreSQLClient for integration tests."""
    c = PostgreSQLClient()
    await c.connect(integration_configs.connection_string)
    yield c
    await c.close()


@pytest.fixture
async def connection_manager(integration_configs, setup_test_schema):
    """A connected ConnectionManager."""
    mgr = ConnectionManager(integration_configs)
    await mgr.connect()
    yield mgr
    await mgr.disconnect()


@pytest.fixture
def metadata_service(connection_manager, integration_configs):
    return MetadataService(connection_manager, integration_configs)


@pytest.fixture
def read_service(connection_manager, integration_configs):
    pipeline = create_pipeline(
        max_calls=100,
        read_only=True,
        default_limit=100,
        max_limit=500,
    )
    return ReadService(connection_manager, integration_configs, pipeline)
