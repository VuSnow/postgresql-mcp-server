# Danh sách tài khoản và số dư của một khách hàng

## Complexity: medium

## Tables Used: customers, accounts

## Question (Vietnamese)
Khách hàng CIF000001 có bao nhiêu tài khoản? Liệt kê số tài khoản, loại tài khoản và số dư khả dụng.

## Join Logic
- Cần `customers` để xác định khách hàng theo `cif_no` (đảm bảo customer tồn tại).
- Cần `accounts` để lấy thông tin tài khoản (số TK, loại, số dư).
- **JOIN path**: `customers.cif_no = accounts.cif_no` — mỗi khách hàng có thể có nhiều tài khoản (1-to-many).
- Filter `accounts.status = 'ACTIVE'` để chỉ hiện tài khoản đang hoạt động.

## SQL
```sql
SELECT
    c.full_name,
    a.account_no,
    a.account_type,
    a.currency,
    a.balance,
    a.available_balance,
    a.status
FROM customers c
JOIN accounts a ON c.cif_no = a.cif_no
WHERE c.cif_no = 'CIF000001'
  AND a.status = 'ACTIVE'
ORDER BY a.account_type;
```

## Explanation
JOIN customers với accounts qua cif_no. Filter theo khách hàng cụ thể và chỉ lấy tài khoản ACTIVE. Sắp xếp theo loại tài khoản để dễ đọc. Không cần LIMIT vì mỗi KH thường chỉ có 2-3 tài khoản.
