# PostgreSQL-MCP-Server

FastMCP-based PostgreSQL MCP server for schema inspection, metadata retrieval, and safe query execution by AI agents.

## Overview

`postgresql-mcp-server` is a Python MCP server built with [FastMCP](https://github.com/PrefectHQ/fastmcp) that exposes PostgreSQL operations as MCP tools. Designed as the **data access layer** for Text2SQL agents and AI data workflows.

An AI agent connects to this MCP server and can:

1. **Explore the database** — list schemas, tables, columns, indexes, constraints
2. **Run safe queries** — execute SELECT with guardrails (injection protection, auto LIMIT, PII masking)
3. **Write data (opt-in)** — insert, update, delete with write allowlist and destructive-op gating

All operations go through a security pipeline. Read-only by default. No raw database access.

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design, layer diagram, guardrails pipeline, security model, project structure |
| [Implementation Plan](docs/PLAN.md) | Phase-by-phase progress, Phase 10 security hardening details |

## Design Principles

| Principle | How |
|-----------|-----|
| **Production-safe defaults** | Read-only mode, rate limiting, query timeout, max query length — all on by default |
| **Defense in depth** | Every query passes through: RateLimiter → SecurityValidator → QueryRewriter → execute → PIIMasker → AuditLogger |
| **Opt-in writes** | 3-layer write gating: `READ_ONLY` → `ALLOW_DESTRUCTIVE` → `WRITE_ALLOWLIST` |
| **LLM-friendly output** | All tools return formatted strings, not raw dicts — optimized for agent consumption |
| **Zero config to start** | Only `POSTGRESQL_CONNECTION_STRING` required. Everything else has sensible defaults |

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Configure
export POSTGRESQL_CONNECTION_STRING="postgresql://user:password@localhost:5432/mydb"

# Run
fastmcp run src/postgresql_mcp/app.py:mcp

# Dev UI
fastmcp dev src/postgresql_mcp/app.py:mcp

# MCP Inspector
npx @modelcontextprotocol/inspector fastmcp run src/postgresql_mcp/app.py:mcp
```

## Configuration

Environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRESQL_CONNECTION_STRING` | *(required)* | PostgreSQL URI (`postgresql://user:pass@host:5432/db`) |
| `READ_ONLY` | `true` | Only allow read/metadata operations |
| `ALLOW_DESTRUCTIVE` | `false` | Allow truncate. Requires `READ_ONLY=false` |
| `WRITE_ALLOWLIST` | *(unset)* | Comma-separated `schema.table` glob patterns for writes |
| `ENABLE_WRITE_TOOLS` | `false` | Register write tools with MCP (insert/update/delete) |
| `BLOCK_SELECT_STAR` | `true` | Reject `SELECT *` — force explicit column listing |
| `BLOCK_SUBQUERIES` | `true` | Reject subqueries in strict mode |
| `COLUMN_POLICY` | *(unset)* | JSON: per-table column/filter/limit policy |
| `COLUMN_POLICY_FILE` | *(unset)* | Path to policy JSON file (takes priority over `COLUMN_POLICY`) |
| `COLUMN_POLICY_MODE` | `permissive` | `permissive`: unlisted tables allowed. `strict`: unlisted tables rejected |
| `ALLOWED_FUNCTIONS` | *(unset)* | JSON array of allowed SQL functions (if set, acts as allowlist) |
| `MAX_OFFSET` | `10000` | Maximum allowed OFFSET value |
| `DEFAULT_SCHEMA` | `public` | Default schema for unqualified table names in policy lookup |
| `USER_CONTEXT_VARIABLE` | *(unset)* | PostgreSQL variable for RLS context (e.g. `app.current_user_id`) |
| `DEFAULT_LIMIT` | `100` | Auto-injected LIMIT for queries without one |
| `MAX_LIMIT` | `1000` | Maximum allowed LIMIT |
| `MAX_QUERY_LENGTH` | `10000` | Max SQL length |
| `QUERY_TIMEOUT_SECONDS` | `300` | Statement timeout |
| `RATE_LIMIT_MAX_CALLS` | `100` | Max queries per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `3600` | Rate limit window |
| `PII_RULES` | *(unset)* | JSON array: `[{"column":"email","method":"hash"}]` |
| `LOG_LEVEL` | `INFO` | Logging level |

## MCP Tools Reference

### Connection

| Tool | Description | Parameters |
|------|-------------|------------|
| `connect` | Connect to PostgreSQL using configured connection string | *(none)* |
| `disconnect` | Disconnect from the database | *(none)* |
| `get_status` | Get connection status and server info | *(none)* |

### Metadata

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_schemas` | List all schemas in the database | *(none)* |
| `list_tables` | List tables in a schema | • `schema` (default: `"public"`): Schema to list tables from |
| `get_table_schema` | Get column definitions for a table | • `table_name` (REQUIRED): Table to inspect<br>• `schema` (default: `"public"`): Schema containing the table |
| `get_indexes` | List indexes on a table | • `table_name` (REQUIRED): Table to inspect<br>• `schema` (default: `"public"`): Schema containing the table |
| `get_constraints` | Get constraints (PK, FK, UNIQUE, CHECK) | • `table_name` (REQUIRED): Table to inspect<br>• `schema` (default: `"public"`): Schema containing the table |
| `get_column_values` | Get distinct values for a column | • `table_name` (REQUIRED): Table to sample from<br>• `column` (REQUIRED): Column name to get values for<br>• `schema` (default: `"public"`): Schema containing the table<br>• `limit` (default: `50`): Max distinct values to return |

### Query

| Tool | Description | Parameters |
|------|-------------|------------|
| `execute_query` | Execute a read-only SQL query (through guardrails) | • `query` (REQUIRED): SQL SELECT statement |
| `dry_run_query` | Validate a query without executing | • `query` (REQUIRED): SQL query to validate |
| `explain_query` | Get the EXPLAIN plan for a query | • `query` (REQUIRED): SQL query to explain<br>• `analyze` (default: `false`): Execute query for real timings<br>• `format` (default: `"text"`): Output format — text/json/xml/yaml |

### Write (requires `ENABLE_WRITE_TOOLS=true`)

| Tool | Description | Parameters |
|------|-------------|------------|
| `insert_one` | Insert a single row | • `table_name` (REQUIRED): Target table<br>• `data` (REQUIRED): Column→value mapping, e.g. `{"name": "Alice"}`<br>• `schema` (default: `"public"`): Schema containing the table |
| `insert_many` | Insert multiple rows | • `table_name` (REQUIRED): Target table<br>• `columns` (REQUIRED): List of column names<br>• `rows` (REQUIRED): List of value lists (one per row)<br>• `schema` (default: `"public"`): Schema containing the table |
| `update` | Update rows matching WHERE | • `table_name` (REQUIRED): Target table<br>• `set_data` (REQUIRED): Column→value mapping for SET<br>• `where_clause` (REQUIRED): WHERE expression with `$N` params<br>• `where_values` (default: `null`): Values for WHERE params<br>• `schema` (default: `"public"`): Schema containing the table |
| `delete` | Delete rows matching WHERE (requires `ALLOW_DESTRUCTIVE=true`) | • `table_name` (REQUIRED): Target table<br>• `where_clause` (REQUIRED): WHERE expression with `$N` params<br>• `where_values` (default: `null`): Values for WHERE params<br>• `schema` (default: `"public"`): Schema containing the table |
| `truncate_table` | Truncate a table (requires `ALLOW_DESTRUCTIVE=true`) | • `table_name` (REQUIRED): Table to truncate<br>• `schema` (default: `"public"`): Schema containing the table |

All tools return `{"result": "..."}` on success or `{"error": "..."}` on failure.

## Testing

```bash
# Unit tests only (no DB required)
pytest

# Integration tests (requires running PostgreSQL)
POSTGRESQL_CONNECTION_STRING="postgresql://user:pass@localhost:5432/dbname" pytest -m integration

# All tests
POSTGRESQL_CONNECTION_STRING="postgresql://user:pass@localhost:5432/dbname" pytest
```

Integration tests auto-skip when the database is unavailable.

## Tech Stack

- **[FastMCP](https://github.com/PrefectHQ/fastmcp)** — MCP server framework
- **[asyncpg](https://github.com/MagicStack/asyncpg)** — Async PostgreSQL driver with connection pooling
- **[sqlglot](https://github.com/tobymao/sqlglot)** — SQL AST parser for security validation
- **[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** — Config from env vars
- **[pytest](https://docs.pytest.org/)** + **[pytest-asyncio](https://pytest-asyncio.readthedocs.io/)** — Async testing

## License

Apache-2.0
