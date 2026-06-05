# Chi tiêu trung bình theo ngày trong tuần

## Complexity: complex

## Tables Used: transactions

## Question (Vietnamese)
Khách hàng CIF000006 chi tiêu trung bình bao nhiêu vào mỗi ngày trong tuần?

## Join Logic
- Chỉ cần bảng `transactions`.
- Cần CTE vì 2 bước aggregation:
  1. Tính tổng chi mỗi ngày cụ thể
  2. AVG theo day_of_week

## SQL
```sql
WITH daily_spending AS (
    SELECT
        transaction_time::DATE AS txn_date,
        EXTRACT(DOW FROM transaction_time) AS dow,
        SUM(amount) AS daily_total
    FROM transactions
    WHERE cif_no = 'CIF000006'
      AND direction = 'OUT'
      AND status = 'SUCCESS'
      AND transaction_time >= CURRENT_DATE - INTERVAL '3 months'
    GROUP BY transaction_time::DATE, EXTRACT(DOW FROM transaction_time)
)
SELECT
    dow,
    CASE dow
        WHEN 0 THEN 'Chủ nhật'
        WHEN 1 THEN 'Thứ 2'
        WHEN 2 THEN 'Thứ 3'
        WHEN 3 THEN 'Thứ 4'
        WHEN 4 THEN 'Thứ 5'
        WHEN 5 THEN 'Thứ 6'
        WHEN 6 THEN 'Thứ 7'
    END AS day_name,
    COUNT(*) AS num_days,
    ROUND(AVG(daily_total)) AS avg_daily_spent,
    MAX(daily_total) AS max_daily_spent
FROM daily_spending
GROUP BY dow
ORDER BY dow;
```

## Explanation
CTE 2 bước: (1) tổng chi MỖI NGÀY cụ thể (GROUP BY date), (2) trung bình theo day of week (GROUP BY dow). Nếu GROUP BY dow trực tiếp → tính trung bình theo GIAO DỊCH (sai).
