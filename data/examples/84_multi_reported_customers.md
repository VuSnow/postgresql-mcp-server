# Reported customers — đa báo cáo (bị report nhiều lần)

## Complexity: complex

## Tables Used: reported_customers, fraud_reports, customers

## Question (Vietnamese)
Tìm khách hàng bị report nhiều lần (>= 2 lần). Ai bị report nhiều nhất?

## Join Logic
- Cần `reported_customers` để đếm số lần bị report.
- Cần `customers` để lấy tên.
- Cần `fraud_reports` để lấy chi tiết.
- **JOIN paths**:
  - `reported_customers.reported_cif = customers.cif_no`
- GROUP BY reported_cif, HAVING COUNT >= 2.

## SQL
```sql
SELECT
    rc.reported_cif,
    c.full_name,
    c.status AS customer_status,
    COUNT(DISTINCT rc.fraud_report_id) AS times_reported,
    ARRAY_AGG(DISTINCT fr.fraud_type) AS fraud_types,
    MIN(fr.reported_at) AS first_reported,
    MAX(fr.reported_at) AS last_reported
FROM reported_customers rc
JOIN customers c ON rc.reported_cif = c.cif_no
JOIN fraud_reports fr ON rc.fraud_report_id = fr.fraud_report_id
GROUP BY rc.reported_cif, c.full_name, c.status
HAVING COUNT(DISTINCT rc.fraud_report_id) >= 2
ORDER BY times_reported DESC
LIMIT 20;
```

## Explanation
3-table JOIN. GROUP BY KH bị report. HAVING COUNT >= 2 → chỉ lấy repeat offenders. ARRAY_AGG(DISTINCT fraud_type) gom tất cả loại fraud vào 1 array. Use case: priority investigation.
