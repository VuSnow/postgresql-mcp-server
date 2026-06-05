# Khách hàng không có giao dịch trong 30 ngày

## Complexity: complex

## Tables Used: customers, accounts, transactions

## Question (Vietnamese)
Tìm khách hàng ACTIVE có tài khoản thanh toán nhưng không phát sinh giao dịch nào trong 30 ngày gần đây.

## Join Logic
- Cần `customers` để lấy danh sách khách hàng ACTIVE.
- Cần `accounts` để đảm bảo KH có tài khoản thanh toán ACTIVE.
- Cần `transactions` để kiểm tra KHÔNG CÓ giao dịch — dùng NOT EXISTS.
- **JOIN path 1**: `customers.cif_no = accounts.cif_no`
- **Subquery**: NOT EXISTS (SELECT FROM transactions WHERE cif_no match AND time >= 30 days ago)

## SQL
```sql
SELECT DISTINCT
    c.cif_no,
    c.full_name,
    c.phone_number,
    c.created_at AS customer_since
FROM customers c
JOIN accounts a ON c.cif_no = a.cif_no
WHERE c.status = 'ACTIVE'
  AND a.account_type = 'PAYMENT'
  AND a.status = 'ACTIVE'
  AND NOT EXISTS (
      SELECT 1
      FROM transactions t
      WHERE t.cif_no = c.cif_no
        AND t.transaction_time >= CURRENT_DATE - INTERVAL '30 days'
  )
ORDER BY c.created_at
LIMIT 100;
```

## Explanation
Pattern "Tìm X không có Y" → NOT EXISTS subquery. DISTINCT vì 1 KH có thể có nhiều TK thanh toán → join duplicate rows. Sắp xếp theo created_at (KH cũ nhất trước).
