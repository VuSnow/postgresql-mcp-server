# Beneficiary bất thường — mới thêm rồi chuyển tiền lớn

## Complexity: complex

## Tables Used: beneficiaries, transactions

## Question (Vietnamese)
Tìm beneficiary được thêm trong 7 ngày gần đây và đã nhận chuyển khoản > 50 triệu. (Có thể suspicious)

## Join Logic
- Cần `beneficiaries` để filter registered_at gần đây.
- Cần `transactions` để check số tiền chuyển cho beneficiary đó.
- **JOIN path**: `transactions.beneficiary_id = beneficiaries.beneficiary_id`
- GROUP BY beneficiary, HAVING SUM > threshold.

## SQL
```sql
SELECT
    b.cif_no,
    b.beneficiary_name,
    b.bank_name,
    b.account_no AS recipient_account,
    b.registered_at,
    COUNT(t.transaction_id) AS transfer_count,
    SUM(t.amount) AS total_transferred,
    MAX(t.amount) AS max_single_transfer
FROM beneficiaries b
JOIN transactions t ON b.beneficiary_id = t.beneficiary_id
WHERE b.registered_at >= CURRENT_DATE - INTERVAL '7 days'
  AND t.transaction_type = 'BANK_TRANSFER'
  AND t.direction = 'OUT'
  AND t.status = 'SUCCESS'
GROUP BY b.beneficiary_id, b.cif_no, b.beneficiary_name, b.bank_name, b.account_no, b.registered_at
HAVING SUM(t.amount) > 50000000
ORDER BY total_transferred DESC
LIMIT 20;
```

## Explanation
JOIN beneficiaries (mới đăng ký) với transactions. HAVING SUM > 50M. Use case: fraud detection — pattern: thêm beneficiary mới → chuyển tiền lớn ngay = suspicious.
