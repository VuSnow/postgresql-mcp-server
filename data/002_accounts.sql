-- Accounts table: bank accounts linked to customers
-- Idempotent: safe to run multiple times

DROP TABLE IF EXISTS public.accounts CASCADE;

CREATE TABLE IF NOT EXISTS public.accounts (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES public.customers(id),
    account_number  VARCHAR(20) UNIQUE NOT NULL,
    account_type    VARCHAR(20) NOT NULL CHECK (account_type IN ('checking', 'savings', 'credit', 'loan')),
    currency        VARCHAR(3) DEFAULT 'VND',
    balance         NUMERIC(18, 2) NOT NULL DEFAULT 0,
    credit_limit    NUMERIC(18, 2),
    interest_rate   NUMERIC(5, 4),
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'frozen', 'closed')),
    opened_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at       TIMESTAMP WITH TIME ZONE
);

INSERT INTO public.accounts (id, customer_id, account_number, account_type, currency, balance, credit_limit, interest_rate, status, opened_at) VALUES
-- Customer 1: An - checking + savings
(1,  1, '1001-0001-0001', 'checking', 'VND', 25000000.00,   NULL,          NULL,   'active', '2023-01-10 08:30:00+07'),
(2,  1, '1001-0001-0002', 'savings',  'VND', 150000000.00,  NULL,          0.0450, 'active', '2023-01-15 09:00:00+07'),
-- Customer 2: Binh - checking + credit
(3,  2, '1001-0002-0001', 'checking', 'VND', 42000000.00,   NULL,          NULL,   'active', '2023-02-14 10:00:00+07'),
(4,  2, '1001-0002-0002', 'credit',   'VND', -8500000.00,   50000000.00,   0.1800, 'active', '2023-03-01 11:00:00+07'),
-- Customer 3: Cuong - checking + savings + loan
(5,  3, '1001-0003-0001', 'checking', 'VND', 18000000.00,   NULL,          NULL,   'active', '2023-03-01 10:30:00+07'),
(6,  3, '1001-0003-0002', 'savings',  'VND', 500000000.00,  NULL,          0.0550, 'active', '2023-03-05 14:00:00+07'),
(7,  3, '1001-0003-0003', 'loan',     'VND', -200000000.00, NULL,          0.0890, 'active', '2023-04-01 08:00:00+07'),
-- Customer 4: Duc - checking
(8,  4, '1001-0004-0001', 'checking', 'VND', 67000000.00,   NULL,          NULL,   'active', '2023-04-20 11:30:00+07'),
-- Customer 5: Em - frozen accounts
(9,  5, '1001-0005-0001', 'checking', 'VND', 3500000.00,    NULL,          NULL,   'frozen', '2023-05-05 14:30:00+07'),
(10, 5, '1001-0005-0002', 'savings',  'VND', 80000000.00,   NULL,          0.0450, 'frozen', '2023-05-10 09:00:00+07'),
-- Customer 6: Phuc - checking + savings
(11, 6, '1001-0006-0001', 'checking', 'VND', 95000000.00,   NULL,          NULL,   'active', '2023-06-15 09:00:00+07'),
(12, 6, '1001-0006-0002', 'savings',  'VND', 320000000.00,  NULL,          0.0600, 'active', '2023-06-20 10:00:00+07'),
-- Customer 7: Giang - checking
(13, 7, '1001-0007-0001', 'checking', 'VND', 12000000.00,   NULL,          NULL,   'active', '2023-07-22 09:30:00+07'),
-- Customer 8: Huy - checking + credit
(14, 8, '1001-0008-0001', 'checking', 'VND', 55000000.00,   NULL,          NULL,   'active', '2023-08-10 17:00:00+07'),
(15, 8, '1001-0008-0002', 'credit',   'VND', -22000000.00,  100000000.00,  0.1500, 'active', '2023-08-15 10:00:00+07'),
-- Customer 9: Inh - closed
(16, 9, '1001-0009-0001', 'checking', 'VND', 0.00,          NULL,          NULL,   'closed', '2023-09-01 07:30:00+07'),
-- Customer 10: Kim - checking + savings
(17, 10, '1001-0010-0001', 'checking', 'VND', 38000000.00,  NULL,          NULL,   'active', '2023-10-18 13:30:00+07'),
(18, 10, '1001-0010-0002', 'savings',  'VND', 720000000.00, NULL,          0.0650, 'active', '2023-10-20 08:00:00+07');

SELECT setval('public.accounts_id_seq', 18);
