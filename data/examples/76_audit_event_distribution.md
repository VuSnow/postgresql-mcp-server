# Audit logs theo event_type phân bổ

## Complexity: medium

## Tables Used: audit_logs

## Question (Vietnamese)
Phân bổ audit logs theo event_type trong 7 ngày gần đây. Loại event nào xảy ra nhiều nhất?

## Join Logic
- Chỉ cần bảng `audit_logs`.
- GROUP BY event_type, đếm và sắp xếp.

## SQL
```sql
SELECT
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT action_id) AS unique_actions,
    COUNT(DISTINCT cif_no) AS unique_customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_total
FROM audit_logs
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY event_type
ORDER BY event_count DESC;
```

## Explanation
GROUP BY event_type. COUNT DISTINCT action_id cho biết bao nhiêu action tạo event đó. Window function tính %. Use case: hiểu workflow pattern hệ thống.
