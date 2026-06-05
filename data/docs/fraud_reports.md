# fraud_reports

## 1. Mục đích bảng

Lưu trữ các báo cáo lừa đảo (fraud report) do khách hàng gửi. Khi user phát hiện bị lừa đảo qua giao dịch chuyển tiền, agent tiếp nhận thông tin và tạo fraud report.

**Nhóm:** Fraud detection / transaction screening

## 2. Ngữ cảnh nghiệp vụ

- Bảng này là **đầu vào** của hệ thống fraud detection.
- Khi user báo cáo bị lừa đảo, FraudReportAgent tạo record ở đây.
- Dữ liệu được aggregate lên `reported_accounts` và `reported_customers` để phục vụ transaction screening.
- Agent dùng bảng này để:
  - Tiếp nhận báo cáo lừa đảo từ user.
  - Tra cứu lịch sử báo cáo cho 1 tài khoản.
  - Xác minh/reject report (status lifecycle).
- Bảng này **không phải** nơi ra quyết định chặn giao dịch. Quyết định screening nằm ở `fraud_decisions`.
- `reported_account_no` là tài khoản **bên ngoài** hệ thống (tài khoản kẻ lừa đảo), không cần tồn tại trong bảng `accounts`.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| report_id | UUID string | ID báo cáo | `1c2372a8-ef70-5c8c-b6a0-d321c8b22f2e` | No | PK | - |
| reporter_cif_no | string | CIF người báo cáo | `CIF000032`, `CIF000051`, `CIF000088` | No | FK → customers.cif_no | Phải là ACTIVE customer |
| transaction_ref | string | Mã giao dịch liên quan | `TXN202603001513`, `TXN202602000633` | Yes | FK → transactions.transaction_ref | Giao dịch mà user bị lừa |
| reported_account_no | string | Số TK bị báo cáo | `43275604177`, `5347355289`, `0094318143` | No | - | TK kẻ lừa đảo (bên ngoài hệ thống) |
| reported_bank_code | string | Bank code TK bị báo | `ACB`, `VIB`, `VPB`, `CTG`, `VCB` | No | - | Từ BANK_MAP |
| reported_customer_cif | string | CIF chủ TK bị báo | - | Yes | - | Nếu biết CIF kẻ lừa đảo |
| fraud_type | enum string | Loại lừa đảo | `ROMANCE_SCAM`, `LOAN_SCAM`, `INVESTMENT_SCAM`, `IMPERSONATION`, `OTHER` | No | - | Phân loại hình thức lừa đảo |
| contact_channel | enum string | Kênh liên lạc với kẻ lừa | `WEBSITE`, `ZALO`, `PHONE`, `OTHER` | No | - | Nơi user tiếp xúc kẻ lừa đảo |
| aftermath | enum string | Hậu quả | `LINK_GONE`, `ASKED_MORE_MONEY`, `BLOCKED_CONTACT`, `NO_GOODS`, `OTHER` | No | - | Tình trạng sau khi bị lừa |
| reason_text | text | Mô tả chi tiết | `Bi lua dao qua website, link gone` | No | - | Nội dung user mô tả |
| has_evidence | boolean | Có bằng chứng | `True`, `False` | No | - | Screenshot, chat log, etc. |
| confidence_score | numeric | Điểm tin cậy (0-100) | `80`, `70`, `50`, `100`, `65` | No | - | Agent/system đánh giá mức tin cậy |
| status | enum string | Trạng thái xử lý | `SUBMITTED`, `VALIDATED`, `CONFIRMED` | No | - | Lifecycle báo cáo |
| created_at | timestamp string | Thời điểm tạo | `2026-05-22 00:02:36`, `2026-05-01 16:39:44` | No | - | - |

## 4. Important Values / Enums

### fraud_type

| Value | Meaning | Example Use Case |
|---|---|---|
| ROMANCE_SCAM | Lừa đảo tình cảm | Quen qua mạng → xin tiền |
| LOAN_SCAM | Lừa đảo cho vay | Giả app cho vay → thu phí trước |
| INVESTMENT_SCAM | Lừa đảo đầu tư | Hứa lãi cao → chiếm đoạt tiền |
| IMPERSONATION | Giả danh | Giả công an / ngân hàng → yêu cầu chuyển tiền |
| OTHER | Khác | Không thuộc nhóm trên |

### contact_channel

| Value | Meaning |
|---|---|
| ZALO | Liên lạc qua Zalo |
| WEBSITE | Website giả / lừa đảo |
| PHONE | Gọi điện thoại |
| OTHER | Kênh khác (Facebook, Telegram...) |

### status

| Value | Meaning |
|---|---|
| SUBMITTED | Mới gửi, chưa xác minh |
| VALIDATED | Đã xác minh bước đầu |
| CONFIRMED | Đã xác nhận là lừa đảo |
| REJECTED | Báo cáo không hợp lệ |

## 5. Relationships

- `fraud_reports.reporter_cif_no` → `customers.cif_no`
- `fraud_reports.transaction_ref` → `transactions.transaction_ref`
- `fraud_reports.reported_account_no` được aggregate lên `reported_accounts.account_no`
- `fraud_reports.reported_customer_cif` được aggregate lên `reported_customers.cif_no`

## 6. Simple Usage Examples

### Xem tất cả báo cáo lừa đảo của 1 khách hàng

```sql
SELECT report_id, fraud_type, reported_account_no, reported_bank_code, status, created_at
FROM fraud_reports
WHERE reporter_cif_no = 'CIF000032'
ORDER BY created_at DESC;
```

### Đếm số report cho 1 tài khoản bị báo cáo

```sql
SELECT reported_account_no, reported_bank_code, COUNT(*) AS report_count
FROM fraud_reports
WHERE reported_account_no = '43275604177'
GROUP BY reported_account_no, reported_bank_code;
```

### Tìm báo cáo đã xác nhận gần đây

```sql
SELECT report_id, reporter_cif_no, fraud_type, reason_text, confidence_score
FROM fraud_reports
WHERE status = 'CONFIRMED'
ORDER BY created_at DESC
LIMIT 5;
```

### Tra cứu report liên quan đến 1 giao dịch

```sql
SELECT *
FROM fraud_reports
WHERE transaction_ref = 'TXN202603001513';
```
