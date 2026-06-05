# fraud_decisions

## 1. Mục đích bảng

Lưu trữ kết quả screening khi user chuyển tiền. Mỗi khi Guardian thực hiện transaction screening (check receiver account có bị báo cáo không), kết quả quyết định ALLOW / WARN / BLOCK được ghi vào đây.

**Nhóm:** Fraud detection / transaction screening

## 2. Ngữ cảnh nghiệp vụ

- Bảng này là **output** của bước transaction screening trong verified workflow.
- Flow: User yêu cầu TRANSFER → Guardian lookup `reported_accounts` → tạo `fraud_decision` → quyết định cho phép / cảnh báo / chặn.
- Agent dùng bảng này để:
  - Ghi lại lịch sử screening decisions.
  - Trace tại sao 1 giao dịch bị block hoặc warn.
  - Audit trail cho fraud workflow.
- Bảng này **chỉ** liên quan đến action_type = TRANSFER.
- Nếu `decision = BLOCK` → `action_requests.status` nên là BLOCKED.
- Nếu `matched_report_count = 0` → chuyển tiền bình thường, risk_score = 0.

## 3. Columns

| Column | Type | Meaning | Example Values From Data | Nullable | Key / Relationship | Notes |
|---|---|---|---|---|---|---|
| decision_id | UUID string | ID quyết định | `ac365eea-48c4-514a-8d7b-15f2da68abae` | No | PK | - |
| action_id | UUID string | Action request liên quan | `95ff56b0-cd92-5fc7-9f5a-c0c32ebbf29f` | No | FK → action_requests.action_id | Chỉ TRANSFER actions |
| receiver_account_no | string | Số TK nhận | `2762126796`, `852986755422`, `1307240787` | No | - | TK người nhận tiền |
| receiver_bank_code | string | Bank code nhận | `VIB`, `TPB`, `MB`, `CTG`, `TCB`, `STB`, `BIDV`, `ACB`, `VCB` | No | - | Từ BANK_MAP |
| matched_report_count | integer | Số report match TK nhận | `0` | No | - | 0 = không có report nào |
| risk_score | numeric | Điểm risk (0.0-1.0) | `0.0` | No | - | Từ reported_accounts hoặc 0 nếu không match |
| risk_level | enum string | Mức risk | `NONE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | No | - | Quyết định mức cảnh báo |
| decision | enum string | Quyết định screening | `ALLOW`, `WARN`, `BLOCK` | No | - | Output chính |
| reason_codes | JSON string | Lý do quyết định | `[]`, `["HIGH_RISK_ACTION"]` | No | - | Array các reason codes |
| created_at | timestamp string | Thời điểm tạo | `2026-04-04 07:55:53`, `2026-05-06 13:54:36` | No | - | - |

## 4. Important Values / Enums

### decision

| Value | Meaning | User Experience |
|---|---|---|
| ALLOW | Cho phép chuyển | Tiếp tục flow bình thường |
| WARN | Cảnh báo | Hiển thị warning cho user, yêu cầu xác nhận thêm |
| BLOCK | Chặn | Không cho chuyển tiền, thông báo lý do |

### risk_level

| Value | Meaning | Trigger |
|---|---|---|
| NONE | Không có risk | matched_report_count = 0 |
| LOW | Risk thấp | reported_accounts.risk_level = LOW |
| MEDIUM | Risk trung bình | reported_accounts.risk_level = MEDIUM |
| HIGH | Risk cao | reported_accounts.risk_level = HIGH |
| CRITICAL | Risk rất cao | reported_accounts.risk_level = CRITICAL |

### reason_codes (common values)

| Value | Meaning |
|---|---|
| REPORTED_ACCOUNT | TK nhận đã bị báo cáo lừa đảo |
| HIGH_RISK_SCORE | Điểm risk cao |
| MULTIPLE_REPORTERS | Nhiều người báo cáo TK này |
| HIGH_RISK_ACTION | Giao dịch có risk cao từ action_requests |
| CRITICAL_ACCOUNT | TK nhận ở mức CRITICAL |

### reason_codes JSON structure

```json
["REPORTED_ACCOUNT", "HIGH_RISK_SCORE", "MULTIPLE_REPORTERS"]
```

## 5. Relationships

- `fraud_decisions.action_id` → `action_requests.action_id` (chỉ TRANSFER)
- `fraud_decisions.receiver_account_no` có thể match `reported_accounts.account_no`
- Mỗi TRANSFER action có tối đa 1 fraud_decision

## 6. Simple Usage Examples

### Xem kết quả screening cho 1 action

```sql
SELECT decision_id, receiver_account_no, receiver_bank_code,
       matched_report_count, risk_level, decision, reason_codes
FROM fraud_decisions
WHERE action_id = '95ff56b0-cd92-5fc7-9f5a-c0c32ebbf29f';
```

### Danh sách giao dịch bị BLOCK

```sql
SELECT fd.decision_id, fd.receiver_account_no, fd.receiver_bank_code,
       fd.risk_score, fd.reason_codes, ar.user_text
FROM fraud_decisions fd
JOIN action_requests ar ON fd.action_id = ar.action_id
WHERE fd.decision = 'BLOCK'
ORDER BY fd.created_at DESC;
```

### Đếm decision theo loại

```sql
SELECT decision, COUNT(*) AS total
FROM fraud_decisions
GROUP BY decision;
```

### Tìm screening có match report

```sql
SELECT decision_id, receiver_account_no, receiver_bank_code,
       matched_report_count, risk_score, decision
FROM fraud_decisions
WHERE matched_report_count > 0
ORDER BY risk_score DESC;
```
