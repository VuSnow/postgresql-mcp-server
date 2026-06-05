# interest_rates

## 1. Mục đích bảng

Lưu lãi suất sản phẩm tiết kiệm và vay của ngân hàng SHB. Agent dùng bảng này để tra cứu lãi suất hiện hành khi tư vấn tài chính cho khách hàng.

Nhóm: Reference/configuration data

## 2. Ngữ cảnh nghiệp vụ

- Bảng này phục vụ financial planning agent: khi khách hỏi "gửi tiết kiệm 6 tháng được bao nhiêu lãi?" → agent query bảng này lấy annual_rate.
- Lãi suất có hiệu lực theo ngày (effective_from/effective_to) và phân biệt theo kênh (ONLINE/COUNTER).
- Mỗi sản phẩm có mức gửi tối thiểu (min_amount).
- Sản phẩm bao gồm: tiết kiệm (SAVINGS) và vay (LOAN).
- Phân khúc khách hàng: ALL (tất cả), RETAIL, PRIORITY, STUDENT.

## 3. Columns

| Column | Type | Meaning | Example Values | Nullable | Notes |
|---|---|---|---|---|---|
| id | UUID | ID kỹ thuật | gen_random_uuid() | No | PK |
| product_code | VARCHAR(50) | Mã sản phẩm | SAVINGS_ONLINE_6M, LOAN_PERSONAL | No | Unique identifier |
| product_type | VARCHAR(30) | Loại sản phẩm | SAVINGS, LOAN | No | Filter chính |
| product_name | VARCHAR(100) | Tên hiển thị | "Tiết kiệm online 6 tháng" | No | Hiển thị cho user |
| currency | VARCHAR(3) | Loại tiền | VND | Yes | Default VND |
| term_months | INT | Kỳ hạn (tháng) | 1, 3, 6, 12, 24, 240 | Yes | NULL = không kỳ hạn |
| annual_rate | DECIMAL(5,2) | Lãi suất năm (%) | 4.50, 5.00, 8.50 | No | 4.50 = 4.5%/năm |
| min_amount | DECIMAL(18,0) | Số tiền gửi tối thiểu | 1000000, 5000000 | Yes | VND |
| max_amount | DECIMAL(18,0) | Số tiền gửi tối đa | NULL = không giới hạn | Yes | |
| customer_segment | VARCHAR(30) | Phân khúc KH | ALL, RETAIL, PRIORITY | Yes | Default ALL |
| channel | VARCHAR(20) | Kênh giao dịch | ALL, ONLINE, COUNTER | Yes | Online thường lãi cao hơn |
| effective_from | DATE | Ngày bắt đầu hiệu lực | 2026-01-01 | No | |
| effective_to | DATE | Ngày hết hiệu lực | NULL = vẫn còn hiệu lực | Yes | |
| status | VARCHAR(10) | Trạng thái | ACTIVE, INACTIVE | Yes | Default ACTIVE |
| created_at | TIMESTAMP | Thời điểm tạo | now() | Yes | |

## 4. Important Values / Enums

- product_type: SAVINGS, LOAN
- channel: ALL, ONLINE, COUNTER
- customer_segment: ALL, RETAIL, PRIORITY, STUDENT
- status: ACTIVE, INACTIVE

## 5. Relationships

- Không có FK từ bảng khác trỏ tới.
- Standalone reference table.

## 6. Simple Usage Examples

### Lấy lãi suất tiết kiệm online hiện hành

```sql
SELECT product_name, term_months, annual_rate, min_amount
FROM interest_rates
WHERE product_type = 'SAVINGS'
  AND status = 'ACTIVE'
  AND (channel = 'ONLINE' OR channel = 'ALL')
  AND effective_from <= CURRENT_DATE
  AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
ORDER BY term_months ASC;
```

### Tìm lãi suất theo kỳ hạn cụ thể

```sql
SELECT product_name, annual_rate, min_amount, channel
FROM interest_rates
WHERE product_type = 'SAVINGS'
  AND term_months = 6
  AND status = 'ACTIVE'
  AND effective_from <= CURRENT_DATE
  AND (effective_to IS NULL OR effective_to >= CURRENT_DATE);
```

### Lấy lãi suất vay

```sql
SELECT product_name, term_months, annual_rate, min_amount
FROM interest_rates
WHERE product_type = 'LOAN'
  AND status = 'ACTIVE'
ORDER BY annual_rate ASC;
```
