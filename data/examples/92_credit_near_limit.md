# Thẻ tín dụng gần hạn mức (CREDIT card near limit)

## Complexity: medium

## Tables Used: cards, accounts

## Question (Vietnamese)
Tìm thẻ tín dụng (CREDIT) có số dư khả dụng dưới 10% hạn mức. (Cần dựa vào account linked)

## Join Logic
- Cần `cards` để filter card_type = 'CREDIT'.
- Cần `accounts` để lấy credit_limit và available_balance từ linked account.
- **JOIN path**: `cards.linked_account_no = accounts.account_no`
- Filter: available_balance < 10% * credit_limit.

## SQL
```sql
SELECT
    ca.cif_no,
    ca.masked_card_no,
    ca.card_network,
    a.account_no,
    a.credit_limit,
    a.available_balance,
    ROUND(a.available_balance * 100.0 / NULLIF(a.credit_limit, 0), 1) AS pct_available
FROM cards ca
JOIN accounts a ON ca.linked_account_no = a.account_no
WHERE ca.card_type = 'CREDIT'
  AND ca.status = 'ACTIVE'
  AND a.credit_limit > 0
  AND a.available_balance < a.credit_limit * 0.10
ORDER BY pct_available ASC
LIMIT 50;
```

## Explanation
JOIN cards với accounts qua linked_account_no. NULLIF tránh chia 0. Filter available_balance < 10% credit_limit → thẻ gần max out. Use case: nhắc nhở KH hoặc risk monitoring.
