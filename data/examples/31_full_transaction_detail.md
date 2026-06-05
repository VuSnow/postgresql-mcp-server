# Giao dịch kèm đầy đủ context (multi-table enrichment)

## Complexity: complex

## Tables Used: transactions, accounts, merchants, transaction_categories, beneficiaries

## Question (Vietnamese)
Cho tôi 10 giao dịch gần nhất của khách hàng CIF000001 với đầy đủ thông tin: tên danh mục, tên merchant (nếu có), tên người nhận (nếu chuyển khoản).

## Join Logic
- `transactions` là bảng trung tâm.
- `accounts` để lấy `account_type`.
- `transaction_categories` để lấy `category_name`.
- `merchants` để lấy `merchant_name` (NULL khi không phải CARD_PAYMENT).
- `beneficiaries` để lấy `beneficiary_name` (NULL khi không phải BANK_TRANSFER).
- Tất cả dùng LEFT JOIN (trừ accounts) vì FK nullable.

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    a.account_type,
    t.amount,
    t.direction,
    t.transaction_type,
    tc.category_name,
    m.merchant_name,
    COALESCE(ben.beneficiary_name, t.counterparty_name) AS receiver_name,
    t.channel,
    t.status,
    t.description
FROM transactions t
JOIN accounts a ON t.account_no = a.account_no
LEFT JOIN transaction_categories tc ON t.category_id = tc.category_id
LEFT JOIN merchants m ON t.merchant_id = m.merchant_id
LEFT JOIN beneficiaries ben ON t.beneficiary_id = ben.beneficiary_id
WHERE t.cif_no = 'CIF000001'
ORDER BY t.transaction_time DESC
LIMIT 10;
```

## Explanation
Multi-table enrichment: 1 bảng trung tâm LEFT JOIN ra nhiều bảng reference. Không bị fan-out vì mỗi FK là many-to-one. COALESCE ưu tiên beneficiary_name, fallback counterparty_name.
