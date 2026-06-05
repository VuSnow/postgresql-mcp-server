# Tỷ lệ ALLOW vs BLOCK trong fraud decisions

## Complexity: medium

## Tables Used: fraud_decisions

## Question (Vietnamese)
Thống kê tỷ lệ các quyết định screening (ALLOW, WARN, BLOCK) trong tháng này.

## Join Logic
- Chỉ cần bảng `fraud_decisions`.
- GROUP BY decision để đếm từng loại.
- Tính phần trăm bằng window function hoặc subquery.

## SQL
```sql
SELECT
    decision,
    COUNT(*) AS decision_count,
    ROUND(
        COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 1
    ) AS percentage
FROM fraud_decisions
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY decision
ORDER BY decision_count DESC;
```

## Explanation
GROUP BY decision + window function SUM(COUNT(*)) OVER () để tính phần trăm so với tổng. OVER () không có PARTITION BY → tổng toàn bộ. Không cần LIMIT vì decision chỉ có 5 giá trị.
