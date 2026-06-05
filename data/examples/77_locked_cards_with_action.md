# Khách hàng có thẻ LOCKED — lý do và action request tương ứng

## Complexity: complex

## Tables Used: cards, action_requests, customers

## Question (Vietnamese)
Liệt kê khách hàng có thẻ bị khóa (LOCKED), kèm action request khóa thẻ gần nhất (nếu có).

## Join Logic
- Cần `cards` để filter status = 'LOCKED'.
- Cần `customers` để lấy tên.
- Cần `action_requests` để tìm action CARD_LOCK tương ứng.
- **JOIN paths**:
  - `cards.cif_no = customers.cif_no`
  - `action_requests.cif_no = cards.cif_no AND action_requests.action_type = 'CARD_LOCK'`
- LEFT JOIN action_requests vì có thể thẻ bị lock bởi system, không qua action_request.

## SQL
```sql
SELECT
    c.full_name,
    ca.masked_card_no,
    ca.card_type,
    ca.card_network,
    ar.action_id,
    ar.status AS action_status,
    ar.risk_tier,
    ar.created_at AS lock_requested_at
FROM cards ca
JOIN customers c ON ca.cif_no = c.cif_no
LEFT JOIN LATERAL (
    SELECT action_id, status, risk_tier, created_at
    FROM action_requests
    WHERE cif_no = ca.cif_no
      AND action_type = 'CARD_LOCK'
    ORDER BY created_at DESC
    LIMIT 1
) ar ON TRUE
WHERE ca.status = 'LOCKED'
ORDER BY ar.created_at DESC NULLS LAST
LIMIT 50;
```

## Explanation
LATERAL subquery lấy action CARD_LOCK mới nhất cho mỗi KH có thẻ locked. LEFT JOIN vì không phải lúc nào cũng có action_request (system có thể auto-lock). Kết hợp 3 bảng.
