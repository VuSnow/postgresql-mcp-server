# Dịch vụ thanh toán hóa đơn đã đăng ký kèm lịch sử

## Complexity: complex

## Tables Used: customer_biller_accounts, billers, transactions

## Question (Vietnamese)
Khách hàng CIF000025 đã đăng ký thanh toán những dịch vụ nào? Với mỗi dịch vụ, cho biết lần thanh toán gần nhất và tổng tiền đã thanh toán.

## Join Logic
- Cần `customer_biller_accounts` (CBA) để biết khách hàng đăng ký dịch vụ nào.
- Cần `billers` để lấy tên và loại nhà cung cấp — CBA chỉ lưu biller_id.
- Cần `transactions` để tính tổng tiền đã thanh toán và lần cuối thanh toán.
- **JOIN path 1**: `customer_biller_accounts.biller_id = billers.biller_id`
- **JOIN path 2**: `transactions.biller_id = cba.biller_id AND transactions.cif_no = cba.cif_no`
- LEFT JOIN cho transactions vì có thể đăng ký dịch vụ nhưng chưa thanh toán lần nào.

## SQL
```sql
SELECT
    b.biller_name,
    b.biller_type,
    cba.customer_bill_code,
    cba.alias,
    COUNT(t.transaction_id) AS payment_count,
    SUM(t.amount) AS total_paid,
    MAX(t.transaction_time) AS last_payment_at
FROM customer_biller_accounts cba
JOIN billers b ON cba.biller_id = b.biller_id
LEFT JOIN transactions t ON t.biller_id = cba.biller_id
    AND t.cif_no = cba.cif_no
    AND t.transaction_type = 'BILL_PAYMENT'
    AND t.status = 'SUCCESS'
WHERE cba.cif_no = 'CIF000025'
  AND cba.status = 'ACTIVE'
GROUP BY b.biller_id, b.biller_name, b.biller_type, cba.customer_bill_code, cba.alias
ORDER BY last_payment_at DESC NULLS LAST;
```

## Explanation
3-table JOIN: CBA → billers (tên/loại) → transactions (lịch sử thanh toán). LEFT JOIN transactions với điều kiện filter trong ON clause (không phải WHERE) để giữ dịch vụ chưa thanh toán. NULLS LAST đảm bảo dịch vụ chưa có payment hiện cuối.
