# Top khách hàng chi tiêu nhiều nhất

## Complexity: complex

## Tables Used: customers, transactions

## Question (Vietnamese)
Cho tôi top 10 khách hàng chi tiêu nhiều nhất trong tháng này, bao gồm tên, tổng chi tiêu và số giao dịch.

## Join Logic
- Cần `transactions` để tính tổng chi tiêu (SUM amount) và đếm số giao dịch.
- Cần `customers` để lấy `full_name` — transactions chỉ có cif_no, không có tên khách hàng.
- **JOIN path**: `transactions.cif_no = customers.cif_no`
- GROUP BY theo khách hàng rồi ORDER BY DESC + LIMIT 10 để lấy top.

## SQL
```sql
SELECT
    c.cif_no,
    c.full_name,
    COUNT(*) AS transaction_count,
    SUM(t.amount) AS total_spent
FROM transactions t
JOIN customers c ON t.cif_no = c.cif_no
WHERE t.direction = 'OUT'
  AND t.status = 'SUCCESS'
  AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY c.cif_no, c.full_name
ORDER BY total_spent DESC
LIMIT 10;
```

## Explanation
JOIN transactions với customers để lấy tên. Aggregate theo khách hàng, SUM(amount) chỉ tính direction='OUT'. DATE_TRUNC('month', CURRENT_DATE) = đầu tháng hiện tại.
