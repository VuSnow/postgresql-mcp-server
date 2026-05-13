from postgresql_mcp.clients.base import BasePostgreSQLClient
from postgresql_mcp.clients.metadata import MetadataMixin
from postgresql_mcp.clients.read import ReadMixin


class PostgreSQLClient(BasePostgreSQLClient, MetadataMixin, ReadMixin):
    """Composed PostgreSQL client — all mixins combined."""
    pass
