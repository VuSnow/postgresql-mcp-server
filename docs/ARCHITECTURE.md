# Architecture

## Overview

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

## Why asyncpg?

- Pure async — natural fit for FastMCP's async tool handlers
- Built-in connection pooling — handles concurrent MCP tool calls
- Fastest Python PostgreSQL driver (binary protocol, no libpq dependency)

## Guardrails Pipeline

Every `execute_query` passes through this pipeline:

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

## Write Policy

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

## Security Model (Phase 10)

### Threat Model for Text2SQL Agents

```
1. Unauthorized data access     — agent queries tables it shouldn't see
2. Mass data leakage            — SELECT * FROM users WHERE '1'='1' dumps everything
3. Sensitive column exposure     — password_hash, api_key, ssn returned in results
4. Over-broad queries           — no WHERE clause on PII tables
5. Expensive/DoS queries        — cartesian joins, full table scans, huge OFFSET
6. System catalog probing       — pg_shadow, pg_authid reveal credentials
```

### Defense Philosophy

Don't let Text2SQL agents query raw database freely. Enforce a **semantic layer** — curated views + column allowlist + query policy. Use **AST parsing** (sqlglot) for structural validation, regex only for auxiliary pattern detection.

### Key Design Decisions

- Function control: **allowlist** (not blacklist) — only explicitly allowed functions can be called
- Table names: always normalized to `schema.table` (default schema = `public`)
- Aggregates: `COUNT(*)` ≠ `SELECT *` — aggregates exempt from filter requirements
- Subqueries: blocked by default in strict mode (`BLOCK_SUBQUERIES=true`)
- EXPLAIN: allow without ANALYZE only; inner query validated by same policy
- Unqualified columns in multi-table queries: rejected (require `table.column`)
- LIMIT: **reject** if exceeds max (not clamp) — agent self-corrects

### Defense Layers

| Layer | What | Enforced By |
|-------|------|-------------|
| Read-only transaction | PostgreSQL blocks writes at engine level | asyncpg `transaction(readonly=True)` |
| System catalog blocking | Prevent credential/config leakage | AST table extraction |
| Block SELECT * | Force explicit column selection | AST star detection |
| Column policy | Only allowed columns returned | AST column extraction |
| Required filter columns | Prevent mass data dumps | AST WHERE analysis |
| Function allowlist | Block dangerous functions | AST function extraction |
| LIMIT/OFFSET enforcement | Cap result size | AST + reject policy |
| Statement timeout | Prevent DoS queries | `SET LOCAL statement_timeout` |
| PII masking | Redact sensitive column values | Post-execute column match |

### Column Policy

Per-table policy controlling what the agent can access:

```json
{
  "public.users": {
    "allowed_columns": ["id", "full_name", "department", "created_at"],
    "required_filter_columns": ["id", "full_name"],
    "allow_aggregates_without_filter": true,
    "group_by_columns": ["department", "created_at"],
    "max_rows": 20
  }
}
```

**Policy modes:**
- `permissive` (default): tables NOT in policy → allow all (backward compatible)
- `strict` (recommended for production): tables NOT in policy → rejected

**Aggregate exception:**
- "Pure aggregate" = query where ALL selected expressions are aggregate functions with no row-level columns
- `SELECT COUNT(*) FROM users` → pass
- `SELECT department, COUNT(*) FROM users GROUP BY department` → pass only if `department` is in `group_by_columns`
- `SELECT id, COUNT(*) FROM users GROUP BY id` → blocked (row-level identifier)

### Recommended Database Setup

These are **strongly recommended** for production — not optional nice-to-haves:

```sql
-- 1. Create restricted user for MCP (NEVER use superuser)
CREATE USER text2sql_reader WITH PASSWORD '...';

-- 2. Create curated views (semantic layer)
CREATE VIEW text2sql_users AS
SELECT id, full_name, department, created_at FROM users;

CREATE VIEW text2sql_transactions AS
SELECT id, amount, transaction_type, status, created_at FROM transactions;

-- 3. Grant only on views, NOT raw tables
GRANT SELECT ON text2sql_users TO text2sql_reader;
GRANT SELECT ON text2sql_transactions TO text2sql_reader;
REVOKE ALL ON users FROM text2sql_reader;

-- 4. Row-Level Security (if multi-tenant)
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_txn_policy ON transactions
  FOR SELECT USING (owner_id = current_setting('app.current_user_id'));
```

**The MCP server MUST connect as `text2sql_reader`, not as superuser or table owner.**

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
│   ├── delete.py       # DeleteMixin — parameterized DELETE, TRUNCATE
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
