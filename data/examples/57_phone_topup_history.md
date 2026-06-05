# Giao dịch nạp điện thoại (PHONE_TOPUP)

## Complexity: simple

## Tables Used: transactions

## Question (Vietnamese)
Liệt kê các giao dịch nạp điện thoại của khách hàng CIF000045 trong 3 tháng gần đây.

## Join Logic
- Chỉ cần bảng `transactions`.
- Filter `transaction_type = 'PHONE_TOPUP'` hoặc tìm trong description.
- Không cần JOIN.

## SQL
```sql
SELECT
    transaction_ref,
    transaction_time,
    amount,
    description,
    channel,
    status
FROM transactions
WHERE cif_no = 'CIF000045'
  AND transaction_type = 'PHONE_TOPUP'
  AND transaction_time >= CURRENT_DATE - INTERVAL '3 months'
ORDER BY transaction_time DESC
LIMIT 50;
```

## Explanation
Query đơn giản. Filter transaction_type cho nạp điện thoại. Description thường chứa số điện thoại được nạp.
