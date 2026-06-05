# Báo cáo fraud theo kênh liên lạc và hậu quả

## Complexity: medium

## Tables Used: fraud_reports

## Question (Vietnamese)
Thống kê số báo cáo lừa đảo theo kênh liên lạc (contact_channel) và hậu quả (aftermath).

## Join Logic
- Chỉ cần bảng `fraud_reports`.
- GROUP BY contact_channel, aftermath để cross-tabulate.

## SQL
```sql
SELECT
    contact_channel,
    aftermath,
    COUNT(*) AS report_count,
    SUM(CASE WHEN status = 'CONFIRMED' THEN 1 ELSE 0 END) AS confirmed_count,
    ROUND(AVG(confidence_score), 1) AS avg_confidence
FROM fraud_reports
WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY contact_channel, aftermath
ORDER BY report_count DESC
LIMIT 50;
```

## Explanation
Cross-tabulation: GROUP BY 2 cột để phân tích pattern (kênh nào + hậu quả nào phổ biến nhất). CASE WHEN đếm confirmed reports trong nhóm.
