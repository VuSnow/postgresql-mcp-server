# Khách hàng inactive — không giao dịch lâu

## Complexity: complex

## Tables Used: customers, transactions

## Question (Vietnamese)
Tìm khách hàng active nhưng không có giao dịch nào trong 90 ngày gần đây (inactive users).

## Join Logic
- Cần `customers` làm base (status = 'ACTIVE').
- Cần check `transactions` — dùng NOT EXISTS hoặc LEFT JOIN + IS NULL.
- NOT EXISTS pattern: không có row nào trong transactions >= 90 ngày trước.

## SQL
```sql
SELECT
    c.cif_no,
    c.full_name,
    c.phone_number,
    c.onboarded_at,
    (
        SELECT MAX(transaction_time)
        FROM transactions
        WHERE cif_no = c.cif_no
    ) AS last_transaction_date
FROM customers c
WHERE c.status = 'ACTIVE'
  AND NOT EXISTS (
      SELECT 1
      FROM transactions t
      WHERE t.cif_no = c.cif_no
        AND t.transaction_time >= CURRENT_DATE - INTERVAL '90 days'
  )
ORDER BY last_transaction_date ASC NULLS FIRST
LIMIT 50;
```

## Explanation
NOT EXISTS: KH active nhưng không có giao dịch trong 90 ngày. Correlated subquery lấy last_transaction_date để biết lần cuối giao dịch khi nào. NULLS FIRST = chưa bao giờ giao dịch lên trước.
