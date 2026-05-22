"""
BaseService — shared foundation for all PostgreSQL service classes.

Provides:
- Auto-connect via ConnectionManager
- Input validation (table names, identifiers)
- Write policy enforcement (read-only, destructive, allowlist)
"""

import fnmatch
import logging
import re

from postgresql_mcp.configs import ServerConfigs
from postgresql_mcp.services.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class BaseService:
    """Base class for all service layers. Owns connection + config access."""

    def __init__(self, connection_manager: ConnectionManager, configs: ServerConfigs):
        self._conn_mgr = connection_manager
        self._configs = configs

    @property
    def client(self):
        """Shortcut to the connected PostgreSQLClient."""
        return self._conn_mgr.client

    async def ensure_connected(self) -> None:
        """Ensure database connection is established (lazy connect)."""
        await self._conn_mgr.ensure_connected()

    # ─── Input Validation ───────────────────────────────────────────────

    def _validate_identifier(self, value: str, label: str = "identifier") -> str:
        """Validate SQL identifier (schema, table, column names)."""
        if not value or not _IDENTIFIER_RE.match(value):
            raise ValueError(
                f"Invalid {label}: '{value}'. "
                "Must start with a letter or underscore, contain only alphanumerics and underscores."
            )
        return value

    def _validate_table_name(self, table_name: str, schema: str = "public") -> tuple[str, str]:
        """Validate and return (schema, table) pair."""
        self._validate_identifier(schema, "schema")
        self._validate_identifier(table_name, "table name")
        return schema, table_name

    # ─── Write Policy Enforcement ───────────────────────────────────────

    def _check_write_allowed(self) -> None:
        """Raise if server is in read-only mode."""
        if self._configs.read_only:
            raise PermissionError(
                "Write operations are disabled. Set READ_ONLY=false to enable writes."
            )

    def _check_destructive_allowed(self) -> None:
        """Raise if destructive operations (delete, truncate) are not enabled."""
        self._check_write_allowed()
        if not self._configs.allow_destructive:
            raise PermissionError(
                "Destructive operations are disabled. "
                "Set ALLOW_DESTRUCTIVE=true to enable delete/truncate."
            )

    def _check_write_target(self, schema: str, table_name: str) -> None:
        """
        Raise if the target table is not in the write allowlist.

        Allowlist rules:
        - None/empty = allow all (when write is enabled)
        - 'public.users' = exact match
        - 'public.*' = all tables in schema
        - '*' = allow all explicitly
        """
        self._check_write_allowed()

        allowlist_raw = self._configs.write_allowlist
        if not allowlist_raw:
            # No allowlist configured → all tables allowed (write already enabled)
            return

        patterns = [p.strip() for p in allowlist_raw.split(",") if p.strip()]
        if not patterns:
            return

        target = f"{schema}.{table_name}"

        for pattern in patterns:
            if pattern == "*":
                return
            if fnmatch.fnmatch(target, pattern):
                return

        raise PermissionError(
            f"Write to '{target}' is not allowed. "
            f"Allowed patterns: {patterns}"
        )
