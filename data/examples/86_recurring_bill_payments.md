# Thanh toán hóa đơn định kỳ (BILL_PAYMENT recurring)

## Complexity: complex

## Tables Used: transactions, customer_biller_accounts, billers

## Question (Vietnamese)
Liệt kê các hóa đơn khách hàng CIF000055 thanh toán định kỳ (có >= 3 lần thanh toán cho cùng 1 biller).

## Join Logic
- Cần `transactions` để lấy giao dịch BILL_PAYMENT.
- Cần `customer_biller_accounts` để biết KH đăng ký với biller nào.
- Cần `billers` để lấy tên biller.
- **JOIN paths**:
  - `transactions.biller_id = billers.biller_id` (hoặc qua CBA)
  - `customer_biller_accounts.biller_id = billers.biller_id`
  - `customer_biller_accounts.cif_no = transactions.cif_no`

## SQL
```sql
SELECT
    b.biller_name,
    b.biller_type,
    COUNT(*) AS payment_count,
    SUM(t.amount) AS total_paid,
    ROUND(AVG(t.amount)) AS avg_amount,
    MIN(t.transaction_time) AS first_payment,
    MAX(t.transaction_time) AS last_payment
FROM transactions t
JOIN billers b ON t.biller_id = b.biller_id
WHERE t.cif_no = 'CIF000055'
  AND t.transaction_type = 'BILL_PAYMENT'
  AND t.status = 'SUCCESS'
GROUP BY b.biller_id, b.biller_name, b.biller_type
HAVING COUNT(*) >= 3
ORDER BY payment_count DESC;
```

## Explanation
JOIN transactions + billers. GROUP BY biller. HAVING >= 3 lần → bills trả định kỳ. AVG amount cho biết mức trả trung bình (tiền điện thường đều, tiền điện thoại ít thay đổi).
