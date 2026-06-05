-- Card controls & limits tables + seed data
BEGIN;

-- ============================================================
-- SCHEMA: card_controls
-- ============================================================

CREATE TABLE IF NOT EXISTS card_controls (
    card_id UUID PRIMARY KEY REFERENCES cards(card_id),
    online_payment_enabled BOOLEAN DEFAULT true,
    international_payment_enabled BOOLEAN DEFAULT false,
    atm_withdrawal_enabled BOOLEAN DEFAULT true,
    pos_payment_enabled BOOLEAN DEFAULT true,
    contactless_enabled BOOLEAN DEFAULT true,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SCHEMA: card_limits
-- ============================================================

CREATE TABLE IF NOT EXISTS card_limits (
    card_id UUID PRIMARY KEY REFERENCES cards(card_id),
    daily_atm_limit BIGINT DEFAULT 50000000,
    daily_pos_limit BIGINT DEFAULT 100000000,
    daily_online_limit BIGINT DEFAULT 30000000,
    per_transaction_limit BIGINT DEFAULT 50000000,
    max_daily_atm_limit BIGINT DEFAULT 200000000,
    max_daily_pos_limit BIGINT DEFAULT 500000000,
    max_daily_online_limit BIGINT DEFAULT 200000000,
    max_per_transaction_limit BIGINT DEFAULT 200000000,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SCHEMA: card_operation_requests
-- ============================================================

CREATE TABLE IF NOT EXISTS card_operation_requests (
    request_id UUID PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    card_id UUID NOT NULL REFERENCES cards(card_id),
    operation VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    old_value JSONB,
    new_value JSONB,
    reason TEXT,
    session_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- ============================================================
-- ALTER cards table: extend status enum
-- ============================================================

ALTER TABLE cards DROP CONSTRAINT IF EXISTS cards_status_check;
ALTER TABLE cards ADD CONSTRAINT cards_status_check
    CHECK(status IN ('ACTIVE','TEMP_LOCKED','LOST','STOLEN','BLOCKED_BY_BANK','EXPIRED','CLOSED'));

-- Migrate existing LOCKED → TEMP_LOCKED
UPDATE cards SET status = 'TEMP_LOCKED' WHERE status = 'LOCKED';

-- ============================================================
-- SEED: card_controls for all existing cards
-- ============================================================

INSERT INTO card_controls (card_id, online_payment_enabled, international_payment_enabled, atm_withdrawal_enabled, pos_payment_enabled, contactless_enabled, updated_at)
SELECT
    card_id,
    true,
    CASE WHEN card_network IN ('VISA', 'MASTERCARD') THEN true ELSE false END,
    true,
    true,
    CASE WHEN card_network IN ('VISA', 'MASTERCARD') THEN true ELSE false END,
    CURRENT_TIMESTAMP
FROM cards
ON CONFLICT (card_id) DO NOTHING;

-- ============================================================
-- SEED: card_limits for all existing cards
-- ============================================================

INSERT INTO card_limits (card_id, daily_atm_limit, daily_pos_limit, daily_online_limit, per_transaction_limit, max_daily_atm_limit, max_daily_pos_limit, max_daily_online_limit, max_per_transaction_limit, updated_at)
SELECT
    card_id,
    CASE WHEN card_type = 'CREDIT' THEN 100000000 ELSE 50000000 END,
    CASE WHEN card_type = 'CREDIT' THEN 200000000 ELSE 100000000 END,
    CASE WHEN card_type = 'CREDIT' THEN 100000000 ELSE 30000000 END,
    CASE WHEN card_type = 'CREDIT' THEN 100000000 ELSE 50000000 END,
    200000000,
    500000000,
    200000000,
    200000000,
    CURRENT_TIMESTAMP
FROM cards
ON CONFLICT (card_id) DO NOTHING;

COMMIT;
