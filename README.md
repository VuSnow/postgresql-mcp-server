# PostgreSQL-MCP-Server

FastMCP-based PostgreSQL MCP server for schema inspection, metadata retrieval, and safe query execution by AI agents.

## Overview

`postgresql-mcp-server` is a Python MCP server built with [FastMCP](https://github.com/PrefectHQ/fastmcp) that exposes PostgreSQL operations as MCP tools. Designed as the **data access layer** for Text2SQL agents and AI data workflows.

## What This Server Does

An AI agent connects to this MCP server and can:

1. **Explore the database** — list schemas, tables, columns, indexes, constraints
2. **Run safe queries** — execute SELECT with guardrails (injection protection, auto LIMIT, PII masking)
3. **Write data (opt-in)** — insert, update, delete with write allowlist and destructive-op gating

All operations go through a security pipeline. Read-only by default. No raw database access.

## Design Principles

| Principle | How |
|-----------|-----|
| **Production-safe defaults** | Read-only mode, rate limiting, query timeout, max query length — all on by default |
| **Defense in depth** | Every query passes through: RateLimiter → SecurityValidator → QueryRewriter → execute → PIIMasker → AuditLogger |
| **Opt-in writes** | 3-layer write gating: `READ_ONLY` → `ALLOW_DESTRUCTIVE` → `WRITE_ALLOWLIST` |
| **LLM-friendly output** | All tools return formatted strings, not raw dicts — optimized for agent consumption |
| **Zero config to start** | Only `POSTGRESQL_CONNECTION_STRING` required. Everything else has sensible defaults |

## Architecture

3-layer architecture, same pattern as [bigquery-mcp-server](../bigquery-mcp-server) and [mongodb-mcp-server](../mongodb-mcp-server):

```
┌─────────────────────────────────────────────────────────┐
│  Tools Layer                                            │
│  Thin MCP tool wrappers — defines schema, formats       │
│  output for LLM, top-level try/except                   │
├─────────────────────────────────────────────────────────┤
│  Services Layer                                         │
│  Business logic — auto-connect, input validation,       │
│  guardrails pipeline, write policy enforcement          │
├─────────────────────────────────────────────────────────┤
│  Clients Layer                                          │
│  Pure asyncpg calls — no business logic, no error       │
│  handling, just translates params → SQL operations      │
├─────────────────────────────────────────────────────────┤
│  Connection Manager (singleton)                         │
│  asyncpg pool — lazy init, health checks                │
└─────────────────────────────────────────────────────────┘
            │
            ▼
       PostgreSQL (via asyncpg)
```

### Why asyncpg?

- Pure async — natural fit for FastMCP's async tool handlers
- Built-in connection pooling — handles concurrent MCP tool calls
- Fastest Python PostgreSQL driver (binary protocol, no libpq dependency)

### Guardrails Pipeline

Every `execute_query` passes through this pipeline (borrowed from bigquery-mcp-server, adapted for PostgreSQL):

```
PRE-EXECUTE                          POST-EXECUTE
┌──────────────────────┐             ┌──────────────────────┐
│ 1. RateLimiter       │             │ 4. PIIMasker         │
│    sliding window    │             │    hash / redact     │
│                      │             │                      │
│ 2. SecurityValidator │             │ 5. AuditLogger       │
│    injection, DDL,   │  → EXECUTE →│    structured log    │
│    forbidden kw      │             │                      │
│                      │             └──────────────────────┘
│ 3. QueryRewriter     │
│    auto LIMIT, cap   │
└──────────────────────┘
```

### Write Policy (from MongoDB pattern)

```
_check_write_allowed()         → READ_ONLY=false?
_check_destructive_allowed()   → ALLOW_DESTRUCTIVE=true? (truncate only)
_check_write_target()          → WRITE_ALLOWLIST match? (schema.table glob)
```

| `READ_ONLY` | `ALLOW_DESTRUCTIVE` | Allowed |
|---|---|---|
| `true` (default) | *(ignored)* | Read + metadata only |
| `false` | `false` (default) | insert, update |
| `false` | `true` | + delete, truncate |

## Configuration

Environment variables (or `.env` file):

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

## Implementation Plan

### Phase 1 — Project Scaffold ✅

> Goal: runnable FastMCP server with `get_status` tool, zero PostgreSQL logic yet.

- `pyproject.toml` — deps: `fastmcp`, `asyncpg`, `pydantic-settings`, dev: `pytest`, `pytest-asyncio`
- `src/postgresql_mcp/app.py` — FastMCP entry point
- `src/postgresql_mcp/configs.py` — pydantic-settings model (all env vars above)
- `.env.example`, `pytest.ini`, `.gitignore`
- Verify: `fastmcp dev src/postgresql_mcp/app.py:mcp` starts without error

### Phase 2 — Client Layer (asyncpg) ✅

> Goal: pure database calls, no business logic. Mixin composition pattern.

- `clients/base.py` — `BasePostgreSQLClient`: create pool, close, ping
- `clients/metadata.py` — `MetadataMixin`: list_schemas, list_tables, get_table_schema, get_indexes, get_constraints, get_column_values (all via `information_schema` / `pg_catalog` queries)
- `clients/read.py` — `ReadMixin`: execute_query (raw), explain_query
- `clients/utils.py` — `validate_identifier()` for SQL identifier safety
- `clients/__init__.py` — `PostgreSQLClient(BasePostgreSQLClient, MetadataMixin, ReadMixin)`

### Phase 3 — Connection Manager + Base Service ✅

> Goal: singleton lifecycle management, auto-connect, input validation.

- `services/connection_manager.py` — state machine: `disconnected → connecting → connected → error`. Lazy pool creation, health check, reconnect
- `services/postgresql/base.py` — `BaseService`: `ensure_connected()`, `_validate_identifier()`, `_validate_table_name()`, `_check_write_allowed()`, `_check_destructive_allowed()`, `_check_write_target()`
- Unit tests: 36 tests — state transitions, validation edge cases, write policy enforcement (all passing)

### Phase 4 — Guardrails Pipeline ✅

> Goal: production security layer. Each module is independent and testable in isolation.

- `guardrails/security_validator.py` — forbidden keywords (DROP, DELETE, ALTER, GRANT...), SQL injection patterns, dangerous functions, comment stripping, query length. Adapted from bigquery-mcp-server.
- `guardrails/query_rewriter.py` — auto LIMIT injection if missing, cap LIMIT to `MAX_LIMIT`, skip for pure aggregates, CTE-aware
- `guardrails/rate_limiter.py` — thread-safe sliding-window (configurable calls/window)
- `guardrails/pii_masker.py` — case-insensitive column match, hash (SHA-256 truncated) or redact
- `guardrails/audit_logger.py` — structured log: query, rows returned, duration, blocked reason
- `guardrails/__init__.py` — `GuardrailsPipeline`: orchestrates pre-execute → execute → post-execute
- Unit tests: **heavy coverage** — injection bypass attempts, edge cases, concurrent rate limiting

### Phase 5 — Metadata Service + Tools ✅

> Goal: first usable tools — agent can explore database structure.

- `services/postgresql/metadata.py` — `MetadataService`: delegates to client, formats output
- `tools/postgresql/metadata.py` — MCP tools: `list_schemas`, `list_tables`, `get_table_schema`, `get_indexes`, `get_constraints`, `get_column_values`
- `tools/connection.py` — `connect`, `disconnect`, `get_status`
- All tools return LLM-friendly strings (not raw dicts)
- Unit tests: service logic + tool output formatting

### Phase 6 — Read Service + Query Tools ✅

> Goal: agent can execute SQL with full guardrails pipeline.

- `services/postgresql/read.py` — `ReadService`: integrates GuardrailsPipeline, statement timeout via asyncpg
- `tools/postgresql/read.py` — MCP tools: `execute_query`, `dry_run_query` (EXPLAIN only), `explain_query` (EXPLAIN ANALYZE, multi-format)
- `dry_run_query` only applies SecurityValidator (no rewrite/PII since no data returned)
- Unit tests: end-to-end pipeline, timeout handling, error formatting

### Phase 7 — Write Service + Tools ✅

> Goal: opt-in write support with safety constraints.

- `clients/create.py` — `CreateMixin`: parameterized INSERT (single + batch)
- `clients/update.py` — `UpdateMixin`: parameterized UPDATE
- `services/postgresql/create.py` — `CreateService`: write policy check → delegate
- `services/postgresql/update.py` — `UpdateService`: write policy check, **require WHERE clause**
- `tools/create.py` — `insert_one`, `insert_many`
- `tools/update.py` — `update` (WHERE mandatory — no accidental full-table updates)
- All write operations use parameterized queries (never string interpolation)
- Unit tests: 24 tests — policy enforcement, allowlist matching, validation, parameterization

### Phase 8 — Delete Service + Tools ✅

> Goal: destructive operations with extra gating.

- `clients/delete.py` — `DeleteMixin`: parameterized DELETE, TRUNCATE
- `services/postgresql/delete.py` — `DeleteService`: write policy + destructive policy check
- `tools/delete.py` — `delete` (WHERE mandatory), `truncate_table` (requires `ALLOW_DESTRUCTIVE=true`)
- Unit tests: 17 tests — destructive gating, validation, success paths
- Integration tests: 10 tests — real INSERT/UPDATE/DELETE/TRUNCATE against PostgreSQL

### Phase 9 — Hardening + Final Tests ✅

> Goal: production-ready quality bar.

- 54 hardening tests covering:
  - SQL injection bypass attempts (CRLF, null byte, stacked queries, comment-based, Unicode homoglyphs)
  - Identifier validation edge cases (special chars, injection via identifiers)
  - Connection resilience (double connect, disconnect when not connected, reconnect after error)
  - Graceful shutdown (pool cleanup, idempotent disconnect)
- Total: **329 tests** (276 unit + 43 integration + 10 write integration)

### Status Tracker

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Project scaffold | ✅ Done |
| 2 | Client layer (asyncpg) | ✅ Done |
| 3 | Connection manager + base service | ✅ Done |
| 4 | Guardrails pipeline | ✅ Done |
| 5 | Metadata service + tools | ✅ Done |
| 6 | Read service + query tools | ✅ Done |
| 7 | Write service + tools | ✅ Done |
| 8 | Delete service + tools | ✅ Done |
| 9 | Hardening + final tests | ✅ Done |

## Project Structure

```
src/postgresql_mcp/
├── app.py              # Entry point — imports tools, exposes mcp
├── server.py           # Shared state — mcp instance, configs, services
├── configs.py          # Pydantic-settings (env vars)
├── clients/
│   ├── base.py         # BasePostgreSQLClient — pool lifecycle
│   ├── create.py       # CreateMixin — parameterized INSERT
│   ├── metadata.py     # MetadataMixin — schema/table/index queries
│   ├── read.py         # ReadMixin — raw execute, explain
│   ├── update.py       # UpdateMixin — parameterized UPDATE
│   └── utils.py        # validate_identifier()
├── services/
│   ├── connection_manager.py  # Singleton state machine
│   └── postgresql/
│       ├── base.py     # BaseService — validation + write policy
│       ├── create.py   # CreateService
│       ├── metadata.py # MetadataService
│       ├── read.py     # ReadService (with guardrails pipeline)
│       ├── update.py   # UpdateService (WHERE mandatory)
│       └── delete.py   # DeleteService (ALLOW_DESTRUCTIVE gating)
├── guardrails/
│   ├── __init__.py     # GuardrailsPipeline + create_pipeline()
│   ├── audit_logger.py
│   ├── pii_masker.py
│   ├── query_rewriter.py
│   ├── rate_limiter.py
│   └── security_validator.py
└── tools/
    ├── connection.py   # connect, disconnect, get_status
    ├── create.py       # insert_one, insert_many
    ├── delete.py       # delete, truncate_table
    ├── metadata.py     # list_schemas, list_tables, get_table_schema, ...
    ├── read.py         # execute_query, dry_run_query, explain_query
    └── update.py       # update (WHERE mandatory)
```

## MCP Tools Reference

| Tool | Description | Returns |
|------|-------------|---------|
| `connect` | Connect to PostgreSQL using configured connection string | `{"result": "Connected ..."}` |
| `disconnect` | Disconnect from the database | `{"result": "Disconnected"}` |
| `get_status` | Get connection status and server info | `{"result": {...}}` |
| `list_schemas` | List all schemas in the database | `{"result": [...]}` |
| `list_tables` | List tables in a schema (default: public) | `{"result": [...]}` |
| `get_table_schema` | Get column definitions for a table | `{"result": [...]}` |
| `list_indexes` | List indexes on a table | `{"result": [...]}` |
| `get_foreign_keys` | Get foreign key relationships | `{"result": [...]}` |
| `get_table_stats` | Get row count and size estimates | `{"result": {...}}` |
| `execute_query` | Execute a read-only SQL query (through guardrails) | `{"result": [...]}` |
| `dry_run_query` | Validate a query without executing | `{"result": "Query is valid"}` |
| `explain_query` | Get the EXPLAIN plan for a query | `{"result": "..."}` |
| `insert_one` | Insert a single row into a table | `{"result": "Inserted 1 row ..."}` |
| `insert_many` | Insert multiple rows into a table | `{"result": "Inserted N row(s)"}` |
| `update` | Update rows matching a WHERE condition | `{"result": "Updated N row(s)"}` |
| `delete` | Delete rows matching a WHERE condition | `{"result": "Deleted N row(s)"}` |
| `truncate_table` | Truncate a table (requires ALLOW_DESTRUCTIVE) | `{"result": "Truncated ..."}` |

All tools return `{"error": "..."}` on failure.

## Tech Stack

- **[FastMCP](https://github.com/PrefectHQ/fastmcp)** — MCP server framework
- **[asyncpg](https://github.com/MagicStack/asyncpg)** — Async PostgreSQL driver with connection pooling
- **[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** — Config from env vars
- **[pytest](https://docs.pytest.org/)** + **[pytest-asyncio](https://pytest-asyncio.readthedocs.io/)** — Async testing

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

## License

Apache-2.0
