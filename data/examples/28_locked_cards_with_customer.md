# Khách hàng có thẻ bị khóa

## Complexity: complex

## Tables Used: customers, cards, accounts

## Question (Vietnamese)
Tìm khách hàng ACTIVE có thẻ bị khóa (LOCKED), liệt kê thông tin thẻ và tài khoản liên kết.

## Join Logic
- Cần `customers` để filter KH ACTIVE và lấy tên.
- Cần `cards` để tìm thẻ LOCKED.
- Cần `accounts` để lấy thông tin TK liên kết.
- **JOIN path 1**: `customers.cif_no = cards.cif_no`
- **JOIN path 2**: `cards.account_no = accounts.account_no`
- INNER JOIN cho tất cả vì FK đều NOT NULL.

## SQL
```sql
SELECT
    c.cif_no,
    c.full_name,
    c.phone_number,
    ca.masked_card_no,
    ca.card_type,
    ca.card_network,
    a.account_no,
    a.account_type,
    a.balance
FROM customers c
JOIN cards ca ON c.cif_no = ca.cif_no
JOIN accounts a ON ca.account_no = a.account_no
WHERE c.status = 'ACTIVE'
  AND ca.status = 'LOCKED'
ORDER BY c.full_name, ca.card_type
LIMIT 100;
```

## Explanation
3-table chain JOIN: customers → cards → accounts. Filter customers.status = ACTIVE, cards.status = LOCKED. Use case: team support cần contact KH có thẻ bị khóa.
