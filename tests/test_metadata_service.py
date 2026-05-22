"""Tests for MetadataService — formatting and delegation."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from postgresql_mcp.services.postgresql.metadata import MetadataService
from postgresql_mcp.services.connection_manager import ConnectionManager
from postgresql_mcp.configs import ServerConfigs


@pytest.fixture
def configs():
    return ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
    )


@pytest.fixture
def service(configs):
    manager = ConnectionManager(configs)
    svc = MetadataService(manager, configs)
    # Patch ensure_connected to skip actual connection
    svc.ensure_connected = AsyncMock()
    return svc


class TestListSchemas:
    @pytest.mark.asyncio
    async def test_formats_schemas(self, service):
        service._conn_mgr._client.list_schemas = AsyncMock(
            return_value=[{"schema_name": "public"}, {"schema_name": "analytics"}]
        )
        service._conn_mgr._state = "connected"

        result = await service.list_schemas()
        assert "public" in result
        assert "analytics" in result
        assert "2 schema(s)" in result

    @pytest.mark.asyncio
    async def test_no_schemas(self, service):
        service._conn_mgr._client.list_schemas = AsyncMock(return_value=[])
        service._conn_mgr._state = "connected"

        result = await service.list_schemas()
        assert "No user schemas found" in result


class TestListTables:
    @pytest.mark.asyncio
    async def test_formats_tables(self, service):
        service._conn_mgr._client.list_tables = AsyncMock(
            return_value=[
                {"table_name": "users", "table_type": "BASE TABLE", "estimated_row_count": 1000},
                {"table_name": "orders", "table_type": "BASE TABLE", "estimated_row_count": 5000},
            ]
        )
        service._conn_mgr._state = "connected"

        result = await service.list_tables("public")
        assert "users" in result
        assert "orders" in result
        assert "2 table(s)" in result
        assert "BASE TABLE" in result

    @pytest.mark.asyncio
    async def test_no_tables(self, service):
        service._conn_mgr._client.list_tables = AsyncMock(return_value=[])
        service._conn_mgr._state = "connected"

        result = await service.list_tables("empty_schema")
        assert "No tables found" in result

    @pytest.mark.asyncio
    async def test_invalid_schema_raises(self, service):
        with pytest.raises(ValueError, match="Invalid schema"):
            await service.list_tables("bad-schema!")


class TestGetTableSchema:
    @pytest.mark.asyncio
    async def test_formats_columns(self, service):
        service._conn_mgr._client.get_table_schema = AsyncMock(
            return_value=[
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "udt_name": "int4",
                    "is_nullable": "NO",
                    "column_default": "nextval('users_id_seq')",
                    "character_maximum_length": None,
                    "numeric_precision": 32,
                    "numeric_scale": 0,
                    "datetime_precision": None,
                    "ordinal_position": 1,
                },
                {
                    "column_name": "email",
                    "data_type": "character varying",
                    "udt_name": "varchar",
                    "is_nullable": "YES",
                    "column_default": None,
                    "character_maximum_length": 255,
                    "numeric_precision": None,
                    "numeric_scale": None,
                    "datetime_precision": None,
                    "ordinal_position": 2,
                },
            ]
        )
        service._conn_mgr._state = "connected"

        result = await service.get_table_schema("users", "public")
        assert "id" in result
        assert "email" in result
        assert "int4" in result
        assert "varchar(255)" in result
        assert "2 column(s)" in result

    @pytest.mark.asyncio
    async def test_table_not_found(self, service):
        service._conn_mgr._client.get_table_schema = AsyncMock(return_value=[])
        service._conn_mgr._state = "connected"

        result = await service.get_table_schema("nonexistent")
        assert "not found" in result


class TestGetIndexes:
    @pytest.mark.asyncio
    async def test_formats_indexes(self, service):
        service._conn_mgr._client.get_indexes = AsyncMock(
            return_value=[
                {
                    "index_name": "users_pkey",
                    "is_unique": True,
                    "is_primary": True,
                    "index_type": "btree",
                    "columns": ["id"],
                    "index_definition": "CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id)",
                },
                {
                    "index_name": "idx_users_email",
                    "is_unique": True,
                    "is_primary": False,
                    "index_type": "btree",
                    "columns": ["email"],
                    "index_definition": "CREATE UNIQUE INDEX idx_users_email ON public.users USING btree (email)",
                },
            ]
        )
        service._conn_mgr._state = "connected"

        result = await service.get_indexes("users")
        assert "users_pkey" in result
        assert "PRIMARY" in result
        assert "UNIQUE" in result
        assert "btree" in result
        assert "2 index(es)" in result

    @pytest.mark.asyncio
    async def test_no_indexes(self, service):
        service._conn_mgr._client.get_indexes = AsyncMock(return_value=[])
        service._conn_mgr._state = "connected"

        result = await service.get_indexes("simple_table")
        assert "No indexes found" in result


class TestGetConstraints:
    @pytest.mark.asyncio
    async def test_formats_constraints(self, service):
        service._conn_mgr._client.get_constraints = AsyncMock(
            return_value=[
                {
                    "constraint_name": "orders_user_fk",
                    "constraint_type": "f",
                    "constraint_type_name": "FOREIGN KEY",
                    "columns": ["user_id"],
                    "constraint_definition": "FOREIGN KEY (user_id) REFERENCES users(id)",
                    "foreign_schema": "public",
                    "foreign_table": "users",
                    "foreign_columns": ["id"],
                },
            ]
        )
        service._conn_mgr._state = "connected"

        result = await service.get_constraints("orders")
        assert "FOREIGN KEY" in result
        assert "orders_user_fk" in result
        assert "References: public.users" in result

    @pytest.mark.asyncio
    async def test_no_constraints(self, service):
        service._conn_mgr._client.get_constraints = AsyncMock(return_value=[])
        service._conn_mgr._state = "connected"

        result = await service.get_constraints("logs")
        assert "No constraints found" in result


class TestGetColumnValues:
    @pytest.mark.asyncio
    async def test_formats_values(self, service):
        service._conn_mgr._client.get_column_values = AsyncMock(
            return_value=["active", "inactive", "pending"]
        )
        service._conn_mgr._state = "connected"

        result = await service.get_column_values("users", "status")
        assert "active" in result
        assert "inactive" in result
        assert "pending" in result
        assert "3 value(s)" in result

    @pytest.mark.asyncio
    async def test_truncation_notice(self, service):
        values = [f"val_{i}" for i in range(50)]
        service._conn_mgr._client.get_column_values = AsyncMock(return_value=values)
        service._conn_mgr._state = "connected"

        result = await service.get_column_values("t", "col", limit=50)
        assert "truncated" in result

    @pytest.mark.asyncio
    async def test_no_values(self, service):
        service._conn_mgr._client.get_column_values = AsyncMock(return_value=[])
        service._conn_mgr._state = "connected"

        result = await service.get_column_values("t", "empty_col")
        assert "No non-null values found" in result

    @pytest.mark.asyncio
    async def test_invalid_column_raises(self, service):
        with pytest.raises(ValueError, match="Invalid column"):
            await service.get_column_values("users", "bad col!")
