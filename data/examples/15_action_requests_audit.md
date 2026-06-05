# Audit trail của action requests

## Complexity: complex

## Tables Used: action_requests, api_call_logs

## Question (Vietnamese)
Cho tôi lịch sử các yêu cầu hành động của khách hàng CIF000030 kèm kết quả API call tương ứng.

## Join Logic
- Cần `action_requests` lưu các yêu cầu từ agent (chuyển tiền, khóa thẻ, thanh toán).
- Cần `api_call_logs` để xem kết quả thực thi API (thành công hay thất bại, HTTP status).
- **JOIN path**: `action_requests.action_id = api_call_logs.action_id`
- LEFT JOIN cho api_call_logs vì action bị reject trước khi gọi API sẽ không có log.

## SQL
```sql
SELECT
    ar.action_type,
    ar.status AS action_status,
    ar.risk_tier,
    ar.user_text,
    ar.created_at AS requested_at,
    acl.api_name,
    acl.http_status,
    acl.status AS api_status,
    acl.created_at AS api_called_at
FROM action_requests ar
LEFT JOIN api_call_logs acl ON ar.action_id = acl.action_id
WHERE ar.cif_no = 'CIF000030'
ORDER BY ar.created_at DESC
LIMIT 50;
```

## Explanation
LEFT JOIN action_requests với api_call_logs. LEFT JOIN vì action có thể bị reject (không gọi API). 1 action có thể có nhiều API calls (retry) → kết quả có thể có nhiều dòng cho cùng 1 action.
