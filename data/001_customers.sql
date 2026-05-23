-- Customers table: banking customer profiles
-- Idempotent: safe to run multiple times

DROP TABLE IF EXISTS public.customers CASCADE;

CREATE TABLE IF NOT EXISTS public.customers (
    id              SERIAL PRIMARY KEY,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    phone           VARCHAR(20),
    date_of_birth   DATE,
    national_id     VARCHAR(20) UNIQUE,
    address         TEXT,
    city            VARCHAR(50),
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'closed')),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO public.customers (id, full_name, email, phone, date_of_birth, national_id, address, city, status, created_at) VALUES
(1, 'Nguyen Van An',     'an.nguyen@email.com',      '0901234567', '1990-05-15', '079090012345', '123 Le Loi, Q1',           'Ho Chi Minh', 'active',    '2023-01-10 08:00:00+07'),
(2, 'Tran Thi Binh',     'binh.tran@email.com',      '0912345678', '1985-11-20', '079085023456', '456 Nguyen Hue, Q1',       'Ho Chi Minh', 'active',    '2023-02-14 09:30:00+07'),
(3, 'Le Hoang Cuong',    'cuong.le@email.com',       '0923456789', '1992-03-08', '001092034567', '78 Hang Bai',              'Ha Noi',      'active',    '2023-03-01 10:00:00+07'),
(4, 'Pham Minh Duc',     'duc.pham@email.com',       '0934567890', '1988-07-25', '048088045678', '90 Bach Dang',             'Da Nang',     'active',    '2023-04-20 11:15:00+07'),
(5, 'Vo Thi Em',         'em.vo@email.com',          '0945678901', '1995-12-01', '079095056789', '12 Vo Van Tan, Q3',        'Ho Chi Minh', 'suspended', '2023-05-05 14:00:00+07'),
(6, 'Hoang Van Phuc',    'phuc.hoang@email.com',     '0956789012', '1991-09-10', '001091067890', '34 Kim Ma',                'Ha Noi',      'active',    '2023-06-15 08:45:00+07'),
(7, 'Dang Thi Giang',    'giang.dang@email.com',     '0967890123', '1987-04-18', '038087078901', '56 Tran Phu',              'Hue',         'active',    '2023-07-22 09:00:00+07'),
(8, 'Bui Quoc Huy',      'huy.bui@email.com',        '0978901234', '1993-08-30', '079093089012', '89 Nguyen Dinh Chieu, Q3', 'Ho Chi Minh', 'active',    '2023-08-10 16:30:00+07'),
(9, 'Ngo Thanh Inh',     'inh.ngo@email.com',        '0989012345', '1996-01-22', '048096090123', '67 Ngo Quyen',             'Da Nang',     'closed',    '2023-09-01 07:00:00+07'),
(10, 'Ly Thi Kim',       'kim.ly@email.com',         '0990123456', '1989-06-14', '001089101234', '23 Doi Can',               'Ha Noi',      'active',    '2023-10-18 13:20:00+07');

SELECT setval('public.customers_id_seq', 10);
