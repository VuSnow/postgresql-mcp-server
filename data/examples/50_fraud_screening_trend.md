# Tổng hợp fraud screening theo tháng (trend)

## Complexity: complex

## Tables Used: fraud_decisions

## Question (Vietnamese)
Cho tôi xu hướng fraud screening theo tháng trong 6 tháng gần đây: bao nhiêu ALLOW, WARN, BLOCK mỗi tháng?

## Join Logic
- Chỉ cần bảng `fraud_decisions`.
- GROUP BY tháng + conditional aggregation theo decision.
- Dùng FILTER clause cho pivot.

## SQL
```sql
SELECT
    DATE_TRUNC('month', created_at) AS month,
    COUNT(*) AS total_screenings,
    COUNT(*) FILTER (WHERE decision = 'ALLOW') AS allow_count,
    COUNT(*) FILTER (WHERE decision = 'WARN') AS warn_count,
    COUNT(*) FILTER (WHERE decision = 'BLOCK') AS block_count,
    COUNT(*) FILTER (WHERE decision = 'STEP_UP_AUTH') AS step_up_count,
    ROUND(
        COUNT(*) FILTER (WHERE decision = 'BLOCK')::NUMERIC /
        NULLIF(COUNT(*), 0) * 100, 1
    ) AS block_rate_percent
FROM fraud_decisions
WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;
```

## Explanation
Time series pivot: mỗi row = 1 tháng, mỗi cột = count per decision type. block_rate_percent cho biết tỷ lệ block theo thời gian (trend tăng = fraud gia tăng). Tối đa 6 rows.
