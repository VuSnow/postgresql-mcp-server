-- Branches table: bank branch offices
-- Idempotent: safe to run multiple times

DROP TABLE IF EXISTS public.branches CASCADE;

CREATE TABLE IF NOT EXISTS public.branches (
    id              SERIAL PRIMARY KEY,
    branch_code     VARCHAR(10) UNIQUE NOT NULL,
    branch_name     VARCHAR(100) NOT NULL,
    city            VARCHAR(50) NOT NULL,
    district        VARCHAR(50),
    address         TEXT NOT NULL,
    phone           VARCHAR(20),
    manager_name    VARCHAR(100),
    is_atm_only     BOOLEAN DEFAULT FALSE,
    opened_date     DATE NOT NULL,
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'closed', 'renovating'))
);

INSERT INTO public.branches (id, branch_code, branch_name, city, district, address, phone, manager_name, is_atm_only, opened_date, status) VALUES
(1, 'HCM-001', 'Chi nhanh Q1 - Le Loi',        'Ho Chi Minh', 'Quan 1',     '100 Le Loi, Phuong Ben Thanh, Quan 1',    '028-3822-0001', 'Nguyen Thanh Tung', FALSE, '2010-03-15', 'active'),
(2, 'HCM-002', 'Chi nhanh Q3 - Vo Van Tan',    'Ho Chi Minh', 'Quan 3',     '200 Vo Van Tan, Phuong 5, Quan 3',        '028-3930-0002', 'Le Thi Huong',      FALSE, '2012-07-20', 'active'),
(3, 'HCM-003', 'Chi nhanh Q7 - Phu My Hung',   'Ho Chi Minh', 'Quan 7',     '45 Nguyen Luong Bang, Tan Phu, Quan 7',   '028-5411-0003', 'Tran Van Minh',     FALSE, '2015-01-10', 'active'),
(4, 'HN-001',  'Chi nhanh Hoan Kiem',           'Ha Noi',      'Hoan Kiem',  '10 Trang Tien, Hoan Kiem',                '024-3825-0001', 'Pham Duc Anh',      FALSE, '2008-11-01', 'active'),
(5, 'HN-002',  'Chi nhanh Cau Giay',            'Ha Noi',      'Cau Giay',   '88 Xuan Thuy, Cau Giay',                 '024-3795-0002', 'Vu Thi Lan',        FALSE, '2014-05-25', 'active'),
(6, 'DN-001',  'Chi nhanh Da Nang',             'Da Nang',     'Hai Chau',   '55 Bach Dang, Hai Chau',                  '0236-382-0001', 'Ho Van Khanh',      FALSE, '2011-09-12', 'active'),
(7, 'HUE-001', 'Chi nhanh Hue',                 'Hue',         'TP Hue',     '12 Tran Hung Dao, TP Hue',                '0234-382-0001', 'Dang Thi Mai',      FALSE, '2016-04-08', 'active'),
(8, 'HCM-ATM-001', 'ATM Vincom Q1',            'Ho Chi Minh', 'Quan 1',     'B1 Vincom Center, 72 Le Thanh Ton, Q1',   NULL,            NULL,                TRUE,  '2018-06-01', 'active'),
(9, 'HN-ATM-001',  'ATM Lotte Ha Noi',         'Ha Noi',      'Ba Dinh',    '54 Lieu Giai, Ba Dinh',                   NULL,            NULL,                TRUE,  '2019-03-15', 'active'),
(10, 'HCM-004', 'Chi nhanh Thu Duc',            'Ho Chi Minh', 'Thu Duc',    '300 Vo Van Ngan, Thu Duc',                '028-3896-0004', NULL,                FALSE, '2020-02-01', 'renovating');

SELECT setval('public.branches_id_seq', 10);
