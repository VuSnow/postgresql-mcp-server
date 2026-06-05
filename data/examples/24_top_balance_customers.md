# Số dư tổng hợp theo khách hàng (tất cả tài khoản)

## Complexity: medium

## Tables Used: customers, accounts

## Question (Vietnamese)
Cho tôi 20 khách hàng có tổng số dư (cộng tất cả tài khoản) lớn nhất.

## Join Logic
- Cần `accounts` để lấy balance từng tài khoản.
- Cần `customers` để lấy `full_name`.
- **JOIN path**: `customers.cif_no = accounts.cif_no`
- GROUP BY khách hàng rồi SUM(balance).

## SQL
```sql
SELECT
    c.cif_no,
    c.full_name,
    c.kyc_level,
    COUNT(a.account_id) AS account_count,
    SUM(a.balance) AS total_balance,
    SUM(a.available_balance) AS total_available
FROM customers c
JOIN accounts a ON c.cif_no = a.cif_no
WHERE c.status = 'ACTIVE'
  AND a.status = 'ACTIVE'
GROUP BY c.cif_no, c.full_name, c.kyc_level
ORDER BY total_balance DESC
LIMIT 20;
```

## Explanation
JOIN customers với accounts, GROUP BY khách hàng. SUM(balance) cộng TẤT CẢ tài khoản. Filter cả 2 bảng theo status = ACTIVE.
