# Fraud report kèm chi tiết giao dịch bị lừa

## Complexity: complex

## Tables Used: fraud_reports, transactions, customers

## Question (Vietnamese)
Liệt kê các báo cáo lừa đảo đã được xác nhận (CONFIRMED) kèm chi tiết giao dịch bị lừa (số tiền, thời gian, người nhận).

## Join Logic
- Cần `fraud_reports` để lấy danh sách báo cáo CONFIRMED.
- Cần `transactions` để lấy chi tiết giao dịch bị lừa (amount, time, counterparty).
- Cần `customers` để lấy tên người báo cáo.
- **JOIN path 1**: `fraud_reports.reporter_cif_no = customers.cif_no`
- **JOIN path 2**: `fraud_reports.transaction_ref = transactions.transaction_ref`
- LEFT JOIN transactions vì transaction_ref có thể NULL (báo cáo không gắn giao dịch cụ thể).

## SQL
```sql
SELECT
    fr.report_id,
    fr.created_at AS report_time,
    c.full_name AS reporter_name,
    fr.fraud_type,
    fr.reported_account_no,
    fr.reported_bank_code,
    t.transaction_time,
    t.amount AS fraud_amount,
    t.counterparty_name,
    fr.contact_channel,
    fr.aftermath,
    fr.confidence_score
FROM fraud_reports fr
JOIN customers c ON fr.reporter_cif_no = c.cif_no
LEFT JOIN transactions t ON fr.transaction_ref = t.transaction_ref
WHERE fr.status = 'CONFIRMED'
ORDER BY fr.created_at DESC
LIMIT 100;
```

## Explanation
3-table JOIN: fraud_reports → customers (tên reporter) → transactions (chi tiết giao dịch). LEFT JOIN transactions vì transaction_ref nullable. Filter status = 'CONFIRMED' → chỉ báo cáo đã xác nhận.
