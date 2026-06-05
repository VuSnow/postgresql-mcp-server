# api_call_logs

## 1. Mục đích bảng

Ghi nhận log mỗi lần agent gọi external banking API mock. Mỗi record tương ứng một HTTP call tới API bên ngoài, lưu request payload, response payload, HTTP status.

**Nhóm:** API call log

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để **audit trail** — ghi lại chính xác agent đã gọi API gì, với payload gì, kết quả ra sao.
- Agent **không query** bảng này trong flow bình thường. Bảng này phục vụ:
  - Debug khi giao dịch fail.
  - Audit/compliance — trace lại mọi API call.
  - Replay/retry logic.
- Mỗi `api_call_log` liên kết với một `action_request` qua `action_id`.
- Bảng này **không phải** nơi lưu transaction result. Kết quả giao dịch lưu ở `transactions`.
- `response_payload` chứa `external_reference` — mã tham chiếu từ hệ thống external.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| api_call_id | UUID string | ID kỹ thuật log entry | `1fc9f267-0993-5fc0-a950-891c60d88548` | No | PK | - |
| action_id | UUID string | Action request liên quan | `10a66751-e588-52b3-8c89-c500d10fd465` | No | FK → action_requests.action_id | Mỗi action có thể có nhiều API call (retry) |
| api_name | string | Tên API được gọi | `external_transfer_api`, `external_bill_payment_api`, `external_phone_topup_api`, `external_card_service_api` | Yes | - | Trùng với action_requests.api_name |
| request_payload | JSON string | Payload gửi đi | `{"from_account_no": "92644220969", "to_account_no": "872975859883", ...}` | Yes | - | Exactly payload đã gửi |
| response_payload | JSON string | Response nhận về | `{"external_reference": "EXTTRA000001", "status": "SUCCESS", "message": "Operation completed successfully"}` | Yes | - | Chứa external_reference nếu thành công |
| http_status | numeric | HTTP status code | `200` | Yes | - | 200 = success, 4xx/5xx = error |
| status | enum string | Kết quả call | `SUCCESS`, `FAILED` | Yes | - | Đơn giản hóa từ http_status |
| created_at | timestamp string | Thời điểm gọi API | `2026-05-22 08:25:15` | Yes | - | - |

## 4. Important Values / Enums

### api_name

| Value | Meaning | Dùng cho action_type |
|---|---|---|
| external_transfer_api | API chuyển khoản | TRANSFER |
| external_bill_payment_api | API thanh toán hóa đơn | BILL_PAYMENT |
| external_phone_topup_api | API nạp điện thoại | PHONE_TOPUP |
| external_card_service_api | API dịch vụ thẻ | CARD_LOCK, CARD_UNLOCK, CARD_LIMIT_CHANGE |

### status

| Value | Meaning |
|---|---|
| SUCCESS | API trả về thành công (HTTP 200) |
| FAILED | API trả về lỗi (HTTP 4xx/5xx) |

### response_payload structure (SUCCESS)

```json
{
  "external_reference": "EXTTRA000001",
  "status": "SUCCESS",
  "message": "Operation completed successfully"
}
```

## 5. Relationships

- `api_call_logs.action_id` → `action_requests.action_id`

## 6. Simple Usage Examples

### Xem API call log của một action

```sql
SELECT api_name, http_status, status, request_payload, response_payload, created_at
FROM api_call_logs
WHERE action_id = '10a66751-e588-52b3-8c89-c500d10fd465'
ORDER BY created_at;
```

Dùng khi cần trace API call đã thực hiện cho một action.

### Tìm API call thất bại

```sql
SELECT acl.api_call_id, acl.api_name, acl.http_status, acl.response_payload, ar.user_text
FROM api_call_logs acl
JOIN action_requests ar ON acl.action_id = ar.action_id
WHERE acl.status = 'FAILED'
ORDER BY acl.created_at DESC
LIMIT 10;
```

Dùng cho debug/monitoring — tìm các call bị lỗi.

### Thống kê success rate theo API

```sql
SELECT api_name, status, COUNT(*) AS count
FROM api_call_logs
GROUP BY api_name, status;
```

Dùng cho monitoring chất lượng external API.
