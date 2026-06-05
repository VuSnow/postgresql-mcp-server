# Tổng tiền lương nhận được trong năm

## Complexity: simple

## Tables Used: transactions

## Question (Vietnamese)
Tổng tiền lương khách hàng CIF000001 nhận được trong năm nay là bao nhiêu?

## Join Logic
- Chỉ cần bảng `transactions` vì thông tin lương nằm ở cột transaction_type = 'SALARY' và direction = 'IN'.
- Không cần JOIN vì không yêu cầu tên KH hay thông tin thêm.

## SQL
```sql
SELECT
    COUNT(*) AS salary_count,
    SUM(amount) AS total_salary,
    ROUND(AVG(amount)) AS avg_monthly_salary
FROM transactions
WHERE cif_no = 'CIF000001'
  AND transaction_type = 'SALARY'
  AND direction = 'IN'
  AND status = 'SUCCESS'
  AND transaction_time >= DATE_TRUNC('year', CURRENT_DATE);
```

## Explanation
Aggregation đơn giản trên 1 bảng. Filter transaction_type = 'SALARY' + direction = 'IN'. DATE_TRUNC('year', CURRENT_DATE) = ngày 1/1 năm nay. Kết quả 1 row.
