# Audit logs theo actor — ai thực hiện nhiều nhất

## Complexity: medium

## Tables Used: audit_logs

## Question (Vietnamese)
Thống kê actor (người thực hiện) trong audit logs. Hệ thống (SYSTEM) hay user thực hiện nhiều hơn?

## Join Logic
- Chỉ cần bảng `audit_logs`.
- GROUP BY actor.

## SQL
```sql
SELECT
    actor,
    COUNT(*) AS action_count,
    COUNT(DISTINCT action_id) AS unique_actions,
    COUNT(DISTINCT cif_no) AS affected_customers,
    MIN(created_at) AS first_activity,
    MAX(created_at) AS last_activity
FROM audit_logs
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY actor
ORDER BY action_count DESC
LIMIT 20;
```

## Explanation
GROUP BY actor. Actors thường là: 'SYSTEM', 'CUSTOMER', 'ADMIN', hoặc user_id cụ thể. COUNT DISTINCT action_id cho biết số action unique. Use case: monitoring ai đang tác động hệ thống nhiều nhất.
