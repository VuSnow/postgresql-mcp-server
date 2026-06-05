# Giao dịch giá trị lớn (anomaly detection)

## Complexity: complex

## Tables Used: transactions, customers, accounts

## Question (Vietnamese)
Liệt kê các giao dịch có giá trị trên 50 triệu đồng trong 7 ngày gần đây, kèm tên khách hàng và loại tài khoản.

## Join Logic
- Cần `transactions` để tìm giao dịch giá trị lớn.
- Cần `customers` để lấy `full_name`.
- Cần `accounts` để lấy `account_type`.
- **JOIN path 1**: `transactions.cif_no = customers.cif_no`
- **JOIN path 2**: `transactions.account_no = accounts.account_no`
- INNER JOIN cho cả 2 vì cif_no và account_no đều NOT NULL.

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    c.full_name,
    a.account_no,
    a.account_type,
    t.amount,
    t.direction,
    t.transaction_type,
    t.counterparty_name,
    t.channel,
    t.status
FROM transactions t
JOIN customers c ON t.cif_no = c.cif_no
JOIN accounts a ON t.account_no = a.account_no
WHERE t.amount >= 50000000
  AND t.transaction_time >= CURRENT_DATE - INTERVAL '7 days'
  AND t.status = 'SUCCESS'
ORDER BY t.amount DESC
LIMIT 100;
```

## Explanation
3-table JOIN: transactions (trung tâm) → customers (tên) → accounts (loại TK). Filter amount >= 50,000,000 (50 triệu VND, BIGINT). Sắp xếp theo amount DESC → giao dịch lớn nhất lên trước.
