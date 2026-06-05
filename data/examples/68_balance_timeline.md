# Số dư thay đổi trong ngày (balance_after tracking)

## Complexity: complex

## Tables Used: transactions

## Question (Vietnamese)
Theo dõi thay đổi số dư trong ngày hôm nay của khách hàng CIF000005 (balance_after mỗi giao dịch).

## Join Logic
- Chỉ cần bảng `transactions` — cột balance_after lưu số dư sau mỗi giao dịch.
- Filter theo ngày hôm nay và cif_no.
- Sắp xếp theo thời gian để thấy biến động số dư.

## SQL
```sql
SELECT
    transaction_time,
    transaction_type,
    direction,
    amount,
    CASE
        WHEN direction = 'IN' THEN '+' || amount::TEXT
        ELSE '-' || amount::TEXT
    END AS change,
    balance_after,
    description
FROM transactions
WHERE cif_no = 'CIF000005'
  AND transaction_time::DATE = CURRENT_DATE
  AND status = 'SUCCESS'
  AND balance_after IS NOT NULL
ORDER BY transaction_time ASC;
```

## Explanation
Filter ngày hôm nay. CASE WHEN hiển thị +/- cho dễ đọc. ORDER BY ASC để thấy timeline số dư. balance_after có thể NULL nên filter NOT NULL.
