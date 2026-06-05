# audit_logs

## 1. Mục đích bảng

Ghi nhận trace toàn bộ workflow từ lúc user gửi yêu cầu đến lúc hoàn tất. Mỗi event trong workflow (intent classified, entity extracted, risk checked, user confirmed, executed...) là một record.

**Nhóm:** Audit log

## 2. Ngữ cảnh nghiệp vụ

- Bảng này tồn tại để **giải thích workflow** — tại sao agent làm gì, ai làm, khi nào.
- Agent dùng bảng này để:
  - Trace lại toàn bộ quá trình xử lý một yêu cầu (debug, explainability).
  - Hiển thị cho user: "Tôi đã phân loại intent → resolve người nhận → check risk → xác nhận → thực thi".
  - Compliance: audit trail cho mọi hành động.
- Mỗi `action_id` có nhiều audit_log records, mỗi record là một bước trong workflow.
- `actor` cho biết ai/module nào thực hiện bước đó: USER, ORCHESTRATOR, TRANSACTION_AGENT, GUARDIAN, EXECUTOR.
- `event_payload` chứa chi tiết của event dưới dạng JSON.
- Bảng này **không dùng** cho Text2SQL thông thường. Chủ yếu cho debug/trace/compliance.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| audit_id | UUID string | ID kỹ thuật audit entry | `90f87dd4-8505-5d93-ae3e-e54de5bdf06a` | No | PK | - |
| action_id | UUID string | Action request liên quan | `10a66751-e588-52b3-8c89-c500d10fd465` | Yes | FK → action_requests.action_id | Nullable cho event không liên quan action |
| cif_no | string | Mã khách hàng | `CIF000066` | No | FK → customers.cif_no | Filter theo khách hàng |
| event_type | enum string | Loại event | `USER_REQUEST_RECEIVED`, `INTENT_CLASSIFIED`, `ENTITY_EXTRACTED` | Yes | - | Xác định bước workflow |
| actor | enum string | Ai thực hiện | `USER`, `ORCHESTRATOR`, `TRANSACTION_AGENT`, `GUARDIAN`, `EXECUTOR` | Yes | - | Module/role thực hiện bước |
| event_payload | JSON string | Chi tiết event | `{"event": "USER_REQUEST_RECEIVED", "action_type": "TRANSFER", "user_text": "..."}` | Yes | - | Context cụ thể của mỗi event |
| created_at | timestamp string | Thời điểm event xảy ra | `2026-05-22 08:25:14` | Yes | - | Dùng ORDER BY để thấy sequence |

## 4. Important Values / Enums

### event_type (theo thứ tự workflow)

| Value | Meaning | Actor thường thấy |
|---|---|---|
| USER_REQUEST_RECEIVED | Nhận yêu cầu từ user | USER |
| INTENT_CLASSIFIED | Phân loại intent (TRANSFER, BILL_PAYMENT...) | ORCHESTRATOR |
| ENTITY_EXTRACTED | Extract entities từ user text | TRANSACTION_AGENT |
| RECIPIENT_RESOLVED | Resolve được người nhận chuyển khoản | TRANSACTION_AGENT |
| BILLER_RESOLVED | Resolve được biller/mã hóa đơn | TRANSACTION_AGENT |
| CARD_RESOLVED | Resolve được thẻ cần thao tác | TRANSACTION_AGENT |
| RISK_CHECKED | Đã kiểm tra risk | GUARDIAN |
| USER_CONFIRMED | User xác nhận thực hiện | USER |
| OTP_VERIFIED | OTP đã verified | USER |
| API_CALLED | Gọi external API | EXECUTOR |
| ACTION_EXECUTED | Action hoàn tất thành công | EXECUTOR |
| ACTION_FAILED | Action thất bại | EXECUTOR |
| ACTION_BLOCKED | Action bị chặn bởi Guardian | GUARDIAN |

### actor

| Value | Meaning |
|---|---|
| USER | Khách hàng (gửi request, confirm, OTP) |
| ORCHESTRATOR | Agent điều phối chính (phân loại intent) |
| TRANSACTION_AGENT | Agent xử lý giao dịch (resolve entities) |
| GUARDIAN | Module kiểm tra risk/permission |
| EXECUTOR | Module thực thi API call |

### event_payload structure examples

**USER_REQUEST_RECEIVED:**
```json
{"event": "USER_REQUEST_RECEIVED", "action_type": "TRANSFER", "user_text": "Chuyen 50 trieu cho nguoi nhan moi"}
```

**INTENT_CLASSIFIED:**
```json
{"event": "INTENT_CLASSIFIED", "action_type": "TRANSFER"}
```

**RISK_CHECKED:**
```json
{"event": "RISK_CHECKED", "risk_score": 0.21, "risk_tier": "GREEN"}
```

## 5. Relationships

- `audit_logs.action_id` → `action_requests.action_id`
- `audit_logs.cif_no` → `customers.cif_no`

## 6. Simple Usage Examples

### Trace toàn bộ workflow của một action

```sql
SELECT event_type, actor, event_payload, created_at
FROM audit_logs
WHERE action_id = '10a66751-e588-52b3-8c89-c500d10fd465'
ORDER BY created_at;
```

Dùng khi cần xem step-by-step agent đã xử lý yêu cầu như thế nào.

### Xem hoạt động gần đây của khách hàng

```sql
SELECT event_type, actor, created_at
FROM audit_logs
WHERE cif_no = 'CIF000066'
ORDER BY created_at DESC
LIMIT 10;
```

Dùng cho audit/compliance — xem mọi event liên quan đến khách hàng.

### Tìm action bị blocked

```sql
SELECT al.action_id, al.event_payload, ar.user_text, ar.risk_tier
FROM audit_logs al
JOIN action_requests ar ON al.action_id = ar.action_id
WHERE al.event_type = 'ACTION_BLOCKED'
ORDER BY al.created_at DESC;
```

Dùng khi cần review các action bị Guardian chặn.

### Đếm events theo actor

```sql
SELECT actor, COUNT(*) AS event_count
FROM audit_logs
WHERE cif_no = 'CIF000066'
GROUP BY actor;
```

Dùng cho monitoring — xem module nào hoạt động nhiều nhất.
