# Card UNLOCK requests — thống kê

## Complexity: medium

## Tables Used: action_requests

## Question (Vietnamese)
Có bao nhiêu yêu cầu mở khóa thẻ (CARD_UNLOCK) trong 30 ngày? Bao nhiêu thành công, bao nhiêu thất bại?

## Join Logic
- Chỉ cần bảng `action_requests`.
- Filter action_type = 'CARD_UNLOCK'.
- GROUP BY status.

## SQL
```sql
SELECT
    status,
    COUNT(*) AS request_count,
    COUNT(DISTINCT cif_no) AS unique_customers
FROM action_requests
WHERE action_type = 'CARD_UNLOCK'
  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status
ORDER BY request_count DESC;
```

## Explanation
Aggregation đơn giản. COUNT DISTINCT cif_no cho biết bao nhiêu KH khác nhau yêu cầu unlock thẻ. Kết quả: vài rows (EXECUTED, FAILED, BLOCKED, PENDING_OTP...).
