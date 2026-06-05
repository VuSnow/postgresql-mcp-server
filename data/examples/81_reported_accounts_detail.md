# Reported accounts — chi tiết tài khoản bị report

## Complexity: complex

## Tables Used: reported_accounts, fraud_reports, customers

## Question (Vietnamese)
Liệt kê TK bị report gian lận, kèm tên chủ TK và chi tiết report gốc (ai report, loại fraud gì).

## Join Logic
- Cần `reported_accounts` để lấy TK bị report.
- Cần `fraud_reports` để lấy chi tiết báo cáo (loại fraud, mô tả).
- Cần `customers` để lấy tên chủ TK bị report.
- **JOIN paths**:
  - `reported_accounts.fraud_report_id = fraud_reports.fraud_report_id`
  - `reported_accounts.reported_cif = customers.cif_no`

## SQL
```sql
SELECT
    ra.reported_account_no,
    c.full_name AS reported_customer_name,
    ra.reported_cif,
    fr.fraud_type,
    fr.description AS report_description,
    fr.reporter_cif,
    fr.reported_at,
    ra.status AS report_status
FROM reported_accounts ra
JOIN fraud_reports fr ON ra.fraud_report_id = fr.fraud_report_id
JOIN customers c ON ra.reported_cif = c.cif_no
ORDER BY fr.reported_at DESC
LIMIT 50;
```

## Explanation
3-table JOIN. reported_accounts → fraud_reports (chi tiết report), reported_accounts → customers (tên KH bị report). Cho thấy ai bị report, vì fraud gì, bởi ai.
