# Fraud decisions — lịch sử screening giao dịch

## Complexity: medium

## Tables Used: fraud_decisions, action_requests

## Question (Vietnamese)
Liệt kê các quyết định screening có decision = BLOCK hoặc WARN trong 30 ngày gần đây, kèm thông tin action request tương ứng.

## Join Logic
- Cần `fraud_decisions` để lấy kết quả screening (decision, risk_level, reason_codes).
- Cần `action_requests` để lấy context (action_type, user_text, cif_no).
- **JOIN path**: `fraud_decisions.action_id = action_requests.action_id`
- INNER JOIN vì fraud_decisions luôn có action_id (NOT NULL).

## SQL
```sql
SELECT
    fd.decision_id,
    fd.created_at,
    ar.cif_no,
    ar.action_type,
    ar.user_text,
    fd.receiver_account_no,
    fd.receiver_bank_code,
    fd.matched_report_count,
    fd.risk_score,
    fd.risk_level,
    fd.decision,
    fd.reason_codes
FROM fraud_decisions fd
JOIN action_requests ar ON fd.action_id = ar.action_id
WHERE fd.decision IN ('BLOCK', 'WARN')
  AND fd.created_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY fd.created_at DESC
LIMIT 100;
```

## Explanation
JOIN fraud_decisions với action_requests để lấy context (KH nào, yêu cầu gì). Filter decision IN ('BLOCK', 'WARN') → chỉ lấy screening có cảnh báo/chặn.
