# API calls thất bại — debug

## Complexity: medium

## Tables Used: api_call_logs, action_requests

## Question (Vietnamese)
Liệt kê các API call thất bại trong 7 ngày gần đây, kèm tên API, HTTP status và action_type tương ứng.

## Join Logic
- Cần `api_call_logs` để filter status = 'FAILED'.
- Cần `action_requests` để lấy context (action_type, cif_no).
- **JOIN path**: `api_call_logs.action_id = action_requests.action_id`

## SQL
```sql
SELECT
    acl.created_at,
    acl.api_name,
    acl.http_status,
    acl.status,
    ar.action_type,
    ar.cif_no,
    acl.request_payload,
    acl.response_payload
FROM api_call_logs acl
JOIN action_requests ar ON acl.action_id = ar.action_id
WHERE acl.status = 'FAILED'
  AND acl.created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY acl.created_at DESC
LIMIT 50;
```

## Explanation
JOIN api_call_logs với action_requests để lấy context. Filter status = 'FAILED'. Bao gồm request/response payload để debug nguyên nhân lỗi.
