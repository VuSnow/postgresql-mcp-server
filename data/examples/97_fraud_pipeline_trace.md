# Fraud report → decision → action pipeline (full trace)

## Complexity: complex

## Tables Used: fraud_reports, fraud_decisions, reported_accounts, accounts

## Question (Vietnamese)
Trace đầy đủ pipeline xử lý 1 fraud report: từ báo cáo → quyết định → tài khoản bị ảnh hưởng → trạng thái TK hiện tại.

## Join Logic
- Cần `fraud_reports` để lấy report gốc.
- Cần `fraud_decisions` để xem quyết định xử lý.
- Cần `reported_accounts` để biết TK nào bị report.
- Cần `accounts` để check trạng thái hiện tại của TK.
- **JOIN paths**:
  - `fraud_decisions.fraud_report_id = fraud_reports.fraud_report_id`
  - `reported_accounts.fraud_report_id = fraud_reports.fraud_report_id`
  - `reported_accounts.reported_account_no = accounts.account_no`

## SQL
```sql
SELECT
    fr.fraud_report_id,
    fr.fraud_type,
    fr.reported_at,
    fr.description AS report_description,
    fd.decision,
    fd.decided_by,
    fd.decided_at,
    fd.reason AS decision_reason,
    ra.reported_account_no,
    a.account_type,
    a.status AS current_account_status,
    a.balance AS current_balance
FROM fraud_reports fr
LEFT JOIN fraud_decisions fd ON fr.fraud_report_id = fd.fraud_report_id
LEFT JOIN reported_accounts ra ON fr.fraud_report_id = ra.fraud_report_id
LEFT JOIN accounts a ON ra.reported_account_no = a.account_no
WHERE fr.fraud_report_id = (
    SELECT fraud_report_id
    FROM fraud_reports
    ORDER BY reported_at DESC
    LIMIT 1
)
ORDER BY fd.decided_at ASC NULLS LAST;
```

## Explanation
4-table JOIN trace full pipeline. LEFT JOIN vì có thể chưa có decision (pending) hoặc chưa link account. Subquery lấy report mới nhất. Use case: investigation dashboard.
