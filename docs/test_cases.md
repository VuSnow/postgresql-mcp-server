# MCP Inspector Test Cases

Manual test cases for validating PostgreSQL MCP Server via MCP Inspector.

**Prerequisites:**
- Seed database: `./data/seed.sh "$POSTGRESQL_CONNECTION_STRING"`
- Default config: `SECURITY_PROFILE=general`, `READ_ONLY=true`, `ENABLE_WRITE_TOOLS=false`
- Start server: `fastmcp dev src/postgresql_mcp/app.py:mcp`

---

## 1. Connection Tools

### TC-1.1: Connect

| Field | Value |
|-------|-------|
| **Tool** | `connect` |
| **Input** | *(none)* |
| **Expected** | `{"result": "Connected to PostgreSQL."}` |

### TC-1.2: Get Status (after connect)

| Field | Value |
|-------|-------|
| **Tool** | `get_status` |
| **Input** | *(none)* |
| **Expected** | `{"result": {"state": "connected", ...}}` — includes server version, pool size |

### TC-1.3: Disconnect

| Field | Value |
|-------|-------|
| **Tool** | `disconnect` |
| **Input** | *(none)* |
| **Expected** | `{"result": "Disconnected."}` |

### TC-1.4: Get Status (after disconnect)

| Field | Value |
|-------|-------|
| **Tool** | `get_status` |
| **Input** | *(none)* |
| **Expected** | `{"result": {"state": "disconnected", ...}}` |

---

## 2. Metadata Tools

### TC-2.1: List Schemas

| Field | Value |
|-------|-------|
| **Tool** | `list_schemas` |
| **Input** | *(none)* |
| **Expected** | Contains `"public"` in result. May also show `information_schema` depending on config. |

### TC-2.2: List Tables

| Field | Value |
|-------|-------|
| **Tool** | `list_tables` |
| **Input** | `schema`: `"public"` |
| **Expected** | Lists 5 tables: `customers`, `accounts`, `transactions`, `cards`, `branches` with row counts (~10, ~18, ~32, ~11, ~10) |

### TC-2.3: Get Table Schema — customers

| Field | Value |
|-------|-------|
| **Tool** | `get_table_schema` |
| **Input** | `table_name`: `"customers"`, `schema`: `"public"` |
| **Expected** | 11 columns: `id` (integer), `full_name` (varchar 100), `email` (varchar 150), `phone` (varchar 20), `date_of_birth` (date), `national_id` (varchar 20), `address` (text), `city` (varchar 50), `status` (varchar 20), `created_at` (timestamptz), `updated_at` (timestamptz) |

### TC-2.4: Get Table Schema — transactions

| Field | Value |
|-------|-------|
| **Tool** | `get_table_schema` |
| **Input** | `table_name`: `"transactions"`, `schema`: `"public"` |
| **Expected** | 12 columns including: `id`, `account_id`, `transaction_type`, `amount`, `balance_after`, `currency`, `description`, `reference_id`, `counterparty_account`, `channel`, `status`, `created_at` |

### TC-2.5: Get Indexes — customers

| Field | Value |
|-------|-------|
| **Tool** | `get_indexes` |
| **Input** | `table_name`: `"customers"`, `schema`: `"public"` |
| **Expected** | At least PK index on `id`, unique indexes on `email` and `national_id` |

### TC-2.6: Get Constraints — accounts

| Field | Value |
|-------|-------|
| **Tool** | `get_constraints` |
| **Input** | `table_name`: `"accounts"`, `schema`: `"public"` |
| **Expected** | PK on `id`, FK `customer_id → customers(id)`, UNIQUE on `account_number`, CHECK on `account_type` and `status` |

### TC-2.7: Get Column Values — account_type

| Field | Value |
|-------|-------|
| **Tool** | `get_column_values` |
| **Input** | `table_name`: `"accounts"`, `column`: `"account_type"`, `schema`: `"public"` |
| **Expected** | Distinct values: `checking`, `savings`, `credit`, `loan` |

### TC-2.8: Get Column Values — transaction channel

| Field | Value |
|-------|-------|
| **Tool** | `get_column_values` |
| **Input** | `table_name`: `"transactions"`, `column`: `"channel"`, `schema`: `"public"` |
| **Expected** | Values include: `atm`, `mobile`, `web`, `branch`, `pos`, `auto` |

### TC-2.9: Get Column Values — customer city

| Field | Value |
|-------|-------|
| **Tool** | `get_column_values` |
| **Input** | `table_name`: `"customers"`, `column`: `"city"`, `schema`: `"public"` |
| **Expected** | Values: `Ho Chi Minh`, `Ha Noi`, `Da Nang`, `Hue` |

### TC-2.10: Get Table Schema — non-existent table

| Field | Value |
|-------|-------|
| **Tool** | `get_table_schema` |
| **Input** | `table_name`: `"nonexistent"`, `schema`: `"public"` |
| **Expected** | Empty result or error indicating table not found |

---

## 3. Query Execution — Happy Path

### TC-3.1: Simple SELECT with explicit columns

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name, city, status FROM customers WHERE status = 'active' LIMIT 10"` |
| **Expected** | 8 rows returned (all active customers). Columns: id, full_name, city, status |

### TC-3.2: SELECT with WHERE on single row

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name, email, city FROM customers WHERE id = 1 LIMIT 1"` |
| **Expected** | 1 row: `(1, 'Nguyen Van An', 'an.nguyen@email.com', 'Ho Chi Minh')` |

### TC-3.3: JOIN query

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT c.full_name, a.account_number, a.account_type, a.balance FROM customers c JOIN accounts a ON c.id = a.customer_id WHERE c.id = 1 LIMIT 10"` |
| **Expected** | 2 rows (An has checking + savings accounts) |

### TC-3.4: Aggregate — COUNT

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT account_type, COUNT(*) as cnt FROM accounts GROUP BY account_type"` |
| **Expected** | 4 rows: checking (~10), savings (~5), credit (~2), loan (~1) |

### TC-3.5: Aggregate — SUM with GROUP BY

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT transaction_type, COUNT(*) as cnt, SUM(amount) as total FROM transactions GROUP BY transaction_type"` |
| **Expected** | Multiple rows with types: deposit, withdrawal, transfer_in, transfer_out, payment |

### TC-3.6: ORDER BY + LIMIT

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name, city FROM customers ORDER BY created_at DESC LIMIT 5"` |
| **Expected** | 5 rows, most recent first (Kim, Inh, Huy, Giang, Phuc) |

### TC-3.7: Multiple conditions

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, account_number, balance FROM accounts WHERE account_type = 'savings' AND balance > 100000000 LIMIT 10"` |
| **Expected** | Savings accounts with balance > 100M VND (accounts 2, 6, 12, 18) |

### TC-3.8: Date range filter

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, account_id, transaction_type, amount FROM transactions WHERE created_at >= '2024-02-01' AND created_at < '2024-03-01' LIMIT 20"` |
| **Expected** | Feb 2024 transactions (~15 rows) |

### TC-3.9: HAVING clause

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT account_id, COUNT(*) as txn_count FROM transactions GROUP BY account_id HAVING COUNT(*) >= 5 LIMIT 10"` |
| **Expected** | Accounts with 5+ transactions (account 1 has 8, account 5 has 7) |

### TC-3.10: CASE expression

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name, CASE WHEN status = 'active' THEN 'Active' WHEN status = 'suspended' THEN 'Suspended' ELSE 'Closed' END as status_label FROM customers LIMIT 10"` |
| **Expected** | 10 rows with readable status labels |

### TC-3.11: Multi-table JOIN

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT c.full_name, a.account_type, t.transaction_type, t.amount FROM customers c JOIN accounts a ON c.id = a.customer_id JOIN transactions t ON a.id = t.account_id WHERE c.id = 1 ORDER BY t.created_at DESC LIMIT 10"` |
| **Expected** | Customer An's transactions with account type info |

### TC-3.12: COALESCE / NULL handling

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, branch_name, COALESCE(manager_name, 'N/A') as manager FROM branches LIMIT 10"` |
| **Expected** | 10 rows, ATM branches show 'N/A' for manager |

---

## 4. Query Security — Blocked Cases

### TC-4.1: SELECT * blocked

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT * FROM customers LIMIT 10"` |
| **Expected** | `"Query blocked: ..."` — SELECT * is rejected (BLOCK_SELECT_STAR=true) |

### TC-4.2: DDL — DROP TABLE

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"DROP TABLE customers"` |
| **Expected** | `"Query blocked: ..."` — DDL forbidden in read-only mode |

### TC-4.3: DML — INSERT

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"INSERT INTO customers (full_name, email) VALUES ('Hacker', 'hack@evil.com')"` |
| **Expected** | `"Query blocked: ..."` — INSERT forbidden in read-only mode |

### TC-4.4: DML — UPDATE

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"UPDATE customers SET status = 'closed' WHERE id = 1"` |
| **Expected** | `"Query blocked: ..."` — UPDATE forbidden |

### TC-4.5: DML — DELETE

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"DELETE FROM customers WHERE id = 1"` |
| **Expected** | `"Query blocked: ..."` — DELETE forbidden |

### TC-4.6: SQL Injection — stacked queries

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id FROM customers; DROP TABLE customers;"` |
| **Expected** | `"Query blocked: ..."` — multiple statements blocked |

### TC-4.7: SQL Injection — UNION injection

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers WHERE id = 1 UNION SELECT 1, password FROM pg_shadow LIMIT 10"` |
| **Expected** | `"Query blocked: ..."` — pg_shadow access blocked by critical patterns |

### TC-4.8: Dangerous function — pg_sleep (DoS)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT pg_sleep(10)"` |
| **Expected** | `"Query blocked: ..."` — pg_sleep blocked |

### TC-4.9: Dangerous function — pg_read_file

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT pg_read_file('/etc/passwd')"` |
| **Expected** | `"Query blocked: ..."` — file system access blocked |

### TC-4.10: Dangerous function — lo_export

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT lo_export(12345, '/tmp/dump.txt')"` |
| **Expected** | `"Query blocked: ..."` — large object export blocked |

### TC-4.11: COPY TO file

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"COPY customers TO '/tmp/customers.csv'"` |
| **Expected** | `"Query blocked: ..."` — COPY blocked (keyword + critical pattern) |

### TC-4.12: Advisory lock (DoS)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT pg_advisory_lock(1)"` |
| **Expected** | `"Query blocked: ..."` — advisory locks blocked |

### TC-4.13: Database exfiltration via XML

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT database_to_xml(true, true, '')"` |
| **Expected** | `"Query blocked: ..."` — bulk XML exfiltration blocked |

### TC-4.14: Dollar-quoted string (code injection)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"DO $$ BEGIN RAISE NOTICE 'pwned'; END; $$;"` |
| **Expected** | `"Query blocked: ..."` — dollar-quoting blocked |

### TC-4.15: dblink (external connection)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT * FROM dblink('host=evil.com', 'SELECT 1') AS t(id int)"` |
| **Expected** | `"Query blocked: ..."` — dblink blocked |

### TC-4.16: pg_authid (credential leakage)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT rolname, rolpassword FROM pg_authid LIMIT 5"` |
| **Expected** | `"Query blocked: ..."` — pg_authid blocked |

### TC-4.17: Query too long

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id FROM customers WHERE id IN (1" + ",1" * 5000 + ") LIMIT 1"` (>10000 chars) |
| **Expected** | `"Query blocked: ..."` — exceeds MAX_QUERY_LENGTH |

### TC-4.18: current_setting() config extraction

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT current_setting('server_version')"` |
| **Expected** | `"Query blocked: ..."` — current_setting pattern blocked |

### TC-4.19: pg_terminate_backend

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT pg_terminate_backend(pg_backend_pid())"` |
| **Expected** | `"Query blocked: ..."` — backend manipulation blocked |

### TC-4.20: Hex escape obfuscation

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT '\\x41\\x42\\x43' FROM customers LIMIT 1"` |
| **Expected** | `"Query blocked: ..."` — hex escape obfuscation blocked |

---

## 5. EXPLAIN Tool

### TC-5.1: EXPLAIN — valid query

| Field | Value |
|-------|-------|
| **Tool** | `explain_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers WHERE status = 'active'"`, `analyze`: `false`, `format`: `"text"` |
| **Expected** | Returns execution plan text (Seq Scan or Index Scan on customers) |

### TC-5.2: EXPLAIN ANALYZE — blocked by default

| Field | Value |
|-------|-------|
| **Tool** | `explain_query` |
| **Input** | `query`: `"SELECT id FROM customers LIMIT 5"`, `analyze`: `true`, `format`: `"text"` |
| **Expected** | `"Query blocked: ..."` — EXPLAIN ANALYZE blocked (BLOCK_EXPLAIN_ANALYZE=true) |

### TC-5.3: EXPLAIN — dangerous query blocked

| Field | Value |
|-------|-------|
| **Tool** | `explain_query` |
| **Input** | `query`: `"SELECT pg_read_file('/etc/passwd')"`, `analyze`: `false` |
| **Expected** | `"Query blocked: ..."` — inner query fails critical pattern check |

### TC-5.4: EXPLAIN — JSON format

| Field | Value |
|-------|-------|
| **Tool** | `explain_query` |
| **Input** | `query`: `"SELECT id, account_type, balance FROM accounts WHERE balance > 0"`, `analyze`: `false`, `format`: `"json"` |
| **Expected** | Returns JSON-formatted execution plan |

---

## 6. Dry Run (Validation Only)

### TC-6.1: Dry run — safe query

| Field | Value |
|-------|-------|
| **Tool** | `dry_run_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers WHERE id = 1 LIMIT 1"` |
| **Expected** | `"Query is valid. No security issues detected."` |

### TC-6.2: Dry run — dangerous query

| Field | Value |
|-------|-------|
| **Tool** | `dry_run_query` |
| **Input** | `query`: `"DROP TABLE customers"` |
| **Expected** | `"Query rejected: ..."` — forbidden keyword detected |

### TC-6.3: Dry run — injection pattern

| Field | Value |
|-------|-------|
| **Tool** | `dry_run_query` |
| **Input** | `query`: `"SELECT id FROM customers WHERE name = '' OR 1=1; DROP TABLE customers;--"` |
| **Expected** | `"Query rejected: ..."` — injection pattern detected |

---

## 7. Subquery Blocking (BLOCK_SUBQUERIES=true)

### TC-7.1: Subquery in WHERE

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers WHERE id IN (SELECT customer_id FROM accounts WHERE balance > 100000000) LIMIT 10"` |
| **Expected** | `"Query blocked: ..."` — subqueries blocked |

### TC-7.2: Subquery in FROM (derived table)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT sub.full_name FROM (SELECT full_name FROM customers) sub LIMIT 10"` |
| **Expected** | `"Query blocked: ..."` — subqueries blocked |

### TC-7.3: CTE blocked by default

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"WITH active AS (SELECT id, full_name FROM customers WHERE status = 'active') SELECT id, full_name FROM active LIMIT 10"` |
| **Expected** | `"Query blocked: ..."` — CTE blocked (ALLOW_CTE=false) |

### TC-7.4: UNION blocked by default

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers WHERE city = 'Ha Noi' UNION SELECT id, full_name FROM customers WHERE city = 'Da Nang' LIMIT 10"` |
| **Expected** | `"Query blocked: ..."` — set operations blocked (ALLOW_SET_OPERATIONS=false) |

---

## 8. LIMIT/OFFSET Enforcement

### TC-8.1: No LIMIT — auto-injected

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name, city FROM customers WHERE status = 'active'"` |
| **Expected** | Returns results (auto LIMIT = 100 injected by QueryRewriter). Up to 8 active customers returned |

### TC-8.2: LIMIT exceeds MAX_LIMIT (1000)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers LIMIT 5000"` |
| **Expected** | `"Query blocked: ..."` — LIMIT exceeds max (1000) |

### TC-8.3: OFFSET exceeds MAX_OFFSET (10000)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers LIMIT 10 OFFSET 20000"` |
| **Expected** | `"Query blocked: ..."` — OFFSET exceeds max (10000) |

### TC-8.4: Valid LIMIT + OFFSET

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers ORDER BY id LIMIT 5 OFFSET 3"` |
| **Expected** | 5 rows starting from id 4 (Duc, Em, Phuc, Giang, Huy) |

### TC-8.5: Aggregate exempt from LIMIT requirement

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT COUNT(*) FROM customers"` |
| **Expected** | Returns count = 10 (no LIMIT needed for pure aggregates) |

---

## 9. Statement Shape Validation

### TC-9.1: Multiple statements (semicolon)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT 1; SELECT 2;"` |
| **Expected** | `"Query blocked: ..."` — only one statement per query allowed |

### TC-9.2: SELECT INTO blocked

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name INTO new_table FROM customers LIMIT 5"` |
| **Expected** | `"Query blocked: ..."` — SELECT INTO is a write operation |

### TC-9.3: DO block

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"DO $$ BEGIN PERFORM 1; END; $$"` |
| **Expected** | `"Query blocked: ..."` — DO statements blocked |

---

## 10. Write Tools (ENABLE_WRITE_TOOLS=false default)

### TC-10.1: Write tools not visible

| Field | Value |
|-------|-------|
| **Tool** | *(check tool list)* |
| **Input** | *(none)* |
| **Expected** | Tools `insert_one`, `insert_many`, `update`, `delete`, `truncate_table` are NOT listed |

---

## 11. Write Tools (with ENABLE_WRITE_TOOLS=true, READ_ONLY=false)

> **Config change required:** Set `ENABLE_WRITE_TOOLS=true`, `READ_ONLY=false`

### TC-11.1: Insert one row

| Field | Value |
|-------|-------|
| **Tool** | `insert_one` |
| **Input** | `table_name`: `"customers"`, `data`: `{"full_name": "Test User", "email": "test@example.com", "city": "Ho Chi Minh", "status": "active"}` |
| **Expected** | Success — returns inserted row or row count |

### TC-11.2: Insert many rows

| Field | Value |
|-------|-------|
| **Tool** | `insert_many` |
| **Input** | `table_name`: `"branches"`, `columns`: `["branch_code", "branch_name", "city", "address", "opened_date"]`, `rows`: `[["TEST-001", "Test Branch 1", "Ho Chi Minh", "123 Test St", "2024-01-01"], ["TEST-002", "Test Branch 2", "Ha Noi", "456 Test Ave", "2024-02-01"]]` |
| **Expected** | Success — 2 rows inserted |

### TC-11.3: Update with WHERE

| Field | Value |
|-------|-------|
| **Tool** | `update` |
| **Input** | `table_name`: `"customers"`, `set_data`: `{"city": "Ho Chi Minh"}`, `where_clause`: `"id = $1"`, `where_values`: `[11]` |
| **Expected** | Success — 1 row updated (test user from TC-11.1) |

### TC-11.4: Delete requires ALLOW_DESTRUCTIVE

| Field | Value |
|-------|-------|
| **Tool** | `delete` |
| **Input** | `table_name`: `"customers"`, `where_clause`: `"email = $1"`, `where_values`: `["test@example.com"]` |
| **Expected** | `{"error": "..."}` — destructive operation requires ALLOW_DESTRUCTIVE=true |

### TC-11.5: Insert — write allowlist rejection

> **Config:** Set `WRITE_ALLOWLIST=public.branches` (only branches writable)

| Field | Value |
|-------|-------|
| **Tool** | `insert_one` |
| **Input** | `table_name`: `"customers"`, `data`: `{"full_name": "Blocked", "email": "blocked@test.com"}` |
| **Expected** | `{"error": "..."}` — table not in write allowlist |

---

## 12. Real-World Query Scenarios (Banking)

### TC-12.1: Top customers by total balance

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT c.id, c.full_name, SUM(a.balance) as total_balance FROM customers c JOIN accounts a ON c.id = a.customer_id WHERE a.status = 'active' AND a.balance > 0 GROUP BY c.id, c.full_name ORDER BY total_balance DESC LIMIT 5"` |
| **Expected** | Top 5 customers by total positive balance (Kim, Cuong, Phuc likely at top) |

### TC-12.2: Monthly transaction summary

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT DATE_TRUNC('month', created_at) as month, transaction_type, COUNT(*) as cnt, SUM(amount) as total FROM transactions WHERE status = 'completed' GROUP BY DATE_TRUNC('month', created_at), transaction_type ORDER BY month, transaction_type LIMIT 50"` |
| **Expected** | Monthly breakdown by transaction type (Jan + Feb 2024) |

### TC-12.3: Accounts with cards expiring soon

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT c.full_name, cr.card_number, cr.brand, cr.expiry_date FROM customers c JOIN accounts a ON c.id = a.customer_id JOIN cards cr ON a.id = cr.account_id WHERE cr.expiry_date < '2026-07-01' AND cr.status = 'active' LIMIT 10"` |
| **Expected** | Cards expiring before July 2026 (Binh's visa debit expires 2026-06-30) |

### TC-12.4: Failed transactions

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT t.id, c.full_name, t.transaction_type, t.amount, t.description, t.status FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN customers c ON a.customer_id = c.id WHERE t.status IN ('failed', 'pending') LIMIT 10"` |
| **Expected** | 2 rows: transaction 31 (failed ATM withdrawal, An) and 32 (pending transfer, Binh) |

### TC-12.5: Branch analysis — non-ATM branches

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT branch_code, branch_name, city, manager_name FROM branches WHERE is_atm_only = false AND status = 'active' ORDER BY city LIMIT 10"` |
| **Expected** | 7 active non-ATM branches across 4 cities |

### TC-12.6: Credit utilization

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT a.account_number, c.full_name, ABS(a.balance) as used, a.credit_limit, ROUND(ABS(a.balance) / a.credit_limit * 100, 1) as utilization_pct FROM accounts a JOIN customers c ON a.customer_id = c.id WHERE a.account_type = 'credit' LIMIT 10"` |
| **Expected** | 2 credit accounts: Binh (17% utilization), Huy (22% utilization) |

### TC-12.7: Customer activity count

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT c.full_name, COUNT(t.id) as txn_count FROM customers c JOIN accounts a ON c.id = a.customer_id LEFT JOIN transactions t ON a.id = t.account_id GROUP BY c.full_name ORDER BY txn_count DESC LIMIT 10"` |
| **Expected** | All customers with their transaction counts. An (8), Cuong (7), Phuc (5), Duc (4), Binh (6) |

---

## 13. Edge Cases

### TC-13.1: Empty result set

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers WHERE city = 'Can Tho' LIMIT 10"` |
| **Expected** | `"Query returned 0 rows."` — no customers in Can Tho |

### TC-13.2: NULL handling in results

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, branch_name, manager_name, phone FROM branches WHERE is_atm_only = true LIMIT 10"` |
| **Expected** | ATM branches (2 rows) with NULL manager_name and phone |

### TC-13.3: Numeric precision

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, account_number, balance, interest_rate FROM accounts WHERE interest_rate IS NOT NULL LIMIT 10"` |
| **Expected** | Shows interest rates with 4 decimal places (0.0450, 0.0550, etc.) |

### TC-13.4: Boolean column

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, card_number, is_contactless FROM cards LIMIT 5"` |
| **Expected** | Boolean values displayed correctly (true/false) |

### TC-13.5: Timestamp formatting

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name, created_at FROM customers ORDER BY id LIMIT 3"` |
| **Expected** | Timestamps displayed with timezone info |

---

## 14. Rate Limiting

### TC-14.1: Burst queries within limit

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | Run 5 sequential queries: `"SELECT id FROM customers LIMIT 1"` |
| **Expected** | All 5 succeed (default: 100 calls per hour) |

### TC-14.2: Rate limit exceeded

> **Config:** Set `RATE_LIMIT_MAX_CALLS=3`, `RATE_LIMIT_WINDOW_SECONDS=60`

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | Run 4th query after 3 successful ones |
| **Expected** | `"Query blocked: ..."` — rate limit exceeded |

---

## 15. PII Masking

> **Config:** Set `PII_RULES=[{"column":"email","method":"hash"},{"column":"national_id","method":"redact"}]`

### TC-15.1: Email hashed in results

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name, email FROM customers WHERE id = 1 LIMIT 1"` |
| **Expected** | `email` column shows a hash value (not `an.nguyen@email.com`) |

### TC-15.2: National ID redacted

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name, national_id FROM customers WHERE id = 1 LIMIT 1"` |
| **Expected** | `national_id` column shows `***REDACTED***` (not `079090012345`) |

---

## 16. Security Profile: text2sql

> **Config:** Set `SECURITY_PROFILE=text2sql`, `COLUMN_POLICY=<see below>`
>
> ```json
> {
>   "public.customers": {
>     "allowed_columns": ["id", "full_name", "city", "status", "created_at"],
>     "sampleable_columns": ["city", "status"],
>     "required_filter_columns": ["id", "full_name", "city"]
>   },
>   "public.accounts": {
>     "allowed_columns": ["id", "customer_id", "account_type", "balance", "status"],
>     "sampleable_columns": ["account_type", "status"],
>     "required_filter_columns": ["customer_id"]
>   },
>   "public.transactions": {
>     "allowed_columns": ["id", "account_id", "transaction_type", "amount", "status", "created_at"],
>     "sampleable_columns": ["transaction_type", "status"],
>     "required_filter_columns": ["account_id"]
>   }
> }
> ```

### TC-16.1: Allowed columns pass

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name, city FROM customers WHERE city = 'Ha Noi' LIMIT 10"` |
| **Expected** | Returns 3 customers in Ha Noi |

### TC-16.2: Disallowed column blocked (email)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name, email FROM customers WHERE city = 'Ha Noi' LIMIT 10"` |
| **Expected** | `"Query blocked: ..."` — column `email` not in allowed_columns |

### TC-16.3: Disallowed column blocked (national_id)

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, national_id FROM customers WHERE id = 1 LIMIT 1"` |
| **Expected** | `"Query blocked: ..."` — column `national_id` not in allowed_columns |

### TC-16.4: Required filter missing

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers LIMIT 10"` |
| **Expected** | `"Query blocked: ..."` — required filter column missing (need id, full_name, or city in WHERE) |

### TC-16.5: Required filter present

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, full_name FROM customers WHERE id = 1 LIMIT 1"` |
| **Expected** | Success — filter on `id` satisfies requirement |

### TC-16.6: Metadata — list_tables filtered

| Field | Value |
|-------|-------|
| **Tool** | `list_tables` |
| **Input** | `schema`: `"public"` |
| **Expected** | Only shows tables in policy: `customers`, `accounts`, `transactions`. Does NOT show `cards`, `branches` |

### TC-16.7: Metadata — get_table_schema filtered

| Field | Value |
|-------|-------|
| **Tool** | `get_table_schema` |
| **Input** | `table_name`: `"customers"`, `schema`: `"public"` |
| **Expected** | Only shows allowed columns: `id`, `full_name`, `city`, `status`, `created_at`. Hides `email`, `phone`, `national_id`, etc. |

### TC-16.8: Metadata — get_column_values only sampleable

| Field | Value |
|-------|-------|
| **Tool** | `get_column_values` |
| **Input** | `table_name`: `"customers"`, `column`: `"city"`, `schema`: `"public"` |
| **Expected** | Success — `city` is in sampleable_columns |

### TC-16.9: Metadata — get_column_values non-sampleable blocked

| Field | Value |
|-------|-------|
| **Tool** | `get_column_values` |
| **Input** | `table_name`: `"customers"`, `column`: `"full_name"`, `schema`: `"public"` |
| **Expected** | `{"error": "..."}` — `full_name` is in allowed_columns but NOT in sampleable_columns |

### TC-16.10: Metadata — unlisted table blocked (strict mode)

| Field | Value |
|-------|-------|
| **Tool** | `get_table_schema` |
| **Input** | `table_name`: `"cards"`, `schema`: `"public"` |
| **Expected** | `{"error": "..."}` — table `cards` not in policy (strict mode) |

### TC-16.11: Aggregate without filter allowed

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT COUNT(*) FROM customers"` |
| **Expected** | Returns count = 10 (pure aggregates exempt from required_filter) |

---

## 17. Function Allowlist (text2sql/sensitive)

> **Config:** `SECURITY_PROFILE=text2sql` (uses default allowlist)

### TC-17.1: Allowed function — COUNT

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT COUNT(*) FROM customers WHERE city = 'Ha Noi'"` |
| **Expected** | Success — COUNT is always allowed |

### TC-17.2: Allowed function — SUM

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT SUM(amount) FROM transactions WHERE account_id = 1"` |
| **Expected** | Success — SUM is always allowed |

### TC-17.3: Allowed function — COALESCE

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT id, COALESCE(manager_name, 'N/A') as mgr FROM branches WHERE id = 1 LIMIT 1"` |
| **Expected** | Success — COALESCE is a safe function |

### TC-17.4: Blocked function — pg_sleep

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT pg_sleep(1) FROM customers WHERE id = 1 LIMIT 1"` |
| **Expected** | `"Query blocked: ..."` — pg_sleep not in allowlist |

### TC-17.5: Allowed function — DATE_TRUNC

| Field | Value |
|-------|-------|
| **Tool** | `execute_query` |
| **Input** | `query`: `"SELECT DATE_TRUNC('month', created_at) as month, COUNT(*) FROM transactions WHERE account_id = 1 GROUP BY DATE_TRUNC('month', created_at) LIMIT 10"` |
| **Expected** | Success — DATE_TRUNC is allowed |

---

## Summary Checklist

| Category | Test Cases | Coverage |
|----------|-----------|----------|
| Connection | TC-1.1 to TC-1.4 | connect, disconnect, status |
| Metadata | TC-2.1 to TC-2.10 | schemas, tables, columns, indexes, constraints, values |
| Query Happy Path | TC-3.1 to TC-3.12 | SELECT, JOIN, aggregates, ORDER BY, CASE, COALESCE |
| Security Blocking | TC-4.1 to TC-4.20 | DDL, DML, injection, dangerous funcs, critical patterns |
| EXPLAIN | TC-5.1 to TC-5.4 | valid explain, analyze blocked, dangerous blocked |
| Dry Run | TC-6.1 to TC-6.3 | validation without execution |
| Subquery Blocking | TC-7.1 to TC-7.4 | WHERE sub, FROM sub, CTE, UNION |
| LIMIT/OFFSET | TC-8.1 to TC-8.5 | auto-inject, max limit, max offset, aggregates |
| Statement Shape | TC-9.1 to TC-9.3 | multi-statement, SELECT INTO, DO block |
| Write Tools Off | TC-10.1 | tools not registered |
| Write Tools On | TC-11.1 to TC-11.5 | insert, update, delete gating, allowlist |
| Banking Queries | TC-12.1 to TC-12.7 | real-world analytics |
| Edge Cases | TC-13.1 to TC-13.5 | nulls, precision, booleans, timestamps |
| Rate Limiting | TC-14.1 to TC-14.2 | within/over limit |
| PII Masking | TC-15.1 to TC-15.2 | hash, redact |
| text2sql Profile | TC-16.1 to TC-16.11 | column policy, metadata filtering |
| Function Allowlist | TC-17.1 to TC-17.5 | allowed/blocked functions |

**Total: 85 test cases**
