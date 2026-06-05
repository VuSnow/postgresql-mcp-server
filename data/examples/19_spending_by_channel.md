# Phân tích chi tiêu theo kênh giao dịch

## Complexity: simple

## Tables Used: transactions

## Question (Vietnamese)
Thống kê số giao dịch và tổng tiền chi tiêu theo từng kênh (MOBILE, WEB, POS, ATM) của khách hàng CIF000018.

## Join Logic
- Chỉ cần bảng `transactions` vì `channel` là cột trực tiếp.
- GROUP BY channel để aggregate theo kênh.

## SQL
```sql
SELECT
    channel,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount,
    ROUND(AVG(amount)) AS avg_amount
FROM transactions
WHERE cif_no = 'CIF000018'
  AND direction = 'OUT'
  AND status = 'SUCCESS'
  AND transaction_time >= DATE_TRUNC('quarter', CURRENT_DATE)
GROUP BY channel
ORDER BY total_amount DESC;
```

## Explanation
Aggregation trên 1 bảng, GROUP BY channel. Không cần LIMIT vì số kênh cố định (5-6 giá trị). DATE_TRUNC('quarter', CURRENT_DATE) = ngày đầu quý hiện tại.
