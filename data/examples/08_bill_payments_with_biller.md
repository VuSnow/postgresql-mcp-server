# Lịch sử thanh toán hóa đơn kèm thông tin nhà cung cấp

## Complexity: medium

## Tables Used: transactions, billers

## Question (Vietnamese)
Liệt kê các lần thanh toán hóa đơn của khách hàng CIF000015 trong tháng trước, bao gồm tên nhà cung cấp và loại hóa đơn.

## Join Logic
- Cần `transactions` để lấy lịch sử giao dịch thanh toán hóa đơn.
- Cần `billers` để lấy `biller_name` và `biller_type` — transactions chỉ lưu biller_id (UUID).
- **JOIN path**: `transactions.biller_id = billers.biller_id`
- Dùng **INNER JOIN** vì đã filter `transaction_type = 'BILL_PAYMENT'` — giao dịch bill payment luôn có biller_id.

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    b.biller_name,
    b.biller_type,
    t.amount,
    t.status,
    t.description
FROM transactions t
JOIN billers b ON t.biller_id = b.biller_id
WHERE t.cif_no = 'CIF000015'
  AND t.transaction_type = 'BILL_PAYMENT'
  AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
  AND t.transaction_time < DATE_TRUNC('month', CURRENT_DATE)
ORDER BY t.transaction_time DESC
LIMIT 100;
```

## Explanation
JOIN transactions với billers để lấy tên và loại nhà cung cấp. Khoảng thời gian tháng trước: từ đầu tháng trước đến đầu tháng này (exclusive). Dùng DATE_TRUNC thay vì EXTRACT để tận dụng index trên transaction_time.
