# beneficiaries

## 1. Mục đích bảng

Lưu danh sách người nhận chuyển tiền đã lưu của khách hàng. Agent dùng bảng này để resolve người nhận khi user yêu cầu chuyển tiền bằng tên gọi, nickname, hoặc thông tin không đầy đủ.

**Nhóm:** Master/reference data

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để agent có thể "nhận diện" người nhận khi user nói "chuyển cho Bình" hoặc "chuyển tiền nhà".
- Agent dùng bảng này để:
  - Resolve `beneficiary_account_no`, `beneficiary_bank_code` từ tên/nickname user cung cấp.
  - Tạo API payload cho `external_transfer_api`.
  - Xác nhận lại với user: "Bạn muốn chuyển cho Nguyen Ngoc Binh - Sacombank?".
- Phục vụ use case: chuyển tiền (TRANSFER) — bước recipient resolution.
- Bảng này **không phải** danh bạ toàn hệ thống. Mỗi khách hàng có danh sách riêng (filter bằng `cif_no`).
- `is_saved = True` nghĩa là người nhận đã được lưu, agent ưu tiên match từ đây.
- `last_used_at` giúp agent ưu tiên người nhận gần đây nhất khi có nhiều kết quả trùng.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| beneficiary_id | UUID string | ID kỹ thuật người nhận | `4ac78c04-ea5a-5990-973d-52f58e78f498` | No | PK | Dùng làm FK trong transactions |
| cif_no | string | Mã khách hàng sở hữu danh sách | `CIF000001`, `CIF000002` | No | FK → customers.cif_no | Mỗi customer có list riêng |
| beneficiary_name | string | Tên người nhận | `Bui Duc Tuan`, `Nguyen Ngoc Binh`, `Dang Duc Em` | No | - | Dùng để match khi user nói tên |
| beneficiary_account_no | string | Số tài khoản người nhận | `9409610556`, `805892583206`, `179086416862` | Yes | - | Đưa vào API payload `to_account_no` |
| beneficiary_bank_code | string | Mã ngân hàng người nhận | `ACB`, `STB`, `BIDV`, `CTG` | Yes | - | Đưa vào API payload `to_bank_code` |
| beneficiary_bank_name | string | Tên ngân hàng người nhận | `ACB`, `Sacombank`, `BIDV`, `VietinBank` | Yes | - | Hiển thị cho user xác nhận |
| nickname | string | Tên gọi tắt/alias | `Tien nha`, `Tien hoc` | Yes | - | User có thể dùng nickname thay vì tên thật |
| is_saved | boolean | Đã lưu vào danh sách | `True` | Yes | - | Agent ưu tiên người nhận đã saved |
| last_used_at | timestamp string | Lần cuối sử dụng | `2026-02-22 20:57:58`, `2026-01-08 01:53:20` | Yes | - | Dùng để rank kết quả khi có nhiều match |
| created_at | timestamp string | Thời điểm lưu | `2025-12-22 15:25:56`, `2024-08-24 03:53:39` | Yes | - | - |

## 4. Important Values / Enums

Không có enum quan trọng.

Lưu ý: `beneficiary_bank_code` không phải enum cố định — có thể là bất kỳ mã ngân hàng nào (ACB, STB, BIDV, CTG, VIB, TCB, TPB, MB...).

## 5. Relationships

- `beneficiaries.cif_no` → `customers.cif_no`
- `beneficiaries.beneficiary_id` được tham chiếu bởi `transactions.beneficiary_id`

## 6. Simple Usage Examples

### Tìm người nhận theo tên (fuzzy match)

```sql
SELECT beneficiary_id, beneficiary_name, beneficiary_account_no, beneficiary_bank_name, nickname
FROM beneficiaries
WHERE cif_no = 'CIF000001' AND beneficiary_name ILIKE '%Binh%';
```

Dùng khi user nói "chuyển cho Bình" — agent tìm trong danh sách đã lưu.

### Tìm người nhận theo nickname

```sql
SELECT beneficiary_id, beneficiary_name, beneficiary_account_no, beneficiary_bank_code
FROM beneficiaries
WHERE cif_no = 'CIF000001' AND nickname ILIKE '%nha%';
```

Dùng khi user nói "chuyển tiền nhà" — agent match nickname.

### Lấy người nhận gần đây nhất

```sql
SELECT beneficiary_id, beneficiary_name, beneficiary_account_no, beneficiary_bank_name
FROM beneficiaries
WHERE cif_no = 'CIF000001' AND is_saved = True
ORDER BY last_used_at DESC NULLS LAST
LIMIT 5;
```

Dùng khi có nhiều kết quả — ưu tiên người nhận sử dụng gần nhất.

### Lấy đầy đủ thông tin để tạo API payload

```sql
SELECT beneficiary_name, beneficiary_account_no, beneficiary_bank_code
FROM beneficiaries
WHERE beneficiary_id = '8ce5b028-4d19-5ea3-8316-15b336b9c8fa';
```

Dùng sau khi đã resolve beneficiary_id — lấy thông tin đưa vào `external_transfer_api` payload.
