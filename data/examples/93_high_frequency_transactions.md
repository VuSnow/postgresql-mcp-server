# Tần suất giao dịch bất thường (quá nhiều trong 1 giờ)

## Complexity: complex

## Tables Used: transactions, customers

## Question (Vietnamese)
Tìm khách hàng có > 10 giao dịch trong cùng 1 giờ (có thể là bot hoặc fraud).

## Join Logic
- Cần `transactions` để đếm theo giờ.
- Cần `customers` để lấy tên.
- **JOIN path**: `transactions.cif_no = customers.cif_no`
- GROUP BY cif_no + giờ, HAVING COUNT > 10.

## SQL
```sql
WITH hourly_activity AS (
    SELECT
        cif_no,
        DATE_TRUNC('hour', transaction_time) AS hour_slot,
        COUNT(*) AS txn_count,
        SUM(amount) AS total_amount
    FROM transactions
    WHERE transaction_time >= CURRENT_DATE - INTERVAL '7 days'
      AND status = 'SUCCESS'
    GROUP BY cif_no, DATE_TRUNC('hour', transaction_time)
    HAVING COUNT(*) > 10
)
SELECT
    ha.cif_no,
    c.full_name,
    ha.hour_slot,
    ha.txn_count,
    ha.total_amount
FROM hourly_activity ha
JOIN customers c ON ha.cif_no = c.cif_no
ORDER BY ha.txn_count DESC
LIMIT 20;
```

## Explanation
CTE GROUP BY KH + giờ, HAVING > 10 giao dịch. JOIN customers lấy tên. Use case: fraud detection — bot thường tạo nhiều giao dịch cùng lúc.
