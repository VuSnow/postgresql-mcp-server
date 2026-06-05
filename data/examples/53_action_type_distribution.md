# Action requests theo loại hành động (distribution)

## Complexity: simple

## Tables Used: action_requests

## Question (Vietnamese)
Thống kê số lượng yêu cầu hành động theo loại (TRANSFER, BILL_PAYMENT, CARD_LOCK...) trong tháng này.

## Join Logic
- Chỉ cần bảng `action_requests`.
- GROUP BY action_type để đếm theo loại.
- Không cần JOIN.

## SQL
```sql
SELECT
    action_type,
    COUNT(*) AS request_count,
    COUNT(*) FILTER (WHERE status = 'EXECUTED') AS executed_count,
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_count,
    COUNT(*) FILTER (WHERE status = 'BLOCKED') AS blocked_count
FROM action_requests
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY action_type
ORDER BY request_count DESC;
```

## Explanation
Aggregation trên 1 bảng. FILTER clause tách count theo status cho mỗi action_type. Không cần LIMIT vì action_type chỉ có ~6 giá trị.
