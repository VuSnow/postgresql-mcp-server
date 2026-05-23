"""
System catalog blocking.

Prevents queries from accessing sensitive PostgreSQL system tables
that could leak credentials, configuration, or internal state.

Always enforced regardless of security profile — these are hardcoded blocks.
"""

from postgresql_mcp.guardrails.models import GuardrailResult
from postgresql_mcp.guardrails.sql_parser import extract_tables, parse_query


# ─── Blocked system tables (always blocked in execute_query) ─────────────────

BLOCKED_SYSTEM_TABLES: frozenset[str] = frozenset(
    [
        # Credential/auth tables
        "pg_catalog.pg_shadow",
        "pg_catalog.pg_authid",
        "pg_catalog.pg_auth_members",
        # Role/user tables
        "pg_catalog.pg_roles",
        "pg_catalog.pg_user",
        "pg_catalog.pg_group",
        # Activity/stats (can leak queries, connection info)
        "pg_catalog.pg_stat_activity",
        "pg_catalog.pg_stat_statements",
        "pg_catalog.pg_stat_ssl",
        "pg_catalog.pg_stat_gssapi",
        # Configuration (can leak sensitive settings)
        "pg_catalog.pg_settings",
        "pg_catalog.pg_file_settings",
        "pg_catalog.pg_hba_file_rules",
        # Replication (can leak topology)
        "pg_catalog.pg_replication_slots",
        "pg_catalog.pg_stat_replication",
    ]
)

# Schemas entirely blocked for raw query access
BLOCKED_SCHEMAS: frozenset[str] = frozenset(
    [
        "pg_catalog",
    ]
)


# Backward-compatible alias
CatalogCheckResult = GuardrailResult


def check_system_catalog_access(
    sql: str, default_schema: str = "public"
) -> CatalogCheckResult:
    """
    Check if a SQL query references blocked system catalogs.

    Args:
        sql: Raw SQL query string.
        default_schema: Default schema for unqualified table names.

    Returns:
        CatalogCheckResult indicating whether access is blocked.
    """
    parsed = parse_query(sql, default_schema)

    if parsed.parse_error:
        # If we can't parse it, let other validators handle it
        return CatalogCheckResult(is_blocked=False)

    for table in parsed.tables:
        # Check exact blocked tables
        if table in BLOCKED_SYSTEM_TABLES:
            return CatalogCheckResult(
                is_blocked=True,
                blocked_table=table,
                reason=f"Access to system table '{table}' is blocked.",
            )

        # Check blocked schemas (any table in pg_catalog)
        parts = table.split(".")
        if len(parts) >= 2:
            schema = parts[0]
            if schema in BLOCKED_SCHEMAS:
                return CatalogCheckResult(
                    is_blocked=True,
                    blocked_table=table,
                    reason=f"Access to schema '{schema}' is blocked for raw queries.",
                )

    return CatalogCheckResult(is_blocked=False)
