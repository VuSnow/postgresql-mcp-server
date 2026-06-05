# Biller alias matching — tìm hóa đơn theo alias

## Complexity: medium

## Tables Used: customer_biller_accounts, billers

## Question (Vietnamese)
Tìm tất cả đăng ký hóa đơn của khách hàng CIF000070 với alias và tên biller tương ứng.

## Join Logic
- Cần `customer_biller_accounts` để lấy đăng ký hóa đơn (alias, customer_bill_code).
- Cần `billers` để lấy tên và loại biller.
- **JOIN path**: `customer_biller_accounts.biller_id = billers.biller_id`

## SQL
```sql
SELECT
    cba.alias,
    b.biller_name,
    b.biller_type,
    cba.customer_bill_code,
    cba.status,
    cba.last_paid_at,
    cba.registered_at
FROM customer_biller_accounts cba
JOIN billers b ON cba.biller_id = b.biller_id
WHERE cba.cif_no = 'CIF000070'
ORDER BY cba.status DESC, cba.last_paid_at DESC NULLS LAST;
```

## Explanation
JOIN CBA với billers. alias = tên KH đặt cho dễ nhớ (vd: "Tiền điện nhà", "Internet FPT"). Sắp xếp ACTIVE trước, last_paid_at gần nhất trước.
