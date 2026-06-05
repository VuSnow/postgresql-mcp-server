# Giao dịch pending quá lâu

## Complexity: medium

## Tables Used: transactions, customers

## Question (Vietnamese)
Tìm giao dịch có status = PENDING quá 1 giờ, kèm thông tin khách hàng.

## Join Logic
- Cần `transactions` để filter status = 'PENDING' và thời gian.
- Cần `customers` để lấy tên và SĐT (liên lạc KH).
- **JOIN path**: `transactions.cif_no = customers.cif_no`

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    c.full_name,
    c.phone_number,
    t.amount,
    t.transaction_type,
    t.channel,
    EXTRACT(EPOCH FROM (NOW() - t.transaction_time)) / 3600 AS hours_pending
FROM transactions t
JOIN customers c ON t.cif_no = c.cif_no
WHERE t.status = 'PENDING'
  AND t.transaction_time < NOW() - INTERVAL '1 hour'
ORDER BY t.transaction_time ASC
LIMIT 50;
```

## Explanation
Filter PENDING + quá 1 giờ. Tính hours_pending cho biết chờ bao lâu. Use case: ops team theo dõi giao dịch stuck cần xử lý.
