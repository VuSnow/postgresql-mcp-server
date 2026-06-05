# Tổng hợp full-stack: KH, TK, thẻ, giao dịch, fraud (5+ tables)

## Complexity: complex

## Tables Used: customers, accounts, cards, transactions, fraud_reports, reported_customers

## Question (Vietnamese)
Cho KH CIF000099: thông tin cá nhân, số TK, số thẻ, giao dịch gần nhất, và có từng bị report fraud không?

## Join Logic
- Cần 6 bảng cho 1 query dashboard tổng hợp.
- **JOIN paths**:
  - `customers.cif_no` = base
  - `accounts.cif_no = customers.cif_no`
  - `cards.cif_no = customers.cif_no`
  - `transactions.cif_no = customers.cif_no` (latest)
  - `reported_customers.reported_cif = customers.cif_no`
- Dùng subquery/CTE cho transactions (latest) và fraud check.

## SQL
```sql
WITH customer_info AS (
    SELECT cif_no, full_name, phone_number, kyc_level, status
    FROM customers
    WHERE cif_no = 'CIF000099'
),
account_stats AS (
    SELECT
        COUNT(*) AS total_accounts,
        SUM(balance) AS total_balance,
        COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_accounts
    FROM accounts
    WHERE cif_no = 'CIF000099'
),
card_stats AS (
    SELECT
        COUNT(*) AS total_cards,
        COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_cards
    FROM cards
    WHERE cif_no = 'CIF000099'
),
last_txn AS (
    SELECT transaction_time, transaction_type, amount, direction
    FROM transactions
    WHERE cif_no = 'CIF000099' AND status = 'SUCCESS'
    ORDER BY transaction_time DESC
    LIMIT 1
),
fraud_check AS (
    SELECT COUNT(*) AS fraud_report_count
    FROM reported_customers
    WHERE reported_cif = 'CIF000099'
)
SELECT
    ci.*,
    ast.total_accounts,
    ast.total_balance,
    ast.active_accounts,
    cs.total_cards,
    cs.active_cards,
    lt.transaction_time AS last_txn_time,
    lt.transaction_type AS last_txn_type,
    lt.amount AS last_txn_amount,
    lt.direction AS last_txn_direction,
    fc.fraud_report_count,
    CASE WHEN fc.fraud_report_count > 0 THEN 'YES' ELSE 'NO' END AS has_fraud_reports
FROM customer_info ci
CROSS JOIN account_stats ast
CROSS JOIN card_stats cs
CROSS JOIN fraud_check fc
LEFT JOIN last_txn lt ON TRUE;
```

## Explanation
5 CTE, mỗi CTE 1 khía cạnh. CROSS JOIN an toàn (mỗi CTE max 1 row). LEFT JOIN last_txn vì có thể chưa có giao dịch. Kết quả: 1 row complete profile. Query phức tạp nhất — demo full capabilities.
