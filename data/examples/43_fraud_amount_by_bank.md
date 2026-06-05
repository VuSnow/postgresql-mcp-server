# Tổng tiền bị lừa đảo theo ngân hàng nhận

## Complexity: medium

## Tables Used: reported_accounts

## Question (Vietnamese)
Thống kê tổng tiền bị báo cáo lừa đảo theo từng ngân hàng (bank_code). Ngân hàng nào có tài khoản lừa đảo nhiều nhất?

## Join Logic
- Chỉ cần bảng `reported_accounts` — đã chứa aggregate data.
- GROUP BY bank_code để thống kê theo ngân hàng.
- Không cần JOIN fraud_reports vì data đã tổng hợp sẵn.

## SQL
```sql
SELECT
    bank_code,
    COUNT(*) AS reported_account_count,
    SUM(valid_report_count) AS total_reports,
    SUM(total_reported_amount) AS total_fraud_amount,
    ROUND(AVG(risk_score), 2) AS avg_risk_score,
    COUNT(*) FILTER (WHERE risk_level IN ('HIGH', 'CRITICAL')) AS high_risk_count
FROM reported_accounts
WHERE status = 'ACTIVE'
GROUP BY bank_code
ORDER BY total_fraud_amount DESC;
```

## Explanation
Aggregation trên bảng đã aggregate. GROUP BY bank_code. SUM(total_reported_amount) = tổng tiền bị mất qua mỗi ngân hàng. FILTER clause đếm TK risk cao. Không cần LIMIT vì số bank_code hữu hạn.
