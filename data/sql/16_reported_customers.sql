-- reported_customers data
BEGIN;

-- reported_customers (3 rows)
INSERT INTO reported_customers (reported_customer_id, cif_no, reported_account_count, valid_report_count, total_reported_amount, risk_score, risk_level, status, created_at, updated_at) VALUES
  ('131ec971-efed-5a6b-9f41-6e41b2e264d5', 'CIF000067', 1, 2, 49701987, 0.4, 'WATCH', 'ACTIVE', '2026-05-30 07:29:57', '2026-05-23 11:45:41'),
  ('26d68bc2-633d-51a3-898e-2528febcc262', 'CIF000080', 2, 4, 74015348, 0.7, 'FROZEN', 'ACTIVE', '2026-05-20 01:58:57', '2026-05-26 23:24:21'),
  ('8ce963ae-702f-5ba1-bba3-63599123eff0', 'CIF000071', 2, 2, 33205321, 0.7, 'FROZEN', 'ACTIVE', '2026-05-14 18:07:01', '2026-05-21 20:03:00');

COMMIT;
