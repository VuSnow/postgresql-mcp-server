# Chuyển khoản cho người nhận đã lưu — aggregate

## Complexity: complex

## Tables Used: transactions, beneficiaries

## Question (Vietnamese)
Liệt kê lịch sử chuyển khoản của khách hàng CIF000008 cho từng người nhận đã lưu, bao gồm tên người nhận, ngân hàng, số lần chuyển và tổng tiền.

## Join Logic
- Cần `transactions` để lấy lịch sử giao dịch chuyển khoản.
- Cần `beneficiaries` để lấy thông tin người nhận (tên, ngân hàng) — transactions chỉ lưu beneficiary_id.
- **JOIN path**: `transactions.beneficiary_id = beneficiaries.beneficiary_id`
- Dùng **INNER JOIN** vì đã filter transaction_type = 'BANK_TRANSFER' VÀ chỉ muốn giao dịch có người nhận đã lưu.
- GROUP BY người nhận để aggregate.

## SQL
```sql
SELECT
    ben.beneficiary_name,
    ben.beneficiary_bank_name,
    ben.nickname,
    COUNT(*) AS transfer_count,
    SUM(t.amount) AS total_amount,
    MAX(t.transaction_time) AS last_transfer_at
FROM transactions t
JOIN beneficiaries ben ON t.beneficiary_id = ben.beneficiary_id
WHERE t.cif_no = 'CIF000008'
  AND t.transaction_type = 'BANK_TRANSFER'
  AND t.direction = 'OUT'
  AND t.status = 'SUCCESS'
GROUP BY ben.beneficiary_id, ben.beneficiary_name, ben.beneficiary_bank_name, ben.nickname
ORDER BY total_amount DESC
LIMIT 20;
```

## Explanation
JOIN transactions với beneficiaries để nhóm giao dịch theo người nhận. GROUP BY dùng beneficiary_id (PK) cộng các cột hiển thị. MAX(transaction_time) cho biết lần chuyển gần nhất. Filter direction='OUT' vì đây là tiền gửi đi.
