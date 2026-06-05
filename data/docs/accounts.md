# accounts

## 1. Mục đích bảng

Lưu thông tin tài khoản ngân hàng của khách hàng. Mỗi khách hàng có thể có nhiều tài khoản (thanh toán, tiết kiệm, settlement thẻ tín dụng). Đây là bảng agent dùng để xác định tài khoản nguồn khi thực hiện giao dịch.

**Nhóm:** Master/reference data

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để agent biết khách hàng có những tài khoản nào, số dư bao nhiêu, và tài khoản nào đang active.
- Agent dùng bảng này để:
  - Chọn tài khoản nguồn (`from_account_no`) khi tạo API payload chuyển tiền/thanh toán.
  - Kiểm tra số dư khả dụng (`available_balance`) trước khi confirm giao dịch.
  - Liệt kê danh sách tài khoản cho khách hàng chọn.
- Phục vụ use case: chuyển tiền, thanh toán hóa đơn, nạp điện thoại (đều cần `account_no` làm nguồn).
- Bảng này **không phải** ledger thật. Số dư là snapshot read model, không phải source of truth.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| account_id | UUID string | ID kỹ thuật tài khoản | `6d253ff0-49a0-528a-be58-111a54d53b11` | No | PK | - |
| account_no | string | Số tài khoản ngân hàng | `31243292127`, `9955271774490`, `411998679807` | No | Unique | Dùng trong API payload, hiển thị cho user |
| cif_no | string | Mã khách hàng sở hữu tài khoản | `CIF000001`, `CIF000002`, `CIF000003` | No | FK → customers.cif_no | Dùng để filter tài khoản theo khách hàng |
| account_type | enum string | Loại tài khoản | `PAYMENT`, `SAVINGS`, `CREDIT_CARD_SETTLEMENT` | Yes | - | Agent thường dùng tài khoản PAYMENT làm nguồn |
| currency | string | Đơn vị tiền tệ | `VND` | Yes | - | Mặc định VND |
| balance | numeric | Số dư hiện tại | `249582907`, `272874417`, `488542479` | Yes | - | Đơn vị: đồng (VND) |
| available_balance | numeric | Số dư khả dụng (trừ hold) | `240389988`, `234979964`, `474605528` | Yes | - | Agent kiểm tra field này trước khi confirm giao dịch |
| status | enum string | Trạng thái tài khoản | `ACTIVE`, `FROZEN`, `CLOSED` | Yes | - | Chỉ tài khoản ACTIVE mới dùng giao dịch được |
| opened_at | timestamp string | Thời điểm mở tài khoản | `2025-06-19 04:08:10`, `2023-02-28 10:05:59` | Yes | - | - |

## 4. Important Values / Enums

| Column | Value | Meaning | Example Use Case |
|---|---|---|---|
| account_type | PAYMENT | Tài khoản thanh toán | Dùng làm tài khoản nguồn chuyển tiền, thanh toán |
| account_type | SAVINGS | Tài khoản tiết kiệm | Không dùng giao dịch trực tiếp, chỉ hiển thị số dư |
| account_type | CREDIT_CARD_SETTLEMENT | Tài khoản quyết toán thẻ tín dụng | Liên kết với thẻ credit |
| status | ACTIVE | Đang hoạt động | Cho phép giao dịch |
| status | FROZEN | Bị đóng băng | Từ chối giao dịch, hiển thị cảnh báo |
| status | CLOSED | Đã đóng | Không hiển thị cho user |

## 5. Relationships

- `accounts.cif_no` → `customers.cif_no`
- `accounts.account_no` được tham chiếu bởi:
  - `cards.account_no`
  - `transactions.account_no`

## 6. Simple Usage Examples

### Lấy tất cả tài khoản active của khách hàng

```sql
SELECT account_no, account_type, balance, available_balance, status
FROM accounts
WHERE cif_no = 'CIF000001' AND status = 'ACTIVE';
```

Dùng khi agent cần liệt kê tài khoản để user chọn nguồn giao dịch.

### Kiểm tra số dư khả dụng trước khi chuyển tiền

```sql
SELECT account_no, available_balance
FROM accounts
WHERE account_no = '31243292127' AND status = 'ACTIVE';
```

Dùng trong bước validate trước khi tạo API payload.

### Lấy tài khoản thanh toán mặc định

```sql
SELECT account_no, balance, available_balance
FROM accounts
WHERE cif_no = 'CIF000001' AND account_type = 'PAYMENT' AND status = 'ACTIVE'
LIMIT 1;
```

Dùng khi user không chỉ định tài khoản nguồn — agent tự chọn tài khoản PAYMENT đầu tiên.
