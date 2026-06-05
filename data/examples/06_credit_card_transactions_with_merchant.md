# Giao dịch thẻ tín dụng kèm thông tin thẻ và merchant

## Complexity: complex

## Tables Used: transactions, cards, merchants

## Question (Vietnamese)
Liệt kê các giao dịch thẻ tín dụng của khách hàng CIF000020 trong tháng này, bao gồm số thẻ (masked), tên merchant và số tiền.

## Join Logic
- Cần `transactions` là bảng chính chứa lịch sử giao dịch.
- Cần `cards` để lấy `masked_card_no` và filter `card_type = 'CREDIT'` — transactions chỉ chứa card_id (UUID).
- Cần `merchants` để lấy `merchant_name` — transactions chỉ chứa merchant_id.
- **JOIN path 1**: `transactions.card_id = cards.card_id` — liên kết giao dịch với thẻ.
- **JOIN path 2**: `transactions.merchant_id = merchants.merchant_id` — liên kết giao dịch với merchant.
- Dùng INNER JOIN cho cards vì đã filter transaction_type = 'CARD_PAYMENT' (card_id NOT NULL).
- Dùng LEFT JOIN cho merchants vì có thể merchant_id NULL trong một số trường hợp hiếm.

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    ca.masked_card_no,
    ca.card_network,
    m.merchant_name,
    m.merchant_category,
    t.amount,
    t.status
FROM transactions t
JOIN cards ca ON t.card_id = ca.card_id
LEFT JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.cif_no = 'CIF000020'
  AND t.transaction_type = 'CARD_PAYMENT'
  AND ca.card_type = 'CREDIT'
  AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
ORDER BY t.transaction_time DESC
LIMIT 100;
```

## Explanation
3-table JOIN: transactions → cards (lấy info thẻ) → merchants (lấy tên merchant). Filter card_type = 'CREDIT' trên bảng cards (không phải transactions) vì transactions không chứa thông tin loại thẻ. DATE_TRUNC('month', CURRENT_DATE) lấy đầu tháng hiện tại.
