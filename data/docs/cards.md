# cards

## 1. Mục đích bảng

Lưu thông tin thẻ ngân hàng (debit/credit) của khách hàng. Agent dùng bảng này để resolve thẻ khi user yêu cầu khóa/mở thẻ, thay đổi hạn mức, hoặc tra cứu giao dịch thẻ.

**Nhóm:** Master/reference data

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để agent biết khách hàng có những thẻ nào, trạng thái thẻ ra sao.
- Agent dùng bảng này để:
  - Resolve `card_id` khi user nói "khóa thẻ visa" hoặc "thẻ credit".
  - Kiểm tra hạn mức thẻ tín dụng (`credit_limit`, `available_limit`).
  - Xác định thẻ liên kết với tài khoản nào (`account_no`).
- Phục vụ use case: khóa/mở thẻ (CARD_LOCK/CARD_UNLOCK), thay đổi hạn mức (CARD_LIMIT_CHANGE), tra cứu giao dịch thẻ.
- Bảng này **không lưu** lịch sử giao dịch thẻ (xem `transactions` với `card_id`).
- `masked_card_no` dùng để hiển thị cho user (không lộ số thẻ đầy đủ).

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| card_id | UUID string | ID kỹ thuật thẻ | `5943f137-22d2-5650-b80e-98c1cfb2031c` | No | PK | Dùng trong API payload khi khóa/mở thẻ |
| cif_no | string | Mã khách hàng sở hữu thẻ | `CIF000081`, `CIF000066`, `CIF000006` | No | FK → customers.cif_no | Filter thẻ theo khách hàng |
| account_no | string | Số tài khoản liên kết | `25579415521`, `92644220969`, `4124782613` | No | FK → accounts.account_no | Thẻ debit liên kết tài khoản thanh toán, credit liên kết settlement |
| masked_card_no | string | Số thẻ đã mask | `**** **** **** 7069`, `**** **** **** 7899` | Yes | - | Hiển thị cho user để nhận diện thẻ |
| card_type | enum string | Loại thẻ | `DEBIT`, `CREDIT` | Yes | - | Thẻ ghi nợ hoặc tín dụng |
| card_network | enum string | Mạng thẻ | `VISA`, `MASTERCARD`, `NAPAS` | Yes | - | Dùng khi user nói "thẻ visa", "thẻ mastercard" |
| credit_limit | numeric | Hạn mức tín dụng | `178121391` | Yes | - | Chỉ có giá trị với thẻ CREDIT |
| available_limit | numeric | Hạn mức khả dụng còn lại | `157240687` | Yes | - | Chỉ có giá trị với thẻ CREDIT |
| status | enum string | Trạng thái thẻ | `ACTIVE`, `LOCKED`, `EXPIRED` | Yes | - | Agent cần check trước khi thực hiện action |
| issued_at | timestamp string | Ngày phát hành thẻ | `2025-09-01 00:59:29`, `2025-11-11 23:20:27` | Yes | - | - |

## 4. Important Values / Enums

| Column | Value | Meaning | Example Use Case |
|---|---|---|---|
| card_type | DEBIT | Thẻ ghi nợ | Giao dịch trừ trực tiếp từ tài khoản |
| card_type | CREDIT | Thẻ tín dụng | Giao dịch dùng hạn mức, trả sau |
| card_network | VISA | Mạng VISA quốc tế | User nói "khóa thẻ visa" |
| card_network | MASTERCARD | Mạng Mastercard quốc tế | User nói "thẻ mastercard" |
| card_network | NAPAS | Mạng nội địa NAPAS | Thẻ ATM nội địa |
| status | ACTIVE | Thẻ đang hoạt động | Cho phép giao dịch, có thể khóa |
| status | LOCKED | Thẻ đã khóa | Có thể mở khóa |
| status | EXPIRED | Thẻ hết hạn | Không thể sử dụng |

## 5. Relationships

- `cards.cif_no` → `customers.cif_no`
- `cards.account_no` → `accounts.account_no`
- `cards.card_id` được tham chiếu bởi `transactions.card_id`

## 6. Simple Usage Examples

### Lấy tất cả thẻ của khách hàng

```sql
SELECT card_id, masked_card_no, card_type, card_network, status
FROM cards
WHERE cif_no = 'CIF000001';
```

Dùng khi agent cần liệt kê thẻ để user chọn khi yêu cầu khóa/mở thẻ.

### Tìm thẻ VISA đang active

```sql
SELECT card_id, masked_card_no, card_type, status
FROM cards
WHERE cif_no = 'CIF000066' AND card_network = 'VISA' AND status = 'ACTIVE';
```

Dùng khi user nói "khóa thẻ visa" — agent resolve card_id từ đây.

### Kiểm tra hạn mức thẻ tín dụng

```sql
SELECT card_id, masked_card_no, credit_limit, available_limit
FROM cards
WHERE cif_no = 'CIF000066' AND card_type = 'CREDIT';
```

Dùng khi user hỏi "còn bao nhiêu hạn mức thẻ tín dụng".

### Tìm thẻ đang bị khóa

```sql
SELECT card_id, masked_card_no, card_type, card_network
FROM cards
WHERE cif_no = 'CIF000066' AND status = 'LOCKED';
```

Dùng khi user yêu cầu "mở khóa thẻ" — agent cần biết thẻ nào đang locked.
