-- ============================================================
-- Bills table — unpaid/paid bills for bill payment flow
-- ============================================================

CREATE TABLE IF NOT EXISTS bills (
    bill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    biller_code VARCHAR(50) NOT NULL,
    customer_bill_code VARCHAR(50) NOT NULL,
    bill_period VARCHAR(20) NOT NULL,
    amount_due NUMERIC(18, 2) NOT NULL,
    due_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'UNPAID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS idx_bills_lookup
ON bills (biller_code, customer_bill_code, status);
