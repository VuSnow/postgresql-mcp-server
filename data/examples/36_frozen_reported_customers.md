# Reported customers — khách hàng bị nghi ngờ lừa đảo

## Complexity: medium

## Tables Used: reported_customers, customers

## Question (Vietnamese)
Liệt kê các khách hàng bị đánh dấu FROZEN (đóng băng do fraud), kèm tên và thông tin risk.

## Join Logic
- Cần `reported_customers` để lấy thông tin fraud risk aggregate.
- Cần `customers` để lấy `full_name`, `phone_number`.
- **JOIN path**: `reported_customers.cif_no = customers.cif_no`
- INNER JOIN vì reported_customers.cif_no FK → customers.

## SQL
```sql
SELECT
    rc.cif_no,
    c.full_name,
    c.phone_number,
    c.status AS customer_status,
    rc.reported_account_count,
    rc.valid_report_count,
    rc.total_reported_amount,
    rc.risk_score,
    rc.risk_level,
    rc.updated_at
FROM reported_customers rc
JOIN customers c ON rc.cif_no = c.cif_no
WHERE rc.risk_level = 'FROZEN'
ORDER BY rc.risk_score DESC
LIMIT 50;
```

## Explanation
JOIN reported_customers với customers để lấy tên. Filter risk_level = 'FROZEN' → KH bị đóng băng do fraud. Sắp xếp theo risk_score.
