# Thẻ hết hạn cần đổi

## Complexity: simple

## Tables Used: cards

## Question (Vietnamese)
Liệt kê các thẻ đã hết hạn (EXPIRED) chưa được thay thế, kèm thông tin KH.

## Join Logic
- Chỉ cần bảng `cards` — status = 'EXPIRED' đã có sẵn.
- Không cần JOIN customers vì cif_no đủ để identify.

## SQL
```sql
SELECT
    cif_no,
    masked_card_no,
    card_type,
    card_network,
    issued_at,
    status
FROM cards
WHERE status = 'EXPIRED'
ORDER BY issued_at ASC
LIMIT 100;
```

## Explanation
Query đơn giản. Filter status = 'EXPIRED'. Sắp xếp theo issued_at ASC → thẻ cũ nhất (hết hạn lâu nhất) lên trước.
