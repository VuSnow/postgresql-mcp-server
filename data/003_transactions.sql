-- Transactions table: financial transactions between accounts
-- Idempotent: safe to run multiple times

DROP TABLE IF EXISTS public.transactions CASCADE;

CREATE TABLE IF NOT EXISTS public.transactions (
    id                  SERIAL PRIMARY KEY,
    account_id          INTEGER NOT NULL REFERENCES public.accounts(id),
    transaction_type    VARCHAR(20) NOT NULL CHECK (transaction_type IN ('deposit', 'withdrawal', 'transfer_in', 'transfer_out', 'payment', 'fee', 'interest')),
    amount              NUMERIC(18, 2) NOT NULL,
    balance_after       NUMERIC(18, 2) NOT NULL,
    currency            VARCHAR(3) DEFAULT 'VND',
    description         TEXT,
    reference_id        VARCHAR(50),
    counterparty_account VARCHAR(20),
    channel             VARCHAR(20) CHECK (channel IN ('atm', 'mobile', 'web', 'branch', 'pos', 'auto')),
    status              VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('completed', 'pending', 'failed', 'reversed')),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO public.transactions (id, account_id, transaction_type, amount, balance_after, currency, description, reference_id, counterparty_account, channel, status, created_at) VALUES
-- Customer 1 (An) transactions on checking account (id=1)
(1,  1, 'deposit',      50000000.00,  50000000.00,  'VND', 'Salary Jan 2024',              'SAL-2024-001', NULL,             'auto',   'completed', '2024-01-05 08:00:00+07'),
(2,  1, 'withdrawal',   5000000.00,   45000000.00,  'VND', 'ATM withdrawal',               'ATM-2024-001', NULL,             'atm',    'completed', '2024-01-10 14:30:00+07'),
(3,  1, 'transfer_out', 20000000.00,  25000000.00,  'VND', 'Transfer to savings',          'TRF-2024-001', '1001-0001-0002', 'mobile', 'completed', '2024-01-12 09:15:00+07'),
(4,  1, 'payment',      3000000.00,   22000000.00,  'VND', 'Electric bill payment',        'PAY-2024-001', NULL,             'mobile', 'completed', '2024-01-15 10:00:00+07'),
(5,  1, 'deposit',      50000000.00,  72000000.00,  'VND', 'Salary Feb 2024',              'SAL-2024-002', NULL,             'auto',   'completed', '2024-02-05 08:00:00+07'),
(6,  1, 'payment',      15000000.00,  57000000.00,  'VND', 'Rent payment',                 'PAY-2024-002', NULL,             'web',    'completed', '2024-02-10 11:00:00+07'),
(7,  1, 'transfer_out', 30000000.00,  27000000.00,  'VND', 'Transfer to savings',          'TRF-2024-002', '1001-0001-0002', 'mobile', 'completed', '2024-02-15 09:00:00+07'),
(8,  1, 'withdrawal',   2000000.00,   25000000.00,  'VND', 'ATM withdrawal',               'ATM-2024-002', NULL,             'atm',    'completed', '2024-02-20 16:45:00+07'),

-- Customer 2 (Binh) transactions on checking (id=3)
(9,  3, 'deposit',      35000000.00,  35000000.00,  'VND', 'Salary Jan 2024',              'SAL-2024-003', NULL,             'auto',   'completed', '2024-01-05 08:00:00+07'),
(10, 3, 'payment',      2500000.00,   32500000.00,  'VND', 'Internet bill',                'PAY-2024-003', NULL,             'mobile', 'completed', '2024-01-18 13:20:00+07'),
(11, 3, 'transfer_out', 10000000.00,  22500000.00,  'VND', 'Transfer to friend',           'TRF-2024-003', '1001-0004-0001', 'mobile', 'completed', '2024-01-22 15:30:00+07'),
(12, 3, 'deposit',      35000000.00,  57500000.00,  'VND', 'Salary Feb 2024',              'SAL-2024-004', NULL,             'auto',   'completed', '2024-02-05 08:00:00+07'),
(13, 3, 'withdrawal',   8000000.00,   49500000.00,  'VND', 'ATM withdrawal',               'ATM-2024-003', NULL,             'atm',    'completed', '2024-02-12 10:00:00+07'),
(14, 3, 'payment',      7500000.00,   42000000.00,  'VND', 'Shopping payment',             'PAY-2024-004', NULL,             'pos',    'completed', '2024-02-25 17:45:00+07'),

-- Customer 3 (Cuong) transactions on checking (id=5)
(15, 5, 'deposit',      80000000.00,  80000000.00,  'VND', 'Salary Jan 2024',              'SAL-2024-005', NULL,             'auto',   'completed', '2024-01-05 08:00:00+07'),
(16, 5, 'transfer_out', 50000000.00,  30000000.00,  'VND', 'Transfer to savings',          'TRF-2024-004', '1001-0003-0002', 'web',    'completed', '2024-01-08 09:00:00+07'),
(17, 5, 'payment',      12000000.00,  18000000.00,  'VND', 'Loan installment',             'PAY-2024-005', NULL,             'auto',   'completed', '2024-01-15 08:00:00+07'),
(18, 5, 'deposit',      80000000.00,  98000000.00,  'VND', 'Salary Feb 2024',              'SAL-2024-006', NULL,             'auto',   'completed', '2024-02-05 08:00:00+07'),
(19, 5, 'transfer_out', 60000000.00,  38000000.00,  'VND', 'Transfer to savings',          'TRF-2024-005', '1001-0003-0002', 'web',    'completed', '2024-02-08 09:00:00+07'),
(20, 5, 'payment',      12000000.00,  26000000.00,  'VND', 'Loan installment',             'PAY-2024-006', NULL,             'auto',   'completed', '2024-02-15 08:00:00+07'),
(21, 5, 'withdrawal',   8000000.00,   18000000.00,  'VND', 'ATM withdrawal',               'ATM-2024-004', NULL,             'atm',    'completed', '2024-02-22 12:00:00+07'),

-- Customer 4 (Duc) checking (id=8) - receives transfer
(22, 8, 'transfer_in',  10000000.00,  77000000.00,  'VND', 'Transfer from Binh',           'TRF-2024-003', '1001-0002-0001', 'mobile', 'completed', '2024-01-22 15:30:00+07'),
(23, 8, 'deposit',      45000000.00,  122000000.00, 'VND', 'Salary Feb 2024',              'SAL-2024-007', NULL,             'auto',   'completed', '2024-02-05 08:00:00+07'),
(24, 8, 'payment',      25000000.00,  97000000.00,  'VND', 'Car insurance',                'PAY-2024-007', NULL,             'web',    'completed', '2024-02-18 14:00:00+07'),
(25, 8, 'withdrawal',   30000000.00,  67000000.00,  'VND', 'Branch withdrawal',            'ATM-2024-005', NULL,             'branch', 'completed', '2024-02-28 10:30:00+07'),

-- Customer 6 (Phuc) checking (id=11) - high balance
(26, 11, 'deposit',     120000000.00, 120000000.00, 'VND', 'Salary Jan 2024',              'SAL-2024-008', NULL,             'auto',   'completed', '2024-01-05 08:00:00+07'),
(27, 11, 'transfer_out', 25000000.00, 95000000.00,  'VND', 'Investment transfer',          'TRF-2024-006', '1001-0006-0002', 'web',    'completed', '2024-01-10 09:00:00+07'),
(28, 11, 'deposit',     120000000.00, 215000000.00, 'VND', 'Salary Feb 2024',              'SAL-2024-009', NULL,             'auto',   'completed', '2024-02-05 08:00:00+07'),
(29, 11, 'transfer_out', 50000000.00, 165000000.00, 'VND', 'Investment transfer',          'TRF-2024-007', '1001-0006-0002', 'web',    'completed', '2024-02-10 09:00:00+07'),
(30, 11, 'payment',      70000000.00, 95000000.00,  'VND', 'Property tax',                 'PAY-2024-008', NULL,             'branch', 'completed', '2024-02-20 15:00:00+07'),

-- Some failed/pending transactions
(31, 1, 'withdrawal',   100000000.00, 25000000.00,  'VND', 'ATM withdrawal - insufficient', 'ATM-2024-006', NULL,            'atm',    'failed',    '2024-02-25 20:00:00+07'),
(32, 3, 'transfer_out', 5000000.00,   42000000.00,  'VND', 'Transfer pending review',       'TRF-2024-008', '1001-0009-0001', 'mobile', 'pending',  '2024-02-28 11:00:00+07');

SELECT setval('public.transactions_id_seq', 32);
