# Fraud decisions — thống kê quyết định xử lý

## Complexity: medium

## Tables Used: fraud_decisions, fraud_reports

## Question (Vietnamese)
Thống kê các quyết định xử lý gian lận theo loại decision và fraud_type. Bao nhiêu case bị freeze? Bao nhiêu case được clear?

## Join Logic
- Cần `fraud_decisions` để lấy decision.
- Cần `fraud_reports` để lấy fraud_type context.
- **JOIN path**: `fraud_decisions.fraud_report_id = fraud_reports.fraud_report_id`

## SQL
```sql
SELECT
    fr.fraud_type,
    fd.decision,
    COUNT(*) AS decision_count,
    MIN(fd.decided_at) AS first_decision,
    MAX(fd.decided_at) AS last_decision
FROM fraud_decisions fd
JOIN fraud_reports fr ON fd.fraud_report_id = fr.fraud_report_id
GROUP BY fr.fraud_type, fd.decision
ORDER BY fr.fraud_type, decision_count DESC;
```

## Explanation
JOIN fraud_decisions với fraud_reports. GROUP BY cả fraud_type + decision → ma trận cross-tab. Use case: review xem loại fraud nào thường bị freeze, loại nào thường được clear.
