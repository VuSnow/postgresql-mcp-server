# Implementation Plan

## Status Tracker

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
| 10 | SQL injection & data leakage hardening | 🔒 Planned |

---

## Phase 1 — Project Scaffold ✅

> Goal: runnable FastMCP server with `get_status` tool, zero PostgreSQL logic yet.

- `pyproject.toml` — deps: `fastmcp`, `asyncpg`, `pydantic-settings`, dev: `pytest`, `pytest-asyncio`
- `src/postgresql_mcp/app.py` — FastMCP entry point
- `src/postgresql_mcp/configs.py` — pydantic-settings model (all env vars above)
- `.env.example`, `pytest.ini`, `.gitignore`
- Verify: `fastmcp dev src/postgresql_mcp/app.py:mcp` starts without error

## Phase 2 — Client Layer (asyncpg) ✅

> Goal: pure database calls, no business logic. Mixin composition pattern.

- `clients/base.py` — `BasePostgreSQLClient`: create pool, close, ping
- `clients/metadata.py` — `MetadataMixin`: list_schemas, list_tables, get_table_schema, get_indexes, get_constraints, get_column_values (all via `information_schema` / `pg_catalog` queries)
- `clients/read.py` — `ReadMixin`: execute_query (raw), explain_query
- `clients/utils.py` — `validate_identifier()` for SQL identifier safety
- `clients/__init__.py` — `PostgreSQLClient(BasePostgreSQLClient, MetadataMixin, ReadMixin)`

## Phase 3 — Connection Manager + Base Service ✅

> Goal: singleton lifecycle management, auto-connect, input validation.

- `services/connection_manager.py` — state machine: `disconnected → connecting → connected → error`. Lazy pool creation, health check, reconnect
- `services/postgresql/base.py` — `BaseService`: `ensure_connected()`, `_validate_identifier()`, `_validate_table_name()`, `_check_write_allowed()`, `_check_destructive_allowed()`, `_check_write_target()`
- Unit tests: 36 tests — state transitions, validation edge cases, write policy enforcement (all passing)

## Phase 4 — Guardrails Pipeline ✅

> Goal: production security layer. Each module is independent and testable in isolation.

- `guardrails/security_validator.py` — forbidden keywords (DROP, DELETE, ALTER, GRANT...), SQL injection patterns, dangerous functions, comment stripping, query length. Adapted from bigquery-mcp-server.
- `guardrails/query_rewriter.py` — auto LIMIT injection if missing, cap LIMIT to `MAX_LIMIT`, skip for pure aggregates, CTE-aware
- `guardrails/rate_limiter.py` — thread-safe sliding-window (configurable calls/window)
- `guardrails/pii_masker.py` — case-insensitive column match, hash (SHA-256 truncated) or redact
- `guardrails/audit_logger.py` — structured log: query, rows returned, duration, blocked reason
- `guardrails/__init__.py` — `GuardrailsPipeline`: orchestrates pre-execute → execute → post-execute
- Unit tests: **heavy coverage** — injection bypass attempts, edge cases, concurrent rate limiting

## Phase 5 — Metadata Service + Tools ✅

> Goal: first usable tools — agent can explore database structure.

- `services/postgresql/metadata.py` — `MetadataService`: delegates to client, formats output
- `tools/postgresql/metadata.py` — MCP tools: `list_schemas`, `list_tables`, `get_table_schema`, `get_indexes`, `get_constraints`, `get_column_values`
- `tools/connection.py` — `connect`, `disconnect`, `get_status`
- All tools return LLM-friendly strings (not raw dicts)
- Unit tests: service logic + tool output formatting

## Phase 6 — Read Service + Query Tools ✅

> Goal: agent can execute SQL with full guardrails pipeline.

- `services/postgresql/read.py` — `ReadService`: integrates GuardrailsPipeline, statement timeout via asyncpg
- `tools/postgresql/read.py` — MCP tools: `execute_query`, `dry_run_query` (EXPLAIN only), `explain_query` (EXPLAIN ANALYZE, multi-format)
- `dry_run_query` only applies SecurityValidator (no rewrite/PII since no data returned)
- Unit tests: end-to-end pipeline, timeout handling, error formatting

## Phase 7 — Write Service + Tools ✅

> Goal: opt-in write support with safety constraints.

- `clients/create.py` — `CreateMixin`: parameterized INSERT (single + batch)
- `clients/update.py` — `UpdateMixin`: parameterized UPDATE
- `services/postgresql/create.py` — `CreateService`: write policy check → delegate
- `services/postgresql/update.py` — `UpdateService`: write policy check, **require WHERE clause**
- `tools/create.py` — `insert_one`, `insert_many`
- `tools/update.py` — `update` (WHERE mandatory — no accidental full-table updates)
- All write operations use parameterized queries (never string interpolation)
- Unit tests: 24 tests — policy enforcement, allowlist matching, validation, parameterization

## Phase 8 — Delete Service + Tools ✅

> Goal: destructive operations with extra gating.

- `clients/delete.py` — `DeleteMixin`: parameterized DELETE, TRUNCATE
- `services/postgresql/delete.py` — `DeleteService`: write policy + destructive policy check
- `tools/delete.py` — `delete` (WHERE mandatory), `truncate_table` (requires `ALLOW_DESTRUCTIVE=true`)
- Unit tests: 17 tests — destructive gating, validation, success paths
- Integration tests: 10 tests — real INSERT/UPDATE/DELETE/TRUNCATE against PostgreSQL

## Phase 9 — Hardening + Final Tests ✅

> Goal: production-ready quality bar.

- 54 hardening tests covering:
  - SQL injection bypass attempts (CRLF, null byte, stacked queries, comment-based, Unicode homoglyphs)
  - Identifier validation edge cases (special chars, injection via identifiers)
  - Connection resilience (double connect, disconnect when not connected, reconnect after error)
  - Graceful shutdown (pool cleanup, idempotent disconnect)
- Total: **329 tests** (276 unit + 43 integration + 10 write integration)

---

## Phase 10 — SQL Injection & Data Leakage Hardening 🔒

> Goal: close remaining injection vectors and prevent data exfiltration. Read-only mode only prevents writes — it does NOT prevent unauthorized data access, mass leakage, or sensitive column exposure.

**Key Dependency:** `sqlglot` — SQL AST parser for reliable SELECT/FROM/WHERE/JOIN analysis.

---

### 10.1 — Read-Only Transaction Enforcement (P0)

Wrap ALL `execute_query` calls in a PostgreSQL read-only transaction with timeouts:
```python
async with conn.transaction(readonly=True):
    # Validate numeric, then use literal (SET does not support $1 bind params)
    timeout_ms = int(timeout_seconds * 1000)
    await conn.execute(f"SET LOCAL statement_timeout = '{timeout_ms}ms'")
    await conn.execute("SET LOCAL idle_in_transaction_session_timeout = '5000ms'")
    # Optional: RLS context
    if user_context_variable and user_id:
        await conn.execute(f"SET LOCAL {validated_var} = $1", user_id)
    stmt = await conn.prepare(query, ...)
    rows = await stmt.fetch(...)
```
- Engine-level guarantee — even if regex/AST is bypassed, PostgreSQL blocks writes
- Also apply to `EXPLAIN` (when enabled). `EXPLAIN ANALYZE` is blocked by policy (10.10)
- `USER_CONTEXT_VARIABLE` name validated with `^[a-zA-Z_][a-zA-Z0-9_.]*$`
- Note: `SET LOCAL` uses validated literal, not `$1` bind param (PostgreSQL SET limitation)

### 10.2 — Block System Catalogs (P0, hardcoded)

Always block queries referencing sensitive system tables (via AST table extraction):
- `pg_shadow`, `pg_authid`, `pg_roles`, `pg_user`, `pg_group`
- `pg_stat_activity`, `pg_stat_statements`, `pg_settings`
- Direct access to `pg_catalog.*` schema in raw queries

Check ALL tables in query — FROM, JOIN, subqueries. Not just the first table.

Metadata tools (`list_tables`, `get_table_schema`) still access `information_schema` internally — bypass at service layer, not exposed to LLM.

### 10.3 — Block SELECT * (P0)

New config: `BLOCK_SELECT_STAR` (default: `true`)

```bash
BLOCK_SELECT_STAR=true   # Force agent to list columns explicitly
```

Detect via AST (not regex):
- `SELECT *` → blocked
- `SELECT users.*` → blocked
- `SELECT u.*` (alias) → blocked
- `SELECT COUNT(*)` → **NOT blocked** (aggregate function, not column wildcard)
- `SELECT COUNT(*), SUM(amount)` → **NOT blocked**

Critical test: `SELECT COUNT(*) FROM users` must PASS.

### 10.4 — Column Policy with AST Enforcement (P0)

New config: `COLUMN_POLICY` (JSON string) or `COLUMN_POLICY_FILE` (path, takes priority)

```bash
COLUMN_POLICY_FILE=/etc/mcp/column_policy.json
# OR inline:
COLUMN_POLICY='{"public.users": {...}}'
```

Policy format:
```json
{
  "public.users": {
    "allowed_columns": ["id", "full_name", "department", "created_at"],
    "required_filter_columns": ["id", "full_name"],
    "allow_aggregates_without_filter": true,
    "group_by_columns": ["department", "created_at"],
    "max_rows": 20
  },
  "public.transactions": {
    "allowed_columns": ["id", "amount", "status", "created_at"],
    "required_filter_columns": ["id", "account_id"],
    "allow_aggregates_without_filter": true,
    "group_by_columns": ["status", "created_at"],
    "max_rows": 100
  }
}
```

Enforcement (via AST):
- **Table normalization**: unqualified table → prepend `DEFAULT_SCHEMA` (default `public`). `users` → `public.users` for policy lookup.
- Parse SELECT column list — check against `allowed_columns`
- Check column references through **aliases**: `SELECT password_hash AS p` → blocked by source column
- **Unqualified columns in multi-table queries**: rejected — require `table.column` or `alias.column` when JOIN is present
- Check ALL tables in FROM/JOIN against policy
- **Policy mode** (`COLUMN_POLICY_MODE`):
  - `permissive` (default): tables NOT in policy → allow all (backward compatible)
  - `strict` (recommended for production): tables NOT in policy → **rejected**
- `required_filter_columns`: WHERE must reference at least one of these columns with a concrete value (not tautology)
- `allow_aggregates_without_filter`: when `true`, **pure aggregate queries** skip the `required_filter_columns` check
  - "Pure aggregate" = query where ALL selected expressions are aggregate functions (COUNT, SUM, AVG, MIN, MAX) with no row-level columns
  - `SELECT COUNT(*) FROM users` → pass (pure aggregate)
  - `SELECT department, COUNT(*) FROM users GROUP BY department` → pass only if `department` is in `group_by_columns`
  - `SELECT id, COUNT(*) FROM users GROUP BY id` → **blocked** (id is row-level identifier, enables user enumeration)
- `group_by_columns` (optional): allowed dimension columns for GROUP BY. If absent, only aggregate-only queries (no GROUP BY) pass the exception
- `max_rows`: per-table LIMIT cap (override global `MAX_LIMIT`)

This subsumes `REQUIRE_WHERE_TABLES` — no need for separate config.

### 10.5 — Tautology Detection (P1, basic)

For tables with `required_filter_columns`, detect trivial WHERE clauses:
- `WHERE '1'='1'`, `WHERE 1=1`, `WHERE true`, `WHERE TRUE`
- `WHERE id = id` (self-reference)

**Not a security boundary** — easily bypassed. But catches common LLM mistakes.

Real enforcement is `required_filter_columns`: WHERE must contain a reference to an allowed filter column with a concrete value (literal or parameter), not a tautological expression.

### 10.6 — WHERE Clause Sanitization for Write Ops (P1)

Validate `where_clause` parameter in UPDATE/DELETE:
- No `;` (stacked queries)
- No SQL comments (`--`, `/* */`)
- No subqueries (`SELECT` keyword) — legitimate for read, but blocked for write WHERE
- No DDL/DCL keywords

Add `_validate_where_clause()` to `BaseService`.

### 10.7 — Enhanced Injection Patterns (P1)

Keep regex as **auxiliary layer** (defense-in-depth, not primary):
- System catalog probe: `\bpg_shadow\b|\bpg_authid\b`
- Config extraction: `\bcurrent_setting\s*\(`
- `COPY\s+(TO|FROM)` (file system access)
- String encoding bypass: `CHR\s*\(\d+\)` chaining
- `\bpg_advisory_lock` (DoS via lock exhaustion)

### 10.8 — Function Allowlist (P1)

Replace dangerous-function blacklist with **function allowlist** (whitelist approach):

```bash
ALLOWED_FUNCTIONS='["count","sum","avg","min","max","date_trunc","coalesce","lower","upper","length","trim","substring","now","current_date","current_timestamp","extract","to_char","round","ceil","floor","abs","nullif","greatest","least","array_agg","string_agg","bool_and","bool_or","json_agg","jsonb_agg"]'
```

Enforcement:
- Extract all function calls from AST
- If `ALLOWED_FUNCTIONS` is configured → only those functions allowed
- If not configured → fall back to dangerous-function blacklist (backward compatible)
- Operators (`+`, `-`, `||`, etc.) are not functions — always allowed

Default allowlist covers: aggregates, string ops, date ops, math ops, type casts, JSON aggs.

### 10.9 — Block Subqueries (P1)

New config: `BLOCK_SUBQUERIES` (default: `true`)

```bash
BLOCK_SUBQUERIES=true   # Subqueries blocked in strict mode
```

- Detect subqueries in SELECT list, FROM, WHERE, HAVING
- Reduces attack surface significantly (no nested data extraction)
- If `false`: subqueries allowed but every referenced table/column validated against policy
- **Note:** Set `BLOCK_SUBQUERIES=false` only when column/table policy validation is fully enabled for nested queries.

### 10.10 — EXPLAIN Safety (P1)

- Allow `EXPLAIN` (plan only) — validated with same SecurityValidator on inner query
- **Block `EXPLAIN ANALYZE`** — it executes the query, potential write/DoS vector
- If `EXPLAIN` inner query fails policy → reject
- In strict mode, block EXPLAIN entirely (optional: `BLOCK_EXPLAIN=false` default)

### 10.11 — Max OFFSET + LIMIT Enforcement (P0)

```bash
DEFAULT_LIMIT=100    # Auto-injected if query has no LIMIT
MAX_LIMIT=100        # Reject if LIMIT > this value
MAX_OFFSET=10000     # Reject if OFFSET > this value
```

Behavior:
- No LIMIT → add `DEFAULT_LIMIT` (existing behavior)
- LIMIT > `max_rows` (per-table policy) or `MAX_LIMIT` (global) → **reject** (not clamp)
- OFFSET > `MAX_OFFSET` → **reject**
- Block OFFSET entirely for tables with `required_filter_columns` (use cursor pagination instead)

Note: `DEFAULT_LIMIT` and `MAX_LIMIT` already exist in configs — Phase 10 changes behavior from "clamp" to "reject" and adds per-table override via policy.

### 10.12 — User Context Support for RLS (P2)

New optional config: `USER_CONTEXT_VARIABLE`

```bash
USER_CONTEXT_VARIABLE=app.current_user_id
```

Variable name validated: `^[a-zA-Z_][a-zA-Z0-9_.]*$`

If set, `execute_query` tool accepts optional `user_id` parameter → `SET LOCAL` before query.

### 10.13 — Disable Write Tools by Default (P0)

New config: `ENABLE_WRITE_TOOLS` (default: `false`)

```bash
ENABLE_WRITE_TOOLS=false  # Text2SQL agents should not write by default
```

When `false`: `insert_one`, `insert_many`, `update`, `delete`, `truncate_table` tools are **not registered** with MCP. They don't appear in tool list at all — not just permission-denied at runtime.

This is separate from `READ_ONLY` (which is a runtime check). `ENABLE_WRITE_TOOLS` controls whether tools are exposed to the LLM.

---

### Implementation Order

**P0 — Core data-exfiltration guardrails:**

| Step | Component |
|------|-----------|
| 1 | Add `sqlglot` dependency + new config fields |
| 2 | Disable write tool registration — `ENABLE_WRITE_TOOLS` (10.13) |
| 3 | AST parser module (parse SQL → extract tables, columns, functions, WHERE, LIMIT, OFFSET) |
| 4 | Block system catalogs via AST (10.2) |
| 5 | Block SELECT * / table.* / alias.* — preserve COUNT(*) (10.3) |
| 6 | Table policy + schema normalization + `COLUMN_POLICY_MODE` (10.4) |
| 7 | Column allowlist enforcement (10.4) |
| 8 | `required_filter_columns` + pure aggregate exception + `group_by_columns` (10.4) |
| 9 | DEFAULT_LIMIT / MAX_LIMIT reject / MAX_OFFSET reject (10.11) |
| 10 | Read-only transaction + SET LOCAL statement_timeout (10.1) |
| 11 | Grouped P0 tests |

**P1 — Extended policy + hardening:**

| Step | Component |
|------|-----------|
| 12 | Function allowlist — `ALLOWED_FUNCTIONS` (10.8) |
| 13 | Block subqueries — `BLOCK_SUBQUERIES` (10.9) |
| 14 | EXPLAIN validation — block ANALYZE (10.10) |
| 15 | Tautology detection (10.5) |
| 16 | WHERE clause sanitization for write ops (10.6) |
| 17 | Auxiliary regex patterns (10.7) |
| 18 | P1 tests |

**P2 — Advanced features:**

| Step | Component |
|------|-----------|
| 19 | User context / RLS support — `USER_CONTEXT_VARIABLE` (10.12) |
| 20 | Documentation polish — DB setup guide, security model explanation |

**Suggested default for `ALLOWED_FUNCTIONS`:**
```
count, sum, avg, min, max, date_trunc, coalesce, lower, upper, length, trim, substring,
now, current_date, current_timestamp, extract, to_char, round, ceil, floor, abs, nullif,
greatest, least, array_agg, string_agg, bool_and, bool_or, json_agg, jsonb_agg
```
