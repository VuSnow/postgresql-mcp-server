# transactions

## 1. Mục đích bảng

Lưu lịch sử giao dịch (read model) của khách hàng. Đây là bảng chính cho Text2SQL — agent query bảng này khi user hỏi về lịch sử chi tiêu, giao dịch gần đây, tìm kiếm giao dịch.

**Nhóm:** Read model / transaction history

## 2. Ngữ cảnh nghiệp vụ

- Đây là **lịch sử giao dịch / read model**. Dùng cho Text2SQL, phân tích chi tiêu, tìm người nhận cũ.
- **KHÔNG phải** core banking ledger. Không phải nơi agent thực thi giao dịch.
- Agent **không insert/update** trực tiếp vào bảng này. Giao dịch mới đi qua `action_requests` → `api_call_logs`.
- Agent dùng bảng này để:
  - Trả lời câu hỏi "giao dịch gần đây của tôi".
  - Phân tích chi tiêu theo thời gian, danh mục, merchant.
  - Tìm người nhận cũ (counterparty) khi resolve recipient.
  - Kiểm tra trạng thái giao dịch (SUCCESS/FAILED/PENDING).
- Phục vụ use case: tra cứu lịch sử, phân tích tài chính, Text2SQL queries.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| transaction_id | UUID string | ID kỹ thuật giao dịch | `8bb38dee-3d86-5f6b-8de4-839d68454a4f` | No | PK | - |
| transaction_ref | string | Mã tham chiếu giao dịch | `TXN202512000001`, `TXN202512000002` | No | Unique | Format: TXN + YYYYMM + sequence |
| cif_no | string | Mã khách hàng | `CIF000097`, `CIF000094`, `CIF000075` | No | FK → customers.cif_no | **Luôn filter theo cif_no** |
| account_no | string | Số tài khoản thực hiện | `110809969308`, `491476607283` | No | FK → accounts.account_no | Tài khoản bị trừ/cộng tiền |
| card_id | UUID string | ID thẻ (nếu giao dịch thẻ) | `d4995ef4-9f95-5484-99c7-ea26c1abd32f` | Yes | FK → cards.card_id | Chỉ có giá trị khi transaction_type = CARD_PAYMENT |
| transaction_time | timestamp string | Thời điểm giao dịch | `2025-12-01 01:03:20` | No | - | Dùng filter theo thời gian, ORDER BY |
| amount | numeric | Số tiền | `42031562`, `46380807`, `3220626` | No | - | Đơn vị: đồng VND |
| currency | string | Đơn vị tiền tệ | `VND` | Yes | - | Mặc định VND |
| direction | enum string | Chiều giao dịch | `IN`, `OUT` | Yes | - | IN = nhận tiền, OUT = chi tiền |
| transaction_type | enum string | Loại giao dịch | `SALARY`, `BANK_TRANSFER`, `CARD_PAYMENT`, `BILL_PAYMENT` | Yes | - | Phân loại giao dịch chính |
| category_id | UUID string | Danh mục chi tiêu | `9559bdbc-3175-5bc5-ad12-4d12da9c3f99` | Yes | FK → transaction_categories.category_id | Join để lấy tên category |
| merchant_id | UUID string | Merchant (nếu thanh toán thẻ) | `1295ef10-bd6c-54b5-b74a-c732a7f4b67a` | Yes | FK → merchants.merchant_id | Chỉ có khi CARD_PAYMENT |
| biller_id | UUID string | Biller (nếu thanh toán hóa đơn) | - | Yes | FK → billers.biller_id | Chỉ có khi BILL_PAYMENT |
| beneficiary_id | UUID string | Người nhận (nếu chuyển khoản) | `cd19c6ab-41f3-5eb1-ba42-039dcd8aca25` | Yes | FK → beneficiaries.beneficiary_id | Chỉ có khi BANK_TRANSFER |
| counterparty_account_no | string | Số TK đối tác | `6792988425995`, `215226557676` | Yes | - | Số tài khoản bên kia (nhận/gửi) |
| counterparty_bank_code | string | Mã ngân hàng đối tác | `VIB` | Yes | - | Ngân hàng bên kia |
| counterparty_name | string | Tên đối tác | `Dang Thi Nhi`, `Ngo Ngoc Lan`, `VinGroup` | Yes | - | Tên người nhận/gửi |
| channel | enum string | Kênh giao dịch | `MOBILE`, `WEB`, `POS`, `ATM`, `QR`, `CARD` | Yes | - | Kênh thực hiện |
| description | string | Nội dung giao dịch | `Luong thang 12/2025`, `Chuyen tien cho Nhi`, `Thanh toan tai The Coffee House` | Yes | - | Mô tả do user/system nhập |
| status | enum string | Trạng thái | `SUCCESS`, `FAILED`, `REVERSED`, `PENDING` | Yes | - | Hầu hết là SUCCESS |
| balance_after | numeric | Số dư sau giao dịch | - | Yes | - | Có thể null |
| external_reference | string | Mã tham chiếu external | `EXTSAL000001`, `EXTBAN000002`, `EXTCAR000004` | Yes | - | Mã từ external banking API |
| created_at | timestamp string | Thời điểm tạo record | `2025-12-01 01:03:29` | Yes | - | - |

## 4. Important Values / Enums

### transaction_type

| Value | Meaning | Direction | Example Use Case |
|---|---|---|---|
| BANK_TRANSFER | Chuyển khoản ngân hàng | OUT (hoặc IN nếu nhận) | "Chuyển tiền cho Bình" |
| CARD_PAYMENT | Thanh toán thẻ tại merchant | OUT | "Chi tiêu thẻ tín dụng" |
| BILL_PAYMENT | Thanh toán hóa đơn | OUT | "Trả tiền điện" |
| PHONE_TOPUP | Nạp điện thoại | OUT | "Nạp 100k cho số 09..." |
| SALARY | Nhận lương | IN | "Lương tháng 12" |
| INTEREST | Lãi suất | IN | "Lãi tiết kiệm" |
| REFUND | Hoàn tiền | IN | "Hoàn tiền đơn hàng" |
| CASH_DEPOSIT | Nạp tiền mặt | IN | "Nạp tiền tại ATM" |
| CASH_WITHDRAWAL | Rút tiền mặt | OUT | "Rút tiền ATM" |
| FEE | Phí ngân hàng | OUT | "Phí duy trì tài khoản" |

### direction

| Value | Meaning |
|---|---|
| IN | Tiền vào (nhận lương, hoàn tiền, người khác chuyển đến) |
| OUT | Tiền ra (chuyển khoản, thanh toán, phí) |

### status

| Value | Meaning |
|---|---|
| SUCCESS | Giao dịch thành công |
| FAILED | Giao dịch thất bại |
| REVERSED | Đã hoàn/đảo |
| PENDING | Đang xử lý |

### channel

| Value | Meaning |
|---|---|
| MOBILE | App mobile banking |
| WEB | Internet banking |
| POS | Máy POS tại cửa hàng |
| ATM | Máy ATM |
| QR | Quét mã QR |
| CARD | Giao dịch thẻ online |

## 5. Relationships

- `transactions.cif_no` → `customers.cif_no`
- `transactions.account_no` → `accounts.account_no`
- `transactions.card_id` → `cards.card_id`
- `transactions.category_id` → `transaction_categories.category_id`
- `transactions.merchant_id` → `merchants.merchant_id`
- `transactions.biller_id` → `billers.biller_id`
- `transactions.beneficiary_id` → `beneficiaries.beneficiary_id`

## 6. Simple Usage Examples

### Giao dịch gần đây nhất

```sql
SELECT transaction_ref, amount, direction, transaction_type, counterparty_name, description, transaction_time
FROM transactions
WHERE cif_no = 'CIF000001'
ORDER BY transaction_time DESC
LIMIT 5;
```

Dùng khi user hỏi "giao dịch gần đây của tôi".

### Tổng chi tiêu tháng này

```sql
SELECT SUM(amount) AS total_spent
FROM transactions
WHERE cif_no = 'CIF000001'
  AND direction = 'OUT'
  AND transaction_time >= '2026-01-01'
  AND status = 'SUCCESS';
```

Dùng khi user hỏi "tháng này tôi chi bao nhiêu".

### Tìm giao dịch chuyển khoản cho một người

```sql
SELECT transaction_ref, amount, counterparty_name, transaction_time, description
FROM transactions
WHERE cif_no = 'CIF000001'
  AND transaction_type = 'BANK_TRANSFER'
  AND counterparty_name ILIKE '%Binh%'
ORDER BY transaction_time DESC;
```

Dùng khi user hỏi "tôi đã chuyển cho Bình bao nhiêu lần".

### Chi tiêu thẻ theo merchant

```sql
SELECT t.amount, t.transaction_time, m.merchant_name, t.description
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.cif_no = 'CIF000001' AND t.transaction_type = 'CARD_PAYMENT'
ORDER BY t.transaction_time DESC
LIMIT 10;
```

Dùng khi user hỏi "giao dịch thẻ gần đây".
