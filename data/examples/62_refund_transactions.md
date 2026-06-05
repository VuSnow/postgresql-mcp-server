# Giao dịch hoàn tiền (REFUND)

## Complexity: medium

## Tables Used: transactions, merchants

## Question (Vietnamese)
Liệt kê các giao dịch hoàn tiền (REFUND) trong 30 ngày gần đây, kèm tên merchant nếu có.

## Join Logic
- Cần `transactions` để filter transaction_type = 'REFUND'.
- Cần `merchants` để lấy tên merchant (nếu refund liên quan thẻ).
- **JOIN path**: `transactions.merchant_id = merchants.merchant_id`
- LEFT JOIN vì merchant_id có thể NULL (refund từ bank transfer không có merchant).

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    t.cif_no,
    t.amount,
    t.description,
    m.merchant_name,
    t.channel,
    t.status
FROM transactions t
LEFT JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.transaction_type = 'REFUND'
  AND t.direction = 'IN'
  AND t.transaction_time >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY t.transaction_time DESC
LIMIT 100;
```

## Explanation
LEFT JOIN merchants vì refund có thể không gắn merchant. Filter direction = 'IN' vì refund là tiền vào.
