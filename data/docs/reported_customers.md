# reported_customers

## 1. Mục đích bảng

Lưu trữ thông tin aggregate risk cho CIF (khách hàng) bị báo cáo lừa đảo nhiều lần hoặc sở hữu nhiều tài khoản bị report. Dùng khi 1 người sở hữu nhiều tài khoản lừa đảo.

**Nhóm:** Fraud detection / transaction screening

## 2. Ngữ cảnh nghiệp vụ

- Bảng này là **aggregate cấp CIF** từ `reported_accounts`.
- Một CIF có thể sở hữu nhiều tài khoản bị report → tổng hợp risk tại đây.
- Agent dùng bảng này để:
  - Đánh giá risk tổng thể của 1 CIF bị báo cáo.
  - Quyết định mức cảnh báo khi chuyển tiền tới bất kỳ TK nào thuộc CIF này.
  - Phát hiện pattern: 1 người mở nhiều TK lừa đảo.
- CIF ở đây là **CIF bên ngoài hệ thống** (CIF kẻ lừa đảo), không nhất thiết tồn tại trong bảng `customers`.
- Bảng này **không phải** danh sách tất cả khách hàng. Chỉ chứa CIF đã bị link tới ít nhất 1 reported_account.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| reported_customer_id | UUID string | ID record | `131ec971-efed-5a6b-9f41-6e41b2e264d5` | No | PK | - |
| cif_no | string | CIF bị báo cáo | `CIF000067`, `CIF000080`, `CIF000071` | No | Unique | CIF kẻ lừa đảo (ngoài hệ thống) |
| reported_account_count | integer | Số TK bị report | `1`, `2` | No | - | Thuộc CIF này |
| valid_report_count | integer | Tổng report liên quan | `2`, `4` | No | - | Tổng report cho mọi TK của CIF |
| total_reported_amount | numeric | Tổng tiền bị mất | `49701987`, `74015348`, `33205321` | No | - | VND |
| risk_score | numeric | Điểm risk (0.0-1.0) | `0.4`, `0.7` | No | - | Aggregate từ reported_accounts |
| risk_level | enum string | Mức risk | `WATCH`, `FROZEN` | No | - | Tương ứng risk_score |
| status | enum string | Trạng thái | `ACTIVE` | No | - | Trạng thái CIF |
| created_at | timestamp string | Thời điểm tạo | `2026-05-30 07:29:57` | No | - | - |
| updated_at | timestamp string | Lần cập nhật cuối | `2026-05-23 11:45:41` | No | - | Cập nhật khi có report mới |

## 4. Important Values / Enums

### risk_level

| Value | Meaning | Implication |
|---|---|---|
| WATCH | Theo dõi (risk thấp-trung) | Cảnh báo nhẹ |
| FROZEN | Bị đóng băng (risk cao) | Block tất cả giao dịch đến TK thuộc CIF |

### status

| Value | Meaning |
|---|---|
| ACTIVE | Đang trong hệ thống monitoring |
| RESOLVED | Đã xử lý xong / cleared |

## 5. Relationships

- `reported_customers.cif_no` ← aggregate từ `reported_accounts.linked_customer_cif`
- Một reported_customer có thể link tới nhiều `reported_accounts`

## 6. Simple Usage Examples

### Tra cứu risk CIF bị báo cáo

```sql
SELECT cif_no, reported_account_count, valid_report_count,
       total_reported_amount, risk_score, risk_level
FROM reported_customers
WHERE cif_no = 'CIF000080';
```

### Danh sách CIF bị FROZEN

```sql
SELECT cif_no, reported_account_count, total_reported_amount, risk_score
FROM reported_customers
WHERE risk_level = 'FROZEN'
ORDER BY risk_score DESC;
```

### CIF có nhiều tài khoản bị báo cáo nhất

```sql
SELECT cif_no, reported_account_count, valid_report_count, total_reported_amount
FROM reported_customers
ORDER BY reported_account_count DESC
LIMIT 5;
```
