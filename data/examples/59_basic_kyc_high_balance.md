# Khách hàng KYC level BASIC — chưa nâng cấp

## Complexity: medium

## Tables Used: customers, accounts

## Question (Vietnamese)
Danh sách khách hàng có KYC level BASIC nhưng có số dư tổng trên 100 triệu (có thể cần nâng KYC).

## Join Logic
- Cần `customers` để filter kyc_level = 'BASIC'.
- Cần `accounts` để tính tổng balance.
- **JOIN path**: `customers.cif_no = accounts.cif_no`
- GROUP BY khách hàng, HAVING SUM(balance) > threshold.

## SQL
```sql
SELECT
    c.cif_no,
    c.full_name,
    c.kyc_level,
    c.phone_number,
    SUM(a.balance) AS total_balance
FROM customers c
JOIN accounts a ON c.cif_no = a.cif_no
WHERE c.status = 'ACTIVE'
  AND c.kyc_level = 'BASIC'
  AND a.status = 'ACTIVE'
GROUP BY c.cif_no, c.full_name, c.kyc_level, c.phone_number
HAVING SUM(a.balance) > 100000000
ORDER BY total_balance DESC
LIMIT 50;
```

## Explanation
JOIN customers với accounts. HAVING clause filter sau GROUP BY: chỉ giữ KH có tổng balance > 100M VND. Use case: campaign nâng cấp KYC cho KH tiềm năng.
