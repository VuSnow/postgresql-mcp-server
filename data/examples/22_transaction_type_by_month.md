# Tổng hợp giao dịch theo loại và tháng (pivot)

## Complexity: complex

## Tables Used: transactions

## Question (Vietnamese)
Thống kê số lượng giao dịch theo loại (SALARY, BANK_TRANSFER, CARD_PAYMENT, BILL_PAYMENT) cho mỗi tháng trong 6 tháng gần đây của khách hàng CIF000004.

## Join Logic
- Chỉ cần bảng `transactions`.
- Dùng PostgreSQL FILTER clause để tạo pivot table.
- GROUP BY month để tạo time series.

## SQL
```sql
SELECT
    DATE_TRUNC('month', transaction_time) AS month,
    COUNT(*) FILTER (WHERE transaction_type = 'SALARY') AS salary_count,
    COUNT(*) FILTER (WHERE transaction_type = 'BANK_TRANSFER') AS transfer_count,
    COUNT(*) FILTER (WHERE transaction_type = 'CARD_PAYMENT') AS card_count,
    COUNT(*) FILTER (WHERE transaction_type = 'BILL_PAYMENT') AS bill_count,
    COUNT(*) AS total_count
FROM transactions
WHERE cif_no = 'CIF000004'
  AND transaction_time >= CURRENT_DATE - INTERVAL '6 months'
  AND status = 'SUCCESS'
GROUP BY DATE_TRUNC('month', transaction_time)
ORDER BY month DESC;
```

## Explanation
Dùng FILTER clause (PostgreSQL-specific) để tạo pivot table: mỗi row = 1 tháng, mỗi cột = số giao dịch theo loại. Không cần LIMIT vì tối đa 6 rows.
