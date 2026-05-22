from postgresql_mcp.clients.base import BasePostgreSQLClient
from postgresql_mcp.clients.metadata import MetadataMixin
from postgresql_mcp.clients.read import ReadMixin
from postgresql_mcp.clients.create import CreateMixin
from postgresql_mcp.clients.update import UpdateMixin
from postgresql_mcp.clients.delete import DeleteMixin


class PostgreSQLClient(BasePostgreSQLClient, MetadataMixin, ReadMixin, CreateMixin, UpdateMixin, DeleteMixin):
    """Composed PostgreSQL client — all mixins combined."""
    pass
