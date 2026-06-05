# Giao dịch thất bại gần đây

## Complexity: medium

## Tables Used: transactions, customers

## Question (Vietnamese)
Liệt kê các giao dịch thất bại hoặc bị đảo trong 3 ngày gần đây, bao gồm tên khách hàng.

## Join Logic
- Cần `transactions` để tìm giao dịch có status FAILED hoặc REVERSED.
- Cần `customers` để lấy `full_name`.
- **JOIN path**: `transactions.cif_no = customers.cif_no`

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    c.full_name,
    t.transaction_type,
    t.amount,
    t.direction,
    t.channel,
    t.status,
    t.description
FROM transactions t
JOIN customers c ON t.cif_no = c.cif_no
WHERE t.status IN ('FAILED', 'REVERSED')
  AND t.transaction_time >= CURRENT_DATE - INTERVAL '3 days'
ORDER BY t.transaction_time DESC
LIMIT 100;
```

## Explanation
JOIN transactions với customers để lấy tên. Filter bằng IN clause cho 2 status lỗi. Query không filter theo 1 KH cụ thể → system-wide monitoring.
