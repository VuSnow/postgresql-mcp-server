# Tài khoản bị báo cáo có risk CRITICAL kèm chi tiết reports

## Complexity: complex

## Tables Used: reported_accounts, fraud_reports, customers

## Question (Vietnamese)
Liệt kê tài khoản có risk_level = CRITICAL, kèm danh sách người đã báo cáo (tên, thời gian báo cáo, loại lừa đảo).

## Join Logic
- Cần `reported_accounts` để filter risk_level = CRITICAL.
- Cần `fraud_reports` để lấy chi tiết từng report cho tài khoản đó.
- Cần `customers` để lấy tên người báo cáo.
- **JOIN path 1**: `fraud_reports.reported_account_no = reported_accounts.account_no AND fraud_reports.reported_bank_code = reported_accounts.bank_code` — match reports với reported accounts.
- **JOIN path 2**: `fraud_reports.reporter_cif_no = customers.cif_no` — lấy tên reporter.

## SQL
```sql
SELECT
    ra.account_no,
    ra.bank_code,
    ra.risk_score,
    ra.risk_level,
    ra.total_reported_amount,
    fr.report_id,
    c.full_name AS reporter_name,
    fr.fraud_type,
    fr.confidence_score,
    fr.status AS report_status,
    fr.created_at AS reported_at
FROM reported_accounts ra
JOIN fraud_reports fr ON fr.reported_account_no = ra.account_no
    AND fr.reported_bank_code = ra.bank_code
JOIN customers c ON fr.reporter_cif_no = c.cif_no
WHERE ra.risk_level = 'CRITICAL'
ORDER BY ra.risk_score DESC, fr.created_at DESC
LIMIT 100;
```

## Explanation
3-table JOIN: reported_accounts → fraud_reports (composite join trên account_no + bank_code) → customers (tên reporter). 1 reported_account có nhiều fraud_reports → multiple rows per account. Filter risk_level = 'CRITICAL'.
