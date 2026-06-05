# Kiểm tra tài khoản nhận có bị báo cáo không (screening)

## Complexity: simple

## Tables Used: reported_accounts

## Question (Vietnamese)
Tài khoản số 43275604177 tại ngân hàng ACB có bị báo cáo lừa đảo không? Nếu có thì mức rủi ro bao nhiêu?

## Join Logic
- Chỉ cần bảng `reported_accounts` — lookup theo cặp (account_no, bank_code).
- Đây là use case chính của bảng này: transaction screening trước khi chuyển tiền.

## SQL
```sql
SELECT
    account_no,
    bank_code,
    valid_report_count,
    unique_reporter_count,
    total_reported_amount,
    risk_score,
    risk_level,
    status,
    first_reported_at,
    last_reported_at
FROM reported_accounts
WHERE account_no = '43275604177'
  AND bank_code = 'ACB';
```

## Explanation
Lookup đơn giản theo composite key (account_no, bank_code). Nếu có kết quả → tài khoản đã bị báo cáo. Nếu không có row → tài khoản clean. Không cần LIMIT vì unique constraint đảm bảo tối đa 1 row.
