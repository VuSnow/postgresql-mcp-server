# Chi tiêu tại merchant cụ thể — cross-customer

## Complexity: complex

## Tables Used: transactions, merchants, customers

## Question (Vietnamese)
Tìm tất cả khách hàng đã chi tiêu tại merchant "The Coffee House" trong tháng này, kèm tổng tiền mỗi người.

## Join Logic
- Cần `transactions` để lấy dữ liệu giao dịch.
- Cần `merchants` để filter theo `merchant_name`.
- Cần `customers` để lấy `full_name`.
- **JOIN path 1**: `transactions.merchant_id = merchants.merchant_id`
- **JOIN path 2**: `transactions.cif_no = customers.cif_no`
- GROUP BY khách hàng để tính tổng chi tiêu mỗi người.

## SQL
```sql
SELECT
    c.cif_no,
    c.full_name,
    COUNT(*) AS visit_count,
    SUM(t.amount) AS total_spent,
    MAX(t.transaction_time) AS last_visit
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
JOIN customers c ON t.cif_no = c.cif_no
WHERE m.merchant_name = 'The Coffee House'
  AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
  AND t.status = 'SUCCESS'
GROUP BY c.cif_no, c.full_name
ORDER BY total_spent DESC
LIMIT 50;
```

## Explanation
3-table JOIN: transactions → merchants (filter tên) → customers (lấy tên KH). GROUP BY khách hàng. Query cross-customer analysis (không filter 1 KH).
