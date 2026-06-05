# customers

## 1. Mục đích bảng

Lưu thông tin master data khách hàng cá nhân trong hệ thống banking agent. Đây là bảng gốc để xác định danh tính khách hàng khi agent xử lý yêu cầu.

**Nhóm:** Master/reference data

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để agent biết khách hàng nào đang tương tác, dựa trên `cif_no`.
- Agent dùng bảng này để xác minh danh tính khách hàng, kiểm tra trạng thái tài khoản (ACTIVE/SUSPENDED/CLOSED), và lấy thông tin liên lạc.
- Phục vụ use case: xác thực customer context trước khi thực thi bất kỳ workflow nào (chuyển tiền, thanh toán, khóa thẻ...).
- Bảng này **không phải** bảng giao dịch. Không lưu lịch sử hành vi hay số dư.
- `cif_no` là khóa nghiệp vụ chính, được dùng xuyên suốt toàn bộ hệ thống để liên kết khách hàng với accounts, cards, transactions, action_requests, audit_logs.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| customer_id | UUID string | ID kỹ thuật duy nhất của khách hàng | `7650a268-4eb3-51ea-ab03-4f6c2ff80501` | No | PK | Không dùng trong business logic, chỉ dùng làm primary key |
| cif_no | string | Mã khách hàng nghiệp vụ (Customer Information File) | `CIF000001`, `CIF000002`, `CIF000003` | No | Unique | Khóa nghiệp vụ chính, được tham chiếu bởi hầu hết các bảng khác |
| full_name | string | Họ tên đầy đủ khách hàng | `Tran Van Lan`, `Do Huu An`, `Pham Thanh Dung` | No | - | Dùng để hiển thị, xác nhận danh tính |
| phone_number | string | Số điện thoại | `0733218196`, `0386379402`, `0961559407` | Yes | - | Dùng cho OTP, liên lạc |
| email | string | Email | `tran.van.lan@example.com`, `do.huu.an@example.com` | Yes | - | Dùng cho thông báo |
| kyc_level | enum string | Mức xác minh KYC | `BASIC`, `VERIFIED`, `ENHANCED` | Yes | - | Ảnh hưởng đến hạn mức giao dịch và permission |
| status | enum string | Trạng thái khách hàng | `ACTIVE`, `SUSPENDED`, `CLOSED` | Yes | - | Agent chỉ xử lý yêu cầu cho khách hàng ACTIVE |
| created_at | timestamp string | Thời điểm tạo bản ghi | `2023-12-28 10:13:36`, `2023-08-30 12:41:45` | Yes | - | - |

## 4. Important Values / Enums

| Column | Value | Meaning | Example Use Case |
|---|---|---|---|
| kyc_level | BASIC | Xác minh cơ bản, hạn mức thấp | Giới hạn số tiền chuyển khoản/ngày |
| kyc_level | VERIFIED | Đã xác minh đầy đủ CMND/CCCD | Cho phép giao dịch hạn mức trung bình |
| kyc_level | ENHANCED | Xác minh nâng cao (video call, eKYC) | Cho phép giao dịch hạn mức cao |
| status | ACTIVE | Đang hoạt động | Agent xử lý yêu cầu bình thường |
| status | SUSPENDED | Tạm khóa | Agent từ chối mọi yêu cầu giao dịch |
| status | CLOSED | Đã đóng | Agent từ chối mọi yêu cầu |

## 5. Relationships

- `customers.cif_no` được tham chiếu bởi:
  - `accounts.cif_no`
  - `cards.cif_no`
  - `beneficiaries.cif_no`
  - `customer_biller_accounts.cif_no`
  - `transactions.cif_no`
  - `action_requests.cif_no`
  - `audit_logs.cif_no`

## 6. Simple Usage Examples

### Lấy thông tin khách hàng theo CIF

```sql
SELECT customer_id, cif_no, full_name, phone_number, kyc_level, status
FROM customers
WHERE cif_no = 'CIF000001';
```

Dùng khi agent cần xác minh danh tính khách hàng đang tương tác.

### Kiểm tra khách hàng có đang active không

```sql
SELECT cif_no, full_name, status
FROM customers
WHERE cif_no = 'CIF000001' AND status = 'ACTIVE';
```

Dùng trước khi thực thi bất kỳ action nào — chỉ cho phép khách hàng ACTIVE.

### Tìm khách hàng theo tên

```sql
SELECT cif_no, full_name, phone_number
FROM customers
WHERE full_name ILIKE '%Tran%';
```

Dùng khi cần tìm kiếm khách hàng theo tên (ít dùng trong agent flow, chủ yếu cho admin).
