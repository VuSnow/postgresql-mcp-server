# Thống kê fraud theo loại lừa đảo

## Complexity: medium

## Tables Used: fraud_reports

## Question (Vietnamese)
Thống kê số lượng báo cáo lừa đảo theo từng loại (fraud_type) trong 3 tháng gần đây.

## Join Logic
- Chỉ cần bảng `fraud_reports` — GROUP BY fraud_type.
- Không cần JOIN vì fraud_type nằm trong bảng fraud_reports.

## SQL
```sql
SELECT
    fraud_type,
    COUNT(*) AS report_count,
    COUNT(*) FILTER (WHERE status = 'CONFIRMED') AS confirmed_count,
    SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected_count,
    ROUND(AVG(confidence_score), 1) AS avg_confidence
FROM fraud_reports
WHERE created_at >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY fraud_type
ORDER BY report_count DESC;
```

## Explanation
Aggregation trên 1 bảng, GROUP BY fraud_type. Dùng FILTER và CASE WHEN để tách count theo status. AVG confidence cho biết mức tin cậy trung bình. Không cần LIMIT vì fraud_type chỉ có ~5 giá trị.
