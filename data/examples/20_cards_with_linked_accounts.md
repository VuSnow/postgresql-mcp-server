# Danh sách thẻ kèm tài khoản liên kết

## Complexity: medium

## Tables Used: cards, accounts

## Question (Vietnamese)
Liệt kê tất cả thẻ của khách hàng CIF000050, bao gồm số tài khoản liên kết và số dư tài khoản đó.

## Join Logic
- Cần `cards` để lấy thông tin thẻ (masked_card_no, card_type, status).
- Cần `accounts` để lấy số dư tài khoản liên kết — cards lưu account_no nhưng không lưu balance.
- **JOIN path**: `cards.account_no = accounts.account_no`

## SQL
```sql
SELECT
    ca.masked_card_no,
    ca.card_type,
    ca.card_network,
    ca.status AS card_status,
    a.account_no,
    a.account_type,
    a.balance,
    a.available_balance,
    ca.issued_at
FROM cards ca
JOIN accounts a ON ca.account_no = a.account_no
WHERE ca.cif_no = 'CIF000050'
ORDER BY ca.card_type, ca.issued_at DESC;
```

## Explanation
JOIN cards với accounts qua account_no. Mỗi thẻ liên kết đúng 1 tài khoản nên INNER JOIN an toàn (không duplicate). Không cần LIMIT vì mỗi KH thường có 2-4 thẻ.
