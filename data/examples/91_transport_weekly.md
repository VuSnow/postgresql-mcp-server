# Chi tiêu giao thông (TRANSPORT) theo tuần

## Complexity: medium

## Tables Used: transactions, transaction_categories

## Question (Vietnamese)
Tổng chi tiêu giao thông của khách hàng CIF000060 mỗi tuần trong tháng này.

## Join Logic
- Cần `transactions` để lấy giao dịch chi tiêu.
- Cần `transaction_categories` để filter category_code = 'TRANSPORT'.
- **JOIN path**: `transactions.category_id = transaction_categories.category_id`
- GROUP BY tuần (DATE_TRUNC('week')).

## SQL
```sql
SELECT
    DATE_TRUNC('week', t.transaction_time) AS week_start,
    COUNT(*) AS trip_count,
    SUM(t.amount) AS total_transport,
    ROUND(AVG(t.amount)) AS avg_per_trip
FROM transactions t
JOIN transaction_categories tc ON t.category_id = tc.category_id
WHERE t.cif_no = 'CIF000060'
  AND tc.category_code = 'TRANSPORT'
  AND t.direction = 'OUT'
  AND t.status = 'SUCCESS'
  AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY DATE_TRUNC('week', t.transaction_time)
ORDER BY week_start ASC;
```

## Explanation
JOIN transaction_categories filter TRANSPORT. GROUP BY tuần → thấy chi tiêu giao thông hàng tuần. avg_per_trip = giá trị trung bình mỗi chuyến đi.
