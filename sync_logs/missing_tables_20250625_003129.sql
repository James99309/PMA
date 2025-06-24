--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 16.9 (Homebrew)

-- Started on 2025-06-25 00:31:29 +08

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

ALTER TABLE IF EXISTS ONLY public.performance_targets DROP CONSTRAINT IF EXISTS performance_targets_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.performance_targets DROP CONSTRAINT IF EXISTS performance_targets_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.performance_targets DROP CONSTRAINT IF EXISTS performance_targets_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.performance_statistics DROP CONSTRAINT IF EXISTS performance_statistics_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.five_star_project_baselines DROP CONSTRAINT IF EXISTS five_star_project_baselines_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.five_star_project_baselines DROP CONSTRAINT IF EXISTS five_star_project_baselines_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.performance_targets DROP CONSTRAINT IF EXISTS unique_user_year_month;
ALTER TABLE IF EXISTS ONLY public.performance_statistics DROP CONSTRAINT IF EXISTS unique_statistics_user_year_month;
ALTER TABLE IF EXISTS ONLY public.five_star_project_baselines DROP CONSTRAINT IF EXISTS unique_baseline_user;
ALTER TABLE IF EXISTS ONLY public.performance_targets DROP CONSTRAINT IF EXISTS performance_targets_pkey;
ALTER TABLE IF EXISTS ONLY public.performance_statistics DROP CONSTRAINT IF EXISTS performance_statistics_pkey;
ALTER TABLE IF EXISTS ONLY public.five_star_project_baselines DROP CONSTRAINT IF EXISTS five_star_project_baselines_pkey;
ALTER TABLE IF EXISTS public.performance_targets ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.performance_statistics ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.five_star_project_baselines ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.performance_targets_id_seq;
DROP TABLE IF EXISTS public.performance_targets;
DROP SEQUENCE IF EXISTS public.performance_statistics_id_seq;
DROP TABLE IF EXISTS public.performance_statistics;
DROP SEQUENCE IF EXISTS public.five_star_project_baselines_id_seq;
DROP TABLE IF EXISTS public.five_star_project_baselines;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 321 (class 1259 OID 30155)
-- Name: five_star_project_baselines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.five_star_project_baselines (
    id integer NOT NULL,
    user_id integer NOT NULL,
    baseline_year integer NOT NULL,
    baseline_month integer NOT NULL,
    baseline_count integer,
    created_at timestamp without time zone,
    created_by integer
);


--
-- TOC entry 4044 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN five_star_project_baselines.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.five_star_project_baselines.user_id IS '用户ID';


--
-- TOC entry 4045 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN five_star_project_baselines.baseline_year; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.five_star_project_baselines.baseline_year IS '基线年份';


--
-- TOC entry 4046 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN five_star_project_baselines.baseline_month; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.five_star_project_baselines.baseline_month IS '基线月份';


--
-- TOC entry 4047 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN five_star_project_baselines.baseline_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.five_star_project_baselines.baseline_count IS '基线五星项目数量';


--
-- TOC entry 4048 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN five_star_project_baselines.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.five_star_project_baselines.created_at IS '创建时间';


--
-- TOC entry 320 (class 1259 OID 30154)
-- Name: five_star_project_baselines_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.five_star_project_baselines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4049 (class 0 OID 0)
-- Dependencies: 320
-- Name: five_star_project_baselines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.five_star_project_baselines_id_seq OWNED BY public.five_star_project_baselines.id;


--
-- TOC entry 319 (class 1259 OID 30139)
-- Name: performance_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performance_statistics (
    id integer NOT NULL,
    user_id integer NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    implant_amount_actual double precision,
    sales_amount_actual double precision,
    new_customers_actual integer,
    new_projects_actual integer,
    five_star_projects_actual integer,
    industry_statistics json,
    calculated_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- TOC entry 4050 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN performance_statistics.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.user_id IS '用户ID';


--
-- TOC entry 4051 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN performance_statistics.year; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.year IS '年份';


--
-- TOC entry 4052 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN performance_statistics.month; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.month IS '月份';


--
-- TOC entry 4053 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN performance_statistics.implant_amount_actual; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.implant_amount_actual IS '植入额实际完成';


--
-- TOC entry 4054 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN performance_statistics.sales_amount_actual; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.sales_amount_actual IS '销售额实际完成';


--
-- TOC entry 4055 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN performance_statistics.new_customers_actual; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.new_customers_actual IS '新增客户数实际完成';


--
-- TOC entry 4056 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN performance_statistics.new_projects_actual; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.new_projects_actual IS '新增项目数实际完成';


--
-- TOC entry 4057 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN performance_statistics.five_star_projects_actual; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.five_star_projects_actual IS '五星项目增量实际完成';


--
-- TOC entry 4058 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN performance_statistics.industry_statistics; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.industry_statistics IS '行业维度统计数据';


--
-- TOC entry 4059 (class 0 OID 0)
-- Dependencies: 319
-- Name: COLUMN performance_statistics.calculated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.calculated_at IS '统计计算时间';


--
-- TOC entry 318 (class 1259 OID 30138)
-- Name: performance_statistics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.performance_statistics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4060 (class 0 OID 0)
-- Dependencies: 318
-- Name: performance_statistics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_statistics_id_seq OWNED BY public.performance_statistics.id;


--
-- TOC entry 317 (class 1259 OID 30120)
-- Name: performance_targets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performance_targets (
    id integer NOT NULL,
    user_id integer NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    implant_amount_target double precision,
    sales_amount_target double precision,
    new_customers_target integer,
    new_projects_target integer,
    five_star_projects_target integer,
    display_currency character varying(10),
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    updated_by integer
);


--
-- TOC entry 4061 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.user_id IS '用户ID';


--
-- TOC entry 4062 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.year; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.year IS '年份';


--
-- TOC entry 4063 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.month; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.month IS '月份';


--
-- TOC entry 4064 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.implant_amount_target; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.implant_amount_target IS '植入额目标';


--
-- TOC entry 4065 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.sales_amount_target; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.sales_amount_target IS '销售额目标';


--
-- TOC entry 4066 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.new_customers_target; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.new_customers_target IS '新增客户数目标';


--
-- TOC entry 4067 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.new_projects_target; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.new_projects_target IS '新增项目数目标';


--
-- TOC entry 4068 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.five_star_projects_target; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.five_star_projects_target IS '五星项目增量目标';


--
-- TOC entry 4069 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.display_currency; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.display_currency IS '用户选择的展示货币';


--
-- TOC entry 4070 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.created_by IS '创建人';


--
-- TOC entry 4071 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.created_at IS '创建时间';


--
-- TOC entry 4072 (class 0 OID 0)
-- Dependencies: 317
-- Name: COLUMN performance_targets.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.updated_at IS '更新时间';


--
-- TOC entry 316 (class 1259 OID 30119)
-- Name: performance_targets_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.performance_targets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4073 (class 0 OID 0)
-- Dependencies: 316
-- Name: performance_targets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_targets_id_seq OWNED BY public.performance_targets.id;


--
-- TOC entry 3875 (class 2604 OID 30158)
-- Name: five_star_project_baselines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.five_star_project_baselines ALTER COLUMN id SET DEFAULT nextval('public.five_star_project_baselines_id_seq'::regclass);


--
-- TOC entry 3872 (class 2604 OID 30142)
-- Name: performance_statistics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_statistics ALTER COLUMN id SET DEFAULT nextval('public.performance_statistics_id_seq'::regclass);


--
-- TOC entry 3871 (class 2604 OID 30123)
-- Name: performance_targets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_targets ALTER COLUMN id SET DEFAULT nextval('public.performance_targets_id_seq'::regclass);


--
-- TOC entry 4038 (class 0 OID 30155)
-- Dependencies: 321
-- Data for Name: five_star_project_baselines; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.five_star_project_baselines (id, user_id, baseline_year, baseline_month, baseline_count, created_at, created_by) FROM stdin;
1	5	2025	1	0	2025-06-24 16:14:59.079681	\N
2	15	2025	1	0	2025-06-24 21:35:27.583925	\N
\.


--
-- TOC entry 4036 (class 0 OID 30139)
-- Dependencies: 319
-- Data for Name: performance_statistics; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.performance_statistics (id, user_id, year, month, implant_amount_actual, sales_amount_actual, new_customers_actual, new_projects_actual, five_star_projects_actual, industry_statistics, calculated_at, created_at, updated_at) FROM stdin;
1	5	2025	1	0	0	0	0	0	{}	2025-06-24 16:14:59.087819	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
2	5	2025	2	0	0	0	0	0	{}	2025-06-24 16:14:59.099404	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
3	5	2025	3	0	0	0	0	0	{}	2025-06-24 16:14:59.113133	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
4	5	2025	4	0	0	0	0	0	{}	2025-06-24 16:14:59.121264	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
5	5	2025	5	461016	0	0	9	0	{}	2025-06-24 16:14:59.12929	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
6	5	2025	6	83262.04	6416320.08	0	2	0	{}	2025-06-24 16:14:59.753447	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
7	5	2025	7	0	0	0	0	0	{}	2025-06-24 16:14:59.768273	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
8	5	2025	8	0	0	0	0	0	{}	2025-06-24 16:14:59.77815	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
9	5	2025	9	0	0	0	0	0	{}	2025-06-24 16:14:59.789501	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
10	5	2025	10	0	0	0	0	0	{}	2025-06-24 16:14:59.800016	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
11	5	2025	11	0	0	0	0	0	{}	2025-06-24 16:14:59.810654	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
12	5	2025	12	0	0	0	0	0	{}	2025-06-24 16:14:59.819642	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
13	15	2025	1	1327059	0	0	3	0	{}	2025-06-24 21:35:27.589841	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
14	15	2025	2	0	0	0	3	0	{}	2025-06-24 21:35:27.602315	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
15	15	2025	3	284868	0	0	3	0	{}	2025-06-24 21:35:27.614044	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
16	15	2025	4	721815	0	0	5	0	{}	2025-06-24 21:35:27.628414	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
17	15	2025	5	0	0	0	0	0	{}	2025-06-24 21:35:27.636608	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
18	15	2025	6	0	184645.66	0	0	0	{}	2025-06-24 21:35:27.644585	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
19	15	2025	7	0	0	0	0	0	{}	2025-06-24 21:35:27.652534	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
20	15	2025	8	0	0	0	0	0	{}	2025-06-24 21:35:27.660171	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
21	15	2025	9	0	0	0	0	0	{}	2025-06-24 21:35:27.668135	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
22	15	2025	10	0	0	0	0	0	{}	2025-06-24 21:35:27.675768	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
23	15	2025	11	0	0	0	0	0	{}	2025-06-24 21:35:27.683271	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
24	15	2025	12	0	0	0	0	0	{}	2025-06-24 21:35:27.690792	2025-06-25 00:08:05.713513	2025-06-25 00:08:05.713513
\.


--
-- TOC entry 4034 (class 0 OID 30120)
-- Dependencies: 317
-- Data for Name: performance_targets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.performance_targets (id, user_id, year, month, implant_amount_target, sales_amount_target, new_customers_target, new_projects_target, five_star_projects_target, display_currency, created_by, created_at, updated_at, updated_by) FROM stdin;
2	5	2025	12	2000000	50000	4	6	3	CNY	5	2025-06-24 21:38:36.498317	2025-06-24 21:38:36.498322	\N
3	5	2025	11	2000000	50000	4	6	3	CNY	5	2025-06-24 21:38:37.372794	2025-06-24 21:38:37.372798	\N
4	5	2025	10	2000000	50000	4	6	3	CNY	5	2025-06-24 21:38:38.163975	2025-06-24 21:38:38.163981	\N
5	5	2025	7	2000000	50000	4	6	3	CNY	5	2025-06-24 21:38:39.375246	2025-06-24 21:38:39.375248	\N
6	5	2025	8	2000000	50000	4	6	3	CNY	5	2025-06-24 21:38:40.124587	2025-06-24 21:38:40.124592	\N
7	5	2025	9	2000000	50000	4	6	3	CNY	5	2025-06-24 21:38:40.858206	2025-06-24 21:38:40.858211	\N
9	5	2025	5	2000000	50000	4	6	3	CNY	5	2025-06-24 21:38:42.838076	2025-06-24 21:38:42.83808	\N
10	5	2025	4	2000000	50000	4	6	3	CNY	5	2025-06-24 21:38:43.51754	2025-06-24 21:38:43.517543	\N
12	5	2025	3	2000000	50000	4	6	3	CNY	5	2025-06-24 21:38:45.897188	2025-06-24 21:38:45.897192	\N
14	15	2025	1	1000000	500000	5	10	2	CNY	5	2025-06-24 21:55:33.974914	2025-06-24 21:55:33.97492	\N
15	15	2025	2	800000	400000	4	8	1	CNY	5	2025-06-24 21:56:17.515427	2025-06-24 21:56:17.515429	\N
16	15	2025	3	1200000	600000	6	12	3	CNY	5	2025-06-24 21:56:17.517351	2025-06-24 21:56:17.517352	\N
17	15	2025	4	900000	450000	4	9	2	CNY	5	2025-06-24 21:56:17.518594	2025-06-24 21:56:17.518596	\N
18	15	2025	5	1100000	550000	5	11	2	CNY	5	2025-06-24 21:56:17.519581	2025-06-24 21:56:17.519582	\N
19	15	2025	6	1000000	500000	5	10	2	CNY	5	2025-06-24 21:56:17.520521	2025-06-24 21:56:17.520522	\N
20	15	2025	7	1300000	650000	6	13	3	CNY	5	2025-06-24 21:56:17.521256	2025-06-24 21:56:17.521257	\N
21	15	2025	8	1000000	500000	5	10	2	CNY	5	2025-06-24 21:56:17.522032	2025-06-24 21:56:17.522033	\N
22	15	2025	9	1100000	550000	5	11	2	CNY	5	2025-06-24 21:56:17.522741	2025-06-24 21:56:17.522741	\N
23	15	2025	10	1200000	600000	6	12	3	CNY	5	2025-06-24 21:56:17.523402	2025-06-24 21:56:17.523402	\N
24	15	2025	11	1000000	500000	5	10	2	CNY	5	2025-06-24 21:56:17.523973	2025-06-24 21:56:17.523973	\N
25	15	2025	12	1500000	750000	7	15	4	CNY	5	2025-06-24 21:56:17.524517	2025-06-24 21:56:17.524517	\N
1	5	2025	1	0	0	0	0	0	CNY	5	2025-06-24 21:37:09.935552	2025-06-24 21:58:33.033393	\N
11	5	2025	2	0	0	0	0	0	CNY	5	2025-06-24 21:38:45.306839	2025-06-24 21:58:41.815093	\N
8	5	2025	6	30000	20000	2	6	3	CNY	5	2025-06-24 21:38:42.198057	2025-06-24 21:59:09.581552	\N
\.


--
-- TOC entry 4074 (class 0 OID 0)
-- Dependencies: 320
-- Name: five_star_project_baselines_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.five_star_project_baselines_id_seq', 2, true);


--
-- TOC entry 4075 (class 0 OID 0)
-- Dependencies: 318
-- Name: performance_statistics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.performance_statistics_id_seq', 24, true);


--
-- TOC entry 4076 (class 0 OID 0)
-- Dependencies: 316
-- Name: performance_targets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.performance_targets_id_seq', 25, true);


--
-- TOC entry 3885 (class 2606 OID 30160)
-- Name: five_star_project_baselines five_star_project_baselines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.five_star_project_baselines
    ADD CONSTRAINT five_star_project_baselines_pkey PRIMARY KEY (id);


--
-- TOC entry 3881 (class 2606 OID 30146)
-- Name: performance_statistics performance_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_statistics
    ADD CONSTRAINT performance_statistics_pkey PRIMARY KEY (id);


--
-- TOC entry 3877 (class 2606 OID 30125)
-- Name: performance_targets performance_targets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_targets
    ADD CONSTRAINT performance_targets_pkey PRIMARY KEY (id);


--
-- TOC entry 3887 (class 2606 OID 30162)
-- Name: five_star_project_baselines unique_baseline_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.five_star_project_baselines
    ADD CONSTRAINT unique_baseline_user UNIQUE (user_id);


--
-- TOC entry 3883 (class 2606 OID 30148)
-- Name: performance_statistics unique_statistics_user_year_month; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_statistics
    ADD CONSTRAINT unique_statistics_user_year_month UNIQUE (user_id, year, month);


--
-- TOC entry 3879 (class 2606 OID 30127)
-- Name: performance_targets unique_user_year_month; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_targets
    ADD CONSTRAINT unique_user_year_month UNIQUE (user_id, year, month);


--
-- TOC entry 3892 (class 2606 OID 30178)
-- Name: five_star_project_baselines five_star_project_baselines_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.five_star_project_baselines
    ADD CONSTRAINT five_star_project_baselines_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3893 (class 2606 OID 30163)
-- Name: five_star_project_baselines five_star_project_baselines_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.five_star_project_baselines
    ADD CONSTRAINT five_star_project_baselines_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3891 (class 2606 OID 30149)
-- Name: performance_statistics performance_statistics_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_statistics
    ADD CONSTRAINT performance_statistics_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3888 (class 2606 OID 30133)
-- Name: performance_targets performance_targets_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_targets
    ADD CONSTRAINT performance_targets_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3889 (class 2606 OID 30171)
-- Name: performance_targets performance_targets_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_targets
    ADD CONSTRAINT performance_targets_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- TOC entry 3890 (class 2606 OID 30128)
-- Name: performance_targets performance_targets_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_targets
    ADD CONSTRAINT performance_targets_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


-- Completed on 2025-06-25 00:31:29 +08

--
-- PostgreSQL database dump complete
--

