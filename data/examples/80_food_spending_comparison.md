# Chi tiêu FOOD + GROCERIES — ngân sách ăn uống

## Complexity: medium

## Tables Used: transactions, transaction_categories

## Question (Vietnamese)
Tổng chi tiêu cho ăn uống (FOOD + GROCERIES) của khách hàng CIF000033 trong tháng, so với tháng trước.

## Join Logic
- Cần `transactions` để lấy giao dịch chi tiêu.
- Cần `transaction_categories` để filter category_code IN ('FOOD', 'GROCERIES').
- **JOIN path**: `transactions.category_id = transaction_categories.category_id`
- Dùng conditional aggregation (FILTER) cho 2 tháng.

## SQL
```sql
SELECT
    SUM(t.amount) FILTER (
        WHERE t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
    ) AS this_month,
    SUM(t.amount) FILTER (
        WHERE t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
          AND t.transaction_time < DATE_TRUNC('month', CURRENT_DATE)
    ) AS last_month
FROM transactions t
JOIN transaction_categories tc ON t.category_id = tc.category_id
WHERE t.cif_no = 'CIF000033'
  AND t.direction = 'OUT'
  AND t.status = 'SUCCESS'
  AND tc.category_code IN ('FOOD', 'GROCERIES')
  AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month';
```

## Explanation
JOIN transaction_categories filter 2 category codes. FILTER clause tách tháng này vs tháng trước trong cùng 1 query. Kết quả: 1 row với 2 cột so sánh.
