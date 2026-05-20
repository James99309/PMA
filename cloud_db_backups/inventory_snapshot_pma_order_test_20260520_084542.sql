--
-- PostgreSQL database dump
--

\restrict wsVvxMMIelkz6k9R81R1pKS8jBOr43pLHJ6JxCTpEfVn22dqRZELa2Muiw0H7aJ

-- Dumped from database version 14.19 (Homebrew)
-- Dumped by pg_dump version 14.19 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: inventory; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (1, 423, 35, 12, NULL, NULL, 0, 0, NULL, '2025-06-10 21:42:20.456089', '2025-06-10 21:42:20.456089', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (2, 424, 114, 12, NULL, NULL, 0, 0, NULL, '2025-06-10 21:42:45.86342', '2025-06-10 21:42:45.86342', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (3, 421, 179, 1, NULL, NULL, 0, 0, NULL, '2025-06-10 21:53:45.336488', '2025-06-10 21:53:45.336488', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (6, 4, 5, 25, '套', 'A-01-002', 5, 50, '测试库存数据 - SK海力士（无锡）产', '2025-06-10 22:46:00.990072', '2025-06-10 22:46:00.990073', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (7, 18, 6, 75, '套', 'B-02-001', 15, 150, '测试库存数据 - 创业慧康科技股份有限', '2025-06-10 22:46:00.991491', '2025-06-10 22:46:00.991491', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (8, 23, 7, 30, '套', 'B-02-002', 8, 60, '测试库存数据 - 杭州创业慧康股份有限', '2025-06-10 22:46:00.992413', '2025-06-10 22:46:00.992414', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (9, 31, 8, 100, '套', 'C-03-001', 20, 200, '测试库存数据 - 江苏航天大为科技股份', '2025-06-10 22:46:00.993703', '2025-06-10 22:46:00.993704', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (11, 4, 10, 80, '套', 'A-02-001', 10, 80, '测试库存数据 - SK海力士（无锡）产', '2025-06-10 22:46:00.995676', '2025-06-10 22:46:00.995676', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (12, 18, 11, 5, '套', 'B-03-001', 10, 50, '测试库存数据 - 创业慧康科技股份有限', '2025-06-10 22:46:00.996499', '2025-06-10 22:46:00.9965', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (13, 23, 12, 0, '个', 'B-03-002', 5, 25, '测试库存数据 - 杭州创业慧康股份有限', '2025-06-10 22:46:00.997298', '2025-06-10 22:46:00.997298', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (14, 31, 13, 120, '台', 'C-04-001', 25, 100, '测试库存数据 - 江苏航天大为科技股份', '2025-06-10 22:46:01.000253', '2025-06-10 22:46:01.000258', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (15, 424, 35, 12, NULL, NULL, 0, 0, NULL, '2025-06-11 07:02:50.011778', '2025-06-11 07:02:50.011778', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (39, 424, 32, 12, '套', NULL, 0, 0, NULL, '2025-07-20 11:25:50.670515', '2025-07-20 11:25:50.670515', 18);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (16, 424, 24, 4, NULL, NULL, 0, 0, NULL, '2025-06-12 11:16:48.933771', '2025-06-12 11:17:24.964563', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (30, 129, 90, 9, NULL, NULL, 0, 0, NULL, '2025-07-19 13:44:22.918423', '2025-07-20 11:33:02.580554', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (24, 129, 25, 22, NULL, NULL, 0, 0, NULL, '2025-07-19 13:41:39.741229', '2025-07-20 11:33:02.580554', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (28, 129, 104, 200, NULL, NULL, 0, 0, NULL, '2025-07-19 13:44:22.909869', '2025-07-20 11:33:02.580554', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (19, 424, 60, 0, NULL, NULL, 0, 0, NULL, '2025-06-12 18:55:10.99042', '2025-06-12 19:31:58.705506', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (20, 4, 36, 10, NULL, NULL, 0, 0, NULL, '2025-06-12 19:41:14.331646', '2025-06-12 19:41:14.331646', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (21, 424, 93, 7, NULL, NULL, 0, 0, NULL, '2025-06-12 22:05:04.906068', '2025-06-12 22:05:04.906068', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (22, 424, 64, 8, NULL, NULL, 0, 0, NULL, '2025-06-12 22:05:04.93394', '2025-06-12 22:05:04.93394', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (37, 424, 90, 201, '套', NULL, 0, 0, NULL, '2025-07-20 11:24:04.240845', '2025-07-20 11:43:10.626311', 18);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (25, 129, 60, 10, NULL, NULL, 0, 0, NULL, '2025-07-19 13:44:22.890792', '2025-07-19 13:44:22.890792', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (29, 129, 88, 100, NULL, NULL, 0, 0, NULL, '2025-07-19 13:44:22.913881', '2025-07-19 13:44:22.913881', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (32, 300, 115, 50, NULL, '测试仓库', 10, 0, NULL, '2025-07-19 15:11:19.342904', '2025-07-19 15:11:19.342904', 11);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (27, 129, 71, 3, NULL, NULL, 0, 0, NULL, '2025-07-19 13:44:22.905198', '2025-07-19 15:12:25.798745', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (33, 129, 115, 40, NULL, NULL, 0, 0, NULL, '2025-07-19 15:39:05.397602', '2025-07-19 15:50:12.767544', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (23, 129, 19, 12, NULL, NULL, 0, 0, NULL, '2025-07-19 13:41:39.714075', '2025-07-19 15:57:46.949919', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (26, 129, 64, 8, NULL, NULL, 0, 0, NULL, '2025-07-19 13:44:22.897164', '2025-07-19 16:04:14.875077', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (34, 129, 39, 5, NULL, NULL, 0, 0, NULL, '2025-07-19 16:06:44.43472', '2025-07-19 16:06:44.43472', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (35, 129, 38, 5, NULL, NULL, 0, 0, NULL, '2025-07-19 16:06:44.441769', '2025-07-19 16:06:44.441769', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (36, 129, 93, 100, NULL, NULL, 0, 0, NULL, '2025-07-19 16:06:44.445579', '2025-07-19 16:06:44.445579', 5);
INSERT INTO public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) VALUES (38, 424, 26, 10, '套', NULL, 0, 0, NULL, '2025-07-20 11:24:07.756419', '2025-07-20 11:24:07.756419', 18);


--
-- Data for Name: inventory_transactions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (1, 1, 'in', 12, 0, 12, 'manual', NULL, '', '2025-06-10 21:42:20.456089', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (2, 2, 'in', 12, 0, 12, 'manual', NULL, '', '2025-06-10 21:42:45.86342', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (3, 3, 'in', 1, 0, 1, 'manual', NULL, '', '2025-06-10 21:53:45.336488', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (4, 15, 'in', 12, 0, 12, 'manual', NULL, '', '2025-06-11 07:02:50.011778', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (5, 16, 'in', 2, 0, 2, 'manual', NULL, '', '2025-06-12 11:16:48.933771', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (6, 16, 'settlement', 2, 2, 4, 'settlement', 1, '结算单SO202506-006产品结算: 分路器', '2025-06-12 11:17:24.951013', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (7, 19, 'in', 4, 0, 4, 'manual', NULL, '', '2025-06-12 18:55:10.99042', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (8, 19, 'out', -4, 4, 0, 'settlement', 357, '结算出库 - SO202506-005（部分结算：4件）', '2025-06-12 19:31:58.691166', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (9, 20, 'in', 10, 0, 10, 'manual', NULL, '', '2025-06-12 19:41:14.331646', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (10, 21, 'in', 7, 0, 7, 'manual', NULL, '批量添加库存 - 定向耦合器', '2025-06-12 22:05:04.906068', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (11, 22, 'in', 8, 0, 8, 'manual', NULL, '批量添加库存 - 智能光纤近端机', '2025-06-12 22:05:04.93394', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (12, 23, 'in', 10, 0, 10, 'manual', NULL, '批量添加库存 - 定向耦合合路器', '2025-07-19 13:41:39.714075', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (13, 24, 'in', 10, 0, 10, 'manual', NULL, '批量添加库存 - 分路器', '2025-07-19 13:41:39.741229', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (14, 23, 'in', 3, 10, 13, 'manual', NULL, '批量添加库存 - 定向耦合合路器', '2025-07-19 13:42:21.353367', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (15, 24, 'in', 3, 10, 13, 'manual', NULL, '批量添加库存 - 分路器', '2025-07-19 13:42:21.359108', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (16, 25, 'in', 10, 0, 10, 'manual', NULL, '批量添加库存 - 常规射频直放站', '2025-07-19 13:44:22.890792', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (17, 26, 'in', 10, 0, 10, 'manual', NULL, '批量添加库存 - 智能光纤近端机', '2025-07-19 13:44:22.897164', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (18, 27, 'in', 10, 0, 10, 'manual', NULL, '批量添加库存 - 智能光纤远端直放站', '2025-07-19 13:44:22.905198', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (19, 28, 'in', 200, 0, 200, 'manual', NULL, '批量添加库存 - 超薄室内全向吸顶天线', '2025-07-19 13:44:22.909869', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (20, 29, 'in', 100, 0, 100, 'manual', NULL, '批量添加库存 - 定向耦合器', '2025-07-19 13:44:22.913881', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (21, 30, 'in', 50, 0, 50, 'manual', NULL, '批量添加库存 - 功率分配器', '2025-07-19 13:44:22.918423', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (22, 27, 'out', 7, 10, 3, 'settlement', 1555, '结算出库 - SO202506-023', '2025-07-19 15:12:25.791879', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (23, 33, 'in', 100, 0, 100, 'manual', NULL, '批量添加库存 - DMR常规对讲机', '2025-07-19 15:39:05.397602', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (24, 33, 'out', 20, 100, 80, 'settlement', 1398, '结算出库 - SO202506-020', '2025-07-19 15:39:29.050986', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (25, 33, 'out', 40, 80, 40, 'settlement', 1312, '结算出库 - SO202506-019', '2025-07-19 15:50:12.761917', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (26, 24, 'out', 1, 13, 12, 'settlement', 1562, '结算出库 - SO202506-023', '2025-07-19 15:57:23.257365', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (27, 23, 'out', 1, 13, 12, 'settlement', 1561, '结算出库 - SO202506-023', '2025-07-19 15:57:46.919284', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (28, 30, 'out', 50, 50, 0, 'settlement', 1560, '结算出库 - SO202506-023', '2025-07-19 15:58:31.665143', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (29, 28, 'out', 200, 200, 0, 'settlement', 1556, '结算出库 - SO202506-023', '2025-07-19 16:04:00.998668', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (30, 26, 'out', 2, 10, 8, 'settlement', 1558, '结算出库 - SO202506-023', '2025-07-19 16:04:14.86976', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (31, 34, 'in', 5, 0, 5, 'manual', NULL, '批量添加库存 - 上行信号剥离器', '2025-07-19 16:06:44.43472', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (32, 35, 'in', 5, 0, 5, 'manual', NULL, '批量添加库存 - 下行信号剥离器', '2025-07-19 16:06:44.441769', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (33, 36, 'in', 100, 0, 100, 'manual', NULL, '批量添加库存 - 定向耦合器', '2025-07-19 16:06:44.445579', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (34, 30, 'in', 1, 0, 1, 'manual', NULL, '手动入库', '2025-07-19 17:34:02.341285', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (35, 30, 'out', -1, 1, 0, 'manual', NULL, '手动出库', '2025-07-19 17:34:14.458124', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (36, 30, 'adjustment', 1, 0, 1, 'manual', NULL, '库存调整至1', '2025-07-19 17:34:35.294325', 5);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (37, 37, 'in', 200, 0, 200, 'order', 5, '订单入库：PUO202507-002 - 功率分配器', '2025-07-20 11:24:04.240845', 18);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (38, 38, 'in', 10, 0, 10, 'order', 5, '批量入库：PUO202507-002 - 分路器', '2025-07-20 11:24:07.756419', 18);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (39, 39, 'in', 12, 0, 12, 'order', 6, '批量入库：PUO202507-003 - 信号剥离矩阵', '2025-07-20 11:25:50.670515', 18);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (40, 30, 'in', 8, 1, 9, 'order', 4, '批量入库：PUO202507-001 - 功率分配器', '2025-07-20 11:33:02.580554', 18);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (41, 24, 'in', 10, 12, 22, 'order', 4, '批量入库：PUO202507-001 - 分路器', '2025-07-20 11:33:02.580554', 18);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (42, 28, 'in', 200, 0, 200, 'order', 4, '批量入库：PUO202507-001 - 超薄室内全向吸顶天线', '2025-07-20 11:33:02.580554', 18);
INSERT INTO public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) VALUES (43, 37, 'in', 1, 200, 201, 'order', 3, '批量入库：PUO202506-001 - 功率分配器', '2025-07-20 11:43:10.626311', 18);


--
-- Data for Name: product_serial_numbers; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: settlements; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.settlements (id, settlement_number, company_id, settlement_date, status, total_items, description, created_by_id, approved_by_id, approved_at, created_at, updated_at) VALUES (1, 'INV-SO202506-006', 424, '2025-06-12 11:17:24.964574', 'completed', 1, '结算单 SO202506-006 产品结算', 5, 5, '2025-06-12 11:17:24.964595', '2025-06-12 11:17:24.951013', '2025-06-12 11:17:24.951013');


--
-- Data for Name: settlement_details; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.settlement_details (id, settlement_id, inventory_id, product_id, quantity_settled, quantity_before, quantity_after, unit, notes) VALUES (1, 1, 16, 24, 2, 2, 4, '套', '结算单SO202506-006产品结算');


--
-- Name: inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_id_seq', 39, true);


--
-- Name: inventory_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_transactions_id_seq', 43, true);


--
-- Name: product_serial_numbers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_serial_numbers_id_seq', 1, false);


--
-- Name: settlement_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.settlement_details_id_seq', 1, true);


--
-- Name: settlements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.settlements_id_seq', 1, true);


--
-- PostgreSQL database dump complete
--

\unrestrict wsVvxMMIelkz6k9R81R1pKS8jBOr43pLHJ6JxCTpEfVn22dqRZELa2Muiw0H7aJ

