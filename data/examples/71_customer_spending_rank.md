# Xếp hạng khách hàng theo tổng chi tiêu (window function)

## Complexity: complex

## Tables Used: transactions, customers

## Question (Vietnamese)
Xếp hạng top 20 khách hàng chi tiêu nhiều nhất trong tháng, kèm tỷ trọng so với tổng chi tiêu hệ thống.

## Join Logic
- Cần `transactions` để tính tổng chi tiêu mỗi KH.
- Cần `customers` để lấy tên.
- **JOIN path**: `transactions.cif_no = customers.cif_no`
- Window function RANK() và SUM() OVER() để tính ranking + tỷ trọng.

## SQL
```sql
WITH monthly_spending AS (
    SELECT
        t.cif_no,
        c.full_name,
        SUM(t.amount) AS total_spent,
        COUNT(*) AS txn_count
    FROM transactions t
    JOIN customers c ON t.cif_no = c.cif_no
    WHERE t.direction = 'OUT'
      AND t.status = 'SUCCESS'
      AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY t.cif_no, c.full_name
)
SELECT
    RANK() OVER (ORDER BY total_spent DESC) AS rank,
    cif_no,
    full_name,
    total_spent,
    txn_count,
    ROUND(total_spent * 100.0 / SUM(total_spent) OVER (), 2) AS pct_of_total
FROM monthly_spending
ORDER BY total_spent DESC
LIMIT 20;
```

## Explanation
CTE tính tổng chi tiêu mỗi KH. RANK() OVER xếp hạng. SUM() OVER() không partition = tổng hệ thống → tính % mỗi KH. Kết quả: top 20 KH kèm tỷ trọng.
