# Giao dịch tiền lãi (INTEREST)

## Complexity: simple

## Tables Used: transactions

## Question (Vietnamese)
Tổng tiền lãi khách hàng CIF000088 nhận được từ ngân hàng trong 12 tháng qua là bao nhiêu?

## Join Logic
- Chỉ cần bảng `transactions` — filter transaction_type = 'INTEREST'.
- Không cần JOIN.

## SQL
```sql
SELECT
    COUNT(*) AS interest_count,
    SUM(amount) AS total_interest,
    MIN(amount) AS min_interest,
    MAX(amount) AS max_interest,
    MIN(transaction_time) AS first_interest,
    MAX(transaction_time) AS last_interest
FROM transactions
WHERE cif_no = 'CIF000088'
  AND transaction_type = 'INTEREST'
  AND direction = 'IN'
  AND status = 'SUCCESS'
  AND transaction_time >= CURRENT_DATE - INTERVAL '12 months';
```

## Explanation
Aggregation đơn giản. transaction_type = 'INTEREST' + direction = 'IN'. Tiền lãi thường nhận hàng tháng hoặc quý.
