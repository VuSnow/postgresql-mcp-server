# Card payment tại merchant theo danh mục (ENTERTAINMENT)

## Complexity: medium

## Tables Used: transactions, merchants

## Question (Vietnamese)
Liệt kê giao dịch thẻ tại merchant thuộc danh mục ENTERTAINMENT của khách hàng CIF000077 trong 3 tháng.

## Join Logic
- Cần `transactions` để lấy giao dịch CARD_PAYMENT.
- Cần `merchants` để filter merchant_category = 'ENTERTAINMENT'.
- **JOIN path**: `transactions.merchant_id = merchants.merchant_id`

## SQL
```sql
SELECT
    t.transaction_time,
    m.merchant_name,
    m.city,
    t.amount,
    t.description,
    t.channel
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.cif_no = 'CIF000077'
  AND t.transaction_type = 'CARD_PAYMENT'
  AND m.merchant_category = 'ENTERTAINMENT'
  AND t.status = 'SUCCESS'
  AND t.transaction_time >= CURRENT_DATE - INTERVAL '3 months'
ORDER BY t.transaction_time DESC
LIMIT 50;
```

## Explanation
JOIN merchants filter theo merchant_category. CARD_PAYMENT là transaction_type cho thanh toán thẻ. Use case: phân tích chi tiêu giải trí.
