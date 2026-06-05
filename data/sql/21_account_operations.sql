-- Account operations: ALTER accounts + account_products table
BEGIN;

-- ============================================================
-- ALTER accounts: add is_primary, nickname, closed_at
-- ============================================================

ALTER TABLE accounts ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT false;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS nickname VARCHAR(100);

-- Set first ACTIVE account per customer as primary
UPDATE accounts a
SET is_primary = true
WHERE a.account_id = (
    SELECT a2.account_id FROM accounts a2
    WHERE a2.cif_no = a.cif_no AND a2.status = 'ACTIVE'
    ORDER BY a2.opened_at ASC
    LIMIT 1
);

-- ============================================================
-- SCHEMA: account_products
-- ============================================================

CREATE TABLE IF NOT EXISTS account_products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_code VARCHAR(30) UNIQUE NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(30) NOT NULL,
    currency VARCHAR(5) NOT NULL DEFAULT 'VND',
    min_age INT DEFAULT 18,
    requires_kyc BOOLEAN DEFAULT true,
    monthly_fee BIGINT DEFAULT 0,
    opening_fee BIGINT DEFAULT 0,
    max_accounts_per_customer INT DEFAULT 3,
    is_active BOOLEAN DEFAULT true,
    description TEXT
);

-- ============================================================
-- SEED: account_products (3 products)
-- ============================================================

INSERT INTO account_products (product_code, product_name, account_type, currency, min_age, requires_kyc, monthly_fee, opening_fee, max_accounts_per_customer, is_active, description)
VALUES
    ('CURRENT_VND', 'Tài khoản thanh toán VND', 'PAYMENT', 'VND', 18, true, 0, 0, 3, true, 'Tài khoản thanh toán nội địa, miễn phí duy trì. Dùng cho chi tiêu hàng ngày, nhận lương, chuyển khoản.'),
    ('CURRENT_USD', 'Tài khoản thanh toán USD', 'PAYMENT', 'USD', 18, true, 50000, 0, 2, true, 'Tài khoản ngoại tệ USD, phí duy trì 50,000 VND/tháng. Dùng để nhận tiền quốc tế, thanh toán nước ngoài.'),
    ('SAVINGS_VND', 'Tài khoản tiết kiệm VND', 'SAVINGS', 'VND', 18, true, 0, 0, 5, true, 'Tài khoản tiết kiệm không kỳ hạn. Lãi suất theo bậc thang số dư.')
ON CONFLICT (product_code) DO NOTHING;

COMMIT;
