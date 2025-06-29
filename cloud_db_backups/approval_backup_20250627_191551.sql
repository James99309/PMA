--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Debian 16.9-1.pgdg120+1)
-- Dumped by pg_dump version 16.9 (Homebrew)

-- Started on 2025-06-27 19:15:52 HKT

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

ALTER TABLE ONLY public.approval_step DROP CONSTRAINT approval_step_process_id_fkey;
ALTER TABLE ONLY public.approval_step DROP CONSTRAINT approval_step_approver_user_id_fkey;
ALTER TABLE ONLY public.approval_record DROP CONSTRAINT approval_record_step_id_fkey;
ALTER TABLE ONLY public.approval_record DROP CONSTRAINT approval_record_instance_id_fkey;
ALTER TABLE ONLY public.approval_record DROP CONSTRAINT approval_record_approver_id_fkey;
ALTER TABLE ONLY public.approval_process_template DROP CONSTRAINT approval_process_template_created_by_fkey;
ALTER TABLE ONLY public.approval_instance DROP CONSTRAINT approval_instance_process_id_fkey;
ALTER TABLE ONLY public.approval_instance DROP CONSTRAINT approval_instance_created_by_fkey;
ALTER TABLE ONLY public.approval_step DROP CONSTRAINT approval_step_pkey;
ALTER TABLE ONLY public.approval_record DROP CONSTRAINT approval_record_pkey;
ALTER TABLE ONLY public.approval_process_template DROP CONSTRAINT approval_process_template_pkey;
ALTER TABLE ONLY public.approval_instance DROP CONSTRAINT approval_instance_pkey;
ALTER TABLE public.approval_step ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.approval_record ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.approval_process_template ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.approval_instance ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE public.approval_step_id_seq;
DROP TABLE public.approval_step;
DROP SEQUENCE public.approval_record_id_seq;
DROP TABLE public.approval_record;
DROP SEQUENCE public.approval_process_template_id_seq;
DROP TABLE public.approval_process_template;
DROP SEQUENCE public.approval_instance_id_seq;
DROP TABLE public.approval_instance;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 277 (class 1259 OID 20719)
-- Name: approval_instance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.approval_instance (
    id integer NOT NULL,
    process_id integer NOT NULL,
    object_id integer NOT NULL,
    object_type character varying(50) NOT NULL,
    current_step integer,
    status public.approvalstatus,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    created_by integer NOT NULL,
    template_snapshot json,
    template_version character varying(50)
);


--
-- TOC entry 3629 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN approval_instance.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.process_id IS '流程模板ID';


--
-- TOC entry 3630 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN approval_instance.object_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_id IS '对应单据ID';


--
-- TOC entry 3631 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN approval_instance.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_type IS '单据类型（如 project）';


--
-- TOC entry 3632 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN approval_instance.current_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.current_step IS '当前步骤序号';


--
-- TOC entry 3633 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN approval_instance.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.status IS '状态';


--
-- TOC entry 3634 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN approval_instance.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.started_at IS '流程发起时间';


--
-- TOC entry 3635 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN approval_instance.ended_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.ended_at IS '审批完成时间';


--
-- TOC entry 3636 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN approval_instance.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.created_by IS '发起人ID';


--
-- TOC entry 3637 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN approval_instance.template_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_snapshot IS '创建时的模板快照';


--
-- TOC entry 3638 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN approval_instance.template_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_version IS '模板版本号';


--
-- TOC entry 276 (class 1259 OID 20718)
-- Name: approval_instance_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.approval_instance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3639 (class 0 OID 0)
-- Dependencies: 276
-- Name: approval_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_instance_id_seq OWNED BY public.approval_instance.id;


--
-- TOC entry 253 (class 1259 OID 20488)
-- Name: approval_process_template; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.approval_process_template (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    object_type character varying(50) NOT NULL,
    is_active boolean,
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    required_fields json DEFAULT '[]'::jsonb,
    lock_object_on_start boolean DEFAULT true,
    lock_reason character varying(200) DEFAULT '审批流程进行中，暂时锁定编辑'::character varying
);


--
-- TOC entry 3640 (class 0 OID 0)
-- Dependencies: 253
-- Name: COLUMN approval_process_template.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.name IS '流程名称';


--
-- TOC entry 3641 (class 0 OID 0)
-- Dependencies: 253
-- Name: COLUMN approval_process_template.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.object_type IS '适用对象（如 quotation）';


--
-- TOC entry 3642 (class 0 OID 0)
-- Dependencies: 253
-- Name: COLUMN approval_process_template.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.is_active IS '是否启用';


--
-- TOC entry 3643 (class 0 OID 0)
-- Dependencies: 253
-- Name: COLUMN approval_process_template.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_by IS '创建人账号ID';


--
-- TOC entry 3644 (class 0 OID 0)
-- Dependencies: 253
-- Name: COLUMN approval_process_template.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_at IS '创建时间';


--
-- TOC entry 3645 (class 0 OID 0)
-- Dependencies: 253
-- Name: COLUMN approval_process_template.required_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.required_fields IS '发起审批时必填字段列表';


--
-- TOC entry 3646 (class 0 OID 0)
-- Dependencies: 253
-- Name: COLUMN approval_process_template.lock_object_on_start; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_object_on_start IS '发起审批后是否锁定对象编辑';


--
-- TOC entry 3647 (class 0 OID 0)
-- Dependencies: 253
-- Name: COLUMN approval_process_template.lock_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_reason IS '锁定原因说明';


--
-- TOC entry 252 (class 1259 OID 20487)
-- Name: approval_process_template_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.approval_process_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3648 (class 0 OID 0)
-- Dependencies: 252
-- Name: approval_process_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_process_template_id_seq OWNED BY public.approval_process_template.id;


--
-- TOC entry 301 (class 1259 OID 20966)
-- Name: approval_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.approval_record (
    id integer NOT NULL,
    instance_id integer NOT NULL,
    step_id integer NOT NULL,
    approver_id integer NOT NULL,
    action character varying(50) NOT NULL,
    comment text,
    "timestamp" timestamp without time zone
);


--
-- TOC entry 3649 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN approval_record.instance_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.instance_id IS '审批流程实例';


--
-- TOC entry 3650 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN approval_record.step_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.step_id IS '流程步骤ID';


--
-- TOC entry 3651 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN approval_record.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.approver_id IS '审批人ID';


--
-- TOC entry 3652 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN approval_record.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.action IS '同意/拒绝';


--
-- TOC entry 3653 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN approval_record.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.comment IS '审批意见';


--
-- TOC entry 3654 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN approval_record."timestamp"; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record."timestamp" IS '审批时间';


--
-- TOC entry 300 (class 1259 OID 20965)
-- Name: approval_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.approval_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3655 (class 0 OID 0)
-- Dependencies: 300
-- Name: approval_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_record_id_seq OWNED BY public.approval_record.id;


--
-- TOC entry 275 (class 1259 OID 20700)
-- Name: approval_step; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.approval_step (
    id integer NOT NULL,
    process_id integer NOT NULL,
    step_order integer NOT NULL,
    approver_user_id integer,
    step_name character varying(100) NOT NULL,
    send_email boolean,
    action_type character varying(50),
    action_params json,
    editable_fields json DEFAULT '[]'::json,
    cc_users json DEFAULT '[]'::json,
    cc_enabled boolean DEFAULT false,
    approver_type character varying(50),
    description text
);


--
-- TOC entry 3656 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN approval_step.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.process_id IS '所属流程模板';


--
-- TOC entry 3657 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN approval_step.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_order IS '流程顺序';


--
-- TOC entry 3658 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN approval_step.approver_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.approver_user_id IS '审批人账号ID';


--
-- TOC entry 3659 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN approval_step.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_name IS '步骤说明（如"财务审批"）';


--
-- TOC entry 3660 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN approval_step.send_email; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.send_email IS '是否发送邮件通知';


--
-- TOC entry 3661 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN approval_step.action_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_type IS '步骤动作类型，如 authorization, quotation_approval';


--
-- TOC entry 3662 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN approval_step.action_params; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_params IS '动作参数，JSON格式';


--
-- TOC entry 3663 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN approval_step.editable_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.editable_fields IS '在此步骤可编辑的字段列表';


--
-- TOC entry 3664 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN approval_step.cc_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_users IS '邮件抄送用户ID列表';


--
-- TOC entry 3665 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN approval_step.cc_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_enabled IS '是否启用邮件抄送';


--
-- TOC entry 274 (class 1259 OID 20699)
-- Name: approval_step_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.approval_step_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3666 (class 0 OID 0)
-- Dependencies: 274
-- Name: approval_step_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_step_id_seq OWNED BY public.approval_step.id;


--
-- TOC entry 3455 (class 2604 OID 21289)
-- Name: approval_instance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance ALTER COLUMN id SET DEFAULT nextval('public.approval_instance_id_seq'::regclass);


--
-- TOC entry 3447 (class 2604 OID 21290)
-- Name: approval_process_template id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template ALTER COLUMN id SET DEFAULT nextval('public.approval_process_template_id_seq'::regclass);


--
-- TOC entry 3456 (class 2604 OID 21291)
-- Name: approval_record id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record ALTER COLUMN id SET DEFAULT nextval('public.approval_record_id_seq'::regclass);


--
-- TOC entry 3451 (class 2604 OID 21292)
-- Name: approval_step id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step ALTER COLUMN id SET DEFAULT nextval('public.approval_step_id_seq'::regclass);


--
-- TOC entry 3621 (class 0 OID 20719)
-- Dependencies: 277
-- Data for Name: approval_instance; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_instance (id, process_id, object_id, object_type, current_step, status, started_at, ended_at, created_by, template_snapshot, template_version) FROM stdin;
54	2	600	project	1	APPROVED	2025-06-16 05:49:24.767786	2025-06-16 06:07:38.277567	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-16T05:49:24.766269", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250616_054924
53	2	563	project	1	REJECTED	2025-06-16 05:48:01.962233	2025-06-18 04:13:06.436247	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-16T05:48:01.960490", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250616_054801
59	2	628	project	1	APPROVED	2025-06-20 05:46:47.58801	2025-06-20 05:56:42.917764	14	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-20T05:46:47.585508", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250620_054647
61	2	520	project	1	APPROVED	2025-06-20 05:59:44.182841	2025-06-20 06:09:20.574505	14	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-20T05:59:44.181245", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250620_055944
62	2	623	project	1	APPROVED	2025-06-20 06:00:41.131978	2025-06-20 06:11:22.863037	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-20T06:00:41.130401", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250620_060041
63	2	629	project	1	APPROVED	2025-06-20 06:01:35.343887	2025-06-20 06:15:19.833866	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-20T06:01:35.342076", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250620_060135
64	2	622	project	1	APPROVED	2025-06-20 06:01:55.15444	2025-06-20 06:16:27.096959	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-20T06:01:55.152996", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250620_060155
65	2	538	project	1	APPROVED	2025-06-20 06:02:24.179204	2025-06-20 06:48:26.201037	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-20T06:02:24.177544", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250620_060224
60	2	521	project	1	APPROVED	2025-06-20 05:58:33.754312	2025-06-20 06:03:48.281034	14	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-20T05:58:33.752393", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250620_055833
68	2	630	project	1	PENDING	2025-06-20 06:17:05.117424	\N	14	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-20T06:17:05.115961", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250620_061705
66	2	586	project	1	APPROVED	2025-06-20 06:02:52.837436	2025-06-20 06:49:51.339728	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-20T06:02:52.829614", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250620_060252
67	2	564	project	1	APPROVED	2025-06-20 06:03:11.95138	2025-06-20 06:50:36.04547	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-20T06:03:11.949656", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250620_060311
93	5	636	project	1	PENDING	2025-06-25 05:03:20.530394	\N	2	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T05:03:20.527217", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Servicemanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 7, "approver_username": "xuhao", "approver_real_name": "\\u5f90\\u660a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_050320
69	2	631	project	1	APPROVED	2025-06-21 02:32:17.219641	2025-06-21 02:33:39.973689	19	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-21T02:32:17.219523", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250621_023217
70	2	634	project	1	APPROVED	2025-06-23 01:48:26.604612	2025-06-23 02:15:20.289499	14	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-23T01:48:26.603038", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250623_014826
71	2	635	project	1	APPROVED	2025-06-23 01:54:02.745322	2025-06-23 02:20:35.453626	14	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-23T01:54:02.743804", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250623_015402
94	5	638	project	1	PENDING	2025-06-25 06:02:52.349335	\N	2	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T06:02:52.347574", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Servicemanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 7, "approver_username": "xuhao", "approver_real_name": "\\u5f90\\u660a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_060252
72	2	573	project	1	APPROVED	2025-06-23 07:43:31.246591	2025-06-23 07:44:22.047056	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-23T07:43:31.245032", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250623_074331
73	2	563	project	1	APPROVED	2025-06-23 07:44:11.9082	2025-06-23 08:02:39.458761	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-23T07:44:11.906474", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250623_074411
95	5	640	project	1	PENDING	2025-06-25 06:37:37.945423	\N	13	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T06:37:37.943825", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Salesdirector\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_063737
96	5	639	project	1	PENDING	2025-06-25 06:38:48.546622	\N	13	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T06:38:48.544586", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Salesdirector\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_063848
55	2	627	project	1	APPROVED	2025-06-18 01:59:18.255513	2025-06-18 04:07:27.340979	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-18T01:59:18.253947", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250618_015918
56	2	626	project	1	APPROVED	2025-06-18 02:08:18.868146	2025-06-18 04:11:28.160728	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-18T02:08:18.866509", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250618_020818
74	2	555	project	1	APPROVED	2025-06-23 07:45:22.496702	2025-06-23 08:07:30.140261	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-23T07:45:22.494942", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250623_074522
97	5	641	project	1	PENDING	2025-06-25 06:45:44.34653	\N	13	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T06:45:44.344721", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Salesdirector\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_064544
50	2	573	project	1	REJECTED	2025-06-12 03:40:23.785232	2025-06-18 04:14:24.059135	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-12T03:40:23.783717", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250612_034023
76	5	553	project	1	PENDING	2025-06-24 00:57:23.859652	\N	16	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-24T00:57:23.854408", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Salesdirector\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250624_005723
98	5	542	project	1	PENDING	2025-06-25 08:56:44.39176	\N	16	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T08:56:44.387846", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_085644
77	5	597	project	1	REJECTED	2025-06-24 01:00:59.732041	2025-06-25 08:59:24.281977	16	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-24T01:00:59.728653", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Salesdirector\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250624_010059
99	5	642	project	1	REJECTED	2025-06-25 09:05:09.349563	2025-06-26 03:41:30.216739	16	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T09:05:09.347717", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_090509
37	2	518	project	1	REJECTED	2025-06-09 02:55:50.828501	2025-06-18 04:19:45.943902	14	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-09T02:55:50.826665", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250609_025550
24	2	538	project	1	REJECTED	2025-06-03 03:26:31.738558	2025-06-18 04:22:29.669765	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-03T03:26:31.736871", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250603_032631
100	5	645	project	1	PENDING	2025-06-27 03:15:18.006454	\N	14	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-27T03:15:18.004655", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250627_031518
9	3	602	project	1	APPROVED	2025-05-30 06:19:06.133288	2025-06-16 03:34:29.569642	2	\N	\N
14	2	521	project	1	REJECTED	2025-05-30 07:11:38.691496	2025-06-18 04:01:21.394789	14	\N	\N
15	2	520	project	1	REJECTED	2025-05-30 07:12:09.280291	2025-06-18 04:20:57.995272	14	\N	\N
21	2	554	project	1	REJECTED	2025-06-03 03:24:52.947073	2025-06-18 04:30:36.24041	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-03T03:24:52.943920", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250603_032452
6	2	568	project	1	APPROVED	2025-05-28 08:40:33.397592	2025-05-28 08:42:08.48878	19	\N	\N
5	2	30	project	1	APPROVED	2025-05-28 07:11:13.272345	2025-05-28 08:49:37.199419	16	\N	\N
11	1	528	project	1	APPROVED	2025-05-30 07:02:57.734992	2025-06-02 01:34:43.650391	14	\N	\N
1	1	511	project	1	REJECTED	2025-05-27 04:33:20.820841	2025-06-02 01:35:17.994849	5	\N	\N
19	2	605	project	1	REJECTED	2025-06-03 03:21:34.868026	2025-06-18 04:31:50.764379	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-03T03:21:34.866119", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250603_032134
18	2	586	project	1	REJECTED	2025-06-03 03:21:09.360347	2025-06-18 04:32:37.183885	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-03T03:21:09.358789", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250603_032109
57	2	554	project	1	APPROVED	2025-06-19 02:28:21.794107	2025-06-19 05:48:03.129821	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-19T02:28:21.792142", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250619_022821
84	5	633	project	1	PENDING	2025-06-25 03:28:04.967209	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:28:04.965274", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Salesdirector\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_032804
80	5	637	project	1	PENDING	2025-06-25 03:26:17.194023	\N	19	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:26:17.190706", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_032617
81	5	580	project	1	PENDING	2025-06-25 03:26:27.852991	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:26:27.851033", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Salesdirector\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_032627
82	5	619	project	1	PENDING	2025-06-25 03:27:15.52505	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:27:15.523318", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_032715
83	5	620	project	1	PENDING	2025-06-25 03:27:42.390936	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:27:42.389246", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_032742
85	5	632	project	1	PENDING	2025-06-25 03:28:28.941389	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:28:28.939504", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Salesdirector\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_032828
10	2	587	project	1	REJECTED	2025-05-30 06:26:41.8909	2025-06-27 03:05:31.758798	14	\N	\N
20	2	601	project	1	APPROVED	2025-06-03 03:24:22.154836	2025-06-04 00:57:37.132977	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-03T03:24:22.153258", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250603_032422
17	2	603	project	1	APPROVED	2025-05-30 07:21:07.748398	2025-06-04 01:03:44.45699	14	\N	\N
16	2	519	project	1	APPROVED	2025-05-30 07:12:35.102361	2025-06-04 01:26:02.219337	14	\N	\N
12	2	593	project	1	APPROVED	2025-05-30 07:09:45.316771	2025-06-04 01:33:30.653268	14	\N	\N
2	2	571	project	1	APPROVED	2025-05-28 07:04:30.049075	2025-06-11 03:24:50.232638	16	\N	\N
3	2	570	project	1	APPROVED	2025-05-28 07:09:56.676918	2025-06-11 03:26:42.372224	16	\N	\N
4	2	572	project	1	APPROVED	2025-05-28 07:10:32.372234	2025-06-11 03:27:15.830343	16	\N	\N
7	2	41	project	1	APPROVED	2025-05-30 06:13:20.666183	2025-06-11 03:27:59.197269	14	\N	\N
8	2	517	project	1	APPROVED	2025-05-30 06:17:48.293485	2025-06-11 03:28:33.068355	14	\N	\N
13	2	524	project	1	APPROVED	2025-05-30 07:11:08.616328	2025-06-11 03:29:11.21321	14	\N	\N
29	2	608	project	1	APPROVED	2025-06-04 01:08:18.114791	2025-06-04 01:09:10.255733	19	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-04T01:08:18.114745", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250604_010818
22	2	556	project	1	APPROVED	2025-06-03 03:25:24.909623	2025-06-03 06:58:41.012567	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-03T03:25:24.907808", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250603_032524
28	1	607	project	1	APPROVED	2025-06-03 10:56:25.066612	2025-06-03 10:56:47.170923	13	{"template_id": 1, "template_name": "\\u9500\\u552e\\u91cd\\u70b9\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "report_source", "project_type"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-03T10:56:25.066545", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u5ba1\\u6279\\u6388\\u6743", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250603_105625
31	1	611	project	1	APPROVED	2025-06-04 02:23:42.229996	2025-06-05 06:21:57.150131	16	{"template_id": 1, "template_name": "\\u9500\\u552e\\u91cd\\u70b9\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "report_source", "project_type"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-04T02:23:42.228432", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u5ba1\\u6279\\u6388\\u6743", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250604_022342
27	2	606	project	1	APPROVED	2025-06-03 10:21:29.02594	2025-06-04 07:28:46.359022	13	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-03T10:21:29.023836", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250603_102129
23	2	564	project	1	REJECTED	2025-06-03 03:26:00.857055	2025-06-18 04:23:47.971673	15	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-03T03:26:00.854604", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250603_032600
86	5	594	project	1	PENDING	2025-06-25 03:28:51.339021	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:28:51.337208", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_032851
87	5	581	project	1	PENDING	2025-06-25 03:30:20.968877	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:30:20.966653", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_033020
30	2	610	project	1	APPROVED	2025-06-04 01:45:48.102595	2025-06-04 07:32:04.757206	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-04T01:45:48.101192", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250604_014548
34	2	613	project	1	APPROVED	2025-06-05 06:44:45.701379	2025-06-07 06:32:47.929771	13	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-05T06:44:45.699196", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250605_064445
32	2	609	project	1	APPROVED	2025-06-04 02:58:10.357811	2025-06-09 01:04:51.924858	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-04T02:58:10.356261", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250604_025810
35	1	614	project	1	APPROVED	2025-06-05 07:16:03.234201	2025-06-05 07:16:28.930605	13	{"template_id": 1, "template_name": "\\u9500\\u552e\\u91cd\\u70b9\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "report_source", "project_type"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-05T07:16:03.234112", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u5ba1\\u6279\\u6388\\u6743", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250605_071603
33	2	612	project	1	APPROVED	2025-06-05 06:15:36.795727	2025-06-07 06:29:19.288919	13	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-05T06:15:36.793463", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250605_061536
36	2	615	project	1	APPROVED	2025-06-06 02:35:49.096663	2025-06-07 06:33:35.307963	14	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-06T02:35:49.094959", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250606_023549
38	1	567	project	1	APPROVED	2025-06-09 06:29:09.551306	2025-06-09 06:29:46.921007	16	{"template_id": 1, "template_name": "\\u9500\\u552e\\u91cd\\u70b9\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "report_source", "project_type"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-09T06:29:09.549727", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u5ba1\\u6279\\u6388\\u6743", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250609_062909
39	1	549	project	1	APPROVED	2025-06-09 06:30:12.730165	2025-06-11 01:40:13.961731	16	{"template_id": 1, "template_name": "\\u9500\\u552e\\u91cd\\u70b9\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "report_source", "project_type"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-09T06:30:12.728487", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u5ba1\\u6279\\u6388\\u6743", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250609_063012
88	5	595	project	1	PENDING	2025-06-25 03:31:16.288735	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:31:16.284777", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_033116
89	5	617	project	1	PENDING	2025-06-25 03:32:18.557699	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:32:18.555965", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_033218
41	1	590	project	1	APPROVED	2025-06-11 06:48:45.089115	2025-06-11 06:49:01.321498	13	{"template_id": 1, "template_name": "\\u9500\\u552e\\u91cd\\u70b9\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "report_source", "project_type"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-11T06:48:45.089040", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u5ba1\\u6279\\u6388\\u6743", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250611_064845
42	2	512	project	1	APPROVED	2025-06-11 07:06:14.446695	2025-06-11 11:12:22.834496	13	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-11T07:06:14.445129", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250611_070614
44	2	529	project	1	APPROVED	2025-06-12 03:33:58.390414	2025-06-12 03:58:31.922623	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-12T03:33:58.388822", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250612_033358
45	2	531	project	1	APPROVED	2025-06-12 03:34:28.393922	2025-06-12 04:00:18.730505	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-12T03:34:28.392337", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250612_033428
49	2	598	project	1	APPROVED	2025-06-12 03:39:50.987207	2025-06-12 04:08:59.399265	16	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-12T03:39:50.985644", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250612_033950
40	2	535	project	1	REJECTED	2025-06-11 06:41:27.108474	2025-06-18 04:18:26.040437	13	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-11T06:41:27.101615", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250611_064127
47	1	600	project	1	REJECTED	2025-06-12 03:35:40.329495	2025-06-12 05:49:25.146072	16	{"template_id": 1, "template_name": "\\u9500\\u552e\\u91cd\\u70b9\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "report_source", "project_type"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-12T03:35:40.327731", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u5ba1\\u6279\\u6388\\u6743", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250612_033540
43	2	618	project	1	APPROVED	2025-06-12 02:40:28.382945	2025-06-12 03:55:16.777294	13	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-12T02:40:28.381371", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250612_024028
51	2	621	project	1	APPROVED	2025-06-13 04:43:35.45532	2025-06-13 04:46:07.131433	18	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-13T04:43:35.450746", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250613_044335
52	2	625	project	1	APPROVED	2025-06-16 02:23:18.164	2025-06-16 02:24:07.197764	19	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-16T02:23:18.163950", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250616_022318
58	2	535	project	1	APPROVED	2025-06-19 03:26:25.201593	2025-06-19 05:48:36.358353	13	{"template_id": 2, "template_name": "\\u6e20\\u9053\\u9879\\u76ee\\u62a5\\u5907\\u6d41\\u7a0b", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-19T03:26:25.199596", "steps": [{"id": 2, "step_order": 1, "step_name": "\\u6e20\\u9053\\u9879\\u76ee\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250619_032625
90	5	578	project	1	PENDING	2025-06-25 03:39:45.939544	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:39:45.937391", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Salesdirector\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_033945
91	5	576	project	1	PENDING	2025-06-25 03:40:34.268539	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:40:34.266933", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Salesdirector\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 13, "approver_username": "gxh", "approver_real_name": "\\u90ed\\u5c0f\\u4f1a", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_034034
92	5	582	project	1	PENDING	2025-06-25 03:41:02.135648	\N	17	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-25T03:41:02.134012", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250625_034102
101	5	646	project	1	PENDING	2025-06-27 03:25:35.0961	\N	14	{"template_id": 5, "template_name": "\\u9879\\u76ee\\u62a5\\u5907", "object_type": "project", "created_at": "2025-06-27T03:25:35.094242", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Channelmanager\\u6388\\u6743\\u5ba1\\u6279", "approver_user_id": 19, "approver_username": "linwenguan", "approver_real_name": "\\u6797\\u6587\\u51a0", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": ["authorization_code"], "cc_users": [5], "cc_enabled": true}]}	v20250627_032535
\.


--
-- TOC entry 3617 (class 0 OID 20488)
-- Dependencies: 253
-- Data for Name: approval_process_template; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_process_template (id, name, object_type, is_active, created_by, created_at, required_fields, lock_object_on_start, lock_reason) FROM stdin;
2	渠道项目报备流程	project	f	5	2025-05-24 06:59:13.929278	["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"]	t	审批流程进行中，暂时锁定编辑
3	销售机会授权审批	project	f	5	2025-05-27 04:30:15.895441	["project_name", "project_type", "report_time", "report_source", "project_name", "report_time", "project_type", "report_source"]	t	审批流程进行中，暂时锁定编辑
5	项目报备	project	t	5	2025-06-24 00:55:56.192611	["project_type", "report_source"]	t	审批流程进行中，暂时锁定编辑
1	销售重点报备流程	project	f	5	2025-05-24 06:57:46.814329	["project_name", "project_type", "report_source", "project_name", "report_source", "project_type"]	t	审批流程进行中，暂时锁定编辑
\.


--
-- TOC entry 3623 (class 0 OID 20966)
-- Dependencies: 301
-- Data for Name: approval_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_record (id, instance_id, step_id, approver_id, action, comment, "timestamp") FROM stdin;
65	57	2	19	approve	确认	2025-06-19 05:48:03.071559
66	58	2	19	approve	确认	2025-06-19 05:48:36.342694
73	65	2	19	approve	予以通过	2025-06-20 06:48:26.186228
74	66	2	19	approve	予以通过	2025-06-20 06:49:51.325939
75	67	2	19	approve	予以通过	2025-06-20 06:50:36.031517
77	70	2	19	approve	系统复核确认，予以审批	2025-06-23 02:15:20.274068
78	71	2	19	approve	系统复核，确认通过	2025-06-23 02:20:35.352663
84	73	2	19	approve	确认审批	2025-06-23 08:02:39.444857
85	74	2	19	approve	确认审核通过	2025-06-23 08:07:30.127062
92	99	5	16	recall	发起人召回审批流程	2025-06-26 03:41:30.222656
1	6	2	19	approve	区域合作商国隆信达联系，并使用和源通信产品投标项目，予以支持	2025-05-28 08:42:08.473519
2	5	2	19	approve	该项目系统内未有冲突，予以报备	2025-05-28 08:49:37.192085
3	11	1	13	approve		2025-06-02 01:34:43.617563
4	1	1	13	reject		2025-06-02 01:35:17.99473
7	22	2	19	approve	系统核实新项目，予以认可	2025-06-03 06:58:40.995366
8	28	1	13	approve		2025-06-03 10:56:47.150486
9	20	2	19	approve	确认为新项目实施，予以审批通过	2025-06-04 00:57:37.112884
10	17	2	19	approve	复核为新项目申报，予以审核通过	2025-06-04 01:03:44.444566
11	29	2	19	approve	线上系统复核，为新项目开发	2025-06-04 01:09:10.2458
12	16	2	19	approve	复核为新项目申报，予以通过	2025-06-04 01:26:02.208663
13	12	2	19	approve	复核为系统内新项目申报，予以通过	2025-06-04 01:33:30.641024
15	27	2	19	approve	经系统内信息复核，为新项目申报，予以许可	2025-06-04 07:28:46.346591
16	30	2	19	approve	经系统内复核，该项目为新项目申报，予以认可	2025-06-04 07:32:04.742795
17	31	1	13	approve		2025-06-05 06:21:57.132295
18	35	1	13	approve		2025-06-05 07:16:28.919844
20	33	2	19	approve	系统内复核为新项目报备，予以批准	2025-06-07 06:29:19.268833
21	34	2	19	approve	系统复核为新项目申报，予以审批通过	2025-06-07 06:32:47.917743
22	36	2	19	approve	系统复核为新项目申报，予以许可通过	2025-06-07 06:33:35.296275
23	32	2	19	approve	线下已报备项目，历史报备编号“HY-CPJ202504-031”，需要线上同步修改	2025-06-09 01:04:51.909914
24	38	1	13	approve		2025-06-09 06:29:46.909731
25	39	1	13	approve		2025-06-11 01:40:13.942656
26	2	2	19	approve	历史授权项目，线上审批许可，延用历史报备编号HY-CPJ202504-030	2025-06-11 03:24:50.227256
27	3	2	19	approve	历史授权项目，线上审批许可，延用历史报备编号HY-CPJ202504-029	2025-06-11 03:26:42.367136
28	4	2	19	approve	历史授权项目，线上审批许可，延用历史报备编号HY-CPJ202412-009	2025-06-11 03:27:15.824913
29	7	2	19	approve	历史授权项目，线上审批许可，延用历史报备编号HY-CPJ202504-024	2025-06-11 03:27:59.179853
30	8	2	19	approve	历史授权项目，线上审批许可，延用历史报备编号HY-CPJ202403-011	2025-06-11 03:28:33.061563
31	13	2	19	approve	历史授权项目，线上审批许可，延用历史报备编号HY-CPJ202410-005	2025-06-11 03:29:11.207839
32	41	1	13	approve		2025-06-11 06:49:01.302649
33	42	2	19	approve	西北区新项目报备，予以许可	2025-06-11 11:12:22.815087
37	43	2	19	approve	系统内复核，为西区新项目申报，予以审批通过	2025-06-12 03:55:16.762607
38	44	2	19	approve	系统内复核，为北京地区新项目，予以审批通过	2025-06-12 03:58:31.90907
39	45	2	19	approve	系统内复核，为新项目申报，予以审核通过	2025-06-12 04:00:18.71159
40	49	2	19	approve	系统内复核，为新项目申报，予以通过	2025-06-12 04:08:59.361321
41	47	1	13	reject		2025-06-12 05:49:25.14586
42	51	2	19	approve		2025-06-13 04:46:07.109271
43	52	2	19	approve	复核上海港汇恒隆广场酒店装修工程之弱电分包工程项目，线上系统未重回，予以审批通过	2025-06-16 02:24:07.183595
44	9	3	7	approve		2025-06-16 03:34:29.555631
45	54	2	19	approve	复核系统为新项目申请，予以审批通过	2025-06-16 06:07:38.26381
52	14	2	19	reject	历史报备项目，编号：HY-CPJ202505-003	2025-06-18 04:01:21.394661
53	55	2	19	approve	系统复核为新项目申报，予以审核通过	2025-06-18 04:07:27.321579
54	56	2	19	approve	复核为新项目开发，予以通过	2025-06-18 04:11:28.150508
55	53	2	19	reject	历史报备项目，编号：HY-CPJ202505-007	2025-06-18 04:13:06.436124
56	50	2	19	reject	历史报备项目，编号：HY-CPJ202405-010	2025-06-18 04:14:24.059013
57	40	2	19	reject	历史报备项目，编号：HY-CPJ202504-032	2025-06-18 04:18:26.04027
58	37	2	19	reject	历史报备项目：编号：HY-CPJ202409-001	2025-06-18 04:19:45.943805
59	15	2	19	reject	历史报备项目，编号：HY-CPJ202505-004	2025-06-18 04:20:57.995113
60	24	2	19	reject	历史报备项目，编号：HY-CPJ202211-011	2025-06-18 04:22:29.669665
61	23	2	19	reject	历史报备项目，编号：HY-CPJ202505-006	2025-06-18 04:23:47.971548
62	21	2	19	reject	历史报备项目，编号：HY-CPJ202505-005	2025-06-18 04:30:36.240267
63	19	2	19	reject	历史报备项目，编号：HY-CPJ202505-009	2025-06-18 04:31:50.764201
64	18	2	19	reject	历史报备项目，编号：HY-CPJ202505-001	2025-06-18 04:32:37.183782
67	59	2	19	approve	予以通过	2025-06-20 05:56:42.845113
68	60	2	19	approve	予以通过	2025-06-20 06:03:48.26725
69	61	2	19	approve	予以通过	2025-06-20 06:09:20.561362
70	62	2	19	approve	予以审批	2025-06-20 06:11:22.760404
71	63	2	19	approve	予以通过	2025-06-20 06:15:19.820075
72	64	2	19	approve	予以通过	2025-06-20 06:16:27.083241
76	69	2	19	approve	新项目确认，予以认可	2025-06-21 02:33:39.956653
83	72	2	19	approve	予以通过	2025-06-23 07:44:22.029339
91	77	5	16	recall	发起人召回审批流程。原因：更新项目类型	2025-06-25 08:59:24.284974
93	10	2	14	recall	发起人召回审批流程。原因：机会填错	2025-06-27 03:05:31.762327
\.


--
-- TOC entry 3619 (class 0 OID 20700)
-- Dependencies: 275
-- Data for Name: approval_step; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_step (id, process_id, step_order, approver_user_id, step_name, send_email, action_type, action_params, editable_fields, cc_users, cc_enabled, approver_type, description) FROM stdin;
1	1	1	13	审批授权	t	authorization	\N	[]	[]	f	\N	\N
2	2	1	19	渠道项目审批	t	authorization	\N	[]	[]	f	\N	\N
3	3	1	7	销售机会授权审批	t	authorization	\N	[]	[]	f	\N	\N
5	5	1	\N	指定授权人审批	t	authorization	\N	["authorization_code"]	[5]	t	user	\N
\.


--
-- TOC entry 3667 (class 0 OID 0)
-- Dependencies: 276
-- Name: approval_instance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_instance_id_seq', 101, true);


--
-- TOC entry 3668 (class 0 OID 0)
-- Dependencies: 252
-- Name: approval_process_template_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_process_template_id_seq', 5, true);


--
-- TOC entry 3669 (class 0 OID 0)
-- Dependencies: 300
-- Name: approval_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_record_id_seq', 95, true);


--
-- TOC entry 3670 (class 0 OID 0)
-- Dependencies: 274
-- Name: approval_step_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_step_id_seq', 5, true);


--
-- TOC entry 3462 (class 2606 OID 20726)
-- Name: approval_instance approval_instance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_pkey PRIMARY KEY (id);


--
-- TOC entry 3458 (class 2606 OID 20495)
-- Name: approval_process_template approval_process_template_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_pkey PRIMARY KEY (id);


--
-- TOC entry 3464 (class 2606 OID 20973)
-- Name: approval_record approval_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_pkey PRIMARY KEY (id);


--
-- TOC entry 3460 (class 2606 OID 20707)
-- Name: approval_step approval_step_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_pkey PRIMARY KEY (id);


--
-- TOC entry 3468 (class 2606 OID 20732)
-- Name: approval_instance approval_instance_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3469 (class 2606 OID 20727)
-- Name: approval_instance approval_instance_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- TOC entry 3465 (class 2606 OID 20496)
-- Name: approval_process_template approval_process_template_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3470 (class 2606 OID 20984)
-- Name: approval_record approval_record_approver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_approver_id_fkey FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- TOC entry 3471 (class 2606 OID 20974)
-- Name: approval_record approval_record_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES public.approval_instance(id);


--
-- TOC entry 3472 (class 2606 OID 20979)
-- Name: approval_record approval_record_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_step_id_fkey FOREIGN KEY (step_id) REFERENCES public.approval_step(id);


--
-- TOC entry 3466 (class 2606 OID 20713)
-- Name: approval_step approval_step_approver_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_approver_user_id_fkey FOREIGN KEY (approver_user_id) REFERENCES public.users(id);


--
-- TOC entry 3467 (class 2606 OID 20708)
-- Name: approval_step approval_step_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


-- Completed on 2025-06-27 19:15:57 HKT

--
-- PostgreSQL database dump complete
--

