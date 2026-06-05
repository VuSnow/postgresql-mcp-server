# transaction_categories

## 1. Mục đích bảng

Lưu danh mục phân loại giao dịch. Mỗi giao dịch trong bảng `transactions` được gắn một `category_id` để phân loại chi tiêu, thu nhập, hóa đơn, phí.

**Nhóm:** Master/reference data

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để hỗ trợ phân tích chi tiêu và phân loại giao dịch cho reporting/Text2SQL.
- Agent dùng bảng này để:
  - Phân loại giao dịch khi user hỏi "tháng này tôi chi bao nhiêu cho ăn uống".
  - Group giao dịch theo `category_group` (SPENDING, TRANSFER, INCOME, BILL, FEE, CASH, OTHER).
  - Translate `category_code` thành tên tiếng Việt cho user.
- Phục vụ use case: phân tích chi tiêu, báo cáo tài chính cá nhân.
- Bảng này **chỉ là reference** — agent không tạo category mới.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| category_id | UUID string | ID kỹ thuật danh mục | `fa45defc-de8f-5173-8b0a-366b8533fd0e` | No | PK | Dùng làm FK trong transactions |
| category_code | string | Mã danh mục unique | `FOOD`, `SHOPPING`, `TRANSPORT`, `SALARY` | No | Unique | Dùng trong query filter |
| category_name | string | Tên tiếng Việt | `An uong`, `Mua sam`, `Di chuyen`, `Luong` | No | - | Hiển thị cho user |
| category_group | string | Nhóm lớn | `SPENDING`, `TRANSFER`, `INCOME`, `BILL`, `FEE`, `CASH`, `OTHER` | Yes | - | Dùng aggregate cấp cao |

## 4. Important Values / Enums

### Nhóm SPENDING (chi tiêu)

| category_code | category_name | Meaning |
|---|---|---|
| FOOD | An uong | Chi tiêu ăn uống |
| SHOPPING | Mua sam | Mua sắm |
| TRANSPORT | Di chuyen | Di chuyển (Grab, taxi) |
| ENTERTAINMENT | Giai tri | Giải trí (phim, game) |
| GROCERIES | Sieu thi / Tap hoa | Siêu thị, tạp hóa |
| CARD_PAYMENT | Thanh toan the | Thanh toán thẻ chung |

### Nhóm TRANSFER (chuyển khoản)

| category_code | category_name | Meaning |
|---|---|---|
| TRANSFER | Chuyen khoan | Chuyển khoản ngân hàng |
| FAMILY_TRANSFER | Chuyen khoan gia dinh | Chuyển tiền gia đình |
| RENT | Tien thue nha | Tiền thuê nhà |

### Nhóm INCOME (thu nhập)

| category_code | category_name | Meaning |
|---|---|---|
| SALARY | Luong | Nhận lương |
| INTEREST | Lai suat | Lãi suất tiết kiệm |
| REFUND | Hoan tien | Hoàn tiền |
| CASH_DEPOSIT | Nap tien mat | Nạp tiền mặt |

### Nhóm BILL (hóa đơn)

| category_code | category_name | Meaning |
|---|---|---|
| BILL_ELECTRICITY | Hoa don dien | Hóa đơn điện |
| BILL_WATER | Hoa don nuoc | Hóa đơn nước |
| BILL_INTERNET | Hoa don internet | Hóa đơn internet |
| PHONE_TOPUP | Nap dien thoai | Nạp điện thoại |

### Nhóm khác

| category_code | category_name | category_group |
|---|---|---|
| BANK_FEE | Phi ngan hang | FEE |
| CASH_WITHDRAWAL | Rut tien mat | CASH |
| OTHER | Khac | OTHER |

## 5. Relationships

- `transaction_categories.category_id` được tham chiếu bởi `transactions.category_id`

## 6. Simple Usage Examples

### Phân tích chi tiêu theo danh mục

```sql
SELECT tc.category_name, SUM(t.amount) AS total
FROM transactions t
JOIN transaction_categories tc ON t.category_id = tc.category_id
WHERE t.cif_no = 'CIF000001' AND t.direction = 'OUT'
GROUP BY tc.category_name
ORDER BY total DESC;
```

Dùng khi user hỏi "tháng này tôi chi cho những gì".

### Tổng chi tiêu theo nhóm lớn

```sql
SELECT tc.category_group, SUM(t.amount) AS total
FROM transactions t
JOIN transaction_categories tc ON t.category_id = tc.category_id
WHERE t.cif_no = 'CIF000001' AND t.direction = 'OUT'
GROUP BY tc.category_group;
```

Dùng khi cần tổng quan spending vs bills vs fees.

### Tìm category_id theo code

```sql
SELECT category_id, category_name
FROM transaction_categories
WHERE category_code = 'FOOD';
```

Dùng khi cần filter giao dịch theo một category cụ thể.
