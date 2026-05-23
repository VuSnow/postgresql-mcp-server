"""
Phase 10.6 — WHERE Clause Sanitization for Write Ops tests.

Tests that UPDATE/DELETE WHERE clauses are sanitized against:
- Stacked queries (;)
- SQL comments (-- and /* */)
- Subqueries (SELECT)
- DDL/DCL keywords (CREATE, ALTER, DROP, TRUNCATE, GRANT, REVOKE, COPY)
"""

import pytest

from postgresql_mcp.services.postgresql.base import BaseService
from postgresql_mcp.services.connection_manager import ConnectionManager
from postgresql_mcp.configs import ServerConfigs


# ─── Helpers ─────────────────────────────────────────────────────────────────


@pytest.fixture
def service():
    """Create a BaseService instance for testing."""
    configs = ServerConfigs(
        POSTGRESQL_CONNECTION_STRING="postgresql://test:test@localhost:5432/testdb",
    )
    manager = ConnectionManager(configs)
    return BaseService(manager, configs)


# ─── Blocked patterns ────────────────────────────────────────────────────────


class TestWhereClauseBlocked:
    """WHERE clauses with dangerous patterns are rejected."""

    def test_stacked_query_semicolon(self, service):
        with pytest.raises(ValueError, match="stacked queries"):
            service._validate_where_clause("id = 1; DROP TABLE users")

    def test_semicolon_at_end(self, service):
        with pytest.raises(ValueError, match="stacked queries"):
            service._validate_where_clause("id = 1;")

    def test_line_comment(self, service):
        with pytest.raises(ValueError, match="comments"):
            service._validate_where_clause("id = 1 -- always true")

    def test_block_comment(self, service):
        with pytest.raises(ValueError, match="block comments"):
            service._validate_where_clause("id = 1 /* bypass */")

    def test_subquery_select(self, service):
        with pytest.raises(ValueError, match="subqueries"):
            service._validate_where_clause("id IN (SELECT id FROM admin_users)")

    def test_subquery_case_insensitive(self, service):
        with pytest.raises(ValueError, match="subqueries"):
            service._validate_where_clause("id IN (select id from admin_users)")

    def test_ddl_create(self, service):
        with pytest.raises(ValueError, match="DDL/DCL"):
            service._validate_where_clause("id = 1 AND CREATE TABLE x()")

    def test_ddl_drop(self, service):
        with pytest.raises(ValueError, match="DDL/DCL"):
            service._validate_where_clause("id = 1 AND DROP TABLE users")

    def test_ddl_alter(self, service):
        with pytest.raises(ValueError, match="DDL/DCL"):
            service._validate_where_clause("id = 1 AND ALTER TABLE users")

    def test_ddl_truncate(self, service):
        with pytest.raises(ValueError, match="DDL/DCL"):
            service._validate_where_clause("id = 1 AND TRUNCATE users")

    def test_dcl_grant(self, service):
        with pytest.raises(ValueError, match="DDL/DCL"):
            service._validate_where_clause("id = 1 AND GRANT ALL ON users TO attacker")

    def test_dcl_revoke(self, service):
        with pytest.raises(ValueError, match="DDL/DCL"):
            service._validate_where_clause("id = 1 AND REVOKE ALL")

    def test_copy_command(self, service):
        with pytest.raises(ValueError, match="DDL/DCL"):
            service._validate_where_clause("id = 1 AND COPY users TO '/tmp/dump'")


# ─── Allowed patterns ────────────────────────────────────────────────────────


class TestWhereClauseAllowed:
    """Legitimate WHERE clauses pass validation."""

    def test_simple_equality(self, service):
        service._validate_where_clause("id = $1")

    def test_multiple_conditions(self, service):
        service._validate_where_clause("id = $1 AND status = $2")

    def test_comparison_operators(self, service):
        service._validate_where_clause("amount > $1 AND created_at < $2")

    def test_in_list(self, service):
        service._validate_where_clause("id IN ($1, $2, $3)")

    def test_like_pattern(self, service):
        service._validate_where_clause("name LIKE $1")

    def test_is_null(self, service):
        service._validate_where_clause("deleted_at IS NULL AND id = $1")

    def test_between(self, service):
        service._validate_where_clause("created_at BETWEEN $1 AND $2")

    def test_not_clause(self, service):
        service._validate_where_clause("NOT (status = $1)")

    def test_empty_string_noop(self, service):
        """Empty/None doesn't raise (handled by caller)."""
        service._validate_where_clause("")
        service._validate_where_clause(None)

    def test_column_named_selection(self, service):
        """Column name containing 'select' substring is fine — regex uses word boundary."""
        service._validate_where_clause("selection_type = $1")

    def test_column_named_created_at(self, service):
        """Column 'created_at' contains 'create' substring — fine with word boundary."""
        service._validate_where_clause("created_at > $1")
