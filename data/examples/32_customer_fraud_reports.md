# Báo cáo lừa đảo của một khách hàng

## Complexity: simple

## Tables Used: fraud_reports

## Question (Vietnamese)
Khách hàng CIF000032 đã gửi bao nhiêu báo cáo lừa đảo? Liệt kê chi tiết.

## Join Logic
- Chỉ cần bảng `fraud_reports` vì tất cả info báo cáo nằm ở đây.
- Filter theo `reporter_cif_no` để lấy báo cáo của đúng KH.
- Không cần JOIN vì không yêu cầu tên KH hay chi tiết giao dịch.

## SQL
```sql
SELECT
    report_id,
    transaction_ref,
    reported_account_no,
    reported_bank_code,
    fraud_type,
    contact_channel,
    aftermath,
    confidence_score,
    status,
    created_at
FROM fraud_reports
WHERE reporter_cif_no = 'CIF000032'
ORDER BY created_at DESC
LIMIT 20;
```

## Explanation
Query đơn giản trên 1 bảng. Filter theo reporter_cif_no. Sắp xếp theo thời gian tạo mới nhất.
