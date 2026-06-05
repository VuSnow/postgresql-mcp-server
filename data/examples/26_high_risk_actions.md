# Action requests có rủi ro cao

## Complexity: complex

## Tables Used: action_requests, customers, audit_logs

## Question (Vietnamese)
Liệt kê các yêu cầu hành động có risk_tier = RED hoặc ORANGE trong 7 ngày gần đây, kèm tên khách hàng và audit events.

## Join Logic
- Cần `action_requests` để filter theo risk_tier.
- Cần `customers` để lấy tên khách hàng.
- Cần `audit_logs` để xem event trail.
- **JOIN path 1**: `action_requests.cif_no = customers.cif_no`
- **JOIN path 2**: `action_requests.action_id = audit_logs.action_id`
- LEFT JOIN audit_logs vì action mới tạo có thể chưa có audit entry.

## SQL
```sql
SELECT
    ar.action_id,
    ar.created_at,
    c.full_name,
    ar.action_type,
    ar.status AS action_status,
    ar.risk_tier,
    ar.risk_score,
    ar.user_text,
    al.event_type,
    al.actor,
    al.created_at AS audit_time
FROM action_requests ar
JOIN customers c ON ar.cif_no = c.cif_no
LEFT JOIN audit_logs al ON ar.action_id = al.action_id
WHERE ar.risk_tier IN ('RED', 'ORANGE')
  AND ar.created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY ar.risk_score DESC, ar.created_at DESC
LIMIT 100;
```

## Explanation
3-table JOIN. LEFT JOIN audit_logs vì action pending chưa có audit. 1 action có thể có nhiều audit events → multiple rows per action. ORDER BY risk_score DESC → rủi ro cao nhất lên đầu.
