# Fraud reports theo thời gian (trend weekly)

## Complexity: complex

## Tables Used: fraud_reports

## Question (Vietnamese)
Xu hướng báo cáo gian lận theo tuần trong 3 tháng gần đây. Tuần nào nhiều nhất?

## Join Logic
- Chỉ cần bảng `fraud_reports`.
- GROUP BY tuần (DATE_TRUNC('week')).
- Window function để so sánh vs tuần trước (LAG).

## SQL
```sql
WITH weekly_reports AS (
    SELECT
        DATE_TRUNC('week', reported_at) AS week_start,
        COUNT(*) AS report_count,
        COUNT(DISTINCT reporter_cif) AS unique_reporters,
        COUNT(*) FILTER (WHERE fraud_type = 'SCAM') AS scam_count,
        COUNT(*) FILTER (WHERE fraud_type = 'UNAUTHORIZED_TXN') AS unauthorized_count
    FROM fraud_reports
    WHERE reported_at >= CURRENT_DATE - INTERVAL '3 months'
    GROUP BY DATE_TRUNC('week', reported_at)
)
SELECT
    week_start,
    report_count,
    unique_reporters,
    scam_count,
    unauthorized_count,
    report_count - LAG(report_count) OVER (ORDER BY week_start) AS diff_vs_last_week
FROM weekly_reports
ORDER BY week_start DESC;
```

## Explanation
CTE GROUP BY tuần. LAG() lấy giá trị tuần trước → tính diff. FILTER clause phân loại fraud_type. Use case: phát hiện spike gian lận.
