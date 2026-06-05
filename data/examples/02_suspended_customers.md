# Khách hàng bị tạm khóa

## Complexity: simple

## Tables Used: customers

## Question (Vietnamese)
Có bao nhiêu khách hàng đang bị tạm khóa (SUSPENDED)?

## Join Logic
- Chỉ cần bảng `customers` vì trạng thái KH nằm ở cột `status`.
- Không cần JOIN — câu hỏi đơn thuần đếm trên 1 bảng.

## SQL
```sql
SELECT
    COUNT(*) AS suspended_count
FROM customers
WHERE status = 'SUSPENDED';
```

## Explanation
Aggregation COUNT trên 1 bảng với 1 điều kiện WHERE. Kết quả là 1 row duy nhất nên không cần LIMIT.
