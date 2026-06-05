# Giao dịch lớn nhất từng tháng (window function)

## Complexity: complex

## Tables Used: transactions

## Question (Vietnamese)
Cho tôi giao dịch chi tiêu lớn nhất mỗi tháng của khách hàng CIF000010 trong 6 tháng qua.

## Join Logic
- Chỉ cần bảng `transactions`.
- Dùng window function ROW_NUMBER() để rank giao dịch theo amount trong mỗi tháng.
- CTE để filter rank = 1.

## SQL
```sql
WITH ranked AS (
    SELECT
        transaction_ref,
        transaction_time,
        amount,
        transaction_type,
        description,
        DATE_TRUNC('month', transaction_time) AS month,
        ROW_NUMBER() OVER (
            PARTITION BY DATE_TRUNC('month', transaction_time)
            ORDER BY amount DESC
        ) AS rn
    FROM transactions
    WHERE cif_no = 'CIF000010'
      AND direction = 'OUT'
      AND status = 'SUCCESS'
      AND transaction_time >= CURRENT_DATE - INTERVAL '6 months'
)
SELECT
    month,
    transaction_ref,
    transaction_time,
    amount,
    transaction_type,
    description
FROM ranked
WHERE rn = 1
ORDER BY month DESC;
```

## Explanation
Window function ROW_NUMBER() PARTITION BY month ORDER BY amount DESC → rank giao dịch theo giá trị trong từng tháng. Filter rn = 1 lấy giao dịch lớn nhất mỗi tháng. Tối đa 6 rows.
