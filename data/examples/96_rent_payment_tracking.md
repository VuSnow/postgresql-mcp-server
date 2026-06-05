# Rent payment tracking (RENT category)

## Complexity: medium

## Tables Used: transactions, transaction_categories

## Question (Vietnamese)
Lịch sử thanh toán tiền thuê nhà (RENT) của khách hàng CIF000035 trong 6 tháng. Tháng nào chưa trả?

## Join Logic
- Cần `transactions` cho giao dịch.
- Cần `transaction_categories` filter category_code = 'RENT'.
- **JOIN path**: `transactions.category_id = transaction_categories.category_id`
- generate_series để tạo list 6 tháng, LEFT JOIN xem tháng nào có payment.

## SQL
```sql
WITH months AS (
    SELECT generate_series(
        DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '5 months',
        DATE_TRUNC('month', CURRENT_DATE),
        '1 month'::INTERVAL
    ) AS month_start
),
rent_payments AS (
    SELECT
        DATE_TRUNC('month', t.transaction_time) AS payment_month,
        SUM(t.amount) AS amount_paid,
        COUNT(*) AS payment_count
    FROM transactions t
    JOIN transaction_categories tc ON t.category_id = tc.category_id
    WHERE t.cif_no = 'CIF000035'
      AND tc.category_code = 'RENT'
      AND t.direction = 'OUT'
      AND t.status = 'SUCCESS'
      AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '5 months'
    GROUP BY DATE_TRUNC('month', t.transaction_time)
)
SELECT
    m.month_start,
    COALESCE(rp.amount_paid, 0) AS amount_paid,
    COALESCE(rp.payment_count, 0) AS payment_count,
    CASE WHEN rp.payment_month IS NULL THEN 'MISSING' ELSE 'PAID' END AS payment_status
FROM months m
LEFT JOIN rent_payments rp ON m.month_start = rp.payment_month
ORDER BY m.month_start ASC;
```

## Explanation
generate_series tạo 6 tháng liên tục. LEFT JOIN với payment data → tháng không có payment sẽ NULL → mark 'MISSING'. Use case: theo dõi trả tiền thuê nhà đều đặn.
