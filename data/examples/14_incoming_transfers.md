# Giao dịch nhận tiền (lương, chuyển khoản đến)

## Complexity: medium

## Tables Used: transactions, accounts

## Question (Vietnamese)
Liệt kê các khoản tiền nhận vào tài khoản thanh toán của khách hàng CIF000003 trong tháng này.

## Join Logic
- Cần `transactions` để lấy lịch sử giao dịch chiều IN (nhận tiền).
- Cần `accounts` để filter chỉ tài khoản thanh toán (PAYMENT) — vì KH có thể có nhiều loại TK.
- **JOIN path**: `transactions.account_no = accounts.account_no`
- Filter `direction = 'IN'`: chỉ giao dịch nhận tiền.
- Filter `accounts.account_type = 'PAYMENT'`: chỉ TK thanh toán.

## SQL
```sql
SELECT
    t.transaction_time,
    t.transaction_type,
    t.amount,
    t.counterparty_name,
    t.counterparty_bank_code,
    t.description,
    a.account_no
FROM transactions t
JOIN accounts a ON t.account_no = a.account_no
WHERE t.cif_no = 'CIF000003'
  AND t.direction = 'IN'
  AND a.account_type = 'PAYMENT'
  AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
  AND t.status = 'SUCCESS'
ORDER BY t.transaction_time DESC
LIMIT 100;
```

## Explanation
JOIN transactions với accounts để filter theo loại tài khoản. Nếu không JOIN accounts, sẽ lấy cả giao dịch vào TK tiết kiệm hoặc settlement.
