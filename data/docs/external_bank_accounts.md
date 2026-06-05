# external_bank_accounts

## 1. Mục đích bảng

Lưu trữ thông tin tài khoản tại các ngân hàng bên ngoài (không phải SHB). Bảng này mô phỏng kết quả tra cứu qua hệ thống Napas/IBFT — khi user chuyển khoản liên ngân hàng, hệ thống dùng bảng này để xác minh chủ tài khoản nhận.

**Nhóm:** Core banking / Inter-bank transfer

## 2. Ngữ cảnh nghiệp vụ

- Đây là bảng **directory** chứa thông tin tài khoản tại ngân hàng khác (VCB, TCB, BIDV, MBB, v.v.).
- Khi user chuyển khoản liên ngân hàng, agent tra cứu bảng này theo (account_no, bank_code) để lấy tên chủ tài khoản.
- Mô phỏng quá trình gọi API Napas thực tế trong banking — thay vì gọi API thật, agent query bảng này.
- Không chứa tài khoản nội bộ SHB (tài khoản SHB nằm trong bảng `accounts`).
- Khác với `reported_accounts` (chỉ chứa tài khoản bị báo cáo) — bảng này chứa **mọi** tài khoản ngoại đã từng được tra cứu.
- Dùng kết hợp với `beneficiaries` — user có thể lưu tài khoản từ bảng này vào danh bạ.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| id | serial | ID auto-increment | `1`, `2`, `3` | No | PK | - |
| account_no | string | Số tài khoản | `90311860909`, `0904298565` | No | Unique(account_no, bank_code) | Số TK tại bank đích |
| account_holder_name | string | Tên chủ tài khoản | `Tran Ngoc Phuc`, `Do Thanh Dung` | No | - | Tên chính thức từ ngân hàng |
| bank_code | string | Mã ngân hàng | `VCB`, `TCB`, `BIDV`, `MBB`, `ACB` | No | - | Mã Swift/Citad rút gọn |
| bank_name | string | Tên ngân hàng đầy đủ | `Vietcombank`, `Techcombank`, `BIDV` | No | - | Tên hiển thị cho user |
| id_number | string | Số CMND/CCCD chủ TK | `051460863137` | Yes | - | Để verify, có thể NULL |
| phone | string | SĐT liên kết | `0865085624` | Yes | - | SĐT đăng ký tại ngân hàng |
| status | enum string | Trạng thái tài khoản | `ACTIVE`, `CLOSED`, `SUSPENDED` | No | - | Chỉ cho phép chuyển khi ACTIVE |
| created_at | timestamp | Thời điểm tạo record | `2024-05-27 00:45:48` | No | - | Thời điểm đăng ký/tra cứu đầu tiên |

## 4. Important Values / Enums

### status

| Value | Meaning | Transfer Allowed |
|---|---|---|
| ACTIVE | Tài khoản đang hoạt động | Có |
| CLOSED | Tài khoản đã đóng | Không |
| SUSPENDED | Tài khoản tạm khóa | Không |

### bank_code (common values)

| Code | Bank Name |
|---|---|
| VCB | Vietcombank |
| TCB | Techcombank |
| BIDV | BIDV |
| MBB | MB Bank |
| ACB | ACB |
| CTG | VietinBank |
| VPB | VPBank |
| TPB | TPBank |
| STB | Sacombank |
| HDB | HDBank |
| EIB | Eximbank |
| VIB | VIB |
| MSB | Maritime Bank |
| OCB | OCB |
| LPB | LienVietPostBank |

## 5. Relationships

- **→ beneficiaries**: User có thể lưu tài khoản từ bảng này vào danh bạ (`beneficiaries.beneficiary_account_no` = `external_bank_accounts.account_no`)
- **→ transactions**: Giao dịch liên ngân hàng tham chiếu tài khoản trong bảng này (`transactions.counterparty_account` = `external_bank_accounts.account_no`)
- **← reported_accounts**: Một số tài khoản trong bảng này cũng có thể xuất hiện trong `reported_accounts` nếu bị báo cáo lừa đảo

## 6. Common Query Patterns

### Tra cứu chủ tài khoản nhận (transfer verification)
```sql
SELECT account_holder_name, bank_name, status
FROM external_bank_accounts
WHERE account_no = '...' AND bank_code = '...'
```

### Kiểm tra tài khoản có active không trước khi chuyển
```sql
SELECT account_no, account_holder_name, status
FROM external_bank_accounts
WHERE account_no = '...' AND bank_code = '...' AND status = 'ACTIVE'
```

### Đếm tài khoản theo ngân hàng
```sql
SELECT bank_code, bank_name, COUNT(*) AS account_count
FROM external_bank_accounts
WHERE status = 'ACTIVE'
GROUP BY bank_code, bank_name
ORDER BY account_count DESC
```

## 7. Lưu ý quan trọng

- Composite key là (account_no, bank_code) — cùng account_no có thể tồn tại ở 2 bank khác nhau.
- Bảng này KHÔNG chứa tài khoản SHB (bank_code != 'SHB'). Tài khoản SHB nằm trong bảng `accounts`.
- Khi transfer verification, luôn check status = 'ACTIVE' trước khi cho phép chuyển.
- Cột `id_number` và `phone` chứa PII — cần cẩn thận khi query/hiển thị.
