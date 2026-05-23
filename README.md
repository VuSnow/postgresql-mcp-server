# PostgreSQL-MCP-Server

FastMCP-based PostgreSQL MCP server for schema inspection, metadata retrieval, and safe query execution by AI agents.

## Overview

`postgresql-mcp-server` is a Python MCP server built with [FastMCP](https://github.com/PrefectHQ/fastmcp) that exposes PostgreSQL operations as MCP tools. Designed as the **data access layer** for Text2SQL agents and AI data workflows.

An AI agent connects to this MCP server and can:

1. **Explore the database** — list schemas, tables, columns, indexes, constraints
2. **Run safe queries** — execute SELECT with guardrails (injection protection, auto LIMIT, PII masking)
3. **Write data (opt-in)** — insert, update, delete with write allowlist and destructive-op gating

All operations go through a security pipeline. Read-only by default. No raw database access.

> **Status:** Prototype / internal demo. Current guardrails use regex-based validation.
> Phase 10 (AST-based security with `sqlglot`, column policy, read-only transactions) is planned but not yet implemented.
> See [Implementation Plan](docs/PLAN.md) for details.

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

# Seed sample data (banking schema, idempotent)
./data/seed.sh "$POSTGRESQL_CONNECTION_STRING"

# Run
fastmcp run src/postgresql_mcp/app.py:mcp

# Dev UI
fastmcp dev src/postgresql_mcp/app.py:mcp

# MCP Inspector
npx @modelcontextprotocol/inspector fastmcp run src/postgresql_mcp/app.py:mcp
```

## Configuration

Environment variables (or `.env` file):

### Implemented

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRESQL_CONNECTION_STRING` | *(required)* | PostgreSQL URI (`postgresql://user:pass@host:5432/db`) |
| `READ_ONLY` | `true` | Only allow read/metadata operations |
| `ALLOW_DESTRUCTIVE` | `false` | Allow truncate. Requires `READ_ONLY=false` |
| `WRITE_ALLOWLIST` | *(unset)* | Comma-separated `schema.table` glob patterns for writes |
| `DEFAULT_LIMIT` | `100` | Auto-injected LIMIT for queries without one |
| `MAX_LIMIT` | `1000` | Maximum allowed LIMIT |
| `MAX_QUERY_LENGTH` | `10000` | Max SQL length |
| `QUERY_TIMEOUT_SECONDS` | `300` | Statement timeout |
| `RATE_LIMIT_MAX_CALLS` | `100` | Max queries per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `3600` | Rate limit window |
| `PII_RULES` | *(unset)* | JSON array: `[{"column":"email","method":"hash"}]` |
| `LOG_LEVEL` | `INFO` | Logging level |

### Planned (Phase 10 — not yet implemented)

| Variable | Default | Description |
|----------|---------|-------------|
| `SECURITY_PROFILE` | `general` | Security mode: `general` (permissive), `text2sql` (strict), `sensitive` (strict + require policy file) |
| `ENABLE_WRITE_TOOLS` | `false` | Register write tools with MCP (insert/update/delete) |
| `BLOCK_SELECT_STAR` | `true` | Reject `SELECT *` — force explicit column listing |
| `BLOCK_SUBQUERIES` | `true` | Reject subqueries (all profiles default) |
| `ALLOW_CTE` | `false` | Allow CTE (`WITH`) queries. Ignored until CTE body validation is implemented |
| `ALLOW_SET_OPERATIONS` | `false` | Allow UNION/INTERSECT/EXCEPT. Same safety interlock as CTE |
| `ALLOW_RECURSIVE_CTE` | `false` | Allow recursive CTE. Requires `ALLOW_CTE=true` |
| `COLUMN_POLICY` | *(unset)* | JSON: per-table column/filter/limit policy (includes `sampleable_columns`) |
| `COLUMN_POLICY_FILE` | *(unset)* | Path to policy JSON file (takes priority over `COLUMN_POLICY`) |
| `COLUMN_POLICY_MODE` | `permissive` | `permissive`: unlisted tables allowed. `strict`: unlisted tables rejected. Auto-set by `SECURITY_PROFILE` |
| `ALLOWED_FUNCTIONS` | *(unset)* | JSON array of allowed SQL functions. P0 for text2sql/sensitive (allowlist), P1 for general (blacklist fallback) |
| `MAX_OFFSET` | `10000` | Maximum allowed OFFSET value |
| `MAX_RESULT_ROWS` | `100` | Hard cap on rows returned (post-execute fallback) |
| `MAX_RESULT_BYTES` | `1048576` | Max total serialized result size (1MB) |
| `MAX_CELL_LENGTH` | `4096` | Truncate individual cell values exceeding this |
| `MAX_COLUMNS_RETURNED` | `50` | Reject query if SELECT has too many columns |
| `DEFAULT_SCHEMA` | `public` | Default schema for unqualified table names in policy lookup |
| `USER_CONTEXT_VARIABLE` | *(unset)* | PostgreSQL variable for RLS context (e.g. `app.current_user_id`) |

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

## Sample Data

The `data/` folder contains idempotent SQL seed files for a banking schema (text2sql testing):

| File | Table | Records |
|------|-------|---------|
| `001_customers.sql` | `customers` | 10 customers with KYC info |
| `002_accounts.sql` | `accounts` | 18 accounts (checking/savings/credit/loan) |
| `003_transactions.sql` | `transactions` | 32 transactions (deposit/withdrawal/transfer/payment) |
| `004_cards.sql` | `cards` | 11 debit/credit cards |
| `005_branches.sql` | `branches` | 10 branch offices + ATMs |

```bash
# Run all seed files (safe to re-run)
./data/seed.sh "postgresql://user:pass@localhost:5432/mydb"
```

## Tech Stack

- **[FastMCP](https://github.com/PrefectHQ/fastmcp)** — MCP server framework
- **[asyncpg](https://github.com/MagicStack/asyncpg)** — Async PostgreSQL driver with connection pooling
- **[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** — Config from env vars
- **[pytest](https://docs.pytest.org/)** + **[pytest-asyncio](https://pytest-asyncio.readthedocs.io/)** — Async testing
- **[sqlglot](https://github.com/tobymao/sqlglot)** *(planned — Phase 10)* — SQL AST parser for security validation

## License

Apache-2.0
