# Tài khoản frozen — danh sách và số dư

## Complexity: medium

## Tables Used: accounts, customers

## Question (Vietnamese)
Liệt kê tất cả tài khoản bị đóng băng (FROZEN), kèm tên chủ tài khoản và số dư bị giữ.

## Join Logic
- Cần `accounts` để filter status = 'FROZEN' và lấy balance.
- Cần `customers` để lấy tên KH.
- **JOIN path**: `accounts.cif_no = customers.cif_no`

## SQL
```sql
SELECT
    a.account_no,
    a.account_type,
    c.full_name,
    c.cif_no,
    a.balance,
    a.available_balance,
    a.opened_at
FROM accounts a
JOIN customers c ON a.cif_no = c.cif_no
WHERE a.status = 'FROZEN'
ORDER BY a.balance DESC
LIMIT 100;
```

## Explanation
JOIN accounts với customers để lấy tên. Filter status = 'FROZEN'. Sắp xếp theo balance DESC → TK bị freeze nhiều tiền nhất lên trước.
