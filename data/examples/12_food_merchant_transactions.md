# Giao dịch tại merchant danh mục FOOD

## Complexity: medium

## Tables Used: transactions, merchants

## Question (Vietnamese)
Tìm tất cả giao dịch tại các merchant thuộc danh mục FOOD của khách hàng CIF000007 trong 30 ngày gần đây.

## Join Logic
- Cần `transactions` để lấy dữ liệu giao dịch.
- Cần `merchants` để filter theo `merchant_category = 'FOOD'` — thông tin danh mục nằm ở bảng merchants.
- **JOIN path**: `transactions.merchant_id = merchants.merchant_id`
- Dùng INNER JOIN vì chỉ muốn giao dịch có merchant (tức CARD_PAYMENT).

## SQL
```sql
SELECT
    t.transaction_time,
    m.merchant_name,
    m.city,
    t.amount,
    t.channel,
    t.status
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.cif_no = 'CIF000007'
  AND m.merchant_category = 'FOOD'
  AND t.transaction_time >= CURRENT_DATE - INTERVAL '30 days'
  AND t.status = 'SUCCESS'
ORDER BY t.transaction_time DESC
LIMIT 50;
```

## Explanation
INNER JOIN transactions với merchants. Filter merchant_category = 'FOOD' trên bảng merchants. Khi dùng INNER JOIN trên merchant_id, các giao dịch không phải CARD_PAYMENT (merchant_id = NULL) tự động bị loại.
