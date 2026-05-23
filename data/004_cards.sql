-- Cards table: debit/credit cards linked to accounts
-- Idempotent: safe to run multiple times

DROP TABLE IF EXISTS public.cards CASCADE;

CREATE TABLE IF NOT EXISTS public.cards (
    id              SERIAL PRIMARY KEY,
    account_id      INTEGER NOT NULL REFERENCES public.accounts(id),
    card_number     VARCHAR(19) UNIQUE NOT NULL,  -- masked: only last 4 visible in queries
    card_type       VARCHAR(10) NOT NULL CHECK (card_type IN ('debit', 'credit')),
    brand           VARCHAR(20) NOT NULL CHECK (brand IN ('visa', 'mastercard', 'jcb', 'napas')),
    cardholder_name VARCHAR(100) NOT NULL,
    expiry_date     DATE NOT NULL,
    daily_limit     NUMERIC(18, 2) NOT NULL DEFAULT 50000000,
    is_contactless  BOOLEAN DEFAULT TRUE,
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'blocked', 'expired', 'cancelled')),
    issued_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO public.cards (id, account_id, card_number, card_type, brand, cardholder_name, expiry_date, daily_limit, is_contactless, status, issued_at) VALUES
-- Customer 1 (An) - debit on checking
(1,  1,  '4111-XXXX-XXXX-1001', 'debit',  'visa',       'NGUYEN VAN AN',      '2026-12-31', 50000000.00,  TRUE,  'active',  '2023-01-10 08:30:00+07'),
-- Customer 2 (Binh) - debit + credit
(2,  3,  '4111-XXXX-XXXX-2001', 'debit',  'visa',       'TRAN THI BINH',      '2026-06-30', 30000000.00,  TRUE,  'active',  '2023-02-14 10:00:00+07'),
(3,  4,  '5500-XXXX-XXXX-2002', 'credit', 'mastercard', 'TRAN THI BINH',      '2027-03-31', 50000000.00,  TRUE,  'active',  '2023-03-01 11:00:00+07'),
-- Customer 3 (Cuong) - debit
(4,  5,  '9704-XXXX-XXXX-3001', 'debit',  'napas',      'LE HOANG CUONG',     '2026-09-30', 100000000.00, TRUE,  'active',  '2023-03-01 10:30:00+07'),
-- Customer 4 (Duc) - debit
(5,  8,  '4111-XXXX-XXXX-4001', 'debit',  'visa',       'PHAM MINH DUC',      '2025-12-31', 50000000.00,  TRUE,  'expired', '2023-04-20 11:30:00+07'),
(6,  8,  '4111-XXXX-XXXX-4002', 'debit',  'visa',       'PHAM MINH DUC',      '2027-12-31', 50000000.00,  TRUE,  'active',  '2025-01-05 09:00:00+07'),
-- Customer 5 (Em) - blocked
(7,  9,  '3528-XXXX-XXXX-5001', 'debit',  'jcb',        'VO THI EM',          '2026-05-31', 20000000.00,  FALSE, 'blocked', '2023-05-05 14:30:00+07'),
-- Customer 6 (Phuc) - premium
(8,  11, '5500-XXXX-XXXX-6001', 'debit',  'mastercard', 'HOANG VAN PHUC',     '2027-06-30', 200000000.00, TRUE,  'active',  '2023-06-15 09:00:00+07'),
-- Customer 8 (Huy) - debit + credit
(9,  14, '4111-XXXX-XXXX-8001', 'debit',  'visa',       'BUI QUOC HUY',       '2026-08-31', 50000000.00,  TRUE,  'active',  '2023-08-10 17:00:00+07'),
(10, 15, '5500-XXXX-XXXX-8002', 'credit', 'mastercard', 'BUI QUOC HUY',       '2027-08-31', 100000000.00, TRUE,  'active',  '2023-08-15 10:00:00+07'),
-- Customer 10 (Kim) - debit
(11, 17, '9704-XXXX-XXXX-0001', 'debit',  'napas',      'LY THI KIM',         '2027-10-31', 80000000.00,  TRUE,  'active',  '2023-10-18 13:30:00+07');

SELECT setval('public.cards_id_seq', 11);
