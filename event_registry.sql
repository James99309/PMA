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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: event_registry; Type: TABLE; Schema: public; Owner: nijie
--

CREATE TABLE public.event_registry (
    id integer NOT NULL,
    event_key character varying(50) NOT NULL,
    label_zh character varying(100) NOT NULL,
    label_en character varying(100),
    default_enabled boolean,
    enabled boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.event_registry OWNER TO nijie;

--
-- Name: event_registry_id_seq; Type: SEQUENCE; Schema: public; Owner: nijie
--

CREATE SEQUENCE public.event_registry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.event_registry_id_seq OWNER TO nijie;

--
-- Name: event_registry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nijie
--

ALTER SEQUENCE public.event_registry_id_seq OWNED BY public.event_registry.id;


--
-- Name: event_registry id; Type: DEFAULT; Schema: public; Owner: nijie
--

ALTER TABLE ONLY public.event_registry ALTER COLUMN id SET DEFAULT nextval('public.event_registry_id_seq'::regclass);


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
-- Name: event_registry event_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: nijie
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_pkey PRIMARY KEY (id);


--
-- Name: ix_event_registry_event_key; Type: INDEX; Schema: public; Owner: nijie
--

CREATE UNIQUE INDEX ix_event_registry_event_key ON public.event_registry USING btree (event_key);


--
-- PostgreSQL database dump complete
--

