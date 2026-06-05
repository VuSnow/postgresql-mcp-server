# Thẻ tín dụng: hạn mức sử dụng hiện tại

## Complexity: simple

## Tables Used: cards

## Question (Vietnamese)
Liệt kê các thẻ tín dụng đang hoạt động của khách hàng CIF000012, cho biết hạn mức tín dụng, hạn mức khả dụng và phần trăm đã sử dụng.

## Join Logic
- Chỉ cần bảng `cards` vì thông tin hạn mức (credit_limit, available_limit) nằm trong bảng cards.
- Filter `card_type = 'CREDIT'` vì chỉ thẻ tín dụng mới có hạn mức.
- Tính phần trăm sử dụng bằng phép tính trên 2 cột cùng bảng.

## SQL
```sql
SELECT
    masked_card_no,
    card_network,
    credit_limit,
    available_limit,
    ROUND(
        (credit_limit - available_limit)::NUMERIC / credit_limit * 100, 1
    ) AS usage_percent
FROM cards
WHERE cif_no = 'CIF000012'
  AND card_type = 'CREDIT'
  AND status = 'ACTIVE'
  AND credit_limit > 0
ORDER BY usage_percent DESC;
```

## Explanation
Query trên 1 bảng. Tính usage_percent = (credit_limit - available_limit) / credit_limit * 100. Cast sang NUMERIC để tránh integer division. Thêm credit_limit > 0 để tránh division by zero.
