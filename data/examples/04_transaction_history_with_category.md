# Lịch sử giao dịch gần đây kèm danh mục

## Complexity: medium

## Tables Used: transactions, transaction_categories

## Question (Vietnamese)
Cho tôi xem 20 giao dịch gần nhất của khách hàng CIF000010, bao gồm tên danh mục giao dịch.

## Join Logic
- Cần `transactions` để lấy lịch sử giao dịch (amount, time, type, status).
- Cần `transaction_categories` để hiển thị tên danh mục thay vì chỉ category_id (UUID không có ý nghĩa với user).
- **JOIN path**: `transactions.category_id = transaction_categories.category_id`
- Dùng **LEFT JOIN** vì `category_id` có thể NULL (không phải giao dịch nào cũng được phân loại).
- Filter theo `cif_no` để lấy giao dịch của đúng khách hàng.

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    t.amount,
    t.direction,
    t.transaction_type,
    tc.category_name,
    t.description,
    t.status
FROM transactions t
LEFT JOIN transaction_categories tc ON t.category_id = tc.category_id
WHERE t.cif_no = 'CIF000010'
ORDER BY t.transaction_time DESC
LIMIT 20;
```

## Explanation
LEFT JOIN với transaction_categories để lấy tên danh mục. Dùng LEFT JOIN (không phải INNER JOIN) vì category_id nullable — nếu dùng INNER JOIN sẽ mất các giao dịch chưa phân loại. Sắp xếp theo thời gian mới nhất và giới hạn 20 bản ghi.
