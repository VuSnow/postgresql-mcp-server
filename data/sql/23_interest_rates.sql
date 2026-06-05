-- Interest rates table for financial planning
CREATE TABLE IF NOT EXISTS interest_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_code VARCHAR(50) NOT NULL,
    product_type VARCHAR(30) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    currency VARCHAR(3) DEFAULT 'VND',
    term_months INT,
    annual_rate DECIMAL(5,2) NOT NULL,
    min_amount DECIMAL(18,0),
    max_amount DECIMAL(18,0),
    customer_segment VARCHAR(30) DEFAULT 'ALL',
    channel VARCHAR(20) DEFAULT 'ALL',
    effective_from DATE NOT NULL,
    effective_to DATE,
    status VARCHAR(10) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_interest_rates_lookup
ON interest_rates(product_type, term_months, status, effective_from);

-- Seed data
INSERT INTO interest_rates (product_code, product_type, product_name, term_months, annual_rate, min_amount, channel, effective_from) VALUES
('DEMAND_VND', 'SAVINGS', 'Tiền gửi không kỳ hạn', NULL, 0.10, 0, 'ALL', '2026-01-01'),
('SAVINGS_ONLINE_1M', 'SAVINGS', 'Tiết kiệm online 1 tháng', 1, 2.90, 1000000, 'ONLINE', '2026-01-01'),
('SAVINGS_ONLINE_3M', 'SAVINGS', 'Tiết kiệm online 3 tháng', 3, 3.40, 1000000, 'ONLINE', '2026-01-01'),
('SAVINGS_ONLINE_6M', 'SAVINGS', 'Tiết kiệm online 6 tháng', 6, 4.50, 1000000, 'ONLINE', '2026-01-01'),
('SAVINGS_ONLINE_12M', 'SAVINGS', 'Tiết kiệm online 12 tháng', 12, 5.00, 1000000, 'ONLINE', '2026-01-01'),
('SAVINGS_ONLINE_24M', 'SAVINGS', 'Tiết kiệm online 24 tháng', 24, 5.20, 1000000, 'ONLINE', '2026-01-01'),
('SAVINGS_COUNTER_3M', 'SAVINGS', 'Tiết kiệm quầy 3 tháng', 3, 3.20, 5000000, 'COUNTER', '2026-01-01'),
('SAVINGS_COUNTER_6M', 'SAVINGS', 'Tiết kiệm quầy 6 tháng', 6, 4.30, 5000000, 'COUNTER', '2026-01-01'),
('SAVINGS_COUNTER_12M', 'SAVINGS', 'Tiết kiệm quầy 12 tháng', 12, 4.80, 5000000, 'COUNTER', '2026-01-01'),
('SAVINGS_COUNTER_24M', 'SAVINGS', 'Tiết kiệm quầy 24 tháng', 24, 5.00, 5000000, 'COUNTER', '2026-01-01'),
('LOAN_PERSONAL', 'LOAN', 'Vay tiêu dùng cá nhân', 12, 8.50, 10000000, 'ALL', '2026-01-01'),
('LOAN_PERSONAL_24M', 'LOAN', 'Vay tiêu dùng 24 tháng', 24, 9.00, 10000000, 'ALL', '2026-01-01'),
('LOAN_MORTGAGE', 'LOAN', 'Vay mua nhà', 240, 7.20, 100000000, 'ALL', '2026-01-01')
ON CONFLICT DO NOTHING;
