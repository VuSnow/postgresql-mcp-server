# merchants

## 1. Mục đích bảng

Lưu thông tin merchant (đơn vị chấp nhận thanh toán thẻ). Agent dùng bảng này để hiển thị tên merchant khi tra cứu giao dịch thẻ, phân tích chi tiêu theo danh mục.

**Nhóm:** Master/reference data

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để cung cấp context cho giao dịch thẻ — khi user hỏi "tôi đã chi bao nhiêu ở quán cà phê", agent cần join với bảng này.
- Agent dùng bảng này để:
  - Hiển thị tên merchant trong lịch sử giao dịch thẻ.
  - Phân tích chi tiêu theo danh mục merchant (`merchant_category`).
  - Tìm giao dịch tại một merchant cụ thể.
- Phục vụ use case: tra cứu giao dịch thẻ (CARD_PAYMENT), phân tích chi tiêu.
- Bảng này **không liên quan** đến chuyển tiền hay thanh toán hóa đơn.
- Merchant data là reference data — agent chỉ đọc, không tạo merchant mới.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| merchant_id | UUID string | ID kỹ thuật merchant | `a7ebff1a-de7e-5a29-9580-65e0a6129d5c` | No | PK | Dùng làm FK trong transactions |
| merchant_name | string | Tên merchant | `Lotte Cinema`, `Pho 24`, `VNR Booking`, `Sendo` | No | - | Hiển thị cho user |
| merchant_category | enum string | Danh mục merchant | `ENTERTAINMENT`, `FOOD`, `TRANSPORT`, `ECOMMERCE` | Yes | - | Dùng phân tích chi tiêu |
| mcc_code | string | Mã MCC (Merchant Category Code) | `7832`, `5812`, `4121`, `5399` | Yes | - | Mã chuẩn quốc tế |
| city | string | Thành phố | `Ho Chi Minh`, `Ha Noi`, `Can Tho` | Yes | - | - |
| country | string | Quốc gia | `VN` | Yes | - | Mặc định VN |
| status | enum string | Trạng thái | `ACTIVE`, `INACTIVE` | Yes | - | - |

## 4. Important Values / Enums

| Column | Value | Meaning | Example Use Case |
|---|---|---|---|
| merchant_category | FOOD | Ăn uống | Phân tích chi tiêu ăn uống |
| merchant_category | ENTERTAINMENT | Giải trí | Chi phí giải trí (phim, game) |
| merchant_category | TRANSPORT | Đi lại | Chi phí di chuyển (Grab, vé tàu) |
| merchant_category | ECOMMERCE | Mua sắm online | Đặt hàng trên Shopee, Sendo... |
| merchant_category | SHOPPING | Mua sắm | Cửa hàng, thời trang |
| merchant_category | GROCERY | Siêu thị / Tạp hóa | Mua sắm hàng ngày |
| merchant_category | ELECTRONICS | Điện tử | Mua thiết bị điện tử |
| merchant_category | DIGITAL_WALLET | Ví điện tử | Nạp ví MoMo, ZaloPay |

## 5. Relationships

- `merchants.merchant_id` được tham chiếu bởi `transactions.merchant_id`

## 6. Simple Usage Examples

### Tìm giao dịch tại một merchant cụ thể

```sql
SELECT t.transaction_ref, t.amount, t.transaction_time, m.merchant_name
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.cif_no = 'CIF000001' AND m.merchant_name ILIKE '%Coffee%';
```

Dùng khi user hỏi "tôi chi bao nhiêu ở Coffee House".

### Phân tích chi tiêu theo danh mục merchant

```sql
SELECT m.merchant_category, SUM(t.amount) AS total_spent
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.cif_no = 'CIF000001' AND t.direction = 'OUT'
GROUP BY m.merchant_category;
```

Dùng khi user hỏi "chi tiêu của tôi chia theo loại hình".

### Liệt kê tất cả merchant trong danh mục

```sql
SELECT merchant_id, merchant_name, city
FROM merchants
WHERE merchant_category = 'FOOD' AND status = 'ACTIVE';
```

Dùng khi cần lookup merchant reference data.
