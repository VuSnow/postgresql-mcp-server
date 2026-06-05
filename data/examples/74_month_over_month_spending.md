# So sánh chi tiêu tháng này vs tháng trước

## Complexity: complex

## Tables Used: transactions

## Question (Vietnamese)
So sánh tổng chi tiêu tháng này với tháng trước của khách hàng CIF000040. Tăng hay giảm bao nhiêu %?

## Join Logic
- Chỉ cần bảng `transactions`.
- Dùng 2 CTE: 1 cho tháng này, 1 cho tháng trước.
- CROSS JOIN để so sánh.

## SQL
```sql
WITH this_month AS (
    SELECT SUM(amount) AS total
    FROM transactions
    WHERE cif_no = 'CIF000040'
      AND direction = 'OUT'
      AND status = 'SUCCESS'
      AND transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
),
last_month AS (
    SELECT SUM(amount) AS total
    FROM transactions
    WHERE cif_no = 'CIF000040'
      AND direction = 'OUT'
      AND status = 'SUCCESS'
      AND transaction_time >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
      AND transaction_time < DATE_TRUNC('month', CURRENT_DATE)
)
SELECT
    lm.total AS last_month_spending,
    tm.total AS this_month_spending,
    tm.total - lm.total AS difference,
    CASE
        WHEN lm.total > 0
        THEN ROUND((tm.total - lm.total) * 100.0 / lm.total, 1)
        ELSE NULL
    END AS pct_change
FROM this_month tm
CROSS JOIN last_month lm;
```

## Explanation
2 CTE tính chi tiêu 2 tháng riêng biệt. CROSS JOIN kết hợp (mỗi CTE 1 row). CASE WHEN tránh chia 0. pct_change > 0 = tăng, < 0 = giảm.
