"""
Load CSV files into SQLite database.
Usage: python load_csv_to_db.py
Output: ../db/banking.db
"""
import csv
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(os.path.dirname(__file__)).parent
DATA_DIR = BASE_DIR / "csv"
DB_PATH = BASE_DIR / "db" / "banking.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    cif_no TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    phone_number TEXT,
    email TEXT,
    kyc_level TEXT CHECK(kyc_level IN ('BASIC','VERIFIED','ENHANCED')),
    status TEXT CHECK(status IN ('ACTIVE','SUSPENDED','CLOSED')),
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    account_no TEXT UNIQUE NOT NULL,
    cif_no TEXT NOT NULL REFERENCES customers(cif_no),
    account_type TEXT CHECK(account_type IN ('PAYMENT','SAVINGS','CREDIT_CARD_SETTLEMENT')),
    currency TEXT DEFAULT 'VND',
    balance INTEGER,
    available_balance INTEGER,
    status TEXT CHECK(status IN ('ACTIVE','FROZEN','CLOSED')),
    opened_at TEXT
);

CREATE TABLE IF NOT EXISTS cards (
    card_id TEXT PRIMARY KEY,
    cif_no TEXT NOT NULL REFERENCES customers(cif_no),
    account_no TEXT NOT NULL REFERENCES accounts(account_no),
    masked_card_no TEXT,
    card_type TEXT CHECK(card_type IN ('DEBIT','CREDIT')),
    card_network TEXT CHECK(card_network IN ('VISA','MASTERCARD','NAPAS')),
    credit_limit INTEGER,
    available_limit INTEGER,
    status TEXT CHECK(status IN ('ACTIVE','LOCKED','EXPIRED')),
    issued_at TEXT
);

CREATE TABLE IF NOT EXISTS beneficiaries (
    beneficiary_id TEXT PRIMARY KEY,
    cif_no TEXT NOT NULL REFERENCES customers(cif_no),
    beneficiary_name TEXT NOT NULL,
    beneficiary_account_no TEXT,
    beneficiary_bank_code TEXT,
    beneficiary_bank_name TEXT,
    nickname TEXT,
    is_saved TEXT,
    last_used_at TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS merchants (
    merchant_id TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    merchant_category TEXT,
    mcc_code TEXT,
    city TEXT,
    country TEXT DEFAULT 'VN',
    status TEXT CHECK(status IN ('ACTIVE','INACTIVE'))
);

CREATE TABLE IF NOT EXISTS billers (
    biller_id TEXT PRIMARY KEY,
    biller_code TEXT UNIQUE NOT NULL,
    biller_name TEXT NOT NULL,
    biller_type TEXT CHECK(biller_type IN ('ELECTRICITY','WATER','INTERNET','PHONE_POSTPAID')),
    provider TEXT,
    status TEXT CHECK(status IN ('ACTIVE','INACTIVE'))
);

CREATE TABLE IF NOT EXISTS customer_biller_accounts (
    customer_biller_account_id TEXT PRIMARY KEY,
    cif_no TEXT NOT NULL REFERENCES customers(cif_no),
    biller_id TEXT NOT NULL REFERENCES billers(biller_id),
    customer_bill_code TEXT,
    alias TEXT,
    status TEXT CHECK(status IN ('ACTIVE','INACTIVE')),
    last_paid_at TEXT
);

CREATE TABLE IF NOT EXISTS transaction_categories (
    category_id TEXT PRIMARY KEY,
    category_code TEXT UNIQUE NOT NULL,
    category_name TEXT NOT NULL,
    category_group TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    transaction_ref TEXT UNIQUE NOT NULL,
    cif_no TEXT NOT NULL REFERENCES customers(cif_no),
    account_no TEXT NOT NULL REFERENCES accounts(account_no),
    card_id TEXT REFERENCES cards(card_id),
    transaction_time TEXT NOT NULL,
    amount INTEGER NOT NULL,
    currency TEXT DEFAULT 'VND',
    direction TEXT CHECK(direction IN ('IN','OUT')),
    transaction_type TEXT,
    category_id TEXT REFERENCES transaction_categories(category_id),
    merchant_id TEXT REFERENCES merchants(merchant_id),
    biller_id TEXT REFERENCES billers(biller_id),
    beneficiary_id TEXT REFERENCES beneficiaries(beneficiary_id),
    counterparty_account_no TEXT,
    counterparty_bank_code TEXT,
    counterparty_name TEXT,
    channel TEXT,
    description TEXT,
    status TEXT CHECK(status IN ('SUCCESS','FAILED','REVERSED','PENDING')),
    balance_after INTEGER,
    external_reference TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS action_requests (
    action_id TEXT PRIMARY KEY,
    cif_no TEXT NOT NULL REFERENCES customers(cif_no),
    action_type TEXT,
    status TEXT,
    user_text TEXT,
    api_name TEXT,
    api_payload TEXT,
    resolved_entities TEXT,
    missing_fields TEXT,
    risk_score REAL,
    risk_tier TEXT CHECK(risk_tier IN ('GREEN','YELLOW','ORANGE','RED')),
    requires_confirmation INTEGER,
    requires_otp INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS api_call_logs (
    api_call_id TEXT PRIMARY KEY,
    action_id TEXT NOT NULL REFERENCES action_requests(action_id),
    api_name TEXT,
    request_payload TEXT,
    response_payload TEXT,
    http_status INTEGER,
    status TEXT CHECK(status IN ('SUCCESS','FAILED')),
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id TEXT PRIMARY KEY,
    action_id TEXT REFERENCES action_requests(action_id),
    cif_no TEXT NOT NULL REFERENCES customers(cif_no),
    event_type TEXT,
    actor TEXT,
    event_payload TEXT,
    created_at TEXT
);

-- Fraud tables
CREATE TABLE IF NOT EXISTS fraud_reports (
    report_id TEXT PRIMARY KEY,
    reporter_cif_no TEXT NOT NULL REFERENCES customers(cif_no),
    transaction_ref TEXT REFERENCES transactions(transaction_ref),
    reported_account_no TEXT NOT NULL,
    reported_bank_code TEXT NOT NULL,
    reported_customer_cif TEXT,
    fraud_type TEXT,
    contact_channel TEXT,
    aftermath TEXT,
    reason_text TEXT,
    has_evidence INTEGER DEFAULT 0,
    confidence_score INTEGER CHECK(confidence_score BETWEEN 0 AND 100),
    status TEXT CHECK(status IN ('SUBMITTED','VALIDATED','CONFIRMED','REJECTED')) DEFAULT 'SUBMITTED',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS reported_accounts (
    reported_account_id TEXT PRIMARY KEY,
    account_no TEXT NOT NULL,
    bank_code TEXT NOT NULL,
    linked_customer_cif TEXT,
    valid_report_count INTEGER DEFAULT 0,
    unique_reporter_count INTEGER DEFAULT 0,
    total_reported_amount INTEGER DEFAULT 0,
    avg_confidence_score INTEGER DEFAULT 0,
    risk_score REAL DEFAULT 0.0,
    risk_level TEXT CHECK(risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')) DEFAULT 'LOW',
    status TEXT CHECK(status IN ('ACTIVE','UNDER_REVIEW','CLEARED')) DEFAULT 'ACTIVE',
    first_reported_at TEXT,
    last_reported_at TEXT,
    UNIQUE(account_no, bank_code)
);

CREATE TABLE IF NOT EXISTS reported_customers (
    reported_customer_id TEXT PRIMARY KEY,
    cif_no TEXT NOT NULL REFERENCES customers(cif_no),
    reported_account_count INTEGER DEFAULT 0,
    valid_report_count INTEGER DEFAULT 0,
    total_reported_amount INTEGER DEFAULT 0,
    risk_score REAL DEFAULT 0.0,
    risk_level TEXT CHECK(risk_level IN ('WATCH','FROZEN','BLOCKED','CLEARED')) DEFAULT 'WATCH',
    status TEXT DEFAULT 'ACTIVE',
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS fraud_decisions (
    decision_id TEXT PRIMARY KEY,
    action_id TEXT REFERENCES action_requests(action_id),
    receiver_account_no TEXT NOT NULL,
    receiver_bank_code TEXT NOT NULL,
    matched_report_count INTEGER DEFAULT 0,
    risk_score REAL DEFAULT 0.0,
    risk_level TEXT,
    decision TEXT CHECK(decision IN ('ALLOW','WARN','STEP_UP_AUTH','HOLD','BLOCK')),
    reason_codes TEXT,
    created_at TEXT
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_accounts_cif ON accounts(cif_no);
CREATE INDEX IF NOT EXISTS idx_cards_cif ON cards(cif_no);
CREATE INDEX IF NOT EXISTS idx_beneficiaries_cif ON beneficiaries(cif_no);
CREATE INDEX IF NOT EXISTS idx_transactions_cif ON transactions(cif_no);
CREATE INDEX IF NOT EXISTS idx_transactions_time ON transactions(transaction_time);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_cif_time ON transactions(cif_no, transaction_time);
CREATE INDEX IF NOT EXISTS idx_action_requests_cif ON action_requests(cif_no);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action_id);
CREATE INDEX IF NOT EXISTS idx_cba_cif ON customer_biller_accounts(cif_no);
CREATE INDEX IF NOT EXISTS idx_fraud_reports_reporter ON fraud_reports(reporter_cif_no);
CREATE INDEX IF NOT EXISTS idx_fraud_reports_account ON fraud_reports(reported_account_no, reported_bank_code);
CREATE INDEX IF NOT EXISTS idx_reported_accounts_lookup ON reported_accounts(account_no, bank_code);
CREATE INDEX IF NOT EXISTS idx_reported_customers_cif ON reported_customers(cif_no);
CREATE INDEX IF NOT EXISTS idx_fraud_decisions_action ON fraud_decisions(action_id);
"""

# Tables in load order (respects FK dependencies)
TABLES = [
    "customers",
    "accounts",
    "cards",
    "beneficiaries",
    "merchants",
    "billers",
    "customer_biller_accounts",
    "transaction_categories",
    "transactions",
    "action_requests",
    "api_call_logs",
    "audit_logs",
    "fraud_reports",
    "reported_accounts",
    "reported_customers",
    "fraud_decisions",
]

# Boolean fields that need conversion from True/False string to 0/1
BOOL_FIELDS = {"is_saved", "requires_confirmation", "requires_otp", "has_evidence"}

# Integer fields (empty string → None)
INT_FIELDS = {"balance", "available_balance", "credit_limit", "available_limit",
              "amount", "balance_after", "http_status", "confidence_score",
              "valid_report_count", "unique_reporter_count", "total_reported_amount",
              "avg_confidence_score", "reported_account_count", "matched_report_count"}


def load_csv(conn, table_name):
    csv_path = DATA_DIR / f"{table_name}.csv"
    if not csv_path.exists():
        print(f"  SKIP {table_name} (file not found)")
        return 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(f"  SKIP {table_name} (empty)")
        return 0

    columns = list(rows[0].keys())
    placeholders = ",".join(["?"] * len(columns))
    col_names = ",".join(columns)
    sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

    values = []
    for row in rows:
        row_values = []
        for col in columns:
            val = row[col]
            # Convert empty strings to None
            if val == "":
                val = None
            # Convert boolean strings
            elif col in BOOL_FIELDS:
                val = 1 if val in ("True", "true", "1") else 0
            # Convert integer fields
            elif col in INT_FIELDS and val is not None:
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    val = None
            # Convert float fields
            elif col == "risk_score" and val is not None:
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = None
            row_values.append(val)
        values.append(tuple(row_values))

    conn.executemany(sql, values)
    return len(values)


def main():
    # Ensure db directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing db
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Create schema
    conn.executescript(SCHEMA)
    print("Schema created.\n")

    # Load tables
    print("Loading CSV data:")
    total = 0
    for table in TABLES:
        count = load_csv(conn, table)
        total += count
        print(f"  {table}: {count} rows")

    conn.commit()

    # Verify
    print(f"\nTotal rows loaded: {total}")
    print(f"Database: {DB_PATH.resolve()}")
    print(f"Size: {DB_PATH.stat().st_size / 1024 / 1024:.2f} MB")

    # Quick sanity check
    cur = conn.cursor()
    for table in TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        assert count > 0, f"Table {table} is empty!"

    print("\nAll tables loaded successfully.")
    conn.close()


if __name__ == "__main__":
    main()
