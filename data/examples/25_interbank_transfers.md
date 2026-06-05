# Giao dịch chuyển khoản liên ngân hàng

## Complexity: complex

## Tables Used: transactions, beneficiaries, customers

## Question (Vietnamese)
Liệt kê top 10 giao dịch chuyển khoản liên ngân hàng giá trị lớn nhất tuần này, kèm thông tin người gửi và người nhận.

## Join Logic
- Cần `transactions` chứa thông tin giao dịch.
- Cần `customers` để lấy tên người gửi.
- Cần `beneficiaries` để lấy thêm info người nhận đã lưu.
- **JOIN path 1**: `transactions.cif_no = customers.cif_no`
- **JOIN path 2**: `transactions.beneficiary_id = beneficiaries.beneficiary_id`
- LEFT JOIN beneficiaries vì KH có thể chuyển cho người mới chưa lưu.

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    c.full_name AS sender_name,
    t.amount,
    t.counterparty_name AS receiver_name,
    t.counterparty_bank_code,
    COALESCE(ben.beneficiary_bank_name, t.counterparty_bank_code) AS receiver_bank,
    ben.nickname AS receiver_nickname,
    t.channel,
    t.status
FROM transactions t
JOIN customers c ON t.cif_no = c.cif_no
LEFT JOIN beneficiaries ben ON t.beneficiary_id = ben.beneficiary_id
WHERE t.transaction_type = 'BANK_TRANSFER'
  AND t.direction = 'OUT'
  AND t.counterparty_bank_code IS NOT NULL
  AND t.transaction_time >= DATE_TRUNC('week', CURRENT_DATE)
  AND t.status = 'SUCCESS'
ORDER BY t.amount DESC
LIMIT 10;
```

## Explanation
3-table JOIN. LEFT JOIN beneficiaries vì có thể NULL. COALESCE ưu tiên tên đẹp từ beneficiaries, fallback về bank_code. Filter counterparty_bank_code IS NOT NULL loại giao dịch nội bộ.
