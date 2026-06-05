# Workflow trace — audit logs cho 1 action

## Complexity: medium

## Tables Used: audit_logs, action_requests

## Question (Vietnamese)
Cho tôi trace toàn bộ workflow của action request mới nhất của khách hàng CIF000066 (từ nhận yêu cầu đến kết quả).

## Join Logic
- Cần `action_requests` để tìm action mới nhất của KH.
- Cần `audit_logs` để lấy toàn bộ event trail.
- **JOIN path**: `audit_logs.action_id = action_requests.action_id`
- Dùng subquery để lấy action_id mới nhất trước.

## SQL
```sql
SELECT
    al.event_type,
    al.actor,
    al.event_payload,
    al.created_at
FROM audit_logs al
WHERE al.action_id = (
    SELECT action_id
    FROM action_requests
    WHERE cif_no = 'CIF000066'
    ORDER BY created_at DESC
    LIMIT 1
)
ORDER BY al.created_at ASC;
```

## Explanation
Subquery lấy action_id mới nhất của KH. Rồi SELECT audit_logs theo action_id đó. ORDER BY created_at ASC để thấy sequence workflow từ đầu đến cuối. Không cần LIMIT vì mỗi action thường có 5-8 audit events.
