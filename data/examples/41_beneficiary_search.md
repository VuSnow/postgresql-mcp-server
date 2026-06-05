# Người nhận đã lưu — tra cứu theo tên

## Complexity: simple

## Tables Used: beneficiaries

## Question (Vietnamese)
Tìm người nhận có tên chứa "Nguyen" trong danh sách đã lưu của khách hàng CIF000010.

## Join Logic
- Chỉ cần bảng `beneficiaries` — tìm kiếm theo tên trong danh sách saved.
- Filter theo cif_no và dùng ILIKE cho fuzzy search.

## SQL
```sql
SELECT
    beneficiary_name,
    beneficiary_account_no,
    beneficiary_bank_name,
    nickname,
    last_used_at
FROM beneficiaries
WHERE cif_no = 'CIF000010'
  AND is_saved = TRUE
  AND beneficiary_name ILIKE '%Nguyen%'
ORDER BY last_used_at DESC NULLS LAST
LIMIT 10;
```

## Explanation
Query đơn giản. ILIKE cho case-insensitive search. Filter is_saved = TRUE chỉ lấy người nhận đã lưu. ORDER BY last_used_at để ưu tiên người nhận gần đây.
