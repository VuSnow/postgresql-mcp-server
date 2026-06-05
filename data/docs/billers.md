# billers

## 1. Mục đích bảng

Lưu danh sách nhà cung cấp dịch vụ thanh toán hóa đơn (điện, nước, internet, điện thoại trả sau). Agent dùng bảng này để resolve biller khi user yêu cầu thanh toán hóa đơn.

**Nhóm:** Master/reference data

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để agent biết có những nhà cung cấp dịch vụ nào trong hệ thống.
- Agent dùng bảng này để:
  - Resolve `biller_id` khi user nói "thanh toán tiền điện" hoặc "trả hóa đơn internet".
  - Join với `customer_biller_accounts` để tìm mã khách hàng hóa đơn.
  - Validate biller có active không trước khi tạo payload.
- Phục vụ use case: thanh toán hóa đơn (BILL_PAYMENT).
- Bảng này **không lưu** thông tin khách hàng đăng ký với biller — xem `customer_biller_accounts`.
- `biller_code` là mã unique dùng để tham chiếu trong API payload.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| biller_id | UUID string | ID kỹ thuật biller | `561cbccd-d404-5833-a5e8-ba6158e9d5a7` | No | PK | Dùng làm FK |
| biller_code | string | Mã biller unique | `EVN_HANOI`, `EVN_HCMC`, `EVN_DANANG`, `EVN_SOUTH` | No | Unique | Dùng trong API payload |
| biller_name | string | Tên hiển thị | `EVN Ha Noi`, `EVN Ho Chi Minh`, `EVN Da Nang` | No | - | Hiển thị cho user xác nhận |
| biller_type | enum string | Loại dịch vụ | `ELECTRICITY`, `WATER`, `INTERNET`, `PHONE_POSTPAID` | Yes | - | Dùng resolve khi user nói "tiền điện", "tiền nước" |
| provider | string | Nhà cung cấp gốc | `EVN`, `SAWACO`, `FPT`, `VNPT`, `VIETTEL` | Yes | - | Phân biệt chi nhánh cùng loại |
| status | enum string | Trạng thái | `ACTIVE`, `INACTIVE` | Yes | - | Chỉ biller ACTIVE mới dùng được |

## 4. Important Values / Enums

| Column | Value | Meaning | Example Use Case |
|---|---|---|---|
| biller_type | ELECTRICITY | Điện | User nói "thanh toán tiền điện" |
| biller_type | WATER | Nước | User nói "trả tiền nước" |
| biller_type | INTERNET | Internet | User nói "thanh toán internet" |
| biller_type | PHONE_POSTPAID | Điện thoại trả sau | User nói "trả cước điện thoại" |

## 5. Relationships

- `billers.biller_id` được tham chiếu bởi:
  - `customer_biller_accounts.biller_id`
  - `transactions.biller_id`

## 6. Simple Usage Examples

### Tìm biller theo loại dịch vụ

```sql
SELECT biller_id, biller_code, biller_name, provider
FROM billers
WHERE biller_type = 'ELECTRICITY' AND status = 'ACTIVE';
```

Dùng khi user nói "thanh toán tiền điện" — agent liệt kê các biller điện.

### Tìm biller theo tên/provider

```sql
SELECT biller_id, biller_code, biller_name, biller_type
FROM billers
WHERE biller_name ILIKE '%FPT%' AND status = 'ACTIVE';
```

Dùng khi user nói "trả tiền internet FPT".

### Lấy thông tin biller theo code

```sql
SELECT biller_id, biller_name, biller_type, provider
FROM billers
WHERE biller_code = 'EVN_HANOI';
```

Dùng khi đã biết biller_code từ customer_biller_accounts.
