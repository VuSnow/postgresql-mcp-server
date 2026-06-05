# CARD_LIMIT_CHANGE — yêu cầu thay đổi hạn mức

## Complexity: medium

## Tables Used: action_requests, cards

## Question (Vietnamese)
Liệt kê yêu cầu thay đổi hạn mức thẻ (CARD_LIMIT_CHANGE) gần đây, kèm thông tin thẻ hiện tại.

## Join Logic
- Cần `action_requests` filter action_type = 'CARD_LIMIT_CHANGE'.
- Cần `cards` để lấy thông tin thẻ liên quan.
- **JOIN path**: thông qua cif_no (action_requests.cif_no = cards.cif_no) + card info có thể trong metadata.
- Lấy thẻ CREDIT active của KH đó.

## SQL
```sql
SELECT
    ar.action_id,
    ar.cif_no,
    ar.status,
    ar.risk_tier,
    ar.user_text,
    ar.created_at,
    ca.masked_card_no,
    ca.card_type,
    ca.card_network
FROM action_requests ar
JOIN cards ca ON ar.cif_no = ca.cif_no
    AND ca.card_type = 'CREDIT'
    AND ca.status = 'ACTIVE'
WHERE ar.action_type = 'CARD_LIMIT_CHANGE'
  AND ar.created_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY ar.created_at DESC
LIMIT 30;
```

## Explanation
JOIN action_requests với cards qua cif_no + filter CREDIT + ACTIVE. action_type = 'CARD_LIMIT_CHANGE'. user_text có thể chứa hạn mức mong muốn. risk_tier cho biết mức rủi ro.
