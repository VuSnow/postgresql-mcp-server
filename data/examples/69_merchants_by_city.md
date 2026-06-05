# Merchant theo thành phố — phân bổ

## Complexity: simple

## Tables Used: merchants

## Question (Vietnamese)
Có bao nhiêu merchant ở mỗi thành phố? Liệt kê top 10 thành phố có nhiều merchant nhất.

## Join Logic
- Chỉ cần bảng `merchants`.
- GROUP BY city để đếm merchant theo thành phố.

## SQL
```sql
SELECT
    city,
    COUNT(*) AS merchant_count,
    COUNT(DISTINCT merchant_category) AS category_count
FROM merchants
WHERE status = 'ACTIVE'
  AND city IS NOT NULL
GROUP BY city
ORDER BY merchant_count DESC
LIMIT 10;
```

## Explanation
Aggregation đơn giản. COUNT DISTINCT merchant_category cho biết đa dạng danh mục trong mỗi TP. Filter city IS NOT NULL loại bỏ merchant không có thông tin TP.
