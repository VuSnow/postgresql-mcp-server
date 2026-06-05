# reported_accounts

## 1. Mục đích bảng

Lưu trữ thông tin aggregate risk cho mỗi tài khoản bị báo cáo lừa đảo. Đây là bảng chính phục vụ **transaction screening**: khi user chuyển tiền, Guardian tra cứu tài khoản nhận trong bảng này để đánh giá rủi ro.

**Nhóm:** Fraud detection / transaction screening

## 2. Ngữ cảnh nghiệp vụ

- Bảng này là **read model aggregate** từ `fraud_reports`, tổng hợp risk signal cho từng tài khoản.
- Guardian dùng bảng này khi user yêu cầu chuyển tiền:
  - Lookup receiver_account_no → nếu match → trả risk_level.
  - risk_level HIGH/CRITICAL → cảnh báo hoặc block giao dịch.
- Agent dùng bảng này để:
  - Transaction screening trước khi execute transfer.
  - Trả lời "tài khoản này có an toàn không?".
  - Quyết định ALLOW / WARN / BLOCK trong `fraud_decisions`.
- Bảng này **không phải** danh sách tất cả tài khoản ngân hàng. Chỉ chứa tài khoản đã bị báo cáo ít nhất 1 lần.
- `account_no` là tài khoản **bên ngoài** hệ thống (tài khoản kẻ lừa đảo).

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| reported_account_id | UUID string | ID record | `f420f3a9-42b3-5536-9d7b-a7e0a3aec844` | No | PK | - |
| account_no | string | Số TK bị báo cáo | `43275604177`, `5347355289`, `0094318143` | No | Unique | Từ fraud_reports.reported_account_no |
| bank_code | string | Bank code | `ACB`, `VIB`, `VPB`, `CTG`, `VCB` | No | - | Từ BANK_MAP |
| linked_customer_cif | string | CIF chủ TK (nếu biết) | - | Yes | - | Link tới reported_customers |
| valid_report_count | integer | Số report hợp lệ | `1` | No | - | SUBMITTED + VALIDATED + CONFIRMED |
| unique_reporter_count | integer | Số người báo cáo khác nhau | `1` | No | - | Distinct reporter_cif_no |
| total_reported_amount | numeric | Tổng tiền bị báo cáo mất | `22238685`, `3198935`, `32520461` | No | - | VND |
| avg_confidence_score | numeric | TB confidence score | `80`, `70`, `50`, `100`, `65` | No | - | Trung bình từ fraud_reports |
| risk_score | numeric | Điểm risk (0.0-1.0) | `0.95`, `0.25` | No | - | Tính từ metrics |
| risk_level | enum string | Mức risk | `CRITICAL`, `LOW` | No | - | Quyết định screening |
| status | enum string | Trạng thái tài khoản | `ACTIVE` | No | - | Trạng thái monitoring |
| first_reported_at | timestamp string | Lần báo cáo đầu tiên | `2026-05-22 00:02:36` | No | - | - |
| last_reported_at | timestamp string | Lần báo cáo gần nhất | `2026-05-22 00:02:36` | No | - | >= first_reported_at |

## 4. Important Values / Enums

### risk_level

| Value | Meaning | Screening Action |
|---|---|---|
| LOW | Risk thấp (< 0.3) | ALLOW — cho phép chuyển |
| MEDIUM | Risk trung bình (0.3-0.6) | WARN — cảnh báo user |
| HIGH | Risk cao (0.6-0.8) | WARN/BLOCK — cảnh báo mạnh hoặc chặn |
| CRITICAL | Risk rất cao (>= 0.8) | BLOCK — chặn giao dịch |

### status

| Value | Meaning |
|---|---|
| ACTIVE | Đang monitoring |
| MONITORING | Theo dõi (risk thấp) |
| FLAGGED | Đã đánh dấu nghi vấn |
| BLOCKED | Bị chặn toàn bộ giao dịch đến |

## 5. Relationships

- `reported_accounts.account_no` ← aggregate từ `fraud_reports.reported_account_no`
- `reported_accounts.linked_customer_cif` → `reported_customers.cif_no`
- `reported_accounts.account_no` được tra cứu bởi `fraud_decisions.receiver_account_no`

## 6. Simple Usage Examples

### Transaction screening — check tài khoản nhận

```sql
SELECT account_no, bank_code, risk_level, risk_score, valid_report_count, status
FROM reported_accounts
WHERE account_no = '43275604177' AND bank_code = 'ACB';
```

Dùng khi Guardian check receiver account trước khi chuyển tiền.

### Danh sách tài khoản CRITICAL

```sql
SELECT account_no, bank_code, risk_score, total_reported_amount, valid_report_count
FROM reported_accounts
WHERE risk_level = 'CRITICAL'
ORDER BY risk_score DESC;
```

### Tìm tài khoản có nhiều reporter nhất

```sql
SELECT account_no, bank_code, unique_reporter_count, total_reported_amount
FROM reported_accounts
ORDER BY unique_reporter_count DESC
LIMIT 5;
```

### Check tài khoản có an toàn không

```sql
SELECT account_no, bank_code, risk_level, risk_score,
       valid_report_count, unique_reporter_count, total_reported_amount
FROM reported_accounts
WHERE account_no = '8812520566';
```
