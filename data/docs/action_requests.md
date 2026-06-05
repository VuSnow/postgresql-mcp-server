# action_requests

## 1. Mục đích bảng

Lưu trữ các yêu cầu hành động (action draft) trong verified workflow. Khi user yêu cầu thực hiện giao dịch (chuyển tiền, thanh toán, khóa thẻ...), agent tạo một action_request chứa toàn bộ thông tin đã resolve, API payload, risk assessment, và trạng thái workflow.

**Nhóm:** Workflow/action store

## 2. Ngữ cảnh nghiệp vụ

- Bảng này là **trung tâm của verified workflow**. Mọi hành động nhạy cảm đều đi qua đây.
- Workflow: User request → Intent → Resolve entities → Risk check → Confirmation → OTP → Execute.
- Agent dùng bảng này để:
  - Lưu draft action khi bắt đầu xử lý yêu cầu.
  - Track trạng thái workflow (DRAFT → READY → PENDING_CONFIRMATION → PENDING_OTP → EXECUTED).
  - Lưu API payload đã resolve (sẵn sàng gọi external API).
  - Ghi nhận risk score và risk tier.
  - Xác định action nào cần confirmation, cần OTP.
- Bảng này **không phải** lịch sử giao dịch. Một action_request có thể FAILED hoặc BLOCKED mà không tạo transaction.
- `api_payload` chứa payload sẵn sàng gửi external API — đây là output của bước entity resolution.
- `resolved_entities` chứa entities đã extract từ user text.
- `missing_fields` chứa fields cần hỏi thêm user.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| action_id | UUID string | ID kỹ thuật action | `10a66751-e588-52b3-8c89-c500d10fd465` | No | PK | Dùng làm FK cho api_call_logs và audit_logs |
| cif_no | string | Mã khách hàng yêu cầu | `CIF000066`, `CIF000039`, `CIF000080` | No | FK → customers.cif_no | Filter theo khách hàng |
| action_type | enum string | Loại hành động | `TRANSFER`, `BILL_PAYMENT`, `PHONE_TOPUP`, `CARD_LOCK`, `CARD_UNLOCK`, `CARD_LIMIT_CHANGE` | Yes | - | Xác định workflow và API cần gọi |
| status | enum string | Trạng thái workflow | `EXECUTED`, `READY_TO_EXECUTE`, `PENDING_OTP`, `PENDING_CONFIRMATION` | Yes | - | Theo dõi bước hiện tại |
| user_text | string | Câu nói gốc của user | `Chuyen 50 trieu cho nguoi nhan moi`, `Gui tien cho me 5 trieu` | Yes | - | Input ban đầu từ user |
| api_name | string | Tên API sẽ gọi | `external_transfer_api`, `external_bill_payment_api`, `external_phone_topup_api`, `external_card_service_api` | Yes | - | Xác định external API endpoint |
| api_payload | JSON string | Payload sẵn sàng gọi API | `{"from_account_no": "92644220969", "to_account_no": "872975859883", ...}` | Yes | - | Output của entity resolution |
| resolved_entities | JSON string | Entities đã extract | `{"beneficiary_name": "Hoang Van Uyen", "amount": 30538599, "bank_code": "TCB"}` | Yes | - | Kết quả NLU/resolution |
| missing_fields | JSON string | Fields cần hỏi thêm | `[]`, `["amount"]`, `["to_account_no"]`, `["phone_number"]` | Yes | - | Nếu không rỗng → status = MISSING_INFO |
| risk_score | numeric | Điểm risk (0.00-1.00) | `0.21`, `0.17`, `0.16`, `0.63` | Yes | - | Guardian tính toán |
| risk_tier | enum string | Mức risk | `GREEN`, `YELLOW`, `ORANGE`, `RED` | Yes | - | Quyết định cần confirm/OTP/block |
| requires_confirmation | boolean | Cần user xác nhận | `True`, `False` | Yes | - | Hầu hết action đều cần |
| requires_otp | boolean | Cần OTP | `True`, `False` | Yes | - | Giao dịch trên ngưỡng hoặc risk cao |
| created_at | timestamp string | Thời điểm tạo | `2026-05-22 08:25:12` | Yes | - | - |
| updated_at | timestamp string | Lần cập nhật cuối | `2026-05-22 08:26:10` | Yes | - | Mỗi bước workflow cập nhật |

## 4. Important Values / Enums

### action_type

| Value | Meaning | API tương ứng |
|---|---|---|
| TRANSFER | Chuyển khoản ngân hàng | external_transfer_api |
| BILL_PAYMENT | Thanh toán hóa đơn | external_bill_payment_api |
| PHONE_TOPUP | Nạp điện thoại | external_phone_topup_api |
| CARD_LOCK | Khóa thẻ | external_card_service_api |
| CARD_UNLOCK | Mở khóa thẻ | external_card_service_api |
| CARD_LIMIT_CHANGE | Thay đổi hạn mức thẻ | external_card_service_api |

### status (lifecycle)

| Value | Meaning | Next Steps |
|---|---|---|
| DRAFT | Mới tạo, đang resolve entities | → MISSING_INFO hoặc READY_TO_EXECUTE |
| MISSING_INFO | Thiếu thông tin, cần hỏi user | → DRAFT (sau khi user cung cấp) |
| READY_TO_EXECUTE | Đã resolve đủ, sẵn sàng | → PENDING_CONFIRMATION |
| PENDING_CONFIRMATION | Chờ user xác nhận | → PENDING_OTP hoặc EXECUTED |
| PENDING_OTP | Chờ OTP | → EXECUTED hoặc FAILED |
| EXECUTED | Đã thực thi thành công | Terminal state |
| FAILED | Thất bại | Terminal state |
| BLOCKED | Guardian chặn (risk quá cao) | Terminal state |

### risk_tier

| Value | Meaning | Action |
|---|---|---|
| GREEN | Risk thấp (< 0.3) | Confirm + có thể không cần OTP |
| YELLOW | Risk trung bình (0.3-0.5) | Confirm + OTP |
| ORANGE | Risk cao (0.5-0.7) | Confirm + OTP + cảnh báo |
| RED | Risk rất cao (> 0.7) | Block hoặc require enhanced verification |

### api_payload structure (TRANSFER example)

```json
{
  "from_account_no": "92644220969",
  "to_account_no": "872975859883",
  "to_bank_code": "TCB",
  "to_name": "Hoang Van Uyen",
  "amount": 30538599,
  "currency": "VND",
  "description": "Chuyen tien cho Uyen"
}
```

## 5. Relationships

- `action_requests.cif_no` → `customers.cif_no`
- `action_requests.action_id` được tham chiếu bởi:
  - `api_call_logs.action_id`
  - `audit_logs.action_id`

## 6. Simple Usage Examples

### Xem action gần đây của khách hàng

```sql
SELECT action_id, action_type, status, user_text, risk_tier, created_at
FROM action_requests
WHERE cif_no = 'CIF000001'
ORDER BY created_at DESC
LIMIT 5;
```

Dùng khi cần trace lại workflow gần đây.

### Tìm action đang chờ xử lý

```sql
SELECT action_id, action_type, status, user_text
FROM action_requests
WHERE cif_no = 'CIF000066' AND status IN ('PENDING_CONFIRMATION', 'PENDING_OTP', 'READY_TO_EXECUTE');
```

Dùng khi cần resume workflow bị gián đoạn.

### Xem chi tiết API payload của một action

```sql
SELECT action_type, api_name, api_payload, resolved_entities, risk_score, risk_tier
FROM action_requests
WHERE action_id = '10a66751-e588-52b3-8c89-c500d10fd465';
```

Dùng khi cần debug hoặc review payload trước khi execute.

### Thống kê action theo trạng thái

```sql
SELECT status, COUNT(*) AS count
FROM action_requests
WHERE cif_no = 'CIF000066'
GROUP BY status;
```

Dùng cho reporting/monitoring workflow.
