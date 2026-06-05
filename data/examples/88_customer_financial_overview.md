# Multi-CTE: tổng hợp tài chính KH (dashboard)

## Complexity: complex

## Tables Used: customers, accounts, transactions, cards

## Question (Vietnamese)
Cho tôi overview tài chính tổng hợp của khách hàng CIF000050: tổng TK, tổng số dư, tổng thẻ, chi tiêu tháng này, thu nhập tháng này.

## Join Logic
- Cần nhiều bảng, dùng Multi-CTE cho rõ ràng:
  - CTE1: đếm accounts + tổng balance
  - CTE2: đếm cards
  - CTE3: chi tiêu tháng (transactions OUT)
  - CTE4: thu nhập tháng (transactions IN)
- CROSS JOIN tất cả CTE (mỗi CTE 1 row).

## SQL
```sql
WITH account_summary AS (
    SELECT
        COUNT(*) AS total_accounts,
        SUM(balance) AS total_balance
    FROM accounts
    WHERE cif_no = 'CIF000050' AND status = 'ACTIVE'
),
card_summary AS (
    SELECT COUNT(*) AS total_cards
    FROM cards
    WHERE cif_no = 'CIF000050' AND status = 'ACTIVE'
),
monthly_out AS (
    SELECT COALESCE(SUM(amount), 0) AS total_spent
    FROM transactions
    WHERE cif_no = 'CIF000050'
      AND direction = 'OUT' AND status = 'SUCCESS'
      AND transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
),
monthly_in AS (
    SELECT COALESCE(SUM(amount), 0) AS total_income
    FROM transactions
    WHERE cif_no = 'CIF000050'
      AND direction = 'IN' AND status = 'SUCCESS'
      AND transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
)
SELECT
    a.total_accounts,
    a.total_balance,
    c.total_cards,
    mo.total_spent,
    mi.total_income,
    mi.total_income - mo.total_spent AS net_flow
FROM account_summary a
CROSS JOIN card_summary c
CROSS JOIN monthly_out mo
CROSS JOIN monthly_in mi;
```

## Explanation
4 CTE, mỗi CTE 1 khía cạnh tài chính. CROSS JOIN kết hợp (mỗi CTE 1 row nên CROSS JOIN an toàn). COALESCE tránh NULL nếu không có giao dịch. Kết quả: 1 row dashboard.
