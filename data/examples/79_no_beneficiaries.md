# EXISTS — khách hàng chưa có beneficiary

## Complexity: medium

## Tables Used: customers, beneficiaries

## Question (Vietnamese)
Tìm khách hàng active nhưng chưa đăng ký người thụ hưởng nào (chưa có beneficiary).

## Join Logic
- Cần `customers` làm base.
- Cần check `beneficiaries` để tìm KH không tồn tại beneficiary.
- Dùng NOT EXISTS thay vì LEFT JOIN + IS NULL → performance tốt hơn.

## SQL
```sql
SELECT
    c.cif_no,
    c.full_name,
    c.phone_number,
    c.onboarded_at
FROM customers c
WHERE c.status = 'ACTIVE'
  AND NOT EXISTS (
      SELECT 1
      FROM beneficiaries b
      WHERE b.cif_no = c.cif_no
  )
ORDER BY c.onboarded_at DESC
LIMIT 50;
```

## Explanation
NOT EXISTS correlated subquery: với mỗi KH, check xem có row nào trong beneficiaries không. Nếu không → trả về. Performance tốt hơn LEFT JOIN + WHERE b.cif_no IS NULL khi bảng lớn.
