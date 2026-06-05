# Hóa đơn quá hạn thanh toán (chưa trả lâu)

## Complexity: complex

## Tables Used: customer_biller_accounts, billers

## Question (Vietnamese)
Tìm các hóa đơn đã đăng ký nhưng chưa thanh toán trong 60 ngày (có thể quá hạn).

## Join Logic
- Cần `customer_biller_accounts` để check last_paid_at.
- Cần `billers` để lấy tên và loại biller.
- **JOIN path**: `customer_biller_accounts.biller_id = billers.biller_id`
- Filter: last_paid_at < 60 ngày trước HOẶC last_paid_at IS NULL.

## SQL
```sql
SELECT
    cba.cif_no,
    b.biller_name,
    b.biller_type,
    cba.customer_bill_code,
    cba.alias,
    cba.last_paid_at,
    CURRENT_DATE - cba.last_paid_at::DATE AS days_since_payment
FROM customer_biller_accounts cba
JOIN billers b ON cba.biller_id = b.biller_id
WHERE cba.status = 'ACTIVE'
  AND (cba.last_paid_at < CURRENT_DATE - INTERVAL '60 days'
       OR cba.last_paid_at IS NULL)
ORDER BY cba.last_paid_at ASC NULLS FIRST
LIMIT 100;
```

## Explanation
JOIN CBA với billers để lấy tên. Filter: last_paid_at quá cũ (> 60 ngày) hoặc NULL (chưa bao giờ trả). NULLS FIRST ưu tiên hóa đơn chưa trả bao giờ. Use case: nhắc nhở KH trả hóa đơn.
