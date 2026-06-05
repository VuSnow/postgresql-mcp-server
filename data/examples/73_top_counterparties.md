# Đối tác nhận chuyển khoản nhiều nhất (counterparty analysis)

## Complexity: complex

## Tables Used: transactions, beneficiaries

## Question (Vietnamese)
Top 5 người nhận tiền chuyển khoản nhiều nhất từ khách hàng CIF000025, kèm tổng số tiền.

## Join Logic
- Cần `transactions` để lấy giao dịch chuyển khoản (BANK_TRANSFER + direction OUT).
- Cần `beneficiaries` để lấy tên người nhận.
- **JOIN path**: `transactions.beneficiary_id = beneficiaries.beneficiary_id`
- GROUP BY beneficiary_id, tên người nhận.

## SQL
```sql
SELECT
    b.beneficiary_name,
    b.bank_name,
    b.account_no AS recipient_account,
    COUNT(*) AS transfer_count,
    SUM(t.amount) AS total_transferred,
    MAX(t.transaction_time) AS last_transfer
FROM transactions t
JOIN beneficiaries b ON t.beneficiary_id = b.beneficiary_id
WHERE t.cif_no = 'CIF000025'
  AND t.transaction_type = 'BANK_TRANSFER'
  AND t.direction = 'OUT'
  AND t.status = 'SUCCESS'
GROUP BY b.beneficiary_id, b.beneficiary_name, b.bank_name, b.account_no
ORDER BY total_transferred DESC
LIMIT 5;
```

## Explanation
JOIN beneficiaries để lấy tên người nhận. GROUP BY beneficiary → đếm và sum. ORDER BY total DESC → top 5 người nhận nhiều nhất.
