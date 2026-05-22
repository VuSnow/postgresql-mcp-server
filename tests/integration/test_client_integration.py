"""
Integration tests for PostgreSQLClient — real DB queries.

Tests actual SQL execution against a live PostgreSQL instance.
"""

import pytest

pytestmark = pytest.mark.integration


class TestBaseClient:
    @pytest.mark.asyncio
    async def test_ping(self, client):
        assert await client.ping() is True

    @pytest.mark.asyncio
    async def test_pool_is_available(self, client):
        assert client.pool is not None


class TestMetadataMixin:
    @pytest.mark.asyncio
    async def test_list_schemas(self, client):
        schemas = await client.list_schemas()
        schema_names = [s["schema_name"] for s in schemas]
        assert "test_integration" in schema_names
        # System schemas should be excluded
        assert "pg_catalog" not in schema_names
        assert "information_schema" not in schema_names

    @pytest.mark.asyncio
    async def test_list_tables(self, client):
        tables = await client.list_tables("test_integration")
        table_names = [t["table_name"] for t in tables]
        assert "users" in table_names
        assert "orders" in table_names

    @pytest.mark.asyncio
    async def test_list_tables_empty_schema(self, client):
        # public schema may or may not have tables, but shouldn't error
        result = await client.list_tables("public")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_table_schema(self, client):
        columns = await client.get_table_schema("users", "test_integration")
        col_names = [c["column_name"] for c in columns]
        assert "id" in col_names
        assert "name" in col_names
        assert "email" in col_names
        assert "status" in col_names

        # Check types
        id_col = next(c for c in columns if c["column_name"] == "id")
        assert id_col["udt_name"] == "int4"

        email_col = next(c for c in columns if c["column_name"] == "email")
        assert email_col["character_maximum_length"] == 255

    @pytest.mark.asyncio
    async def test_get_indexes(self, client):
        indexes = await client.get_indexes("orders", "test_integration")
        index_names = [i["index_name"] for i in indexes]
        assert "idx_orders_user_id" in index_names

        # Check primary key
        pk = next((i for i in indexes if i["is_primary"]), None)
        assert pk is not None

    @pytest.mark.asyncio
    async def test_get_constraints(self, client):
        constraints = await client.get_constraints("orders", "test_integration")
        # asyncpg returns contype as bytes (e.g. b'p', b'f')
        constraint_types = [
            c["constraint_type"].decode() if isinstance(c["constraint_type"], bytes) else c["constraint_type"]
            for c in constraints
        ]
        # Should have PK and FK
        assert "p" in constraint_types  # primary key
        assert "f" in constraint_types  # foreign key

        # FK should reference users
        fk = next(
            c for c in constraints
            if (c["constraint_type"].decode() if isinstance(c["constraint_type"], bytes) else c["constraint_type"]) == "f"
        )
        assert fk["foreign_table"] == "users"
        assert fk["foreign_schema"] == "test_integration"

    @pytest.mark.asyncio
    async def test_get_column_values(self, client):
        values = await client.get_column_values(
            "users", "status", "test_integration", limit=10
        )
        assert "active" in values
        assert "inactive" in values

    @pytest.mark.asyncio
    async def test_get_column_values_limit(self, client):
        values = await client.get_column_values(
            "users", "name", "test_integration", limit=2
        )
        assert len(values) == 2


class TestReadMixin:
    @pytest.mark.asyncio
    async def test_execute_query(self, client):
        rows, columns = await client.execute_query(
            "SELECT id, name FROM test_integration.users ORDER BY id"
        )
        assert len(rows) == 3
        assert columns == ["id", "name"]
        assert rows[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_execute_query_with_aggregation(self, client):
        rows, columns = await client.execute_query(
            "SELECT COUNT(*) as cnt FROM test_integration.orders"
        )
        assert rows[0]["cnt"] == 3

    @pytest.mark.asyncio
    async def test_execute_query_join(self, client):
        rows, columns = await client.execute_query("""
            SELECT u.name, SUM(o.amount) as total
            FROM test_integration.users u
            JOIN test_integration.orders o ON o.user_id = u.id
            GROUP BY u.name
            ORDER BY total DESC
        """)
        assert len(rows) == 2  # Alice and Bob have orders
        assert rows[0]["name"] == "Alice"  # highest total

    @pytest.mark.asyncio
    async def test_explain_query(self, client):
        plan = await client.explain_query(
            "SELECT * FROM test_integration.users WHERE id = 1"
        )
        assert "Scan" in plan or "Index" in plan

    @pytest.mark.asyncio
    async def test_explain_query_json_format(self, client):
        plan = await client.explain_query(
            "SELECT * FROM test_integration.users",
            format="json",
        )
        assert "Plan" in plan or "plan" in plan
