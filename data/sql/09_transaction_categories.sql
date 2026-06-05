-- transaction_categories data
BEGIN;

-- transaction_categories (20 rows)
INSERT INTO transaction_categories (category_id, category_code, category_name, category_group) VALUES
  ('fa45defc-de8f-5173-8b0a-366b8533fd0e', 'FOOD', 'An uong', 'SPENDING'),
  ('82fa388e-becc-53b4-9980-e141ca144df8', 'SHOPPING', 'Mua sam', 'SPENDING'),
  ('acc0d9f0-977e-5858-9981-7c22f26df124', 'TRANSPORT', 'Di chuyen', 'SPENDING'),
  ('4ecfbe52-8abc-53e2-b6a3-0bb910060f04', 'ENTERTAINMENT', 'Giai tri', 'SPENDING'),
  ('c2a4fdbf-1c5d-5a12-85b9-1806866c131f', 'GROCERIES', 'Sieu thi / Tap hoa', 'SPENDING'),
  ('0c208548-39e7-56a9-8f0c-7770ee56e590', 'CARD_PAYMENT', 'Thanh toan the', 'SPENDING'),
  ('6efaea39-4fd1-59aa-a81b-d89705f36f3f', 'TRANSFER', 'Chuyen khoan', 'TRANSFER'),
  ('a056f3e0-c309-546d-84f0-0f37db660097', 'FAMILY_TRANSFER', 'Chuyen khoan gia dinh', 'TRANSFER'),
  ('37b19597-7dfa-5867-8c50-54983997f594', 'RENT', 'Tien thue nha', 'TRANSFER'),
  ('9559bdbc-3175-5bc5-ad12-4d12da9c3f99', 'SALARY', 'Luong', 'INCOME'),
  ('18307fff-86b7-5226-9edf-a62c6fd4f260', 'INTEREST', 'Lai suat', 'INCOME'),
  ('bdaf3269-d9a0-5d81-b1c1-9240424b6991', 'REFUND', 'Hoan tien', 'INCOME'),
  ('11d8a18c-057b-5c06-942a-8188e74f50eb', 'CASH_DEPOSIT', 'Nap tien mat', 'INCOME'),
  ('9b3ebe1a-b894-5a73-8615-356a1bc2a34e', 'BILL_ELECTRICITY', 'Hoa don dien', 'BILL'),
  ('90942bff-e299-5932-bde4-ea5aec361dd5', 'BILL_WATER', 'Hoa don nuoc', 'BILL'),
  ('63ab23bb-7182-516f-ad60-8fa10449dee2', 'BILL_INTERNET', 'Hoa don internet', 'BILL'),
  ('a6b39adc-fce8-51c8-a937-bfcc53948dd7', 'PHONE_TOPUP', 'Nap dien thoai', 'BILL'),
  ('365e9b53-30f7-5423-8d20-febb758c4516', 'BANK_FEE', 'Phi ngan hang', 'FEE'),
  ('a57d1aed-a55d-5367-b993-6f9e4aac6c97', 'CASH_WITHDRAWAL', 'Rut tien mat', 'CASH'),
  ('acf90ecb-be0b-5d86-92cd-bac85e4ed851', 'OTHER', 'Khac', 'OTHER');

COMMIT;
