--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Debian 16.9-1.pgdg120+1)
-- Dumped by pg_dump version 16.9 (Homebrew)

-- Started on 2025-07-14 09:12:47 CST

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
-- TOC entry 3593 (class 0 OID 20639)
-- Dependencies: 250
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: pma_db_ovs_user
--

COPY public.permissions (id, user_id, module, can_view, can_create, can_edit, can_delete) FROM stdin;
1	1	user	t	t	t	t
2	1	customer	t	t	t	t
3	1	project	t	t	t	t
4	1	quotation	t	t	t	t
5	1	product	t	t	t	t
6	1	admin	t	t	t	t
7	1	inventory	t	t	t	t
8	1	pricing_order	t	t	t	t
9	1	approval	t	t	t	t
10	1	backup	t	t	t	t
11	1	system	t	t	t	t
\.


--
-- TOC entry 3595 (class 0 OID 20803)
-- Dependencies: 296
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: pma_db_ovs_user
--

COPY public.role_permissions (id, role, module, can_view, can_create, can_edit, can_delete, pricing_discount_limit, settlement_discount_limit, permission_level, permission_level_description) FROM stdin;
14	sales_manager	project	t	t	t	t	\N	\N	personal	\N
15	sales_manager	customer	t	t	t	t	\N	\N	personal	\N
16	sales_manager	quotation	t	t	t	t	\N	\N	personal	\N
17	sales_manager	product	t	f	f	f	\N	\N	personal	\N
18	sales_manager	product_code	f	f	f	f	\N	\N	personal	\N
19	sales_manager	inventory	f	f	f	f	\N	\N	personal	\N
20	sales_manager	settlement	f	f	f	f	\N	\N	personal	\N
21	sales_manager	order	f	f	f	f	\N	\N	personal	\N
22	sales_manager	pricing_order	f	f	f	f	70	65	personal	\N
23	sales_manager	settlement_order	f	f	f	f	70	65	personal	\N
24	sales_manager	user	f	f	f	f	\N	\N	personal	\N
25	sales_manager	permission	f	f	f	f	\N	\N	personal	\N
26	sales_manager	project_rating	f	f	f	f	\N	\N	personal	\N
\.


--
-- TOC entry 3602 (class 0 OID 0)
-- Dependencies: 251
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_ovs_user
--

SELECT pg_catalog.setval('public.permissions_id_seq', 11, true);


--
-- TOC entry 3603 (class 0 OID 0)
-- Dependencies: 297
-- Name: role_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_ovs_user
--

SELECT pg_catalog.setval('public.role_permissions_id_seq', 26, true);


-- Completed on 2025-07-14 09:13:36 CST

--
-- PostgreSQL database dump complete
--

