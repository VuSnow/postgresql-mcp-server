# customer_biller_accounts

## 1. Mục đích bảng

Lưu mapping giữa khách hàng ngân hàng và mã khách hàng tại các nhà cung cấp dịch vụ (biller). Ví dụ: khách hàng CIF000001 có mã hóa đơn điện PD867472238 tại EVN.

**Nhóm:** Master/reference data

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để agent resolve được mã hóa đơn (`customer_bill_code`) khi user yêu cầu thanh toán.
- Agent dùng bảng này để:
  - Tìm `customer_bill_code` khi user nói "thanh toán tiền điện" — không cần user nhớ mã.
  - Tạo API payload cho `external_bill_payment_api` (cần `customer_bill_code` + `biller_id`).
  - Hiển thị alias cho user xác nhận: "Thanh toán tiền điện - Nhà Hà Nội?".
- Phục vụ use case: thanh toán hóa đơn (BILL_PAYMENT) — bước biller resolution.
- `alias` là tên gọi user tự đặt, giúp agent match khi user nói "tiền điện nhà Hà Nội".
- `last_paid_at` cho biết lần cuối thanh toán — hữu ích để suggest hóa đơn cần trả.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| customer_biller_account_id | UUID string | ID kỹ thuật | `cc9c6130-5a30-5082-a79c-0d679825f36d` | No | PK | - |
| cif_no | string | Mã khách hàng ngân hàng | `CIF000001`, `CIF000002` | No | FK → customers.cif_no | Filter theo khách hàng |
| biller_id | UUID string | ID biller liên kết | `ecb27041-5475-5616-8e1f-fa9c73a0fa96` | No | FK → billers.biller_id | Join với billers để lấy tên/loại |
| customer_bill_code | string | Mã khách hàng tại biller | `PD867472238`, `PD989388663`, `PI945489578`, `PP986082452` | Yes | - | Đưa vào API payload |
| alias | string | Tên gợi nhớ do user đặt | `Nha Ha Noi`, `Internet nha`, `So phu` | Yes | - | Dùng match khi user nói alias |
| status | enum string | Trạng thái đăng ký | `ACTIVE`, `INACTIVE` | Yes | - | Chỉ active mới dùng thanh toán |
| last_paid_at | timestamp string | Lần cuối thanh toán | `2026-04-19 16:01:13`, `2026-02-02 19:22:48` | Yes | - | Null = chưa thanh toán lần nào |

## 4. Important Values / Enums

| Column | Value | Meaning | Example Use Case |
|---|---|---|---|
| status | ACTIVE | Đang sử dụng | Có thể thanh toán |
| status | INACTIVE | Ngưng sử dụng | Không hiển thị / không cho thanh toán |

Prefix mã `customer_bill_code`:
- `PD` — Power/Điện (ELECTRICITY)
- `PI` — Internet
- `PP` — Phone Postpaid
- `PW` — Water (example format)

## 5. Relationships

- `customer_biller_accounts.cif_no` → `customers.cif_no`
- `customer_biller_accounts.biller_id` → `billers.biller_id`

## 6. Simple Usage Examples

### Lấy danh sách hóa đơn đã đăng ký của khách hàng

```sql
SELECT cba.customer_bill_code, cba.alias, b.biller_name, b.biller_type, cba.last_paid_at
FROM customer_biller_accounts cba
JOIN billers b ON cba.biller_id = b.biller_id
WHERE cba.cif_no = 'CIF000001' AND cba.status = 'ACTIVE';
```

Dùng khi user hỏi "tôi có những hóa đơn nào" hoặc khi cần liệt kê để user chọn.

### Tìm mã hóa đơn điện của khách hàng

```sql
SELECT cba.customer_bill_code, cba.alias, b.biller_name
FROM customer_biller_accounts cba
JOIN billers b ON cba.biller_id = b.biller_id
WHERE cba.cif_no = 'CIF000002' AND b.biller_type = 'ELECTRICITY' AND cba.status = 'ACTIVE';
```

Dùng khi user nói "thanh toán tiền điện" — agent resolve bill_code từ đây.

### Tìm hóa đơn theo alias

```sql
SELECT cba.customer_bill_code, b.biller_name, b.biller_type
FROM customer_biller_accounts cba
JOIN billers b ON cba.biller_id = b.biller_id
WHERE cba.cif_no = 'CIF000002' AND cba.alias ILIKE '%internet%' AND cba.status = 'ACTIVE';
```

Dùng khi user nói "trả tiền internet nhà" — match alias.
