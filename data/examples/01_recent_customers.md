# Danh sách khách hàng mới đăng ký gần đây

## Complexity: simple

## Tables Used: customers

## Question (Vietnamese)
Cho tôi danh sách 10 khách hàng đăng ký mới nhất, bao gồm tên, số điện thoại và mức KYC.

## Join Logic
- Chỉ cần bảng `customers` vì tất cả thông tin yêu cầu (tên, SĐT, KYC, thời điểm đăng ký) đều nằm trong 1 bảng.
- Không cần JOIN vì không hỏi về tài khoản, giao dịch hay thẻ.
- Sắp xếp theo `created_at DESC` để lấy khách hàng mới nhất.

## SQL
```sql
SELECT
    cif_no,
    full_name,
    phone_number,
    kyc_level,
    status,
    created_at
FROM customers
ORDER BY created_at DESC
LIMIT 10;
```

## Explanation
Query đơn giản trên 1 bảng, sắp xếp theo ngày tạo giảm dần để lấy 10 bản ghi mới nhất. Không cần filter vì muốn xem tất cả trạng thái.
