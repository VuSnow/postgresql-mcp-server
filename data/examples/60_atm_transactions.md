# Giao dịch ATM (rút/nạp tiền mặt)

## Complexity: simple

## Tables Used: transactions

## Question (Vietnamese)
Liệt kê giao dịch ATM (rút và nạp tiền mặt) của khách hàng CIF000030 trong tháng này.

## Join Logic
- Chỉ cần bảng `transactions`.
- Filter transaction_type IN ('CASH_WITHDRAWAL', 'CASH_DEPOSIT') hoặc channel = 'ATM'.

## SQL
```sql
SELECT
    transaction_time,
    transaction_type,
    amount,
    direction,
    balance_after,
    status
FROM transactions
WHERE cif_no = 'CIF000030'
  AND transaction_type IN ('CASH_WITHDRAWAL', 'CASH_DEPOSIT')
  AND transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
ORDER BY transaction_time DESC
LIMIT 50;
```

## Explanation
Filter bằng IN clause cho 2 loại giao dịch ATM. balance_after cho biết số dư sau giao dịch.
