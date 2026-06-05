# Phân tích chi tiêu theo merchant category

## Complexity: complex

## Tables Used: transactions, merchants

## Question (Vietnamese)
Phân tích chi tiêu thẻ của khách hàng CIF000005 theo danh mục merchant trong 3 tháng gần đây. Cho biết tổng tiền và số lượng giao dịch mỗi danh mục.

## Join Logic
- Cần `transactions` để lấy dữ liệu giao dịch (amount, time, type).
- Cần `merchants` để lấy `merchant_category` — thông tin phân loại merchant nằm ở bảng riêng, không nằm trong transactions.
- **JOIN path**: `transactions.merchant_id = merchants.merchant_id`
- Dùng **INNER JOIN** vì đã filter `transaction_type = 'CARD_PAYMENT'` — chỉ giao dịch thẻ mới có merchant_id.
- Filter `direction = 'OUT'` vì chi tiêu = tiền ra.
- GROUP BY merchant_category để aggregate theo danh mục.

## SQL
```sql
SELECT
    m.merchant_category,
    COUNT(*) AS transaction_count,
    SUM(t.amount) AS total_spent,
    AVG(t.amount) AS avg_per_transaction
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.cif_no = 'CIF000005'
  AND t.transaction_type = 'CARD_PAYMENT'
  AND t.direction = 'OUT'
  AND t.status = 'SUCCESS'
  AND t.transaction_time >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY m.merchant_category
ORDER BY total_spent DESC;
```

## Explanation
JOIN transactions với merchants để lấy merchant_category. Filter transaction_type = CARD_PAYMENT đảm bảo merchant_id NOT NULL. GROUP BY merchant_category rồi tính COUNT, SUM, AVG. Sắp xếp theo tổng chi tiêu giảm dần. Không cần LIMIT vì số danh mục merchant hữu hạn (~8 loại).
