# KH bị report nhiều tài khoản (multi-account fraud)

## Complexity: complex

## Tables Used: reported_customers, reported_accounts, customers

## Question (Vietnamese)
Tìm các CIF có nhiều hơn 1 tài khoản bị báo cáo lừa đảo, kèm danh sách tài khoản và risk level từng TK.

## Join Logic
- Cần `reported_customers` để filter `reported_account_count > 1` (multi-account).
- Cần `reported_accounts` để lấy chi tiết từng TK bị report.
- Cần `customers` để lấy tên.
- **JOIN path 1**: `reported_customers.cif_no = customers.cif_no`
- **JOIN path 2**: `reported_accounts.linked_customer_cif = reported_customers.cif_no`
- LEFT JOIN reported_accounts vì linked_customer_cif có thể NULL.

## SQL
```sql
SELECT
    rc.cif_no,
    c.full_name,
    rc.reported_account_count,
    rc.risk_score AS customer_risk,
    rc.risk_level AS customer_risk_level,
    ra.account_no,
    ra.bank_code,
    ra.risk_level AS account_risk_level,
    ra.valid_report_count,
    ra.total_reported_amount
FROM reported_customers rc
JOIN customers c ON rc.cif_no = c.cif_no
LEFT JOIN reported_accounts ra ON ra.linked_customer_cif = rc.cif_no
WHERE rc.reported_account_count > 1
ORDER BY rc.risk_score DESC, ra.risk_score DESC
LIMIT 100;
```

## Explanation
3-table JOIN: reported_customers → customers (tên) → reported_accounts (chi tiết TK). LEFT JOIN reported_accounts qua linked_customer_cif (có thể NULL). Filter reported_account_count > 1 → KH có nhiều TK lừa đảo.
