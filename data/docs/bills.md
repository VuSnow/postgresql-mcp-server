# bills

## 1. Mục đích bảng

Lưu hóa đơn cụ thể từng kỳ (tháng) mà khách hàng cần thanh toán. Mỗi row là một hóa đơn: điện tháng 5, internet tháng 6, v.v.

**Nhóm:** Transactional data (bill payment)

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để biết khách hàng đang **nợ bao nhiêu** cho từng dịch vụ, từng kỳ.
- Khác với `billers` (danh sách nhà cung cấp) và `customer_biller_accounts` (đăng ký dịch vụ):
  - `billers` = "Có những nhà cung cấp nào?" (EVN, FPT, VNPT...)
  - `customer_biller_accounts` = "User đăng ký dịch vụ nào, mã KH là gì?"
  - `bills` = "Kỳ này phải trả bao nhiêu? Đã trả chưa?"
- Agent dùng bảng này để:
  - Tự động điền số tiền khi user nói "thanh toán tiền điện" (lấy `amount_due` từ bill UNPAID)
  - Kiểm tra hóa đơn đã thanh toán chưa trước khi tạo draft
  - Liệt kê hóa đơn sắp đến hạn
  - Tổng hợp chi tiêu dịch vụ theo kỳ
- Link bảng: `bills.biller_code` → `billers.biller_code`, `bills.customer_bill_code` → `customer_biller_accounts.customer_bill_code`

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| bill_id | UUID | ID hóa đơn | `b001a1a1-1111-4000-a001-000000000001` | No | PK | - |
| biller_code | string | Mã nhà cung cấp | `EVN_HANOI`, `EVN_CENTRAL`, `VNPT_NET_HCM`, `SAWACO` | No | FK → billers.biller_code | Xác định nhà cung cấp |
| customer_bill_code | string | Mã KH tại biller | `PD867472238`, `PI945489578`, `PP986082452` | No | FK → customer_biller_accounts.customer_bill_code | Xác định KH nào |
| bill_period | string | Kỳ thanh toán | `2026-05`, `2026-04`, `2026-06` | No | - | Format: YYYY-MM |
| amount_due | numeric | Số tiền cần trả | `487000`, `220000`, `1245000`, `352000` | No | - | Đơn vị VND |
| due_date | date | Hạn thanh toán | `2026-06-10`, `2026-06-15`, `2026-06-20` | Yes | - | Quá hạn = trễ |
| status | enum string | Trạng thái | `UNPAID`, `PAID`, `CANCELLED` | No | - | Chỉ bill UNPAID mới cho thanh toán |
| created_at | timestamp | Ngày tạo hóa đơn | `2026-05-25 08:00:00` | No | - | Khi nhà cung cấp phát hành |
| paid_at | timestamp | Ngày thanh toán | `2026-05-05 14:23:11`, NULL | Yes | - | NULL = chưa trả |

## 4. Important Values / Enums

### status

| Value | Meaning | Cho phép thanh toán |
|---|---|---|
| UNPAID | Chưa thanh toán | Có |
| PAID | Đã thanh toán | Không |
| CANCELLED | Đã hủy | Không |

### Prefix customer_bill_code

| Prefix | Biller Type | Ví dụ |
|---|---|---|
| PD | Điện (ELECTRICITY) | PD867472238 |
| PW | Nước (WATER) | PW112233445 |
| PI | Internet | PI945489578 |
| PP | Điện thoại trả sau (PHONE_POSTPAID) | PP986082452 |

## 5. Relationships

- `bills.biller_code` → `billers.biller_code` (xác định nhà cung cấp)
- `bills.customer_bill_code` → `customer_biller_accounts.customer_bill_code` (xác định khách hàng)
- Qua `customer_biller_accounts.cif_no` → `customers.cif_no` (filter theo user)

## 6. Common Query Patterns

### Tìm hóa đơn chưa thanh toán của user (qua customer_biller_accounts)
```sql
SELECT b.bill_id, b.biller_code, b.customer_bill_code, b.bill_period,
       b.amount_due, b.due_date, bl.biller_name, bl.biller_type, cba.alias
FROM bills b
JOIN customer_biller_accounts cba ON b.customer_bill_code = cba.customer_bill_code
JOIN billers bl ON b.biller_code = bl.biller_code
WHERE cba.cif_no = 'CIF000001'
  AND b.status = 'UNPAID'
ORDER BY b.due_date ASC;
```

### Tìm hóa đơn điện chưa trả
```sql
SELECT b.bill_period, b.amount_due, b.due_date, bl.biller_name, cba.alias
FROM bills b
JOIN billers bl ON b.biller_code = bl.biller_code
JOIN customer_biller_accounts cba ON b.customer_bill_code = cba.customer_bill_code
WHERE cba.cif_no = 'CIF000001'
  AND bl.biller_type = 'ELECTRICITY'
  AND b.status = 'UNPAID';
```

### Tổng tiền hóa đơn đã trả trong tháng
```sql
SELECT SUM(b.amount_due) AS total_paid, COUNT(*) AS bill_count
FROM bills b
JOIN customer_biller_accounts cba ON b.customer_bill_code = cba.customer_bill_code
WHERE cba.cif_no = 'CIF000001'
  AND b.status = 'PAID'
  AND b.paid_at >= '2026-05-01';
```

### Hóa đơn sắp đến hạn (trong 7 ngày tới)
```sql
SELECT b.biller_code, bl.biller_name, cba.alias, b.amount_due, b.due_date
FROM bills b
JOIN billers bl ON b.biller_code = bl.biller_code
JOIN customer_biller_accounts cba ON b.customer_bill_code = cba.customer_bill_code
WHERE cba.cif_no = 'CIF000001'
  AND b.status = 'UNPAID'
  AND b.due_date <= CURRENT_DATE + INTERVAL '7 days'
ORDER BY b.due_date ASC;
```

### Lịch sử thanh toán theo loại dịch vụ
```sql
SELECT bl.biller_type, bl.biller_name, b.bill_period, b.amount_due, b.paid_at
FROM bills b
JOIN billers bl ON b.biller_code = bl.biller_code
JOIN customer_biller_accounts cba ON b.customer_bill_code = cba.customer_bill_code
WHERE cba.cif_no = 'CIF000002'
  AND b.status = 'PAID'
ORDER BY b.paid_at DESC
LIMIT 10;
```

## 7. Lưu ý quan trọng

- Composite lookup key: (biller_code, customer_bill_code, status) — có index.
- Mỗi kỳ (bill_period) mỗi customer_bill_code chỉ có 1 bill.
- `amount_due` luôn > 0, đơn vị VND.
- Khi thanh toán xong, update `status = 'PAID'` và `paid_at = NOW()`.
- Nếu query hóa đơn "của user" → phải JOIN qua `customer_biller_accounts` vì `bills` không có trường `cif_no` trực tiếp.
