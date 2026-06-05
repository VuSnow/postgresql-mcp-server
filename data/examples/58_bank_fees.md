# Giao dịch phí ngân hàng (FEE)

## Complexity: medium

## Tables Used: transactions, transaction_categories

## Question (Vietnamese)
Tổng phí ngân hàng khách hàng CIF000020 đã bị trừ trong quý này là bao nhiêu? Liệt kê từng khoản phí.

## Join Logic
- Cần `transactions` để lấy giao dịch phí.
- Cần `transaction_categories` để confirm category_group = 'FEE' và lấy tên danh mục cụ thể.
- **JOIN path**: `transactions.category_id = transaction_categories.category_id`
- Có thể filter bằng transaction_type = 'FEE' hoặc qua category_group.

## SQL
```sql
SELECT
    t.transaction_time,
    t.amount,
    tc.category_name,
    t.description,
    t.status
FROM transactions t
JOIN transaction_categories tc ON t.category_id = tc.category_id
WHERE t.cif_no = 'CIF000020'
  AND tc.category_group = 'FEE'
  AND t.transaction_time >= DATE_TRUNC('quarter', CURRENT_DATE)
  AND t.status = 'SUCCESS'
ORDER BY t.transaction_time DESC;
```

## Explanation
JOIN transaction_categories để filter theo category_group = 'FEE'. Dùng INNER JOIN (không LEFT JOIN) vì cần category match. Lấy toàn bộ quý hiện tại.
