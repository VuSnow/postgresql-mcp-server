# Action requests cần OTP nhưng chưa verify

## Complexity: medium

## Tables Used: action_requests, customers

## Question (Vietnamese)
Liệt kê các action requests đang chờ OTP (PENDING_OTP) quá 10 phút, kèm tên khách hàng.

## Join Logic
- Cần `action_requests` để filter status = 'PENDING_OTP' và thời gian.
- Cần `customers` để lấy tên.
- **JOIN path**: `action_requests.cif_no = customers.cif_no`

## SQL
```sql
SELECT
    ar.action_id,
    c.full_name,
    ar.action_type,
    ar.risk_tier,
    ar.user_text,
    ar.updated_at,
    EXTRACT(EPOCH FROM (NOW() - ar.updated_at)) / 60 AS minutes_waiting
FROM action_requests ar
JOIN customers c ON ar.cif_no = c.cif_no
WHERE ar.status = 'PENDING_OTP'
  AND ar.updated_at < NOW() - INTERVAL '10 minutes'
ORDER BY ar.updated_at ASC
LIMIT 50;
```

## Explanation
Filter PENDING_OTP + updated_at quá 10 phút. Tính minutes_waiting = (NOW() - updated_at) / 60. Use case: monitoring stuck actions, có thể cần timeout.
