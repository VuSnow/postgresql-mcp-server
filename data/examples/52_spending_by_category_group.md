# Phân tích chi tiêu theo category_group

## Complexity: medium

## Tables Used: transactions, transaction_categories

## Question (Vietnamese)
Phân tích chi tiêu tháng này của khách hàng CIF000015 theo nhóm danh mục (SPENDING, TRANSFER, BILL, FEE).

## Join Logic
- Cần `transactions` để lấy dữ liệu giao dịch.
- Cần `transaction_categories` để lấy `category_group` — nhóm lớn của danh mục.
- **JOIN path**: `transactions.category_id = transaction_categories.category_id`
- LEFT JOIN vì category_id có thể NULL.
- GROUP BY category_group để aggregate theo nhóm.

## SQL
```sql
SELECT
    COALESCE(tc.category_group, 'UNKNOWN') AS category_group,
    COUNT(*) AS transaction_count,
    SUM(t.amount) AS total_amount,
    ROUND(AVG(t.amount)) AS avg_amount
FROM transactions t
LEFT JOIN transaction_categories tc ON t.category_id = tc.category_id
WHERE t.cif_no = 'CIF000015'
  AND t.direction = 'OUT'
  AND t.status = 'SUCCESS'
  AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY tc.category_group
ORDER BY total_amount DESC;
```

## Explanation
LEFT JOIN transaction_categories để GROUP BY category_group. COALESCE xử lý trường hợp category_id NULL → nhóm vào 'UNKNOWN'. Chỉ tính chi tiêu (direction = 'OUT').
