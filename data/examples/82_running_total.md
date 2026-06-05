# Running total — tổng dồn trong ngày

## Complexity: complex

## Tables Used: transactions

## Question (Vietnamese)
Tính tổng chi tiêu dồn (running total) trong ngày hôm nay của khách hàng CIF000012.

## Join Logic
- Chỉ cần bảng `transactions`.
- Window function SUM() OVER(ORDER BY transaction_time) để tính running total.

## SQL
```sql
SELECT
    transaction_time,
    transaction_type,
    amount,
    description,
    SUM(amount) OVER (ORDER BY transaction_time ASC) AS running_total_spent
FROM transactions
WHERE cif_no = 'CIF000012'
  AND direction = 'OUT'
  AND status = 'SUCCESS'
  AND transaction_time::DATE = CURRENT_DATE
ORDER BY transaction_time ASC;
```

## Explanation
SUM(amount) OVER (ORDER BY transaction_time) = running total: cộng dồn từ giao dịch đầu tiên đến hiện tại. Mỗi row hiển thị tổng tích lũy đến thời điểm đó. Use case: monitoring chi tiêu trong ngày.
