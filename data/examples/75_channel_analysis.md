# Phân tích channel sử dụng (MOBILE vs WEB)

## Complexity: medium

## Tables Used: transactions

## Question (Vietnamese)
Thống kê tỷ lệ sử dụng từng channel (MOBILE_APP, WEB, ATM, BRANCH) theo số giao dịch và giá trị trong 30 ngày.

## Join Logic
- Chỉ cần bảng `transactions`.
- GROUP BY channel.
- Window function SUM() OVER() để tính tỷ lệ.

## SQL
```sql
SELECT
    channel,
    COUNT(*) AS txn_count,
    SUM(amount) AS total_amount,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_by_count,
    ROUND(SUM(amount) * 100.0 / SUM(SUM(amount)) OVER (), 1) AS pct_by_value
FROM transactions
WHERE status = 'SUCCESS'
  AND transaction_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY channel
ORDER BY txn_count DESC;
```

## Explanation
GROUP BY channel. SUM(COUNT(*)) OVER() = tổng giao dịch hệ thống → tính %. Tương tự SUM(SUM(amount)) OVER() = tổng giá trị. Kết quả: mỗi channel chiếm bao nhiêu % theo số lượng và giá trị.
