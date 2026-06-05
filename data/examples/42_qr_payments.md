# Giao dịch QR Payment

## Complexity: simple

## Tables Used: transactions

## Question (Vietnamese)
Liệt kê các giao dịch thanh toán QR của khách hàng CIF000040 trong 2 tuần gần đây.

## Join Logic
- Chỉ cần bảng `transactions`.
- Filter theo `channel = 'QR'` hoặc `transaction_type = 'QR_PAYMENT'`.
- Không cần JOIN vì chỉ cần data từ transactions.

## SQL
```sql
SELECT
    transaction_ref,
    transaction_time,
    amount,
    direction,
    counterparty_name,
    description,
    status
FROM transactions
WHERE cif_no = 'CIF000040'
  AND transaction_type = 'QR_PAYMENT'
  AND transaction_time >= CURRENT_DATE - INTERVAL '14 days'
ORDER BY transaction_time DESC
LIMIT 50;
```

## Explanation
Query đơn giản trên 1 bảng. Filter transaction_type = 'QR_PAYMENT'. Sắp xếp theo thời gian mới nhất.
