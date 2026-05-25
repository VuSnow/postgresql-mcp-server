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
│  asyncpg pool — lazy init, health checks,               │
│  auto-reconnect with exponential backoff                │
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
PRE-EXECUTE                              POST-EXECUTE
┌────────────────────────────────┐       ┌──────────────────────────┐
│ 1. Critical Patterns (regex)   │       │ 7. Result Budget         │
│    defense-in-depth            │       │    row/byte/cell truncate│
│                                │       │                          │
│ 2. RateLimiter                 │       │ 8. PIIMasker             │
│    sliding window              │       │    hash / redact         │
│                                │       │                          │
│ 3. SecurityValidator           │       │ 9. AuditLogger           │
│    injection, DDL, functions   │       │    structured log        │
│                                │       └──────────────────────────┘
│ 4. Statement Guard             │
│    single stmt, shapes         │  → EXECUTE →
│                                │
│ 5. AST Guardrails              │
│    star, columns, functions,   │
│    subqueries, limit/offset    │
│                                │
│ 6. QueryRewriter               │
│    auto LIMIT, cap             │
└────────────────────────────────┘
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

### Security Profiles

```bash
SECURITY_PROFILE=general | text2sql | sensitive
```

| Profile | COLUMN_POLICY_MODE | Metadata filtering | Require policy file | Notes |
|---------|-------------------|-------------------|--------------------|---------|
| `general` (default) | permissive | off | no | Backward compatible, demo/learning |
| `text2sql` | strict | on | recommended | Text2SQL agents, analytics |
| `sensitive` | strict | on | **required** | Banking, PII, production |

All profiles default to `ALLOW_CTE=false` and `BLOCK_SUBQUERIES=true`. Individual configs can be overridden explicitly.

### Defense Philosophy

Don't let Text2SQL agents query raw database freely. Enforce a **semantic layer** — curated views + column allowlist + query policy. Use **AST parsing** (sqlglot) for structural validation, regex only for auxiliary pattern detection.

### Defense-in-Depth Ordering

```
DB privilege / views / RLS          ← PRIMARY security boundary
  → Read-only transaction           ← Engine-level write safety (NOT data-leakage control)
    → AST table + column policy     ← Structural query validation
      → Required filter + LIMIT     ← Mass-leakage prevention
        → Execute query
          → PII masking             ← FALLBACK ONLY (data already left DB)
            → Audit log
```

**Important:** Read-only transaction only prevents writes. It does NOT prevent SELECT leakage, catalog probing, or access to sensitive tables if DB privilege allows it. PII masking is NOT a security boundary — it's best-effort post-execute redaction.

### Key Design Decisions

- Function control: **allowlist** (not blacklist) — only explicitly allowed functions can be called
- Table names: always normalized to `schema.table` (default schema = `public`)
- Aggregates: `COUNT(*)` ≠ `SELECT *` — aggregates exempt from filter requirements
- Subqueries: blocked by default in strict mode (`BLOCK_SUBQUERIES=true`)
- EXPLAIN: allow without ANALYZE only; inner query validated by same policy
- Unqualified columns in multi-table queries: rejected (require `table.column`)
- LIMIT: **reject** if exceeds max (not clamp) — agent self-corrects

### Defense Layers

| Layer | What | Enforced By | Scope |
|-------|------|-------------|-------|
| Read-only transaction | PostgreSQL blocks writes at engine level | asyncpg `transaction(readonly=True)` | Write safety only |
| Single statement + shape validation | Only supported SQL shapes pass | AST structural check | P0 |
| System catalog blocking | Prevent credential/config leakage | AST table extraction | P0 |
| Block SELECT * | Force explicit column selection | AST star detection | P0 |
| Column policy | Only allowed columns returned | AST column extraction | P0 |
| Required filter columns | Prevent mass data dumps | AST WHERE analysis | P0 |
| Metadata tools policy | Filter schema/table/column visibility | Policy-aware service layer | P0 |
| Function allowlist | Block dangerous functions | AST function extraction | P0 (text2sql/sensitive), P1 (general) |
| LIMIT/OFFSET enforcement | Cap result size | AST + reject policy | P0 |
| Result budget | Cap output volume | Post-execute size check | P0 |
| Statement timeout | Prevent DoS queries | `SET LOCAL statement_timeout` | P0 |
| PII masking | Redact sensitive column values (fallback) | Post-execute column match | Fallback |

### Column Policy

Per-table policy controlling what the agent can access:

```json
{
  "public.users": {
    "allowed_columns": ["id", "full_name", "department", "created_at"],
    "sampleable_columns": ["department"],
    "required_filter_columns": ["id", "full_name"],
    "allow_aggregates_without_filter": true,
    "group_by_columns": ["department", "created_at"],
    "max_rows": 20
  }
}
```

**Field semantics:**
- `allowed_columns`: columns that may appear in SELECT/WHERE of `execute_query`
- `sampleable_columns`: columns allowed for `get_column_values` (distinct value enumeration). Subset of `allowed_columns`. Typically dimension/enum columns only — NEVER PII.
- `required_filter_columns`: WHERE must reference at least one with a concrete value
- `max_rows`: per-table LIMIT cap

**Policy modes:**
- `permissive` (default): tables NOT in policy → allow all (backward compatible)
- `strict` (recommended for text2sql/sensitive): tables NOT in policy → rejected

**Aggregate exception:**
- "Pure aggregate" = query where ALL selected expressions are aggregate functions with no row-level columns
- `SELECT COUNT(*) FROM users` → pass
- `SELECT department, COUNT(*) FROM users GROUP BY department` → pass only if `department` is in `group_by_columns`
- `SELECT id, COUNT(*) FROM users GROUP BY id` → blocked (row-level identifier)

### Metadata Tools Policy

In `text2sql` / `sensitive` profile (or when `COLUMN_POLICY_MODE=strict`):

| Tool | Behavior |
|------|----------|
| `list_tables` | Only return tables/views present in column policy |
| `get_table_schema` | Only return `allowed_columns`, hide unlisted columns |
| `get_indexes` / `get_constraints` | Only for policy tables |
| `get_column_values` | Only for `sampleable_columns` (NOT `allowed_columns`) |

Rationale: if only `execute_query` is guarded, the agent can still learn sensitive schema structure via metadata tools. In banking, knowing a table `fraud_flags` or `blacklist_accounts` exists is already information disclosure.

**In `general` profile:** metadata tools operate without filtering (backward compatible).

### Supported SQL Shapes

By default, only these query shapes are allowed through `execute_query`:

| Shape | Default | Config |
|-------|---------|--------|
| Simple SELECT | ✅ allowed | — |
| SELECT with JOIN | ✅ allowed | — |
| GROUP BY / ORDER BY / HAVING | ✅ allowed | — |
| CTE (`WITH ... SELECT`) | ❌ blocked | `ALLOW_CTE=true` |
| UNION / INTERSECT / EXCEPT | ❌ blocked | `ALLOW_SET_OPERATIONS=true` |
| Recursive CTE | ❌ blocked | `ALLOW_RECURSIVE_CTE=true` |
| LATERAL | ❌ blocked | — |
| SELECT INTO | ❌ blocked | — |
| COPY / DO / CALL | ❌ blocked | — |
| Multiple statements (`;`) | ❌ blocked | — |

**CTE validation rules** (when `ALLOW_CTE=true`):
- Every CTE body validated as a normal SELECT (same table/column policy)
- Source tables/columns extracted from CTE body, not CTE alias
- CTE alias is NOT treated as a policy target
- Recursive CTE blocked unless `ALLOW_RECURSIVE_CTE=true`

**Safety interlock:** `ALLOW_CTE=true` is only honored when full CTE body validation is implemented. Until then, CTE is hard-disabled regardless of config.

This prevents bypass like:
```sql
WITH leak AS (SELECT password_hash FROM users)
SELECT * FROM leak;
```
Outer query sees `leak`, but validator traces to `users.password_hash` → blocked.

### Result Budget

Even with column policy and LIMIT, a query can return excessive data if rows are wide or contain large text/JSON:

```bash
MAX_RESULT_ROWS=100        # Hard cap on rows returned
MAX_RESULT_BYTES=1048576   # 1MB max total result size
MAX_CELL_LENGTH=4096       # Truncate individual cell values
MAX_COLUMNS_RETURNED=50    # Reject if SELECT has too many columns
```

**Output size control has two layers:**
1. **Pre-execute (primary):** LIMIT enforcement via AST — reject queries without LIMIT or with LIMIT > max. This prevents fetching excess data into memory.
2. **Post-execute (fallback):** Result budget truncation — caps rows/bytes/cell-length before returning to LLM. Defense against policy bugs or wide-row scenarios.

Prevents:
- Wide-row leakage: `SELECT id, profile_json, full_address, notes FROM users LIMIT 20`
- Large text extraction via JSON/text columns
- Memory exhaustion from unbounded fetches

### Database Setup (Primary Security Boundary)

> **For `text2sql` / `sensitive` deployments, this is REQUIRED — not optional.**
> For local demo / general analytics with `general` profile, direct table access may be acceptable.

The database privilege layer is the **primary security boundary**. MCP guardrails (AST validation, column policy) are the **secondary layer**. If the parser has a bug, DB privileges still prevent access to unauthorized data.

```sql
-- 1. Create restricted user for MCP (NEVER use superuser)
CREATE USER text2sql_reader WITH PASSWORD '...';

-- 2. Create curated views (semantic layer)
CREATE VIEW text2sql.users_view AS
SELECT id, full_name, department, created_at FROM users;

CREATE VIEW text2sql.transactions_view AS
SELECT id, amount, transaction_type, status, created_at FROM transactions;

-- 3. Grant only on views, NOT raw tables
GRANT USAGE ON SCHEMA text2sql TO text2sql_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA text2sql TO text2sql_reader;
REVOKE ALL ON users FROM text2sql_reader;
REVOKE ALL ON transactions FROM text2sql_reader;

-- 4. Row-Level Security (if multi-tenant)
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_txn_policy ON transactions
  FOR SELECT USING (owner_id = current_setting('app.current_user_id'));
```

**The MCP server MUST connect as `text2sql_reader`, not as superuser or table owner.**

Why this matters:
- MCP guardrails are a single point of failure — one parser edge case = data leak
- DB privileges are enforced by PostgreSQL engine regardless of application bugs
- Even if AST validator is bypassed, `text2sql_reader` cannot see raw tables

## Project Structure

```
src/postgresql_mcp/
├── app.py              # Entry point — imports tools, exposes mcp
├── server.py           # Shared state — mcp instance, configs, services, lifespan
├── configs.py          # Pydantic-settings (env vars)
├── logging_config.py   # Structured JSON logging (stdout, ELK/CloudWatch ready)
├── clients/
│   ├── base.py         # BasePostgreSQLClient — pool lifecycle (configurable size)
│   ├── create.py       # CreateMixin — parameterized INSERT
│   ├── metadata.py     # MetadataMixin — schema/table/index queries
│   ├── read.py         # ReadMixin — raw execute, explain
│   ├── update.py       # UpdateMixin — parameterized UPDATE
│   ├── delete.py       # DeleteMixin — parameterized DELETE, TRUNCATE
│   └── utils.py        # validate_identifier()
├── services/
│   ├── connection_manager.py  # Singleton state machine + retry with backoff
│   └── postgresql/
│       ├── base.py     # BaseService — validation + write policy
│       ├── create.py   # CreateService
│       ├── metadata.py # MetadataService
│       ├── read.py     # ReadService (with guardrails pipeline)
│       ├── update.py   # UpdateService (WHERE mandatory)
│       └── delete.py   # DeleteService (ALLOW_DESTRUCTIVE gating)
├── guardrails/
│   ├── __init__.py     # GuardrailsPipeline + create_pipeline()
│   ├── models.py       # GuardrailResult, TablePolicy, AuditEntry
│   ├── sql_parser.py   # Reusable SQL AST extraction (sqlglot)
│   ├── audit_logger.py # Capped deque (AUDIT_MAX_ENTRIES) + structured log
│   ├── pii_masker.py
│   ├── query_rewriter.py
│   ├── rate_limiter.py
│   ├── security_validator.py
│   ├── critical_patterns.py   # Phase 10.17: regex defense-in-depth
│   ├── subquery_blocker.py    # Phase 10.9: block subqueries/CTE/set-ops
│   ├── explain_guard.py       # Phase 10.10: EXPLAIN safety
│   ├── limit_guard.py         # Phase 10.11: LIMIT/OFFSET enforcement
│   ├── user_context.py        # Phase 10.12: RLS user context (SET LOCAL)
│   ├── statement_guard.py     # Phase 10.14: single statement + shapes
│   ├── metadata_filter.py     # Phase 10.15: metadata tools policy
│   └── result_budget.py       # Phase 10.16: row/byte/cell truncation
└── tools/
    ├── connection.py   # connect, disconnect, get_status (with health check)
    ├── create.py       # insert_one, insert_many
    ├── delete.py       # delete, truncate_table
    ├── metadata.py     # list_schemas, list_tables, get_table_schema, ...
    ├── read.py         # execute_query, dry_run_query, explain_query
    └── update.py       # update (WHERE mandatory)
```

## Production Hardening

### Lifecycle Management

The server uses FastMCP's `lifespan` async context manager for graceful startup/shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastMCP):
    logger.info("Starting PostgreSQL MCP Server...")
    try:
        yield
    finally:
        await connection_manager.disconnect()  # close pool cleanly
```

This ensures the connection pool is closed on SIGTERM/SIGINT — no connection leaks.

### Structured Logging

All logs are emitted as single-line JSON to stdout (`logging_config.py`):

```json
{"timestamp": "2026-05-24T10:00:00+0000", "level": "INFO", "logger": "postgresql_mcp.audit", "message": "Query executed", "audit": {...}}
```

Configured via `LOG_LEVEL` env var. Compatible with CloudWatch, ELK, Datadog.

### Connection Resilience

`ensure_connected()` retries with exponential backoff on transient failures:

```bash
CONNECT_MAX_RETRIES=3       # Max retry attempts
CONNECT_BASE_DELAY=1.0      # Initial delay (seconds)
CONNECT_MAX_DELAY=10.0      # Cap on delay between retries
```

Sequence: attempt → fail → sleep 1s → attempt → fail → sleep 2s → attempt → fail → raise.

### Connection Pool

Pool size is tunable via env vars:

```bash
POOL_MIN_SIZE=1     # Minimum idle connections
POOL_MAX_SIZE=10    # Maximum concurrent connections
```

### Audit Log Memory

In-memory audit entries are capped via `deque(maxlen=AUDIT_MAX_ENTRIES)` (default 10,000).
Oldest entries are evicted when the cap is reached. All entries are also emitted as
structured log lines, so no data is lost — just not retained in process memory.

### Docker

- Non-root user (`appuser`) for container security
- `pip install .` (not editable) for reproducible builds
- Health check verifies server process is alive
- Production deps only (no pytest in image)
