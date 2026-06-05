# Thời gian trung bình hoàn tất action (từ tạo đến execute)

## Complexity: complex

## Tables Used: action_requests

## Question (Vietnamese)
Thời gian trung bình từ lúc tạo action request đến lúc execute thành công, phân theo loại action.

## Join Logic
- Chỉ cần bảng `action_requests` — có cả created_at và updated_at.
- Filter status = 'EXECUTED' để chỉ tính action thành công.
- Tính khoảng cách thời gian = updated_at - created_at.
- GROUP BY action_type.

## SQL
```sql
SELECT
    action_type,
    COUNT(*) AS executed_count,
    ROUND(AVG(EXTRACT(EPOCH FROM (updated_at - created_at)))) AS avg_seconds,
    ROUND(MIN(EXTRACT(EPOCH FROM (updated_at - created_at)))) AS min_seconds,
    ROUND(MAX(EXTRACT(EPOCH FROM (updated_at - created_at)))) AS max_seconds
FROM action_requests
WHERE status = 'EXECUTED'
  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY action_type
ORDER BY avg_seconds DESC;
```

## Explanation
EXTRACT(EPOCH FROM interval) chuyển khoảng thời gian thành giây. AVG tính thời gian trung bình hoàn tất mỗi loại action. Use case: monitoring performance workflow.
