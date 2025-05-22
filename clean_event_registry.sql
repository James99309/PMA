--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 16.8 (Homebrew)

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
-- Data for Name: event_registry; Type: TABLE DATA; Schema: public; Owner: nijie
--

INSERT INTO public.event_registry VALUES (1, 'project_created', '项目创建', 'Project Created', true, true, '2025-05-17 17:15:52.835698', '2025-05-17 17:15:52.835704');
INSERT INTO public.event_registry VALUES (2, 'project_status_updated', '项目状态更新', 'Project Status Updated', true, true, '2025-05-17 17:15:52.835704', '2025-05-17 17:15:52.835705');
INSERT INTO public.event_registry VALUES (3, 'quotation_created', '报价单创建', 'Quotation Created', true, true, '2025-05-17 17:15:52.835705', '2025-05-17 17:15:52.835706');
INSERT INTO public.event_registry VALUES (4, 'customer_created', '客户创建', 'Customer Created', false, true, '2025-05-17 17:15:52.835706', '2025-05-17 17:15:52.835707');


--
-- Name: event_registry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: nijie
--

SELECT pg_catalog.setval('public.event_registry_id_seq', 9, true);


--
-- PostgreSQL database dump complete
--

