# Fraud decision kèm thông tin người chuyển tiền

## Complexity: complex

## Tables Used: fraud_decisions, action_requests, customers

## Question (Vietnamese)
Liệt kê các giao dịch bị BLOCK do fraud screening trong tháng này, kèm tên khách hàng muốn chuyển tiền và số tiền.

## Join Logic
- Cần `fraud_decisions` để filter decision = 'BLOCK'.
- Cần `action_requests` để lấy api_payload (chứa amount) và cif_no.
- Cần `customers` để lấy tên KH.
- **JOIN path 1**: `fraud_decisions.action_id = action_requests.action_id`
- **JOIN path 2**: `action_requests.cif_no = customers.cif_no`

## SQL
```sql
SELECT
    fd.created_at,
    c.full_name,
    c.cif_no,
    fd.receiver_account_no,
    fd.receiver_bank_code,
    fd.risk_score,
    fd.risk_level,
    fd.matched_report_count,
    fd.reason_codes,
    ar.user_text
FROM fraud_decisions fd
JOIN action_requests ar ON fd.action_id = ar.action_id
JOIN customers c ON ar.cif_no = c.cif_no
WHERE fd.decision = 'BLOCK'
  AND fd.created_at >= DATE_TRUNC('month', CURRENT_DATE)
ORDER BY fd.created_at DESC
LIMIT 100;
```

## Explanation
3-table chain: fraud_decisions → action_requests → customers. Filter decision = 'BLOCK' và thời gian tháng này. Cho biết ai bị chặn khi chuyển đến đâu, lý do gì.
