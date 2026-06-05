# So sánh thu chi trong khoảng thời gian

## Complexity: medium

## Tables Used: transactions

## Question (Vietnamese)
So sánh tổng thu và tổng chi của khách hàng CIF000002 trong tháng trước.

## Join Logic
- Chỉ cần bảng `transactions` vì direction (IN/OUT) và amount đều nằm trong 1 bảng.
- Dùng conditional aggregation (SUM + CASE WHEN) để tách theo direction.
- Không cần JOIN.

## SQL
```sql
SELECT
    SUM(CASE WHEN direction = 'IN' THEN amount ELSE 0 END) AS total_income,
    SUM(CASE WHEN direction = 'OUT' THEN amount ELSE 0 END) AS total_expense,
    SUM(CASE WHEN direction = 'IN' THEN amount ELSE -amount END) AS net_balance
FROM transactions
WHERE cif_no = 'CIF000002'
  AND status = 'SUCCESS'
  AND transaction_time >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
  AND transaction_time < DATE_TRUNC('month', CURRENT_DATE);
```

## Explanation
Conditional aggregation: SUM + CASE WHEN tách thu/chi trong cùng 1 query. Kết quả là 1 row duy nhất. Không cần LIMIT hay GROUP BY.
