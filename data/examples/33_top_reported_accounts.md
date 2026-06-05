# Tài khoản bị báo cáo nhiều nhất

## Complexity: simple

## Tables Used: reported_accounts

## Question (Vietnamese)
Liệt kê top 10 tài khoản bị báo cáo lừa đảo nhiều nhất, sắp xếp theo risk score.

## Join Logic
- Chỉ cần bảng `reported_accounts` — đã chứa aggregate data (valid_report_count, risk_score, total_reported_amount).
- Không cần JOIN fraud_reports vì reported_accounts đã tổng hợp sẵn.

## SQL
```sql
SELECT
    account_no,
    bank_code,
    valid_report_count,
    unique_reporter_count,
    total_reported_amount,
    avg_confidence_score,
    risk_score,
    risk_level,
    status,
    first_reported_at,
    last_reported_at
FROM reported_accounts
WHERE status = 'ACTIVE'
ORDER BY risk_score DESC, valid_report_count DESC
LIMIT 10;
```

## Explanation
Query trên bảng aggregate. Sắp xếp theo risk_score giảm dần. Filter status = ACTIVE (đang monitoring). Không cần GROUP BY vì data đã aggregate sẵn.
