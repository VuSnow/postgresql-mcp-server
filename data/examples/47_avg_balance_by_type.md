# Số dư trung bình theo loại tài khoản

## Complexity: simple

## Tables Used: accounts

## Question (Vietnamese)
Số dư trung bình theo từng loại tài khoản (PAYMENT, SAVINGS, CREDIT_CARD_SETTLEMENT) trong hệ thống?

## Join Logic
- Chỉ cần bảng `accounts`.
- GROUP BY account_type để aggregate theo loại.

## SQL
```sql
SELECT
    account_type,
    COUNT(*) AS account_count,
    ROUND(AVG(balance)) AS avg_balance,
    MIN(balance) AS min_balance,
    MAX(balance) AS max_balance,
    SUM(balance) AS total_balance
FROM accounts
WHERE status = 'ACTIVE'
GROUP BY account_type
ORDER BY avg_balance DESC;
```

## Explanation
Aggregation đơn giản, GROUP BY account_type. Filter status ACTIVE. Không cần LIMIT vì chỉ có 3 loại TK.
