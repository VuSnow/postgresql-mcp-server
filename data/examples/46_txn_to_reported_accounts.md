# Giao dịch với tài khoản đã bị report (cross-domain)

## Complexity: complex

## Tables Used: transactions, reported_accounts

## Question (Vietnamese)
Tìm các giao dịch chuyển khoản thành công mà tài khoản nhận đã nằm trong danh sách bị báo cáo lừa đảo (nhưng giao dịch xảy ra trước khi bị report).

## Join Logic
- Cần `transactions` để lấy giao dịch chuyển khoản (BANK_TRANSFER, direction OUT).
- Cần `reported_accounts` để check xem counterparty_account_no có bị report không.
- **JOIN path**: `transactions.counterparty_account_no = reported_accounts.account_no AND transactions.counterparty_bank_code = reported_accounts.bank_code`
- INNER JOIN vì chỉ muốn giao dịch match với TK bị report.
- Filter transaction_time < first_reported_at → giao dịch xảy ra trước khi bị báo cáo.

## SQL
```sql
SELECT
    t.transaction_ref,
    t.transaction_time,
    t.cif_no,
    t.amount,
    t.counterparty_name,
    t.counterparty_account_no,
    t.counterparty_bank_code,
    ra.risk_level,
    ra.risk_score,
    ra.first_reported_at
FROM transactions t
JOIN reported_accounts ra ON t.counterparty_account_no = ra.account_no
    AND t.counterparty_bank_code = ra.bank_code
WHERE t.transaction_type = 'BANK_TRANSFER'
  AND t.direction = 'OUT'
  AND t.status = 'SUCCESS'
  AND t.transaction_time < ra.first_reported_at
ORDER BY t.amount DESC
LIMIT 100;
```

## Explanation
Cross-domain JOIN: transactions ↔ reported_accounts qua counterparty info. Tìm giao dịch "nghi vấn" — tiền đã chuyển đến TK mà sau này bị report lừa đảo. Filter transaction_time < first_reported_at đảm bảo giao dịch xảy ra trước khi report.
