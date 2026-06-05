# Khách hàng mở nhiều tài khoản trong thời gian ngắn

## Complexity: complex

## Tables Used: customers, accounts

## Question (Vietnamese)
Tìm khách hàng đã mở 3 tài khoản trở lên trong 90 ngày gần đây.

## Join Logic
- Cần `accounts` để đếm TK mở gần đây (opened_at).
- Cần `customers` để lấy tên KH.
- **JOIN path**: `accounts.cif_no = customers.cif_no`
- GROUP BY khách hàng, HAVING COUNT >= 3.

## SQL
```sql
SELECT
    c.cif_no,
    c.full_name,
    c.status,
    COUNT(a.account_id) AS accounts_opened,
    MIN(a.opened_at) AS first_opened,
    MAX(a.opened_at) AS last_opened
FROM accounts a
JOIN customers c ON a.cif_no = c.cif_no
WHERE a.opened_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY c.cif_no, c.full_name, c.status
HAVING COUNT(a.account_id) >= 3
ORDER BY accounts_opened DESC
LIMIT 50;
```

## Explanation
GROUP BY khách hàng + HAVING COUNT >= 3. Use case: phát hiện hành vi bất thường (mở nhiều TK nhanh có thể là fraud indicator).
