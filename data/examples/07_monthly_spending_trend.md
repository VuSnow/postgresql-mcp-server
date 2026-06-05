# Tổng chi tiêu hàng tháng (xu hướng theo thời gian)

## Complexity: complex

## Tables Used: transactions

## Question (Vietnamese)
Cho tôi tổng chi tiêu mỗi tháng của khách hàng CIF000003 trong 6 tháng gần đây.

## Join Logic
- Chỉ cần bảng `transactions` vì tất cả thông tin cần thiết (amount, time, direction) đều nằm trong 1 bảng.
- Không cần JOIN vì không yêu cầu tên danh mục, tên merchant, hay thông tin khách hàng.
- Dùng `DATE_TRUNC('month', transaction_time)` để group theo tháng.
- Filter `direction = 'OUT'` vì "chi tiêu" = tiền đi ra.

## SQL
```sql
SELECT
    DATE_TRUNC('month', transaction_time) AS month,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_spent
FROM transactions
WHERE cif_no = 'CIF000003'
  AND direction = 'OUT'
  AND status = 'SUCCESS'
  AND transaction_time >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', transaction_time)
ORDER BY month DESC;
```

## Explanation
Aggregation theo tháng trên 1 bảng. Dùng DATE_TRUNC để nhóm giao dịch theo tháng. Filter direction='OUT' cho chi tiêu, status='SUCCESS' để chỉ đếm giao dịch thành công. Không cần LIMIT vì kết quả tối đa 6 dòng.
