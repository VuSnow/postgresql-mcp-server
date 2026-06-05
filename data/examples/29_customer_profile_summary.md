# Tổng hợp thông tin khách hàng (profile view)

## Complexity: complex

## Tables Used: customers, accounts, cards, transactions

## Question (Vietnamese)
Cho tôi thông tin tổng hợp về khách hàng CIF000001: số tài khoản, số thẻ, tổng giao dịch tháng này, và tổng chi tiêu.

## Join Logic
- Vấn đề fan-out: JOIN tất cả bảng cùng lúc → cartesian product (N accounts × M cards × K transactions).
- Giải pháp: dùng scalar subqueries trong SELECT.
- Mỗi subquery trả về đúng 1 giá trị → kết quả luôn 1 row.

## SQL
```sql
SELECT
    c.cif_no,
    c.full_name,
    c.kyc_level,
    c.status,
    (SELECT COUNT(*) FROM accounts a WHERE a.cif_no = c.cif_no AND a.status = 'ACTIVE') AS active_accounts,
    (SELECT COUNT(*) FROM cards ca WHERE ca.cif_no = c.cif_no AND ca.status = 'ACTIVE') AS active_cards,
    (SELECT COUNT(*)
     FROM transactions t
     WHERE t.cif_no = c.cif_no
       AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
       AND t.status = 'SUCCESS'
    ) AS txn_count_this_month,
    (SELECT COALESCE(SUM(amount), 0)
     FROM transactions t
     WHERE t.cif_no = c.cif_no
       AND t.direction = 'OUT'
       AND t.transaction_time >= DATE_TRUNC('month', CURRENT_DATE)
       AND t.status = 'SUCCESS'
    ) AS total_spent_this_month
FROM customers c
WHERE c.cif_no = 'CIF000001';
```

## Explanation
Scalar subqueries tránh fan-out problem. COALESCE(SUM(...), 0) tránh NULL khi không có giao dịch. Trade-off: scalar subqueries OK cho 1 KH, chậm cho danh sách nhiều KH.
