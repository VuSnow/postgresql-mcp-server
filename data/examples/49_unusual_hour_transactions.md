# Giao dịch trong giờ bất thường (ngoài giờ hành chính)

## Complexity: complex

## Tables Used: transactions, customers

## Question (Vietnamese)
Tìm các giao dịch giá trị lớn (> 20 triệu) xảy ra ngoài giờ hành chính (trước 7h sáng hoặc sau 22h) trong tuần này.

## Join Logic
- Cần `transactions` để filter theo thời gian và amount.
- Cần `customers` để lấy tên KH.
- **JOIN path**: `transactions.cif_no = customers.cif_no`
- Dùng EXTRACT(HOUR FROM transaction_time) để filter giờ.

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    c.full_name,
    t.amount,
    t.direction,
    t.transaction_type,
    t.channel,
    t.counterparty_name,
    EXTRACT(HOUR FROM t.transaction_time) AS txn_hour
FROM transactions t
JOIN customers c ON t.cif_no = c.cif_no
WHERE t.amount > 20000000
  AND t.transaction_time >= DATE_TRUNC('week', CURRENT_DATE)
  AND t.status = 'SUCCESS'
  AND (EXTRACT(HOUR FROM t.transaction_time) < 7
       OR EXTRACT(HOUR FROM t.transaction_time) >= 22)
ORDER BY t.amount DESC
LIMIT 100;
```

## Explanation
Filter giờ bất thường bằng EXTRACT(HOUR FROM ...). Kết hợp filter amount > 20M để tìm giao dịch anomaly. Use case: fraud detection / risk monitoring.
