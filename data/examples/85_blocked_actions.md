# Action requests bị BLOCKED — phân tích risk

## Complexity: medium

## Tables Used: action_requests, customers

## Question (Vietnamese)
Liệt kê action requests bị block trong tháng này. Tại sao bị block? (risk_tier nào?)

## Join Logic
- Cần `action_requests` để filter status = 'BLOCKED'.
- Cần `customers` để lấy tên + status KH.
- **JOIN path**: `action_requests.cif_no = customers.cif_no`

## SQL
```sql
SELECT
    ar.action_id,
    c.full_name,
    c.status AS customer_status,
    ar.action_type,
    ar.risk_tier,
    ar.user_text,
    ar.created_at
FROM action_requests ar
JOIN customers c ON ar.cif_no = c.cif_no
WHERE ar.status = 'BLOCKED'
  AND ar.created_at >= DATE_TRUNC('month', CURRENT_DATE)
ORDER BY ar.created_at DESC
LIMIT 50;
```

## Explanation
Filter BLOCKED actions. risk_tier cho biết mức rủi ro đánh giá (LOW/MEDIUM/HIGH/CRITICAL). Kết hợp customer_status để xem KH có bị SUSPENDED/FROZEN không.
