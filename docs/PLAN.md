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

**Key Dependencies:**
- `sqlglot` — SQL AST parser for reliable SELECT/FROM/WHERE/JOIN analysis
- `SECURITY_PROFILE` — deployment mode that determines default strictness

---

### 10.0 — Security Profile (P0)

New config: `SECURITY_PROFILE` (default: `general`)

```bash
SECURITY_PROFILE=general    # permissive defaults, backward compatible
SECURITY_PROFILE=text2sql   # strict column policy, metadata filtering
SECURITY_PROFILE=sensitive  # strict + require policy file + all guards on
```

| Profile | COLUMN_POLICY_MODE | Metadata filtering | Require policy file | ALLOW_CTE | BLOCK_SUBQUERIES | Function control |
|---------|-------------------|-------------------|--------------------|-----------|----|---|
| `general` | permissive | off | no | false | true | blacklist |
| `text2sql` | strict | on | recommended | false | true | allowlist |
| `sensitive` | strict | on | **required** | false | true | allowlist |

All profiles default to `ALLOW_CTE=false` and `BLOCK_SUBQUERIES=true` — minimal attack surface by default. Override individually if needed.

**Safety interlock:** `ALLOW_CTE=true` is only honored when full CTE body validation (10.14 advanced) is implemented. Until then, CTE is hard-disabled regardless of config.

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
- Engine-level **write safety** guarantee — even if regex/AST is bypassed, PostgreSQL blocks writes
- Also apply to `EXPLAIN` (when enabled). `EXPLAIN ANALYZE` is blocked by policy (10.10)
- `USER_CONTEXT_VARIABLE` name validated with `^[a-zA-Z_][a-zA-Z0-9_.]*$`
- Note: `SET LOCAL` uses validated literal, not `$1` bind param (PostgreSQL SET limitation)

**Scope clarification:** Read-only transaction is a **write safety control only**. It does NOT:
- Prevent SELECT on sensitive tables (that's DB privilege + column policy)
- Prevent `SELECT pg_catalog.*` if DB role has access (that's AST blocking)
- Act as data-leakage prevention (that's column policy + required filters)

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
    "sampleable_columns": ["department"],
    "required_filter_columns": ["id", "full_name"],
    "allow_aggregates_without_filter": true,
    "group_by_columns": ["department", "created_at"],
    "max_rows": 20
  },
  "public.transactions": {
    "allowed_columns": ["id", "amount", "status", "created_at"],
    "sampleable_columns": ["status"],
    "required_filter_columns": ["id", "account_id"],
    "allow_aggregates_without_filter": true,
    "group_by_columns": ["status", "created_at"],
    "max_rows": 100
  }
}
```

**Field definitions:**
- `allowed_columns`: columns permitted in SELECT/WHERE of `execute_query`
- `sampleable_columns`: columns permitted for `get_column_values` (distinct value enumeration). Must be subset of `allowed_columns`. Use for dimension/enum columns only — NEVER for PII or high-cardinality identifiers.
- `required_filter_columns`: WHERE must reference at least one with a concrete value
- `max_rows`: per-table LIMIT cap (override global `MAX_LIMIT`)

Enforcement (via AST):
- **Table normalization**: unqualified table → prepend `DEFAULT_SCHEMA` (default `public`). `users` → `public.users` for policy lookup.
- Parse SELECT column list — check against `allowed_columns`
- Check column references through **aliases**: `SELECT password_hash AS p` → blocked by source column
- **Unqualified columns in multi-table queries**: rejected — require `table.column` or `alias.column` when JOIN is present
- Check ALL tables in FROM/JOIN against policy
- **Policy mode** (`COLUMN_POLICY_MODE`):
  - `permissive` (default for `general` profile): tables NOT in policy → allow all (backward compatible)
  - `strict` (default for `text2sql` / `sensitive` profiles): tables NOT in policy → **rejected**
  - Can be overridden explicitly regardless of profile
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

### 10.8 — Function Allowlist (P0 for text2sql/sensitive, P1 for general)

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

### 10.9 — Block Subqueries (P0 basic / P1 advanced)

New config: `BLOCK_SUBQUERIES` (default: `true`)

```bash
BLOCK_SUBQUERIES=true   # Subqueries blocked by default
```

**P0 (basic):** detect and reject subqueries in SELECT list, FROM, WHERE, HAVING when `BLOCK_SUBQUERIES=true`.

**P1 (advanced):** if `BLOCK_SUBQUERIES=false`, allow subqueries but validate every referenced table/column against policy (same as CTE body validation approach).

- Reduces attack surface significantly (no nested data extraction)
- **Note:** Set `BLOCK_SUBQUERIES=false` only after P1 nested validation is implemented and tested.

### 10.10 — EXPLAIN Safety (P0)

- Allow `EXPLAIN` (plan only) — validated with same SecurityValidator + column policy on inner query
- **Block `EXPLAIN ANALYZE`** — it executes the query, potential write/DoS vector
- If `EXPLAIN` inner query fails policy → reject
- In `sensitive` profile: block EXPLAIN entirely (`BLOCK_EXPLAIN=true`)
- In `text2sql` profile: EXPLAIN allowed but inner query fully validated
- In `general` profile: EXPLAIN allowed, inner query gets basic validation

**Rationale for P0:** `explain_query` tool already exists since Phase 6 with `EXPLAIN ANALYZE` support. Must be secured before Phase 10 ships.

### 10.11 — Max OFFSET + LIMIT Enforcement (P0)

```bash
DEFAULT_LIMIT=100    # Auto-injected if query has no LIMIT
MAX_LIMIT=100        # Reject if LIMIT > this value
MAX_OFFSET=10000     # Reject if OFFSET > this value
```

Behavior:
- No LIMIT → **reject** in `text2sql`/`sensitive` mode; auto-inject `DEFAULT_LIMIT` in `general` mode
- LIMIT > `max_rows` (per-table policy) or `MAX_LIMIT` (global) → **reject** (not clamp)
- OFFSET > `MAX_OFFSET` → **reject**
- Block OFFSET entirely for tables with `required_filter_columns` (use cursor pagination instead)

**Aggregate exception:** Pure aggregate queries (all expressions are aggregate functions, no row-level columns) do NOT require LIMIT since they return a bounded single row. GROUP BY aggregates still require LIMIT unless `group_by_columns` cardinality is explicitly bounded by policy.

Examples:
- `SELECT COUNT(*) FROM users` → pass without LIMIT (single-row result)
- `SELECT department, COUNT(*) FROM users GROUP BY department` → needs LIMIT (unbounded groups)
- `SELECT department, COUNT(*) FROM users GROUP BY department LIMIT 20` → pass

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

### 10.14 — Single Statement + Supported SQL Shapes (P0)

Only ONE statement per `execute_query` call. Only supported shapes pass.

**Always blocked:**
- Multiple statements (`;` separator)
- `SELECT INTO`, `COPY`, `DO`, `CALL`
- `LATERAL`

**Blocked by default (opt-in via config):**

| Shape | Default | Config to enable |
|-------|---------|-----------------|
| CTE (`WITH ... SELECT`) | blocked | `ALLOW_CTE=true` |
| UNION / INTERSECT / EXCEPT | blocked | `ALLOW_SET_OPERATIONS=true` |
| Recursive CTE | blocked | `ALLOW_RECURSIVE_CTE=true` |

**CTE validation rules** (when `ALLOW_CTE=true` AND CTE body validation is implemented):
- Every CTE body validated as a normal SELECT (same table/column policy applies)
- Source tables/columns extracted from CTE body, not from CTE alias name
- CTE alias is NOT treated as a policy target — validator traces through to real tables
- Recursive CTE blocked unless `ALLOW_RECURSIVE_CTE=true` separately

**Safety interlock:** `ALLOW_CTE=true` config is IGNORED until full CTE body validation (P1 Step 23) is implemented and tested. Before that, CTE is hard-disabled regardless of config. Same interlock applies to `ALLOW_SET_OPERATIONS`.

This prevents bypass like:
```sql
WITH leak AS (SELECT password_hash FROM users)
SELECT * FROM leak;
```
Outer query references `leak`, but validator traces to `users.password_hash` → blocked by column policy.

### 10.15 — Metadata Tools Policy (P0)

In `text2sql` / `sensitive` profile (or when `COLUMN_POLICY_MODE=strict`), metadata tools are filtered:

| Tool | Behavior |
|------|----------|
| `list_tables` | Only return tables/views present in column policy |
| `get_table_schema` | Only return `allowed_columns`, hide unlisted columns |
| `get_indexes` / `get_constraints` | Only for tables in policy |
| `get_column_values` | Only for `sampleable_columns` (NOT `allowed_columns`) |

**`get_column_values` is a data leakage vector.** Even columns allowed in filtered queries should not be freely enumerable:
- `full_name` may be allowed with `WHERE id = $1`, but `get_column_values(users, full_name)` dumps all names
- Only `sampleable_columns` (dimension/enum columns) are safe for distinct value listing
- If table has no policy in strict mode → all metadata tools blocked for that table
- Audit log mandatory for all metadata tool calls

In `general` profile: metadata tools operate without filtering (backward compatible).

### 10.16 — Result Budget (P0)

Even with column policy and LIMIT, results can be excessively large (wide rows, JSON/text columns):

```bash
MAX_RESULT_ROWS=100        # Hard cap on rows returned (defense against policy bugs)
MAX_RESULT_BYTES=1048576   # 1MB max total serialized result size
MAX_CELL_LENGTH=4096       # Truncate individual cell values exceeding this
MAX_COLUMNS_RETURNED=50    # Reject if SELECT has too many columns
```

**Two-layer output size control:**

1. **Pre-execute (primary):** LIMIT enforcement via AST validation (10.11). Queries without LIMIT are rejected (not auto-injected in strict mode). This prevents fetching excess data into application memory.
2. **Post-execute (fallback):** Result budget truncation before returning to LLM. Catches edge cases where LIMIT alone isn't sufficient (wide rows, large cells).

Post-execute enforcement:
- Rows exceeding `MAX_RESULT_ROWS` → truncate + warning
- Total result size exceeding `MAX_RESULT_BYTES` → truncate + warning
- Individual cells exceeding `MAX_CELL_LENGTH` → truncate with `...[truncated]`

Pre-execute enforcement:
- Query with more than `MAX_COLUMNS_RETURNED` columns → reject at AST validation
- No LIMIT clause → reject in strict/text2sql mode (general mode still auto-injects DEFAULT_LIMIT)

Prevents:
- `SELECT id, profile_json, full_address, notes FROM users LIMIT 20` (wide-row leakage)
- Large text/JSON extraction even with valid column policy
- Memory exhaustion from unbounded fetches before truncation

### 10.17 — Critical Pattern Blocking (P0)

Block dangerous patterns that should NEVER pass through `execute_query`, regardless of profile:

```text
COPY (TO|FROM)           — file system access
current_setting(...)      — PostgreSQL config extraction
pg_advisory_lock(...)    — DoS via lock exhaustion
pg_read_file(...)        — direct file read
pg_ls_dir(...)           — directory listing
lo_import/lo_export      — large object file access
```

Enforced via regex as auxiliary layer (AST catches most, regex catches edge cases).
Moved from P1 to P0 because these are high-severity vectors — a single bypass = system compromise.

---

### Implementation Order

**P0 — Core data-exfiltration guardrails:**

| Step | Component |
|------|-----------|
| 1 | Add `sqlglot` dependency + new config fields + `SECURITY_PROFILE` (10.0) |
| 2 | Disable write tool registration — `ENABLE_WRITE_TOOLS` (10.13) |
| 3 | Read-only transaction + SET LOCAL statement_timeout (10.1) |
| 4 | Single-statement validation + supported SQL shapes (10.14) |
| 5 | Critical pattern blocking — COPY, current_setting, pg_advisory_lock, pg_read_file (10.17) |
| 6 | EXPLAIN safety — block ANALYZE, validate inner query (10.10) |
| 7 | AST parser module (parse SQL → extract tables, columns, functions, WHERE, LIMIT, OFFSET) |
| 8 | Block system catalogs via AST (10.2) |
| 9 | Block SELECT * / table.* / alias.* — preserve COUNT(*) (10.3) |
| 10 | Table policy + schema normalization + `COLUMN_POLICY_MODE` (10.4) |
| 11 | Column allowlist enforcement (10.4) |
| 12 | `required_filter_columns` + pure aggregate exception + `group_by_columns` (10.4) |
| 13 | DEFAULT_LIMIT / MAX_LIMIT reject / MAX_OFFSET reject + aggregate exception (10.11) |
| 14 | Function allowlist for `text2sql` + `sensitive` profiles (10.8) |
| 15 | Block subqueries — basic detection + reject (10.9 P0) |
| 16 | Metadata tools policy — filtering by profile (10.15) |
| 17 | Result budget — pre-execute LIMIT reject + post-execute truncate (10.16) |
| 18 | Grouped P0 tests |

**P1 — Extended policy + hardening:**

| Step | Component |
|------|-----------|
| 19 | Function allowlist for `general` (fallback blacklist) (10.8) |
| 20 | Block subqueries — advanced nested validation when `BLOCK_SUBQUERIES=false` (10.9 P1) |
| 21 | Tautology detection (10.5) |
| 22 | WHERE clause sanitization for write ops (10.6) |
| 23 | Auxiliary regex patterns — remaining (10.7) |
| 24 | CTE body validation — enable `ALLOW_CTE=true` safety interlock release (10.14 advanced) |
| 25 | P1 tests |

**P2 — Advanced features:**

| Step | Component |
|------|-----------|
| 26 | User context / RLS support — `USER_CONTEXT_VARIABLE` (10.12) |
| 27 | Documentation polish — DB setup guide, security model explanation |

**Safety interlocks:**
- `ALLOW_CTE=true` is ignored until Step 24 (CTE body validation) is complete
- `ALLOW_SET_OPERATIONS=true` follows same interlock pattern as CTE
- `BLOCK_SUBQUERIES=false` is ignored until Step 20 (nested validation) is complete
- `BLOCK_EXPLAIN=false` in sensitive profile requires Step 6 to be complete

---

### Security Test Cases

**Must BLOCK (P0 tests):**

```sql
-- Mass leakage / tautology
SELECT * FROM users WHERE '1'='1';
SELECT id, full_name FROM users WHERE '1'='1';

-- Sensitive column exposure
SELECT password_hash AS p FROM users WHERE id = 1;

-- CTE bypass
WITH leak AS (SELECT password_hash FROM users) SELECT * FROM leak;

-- Row-level enumeration via GROUP BY
SELECT COUNT(*) FROM users GROUP BY id;

-- EXPLAIN ANALYZE (executes query)
EXPLAIN ANALYZE SELECT id FROM users LIMIT 1;

-- System function extraction
SELECT current_setting('server_version');
SELECT pg_read_file('/etc/passwd');
SELECT pg_ls_dir('/tmp');

-- Large OFFSET data scraping
SELECT id FROM users OFFSET 999999 LIMIT 10;

-- System catalog probing
SELECT * FROM pg_shadow;
SELECT rolname, rolpassword FROM pg_authid;

-- Subquery data extraction
SELECT (SELECT password_hash FROM users LIMIT 1) AS leaked;

-- Multi-statement injection
SELECT 1; DROP TABLE users;

-- COPY file access
COPY users TO '/tmp/dump.csv';

-- Advisory lock DoS
SELECT pg_advisory_lock(1);

-- No LIMIT on row-level query (text2sql/sensitive)
SELECT id, full_name FROM users WHERE department = 'eng';

-- Unlisted table in strict mode
SELECT * FROM secret_internal_table;
```

**Must PASS (P0 tests):**

```sql
-- Pure aggregates (no LIMIT needed)
SELECT COUNT(*) FROM users;
SELECT AVG(amount) FROM transactions;

-- Allowed GROUP BY dimension with LIMIT
SELECT department, COUNT(*) FROM users GROUP BY department LIMIT 20;

-- Valid filtered query with LIMIT
SELECT id, full_name FROM users WHERE id = 1 LIMIT 1;
SELECT id, full_name FROM users WHERE full_name = 'Alice' LIMIT 10;

-- EXPLAIN without ANALYZE (text2sql/general)
EXPLAIN SELECT id, full_name FROM users WHERE id = 1 LIMIT 1;

-- Allowed functions
SELECT COUNT(*), AVG(amount) FROM transactions WHERE account_id = 1 LIMIT 10;
SELECT LOWER(full_name) FROM users WHERE id = 1 LIMIT 1;
```

**Suggested default for `ALLOWED_FUNCTIONS`:**
```
count, sum, avg, min, max, date_trunc, coalesce, lower, upper, length, trim, substring,
now, current_date, current_timestamp, extract, to_char, round, ceil, floor, abs, nullif,
greatest, least, array_agg, string_agg, bool_and, bool_or, json_agg, jsonb_agg
```
