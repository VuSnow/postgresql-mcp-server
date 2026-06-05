# Daily transaction volume (time series)

## Complexity: complex

## Tables Used: transactions

## Question (Vietnamese)
Cho tôi số lượng giao dịch và tổng giá trị theo từng ngày trong 14 ngày gần đây (toàn hệ thống).

## Join Logic
- Chỉ cần bảng `transactions` — aggregation theo ngày toàn hệ thống.
- Dùng transaction_time::DATE để group theo ngày.
- Tính failure_rate bằng FILTER clause.

## SQL
```sql
SELECT
    transaction_time::DATE AS txn_date,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE status = 'SUCCESS') AS success_count,
    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_count,
    SUM(amount) FILTER (WHERE status = 'SUCCESS') AS total_value,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'FAILED')::NUMERIC /
        NULLIF(COUNT(*), 0) * 100, 2
    ) AS failure_rate_percent
FROM transactions
WHERE transaction_time >= CURRENT_DATE - INTERVAL '14 days'
GROUP BY transaction_time::DATE
ORDER BY txn_date DESC;
```

## Explanation
Time series aggregation. FILTER clause tách đếm theo status. NULLIF(COUNT(*), 0) tránh division by zero. Cast NUMERIC cho phép chia thập phân. Tối đa 14 rows.
