--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Debian 16.9-1.pgdg120+1)
-- Dumped by pg_dump version 16.9 (Homebrew)

-- Started on 2025-06-13 18:41:50 CST

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
-- TOC entry 5 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: pma_db_sp8d_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO pma_db_sp8d_user;

--
-- TOC entry 1016 (class 1247 OID 19549)
-- Name: approval_action; Type: TYPE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TYPE public.approval_action AS ENUM (
    'approve',
    'reject'
);


ALTER TYPE public.approval_action OWNER TO pma_db_sp8d_user;

--
-- TOC entry 1019 (class 1247 OID 19554)
-- Name: approval_status; Type: TYPE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TYPE public.approval_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);


ALTER TYPE public.approval_status OWNER TO pma_db_sp8d_user;

--
-- TOC entry 1022 (class 1247 OID 19562)
-- Name: approvalaction; Type: TYPE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TYPE public.approvalaction AS ENUM (
    'approve',
    'reject'
);


ALTER TYPE public.approvalaction OWNER TO pma_db_sp8d_user;

--
-- TOC entry 1025 (class 1247 OID 19568)
-- Name: approvalinstancestatus; Type: TYPE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TYPE public.approvalinstancestatus AS ENUM (
    'pending',
    'approved',
    'rejected'
);


ALTER TYPE public.approvalinstancestatus OWNER TO pma_db_sp8d_user;

--
-- TOC entry 989 (class 1247 OID 18712)
-- Name: approvalstatus; Type: TYPE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TYPE public.approvalstatus AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED'
);


ALTER TYPE public.approvalstatus OWNER TO pma_db_sp8d_user;

--
-- TOC entry 1028 (class 1247 OID 19576)
-- Name: pricingorderapprovalflowtype; Type: TYPE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TYPE public.pricingorderapprovalflowtype AS ENUM (
    'CHANNEL_FOLLOW',
    'SALES_KEY',
    'SALES_OPPORTUNITY'
);


ALTER TYPE public.pricingorderapprovalflowtype OWNER TO pma_db_sp8d_user;

--
-- TOC entry 1031 (class 1247 OID 19584)
-- Name: pricingorderstatus; Type: TYPE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TYPE public.pricingorderstatus AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


ALTER TYPE public.pricingorderstatus OWNER TO pma_db_sp8d_user;

--
-- TOC entry 1034 (class 1247 OID 19594)
-- Name: settlementorderstatus; Type: TYPE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TYPE public.settlementorderstatus AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


ALTER TYPE public.settlementorderstatus OWNER TO pma_db_sp8d_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 263 (class 1259 OID 19603)
-- Name: action_reply; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.action_reply (
    id integer NOT NULL,
    action_id integer NOT NULL,
    parent_reply_id integer,
    content text NOT NULL,
    owner_id integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.action_reply OWNER TO pma_db_sp8d_user;

--
-- TOC entry 264 (class 1259 OID 19608)
-- Name: action_reply_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.action_reply_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.action_reply_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4106 (class 0 OID 0)
-- Dependencies: 264
-- Name: action_reply_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.action_reply_id_seq OWNED BY public.action_reply.id;


--
-- TOC entry 265 (class 1259 OID 19609)
-- Name: actions; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.actions (
    id integer NOT NULL,
    date date NOT NULL,
    contact_id integer,
    company_id integer,
    project_id integer,
    communication text NOT NULL,
    created_at timestamp without time zone,
    owner_id integer
);


ALTER TABLE public.actions OWNER TO pma_db_sp8d_user;

--
-- TOC entry 266 (class 1259 OID 19614)
-- Name: actions_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.actions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.actions_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4107 (class 0 OID 0)
-- Dependencies: 266
-- Name: actions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.actions_id_seq OWNED BY public.actions.id;


--
-- TOC entry 267 (class 1259 OID 19615)
-- Name: affiliations; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.affiliations (
    id integer NOT NULL,
    owner_id integer NOT NULL,
    viewer_id integer NOT NULL,
    created_at double precision
);


ALTER TABLE public.affiliations OWNER TO pma_db_sp8d_user;

--
-- TOC entry 268 (class 1259 OID 19618)
-- Name: affiliations_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.affiliations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.affiliations_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4108 (class 0 OID 0)
-- Dependencies: 268
-- Name: affiliations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.affiliations_id_seq OWNED BY public.affiliations.id;


--
-- TOC entry 269 (class 1259 OID 19619)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO pma_db_sp8d_user;

--
-- TOC entry 270 (class 1259 OID 19622)
-- Name: approval_instance; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.approval_instance (
    id integer NOT NULL,
    object_id integer NOT NULL,
    object_type character varying(50) NOT NULL,
    current_step integer,
    status public.approvalstatus,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    process_id integer NOT NULL,
    created_by integer NOT NULL,
    template_snapshot json,
    template_version character varying(50)
);


ALTER TABLE public.approval_instance OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4109 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN approval_instance.object_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_instance.object_id IS '对应单据ID';


--
-- TOC entry 4110 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN approval_instance.object_type; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_instance.object_type IS '单据类型（如 project）';


--
-- TOC entry 4111 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN approval_instance.current_step; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_instance.current_step IS '当前步骤序号';


--
-- TOC entry 4112 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN approval_instance.status; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_instance.status IS '状态';


--
-- TOC entry 4113 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN approval_instance.started_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_instance.started_at IS '流程发起时间';


--
-- TOC entry 4114 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN approval_instance.ended_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_instance.ended_at IS '审批完成时间';


--
-- TOC entry 4115 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN approval_instance.process_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_instance.process_id IS '流程模板ID';


--
-- TOC entry 4116 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN approval_instance.created_by; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_instance.created_by IS '发起人ID';


--
-- TOC entry 4117 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN approval_instance.template_snapshot; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_instance.template_snapshot IS '创建时的模板快照';


--
-- TOC entry 4118 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN approval_instance.template_version; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_instance.template_version IS '模板版本号';


--
-- TOC entry 271 (class 1259 OID 19627)
-- Name: approval_instance_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.approval_instance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.approval_instance_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4119 (class 0 OID 0)
-- Dependencies: 271
-- Name: approval_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.approval_instance_id_seq OWNED BY public.approval_instance.id;


--
-- TOC entry 248 (class 1259 OID 18720)
-- Name: approval_process_template; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
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


ALTER TABLE public.approval_process_template OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4120 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN approval_process_template.name; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_process_template.name IS '流程名称';


--
-- TOC entry 4121 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN approval_process_template.object_type; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_process_template.object_type IS '适用对象（如 quotation）';


--
-- TOC entry 4122 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN approval_process_template.is_active; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_process_template.is_active IS '是否启用';


--
-- TOC entry 4123 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN approval_process_template.created_by; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_process_template.created_by IS '创建人账号ID';


--
-- TOC entry 4124 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN approval_process_template.created_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_process_template.created_at IS '创建时间';


--
-- TOC entry 4125 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN approval_process_template.required_fields; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_process_template.required_fields IS '发起审批时必填字段列表';


--
-- TOC entry 4126 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN approval_process_template.lock_object_on_start; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_process_template.lock_object_on_start IS '发起审批后是否锁定对象编辑';


--
-- TOC entry 4127 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN approval_process_template.lock_reason; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_process_template.lock_reason IS '锁定原因说明';


--
-- TOC entry 247 (class 1259 OID 18719)
-- Name: approval_process_template_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.approval_process_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.approval_process_template_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4128 (class 0 OID 0)
-- Dependencies: 247
-- Name: approval_process_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.approval_process_template_id_seq OWNED BY public.approval_process_template.id;


--
-- TOC entry 272 (class 1259 OID 19628)
-- Name: approval_record_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.approval_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.approval_record_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 273 (class 1259 OID 19629)
-- Name: approval_record; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.approval_record (
    id integer DEFAULT nextval('public.approval_record_id_seq'::regclass) NOT NULL,
    instance_id integer NOT NULL,
    step_id integer NOT NULL,
    approver_id integer NOT NULL,
    action character varying(50) NOT NULL,
    comment text,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.approval_record OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4129 (class 0 OID 0)
-- Dependencies: 273
-- Name: COLUMN approval_record.instance_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_record.instance_id IS '审批流程实例';


--
-- TOC entry 4130 (class 0 OID 0)
-- Dependencies: 273
-- Name: COLUMN approval_record.step_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_record.step_id IS '流程步骤ID';


--
-- TOC entry 4131 (class 0 OID 0)
-- Dependencies: 273
-- Name: COLUMN approval_record.approver_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_record.approver_id IS '审批人ID';


--
-- TOC entry 4132 (class 0 OID 0)
-- Dependencies: 273
-- Name: COLUMN approval_record.action; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_record.action IS '同意/拒绝';


--
-- TOC entry 4133 (class 0 OID 0)
-- Dependencies: 273
-- Name: COLUMN approval_record.comment; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_record.comment IS '审批意见';


--
-- TOC entry 4134 (class 0 OID 0)
-- Dependencies: 273
-- Name: COLUMN approval_record."timestamp"; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_record."timestamp" IS '审批时间';


--
-- TOC entry 274 (class 1259 OID 19635)
-- Name: approval_step; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.approval_step (
    id integer NOT NULL,
    process_id integer NOT NULL,
    step_order integer NOT NULL,
    approver_user_id integer NOT NULL,
    step_name character varying(100) NOT NULL,
    send_email boolean,
    action_type character varying(50),
    action_params json,
    editable_fields json DEFAULT '[]'::json,
    cc_users json DEFAULT '[]'::json,
    cc_enabled boolean DEFAULT false
);


ALTER TABLE public.approval_step OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4135 (class 0 OID 0)
-- Dependencies: 274
-- Name: COLUMN approval_step.process_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_step.process_id IS '所属流程模板';


--
-- TOC entry 4136 (class 0 OID 0)
-- Dependencies: 274
-- Name: COLUMN approval_step.step_order; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_step.step_order IS '流程顺序';


--
-- TOC entry 4137 (class 0 OID 0)
-- Dependencies: 274
-- Name: COLUMN approval_step.approver_user_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_step.approver_user_id IS '审批人账号ID';


--
-- TOC entry 4138 (class 0 OID 0)
-- Dependencies: 274
-- Name: COLUMN approval_step.step_name; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_step.step_name IS '步骤说明（如"财务审批"）';


--
-- TOC entry 4139 (class 0 OID 0)
-- Dependencies: 274
-- Name: COLUMN approval_step.send_email; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_step.send_email IS '是否发送邮件通知';


--
-- TOC entry 4140 (class 0 OID 0)
-- Dependencies: 274
-- Name: COLUMN approval_step.action_type; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_step.action_type IS '步骤动作类型，如 authorization, quotation_approval';


--
-- TOC entry 4141 (class 0 OID 0)
-- Dependencies: 274
-- Name: COLUMN approval_step.action_params; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_step.action_params IS '动作参数，JSON格式';


--
-- TOC entry 4142 (class 0 OID 0)
-- Dependencies: 274
-- Name: COLUMN approval_step.editable_fields; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_step.editable_fields IS '在此步骤可编辑的字段列表';


--
-- TOC entry 4143 (class 0 OID 0)
-- Dependencies: 274
-- Name: COLUMN approval_step.cc_users; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_step.cc_users IS '邮件抄送用户ID列表';


--
-- TOC entry 4144 (class 0 OID 0)
-- Dependencies: 274
-- Name: COLUMN approval_step.cc_enabled; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.approval_step.cc_enabled IS '是否启用邮件抄送';


--
-- TOC entry 275 (class 1259 OID 19643)
-- Name: approval_step_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.approval_step_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.approval_step_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4145 (class 0 OID 0)
-- Dependencies: 275
-- Name: approval_step_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.approval_step_id_seq OWNED BY public.approval_step.id;


--
-- TOC entry 276 (class 1259 OID 19644)
-- Name: change_logs; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.change_logs (
    id integer NOT NULL,
    module_name character varying(50) NOT NULL,
    table_name character varying(50) NOT NULL,
    record_id integer NOT NULL,
    operation_type character varying(20) NOT NULL,
    field_name character varying(100),
    old_value text,
    new_value text,
    user_id integer,
    user_name character varying(80),
    created_at timestamp without time zone,
    description character varying(255),
    ip_address character varying(45),
    user_agent character varying(255),
    record_info character varying(255)
);


ALTER TABLE public.change_logs OWNER TO pma_db_sp8d_user;

--
-- TOC entry 277 (class 1259 OID 19649)
-- Name: change_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.change_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.change_logs_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4146 (class 0 OID 0)
-- Dependencies: 277
-- Name: change_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.change_logs_id_seq OWNED BY public.change_logs.id;


--
-- TOC entry 230 (class 1259 OID 18177)
-- Name: companies; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.companies (
    id integer NOT NULL,
    company_code character varying(20) NOT NULL,
    company_name character varying(100) NOT NULL,
    country character varying(50),
    region character varying(50),
    address character varying(200),
    industry character varying(50),
    company_type character varying(20),
    status character varying(20),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    notes text,
    is_deleted boolean,
    owner_id integer,
    shared_with_users json,
    share_contacts boolean
);


ALTER TABLE public.companies OWNER TO pma_db_sp8d_user;

--
-- TOC entry 229 (class 1259 OID 18176)
-- Name: companies_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.companies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.companies_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4147 (class 0 OID 0)
-- Dependencies: 229
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- TOC entry 236 (class 1259 OID 18225)
-- Name: contacts; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.contacts (
    id integer NOT NULL,
    company_id integer NOT NULL,
    name character varying(50) NOT NULL,
    department character varying(50),
    "position" character varying(50),
    phone character varying(20),
    email character varying(100),
    is_primary boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    notes text,
    owner_id integer,
    override_share boolean,
    shared_disabled boolean
);


ALTER TABLE public.contacts OWNER TO pma_db_sp8d_user;

--
-- TOC entry 235 (class 1259 OID 18224)
-- Name: contacts_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.contacts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contacts_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4148 (class 0 OID 0)
-- Dependencies: 235
-- Name: contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.contacts_id_seq OWNED BY public.contacts.id;


--
-- TOC entry 278 (class 1259 OID 19650)
-- Name: dev_product_specs; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.dev_product_specs (
    id integer NOT NULL,
    dev_product_id integer,
    field_name character varying(100),
    field_value character varying(255),
    field_code character varying(10)
);


ALTER TABLE public.dev_product_specs OWNER TO pma_db_sp8d_user;

--
-- TOC entry 279 (class 1259 OID 19653)
-- Name: dev_product_specs_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.dev_product_specs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dev_product_specs_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4149 (class 0 OID 0)
-- Dependencies: 279
-- Name: dev_product_specs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.dev_product_specs_id_seq OWNED BY public.dev_product_specs.id;


--
-- TOC entry 242 (class 1259 OID 18287)
-- Name: dev_products; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.dev_products (
    id integer NOT NULL,
    category_id integer,
    subcategory_id integer,
    region_id integer,
    name character varying(100),
    model character varying(100),
    status character varying(50),
    unit character varying(20),
    retail_price double precision,
    description text,
    image_path character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    owner_id integer,
    created_by integer,
    mn_code character varying(20),
    pdf_path character varying(255)
);


ALTER TABLE public.dev_products OWNER TO pma_db_sp8d_user;

--
-- TOC entry 241 (class 1259 OID 18286)
-- Name: dev_products_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.dev_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dev_products_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4150 (class 0 OID 0)
-- Dependencies: 241
-- Name: dev_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.dev_products_id_seq OWNED BY public.dev_products.id;


--
-- TOC entry 280 (class 1259 OID 19654)
-- Name: dictionaries; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.dictionaries (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    key character varying(50) NOT NULL,
    value character varying(100) NOT NULL,
    is_active boolean,
    sort_order integer,
    created_at double precision,
    updated_at double precision
);


ALTER TABLE public.dictionaries OWNER TO pma_db_sp8d_user;

--
-- TOC entry 281 (class 1259 OID 19657)
-- Name: dictionaries_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.dictionaries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dictionaries_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4151 (class 0 OID 0)
-- Dependencies: 281
-- Name: dictionaries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.dictionaries_id_seq OWNED BY public.dictionaries.id;


--
-- TOC entry 282 (class 1259 OID 19658)
-- Name: event_registry; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.event_registry (
    id integer NOT NULL,
    event_key character varying(50) NOT NULL,
    label_zh character varying(100) NOT NULL,
    label_en character varying(100) NOT NULL,
    default_enabled boolean,
    enabled boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.event_registry OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4152 (class 0 OID 0)
-- Dependencies: 282
-- Name: COLUMN event_registry.event_key; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.event_registry.event_key IS '事件唯一键';


--
-- TOC entry 4153 (class 0 OID 0)
-- Dependencies: 282
-- Name: COLUMN event_registry.label_zh; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.event_registry.label_zh IS '中文名称';


--
-- TOC entry 4154 (class 0 OID 0)
-- Dependencies: 282
-- Name: COLUMN event_registry.label_en; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.event_registry.label_en IS '英文名称';


--
-- TOC entry 4155 (class 0 OID 0)
-- Dependencies: 282
-- Name: COLUMN event_registry.default_enabled; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.event_registry.default_enabled IS '是否默认开启';


--
-- TOC entry 4156 (class 0 OID 0)
-- Dependencies: 282
-- Name: COLUMN event_registry.enabled; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.event_registry.enabled IS '是否在通知中心展示';


--
-- TOC entry 283 (class 1259 OID 19661)
-- Name: event_registry_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.event_registry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.event_registry_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4157 (class 0 OID 0)
-- Dependencies: 283
-- Name: event_registry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.event_registry_id_seq OWNED BY public.event_registry.id;


--
-- TOC entry 284 (class 1259 OID 19662)
-- Name: feature_changes; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.feature_changes (
    id integer NOT NULL,
    version_id integer NOT NULL,
    change_type character varying(20) NOT NULL,
    module_name character varying(50),
    title character varying(200) NOT NULL,
    description text,
    priority character varying(20),
    impact_level character varying(20),
    affected_files text,
    git_commits text,
    test_status character varying(20),
    test_notes text,
    developer_id integer,
    developer_name character varying(50),
    created_at timestamp without time zone,
    completed_at timestamp without time zone
);


ALTER TABLE public.feature_changes OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4158 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.version_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.version_id IS '版本ID';


--
-- TOC entry 4159 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.change_type; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.change_type IS '变更类型：feature/fix/improvement/security';


--
-- TOC entry 4160 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.module_name; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.module_name IS '模块名称';


--
-- TOC entry 4161 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.title; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.title IS '变更标题';


--
-- TOC entry 4162 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.description; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.description IS '详细描述';


--
-- TOC entry 4163 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.priority; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.priority IS '优先级：low/medium/high/critical';


--
-- TOC entry 4164 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.impact_level; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.impact_level IS '影响级别：minor/major/breaking';


--
-- TOC entry 4165 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.affected_files; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.affected_files IS '影响的文件列表（JSON格式）';


--
-- TOC entry 4166 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.git_commits; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.git_commits IS '相关Git提交（JSON格式）';


--
-- TOC entry 4167 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.test_status; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.test_status IS '测试状态：pending/passed/failed';


--
-- TOC entry 4168 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.test_notes; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.test_notes IS '测试说明';


--
-- TOC entry 4169 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.developer_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.developer_id IS '开发人员ID';


--
-- TOC entry 4170 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.developer_name; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.developer_name IS '开发人员姓名';


--
-- TOC entry 4171 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.created_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.created_at IS '创建时间';


--
-- TOC entry 4172 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN feature_changes.completed_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.feature_changes.completed_at IS '完成时间';


--
-- TOC entry 285 (class 1259 OID 19667)
-- Name: feature_changes_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.feature_changes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.feature_changes_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4173 (class 0 OID 0)
-- Dependencies: 285
-- Name: feature_changes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.feature_changes_id_seq OWNED BY public.feature_changes.id;


--
-- TOC entry 258 (class 1259 OID 19409)
-- Name: inventory; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.inventory (
    id integer NOT NULL,
    company_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity integer NOT NULL,
    unit character varying(20),
    location character varying(100),
    min_stock integer,
    max_stock integer,
    notes text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by_id integer NOT NULL
);


ALTER TABLE public.inventory OWNER TO pma_db_sp8d_user;

--
-- TOC entry 257 (class 1259 OID 19408)
-- Name: inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.inventory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inventory_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4174 (class 0 OID 0)
-- Dependencies: 257
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- TOC entry 286 (class 1259 OID 19668)
-- Name: inventory_transactions; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.inventory_transactions (
    id integer NOT NULL,
    inventory_id integer NOT NULL,
    transaction_type character varying(20) NOT NULL,
    quantity integer NOT NULL,
    quantity_before integer NOT NULL,
    quantity_after integer NOT NULL,
    reference_type character varying(50),
    reference_id integer,
    description text,
    transaction_date timestamp without time zone,
    created_by_id integer NOT NULL
);


ALTER TABLE public.inventory_transactions OWNER TO pma_db_sp8d_user;

--
-- TOC entry 287 (class 1259 OID 19673)
-- Name: inventory_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.inventory_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inventory_transactions_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4175 (class 0 OID 0)
-- Dependencies: 287
-- Name: inventory_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.inventory_transactions_id_seq OWNED BY public.inventory_transactions.id;


--
-- TOC entry 288 (class 1259 OID 19674)
-- Name: permissions; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.permissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    module character varying(50) NOT NULL,
    can_view boolean,
    can_create boolean,
    can_edit boolean,
    can_delete boolean
);


ALTER TABLE public.permissions OWNER TO pma_db_sp8d_user;

--
-- TOC entry 289 (class 1259 OID 19677)
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.permissions_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4176 (class 0 OID 0)
-- Dependencies: 289
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- TOC entry 290 (class 1259 OID 19678)
-- Name: pricing_order_approval_records; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.pricing_order_approval_records (
    id integer NOT NULL,
    pricing_order_id integer NOT NULL,
    step_order integer NOT NULL,
    step_name character varying(64) NOT NULL,
    approver_role character varying(64) NOT NULL,
    approver_id integer NOT NULL,
    action character varying(16),
    comment text,
    approved_at timestamp without time zone,
    is_fast_approval boolean,
    fast_approval_reason character varying(255)
);


ALTER TABLE public.pricing_order_approval_records OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4177 (class 0 OID 0)
-- Dependencies: 290
-- Name: COLUMN pricing_order_approval_records.pricing_order_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_approval_records.pricing_order_id IS '批价单ID';


--
-- TOC entry 4178 (class 0 OID 0)
-- Dependencies: 290
-- Name: COLUMN pricing_order_approval_records.step_order; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_order IS '审批步骤顺序';


--
-- TOC entry 4179 (class 0 OID 0)
-- Dependencies: 290
-- Name: COLUMN pricing_order_approval_records.step_name; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_name IS '审批步骤名称';


--
-- TOC entry 4180 (class 0 OID 0)
-- Dependencies: 290
-- Name: COLUMN pricing_order_approval_records.approver_role; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_role IS '审批人角色';


--
-- TOC entry 4181 (class 0 OID 0)
-- Dependencies: 290
-- Name: COLUMN pricing_order_approval_records.approver_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_id IS '审批人ID';


--
-- TOC entry 4182 (class 0 OID 0)
-- Dependencies: 290
-- Name: COLUMN pricing_order_approval_records.action; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_approval_records.action IS '审批动作：approve/reject';


--
-- TOC entry 4183 (class 0 OID 0)
-- Dependencies: 290
-- Name: COLUMN pricing_order_approval_records.comment; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_approval_records.comment IS '审批意见';


--
-- TOC entry 4184 (class 0 OID 0)
-- Dependencies: 290
-- Name: COLUMN pricing_order_approval_records.approved_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_approval_records.approved_at IS '审批时间';


--
-- TOC entry 4185 (class 0 OID 0)
-- Dependencies: 290
-- Name: COLUMN pricing_order_approval_records.is_fast_approval; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_approval_records.is_fast_approval IS '是否快速通过';


--
-- TOC entry 4186 (class 0 OID 0)
-- Dependencies: 290
-- Name: COLUMN pricing_order_approval_records.fast_approval_reason; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_approval_records.fast_approval_reason IS '快速通过原因';


--
-- TOC entry 291 (class 1259 OID 19683)
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.pricing_order_approval_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pricing_order_approval_records_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4187 (class 0 OID 0)
-- Dependencies: 291
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.pricing_order_approval_records_id_seq OWNED BY public.pricing_order_approval_records.id;


--
-- TOC entry 256 (class 1259 OID 19310)
-- Name: pricing_order_details; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.pricing_order_details (
    id integer NOT NULL,
    pricing_order_id integer NOT NULL,
    product_name character varying(255) NOT NULL,
    product_model character varying(128),
    product_desc text,
    brand character varying(64),
    unit character varying(16),
    product_mn character varying(64),
    market_price double precision NOT NULL,
    unit_price double precision NOT NULL,
    quantity integer NOT NULL,
    discount_rate double precision,
    total_price double precision NOT NULL,
    source_type character varying(32),
    source_quotation_detail_id integer
);


ALTER TABLE public.pricing_order_details OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4188 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.pricing_order_id IS '批价单ID';


--
-- TOC entry 4189 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.product_name; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.product_name IS '产品名称';


--
-- TOC entry 4190 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.product_model; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.product_model IS '产品型号';


--
-- TOC entry 4191 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.product_desc; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.product_desc IS '产品描述';


--
-- TOC entry 4192 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.brand; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.brand IS '品牌';


--
-- TOC entry 4193 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.unit; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.unit IS '单位';


--
-- TOC entry 4194 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.product_mn; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.product_mn IS '产品MN编码';


--
-- TOC entry 4195 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.market_price; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.market_price IS '市场价';


--
-- TOC entry 4196 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.unit_price; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.unit_price IS '单价';


--
-- TOC entry 4197 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.quantity; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.quantity IS '数量';


--
-- TOC entry 4198 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.discount_rate IS '折扣率';


--
-- TOC entry 4199 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.total_price; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.total_price IS '小计金额';


--
-- TOC entry 4200 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.source_type; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.source_type IS '数据来源：quotation/manual';


--
-- TOC entry 4201 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_order_details.source_quotation_detail_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_order_details.source_quotation_detail_id IS '来源报价单明细ID';


--
-- TOC entry 255 (class 1259 OID 19309)
-- Name: pricing_order_details_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.pricing_order_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pricing_order_details_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4202 (class 0 OID 0)
-- Dependencies: 255
-- Name: pricing_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.pricing_order_details_id_seq OWNED BY public.pricing_order_details.id;


--
-- TOC entry 252 (class 1259 OID 19227)
-- Name: pricing_orders; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.pricing_orders (
    id integer NOT NULL,
    order_number character varying(64) NOT NULL,
    project_id integer NOT NULL,
    quotation_id integer NOT NULL,
    dealer_id integer,
    distributor_id integer,
    is_direct_contract boolean DEFAULT false,
    is_factory_pickup boolean DEFAULT false,
    approval_flow_type character varying(32) NOT NULL,
    status character varying(20),
    current_approval_step integer,
    pricing_total_amount double precision,
    pricing_total_discount_rate double precision,
    settlement_total_amount double precision,
    settlement_total_discount_rate double precision,
    approved_by integer,
    approved_at timestamp without time zone,
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.pricing_orders OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4203 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.order_number; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.order_number IS '批价单号';


--
-- TOC entry 4204 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.project_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.project_id IS '项目ID';


--
-- TOC entry 4205 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.quotation_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.quotation_id IS '报价单ID';


--
-- TOC entry 4206 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.dealer_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.dealer_id IS '经销商ID';


--
-- TOC entry 4207 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.distributor_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.distributor_id IS '分销商ID';


--
-- TOC entry 4208 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.is_direct_contract; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.is_direct_contract IS '厂商直签';


--
-- TOC entry 4209 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.is_factory_pickup; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.is_factory_pickup IS '厂家提货';


--
-- TOC entry 4210 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.approval_flow_type; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.approval_flow_type IS '审批流程类型';


--
-- TOC entry 4211 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.status; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.status IS '批价单状态';


--
-- TOC entry 4212 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.current_approval_step; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.current_approval_step IS '当前审批步骤';


--
-- TOC entry 4213 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.pricing_total_amount; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_amount IS '批价单总金额';


--
-- TOC entry 4214 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.pricing_total_discount_rate; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_discount_rate IS '批价单总折扣率';


--
-- TOC entry 4215 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.settlement_total_amount; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_amount IS '结算单总金额';


--
-- TOC entry 4216 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.settlement_total_discount_rate; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_discount_rate IS '结算单总折扣率';


--
-- TOC entry 4217 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.approved_by; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.approved_by IS '最终批准人';


--
-- TOC entry 4218 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.approved_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.approved_at IS '批准时间';


--
-- TOC entry 4219 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.created_by; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.created_by IS '创建人';


--
-- TOC entry 4220 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.created_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.created_at IS '创建时间';


--
-- TOC entry 4221 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_orders.updated_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.pricing_orders.updated_at IS '更新时间';


--
-- TOC entry 251 (class 1259 OID 19226)
-- Name: pricing_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.pricing_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pricing_orders_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4222 (class 0 OID 0)
-- Dependencies: 251
-- Name: pricing_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.pricing_orders_id_seq OWNED BY public.pricing_orders.id;


--
-- TOC entry 224 (class 1259 OID 18069)
-- Name: product_categories; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.product_categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code_letter character varying(1) NOT NULL,
    description text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.product_categories OWNER TO pma_db_sp8d_user;

--
-- TOC entry 223 (class 1259 OID 18068)
-- Name: product_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.product_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_categories_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4223 (class 0 OID 0)
-- Dependencies: 223
-- Name: product_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.product_categories_id_seq OWNED BY public.product_categories.id;


--
-- TOC entry 246 (class 1259 OID 18362)
-- Name: product_code_field_options; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.product_code_field_options (
    id integer NOT NULL,
    field_id integer NOT NULL,
    value character varying(100) NOT NULL,
    code character varying(10) NOT NULL,
    description text,
    is_active boolean,
    "position" integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.product_code_field_options OWNER TO pma_db_sp8d_user;

--
-- TOC entry 245 (class 1259 OID 18361)
-- Name: product_code_field_options_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.product_code_field_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_code_field_options_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4224 (class 0 OID 0)
-- Dependencies: 245
-- Name: product_code_field_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.product_code_field_options_id_seq OWNED BY public.product_code_field_options.id;


--
-- TOC entry 292 (class 1259 OID 19684)
-- Name: product_code_field_values; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.product_code_field_values (
    id integer NOT NULL,
    product_code_id integer NOT NULL,
    field_id integer NOT NULL,
    option_id integer,
    custom_value character varying(100)
);


ALTER TABLE public.product_code_field_values OWNER TO pma_db_sp8d_user;

--
-- TOC entry 293 (class 1259 OID 19687)
-- Name: product_code_field_values_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.product_code_field_values_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_code_field_values_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4225 (class 0 OID 0)
-- Dependencies: 293
-- Name: product_code_field_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.product_code_field_values_id_seq OWNED BY public.product_code_field_values.id;


--
-- TOC entry 238 (class 1259 OID 18244)
-- Name: product_code_fields; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.product_code_fields (
    id integer NOT NULL,
    subcategory_id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(10),
    description text,
    field_type character varying(20) NOT NULL,
    "position" integer NOT NULL,
    max_length integer,
    is_required boolean,
    use_in_code boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.product_code_fields OWNER TO pma_db_sp8d_user;

--
-- TOC entry 237 (class 1259 OID 18243)
-- Name: product_code_fields_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.product_code_fields_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_code_fields_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4226 (class 0 OID 0)
-- Dependencies: 237
-- Name: product_code_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.product_code_fields_id_seq OWNED BY public.product_code_fields.id;


--
-- TOC entry 240 (class 1259 OID 18258)
-- Name: product_codes; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.product_codes (
    id integer NOT NULL,
    product_id integer NOT NULL,
    category_id integer NOT NULL,
    subcategory_id integer NOT NULL,
    full_code character varying(50) NOT NULL,
    status character varying(20),
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.product_codes OWNER TO pma_db_sp8d_user;

--
-- TOC entry 239 (class 1259 OID 18257)
-- Name: product_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.product_codes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_codes_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4227 (class 0 OID 0)
-- Dependencies: 239
-- Name: product_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.product_codes_id_seq OWNED BY public.product_codes.id;


--
-- TOC entry 226 (class 1259 OID 18080)
-- Name: product_regions; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.product_regions (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code_letter character varying(1) NOT NULL,
    description text,
    created_at timestamp without time zone
);


ALTER TABLE public.product_regions OWNER TO pma_db_sp8d_user;

--
-- TOC entry 225 (class 1259 OID 18079)
-- Name: product_regions_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.product_regions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_regions_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4228 (class 0 OID 0)
-- Dependencies: 225
-- Name: product_regions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.product_regions_id_seq OWNED BY public.product_regions.id;


--
-- TOC entry 234 (class 1259 OID 18209)
-- Name: product_subcategories; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.product_subcategories (
    id integer NOT NULL,
    category_id integer NOT NULL,
    name character varying(100) NOT NULL,
    code_letter character varying(1) NOT NULL,
    description text,
    display_order integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.product_subcategories OWNER TO pma_db_sp8d_user;

--
-- TOC entry 233 (class 1259 OID 18208)
-- Name: product_subcategories_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.product_subcategories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_subcategories_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4229 (class 0 OID 0)
-- Dependencies: 233
-- Name: product_subcategories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.product_subcategories_id_seq OWNED BY public.product_subcategories.id;


--
-- TOC entry 232 (class 1259 OID 18193)
-- Name: products; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.products (
    id integer NOT NULL,
    type character varying(50),
    category character varying(50),
    product_mn character varying(50),
    product_name character varying(100),
    model character varying(100),
    specification text,
    brand character varying(50),
    unit character varying(20),
    retail_price numeric(10,2),
    status character varying(20),
    image_path character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    owner_id integer,
    pdf_path character varying(255)
);


ALTER TABLE public.products OWNER TO pma_db_sp8d_user;

--
-- TOC entry 231 (class 1259 OID 18192)
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.products_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4230 (class 0 OID 0)
-- Dependencies: 231
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- TOC entry 294 (class 1259 OID 19688)
-- Name: project_members; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.project_members (
    id integer NOT NULL,
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    role character varying(50) NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.project_members OWNER TO pma_db_sp8d_user;

--
-- TOC entry 295 (class 1259 OID 19691)
-- Name: project_members_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.project_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.project_members_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4231 (class 0 OID 0)
-- Dependencies: 295
-- Name: project_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.project_members_id_seq OWNED BY public.project_members.id;


--
-- TOC entry 296 (class 1259 OID 19692)
-- Name: project_rating_records; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.project_rating_records (
    id integer NOT NULL,
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    rating integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    CONSTRAINT ck_rating_value CHECK ((rating = 1))
);


ALTER TABLE public.project_rating_records OWNER TO pma_db_sp8d_user;

--
-- TOC entry 297 (class 1259 OID 19696)
-- Name: project_rating_records_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.project_rating_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.project_rating_records_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4232 (class 0 OID 0)
-- Dependencies: 297
-- Name: project_rating_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.project_rating_records_id_seq OWNED BY public.project_rating_records.id;


--
-- TOC entry 298 (class 1259 OID 19697)
-- Name: project_scoring_config; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.project_scoring_config (
    id integer NOT NULL,
    category character varying(50) NOT NULL,
    field_name character varying(100) NOT NULL,
    field_label character varying(200) NOT NULL,
    score_value numeric(3,2) DEFAULT 0.0 NOT NULL,
    prerequisite text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.project_scoring_config OWNER TO pma_db_sp8d_user;

--
-- TOC entry 299 (class 1259 OID 19706)
-- Name: project_scoring_config_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.project_scoring_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.project_scoring_config_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4233 (class 0 OID 0)
-- Dependencies: 299
-- Name: project_scoring_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.project_scoring_config_id_seq OWNED BY public.project_scoring_config.id;


--
-- TOC entry 300 (class 1259 OID 19707)
-- Name: project_scoring_records; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.project_scoring_records (
    id integer NOT NULL,
    project_id integer NOT NULL,
    category character varying(50) NOT NULL,
    field_name character varying(100) NOT NULL,
    score_value numeric(3,2) DEFAULT 0.0 NOT NULL,
    awarded_by integer,
    auto_calculated boolean DEFAULT true,
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.project_scoring_records OWNER TO pma_db_sp8d_user;

--
-- TOC entry 301 (class 1259 OID 19716)
-- Name: project_scoring_records_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.project_scoring_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.project_scoring_records_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4234 (class 0 OID 0)
-- Dependencies: 301
-- Name: project_scoring_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.project_scoring_records_id_seq OWNED BY public.project_scoring_records.id;


--
-- TOC entry 302 (class 1259 OID 19717)
-- Name: project_stage_history; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.project_stage_history (
    id integer NOT NULL,
    project_id integer NOT NULL,
    from_stage character varying(64),
    to_stage character varying(64) NOT NULL,
    change_date timestamp without time zone NOT NULL,
    change_week integer,
    change_month integer,
    change_year integer,
    account_id integer,
    remarks text,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.project_stage_history OWNER TO pma_db_sp8d_user;

--
-- TOC entry 303 (class 1259 OID 19723)
-- Name: project_stage_history_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.project_stage_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.project_stage_history_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4235 (class 0 OID 0)
-- Dependencies: 303
-- Name: project_stage_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.project_stage_history_id_seq OWNED BY public.project_stage_history.id;


--
-- TOC entry 304 (class 1259 OID 19724)
-- Name: project_total_scores; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.project_total_scores (
    id integer NOT NULL,
    project_id integer NOT NULL,
    information_score numeric(3,2) DEFAULT 0.0,
    quotation_score numeric(3,2) DEFAULT 0.0,
    stage_score numeric(3,2) DEFAULT 0.0,
    manual_score numeric(3,2) DEFAULT 0.0,
    total_score numeric(3,2) DEFAULT 0.0,
    star_rating numeric(2,1) DEFAULT 0,
    last_calculated timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.project_total_scores OWNER TO pma_db_sp8d_user;

--
-- TOC entry 305 (class 1259 OID 19736)
-- Name: project_total_scores_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.project_total_scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.project_total_scores_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4236 (class 0 OID 0)
-- Dependencies: 305
-- Name: project_total_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.project_total_scores_id_seq OWNED BY public.project_total_scores.id;


--
-- TOC entry 228 (class 1259 OID 18159)
-- Name: projects; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    project_name character varying(64) NOT NULL,
    report_time date,
    project_type character varying(64),
    report_source character varying(64),
    product_situation character varying(128),
    end_user character varying(128),
    design_issues character varying(128),
    dealer character varying(128),
    contractor character varying(128),
    system_integrator character varying(128),
    current_stage character varying(64),
    stage_description text,
    authorization_code character varying(64),
    delivery_forecast date,
    quotation_customer double precision,
    authorization_status character varying(20),
    feedback text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    owner_id integer,
    is_locked boolean DEFAULT false NOT NULL,
    locked_reason character varying(100),
    locked_by integer,
    locked_at timestamp without time zone,
    is_active boolean DEFAULT true NOT NULL,
    last_activity_date timestamp without time zone DEFAULT now(),
    activity_reason character varying(50),
    vendor_sales_manager_id integer,
    rating integer,
    CONSTRAINT projects_rating_check CHECK (((rating IS NULL) OR (((rating)::numeric >= (1)::numeric) AND ((rating)::numeric <= (5)::numeric))))
);


ALTER TABLE public.projects OWNER TO pma_db_sp8d_user;

--
-- TOC entry 227 (class 1259 OID 18158)
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.projects_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4237 (class 0 OID 0)
-- Dependencies: 227
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- TOC entry 306 (class 1259 OID 19737)
-- Name: purchase_order_details; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.purchase_order_details (
    id integer NOT NULL,
    order_id integer NOT NULL,
    product_id integer NOT NULL,
    product_name character varying(200) NOT NULL,
    product_model character varying(100),
    product_desc text,
    brand character varying(100),
    quantity integer NOT NULL,
    unit character varying(20),
    unit_price numeric(15,2),
    discount numeric(5,4),
    total_price numeric(15,2),
    received_quantity integer,
    notes text
);


ALTER TABLE public.purchase_order_details OWNER TO pma_db_sp8d_user;

--
-- TOC entry 307 (class 1259 OID 19742)
-- Name: purchase_order_details_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.purchase_order_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.purchase_order_details_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4238 (class 0 OID 0)
-- Dependencies: 307
-- Name: purchase_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.purchase_order_details_id_seq OWNED BY public.purchase_order_details.id;


--
-- TOC entry 262 (class 1259 OID 19461)
-- Name: purchase_orders; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.purchase_orders (
    id integer NOT NULL,
    order_number character varying(50) NOT NULL,
    company_id integer NOT NULL,
    order_type character varying(20),
    order_date timestamp without time zone,
    expected_date timestamp without time zone,
    status character varying(20),
    total_amount numeric(15,2),
    total_quantity integer,
    currency character varying(10),
    payment_terms character varying(100),
    delivery_address text,
    description text,
    created_by_id integer NOT NULL,
    approved_by_id integer,
    approved_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.purchase_orders OWNER TO pma_db_sp8d_user;

--
-- TOC entry 261 (class 1259 OID 19460)
-- Name: purchase_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.purchase_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.purchase_orders_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4239 (class 0 OID 0)
-- Dependencies: 261
-- Name: purchase_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.purchase_orders_id_seq OWNED BY public.purchase_orders.id;


--
-- TOC entry 308 (class 1259 OID 19743)
-- Name: quotation_details; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.quotation_details (
    id integer NOT NULL,
    quotation_id integer,
    product_name character varying(100),
    product_model character varying(100),
    product_desc text,
    brand character varying(50),
    unit character varying(20),
    quantity integer,
    discount double precision,
    market_price double precision,
    unit_price double precision,
    total_price double precision,
    product_mn character varying(100),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    implant_subtotal double precision DEFAULT 0.00
);


ALTER TABLE public.quotation_details OWNER TO pma_db_sp8d_user;

--
-- TOC entry 309 (class 1259 OID 19749)
-- Name: quotation_details_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.quotation_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.quotation_details_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4240 (class 0 OID 0)
-- Dependencies: 309
-- Name: quotation_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.quotation_details_id_seq OWNED BY public.quotation_details.id;


--
-- TOC entry 244 (class 1259 OID 18338)
-- Name: quotations; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.quotations (
    id integer NOT NULL,
    quotation_number character varying(20) NOT NULL,
    project_id integer NOT NULL,
    contact_id integer,
    amount double precision,
    project_stage character varying(20),
    project_type character varying(20),
    created_at timestamp with time zone,
    updated_at timestamp without time zone,
    owner_id integer,
    approval_status character varying(50) DEFAULT 'pending'::character varying,
    approved_stages json DEFAULT '[]'::json,
    approval_history json DEFAULT '[]'::json,
    is_locked boolean DEFAULT false,
    lock_reason character varying(200),
    locked_by integer,
    locked_at timestamp without time zone,
    confirmed_at timestamp without time zone,
    confirmation_badge_color character varying(20) DEFAULT NULL::character varying,
    product_signature character varying(64) DEFAULT NULL::character varying,
    confirmed_by integer,
    confirmation_badge_status character varying(20) DEFAULT 'none'::character varying,
    implant_total_amount double precision DEFAULT 0.00
);


ALTER TABLE public.quotations OWNER TO pma_db_sp8d_user;

--
-- TOC entry 243 (class 1259 OID 18337)
-- Name: quotations_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.quotations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.quotations_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4241 (class 0 OID 0)
-- Dependencies: 243
-- Name: quotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.quotations_id_seq OWNED BY public.quotations.id;


--
-- TOC entry 310 (class 1259 OID 19750)
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.role_permissions (
    id integer NOT NULL,
    role character varying(50) NOT NULL,
    module character varying(50) NOT NULL,
    can_view boolean,
    can_create boolean,
    can_edit boolean,
    can_delete boolean
);


ALTER TABLE public.role_permissions OWNER TO pma_db_sp8d_user;

--
-- TOC entry 311 (class 1259 OID 19753)
-- Name: role_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.role_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.role_permissions_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4242 (class 0 OID 0)
-- Dependencies: 311
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- TOC entry 312 (class 1259 OID 19754)
-- Name: settlement_details; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.settlement_details (
    id integer NOT NULL,
    settlement_id integer NOT NULL,
    inventory_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity_settled integer NOT NULL,
    quantity_before integer NOT NULL,
    quantity_after integer NOT NULL,
    unit character varying(20),
    notes text
);


ALTER TABLE public.settlement_details OWNER TO pma_db_sp8d_user;

--
-- TOC entry 313 (class 1259 OID 19759)
-- Name: settlement_details_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.settlement_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.settlement_details_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4243 (class 0 OID 0)
-- Dependencies: 313
-- Name: settlement_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.settlement_details_id_seq OWNED BY public.settlement_details.id;


--
-- TOC entry 314 (class 1259 OID 19760)
-- Name: settlement_order_details; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.settlement_order_details (
    id integer NOT NULL,
    pricing_order_id integer NOT NULL,
    product_name character varying(255) NOT NULL,
    product_model character varying(128),
    product_desc text,
    brand character varying(64),
    unit character varying(16),
    product_mn character varying(64),
    market_price double precision NOT NULL,
    unit_price double precision NOT NULL,
    quantity integer NOT NULL,
    discount_rate double precision,
    total_price double precision NOT NULL,
    pricing_detail_id integer NOT NULL,
    settlement_order_id integer,
    settlement_company_id integer,
    settlement_status character varying(20),
    settlement_date timestamp without time zone,
    settlement_notes text
);


ALTER TABLE public.settlement_order_details OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4244 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.pricing_order_id IS '批价单ID';


--
-- TOC entry 4245 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.product_name; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.product_name IS '产品名称';


--
-- TOC entry 4246 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.product_model; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.product_model IS '产品型号';


--
-- TOC entry 4247 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.product_desc; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.product_desc IS '产品描述';


--
-- TOC entry 4248 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.brand; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.brand IS '品牌';


--
-- TOC entry 4249 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.unit; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.unit IS '单位';


--
-- TOC entry 4250 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.product_mn; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.product_mn IS '产品MN编码';


--
-- TOC entry 4251 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.market_price; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.market_price IS '市场价';


--
-- TOC entry 4252 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.unit_price; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.unit_price IS '单价';


--
-- TOC entry 4253 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.quantity; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.quantity IS '数量';


--
-- TOC entry 4254 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.discount_rate IS '折扣率';


--
-- TOC entry 4255 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.total_price; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.total_price IS '小计金额';


--
-- TOC entry 4256 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.pricing_detail_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.pricing_detail_id IS '关联批价单明细ID';


--
-- TOC entry 4257 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.settlement_order_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.settlement_order_id IS '结算单ID';


--
-- TOC entry 4258 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.settlement_company_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.settlement_company_id IS '结算目标公司ID';


--
-- TOC entry 4259 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.settlement_status; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.settlement_status IS '结算状态: pending, completed';


--
-- TOC entry 4260 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.settlement_date; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.settlement_date IS '结算完成时间';


--
-- TOC entry 4261 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN settlement_order_details.settlement_notes; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_order_details.settlement_notes IS '结算备注';


--
-- TOC entry 315 (class 1259 OID 19765)
-- Name: settlement_order_details_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.settlement_order_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.settlement_order_details_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4262 (class 0 OID 0)
-- Dependencies: 315
-- Name: settlement_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.settlement_order_details_id_seq OWNED BY public.settlement_order_details.id;


--
-- TOC entry 254 (class 1259 OID 19266)
-- Name: settlement_orders; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.settlement_orders (
    id integer NOT NULL,
    order_number character varying(64) NOT NULL,
    pricing_order_id integer NOT NULL,
    project_id integer NOT NULL,
    quotation_id integer NOT NULL,
    distributor_id integer NOT NULL,
    dealer_id integer,
    total_amount double precision,
    total_discount_rate double precision,
    status character varying(20),
    approved_by integer,
    approved_at timestamp without time zone,
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.settlement_orders OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4263 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.order_number; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.order_number IS '结算单号';


--
-- TOC entry 4264 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.pricing_order_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.pricing_order_id IS '关联批价单ID';


--
-- TOC entry 4265 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.project_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.project_id IS '项目ID';


--
-- TOC entry 4266 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.quotation_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.quotation_id IS '报价单ID';


--
-- TOC entry 4267 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.distributor_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.distributor_id IS '分销商ID';


--
-- TOC entry 4268 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.dealer_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.dealer_id IS '经销商ID（辅助信息）';


--
-- TOC entry 4269 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.total_amount; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.total_amount IS '结算总金额';


--
-- TOC entry 4270 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.total_discount_rate; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.total_discount_rate IS '结算总折扣率';


--
-- TOC entry 4271 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.status; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.status IS '结算单状态';


--
-- TOC entry 4272 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.approved_by; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.approved_by IS '批准人';


--
-- TOC entry 4273 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.approved_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.approved_at IS '批准时间';


--
-- TOC entry 4274 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.created_by; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.created_by IS '创建人';


--
-- TOC entry 4275 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.created_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.created_at IS '创建时间';


--
-- TOC entry 4276 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN settlement_orders.updated_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.settlement_orders.updated_at IS '更新时间';


--
-- TOC entry 253 (class 1259 OID 19265)
-- Name: settlement_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.settlement_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.settlement_orders_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4277 (class 0 OID 0)
-- Dependencies: 253
-- Name: settlement_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.settlement_orders_id_seq OWNED BY public.settlement_orders.id;


--
-- TOC entry 260 (class 1259 OID 19435)
-- Name: settlements; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.settlements (
    id integer NOT NULL,
    settlement_number character varying(50) NOT NULL,
    company_id integer NOT NULL,
    settlement_date timestamp without time zone,
    status character varying(20),
    total_items integer,
    description text,
    created_by_id integer NOT NULL,
    approved_by_id integer,
    approved_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.settlements OWNER TO pma_db_sp8d_user;

--
-- TOC entry 259 (class 1259 OID 19434)
-- Name: settlements_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.settlements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.settlements_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4278 (class 0 OID 0)
-- Dependencies: 259
-- Name: settlements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.settlements_id_seq OWNED BY public.settlements.id;


--
-- TOC entry 316 (class 1259 OID 19766)
-- Name: solution_manager_email_settings; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.solution_manager_email_settings (
    id integer NOT NULL,
    user_id integer NOT NULL,
    quotation_created boolean,
    quotation_updated boolean,
    project_created boolean,
    project_stage_changed boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.solution_manager_email_settings OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4279 (class 0 OID 0)
-- Dependencies: 316
-- Name: COLUMN solution_manager_email_settings.user_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.solution_manager_email_settings.user_id IS '解决方案经理用户ID';


--
-- TOC entry 4280 (class 0 OID 0)
-- Dependencies: 316
-- Name: COLUMN solution_manager_email_settings.quotation_created; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_created IS '报价单新建通知';


--
-- TOC entry 4281 (class 0 OID 0)
-- Dependencies: 316
-- Name: COLUMN solution_manager_email_settings.quotation_updated; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_updated IS '报价单更新通知';


--
-- TOC entry 4282 (class 0 OID 0)
-- Dependencies: 316
-- Name: COLUMN solution_manager_email_settings.project_created; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_created IS '项目新建通知';


--
-- TOC entry 4283 (class 0 OID 0)
-- Dependencies: 316
-- Name: COLUMN solution_manager_email_settings.project_stage_changed; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_stage_changed IS '项目阶段推进通知';


--
-- TOC entry 317 (class 1259 OID 19769)
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.solution_manager_email_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.solution_manager_email_settings_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4284 (class 0 OID 0)
-- Dependencies: 317
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.solution_manager_email_settings_id_seq OWNED BY public.solution_manager_email_settings.id;


--
-- TOC entry 318 (class 1259 OID 19770)
-- Name: system_metrics; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.system_metrics (
    id integer NOT NULL,
    version_id integer,
    avg_response_time double precision,
    max_response_time double precision,
    error_rate double precision,
    active_users integer,
    total_requests integer,
    database_size bigint,
    cpu_usage double precision,
    memory_usage double precision,
    disk_usage double precision,
    recorded_at timestamp without time zone
);


ALTER TABLE public.system_metrics OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4285 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.version_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.version_id IS '版本ID';


--
-- TOC entry 4286 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.avg_response_time; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.avg_response_time IS '平均响应时间（毫秒）';


--
-- TOC entry 4287 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.max_response_time; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.max_response_time IS '最大响应时间（毫秒）';


--
-- TOC entry 4288 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.error_rate; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.error_rate IS '错误率（百分比）';


--
-- TOC entry 4289 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.active_users; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.active_users IS '活跃用户数';


--
-- TOC entry 4290 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.total_requests; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.total_requests IS '总请求数';


--
-- TOC entry 4291 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.database_size; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.database_size IS '数据库大小（字节）';


--
-- TOC entry 4292 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.cpu_usage; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.cpu_usage IS 'CPU使用率（百分比）';


--
-- TOC entry 4293 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.memory_usage; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.memory_usage IS '内存使用率（百分比）';


--
-- TOC entry 4294 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.disk_usage; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.disk_usage IS '磁盘使用率（百分比）';


--
-- TOC entry 4295 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN system_metrics.recorded_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.system_metrics.recorded_at IS '记录时间';


--
-- TOC entry 319 (class 1259 OID 19773)
-- Name: system_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.system_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_metrics_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4296 (class 0 OID 0)
-- Dependencies: 319
-- Name: system_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.system_metrics_id_seq OWNED BY public.system_metrics.id;


--
-- TOC entry 320 (class 1259 OID 19774)
-- Name: system_settings; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.system_settings (
    id integer NOT NULL,
    key character varying(100) NOT NULL,
    value text,
    description character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.system_settings OWNER TO pma_db_sp8d_user;

--
-- TOC entry 321 (class 1259 OID 19779)
-- Name: system_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.system_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_settings_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4297 (class 0 OID 0)
-- Dependencies: 321
-- Name: system_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.system_settings_id_seq OWNED BY public.system_settings.id;


--
-- TOC entry 322 (class 1259 OID 19780)
-- Name: upgrade_logs; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.upgrade_logs (
    id integer NOT NULL,
    version_id integer NOT NULL,
    from_version character varying(20),
    to_version character varying(20) NOT NULL,
    upgrade_date timestamp without time zone NOT NULL,
    upgrade_type character varying(20),
    status character varying(20),
    upgrade_notes text,
    error_message text,
    duration_seconds integer,
    operator_id integer,
    operator_name character varying(50),
    environment character varying(20),
    server_info text
);


ALTER TABLE public.upgrade_logs OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4298 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.version_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.version_id IS '版本ID';


--
-- TOC entry 4299 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.from_version; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.from_version IS '升级前版本';


--
-- TOC entry 4300 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.to_version; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.to_version IS '升级后版本';


--
-- TOC entry 4301 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.upgrade_date; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_date IS '升级时间';


--
-- TOC entry 4302 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.upgrade_type; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_type IS '升级类型：manual/automatic';


--
-- TOC entry 4303 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.status; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.status IS '升级状态：success/failed/rollback';


--
-- TOC entry 4304 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.upgrade_notes; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_notes IS '升级说明';


--
-- TOC entry 4305 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.error_message; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.error_message IS '错误信息（如果升级失败）';


--
-- TOC entry 4306 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.duration_seconds; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.duration_seconds IS '升级耗时（秒）';


--
-- TOC entry 4307 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.operator_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.operator_id IS '操作人员ID';


--
-- TOC entry 4308 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.operator_name; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.operator_name IS '操作人员姓名';


--
-- TOC entry 4309 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.environment; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.environment IS '升级环境';


--
-- TOC entry 4310 (class 0 OID 0)
-- Dependencies: 322
-- Name: COLUMN upgrade_logs.server_info; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.upgrade_logs.server_info IS '服务器信息';


--
-- TOC entry 323 (class 1259 OID 19785)
-- Name: upgrade_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.upgrade_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.upgrade_logs_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4311 (class 0 OID 0)
-- Dependencies: 323
-- Name: upgrade_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.upgrade_logs_id_seq OWNED BY public.upgrade_logs.id;


--
-- TOC entry 324 (class 1259 OID 19786)
-- Name: user_event_subscriptions; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.user_event_subscriptions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    target_user_id integer NOT NULL,
    event_id integer NOT NULL,
    enabled boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.user_event_subscriptions OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4312 (class 0 OID 0)
-- Dependencies: 324
-- Name: COLUMN user_event_subscriptions.user_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.user_event_subscriptions.user_id IS '订阅者用户ID';


--
-- TOC entry 4313 (class 0 OID 0)
-- Dependencies: 324
-- Name: COLUMN user_event_subscriptions.target_user_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.user_event_subscriptions.target_user_id IS '被订阅的用户ID';


--
-- TOC entry 4314 (class 0 OID 0)
-- Dependencies: 324
-- Name: COLUMN user_event_subscriptions.event_id; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.user_event_subscriptions.event_id IS '事件ID';


--
-- TOC entry 4315 (class 0 OID 0)
-- Dependencies: 324
-- Name: COLUMN user_event_subscriptions.enabled; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.user_event_subscriptions.enabled IS '是否启用订阅';


--
-- TOC entry 325 (class 1259 OID 19789)
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.user_event_subscriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_event_subscriptions_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4316 (class 0 OID 0)
-- Dependencies: 325
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.user_event_subscriptions_id_seq OWNED BY public.user_event_subscriptions.id;


--
-- TOC entry 222 (class 1259 OID 18054)
-- Name: users; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    password_hash character varying(256) NOT NULL,
    real_name character varying(80),
    company_name character varying(100),
    email character varying(120),
    phone character varying(20),
    department character varying(100),
    is_department_manager boolean,
    role character varying(20),
    is_profile_complete boolean,
    wechat_openid character varying(64),
    wechat_nickname character varying(64),
    wechat_avatar character varying(256),
    is_active boolean,
    created_at double precision,
    last_login double precision,
    updated_at double precision
);


ALTER TABLE public.users OWNER TO pma_db_sp8d_user;

--
-- TOC entry 221 (class 1259 OID 18053)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4317 (class 0 OID 0)
-- Dependencies: 221
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 250 (class 1259 OID 18875)
-- Name: version_records; Type: TABLE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE TABLE public.version_records (
    id integer NOT NULL,
    version_number character varying(20) NOT NULL,
    version_name character varying(100),
    release_date timestamp without time zone NOT NULL,
    description text,
    is_current boolean,
    environment character varying(20),
    total_features integer,
    total_fixes integer,
    total_improvements integer,
    git_commit character varying(40),
    build_number character varying(20),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.version_records OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4318 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.version_number; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.version_number IS '版本号，如1.0.0';


--
-- TOC entry 4319 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.version_name; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.version_name IS '版本名称';


--
-- TOC entry 4320 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.release_date; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.release_date IS '发布日期';


--
-- TOC entry 4321 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.description; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.description IS '版本描述';


--
-- TOC entry 4322 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.is_current; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.is_current IS '是否为当前版本';


--
-- TOC entry 4323 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.environment; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.environment IS '环境：development/production';


--
-- TOC entry 4324 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.total_features; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.total_features IS '新增功能数量';


--
-- TOC entry 4325 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.total_fixes; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.total_fixes IS '修复问题数量';


--
-- TOC entry 4326 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.total_improvements; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.total_improvements IS '改进数量';


--
-- TOC entry 4327 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.git_commit; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.git_commit IS 'Git提交哈希';


--
-- TOC entry 4328 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.build_number; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.build_number IS '构建号';


--
-- TOC entry 4329 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.created_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.created_at IS '创建时间';


--
-- TOC entry 4330 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN version_records.updated_at; Type: COMMENT; Schema: public; Owner: pma_db_sp8d_user
--

COMMENT ON COLUMN public.version_records.updated_at IS '更新时间';


--
-- TOC entry 249 (class 1259 OID 18874)
-- Name: version_records_id_seq; Type: SEQUENCE; Schema: public; Owner: pma_db_sp8d_user
--

CREATE SEQUENCE public.version_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.version_records_id_seq OWNER TO pma_db_sp8d_user;

--
-- TOC entry 4331 (class 0 OID 0)
-- Dependencies: 249
-- Name: version_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pma_db_sp8d_user
--

ALTER SEQUENCE public.version_records_id_seq OWNED BY public.version_records.id;


--
-- TOC entry 3535 (class 2604 OID 19790)
-- Name: action_reply id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.action_reply ALTER COLUMN id SET DEFAULT nextval('public.action_reply_id_seq'::regclass);


--
-- TOC entry 3536 (class 2604 OID 19791)
-- Name: actions id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.actions ALTER COLUMN id SET DEFAULT nextval('public.actions_id_seq'::regclass);


--
-- TOC entry 3537 (class 2604 OID 19792)
-- Name: affiliations id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.affiliations ALTER COLUMN id SET DEFAULT nextval('public.affiliations_id_seq'::regclass);


--
-- TOC entry 3538 (class 2604 OID 19793)
-- Name: approval_instance id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_instance ALTER COLUMN id SET DEFAULT nextval('public.approval_instance_id_seq'::regclass);


--
-- TOC entry 3522 (class 2604 OID 19794)
-- Name: approval_process_template id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_process_template ALTER COLUMN id SET DEFAULT nextval('public.approval_process_template_id_seq'::regclass);


--
-- TOC entry 3540 (class 2604 OID 19795)
-- Name: approval_step id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_step ALTER COLUMN id SET DEFAULT nextval('public.approval_step_id_seq'::regclass);


--
-- TOC entry 3544 (class 2604 OID 19796)
-- Name: change_logs id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.change_logs ALTER COLUMN id SET DEFAULT nextval('public.change_logs_id_seq'::regclass);


--
-- TOC entry 3505 (class 2604 OID 19797)
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- TOC entry 3508 (class 2604 OID 19798)
-- Name: contacts id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.contacts ALTER COLUMN id SET DEFAULT nextval('public.contacts_id_seq'::regclass);


--
-- TOC entry 3545 (class 2604 OID 19799)
-- Name: dev_product_specs id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dev_product_specs ALTER COLUMN id SET DEFAULT nextval('public.dev_product_specs_id_seq'::regclass);


--
-- TOC entry 3511 (class 2604 OID 19800)
-- Name: dev_products id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dev_products ALTER COLUMN id SET DEFAULT nextval('public.dev_products_id_seq'::regclass);


--
-- TOC entry 3546 (class 2604 OID 19801)
-- Name: dictionaries id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dictionaries ALTER COLUMN id SET DEFAULT nextval('public.dictionaries_id_seq'::regclass);


--
-- TOC entry 3547 (class 2604 OID 19802)
-- Name: event_registry id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.event_registry ALTER COLUMN id SET DEFAULT nextval('public.event_registry_id_seq'::regclass);


--
-- TOC entry 3548 (class 2604 OID 19803)
-- Name: feature_changes id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.feature_changes ALTER COLUMN id SET DEFAULT nextval('public.feature_changes_id_seq'::regclass);


--
-- TOC entry 3532 (class 2604 OID 19804)
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- TOC entry 3549 (class 2604 OID 19805)
-- Name: inventory_transactions id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.inventory_transactions ALTER COLUMN id SET DEFAULT nextval('public.inventory_transactions_id_seq'::regclass);


--
-- TOC entry 3550 (class 2604 OID 19806)
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- TOC entry 3551 (class 2604 OID 19807)
-- Name: pricing_order_approval_records id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_order_approval_records ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_approval_records_id_seq'::regclass);


--
-- TOC entry 3531 (class 2604 OID 19808)
-- Name: pricing_order_details id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_order_details ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_details_id_seq'::regclass);


--
-- TOC entry 3527 (class 2604 OID 19809)
-- Name: pricing_orders id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_orders ALTER COLUMN id SET DEFAULT nextval('public.pricing_orders_id_seq'::regclass);


--
-- TOC entry 3497 (class 2604 OID 19810)
-- Name: product_categories id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_categories ALTER COLUMN id SET DEFAULT nextval('public.product_categories_id_seq'::regclass);


--
-- TOC entry 3521 (class 2604 OID 19811)
-- Name: product_code_field_options id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_field_options ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_options_id_seq'::regclass);


--
-- TOC entry 3552 (class 2604 OID 19812)
-- Name: product_code_field_values id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_field_values ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_values_id_seq'::regclass);


--
-- TOC entry 3509 (class 2604 OID 19813)
-- Name: product_code_fields id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_fields ALTER COLUMN id SET DEFAULT nextval('public.product_code_fields_id_seq'::regclass);


--
-- TOC entry 3510 (class 2604 OID 19814)
-- Name: product_codes id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_codes ALTER COLUMN id SET DEFAULT nextval('public.product_codes_id_seq'::regclass);


--
-- TOC entry 3498 (class 2604 OID 19815)
-- Name: product_regions id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_regions ALTER COLUMN id SET DEFAULT nextval('public.product_regions_id_seq'::regclass);


--
-- TOC entry 3507 (class 2604 OID 19816)
-- Name: product_subcategories id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_subcategories ALTER COLUMN id SET DEFAULT nextval('public.product_subcategories_id_seq'::regclass);


--
-- TOC entry 3506 (class 2604 OID 19817)
-- Name: products id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- TOC entry 3553 (class 2604 OID 19818)
-- Name: project_members id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_members ALTER COLUMN id SET DEFAULT nextval('public.project_members_id_seq'::regclass);


--
-- TOC entry 3554 (class 2604 OID 19819)
-- Name: project_rating_records id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_rating_records ALTER COLUMN id SET DEFAULT nextval('public.project_rating_records_id_seq'::regclass);


--
-- TOC entry 3555 (class 2604 OID 19820)
-- Name: project_scoring_config id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_scoring_config ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_config_id_seq'::regclass);


--
-- TOC entry 3560 (class 2604 OID 19821)
-- Name: project_scoring_records id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_scoring_records ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_records_id_seq'::regclass);


--
-- TOC entry 3565 (class 2604 OID 19822)
-- Name: project_stage_history id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_stage_history ALTER COLUMN id SET DEFAULT nextval('public.project_stage_history_id_seq'::regclass);


--
-- TOC entry 3567 (class 2604 OID 19823)
-- Name: project_total_scores id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_total_scores ALTER COLUMN id SET DEFAULT nextval('public.project_total_scores_id_seq'::regclass);


--
-- TOC entry 3499 (class 2604 OID 19824)
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- TOC entry 3577 (class 2604 OID 19825)
-- Name: purchase_order_details id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.purchase_order_details ALTER COLUMN id SET DEFAULT nextval('public.purchase_order_details_id_seq'::regclass);


--
-- TOC entry 3534 (class 2604 OID 19826)
-- Name: purchase_orders id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.purchase_orders ALTER COLUMN id SET DEFAULT nextval('public.purchase_orders_id_seq'::regclass);


--
-- TOC entry 3578 (class 2604 OID 19827)
-- Name: quotation_details id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotation_details ALTER COLUMN id SET DEFAULT nextval('public.quotation_details_id_seq'::regclass);


--
-- TOC entry 3512 (class 2604 OID 19828)
-- Name: quotations id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotations ALTER COLUMN id SET DEFAULT nextval('public.quotations_id_seq'::regclass);


--
-- TOC entry 3580 (class 2604 OID 19829)
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- TOC entry 3581 (class 2604 OID 19830)
-- Name: settlement_details id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_details_id_seq'::regclass);


--
-- TOC entry 3582 (class 2604 OID 19831)
-- Name: settlement_order_details id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_order_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_order_details_id_seq'::regclass);


--
-- TOC entry 3530 (class 2604 OID 19832)
-- Name: settlement_orders id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_orders ALTER COLUMN id SET DEFAULT nextval('public.settlement_orders_id_seq'::regclass);


--
-- TOC entry 3533 (class 2604 OID 19833)
-- Name: settlements id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlements ALTER COLUMN id SET DEFAULT nextval('public.settlements_id_seq'::regclass);


--
-- TOC entry 3583 (class 2604 OID 19834)
-- Name: solution_manager_email_settings id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.solution_manager_email_settings ALTER COLUMN id SET DEFAULT nextval('public.solution_manager_email_settings_id_seq'::regclass);


--
-- TOC entry 3584 (class 2604 OID 19835)
-- Name: system_metrics id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.system_metrics ALTER COLUMN id SET DEFAULT nextval('public.system_metrics_id_seq'::regclass);


--
-- TOC entry 3585 (class 2604 OID 19836)
-- Name: system_settings id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.system_settings ALTER COLUMN id SET DEFAULT nextval('public.system_settings_id_seq'::regclass);


--
-- TOC entry 3586 (class 2604 OID 19837)
-- Name: upgrade_logs id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.upgrade_logs ALTER COLUMN id SET DEFAULT nextval('public.upgrade_logs_id_seq'::regclass);


--
-- TOC entry 3587 (class 2604 OID 19838)
-- Name: user_event_subscriptions id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.user_event_subscriptions ALTER COLUMN id SET DEFAULT nextval('public.user_event_subscriptions_id_seq'::regclass);


--
-- TOC entry 3496 (class 2604 OID 19839)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 3526 (class 2604 OID 19840)
-- Name: version_records id; Type: DEFAULT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.version_records ALTER COLUMN id SET DEFAULT nextval('public.version_records_id_seq'::regclass);


--
-- TOC entry 4038 (class 0 OID 19603)
-- Dependencies: 263
-- Data for Name: action_reply; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.action_reply (id, action_id, parent_reply_id, content, owner_id, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4040 (class 0 OID 19609)
-- Dependencies: 265
-- Data for Name: actions; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.actions (id, date, contact_id, company_id, project_id, communication, created_at, owner_id) FROM stdin;
2	2025-06-13	\N	524	\N	李总表示现在杭州四季酒店的餐饮部在用公网的对讲机了，是小米的；   跟客户提了3种合作模式，李总选择第3种，进行远程技术指导，客户这出人，进行实地操作；我司提供培训等； 再跟最终用户去谈；客户提出的问题：1.关于系统我司是否能进行培训？2.我们公司在杭州有多少用户？这决定了客户是否跟我们进行此模式的合作；3.如果合作的话，分成模式，结算模式是怎样的？	2025-06-13 09:39:26.563559	20
3	2025-06-11	668	476	\N	跟客户约拜访，客户表示最近在休年假，下周再说；	2025-06-13 09:40:13.881163	20
4	2025-06-13	\N	525	\N	客户表示一期跟二期的项目已经在收尾阶段了，维保这块是可以聊的，加了微信后续继续沟通；	2025-06-13 09:49:26.160185	20
\.


--
-- TOC entry 4042 (class 0 OID 19615)
-- Dependencies: 267
-- Data for Name: affiliations; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.affiliations (id, owner_id, viewer_id, created_at) FROM stdin;
143	14	13	1749268821.588618
10	6	4	1746779511.618965
11	9	4	1746779511.6236396
12	14	4	1746779511.6273415
13	13	4	1746779511.6309817
14	16	4	1746779511.6343372
15	7	4	1746779511.637673
16	15	4	1746779511.6410823
17	17	4	1746779511.6449625
144	16	13	1749268821.59286
145	17	13	1749268821.5938659
146	15	13	1749268821.595312
147	18	13	1749268821.596781
148	6	13	1749268821.597939
149	19	13	1749268821.599179
46	7	29	1746925351.10497
123	20	7	1747446680.6893282
125	2	7	1747446680.692526
83	6	10	1747121880.986594
150	16	18	1749808708.5590787
151	19	18	1749808708.6448035
152	13	18	1749808708.6484036
153	17	18	1749808708.6517854
154	25	18	1749808708.6551285
155	24	18	1749808708.6582808
156	23	18	1749808708.7463987
157	14	18	1749808708.74968
158	15	18	1749808708.8439534
\.


--
-- TOC entry 4044 (class 0 OID 19619)
-- Dependencies: 269
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.alembic_version (version_num) FROM stdin;
\.


--
-- TOC entry 4045 (class 0 OID 19622)
-- Dependencies: 270
-- Data for Name: approval_instance; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.approval_instance (id, object_id, object_type, current_step, status, started_at, ended_at, process_id, created_by, template_snapshot, template_version) FROM stdin;
\.


--
-- TOC entry 4023 (class 0 OID 18720)
-- Dependencies: 248
-- Data for Name: approval_process_template; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.approval_process_template (id, name, object_type, is_active, created_by, created_at, required_fields, lock_object_on_start, lock_reason) FROM stdin;
1	销售重点报备流程	project	t	5	2025-05-24 06:57:46.814329	["project_name", "project_type", "report_source", "project_name", "report_source", "project_type"]	t	审批流程进行中，暂时锁定编辑
2	渠道项目报备流程	project	t	5	2025-05-24 06:59:13.929278	["project_name", "project_type", "report_source", "project_name", "project_type", "report_source"]	t	审批流程进行中，暂时锁定编辑
3	销售机会授权审批	project	t	5	2025-05-27 04:30:15.895441	["project_name", "project_type", "report_time", "report_source", "project_name", "report_time", "project_type", "report_source"]	t	审批流程进行中，暂时锁定编辑
\.


--
-- TOC entry 4048 (class 0 OID 19629)
-- Dependencies: 273
-- Data for Name: approval_record; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.approval_record (id, instance_id, step_id, approver_id, action, comment, "timestamp") FROM stdin;
\.


--
-- TOC entry 4049 (class 0 OID 19635)
-- Dependencies: 274
-- Data for Name: approval_step; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.approval_step (id, process_id, step_order, approver_user_id, step_name, send_email, action_type, action_params, editable_fields, cc_users, cc_enabled) FROM stdin;
1	3	1	7	授权	t	authorization	\N	[]	[]	f
2	2	1	19	授权	t	authorization	\N	[]	[]	t
3	1	1	13	授权	t	authorization	\N	[]	[]	t
\.


--
-- TOC entry 4051 (class 0 OID 19644)
-- Dependencies: 276
-- Data for Name: change_logs; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.change_logs (id, module_name, table_name, record_id, operation_type, field_name, old_value, new_value, user_id, user_name, created_at, description, ip_address, user_agent, record_info) FROM stdin;
1	user	users	18	UPDATE	角色	sales_manager	business_admin	5	admin	2025-06-13 07:36:25.262104	\N	10.210.204.229	\N	公司: 和源通信（上海）股份有限公司
2	user	users	18	UPDATE	updated_at	1749786322.4707355	1749800185.2479403	5	admin	2025-06-13 07:36:25.262106	\N	10.210.204.229	\N	公司: 和源通信（上海）股份有限公司
3	user	users	6	UPDATE	角色	sales_manager	ceo	5	admin	2025-06-13 08:10:53.088625	\N	10.210.235.13	\N	公司: 和源通信（上海）股份有限公司
4	user	users	6	UPDATE	updated_at	1749183880.6086416	1749802253.0742986	5	admin	2025-06-13 08:10:53.088627	\N	10.210.235.13	\N	公司: 和源通信（上海）股份有限公司
5	project	projects	624	CREATE	\N	\N	\N	15	lihuawei	2025-06-13 09:32:28.349714	\N	10.210.235.13	\N	项目: 测试批价单项目
6	quotation	quotations	694	CREATE	\N	\N	\N	15	lihuawei	2025-06-13 09:32:48.688406	\N	10.210.204.229	\N	报价单: QU202506-017
7	customer	companies	524	CREATE	\N	\N	\N	20	shengyh	2025-06-13 09:35:34.935956	\N	10.210.177.220	\N	公司: 杭州云沛环保科技有限责任公司
8	customer	companies	525	CREATE	\N	\N	\N	20	shengyh	2025-06-13 09:49:05.122013	\N	10.210.29.225	\N	公司: 芯恩(青岛)集成电路有限公司
\.


--
-- TOC entry 4005 (class 0 OID 18177)
-- Dependencies: 230
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.companies (id, company_code, company_name, country, region, address, industry, company_type, status, created_at, updated_at, notes, is_deleted, owner_id, shared_with_users, share_contacts) FROM stdin;
472	25E14001	上海松江站	CN	上海市	上海市松江区盐仓路	transport	user	active	2025-05-14 01:35:34.354343	2025-05-26 14:20:22.638111		f	20	\N	\N
480	25E14009	国家会展中心	CN	上海市	上海市青浦区崧泽大道333号	government	user	active	2025-05-14 02:40:19.237043	2025-05-27 17:46:07.187653		f	20	\N	\N
148	25E09145	深圳市星河智善科技有限公司	中国	\N	深圳市福田区福田街道岗厦社区彩田路3069号星河世纪A栋39层3910	\N	integrator	active	2025-02-23 00:00:00	2025-05-09 06:43:11.383713	\N	f	17	\N	\N
162	25E09159	香港华艺设计顾问（深圳）有限公司	中国	\N	深圳市南山区南头街道马家龙社区大新路198号创新大厦A栋601	\N	designer	inactive	2024-12-13 23:57:25	2025-05-09 06:43:11.484129	\N	f	17	\N	\N
473	25E14002	上海汽车服务产业集聚区	CN	上海市	上海市普陀区云岭东路570号	transport	user	inactive	2025-05-14 01:47:42.66058	2025-05-14 01:47:42.660583		f	20	\N	\N
478	25E14007	上海浦东丽晶酒店	CN	上海市	上海市浦东新区		user	inactive	2025-05-14 02:11:57.417881	2025-05-21 10:09:14.228185		f	20	\N	\N
518	25F04001	南京天溯自动化控制系统有限公司	CN	江苏省	南京市雨花台区软件大道170-1号	other	integrator	active	2025-06-04 02:22:14.435807	2025-06-04 10:54:29.607967		f	16	[]	t
476	25E14005	上海港国际客运中心	CN	上海市	上海市虹口区东大名路500号上海港国际客运中心（北外滩）B1层3号门	transport	user	active	2025-05-14 02:02:43.465232	2025-06-13 17:40:13.884457		f	20	\N	\N
18	25E09015	创业慧康科技股份有限公司	中国	\N	\N	\N	\N	inactive	2024-06-25 14:38:32	2025-05-09 06:42:32.549246	\N	f	16	\N	\N
34	25E09031	江苏锐泽思通信技术有限公司	中国	\N	\N	\N	\N	inactive	2024-11-10 09:50:41	2025-05-09 06:42:32.665979	\N	f	16	\N	\N
36	25E09033	江苏英仕全通讯科技有限公司	中国	\N	\N	\N	\N	inactive	2024-06-23 13:43:30	2025-05-09 06:42:32.675071	\N	f	16	\N	\N
251	25E09248	上海港国际客运中心开发有限公司	中国	\N	\N	\N	user	inactive	2025-02-26 00:00:00	2025-05-09 06:44:23.989549	\N	f	7	\N	\N
252	25E09249	上海国际机场股份有限公司	中国	\N	上海市浦东新区启航路900号	\N	user	inactive	2025-02-14 00:00:00	2025-05-09 06:44:23.993684	\N	f	7	\N	\N
253	25E09250	上海久事国际体育中心有限公司	中国	\N	上海市嘉定区伊宁路2000号	\N	user	inactive	2025-02-14 00:00:00	2025-05-09 06:44:23.997538	\N	f	7	\N	\N
112	25E09109	广州宇洪科技股份有限公司	中国	\N	天河区软件路11号402室	\N	dealer	inactive	2024-09-28 15:26:05	2025-05-09 06:43:11.063751	\N	f	17	\N	\N
474	25E14003	苏州四季酒店	CN	浙江省	苏州市工业园区四季路88号	\N	user	active	2025-05-14 01:51:18.397436	2025-05-30 00:29:58.890891		f	20	\N	\N
516	25E30001	仁恩格（北京）科技有限公司	CN	北京市	北京市大兴区金苑路甲15号6幢7层B817室	other	integrator	active	2025-05-30 02:00:36.730046	2025-05-30 10:00:36.735193		f	16	[]	t
519	25F04002	江苏方德信息技术有限公司	CN	江苏省	南通市经济技术开发区创业外包服务中心E幢20层2003室	other	integrator	active	2025-06-04 02:55:37.803639	2025-06-04 10:55:37.815658		f	16	[]	t
371	25E09368	上海积塔半导体有限公司	中国	\N	上海临港	\N	user	inactive	2024-09-28 10:00:49	2025-05-09 06:45:19.785784	\N	f	13	\N	\N
496	25E28001	上海瑞康通信科技有限公司	\N	\N	\N	other	dealer	active	2025-05-28 02:56:40.931088	2025-05-28 10:59:17.889261	\N	f	19	[]	t
497	25E28002	上海瀚网智能科技有限公司	\N	\N	\N	other	dealer	active	2025-05-28 03:00:27.867784	2025-05-28 11:01:00.457872	\N	f	19	[]	t
498	25E28003	上海淳泊信息科技有限公司	\N	\N	\N	other	dealer	active	2025-05-28 03:02:42.470548	2025-05-28 11:03:10.800244	\N	f	19	[]	t
500	25E28005	福淳智能科技(四川)有限公司	\N	\N	\N	other	dealer	active	2025-05-28 03:04:58.676863	2025-05-28 11:07:17.589872	\N	f	19	[]	t
501	25E28006	广州宇洪科技股份有限公司	\N	\N	\N	other	dealer	active	2025-05-28 03:08:14.385105	2025-05-28 11:10:01.54253	\N	f	19	[]	t
517	25E30002	上海恒高船舶设计有限公司	CN	上海市	上海市浦东新区金海路1000号12号楼	manufacturing	designer	active	2025-05-30 04:38:03.235945	2025-05-30 12:41:35.222951		f	7	[]	t
249	25E09246	沪东中华造船（集团）有限公司	中国	\N	浦东大道2851号	\N	user	active	2025-03-15 00:00:00	2025-05-30 12:45:46.600778	\N	f	7	\N	\N
444	25E09441	上海华虹宏力半导体制造有限公司	中国	\N	中国（上海）自由贸易试验区祖冲之路1399号	\N	user	active	2025-02-21 00:00:00	2025-06-10 14:06:21.035665	\N	f	2	\N	\N
499	25E28004	上海福玛通信信息科技有限公司	\N	\N	\N	other	dealer	inactive	2025-05-28 03:03:42.640623	2025-05-28 11:04:18.774984	\N	f	19	[]	t
503	25E28008	北京联航迅达通信技术有限公司	\N	\N	\N	other	dealer	active	2025-05-28 03:13:46.244519	2025-05-28 11:16:20.159693	\N	f	19	[]	t
504	25E28009	苏州邦耀电子科技有限公司	\N	\N	\N	other	dealer	active	2025-05-28 03:17:20.870426	2025-05-28 11:17:48.562104	\N	f	19	[]	t
505	25E28010	敦力(南京)科技有限公司	\N	\N	\N	other	dealer	active	2025-05-28 03:18:21.121511	2025-05-28 11:18:50.358821	\N	f	19	[]	t
506	25E28011	广州洪昇智能科技有限公司	\N	\N	\N	other	dealer	active	2025-05-28 03:19:25.560314	2025-05-28 11:20:28.843553	\N	f	19	[]	t
502	25E28007	浙江航博智能工程有限公司	\N	\N	\N	other	dealer	active	2025-05-28 03:10:51.291522	2025-05-28 11:11:34.206175	\N	f	19	[]	t
520	25F05001	民航机场建设集团西南设计研究院有限公司	CN	四川省	成都 	transport	designer	inactive	2025-06-05 06:39:53.123775	2025-06-05 14:39:53.145722		f	13	[]	t
435	25E09432	科思创聚合物(中国)有限公司	中国	\N	化工区目华路82号	\N	user	active	2025-02-21 00:00:00	2025-06-12 13:38:02.035528	\N	f	2	\N	\N
135	25E09132	深圳市电信工程有限公司	中国	\N	深圳市罗湖区洪湖一街10号大院12栋	\N	integrator	inactive	2025-04-07 00:00:00	2025-05-09 06:43:11.26653	\N	f	17	\N	\N
154	25E09151	深圳英飞拓科技股份有限公司	CN	广东省	深圳市龙华区观湖街道鹭湖社区观盛五路英飞好成科技园1515	real_estate	integrator	active	2024-04-16 11:08:09	2025-06-08 21:44:36.409569	None	f	17	\N	\N
141	25E09138	深圳市旗云智能科技有限公司	中国	\N	深圳市龙华区民治街道大岭社区安宏基天曜广场1栋A座12A01	\N	integrator	active	2024-05-12 14:16:56.999	2025-05-09 06:43:11.341961	\N	f	17	\N	\N
264	25E09261	中芯南方集成电路制造有限公司	\N	\N	\N	\N	user	active	2025-02-13 00:00:00	2025-06-12 13:47:02.357186	\N	f	7	\N	\N
486	25E16003	上海国鑫音达信息科技有限公司	CN	上海市	上海市金山区吕巷镇璜溪西街88号	manufacturing	user	active	2025-05-16 03:56:17.3426	2025-06-12 13:49:22.954114	合作厂商	f	7	[]	t
259	25E09256	上海中心大厦建设发展有限公司	中国	\N	陆家嘴环路479号	\N	user	active	2025-02-14 00:00:00	2025-06-12 13:54:15.906464	\N	f	7	\N	\N
164	25E09161	中建科工集团有限公司	中国	\N	深圳市南山区粤海街道蔚蓝海岸社区中心路3331号中建科工大厦38层3801	\N	integrator	active	2025-03-01 00:00:00	2025-05-09 06:43:11.54278	\N	f	17	\N	\N
508	25E28013	合肥兴和通讯设备有限公司	\N	\N	\N	other	dealer	active	2025-05-28 08:29:12.608792	2025-05-28 16:29:45.268295	\N	f	19	[]	t
509	25E28014	深圳市信元智能系统有限公司	\N	\N	\N	other	dealer	active	2025-05-28 08:30:26.230422	2025-05-28 16:31:03.847225	\N	f	19	[]	t
511	25E28016	北京国隆信达通信技术有限公司	\N	\N	\N	other	dealer	active	2025-05-28 08:32:48.197776	2025-05-28 16:33:54.181653	\N	f	19	[]	t
513	25E28018	成都市天皓科技有限公司	\N	\N	\N	other	dealer	active	2025-05-28 08:35:26.072464	2025-05-28 16:35:57.097375	\N	f	19	[]	t
514	25E28019	上海常森电子有限公司	\N	\N	\N	other	dealer	active	2025-05-28 08:36:50.905352	2025-05-28 16:37:37.047202	\N	f	19	[]	t
515	25E28020	杭州合义信息技术有限公司	\N	\N	\N	other	dealer	active	2025-05-28 08:38:17.112682	2025-05-28 16:38:49.124497	\N	f	19	[]	t
512	25E28017	北京佰沃信通科技有限公司	\N	\N	\N	other	dealer	inactive	2025-05-28 08:34:27.015704	2025-05-28 16:34:54.963143	\N	f	19	[]	t
507	25E28012	重庆大鹏鸟科技有限公司	\N	\N	\N	other	dealer	inactive	2025-05-28 08:28:07.244959	2025-05-28 16:28:40.047644	\N	f	19	[]	t
510	25E28015	天津比信科技股份有限公司	\N	\N	\N	other	dealer	inactive	2025-05-28 08:31:49.946498	2025-05-28 16:32:16.081152	\N	f	19	[]	t
142	25E09139	深圳市深国铁路物流发展有限公司	中国	\N	深圳市龙岗区南湾街道下李朗社区李东路10号海大科技园4栋1801	\N	user	active	2024-08-31 11:11:04	2025-06-08 22:20:09.375334	\N	f	17	\N	\N
521	25F10001	上海新美阁展览有限公司	CN	上海市	浦东新区牡丹路60号	other	user	active	2025-06-10 02:09:39.569394	2025-06-10 10:16:18.684314	主要从事展览、会议会务等各种规模活动的策划、运营与执行，以及展会工程的设计与搭建等等	f	7	[]	t
246	25E09243	中铁二局建设有限公司	中国	\N	\N	\N	integrator	inactive	2024-08-21 00:00:00	2025-05-09 06:44:00.369879	\N	f	14	\N	\N
522	25F11001	北京中电力泰科有限公司	CN	北京市	北京市朝阳路	transport	integrator	active	2025-06-11 06:37:14.661601	2025-06-11 14:37:14.745849		f	13	[]	t
381	25E09378	深圳达实智能股份有限公司	CN	None	深圳市南山区高新技术村W1栋A座五楼	real_estate	integrator	inactive	2024-02-22 00:00:00	2025-06-08 22:26:27.09929	None	f	13	[17]	f
523	25F13001	测试用***有限公司	CN	上海市	武威路88号	other	dealer	active	2025-06-13 02:55:45.191022	2025-06-13 12:50:40.63024		f	18	[]	t
119	25E09116	华阳国际设计集团	中国	\N	深圳市龙华区民治街道北站社区龙华设计产业园总部大厦3栋101	\N	designer	active	2025-03-21 00:00:00	2025-05-09 06:43:11.14255	\N	f	17	\N	\N
125	25E09122	厦门万安智能有限公司深圳分公司	中国	\N	\r\n南山区粤海街道高新区社区高新南九道45号西北工业大学三航科技大厦8层8008	\N	designer	active	2024-10-09 14:50:47	2025-05-09 06:43:11.168566	\N	f	17	\N	\N
138	25E09135	深圳市建筑设计研究总院有限公司	中国	\N	福田区振华路八号	\N	designer	active	2024-09-14 16:48:50	2025-05-09 06:43:11.277794	\N	f	17	\N	\N
81	25E09078	中宏恒大智能科技工程有限公司	中国	\N	苏州吴中经济开发区越溪街道东太湖路38号6幢	\N	integrator	active	2024-06-20 17:43:20.999	2025-05-09 06:42:33.177116	\N	f	16	\N	\N
85	25E09082	中建电子工程有限公司-北京分公司	中国	\N	\N	\N	integrator	active	2024-12-02 09:11:35	2025-05-09 06:42:33.249725	\N	f	16	\N	\N
524	25F13002	杭州云沛环保科技有限责任公司	CN	浙江省	浙江省杭州市上城区大世界五金城28幢214室	other	integrator	active	2025-06-13 09:35:34.925302	2025-06-13 17:39:26.567302		f	20	[]	t
525	25F13003	芯恩(青岛)集成电路有限公司	CN	山东省	中国山东省青岛市西海岸新区山王河路1088号	manufacturing	user	active	2025-06-13 09:49:05.113526	2025-06-13 17:49:26.163459		f	20	[]	t
55	25E09052	清华同方股份有限公司同方智慧建筑与园区公司	中国	\N	\N	\N	integrator	inactive	2025-03-01 00:00:00	2025-05-09 06:42:32.970951	\N	f	16	\N	\N
56	25E09053	上海安保设备开发工程有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:25:49	2025-05-09 06:42:32.975377	\N	f	16	\N	\N
57	25E09054	上海宝冶集团有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:40:00	2025-05-09 06:42:32.980579	\N	f	16	\N	\N
60	25E09057	尚高科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:06:57	2025-05-09 06:42:32.9914	\N	f	16	\N	\N
61	25E09058	盛云科技有限公司南京分公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:19:57	2025-05-09 06:42:32.9949	\N	f	16	\N	\N
64	25E09061	苏州宏凡信息科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-11-17 17:33:28	2025-05-09 06:42:33.0439	\N	f	16	\N	\N
65	25E09062	苏州朗捷通智能科技有限公司	中国	\N	苏州高新区邓尉路109号1幢狮山街道办公楼211室	\N	integrator	inactive	2024-03-02 00:00:00	2025-05-09 06:42:33.047568	\N	f	16	\N	\N
67	25E09064	苏州中亿丰科技有限公司	中国	\N	苏州市姑苏区公园路55号智能科技大厦	\N	integrator	inactive	2024-03-02 00:00:00	2025-05-09 06:42:33.055151	\N	f	16	\N	\N
68	25E09065	太极计算机股份有限公司	中国	\N	北京市海淀区北四环中路211号	\N	integrator	inactive	2024-05-07 08:50:54	2025-05-09 06:42:33.060218	\N	f	16	\N	\N
69	25E09066	天津奥杰信诚科技有限公司	中国	\N	天津市南开区航海道西端南侧金杭大厦1号楼2门802	\N	integrator	inactive	2025-02-08 00:00:00	2025-05-09 06:42:33.063666	\N	f	16	\N	\N
71	25E09068	天津市健坤长弘工程股份有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:31:54	2025-05-09 06:42:33.075173	\N	f	16	\N	\N
72	25E09069	天威虎建设集团有限公司	中国	\N	南京市鼓楼区江东北路301号滨江广场01幢20层	\N	integrator	inactive	2024-06-20 17:19:31	2025-05-09 06:42:33.079136	\N	f	16	\N	\N
74	25E09071	无锡简成道工程技术有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:29:05.999	2025-05-09 06:42:33.14502	\N	f	16	\N	\N
75	25E09072	泽宇科技工程有限公司	中国	\N	上海市虹桥路693号30弄202室	\N	integrator	inactive	2024-12-08 19:32:10	2025-05-09 06:42:33.150778	\N	f	16	\N	\N
80	25E09077	中国江苏国际经济技术合作有限公司	中国	\N	\N	\N	integrator	inactive	2024-12-29 09:05:42	2025-05-09 06:42:33.173496	\N	f	16	\N	\N
82	25E09079	中辉至诚北京建设工程有限公司	中国	\N	\N	\N	integrator	inactive	2025-04-20 00:00:00	2025-05-09 06:42:33.182697	\N	f	16	\N	\N
83	25E09080	中建八局第三建设有限公司	中国	\N	栖霞区绕门路	\N	integrator	inactive	2024-12-02 08:47:31	2025-05-09 06:42:33.24171	\N	f	16	\N	\N
86	25E09083	中建电子工程有限公司-上海分公司杭州办事处	中国	\N	\N	\N	integrator	inactive	2024-04-21 10:51:32	2025-05-09 06:42:33.253261	\N	f	16	\N	\N
87	25E09084	中建二局数字化智能分公司	中国	\N	\N	\N	integrator	inactive	2024-06-23 13:54:10.999	2025-05-09 06:42:33.256849	\N	f	16	\N	\N
447	25E09444	上海申弗商业管理有限公司	中国	\N	\N	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.41104	\N	f	2	\N	\N
271	25E09268	杭州北控科技有限公司	中国	\N	\N	\N	designer	inactive	2025-04-15 00:00:00	2025-05-09 06:44:49.024551	\N	f	15	\N	\N
127	25E09124	厦门纵横集团科技股份有限公司	中国	\N	思明区软件园二期观日路16号302单元	\N	integrator	active	2024-09-28 15:57:39.999	2025-05-09 06:43:11.176288	\N	f	17	\N	\N
482	25E14011	上海博物馆东馆	CN	上海市	上海市浦东新区世纪大道1952号	\N	user	active	2025-05-14 02:53:05.711723	2025-06-06 10:15:12.394368		f	20	\N	\N
4	25E09001	SK海力士（无锡）产业发展有限公司	中国	\N	暂无	\N	user	inactive	2024-03-02 13:04:49.999	2025-05-09 06:42:32.478059	\N	f	16	\N	\N
88	25E09085	中建四局安装公司深圳分公司	中国	\N	深圳市龙华新区龙华街道梅龙大道98号	\N	integrator	inactive	2024-09-22 16:37:51.999	2025-05-09 06:42:33.260633	\N	f	16	\N	\N
91	25E09088	中邮建技术有限公司无锡分公司	中国	\N	无锡市水厂路11号	\N	integrator	inactive	2024-06-20 18:07:40	2025-05-09 06:42:33.274327	\N	f	16	\N	\N
96	25E09093	鼎熙国讯科技有限公司	中国	\N	广东省广州市天河区大观南路67号701房	\N	integrator	inactive	2024-08-19 11:28:38.999	2025-05-09 06:43:10.965049	\N	f	17	\N	\N
97	25E09094	广东创能科技股份有限公司	中国	\N	广东省广州市天河区软件路15号5楼501室	\N	integrator	inactive	2024-05-18 16:30:27	2025-05-09 06:43:10.969714	\N	f	17	\N	\N
98	25E09095	广东恒信安电子有限公司	中国	\N	龙湖区长江路17号1201单元	\N	integrator	inactive	2024-10-19 17:02:44	2025-05-09 06:43:10.973537	\N	f	17	\N	\N
99	25E09096	广东宏景科技股份有限公司	中国	\N	广州市黄埔区映日路111号	\N	integrator	inactive	2025-03-08 00:00:00	2025-05-09 06:43:10.977327	\N	f	17	\N	\N
102	25E09099	广东省工业设备安装有限公司	中国	\N	重庆市南岸区南滨路长江国际写字楼15层	\N	integrator	inactive	2024-10-09 14:54:03	2025-05-09 06:43:10.991735	\N	f	17	\N	\N
106	25E09103	广州宝露智能科技有限公司	中国	\N	广州市天河区桃园中路339号102单元、202单元	\N	integrator	inactive	2025-02-22 00:00:00	2025-05-09 06:43:11.039082	\N	f	17	\N	\N
108	25E09105	广州广电五舟科技股份有限公司	中国	\N	广州市黄埔区开源大道11号C2栋401室	\N	integrator	inactive	2024-11-20 15:48:49.999	2025-05-09 06:43:11.047502	\N	f	17	\N	\N
110	25E09107	广州网远信息技术有限公司	中国	\N	广州市黄埔区科学大道162号B1栋1003房	\N	integrator	inactive	2024-07-20 14:17:31	2025-05-09 06:43:11.055635	\N	f	17	\N	\N
111	25E09108	广州鑫宇视通科技有限公司	中国	\N	广州市天河区中山大道建中路5号1101、1102房	\N	integrator	inactive	2025-04-19 00:00:00	2025-05-09 06:43:11.060204	\N	f	17	\N	\N
113	25E09110	广州中科诺泰技术有限公司	中国	\N	广州天河区信源大厦3206	\N	integrator	inactive	2024-06-27 21:51:35	2025-05-09 06:43:11.067297	\N	f	17	\N	\N
114	25E09111	广州中御信息科技有限公司	中国	\N	广州市天河区荷光路3号231室	\N	integrator	inactive	2024-11-16 16:51:17	2025-05-09 06:43:11.072015	\N	f	17	\N	\N
115	25E09112	海南联炜智能科技有限公司	中国	\N	玉沙路玉沙广场京华城2幢2102室	\N	integrator	inactive	2024-09-28 15:33:04	2025-05-09 06:43:11.075961	\N	f	17	\N	\N
116	25E09113	浩天建工集团有限公司	中国	\N	中国（湖南）自由贸易试验区长沙片区芙蓉区隆平高科技园合平路618号A座202-40	\N	integrator	inactive	2024-05-12 14:19:24.999	2025-05-09 06:43:11.079842	\N	f	17	\N	\N
121	25E09118	科越工程苏州有限公司 	中国	\N	中国（江苏）自由贸易试验区苏州片区苏州工业园区裕新路188号同程大厦B区9楼	\N	integrator	inactive	2025-03-08 00:00:00	2025-05-09 06:43:11.150489	\N	f	17	\N	\N
122	25E09119	联通数字科技有限公司	中国	\N	北京市北京经济技术开发区科谷一街10号院8号楼12层1201（北京自贸试验区高端产业片区亦庄组团）	\N	integrator	inactive	2025-04-24 00:00:00	2025-05-09 06:43:11.155579	\N	f	17	\N	\N
124	25E09121	厦门万安智能有限公司	中国	\N	厦门市思明区观日路28号301室	\N	integrator	inactive	2024-10-09 14:48:39	2025-05-09 06:43:11.164865	\N	f	17	\N	\N
126	25E09123	厦门中智达信息科技有限公司	中国	\N	思明区软件园二期观日路16号302单元	\N	integrator	inactive	2024-09-28 16:04:05	2025-05-09 06:43:11.172376	\N	f	17	\N	\N
128	25E09125	汕头市晖信电器科技有限公司	中国	\N	汕头市龙湖区珠池路60号凯胜悦景轩207、208号	\N	integrator	inactive	2024-08-10 20:51:16.999	2025-05-09 06:43:11.179998	\N	f	17	\N	\N
132	25E09129	深圳三图建设集团有限公司	中国	\N	深圳市福田区沙头街道天安社区泰然九路11号海松大厦A座二层	\N	integrator	inactive	2024-06-22 16:22:24	2025-05-09 06:43:11.252237	\N	f	17	\N	\N
24	25E09021	河南空港建设发展有限公司	中国	\N	\N	\N	user	inactive	2024-12-08 19:16:13	2025-05-09 06:42:32.570683	\N	f	16	\N	\N
133	25E09130	深圳市博达安智能科技有限公司	中国	\N	深圳市龙岗区龙城街道回龙埔社区恒明湾创汇中心3栋A座2702	\N	integrator	inactive	2024-05-18 16:32:14	2025-05-09 06:43:11.257247	\N	f	17	\N	\N
134	25E09131	深圳市畅想科技有限公司	中国	\N	龙岗区坂田雪岗南路91号三楼南	\N	integrator	inactive	2024-09-28 15:45:02	2025-05-09 06:43:11.262651	\N	f	17	\N	\N
136	25E09133	深圳市和一实业有限公司	中国	\N	深圳市南山区南山大道3838号设计产业园区金栋四层403、405、406	\N	integrator	inactive	2024-12-07 13:34:01	2025-05-09 06:43:11.270321	\N	f	17	\N	\N
137	25E09134	深圳市华红工程有限公司	中国	\N	深圳市福田区福保街道福保社区市花路19号港安大厦六层B	\N	integrator	inactive	2024-03-23 14:01:18	2025-05-09 06:43:11.273912	\N	f	17	\N	\N
140	25E09137	深圳市迈邦建设有限公司	中国	\N	深圳市龙华区华兴路10号智云ONE大厦A座2307	\N	integrator	inactive	2024-05-25 15:48:06.999	2025-05-09 06:43:11.285464	\N	f	17	\N	\N
144	25E09141	深圳市泰英通信工程有限公司	中国	\N	深圳市龙岗区吉华街道三联社区赛格新城市广场（二期）5号楼1702	\N	integrator	inactive	2025-01-11 18:14:21	2025-05-09 06:43:11.3617	\N	f	17	\N	\N
145	25E09142	深圳市特发泰科通信科技有限公司	中国	\N	福田区福田街道圩镇社区福田路24号海岸环庆大厦25层2502A房	\N	integrator	inactive	2024-03-30 16:39:58	2025-05-09 06:43:11.368042	\N	f	17	\N	\N
146	25E09143	深圳市天威视讯股份有限公司福田分公司	中国	\N	深圳市福田区彩田路6001号	\N	integrator	inactive	2024-08-31 12:35:12	2025-05-09 06:43:11.373864	\N	f	17	\N	\N
149	25E09146	深圳市燕翔云天科技有限公司	中国	\N	深圳市宝安区新安街道海裕社区玉律路花样年花乡家园A座8N	\N	integrator	inactive	2025-03-01 00:00:00	2025-05-09 06:43:11.387643	\N	f	17	\N	\N
150	25E09147	深圳市沅欣智能科技有限公司	中国	\N	南山区南头街道南联社区北环大道11008号豪方天际广场写字楼4606	\N	integrator	inactive	2024-10-09 15:03:49	2025-05-09 06:43:11.39184	\N	f	17	\N	\N
151	25E09148	深圳市智宇实业发展有限公司	中国	\N	深圳市南山区高新技术产业园区科技中二路深圳软件园6栋6楼	\N	integrator	inactive	2024-03-23 14:01:00	2025-05-09 06:43:11.395695	\N	f	17	\N	\N
152	25E09149	深圳市坐标建筑装饰工程股份有限公司	中国	\N	深圳市福田区莲花街道景田西路17号赛格景苑二层（2）、三层（1）	\N	integrator	inactive	2025-01-04 15:36:23	2025-05-09 06:43:11.399484	\N	f	17	\N	\N
155	25E09152	深圳招商建筑科技有限公司	中国	\N	深圳市南山区招商街道水湾社区太子路1号新时代广场29L	\N	integrator	inactive	2025-04-12 00:00:00	2025-05-09 06:43:11.450901	\N	f	17	\N	\N
156	25E09153	深圳智慧空间信息技术有限公司	中国	\N	圳市福田区沙头街道天安社区泰然四路25号天安创新科技广场一期B座207	\N	integrator	inactive	2024-05-12 14:44:22.999	2025-05-09 06:43:11.457461	\N	f	17	\N	\N
157	25E09154	深圳中电瑞达智能技术有限公司	中国	\N	深圳市南山区粤海街道科技园社区深圳市南山区科技园科丰路2号特发信息港大厦B栋8楼	\N	integrator	inactive	2024-11-11 21:04:18	2025-05-09 06:43:11.462063	\N	f	17	\N	\N
158	25E09155	天津田泉智能科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-27 21:36:31	2025-05-09 06:43:11.466647	\N	f	17	\N	\N
160	25E09157	武汉烽火信息集成技术有限公司	中国	\N	洪山区邮科院路８８号	\N	integrator	inactive	2025-03-29 00:00:00	2025-05-09 06:43:11.476484	\N	f	17	\N	\N
166	25E09163	中建三局智能技术有限公司深圳分公司	中国	\N	深圳市福田区福田街道福安社区深南大道4019号航天大厦A1501-A1503	\N	integrator	inactive	2024-08-24 15:28:20.999	2025-05-09 06:43:11.551938	\N	f	17	\N	\N
167	25E09164	中建四局安装工程有限公司	中国	\N	\N	\N	integrator	inactive	2024-08-10 21:01:48	2025-05-09 06:43:11.556008	\N	f	17	\N	\N
170	25E09167	珠海华发数智技术有限公司	中国	\N	珠海市横琴新区华金街58号401-1	\N	integrator	inactive	2025-04-08 00:00:00	2025-05-09 06:43:11.568545	\N	f	17	\N	\N
173	25E09170	北京江森自控有限公司-南京分公司	中国	\N	南京市玄武区珠江路1号（金鹰国际）	\N	integrator	inactive	2024-05-05 00:00:00	2025-05-09 06:43:59.707766	\N	f	14	\N	\N
177	25E09174	霍尼韦尔(天津)有限公司-上海分公司	中国	\N	张江高科技园区环科路555弄1号楼	\N	integrator	inactive	2024-05-05 00:00:00	2025-05-09 06:43:59.775367	\N	f	14	\N	\N
178	25E09175	江西盈石信息工程有限公司	中国	\N	\N	\N	integrator	inactive	2025-03-22 00:00:00	2025-05-09 06:43:59.782241	\N	f	14	\N	\N
179	25E09176	恺驰智能科技有限公司	中国	\N	上海市静安区石门二路街道北京西路669号东展商业大厦9C	\N	integrator	inactive	2024-06-21 00:00:00	2025-05-09 06:43:59.790083	\N	f	14	\N	\N
250	25E09247	浦东新区消防救援支队	中国	\N	上海市浦东新区三林镇浦三路3481号	\N	\N	inactive	2025-04-08 00:00:00	2025-05-09 06:44:23.984626	\N	f	7	\N	\N
254	25E09251	上海市消防救援总队	中国	\N	上海市长宁区中山西路229号 	\N	\N	inactive	2025-04-08 00:00:00	2025-05-09 06:44:24.001755	\N	f	7	\N	\N
279	25E09276	仁恒置地	中国	\N	\N	\N	user	inactive	2025-03-14 00:00:00	2025-05-09 06:44:49.076557	\N	f	15	\N	\N
184	25E09181	上海昂泰兰捷尔信息科技股份有限公司	中国	\N	区西康路1255号3楼	\N	integrator	inactive	2024-02-22 00:00:00	2025-05-09 06:43:59.826935	\N	f	14	\N	\N
185	25E09182	上海宝通汎球电子有限公司	中国	\N	\N	\N	integrator	inactive	2024-12-28 00:00:00	2025-05-09 06:43:59.830746	\N	f	14	\N	\N
188	25E09185	上海电科智能系统股份有限公司	中国	\N	\N	\N	integrator	inactive	2025-03-22 00:00:00	2025-05-09 06:43:59.842177	\N	f	14	\N	\N
189	25E09186	上海电器科学研究所集团有限公司	中国	\N	\N	\N	integrator	inactive	2024-10-09 00:00:00	2025-05-09 06:43:59.846682	\N	f	14	\N	\N
190	25E09187	上海电信科技发展有限公司	中国	\N	\N	\N	integrator	inactive	2025-01-07 00:00:00	2025-05-09 06:43:59.850791	\N	f	14	\N	\N
191	25E09188	上海鼎时智能化设备工程有限公司	中国	\N	\N	\N	integrator	inactive	2025-04-14 00:00:00	2025-05-09 06:43:59.854491	\N	f	14	\N	\N
192	25E09189	上海东大金智信息系统有限公司	中国	\N	上海市杨浦区国泰路11号1705室	\N	integrator	inactive	2024-08-08 00:00:00	2025-05-09 06:43:59.858342	\N	f	14	\N	\N
194	25E09191	上海恒能电子科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-08-08 00:00:00	2025-05-09 06:43:59.867405	\N	f	14	\N	\N
489	25E18001	测试客户	CN	上海市	12312	real_estate	user	inactive	2025-05-18 02:32:09.934056	2025-05-18 02:32:09.934057		f	6	[]	t
139	25E09136	深圳市金证科技股份有限公司	中国	\N	深圳市南山区科技园高新区南区高新南五道金证科技大楼8-9楼	\N	integrator	active	2024-02-23 00:00:00	2025-05-09 06:43:11.281636	\N	f	17	\N	\N
147	25E09144	深圳市万睿智能科技有限公司	中国	\N	深圳市福田区梅林路63号梅林万科中心四层	\N	integrator	active	2024-02-23 00:00:00	2025-05-09 06:43:11.378936	\N	f	17	\N	\N
165	25E09162	中建三局智能技术有限公司	中国	\N	武汉东湖新技术开发区高新大道797号中建·光谷之星GC栋10层	\N	integrator	active	2024-07-06 16:09:45	2025-05-09 06:43:11.547443	\N	f	17	\N	\N
186	25E09183	上海奔逸智能科技有限公司	中国	\N	\N	\N	integrator	active	2024-12-28 00:00:00	2025-05-09 06:43:59.834354	\N	f	14	\N	\N
205	25E09202	上海凯通实业有限公司	中国	\N	杨浦区国霞路259号1号楼812室	\N	integrator	active	2024-03-12 00:00:00	2025-05-09 06:43:59.974061	\N	f	14	\N	\N
221	25E09218	上海万坤实业发展有限公司	中国	\N	\N	\N	integrator	active	2025-04-19 00:00:00	2025-05-30 14:14:10.465544	\N	f	14	\N	\N
215	25E09212	上海市安装工程集团有限公司-第九分公司	中国	\N	曲阳路930号	\N	integrator	active	2024-10-09 00:00:00	2025-05-09 06:44:00.086002	\N	f	14	\N	\N
490	25E18002	霍尼韦尔智能建筑与家居集团	CN	广东省	深圳市南山区东滨中路4078号永新汇1号楼17层	real_estate	integrator	active	2025-05-18 12:51:43.933673	2025-05-18 12:51:43.933674		f	17	[]	t
196	25E09193	上海华虹智联信息科技有限公司	中国	\N	上海市浦东新区锦绣东路2777	\N	integrator	inactive	2024-09-21 00:00:00	2025-05-09 06:43:59.875506	\N	f	14	\N	\N
197	25E09194	上海吉拓网络技术有限公司	中国	\N	\N	\N	integrator	inactive	2024-12-28 00:00:00	2025-05-09 06:43:59.879721	\N	f	14	\N	\N
198	25E09195	上海建工二建集团有限公司	中国	\N	\N	\N	integrator	inactive	2024-11-12 00:00:00	2025-05-09 06:43:59.943622	\N	f	14	\N	\N
199	25E09196	上海建工四建集团有限公司	中国	\N	\N	\N	integrator	inactive	2025-02-22 00:00:00	2025-05-09 06:43:59.947967	\N	f	14	\N	\N
200	25E09197	上海经意实业有限公司	中国	\N	金山区北随塘河路3号	\N	integrator	inactive	2024-05-05 00:00:00	2025-05-09 06:43:59.953731	\N	f	14	\N	\N
202	25E09199	上海景文同安机电消防工程有限公司	中国	\N	同普路339弄2号楼5楼	\N	integrator	inactive	2024-09-14 00:00:00	2025-05-09 06:43:59.961389	\N	f	14	\N	\N
203	25E09200	上海九谷科技发展有限公司	中国	\N	\N	\N	integrator	inactive	2024-05-05 00:00:00	2025-05-09 06:43:59.965613	\N	f	14	\N	\N
204	25E09201	上海久纽智能科技有限公司	中国	\N	徐汇区虹梅路街道古美路1528号	\N	integrator	inactive	2024-07-05 00:00:00	2025-05-09 06:43:59.969892	\N	f	14	\N	\N
206	25E09203	上海蓝极星智能科技有限公司	中国	\N	\N	\N	integrator	inactive	2025-02-22 00:00:00	2025-05-09 06:43:59.977743	\N	f	14	\N	\N
207	25E09204	上海临港景鸿安全防范科技发展有限公司	中国	\N	田林街道宜山路508号8B室	\N	integrator	inactive	2024-03-21 00:00:00	2025-05-09 06:44:00.038192	\N	f	14	\N	\N
209	25E09206	上海美控智慧建筑有限公司	中国	\N	上海市青浦区盈港东路88号	\N	integrator	inactive	2024-06-21 00:00:00	2025-05-09 06:44:00.046583	\N	f	14	\N	\N
210	25E09207	上海沐东机电设备有限公司	中国	\N	浦东大道555号B座31楼	\N	integrator	inactive	2024-03-12 00:00:00	2025-05-09 06:44:00.051844	\N	f	14	\N	\N
211	25E09208	上海秋煜电力工程有限公司	中国	\N	\N	\N	integrator	inactive	2024-07-05 00:00:00	2025-05-09 06:44:00.060654	\N	f	14	\N	\N
212	25E09209	上海申源电子工程技术设备有限公司	中国	\N	\N	\N	integrator	inactive	2025-01-09 00:00:00	2025-05-09 06:44:00.067476	\N	f	14	\N	\N
213	25E09210	上海世茂物联网科技有限公司	中国	\N	\N	\N	integrator	inactive	2025-03-01 00:00:00	2025-05-09 06:44:00.075801	\N	f	14	\N	\N
216	25E09213	上海市安装工程集团有限公司-第四分公司	中国	\N	\N	\N	integrator	inactive	2024-05-25 00:00:00	2025-05-09 06:44:00.091108	\N	f	14	\N	\N
218	25E09215	上海市建设工程机电设备有限公司	中国	\N	\N	\N	integrator	inactive	2025-01-07 00:00:00	2025-05-09 06:44:00.141285	\N	f	14	\N	\N
220	25E09217	上海数码通系统集成有限公司	中国	\N	\N	\N	integrator	inactive	2025-04-19 00:00:00	2025-05-09 06:44:00.150658	\N	f	14	\N	\N
222	25E09219	上海维瓴智能科技有限公司	中国	\N	秀浦路3188弄K8栋5楼（创研智造）	\N	integrator	inactive	2024-02-22 00:00:00	2025-05-09 06:44:00.15816	\N	f	14	\N	\N
224	25E09221	上海宵远信息技术有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-21 00:00:00	2025-05-09 06:44:00.165737	\N	f	14	\N	\N
225	25E09222	上海协利科技工程有限公司	中国	\N	张杨路707号23楼（生命人寿大厦）	\N	integrator	inactive	2024-02-22 00:00:00	2025-05-09 06:44:00.169375	\N	f	14	\N	\N
226	25E09223	上海壹杰信息技术有限公司	中国	\N	浦东南路2250号	\N	integrator	inactive	2024-03-12 00:00:00	2025-05-09 06:44:00.173354	\N	f	14	\N	\N
227	25E09224	上海仪电楼宇科技有限公司	中国	\N	田林路192号b1座	\N	integrator	inactive	2024-03-21 00:00:00	2025-05-09 06:44:00.177671	\N	f	14	\N	\N
228	25E09225	上海益邦智能技术股份有限公司	中国	\N	秀浦路2555号C1座11楼（漕河泾康桥园区）	\N	integrator	inactive	2024-02-22 00:00:00	2025-05-09 06:44:00.184113	\N	f	14	\N	\N
229	25E09226	上海银欣高新技术发展股份有限公司	中国	\N	江宁路428号二层	\N	integrator	inactive	2024-03-12 00:00:00	2025-05-09 06:44:00.242049	\N	f	14	\N	\N
230	25E09227	上海永通通信科技发展有限公司	中国	\N	上海市金山区朱泾镇金龙新村270号	\N	integrator	inactive	2024-06-18 00:00:00	2025-05-09 06:44:00.246727	\N	f	14	\N	\N
231	25E09228	上海圆信智能科技有限公司	中国	\N	\N	\N	integrator	inactive	2025-03-08 00:00:00	2025-05-09 06:44:00.251355	\N	f	14	\N	\N
232	25E09229	上海跃燕弱电工程有限公司	中国	\N	\N	\N	integrator	inactive	2025-04-14 00:00:00	2025-05-09 06:44:00.255765	\N	f	14	\N	\N
233	25E09230	上海云思智慧信息技术有限公司	中国	\N	桂平路391号A座33层（新漕河泾国际商务中心）	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:00.259759	\N	f	14	\N	\N
235	25E09232	上海正德天佑防火设备安装有限公司	中国	\N	\N	\N	integrator	inactive	2024-12-28 00:00:00	2025-05-09 06:44:00.267836	\N	f	14	\N	\N
236	25E09233	上海执讯智能科技有限公司	中国	\N	\N	\N	integrator	inactive	2025-02-26 00:00:00	2025-05-09 06:44:00.272159	\N	f	14	\N	\N
485	25E16002	都市创想（上海）城市更新建设有限公司   高道喜	CN	上海市	上海	real_estate	integrator	inactive	2025-05-16 03:32:27.82668	2025-05-16 03:32:27.826682		f	14	[]	t
239	25E09236	苏州工业园区汉威控制系统工程有限公司	中国	\N	\N	\N	integrator	inactive	2025-02-26 00:00:00	2025-05-09 06:44:00.28465	\N	f	14	\N	\N
241	25E09238	通号通信信息集团上海有限公司	中国	\N	\N	\N	integrator	inactive	2025-03-14 00:00:00	2025-05-09 06:44:00.347842	\N	f	14	\N	\N
460	25E09457	上海新源广场物业管理有限公司	中国	\N	上海市中山南路318号2号监控	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.513716	\N	f	2	\N	\N
298	25E09295	上海派汇网络科技有限公司	中国	\N	上海市奉贤区岚丰路1150号	\N	integrator	inactive	2024-10-19 15:25:55	2025-06-06 10:21:24.171091	\N	f	15	\N	\N
242	25E09239	同方泰德智能科技（上海）有限公司	中国	\N	\N	\N	integrator	inactive	2024-12-28 00:00:00	2025-05-09 06:44:00.352283	\N	f	14	\N	\N
245	25E09242	中国建筑第八工程局有限公司	中国	\N	\N	\N	integrator	inactive	2024-11-27 00:00:00	2025-05-09 06:44:00.365454	\N	f	14	\N	\N
247	25E09244	中铁四局集团有限公司	中国	\N	\N	\N	integrator	inactive	2024-12-28 00:00:00	2025-05-09 06:44:00.374217	\N	f	14	\N	\N
266	25E09263	奥乐科技有限公司	中国	\N	上海市上海市松江区临港卓越科技园	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.003468	\N	f	15	\N	\N
268	25E09265	北京真视通科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-09-15 15:26:01	2025-05-09 06:44:49.012612	\N	f	15	\N	\N
269	25E09266	常州电信工程有限公司	中国	\N	钟楼区泰西路64号	\N	integrator	inactive	2024-06-08 14:32:58	2025-05-09 06:44:49.016562	\N	f	15	\N	\N
273	25E09270	华维星电技术有限公司	中国	\N	\N	\N	integrator	inactive	2025-02-12 00:00:00	2025-05-09 06:44:49.036866	\N	f	15	\N	\N
274	25E09271	江苏达海智能系统股份有限公司	中国	\N	启帆路505号	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.043021	\N	f	15	\N	\N
275	25E09272	江苏华瑞克科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-11-02 16:35:02	2025-05-09 06:44:49.052118	\N	f	15	\N	\N
307	25E09304	上海仪电鑫森科技发展有限公司	中国	\N	上海市虹口区广纪路738号2幢226室	\N	integrator	active	2024-09-30 12:24:53	2025-05-09 06:44:49.283558	\N	f	15	\N	\N
276	25E09273	江苏金鼎智能系统工程有限公司	中国	\N	常州市天宁区青洋北路47号7号楼	\N	integrator	inactive	2024-10-11 14:08:52	2025-05-09 06:44:49.06176	\N	f	15	\N	\N
277	25E09274	江苏南通二建集团讯腾云创智能科技有限公司	中国	\N	启东市经济开发区林洋路500号	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.066192	\N	f	15	\N	\N
281	25E09278	上海谌亚智能化系统有限公司	中国	\N	\N	\N	integrator	inactive	2024-11-29 13:40:21	2025-05-09 06:44:49.085526	\N	f	15	\N	\N
283	25E09280	上海存在自动化控制设备有限公司	中国	\N	\N	\N	integrator	inactive	2024-12-21 11:49:15	2025-05-09 06:44:49.101503	\N	f	15	\N	\N
286	25E09283	上海东元信息科技发展有限公司	中国	\N	上海市肇嘉浜路366号6楼E座	\N	integrator	inactive	2024-02-22 00:00:00	2025-05-09 06:44:49.141461	\N	f	15	\N	\N
287	25E09284	上海梵华信息技术有限公司	中国	\N	上海复星中路369号大同商务大厦	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.14596	\N	f	15	\N	\N
289	25E09286	上海行余信息技术有限公司	中国	\N	上海市浦东新区牡丹路60号东辰大厦803室	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.158478	\N	f	15	\N	\N
290	25E09287	上海昊蕾信息技术有限公司	中国	\N	嘉定区嘉罗公路1661号45号楼2楼	\N	integrator	inactive	2024-02-22 12:49:43	2025-05-09 06:44:49.162632	\N	f	15	\N	\N
293	25E09290	上海奂源工程设备有限公司	中国	\N	上海市上海市虹口区武进大楼	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.175314	\N	f	15	\N	\N
294	25E09291	上海慧谷多高信息工程有限公司	中国	\N	上海市闵行区春东路508号2号楼309室	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.179147	\N	f	15	\N	\N
295	25E09292	上海金槐智能科技有限公司	中国	\N	上海市徐汇区田州路159号15单元1002室	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.182908	\N	f	15	\N	\N
296	25E09293	上海康悦信息技术有限公司	中国	\N	上海市上海市浦东新区孙桥中心绿地	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.186825	\N	f	15	\N	\N
297	25E09294	上海灵一建筑配套工程有限公司	中国	\N	上海市静安区西康路770号（53）	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.190519	\N	f	15	\N	\N
299	25E09296	上海擎天电子科技有限公司	中国	\N	上海市浦东新区东方路1217号A座6楼	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.249217	\N	f	15	\N	\N
301	25E09298	上海书柏智能科技有限公司	中国	\N	上海市普陀区怒江北路449弄8号C5幢4幢	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.257621	\N	f	15	\N	\N
302	25E09299	上海双桥信息有限公司	中国	\N	\N	\N	integrator	inactive	2025-04-07 00:00:00	2025-05-09 06:44:49.262057	\N	f	15	\N	\N
303	25E09300	上海天跃科技股份有限公司	中国	\N	浦东新区金海路1000号金领之都50号楼	\N	integrator	inactive	2024-03-22 12:06:17.999	2025-05-09 06:44:49.2664	\N	f	15	\N	\N
306	25E09303	上海信业智能科技股份有限公司	中国	\N	上海市浦东新区张江集电港·科技领袖之都19幢	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.279427	\N	f	15	\N	\N
308	25E09305	上海亦强智能科技有限公司	中国	\N	上海市上海市闵行区浦江智汇园	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.287574	\N	f	15	\N	\N
309	25E09306	上海永天科技股份有限公司	中国	\N	上海市青浦区徐乐路208号虹泾总部C栋	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.339263	\N	f	15	\N	\N
310	25E09307	上海源和智能科技股份有限公司	中国	\N	上海市浦东新区启帆路505号	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.344266	\N	f	15	\N	\N
311	25E09308	上海云赛智联信息科技有限公司	中国	\N	上海市徐汇区宜州路180号B6幢6层	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.348878	\N	f	15	\N	\N
312	25E09309	上海众频网络系统工程有限公司	中国	\N	\N	\N	integrator	inactive	2025-01-07 10:22:50	2025-05-09 06:44:49.354084	\N	f	15	\N	\N
314	25E09311	同方股份有限公司-上海光大会展分公司	中国	\N	徐汇区漕宝路66号光大会展中心29层	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.362418	\N	f	15	\N	\N
317	25E09314	浙大网新系统工程有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-15 15:49:29	2025-05-09 06:44:49.374749	\N	f	15	\N	\N
318	25E09315	浙江东冠信息技术有限公司	中国	\N	浙江省杭州市滨江区长河街道江南大道588号恒鑫大厦主楼8层802室	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.378726	\N	f	15	\N	\N
320	25E09317	浙江建工设备安装有限公司	中国	\N	杭州市拱墅区杭州新天地商务中心5幢13层	\N	integrator	inactive	2024-03-16 14:46:20	2025-05-09 06:44:49.386658	\N	f	15	\N	\N
325	25E09322	浙江微风智能科技有限公司	中国	\N	萧山区建设一路中栋国际银座1幢1207室	\N	integrator	inactive	2024-02-22 12:42:16	2025-05-09 06:44:49.45765	\N	f	15	\N	\N
327	25E09324	中达电通股份有限公司	中国	\N	上海市浦东新区民夏路238号	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.466364	\N	f	15	\N	\N
328	25E09325	中电科数字技术股份有限公司	中国	\N	浦东新区白莲泾路127号中电科信息科技大厦16层	\N	integrator	inactive	2024-02-21 14:45:19	2025-05-09 06:44:49.471361	\N	f	15	\N	\N
329	25E09326	中国电信股份有限公司上海宝山电信局	中国	\N	上海市宝山区牡丹江路1325号406室	\N	integrator	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.476801	\N	f	15	\N	\N
330	25E09327	中建电子工程有限公司-上海分公司	中国	\N	杨树路1062号滨江国际广场2号楼1001室	\N	integrator	inactive	2024-09-19 11:02:22.999	2025-05-09 06:44:49.48228	\N	f	15	\N	\N
8	25E09005	北京博易基业工程顾问有限公司	中国	\N	\N	\N	designer	active	2025-03-01 00:00:00	2025-05-09 06:42:32.499292	\N	f	16	\N	\N
339	25E09336	北京中加集成智能系统工程有限公司	中国	\N	北京西城区外大街271号	\N	integrator	active	2024-12-28 16:43:35	2025-05-09 06:45:19.412133	\N	f	13	\N	\N
331	25E09328	安徽数安桥数据科技有限公司	中国	\N	成都	\N	integrator	inactive	2025-03-14 00:00:00	2025-05-09 06:45:19.37704	\N	f	13	\N	\N
335	25E09332	北京京航安机场工程有限公司	中国	\N	北京市平谷区林荫北街13号信息大厦1002-39室	\N	integrator	inactive	2024-02-20 00:00:00	2025-05-09 06:45:19.395277	\N	f	13	\N	\N
348	25E09345	湖南安众智能科技有限公司	中国	\N	长沙市雨花区人民路9号	\N	integrator	inactive	2024-03-14 18:29:21	2025-05-09 06:45:19.476456	\N	f	13	\N	\N
349	25E09346	湖南悟意信息技术有限公司	中国	\N	长沙雨花区香丽名苑3栋	\N	integrator	inactive	2024-09-11 15:20:13	2025-05-09 06:45:19.481141	\N	f	13	\N	\N
354	25E09351	吉林市天达伟业科贸有限公司	中国	\N	吉林南京街181号	\N	integrator	inactive	2024-06-13 16:32:54	2025-05-09 06:45:19.56277	\N	f	13	\N	\N
355	25E09352	江苏中业信息科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-02-21 15:41:15	2025-05-09 06:45:19.567758	\N	f	13	\N	\N
390	25E09387	四川中科航建信息技术有限公司	中国	\N	武侯区天益街38号理想中心2-701室	\N	integrator	active	2024-11-16 11:54:10	2025-05-09 06:45:19.899798	\N	f	13	\N	\N
356	25E09353	杰创智能科技股份有限公司	中国	\N	广州黄浦区瑞详路88号	\N	integrator	inactive	2024-02-22 21:07:35	2025-05-09 06:45:19.572984	\N	f	13	\N	\N
357	25E09354	金盛投资发展有限公司	中国	\N	\N	\N	integrator	inactive	2024-05-24 21:56:02	2025-05-09 06:45:19.579187	\N	f	13	\N	\N
360	25E09357	南京禄口国际机场空港科技有限公司6	中国	\N	南京禄口国际机场翔鹰二路9号2号办公楼2楼	\N	integrator	inactive	2025-04-11 00:00:00	2025-05-09 06:45:19.647953	\N	f	13	\N	\N
364	25E09361	润建股份有限公司	中国	\N	\N	\N	integrator	inactive	2024-02-27 19:41:07	2025-05-09 06:45:19.709985	\N	f	13	\N	\N
367	25E09364	上海博望电子科技有限公司	中国	\N	上海杨浦区逸仙路205号1915室	\N	integrator	inactive	2024-02-21 14:40:31	2025-05-09 06:45:19.747906	\N	f	13	\N	\N
368	25E09365	上海华携实业发展有限公司	中国	\N	上海市金山区张堰镇松金公路2758号10幢A1217室	\N	integrator	inactive	2024-02-20 00:00:00	2025-05-09 06:45:19.758813	\N	f	13	\N	\N
372	25E09369	上海竞拓数码信息技术有限公司	中国	\N	上海浦东	\N	integrator	inactive	2025-03-14 00:00:00	2025-05-09 06:45:19.791788	\N	f	13	\N	\N
377	25E09374	上海市安装工程集团的限公司	中国	\N	上海曲阳路930号	\N	integrator	inactive	2025-03-12 00:00:00	2025-05-09 06:45:19.815681	\N	f	13	\N	\N
382	25E09379	深圳达实智能股份有限公司成都分公司	中国	\N	成都	\N	integrator	inactive	2025-04-22 00:00:00	2025-05-09 06:45:19.861814	\N	f	13	\N	\N
385	25E09382	四川倍智数能信息工程有限公司	中国	\N	成都天华一路99号	\N	integrator	inactive	2024-10-20 15:25:25	2025-05-09 06:45:19.875524	\N	f	13	\N	\N
387	25E09384	四川三创联和信息技术服务有限公司	中国	\N	成都高新区天府大道中段530号1栋19楼1903	\N	integrator	inactive	2024-09-17 10:37:45	2025-05-09 06:45:19.88589	\N	f	13	\N	\N
389	25E09386	四川天启智源科技有限公司	中国	\N	成都	\N	integrator	inactive	2024-07-15 09:57:31	2025-05-09 06:45:19.895243	\N	f	13	\N	\N
392	25E09389	苏中达科智能工程有限公司西安分公司	中国	\N	西安	\N	integrator	inactive	2025-04-06 00:00:00	2025-05-09 06:45:19.946502	\N	f	13	\N	\N
393	25E09390	苏州商普智能科技有限公司	中国	\N	江苏昆山g-a发区中冶累庭4号楼	\N	integrator	inactive	2024-06-22 12:27:55	2025-05-09 06:45:19.951692	\N	f	13	\N	\N
394	25E09391	太通建设有限公司	中国	\N	北京市城庙城299号	\N	integrator	inactive	2024-04-24 08:53:40	2025-05-09 06:45:19.955623	\N	f	13	\N	\N
398	25E09395	武汉意丰科技有限公司	中国	\N	武汉洪山区文化大道555号	\N	integrator	inactive	2024-09-28 10:31:24	2025-05-09 06:45:19.972485	\N	f	13	\N	\N
400	25E09397	西安悦泰科技有限责任公司	中国	\N	西安南三环	\N	integrator	inactive	2024-02-21 13:45:29	2025-05-09 06:45:19.980754	\N	f	13	\N	\N
409	25E09406	中国移动通信集团陕西有限公司西安分公司	中国	\N	\N	\N	integrator	inactive	2024-02-21 10:15:37	2025-05-09 06:45:20.072659	\N	f	13	\N	\N
413	25E09410	中建四局智控与数字科技事业部	中国	\N	深圳	\N	integrator	inactive	2024-09-10 13:24:35	2025-05-09 06:45:20.096839	\N	f	13	\N	\N
414	25E09411	中科院成都信息技术有限公司	中国	\N	成都	\N	integrator	inactive	2024-10-20 22:08:32	2025-05-09 06:45:20.101022	\N	f	13	\N	\N
432	25E09429	江苏启安建设集团有限公司	中国	\N	汇龙镇人民中路683号	\N	integrator	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.305693	\N	f	2	\N	\N
433	25E09430	江苏中铭慧业科技有限公司	中国	\N	无锡市新吴区锡钦路26号   	\N	integrator	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.311203	\N	f	2	\N	\N
438	25E09435	上海赤通冷链物流有限公司	中国	\N	上海市闵行区通海路333号127幢401室	\N	integrator	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.33875	\N	f	2	\N	\N
441	25E09438	上海固晓消防设备有限公司	中国	\N	上海市青浦区徐泾镇华徐公路91号1层A区184号	\N	integrator	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.356964	\N	f	2	\N	\N
446	25E09443	上海麦摩通信技术有限公司	中国	\N	上海市杨浦区平凉路1090号天科国际大厦713室	\N	integrator	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.399921	\N	f	2	\N	\N
456	25E09453	上海塑鼎机电工程有限公司	中国	\N	上海市浦东新区盛夏路169号\r\nA 栋413室	\N	integrator	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.48292	\N	f	2	\N	\N
457	25E09454	上海先景电子科技有限公司	中国	\N	\N	\N	integrator	inactive	2025-03-06 00:00:00	2025-05-09 06:48:02.496792	\N	f	2	\N	\N
458	25E09455	上海祥明仪表机箱有限公司	中国	\N	上海市宝山区罗泾镇陈川路1051号 	\N	integrator	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.502847	\N	f	2	\N	\N
459	25E09456	上海享暨实业有限公司	中国	\N	上海市松江区泗泾镇沪松公路2511弄86号五金城商务楼437	\N	integrator	inactive	2025-02-21 00:00:00	2025-05-09 06:48:02.507858	\N	f	2	\N	\N
358	25E09355	民航成都电子技术有限责任公司	中国	\N	四川省新津工业园区新材料产业功能区新材28路南侧	\N	integrator	active	2024-02-21 11:55:49	2025-05-09 06:45:19.584079	\N	f	13	\N	\N
462	25E09459	上海赢安实业有限公司	中国	\N	\N	\N	integrator	inactive	2025-03-06 00:00:00	2025-05-09 06:48:02.544726	\N	f	2	\N	\N
464	25E09461	上海置根智能电子技术有限公司	中国	\N	上海市嘉定区封周路655号14幢201室J2272	\N	integrator	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.554638	\N	f	2	\N	\N
466	25E09463	上海逐日机电工程有限公司	中国	\N	\N	\N	integrator	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.564181	\N	f	2	\N	\N
365	25E09362	山西云时代技术有限公司	中国	\N	太原	\N	integrator	active	2025-03-05 00:00:00	2025-05-09 06:45:19.724746	\N	f	13	\N	\N
410	25E09407	中国中钢股份有限公司	中国	\N	北京市海淀区海淀大街8号	\N	integrator	active	2025-01-19 09:42:38	2025-05-09 06:45:20.078538	\N	f	13	\N	\N
20	25E09017	东南大学建筑设计研究院	中国	\N	东南大学四牌楼校区	\N	designer	active	2024-03-02 13:06:48	2025-05-09 06:42:32.556665	\N	f	16	\N	\N
129	25E09126	上海瀚网智能科技有限公司	中国	\N	上海市宝山区长江南路668号A1380室	\N	dealer	active	2024-09-14 16:27:03	2025-05-21 06:47:22.954008	\N	f	17	[14]	f
39	25E09036	科进柏城咨询有限公司上海分公司	中国	\N	上海市长宁区新华路643号	\N	designer	inactive	2024-03-24 00:00:00	2025-05-09 06:42:32.745324	\N	f	16	\N	\N
45	25E09042	南京市建筑设计研究院有限责任公司	中国	\N	南京市秦淮区运粮河西路9号	\N	designer	inactive	2024-05-10 09:21:50	2025-05-09 06:42:32.858968	\N	f	16	\N	\N
49	25E09046	南京长安规划设计有限公司	中国	\N	\N	\N	designer	inactive	2024-12-22 19:00:26	2025-05-09 06:42:32.87358	\N	f	16	\N	\N
58	25E09055	上海天华建筑设计有限公司	中国	\N	\N	\N	designer	inactive	2024-06-30 10:54:18	2025-05-09 06:42:32.98396	\N	f	16	\N	\N
59	25E09056	上海邮电设计咨询研究院有限公司	中国	\N	上海市杨浦区国康路38号3号楼	\N	designer	inactive	2024-02-27 00:00:00	2025-05-09 06:42:32.987413	\N	f	16	\N	\N
62	25E09059	苏交科集团股份有限公司南京设计中心	中国	\N	江苏省南京市建邺区富春江东街8号	\N	designer	inactive	2024-03-01 00:00:00	2025-05-09 06:42:32.999134	\N	f	16	\N	\N
77	25E09074	中国船舶重工集团国际工程有限公司	中国	\N	北京市朝阳区双桥中路北院1号	\N	designer	inactive	2024-12-08 19:46:34	2025-05-09 06:42:33.159572	\N	f	16	\N	\N
78	25E09075	中国建筑设计研究院有限公司	中国	\N	\N	\N	designer	inactive	2024-06-30 10:50:35.999	2025-05-09 06:42:33.164088	\N	f	16	\N	\N
79	25E09076	中国江苏国际经济技术合作集团有限公司建筑设计院	中国	\N	南京市鼓楼区虎踞北路181号方源国际酒店18F	\N	designer	inactive	2024-03-02 00:00:00	2025-05-09 06:42:33.168677	\N	f	16	\N	\N
89	25E09086	中通服咨询设计研究院有限公司	中国	\N	江苏省南京市建邺区楠溪江东街58号	\N	designer	inactive	2024-03-02 00:00:00	2025-05-09 06:42:33.26516	\N	f	16	\N	\N
92	25E09089	中元国际工程设计研究院有限公司	中国	\N	北京市西三环北路5号	\N	designer	inactive	2024-03-02 00:00:00	2025-05-09 06:42:33.27796	\N	f	16	\N	\N
95	25E09092	奥意建筑工程设计有限公司	中国	\N	深圳市福田区华发北路30号	\N	designer	inactive	2024-02-23 00:00:00	2025-05-09 06:43:10.961192	\N	f	17	\N	\N
100	25E09097	广东南方电信规划咨询设计院有限公司 	中国	\N	深圳市福田区福田保税区凤凰路万利工业大厦2期东座5、6楼	\N	designer	inactive	2024-08-19 11:04:34.999	2025-05-09 06:43:10.982195	\N	f	17	\N	\N
101	25E09098	广东省电信规划设计院有限公司	中国	\N	广州市天河区中山大道华景路1号11-19层	\N	designer	inactive	2025-03-09 00:00:00	2025-05-09 06:43:10.985853	\N	f	17	\N	\N
103	25E09100	广东省建筑设计研究院有限公司	中国	\N	广州市荔湾区流花路９７号	\N	designer	inactive	2024-05-01 16:20:59	2025-05-09 06:43:10.995413	\N	f	17	\N	\N
104	25E09101	广东省建筑设计研究院有限公司第三机电所	中国	\N	越秀区解放北路863号盘福大厦11楼	\N	designer	inactive	2025-03-08 00:00:00	2025-05-09 06:43:10.999133	\N	f	17	\N	\N
117	25E09114	华东建筑设计研究院有限公司深圳分公司	中国	\N	深圳市南山区粤海街道深大社区深南大道9819号地铁金融科技大厦16F	\N	designer	inactive	2024-12-21 13:01:03	2025-05-09 06:43:11.083842	\N	f	17	\N	\N
118	25E09115	华南理工大学建筑设计研究院	中国	\N	广州市天河区华南理工大学	\N	designer	inactive	2024-02-23 00:00:00	2025-05-09 06:43:11.087641	\N	f	17	\N	\N
120	25E09117	机械工业部深圳设计研究院有限公司	中国	\N	深圳市福田区同德路8号	\N	designer	inactive	2024-03-04 00:00:00	2025-05-09 06:43:11.146582	\N	f	17	\N	\N
123	25E09120	麦驰设计研究院	中国	\N	南山区留仙大道南山智园崇文园区1号楼23楼	\N	designer	inactive	2024-09-07 14:20:36	2025-05-09 06:43:11.160478	\N	f	17	\N	\N
130	25E09127	深圳大学建筑设计研究院有限公司	中国	\N	深圳市南山区深圳大学校内	\N	designer	inactive	2024-02-23 00:00:00	2025-05-09 06:43:11.239425	\N	f	17	\N	\N
131	25E09128	深圳华森建筑与工程设计顾问有限公司	中国	\N	深圳市南山区滨海之窗花园八栋办公楼第六层	\N	designer	inactive	2025-04-26 00:00:00	2025-05-09 06:43:11.246706	\N	f	17	\N	\N
153	25E09150	深圳壹创国际设计股份有限公司	中国	\N	深圳市南山区华侨城东部工业区东北B-1栋202（二楼东侧）	\N	designer	inactive	2024-02-23 00:00:00	2025-05-09 06:43:11.441572	\N	f	17	\N	\N
159	25E09156	万安智能设计研究院	中国	\N	深圳市南山区粤海五道三航大厦808	\N	designer	inactive	2024-07-20 14:46:30	2025-05-09 06:43:11.470486	\N	f	17	\N	\N
161	25E09158	悉地国际设计顾问（深圳）有限公司	中国	\N	深圳市南山区粤海街道麻岭社区科技中二路19号劲嘉科技大厦201	\N	designer	inactive	2025-03-21 00:00:00	2025-05-09 06:43:11.480394	\N	f	17	\N	\N
172	25E09169	奥雅纳工程咨询(上海)有限公司	中国	\N	\N	\N	designer	inactive	2025-02-26 00:00:00	2025-05-09 06:43:59.681979	\N	f	14	\N	\N
180	25E09177	铠延机电设计(上海)有限公司	中国	\N	共和新路5000弄6号楼910室	\N	designer	inactive	2024-02-22 00:00:00	2025-05-09 06:43:59.79857	\N	f	14	\N	\N
182	25E09179	启迪设计集团股份有限公司	中国	\N	\N	\N	designer	inactive	2024-06-21 00:00:00	2025-05-09 06:43:59.813951	\N	f	14	\N	\N
201	25E09198	上海菁峰设计咨询有限公司	中国	\N	灵石路1477号209	\N	designer	inactive	2024-05-05 00:00:00	2025-05-09 06:43:59.957727	\N	f	14	\N	\N
214	25E09211	上海世源科技工程有限公司	中国	\N	\N	\N	designer	inactive	2025-02-17 00:00:00	2025-05-09 06:44:00.08197	\N	f	14	\N	\N
217	25E09214	上海市城市建设设计研究总院(集团)有限公司	中国	\N	\N	\N	designer	inactive	2025-04-26 00:00:00	2025-05-09 06:44:00.095212	\N	f	14	\N	\N
219	25E09216	上海市政工程设计研究总院（集团）有限公司	中国	\N	国康路8号	\N	designer	inactive	2024-02-27 00:00:00	2025-05-09 06:44:00.145634	\N	f	14	\N	\N
237	25E09234	沈麦韦(上海)商务咨询有限公司	中国	\N	中山西路1055号904室（SOHO中山广场）	\N	designer	inactive	2024-03-21 00:00:00	2025-05-09 06:44:00.276224	\N	f	14	\N	\N
244	25E09241	信息产业电子第十一设计研究院科技工程\r\n股份有限公司-上海分公司	中国	\N	宜山路810号2-4F楼（贝岭大厦）	\N	designer	inactive	2024-09-20 00:00:00	2025-05-09 06:44:00.361077	\N	f	14	\N	\N
248	25E09245	卓展工程顾问(北京)有限公司-上海分公司	中国	\N	宜山路508号19层（景鸿大楼）	\N	designer	inactive	2024-02-27 00:00:00	2025-05-09 06:44:00.377979	\N	f	14	\N	\N
265	25E09262	AECOM（上海）	中国	\N	上海市杨浦区政立路500号创智天地企业中心7号楼9-12层	\N	designer	inactive	2024-02-21 00:00:00	2025-05-09 06:44:48.996302	\N	f	15	\N	\N
54	25E09051	清华大学建筑设计研究院有限公司	中国	\N	\N	\N	designer	active	2025-04-26 00:00:00	2025-05-09 06:42:32.964259	\N	f	16	\N	\N
50	25E09047	南京长江都市建筑设计院	中国	\N	南京市秦淮区卡子门大街19号	\N	designer	active	2024-03-01 18:44:17	2025-05-09 06:42:32.876923	\N	f	16	\N	\N
223	25E09220	上海现代建筑设计研究院有限公司	中国	\N	\N	\N	designer	active	2024-11-27 00:00:00	2025-05-09 06:44:00.161808	\N	f	14	\N	\N
93	25E09090	AECOM（深圳）	中国	\N	广东省深圳市南山区蛇口街道南海大道1052号海翔广场9层	\N	designer	active	2025-03-01 00:00:00	2025-05-09 06:43:10.952813	\N	f	17	\N	\N
171	25E09168	筑博设计集团股份有限公司	中国	\N	广东省深圳市福田区泰然六路52号2-5-6楼	\N	designer	active	2024-11-09 15:43:02	2025-05-09 06:43:11.57245	\N	f	17	\N	\N
243	25E09240	同济大学建筑设计研究院（集团）有限公司	中国	\N	上海市杨浦区四平路街道四平路1230号	\N	designer	inactive	2024-06-18 00:00:00	2025-05-09 06:44:00.356884	\N	f	14	\N	\N
25	25E09022	华泰证券股份有限公司	中国	\N	\N	\N	user	active	2025-02-21 00:00:00	2025-05-09 06:42:32.574298	\N	f	16	\N	\N
267	25E09264	北京信诚百年工程技术有限公司上海分公司	中国	\N	上海市黄浦区河南南路16号809室	\N	designer	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.008529	\N	f	15	\N	\N
270	25E09267	德利思工程咨询	中国	\N	上海市长宁区中山西路1051号靠近中山广场B座	\N	designer	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.020528	\N	f	15	\N	\N
272	25E09269	华建集团EPC总承包部	中国	\N	闵行区龙吴路888号	\N	designer	inactive	2024-02-22 12:36:10	2025-05-09 06:44:49.029391	\N	f	15	\N	\N
278	25E09275	迈进工程设计咨询(上海)有限公司	中国	\N	上海市徐汇区龙漕路299号天华信息科技园区3A幢6楼	\N	designer	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.070895	\N	f	15	\N	\N
285	25E09282	上海德恳设计咨询顾问有限公司	中国	\N	上海市上海市长宁区延安西路726-728号	\N	designer	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.117403	\N	f	15	\N	\N
304	25E09301	上海文讯电子有限公司	中国	\N	\N	\N	designer	inactive	2025-04-12 00:00:00	2025-05-09 06:44:49.270849	\N	f	15	\N	\N
313	25E09310	思迈建筑咨询(上海)有限公司	中国	\N	上海市静安区恒丰路436号环智国际大厦2701室	\N	designer	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.358239	\N	f	15	\N	\N
315	25E09312	悉地国际设计顾问(深圳)有限公司上海分公司	中国	\N	上海市杨浦国权北路1688弄78号湾谷科技园A4栋8层公司	\N	designer	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.366577	\N	f	15	\N	\N
322	25E09319	浙江美阳国际工程设计有限公司	中国	\N	\N	\N	designer	inactive	2025-03-29 00:00:00	2025-05-09 06:44:49.443023	\N	f	15	\N	\N
324	25E09321	浙江天正设计工程有限公司	中国	\N	西湖区吉园街郡原公园里7楼	\N	designer	inactive	2025-03-14 00:00:00	2025-05-09 06:44:49.453045	\N	f	15	\N	\N
333	25E09330	巴马丹拿建筑设计咨询(上海)有限公司	中国	\N	上海市长宁区遵义路100号虹桥南丰城B座31楼	\N	designer	inactive	2024-02-22 00:00:00	2025-05-09 06:45:19.38692	\N	f	13	\N	\N
334	25E09331	北京建筑设计研究院成都分院	中国	\N	成都	\N	designer	inactive	2025-03-01 00:00:00	2025-05-09 06:45:19.391179	\N	f	13	\N	\N
337	25E09334	北京沃利帕森工程技术有限公司上海分公司	中国	\N	上海闵行	\N	designer	inactive	2025-03-29 00:00:00	2025-05-09 06:45:19.40349	\N	f	13	\N	\N
338	25E09335	北京中电电子工程咨询公司	中国	\N	北京市海淀区万寿路27号院内	\N	designer	inactive	2024-02-20 00:00:00	2025-05-09 06:45:19.407712	\N	f	13	\N	\N
342	25E09339	广州省建筑设计研究院	中国	\N	广州越秀	\N	designer	inactive	2025-03-07 00:00:00	2025-05-09 06:45:19.444059	\N	f	13	\N	\N
351	25E09348	华东建筑设计研究院有限公司重庆西南中心	中国	\N	市渝中区华盛路10号14层1#	\N	designer	inactive	2024-02-22 00:00:00	2025-05-09 06:45:19.545745	\N	f	13	\N	\N
361	25E09358	青岛青咨工程咨询有限公司	中国	\N	青岛	\N	designer	inactive	2024-04-14 09:36:21	2025-05-09 06:45:19.670223	\N	f	13	\N	\N
369	25E09366	上海慧腾信息科技有限公司	中国	\N	普陀区同普路1175弄14号309室	\N	designer	inactive	2024-11-02 09:51:44.999	2025-05-09 06:45:19.769387	\N	f	13	\N	\N
376	25E09373	上海申通地铁集团有限公司	中国	\N	上海衡山路12号	\N	designer	inactive	2024-02-22 21:15:22	2025-05-09 06:45:19.811526	\N	f	13	\N	\N
378	25E09375	上海天华建筑设计有限公司武汉公分公司	中国	\N	\N	\N	designer	inactive	2024-03-01 11:24:07	2025-05-09 06:45:19.841871	\N	f	13	\N	\N
379	25E09376	上海延华智能科技（集团）股份有限公司	中国	\N	上海市西康路1255号普陀科技大厦6楼	\N	designer	inactive	2024-03-01 13:07:06	2025-05-09 06:45:19.847898	\N	f	13	\N	\N
90	25E09087	中芯京城集成电路制造(北京)有限公司	中国	\N	\N	\N	user	inactive	2024-07-19 08:25:50	2025-05-09 06:42:33.269416	\N	f	16	\N	\N
94	25E09091	TCL建设管理（深圳）有限公司	中国	\N	深圳市前海深港合作区南山街道临海大道59号海运中心口岸楼3楼310号-J336	\N	user	inactive	2025-04-12 00:00:00	2025-05-09 06:43:10.957207	\N	f	17	\N	\N
107	25E09104	广州鼎信科技有限公司	中国	\N	广州市黄埔区科丰路33号20栋333房	\N	user	inactive	2025-04-26 00:00:00	2025-05-09 06:43:11.04351	\N	f	17	\N	\N
169	25E09166	珠海华发实业股份有限公司	中国	\N	南山区铜鼓路5号	\N	user	inactive	2024-09-21 14:15:24	2025-05-09 06:43:11.563853	\N	f	17	\N	\N
175	25E09172	沪东造船厂	中国	\N	\N	\N	user	inactive	2024-11-01 00:00:00	2025-05-09 06:43:59.750798	\N	f	14	\N	\N
176	25E09173	华润置地	中国	\N	\N	\N	user	inactive	2025-04-26 00:00:00	2025-05-09 06:43:59.763128	\N	f	14	\N	\N
181	25E09178	默林娱乐集团	中国	\N	金山区成毛路2123号10区	\N	user	inactive	2024-05-05 00:00:00	2025-05-09 06:43:59.806834	\N	f	14	\N	\N
193	25E09190	上海福瑞科技有限公司	中国	\N	\N	\N	user	inactive	2024-12-28 00:00:00	2025-05-09 06:43:59.86327	\N	f	14	\N	\N
195	25E09192	上海华虹(集团)有限公司 	中国	\N	\N	\N	user	inactive	2025-02-17 00:00:00	2025-05-09 06:43:59.87137	\N	f	14	\N	\N
208	25E09205	上海龙旗科技股份有限公司	中国	\N	\N	\N	user	inactive	2025-03-14 00:00:00	2025-05-09 06:44:00.042562	\N	f	14	\N	\N
234	25E09231	上海张江国信安地产有限公司	中国	\N	张东路1387号16幢E楼301室	\N	user	inactive	2024-02-21 00:00:00	2025-05-09 06:44:00.26364	\N	f	14	\N	\N
488	25E16004	苏州沸点科技有限公司	CN	江苏省	中国（江苏）自由贸易试验区苏州片区苏州工业园区金鸡湖大道88号人工智能产业园C1-901	other	integrator	inactive	2025-05-16 06:48:25.430608	2025-05-16 06:48:25.430611		f	16	[]	t
238	25E09235	舜宇奥来微纳光学（上海）有限公司	中国	\N	\N	\N	user	inactive	2025-02-26 00:00:00	2025-05-09 06:44:00.280875	\N	f	14	\N	\N
240	25E09237	天合光能股份有限公司	中国	\N	\N	\N	user	inactive	2024-12-28 00:00:00	2025-05-09 06:44:00.342338	\N	f	14	\N	\N
380	25E09377	上海远菁工程项目管理有限公司	中国	\N	上海宝山区逸仙路2816号	\N	designer	active	2025-01-04 09:45:02	2025-05-09 06:45:19.85246	\N	f	13	\N	\N
323	25E09320	浙江省建筑设计院	中国	\N	杭州市滨江区江虹路人工智能产业园A幢23楼	\N	designer	active	2024-04-08 10:00:47	2025-05-09 06:44:49.448006	\N	f	15	\N	\N
359	25E09356	民航机场成都电子工程设计有限责任公司	中国	\N	成都市二环路南二癹17号	\N	designer	active	2024-02-21 12:04:43.999	2025-06-03 18:57:58.44024	\N	f	13	\N	\N
423	25E09420	\t上海久事国际体育中心有限公司	CN	上海市	伊宁路2000号	\N	user	active	2025-02-21 00:00:00	2025-05-14 07:58:18.647873	None	f	2	\N	\N
350	25E09347	华东建筑设计研究院有限公司	中国	\N	黄浦区世博滨江大道北座	\N	designer	active	2024-12-28 17:33:26	2025-05-30 14:20:20.913846	\N	f	13	\N	\N
461	25E09458	上海扬子饭店有限公司	中国	\N	黄浦区汉口路740号	\N	user	active	2025-02-25 00:00:00	2025-06-10 13:44:38.175221	\N	f	2	\N	\N
420	25E09417	\t\r\n上海市黄浦区人民政府外滩街道办事处	中国	\N	上海市黄浦区外滩街道山西南路350号物资大厦1301室 	\N	user	active	2025-02-25 00:00:00	2025-06-10 13:46:19.443519	\N	f	2	\N	\N
470	25E09467	中芯国际集成电路制造（深圳）有限公司	CN	广东省	广东省深圳市坪山新区出口加工区高芯路18号	manufacturing	user	active	2025-02-22 00:00:00	2025-06-12 13:58:10.958858	None	f	2	\N	\N
463	25E09460	上海毓恺工程技术有限公司	中国	\N	上海市金山区卫昌路293号2幢7172室	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.549805	\N	f	2	\N	\N
465	25E09462	上海竹园物业管理有限公司	中国	\N	杨高南路388号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.559313	\N	f	2	\N	\N
469	25E09466	豫园街道办事处	中国	\N	大境路56号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.578104	\N	f	2	\N	\N
7	25E09004	北京佰沃信通科技有限公司	中国	\N	\N	\N	dealer	inactive	2025-04-26 00:00:00	2025-05-09 06:42:32.494509	\N	f	16	\N	\N
9	25E09006	北京国隆信达通信技术有限公司	中国	\N	\N	\N	dealer	inactive	2024-12-29 08:54:35.999	2025-05-09 06:42:32.503846	\N	f	16	\N	\N
11	25E09008	北京联航迅达通信技术有限公司	中国	\N	北京市怀柔区迎宾中路36号2层22632室	\N	dealer	inactive	2024-11-10 10:15:05	2025-05-09 06:42:32.513029	\N	f	16	\N	\N
21	25E09018	敦力(南京)科技有限公司	中国	\N	南京市江北新区长芦街道利民路11号E幢315室	\N	dealer	inactive	2024-12-22 19:46:59	2025-05-09 06:42:32.560304	\N	f	16	\N	\N
491	25E19001	杭州合义信息技术有限公司	CN	浙江省	杭州西湖区	other	dealer	inactive	2025-05-19 01:15:34.057894	2025-05-19 01:15:34.057896		f	15	[]	t
6	25E09003	北京安维创时科技有限公司	中国	\N	\N	\N	integrator	inactive	2025-04-26 00:00:00	2025-05-09 06:42:32.489187	\N	f	16	\N	\N
492	25E20001	四川锦辰瑞建设工程有限公司	CN	四川省	成都	real_estate	integrator	inactive	2025-05-20 06:07:25.646941	2025-05-20 06:07:25.646942		f	13	[]	t
493	25E20002	嘉兴贝斯特电子技术有限公司	CN	浙江省	平湖市虹霞路135号	other	integrator	inactive	2025-05-20 06:53:09.40349	2025-05-20 06:53:09.403492		f	15	[]	t
84	25E09081	中建八局-华北分公司	中国	\N	\N	\N	integrator	inactive	2024-11-10 10:11:30	2025-05-09 06:42:33.245726	\N	f	16	\N	\N
494	25E23001	上海浦东建设股份有限公司	CN	上海市	上海	real_estate	user	inactive	2025-05-23 03:06:07.307113	2025-05-23 03:06:07.307114		f	14	[]	t
384	25E09381	深圳市麦驰物联股份有限公司上海分公司	中国	\N	上海浦发广场E座	\N	designer	inactive	2024-10-31 11:43:53	2025-05-09 06:45:19.870997	\N	f	13	\N	\N
386	25E09383	四川三创联和技术服务有限公司	中国	\N	四川成都天府大道中段530号	\N	designer	inactive	2024-03-18 16:08:26	2025-05-09 06:45:19.880296	\N	f	13	\N	\N
388	25E09385	四川省建筑设计研究院有限公司	中国	\N	成都	\N	designer	inactive	2024-10-20 21:49:53	2025-05-09 06:45:19.890248	\N	f	13	\N	\N
404	25E09401	长沙市规划设计院有限责任公司	中国	\N	长沙芙蓉区	\N	designer	inactive	2024-03-10 00:00:00	2025-05-09 06:45:20.043246	\N	f	13	\N	\N
406	25E09403	中国航空规划设计院	中国	\N	\N	\N	designer	inactive	2024-03-10 15:36:33	2025-05-09 06:45:20.054424	\N	f	13	\N	\N
407	25E09404	中国建筑西南设计研究院有限公司	中国	\N	成都市花圃北路14号	\N	designer	inactive	2024-02-22 00:00:00	2025-05-09 06:45:20.060564	\N	f	13	\N	\N
408	25E09405	中国移动设计院云南分公司	中国	\N	昆明	\N	designer	inactive	2025-04-20 00:00:00	2025-05-09 06:45:20.066463	\N	f	13	\N	\N
411	25E09408	中国中铁二院	中国	\N	成都	\N	designer	inactive	2025-03-01 00:00:00	2025-05-09 06:45:20.087806	\N	f	13	\N	\N
412	25E09409	中国中元国际工程有限公司	中国	\N	北京海淀区西三环北路5号	\N	designer	inactive	2024-03-18 13:41:37.999	2025-05-09 06:45:20.092541	\N	f	13	\N	\N
471	25E11001	中国电子系统工程第二建设有限公司	CN	上海市	上海闵行	manufacturing	designer	inactive	2025-05-11 14:19:29.286687	2025-05-11 14:19:29.286689		f	13	\N	\N
401	25E09398	信息产业电子第十一设计院科技工程股份有限公司	中国	\N	成都市成华区双林路251号	\N	designer	active	2024-02-21 14:45:40.999	2025-05-09 06:45:19.9848	\N	f	13	\N	\N
495	25E23002	浙江洲之宇建设有限公司	CN	浙江省	浙江省杭州市拱墅区沈半路279、281号（杭州星河灯饰市场A馆507-11号）	real_estate	integrator	inactive	2025-05-23 10:33:52.343663	2025-05-23 10:33:52.343665		f	17	[]	t
255	25E09252	上海咸力环境设备有限公司	中国	\N	浦东金海路1000号31栋401	\N	user	inactive	2025-04-19 00:00:00	2025-05-09 06:44:24.00556	\N	f	7	\N	\N
257	25E09254	上海星外滩开发建设有限公司	中国	\N	\N	\N	user	inactive	2025-02-28 00:00:00	2025-05-09 06:44:24.013327	\N	f	7	\N	\N
258	25E09255	上海振华重工(集团)股份有限公司	中国	\N	浦东南路3470号	\N	user	inactive	2025-02-14 00:00:00	2025-05-09 06:44:24.017248	\N	f	7	\N	\N
261	25E09258	英伟达半导体科技（上海）有限公司(公司)	中国	\N	\N	\N	user	inactive	2025-03-01 00:00:00	2025-05-09 06:44:24.041147	\N	f	7	\N	\N
262	25E09259	长飞先进半导体（武汉）有限公司	中国	\N	\N	\N	user	inactive	2025-02-28 00:00:00	2025-05-09 06:44:24.044828	\N	f	7	\N	\N
263	25E09260	上海瑞明置业有限公司	中国	\N	\N	\N	user	inactive	2025-02-28 00:00:00	2025-05-09 06:44:24.049367	\N	f	7	\N	\N
280	25E09277	厦门士兰集科微电子有限公司	中国	\N	\N	\N	user	inactive	2025-03-01 00:00:00	2025-05-09 06:44:49.080987	\N	f	15	\N	\N
467	25E09464	银行间市场清算所股份有限公司	中国	\N	黄浦区中山南路318号33-34层	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.568793	\N	f	2	\N	\N
468	25E09465	永安百货有限公司	中国	\N	上海市南京东路635号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.573309	\N	f	2	\N	\N
292	25E09289	上海华美达酒店	中国	\N	上海市黄浦区蒙自路靠近歌斐中心	\N	user	inactive	2024-02-21 00:00:00	2025-05-09 06:44:49.170873	\N	f	15	\N	\N
316	25E09313	招商蛇口	中国	\N	\N	\N	user	inactive	2025-03-29 00:00:00	2025-05-09 06:44:49.370732	\N	f	15	\N	\N
321	25E09318	浙江交通投资集团有限公司	中国	\N	上城区五星路199号	\N	user	inactive	2025-03-14 00:00:00	2025-05-09 06:44:49.392201	\N	f	15	\N	\N
326	25E09323	浙江银泰投资有限公司	中国	\N	\N	\N	user	inactive	2025-03-01 00:00:00	2025-05-09 06:44:49.461833	\N	f	15	\N	\N
332	25E09329	安徽长飞先进半导体有限公司	中国	\N	芜湖市利民东路82号	\N	user	inactive	2024-02-21 15:02:50.999	2025-05-09 06:45:19.382514	\N	f	13	\N	\N
344	25E09341	广州粤芯半导体技术有限公司	中国	\N	广州市萝岗知识城	\N	user	inactive	2024-02-20 00:00:00	2025-05-09 06:45:19.45462	\N	f	13	\N	\N
345	25E09342	国电四川发电有限公司	中国	\N	成都	\N	user	inactive	2025-04-23 00:00:00	2025-05-09 06:45:19.460776	\N	f	13	\N	\N
353	25E09350	华虹半导体(无锡)有限公司	中国	\N	无锡市新吴区新洲路28号	\N	user	inactive	2024-02-20 00:00:00	2025-05-09 06:45:19.556684	\N	f	13	\N	\N
370	25E09367	上海机场(集团)有限公司	中国	\N	上海浦东	\N	user	inactive	2025-03-22 00:00:00	2025-05-09 06:45:19.781028	\N	f	13	\N	\N
481	25E14010	上海北外滩来福士广场	CN	上海市	上海市虹口区东大名路999号	\N	user	inactive	2025-05-14 02:48:26.161412	2025-05-14 02:48:26.161414		f	20	\N	\N
483	25E15001	上海市徐家汇人民政府	CN	上海市	上海市徐汇区南丹路78号	government	user	inactive	2025-05-15 02:38:18.047884	2025-05-15 02:38:18.047886		f	20	\N	\N
256	25E09253	上海新国际博览中心有限公司	中国	\N	\N	\N	user	inactive	2025-02-28 00:00:00	2025-05-19 00:56:20.625271	\N	f	7	[2, 20]	f
373	25E09370	上海临港经济发展（集团）有限公司	中国	\N	上海临港	\N	user	inactive	2025-03-19 00:00:00	2025-05-09 06:45:19.797618	\N	f	13	\N	\N
383	25E09380	深圳华大基因股份有限公司	中国	\N	盐田区洪安三街21号华大综合园7栋7层-14层	\N	user	inactive	2024-02-20 00:00:00	2025-05-09 06:45:19.86622	\N	f	13	\N	\N
396	25E09393	天津中海地产有限公司	中国	\N	河东区海河东路518号	\N	user	inactive	2024-02-22 00:00:00	2025-05-09 06:45:19.963889	\N	f	13	\N	\N
397	25E09394	武汉新芯集成电路制造有限公司	中国	\N	武汉市东湖开发区高新四路18号	\N	user	inactive	2024-02-20 00:00:00	2025-05-09 06:45:19.968106	\N	f	13	\N	\N
402	25E09399	英威达尼龙化工（中国）有限公司	中国	\N	上海金山天华路88号	\N	user	inactive	2024-03-18 14:25:37	2025-05-09 06:45:19.989017	\N	f	13	\N	\N
403	25E09400	长江存储科技有限责任公司	中国	\N	武汉市东湖开发区关东科技工业园华光大道18号7018室	\N	user	inactive	2024-02-20 00:00:00	2025-05-09 06:45:20.038183	\N	f	13	\N	\N
405	25E09402	中国海螺创业控股有限公司	中国	\N	嘉定区天祝路海螺总部大楼	\N	user	inactive	2024-02-21 15:14:01	2025-05-09 06:45:20.048542	\N	f	13	\N	\N
415	25E09412	中芯国际集成电路制造（绍兴）有限公司	中国	\N	稠州路	\N	user	inactive	2024-02-20 00:00:00	2025-05-09 06:45:20.149335	\N	f	13	\N	\N
418	25E09415	\t\r\n上海观复博物馆	中国	\N	银城中路501号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.147915	\N	f	2	\N	\N
419	25E09416	\t\r\n上海市黄浦区人民政府南京东路街道办事处	中国	\N	上海市黄浦区宁波路595号南京东路街道综治中心	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.153915	\N	f	2	\N	\N
421	25E09418	\t\r\n上海市长宁区新泾镇人民政府	中国	\N	泉口路68号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.163695	\N	f	2	\N	\N
422	25E09419	\t\r\n中芯国际集成电路制造(上海)有限公司	中国	\N	中国（上海）自由贸易试验区张江路18号	\N	user	inactive	2025-04-24 00:00:00	2025-05-09 06:48:02.168184	\N	f	2	\N	\N
425	25E09422	艾仕得涂料系统(上海)有限公司	中国	\N	上海市嘉定区胜辛北路3199号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.190359	\N	f	2	\N	\N
426	25E09423	北京世邦魏理仕物业管理服务有限公司上海分公司	中国	\N	上海市杨浦区眉州路381号404-2室	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.205033	\N	f	2	\N	\N
427	25E09424	北京搜厚物业管理有限公司上海第六分公司	中国	\N	中山东二路58号A栋303 	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.244349	\N	f	2	\N	\N
428	25E09425	打浦桥街道办事处	中国	\N	上海市黄浦区斜土路191号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.253238	\N	f	2	\N	\N
429	25E09426	广州科思创聚合物有限公司	中国	\N	广州经济技术开发区永和经济区斗塘路10号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.280892	\N	f	2	\N	\N
430	25E09427	国家税务总局上海市黄浦区税务局	中国	\N	黄浦区斜土路313号609	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.28888	\N	f	2	\N	\N
431	25E09428	黄浦区消防救援支队	中国	\N	白渡路66号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.299462	\N	f	2	\N	\N
434	25E09431	交通银行股份有限公司上海市分行	中国	\N	江西中路200号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.316406	\N	f	2	\N	\N
352	25E09349	华虹半导体（上海）有限公司	中国	\N	上海市浦东新区康桥	\N	user	active	2024-07-18 15:23:27	2025-05-09 06:45:19.551217	\N	f	13	\N	\N
346	25E09343	合肥新桥国际机场有限公司	中国	\N	\N	\N	user	active	2024-02-21 13:48:02	2025-05-09 06:45:19.466677	\N	f	13	\N	\N
260	25E09257	上海中心大厦世邦魏理仕物业管理有限公司	中国	\N	陆家嘴环路479号	\N	user	active	2025-02-14 00:00:00	2025-06-10 14:03:53.49315	\N	f	7	\N	\N
479	25E14008	上海银行张江数据处理中心	CN	上海市	上海市浦东新区华东路锦绣东路	\N	user	active	2025-05-14 02:37:06.359685	2025-06-05 09:37:22.526191		f	20	\N	\N
475	25E14004	汇添富基金大楼	CN	上海市	上海市黄浦区外马路728号	\N	user	active	2025-05-14 01:57:34.347268	2025-06-12 16:19:08.916793		f	20	\N	\N
477	25E14006	上海海昌海洋世界	CN	上海市	上海市浦东新区银飞路166号	\N	user	active	2025-05-14 02:11:57.225825	2025-06-10 23:29:14.918113		f	20	\N	\N
436	25E09433	上海百联百货经营有限公司上海时装商店	中国	\N	南京东路660号－690号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.327302	\N	f	2	\N	\N
437	25E09434	上海城市规划展示馆	中国	\N	黄浦区人民大道100号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.332942	\N	f	2	\N	\N
439	25E09436	上海凡枫实业有限公司	中国	\N	河南中路555号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.344667	\N	f	2	\N	\N
440	25E09437	上海港机重工有限公司	中国	\N	浦东新区东方路3261号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.350653	\N	f	2	\N	\N
442	25E09439	上海国际赛车场经营发展有限公司	中国	\N	\N	\N	user	inactive	2025-04-24 00:00:00	2025-05-09 06:48:02.362057	\N	f	2	\N	\N
448	25E09445	上海市黄浦区人民政府半淞园路街道办事处	中国	\N	西藏南路1427号司法所	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.418419	\N	f	2	\N	\N
449	25E09446	上海市黄浦区人民政府淮海中路街道办事处	中国	\N	上海市黄浦区淡水路91弄8号前门	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.424678	\N	f	2	\N	\N
450	25E09447	上海市黄浦区人民政府老西门街道办事处	中国	\N	 乔家栅47号	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.446375	\N	f	2	\N	\N
451	25E09448	上海市黄浦区人民政府瑞金二路街道办事处	中国	\N	上海市黄浦区人民政府瑞金二路街道办事处	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.453278	\N	f	2	\N	\N
452	25E09449	上海市黄浦区人民政府五里桥街道办事处	中国	\N	黄浦区瞿溪路758号1号楼204	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.461295	\N	f	2	\N	\N
455	25E09452	上海澍予设备安装工程有限公司	中国	\N	上海市金山区卫昌路293号2幢11313室	\N	user	inactive	2025-02-25 00:00:00	2025-05-09 06:48:02.477198	\N	f	2	\N	\N
22	25E09019	国隆信达通信技术有限公司	中国	\N	\N	\N	dealer	inactive	2024-12-29 09:25:07	2025-05-09 06:42:32.563768	\N	f	16	\N	\N
47	25E09044	南京网联通信技术有限公司	中国	\N	南京市骐谷产业园B座5F	\N	dealer	inactive	2024-03-01 13:37:02	2025-05-09 06:42:32.866693	\N	f	16	\N	\N
63	25E09060	苏州邦耀电子科技有限公司	中国	\N	\N	\N	dealer	inactive	2024-12-02 09:19:08	2025-05-09 06:42:33.039973	\N	f	16	\N	\N
66	25E09063	苏州中瀚通信科技有限公司	中国	\N	苏州工业园区星湖花园36商幢105室	\N	dealer	inactive	2024-03-02 13:15:38	2025-05-09 06:42:33.051037	\N	f	16	\N	\N
70	25E09067	天津比信科技股份有限公司	中国	\N	\N	\N	dealer	inactive	2024-12-22 20:03:50	2025-05-09 06:42:33.069836	\N	f	16	\N	\N
73	25E09070	无锡达人电子科技有限公司	中国	\N	无锡市锡惠里小区8号	\N	dealer	inactive	2024-03-02 13:04:22	2025-05-09 06:42:33.139317	\N	f	16	\N	\N
76	25E09073	中策大数据咨询(深圳)有限公司	中国	\N	\N	\N	dealer	inactive	2025-03-08 00:00:00	2025-05-09 06:42:33.155421	\N	f	16	\N	\N
109	25E09106	广州洪昇智能科技有限公司	中国	\N	广州市天河区大观中路95号1栋311房	\N	dealer	inactive	2024-12-10 16:25:00	2025-05-09 06:43:11.05149	\N	f	17	\N	\N
105	25E09102	广东同博信息科技有限公司	中国	\N	广州市天河区高普路1039号201-29室	\N	\N	inactive	2025-01-11 17:27:43	2025-05-09 06:43:11.003146	\N	f	17	\N	\N
143	25E09140	深圳市深嘉创达科技有限公司	中国	\N	宝安区鼎新工业园2楼	\N	dealer	inactive	2024-11-20 15:27:13.999	2025-05-09 06:43:11.356048	\N	f	17	\N	\N
163	25E09160	浙江德方智能科技有限公司	中国	\N	拱墅区丰谭路508号7号楼16层	\N	dealer	inactive	2024-02-21 00:00:00	2025-05-09 06:43:11.487677	\N	f	17	\N	\N
168	25E09165	中冶交通建设集团有限公司	中国	\N	北京海淀区高粱桥斜街11号院3号楼	\N	dealer	inactive	2024-08-24 15:41:57	2025-05-09 06:43:11.559926	\N	f	17	\N	\N
174	25E09171	海康威视数字技术(上海)有限公司	中国	\N	\N	\N	dealer	inactive	2025-03-14 00:00:00	2025-05-09 06:43:59.725692	\N	f	14	\N	\N
183	25E09180	上海艾亿智能科技有限公司	中国	\N	\N	\N	dealer	inactive	2024-06-21 00:00:00	2025-05-09 06:43:59.821551	\N	f	14	\N	\N
187	25E09184	上海常森电子有限公司	中国	\N	静安区天目西路547号	\N	dealer	inactive	2024-05-05 00:00:00	2025-05-09 06:43:59.838441	\N	f	14	\N	\N
282	25E09279	上海淳泊信息科技有限公司	中国	\N	上海市宝山区长江西路1180号4楼402-197	\N	dealer	inactive	2024-02-21 15:18:06	2025-05-09 06:44:49.093567	\N	f	15	\N	\N
284	25E09281	上海大展通信电子设备有限公司	中国	\N	\N	\N	dealer	inactive	2024-11-05 15:05:10	2025-05-09 06:44:49.106154	\N	f	15	\N	\N
291	25E09288	上海弘谊工程科技有限公司	中国	\N	上海市宝山区长江南路180号A437	\N	dealer	inactive	2024-11-05 09:56:15	2025-05-09 06:44:49.166486	\N	f	15	\N	\N
300	25E09297	上海瑞康通信科技有限公司	中国	\N	上海市嘉定区双单路86弄海上荟商办4号楼4层	\N	dealer	inactive	2024-02-21 15:18:26	2025-05-09 06:44:49.253313	\N	f	15	\N	\N
305	25E09302	上海鑫桉信息工程有限公司	中国	\N	上海市黄浦区南京西路77号	\N	dealer	inactive	2024-02-22 13:04:45	2025-05-09 06:44:49.275154	\N	f	15	\N	\N
319	25E09316	浙江航博智能工程有限公司	中国	\N	浙江省杭州经济技术开发区宝龙商业中心29幢1510室	\N	dealer	inactive	2024-04-13 17:54:53	2025-05-09 06:44:49.382788	\N	f	15	\N	\N
336	25E09333	北京朗易通科技有限公司	中国	\N	北京海淀区交大东路66号	\N	dealer	inactive	2024-09-28 14:13:27	2025-05-09 06:45:19.399385	\N	f	13	\N	\N
340	25E09337	成都市天皓科技有限公司	中国	\N	成都金牛区一环路北三段100号	\N	dealer	inactive	2024-09-28 10:54:37	2025-05-09 06:45:19.416929	\N	f	13	\N	\N
341	25E09338	福淳智能科技(四川)有限公司	中国	\N	成都高新区新程大道78号	\N	dealer	inactive	2024-02-21 14:50:19	2025-05-09 06:45:19.438533	\N	f	13	\N	\N
347	25E09344	合肥兴和通讯设备有限公司	中国	\N	安徽合肥包河区巢湖南路89号	\N	dealer	inactive	2024-12-28 17:00:48.999	2025-05-09 06:45:19.471566	\N	f	13	\N	\N
362	25E09359	青岛智联慧通电子科技有限公司	中国	\N	青岛瑞海北路11号	\N	dealer	inactive	2024-04-14 09:35:59	2025-05-09 06:45:19.685314	\N	f	13	\N	\N
363	25E09360	青岛中亿海电子科技有限公司	中国	\N	青岛漳州二路9号	\N	dealer	inactive	2024-09-30 13:39:46	2025-05-09 06:45:19.701488	\N	f	13	\N	\N
366	25E09363	陕西无线电通信服务中心	中国	\N	西安新城国际大厦A1103	\N	dealer	inactive	2024-04-24 08:38:43.999	2025-05-09 06:45:19.73922	\N	f	13	\N	\N
374	25E09371	上海霹迪梯通讯科技有限公司	中国	\N	上海曹杨汇融大厦1107	\N	dealer	inactive	2025-02-22 00:00:00	2025-05-09 06:45:19.803429	\N	f	13	\N	\N
445	25E09442	上海集成电路研发中心有限公司	中国	\N	上海市浦东新区高斯路497号	\N	user	active	2025-02-21 00:00:00	2025-05-09 06:48:02.387769	\N	f	2	\N	\N
343	25E09340	广州希耐特船舶科技有限公司	CN	None	广州	transport	integrator	active	2025-03-07 00:00:00	2025-05-09 06:45:19.44875	None	f	13	\N	\N
454	25E09451	上海市机关事务管理局	中国	\N	大沽路100号	\N	user	active	2025-02-21 00:00:00	2025-06-09 11:33:59.225774	\N	f	2	\N	\N
288	25E09285	上海福玛通信信息科技有限公司	中国	\N	上海市浦东新区秀浦路800弄35号901室	\N	dealer	active	2024-02-21 15:18:40	2025-06-09 15:06:16.3435	\N	f	15	\N	\N
453	25E09450	上海市黄浦区人民政府小东门街道办事处	中国	\N	上海市黄浦区东街48号	\N	user	active	2025-02-25 00:00:00	2025-06-10 13:45:32.456568	\N	f	2	\N	\N
443	25E09440	上海和平饭店有限公司	中国	\N	上海市南京东路20号	\N	user	active	2025-02-25 00:00:00	2025-06-10 13:47:00.563965	\N	f	2	\N	\N
30	25E09027	江苏瀚远科技股份有限公司	中国	\N	\N	\N	integrator	active	2025-03-23 00:00:00	2025-05-09 06:42:32.645806	\N	f	16	\N	\N
44	25E09041	南京聚立科技股份有限公司	中国	\N	\N	\N	integrator	active	2024-09-22 16:22:09	2025-05-09 06:42:32.854952	\N	f	16	\N	\N
10	25E09007	北京航天星桥科技股份有限公司	中国	\N	\N	\N	integrator	active	2024-09-22 16:25:15	2025-05-09 06:42:32.50816	\N	f	16	\N	\N
12	25E09009	北京瑞华赢科技发展股份有限公司	中国	\N	\N	\N	integrator	active	2025-02-22 00:00:00	2025-05-09 06:42:32.517314	\N	f	16	\N	\N
399	25E09396	西安瑞林达通信技术有限公司	中国	\N	西安市灞桥区高科绿水东城四期	\N	dealer	active	2024-09-28 15:52:05	2025-05-09 06:45:19.976746	\N	f	13	\N	\N
40	25E09037	朗高科技有限公司	中国	\N	南京市建邺区白龙江东街19号舜禹大厦11F	\N	integrator	active	2024-03-24 14:39:45	2025-05-09 06:42:32.751154	\N	f	16	\N	\N
375	25E09372	上海瑞测通信科技有限公司	中国	\N	上海普陀	\N	dealer	inactive	2025-04-23 00:00:00	2025-05-09 06:45:19.807495	\N	f	13	\N	\N
391	25E09388	四川中资世纪科技有限公司	中国	\N	成都市成华区成华大道二段298号	\N	dealer	inactive	2024-08-02 10:58:49	2025-05-09 06:45:19.941987	\N	f	13	\N	\N
395	25E09392	天津比信科技有限公司	中国	\N	金航大厦1-1-102室	\N	dealer	inactive	2024-09-28 15:54:58	2025-05-09 06:45:19.959643	\N	f	13	\N	\N
416	25E09413	重庆大鹏鸟科技有限公司	中国	\N	重庆渝中区临江路19号	\N	dealer	inactive	2024-12-31 15:27:02.999	2025-05-09 06:45:20.156901	\N	f	13	\N	\N
417	25E09414	重庆君知鹏科技有限公司	中国	\N	重庆市南岸区海棠溪街道交院大道66号	\N	dealer	inactive	2024-03-09 14:26:45.999	2025-05-09 06:45:20.162393	\N	f	13	\N	\N
424	25E09421	\t上海瑞康通信科技有限公司	中国	\N	上海嘉定	\N	dealer	inactive	2025-04-17 00:00:00	2025-05-09 06:48:02.181146	\N	f	2	\N	\N
5	25E09002	安徽亿诺网络科技有限公司	中国	\N	安徽省阜阳市颍州区金悦大厦A座1003	\N	integrator	inactive	2024-03-02 00:00:00	2025-05-09 06:42:32.484746	\N	f	16	\N	\N
13	25E09010	北京时代凌宇科技股份有限公司	中国	\N	北京市朝阳区容创路17号时代凌宇大厦8层	\N	integrator	inactive	2024-03-02 00:00:00	2025-05-09 06:42:32.52122	\N	f	16	\N	\N
14	25E09011	北京市设备安装工程集团有限公司	中国	\N	北京市西城区南礼士路15号	\N	integrator	inactive	2024-06-20 17:44:17	2025-05-09 06:42:32.524897	\N	f	16	\N	\N
15	25E09012	北京泰豪智能工程有限公司	中国	\N	北京市大兴区运城街2号泰豪智能大厦	\N	integrator	inactive	2024-03-02 00:00:00	2025-05-09 06:42:32.528466	\N	f	16	\N	\N
16	25E09013	北京自动化-自动化设备有限公司	中国	\N	\N	\N	integrator	inactive	2024-07-20 15:04:48	2025-05-09 06:42:32.54116	\N	f	16	\N	\N
17	25E09014	博宇融通（北京）电气设备有限公司	中国	\N	北京市朝阳区望京北路9号9幢八层D818	\N	integrator	inactive	2024-03-30 13:48:48	2025-05-09 06:42:32.54523	\N	f	16	\N	\N
19	25E09016	东莞市海悦电脑科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:16:13.999	2025-05-09 06:42:32.552849	\N	f	16	\N	\N
23	25E09020	杭州创业慧康股份有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:55:16	2025-05-09 06:42:32.567181	\N	f	16	\N	\N
26	25E09023	吉林省济远建设有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 10:58:00	2025-05-09 06:42:32.577769	\N	f	16	\N	\N
27	25E09024	吉林省宇川建筑工程有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:01:30	2025-05-09 06:42:32.582863	\N	f	16	\N	\N
28	25E09025	江苏艾迪生电子科技有限公司	中国	\N	南京雨花区凤华路18号阿尔法楼B201室	\N	integrator	inactive	2024-04-04 00:00:00	2025-05-09 06:42:32.586576	\N	f	16	\N	\N
29	25E09026	江苏东大金智信息系统有限公司	中国	\N	江宁区将军大道100号靠近金智科技园A幢3F	\N	integrator	inactive	2024-12-02 09:06:44.999	2025-05-09 06:42:32.640801	\N	f	16	\N	\N
31	25E09028	江苏航天大为科技股份有限公司	中国	\N	锡山经济开发区科技股份有限公司	\N	integrator	inactive	2024-03-02 00:00:00	2025-05-09 06:42:32.650225	\N	f	16	\N	\N
32	25E09029	江苏晶旭旸信息系统技术有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:12:41	2025-05-09 06:42:32.654735	\N	f	16	\N	\N
33	25E09030	江苏普尊科技开发有限公司	中国	\N	\N	\N	integrator	inactive	2024-05-25 21:41:40	2025-05-09 06:42:32.661614	\N	f	16	\N	\N
484	25E16001	上海博电诺恒数码科技有限公司	CN	上海市	上海	real_estate	integrator	inactive	2025-05-16 02:36:11.062777	2025-05-16 02:36:11.06278		f	14	[]	t
35	25E09032	江苏苏美达成套设备工程有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:30:27	2025-05-09 06:42:32.670739	\N	f	16	\N	\N
37	25E09034	江苏智威信息工程有限公司	中国	\N	\N	\N	integrator	inactive	2024-08-10 16:47:40.999	2025-05-09 06:42:32.682379	\N	f	16	\N	\N
38	25E09035	江苏中科智能系统有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:35:08	2025-05-09 06:42:32.739043	\N	f	16	\N	\N
41	25E09038	南京东大智能化系统有限公司	中国	\N	\N	\N	integrator	inactive	2024-10-25 10:37:13	2025-05-09 06:42:32.842488	\N	f	16	\N	\N
42	25E09039	南京赫尔斯科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:19:06	2025-05-09 06:42:32.847249	\N	f	16	\N	\N
43	25E09040	南京赫耳斯科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-11-01 11:27:55	2025-05-09 06:42:32.851155	\N	f	16	\N	\N
46	25E09043	南京思宜德电子科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:33:04	2025-05-09 06:42:32.863167	\N	f	16	\N	\N
48	25E09045	南京熊猫信息产业有限公司	中国	\N	\N	\N	integrator	inactive	2025-02-26 00:00:00	2025-05-09 06:42:32.870476	\N	f	16	\N	\N
51	25E09048	南京中建安装集团	中国	\N	\N	\N	integrator	inactive	2024-09-29 11:26:08	2025-05-09 06:42:32.880246	\N	f	16	\N	\N
52	25E09049	南通盛云电子科技有限公司	中国	\N	\N	\N	integrator	inactive	2024-06-30 11:17:35	2025-05-09 06:42:32.942913	\N	f	16	\N	\N
53	25E09050	青岛九渊通自动化工程有限公司	中国	\N	山东省青岛市高新区泰鸿路67号1号楼302	\N	integrator	inactive	2024-05-10 09:46:16	2025-05-09 06:42:32.954033	\N	f	16	\N	\N
\.


--
-- TOC entry 4011 (class 0 OID 18225)
-- Dependencies: 236
-- Data for Name: contacts; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.contacts (id, company_id, name, department, "position", phone, email, is_primary, created_at, updated_at, notes, owner_id, override_share, shared_disabled) FROM stdin;
1	15	邹卫明					f	2024-03-02 00:00:00	2025-05-09 07:01:13.882516	\N	16	\N	\N
2	50	邹万流		电气主任工程师			f	2024-03-01 00:00:00	2025-05-09 07:01:13.951779	\N	16	\N	\N
3	62	周新华	设计部门	主任设计工程师			f	2024-03-01 00:00:00	2025-05-09 07:01:13.960121	\N	16	\N	\N
4	50	周贤静		弱电工程师			f	2024-03-01 00:00:00	2025-05-09 07:01:13.968121	\N	16	\N	\N
5	44	周丽丽	招标采购部	总监			f	2024-09-14 15:59:12	2025-05-09 07:01:13.978276	\N	16	\N	\N
6	31	周健	工程部	项目经理			f	2024-03-02 00:00:00	2025-05-09 07:01:13.985655	\N	16	\N	\N
7	92	赵习习					f	2024-03-02 00:00:00	2025-05-09 07:01:13.992846	\N	16	\N	\N
8	60	赵娟娟	采购部门	部门经理			f	2025-02-22 00:00:00	2025-05-09 07:01:13.999166	\N	16	\N	\N
9	15	赵婧婧		采购副总			f	2024-03-02 00:00:00	2025-05-09 07:01:14.007795	\N	16	\N	\N
10	89	赵婧	设计部门	弱电工程师			f	2025-02-22 00:00:00	2025-05-09 07:01:14.013809	\N	16	\N	\N
11	9	张志刚	业务部门	部门经理			f	2024-12-29 08:54:35.999	2025-05-09 07:01:14.020694	\N	16	\N	\N
12	83	张越	技术部	技术工程师			f	2024-12-02 08:47:31	2025-05-09 07:01:14.038165	\N	16	\N	\N
13	67	张元东	采购部门	普通员工			f	2024-03-02 00:00:00	2025-05-09 07:01:14.041676	\N	16	\N	\N
14	89	张艳	通信规划设计院	总监			f	2025-03-15 00:00:00	2025-05-09 07:01:14.045062	\N	16	\N	\N
15	50	张延洲	智能所	总工			f	2024-03-01 00:00:00	2025-05-09 07:01:14.056897	\N	16	\N	\N
16	15	张亚丽		销售			f	2024-03-02 00:00:00	2025-05-09 07:01:14.066826	\N	16	\N	\N
17	39	张新		四组行政组长			f	2024-03-24 00:00:00	2025-05-09 07:01:14.070165	\N	16	\N	\N
18	39	张青		主任工程师			f	2024-03-24 00:00:00	2025-05-09 07:01:14.073412	\N	16	\N	\N
19	20	臧胜					f	2024-03-02 00:00:00	2025-05-09 07:01:14.077388	\N	16	\N	\N
20	30	姚强	工程部	工程技术总监			f	2025-04-20 00:00:00	2025-05-09 07:01:14.080671	\N	16	\N	\N
21	75	徐盛斌	业务部门	市场总监			f	2024-12-08 19:32:10	2025-05-09 07:01:14.083838	\N	16	\N	\N
22	44	徐湖滨	技术部	总监			f	2024-09-22 16:22:09	2025-05-09 07:01:14.091249	\N	16	\N	\N
23	29	徐彬	采购部门	部门主管			f	2024-04-12 00:00:00	2025-05-09 07:01:14.094559	\N	16	\N	\N
24	40	吴晓磊	设计部门	部门经理			f	2024-03-24 00:00:00	2025-05-09 07:01:14.099842	\N	16	\N	\N
25	165	吴会从	工程部	项目负责人			f	2025-03-01 00:00:00	2025-05-09 07:01:14.145549	\N	16	\N	\N
26	40	翁怀琴	业务部门	市场总监			f	2024-03-24 00:00:00	2025-05-09 07:01:14.154378	\N	16	\N	\N
27	29	王永军	政企事业部	政企事业部			f	2024-04-12 00:00:00	2025-05-09 07:01:14.159063	\N	16	\N	\N
28	69	王颖	采购部门	部门经理			f	2025-02-08 00:00:00	2025-05-09 07:01:14.166852	\N	16	\N	\N
29	63	王秀凤	总经理办	总经理			f	2024-12-02 09:18:54	2025-05-09 07:01:14.174076	\N	16	\N	\N
30	51	王笑	技术部	技术工程师			f	2024-09-29 11:26:08	2025-05-09 07:01:14.177442	\N	16	\N	\N
31	80	王少武	业务部门	部门经理			f	2024-12-29 09:05:42	2025-05-09 07:01:14.185112	\N	16	\N	\N
32	67	王莉娜	采购部门	采购经理			f	2024-03-02 00:00:00	2025-05-09 07:01:14.203955	\N	16	\N	\N
33	43	王经理	业务部门	部门经理			f	2024-11-01 11:27:55	2025-05-09 07:01:14.209039	\N	16	\N	\N
34	39	王宏铭		二组行政组长			f	2024-03-24 00:00:00	2025-05-09 07:01:14.247964	\N	16	\N	\N
35	73	王光凯					f	2024-03-02 00:00:00	2025-05-09 07:01:14.262077	\N	16	\N	\N
36	5	王迪					f	2024-03-02 00:00:00	2025-05-09 07:01:14.269726	\N	16	\N	\N
37	40	王崇营	工程部	项目经理			f	2024-03-24 00:00:00	2025-05-09 07:01:14.277269	\N	16	\N	\N
38	11	王超	总经理办	总经理			f	2024-11-10 10:15:05	2025-05-09 07:01:14.281871	\N	16	\N	\N
39	41	汪俊秀	技术部	技术工程师			f	2024-10-24 12:25:07	2025-05-09 07:01:14.288637	\N	16	\N	\N
40	8	田亚欧	设计部门	弱电工程师			f	2025-03-01 00:00:00	2025-05-09 07:01:14.296166	\N	16	\N	\N
41	89	田恺	设计部门	区域总监			f	2024-03-02 00:00:00	2025-05-09 07:01:14.303388	\N	16	\N	\N
42	28	唐金鑫		副总经理			f	2024-04-04 00:00:00	2025-05-09 07:01:14.310919	\N	16	\N	\N
43	4	唐宝军	业务部门	智能化负责人			f	2024-03-02 00:00:00	2025-05-09 07:01:14.317813	\N	16	\N	\N
44	30	孙振强	总经理办	副总经理			f	2025-03-23 00:00:00	2025-05-09 07:01:14.32394	\N	16	\N	\N
45	15	孙鹏飞		项目经理			f	2024-03-02 00:00:00	2025-05-09 07:01:14.338701	\N	16	\N	\N
46	66	孙建中			0512-67089757		f	2024-03-02 00:00:00	2025-05-09 07:01:14.343249	\N	16	\N	\N
47	89	孙峰	总工办	技术总监			f	2024-03-02 00:00:00	2025-05-09 07:01:14.347792	\N	16	\N	\N
48	48	时俊华	工程部	项目总			f	2025-02-26 00:00:00	2025-05-09 07:01:14.353632	\N	16	\N	\N
49	29	石磊	政企事业部	政企事业部技术			f	2024-04-12 00:00:00	2025-05-09 07:01:14.359704	\N	16	\N	\N
50	39	施庆		主任工程师			f	2024-03-24 00:00:00	2025-05-09 07:01:14.365889	\N	16	\N	\N
51	15	权星兰		采购经理			f	2024-03-02 00:00:00	2025-05-09 07:01:14.373569	\N	16	\N	\N
52	92	钱澄雨	设计部门	项目负责人			f	2024-03-02 00:00:00	2025-05-09 07:01:14.377776	\N	16	\N	\N
53	50	蒲红星	设计部门	主任工程师			f	2024-03-01 00:00:00	2025-05-09 07:01:14.380933	\N	16	\N	\N
54	20	皮小军	智能所	弱电工程师			f	2025-04-13 00:00:00	2025-05-09 07:01:14.384123	\N	16	\N	\N
55	25	庞作崇	工程部	项目部弱电工程师			f	2025-02-21 00:00:00	2025-05-09 07:01:14.387289	\N	16	\N	\N
56	83	庞总		项目总			f	2024-03-02 00:00:00	2025-05-09 07:01:14.390489	\N	16	\N	\N
57	40	潘一帆					f	2024-03-24 00:00:00	2025-05-09 07:01:14.393719	\N	16	\N	\N
58	22	孟祥福	采购部门	部门经理			f	2024-12-29 09:25:07	2025-05-09 07:01:14.397455	\N	16	\N	\N
59	89	马骏		弱电工程师			f	2025-04-13 00:00:00	2025-05-09 07:01:14.401061	\N	16	\N	\N
60	10	马经理	工程部	项目经理			f	2024-09-22 16:25:15	2025-05-09 07:01:14.440327	\N	16	\N	\N
61	82	罗布					f	2025-04-20 00:00:00	2025-05-09 07:01:14.444247	\N	16	\N	\N
62	77	卢青峰		副总工程师			f	2024-12-08 19:46:34	2025-05-09 07:01:14.448069	\N	16	\N	\N
63	29	刘清响	智慧城市事业部	工程技术总监			f	2024-12-02 09:06:44.999	2025-05-09 07:01:14.451951	\N	16	\N	\N
64	40	林婷	采购部门	采购			f	2024-03-24 00:00:00	2025-05-09 07:01:14.45578	\N	16	\N	\N
65	62	李志远	设计部门	主任设计工程师			f	2024-03-01 00:00:00	2025-05-09 07:01:14.459899	\N	16	\N	\N
66	70	李霩	业务部门	销售			f	2024-12-22 20:03:50	2025-05-09 07:01:14.463967	\N	16	\N	\N
67	13	李珂					f	2024-03-02 00:00:00	2025-05-09 07:01:14.46884	\N	16	\N	\N
68	20	李骥	智能所	所长			f	2025-02-22 00:00:00	2025-05-09 07:01:14.472462	\N	16	\N	\N
69	79	李从军	设备所	所长			f	2024-03-02 00:00:00	2025-05-09 07:01:14.476155	\N	16	\N	\N
70	6	黎德宏		工程技术总监			f	2025-04-26 00:00:00	2025-05-09 07:01:14.486124	\N	16	\N	\N
71	50	柯中华	智能所	项目负责人			f	2024-03-01 00:00:00	2025-05-09 07:01:14.493874	\N	16	\N	\N
72	13	靳莉	技术部	项目负责人	829339888715	jinl@timeloit.com	f	2024-03-02 00:00:00	2025-05-09 07:01:14.50595	\N	16	\N	\N
73	55	蒋海宾	工程部	项目负责人			f	2025-03-01 00:00:00	2025-05-09 07:01:14.543026	\N	16	\N	\N
74	29	姜小平	采购部门	运营总监			f	2024-04-12 00:00:00	2025-05-09 07:01:14.550104	\N	16	\N	\N
75	40	姜静	设计部门	技术工程师			f	2024-03-24 00:00:00	2025-05-09 07:01:14.557953	\N	16	\N	\N
76	39	季浩		三组行政组长			f	2024-03-24 00:00:00	2025-05-09 07:01:14.565363	\N	16	\N	\N
77	21	花伟	业务部门	部门经理			f	2024-12-13 19:46:11	2025-05-09 07:01:14.575428	\N	16	\N	\N
233	387	汪总	业务部门	经理			f	2024-09-17 10:37:45	2025-05-09 07:10:25.961842	\N	13	\N	\N
78	62	胡少科	设计部门	设计师			f	2024-03-01 00:00:00	2025-05-09 07:01:14.581643	\N	16	\N	\N
79	39	贺海洋		一组行政组长			f	2024-03-24 00:00:00	2025-05-09 07:01:14.589288	\N	16	\N	\N
80	31	何正天	技术部	设计经理			f	2024-03-02 00:00:00	2025-05-09 07:01:14.597905	\N	16	\N	\N
81	12	郭金亮		项目负责人			f	2025-02-22 00:00:00	2025-05-09 07:01:14.607884	\N	16	\N	\N
82	54	郭红艳		主任设计工程师			f	2025-04-26 00:00:00	2025-05-09 07:01:14.619388	\N	16	\N	\N
83	50	顾小军		智能化所长			f	2024-03-01 00:00:00	2025-05-09 07:01:14.631835	\N	16	\N	\N
84	59	顾浩		网络规划咨询研究院院长		guh001@126.com	f	2024-02-27 00:00:00	2025-05-09 07:01:14.639294	\N	16	\N	\N
85	64	龚晨皓	采购部门	部门经理			f	2024-11-17 17:33:28	2025-05-09 07:01:14.647774	\N	16	\N	\N
86	15	宫庆强		项目经理			f	2024-03-02 00:00:00	2025-05-09 07:01:14.659803	\N	16	\N	\N
87	39	付伟		主任工程师			f	2024-03-24 00:00:00	2025-05-09 07:01:14.67405	\N	16	\N	\N
88	85	冯子煜	工程部	项目经理			f	2024-12-02 09:11:35	2025-05-09 07:01:14.687801	\N	16	\N	\N
89	59	方雅雯		设计师			f	2024-02-27 00:00:00	2025-05-09 07:01:14.699135	\N	16	\N	\N
90	15	范东华		项目工程师			f	2024-03-02 00:00:00	2025-05-09 07:01:14.708921	\N	16	\N	\N
91	15	范晨	设计部门	技术部副经理	010-59380818-82852	fanchen725@126.com	f	2024-03-02 00:00:00	2025-05-09 07:01:14.716287	\N	16	\N	\N
92	88	段荣辉	工程部	项目经理			f	2024-09-22 16:37:51.999	2025-05-09 07:01:14.724654	\N	16	\N	\N
93	81	杜国君	采购部门	部门经理			f	2025-03-23 00:00:00	2025-05-09 07:01:14.732804	\N	16	\N	\N
94	15	董鹏		技术总监			f	2024-03-02 00:00:00	2025-05-09 07:01:14.740023	\N	16	\N	\N
95	50	戴涛	智能所	项目经理			f	2024-03-01 00:00:00	2025-05-09 07:01:14.747178	\N	16	\N	\N
96	76	戴莉					f	2025-03-08 00:00:00	2025-05-09 07:01:14.753394	\N	16	\N	\N
97	21	陈华	总经理办	总经理			f	2024-12-22 19:46:59	2025-05-09 07:01:14.760646	\N	16	\N	\N
98	15	陈枫		技术			f	2024-03-02 00:00:00	2025-05-09 07:01:14.76856	\N	16	\N	\N
99	34	查丛林	技术部				f	2024-11-10 09:50:41	2025-05-09 07:01:14.774531	\N	16	\N	\N
100	418	陈瑶			13120711199		f	2025-02-25 00:00:00	2025-05-09 07:04:09.152046	\N	2	\N	\N
101	419	乔峰			15216866895		f	2025-02-25 00:00:00	2025-05-09 07:04:09.240743	\N	2	\N	\N
102	420	鲁卡			18758255131		f	2025-02-25 00:00:00	2025-05-09 07:04:09.246033	\N	2	\N	\N
103	421	包惠青			15800787781		f	2025-02-25 00:00:00	2025-05-09 07:04:09.250365	\N	2	\N	\N
104	422	叶亮					f	2025-04-24 00:00:00	2025-05-09 07:04:09.254571	\N	2	\N	\N
105	425	王飞			15806227683		f	2025-02-25 00:00:00	2025-05-09 07:04:09.258652	\N	2	\N	\N
106	426	朱伟杰	物业办公室		13818200827		f	2025-02-25 00:00:00	2025-05-09 07:04:09.262575	\N	2	\N	\N
107	427	陆晨云					f	2025-02-25 00:00:00	2025-05-09 07:04:09.266722	\N	2	\N	\N
108	428	陆岩			15146977030		f	2025-02-25 00:00:00	2025-05-09 07:04:09.339195	\N	2	\N	\N
109	429	Tony Jiang	PO Execution APAC		 021 80208671		f	2025-02-25 00:00:00	2025-05-09 07:04:09.344016	\N	2	\N	\N
110	430	陈申			15618886178		f	2025-02-25 00:00:00	2025-05-09 07:04:09.348045	\N	2	\N	\N
111	431	舒舜			15202136070		f	2025-02-25 00:00:00	2025-05-09 07:04:09.351936	\N	2	\N	\N
112	432	黄俊男			13611930686		f	2025-02-25 00:00:00	2025-05-09 07:04:09.35589	\N	2	\N	\N
113	433	黄鸣鹤			13347780171		f	2025-02-25 00:00:00	2025-05-09 07:04:09.359696	\N	2	\N	\N
114	434	 陈祺路			13601706616		f	2025-02-25 00:00:00	2025-05-09 07:04:09.363691	\N	2	\N	\N
115	435	Amy Yan	采购	采购	3749-2757	amy.yan@covestro.com	f	2025-02-21 00:00:00	2025-05-09 07:04:09.367715	\N	2	\N	\N
116	435	Jimmy Cheng			13801650434		f	2025-03-22 00:00:00	2025-05-09 07:04:09.371684	\N	2	\N	\N
117	435	Jimmy Wang			37494046	jimmyds.wang@covestro.com	f	2025-03-18 00:00:00	2025-05-09 07:04:09.37541	\N	2	\N	\N
118	435	Jimmy Wang,			37494046	jimmyds.wang@covestro.com	f	2025-03-18 00:00:00	2025-05-09 07:04:09.379405	\N	2	\N	\N
120	435	陈明	CISS-MM-ME-PCS		13701836178		f	2025-02-26 00:00:00	2025-05-09 07:04:09.439477	\N	2	\N	\N
121	435	蒋永新	CISS-TSM-TM-TAEN	技术员	199 2160 5802	yongxin.jiang1@covestro.com	f	2025-02-21 00:00:00	2025-05-09 07:04:09.449835	\N	2	\N	\N
122	435	任立国			18516172356	liguo.ren1@covestro.com\r\n	f	2025-04-08 00:00:00	2025-05-09 07:04:09.458536	\N	2	\N	\N
123	436	陆伟	安保部		13611737180		f	2025-02-25 00:00:00	2025-05-09 07:04:09.464196	\N	2	\N	\N
124	437	王睿澍			13501798747		f	2025-02-25 00:00:00	2025-05-09 07:04:09.468423	\N	2	\N	\N
125	438	王庄			13306677708		f	2025-02-25 00:00:00	2025-05-09 07:04:09.475292	\N	2	\N	\N
126	439	邓海洋			181 1629 3891		f	2025-02-25 00:00:00	2025-05-09 07:04:09.48262	\N	2	\N	\N
127	251	陈戌源			 021-61819967		f	2025-02-25 00:00:00	2025-05-09 07:04:09.490682	\N	2	\N	\N
128	440	王秋月			18742052296		f	2025-02-25 00:00:00	2025-05-09 07:04:09.497933	\N	2	\N	\N
129	441	马建荣			13701982845		f	2025-02-25 00:00:00	2025-05-09 07:04:09.505333	\N	2	\N	\N
130	443	邵师傅			13621999089		f	2025-02-25 00:00:00	2025-05-09 07:04:09.513707	\N	2	\N	\N
131	444	马珂	采购	采购	38829909	ke.ma@hhgrace.com	f	2025-02-21 00:00:00	2025-05-09 07:04:09.522524	\N	2	\N	\N
132	444	倪洁	二厂		18818223357		f	2025-02-21 00:00:00	2025-05-09 07:04:09.539688	\N	2	\N	\N
133	444	孙权	一厂		15901880015	quan.sun@hhgrace.com	f	2025-02-21 00:00:00	2025-05-09 07:04:09.54384	\N	2	\N	\N
134	444	杨震	三厂		13918107766	Colee.Yang@hhgrace.com	f	2025-02-21 00:00:00	2025-05-09 07:04:09.547572	\N	2	\N	\N
135	446	Vicky田			13761812001		f	2025-02-25 00:00:00	2025-05-09 07:04:09.551269	\N	2	\N	\N
136	263	李明鑫	IT		15267591887	williamli@mohg.com	f	2025-02-21 00:00:00	2025-05-09 07:04:09.555361	\N	2	\N	\N
137	447	谢雨晨收			13918722263		f	2025-02-25 00:00:00	2025-05-09 07:04:09.559011	\N	2	\N	\N
138	448	李壮林					f	2025-02-25 00:00:00	2025-05-09 07:04:09.564352	\N	2	\N	\N
139	449	谭冬培			18173167152		f	2025-02-25 00:00:00	2025-05-09 07:04:09.568522	\N	2	\N	\N
140	450	王建良			18607413093		f	2025-02-25 00:00:00	2025-05-09 07:04:09.573358	\N	2	\N	\N
141	451	汤智敏			13564785420		f	2025-02-25 00:00:00	2025-05-09 07:04:09.577567	\N	2	\N	\N
142	452	张鑫			18930801262		f	2025-02-25 00:00:00	2025-05-09 07:04:09.582536	\N	2	\N	\N
143	453	俞麟			13482401802		f	2025-02-25 00:00:00	2025-05-09 07:04:09.586243	\N	2	\N	\N
144	454	朱聪	保卫处		18901788615		f	2025-02-21 00:00:00	2025-05-09 07:04:09.590061	\N	2	\N	\N
145	455	孙惊生			18001663668		f	2025-02-25 00:00:00	2025-05-09 07:04:09.651413	\N	2	\N	\N
146	456	王炜 			138-1657-2313		f	2025-02-25 00:00:00	2025-05-09 07:04:09.668359	\N	2	\N	\N
147	457	陈丽霞			13585788671		f	2025-03-06 00:00:00	2025-05-09 07:04:09.688142	\N	2	\N	\N
148	458	王闱 			13816942652		f	2025-02-25 00:00:00	2025-05-09 07:04:09.695536	\N	2	\N	\N
149	459	余佳娜			18870424005		f	2025-02-21 00:00:00	2025-05-09 07:04:09.706263	\N	2	\N	\N
150	460	魏来			13817328258		f	2025-02-25 00:00:00	2025-05-09 07:04:09.71382	\N	2	\N	\N
151	461	杨晓清 	安保部		13764623286		f	2025-02-25 00:00:00	2025-05-09 07:04:09.729429	\N	2	\N	\N
152	462	李方军			13611864157		f	2025-03-06 00:00:00	2025-05-09 07:04:09.735968	\N	2	\N	\N
153	463	周殿宝			17723190423		f	2025-02-25 00:00:00	2025-05-09 07:04:09.74369	\N	2	\N	\N
154	464	舒俊					f	2025-04-11 00:00:00	2025-05-09 07:04:09.753478	\N	2	\N	\N
155	260	吴恺	工程部		15021367640	wukai@shtowercbre.com	f	2025-02-21 00:00:00	2025-05-09 07:04:09.763302	\N	2	\N	\N
385	314	邹琦	设计部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.661689	\N	15	\N	\N
156	260	赵寅	采购部		18601626294	zhaoyin@shanghaitower.com	f	2025-02-21 00:00:00	2025-05-09 07:04:09.771452	\N	2	\N	\N
157	466	林斌			13817810592		f	2025-02-25 00:00:00	2025-05-09 07:04:09.780095	\N	2	\N	\N
158	465	俞工			18918500832		f	2025-02-25 00:00:00	2025-05-09 07:04:09.790512	\N	2	\N	\N
159	467	胡蝶					f	2025-02-25 00:00:00	2025-05-09 07:04:09.805953	\N	2	\N	\N
160	468	苏诗豪	安保部		1592178360		f	2025-02-25 00:00:00	2025-05-09 07:04:09.821872	\N	2	\N	\N
161	469	张黎					f	2025-02-25 00:00:00	2025-05-09 07:04:09.829793	\N	2	\N	\N
162	422	王寒冰					f	2025-02-25 00:00:00	2025-05-09 07:04:09.838677	\N	2	\N	\N
163	333	钱成忠		弱电主任工程师			f	2024-02-22 00:00:00	2025-05-09 07:10:25.358953	\N	13	\N	\N
164	334	张莉	设计部门	经理			f	2025-03-01 00:00:00	2025-05-09 07:10:25.364408	\N	13	\N	\N
165	335	曹轶男		采购			f	2024-02-20 00:00:00	2025-05-09 07:10:25.36899	\N	13	\N	\N
166	335	胡俊凯		采购			f	2024-02-20 00:00:00	2025-05-09 07:10:25.374776	\N	13	\N	\N
167	335	贾总		事业部经理			f	2024-02-20 00:00:00	2025-05-09 07:10:25.383567	\N	13	\N	\N
168	335	徐述勤			13910774801		f	2024-02-20 00:00:00	2025-05-09 07:10:25.443771	\N	13	\N	\N
169	335	朱君丽	业务部门	经理			f	2025-02-20 00:00:00	2025-05-09 07:10:25.450422	\N	13	\N	\N
170	336	王斌	业务部门	总经理	13601362550		f	2024-09-28 14:13:27	2025-05-09 07:10:25.456958	\N	13	\N	\N
171	337	张伟伟	设计部门	经理			f	2025-03-29 00:00:00	2025-05-09 07:10:25.461676	\N	13	\N	\N
172	338	胡萍					f	2024-02-20 00:00:00	2025-05-09 07:10:25.466125	\N	13	\N	\N
173	338	王辉		总经理			f	2024-02-20 00:00:00	2025-05-09 07:10:25.471849	\N	13	\N	\N
174	339	孟凡丽	业务部门	经理	13817757566		f	2024-12-28 16:43:35	2025-05-09 07:10:25.476876	\N	13	\N	\N
175	340	李瑞	业务部门	总经理			f	2024-09-28 10:54:37	2025-05-09 07:10:25.483431	\N	13	\N	\N
176	341	邹娟	业务部门	经理	17208290989		f	2024-02-21 14:50:19	2025-05-09 07:10:25.490581	\N	13	\N	\N
177	343	易利鹏	业务部门	总经理			f	2025-03-07 00:00:00	2025-05-09 07:10:25.49836	\N	13	\N	\N
178	344	刘津佑		部长			f	2024-02-20 00:00:00	2025-05-09 07:10:25.502416	\N	13	\N	\N
179	347	尤力	总经理	总经理	18130051105		f	2024-12-28 17:00:48.999	2025-05-09 07:10:25.506411	\N	13	\N	\N
180	348	杨刚	业务部门	经理	18670046866		f	2024-03-14 18:29:21	2025-05-09 07:10:25.539144	\N	13	\N	\N
181	349	于来权	业务部门	经理	15308403622		f	2024-09-11 15:20:13	2025-05-09 07:10:25.544945	\N	13	\N	\N
182	350	陈元骏	设计部门	弱电主任工程师			f	2025-02-20 00:00:00	2025-05-09 07:10:25.55305	\N	13	\N	\N
183	350	吴文芳	设计部门	弱电主任工程师			f	2024-12-28 17:09:46.999	2025-05-09 07:10:25.557739	\N	13	\N	\N
184	350	徐珣	设计部门	弱电主任工程师			f	2024-12-28 17:31:39	2025-05-09 07:10:25.56289	\N	13	\N	\N
185	350	余杰	设计部门	经理	13501990647		f	2024-02-22 13:09:07	2025-05-09 07:10:25.567182	\N	13	\N	\N
186	351	廖凯峰		弱电主任工程师			f	2024-02-22 00:00:00	2025-05-09 07:10:25.571514	\N	13	\N	\N
187	352	冯跃	信息设备部	经理			f	2024-07-18 15:23:27	2025-05-09 07:10:25.575485	\N	13	\N	\N
188	353	陶亮		ESH部长			f	2024-02-20 00:00:00	2025-05-09 07:10:25.579477	\N	13	\N	\N
189	354	张永泽	业务部门	经理	13904403832		f	2024-06-13 16:26:11	2025-05-09 07:10:25.58337	\N	13	\N	\N
190	356	凌剑传	设计部门	经理	13824439019		f	2024-02-22 21:07:35	2025-05-09 07:10:25.587354	\N	13	\N	\N
191	358	陈旭东	采购部门	经理	13518181739		f	2024-02-21 11:55:50	2025-05-09 07:10:25.591123	\N	13	\N	\N
196	360	付强	设计部门	经理	13951013842		f	2025-04-11 00:00:00	2025-05-09 07:10:25.663092	\N	13	\N	\N
197	361	万伟民	设计部门	经理	15345428848		f	2024-04-13 23:57:27	2025-05-09 07:10:25.668346	\N	13	\N	\N
198	362	李永杰	业务部门	总经理	13285329285		f	2024-04-13 23:53:13	2025-05-09 07:10:25.673117	\N	13	\N	\N
199	363	李京芳	业务部门	经理			f	2024-09-30 13:39:46	2025-05-09 07:10:25.678266	\N	13	\N	\N
200	365	王文	民航智能中心	经理			f	2025-03-05 00:00:00	2025-05-09 07:10:25.684151	\N	13	\N	\N
201	366	张士彦	业务部门	总经理			f	2025-04-06 00:00:00	2025-05-09 07:10:25.688783	\N	13	\N	\N
202	367	程斌	业务部门	经理	17765115659		f	2024-02-21 14:40:32	2025-05-09 07:10:25.69338	\N	13	\N	\N
203	368	秦磊					f	2024-02-20 00:00:00	2025-05-09 07:10:25.698027	\N	13	\N	\N
204	369	孙晓文	设计部门	技术经理			f	2024-02-22 00:00:00	2025-05-09 07:10:25.702722	\N	13	\N	\N
205	369	严俊松		商务副总（采购）			f	2024-02-22 00:00:00	2025-05-09 07:10:25.739347	\N	13	\N	\N
206	371	夏鑫	信息设备部	经理			f	2024-09-28 10:00:49	2025-05-09 07:10:25.744068	\N	13	\N	\N
207	372	曹雪芹	工程部门	经理			f	2025-03-14 00:00:00	2025-05-09 07:10:25.748329	\N	13	\N	\N
208	373	朱秀兰	业务部门	经理			f	2025-03-19 00:00:00	2025-05-09 07:10:25.755796	\N	13	\N	\N
209	374	庹伟	业务部门	经理			f	2025-02-22 00:00:00	2025-05-09 07:10:25.762207	\N	13	\N	\N
210	375	汤晓波	业务部门	总经理			f	2025-04-23 00:00:00	2025-05-09 07:10:25.767479	\N	13	\N	\N
211	300	李冬	业务部门	总经理	13585572944		f	2024-02-21 15:36:42	2025-05-09 07:10:25.772712	\N	13	\N	\N
212	377	应寅	工程部门	经理			f	2025-03-12 00:00:00	2025-05-09 07:10:25.777993	\N	13	\N	\N
213	332	谭理	信息设备部	经理	15921538269		f	2024-02-21 15:02:52	2025-05-09 07:10:25.784666	\N	13	\N	\N
214	219	郑翔	设计部门	经理	17749714586		f	2024-03-14 19:13:04.999	2025-05-09 07:10:25.78879	\N	13	\N	\N
215	305	祁桢	业务部门	经理	15800577707		f	2024-08-31 11:52:40	2025-05-09 07:10:25.795627	\N	13	\N	\N
216	379	蔡伟	设计部门	经理	13817139998		f	2024-03-01 13:07:07	2025-05-09 07:10:25.8424	\N	13	\N	\N
217	379	顾云凯		设计经理			f	2024-02-20 00:00:00	2025-05-09 07:10:25.848716	\N	13	\N	\N
218	379	田亚辉		设计经理			f	2024-02-20 00:00:00	2025-05-09 07:10:25.853878	\N	13	\N	\N
219	379	吴晓珉		采购			f	2024-02-20 00:00:00	2025-05-09 07:10:25.858494	\N	13	\N	\N
220	379	薛珈		采购			f	2024-02-20 00:00:00	2025-05-09 07:10:25.864951	\N	13	\N	\N
221	379	杨黎晶		合约			f	2024-02-20 00:00:00	2025-05-09 07:10:25.869423	\N	13	\N	\N
222	379	周吉		采购			f	2024-02-20 00:00:00	2025-05-09 07:10:25.880111	\N	13	\N	\N
223	379	朱海燕		合约经理			f	2024-02-20 00:00:00	2025-05-09 07:10:25.889116	\N	13	\N	\N
224	379	王磊		技术			f	2024-02-20 00:00:00	2025-05-09 07:10:25.894948	\N	13	\N	\N
225	380	马林波	业务部门	经理			f	2025-01-04 09:44:50	2025-05-09 07:10:25.898821	\N	13	\N	\N
226	381	孙启超		销售经理			f	2024-02-22 00:00:00	2025-05-09 07:10:25.903122	\N	13	\N	\N
227	381	田飞	设计部门	负责人			f	2024-02-22 00:00:00	2025-05-09 07:10:25.906837	\N	13	\N	\N
228	381	张明		商务经理			f	2024-02-22 00:00:00	2025-05-09 07:10:25.939568	\N	13	\N	\N
229	383	黄总		弱电经理			f	2024-02-20 00:00:00	2025-05-09 07:10:25.944258	\N	13	\N	\N
230	384	孙方正	设计部门	总经理			f	2024-10-31 11:43:53	2025-05-09 07:10:25.948257	\N	13	\N	\N
231	384	孙月红	设计部门	经理			f	2025-03-29 00:00:00	2025-05-09 07:10:25.952208	\N	13	\N	\N
232	385	贺鹤明	业务部门	经理			f	2024-10-20 15:25:25	2025-05-09 07:10:25.956648	\N	13	\N	\N
234	388	杨松	设计部门	设计经理			f	2024-10-20 21:49:53	2025-05-09 07:10:25.967281	\N	13	\N	\N
235	390	孙佳梅	业务部门	经理	13086651575		f	2024-11-16 11:53:55	2025-05-09 07:10:25.972528	\N	13	\N	\N
236	391	刘贵东	业务部门	经理	18983808184		f	2024-08-02 10:58:49	2025-05-09 07:10:25.976314	\N	13	\N	\N
237	392	马年伟	工程部门	经理			f	2025-04-06 00:00:00	2025-05-09 07:10:25.980115	\N	13	\N	\N
238	395	张群	业务部门	总经理			f	2024-09-28 15:54:58	2025-05-09 07:10:25.983696	\N	13	\N	\N
239	331	俞工	业务部门	经理			f	2025-03-14 00:00:00	2025-05-09 07:10:25.987294	\N	13	\N	\N
240	243	包顺强		组长			f	2024-02-22 00:00:00	2025-05-09 07:10:25.990797	\N	13	\N	\N
241	243	施国平		普通工程师			f	2024-02-22 00:00:00	2025-05-09 07:10:26.038152	\N	13	\N	\N
242	243	唐平	设计部门	弱电主任工程师			f	2024-09-28 16:13:39	2025-05-09 07:10:26.042516	\N	13	\N	\N
243	243	宛紫晶		普通工程师			f	2024-02-22 00:00:00	2025-05-09 07:10:26.046512	\N	13	\N	\N
244	243	王昌		弱电主任工程师（组长）			f	2024-02-22 00:00:00	2025-05-09 07:10:26.050257	\N	13	\N	\N
245	243	谢文黎		弱电主任工程师			f	2024-02-22 00:00:00	2025-05-09 07:10:26.056369	\N	13	\N	\N
246	243	尤文捷	设计部门	设计师			f	2024-02-22 00:00:00	2025-05-09 07:10:26.060323	\N	13	\N	\N
247	243	张深		普通工程师			f	2024-02-22 00:00:00	2025-05-09 07:10:26.064522	\N	13	\N	\N
248	397	诸力		环安经理			f	2024-02-20 00:00:00	2025-05-09 07:10:26.068534	\N	13	\N	\N
249	398	宋登	工程部门	经理			f	2024-09-28 10:31:24	2025-05-09 07:10:26.072615	\N	13	\N	\N
250	399	邹茹飞	业务部门	总经理			f	2024-09-28 15:52:05	2025-05-09 07:10:26.077165	\N	13	\N	\N
251	400	张晓龙	采购部门	经理			f	2025-04-06 00:00:00	2025-05-09 07:10:26.081294	\N	13	\N	\N
252	401	陈霆斌	设计部门	经理	18980991113		f	2024-02-21 14:45:42	2025-05-09 07:10:26.085252	\N	13	\N	\N
253	401	施君	设计部门	经理			f	2025-02-08 00:00:00	2025-05-09 07:10:26.089314	\N	13	\N	\N
254	401	王兵	工程部门	经理			f	2025-02-22 00:00:00	2025-05-09 07:10:26.093316	\N	13	\N	\N
255	402	曹高余	信息设备部	经理	18116017977		f	2024-03-18 14:25:38	2025-05-09 07:10:26.143166	\N	13	\N	\N
256	403	陆大鼎		环安经理			f	2024-02-20 00:00:00	2025-05-09 07:10:26.147272	\N	13	\N	\N
257	403	王羽东		环安经理			f	2024-02-20 00:00:00	2025-05-09 07:10:26.151114	\N	13	\N	\N
258	404	许良赛					f	2024-03-10 00:00:00	2025-05-09 07:10:26.156719	\N	13	\N	\N
259	405	张权玉	工程部门	经理	13023198881		f	2024-02-21 15:14:02	2025-05-09 07:10:26.162889	\N	13	\N	\N
260	406	朱岩旭	 民航智能中心	技术经理	18610783499		f	2024-03-10 15:36:34	2025-05-09 07:10:26.16687	\N	13	\N	\N
261	407	李佳莉	设计部门	技术经理			f	2024-02-22 00:00:00	2025-05-09 07:10:26.170888	\N	13	\N	\N
262	407	邱小勇					f	2024-02-22 00:00:00	2025-05-09 07:10:26.175453	\N	13	\N	\N
263	407	熊泽祝	设计部门	总工			f	2024-02-22 00:00:00	2025-05-09 07:10:26.179456	\N	13	\N	\N
264	407	余海威	18623100394	技术经理			f	2024-02-22 00:00:00	2025-05-09 07:10:26.183367	\N	13	\N	\N
265	408	吴有博	设计部门	技术经理			f	2025-04-20 00:00:00	2025-05-09 07:10:26.187167	\N	13	\N	\N
266	411	程智源	设计部门	设计经理			f	2025-03-01 00:00:00	2025-05-09 07:10:26.241027	\N	13	\N	\N
267	412	时姗姗	设计部门	经理	13691001868		f	2024-03-18 13:41:39	2025-05-09 07:10:26.245685	\N	13	\N	\N
268	414	张伟	业务部门	经理			f	2024-10-20 22:08:24	2025-05-09 07:10:26.250197	\N	13	\N	\N
269	415	刘询		环安经理			f	2024-02-20 00:00:00	2025-05-09 07:10:26.25426	\N	13	\N	\N
270	415	杨孝桥		环安工程师			f	2024-02-20 00:00:00	2025-05-09 07:10:26.258224	\N	13	\N	\N
271	415	赵奇					f	2024-02-20 00:00:00	2025-05-09 07:10:26.26252	\N	13	\N	\N
272	416	谭超洋	业务部门	经理			f	2024-12-31 15:27:02.999	2025-05-09 07:10:26.266505	\N	13	\N	\N
273	416	唐明勇	业务部门	经理			f	2025-02-08 00:00:00	2025-05-09 07:10:26.270321	\N	13	\N	\N
274	417	宋崇高	业务部门	经理	13996286755		f	2024-02-22 12:26:03	2025-05-09 07:10:26.274211	\N	13	\N	\N
275	265	董剑喆	设计部门	弱电工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.650354	\N	15	\N	\N
276	265	雷亮	设计部门	弱电主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.656689	\N	15	\N	\N
277	265	李坤昊	设计部门	弱电工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.673666	\N	15	\N	\N
278	265	乔曼丽	设计部门	弱电工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.681745	\N	15	\N	\N
279	265	孙佳	设计部门	电气工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.690927	\N	15	\N	\N
280	265	张明亮	设计部门	弱电工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.696663	\N	15	\N	\N
281	266	雷开准					f	2024-02-21 00:00:00	2025-05-09 07:12:42.704684	\N	15	\N	\N
282	267	刘冬华	设计部门	主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.711207	\N	15	\N	\N
283	268	刘晨	设计部门	技术经理	13810976552		f	2024-09-15 00:00:00	2025-05-09 07:12:42.717671	\N	15	\N	\N
284	269	雷军	设计部门	技术	15061936518		f	2024-06-08 00:00:00	2025-05-09 07:12:42.723653	\N	15	\N	\N
285	270	林燕	设计部门	主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.742367	\N	15	\N	\N
286	270	詹杰	设计部门	主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.747246	\N	15	\N	\N
287	271	陈进如	总经理	总经理	18057838002		f	2025-04-15 00:00:00	2025-05-09 07:12:42.752911	\N	15	\N	\N
288	272	朱一众	项目部门	项目经理	13002110983		f	2024-02-22 00:00:00	2025-05-09 07:12:42.757576	\N	15	\N	\N
289	205	桂萍	采购部门	采购经理			f	2024-02-21 00:00:00	2025-05-09 07:12:42.762171	\N	15	\N	\N
290	273	李亚林	项目部门	项目经理	13730036533		f	2025-02-12 00:00:00	2025-05-09 07:12:42.766749	\N	15	\N	\N
291	274	李爱祥	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:42.7713	\N	15	\N	\N
292	274	梁凤伟	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:42.777573	\N	15	\N	\N
293	274	马海南	市场部门	市场商务			f	2024-02-21 00:00:00	2025-05-09 07:12:42.782558	\N	15	\N	\N
294	350	黄辰赟	设计部门	设计高工	135 0162 8332		f	2024-02-22 00:00:00	2025-05-09 07:12:42.787806	\N	15	\N	\N
295	274	王郭玮	采购部门	采购经理			f	2024-02-21 00:00:00	2025-05-09 07:12:42.792796	\N	15	\N	\N
296	274	魏鑫	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:42.796474	\N	15	\N	\N
297	274	尹春峰	采购部门	采购专员			f	2024-02-21 00:00:00	2025-05-09 07:12:42.800625	\N	15	\N	\N
298	274	张志键	采购部门	采购总监			f	2024-02-21 00:00:00	2025-05-09 07:12:42.843836	\N	15	\N	\N
299	274	章和平	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:42.84794	\N	15	\N	\N
300	275	叶月华	采购部门	采购经理	17717235417		f	2024-11-02 00:00:00	2025-05-09 07:12:42.851921	\N	15	\N	\N
301	276	许经理	设计部门	技术			f	2024-10-11 00:00:00	2025-05-09 07:12:42.856183	\N	15	\N	\N
302	277	蔡楠楠	设计部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:42.860342	\N	15	\N	\N
303	277	陈春灵	采购部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:42.866713	\N	15	\N	\N
304	278	陈适	设计部门	主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.870838	\N	15	\N	\N
305	278	柯蕴知	设计部门	智能化设计			f	2024-02-21 00:00:00	2025-05-09 07:12:42.874586	\N	15	\N	\N
306	278	李幸	设计部门	电气主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.880393	\N	15	\N	\N
307	278	王佳佳	设计部门	弱电主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.886325	\N	15	\N	\N
308	279	李俊	项目部门	项目经理	17794511906		f	2025-03-14 00:00:00	2025-05-09 07:12:42.891578	\N	15	\N	\N
309	280	郑德聪	项目部门	项目经理	13607527867		f	2025-03-01 00:00:00	2025-05-09 07:12:42.895361	\N	15	\N	\N
310	124	王兴	设计部门	技术经理	13400601951		f	2024-02-22 00:00:00	2025-05-09 07:12:42.939741	\N	15	\N	\N
311	283	许文静	副总经理	总经理	17775645280		f	2024-12-21 00:00:00	2025-05-09 07:12:42.944491	\N	15	\N	\N
312	285	包越	设计部门	弱电主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.948813	\N	15	\N	\N
313	285	邬颖坚	设计部门	弱电工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:42.953314	\N	15	\N	\N
314	286	韦力		技术			f	2024-02-22 00:00:00	2025-05-09 07:12:42.958216	\N	15	\N	\N
315	287	陈利华	采购部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:42.963065	\N	15	\N	\N
316	289	顾剑豪	项目部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:42.968085	\N	15	\N	\N
317	289	李建荣	销售部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.039715	\N	15	\N	\N
318	289	马春燕	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.044765	\N	15	\N	\N
319	289	王俊	销售部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.049642	\N	15	\N	\N
320	289	徐经理	采购部门	主管（财务合约）			f	2024-02-21 00:00:00	2025-05-09 07:12:43.054087	\N	15	\N	\N
321	289	张俊义	销售部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.059859	\N	15	\N	\N
322	290	樊静	采购部门	采购	13661588964		f	2024-02-22 00:00:00	2025-05-09 07:12:43.06446	\N	15	\N	\N
323	291	白银龙	总经理	总经理	13301785650		f	2024-11-05 00:00:00	2025-05-09 07:12:43.069622	\N	15	\N	\N
324	293	曹剑华					f	2024-02-21 00:00:00	2025-05-09 07:12:43.077074	\N	15	\N	\N
325	294	胡骏	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.083809	\N	15	\N	\N
326	294	王小波	项目部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.092211	\N	15	\N	\N
327	294	武宗庆	采购部门	采购经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.100811	\N	15	\N	\N
328	294	徐慧	采购部门	采购			f	2024-02-21 00:00:00	2025-05-09 07:12:43.142762	\N	15	\N	\N
329	294	杨新	设计部门	普通员工			f	2024-02-21 00:00:00	2025-05-09 07:12:43.147231	\N	15	\N	\N
330	295	陈鹏	业务部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.155996	\N	15	\N	\N
331	205	范张亮	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.163723	\N	15	\N	\N
332	205	李凯捷	设计部门	负责人			f	2024-02-21 00:00:00	2025-05-09 07:12:43.168197	\N	15	\N	\N
333	205	刘小芬	副总经理	副总经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.173483	\N	15	\N	\N
334	205	龙剑辉	项目部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.178763	\N	15	\N	\N
335	205	邵思琦	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.18381	\N	15	\N	\N
336	205	肖彦	设计部门	负责人			f	2024-02-21 00:00:00	2025-05-09 07:12:43.188626	\N	15	\N	\N
337	205	徐闻发	总经理	总经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.193262	\N	15	\N	\N
338	205	薛刚	设计部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.197762	\N	15	\N	\N
339	205	周凯凯	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.239238	\N	15	\N	\N
340	296	张斌					f	2024-02-21 00:00:00	2025-05-09 07:12:43.245519	\N	15	\N	\N
341	297	曾懿					f	2024-02-21 00:00:00	2025-05-09 07:12:43.250507	\N	15	\N	\N
342	298	范佳顺	设计部门	技术经理	13817689237		f	2024-10-19 00:00:00	2025-05-09 07:12:43.255585	\N	15	\N	\N
343	299	蒋佩佩	采购部门	采购经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.260265	\N	15	\N	\N
344	299	李娟	采购部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.265205	\N	15	\N	\N
345	299	刘学军	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.270856	\N	15	\N	\N
346	299	彭卫兵	业务部门	销售经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.27588	\N	15	\N	\N
347	299	杨通清	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.280791	\N	15	\N	\N
348	301	董碧雄	项目部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.285412	\N	15	\N	\N
349	301	李芹	采购部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.290526	\N	15	\N	\N
350	301	王文乐	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.297298	\N	15	\N	\N
351	306	陈晨	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.341759	\N	15	\N	\N
352	306	范西	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.347802	\N	15	\N	\N
353	306	陆继龙	销售部门	销售经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.352381	\N	15	\N	\N
354	306	邱宏建	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.35774	\N	15	\N	\N
355	306	任庆欣	采购部门	商务经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.363714	\N	15	\N	\N
356	306	吴烨琪	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.368897	\N	15	\N	\N
357	306	杨德月	采购部门	采购专员			f	2024-02-21 00:00:00	2025-05-09 07:12:43.3747	\N	15	\N	\N
358	306	周枫	采购部门	采购			f	2024-02-21 00:00:00	2025-05-09 07:12:43.379918	\N	15	\N	\N
359	226	沈弈恺	项目部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.385002	\N	15	\N	\N
360	226	唐宇凡	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.391061	\N	15	\N	\N
361	314	王磊	项目部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.398156	\N	15	\N	\N
362	226	徐俊	采购部门	采购经理	13761386533		f	2024-03-16 00:00:00	2025-05-09 07:12:43.440495	\N	15	\N	\N
363	307	李鹤翔	设计部门	技术	15000124252		f	2024-09-30 00:00:00	2025-05-09 07:12:43.477248	\N	15	\N	\N
364	309	杨靖	采购部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.485817	\N	15	\N	\N
365	310	刘王强	采购部门	商务总监			f	2024-02-21 00:00:00	2025-05-09 07:12:43.495285	\N	15	\N	\N
366	310	郑东	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.50187	\N	15	\N	\N
367	310	周青中	设计部门	普通员工			f	2024-02-21 00:00:00	2025-05-09 07:12:43.506878	\N	15	\N	\N
368	310	周志超	总经理	总经理		zzc@youhe.co	f	2024-02-21 00:00:00	2025-05-09 07:12:43.512317	\N	15	\N	\N
369	311	曾俊辉	销售部门	销售			f	2024-02-21 00:00:00	2025-05-09 07:12:43.518937	\N	15	\N	\N
370	311	陈玉玲	采购部门	采购			f	2024-02-21 00:00:00	2025-05-09 07:12:43.524014	\N	15	\N	\N
371	311	高慧霞	销售部门	商务专员			f	2024-02-21 00:00:00	2025-05-09 07:12:43.528736	\N	15	\N	\N
372	311	高志强	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.541981	\N	15	\N	\N
373	311	雷前锋	项目部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.54658	\N	15	\N	\N
374	311	倪刚	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.550967	\N	15	\N	\N
375	311	齐立	采购部门	采购经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.555205	\N	15	\N	\N
376	311	尹臻	项目部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.55982	\N	15	\N	\N
377	311	朱俨	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.5642	\N	15	\N	\N
378	313	林杜宾	设计部门	主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:43.568542	\N	15	\N	\N
379	314	鲍磊	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.57414	\N	15	\N	\N
380	314	曹群峰	采购部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.578793	\N	15	\N	\N
381	314	杜昌超	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.583398	\N	15	\N	\N
382	314	郭辉	项目部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.587788	\N	15	\N	\N
383	314	梁尔路	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.647064	\N	15	\N	\N
384	314	张泳	设计部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.655492	\N	15	\N	\N
386	315	束立	设计部门	弱电主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:43.672045	\N	15	\N	\N
387	315	钟春华	设计部门	弱电主任工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:43.677923	\N	15	\N	\N
388	316	王靖宇	项目部门	项目经理			f	2025-03-29 00:00:00	2025-05-09 07:12:43.683732	\N	15	\N	\N
389	317	吴总	副总经理	总经理	18657105009		f	2024-06-15 00:00:00	2025-05-09 07:12:43.689692	\N	15	\N	\N
390	318	沈永明					f	2024-02-21 00:00:00	2025-05-09 07:12:43.694411	\N	15	\N	\N
391	319	李波	总经理	总经理			f	2024-03-16 00:00:00	2025-05-09 07:12:43.698904	\N	15	\N	\N
392	319	李君	销售部门	销售经理	13627154355		f	2024-04-13 00:00:00	2025-05-09 07:12:43.705752	\N	15	\N	\N
393	320	甘罗	项目部门	项目经理	13777856897		f	2024-03-16 00:00:00	2025-05-09 07:12:43.713152	\N	15	\N	\N
394	321	李伟	设计部门	技术	18857748044		f	2025-03-14 00:00:00	2025-05-09 07:12:43.743218	\N	15	\N	\N
395	322	金晓望	设计部门	技术	13757164012		f	2025-03-29 00:00:00	2025-05-09 07:12:43.748571	\N	15	\N	\N
396	323	黄震	设计部门	智能化院长	15088694745		f	2024-04-08 00:00:00	2025-05-09 07:12:43.752651	\N	15	\N	\N
397	323	刘译泽	设计部门	设计高工	13958189001		f	2025-03-01 00:00:00	2025-05-09 07:12:43.75796	\N	15	\N	\N
398	323	俞海泉	设计部门	设计部门组长	15868462553		f	2025-03-01 00:00:00	2025-05-09 07:12:43.761865	\N	15	\N	\N
399	324	陈峰庭	设计部门	技术	13515816104		f	2025-03-14 00:00:00	2025-05-09 07:12:43.768328	\N	15	\N	\N
400	325	田经理	设计部门	技术经理	18958151816		f	2024-02-22 00:00:00	2025-05-09 07:12:43.772842	\N	15	\N	\N
401	326	郑宸	设计部门	技术经理			f	2025-03-01 00:00:00	2025-05-09 07:12:43.777503	\N	15	\N	\N
402	327	郑平					f	2024-02-21 00:00:00	2025-05-09 07:12:43.781718	\N	15	\N	\N
403	328	王浩	采购部门	商务经理（采购）	18827388017		f	2024-02-21 00:00:00	2025-05-09 07:12:43.786123	\N	15	\N	\N
404	329	陆征海		技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.844141	\N	15	\N	\N
405	330	何永贵	总经理	总经理			f	2024-09-19 00:00:00	2025-05-09 07:12:43.849296	\N	15	\N	\N
406	330	李强	设计部门	技术经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.858713	\N	15	\N	\N
407	330	李霄	采购部门	普通员工			f	2024-02-21 00:00:00	2025-05-09 07:12:43.865184	\N	15	\N	\N
408	330	刘睿	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.87127	\N	15	\N	\N
409	330	彭朝位	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.877329	\N	15	\N	\N
410	330	孙铖	项目部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.88328	\N	15	\N	\N
411	330	孙彦辉	项目部门	项目经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.889074	\N	15	\N	\N
412	330	杨鼓飞	采购部门	采购			f	2024-02-21 00:00:00	2025-05-09 07:12:43.89389	\N	15	\N	\N
413	330	张光武	设计部门	技术			f	2024-02-21 00:00:00	2025-05-09 07:12:43.898051	\N	15	\N	\N
414	165	武薇					f	2024-02-21 00:00:00	2025-05-09 07:12:43.942261	\N	15	\N	\N
415	165	朱高峰	设计部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:12:43.947039	\N	15	\N	\N
416	248	丁工	设计部门	设计部负责人			f	2024-02-21 00:00:00	2025-05-09 07:12:43.95178	\N	15	\N	\N
417	248	高歌		普通工程师			f	2024-02-21 00:00:00	2025-05-09 07:12:43.956307	\N	15	\N	\N
418	248	李霄云		设计部门组长			f	2024-02-21 00:00:00	2025-05-09 07:12:43.96151	\N	15	\N	\N
419	248	赵铁军		弱电主任工程师（组长）			f	2024-02-21 00:00:00	2025-05-09 07:12:43.966344	\N	15	\N	\N
420	248	庄研华		弱电主任工程师（组长）			f	2024-02-21 00:00:00	2025-05-09 07:12:43.970528	\N	15	\N	\N
421	445	陆晨丰	ERC		15821094481		f	2025-02-14 00:00:00	2025-05-09 07:16:22.040363	\N	7	\N	\N
422	249	林岭	设计院	工程师	13042162149		f	2025-03-15 00:00:00	2025-05-09 07:16:22.048088	\N	7	\N	\N
423	249	殷玲	设计所	工程师			f	2025-03-15 00:00:00	2025-05-09 07:16:22.053659	\N	7	\N	\N
424	431	舒顺	信通	通信负责人	15202136070		f	2025-02-26 00:00:00	2025-05-09 07:16:22.062033	\N	7	\N	\N
425	435	黄代梅	CAS	区域负责人	13512134334	daimei.huang@covestro.com	f	2025-02-14 00:00:00	2025-05-09 07:16:22.068515	\N	7	\N	\N
426	435	王金元	IOBC	区域负责人	13501797967	jinyuan.wang1@covestro.com	f	2025-02-14 00:00:00	2025-05-09 07:16:22.076206	\N	7	\N	\N
427	435	吴天杰	PCS	区域负责人	13917102919	tianjie.wu@covestro.com	f	2025-02-14 00:00:00	2025-05-09 07:16:22.081517	\N	7	\N	\N
428	435	肖开銮	E188	工程师	13564524932		f	2025-02-28 00:00:00	2025-05-09 07:16:22.087378	\N	7	\N	\N
429	435	张岩松	E188	区域负责人	13248233912	rock.zhang@covestro.com	f	2025-02-14 00:00:00	2025-05-09 07:16:22.092945	\N	7	\N	\N
430	435	赵文丰	MDI	区域负责人	15618125897	wenfeng.zhao@covestro.com	f	2025-02-14 00:00:00	2025-05-09 07:16:22.098689	\N	7	\N	\N
431	435	邹伟奇	TDI	区域负责人	13816498667	weiqi.zou@covestro.com	f	2025-02-14 00:00:00	2025-05-09 07:16:22.142336	\N	7	\N	\N
432	250	余启源	浦东支队信通处		13681775448		f	2025-04-08 00:00:00	2025-05-09 07:16:22.147054	\N	7	\N	\N
433	251	戴斌	弱电	负责人	13601840893		f	2025-02-26 00:00:00	2025-05-09 07:16:22.152811	\N	7	\N	\N
434	252	顾婷婷	机电	负责人	13501635463		f	2025-02-14 00:00:00	2025-05-09 07:16:22.157351	\N	7	\N	\N
435	252	黄亮	合约	经办人	13564263920		f	2025-02-14 00:00:00	2025-05-09 07:16:22.161563	\N	7	\N	\N
436	252	张晓明	机电	负责人	13761049588		f	2025-02-14 00:00:00	2025-05-09 07:16:22.170444	\N	7	\N	\N
437	253	黄周迪	弱电	工程师	13816856851	jthzd@jtzx.sh.cn	f	2025-02-14 00:00:00	2025-05-09 07:16:22.174624	\N	7	\N	\N
438	253	奚晗之	弱电	部门经理	18918582662	jtxhz@jtzx.sh.cn	f	2025-02-14 00:00:00	2025-05-09 07:16:22.184655	\N	7	\N	\N
439	470	石维	ERC	无线对讲系统负责人	17872130618		f	2025-02-21 00:00:00	2025-05-09 07:16:22.194547	\N	7	\N	\N
440	263	nik	IT	工程师	13120686808		f	2025-02-28 00:00:00	2025-05-09 07:16:22.202693	\N	7	\N	\N
441	263	Samuel	IT	IT部经理	18121217251		f	2025-02-28 00:00:00	2025-05-09 07:16:22.211658	\N	7	\N	\N
442	454	曹丞	弱电	负责人	15316507856		f	2025-02-28 00:00:00	2025-05-09 07:16:22.238911	\N	7	\N	\N
443	454	丁正率	合约审核	负责人	18019789993		f	2025-02-26 00:00:00	2025-05-09 07:16:22.247099	\N	7	\N	\N
444	262	谭理	IT	负责人	18917860570		f	2025-02-28 00:00:00	2025-05-09 07:16:22.255232	\N	7	\N	\N
445	254	张琛	总队信通处				f	2025-04-08 00:00:00	2025-05-09 07:16:22.267778	\N	7	\N	\N
446	255	徐亮	总经办	总经理		xuliang@timeast.com.cn	f	2025-04-19 00:00:00	2025-05-09 07:16:22.281942	\N	7	\N	\N
447	256	马建强	弱电	负责人	13601784093		f	2025-02-28 00:00:00	2025-05-09 07:16:22.288293	\N	7	\N	\N
448	257	李家俊	弱电	工程师	13817667467		f	2025-02-28 00:00:00	2025-05-09 07:16:22.298978	\N	7	\N	\N
449	258	杜隽杰	采购部	经理	13816337607		f	2025-02-14 00:00:00	2025-05-09 07:16:22.314061	\N	7	\N	\N
450	258	孟培寅	物资采购部	采购员	13817921033		f	2025-02-28 00:00:00	2025-05-09 07:16:22.327892	\N	7	\N	\N
451	259	崔正君	弱电	负责人	13918682887		f	2025-04-09 00:00:00	2025-05-09 07:16:22.337339	\N	7	\N	\N
452	259	冯佳	采购部	采购部无线对讲系统产品采购经办人	13764574926		f	2025-02-28 00:00:00	2025-05-09 07:16:22.34596	\N	7	\N	\N
453	259	李玉洁	采购部	负责人	18817327869		f	2025-02-28 00:00:00	2025-05-09 07:16:22.361829	\N	7	\N	\N
454	259	施培璐	采购部	采购员	18616970939		f	2025-02-28 00:00:00	2025-05-09 07:16:22.377322	\N	7	\N	\N
455	261	刘禹彤		工程师	13120994403		f	2025-03-01 00:00:00	2025-05-09 07:16:22.392486	\N	7	\N	\N
456	422	袁邓多	IT	负责人	13564430591		f	2025-02-28 00:00:00	2025-05-09 07:16:22.402716	\N	7	\N	\N
457	470	吴林建	IT	工程师	18370269716		f	2025-02-28 00:00:00	2025-05-09 07:16:22.408266	\N	7	\N	\N
458	470	张尚东	ERC	工程师	13658163947		f	2025-03-15 00:00:00	2025-05-09 07:16:22.414734	\N	7	\N	\N
459	470	赵泽奇	IT	负责人	17727587660		f	2025-02-28 00:00:00	2025-05-09 07:16:22.421157	\N	7	\N	\N
460	264	马振邦	ERC	部门经理	13482849402	zhenbang_ma@smscs.com	f	2025-02-14 00:00:00	2025-05-09 07:16:22.42703	\N	7	\N	\N
461	172	陈丽娟	设计部	主任工程师			f	2025-02-26 00:00:00	2025-05-09 07:19:14.445725	\N	14	\N	\N
462	173	郭清峰	项目部门	项目经理			f	2024-02-20 00:00:00	2025-05-09 07:19:14.453333	\N	14	\N	\N
463	173	金工	设计部门	普通员工			f	2024-02-20 00:00:00	2025-05-09 07:19:14.459094	\N	14	\N	\N
464	173	陆炎	项目部门	苏南项目部经理			f	2024-02-20 00:00:00	2025-05-09 07:19:14.464735	\N	14	\N	\N
465	173	王进	项目部门	项目经理			f	2024-02-20 00:00:00	2025-05-09 07:19:14.470198	\N	14	\N	\N
466	173	魏巍	技术	技术			f	2024-05-05 12:53:37	2025-05-09 07:19:14.475379	\N	14	\N	\N
467	173	吴侃	设计部门	技术经理			f	2024-02-20 00:00:00	2025-05-09 07:19:14.480031	\N	14	\N	\N
468	173	谢丹	项目部门	西区江森重庆办技术			f	2024-02-20 00:00:00	2025-05-09 07:19:14.485328	\N	14	\N	\N
469	173	薛鹏飞	项目部门	项目经理			f	2024-02-20 00:00:00	2025-05-09 07:19:14.492135	\N	14	\N	\N
470	173	尤经理	设计部门	普通员工			f	2024-02-20 00:00:00	2025-05-09 07:19:14.496833	\N	14	\N	\N
471	173	张宁	项目部门	项目经理			f	2024-02-20 00:00:00	2025-05-09 07:19:14.50211	\N	14	\N	\N
472	174	杨敬鹏	销售	经理			f	2025-03-14 00:00:00	2025-05-09 07:19:14.542745	\N	14	\N	\N
473	350	陈未	技术	技术			f	2024-06-21 15:26:25	2025-05-09 07:19:14.548762	\N	14	\N	\N
474	350	陈允强	设计部门	工程师			f	2024-03-21 16:16:42	2025-05-09 07:19:14.554537	\N	14	\N	\N
475	350	龚伟	设计部门	主任工程师	13901875076		f	2024-02-22 12:21:06	2025-05-09 07:19:14.559821	\N	14	\N	\N
476	350	韩翌	设计	工程师			f	2024-08-08 15:06:12	2025-05-09 07:19:14.567063	\N	14	\N	\N
477	350	李源	设计部	工程师			f	2024-05-25 15:43:29.999	2025-05-09 07:19:14.572973	\N	14	\N	\N
478	350	毛晶轶	设计部	工程师			f	2025-03-08 00:00:00	2025-05-09 07:19:14.578638	\N	14	\N	\N
479	350	王小安	设计部门	主任工程师			f	2024-03-21 16:10:35	2025-05-09 07:19:14.583538	\N	14	\N	\N
480	350	殷平	设计部门	工程师			f	2024-03-16 17:09:26	2025-05-09 07:19:14.588363	\N	14	\N	\N
481	350	张航	设计部门	工程师			f	2024-05-21 15:34:21	2025-05-09 07:19:14.59323	\N	14	\N	\N
482	350	张晓波	设计部	主任工程师			f	2025-04-19 00:00:00	2025-05-09 07:19:14.597872	\N	14	\N	\N
483	350	周天文	设计部门	主任工程师			f	2024-03-12 11:53:24	2025-05-09 07:19:14.602502	\N	14	\N	\N
484	224	桂萍	采购	采购			f	2024-06-21 14:55:18	2025-05-09 07:19:14.643304	\N	14	\N	\N
485	176	巫和昕	设计	经理			f	2025-04-26 00:00:00	2025-05-09 07:19:14.648747	\N	14	\N	\N
486	177	端云	销售	销售			f	2024-05-05 12:58:30.999	2025-05-09 07:19:14.654062	\N	14	\N	\N
487	177	胡从焰	设计部门	技术经理			f	2024-02-27 10:23:51	2025-05-09 07:19:14.659257	\N	14	\N	\N
488	276	朱焱	采购部	采购经理			f	2025-03-08 00:00:00	2025-05-09 07:19:14.664464	\N	14	\N	\N
489	179	陈怡					f	2024-06-21 13:59:25	2025-05-09 07:19:14.669719	\N	14	\N	\N
490	180	陈林	设计部门	弱电工程师	13262655581		f	2024-02-22 12:42:19	2025-05-09 07:19:14.674485	\N	14	\N	\N
491	39	金晓俊	设计部门	主任工程师			f	2024-02-27 10:21:29	2025-05-09 07:19:14.679906	\N	14	\N	\N
492	39	盛令弢	设计部门	工程师			f	2024-03-16 16:38:09	2025-05-09 07:19:14.685959	\N	14	\N	\N
493	181	舒辉	弱电	主任工程师			f	2024-05-05 12:50:06	2025-05-09 07:19:14.691313	\N	14	\N	\N
494	182	钱程	技术	技术			f	2024-06-21 10:58:55.999	2025-05-09 07:19:14.696735	\N	14	\N	\N
495	183	梅小好	总经理	总经理			f	2024-06-21 13:56:46.999	2025-05-09 07:19:14.738444	\N	14	\N	\N
496	185	张旭东	设计部	主任工程师			f	2025-02-07 00:00:00	2025-05-09 07:19:14.744076	\N	14	\N	\N
497	186	徐良健	总经理	总经理			f	2025-04-11 00:00:00	2025-05-09 07:19:14.748835	\N	14	\N	\N
498	187	林常森	经理	销售经理			f	2024-05-05 12:37:25	2025-05-09 07:19:14.7535	\N	14	\N	\N
499	281	刘亚	总经理	总经理			f	2024-08-08 14:01:58.999	2025-05-09 07:19:14.758027	\N	14	\N	\N
500	282	邹飞	总经理	总经理	18521857787		f	2024-02-21 12:30:23	2025-05-09 07:19:14.76237	\N	14	\N	\N
501	188	陈立彦	项目部	项目经理			f	2025-03-22 00:00:00	2025-05-09 07:19:14.766804	\N	14	\N	\N
502	188	赵泽飞	项目部	项目经理			f	2025-03-22 00:00:00	2025-05-09 07:19:14.771383	\N	14	\N	\N
503	190	吴洁					f	2025-01-07 14:12:03	2025-05-09 07:19:14.775777	\N	14	\N	\N
504	192	冯剑	设计部	技术			f	2025-03-22 00:00:00	2025-05-09 07:19:14.780238	\N	14	\N	\N
505	192	李兵	技术	经理			f	2024-08-08 13:13:30	2025-05-09 07:19:14.78483	\N	14	\N	\N
506	192	林志明	设计部	技术			f	2025-03-22 00:00:00	2025-05-09 07:19:14.789709	\N	14	\N	\N
507	288	陈刘祥	销售	销售			f	2024-05-05 12:54:23	2025-05-09 07:19:14.794648	\N	14	\N	\N
508	288	付言新	总经理	总经理	18616029812		f	2024-10-09 13:47:48.999	2025-05-09 07:19:14.799721	\N	14	\N	\N
509	194	黄薛娇	采购	经理			f	2024-08-08 14:52:45	2025-05-09 07:19:14.847222	\N	14	\N	\N
510	195	王炜					f	2025-02-17 00:00:00	2025-05-09 07:19:14.855354	\N	14	\N	\N
511	196	付海涛	设计部门	技术			f	2024-09-21 16:06:52	2025-05-09 07:19:14.868408	\N	14	\N	\N
512	196	周心一	采购部门	采购经理			f	2024-03-21 15:47:48	2025-05-09 07:19:14.877105	\N	14	\N	\N
513	196	周羽	项目部	项目经理			f	2025-03-22 00:00:00	2025-05-09 07:19:14.947518	\N	14	\N	\N
514	197	郑国慧	总经理	经理			f	2025-02-22 00:00:00	2025-05-09 07:19:15.043283	\N	14	\N	\N
515	198	文海					f	2024-11-12 16:07:07	2025-05-09 07:19:15.048795	\N	14	\N	\N
516	199	薛晨鑫	经营部	经理			f	2025-03-15 00:00:00	2025-05-09 07:19:15.144367	\N	14	\N	\N
517	199	赵展鹏	经营部	工程师			f	2025-02-22 00:00:00	2025-05-09 07:19:15.239369	\N	14	\N	\N
518	200	陈志龙	经理	副总经理			f	2024-05-05 13:04:54	2025-05-09 07:19:15.24778	\N	14	\N	\N
519	201	黄攀	技术	主任工程师			f	2024-05-05 12:31:28	2025-05-09 07:19:15.339673	\N	14	\N	\N
520	201	朱逸飞	设计部门	主任工程师	18621671757		f	2024-02-21 14:32:05.999	2025-05-09 07:19:15.346116	\N	14	\N	\N
521	202	汪加成	采购	经理			f	2024-09-14 11:49:27	2025-05-09 07:19:15.35186	\N	14	\N	\N
522	206	宋治军	总经理	经理			f	2025-02-22 00:00:00	2025-05-09 07:19:15.358029	\N	14	\N	\N
523	373	张小宁					f	2025-01-07 15:30:26	2025-05-09 07:19:15.363859	\N	14	\N	\N
524	207	刘强（挂靠）	项目部门	项目经理			f	2024-03-21 16:08:27.999	2025-05-09 07:19:15.369933	\N	14	\N	\N
525	208	彭俊	设计部	经理			f	2025-03-14 00:00:00	2025-05-09 07:19:15.377442	\N	14	\N	\N
526	209	朱艳伟	技术	技术			f	2024-06-21 11:43:31	2025-05-09 07:19:15.38267	\N	14	\N	\N
527	210	周永鹤	采购部	采购			f	2024-03-12 11:30:51	2025-05-09 07:19:15.388661	\N	14	\N	\N
528	211	冯一	项目部	项目经理			f	2024-07-05 15:03:36	2025-05-09 07:19:15.393383	\N	14	\N	\N
529	213	朱丹	设计部	工程师			f	2025-03-01 00:00:00	2025-05-09 07:19:15.399747	\N	14	\N	\N
530	214	高源	设计部	弱电工程师			f	2025-02-17 00:00:00	2025-05-09 07:19:15.405397	\N	14	\N	\N
531	214	张辉	设计	主任工程师			f	2025-04-26 00:00:00	2025-05-09 07:19:15.443516	\N	14	\N	\N
532	215	陈华林	设计部	弱电工程师			f	2025-02-07 00:00:00	2025-05-09 07:19:15.451422	\N	14	\N	\N
533	215	丁愉豪	设计部	工程师			f	2025-04-19 00:00:00	2025-05-09 07:19:15.461174	\N	14	\N	\N
534	215	龚俊瑜	采购部	经理			f	2025-04-26 00:00:00	2025-05-09 07:19:15.469538	\N	14	\N	\N
535	215	焦峰	经营部	经理			f	2025-03-14 00:00:00	2025-05-09 07:19:15.475924	\N	14	\N	\N
536	215	梁晓君	技术	经理			f	2024-05-05 12:55:23	2025-05-09 07:19:15.481139	\N	14	\N	\N
537	215	曲文博	项目部	项目经理			f	2025-03-22 00:00:00	2025-05-09 07:19:15.485966	\N	14	\N	\N
538	215	张东伟	项目部	项目经理			f	2025-04-11 00:00:00	2025-05-09 07:19:15.490514	\N	14	\N	\N
539	215	郑梓璇	华南技术	技术			f	2024-10-09 12:47:44	2025-05-09 07:19:15.495365	\N	14	\N	\N
540	216	邬丹					f	2024-05-25 15:34:37	2025-05-09 07:19:15.500012	\N	14	\N	\N
541	217	卢荣祥	设计	主任工程师			f	2025-04-26 00:00:00	2025-05-09 07:19:15.504404	\N	14	\N	\N
542	219	王佳斌	设计部	主任工程师			f	2025-03-22 00:00:00	2025-05-09 07:19:15.50912	\N	14	\N	\N
543	219	王微微	设计部门	主任工程师			f	2024-02-27 11:03:30	2025-05-09 07:19:15.539084	\N	14	\N	\N
544	220	姜涛	设计部	技术			f	2025-04-19 00:00:00	2025-05-09 07:19:15.545208	\N	14	\N	\N
545	223	瞿迪	设计部	主任工程师			f	2025-03-22 00:00:00	2025-05-09 07:19:15.550571	\N	14	\N	\N
546	223	闻锋	设计部	主任工程师			f	2025-02-07 00:00:00	2025-05-09 07:19:15.555711	\N	14	\N	\N
547	223	徐楷程	设计部	工程师			f	2025-03-01 00:00:00	2025-05-09 07:19:15.56172	\N	14	\N	\N
548	225	陆经纬	采购部门	采购经理	13818446992		f	2024-02-22 13:01:36	2025-05-09 07:19:15.566855	\N	14	\N	\N
549	305	祁祯	总经理	总经理			f	2024-02-27 10:32:49	2025-05-09 07:19:15.571907	\N	14	\N	\N
550	221	王磊	项目部	项目经理			f	2025-04-19 00:00:00	2025-05-09 07:19:15.576756	\N	14	\N	\N
551	226	徐骏	采购部	采购经理			f	2024-03-12 12:06:09	2025-05-09 07:19:15.5814	\N	14	\N	\N
552	227	胡铭杰	项目部门	经理			f	2024-03-21 15:53:21	2025-05-09 07:19:15.585859	\N	14	\N	\N
553	228	贾雪凤	采购部门	采购	13063493310		f	2024-02-21 15:04:51.999	2025-05-09 07:19:15.590277	\N	14	\N	\N
554	228	靳丽	采购部门	采购经理	15221770849		f	2024-02-22 12:47:58.999	2025-05-09 07:19:15.594912	\N	14	\N	\N
555	229	傅宏伟	采购部	采购经理			f	2024-03-12 11:43:29	2025-05-09 07:19:15.599647	\N	14	\N	\N
556	229	王毅涛	设计部	工程师			f	2025-02-22 00:00:00	2025-05-09 07:19:15.640191	\N	14	\N	\N
557	229	奚志坚	设计部门	技术			f	2024-03-12 11:43:19	2025-05-09 07:19:15.646974	\N	14	\N	\N
558	230	申时政	技术	技术			f	2024-06-18 10:59:44	2025-05-09 07:19:15.652221	\N	14	\N	\N
559	231	杨冰峰	项目部	项目经理			f	2025-03-08 00:00:00	2025-05-09 07:19:15.658024	\N	14	\N	\N
560	311	周杰	销售	销售经理			f	2025-04-19 00:00:00	2025-05-09 07:19:15.663912	\N	14	\N	\N
561	233	戴卓莹	设计部门	主任工程师	13818663996		f	2024-02-21 14:59:01	2025-05-09 07:19:15.669811	\N	14	\N	\N
562	233	刘宗怡	设计	弱电工程师			f	2025-04-26 00:00:00	2025-05-09 07:19:15.675281	\N	14	\N	\N
563	234	庄彦	设计部门	主任工程师	13917339483		f	2024-02-21 15:11:15	2025-05-09 07:19:15.681105	\N	14	\N	\N
564	237	刘鸿儒	设计部	经理			f	2024-03-21 16:02:55	2025-05-09 07:19:15.686955	\N	14	\N	\N
565	237	徐强	设计部门	主任设计师	15900607045		f	2024-02-21 12:22:50	2025-05-09 07:19:15.693869	\N	14	\N	\N
566	238	俞晖	设计部	主任工程师			f	2025-02-26 00:00:00	2025-05-09 07:19:15.700024	\N	14	\N	\N
567	239	柴经理	采购部	采购			f	2025-02-26 00:00:00	2025-05-09 07:19:15.70604	\N	14	\N	\N
568	240	朱永兴					f	2024-12-28 13:45:28	2025-05-09 07:19:15.711424	\N	14	\N	\N
569	241	关鹏	经营部	经理			f	2025-03-14 00:00:00	2025-05-09 07:19:15.743172	\N	14	\N	\N
570	204	俞春磊	技术	技术			f	2024-07-05 14:48:23	2025-05-09 07:19:15.75018	\N	14	\N	\N
571	200	俞春磊	设计部门	技术			f	2024-03-29 14:17:29	2025-05-09 07:19:15.756166	\N	14	\N	\N
572	244	江勤平	设计部门	主任工程师			f	2024-03-21 15:45:33	2025-05-09 07:19:15.762581	\N	14	\N	\N
573	244	刘健	设计部门	主任工程师			f	2024-03-21 15:46:12	2025-05-09 07:19:15.767405	\N	14	\N	\N
574	246	刘思成	项目部	技术			f	2024-08-21 11:58:03	2025-05-09 07:19:15.772342	\N	14	\N	\N
575	248	史伟杰	设计部门	工程师			f	2024-02-27 11:43:20	2025-05-09 07:19:15.777107	\N	14	\N	\N
576	248	庄妍华	设计部门	主任工程师			f	2024-02-27 11:43:33	2025-05-09 07:19:15.782157	\N	14	\N	\N
577	93	李欣	智能化	经理	15818541034		f	2025-03-01 00:00:00	2025-05-09 07:22:51.270803	\N	17	\N	\N
578	94	王如郑	招采	经理			f	2025-04-12 00:00:00	2025-05-09 07:22:51.280817	\N	17	\N	\N
579	95	李标					f	2024-02-23 00:00:00	2025-05-09 07:22:51.339087	\N	17	\N	\N
580	95	李超华		弱电工程师			f	2024-02-23 00:00:00	2025-05-09 07:22:51.346352	\N	17	\N	\N
581	95	王永海		电气设计总工			f	2024-02-23 00:00:00	2025-05-09 07:22:51.353851	\N	17	\N	\N
582	95	周登登		电气工程师			f	2024-02-23 00:00:00	2025-05-09 07:22:51.360379	\N	17	\N	\N
583	96	陈昊	采购	副总经理	13922200737		f	2024-08-19 11:28:38.999	2025-05-09 07:22:51.37004	\N	17	\N	\N
584	98	黄晓光	综合	总经理		546642854@qq.com	f	2024-10-19 17:02:44	2025-05-09 07:22:51.377192	\N	17	\N	\N
585	99	张经理	采购	商务	13710201014		f	2025-03-08 00:00:00	2025-05-09 07:22:51.384408	\N	17	\N	\N
586	100	刘志兴	项目部	项目经理	13632779376		f	2024-08-19 11:04:34.999	2025-05-09 07:22:51.390755	\N	17	\N	\N
587	101	杨文武	智能化	工程师	13926402199		f	2025-03-09 00:00:00	2025-05-09 07:22:51.396246	\N	17	\N	\N
588	102	周渝杰	设计	设计	18875129202		f	2024-10-09 14:54:03	2025-05-09 07:22:51.403414	\N	17	\N	\N
589	105	刘嵩	技术	工程师	13652364267		f	2025-01-11 17:27:43	2025-05-09 07:22:51.408895	\N	17	\N	\N
590	107	秦家俊	智能化	经理			f	2025-04-26 00:00:00	2025-05-09 07:22:51.414404	\N	17	\N	\N
591	109	宋洋洋	综合	总经理			f	2024-12-10 16:25:00	2025-05-09 07:22:51.419814	\N	17	\N	\N
592	111	曾帅	销售部	总监			f	2025-04-19 00:00:00	2025-05-09 07:22:51.443398	\N	17	\N	\N
593	112	裴小印	销售	经理	15013037131		f	2024-09-28 15:26:05	2025-05-09 07:22:51.449412	\N	17	\N	\N
594	112	李莉	总经办	总经理			f	2024-02-23 00:00:00	2025-05-09 07:22:51.456568	\N	17	\N	\N
595	114	蔡卫贤	销售	经理	15347413574		f	2024-11-16 16:51:17	2025-05-09 07:22:51.462819	\N	17	\N	\N
596	115	张莲苓	商务	采购	13337676392		f	2024-09-28 15:33:04	2025-05-09 07:22:51.469385	\N	17	\N	\N
597	117	张炳伙	售前	设计师	18565698829		f	2024-12-21 13:01:03	2025-05-09 07:22:51.474814	\N	17	\N	\N
598	118	陈涛		设计师			f	2024-02-23 00:00:00	2025-05-09 07:22:51.480454	\N	17	\N	\N
599	118	陈映宏		高级工程师			f	2024-02-23 00:00:00	2025-05-09 07:22:51.486423	\N	17	\N	\N
600	118	黄志炜	智能化	主任			f	2025-03-21 00:00:00	2025-05-09 07:22:51.491749	\N	17	\N	\N
601	119	谌贻涛	智能化	工程师			f	2025-03-21 00:00:00	2025-05-09 07:22:51.498208	\N	17	\N	\N
602	119	焦培荣	智能化	总工			f	2025-04-12 00:00:00	2025-05-09 07:22:51.503734	\N	17	\N	\N
603	120	程龙		弱电工程师			f	2024-03-04 00:00:00	2025-05-09 07:22:51.509879	\N	17	\N	\N
604	120	丁瑞斌					f	2024-03-04 00:00:00	2025-05-09 07:22:51.543813	\N	17	\N	\N
605	104	黄宇清	第三机电所	总工			f	2025-03-08 00:00:00	2025-05-09 07:22:51.550902	\N	17	\N	\N
606	121	夏萌	采购	采购	18934592951		f	2025-03-08 00:00:00	2025-05-09 07:22:51.560422	\N	17	\N	\N
607	123	王巍	智能化设计部	经理	13528884452		f	2024-09-07 14:20:36	2025-05-09 07:22:51.567175	\N	17	\N	\N
608	124	陈新	采购	经理	13806041966		f	2024-10-09 14:48:39	2025-05-09 07:22:51.572654	\N	17	\N	\N
609	125	方奕广	设计	经理	13535359905		f	2024-10-09 14:50:47	2025-05-09 07:22:51.580032	\N	17	\N	\N
610	126	李慧敏	综合	总经理	18060919169		f	2024-09-28 16:04:05	2025-05-09 07:22:51.585464	\N	17	\N	\N
611	127	綦刚	市场部	总监	18159883866		f	2024-09-28 15:57:39.999	2025-05-09 07:22:51.592295	\N	17	\N	\N
612	129	张兴	深圳分公司	销售经理	18701952969		f	2024-09-14 16:27:03	2025-05-09 07:22:51.598182	\N	17	\N	\N
613	381	安建月		副总工			f	2024-02-23 00:00:00	2025-05-09 07:22:51.60502	\N	17	\N	\N
614	381	李进保		工程师			f	2024-02-23 00:00:00	2025-05-09 07:22:51.611552	\N	17	\N	\N
615	381	李新鑫		采购总监			f	2024-02-23 00:00:00	2025-05-09 07:22:51.63921	\N	17	\N	\N
616	381	李莹	医疗部售前	工程师			f	2025-04-07 00:00:00	2025-05-09 07:22:51.646403	\N	17	\N	\N
617	381	李振辉		项目经理			f	2024-02-23 00:00:00	2025-05-09 07:22:51.653264	\N	17	\N	\N
618	381	刘良栾		项目经理			f	2024-02-23 00:00:00	2025-05-09 07:22:51.662003	\N	17	\N	\N
619	381	彭建肖		设计经理			f	2024-02-23 00:00:00	2025-05-09 07:22:51.669445	\N	17	\N	\N
620	381	帅进	技术部	总监	13510633210		f	2024-09-28 15:52:04	2025-05-09 07:22:51.67694	\N	17	\N	\N
621	381	唐经理	采购	经理			f	2025-04-26 00:00:00	2025-05-09 07:22:51.683128	\N	17	\N	\N
622	381	王康		技术经理			f	2024-02-23 00:00:00	2025-05-09 07:22:51.689733	\N	17	\N	\N
623	381	谢晓云					f	2024-02-23 00:00:00	2025-05-09 07:22:51.69662	\N	17	\N	\N
624	381	徐道锦	政企部	销售	15889713109		f	2025-03-29 00:00:00	2025-05-09 07:22:51.70174	\N	17	\N	\N
625	381	张韬		项目经理			f	2024-02-23 00:00:00	2025-05-09 07:22:51.707136	\N	17	\N	\N
626	130	陈爱莲		电气设计总工			f	2024-02-23 00:00:00	2025-05-09 07:22:51.744833	\N	17	\N	\N
627	131	徐松岩	智能化	总工			f	2025-04-26 00:00:00	2025-05-09 07:22:51.750661	\N	17	\N	\N
628	135	胡程序	工程部	项目经理			f	2025-04-26 00:00:00	2025-05-09 07:22:51.756002	\N	17	\N	\N
629	135	林嘉豪	售前	总监			f	2025-04-07 00:00:00	2025-05-09 07:22:51.761208	\N	17	\N	\N
630	136	黄平旗	采购	采购	15361580882		f	2024-12-07 13:34:01	2025-05-09 07:22:51.766429	\N	17	\N	\N
631	138	梁宝桦	第一湾区设计院	设计师	15913155965		f	2024-09-14 16:48:50	2025-05-09 07:22:51.77178	\N	17	\N	\N
632	138	刘汉伟	智能化	副总工	13926418655		f	2025-03-01 00:00:00	2025-05-09 07:22:51.776734	\N	17	\N	\N
633	139	蔡涛		技术工程师			f	2024-02-23 00:00:00	2025-05-09 07:22:51.78133	\N	17	\N	\N
634	139	陈勇		售前设计			f	2024-02-23 00:00:00	2025-05-09 07:22:51.786379	\N	17	\N	\N
635	139	赵剑					f	2024-02-23 00:00:00	2025-05-09 07:22:51.791885	\N	17	\N	\N
636	141	张坤成	采购	副总			f	2025-03-21 00:00:00	2025-05-09 07:22:51.842918	\N	17	\N	\N
637	142	李进	设计部	经理	18681507600		f	2024-08-31 11:11:04	2025-05-09 07:22:51.848694	\N	17	\N	\N
638	143	樊勇	综合	总经理	13480616429		f	2024-11-20 15:27:13.999	2025-05-09 07:22:51.853872	\N	17	\N	\N
639	144	陈少彬	采购	总监	13760482739		f	2025-01-11 18:14:21	2025-05-09 07:22:51.859292	\N	17	\N	\N
640	146	李维	政企事业部	经理	18566686996		f	2024-08-31 11:18:17	2025-05-09 07:22:51.864743	\N	17	\N	\N
641	146	肖阳陵	设计部	智能化	13265549090		f	2024-08-31 12:35:12	2025-05-09 07:22:51.871962	\N	17	\N	\N
642	147	崔华		售前工程师			f	2024-02-23 00:00:00	2025-05-09 07:22:51.8779	\N	17	\N	\N
643	149	李琪	综合	总经理	18088885755		f	2025-03-01 00:00:00	2025-05-09 07:22:51.884521	\N	17	\N	\N
644	150	彭经理	工程	经理	15999565911		f	2024-10-09 15:03:49	2025-05-09 07:22:51.890947	\N	17	\N	\N
645	152	李工	智能化项目负责人	经理	18565686904		f	2025-01-04 15:36:23	2025-05-09 07:22:51.895659	\N	17	\N	\N
646	153	陈升城		主创建筑师			f	2024-02-23 00:00:00	2025-05-09 07:22:51.900229	\N	17	\N	\N
647	153	严定刚					f	2024-02-23 00:00:00	2025-05-09 07:22:51.905192	\N	17	\N	\N
648	155	柯创伟	销售	销售经理			f	2025-04-19 00:00:00	2025-05-09 07:22:51.942691	\N	17	\N	\N
649	155	孟凡涛	智能化技术部	经理			f	2025-04-12 00:00:00	2025-05-09 07:22:51.948277	\N	17	\N	\N
650	157	邹莉	采购	采购	13510574103		f	2024-11-11 21:04:18	2025-05-09 07:22:51.95349	\N	17	\N	\N
651	162	曹焕	智能化	主任	13480656591		f	2024-12-13 23:57:25	2025-05-09 07:22:51.958384	\N	17	\N	\N
652	162	何雁	智能化	所长	13510288186		f	2025-02-17 00:00:00	2025-05-09 07:22:51.963318	\N	17	\N	\N
653	163	杨彩荣	采购部门	经理			f	2024-02-21 00:00:00	2025-05-09 07:22:51.96784	\N	17	\N	\N
654	164	钟经理	工程	项目经理	18310138521		f	2025-03-01 00:00:00	2025-05-09 07:22:51.972455	\N	17	\N	\N
655	166	邹翔龙	采购	经理	18666371963		f	2024-08-24 15:28:20.999	2025-05-09 07:22:51.977095	\N	17	\N	\N
656	89	李梦佳	系统集成事业部	商务经理	15720602030		f	2024-09-14 16:37:37	2025-05-09 07:22:51.981471	\N	17	\N	\N
657	89	王浩文	项目	项目经理	18565026655		f	2025-03-08 00:00:00	2025-05-09 07:22:51.98635	\N	17	\N	\N
658	168	陈经理	采购	采购经理	13363091682		f	2024-08-24 15:41:57	2025-05-09 07:22:51.99084	\N	17	\N	\N
659	169	文杰	设计部	设计部	18194090730		f	2024-09-21 14:15:24	2025-05-09 07:22:52.03912	\N	17	\N	\N
660	171	王琦	综合	总经理	13641407642		f	2024-11-09 15:43:02	2025-05-09 07:22:52.045448	\N	17	\N	\N
661	171	周小强	智能化	教授高级工程师	13923800500		f	2025-02-23 00:00:00	2025-05-09 07:22:52.051236	\N	17	\N	\N
676	486	张真福		总经理	15596679133		f	2025-05-16 03:57:05.894611	2025-05-16 03:57:05.894614		7	f	f
662	471	刘林	技术中心	弱电经理	13438921756		t	2025-05-11 14:25:54.368567	2025-05-11 14:25:54.382393		13	\N	\N
663	472	韩飞	总包	总包	13703300332		f	2025-05-14 01:36:14.208844	2025-05-14 01:36:14.208847		20	\N	\N
664	472	许涛	业主方	上海松江物业工程部长	13851615815		f	2025-05-14 01:38:11.087538	2025-05-14 01:38:11.087541		20	\N	\N
665	473	陈琦	业主方	业主方	13564889806		f	2025-05-14 01:48:29.271466	2025-05-14 01:48:29.271468		20	\N	\N
666	474	王鑫	总包	总包	18021519922		f	2025-05-14 01:52:05.343349	2025-05-14 01:52:05.343352		20	\N	\N
667	475	焦 通	总包	总包	15021941950		f	2025-05-14 01:58:54.544342	2025-05-14 01:58:54.544345		20	\N	\N
668	476	戴斌	工程部	工程部经理	13601840893		f	2025-05-14 02:03:28.269447	2025-05-14 02:03:28.26945		20	\N	\N
669	478	须工	总包	总包	18202188031		f	2025-05-14 02:33:41.694481	2025-05-14 02:33:41.694484		20	\N	\N
670	479	傅颖毅	总包	总包	13816764728		f	2025-05-14 02:38:36.563022	2025-05-14 02:38:36.563024		20	\N	\N
671	480	房保飞	工程部	工程部	15317283152		f	2025-05-14 02:42:17.840174	2025-05-14 02:42:40.050398		20	\N	\N
672	481	李家俊	业主方	业主方	13817667467		f	2025-05-14 02:49:28.04582	2025-05-14 02:49:28.045822		20	\N	\N
673	482	鲍磊	总包	总包	13262968899		f	2025-05-14 02:53:56.157208	2025-05-14 02:53:56.157213		20	\N	\N
674	474	孙经理	安保	安保经理	13915557556		f	2025-05-14 05:44:16.766062	2025-05-14 05:44:16.766063		20	\N	\N
119	435	Kevin			37491461		f	2025-04-18 00:00:00	2025-05-14 08:08:26.53836	None	2	\N	\N
675	483	陈浩	武装部军事课	参谋长	17501639843		f	2025-05-15 02:39:54.396996	2025-05-15 02:39:54.396999		20	\N	\N
677	486	沈杰		产品方案技术负责人	13817331415		f	2025-05-16 03:58:29.764569	2025-05-16 03:58:29.764572		7	f	f
679	256	潘继峰	设施管理部	弱电组副组长	13636673176		f	2025-05-19 02:14:07.586944	2025-05-19 02:14:07.586946		20	f	f
680	477	俞工	工程部	工程部经理	13795219543		f	2025-05-19 09:30:41.844827	2025-05-19 09:30:41.844829		20	f	f
681	215	蒯乃骏	项目部	项目经理			f	2025-05-21 06:27:17.40915	2025-05-21 06:27:17.409154		14	f	f
682	129	李冬	总经理	总经理			f	2025-05-21 06:54:21.152652	2025-05-21 06:54:21.152654		14	f	f
683	478	方俊斌	工程部	工程部经理	13896898978		f	2025-05-21 10:13:06.365327	2025-05-21 10:13:06.365329		20	f	f
684	477	张宇	弱电	负责人	13122003777		f	2025-05-23 01:40:53.157975	2025-05-23 01:40:53.157977		7	f	f
685	494	徐畅慧	技术不	技术			f	2025-05-23 04:17:22.48948	2025-05-23 04:17:22.489482		14	f	f
686	496	李冬	管理部	总经理			t	2025-05-28 02:57:23.241306	2025-05-28 02:57:23.27125		19	f	f
687	496	贺花明	财务部	财务经理			f	2025-05-28 02:57:53.259238	2025-05-28 02:57:53.259239		19	f	f
688	496	张国栋	销售部	销售经理			f	2025-05-28 02:59:17.8845	2025-05-28 02:59:17.884502		19	f	f
689	497	张兴	销售部	销售经理			f	2025-05-28 03:01:00.454282	2025-05-28 03:01:00.454284		19	f	f
690	498	邹飞	管理部	总经理			f	2025-05-28 03:03:10.795736	2025-05-28 03:03:10.795737		19	f	f
691	499	付言新	管理部	总经理			f	2025-05-28 03:04:18.769828	2025-05-28 03:04:18.76983		19	f	f
693	500	邹娟	销售部	销售经理			f	2025-05-28 03:07:17.585331	2025-05-28 03:07:17.585332		19	f	f
694	501	裴小印	管理部	副总经理			f	2025-05-28 03:10:01.472487	2025-05-28 03:10:01.47249		19	f	f
695	502	李波	管理部	总经理			f	2025-05-28 03:11:34.201698	2025-05-28 03:11:34.201701		19	f	f
696	503	王超	管理部	总经理			f	2025-05-28 03:16:20.15575	2025-05-28 03:16:20.155751		19	f	f
697	504	王秀凤	管理部	总经理			f	2025-05-28 03:17:48.553431	2025-05-28 03:17:48.553433		19	f	f
698	505	花伟	销售部	销售经理			f	2025-05-28 03:18:50.353513	2025-05-28 03:18:50.353515		19	f	f
699	506	宋洋洋	管理部	总经理			f	2025-05-28 03:20:03.324047	2025-05-28 03:20:03.324049		19	f	f
700	506	龚维	销售部	销售经理			f	2025-05-28 03:20:28.839675	2025-05-28 03:20:28.839677		19	f	f
701	507	魏凌	管理部	总经理			f	2025-05-28 08:28:40.043144	2025-05-28 08:28:40.043146		19	f	f
702	508	尤力	管理部	总经理			f	2025-05-28 08:29:45.258025	2025-05-28 08:29:45.258027		19	f	f
703	509	刘洪瑄	管理部	总经理			f	2025-05-28 08:31:03.843449	2025-05-28 08:31:03.843451		19	f	f
704	510	张群	管理部	总经理			f	2025-05-28 08:32:16.074142	2025-05-28 08:32:16.074144		19	f	f
706	511	孟宪福	管理部	总经理			f	2025-05-28 08:33:54.177843	2025-05-28 08:33:54.177845		19	f	f
707	512	王斌	管理部	总经理			f	2025-05-28 08:34:54.95791	2025-05-28 08:34:54.957912		19	f	f
708	513	李瑞	管理部	总经理			f	2025-05-28 08:35:57.093695	2025-05-28 08:35:57.093697		19	f	f
709	514	林常森	管理部	总经理			f	2025-05-28 08:37:37.042377	2025-05-28 08:37:37.04238		19	f	f
710	515	张炜	管理部	总经理			f	2025-05-28 08:38:49.120795	2025-05-28 08:38:49.120796		19	f	f
711	517	施旻			13918445882		f	2025-05-30 04:39:21.973877	2025-05-30 04:39:21.973879		7	f	f
712	221	林瑾	采购部	采购经理			f	2025-05-30 06:14:10.461421	2025-05-30 06:14:10.461423		14	f	f
713	350	叶海茂	设计部-数创	主任工程师			f	2025-05-30 06:20:20.909997	2025-05-30 06:20:20.909999		14	f	f
192	359	黄小兵	设计部门	经理			f	2025-03-14 00:00:00	2025-06-03 10:57:58.456503	\N	13	\N	\N
193	359	李小将	设计部门	技术经理			f	2025-03-07 00:00:00	2025-06-03 10:57:58.456503	\N	13	\N	\N
194	359	叶中贵	设计部门	弱电主任工程师			f	2025-02-15 00:00:00	2025-06-03 10:57:58.456503	\N	13	\N	\N
195	359	余沛霖	设计部门	技术经理	18628333765		f	2024-02-21 11:52:16	2025-06-03 10:57:58.456503	\N	13	\N	\N
714	359	叶昌金	设计部	设计经理			t	2025-06-03 10:57:58.424942	2025-06-03 10:57:58.458701		13	f	f
715	518	戴涛	技术				f	2025-06-04 02:54:29.596513	2025-06-04 02:54:29.596515		16	f	f
716	154	吴业强	采购	经理			f	2025-06-08 13:44:36.394269	2025-06-08 13:44:36.39427		17	f	f
717	142	肖阳陵	综合办	经理			f	2025-06-08 14:20:09.362498	2025-06-08 14:20:09.362499		17	f	f
718	381	时飞福	工程部	项目经理			f	2025-06-08 14:26:27.085868	2025-06-08 14:26:27.08587		17	f	f
719	288	付海军					f	2025-06-09 07:06:16.247649	2025-06-09 07:06:16.24765		14	f	f
720	521	王昀			18501650631		f	2025-06-10 02:14:05.853683	2025-06-10 02:14:05.853685		7	f	f
721	523	程经理					f	2025-06-13 04:50:40.615667	2025-06-13 04:50:40.615668		18	f	f
\.


--
-- TOC entry 4053 (class 0 OID 19650)
-- Dependencies: 278
-- Data for Name: dev_product_specs; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.dev_product_specs (id, dev_product_id, field_name, field_value, field_code) FROM stdin;
\.


--
-- TOC entry 4017 (class 0 OID 18287)
-- Dependencies: 242
-- Data for Name: dev_products; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.dev_products (id, category_id, subcategory_id, region_id, name, model, status, unit, retail_price, description, image_path, created_at, updated_at, owner_id, created_by, mn_code, pdf_path) FROM stdin;
4	3	13	1	E-BDA400B LT	E-BDA400B LT	研发中		\N		\N	2025-04-26 05:35:30.182401	2025-04-26 05:35:30.182407	\N	5	OAARPI9X	\N
5	3	13	1	E-BDA400B LT	E-BDA400B LT	研发中		\N		\N	2025-04-26 06:19:33.620345	2025-04-26 06:19:33.620354	\N	5	OAANAAAA	\N
1	3	13	1	E-BDA410B-LT	E-BDA410B-LT	研发中	套	\N	研发一款采用全新的壁挂机箱和内置10W放大模块的 同轴电缆放大器，具备和2W放大器一样的功能	\N	2025-04-26 01:35:27.145947	2025-04-26 05:35:56.955025	\N	5	OAA2NH71	\N
2	3	13	1	E-BDA410B-LT	E-BDA410B-LT	研发中	套	\N		\N	2025-04-26 02:04:11.235883	2025-04-26 05:35:56.955735	\N	5	OAARN0KA	\N
3	3	20	1	RFT-BDA410 LT/M	RFT-BDA410 LT/M	研发中	套	\N		\N	2025-04-26 03:10:38.83065	2025-04-26 05:35:56.956344	\N	5	OCAA4R71	\N
\.


--
-- TOC entry 4055 (class 0 OID 19654)
-- Dependencies: 280
-- Data for Name: dictionaries; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.dictionaries (id, type, key, value, is_active, sort_order, created_at, updated_at) FROM stdin;
1	role	admin	系统管理员	t	10	1745667318.529633	1745723213.991283
2	role	user	普通用户	t	20	1745716772.6006558	1745716772.600658
10	role	dealer	代理商	t	100	1745716772.6010182	1745716772.6010182
13	role	solution_manager	解决方案经理	t	130	1745716772.6038039	1745716963.2245371
14	role	sales_director	营销总监	t	140	1745716772.604226	1745717015.457986
17	role	product_manager	产品经理	t	170	1745716772.6054158	1745717037.573678
20	role	service_manager	服务经理	t	200	1745716772.606497	1745717151.156446
21	role	finace_director	财务总监	t	210	1745716772.606807	1746440593.9798028
18	role	customer_sales	客户销售	t	180	1745716772.605782	1746440605.527481
16	role	sales_manager	销售经理	t	160	1745716772.6050391	1746440616.621388
24	department	sales_dep	销售部	t	10	1746443555.595523	1746443555.595524
25	department	rd_dep	产品和解决方案部	t	20	1746443615.569504	1746443615.569506
26	department	service_dep	服务部	t	30	1746443643.629589	1746443643.629589
27	company	evertacsh_company	和源通信（上海）股份有限公司	t	10	1746443714.853514	1746443714.853515
12	role	business_admin	商务助理	t	120	1745716772.603283	1746443802.069152
28	role	ceo	总经理	t	220	1746443836.45206	1746443836.452061
29	department	finance_dep	财务部	t	40	1746489399.2419264	1746489399.2419312
30	company	recoo_company	上海瑞康通信科技有限公司	t	20	1746783363.4526942	1746783363.452697
31	company	dunli_company	敦力(南京)科技有限公司	t	30	1746783506.5529208	1746783506.552924
32	company	hangbo_company	浙江航博智能工程有限公司	t	40	1746783587.0208042	1746783587.0208097
33	company	focus_company	福淳智能科技(四川)有限公司	t	50	1746783704.9451404	1746783704.9451442
34	company	chunbo_company	上海淳泊信息科技有限公司	t	60	1746784102.0071158	1746784102.0071204
19	role	channel_manager	渠道经理	t	190	1745716772.60614	1748071365.134846
\.


--
-- TOC entry 4057 (class 0 OID 19658)
-- Dependencies: 282
-- Data for Name: event_registry; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.event_registry (id, event_key, label_zh, label_en, default_enabled, enabled, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4059 (class 0 OID 19662)
-- Dependencies: 284
-- Data for Name: feature_changes; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.feature_changes (id, version_id, change_type, module_name, title, description, priority, impact_level, affected_files, git_commits, test_status, test_notes, developer_id, developer_name, created_at, completed_at) FROM stdin;
\.


--
-- TOC entry 4033 (class 0 OID 19409)
-- Dependencies: 258
-- Data for Name: inventory; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) FROM stdin;
\.


--
-- TOC entry 4061 (class 0 OID 19668)
-- Dependencies: 286
-- Data for Name: inventory_transactions; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) FROM stdin;
\.


--
-- TOC entry 4063 (class 0 OID 19674)
-- Dependencies: 288
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.permissions (id, user_id, module, can_view, can_create, can_edit, can_delete) FROM stdin;
\.


--
-- TOC entry 4065 (class 0 OID 19678)
-- Dependencies: 290
-- Data for Name: pricing_order_approval_records; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.pricing_order_approval_records (id, pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval, fast_approval_reason) FROM stdin;
1	3	1	营销总监审批	营销总监	13	\N	\N	\N	f	\N
2	3	2	总经理审批	总经理	5	\N	\N	\N	f	\N
\.


--
-- TOC entry 4031 (class 0 OID 19310)
-- Dependencies: 256
-- Data for Name: pricing_order_details; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.pricing_order_details (id, pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, source_quotation_detail_id) FROM stdin;
10	2	定向耦合合路器	E-FH400-8	频率范围：400-430MHz 单端口承载功率：50W;插入损耗：≤12dB;接入端口数量：8;安装方式：机柜式;尺寸：2U	和源通信	套	ECM1B082CZ1	14120	14120	1	1	14120	quotation	8183
11	2	分路器	E-JF350/400-8	频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤10.5dB 接入端口数量：8 安装方式：机柜式 尺寸1U	和源通信	套	EDE1BU8xCZ1	4962	4962	1	1	4962	quotation	8184
12	2	上行信号剥离器	R-EVDC-BLST-U	频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U	和源通信	套	EDE1AU6xCZ1	4569	4569	4	1	18276	quotation	8185
13	2	下行信号剥离器	R-EVDC-BLST-D	频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U	和源通信	套	EDE1AD6xCZ1	4569	4569	4	1	18276	quotation	8186
14	2	双工器	E-SGQ400D	频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U	和源通信	套	EDULB4H1CZ1	7876	7876	1	1	7876	quotation	8187
15	2	智能光纤近端机	RFS-400 LT/M	频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台	和源通信	套	HYR2SI030	9876	9876	18	1	177768	quotation	8188
16	2	智能光纤远端直放站	RFT-BDA410 LT/M	频率范围：410-414/420-424MHz 带宽：≤4M 输出：10W 功能： 正面状态灯/网讯平台	和源通信	套	HYR3SI340	21250	21250	46	1	977500	quotation	8189
17	2	馈电模组	FDPower400	馈电功能模组    需搭配可扩展远端机;内置远端内向天馈提供电力;	和源通信	套	HYGF20000	1583	1583	46	1	72818	quotation	8190
18	2	馈电功率分配器	MAPD-2	频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信	套	HYCDF24Y	208	208	265	1	55120	quotation	8191
19	2	馈电定向耦合器	MADC-6	频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信	套	HYCCF34Y	246	246	379	1	93234	quotation	8192
20	2	智能室内全向吸顶天线	MA11	频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯	和源通信	套	HYAIOCL4Y	208	208	609	1	126672	quotation	8193
21	2	室外全向玻璃钢天线	E-ANTG 400	频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade	和源通信	套	EANLOMO5HR1	458	458	18	1	8244	quotation	8194
22	2	防爆型高防护全向天线	MAEX 10	频率范围: 350-470 MHz  增益: 0 dB   工作环境: 室内/室外   极化方向: 全向极化   功能: 防爆    IP防护: IP 65	和源通信	套	ACC3OOCXS	7200	7200	45	1	324000	quotation	8195
23	2	网讯网关服务 软件	NFX_GATW	用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理	和源通信	套	HYWG0NB1	12500	12500	1	1	12500	quotation	8196
24	2	网讯平台服务 软件	NFX_MAST_OPETN	-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权    4个信道机授权    100个终端授权	和源通信	套	HYWP0NC1	105000	105000	1	1	105000	quotation	8197
25	2	信道机接入许可	LS-NFX-RPT	网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析	和源通信	套	HYWSPNB1	2500	2500	4	1	10000	quotation	8198
26	2	远端站接入许可	LS-NFX-BDA	网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新	和源通信	套	HYWSRNB1	1500	1500	26	1	39000	quotation	8199
27	2	对讲机终端接入许可	LS-NFX-RAD	网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析	和源通信	套	HYWSTNB1	180	180	220	1	39600	quotation	8200
28	2	MOTOROLA 信道服务软件	GW-MOT-RPT	MOTOROLA信道机协议通信服务软件 功能 CP LCP 常规模式互通	和源通信	套	EHYW521066	36667	36667	1	1	36667	quotation	8201
29	1	超薄室内全向吸顶天线	MA10	频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65	和源通信	套	HYAIOCN4Y	142	63.9	1	0.45	63.9	manual	\N
30	1	功率分配器	EVPD-2 LT	频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;	和源通信	套	HYCDN24Y	142	63.9	1	0.45	63.9	manual	\N
31	1	定向耦合器	EVDC-6 LT	频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;	和源通信	套	HYCCN34Y	142	63.9	1	0.45	63.9	manual	\N
35	3	智能信道交换机	S1024	端口数量：24个  网线类型：3、4、5类双绞线   防雷等级：4级（6KV） 用途：CP、IP、LCP、系统监控配件/信道机	华三	套	OBJSVOTXQ01	780	312	1	0.4	312	manual	\N
36	3	馈电功率分配器	MAPD-2	频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信	套	HYCDF24Y	208	83.2	1	0.4	83.2	manual	\N
37	3	分路器	E-JF150-4	频率范围：130-170MHz 单端口承载功率：1W;插入损耗：≤7.0dB接入端口数量：4;安装方式：机柜式;	和源通信	套	HYMJC4010	2913	1165.2	1	0.4	1165.2	manual	\N
\.


--
-- TOC entry 4027 (class 0 OID 19227)
-- Dependencies: 252
-- Data for Name: pricing_orders; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.pricing_orders (id, order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at) FROM stdin;
2	PO202506-002	100	428	\N	\N	f	f	sales_key	draft	0	2141633	1	2141633	1	\N	\N	13	2025-06-13 05:51:19.771083	2025-06-13 05:51:19.802176
1	PO202506-001	621	691	523	523	f	f	channel_follow	pending	1	191.7	0.44999999999999996	191.7	0.44999999999999996	\N	\N	18	2025-06-13 03:28:43.549302	2025-06-13 08:37:55.168461
3	PO202506-003	624	694	284	112	f	f	sales_key	pending	1	1560.4	0.4	1560.4	0.4	\N	\N	5	2025-06-13 09:41:41.791958	2025-06-13 09:42:00.495018
\.


--
-- TOC entry 3999 (class 0 OID 18069)
-- Dependencies: 224
-- Data for Name: product_categories; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.product_categories (id, name, code_letter, description, created_at, updated_at) FROM stdin;
1	基站	B	核心交换层设备	2025-04-22 23:21:42.420247	2025-04-25 09:48:46.435854
2	合路平台	M		2025-04-24 07:46:40.759023	2025-04-25 09:49:25.406365
3	直放站	O		2025-04-24 07:49:44.922729	2025-04-25 09:49:33.407422
4	对讲机	R		2025-04-22 23:36:12.707747	2025-04-25 09:48:59.182939
6	功率/耦合器	S		2025-04-24 23:33:16.087046	2025-04-25 09:50:23.605273
7	天线	A		2025-04-24 23:33:33.804228	2025-04-25 09:50:30.187875
8	应用	L		2025-04-24 23:33:46.820829	2025-04-25 09:50:42.521192
10	配件	Y		2025-04-24 23:34:20.205585	2025-04-25 09:50:55.676612
\.


--
-- TOC entry 4021 (class 0 OID 18362)
-- Dependencies: 246
-- Data for Name: product_code_field_options; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.product_code_field_options (id, field_id, value, code, description, is_active, "position", created_at, updated_at) FROM stdin;
1	5	中国	A	自动生成的销售区域编码: 中国	t	0	2025-04-24 16:04:57.521844	2025-04-25 00:07:57.336829
2	6	亚太	B	自动生成的销售区域编码: 亚太	t	0	2025-04-24 16:05:25.275686	2025-04-25 00:05:25.275689
4	8	150-170MHz	L		t	0	2025-04-24 16:19:37.975551	2025-04-25 00:19:37.975559
5	9	越南	C	自动生成的销售区域编码: 越南	t	0	2025-04-24 16:29:11.019841	2025-04-25 00:29:11.019843
6	1	150MHZ	J		t	0	2025-04-24 23:22:49.52391	2025-04-25 07:22:49.523918
7	1	350MHz	R		t	0	2025-04-24 23:23:02.866403	2025-04-25 07:23:02.86641
8	2	12.5KHz	X		t	0	2025-04-24 23:23:39.933158	2025-04-25 07:23:39.933169
9	11	150MHz-170MHz	I		t	0	2025-04-25 05:08:00.668728	2025-04-25 13:08:00.668735
10	11	350MHz-370MHz	A	从产品 Mark1000 MAX 自动添加的指标	t	1	2025-04-25 05:08:42.179287	2025-04-25 13:08:42.179296
11	11	400-450MHz	B	从产品 Mark1000 MAX 自动添加的指标	t	2	2025-04-25 05:11:44.545207	2025-04-25 13:11:44.545215
12	11	800MHz-890MHz	C	从产品 Mark1000 MAX 自动添加的指标	t	3	2025-04-25 09:16:50.615312	2025-04-25 17:16:50.615323
13	12	25MHz	A	从产品 Mark1000 MAX 自动添加的指标	t	1	2025-04-25 09:20:06.256423	2025-04-25 17:20:06.256431
14	13	25	1	从产品 Mark1000 MAX 自动添加的规格值	t	1	2025-04-25 10:32:13.677906	2025-04-25 18:32:13.677909
15	14	150-170MHz	A	从产品 R-EVDC-BLST-U 自动添加的规格值	t	1	2025-04-25 13:51:56.17399	2025-04-25 21:51:56.173992
16	3	12500MHz	A	从产品 Mark3000BS 自动添加的指标	t	1	2025-04-25 15:57:08.488471	2025-04-25 23:57:08.488483
17	15	50欧姆	L		t	0	2025-04-25 23:58:56.032705	2025-04-26 07:58:56.032712
18	16	220V欧标	Q		t	0	2025-04-25 23:59:12.618438	2025-04-26 07:59:12.618447
19	17	412-416MHz（下行）/ 402-406MHz（上行）	A	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.154118	2025-04-26 09:35:27.154121
20	18	10W （40±1dBm）	A	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.15538	2025-04-26 11:44:33.223697
21	19	50±2dB	A	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.156259	2025-04-26 09:35:27.15626
22	20	0-30dB	A	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.157106	2025-04-26 09:35:27.157107
23	21	1dB	A	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.15799	2025-04-26 09:35:27.157991
24	22	≤6	A	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.158795	2025-04-26 09:35:27.158796
25	23	≤5 us	A	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.15964	2025-04-26 09:35:27.15964
26	24	≤3dB	A	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.161212	2025-04-26 09:35:27.161214
27	25	≥75dB	A	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.163617	2025-04-26 09:35:27.163618
28	26	≤1.5	A	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.164727	2025-04-26 09:35:27.16473
29	27	室内外 壁挂	室	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.16615	2025-04-26 09:35:27.166151
30	28	IP65	I	从产品 E-BDA410B-LT 自动添加的规格值	t	1	2025-04-26 01:35:27.167939	2025-04-26 09:35:27.16794
31	29	4MHz	M		t	0	2025-04-26 01:40:00.500847	2025-04-26 09:40:00.500855
32	17	420-424MHz（下行）/ 410-414MHz（上行）	N		t	0	2025-04-26 02:00:38.035383	2025-04-26 10:00:38.035386
33	30	420-424MHz（下行） / 410-414MHz（上行）	A	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:07:12.683679	2025-04-26 11:07:12.683687
34	41	50±2dB	A	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:29.997055	2025-04-26 11:09:29.997065
35	40	IP65	I	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:31.260702	2025-04-26 11:09:31.260709
36	39	壁挂 室外	壁	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:32.296944	2025-04-26 11:09:32.296951
37	38	≤1.5	A	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:33.508577	2025-04-26 11:09:33.508586
38	37	≥75dB	A	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:34.02539	2025-04-26 11:09:34.025404
39	36	≤3dB	A	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:35.294243	2025-04-26 11:09:35.294251
40	35	≤5 us	A	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:35.909568	2025-04-26 11:09:35.909572
41	33	1dB	A	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:37.584573	2025-04-26 11:09:37.584581
42	34	≤6	A	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:38.613985	2025-04-26 11:09:38.613993
43	32	0-30dB	A	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:39.695985	2025-04-26 11:09:39.695991
44	31	40±1dBm	A	从产品 RFT-BDA410 LT/M 自动添加的指标	t	1	2025-04-26 03:09:40.253768	2025-04-26 11:09:40.253777
45	42	1	A	从产品 RFT-BDA410 LT/M 自动添加的规格值	t	1	2025-04-26 03:10:38.841406	2025-04-26 11:23:02.910007
46	43	4MHz	F		t	0	2025-04-26 03:13:09.349774	2025-04-26 11:13:09.349785
\.


--
-- TOC entry 4067 (class 0 OID 19684)
-- Dependencies: 292
-- Data for Name: product_code_field_values; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.product_code_field_values (id, product_code_id, field_id, option_id, custom_value) FROM stdin;
\.


--
-- TOC entry 4013 (class 0 OID 18244)
-- Dependencies: 238
-- Data for Name: product_code_fields; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.product_code_fields (id, subcategory_id, name, code, description, field_type, "position", max_length, is_required, use_in_code, created_at, updated_at) FROM stdin;
1	1	频率范围	\N		spec	1	1	t	t	2025-04-24 13:03:54.647207	2025-04-24 21:03:54.647217
2	1	带宽	\N		spec	2	1	t	t	2025-04-24 13:04:21.945066	2025-04-24 21:04:21.945069
3	2	频率范围	\N		spec	1	1	t	t	2025-04-24 13:04:55.357523	2025-04-24 21:04:55.357534
4	2	带宽	\N		spec	2	1	t	t	2025-04-24 13:05:06.343133	2025-04-24 21:05:06.343143
5	1	中国	A		origin_location	1	1	t	t	2025-04-24 16:04:57.516746	2025-04-25 00:07:57.333313
6	1	亚太	B		origin_location	1	1	t	t	2025-04-24 16:05:25.270888	2025-04-25 00:05:25.275092
8	3	频率范围	\N		spec	1	1	t	t	2025-04-24 16:19:24.672162	2025-04-25 00:19:24.672169
9	3	越南	C		origin_location	1	1	t	t	2025-04-24 16:29:11.015821	2025-04-25 00:29:11.019415
10	2	颜色	\N		spec	3	1	t	t	2025-04-24 16:30:00.658174	2025-04-25 00:30:00.65818
11	4	频率范围	\N		spec	1	1	t	t	2025-04-25 05:07:12.816972	2025-04-25 13:13:07.301201
12	4	带宽	\N		spec	2	1	t	t	2025-04-25 05:13:33.315139	2025-04-25 13:13:33.315149
13	4	功率	\N	从产品 Mark1000 MAX 自动添加的规格字段	spec	3	1	f	t	2025-04-25 10:32:13.676155	2025-04-25 18:32:13.676159
14	16	频率范围	\N	从产品 R-EVDC-BLST-U 自动添加的规格字段	spec	1	1	f	t	2025-04-25 13:51:56.17179	2025-04-25 21:51:56.1718
15	4	阻抗	\N		spec	4	1	t	t	2025-04-25 23:58:31.339286	2025-04-26 07:58:31.339291
16	4	电源类型	\N		spec	5	1	t	t	2025-04-25 23:58:42.621219	2025-04-26 07:58:42.621227
17	13	工作频率	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	0	1	t	t	2025-04-26 01:35:27.152086	2025-04-26 11:04:14.472249
18	13	最大输出功率	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	1	1	t	t	2025-04-26 01:35:27.15482	2025-04-26 11:04:14.47293
19	13	上下行增益	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	2	1	t	t	2025-04-26 01:35:27.155789	2025-04-26 11:04:14.473233
20	13	增益调节范围	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	4	1	f	f	2025-04-26 01:35:27.15664	2025-04-26 11:04:14.473663
21	13	增益调节步进	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	5	1	f	f	2025-04-26 01:35:27.157521	2025-04-26 11:04:14.473848
22	13	噪声系数	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	6	1	f	f	2025-04-26 01:35:27.158359	2025-04-26 11:04:14.47404
23	13	时延	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	7	1	f	f	2025-04-26 01:35:27.159167	2025-04-26 11:04:14.474246
24	13	带内波动	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	8	1	f	f	2025-04-26 01:35:27.16021	2025-04-26 11:04:14.474426
25	13	上下行隔离度	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	9	1	f	f	2025-04-26 01:35:27.162642	2025-04-26 11:04:14.474604
26	13	驻波比	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	10	1	f	f	2025-04-26 01:35:27.164105	2025-04-26 11:04:14.474778
27	13	安装方式	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	12	1	t	t	2025-04-26 01:35:27.165595	2025-04-26 11:04:14.475446
28	13	防护等级	\N	从产品 E-BDA410B-LT 自动添加的规格字段	spec	11	1	f	f	2025-04-26 01:35:27.166878	2025-04-26 11:04:14.475253
29	13	工作带宽	\N		spec	3	1	t	t	2025-04-26 01:39:44.034071	2025-04-26 11:04:14.473475
30	20	工作频率	\N		spec	0	1	t	t	2025-04-26 02:13:26.25419	2025-04-26 11:14:23.559732
31	20	最大输出功率	\N		spec	1	1	t	t	2025-04-26 02:13:47.2431	2025-04-26 11:14:23.560384
32	20	增益调节范围	\N		spec	6	1	f	f	2025-04-26 02:14:03.887624	2025-04-26 11:14:23.561495
33	20	增益调节步进	\N		spec	7	1	t	f	2025-04-26 02:14:20.347429	2025-04-26 11:14:23.561687
34	20	噪声系数	\N		spec	8	1	f	f	2025-04-26 02:14:54.630395	2025-04-26 11:14:23.561891
35	20	时延	\N		spec	9	1	f	f	2025-04-26 02:19:55.576082	2025-04-26 11:14:23.562084
36	20	带内波动	\N		spec	10	1	f	f	2025-04-26 02:22:51.869022	2025-04-26 11:14:23.562278
37	20	上下行隔离度	\N		spec	11	1	f	f	2025-04-26 02:23:36.18269	2025-04-26 11:14:23.562446
38	20	驻波比	\N		spec	12	1	f	f	2025-04-26 02:23:48.633014	2025-04-26 11:14:23.562621
39	20	安装方式	\N		spec	4	1	t	t	2025-04-26 02:24:04.999174	2025-04-26 11:14:29.897417
40	20	防护等级	\N		spec	13	1	f	f	2025-04-26 02:24:20.281865	2025-04-26 11:14:23.562791
41	20	上下行增益	\N		spec	5	1	t	f	2025-04-26 02:25:40.380485	2025-04-26 11:14:23.561298
42	20	光口数量	\N	从产品 RFT-BDA410 LT/M 自动添加的规格字段	spec	3	1	f	t	2025-04-26 03:10:38.84042	2025-04-26 11:14:23.560886
43	20	带宽	\N		spec	2	1	t	t	2025-04-26 03:12:50.918148	2025-04-26 11:14:23.560636
44	60	工作频率	\N		spec	1	1	t	t	2025-04-26 03:26:44.269755	2025-04-26 11:26:44.269774
\.


--
-- TOC entry 4015 (class 0 OID 18258)
-- Dependencies: 240
-- Data for Name: product_codes; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.product_codes (id, product_id, category_id, subcategory_id, full_code, status, created_by, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4001 (class 0 OID 18080)
-- Dependencies: 226
-- Data for Name: product_regions; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.product_regions (id, name, code_letter, description, created_at) FROM stdin;
1	中国	A		2025-04-24 13:10:26.789192
2	亚太	B		2025-04-24 13:10:42.347967
3	欧洲	C	\N	2025-04-26 07:07:59.903453
4	北美	D	\N	2025-04-26 07:07:59.903759
5	南美	E	\N	2025-04-26 07:07:59.903792
6	中东	F	\N	2025-04-26 07:07:59.903815
7	非洲	G	\N	2025-04-26 07:07:59.903834
8	大洋洲	H	\N	2025-04-26 07:07:59.90385
\.


--
-- TOC entry 4009 (class 0 OID 18209)
-- Dependencies: 234
-- Data for Name: product_subcategories; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.product_subcategories (id, category_id, name, code_letter, description, display_order, created_at, updated_at) FROM stdin;
1	1	消防救援对讲通信基站	I		4	2025-04-23 14:04:52.359072	2025-04-25 13:03:05.491484
2	1	常规数字基站	G		2	2025-04-23 00:43:11.930733	2025-04-25 13:02:53.627153
3	1	智能集群基站	H		3	2025-04-24 12:04:20.734878	2025-04-25 13:02:53.627507
4	1	数字智能信道机	D		1	2025-04-24 23:36:16.496589	2025-04-25 13:02:53.626478
5	1	信道机虚拟集群功能许可	C		8	2025-04-24 23:36:49.636312	2025-04-25 13:03:18.168673
6	1	虚拟集群服务器主机	1		6	2025-04-24 23:36:58.811911	2025-04-25 13:03:19.699711
7	1	虚拟集群服务	E		7	2025-04-24 23:37:06.652735	2025-04-25 13:03:19.699974
8	1	广播多频点调频处理器	F		5	2025-04-24 23:37:20.290849	2025-04-25 13:03:19.699142
9	2	定向耦合合路器	A		7	2025-04-24 23:40:29.814626	2025-04-25 07:40:29.814633
10	2	分路器	B		4	2025-04-24 23:40:41.642009	2025-04-25 07:40:41.642015
11	2	多信道分合路器	C		6	2025-04-24 23:40:59.102466	2025-04-25 07:40:59.102473
12	2	信号剥离矩阵	D		3	2025-04-24 23:54:12.355449	2025-04-25 07:54:12.355451
13	3	常规射频直放站	A		1	2025-04-24 23:59:58.231543	2025-04-25 12:54:25.207024
14	3	智能光纤近端机	B		5	2025-04-25 00:00:04.335942	2025-04-25 08:17:55.381762
15	2	下行信号剥离器	E		2	2025-04-25 00:16:29.016775	2025-04-25 08:16:29.016783
16	2	上行信号剥离器	F		1	2025-04-25 00:16:55.163424	2025-04-25 08:16:55.163427
17	2	双工器	G		5	2025-04-25 00:17:11.658209	2025-04-25 08:17:11.658212
18	2	系统合路器	H		8	2025-04-25 00:17:20.953839	2025-04-25 08:17:20.953844
19	2	系统合路器 | 供电	I		9	2025-04-25 00:17:29.078049	2025-04-25 08:17:29.078055
20	3	智能光纤远端直放站	C		6	2025-04-25 00:18:02.140578	2025-04-25 08:18:02.140585
21	3	数字智能光纤近端机	D		2	2025-04-25 00:18:10.874507	2025-04-26 10:28:10.74907
22	3	数字智能光纤	E		4	2025-04-25 00:18:18.555414	2025-04-26 10:28:01.177677
23	3	数字智能光纤交织型远端直放站	F		3	2025-04-25 00:18:26.749583	2025-04-26 10:28:10.74971
24	3	馈电模组	G		8	2025-04-25 00:18:35.586307	2025-04-26 11:26:18.027559
25	6	定向耦合器	A		3	2025-04-25 00:36:50.161537	2025-04-25 08:36:50.161545
26	6	功率分配器	B		1	2025-04-25 00:36:57.786156	2025-04-25 08:36:57.786162
27	6	功率分配器	C		2	2025-04-25 00:37:08.360849	2025-04-25 08:37:08.360853
28	6	馈电功率分配器	D		4	2025-04-25 00:37:49.828753	2025-04-25 08:37:49.828759
29	6	馈电定向耦合器	E		5	2025-04-25 00:38:00.368274	2025-04-25 08:38:00.36828
30	7	室内全向吸顶天线	A		1	2025-04-25 00:38:18.705562	2025-04-25 08:38:18.705569
31	7	超薄室内全向吸顶天线	B		7	2025-04-25 00:38:26.623988	2025-04-25 08:38:26.623994
32	7	智能室内全向吸顶天线	C		5	2025-04-25 00:38:50.089886	2025-04-25 08:38:50.089892
33	7	智能室内蓝牙全向吸顶天线	D		6	2025-04-25 00:39:10.918878	2025-04-25 08:39:10.918884
34	7	室外定向板状天线	E		4	2025-04-25 00:39:18.454577	2025-04-25 08:39:18.454583
35	7	室外全向玻璃钢天线	F		2	2025-04-25 00:39:27.419476	2025-04-25 08:39:27.419479
36	7	室外八木定向天线	G		3	2025-04-25 00:39:38.820347	2025-04-25 08:39:38.820349
37	7	防爆型高防护全向天线	H		8	2025-04-25 00:39:46.887715	2025-04-25 08:39:46.887721
38	4	DMR常规对讲机	G		1	2025-04-25 00:40:18.125842	2025-04-25 09:54:16.257293
39	4	DMR智能对讲机	D		2	2025-04-25 00:40:26.330632	2025-04-25 09:54:35.551401
40	4	常规锂电池板	C		4	2025-04-25 00:40:36.17181	2025-04-25 08:40:36.171816
41	4	智能锂电池板	S		7	2025-04-25 00:40:43.687131	2025-04-25 09:54:54.369159
42	4	智能多联充电器	E		5	2025-04-25 00:40:53.825266	2025-04-25 08:40:53.82527
43	4	智能多联充电栈	F		6	2025-04-25 00:41:03.504495	2025-04-25 08:41:03.504505
44	4	多联充电柜	B		3	2025-04-25 00:41:09.771136	2025-04-25 09:55:17.908559
45	8	网关服务器主机	A		7	2025-04-25 00:41:48.804359	2025-04-25 08:41:48.804366
46	8	网讯网关服务 软件	B		12	2025-04-25 00:42:00.62644	2025-04-25 08:42:00.626446
47	8	平台服务器主机	C		4	2025-04-25 00:42:08.637057	2025-04-25 08:42:08.637062
48	8	网讯平台服务 软件	D		10	2025-04-25 00:42:16.832686	2025-04-25 08:42:16.832693
49	8	系统工作台	E		6	2025-04-25 00:42:24.612347	2025-04-25 08:42:24.612353
50	8	网讯平台在线巡检功能	F		9	2025-04-25 00:42:31.633327	2025-04-25 08:42:31.633333
51	8	网讯平台人员分布功能	G		8	2025-04-25 00:42:38.607732	2025-04-25 08:42:38.607739
52	8	网讯平台终端录音功能	H		11	2025-04-25 00:42:47.051361	2025-04-25 08:42:47.051366
53	8	运维工具包	I		14	2025-04-25 00:42:56.050105	2025-04-25 08:42:56.050112
54	8	消防救援通信系统资源管理	J		5	2025-04-25 00:43:02.403363	2025-04-25 08:43:02.403369
55	8	信道机接入许可	K		2	2025-04-25 00:43:09.774004	2025-04-25 08:43:09.774011
56	8	远端站接入许可	L		15	2025-04-25 00:43:15.775442	2025-04-25 08:43:15.775448
57	8	对讲机终端接入许可	M		3	2025-04-25 00:43:21.474339	2025-04-25 08:43:21.474345
58	8	蓝牙定位信标+许可证	N		13	2025-04-25 00:43:27.392745	2025-04-25 08:43:27.392751
59	8	MOTOROLA 信道服务软件	O		1	2025-04-25 00:43:33.973843	2025-04-25 08:43:33.973848
60	3	防爆光纤远端直放站	X		7	2025-04-26 03:26:10.330364	2025-04-26 11:26:18.026789
\.


--
-- TOC entry 4007 (class 0 OID 18193)
-- Dependencies: 232
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.products (id, type, category, product_mn, product_name, model, specification, brand, unit, retail_price, status, image_path, created_at, updated_at, owner_id, pdf_path) FROM stdin;
3	项目产品	基站	HYBC3XI30	消防救援对讲通信基站	MarkNET3000	频率范围：351-356/361-366MHz 带宽：≤5M      -基站控制器 -基站交换机 -三载波数模兼容信道 -三载波合路平台    合路输出：10W -功能：网讯平台	和源通信	套	125000.00	active	\N	2025-04-15 00:23:07.94176	2025-04-18 23:53:55.989533	5	\N
4	项目产品	基站	BC4I2X4NN	常规数字基站	Mark3000BS	频率范围：400-430MHz  数字/模拟二载波信道 -一体化合路剥离矩阵  可升级NetFlex网络服务  可升级虚拟集群	和源通信	套	48000.00	upcoming	\N	2025-04-15 00:23:07.941761	2025-04-22 00:11:34.764235	5	\N
5	项目产品	基站	BC4I3X4NN	常规数字基站	Mark3000BS	频率范围：400-430MHz  数字/模拟三载波信道 -一体化合路剥离矩阵  可升级NetFlex网络服务  可升级虚拟集群	和源通信	套	63500.00	upcoming	\N	2025-04-15 00:23:07.941762	2025-04-22 00:11:34.004622	5	\N
6	项目产品	基站	BC4I4X4NN	常规数字基站	Mark3000BS	频率范围：400-430MHz  数字/模拟四载波信道 -一体化合路剥离矩阵  可升级NetFlex网络服务  可升级虚拟集群	和源通信	套	79000.00	upcoming	\N	2025-04-15 00:23:07.941763	2025-04-22 00:11:33.275791	5	\N
7	项目产品	基站	BC4I4X4GE	智能集群基站	Mark3000BS PLUS	频率范围：400-430MHz  数字/模拟虚拟集群二载波信道 -一体化合路剥离矩阵  NetFlex网络服务	和源通信	套	100300.00	upcoming	\N	2025-04-15 00:23:07.941764	2025-04-22 00:11:20.851801	5	\N
8	项目产品	基站	BC4I3X4GE	智能集群基站	Mark3000BS PLUS	频率范围：400-430MHz  数字/模拟虚拟集群三载波信道 -一体化合路剥离矩阵  NetFlex网络服务	和源通信	套	125700.00	upcoming	\N	2025-04-15 00:23:07.941764	2025-04-22 00:11:22.043299	5	\N
9	项目产品	基站	BC4I2X4GE	智能集群基站	Mark3000BS PLUS	频率范围：400-430MHz  数字/模拟虚拟集群四载波信道 -一体化合路剥离矩阵  NetFlex网络服务	和源通信	套	143200.00	upcoming	\N	2025-04-15 00:23:07.941765	2025-04-22 00:11:23.379421	5	\N
12	渠道产品	基站	WCF9PH	信道机虚拟集群功能许可	LS-VTT-RPT	授权信道机在注册虚拟集群功能许可	和源通信	个	3000.00	upcoming	\N	2025-04-15 00:23:07.941767	2025-04-22 00:11:46.175663	5	\N
13	渠道产品	基站	OBUSWG10	虚拟集群服务器主机	R240/虚拟集群软件	4背板奔腾双核G5400 3.8GH 8G内存丨1*1T硬盘 微软正版系统win10软件/虚拟集群服务软件	戴尔	台	13600.00	upcoming	\N	2025-04-15 00:23:07.941768	2025-04-22 00:11:47.069138	5	\N
14	渠道产品	基站	WCP0PH	虚拟集群服务	GW-VTT-RPT	服务器虚拟集群信道控制服务软件，服务器配套	和源通信	个	\N	discontinued	\N	2025-04-15 00:23:07.941769	2025-04-18 23:53:55.989541	5	\N
15	项目产品	基站	OAMFF5WUGH1	广播多频点调频处理器	E-BDA088-U FM	频率范围：087-108MHz;最大功率：1mW;机柜式;尺寸：3U;供电供电220VAC;内置功能：16信道广播接入&广播告警切换;监控能力：不支持	和源通信	套	116667.00	active	\N	2025-04-15 00:23:07.941769	2025-04-18 23:53:55.989542	5	\N
2	项目产品	基站	BC3I3X4GN	消防救援对讲通信基站	MarkNET3000	频率范围：350-370MHz  数字/模拟虚拟集群三载波信道 -一体化合路剥离矩阵  NetFlex网络服务	和源通信	套	147000.00	discontinued	\N	2025-04-15 00:23:07.941759	2025-06-03 01:44:20.257675	5	\N
173	第三方产品	配件	W000161	衰减器	E-RFATT50-20DB	衰减值：20dB    功率：50W    接口： N型	国产	个	190.00	active	\N	2025-04-15 00:23:07.941875	2025-06-05 08:43:07.028008	5	\N
136	项目产品	应用	HYBIOCBNY	蓝牙定位信标+许可证	BTN10	标准iBeacon协议    电池续航3年    专用对讲机广播报文    许可证：蓝牙定位入网许可	和源通信	套	110.00	active	\N	2025-04-15 00:23:07.94185	2025-04-20 18:33:07.934665	5	\N
63	渠道产品	直放站	HYR2SI010	智能光纤近端机	RFS-100 LT/M	频率范围：150-170MHz 带宽：≤20M 远端携带：4 功能： 正面状态灯/网讯平台	和源通信	套	8958.00	discontinued	\N	2025-04-15 00:23:07.941801	2025-06-06 01:39:49.216559	5	\N
87	渠道产品	直放站	HYGF20000	馈电模组	FDPower400	馈电功能模组    需搭配可扩展远端机;内置远端内向天馈提供电力;	和源通信	套	1583.00	active	\N	2025-04-15 00:23:07.941818	2025-04-20 18:31:15.684608	5	\N
137	渠道产品	应用	EHYW521066	MOTOROLA 信道服务软件	GW-MOT-RPT	MOTOROLA信道机协议通信服务软件 功能 CP LCP 常规模式互通	和源通信	套	36667.00	active	\N	2025-04-15 00:23:07.941851	2025-04-20 18:33:08.953826	5	\N
124	渠道产品	应用	HYWG0NB1	网讯网关服务 软件	NFX_GATW	用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理	和源通信	套	12500.00	active	\N	2025-04-15 00:23:07.941842	2025-04-20 18:32:51.47406	5	\N
126	渠道产品	应用	HYWP0NC1	网讯平台服务 软件	NFX_MAST_OPETN	-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权    4个信道机授权    100个终端授权	和源通信	套	105000.00	active	\N	2025-04-15 00:23:07.941844	2025-04-20 18:32:56.242962	5	\N
127	渠道产品	应用	HYWF0NA1	系统工作台	ACC-CWT	提供某一个项目上所有系统的工作管理    直观全面的反映系统的整体面貌和其中设备的布局    并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块    含一年的在线后台服	和源通信	个/年	8333.00	active	\N	2025-04-15 00:23:07.941844	2025-04-20 18:32:58.019975	5	\N
128	项目产品	应用	HYWACHA1	网讯平台在线巡检功能	NFX-PAT-OPETN	支持携带对讲机完成在线的路线巡检记录及任务编排	和源通信	套	22000.00	active	\N	2025-04-15 00:23:07.941845	2025-04-20 18:32:58.759172	5	\N
129	项目产品	应用	HYWADHA1	网讯平台人员分布功能	NFX-LCN-OPETN	支持对讲机在地图上人员的动态分布和查询功能	和源通信	套	14600.00	active	\N	2025-04-15 00:23:07.941846	2025-04-20 18:32:59.826766	5	\N
130	项目产品	应用	HYWAEHA1	网讯平台终端录音功能	NFX-RCD-OPETN	支持对讲机在线通话的实时录音    回访和ID检索功能	和源通信	套	8400.00	active	\N	2025-04-15 00:23:07.941846	2025-04-20 18:33:01.390951	5	\N
131	渠道产品	应用	HYWT0NA1	运维工具包	ACC-NUT	提供多单位的系统运维流程跟踪-告警管理和推送-故障设备快速定位-维护更新工作单	和源通信	个/年	4167.00	active	\N	2025-04-15 00:23:07.941847	2025-04-20 18:33:02.371983	5	\N
132	项目产品	应用	HYWR0NA1	消防救援通信系统资源管理	ACC-NRR	消防管理机构对日常所辖区域内救援通信资源-在线单位数量    系统信息-通信健康度情况 含一年后台服务	和源通信	个	50000.00	active	\N	2025-04-15 00:23:07.941848	2025-04-20 18:33:03.74643	5	\N
133	渠道产品	应用	HYWSPNB1	信道机接入许可	LS-NFX-RPT	网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析	和源通信	套	2500.00	active	\N	2025-04-15 00:23:07.941848	2025-04-20 18:33:04.566099	5	\N
134	渠道产品	应用	HYWSRNB1	远端站接入许可	LS-NFX-BDA	网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新	和源通信	套	1500.00	active	\N	2025-04-15 00:23:07.941849	2025-04-20 18:33:06.975155	5	\N
135	渠道产品	应用	HYWSTNB1	对讲机终端接入许可	LS-NFX-RAD	网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析	和源通信	套	180.00	active	\N	2025-04-15 00:23:07.94185	2025-04-20 16:38:01.196787	5	\N
112	项目产品	天线	EAN2ICO2FZ1	综合防爆型室内全向吸顶天	E-ANTO EX	频率范围：351-470MHz 承载功率：100W 增益3dBi/IP65/IICA21防爆	和源通信	套	6667.00	discontinued	\N	2025-04-15 00:23:07.941834	2025-06-05 06:15:37.340496	5	\N
172	第三方产品	配件	W000162	衰减器	E-RFATT50-30DB	衰减值：30dB    功率：50W    接口： N型	国产	个	190.00	active	\N	2025-04-15 00:23:07.941874	2025-06-05 08:42:37.536583	5	\N
117	渠道产品	对讲机	HYTCANR01	常规锂电池板	HYTCANR01	3800mA 3.7V 锂电子 电池组 支持 PNR2000系列	和源通信	套	160.00	active	\N	2025-04-15 00:23:07.941838	2025-06-05 03:35:20.69369	5	\N
147	第三方产品	配件	ECAWYGYXTH0401	轻低烟无卤阻燃铠光缆	GYXTH-4B1 4芯	芯数：4芯    钢带：铠装    特性：单模    低烟无卤阻燃	国产	米	9.00	discontinued	\N	2025-04-15 00:23:07.941858	2025-04-18 23:53:55.989624	5	\N
148	第三方产品	配件	80093324	普通中心束管式光缆	GYXTW-24B1	芯数：24芯    钢带：铠装    特性：单模	国产	米	15.00	active	\N	2025-04-15 00:23:07.941858	2025-04-18 23:53:55.989625	5	\N
149	第三方产品	配件	ECAWYGYXTH1601	轻低烟无卤阻燃铠光缆	GYXTH-16B1 16芯	芯数：16芯    钢带：铠装    特性：单模    低烟无卤阻燃	国产	米	17.00	active	\N	2025-04-15 00:23:07.941859	2025-04-18 23:53:55.989625	5	\N
150	第三方产品	配件	W000611	轻低烟无卤阻燃铠光缆	GYXTH-8B1.3	芯数：8芯;钢带：铠装;特性：单模;低烟无卤阻燃	国产	米	8.00	active	\N	2025-04-15 00:23:07.94186	2025-04-18 23:53:55.989626	5	\N
152	第三方产品	配件	OBJANOTHS01	同轴避雷器	CA-23RS	频率范围：0-1000MHz 功率：700W 阻抗：50Ω 接口（可选）：N	钻石	套	133.00	active	\N	2025-04-15 00:23:07.941861	2025-04-20 18:33:26.227182	5	\N
153	第三方产品	配件	OZCH221035	波纹管同轴电缆	HCAAYZ -50-12	尺寸：1/2＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω	浙江联创	米	13.00	active	\N	2025-04-15 00:23:07.941862	2025-04-20 18:33:28.062541	5	\N
154	第三方产品	配件	OZCH221036	波纹管同轴电缆	HCTAYZ -50-22	尺寸：7/8＂    特性1：低烟无卤    特性2：阻燃    阻抗：50Ω	浙江联创	米	35.00	active	\N	2025-04-15 00:23:07.941862	2025-04-18 23:53:55.989628	5	\N
155	第三方产品	配件	40425003	漏泄同轴电缆	HLCTYZ-50-42	尺寸：1-5/8＂特性：低烟无卤    用途：漏泄同轴电缆	联创	米	83.00	active	\N	2025-04-15 00:23:07.941863	2025-04-18 23:53:55.989629	5	\N
157	第三方产品	配件	EJUMJK4310NJNJ	同轴电缆跳接线	NJ/NJ-3 1米	接口：NJ转NJ    长度：1米    用途：机柜内跳线	国产	根	37.00	active	\N	2025-04-15 00:23:07.941864	2025-04-20 18:33:31.549517	5	\N
158	第三方产品	配件	W0000225	同轴电缆跳接线	NJ/NJ-3 10米	接口：NJ转NJ    长度：10米    用途：机柜内跳线	国产	根	100.00	active	\N	2025-04-15 00:23:07.941865	2025-04-18 23:53:55.989631	5	\N
159	第三方产品	配件	W000188	超柔同轴电缆跳接线	NJ-3/NJ-3-1.5M	接口：NJ转NJ    长度：1.5米    特性1：超柔    特性2：SYV-50-3	国产	根	100.00	active	\N	2025-04-15 00:23:07.941865	2025-04-18 23:53:55.989631	5	\N
160	第三方产品	配件	W000185	同轴电缆跳接线	NJ-3/NJ-3-0.3M	接口：NJ转NJ    长度：0.3米    用途：机柜内跳线	国产	根	33.00	active	\N	2025-04-15 00:23:07.941866	2025-04-18 23:53:55.989632	5	\N
161	第三方产品	配件	EJUMJK4320NJQJ	同轴电缆跳接线	N/Q9-3 2米	接口：NJ转BNC    长度：2米    用途：机柜内跳线	国产	根	35.00	active	\N	2025-04-15 00:23:07.941867	2025-04-18 23:53:55.989633	5	\N
162	第三方产品	配件	EJUMJK4325NJNJ	同轴电缆跳接线	NJ-3/NJ-3_2.5m	接口：NJ转NJ    长度：2.5米    用途：机柜内跳线	国产	根	42.00	active	\N	2025-04-15 00:23:07.941867	2025-04-18 23:53:55.989633	5	\N
163	第三方产品	配件	EJUMJK4315NJQJ	同轴电缆跳接线	NJ/Q9-3 1.5米	接口：NJ转BNC    长度：1.5米    用途：机柜内跳线	国产	根	38.00	active	\N	2025-04-15 00:23:07.941868	2025-04-18 23:53:55.989634	5	\N
164	第三方产品	配件	EJUMJK4320NJNJ	同轴电缆跳接线	NJ/NJ-3 2米	接口：NJ转NJ    长度：2米    用途：机柜内跳线	国产	根	41.00	active	\N	2025-04-15 00:23:07.941869	2025-04-18 23:53:55.989635	5	\N
165	第三方产品	配件	EJUMJK4315NJNJ	同轴电缆跳接线	NJ/NJ-3 1.5米	接口：NJ转NJ    长度：1.5米    用途：机柜内跳线	国产	根	40.00	active	\N	2025-04-15 00:23:07.941869	2025-04-18 23:53:55.989635	5	\N
166	第三方产品	配件	EJUMJK4310NJQJ	同轴电缆跳接线	NJ/Q9-3 1米	接口：NJ转BNC    长度：1米    用途：机柜内跳线	国产	根	34.00	active	\N	2025-04-15 00:23:07.94187	2025-04-18 23:53:55.989636	5	\N
168	第三方产品	配件	OCIN5JZALC1	同轴电缆连接器	N-J1/2	尺寸：1/2＂    接口：N-J     外径：15.7mm    用途：同轴电缆连接器	国产	只	15.00	active	\N	2025-04-15 00:23:07.941871	2025-04-20 18:33:35.504947	5	\N
169	第三方产品	配件	OCIN5JWALC1	同轴电缆连接转换器	N-50JKW	类型：N型    特性：直角弯    用途：连接器	国产	只	15.00	active	\N	2025-04-15 00:23:07.941872	2025-04-18 23:53:55.989638	5	\N
170	第三方产品	配件	OCIN5KZALC1	同轴电缆连接转换器	N-50KK	类型：N型    特性：双通    用途：连接器	国产	只	15.00	active	\N	2025-04-15 00:23:07.941873	2025-04-18 23:53:55.989639	5	\N
171	第三方产品	配件	OCIN5JZELC1	同轴电缆连接器	N-J7/8	尺寸：7/8＂    接口：N-J    外径：32.5mm    用途：同轴电缆连接器	国产	只	30.00	active	\N	2025-04-15 00:23:07.941873	2025-04-18 23:53:55.98964	5	\N
175	第三方产品	配件	W000160	馈线接地卡	环扣式接地卡	尺寸：1/2＂    长度：5m    线径：BVC16mm平方     用途：漏缆专用接地卡	联创	个	67.00	active	\N	2025-04-15 00:23:07.941876	2025-04-18 23:53:55.989643	5	\N
176	第三方产品	配件	W000159	馈线接地卡	环扣式接地卡	尺寸：7/8＂    长度：5m    线径：BVC16mm平方     用途：漏缆专用接地卡	联创	个	75.00	active	\N	2025-04-15 00:23:07.941877	2025-04-18 23:53:55.989644	5	\N
177	第三方产品	配件	W000140	馈线接地卡	环扣式接地卡	尺寸：1-5/8＂    长度：5m    线径：-22     用途：漏缆专用接地卡	联创	个	170.00	active	\N	2025-04-15 00:23:07.941877	2025-04-18 23:53:55.989644	5	\N
178	第三方产品	配件	4042RNM	1-5/8”漏泄同轴电缆接头	NM-42R	尺寸：1-5/8”    用途：漏泄同轴电缆接头	联创	个	150.00	active	\N	2025-04-15 00:23:07.941878	2025-04-18 23:53:55.989645	5	\N
179	第三方产品	配件	4042RDNPT	1-5/8”漏泄同轴电缆吊夹	KXC-42R-DNPT	尺寸：1-5/8”    用途：漏泄同轴电缆吊夹	联创	个	33.00	active	\N	2025-04-15 00:23:07.941879	2025-04-18 23:53:55.989646	5	\N
180	第三方产品	配件	4042RDNFH	1-5/8”漏泄同轴电缆防火吊夹	KXC-42R-DNFH	尺寸：1-5/8”    用途：漏泄同轴电缆防火吊夹	联创	个	40.00	active	\N	2025-04-15 00:23:07.941879	2025-04-18 23:53:55.989648	5	\N
181	第三方产品	配件	W000141	直流隔断器	DC-BLOCK	测试电压：DC100V    接口类型：N公-N母    最大功率：5W    频率：DC-6GHz        外形尺寸：φ15.8*50mm	定制	个	330.00	active	\N	2025-04-15 00:23:07.94188	2025-04-18 23:53:55.989649	5	\N
182	第三方产品	服务	W000008	施工附件	/	安装所需要的小型支架    紧固件    防水胶布    轧带和标签    管线材料    按施工要求决定	服务	批	0.00	active	\N	2025-04-15 00:23:07.941881	2025-04-20 18:33:38.697715	5	\N
183	第三方产品	服务	F0005	调试开通	/	-深化图纸现场施工图    竣工图纸\n-安装督导和图纸交底协调\n-部署调试开通    软件环境部署    培训	服务	次	30000.00	active	\N	2025-04-15 00:23:07.941881	2025-04-20 18:33:39.496499	5	\N
184	第三方产品	服务	F0011	主站频率占用费	转移支付	根据系统使用的信道机数量来申报的每年一次的基站频率占用费    按国家核定标准收取	服务	台	3300.00	active	\N	2025-04-15 00:23:07.941882	2025-04-20 18:33:40.286414	5	\N
185	第三方产品	服务	F0010	对讲机频率占用费	转移支付	根据系统使用的对讲机终端数量来申报的每年一次的对讲机频率占用费    按国家核定标准收取	服务	台	170.00	active	\N	2025-04-15 00:23:07.941883	2025-04-20 16:38:24.018364	5	\N
186	第三方产品	服务	F0012	电磁环境检测及申报报告费	/	提供前期安装现场电磁环境测试和申请频率的初选建议报告及提高无线电管理局的申报材料的准备    指导申请过程    包含1天的现场测试二个工程师    2天测试报告的撰写和一周的资料准备工作量	服务	次	8000.00	active	\N	2025-04-15 00:23:07.941883	2025-04-20 18:33:41.716173	5	\N
167	第三方产品	配件	W000163	终端负载	E-TF50	功率：50W    接口：N型	国产	个	142.00	active	\N	2025-04-15 00:23:07.941871	2025-06-05 08:41:54.316305	5	\N
156	第三方产品	配件	OISKHB1JLC1	跳线	E-JP50-7	长度：0.5米 接口：NJ转NJ 用途：天线连接跳线	国产	根	35.00	active	\N	2025-04-15 00:23:07.941864	2025-06-05 08:44:10.134332	5	\N
1	第三方产品	基站	OBJSVOTXQ01	智能信道交换机	S1024	端口数量：24个  网线类型：3、4、5类双绞线   防雷等级：4级（6KV） 用途：CP、IP、LCP、系统监控配件/信道机	华三	套	780.00	upcoming	\N	2025-04-15 00:23:07.941755	2025-06-06 02:24:33.035118	5	\N
174	第三方产品	配件	W000072	衰减器	E-RFATT50-10DB	衰减值：10dB    功率：50W    接口： N型	国产	个	190.00	active	\N	2025-04-15 00:23:07.941875	2025-06-05 08:43:23.819454	5	\N
61	渠道产品	直放站	EAMLR4FBKR2	射频中继组件 413MHz	E-BDA400-B LT	频率范围:403-405/413-415MHz 输出功率:33dB 增益:≥50dB 收发频率间隔:10M 工作带宽:2M 安装方式:壁挂式	和源通信	套	10120.00	discontinued	\N	2025-04-15 00:23:07.9418	2025-06-06 01:38:03.748392	5	\N
56	渠道产品	合路平台	HYMPC3AA0	系统合路器	E-FHP2000-3	频率范围：87-108MHz/163-166MHz/361-366MHz 单端口承载功率：50W;插入损耗：≤12dB;接入端口数量：3 安装方式：机柜式;尺寸：2U	和源通信	套	8750.00	discontinued	\N	2025-04-15 00:23:07.941797	2025-06-06 01:30:56.956814	5	\N
62	渠道产品	直放站	HYR2SI000	智能光纤近端机	RFS-88 LT/M	频率范围：87-108MHz 远端携带：4 功能：正面状态灯/面板调试	和源通信	套	8958.00	discontinued	\N	2025-04-15 00:23:07.941801	2025-06-06 01:38:52.5169	5	\N
88	渠道产品	功率/耦合器	HYCCN31Y	定向耦合器	EVDC-6 LT	频率范围：150-170MHz    承载功率：100W;耦合规格：6dB	和源通信	套	184.00	discontinued	\N	2025-04-15 00:23:07.941819	2025-06-05 09:27:51.511127	5	\N
86	项目产品	直放站	HYR3DI34J	数字智能光纤交织型远端直放站	DRFT-BDA410/MITW	频率范围：410-414/420-424MHz 带宽：≤4M 输出：10W 数字交织型 功能：触摸屏/网讯平台 扩展：馈电	和源通信	套	66667.00	active	\N	2025-04-15 00:23:07.941817	2025-06-06 01:47:50.707725	5	\N
89	渠道产品	功率/耦合器	HYCCN41Y	定向耦合器	EVDC-10 LT	频率范围：150-170MHz    承载功率：100W;耦合规格：10dB	和源通信	套	184.00	discontinued	\N	2025-04-15 00:23:07.941819	2025-06-05 09:28:07.394449	5	\N
116	项目产品	对讲机	HYTX0NA	DMR智能对讲机	PNR2100	频率范围：400-470MHz/ 4G     功率：1-2W    3800mAH锂电池    蓝牙 5.0 定位    电池管理	和源通信	套	2750.00	upcoming	\N	2025-04-15 00:23:07.941837	2025-06-05 03:34:19.955194	5	\N
118	渠道产品	对讲机	HYTCAZR02	智能锂电池板	HYTCAZR02	3800mA 3.7V 锂电池组 内置充放电效能管理芯片 支持PNR2000系列	和源通信	套	200.00	upcoming	\N	2025-04-15 00:23:07.941838	2025-06-05 03:35:55.940327	5	\N
123	第三方产品	应用	OBUSWG00	网关服务器主机	R240	4背板奔腾双核G5400 3.8GH 8G内存丨1*1T硬盘 微软正版系统win10软件	戴尔	台	13600.00	active	\N	2025-04-15 00:23:07.941842	2025-06-06 02:12:11.441973	5	\N
125	第三方产品	应用	OBUSWP00	平台服务器主机	R340	R340 4背板E-2134 3.5G 4核8线程 16G内存丨3*1T硬盘 微软正版系统win10软件	戴尔	台	23300.00	active	\N	2025-04-15 00:23:07.941843	2025-06-06 02:12:29.64192	5	\N
143	第三方产品	配件	EJUWY05A4001	单模光纤跳线单芯	单模单芯 FC-FC  5米	光纤类型：单模    光缆类型：单芯    接口类型：FC/PC-FC/PC    长度：5米	国产	根	30.00	active	\N	2025-04-15 00:23:07.941855	2025-06-09 09:14:30.939173	5	\N
151	第三方产品	配件	OBJANOTGR01	标准L型贴墙室外天线支架	MONT80	曲臂长度50cm 材料：不锈钢 结构类型：L型结构	国产	套	150.00	active	\N	2025-04-15 00:23:07.94186	2025-06-06 02:23:33.533635	5	\N
142	第三方产品	配件	W0000144	单模光纤跳线单芯	单模单芯FC-LC 5米	光纤类型：单模    光缆类型：单芯    接口类型：FC/PC-LC/PC    长度：5米	国产	根	33.00	active	\N	2025-04-15 00:23:07.941854	2025-06-09 09:13:47.635822	5	\N
103	渠道产品	天线	HYAIOCN1N	室内全向吸顶天线	E-ANTO LT	频率范围：88-430MHz 承载功率：50W 性能：室内全向 天线增益：0dBi	和源通信	套	209.00	active	\N	2025-04-15 00:23:07.941829	2025-06-05 06:08:06.54781	5	\N
145	第三方产品	配件	W000154	单模光纤跳线单芯	单模单芯FC-LC 10米	光纤类型：单模    光缆类型：单芯    接口类型：FC/PC-LC/PC    长度：10米	国产	根	58.00	active	\N	2025-04-15 00:23:07.941856	2025-06-09 09:15:40.02772	5	\N
144	第三方产品	配件	W000612	单模光纤跳线单芯	FC/APC-FC/APC 5M	光纤类型：单模    光缆类型：单芯    接口类型：FC/APC-FC/APC    长度：5米	国产	根	27.00	active	\N	2025-04-15 00:23:07.941856	2025-06-06 05:56:29.805622	5	\N
146	第三方产品	配件	EJUWY10A4001	单模光纤跳线单芯	单模单芯 FC-FC 10米	光纤类型：单模    光缆类型：单芯    接口类型：FC/PC-FC/PC    长度：10米	国产	米	35.00	active	\N	2025-04-15 00:23:07.941857	2025-06-09 09:16:06.910199	5	\N
80	项目产品	直放站	HYR3DI300	数字智能光纤远端直放站	DRFT-BDA88/M	频率范围：87-108MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电	和源通信	套	45833.00	active	\N	2025-04-15 00:23:07.941814	2025-06-06 01:45:35.384426	5	\N
58	项目产品	合路平台	HYMPC3ABP	系统合路器 | 供电	E-FHP2000-3 /P	频率范围：87-108MHz/361-366MHz/403-430 单端口承载功率：50W;插入损耗：≤12dB;接入端口数量：3 内置电源模块	和源通信	套	20450.00	discontinued	\N	2025-04-15 00:23:07.941798	2025-06-06 01:30:22.861834	5	\N
49	渠道产品	合路平台	HYMPC2A30	系统合路器	E-FHP2000-2	频率范围：351-366/372-386MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：2	和源通信	套	6691.00	discontinued	\N	2025-04-15 00:23:07.941792	2025-06-06 07:08:33.269178	5	\N
78	项目产品	直放站	HYR2DI040	数字智能光纤近端机	DRFS-400/M	频率范围：410-414/420-424MHz 远端携带：32 数字型 功能：触摸屏/网讯平台	和源通信	套	25000.00	active	\N	2025-04-15 00:23:07.941812	2025-06-06 01:42:53.978421	5	\N
100	渠道产品	功率/耦合器	HYCCF44Y	馈电定向耦合器	MADC-10	频率范围：351-470MHz 承载功率：100W 耦合规格：10dB 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信	套	246.00	active	\N	2025-04-15 00:23:07.941827	2025-06-05 09:25:39.791254	5	\N
111	渠道产品	天线	OANFOYD7MJ1	室外八木定向天线	E-ANTY 100	频率范围：087-108MHz 增益：6dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外	和源通信	套	750.00	active	\N	2025-04-15 00:23:07.941834	2025-06-05 06:12:10.115322	5	\N
141	第三方产品	配件	EDFWYFC08O	光纤配线架	ST/FC  8口	尺寸类型：标准尺寸FC口    端口数：8口    产品类型：墙上型    特性：含法兰头    不含配套尾纤	国产	套	250.00	active	\N	2025-04-15 00:23:07.941854	2025-06-09 08:56:57.926086	5	\N
10	项目产品	基站	HYPSMXI30	数字智能信道机	Mark1000 MAX	频率范围：350-400MHz-功率 25W-网讯平台-数模兼容	和源通信	套	14583.00	active	\N	2025-04-15 00:23:07.941766	2025-06-05 08:52:17.330989	5	\N
60	渠道产品	直放站	HYR1SN14A	常规射频直放站	E-BDA400B LT	频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W  功能：正面状态灯	和源通信	套	8396.00	active	\N	2025-04-15 00:23:07.941799	2025-06-05 06:55:19.646256	5	\N
119	渠道产品	对讲机	ZCTZ6NN	智能多联充电器	CMP2600	功能: 智能   充电座数量: 6  NetFlex网络服务：电池健康度管理	和源通信	套	1860.00	active	\N	2025-04-15 00:23:07.941839	2025-06-06 07:23:14.408868	5	\N
120	渠道产品	对讲机	ZCTS6NN	智能多联充电栈	CRSTC1000	功能: 智能多联充电器+托架结构  类型: 栈    充电座数量: 6    功能: 智能   充电座数量: 6  NetFlex网络服务：电池健康度管理	和源通信	套	2460.00	active	\N	2025-04-15 00:23:07.94184	2025-06-06 07:24:09.14339	5	\N
20	渠道产品	合路平台	ECM1B042CZ1	定向耦合合路器	E-FH400-4	频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U	和源通信	套	6642.00	active	\N	2025-04-15 00:23:07.941773	2025-06-06 01:27:26.697621	5	\N
21	渠道产品	合路平台	ECM1B062CZ1	定向耦合合路器	E-FH400-6	频率范围：400-430MHz 单端口承载功率：50W;插入损耗：≤11dB;接入端口数量：6;安装方式：机柜式;尺寸：2U	和源通信	套	10760.00	active	\N	2025-04-15 00:23:07.941773	2025-06-06 01:27:45.244982	5	\N
106	项目产品	天线	HYAIOCB4Y	智能室内蓝牙全向吸顶天线	MA12	频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯 蓝牙信标	和源通信	套	329.00	discontinued	\N	2025-04-15 00:23:07.941831	2025-06-05 06:03:37.417184	5	\N
22	渠道产品	合路平台	ECM1B082CZ1	定向耦合合路器	E-FH400-8	频率范围：400-430MHz 单端口承载功率：50W;插入损耗：≤12dB;接入端口数量：8;安装方式：机柜式;尺寸：2U	和源通信	套	14120.00	discontinued	\N	2025-04-15 00:23:07.941774	2025-06-06 01:28:12.020918	5	\N
19	渠道产品	合路平台	ECM1B022CZ1	定向耦合合路器	E-FH400-2	频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U	和源通信	套	4569.00	active	\N	2025-04-15 00:23:07.941772	2025-06-06 01:26:58.063305	5	\N
26	渠道产品	合路平台	EDE1BU4xCZ1	分路器	E-JF350/400-4	频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U	和源通信	套	2493.00	active	\N	2025-04-15 00:23:07.941777	2025-06-06 01:21:51.784309	5	\N
17	渠道产品	合路平台	HYMFC4A10	定向耦合合路器	E-FH150-4	频率范围：163-167MHz 单端口承载功率：50W;插入损耗：≤7.0dB接入端口数量：4;安装方式：机柜式;	和源通信	套	11111.00	discontinued	\N	2025-04-15 00:23:07.941771	2025-06-06 01:26:14.241598	5	\N
25	渠道产品	合路平台	EDE1BU2xCZ1	分路器	E-JF350/400-2	频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U	和源通信	套	2320.00	active	\N	2025-04-15 00:23:07.941776	2025-06-06 01:21:34.622322	5	\N
24	渠道产品	合路平台	HYMJC4010	分路器	E-JF150-4	频率范围：130-170MHz 单端口承载功率：1W;插入损耗：≤7.0dB接入端口数量：4;安装方式：机柜式;	和源通信	套	2913.00	discontinued	\N	2025-04-15 00:23:07.941775	2025-06-06 01:21:19.039277	5	\N
38	渠道产品	合路平台	EDE1AD6xCZ1	下行信号剥离器	R-EVDC-BLST-D	频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U	和源通信	套	4569.00	active	\N	2025-04-15 00:23:07.941785	2025-06-05 09:37:11.700378	5	\N
34	项目产品	合路平台	MCHFLL52C	一体化分合路矩阵	FHJ400-BLST-4	频率范围: 350-370MHz/350-470MHz    信道端口数: 4    最大输入功率: 250mw/24dB    插入损耗: ≤6dB    驻波比: ≤1.5    端口隔离度: ≥16dB    电源: 220V/ CN	和源通信	套	16000.00	upcoming	\N	2025-04-15 00:23:07.941782	2025-06-06 07:04:46.052672	5	\N
47	渠道产品	合路平台	ECM1BB22CZ2	系统合路器	E-FHP2000-2	频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U	和源通信	套	7917.00	active	\N	2025-04-15 00:23:07.941791	2025-06-06 07:07:53.717741	5	\N
44	渠道产品	合路平台	EDULB4H1CZ1	双工器	E-SGQ400D	频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U	和源通信	套	7876.00	active	\N	2025-04-15 00:23:07.941789	2025-06-05 09:33:03.541115	5	\N
48	渠道产品	合路平台	ECM1BB22CZ1	系统合路器	E-FHP2000-2	频率范围：351-366/402-416MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U	和源通信	套	7917.00	active	\N	2025-04-15 00:23:07.941791	2025-06-06 07:08:13.675884	5	\N
46	渠道产品	合路平台	EDUPGFH1CZ1	双工器	E-SGQ800D	频率范围：806-821/851-866MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：45M 隔离方式：带通 工作带宽：15M 安装方式：机柜式 尺寸：2U	和源通信	套	9167.00	active	\N	2025-04-15 00:23:07.94179	2025-06-05 09:33:20.45068	5	\N
45	渠道产品	合路平台	EDULB4H1CZ2	双工器	E-SGQ400D	频率范围：402-406/412-416MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U	和源通信	套	7876.00	active	\N	2025-04-15 00:23:07.94179	2025-06-05 09:33:45.816934	5	\N
50	渠道产品	合路平台	EHYR321092	系统合路器	E-FHP2000-2	频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤4dB 工作带宽：30M 接入端口数量：2 安装方式：机柜式 尺寸：2U	和源通信	套	5000.00	discontinued	\N	2025-04-15 00:23:07.941793	2025-06-06 07:08:50.466107	5	\N
39	渠道产品	合路平台	EDE1AU6xCZ1	上行信号剥离器	R-EVDC-BLST-U	频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U	和源通信	套	4569.00	active	\N	2025-04-15 00:23:07.941786	2025-06-05 09:37:26.829262	5	\N
29	渠道产品	合路平台	MCFCMN53N	多信道分合路器	FHJ400-2	频率范围: 400-430MHz    信道端口数: 2    最大输入功率: 50W    插入损耗: ≤9dB    驻波比: ≤1.5    端口隔离度: ≥35dB    电源: /	和源通信	套	6800.00	active	\N	2025-04-15 00:23:07.941779	2025-06-06 07:02:03.750271	5	\N
30	渠道产品	合路平台	MCFFMM53N	多信道分合路器	FHJ400-4	频率范围: 400-430MHz    信道端口数: 4    最大输入功率: 50W    插入损耗: ≤7.5dB    驻波比: ≤1.5    端口隔离度: ≥35dB	和源通信	套	9100.00	active	\N	2025-04-15 00:23:07.94178	2025-06-06 07:02:50.217001	5	\N
31	渠道产品	合路平台	MCFHMO53N	多信道分合路器	FHJ400-6	频率范围: 400-430MHz    信道端口数: 6    最大输入功率: 50W    插入损耗: ≤11dB    驻波比: ≤1.5    端口隔离度: ≥35dB	和源通信	套	14000.00	active	\N	2025-04-15 00:23:07.94178	2025-06-06 07:03:11.960392	5	\N
32	渠道产品	合路平台	EC3FATN31N	信号剥离矩阵	R-EVDC-BLST-4	频率范围: 350-430MHz    信道端口数: 4 input/ 4 output    最大输入功率: 100W    路由: Two-way    工作电压: /    端口耦合度: ≤29dB    Insert Loss: ≤1dB	和源通信	套	7500.00	active	\N	2025-04-15 00:23:07.941781	2025-06-06 07:06:33.293453	5	\N
33	渠道产品	合路平台	EC3SATN31N	信号剥离矩阵	R-EVDC-BLST-6	频率范围: 350-430MHz    信道端口数: 6 input/ 6 output    最大输入功率: 100W    路由: Two-way    工作电压: /    端口耦合度: ≤29dB    Insert Loss: ≤1dB	和源通信	套	9200.00	active	\N	2025-04-15 00:23:07.941782	2025-06-06 07:06:50.756935	5	\N
36	渠道产品	合路平台	HYMBC6A1U	上行信号剥离器	R-EVDC-BLST-U	频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U	和源通信	套	4938.00	discontinued	\N	2025-04-15 00:23:07.941784	2025-06-05 09:36:42.782799	5	\N
51	渠道产品	合路平台	EHYR321078	系统合路器	E-FHP2000-2	频率范围：400-424/806-866MHz 单端口承载功率：50W 接入端口数量：2 安装方式：机柜式	和源通信	套	7917.00	discontinued	\N	2025-04-15 00:23:07.941793	2025-06-06 07:09:17.252472	5	\N
68	渠道产品	直放站	HYR3S1130	智能光纤远端直放站	RFT-BDA300B LT	频率范围：351-356/361-366MHz 带宽：≤4M 输出：2W 功能：正面状态灯/网讯平台	和源通信	套	12851.00	active	\N	2025-04-15 00:23:07.941804	2025-06-05 07:31:09.076431	5	\N
70	渠道产品	直放站	HYR3SI14A	智能光纤远端直放站	RFT-BDA400B LT/M	频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W  功能： 网讯平台	和源通信	套	11851.00	active	\N	2025-04-15 00:23:07.941806	2025-06-05 07:36:31.832984	5	\N
72	渠道产品	直放站	HYR3SI340	智能光纤远端直放站	RFT-BDA410 LT/M	频率范围：410-414/420-424MHz 带宽：≤4M 输出：10W 功能： 正面状态灯/网讯平台	和源通信	套	21250.00	active	\N	2025-04-15 00:23:07.941808	2025-06-06 02:07:21.008789	5	\N
73	渠道产品	直放站	HYR3SI380	智能光纤远端直放站	RFT-BDA810 LT/M	频率范围：806-821/851-866MHz 带宽：≤15M 输出：10W 2U机箱 功能： 正面状态灯/网讯平台	和源通信	套	21250.00	active	\N	2025-04-15 00:23:07.941809	2025-06-06 02:07:39.911821	5	\N
52	渠道产品	合路平台	ECM4BB32CZ1	系统合路器	E-FHP2000-3	频率范围：351-366/372-386/410-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：3 安装方式：机柜式 尺寸：2U	和源通信	套	16667.00	discontinued	\N	2025-04-15 00:23:07.941794	2025-06-06 07:09:36.070822	5	\N
55	渠道产品	合路平台	EHYR321079	系统合路器	E-FHP2000-3	频率范围：351-365/400-424/806-866MHz 单端口承载功率：50W 接入端口数量：3 安装方式：机柜式	和源通信	套	16667.00	discontinued	\N	2025-04-15 00:23:07.941796	2025-06-06 07:10:59.432128	5	\N
79	项目产品	直放站	HYR2DI080	数字智能光纤近端机	DRFS-800/M	频率范围：800-890MHz 远端携带：32 数字型 功能：触摸屏/网讯平台	和源通信	套	25000.00	active	\N	2025-04-15 00:23:07.941813	2025-06-06 01:43:16.706832	5	\N
67	渠道产品	直放站	HYR3SI310	智能光纤远端直放站	RFT-BDA110 LT/M	频率范围：157-161/163-167MHz 带宽：≤4M 输出：10W 功能： 正面状态灯/网讯平台	和源通信	套	25000.00	active	\N	2025-04-15 00:23:07.941804	2025-06-06 02:04:07.610883	5	\N
69	渠道产品	直放站	HYR3SI330	智能光纤远端直放站	RFT-BDA310 LT/M	频率范围：351-356/361-366MHz 带宽：≤5M 输出：10W 2U机箱 功能： 正面状态灯/网讯平台	和源通信	套	21250.00	active	\N	2025-04-15 00:23:07.941805	2025-06-06 02:04:34.808833	5	\N
64	渠道产品	直放站	HYR2SI030	智能光纤近端机	RFS-400 LT/M	频率范围：350-50MHz 带宽：≤15M 远端携带：4 功能： 网讯平台	和源通信	套	9876.00	active	\N	2025-04-15 00:23:07.941802	2025-06-06 01:40:11.618384	5	\N
76	项目产品	直放站	HYR2DI030	数字智能光纤近端机	DRFS-300/M	频率范围：350MHz 远端携带：32 数字型 功能：触摸屏/网讯平台	和源通信	套	25000.00	active	\N	2025-04-15 00:23:07.941811	2025-06-06 01:41:57.463629	5	\N
53	渠道产品	合路平台	ECM5BB32CZ1	系统合路器	E-FHP2000-3	频率范围：87-108/351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：3 安装方式：机柜式 尺寸：2U	和源通信	套	16667.00	discontinued	\N	2025-04-15 00:23:07.941795	2025-06-06 07:09:56.398889	5	\N
54	渠道产品	合路平台	ECM5BB32CZ2	系统合路器	E-FHP2000-3	频率范围：87-108/351-366/402-416MHz 单端口承载功率：50W 插入损耗：≤2.0dB 接入端口数量：3 安装方式：机柜式 尺寸：2U	和源通信	套	16667.00	discontinued	\N	2025-04-15 00:23:07.941795	2025-06-06 07:10:15.93561	5	\N
96	渠道产品	功率/耦合器	HYCCN64Y	定向耦合器	EVDC-20 LT	频率范围：351-470MHz;承载功率：100W;耦合规格：20dB;分路端口数量：2;防护等级：IP53;	和源通信	套	142.00	active	\N	2025-04-15 00:23:07.941824	2025-06-05 09:30:13.959087	5	\N
102	渠道产品	功率/耦合器	HYCCF64Y	馈电定向耦合器	MADC-20	频率范围：351-470MHz 承载功率：100W 耦合规格：20dB 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信	套	246.00	active	\N	2025-04-15 00:23:07.941828	2025-06-05 09:26:17.14305	5	\N
104	渠道产品	天线	HYAIOCN4Y	超薄室内全向吸顶天线	MA10	频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65	和源通信	套	142.00	active	\N	2025-04-15 00:23:07.941829	2025-06-05 06:02:31.23177	5	\N
107	渠道产品	天线	EAN2OFD2TE2	室外定向板状天线	E-ANTD 400	频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外	和源通信	套	354.00	active	\N	2025-04-15 00:23:07.941831	2025-06-05 06:09:25.246699	5	\N
105	渠道产品	天线	HYAIOCL4Y	智能室内全向吸顶天线	MA11	频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯	和源通信	套	291.00	discontinued	\N	2025-04-15 00:23:07.94183	2025-06-05 06:03:05.737908	5	\N
99	渠道产品	功率/耦合器	HYCCF34Y	馈电定向耦合器	MADC-6	频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信	套	246.00	active	\N	2025-04-15 00:23:07.941826	2025-06-05 09:25:20.751778	5	\N
93	渠道产品	功率/耦合器	HYCCN34Y	定向耦合器	EVDC-6 LT	频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;	和源通信	套	142.00	active	\N	2025-04-15 00:23:07.941822	2025-06-05 09:29:01.43956	5	\N
85	项目产品	直放站	HYR3DI380	数字智能光纤远端直放站	DRFT-BDA810/M	频率范围：806-821/851-866MHz 带宽：≤15M ；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电	和源通信	套	45833.00	active	\N	2025-04-15 00:23:07.941817	2025-06-06 01:47:07.281724	5	\N
95	渠道产品	功率/耦合器	HYCCN54Y	定向耦合器	EVDC-15 LT	频率范围：351-470MHz;承载功率：100W;耦合规格：15dB;分路端口数量：2;防护等级：IP53;	和源通信	套	142.00	active	\N	2025-04-15 00:23:07.941823	2025-06-05 09:29:47.914601	5	\N
82	项目产品	直放站	HYR3DI330	数字智能光纤远端直放站	DRFT-BDA310/M	频率范围：351-356/361-366MHz；带宽：≤21M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电	和源通信	套	47917.00	active	\N	2025-04-15 00:23:07.941815	2025-06-06 01:46:09.170125	5	\N
92	渠道产品	功率/耦合器	HYCCN61Y	定向耦合器	EVDC-20 LT	频率范围：150-170MHz    承载功率：100W;耦合规格：20dB	和源通信	套	184.00	active	\N	2025-04-15 00:23:07.941821	2025-06-05 09:28:42.978486	5	\N
121	渠道产品	对讲机	ZCTCN4T	多联充电柜	CRCAB2000	功能: 智能    类型: 柜    充电栈数量: 3     Dimensions: 27U  功能: 智能   充电座数量: 6  NetFlex网络服务：电池健康度管理	和源通信	套	9800.00	active	\N	2025-04-15 00:23:07.94184	2025-06-06 07:19:25.193561	5	\N
122	渠道产品	对讲机	HYZNC5000	多联充电柜	EVT-CRCAB2000	五套六联充电栈    支持同时30路对讲机的充电储存    42U    独立供电    电源保护    适用PNR系列对讲机	和源通信	套	11500.00	active	\N	2025-04-15 00:23:07.941841	2025-06-06 07:19:55.395542	5	\N
113	项目产品	天线	ACC3OOCXS	防爆型高防护全向天线	MAEX 10	频率范围: 350-470 MHz  增益: 0 dB   工作环境: 室内/室外   极化方向: 全向极化   功能: 防爆    IP防护: IP 65	和源通信	套	7200.00	active	\N	2025-04-15 00:23:07.941835	2025-06-05 06:15:16.848424	5	\N
114	渠道产品	对讲机	HYTD1MA	DMR常规对讲机	PNR2000	频率范围：150-170MHz    锂电池 3700mAh	和源通信	套	1333.00	active	\N	2025-04-15 00:23:07.941836	2025-06-06 07:14:33.687051	5	\N
140	第三方产品	配件	EDFWYFC04O	光纤配线架	ST/FC  4口	尺寸类型：标准尺寸FC口    端口数：4口    产品类型：墙上型    特性：含法兰头    不含配套尾纤	国产	套	163.00	active	\N	2025-04-15 00:23:07.941853	2025-06-09 08:56:42.262456	5	\N
23	渠道产品	合路平台	HYMJC2010	分路器	E-JF150-2	频率范围：130-170MHz 单端口承载功率：1W 插入损耗：≤3.5dB 接入端口数量：2 安装方式：机柜式 尺寸 1U	和源通信	套	2493.00	discontinued	\N	2025-04-15 00:23:07.941775	2025-06-05 08:54:33.73521	5	\N
98	渠道产品	功率/耦合器	HYCDF24Y	馈电功率分配器	MAPD-2	频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信	套	208.00	active	\N	2025-04-15 00:23:07.941825	2025-06-05 05:45:18.209158	5	\N
91	渠道产品	功率/耦合器	HYCCN51Y	定向耦合器	EVDC-15 LT	频率范围：150-170MHz    ;承载功率：100W;耦合规格：15dB	和源通信	套	184.00	active	\N	2025-04-15 00:23:07.941821	2025-06-05 09:28:25.329368	5	\N
94	渠道产品	功率/耦合器	HYCCN44Y	定向耦合器	EVDC-10 LT	频率范围：351-470MHz;承载功率：100W;耦合规格：10dB;分路端口数量：2;防护等级：IP53;	和源通信	套	142.00	active	\N	2025-04-15 00:23:07.941823	2025-06-05 09:29:28.155083	5	\N
101	渠道产品	功率/耦合器	HYCCF54Y	馈电定向耦合器	MADC-15	频率范围：351-470MHz 承载功率：100W 耦合规格：15dB 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信	套	246.00	active	\N	2025-04-15 00:23:07.941827	2025-06-05 09:25:57.16834	5	\N
27	渠道产品	合路平台	EDE1BU6xCZ1	分路器	E-JF350/400-6	频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤9.5dB 接入端口数量：6 安装方式：机柜式 尺寸1U	和源通信	套	3580.00	active	\N	2025-04-15 00:23:07.941778	2025-06-06 01:22:28.14763	5	\N
28	渠道产品	合路平台	EDE1BU8xCZ1	分路器	E-JF350/400-8	频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤10.5dB 接入端口数量：8 安装方式：机柜式 尺寸1U	和源通信	套	4962.00	discontinued	\N	2025-04-15 00:23:07.941778	2025-06-06 01:22:44.507246	5	\N
16	渠道产品	合路平台	HYMFC2A10	定向耦合合路器	E-FH150-2	频率范围：163-167MHz 单端口承载功率：50W;插入损耗：≤4.0dB接入端口数量：2;安装方式：机柜式;	和源通信	套	7902.00	discontinued	\N	2025-04-15 00:23:07.94177	2025-06-06 01:25:59.209053	5	\N
11	渠道产品	基站	HYPSMXI40	数字智能信道机	Mark1000 MAX	频率范围：400-470MHz -功率 25W-网讯平台-数模兼容	和源通信	套	13580.00	active	\N	2025-04-15 00:23:07.941766	2025-06-05 08:52:57.307648	5	\N
18	渠道产品	合路平台	ECM1B042CZ2	定向耦合合路器	E-FH350-4	频率范围：350-390MHz 单端口承载功率：50W;插入损耗：≤8.5dB接入端口数量：4;安装方式：机柜式;尺寸：2U	和源通信	套	6667.00	active	\N	2025-04-15 00:23:07.941771	2025-06-06 01:26:33.370079	5	\N
74	项目产品	直放站	HYR2DI000	数字智能光纤近端机	DRFS-88/M	频率范围：87-108MHz 远端携带：32 数字型 功能：触摸屏/网讯平台	和源通信	套	25000.00	active	\N	2025-04-15 00:23:07.94181	2025-06-06 01:41:17.194744	5	\N
77	项目产品	直放站	OC4DC4IN	数字智能光纤近端机	DRFS-400B/M	频率范围: 400-470MHz    工作模式: Digital    安装方式: Cabinet 2U    IP防护: IP40    光纤端口类型: LC-LC   功能: NetFlex	和源通信	套	21000.00	active	\N	2025-04-15 00:23:07.941812	2025-06-06 01:42:26.416873	5	\N
115	渠道产品	对讲机	HYTD4MA	DMR常规对讲机	PNR2000	频率范围：400-470MHz    锂电池 3700mAh	和源通信	套	1333.00	active	\N	2025-04-15 00:23:07.941836	2025-06-06 07:14:55.151999	5	\N
66	渠道产品	直放站	HYR3SI300	智能光纤远端直放站	RFT-BDA88 LT/M	频率范围：87-108MHz；带宽：≤21M；输出：10W；2U机柜；功能：正面状态灯/面板调试	和源通信	套	22500.00	active	\N	2025-04-15 00:23:07.941803	2025-06-06 02:03:46.54321	5	\N
90	渠道产品	功率/耦合器	HYCDN24Y	功率分配器	EVPD-2 LT	频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;	和源通信	套	142.00	active	\N	2025-04-15 00:23:07.94182	2025-06-05 09:27:19.329324	5	\N
108	渠道产品	天线	EANFOMO5HR1	室外全向玻璃钢天线	E-ANTG-150	频率范围：150-170MHz    增益：5dBi    防护等级：IP65    辐射方向：全向    最大承载功率：50W    接头类型：N-Femade    特性：室外	和源通信	套	1333.00	active	\N	2025-04-15 00:23:07.941832	2025-06-06 07:35:12.028915	5	\N
40	渠道产品	合路平台	HYMDF2A10	双工器	E-SGQ150D	频率范围：157.3-160.6/163.0-166.3MHz;单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：5.7M 隔离方式：带通 工作带宽：2M（可调） 安装方式：机柜式;	和源通信	套	7902.00	discontinued	\N	2025-04-15 00:23:07.941786	2025-06-05 09:32:09.978635	5	\N
37	渠道产品	合路平台	HYMBC6A1D	下行信号剥离器	R-EVDC-BLST-D	频率范围：87-170MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U	和源通信	套	4938.00	discontinued	\N	2025-04-15 00:23:07.941784	2025-06-05 09:36:56.743323	5	\N
97	渠道产品	功率/耦合器	HYCCN74Y	定向耦合器	EVDC-30 LT	频率范围：351-470MHz;承载功率：100W;耦合规格：30dB;分路端口数量：2;防护等级：IP53;	和源通信	套	142.00	active	\N	2025-04-15 00:23:07.941825	2025-06-05 09:30:47.596567	5	\N
109	渠道产品	天线	EANPOMO5HR1	室外全向玻璃钢天线	E-ANTG 350	频率范围：350-380MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade 特性：室外	和源通信	套	625.00	active	\N	2025-04-15 00:23:07.941833	2025-06-06 07:35:32.312996	5	\N
65	渠道产品	直放站	HYR2SI080	智能光纤近端机	RFS-800 LT/M	频率范围：800-890MHz 带宽：≤15M 远端携带：4 功能： 网讯平台	和源通信	套	8958.00	active	\N	2025-04-15 00:23:07.941802	2025-06-06 01:40:29.81713	5	\N
59	渠道产品	直放站	HYR1SN140	常规射频直放站	E-BDA400B LT	频率范围：410-414/420-424      链路带宽 4MHz     最大射频输出功率 33dBm(2W)	和源通信	套	8396.00	active	\N	2025-04-15 00:23:07.941799	2025-06-05 06:54:59.003288	5	\N
75	项目产品	直放站	HYR2DI010	数字智能光纤近端机	DRFS-100/M	频率范围：150-170MHz 带宽：≤20M 远端携带：32 数字型 功能：触摸屏/网讯平台	和源通信	套	25000.00	active	\N	2025-04-15 00:23:07.94181	2025-06-06 01:41:38.389979	5	\N
81	项目产品	直放站	HYR3DI310	数字智能光纤远端直放站	DRFT-BDA110/M	频率范围：157-161/163-167MHz 带宽：≤4M；输出：10W；数字型 功能：触摸屏/网讯平台 扩展：馈电	和源通信	套	51250.00	active	\N	2025-04-15 00:23:07.941814	2025-06-06 01:45:50.147365	5	\N
71	渠道产品	直放站	HYR3SI140	智能光纤远端直放站	RFT-BDA400B LT/M	频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 1U机箱 功能： 网讯平台	和源通信	套	11851.00	active	\N	2025-04-15 00:23:07.941806	2025-06-05 07:37:02.538839	5	\N
84	项目产品	直放站	HYR3DI340	数字智能光纤远端直放站	DRFT-BDA410/M	频率范围：410-414/420-424MHz 数字带宽：≤4M 输出：10W 数字型 功能：触摸屏/网讯平台 扩展：馈电	和源通信	套	47917.00	active	\N	2025-04-15 00:23:07.941816	2025-06-06 01:46:50.986928	5	\N
43	渠道产品	合路平台	EDULN4N1CZ1	双工器	E-SGQ400N	频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式	和源通信	套	3753.00	active	\N	2025-04-15 00:23:07.941788	2025-06-05 09:34:08.031123	5	\N
41	渠道产品	合路平台	EDUPB5H1CZ1	双工器	E-SGQ350D	频率范围：351-356/361-366MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：5M 安装方式：机柜式 尺寸：2U	和源通信	套	9167.00	discontinued	\N	2025-04-15 00:23:07.941787	2025-06-05 09:32:29.122498	5	\N
42	渠道产品	合路平台	EDULN4N1CZ2	双工器	E-SGQ400N	频率范围：402-406/412-416MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式	和源通信	套	3753.00	active	\N	2025-04-15 00:23:07.941788	2025-06-05 09:32:47.335608	5	\N
83	项目产品	直放站	RC4D2C4IN	数字智能光纤远端直放站	DRFT-BDA400B/M	频率范围: 400-470MHz    工作模式: Digital   最大输出功率: 2W   安装方式: Cabinet 2U    IP防护: IP40   光纤端口类型: LC-LC   功能: NetFlex	和源通信	套	27200.00	discontinued	\N	2025-04-15 00:23:07.941816	2025-06-06 01:46:35.222802	5	\N
35	项目产品	合路平台	MCGFLF52C	一体化分合路矩阵	FHJ400-BLST-4	频率范围: 410-430MHz/350-470MHz    信道端口数: 4    最大输入功率: 250mw/24dB    插入损耗: /    驻波比: ≤1.5    端口隔离度: ≥16dB    电源: 220V/ CN	和源通信	套	18000.00	upcoming	\N	2025-04-15 00:23:07.941783	2025-06-06 07:05:02.895932	5	\N
57	项目产品	合路平台	HYMPC2ACP	系统合路器 | 供电	E-FHP2000-2/P	频率范围：351-366/403-430MHz 单端口承载功率：50W 插入损耗：≤2.0dB 供电模块	和源通信	套	10450.00	discontinued	\N	2025-04-15 00:23:07.941797	2025-06-06 07:11:20.151624	5	\N
110	渠道产品	天线	EANLOMO5HR1	室外全向玻璃钢天线	E-ANTG 400	频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade	和源通信	套	458.00	active	\N	2025-04-15 00:23:07.941833	2025-06-06 07:35:47.327202	5	\N
138	第三方产品	配件	EDFWYFC24W	光纤配线架	ST/FC  24口	尺寸类型：标准尺寸FC口    端口数：24口    产品类型：机架式    特性：含法兰头    不含配套尾纤	国产	套	430.00	active	\N	2025-04-15 00:23:07.941852	2025-06-09 08:54:50.892576	5	\N
139	第三方产品	配件	EDFWYFC48W	光纤配线架	ST/FC 48口	尺寸类型：标准尺寸FC口    端口数：48口    产品类型：机架式    特性：含法兰头    不含配套尾纤	国产	套	860.00	active	\N	2025-04-15 00:23:07.941852	2025-06-09 08:56:17.23201	5	\N
\.


--
-- TOC entry 4069 (class 0 OID 19688)
-- Dependencies: 294
-- Data for Name: project_members; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.project_members (id, project_id, user_id, role, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4071 (class 0 OID 19692)
-- Dependencies: 296
-- Data for Name: project_rating_records; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.project_rating_records (id, project_id, user_id, rating, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4073 (class 0 OID 19697)
-- Dependencies: 298
-- Data for Name: project_scoring_config; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.project_scoring_config (id, category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4075 (class 0 OID 19707)
-- Dependencies: 300
-- Data for Name: project_scoring_records; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.project_scoring_records (id, project_id, category, field_name, score_value, awarded_by, auto_calculated, notes, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4077 (class 0 OID 19717)
-- Dependencies: 302
-- Data for Name: project_stage_history; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.project_stage_history (id, project_id, from_stage, to_stage, change_date, change_week, change_month, change_year, account_id, remarks, created_at) FROM stdin;
1	624	discover	embed	2025-06-13 09:32:31.67804	202523	202506	2025	\N	API推进: lihuawei	2025-06-13 09:32:31.662263
2	624	embed	pre_tender	2025-06-13 09:32:58.200725	202523	202506	2025	\N	API推进: lihuawei	2025-06-13 09:32:58.189192
3	624	pre_tender	pre_tender	2025-06-13 09:32:59.516099	202523	202506	2025	\N	API推进: lihuawei	2025-06-13 09:32:59.506028
4	624	pre_tender	pre_tender	2025-06-13 09:33:00.233571	202523	202506	2025	\N	API推进: lihuawei	2025-06-13 09:33:00.222942
5	624	pre_tender	pre_tender	2025-06-13 09:33:02.538813	202523	202506	2025	\N	API推进: lihuawei	2025-06-13 09:33:02.528174
6	624	pre_tender	tendering	2025-06-13 09:37:34.143954	202523	202506	2025	\N	API推进: lihuawei	2025-06-13 09:37:34.131292
7	624	tendering	awarded	2025-06-13 09:41:12.129269	202523	202506	2025	\N	API推进: admin	2025-06-13 09:41:12.120493
8	624	awarded	quoted	2025-06-13 09:41:37.120674	202523	202506	2025	\N	API推进: admin	2025-06-13 09:41:37.112435
\.


--
-- TOC entry 4079 (class 0 OID 19724)
-- Dependencies: 304
-- Data for Name: project_total_scores; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.project_total_scores (id, project_id, information_score, quotation_score, stage_score, manual_score, total_score, star_rating, last_calculated, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4003 (class 0 OID 18159)
-- Dependencies: 228
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.projects (id, project_name, report_time, project_type, report_source, product_situation, end_user, design_issues, dealer, contractor, system_integrator, current_stage, stage_description, authorization_code, delivery_forecast, quotation_customer, authorization_status, feedback, created_at, updated_at, owner_id, is_locked, locked_reason, locked_by, locked_at, is_active, last_activity_date, activity_reason, vendor_sales_manager_id, rating) FROM stdin;
52	TCL华星光电技术有限公司（中韩合资）TCL华星光电高世代面板产业配套项目（含装配式）	2025-04-18	channel_follow	sales	unqualified	TCL建设管理（深圳）有限公司	\N	上海瀚网智能科技有限公司	\N	\N	discover	2025/4/18 12:00:29 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-016\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/16 周裔锦\r\n\r「王如郑」 TCL建设管理（深圳）有限公司  王经理，介绍项目上近期出了安全问题，所有人员都在做安全管理规范学习，需要改下周到公司去找关键人做品牌入库工作。\r\n\r2025/4/11 12:45:58 周裔锦\r\n\r【直接用户】：添加   TCL建设管理（深圳）有限公司\r\r\n\r\n\r2025/4/9 周裔锦\r\n\r「王如郑」 TCL建设管理（深圳）有限公司  王经理介绍，他们有自己的品牌库，要对接设计院建议先做品牌入库工作，避免浪费时间。了解了入库流程以及关键人联系方式，建议下周再联系拜访。\r\n\r	CPJ202504-016	2025-04-18	0	\N	\N	2025-04-18 00:00:00	2025-04-18 12:00:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
440	武侯人民医院	2025-03-28	channel_follow	marketing	qualified	\N	四川宏利兴建筑工程公司	福淳智能科技(四川)有限公司	\N	四川宏利兴建筑工程公司	embed	2025/4/2 19:07:54 邹娟\r\n\r【完善价格】 121062\r\n\r2025/4/2 18:59:46 邹娟\r\n\r【授权编号】：改变成   HY-CPJ202503-020\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/3/28 16:35:38 邹娟\r\n\r【设计院及顾问】：添加   四川宏利兴建筑工程公司\r\r\n【面价金额】：添加   42690.5\r\r\n【授权编号】：添加   106\r\r\n\r\n\r	CPJ202503-020	2025-04-02	0	\N	\N	2025-03-28 00:00:00	2025-04-02 19:07:00	25	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	\N
267	茂名南站综合交通枢纽配套工程一期	2024-08-23	sales_focus	sales	unqualified	\N	\N	\N	\N	中冶交通建设集团有限公司	discover	2024/10/8 周裔锦\r\n\r【阶段变更】品牌植入->发现\r\r\n\r\n\r	SPJ202408-004	2024-10-08	0	\N	\N	2024-08-23 00:00:00	2024-10-08 15:05:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
190	国深博物馆项目	2024-11-29	sales_focus	sales	unqualified	\N	华南理工大学建筑设计研究院	\N	\N	\N	discover	2025/2/21 13:26:36 周裔锦\r\n\r【当前阶段】：改变成   发现\r\r\n【当前阶段情况说明】：添加   项目属于土建总包招标阶段，智能化部分尚未招标。\r\r\n\r\n\r	SPJ202411-014	2025-02-21	0	\N	\N	2024-11-29 00:00:00	2025-02-21 13:26:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
51	宝龙生物药创新发展先导区（二期）项目	2025-04-18	channel_follow	channel	unqualified	\N	\N	\N	\N	\N	discover	2025/4/18 12:01:17 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-017\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202504-017	2025-04-18	0	\N	\N	2025-04-18 00:00:00	2025-04-18 12:01:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
475	粤港澳科技金融中心二，三期	2025-02-27	channel_follow	channel	\N	\N	\N	北京联航迅达通信技术有限公司	\N	\N	embed	2025/2/27 10:29:57 邹飞\r\n\r【授权编号】：添加   HY-CPJ202404-001\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/25 15:34:50 范敬\r\n\r【完善价格】 904977\r\n\r	CPJ202404-001	2025-02-27	0	\N	\N	2025-02-27 00:00:00	2025-02-27 10:29:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
258	铁汉生态广场	2024-03-03	channel_follow	sales	unqualified	\N	机械工业部深圳设计研究院有限公司	\N	\N	\N	embed	2024/10/27 周裔锦\r\n\r【出现困难】张兴没有跟进，表内联系人：丁瑞斌和程龙没有联系电话。\r\r\n\r\n\r2024/3/3 17:41:13 庄海鑫\r\n\r【提案】  :  项目处于品牌植入阶段，配合设计院完成无线对讲系统部分的设计\r\n\r	CPJ202403-002	2024-10-27	395470	\N	\N	2024-03-03 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
269	漳州军用机场	2024-10-08	sales_focus	sales	unqualified	\N	\N	\N	\N	厦门纵横集团科技股份有限公司	lost	\N	SPJ202410-002	2024-10-08	0	\N	\N	2024-10-08 00:00:00	2025-06-09 01:20:42.061173	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
513	上赛-5月China-GT赛事	2025-05-14	normal			\t上海久事国际体育中心有限公司					signed	5月16-18日赛事，人员保障	\N	2025-05-14	7008	\N	\N	2025-05-14 07:56:24.002787	2025-05-21 13:14:04.436977	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
600	BOC总部大楼项目（伊拉克）	2025-05-29	channel_follow	channel	qualified			敦力(南京)科技有限公司			embed	配合国内集成商参与项目前期品牌植入、方案清单及预算编制	\N	\N	575344	\N	\N	2025-05-29 07:28:24.938353	2025-05-29 07:44:07.615755	16	f	\N	\N	\N	t	2025-05-29 07:28:24.938353	\N	16	1
598	天津宝坻康万佳商业中心	2025-06-12	channel_follow	sales	qualified			天津比信科技股份有限公司		天津市健坤长弘工程股份有限公司	embed	配合集成商出初步方案清单	CPJ202506-018	\N	254494	\N	\N	2025-05-29 06:20:00.898329	2025-06-12 04:08:59.39052	16	f	\N	\N	\N	t	2025-05-29 06:20:00.898329	\N	16	1
105	华泰证券股份有限公司华泰证券研发及培训中心项目	2025-02-20	sales_focus	sales	qualified	华泰证券股份有限公司	中通服咨询设计研究院有限公司	敦力(南京)科技有限公司	\N	\N	embed	2025/4/10 范敬\r\n\r\n「赵婧」 中通服咨询设计研究院有限公司  与设计工程师沟通推荐品牌事宜，目前推荐品牌如下：\r\n信道机和对讲机：摩托罗拉，海能达，和源通信；\r\n信号中继（近、远端直放站）及天馈（天线、功分耦合器）分布：福玛通信、淳泊、和源通信；\r\n线缆：中天、亨鑫、德通；\r\n\r\n2025/2/20 16:41:50 范敬\r\n\r\n【直接用户】：添加   华泰证券股份有限公司\r\n\r\n\r\n\r\n2025/2/20 16:31:25 范敬\r\n\r\n【授权编号】：添加   HY-SPJ202501-006\r\n\r\n【类型】：添加   销售重点\r\n\r\n\r\n\r\n	SPJ202501-006	2025-11-25	413864.63699999993	\N	\N	2025-02-20 00:00:00	2025-06-12 11:52:06.857929	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
435	四川美术学院悦来校区实验中心建设项目	2025-02-28	channel_follow	channel	\N	\N	\N	重庆大鹏鸟科技有限公司	\N	\N	embed	2025/4/3 23:20:24 邹飞\r\n\r【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/28 12:13:14 邹飞\r\n\r【授权编号】：添加   HY-CPJ202408-014\r\r\n\r\n\r	CPJ202408-014	2025-04-03	0	\N	\N	2025-02-28 00:00:00	2025-04-03 23:20:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
467	哗哩哔哩上海总部大楼	2025-02-28	channel_follow	channel	\N	\N	\N	\N	\N	\N	embed	2025/2/28 13:03:48 邹飞\r\n\r【授权编号】：添加   HY-CPJ202409-016\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/17 16:45:40 李华伟\r\n\r【分销商】：添加   上海淳泊\r\r\n【经销商】：添加   上海福玛通信信息科技有限公司\r\r\n\r\n\r2025/2/17 16:22:12 李华伟\r\n\r【授权编号】：改变成   HY-CPJ202409-016\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r	CPJ202409-016	2025-02-28	0	\N	\N	2025-02-28 00:00:00	2025-02-28 13:03:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
318	江苏省妇幼保健院总部项目	2022-11-09	channel_follow	sales	unqualified	\N	\N	敦力(南京)科技有限公司	\N	\N	lost	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、EPC项目，目前大总包已招标完毕。\r\n2、目前北京院在进行智能化设计。\r\n\r2023/11/1 花伟\r\n\r「阶段变更」\r\r\n1、EPC项目，目前大总包已招标完毕。\r\n2、目前北京院在进行智能化设计。\r\n\r	CPJ202211-007	2024-02-29	0	\N	\N	2022-11-09 00:00:00	2025-05-30 10:40:34.188277	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	\N
137	济南市黄冈路穿黄隧道	2025-03-29	channel_follow	sales	qualified	\N	上海市政工程设计研究总院（集团）有限公司	\N	\N	\N	embed	2025/3/29 12:50:13 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202503-018\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r	CPJ202503-018	2025-03-29	0	\N	\N	2025-03-29 00:00:00	2025-03-29 12:50:00	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	\N
426	海南省新国宾馆改造	2025-02-25	channel_follow	sales	qualified	\N	\N	上海瀚网智能科技有限公司	\N	\N	embed	2025/4/3 23:45:41 李冬\r\n\r【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/25 14:17:23 李冬\r\n\r【授权编号】：添加   HY-CPJ202302-001\r\r\n\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n配合设计顾问公司进行项目设计及品牌预算编制\r\n\r	CPJ202302-001	2025-04-03	0	\N	\N	2025-02-25 00:00:00	2025-04-03 23:45:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
433	郑大一附院惠济院区项目	2025-02-28	channel_follow	channel	\N	\N	\N	北京联航迅达通信技术有限公司	\N	北京泰豪智能工程有限公司	embed	2025/4/3 23:22:36 邹飞\r\n\r【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/28 11:45:05 邹飞\r\n\r【授权编号】：添加   HY-CPJ202405-011\r\r\n\r\n\r2024/7/18 08:32:57 范敬\r\n\r【消息】「」目前等待招标\r\n\r2024/5/24 21:40:12 范敬\r\n\r【提案】「」:  配合集成商方案设计并配置清单\r\n\r	CPJ202405-011	2025-04-03	0	\N	\N	2025-02-28 00:00:00	2025-04-03 23:22:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
469	唐镇南社区13A-05地块项目	2025-02-28	channel_follow	channel	\N	\N	\N	上海福玛通信信息科技有限公司	\N	上海益邦智能技术股份有限公司	awarded	2025/2/28 12:05:53 邹飞\r\n\r【授权编号】：添加   HY-CPJ202407-001\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r跟进记录 杨俊杰\r\n\r【阶段变更】中标->签约\r\n\r2024/7/4 杨俊杰\r\n\r该项目渠道报备，反馈之前配合集成商上海益邦参与项目投标。目前益邦已经中标，商务方面正在推进，预计本月会落实结果\r\n\r	CPJ202407-001	2025-02-28	0	\N	\N	2025-02-28 00:00:00	2025-02-28 12:05:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
65	桑田科学岛科创中心项目东片区实验室项目（实验楼、地库及能源中心）	2025-01-07	sales_focus	sales	qualified	\N	\N	\N	\N	江苏瀚远科技股份有限公司	awarded	2025/4/15 范敬\r\n\r\n「姚强」 江苏瀚远科技股份有限公司  沟通项目进展，目前刚刚进场施工，主要集中在桥架管线，系统品牌基本计划在5月中旬确定。目前苏州2家产品商已和他们有所接触；苏州中瀚（孙建忠）已报出非常低的价格；但瀚远目前没有采纳中瀚。\r\n\r\n2025/3/24 13:13:10 范敬\r\n\r\n【出货时间预测】：添加   2025年二季度\r\n\r\n\r\n\r\n2025/3/22 10:02:56 范敬\r\n\r\n【当前阶段】：改变成   中标\r\n\r\n【系统集成商】：添加   江苏瀚远科技股份有限公司\r\n\r\n【当前阶段情况说明】：改变成   已完成招标，中标单位已公示。\r\n\r\n\r\n\r\n2025/2/25 15:20:53 范敬\r\n\r\n【完善价格】 1955362\r\n\r\n2025/1/7 08:50:48 范敬\r\n\r\n【授权编号】：添加   HY-SPJ202412-006\r\n\r\n【类型】：添加   销售重点\r\n\r\n\r\n\r\n	SPJ202412-006	2025-06-25	1016951	\N	\N	2025-01-07 00:00:00	2025-05-28 16:32:34.430616	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
90	中信金融中心项目	2025-04-11	channel_follow	channel	unqualified	\N	\N	上海瀚网智能科技有限公司	\N	中建三局智能技术有限公司深圳分公司	awarded	2025/4/11 11:13:02 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-002\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202504-002	2025-04-11	0	\N	\N	2025-04-11 00:00:00	2025-04-11 11:13:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
28	天津中芯国际-改造项目	2024-12-21	channel_follow	sales	qualified	\N	\N	天津比信科技股份有限公司	\N	\N	embed	2025/4/23 范敬\r\n\r「张群」 天津比信科技股份有限公司  对该项目进行了沟通，目前项目处于停滞阶段。\r\n\r2025/2/25 15:24:56 范敬\r\n\r【完善价格】 362013\r\n\r2025/1/3 范敬\r\n\r类型改变为渠道跟进 \r\n\r	CPJ202412-010	2025-04-23	362013	\N	\N	2024-12-21 00:00:00	2025-05-11 00:59:24.476988	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
597	雄安国贸中心（D03-04-41/42/43/44号地块）项目--酒店区域(42-3)	2025-05-28	sales_focus	sales	qualified		中国建筑设计研究院有限公司				embed	配合设计院完成初步方案预算	\N	\N	276276.924	\N	\N	2025-05-28 09:05:20.746659	2025-05-29 07:10:37.969603	16	t	授权编号审批锁定: 渠道项目报备流程	16	2025-06-12 03:36:35.88057	t	2025-05-28 09:05:20.746659	\N	16	1
519	宁波中哲（浙江）高分子新材料有限公司	2025-06-04	channel_follow	sales	controlled					苏州工业园区汉威控制系统工程有限公司	discover	该项目因舜宇项目合作，苏州汉威负责人冀方萌找到我，目前他们在跟进用户，做前期品牌入围工作，给与品牌建议，与冀方萌沟通，待后续看是否有机会推进设计方案配套	CPJ202506-005	2026-06-30	0	\N	\N	2025-05-16 03:29:33.138015	2025-05-16 03:29:33.138015	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	\N
436	成都音乐文创总部基地7号地块	2025-03-28	channel_follow	marketing	qualified	\N	\N	\N	\N	四川欣奕建设工程有限公司	pre_tender	2025/4/3 22:45:28 邹娟\r\n\r【完善价格】 561290\r\n\r2025/4/2 18:58:51 邹娟\r\n\r【授权编号】：改变成   HY-CPJ202503-032\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/3/28 17:10:52 邹娟\r\n\r【授权编号】：添加   107\r\r\n\r\n\r	CPJ202503-032	2025-04-03	0	\N	\N	2025-03-28 00:00:00	2025-04-03 22:45:00	25	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	\N
468	洋泾西区EC8-4、E10-2、E12-1地块	2025-02-28	channel_follow	channel	\N	\N	\N	上海福玛通信信息科技有限公司	\N	上海行余信息技术有限公司	pre_tender	2025/2/28 13:00:35 邹飞\r\n\r【授权编号】：添加   HY-CPJ202409-015\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/26 10:46:46 邹飞\r\n\r【授权编号】：改变成   HY-CPJ202409-015\r\r\n\r\n\r	CPJ202409-015	2025-02-28	0	\N	\N	2025-02-28 00:00:00	2025-02-28 13:00:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
194	苏州漕湖商务中心项目	2022-11-08	sales_focus	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	尚高科技有限公司	embed	2025/2/21 11:55:16 范敬\r\n\r\n【当前阶段】：改变成   搁置\r\n\r\n【当前阶段情况说明】：添加   处于暂停状态，业主在走内部流程\r\n\r\n\r\n\r\n2024/6/29 11:06:21 范敬\r\n\r\n【消息】「」预计三季度项目会进入启动\r\n\r\n2024/6/9 12:38:16 范敬\r\n\r\n【提案】「」:  与集成商沟通了项目后续招标清单，根据需求建议采用MA12天线及配置清单。\r\n\r\n2023/11/1 范敬\r\n\r\n「阶段变更」\r\n\r\n1、项目整体为EPC方式，目前集成商已通过业主成为意向中标方。项目整体设计由集成商负责，目前已完成系统整体设计（按和源产品），品牌推荐为和源。\r\n2、目前方案已经过技防办评审，进入编标阶段。\r\n\r\n	SPJ202211-002	2025-06-26	591916	\N	\N	2022-11-08 00:00:00	2025-05-30 02:56:26.512904	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
521	乐青研究基地	2025-05-16	channel_follow	channel	qualified			上海福玛通信信息科技有限公司		上海市安装工程集团有限公司-第九分公司	tendering	渠道报备，配合上安九分、浙江奥乐参与项目投标报价	\N	2026-06-30	217007	\N	\N	2025-05-16 03:45:21.046977	2025-05-16 03:52:15.73953	14	t	授权编号审批锁定: 渠道项目报备流程	14	2025-05-30 07:11:38.671608	t	2025-05-24 05:20:56.993177	\N	14	1
6	静安假日酒店	2024-05-17	channel_follow	channel	controlled	\N	\N	\N	\N	上海奂源工程设备有限公司	signed	2025/4/25 18:28:07 李华伟\r\n\r\n【出货时间预测】：改变成   2025-05-23\r\n\r\n\r\n\r\n2025/4/6 09:36:30 李华伟\r\n\r\n【完善价格】 190200\r\n\r\n2025/3/24 10:00:35 李华伟\r\n\r\n【出货时间预测】：改变成   2025年二季度\r\n\r\n\r\n\r\n2025/2/17 14:39:39 李华伟\r\n\r\n【当前阶段情况说明】：添加   代理商反馈合同预计2月底-3月签约，现场还没提起采购流程，价格基本已经初步确认。\r\n\r\n\r\n\r\n45674.4659837963 李冬\r\n\r\n【出货时间预测】：添加   2025年一季度\r\n\r\n\r\n\r\n2025/1/17 11:11:01 李华伟\r\n\r\n【出货时间预测】：添加   2025年一季度\r\n\r\n\r\n\r\n45596.7189236111 李冬\r\n\r\n【完善价格】 202700\r\n\r\n2024/10/31 17:15:15 李华伟\r\n\r\n【完善价格】 202700\r\n\r\n45443.6553935185 李冬\r\n\r\n【阶段变更】招标前->中标\r\n\r\n2024/5/31 15:43:46 李华伟\r\n\r\n【阶段变更】招标前->中标\r\n\r\n45429 李冬\r\n\r\n【提案】: 瀚网配合集成商设计，植入围标品牌。预计即将招标，集成商操作此项目，几率较大。\r\n\r\n2024/5/17 李华伟\r\n\r\n【提案】: 瀚网配合集成商设计，植入围标品牌。预计即将招标，集成商操作此项目，几率较大。\r\n\r\n	CPJ202405-007	2025-05-25	190200	\N	\N	2024-05-17 00:00:00	2025-05-30 03:15:30.541505	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
244	佛山市禅城区华侨城绿景东路南侧、华祥路北侧、规划十四路东侧地块项目	2024-11-29	channel_follow	channel	qualified	\N	\N	广州宇洪科技股份有限公司	\N	\N	pre_tender	2024/11/29 12:59:32 周裔锦\r\n\r【完善价格】 64246\r\n\r	CPJ202411-015	2024-11-29	64246	\N	\N	2024-11-29 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
47	深圳职业技术学院深汕校区项目	2025-04-18	channel_follow	channel	unqualified	\N	华阳国际设计集团	上海瀚网智能科技有限公司	\N	\N	discover	2025/4/18 16:06:15 周裔锦\r\n\r【设计院及顾问】：添加   华阳国际设计集团\r\r\n\r\n\r2025/4/18 12:05:04 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-020\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/16 周裔锦\r\n\r「焦培荣」 华阳国际设计集团  焦总介绍，本项目分四个单位配合设计，分别是华阳、华东、浙江院、北京院。他们这边到时候让我们配合，最好去找剩下的三个院沟通，大家也希望尽量做到统一，避免后续的扯皮。\r\n\r	CPJ202504-020	2025-04-18	0	\N	\N	2025-04-18 00:00:00	2025-04-18 16:06:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
288	长春瑯珀凯越甄选酒店	2023-11-01	channel_follow	sales	controlled	\N	吉林省济远建设有限公司	北京联航迅达通信技术有限公司	\N	吉林省济远建设有限公司	embed	2024/7/18 08:11:28 范敬\r\n\r【消息】「」目前没有新进展\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、配合出清单、图纸；\r\n\r	CPJ202311-001	2024-07-18	146451	\N	\N	2023-11-01 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
235	琶洲算谷	2024-04-30	sales_focus	sales	qualified	\N	广东省建筑设计研究院有限公司	广州宇洪智能技术有限公司	\N	\N	pre_tender	2024/12/15 周裔锦\r\n\r类型改变为销售重点 \r\n\r2024/11/29 周裔锦\r\n\r【阶段变更】中标->招标前\r\r\n\r\n\r2024/11/22 周裔锦\r\n\r【出现困难】中建三局二安公司已经中标，目前文工在核对图纸，等核对完成后让我们配合深化。\r\r\n\r\n\r2024/9/6 17:27:21 庄海鑫\r\n\r【阶段变更】品牌植入->失败\r\r\n\r\n\r2024/4/30 庄海鑫\r\n\r【提案】:  根据项目情况推荐对讲+巡更的方案\r\n\r	SPJ202404-006	2024-12-15	315624	\N	\N	2024-04-30 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
601	阿里达摩院增补改建	2025-06-04	channel_follow	channel	not_required			浙江航博智能工程有限公司		浙大网新系统工程有限公司	embed	项目原系统汉界实施，系统重新改造，目前代理商航博在配合客户投标，品牌原来是摩托，尝试换成和源。	CPJ202506-002	\N	168556	\N	\N	2025-05-30 06:15:20.863758	2025-06-04 00:57:37.130119	15	f	\N	\N	\N	t	2025-05-30 06:15:20.863758	\N	15	1
437	重庆鹿角隧道	2025-03-14	channel_follow	channel	qualified	\N	四川欣邦高科科技有限公司	福淳智能科技(四川)有限公司	\N	\N	tendering	2025/4/3 22:21:31 邹娟\r\n\r【完善价格】 952387\r\n\r2025/4/3 22:07:26 邹娟\r\n\r【经销商】：添加   福淳智能科技(四川)有限公司\r\r\n\r\n\r2025/4/2 19:26:41 邹娟\r\n\r【完善价格】 775577\r\n\r2025/3/14 22:15:39 邹娟\r\n\r【授权编号】：添加   HY-CPJ202503-009\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/3/14 22:10:24 邹娟\r\n\r【当前阶段】：添加   招标中\r\r\n【当前阶段情况说明】：添加   隧道项目总包已订，分包询价报价\r\r\n\r\n\r2025/3/14 22:07:27 邹娟\r\n\r【品牌情况】：添加   入围\r\r\n【设计院及顾问】：添加   四川欣邦高科科技有限公司\r\r\n【分销商】：添加   上海淳泊\r\r\n\r\n\r	CPJ202503-009	2025-04-03	0	\N	\N	2025-03-14 00:00:00	2025-04-03 22:21:00	25	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
266	厦门嘉丽广场	2024-09-27	channel_follow	channel	unqualified	\N	\N	广州宇洪科技股份有限公司	\N	广东省工业设备安装有限公司	tendering	2024/10/9 17:08:15 周裔锦\r\n\r【完善价格】 164492\r\n\r2024/10/9 16:51:43 周裔锦\r\n\r【完善价格】 152365\r\n\r2024/10/8 周裔锦\r\n\r【阶段变更】->招标中\r\r\n\r\n\r	CPJ202409-012	2024-10-09	164492	\N	\N	2024-09-27 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
10	长兴镇38-07地块	2025-04-21	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海数码通系统集成有限公司	tendering	2025/4/25 14:29:03 杨俊杰\r\n\r【完善价格】 157618\r\n\r2025/4/21 11:52:09 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202504-025\r\n\r\r\n\r2025/4/18 17:09:26 杨俊杰\r\n\r提交报备\r\n\r	CPJ202504-025	2025-04-25	157618	\N	\N	2025-04-21 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
535	德赛西威中西部基地（一期）项目	2025-04-22	channel_follow	channel	qualified			福淳智能科技(四川)有限公司			tendering	代商理配合当地集成商投标	\N	2025-05-16	258920	\N	\N	2025-05-16 05:21:58.538958	2025-06-11 14:45:59.959632	13	t	授权编号审批锁定: 渠道项目报备流程	13	2025-06-11 06:41:27.112471	t	2025-05-24 05:20:56.993177	\N	13	1
62	南京惠民路隧道项目	2022-11-08	sales_focus	sales	qualified	\N	苏交科集团股份有限公司南京设计中心	敦力(南京)科技有限公司	\N	北京瑞华赢科技发展股份有限公司	quoted	2025/4/17 范敬\r\n\r\n「郭金亮」 北京瑞华赢科技发展股份有限公司  配合集成商完成询价工作\r\n\r\n2025/4/11 范敬\r\n\r\n「郭金亮」 北京瑞华赢科技发展股份有限公司  沟通项目目前推进情况，配合准备相关资料；项目负责人透露目前已有海能达代理商通过相关人员介绍在接触项目部。\r\n\r\n2025/2/21 11:24:11 范敬\r\n\r\n【当前阶段】：改变成   中标\r\n\r\n【系统集成商】：添加   北京瑞华赢科技发展股份有限公司\r\n\r\n【当前阶段情况说明】：添加   机电分包单位已中标。\r\n\r\n\r\n\r\n2024/7/20 14:19:29 范敬\r\n\r\n【消息】「」目前主体结构基本结束，计划2024年四季度开始机电招标，计划2025年完工。土建总包单位：中铁四局。\r\n\r\n2023/11/1 范敬\r\n\r\n「阶段变更」\r\n\r\n项目设计已结束，目前项目在审图阶段；按和源品牌设计。\r\n该项目EPC总承包，已进入总包预算询价中。后期会采用专业分包模式。\r\n\r\n	SPJ202211-004	2025-06-24	480232	\N	\N	2022-11-08 00:00:00	2025-06-10 02:57:41.341338	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
50	机场东车辆段上盖物业开发项目	2025-04-18	channel_follow	sales	unqualified	\N	香港华艺设计顾问（深圳）有限公司	上海瀚网智能科技有限公司	\N	深圳达实智能股份有限公司	discover	2025/4/18 12:03:30 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-018\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/17 周裔锦\r\n\r「何雁」 香港华艺设计顾问（深圳）有限公司  何总介绍，深铁置业让他们配合出设计规范，这个工作大概会在5-6月启动，到时候需要将我们上海做的无线对讲行业规范梳理出核心关键，给到他们。\r\n河套项目还在做土建设计，智能化还远。\r\n\r2025/3/28 16:40:35 周裔锦\r\n\r【系统集成商】：改变成   深圳达实智能股份有限公司\r\r\n\r\n\r2025/3/25 21:57:11 周裔锦\r\n\r【当前阶段】：添加   发现\r\r\n\r\n\r2025/2/28 16:28:54 周裔锦\r\n\r【系统集成商】：添加   深圳市燕翔云天科技有限公司\r\r\n\r\n\r2025/2/14 19:49:09 周裔锦\r\n\r【设计院及顾问】：添加   香港华艺设计顾问（深圳）有限公司\r\r\n【当前阶段情况说明】：添加   深圳壹创国际负责总包设计，华艺负责智能化设计，何雁介绍本项目属于地铁，地铁项目可能不会定品牌，最好跟总包或者智能化分包配合。\r\r\n\r\n\r	CPJ202504-018	2025-04-18	0	\N	\N	2025-04-18 00:00:00	2025-04-18 12:03:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
438	宜宾城市体育文化综合体项目	2025-04-03	channel_follow	channel	\N	\N	\N	福淳智能科技(四川)有限公司	\N	\N	embed	2025/4/3 22:07:05 邹娟\r\n\r【授权编号】：添加   HY-CPJ202504-005\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202504-005	2025-04-03	0	\N	\N	2025-04-03 00:00:00	2025-04-03 22:07:00	25	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	\N
49	珠海市九洲港客运站场及配套设施项目客运港区域智能化工程	2025-04-18	channel_follow	sales	unqualified	\N	\N	广州洪昇智能科技有限公司	\N	\N	pre_tender	2025/4/18 12:04:19 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-019\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/7 17:41:37 周裔锦\r\n\r【完善价格】 205591\r\n\r2025/4/7 16:55:38 周裔锦\r\n\r【当前阶段】：添加   招标前\r\r\n【当前阶段情况说明】：添加   投标前报价。\r\r\n\r\n\r2025/4/7 16:51:02 周裔锦\r\n\r【系统集成商】：添加   珠海华发数智技术有限公司\r\r\n\r\n\r	CPJ202504-019	2025-04-18	205591	\N	\N	2025-04-18 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
536	大渡河公司大岗山项目	2025-04-12	channel_follow	channel	qualified			成都市天皓科技有限公司			pre_tender		CPJ202412-001	2025-05-16	118460	yes	\N	2025-05-16 05:28:23.573688	2025-05-16 07:17:21.737345	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
532	重庆天玺壹号168亩	2024-07-14	channel_follow	channel	qualified			福淳智能科技(四川)有限公司			awarded	集成商已中标，福淳在对接	CPJ202407-006	2025-10-16	145461	yes	\N	2025-05-16 04:44:25.57084	2025-05-16 04:53:44.179548	25	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
546	衢州希尔顿	2024-03-15	channel_follow	channel	qualified			浙江航博智能工程有限公司		浙江建工设备安装有限公司	awarded	前期航博配合集成商设计植入和源品牌，对讲机后续在操作沟通换成和源，预计7-8月份进场。	CPJ202403-004	2025-06-25	292672	yes	\N	2025-05-16 06:26:08.851229	2025-06-03 04:01:34.858484	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
256	上海黄浦江南自延伸段WS3单元xh130E街坊	2024-08-09	channel_follow	channel	qualified	\N	\N	广州宇洪科技股份有限公司	\N	厦门万安智能有限公司	tendering	2024/10/27 周裔锦\r\n\r【出现困难】裴小印说同事在跟进中，要跟同事同步后反馈给我最新结果。\r\r\n\r\n\r	CPJ202408-006	2024-10-27	0	\N	\N	2024-08-09 00:00:00	2024-10-27 21:20:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
39	舜宇12英寸透明衬底晶圆AR眼镜微纳光学产品	2025-03-13	sales_focus	sales	qualified	舜宇奥来微纳光学（上海）有限公司	\N	上海瀚网智能科技有限公司	\N	苏州工业园区汉威控制系统工程有限公司	signed	2025/4/21 13:14:46 杨俊杰\r\n\r申请项目批价\r\n\r2025/4/21 13:13:58 杨俊杰\r\n\r【完善价格】 47586\r\n\r2025/4/21 13:09:37 杨俊杰\r\n\r【完善价格】 37710\r\n\r2025/4/21 杨俊杰\r\n\r「柴经理」 苏州工业园区汉威控制系统工程有限公司  跟踪渠道，确认商务合同已经确认，发起渠道业务批价确认\r\n\r2025/4/13 15:36:31 杨俊杰\r\n\r【完善价格】 47611\r\n\r2025/3/29 12:54:56 杨俊杰\r\n\r【出货时间预测】：改变成   2025年二季度\r\n\r\r\n\r2025/3/13 14:05:14 杨俊杰\r\n\r【出货时间预测】：改变成   舜宇奥来微纳光学（上海）有限公司「2025年二季度」\r\n\r【授权编号】：添加   HY-SPJ202502-002\r\n\r【类型】：添加   销售重点\r\n\r\r\n\r	SPJ202502-002	2025-04-21	47586	\N	\N	2025-03-13 00:00:00	2025-05-30 07:18:08.016186	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
185	嘉定区嘉定新城主城区JDC11201单元26-04地块	2024-10-08	channel_follow	channel	qualified	\N	\N	上海艾亿智能科技有限公司	\N	上海电器科学研究所集团有限公司	tendering	2025/2/21 16:29:49 杨俊杰\r\n\r【完善价格】 137091\r\n\r2024/10/8 13:04:07 杨俊杰\r\n\r【完善价格】 140961\r\n\r	CPJ202410-002	2025-02-21	137091	\N	\N	2024-10-08 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
8	广州鼎信科技有限公司室内无线对讲及巡更系统运维设备采购项目	2025-04-25	channel_follow	channel	unqualified	广州鼎信科技有限公司	\N	上海瀚网智能科技有限公司	\N	\N	embed	2025/4/25 15:00:02 周裔锦\r\n\r【直接用户】：添加   广州鼎信科技有限公司\r\r\n\r\n\r2025/4/25 11:28:59 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-036\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/25 10:52:25 周裔锦\r\n\r【完善价格】 273631\r\n\r2025/4/25 10:45:00 周裔锦\r\n\r【当前阶段情况说明】：改变成   广州鼎信科技有限公司生产厂区内使用，由他们自己内部采购和施工。\r\r\n\r\n\r2025/4/23 周裔锦\r\n\r「秦家俊」 广州鼎信科技有限公司  秦经理介绍，老板暂时叫停了我们系统，觉得报价高。项目目前在走管线，约了秦经理后续拜访，与技术当面核对配置，了解秦经理是否有个人述求。\r\n\r	CPJ202504-036	2025-04-25	273631	\N	\N	2025-04-25 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
471	北京CBD核心区Z3 地块项目智能化分包工程	2025-02-28	channel_follow	channel	qualified	\N	\N	\N	\N	太极计算机股份有限公司	embed	2025/2/28 11:32:40 邹飞\r\n\r【授权编号】：添加   HY-CPJ202405-001\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/5/6 范敬\r\n\r【提案】:  配合集成商清单及方案植入\r\n\r	CPJ202405-001	2025-02-28	0	\N	\N	2025-02-28 00:00:00	2025-02-28 11:32:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
20	广州珠江科技创新园五星级酒店及酒店式公寓项目	2025-04-25	channel_follow	channel	qualified	\N	\N	广州洪昇智能科技有限公司	\N	\N	embed	2025/4/25 11:13:01 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-035\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202504-035	2025-04-25	0	\N	\N	2025-04-25 00:00:00	2025-04-25 11:13:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
41	杨浦区定海社区G1-2地块（定海138街坊）	2025-04-21	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海万坤实业发展有限公司	tendering	2025/4/21 11:51:27 杨俊杰\r\n\r【当前阶段】：改变成   招标中\r\n\r\r\n\r2025/4/21 11:51:16 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202504-024\r\n\r\r\n\r2025/4/18 17:06:14 杨俊杰\r\n\r提交报备\r\n\r	CPJ202504-024	2025-04-21	77435	\N	\N	2025-04-21 00:00:00	2025-05-30 14:17:03.476549	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
138	湖北交投实业大厦	2025-03-28	channel_follow	channel	qualified	\N	\N	广州宇洪科技股份有限公司	\N	武汉烽火信息集成技术有限公司	awarded	2025/3/28 17:34:55 周裔锦\r\n\r\n【系统集成商】：添加   武汉烽火信息集成技术有限公司\r\n\r\n\r\n\r\n2025/3/28 17:11:56 周裔锦\r\n\r\n【授权编号】：添加   HY-CPJ202306-003\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n2025/3/3 10:27:01 郭小会\r\n\r\n【当前阶段】：改变成   转移\r\n\r\n【当前阶段情况说明】：添加   此项目宇洪在跟进，转移到南区销售周裔锦那边\r\n\r\n【类型】：改变成   渠道跟进\r\n\r\n\r\n\r\n2024/11/23 郭小会\r\n\r\n【阶段变更】品牌植入->中标\r\n\r\n\r\n\r\n2024/3/8 13:32:24 郭小会\r\n\r\n安排宇洪的李小飞去对接潜在的集成商\r\n\r\n2024/2/29 11:24:21 郭小会\r\n\r\n和天华设计杨经理确认，品牌这块去年和业主沟通完后，业主坚持对讲机要用摩托罗拉的。\r\n\r\n2023/11/1 郭小会\r\n\r\n项目前期设计\r\n\r\n	CPJ202306-003	2025-07-01	434195	\N	\N	2025-03-28 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
603	静安图书馆二期	2025-06-04	channel_follow	sales	qualified		上海现代建筑设计研究院有限公司				discover	该项目闻锋找到我们，配合前期方案扩粗，提供系统概算用于项目报批预算	CPJ202506-003	\N	149031	\N	\N	2025-05-30 07:20:55.517236	2025-06-04 01:03:44.454329	14	f	\N	\N	\N	t	2025-05-30 07:20:55.517236	\N	14	1
139	恒力集团深圳湾超级总部基地	2025-03-25	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	\N	tendering	2025/3/25 21:45:34 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202503-024\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202503-024	2025-03-25	0	\N	\N	2025-03-25 00:00:00	2025-03-25 21:45:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
514	广佛环线广州南站至白云机场段公安安防通信系统	2025-05-15	channel_follow	sales	not_required						discover	合作伙伴深圳信元刘总介绍，集成商投标前询价阶段，5月13号报名截止，目前已购买标书，28号投标。	\N	2025-05-15	2454599	pending	申请备注: 目前已经跟合作伙伴深圳信元确认，使用我品牌去投标。需要我方开唯一授权支持。	2025-05-15 12:35:50.030336	2025-05-15 12:42:54.561649	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
13	深圳中芯-调度录音	2025-04-25	business_opportunity	\N	\N	中芯国际集成电路制造（深圳）有限公司	\N	\N	\N	\N	pre_tender	2025/4/25 13:23:28 方玲\r\n\r【授权编号】：添加   HY-APJ-202504-008\r\r\n\r\n\r2025/4/24 17:06:46 方玲\r\n\r【完善价格】 32800\r\n\r	APJ202504-008	2025-04-25	19800	\N	\N	2025-04-25 00:00:00	2025-05-11 00:59:24.476988	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	1
257	淀山湖喜来登、雅乐轩项目	2023-11-22	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳达实智能股份有限公司	signed	2024/10/27 周裔锦\r\n\r【出现困难】张兴说本项目还在待签约状态，最快四季度能下来。\r\r\n\r\n\r2024/7/1 10:49:02 庄海鑫\r\n\r【阶段变更】中标->签约\r\n\r2023/11/1 庄海鑫\r\n\r1、目前项目已由深圳达智能中标，进行询价阶段。\r\n2、代理商已寄样给到达实\r\n\r	CPJ202311-005	2024-10-27	39376.34999999999	\N	\N	2023-11-22 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
122	集成电路 远端机	2025-04-02	business_opportunity	\N	qualified	上海集成电路研发中心有限公司	\N	\N	\N	\N	tendering	2025/4/2 10:07:25 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-001\r\r\n\r\n\r2025/3/5 10:26:14 方玲\r\n\r【完善价格】 16000\r\n\r	APJ202503-001	2025-04-02	16000	\N	\N	2025-04-02 00:00:00	2025-06-04 14:25:47.398803	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	1
53	粤海云港城	2025-04-18	channel_follow	channel	qualified	\N	\N	\N	\N	广州鑫宇视通科技有限公司	pre_tender	2025/4/18 11:59:46 周裔锦\r\n\r【系统集成商】：添加   广州鑫宇视通科技有限公司\r\r\n【授权编号】：添加   HY-CPJ202504-021\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/18 11:48:21 周裔锦\r\n\r【完善价格】 859965\r\n\r2025/4/18 11:25:46 周裔锦\r\n\r【完善价格】 13580\r\n\r	CPJ202504-021	2025-04-18	859965	\N	\N	2025-04-18 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
575	祐富百胜宝总部项目	2025-05-18	sales_focus	sales	unqualified		奥意建筑工程设计有限公司				discover		\N	\N	0	\N	\N	2025-05-18 12:37:05.892646	2025-05-18 12:37:05.892646	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
576	深圳市创鑫激光股份有限公司深圳市创鑫激光谷项目	2025-05-18	sales_focus	sales	unqualified		华阳国际设计集团				discover		\N	\N	0	\N	\N	2025-05-18 12:38:09.280568	2025-05-18 12:38:09.280568	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
578	平安汽融大厦项目	2025-05-18	sales_focus	channel	unqualified			上海瀚网智能科技有限公司		深圳达实智能股份有限公司	discover		\N	\N	0	\N	\N	2025-05-18 12:42:01.246029	2025-05-18 12:42:01.246029	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
583	广州珠江科技孵化园项目	2025-05-18	channel_follow	channel	qualified			广州洪昇智能科技有限公司			embed		\N	\N	0	\N	\N	2025-05-18 12:55:22.873893	2025-05-22 07:37:35.417094	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
218	深圳湾超级总部基地C塔项目	2024-09-13	sales_focus	channel	unqualified	\N	深圳市建筑设计研究总院有限公司	上海瀚网智能科技有限公司	\N	\N	embed	2025/1/3 09:40:51 周裔锦\r\n\r【完善价格】 1089433\r\n\r2024/12/15 周裔锦\r\n\r类型改变为销售重点 \r\n\r2024/9/13 周裔锦\r\n\r【出现困难】当前配合设计院做方案，业主需求不清晰，还需要进一步了解确定预算和需求。\r\r\n类型改变为渠道管理 \r\n\r	SPJ202409-006	2025-01-03	1089433	\N	\N	2024-09-13 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
528	真如副中心地下公共车行通道	2025-06-02	sales_focus	sales			上海市城市建设设计研究总院 ( 集团) 有限公司				embed	该项目城建院卢洪祥负责智能化设计，经了解项目为改造，需要增加除常规调度以外应急对讲通信，涵盖公安、消防及广播，配合做方案规划	SPJ202506-001	2025-05-16	557063	\N	申请备注: 项目为新增业务，考虑业务为行业项目，目前配合设计院在推进方案植入，申请重点业务跟进	2025-05-16 04:13:02.499773	2025-06-02 01:34:43.647022	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
240	重庆协和医院	2024-11-26	channel_follow	channel	qualified	\N	\N	北京佰沃信通科技有限公司	\N	中国建筑第八工程局有限公司	signed	2024/12/6 杨俊杰\r\n\r【阶段变更】中标->签约\r\n\r\r\n\r2024/11/29 16:11:48 杨俊杰\r\n\r【完善价格】 531084\r\n\r2024/11/26 15:30:51 杨俊杰\r\n\r【完善价格】 521946\r\n\r	CPJ202411-012	2025-04-25	169946.88	\N	\N	2024-11-26 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
580	罗山科技园	2025-05-18	sales_focus	sales	not_required		华阳国际设计集团	上海瀚网智能科技有限公司		霍尼韦尔智能建筑与家居集团	awarded		\N	\N	0	\N	\N	2025-05-18 12:46:05.315808	2025-05-19 01:35:43.218792	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
581	九江市市民活动中心项目	2025-05-18	channel_follow	channel	qualified			上海瀚网智能科技有限公司		广东宏景科技股份有限公司	tendering		\N	\N	0	\N	\N	2025-05-18 12:53:22.298422	2025-05-22 07:38:04.970221	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
585	德赛西威中西部基地	2025-05-18	sales_focus	sales	qualified			广州洪昇智能科技有限公司		联通数字科技有限公司	discover		\N	\N	0	\N	\N	2025-05-18 12:57:18.653496	2025-05-18 12:57:18.653496	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
80	浙江横店喜来登业	2025-03-13	channel_follow	channel	controlled	\N	\N	上海艾亿智能科技有限公司	\N	\N	tendering	2025/4/13 15:28:29 杨俊杰\r\n\r【完善价格】 171215\r\n\r2025/4/13 15:21:57 杨俊杰\r\n\r【当前阶段】：改变成   招标中\r\n\r【分销商】：添加   上海瑞康\r\n\r【当前阶段情况说明】：改变成   该项目招标，经核实品牌的确如艾亿梅小好反馈一致。现阶段范敬区域代理商在配合参与投标，给与指导价格\r\n\r\r\n\r2025/3/13 14:07:05 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202502-016\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r	CPJ202502-016	2025-04-13	171215	\N	\N	2025-03-13 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
24	张家浜绿地C1B-02和C1C-01地块	2025-03-07	channel_follow	sales	controlled	\N	卓展工程顾问(北京)有限公司-上海分公司	上海艾亿智能科技有限公司	\N	\N	tendering	2025/4/24 杨俊杰\r\n\r「梅小好」 上海艾亿智能科技有限公司  张家浜业务招标，目前询价仅壹杰和九分及九分分包单位，与梅小好沟通复核情况。经了解基本确认壹杰中标C1B-02地块，而九分会中标C1C-01地块，但九分即使中标还是通过另外一家采购，关系基本都是另外一家在处理\r\n\r2025/4/13 15:24:01 杨俊杰\r\n\r【当前阶段】：改变成   招标中\r\n\r【当前阶段情况说明】：改变成   该项目招标，李华伟配套壹杰，通过招标资料了解招标品牌，基站设备未入围，仅传输设备围标，为和源、瀚网及福玛\r\n\r\r\n\r2025/4/10 13:30:50 杨俊杰\r\n\r【当前阶段】：改变成   招标前\r\n\r【当前阶段情况说明】：添加   该项目预计二季度招标，目前已知潜在参与集成商：信业、中建电子、益邦及万安，品牌初步确认为可控范围，待项目招标，复核招标品牌，了解具体参与集成商信息，跟进配合投标\r\n\r\r\n\r2025/4/10 杨俊杰\r\n\r「梅小好」 上海艾亿智能科技有限公司  与梅小好沟通反馈有集成商挂靠九分资质，通过初步复核品牌的确可控，但参与集成商通过九分关系了解到并没有参考招标品牌，用的是浙江尧起，将次情况让梅小好复核集成商信息，判断用户除了品牌招标在可控范围内以外，是否有能力可以掌控集成商。项目预计二季度招标，潜在参与集成商：信业、中建电子、益邦及万安都有可能参与，待项目正式招标，了解参与集成商具体情况\r\n\r2025/3/7 11:31:43 杨俊杰\r\n\r【授权编号】：改变成   HY-CPJ202408-018\r\n\r【类型】：改变成   渠道跟进\r\n\r\r\n\r2025/2/21 16:35:09 杨俊杰\r\n\r【完善价格】 477632\r\n\r2024/12/27 杨俊杰\r\n\r类型改变为渠道跟进 \r\n\r2024/9/20 16:48:18 杨俊杰\r\n\r【完善价格】 490551\r\n\r	CPJ202408-018	2025-04-24	477632	\N	\N	2025-03-07 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
18	御桥12C-18地块	2025-04-18	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海鼎时智能化设备工程有限公司	signed	2025/4/25 12:42:32 杨俊杰\r\n\r[阶段变更] ->签约\r\n\r2025/4/21 14:35:57 杨俊杰\r\n\r申请项目批价\r\n\r2025/4/18 17:02:27 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202401-005\r\n\r\r\n\r2025/4/14 21:02:53 杨俊杰\r\n\r提交报备\r\n\r2025/4/14 21:02:32 杨俊杰\r\n\r提交报备\r\n\r2025/4/13 16:06:14 杨俊杰\r\n\r提交报备\r\n\r2025/4/13 15:54:34 杨俊杰\r\n\r【完善价格】 81095\r\n\r2024/2/21 12:29:51 李华伟\r\n\r类型改变为  渠道跟进     \r\n\r45343.5207291667 邹飞\r\n\r类型改变为  渠道跟进     \r\n\r2023/11/1 李华伟\r\n\r品牌入围，目前代理商淳泊配合行余凯通投标，后续跟进投标结果。\r\n\r45231 邹飞\r\n\r品牌入围，目前代理商淳泊配合行余凯通投标，后续跟进投标结果。\r\n\r	CPJ202401-005	2025-04-25	36492.299999999996	\N	\N	2025-04-18 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
573	中欧轨道智能交通国际研创基地启动区项目智城大厦	2024-05-24	channel_follow	channel	qualified			敦力(南京)科技有限公司			tendering		\N	2025-07-24	191777	\N	\N	2025-05-16 09:07:34.587643	2025-05-28 06:29:07.603949	16	t	授权编号审批锁定: 渠道项目报备流程	16	2025-06-12 03:40:23.787371	t	2025-05-24 05:20:56.993177	\N	16	1
19	西丽综合交通枢纽工程	2025-04-25	channel_follow	sales	unqualified	\N	深圳市建筑设计研究总院有限公司	上海瀚网智能科技有限公司	\N	\N	discover	2025/4/25 11:29:38 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-037\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/3/25 21:56:35 周裔锦\r\n\r【当前阶段】：添加   发现\r\r\n【分销商】：添加   上海瑞康\r\r\n【当前阶段情况说明】：添加   设计院介绍，目前在做智能化整体设计，还没有到施工图。\r\r\n\r\n\r2025/2/28 17:05:58 周裔锦\r\n\r【设计院及顾问】：添加   深圳市建筑设计研究总院有限公司\r\r\n\r\n\r	CPJ202504-037	2025-04-25	0	\N	\N	2025-04-25 00:00:00	2025-04-25 11:29:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
517	松江海螺水泥	2025-05-16	channel_follow	sales	qualified					上海华虹智联信息科技有限公司	awarded	该项目集成商华虹智联中标，渠道瀚网跟进，目前深化方案已经确认，原定采购计划在二季度，但集成商项目经理迟迟没有下采购计划，与其沟通了解主要因为甲方资金付款有些问题，所以暂且不着急，目前安排渠道张国栋定期跟进了解项目进度	CPJ202403-011	2025-08-31	152502	yes	申请备注: 该项目为老项目报表中未导入成功，重新提交，代理商瀚网，因客户负责人归属权在其他销售手中，无法登记	2025-05-16 03:04:45.242692	2025-05-26 14:47:23.052898	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
586	杭州市富阳区粮食收储有限公司富阳区第二粮库二期工程	2025-05-19	channel_follow	channel	qualified			杭州合义信息技术有限公司			discover	前期植入品牌方案阶段，意向代理商报备项目，后续跟进辅助对方植入方案品牌工作。	\N	\N	0	\N	\N	2025-05-19 01:17:00.195348	2025-05-19 01:17:00.195348	15	t	授权编号审批锁定: 渠道项目报备流程	15	2025-06-03 03:21:09.363589	t	2025-05-24 05:20:56.993177	\N	15	\N
591	深圳职业技术学院深汕校区项目	2025-05-20	sales_focus	sales	unqualified		华阳国际设计集团	上海瀚网智能科技有限公司			discover		\N	\N	0	\N	\N	2025-05-20 06:45:29.8322	2025-06-02 23:35:20.120829	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
40	新世代产业园	2025-04-21	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海东大金智信息系统有限公司	tendering	2025/4/21 11:51:47 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202504-026\r\n\r\r\n\r2025/4/18 17:11:05 杨俊杰\r\n\r提交报备\r\n\r	CPJ202504-026	2025-04-21	0	\N	\N	2025-04-21 00:00:00	2025-04-21 11:51:00	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
45	松江区俊普智造中心改造	2025-04-18	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海跃燕弱电工程有限公司	tendering	2025/4/18 17:03:28 杨俊杰\r\n\r【分销商】：添加   上海瑞康\r\n\r【授权编号】：添加   HY-CPJ202504-014\r\n\r\r\n\r2025/4/13 16:05:39 杨俊杰\r\n\r提交报备\r\n\r2025/4/13 16:03:21 杨俊杰\r\n\r【完善价格】 80097\r\n\r	CPJ202504-014	2025-04-18	80097	\N	\N	2025-04-18 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
76	市政九珑汇	2025-03-29	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	江西盈石信息工程有限公司	tendering	2025/4/13 15:46:15 杨俊杰\r\n\r【完善价格】 145766\r\n\r2025/4/10 10:52:12 李冬\r\n\r【完善价格】 95077\r\n\r2025/3/29 12:51:11 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202503-011\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r2025/3/17 17:31:53 李冬\r\n\r【授权编号】：添加   HY-CPJ202503-011\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202503-011	2025-04-13	92446	\N	\N	2025-03-29 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
72	粤芯半导体集成电路厂改造	2025-04-14	channel_follow	channel	qualified	\N	\N	广州宇洪科技股份有限公司	\N	\N	awarded	2025/4/14 09:50:06 周裔锦\r\n\r\n【授权编号】：添加   HY-CPJ202412-017\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n2025/4/14 09:49:16 周裔锦\r\n\r\n【当前阶段】：添加   中标\r\n\r\n【当前阶段情况说明】：添加   业主已经确定集成商。\r\n\r\n\r\n\r\n2025/3/25 21:49:19 周裔锦\r\n\r\n【当前阶段】：添加   发现\r\n\r\n【授权编号】：添加   HY-CPJ202412-017\r\n\r\n【当前阶段情况说明】：添加   设计院介绍项目尚未进入施工图设计。\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n2025/3/25 13:42:01 周裔锦\r\n\r\n【完善价格】 37878\r\n\r\n	CPJ202412-017	2025-06-01	0	\N	\N	2025-04-14 00:00:00	2025-04-14 09:50:00	17	f	\N	\N	\N	f	2025-05-24 05:20:56.993177	\N	17	1
156	马来西亚万国数据中心	2025-03-05	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	\N	signed	2025/3/14 14:03:15 杨俊杰\r\n\r[阶段变更] ->签约\r\n\r2025/3/5 15:01:59 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202503-001\r\n\r\r\n\r	CPJ202503-001	2025-03-14	42860.25	\N	\N	2025-03-05 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
423	张江78地块	2025-02-25	channel_follow	channel	qualified	\N	\N	\N	\N	同方股份有限公司-上海光大会展分公司	signed	2025/4/7 17:30:22 李冬\r\n\r【当前阶段】：改变成   签约\r\r\n\r\n\r2025/2/25 15:02:38 李冬\r\n\r【授权编号】：添加   HY-CPJ202406-008\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/8/23 18:26:23 李华伟\r\n\r【阶段变更】中标->签约\r\r\n\r\n\r2024/6/17 李华伟\r\n\r【拜访】:  目前瀚网配合投标的同方中标，已经在配合深化，预计8月份左右进场。\r\n\r	CPJ202406-008	2025-04-07	0	\N	\N	2025-02-25 00:00:00	2025-04-07 17:30:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	2
590	浦东机场四期配套信息中心（ITC)	2025-06-11	sales_focus	sales	not_required		华东建筑设计研究院有限公司				embed	配合华东院徐工做前期规划	SPJ202506-006	\N	437667	\N	\N	2025-05-20 06:30:41.045536	2025-06-11 06:49:01.317173	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
100	康桥二期集成电路生产线厂房及配套设施建设项目	2024-01-31	sales_focus	sales	qualified	华虹半导体（上海）有限公司	信息产业电子第十一设计院科技工程股份有限公司	上海福玛通信信息科技有限公司	\N	北京中加集成智能系统工程有限公司	quoted	2025/4/10 16:58:52 郭小会\r\n\r\n【完善价格】 2141633\r\n\r\n2025/4/9 12:01:32 郭小会\r\n\r\n【完善价格】 2199233\r\n\r\n2025/4/9 郭小会\r\n\r\n「孟凡丽」 北京中加集成智能系统工程有限公司  和孟总他们沟通深化方案的问题，有几栋楼本次建设是毛坯，和业主沟通协商后，从本次清单中去掉，采用简单的临时系统，核对好深化的清单给集成商进行确认\r\n\r\n2025/3/8 10:05:05 郭小会\r\n\r\n【出货时间预测】：添加   2025年二季度\r\n\r\n\r\n\r\n2025/2/24 17:08:40 郭小会\r\n\r\n【完善价格】 2539508\r\n\r\n2025/2/21 17:28:19 杨俊杰\r\n\r\n【当前阶段】：改变成   转移\r\n\r\n【当前阶段情况说明】：添加   该项目由郭总负责\r\n\r\n\r\n\r\n2025/2/21 16:33:27 杨俊杰\r\n\r\n【完善价格】 2019670\r\n\r\n2025/2/7 09:10:58 郭小会\r\n\r\n【直接用户】：添加   华虹半导体（上海）有限公司\r\n\r\n\r\n\r\n2024/12/27 郭小会\r\n\r\n【阶段变更】招标中->中标\r\n\r\n\r\n\r\n2024/11/1 杨俊杰\r\n\r\n【阶段变更】招标中->中标\r\n\r\n\r\n\r\n2024/9/20 17:11:28 杨俊杰\r\n\r\n【完善价格】 2019731\r\n\r\n2024/9/14 郭小会\r\n\r\n【阶段变更】品牌植入->招标中\r\n\r\n\r\n\r\n2024/7/17 15:23:47 郭小会\r\n\r\n【消息】「」通过博望程总介绍，和二期业主冯总对接，沟通需求，帮助业主出预算、推荐品牌\r\n\r\n2024/6/15 09:06:43 郭小会\r\n\r\n【消息】「」带刘威去一期现场勘查，和一期业主交流沟通现在存在的问题 以及二期的需求\r\n\r\n2024/3/17 14:26:47 郭小会\r\n\r\n博望电子在帮业主进行初设计，博望已发我们品算牌提给业主\r\n\r\n2024/2/20 15:06:27 郭小会\r\n\r\n设计方改变为  信息产业电子第十一设计院科技工程股份有限公司 类型改变为  销售重点 集成商改变为  上海博望电子科技有限公司    \r\n\r\n2023/11/1 郭小会\r\n\r\n1、配合陈总提供品牌资料，做品牌入围\r\n\r\n	SPJ202401-003	2025-06-05	2141633	\N	\N	2024-01-31 00:00:00	2025-06-11 16:02:52.064243	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	3
592	嘉兴湖畔酒店	2025-05-20	channel_follow	sales	not_required			浙江航博智能工程有限公司		嘉兴贝斯特电子技术有限公司	discover	目前客户已经中标，预计8月份左右进场，配合商务环节。	SPJ202411-004	\N	0	yes	\N	2025-05-20 06:55:41.33944	2025-05-20 06:55:41.33944	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
117	科思创对讲机维修	2025-04-02	business_opportunity	\N	\N	科思创聚合物(中国)有限公司	\N	\N	\N	\N	signed	2025/4/2 10:13:02 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-006\r\r\n\r\n\r2025/3/11 13:34:11 方玲\r\n\r【完善价格】 660\r\n\r	APJ202503-006	2025-04-02	660	\N	\N	2025-04-02 00:00:00	2025-05-15 06:43:30.080639	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
116	科思创采购20套P8668i	2025-04-02	business_opportunity	\N	\N	科思创聚合物(中国)有限公司	\N	\N	\N	\N	signed	2025/4/2 10:14:31 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-008\r\r\n\r\n\r2025/3/17 09:45:40 方玲\r\n\r【完善价格】 95000\r\n\r	APJ202503-008	2025-04-02	95000	\N	\N	2025-04-02 00:00:00	2025-05-15 06:42:39.278541	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
46	上海金山枫泾臻品之选酒店	2025-04-18	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海电信科技发展有限公司	tendering	2025/4/18 17:03:01 杨俊杰\r\n\r【分销商】：添加   上海瑞康\r\n\r\r\n\r2025/4/18 17:02:51 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202504-013\r\n\r\r\n\r2025/4/13 16:06:01 杨俊杰\r\n\r提交报备\r\n\r2025/4/13 15:58:09 杨俊杰\r\n\r【完善价格】 18904\r\n\r	CPJ202504-013	2025-04-18	18904	\N	\N	2025-04-18 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
210	南大104-02、105-01、02、106-01	2025-01-06	sales_focus	sales	qualified	上海临港经济发展（集团）有限公司	华东建筑设计研究院有限公司	\N	\N	\N	embed	2025/2/6 12:08:41 杨俊杰\r\n\r【设计院及顾问】：改变成   周天文「华东建筑设计研究院有限公司」\r\n\r【直接用户】：改变成   张小宁「上海临港经济发展（集团）有限公司」\r\n\r\r\n\r2025/1/6 16:08:38 杨俊杰\r\n\r【授权编号】：添加   HY-SPJ202411-015\r\n\r【类型】：添加   销售重点\r\n\r\r\n\r	SPJ202411-015	2025-02-06	922634	\N	\N	2025-01-06 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
429	无锡经开区万象城西侧地块项目	2024-07-04	channel_follow	channel	qualified	\N	\N	上海淳泊信息科技有限公司	\N	上海久纽智能科技有限公司	tendering	2025/4/3 23:28:11 邹飞\r\n\r【分销商】：添加   上海淳泊\r\r\n\r\n\r2025/2/21 17:06:05 杨俊杰\r\n\r【完善价格】 254627\r\n\r2024/7/4 杨俊杰\r\n\r渠道反馈项目为EPC，大总包找到上海久纽复核弱电价格，配合久钮提供系统报价\r\n\r45477 邹飞\r\n\r渠道反馈项目为EPC，大总包找到上海久纽复核弱电价格，配合久钮提供系统报价\r\n\r	CPJ202407-002	2025-04-03	0	\N	\N	2024-07-04 00:00:00	2025-04-03 23:28:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
77	临港新片区数字文化装备产业总部基地	2025-03-29	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海东大金智信息系统有限公司	pre_tender	2025/4/13 15:42:37 杨俊杰\r\n\r【完善价格】 293347\r\n\r2025/4/10 10:43:20 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：改变成   渠道报备，沟通梳理了解配合东大报价，用于项目招标前概算统计\r\n客户反馈没有中标，具体中标单位未知\r\r\n\r\n\r2025/4/10 李冬\r\n\r「李兵」 上海东大金智信息系统有限公司  客户反馈没有中标，具体中标单位未知\r\n\r2025/3/29 12:51:55 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202503-016\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r2025/3/21 11:52:17 李冬\r\n\r【授权编号】：添加   HY-CPJ202503-016\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/3/21 11:25:01 李冬\r\n\r【完善价格】 184764\r\n\r2025/3/21 11:14:36 李冬\r\n\r【分销商】：添加   上海瑞康\r\r\n\r\n\r2025/3/21 11:10:11 李冬\r\n\r【完善价格】 192254\r\n\r	CPJ202503-016	2025-04-13	293347	\N	\N	2025-03-29 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
594	前海深港青年梦工场南区智能化工程	2025-05-22	channel_follow	channel	unqualified			上海瀚网智能科技有限公司		深圳达实智能股份有限公司	pre_tender	配合集成商投标，最快本月出结果。	\N	\N	0	\N	\N	2025-05-22 07:06:59.792513	2025-05-22 07:15:11.475302	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
462	成都天府新区医院	2024-11-30	channel_follow	channel	unqualified	\N	\N	福淳智能科技(四川)有限公司	\N	四川锦辰瑞建设工程有限公司	embed	2025/3/1 13:51:44 邹娟\r\n\r【系统集成商】：添加   四川锦辰瑞建设工程有限公司\r\r\n\r\n\r2025/3/1 13:44:56 邹娟\r\n\r【当前阶段情况说明】：添加   品牌库里没有我们品牌，需要做品牌植入，已跟进总包、分包，项目经理把我们方案已提\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r2024/11/30 21:11:16 郭小会\r\n\r【完善价格】 504544\r\n\r45626.8828240741 邹娟\r\n\r【完善价格】 504544\r\n\r	CPJ202411-016	2025-03-01	0	yes	\N	2024-11-30 00:00:00	2025-03-01 13:51:00	25	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	\N
463	宜宾中心	2025-02-28	channel_follow	channel	\N	\N	\N	上海福玛通信信息科技有限公司	\N	\N	embed	2025/2/28 13:45:14 邹飞\r\n\r【授权编号】：添加   HY-CPJ202502-002\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/8 10:46:18 杨俊杰\r\n\r【完善价格】 279444\r\n\r2025/2/7 12:03:54 杨俊杰\r\n\r【完善价格】 237411\r\n\r2025/2/6 13:46:16 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202502-002\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r	CPJ202502-002	2025-02-28	0	\N	\N	2025-02-28 00:00:00	2025-02-28 13:45:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
587	老凤祥新楼	2025-05-19	business_opportunity	sales	qualified		华东建筑设计研究院有限公司				embed	该项目华东院叶海茂负责智能化设计，配合相关设计方案，经了解现阶段这版方案主要是对系统要求及概算进行确认	\N	2025-05-19	0	pending	申请备注: 新增业务，申请授权编号。项目类型选择错误，需改为渠道跟进	2025-05-19 01:55:53.978974	2025-05-30 14:25:58.429075	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
520	静安希尔顿酒店	2025-05-16	channel_follow	channel	qualified					都市创想（上海）城市更新建设有限公司   高道喜	tendering	渠道报备，配合都市创想参与项目投标报价，项目预计本月底投标	\N	2026-06-30	38350	\N	\N	2025-05-16 03:33:43.927182	2025-05-16 03:43:34.269322	14	t	授权编号审批锁定: 渠道项目报备流程	14	2025-05-30 07:12:09.264451	t	2025-05-24 05:20:56.993177	\N	14	1
54	科思创E188区域材料增补	2025-04-18	business_opportunity	sales	qualified	科思创聚合物(中国)有限公司	\N	\N	\N	\N	awarded	2025/4/18 10:26:11 徐昊\r\n\r【授权编号】：添加   HY-APJ-202503-007\r\r\n\r\n\r2025/4/2 10:13:50 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-007\r\r\n\r\n\r2025/3/28 11:20:16 徐昊\r\n\r【面价金额】：添加   2705.22\r\r\n\r\n\r2025/3/28 11:19:27 徐昊\r\n\r【当前阶段情况说明】：改变成   已完成合约签订并且供货\r\r\n\r\n\r2025/3/17 09:44:25 方玲\r\n\r【完善价格】 2706\r\n\r	APJ202503-007	2025-04-18	0	\N	\N	2025-04-18 00:00:00	2025-04-18 10:26:00	7	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	7	1
167	国际体操馆	2023-10-30	channel_follow	channel	qualified	\N	上海维瓴智能科技有限公司	上海瀚网智能科技有限公司	\N	上海仪电鑫森科技发展有限公司	awarded	2025/2/28 14:41:16 杨俊杰\r\n\r【出货时间预测】：添加   2025年四季度\r\n\r\r\n\r45534.5436574074 李冬\r\n\r【消息】「」该项目渠道反馈仪电鑫森中标，但项目进度比较慢，建筑还未完成，项目实际启动预计需要到明年\r\n\r2024/8/30 13:02:52 杨俊杰\r\n\r【消息】「」该项目渠道反馈仪电鑫森中标，但项目进度比较慢，建筑还未完成，项目实际启动预计需要到明年\r\n\r45450.5319791667 李冬\r\n\r【消息】「」该项目仪电鑫森中标，但经了解项目建筑还在实施过程，明确弱电智能化要明年才会启动\r\n\r2024/6/7 12:46:03 杨俊杰\r\n\r【消息】「」该项目仪电鑫森中标，但经了解项目建筑还在实施过程，明确弱电智能化要明年才会启动\r\n\r45419.5486458333 李冬\r\n\r【消息】「」渠道反馈仪电鑫森宋振兴告知目前合同还在双签过程，具体时间还无法确定，主要因为总包管理费收取标准太高，还在洽谈过程中\r\n\r2024/5/7 13:10:03 杨俊杰\r\n\r【消息】「」渠道反馈仪电鑫森宋振兴告知目前合同还在双签过程，具体时间还无法确定，主要因为总包管理费收取标准太高，还在洽谈过程中\r\n\r45416.5466782407 李冬\r\n\r【阶段变更】品牌植入->中标\r\n\r2024/5/4 13:07:13 杨俊杰\r\n\r【阶段变更】品牌植入->中标\r\n\r45231 李冬\r\n\r该项目维瓴通过业主提前拿到设计资料，提前安排渠道技术配套，复核设计资料，并给予招标清单及报价概算。通过维瓴了解品牌负责情况，推动植入和源全系列产品。\r\n\r2023/11/1 杨俊杰\r\n\r该项目维瓴通过业主提前拿到设计资料，提前安排渠道技术配套，复核设计资料，并给予招标清单及报价概算。通过维瓴了解品牌负责情况，推动植入和源全系列产品。\r\n\r	CPJ202310-004	2025-02-28	147944	\N	\N	2023-10-30 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
618	成都部队66007项目	2025-06-12	channel_follow	channel	qualified			福淳智能科技(四川)有限公司			awarded	集成商中标，之前是其他家的产品，现在福淳在和客户沟通，推动换成我们的产品	CPJ202506-015	\N	26920	\N	\N	2025-06-12 02:31:04.185748	2025-06-12 03:55:16.774225	13	f	\N	\N	\N	t	2025-06-12 02:31:04.185748	\N	13	1
74	中芯南方高精度智能人员定位需求	2025-04-02	business_opportunity	sales	unqualified	中芯南方集成电路制造有限公司	\N	\N	\N	\N	discover	2025/4/14 徐昊\r\n\r「马振邦」 中芯南方集成电路制造有限公司  和供应商根据上海厂和南方厂FAB区域的平面图后，向业主提出了方案和方案相关的终端形式，与业主分析了目前方案和终端的利弊，业主已接收提出的方案和终端的形式，业主方表示将在中芯南方内部进行方案讨论，后续继续跟踪；\r\n\r2025/4/11 徐昊\r\n\r「马振邦」 中芯南方集成电路制造有限公司  与供应商根据与业主确认的中芯南方/中芯上海厂的FAB三个区域的平面图，提出可行的硬件方案，选择高精度UWB及有源定位终端的方案，确定可提供的两种终端维护模式与业主下周进一步沟通；\r\n\r2025/4/10 徐昊\r\n\r「马振邦」 中芯南方集成电路制造有限公司  在中芯南方现场召开会议，与业主沟通高精度智能人员定位方案，本次沟通完全针对中芯南方与上海厂三个互通的fab区域的建筑结构，连廊通道互相关系等等，根据区域的入口/人员值守工况等等一一讨论定位的需求和终端的形式并且明确了软件功能的要求，会后会再和供应商沟通提出的有源终端的工作形式和呈现形式，然后再与业主沟通；\r\n\r2025/4/7 徐昊\r\n\r「马振邦」 中芯南方集成电路制造有限公司  与供应商沟通定位需求芯片厂的实际场景，根据芯片厂FAB区域的特殊流程，防护服防护装备消杀通道等等，筛选可行性，与业主方进一步商讨；\r\n\r2025/4/2 13:22:31 徐昊\r\n\r【授权编号】：添加   HY-APJ-202502-006\r\r\n\r\n\r2025/4/1 徐昊\r\n\r「马振邦」 中芯南方集成电路制造有限公司  与业主进一步确定以FAB区域为定位人员统计项目目标区域，结合进入FAB的人员工作流程（进入区域闸机/穿特定的防护服/通过特定消毒区域/指定离开通道）等特定场景特定流程特定区域来商榷定位基站和终端的形式；根据与业主沟通的信息与供应商联系，约定下周一供应商至公司沟通；\r\n\r2025/3/28 11:17:36 徐昊\r\n\r【面价金额】：添加   500000\r\r\n\r\n\r2025/2/28 10:48:42 徐昊\r\n\r【品牌情况】：添加   不确定\r\r\n【当前阶段】：添加   发现\r\r\n\r\n\r	APJ202502-006	2025-04-14	0	\N	\N	2025-04-02 00:00:00	2025-04-14 00:00:00	7	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	7	\N
94	深圳中芯国际无线对讲系统2025年系统维护检测	2025-04-02	business_opportunity	\N	qualified	中芯国际集成电路制造(深圳)有限公司	\N	\N	\N	\N	discover	2025/4/11 10:46:10 徐昊\r\n\r【完善价格】 0\r\n\r2025/4/2 13:42:17 徐昊\r\n\r【当前阶段】：添加   发现\r\r\n【授权编号】：添加   HY-APJ-202503-015\r\r\n\r\n\r2025/3/28 11:21:57 徐昊\r\n\r【面价金额】：添加   13000\r\r\n\r\n\r	APJ202503-015	2025-04-11	0	\N	\N	2025-04-02 00:00:00	2025-04-11 10:46:00	7	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	7	\N
482	浦东机场南进路北端改造工程隧道	2025-02-25	channel_follow	channel	\N	\N	\N	\N	\N	上海信业智能科技股份有限公司	embed	2025/2/25 16:17:48 李冬\r\n\r【授权编号】：添加   HY-CPJ202412-018\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202412-018	2025-02-25	0	\N	\N	2025-02-25 00:00:00	2025-02-25 16:17:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
186	北京西路1399号信达大厦	2024-11-26	sales_focus	sales	qualified	\N	上海现代建筑设计研究院有限公司	\N	\N	\N	embed	2025/2/21 16:23:56 杨俊杰\r\n\r【完善价格】 285403\r\n\r2024/12/27 14:18:21 杨俊杰\r\n\r【完善价格】 285405\r\n\r2024/12/27 杨俊杰\r\n\r类型改变为销售重点 \r\n\r	SPJ202411-013	2025-02-21	285403	\N	\N	2024-11-26 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
291	舟山东港养生馆	2024-06-07	channel_follow	channel	qualified	\N	\N	浙江航博智能工程有限公司	\N	浙江建工设备安装有限公司	signed	2024/7/15 14:15:30 李华伟\r\n\r【阶段变更】中标->签约\r\n\r2024/6/7 李华伟\r\n\r【提案采纳】:  品牌入围，目前航博配合分包在深化，预计下个月进场。\r\n\r	CPJ202406-001	2024-07-15	36132.3	\N	\N	2024-06-07 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
477	川沙C06-03地块	2025-02-27	channel_follow	sales	qualified	\N	\N	\N	\N	上海凯通实业有限公司	awarded	2025/2/27 10:22:53 邹飞\r\n\r【授权编号】：添加   HY-CPJ202401-002\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/6/14 16:16:49 李华伟\r\n\r【阶段变更】中标->签约\r\n\r2024/5/24 14:03:58 李华伟\r\n\r【阶段变更】招投标->中标\r\n\r2024/2/21 12:37:35 李华伟\r\n\r类型改变为  渠道管理    \r\n\r2023/11/1 李华伟\r\n\r品牌入围，目前代理商淳泊配合行余鑫桉配合擎天投标，后续跟进投标结果。\r\n\r	CPJ202401-002	2025-02-27	0	\N	\N	2025-02-27 00:00:00	2025-02-27 10:22:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
476	北京创业中心大厦(C座)改造项目	2025-02-27	channel_follow	channel	qualified	\N	\N	北京联航迅达通信技术有限公司	\N	\N	awarded	2025/2/27 10:26:32 邹飞\r\n\r【授权编号】：添加   HY-CPJ202403-001\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/4/2 19:59:11 范敬\r\n\r[阶段变更] ->签约\r\n\r2024/3/29 14:31:24 范敬\r\n\r「阶段变更」\r\n\r2024/3/15 15:13:01 范敬\r\n\r「提案采纳」  :  完成项目批价手续\r\n\r2024/3/1 12:13:45 范敬\r\n\r「提案」  :  系统改造，通过与业主沟通，将原摩托主设备及对讲机更换为和源品牌\r\n\r	CPJ202403-001	2025-02-27	0	\N	\N	2025-02-27 00:00:00	2025-02-27 10:26:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
299	张江56-01希尔顿酒店	2023-03-27	channel_follow	sales	qualified	\N	\N	上海淳泊信息科技有限公司	\N	上海凯通实业有限公司	signed	2024/5/17 13:04:52 李华伟\r\n\r【阶段变更】中标->签约\r\n\r2024/2/21 12:55:19 李华伟\r\n\r分销商改编为   上海淳泊  类型改变为  渠道跟进     \r\n\r2023/11/1 李华伟\r\n\r品牌入围和源亦朗欣民，淳泊配合投标。\r\n\r	CPJ202303-005	2024-05-17	22569.3	\N	\N	2023-03-27 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
518	美团科技中心	2025-05-16	channel_follow	sales	qualified			上海福玛通信信息科技有限公司		上海蓝极星智能科技有限公司	signed	该项目AECOM作为机电顾问，品牌入围，主要竞争：烈龙及正禄。蓝极星中标，代理商福玛在配套项目现场，目前深化方案基本确认，与代理商负责人付言新沟通，价格参考九星城项目，给与集成商价格承诺一致，推动代理商与蓝极星把品牌先锁定。项目现场预计要6-8月份之间才会启动穿线工作	\N	2025-07-31	170570.37	pending	申请备注: 项目之前有过报备，系统更换后没有导入	2025-05-16 03:14:20.97411	2025-06-03 02:12:13.297822	14	t	授权编号审批锁定: 渠道项目报备流程	14	2025-06-09 02:55:50.831996	t	2025-05-24 05:20:56.993177	\N	14	2
179	无锡锡山映月湖生态数字文体产业中心	2025-02-24	sales_focus	channel	qualified	\N	悉地国际设计顾问(深圳)有限公司上海分公司	上海瀚网智能科技有限公司	\N	\N	embed	2025/2/24 13:28:51 李华伟\r\n\r【授权编号】：改变成   HY-SPJ202405-002\r\r\n【类型】：改变成   销售重点\r\r\n\r\n\r2025/2/17 22:08:37 周裔锦\r\n\r【完善价格】 527349\r\n\r2025/2/13 10:20:22 周裔锦\r\n\r【授权编号】：添加   HY-SPJ202405-002\r\r\n【类型】：添加   销售重点\r\r\n\r\n\r2025/1/11 15:55:33 杨俊杰\r\n\r【授权编号】：添加   HY-SPJ202405-002\r\n\r\r\n\r	SPJ202405-002	2025-02-25	816922	\N	\N	2025-02-24 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
248	上海前海人寿金融中心	2024-11-04	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海书柏智能科技有限公司	signed	2024/11/14 李华伟\r\n\r【阶段变更】中标->签约\r\r\n\r\n\r2024/11/14 11:42:43 李华伟\r\n\r【完善价格】 49409\r\n\r2024/11/4 15:08:19 李华伟\r\n\r【完善价格】 108664\r\n\r	CPJ202411-002	2024-11-14	22233.6	\N	\N	2024-11-04 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
545	上海福瑞科技二期厂房	2025-01-11	channel_follow	channel	qualified			上海瑞康通信科技有限公司		上海存在自动化控制设备有限公司	awarded	客户中标配合深化，目前项目由于甲方资金问题，分包已经停工。原计划7月份要确认采购品牌。	CPJ202501-004	2025-08-16	129924	yes	\N	2025-05-16 06:21:44.030176	2025-05-16 09:19:39.89358	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
70	厦门士兰微8英寸SiC功率器件芯片制造生产线	2025-03-10	sales_focus	channel	unqualified	厦门士兰集科微电子有限公司	\N	上海瀚网智能科技有限公司	\N	\N	discover	2025/4/14 14:20:02 李华伟\r\n\r【授权编号】：改变成   HY-SPJ202503-005\r\r\n【类型】：改变成   销售重点\r\r\n\r\n\r2025/3/10 09:51:17 李华伟\r\n\r【授权编号】：添加   HY-CPJ202503-005\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/3/3 10:54:02 李华伟\r\n\r【当前阶段】：添加   发现\r\r\n\r\n\r	SPJ202503-005	2025-04-14	265434	\N	\N	2025-03-10 00:00:00	2025-05-16 07:37:33.112734	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
132	招商银行深圳总部大厦	2025-03-07	channel_follow	sales	qualified	\N	\N	广州宇洪智能技术有限公司	\N	深圳达实智能股份有限公司	signed	2025/3/29 13:36:12 周裔锦\r\n\r[阶段变更] ->签约\r\n\r2025/3/20 21:31:52 周裔锦\r\n\r【完善价格】 420877\r\n\r2025/3/20 13:18:14 周裔锦\r\n\r【完善价格】 539389\r\n\r2025/3/20 12:34:24 周裔锦\r\n\r【完善价格】 539390\r\n\r2025/3/14 16:28:05 周裔锦\r\n\r【完善价格】 573345\r\n\r2025/3/7 01:15:34 周裔锦\r\n\r【授权编号】：改变成   HY-CPJ202409-022\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r	CPJ202409-022	2025-03-29	19816.649999999998	\N	\N	2025-03-07 00:00:00	2025-05-25 15:40:27.507331	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
198	前滩210203地块（商业）	2022-11-25	channel_follow	sales	qualified	\N	上海凯通实业有限公司	上海淳泊信息科技有限公司	\N	上海凯通实业有限公司	lost	2025/2/17 16:04:59 李华伟\r\n\r【完善价格】 225000\r\n\r2024/2/21 13:06:34 李华伟\r\n\r分销商改编为   上海淳泊  类型改变为  渠道跟进     \r\n\r45343.5462268519 邹飞\r\n\r分销商改编为   上海淳泊  类型改变为  渠道跟进     \r\n\r2023/11/1 李华伟\r\n\r1、品牌入围，配合凯通电信行余投标。\r\n2、目前凯通老板徐总反馈系统业主指定了原来的地块品牌亦朗。淳泊还在沟通看是否有机会。\r\n\r45231 邹飞\r\n\r1、品牌入围，配合凯通电信行余投标。\r\n2、目前凯通老板徐总反馈系统业主指定了原来的地块品牌亦朗。淳泊还在沟通看是否有机会。\r\n\r	CPJ202211-015	2025-02-17	225000	\N	\N	2022-11-25 00:00:00	2025-05-30 14:12:53.705797	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
296	前滩E08-E10-E12	2023-01-03	channel_follow	sales	qualified	\N	上海凯通实业有限公司	上海福玛通信信息科技有限公司	\N	上海凯通实业有限公司	tendering	2024/3/15 14:25:16 李华伟\r\n\r「阶段变更」\r\n\r45366.6008796296 邹飞\r\n\r「阶段变更」\r\n\r2024/2/21 13:05:25 李华伟\r\n\r经销商改变为   上海福玛通信信息科技有限公司 类型改变为  渠道管理    \r\n\r45343.5454282407 邹飞\r\n\r经销商改变为   上海福玛通信信息科技有限公司 类型改变为  渠道管理    \r\n\r2023/11/1 李华伟\r\n\r配合集成商设计，预计年后招标。\r\n\r45231 邹飞\r\n\r配合集成商设计，预计年后招标。\r\n\r	CPJ202301-001	2024-06-29	605398	\N	\N	2023-01-03 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
300	前滩54号地块	2022-11-25	channel_follow	sales	qualified	\N	上海凯通实业有限公司	上海淳泊信息科技有限公司	\N	上海行余信息技术有限公司	signed	2024/5/17 13:05:07 李华伟\r\n\r【阶段变更】招投标->签约\r\n\r2024/2/21 13:05:52 李华伟\r\n\r分销商改编为   上海淳泊  类型改变为  渠道跟进     \r\n\r2023/11/1 李华伟\r\n\r品牌入围，配合凯通电信行余投标。\r\n\r	CPJ202211-013	2024-05-17	76909.95000000001	\N	\N	2022-11-25 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
294	陆家嘴昌邑路梅园社区	2024-01-10	channel_follow	sales	qualified	\N	上海德恳设计咨询顾问有限公司	上海福玛通信信息科技有限公司	\N	\N	embed	2024/3/15 14:00:58 李华伟\r\n\r「提案」  上海德恳设计咨询顾问有限公司:  目前设计方案推的全和源产品和平台，品牌已经提交上去，后续跟进确认。\r\n\r45366.5840046296 邹飞\r\n\r「提案」  上海德恳设计咨询顾问有限公司:  目前设计方案推的全和源产品和平台，品牌已经提交上去，后续跟进确认。\r\n\r2024/2/21 12:38:08 李华伟\r\n\r设计方改变为  上海德恳设计咨询顾问有限公司 类型改变为  渠道管理 集成商改变为      \r\n\r45343.5264814815 邹飞\r\n\r设计方改变为  上海德恳设计咨询顾问有限公司 类型改变为  渠道管理 集成商改变为      \r\n\r2023/11/1 李华伟\r\n\r目前配合德恳前期设计，计划植入和源对讲机品牌。\r\n\r45231 邹飞\r\n\r目前配合德恳前期设计，计划植入和源对讲机品牌。\r\n\r	CPJ202401-003	2024-07-08	877573	\N	\N	2024-01-10 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
4	江苏太仓市东亭路南延新建工程（朝阳路-桴亭路）	2025-04-21	sales_focus	sales	qualified	\N	杭州北控科技有限公司	浙江航博智能工程有限公司	\N	\N	embed	2025/4/25 18:37:37 李华伟\r\n\r【授权编号】：改变成   HY-SPJ202504-002\r\r\n【类型】：改变成   销售重点\r\r\n\r\n\r2025/4/21 14:32:59 李华伟\r\n\r【授权编号】：添加   HY-CPJ202504-023\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/14 15:49:06 李华伟\r\n\r【设计院及顾问】：添加   杭州北控科技有限公司\r\r\n\r\n\r	SPJ202504-002	2025-04-25	506728	\N	\N	2025-04-21 00:00:00	2025-05-16 08:00:12.879523	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
203	南昌昌北机场三期扩建工程	2025-02-14	sales_focus	sales	unqualified	\N	民航机场成都电子工程设计有限责任公司	\N	\N	\N	embed	2025/2/14 10:53:45 郭小会\r\n\r【设计院及顾问】：添加   民航机场成都电子工程设计有限责任公司\r\r\n【类型】：添加   销售重点\r\r\n\r\n\r2025/2/14 10:49:46 郭小会\r\n\r【授权编号】：添加   HY-SPJ202501-005\r\r\n\r\n\r	SPJ202501-005	2025-02-14	0	\N	\N	2025-02-14 00:00:00	2025-02-14 10:53:00	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	\N
181	深圳市创新金融总部基地	2025-02-23	channel_follow	sales	unqualified	\N	\N	深圳市深嘉创达科技有限公司	\N	\N	discover	2025/2/23 21:57:31 周裔锦\r\n\r【当前阶段】：改变成   发现\r\r\n【当前阶段情况说明】：添加   由于尚无清单，改为发现阶段。\r\r\n\r\n\r2025/2/23 21:56:14 周裔锦\r\n\r【授权编号】：改变成   HY-CPJ202412-021\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r	CPJ202412-021	2025-02-23	0	\N	\N	2025-02-23 00:00:00	2025-02-23 21:57:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
157	金桥地铁上盖J09-04、05、06、07地块	2025-03-13	channel_follow	sales	qualified	上海浦东建设股份有限公司	\N	\N	\N	\N	embed	2025/3/13 14:05:41 杨俊杰\r\n\r\n【授权编号】：添加   HY-CPJ202502-020\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n	CPJ202502-020	2025-03-13	0	\N	\N	2025-03-13 00:00:00	2025-05-23 04:16:44.441412	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	\N
188	香港科技大学（广州）二期	2024-10-18	sales_focus	sales	unqualified	\N	华南理工大学建筑设计研究院	上海瀚网智能科技有限公司	\N	\N	discover	2025/2/21 13:28:40 周裔锦\r\n\r【当前阶段】：改变成   发现\r\r\n【当前阶段情况说明】：添加   项目施工图尚未出来，属于发现阶段。\r\r\n\r\n\r2024/11/29 周裔锦\r\n\r【阶段变更】发现->品牌植入\r\r\n\r\n\r	SPJ202410-003	2025-02-21	0	\N	\N	2024-10-18 00:00:00	2025-02-21 13:28:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
224	嘉兴诺德智联中心	2024-06-07	channel_follow	channel	qualified	\N	浙江省建筑设计院	浙江航博智能工程有限公司	\N	浙江东冠信息技术有限公司	lost	2024/12/30 李华伟\r\n\r【阶段变更】招标前->失败\r\r\n\r\n\r	CPJ202406-002	2024-12-30	130256	\N	\N	2024-06-07 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
558	黄浦区广场社区 C010102 单元 064-01、065-01 地块（嘉里金陵）	2024-10-18	channel_follow	channel	qualified			上海瑞康通信科技有限公司		上海永天科技股份有限公司	awarded	品牌和源烈龙宣利，柏诚顾问，预计年后进场，目前代理商在配合永天商务谈判阶段。	CPJ202410-008	2026-03-14	493320	yes	\N	2025-05-16 07:15:19.35021	2025-05-16 08:35:46.960967	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
554	临港英迪格酒店	2025-05-09	channel_follow	channel	qualified			上海福玛通信信息科技有限公司			awarded	目前代理商配合深化资料报验，预计8月份进场。	\N	2025-08-23	54718	\N	\N	2025-05-16 07:02:07.8786	2025-06-03 03:50:30.292516	15	t	授权编号审批锁定: 渠道项目报备流程	15	2025-06-03 03:24:52.949762	t	2025-05-24 05:20:56.993177	\N	15	2
275	杭州西站北广场金钥匙	2024-02-21	sales_focus	sales	qualified	\N	厦门万安智能有限公司	浙江航博智能工程有限公司	\N	\N	embed	2024/5/11 21:19:51 李华伟\r\n\r【拜访】「厦门万安智能有限公司」:  目前方案配合设计院和业主已经确认下来，等待业主审核整个项目的预算情况。品牌是由设计院推荐业主进行审核，跟进业主关系，看能否进行合作。\r\n\r2024/3/15 15:04:46 李华伟\r\n\r「阶段变更」\r\n\r2024/3/15 13:21:20 李华伟\r\n\r「提案」  :  目前方案按照2套系统，品牌这块设计院目前已经确认，后续需要邀约业主进行沟通，目前业主有意向要参观上海中心项目已经在确认时间。\r\n\r2024/2/21 李华伟\r\n\r目前厦门万安负责设计方案，初步对接上设计配合，后续跟进对方方案的设计和业主信息，找到业主。\r\n\r	SPJ202402-001	2024-09-24	1513640	\N	\N	2024-02-21 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
175	青少年体育发展中心智能化工程	2024-10-23	channel_follow	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	南京东大智能化系统有限公司	embed	2025/2/25 15:18:54 范敬\r\n\r【完善价格】 169599\r\n\r2024/10/24 10:33:39 范敬\r\n\r【完善价格】 169601\r\n\r2024/10/24 10:33:39 花伟\r\n\r【完善价格】 169601\r\n\r	CPJ202410-013	2025-02-25	169599	\N	\N	2024-10-23 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
278	松江站服务中心	2024-08-20	sales_focus	sales	controlled	\N	\N	无	\N	中铁二局建设有限公司	signed	2024/9/21 15:54:18 杨俊杰\r\n\r[阶段变更] ->签约\r\n\r2024/9/5 13:50:16 杨俊杰\r\n\r【消息】「」该项目中铁二局内部告知我们中标，现场进度较急，计划今年12月份交付运营。现阶段需要通过盛建国与三吉电子对接，并与中铁二局商议商务付款\r\r\n【阶段变更】招标中->中标\r\n\r2024/8/20 12:24:54 杨俊杰\r\n\r【消息】「」该项目盛建国介绍，他利用公安和消防的关系把控整个业务。现阶段中铁二局挂网招标，一共三家参与，我们、三吉和瀚网，等待中标公布结果。与现场沟通了解已经具备实施条件，就等招标完成后商务确定就需要启动设备供货\r\n\r	SPJ202408-003	2024-09-21	1002300	\N	\N	2024-08-20 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
182	深圳机场教育基地建设项目智能化工程	2025-02-23	channel_follow	channel	unqualified	\N	\N	深圳市深嘉创达科技有限公司	\N	深圳达实智能股份有限公司	awarded	2025/2/23 21:54:49 周裔锦\r\n\r【系统集成商】：添加   深圳达实智能股份有限公司\r\r\n\r\n\r2025/2/23 21:54:13 周裔锦\r\n\r【授权编号】：改变成   HY-CPJ202409-020\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r	CPJ202409-020	2025-02-23	291804	\N	\N	2025-02-23 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
282	前滩媒体城08-01&13-01	2023-10-23	channel_follow	sales	not_required	\N	华东建筑设计研究院有限公司	上海鑫桉信息工程有限公司	\N	上海擎天电子科技有限公司	signed	2024/9/6 14:30:23 李华伟\r\n\r【阶段变更】中标->签约\r\r\n\r\n\r2024/2/21 12:51:54 李华伟\r\n\r设计方改变为  华东建筑设计研究院有限公司 分销商改编为   上海淳泊  类型改变为  渠道跟进     \r\n\r2023/11/1 李华伟\r\n\r品牌入围和源尚岛亦郎，擎天中标鑫桉在跟进。关注进度以及深化清单。\r\n\r	CPJ202310-001	2024-09-06	54470.09999999999	\N	\N	2023-10-23 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
140	润友科技（临港）总部大楼	2023-07-25	channel_follow	sales	unqualified	\N	上海延华智能科技（集团）股份有限公司	\N	\N	\N	lost	2025/3/25 15:20:51 郭小会\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   此项目资金有问题，改成毛坯交付，无线对讲系统取消\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/12/31 郭小会\r\n\r类型改变为 \r\n\r	CPJ202307-003	2025-03-25	188550	\N	\N	2023-07-25 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
189	广州大学城校区新建学生宿舍工程	2024-12-06	sales_focus	sales	unqualified	\N	华南理工大学建筑设计研究院	\N	\N	\N	discover	2025/2/21 13:27:55 周裔锦\r\n\r【当前阶段】：改变成   发现\r\r\n【当前阶段情况说明】：添加   智能化施工图尚未出来，属于发现阶段。\r\r\n\r\n\r	SPJ202412-002	2025-02-21	0	\N	\N	2024-12-06 00:00:00	2025-02-21 13:27:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
566	915项目弱电工程	2025-01-06	channel_follow	channel	qualified			上海瑞康通信科技有限公司		上海仪电鑫森科技发展有限公司	awarded	目前代理商配合深化以及资料报审，预计在9月份左右进场。	CPJ202406-004	2025-10-30	359535	yes	\N	2025-05-16 07:27:58.135412	2025-06-13 10:50:05.523835	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
307	内蒙古国际会议中心项目	2024-04-16	sales_focus	sales	\N	\N	华东建筑设计研究院有限公司	\N	\N	\N	embed	2024/4/16 郭小会\r\n\r配合华东院王总提交对讲系统规划方案，王总整合后做总体汇报\r\n\r	SPJ202404-001	2024-04-16	1999935	\N	\N	2024-04-16 00:00:00	2025-06-03 01:10:20.11635	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
259	川沙C06-04地块	2024-10-10	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海凯通实业有限公司	signed	2024/10/25 李华伟\r\n\r【阶段变更】中标->签约\r\r\n\r\n\r2024/10/21 11:06:59 李华伟\r\n\r【完善价格】 81067\r\n\r2024/10/21 李华伟\r\n\r【阶段变更】招标中->中标\r\r\n\r\n\r2024/10/18 15:34:25 李华伟\r\n\r【完善价格】 90883\r\n\r2024/10/10 14:00:35 李华伟\r\n\r【完善价格】 102119\r\n\r	CPJ202410-003	2024-10-25	36480.15	\N	\N	2024-10-10 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
68	崇明长兴38-07地块商业项目	2025-04-14	channel_follow	sales	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海双桥信息有限公司	tendering	2025/4/14 15:44:08 李华伟\r\n\r【授权编号】：添加   HY-CPJ202504-011\r\r\n\r\n\r2025/4/11 14:07:55 李华伟\r\n\r提交报备\r\n\r2025/4/11 14:07:41 李华伟\r\n\r提交报备\r\n\r2025/4/11 13:48:10 李华伟\r\n\r【完善价格】 121378\r\n\r2025/4/11 13:46:48 李华伟\r\n\r【完善价格】 687496\r\n\r2025/4/11 李华伟\r\n\r「」 上海双桥信息有限公司  配合客户设计植入和源对讲机全品牌，目前已经招标，代理商配合书柏、早田、铭洪投标。\r\n\r	CPJ202504-011	2025-04-14	121378	\N	\N	2025-04-14 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
222	市北高新技术服务业园区N070501单元21-02地块商办	2022-12-05	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	\N	lost	2024/12/30 李华伟\r\n\r【阶段变更】招标中->失败\r\r\n类型改变为渠道跟进 \r\n\r2024/5/13 10:22:42 李华伟\r\n\r【阶段变更】品牌植入->招标中\r\n\r2024/3/15 14:30:35 李华伟\r\n\r「拜访」  :\r\n\r2024/2/21 13:01:37 李华伟\r\n\r类型改变为  渠道跟进     \r\n\r2023/11/1 李华伟\r\n\r前期扩粗阶段，项目酒店办公各一套系统\r\n\r	CPJ202212-001	2024-12-30	118240	\N	\N	2022-12-05 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
221	深圳蛇口颐养康复医疗中心	2024-06-14	channel_follow	channel	qualified	\N	\N	浙江航博智能工程有限公司	\N	浙大网新系统工程有限公司	lost	2024/12/30 李华伟\r\n\r【阶段变更】招标中->失败\r\r\n\r\n\r2024/6/14 李华伟\r\n\r【提案】:  航博配合浙大网新投标，品牌入围。\r\n\r	CPJ202406-005	2024-12-30	78088	\N	\N	2024-06-14 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
223	上海市第一人民医院南部院区二期	2024-03-21	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海天跃科技股份有限公司	lost	2024/12/30 李华伟\r\n\r【阶段变更】品牌植入->失败\r\r\n类型改变为渠道跟进 \r\n\r2024/3/21 12:11:45 李华伟\r\n\r「提案」  :  瀚网配合集成商设计方案植入，目前品牌推荐过去，后续确认品牌是否敲定。\r\n\r2024/3/21 12:07:24 李华伟\r\n\r「阶段变更」\r\n\r	CPJ202403-007	2024-12-30	462240	\N	\N	2024-03-21 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
272	盐城郁金香希尔顿	2024-09-24	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海金槐智能科技有限公司	signed	2024/9/29 李华伟\r\n\r【阶段变更】中标->签约\r\r\n\r\n\r2024/9/24 李华伟\r\n\r类型改变为渠道跟进 \r\n\r2024/9/24 李华伟\r\n\r【出现困难】项目为升级质保后的改造，原系统天馈为其他品牌保留，关于对讲机和主机进行更新替换。\r\r\n\r\n\r2024/9/24 14:14:56 李华伟\r\n\r【完善价格】 67150\r\n\r	CPJ202409-008	2025-02-28	30217.5	\N	\N	2024-09-24 00:00:00	2025-06-03 02:20:59.152008	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
170	增城区牛仔服装智能制造示范基地	2024-10-18	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	广东恒信安电子有限公司	pre_tender	2025/2/26 17:49:42 周裔锦\r\n\r【完善价格】 99399\r\n\r	CPJ202410-011	2025-02-26	99399	\N	\N	2024-10-18 00:00:00	2025-05-11 00:59:24.476988	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
564	奉贤区生物科技园	2025-05-09	channel_follow	channel	qualified			上海瑞康通信科技有限公司		上海行余信息技术有限公司	awarded	目前客户中标，预计8月份进场，代理商配合深化工作。	\N	2025-09-16	152298	\N	\N	2025-05-16 07:23:16.961089	2025-05-16 08:21:52.404182	15	t	授权编号审批锁定: 渠道项目报备流程	15	2025-06-03 03:26:00.859548	t	2025-05-24 05:20:56.993177	\N	15	2
582	哈尔滨工业大学(深圳)重点实验室集群项目智能化工程	2025-05-18	channel_follow	sales	not_required			上海瀚网智能科技有限公司		中建三局智能技术有限公司深圳分公司	awarded		\N	\N	99271	\N	\N	2025-05-18 12:54:39.993297	2025-05-22 07:36:18.174463	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
283	宝华和平工业园总包项目	2024-09-06	sales_focus	sales	unqualified	\N	麦驰设计研究院	\N	\N	\N	embed	2024/9/6 14:21:43 周裔锦\r\n\r【出现困难】当前项目已经设计完成，专网没有定品牌，估计20万金额。智能化总包不一定参与。\r\r\n\r\n\r	SPJ202409-002	2025-02-25	0	\N	\N	2024-09-06 00:00:00	2025-02-25 15:55:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
487	中国五冶集团有限公司五冶集团临港总部基地项目	2025-02-25	channel_follow	channel	\N	\N	\N	\N	\N	\N	embed	2025/2/25 15:34:38 李冬\r\n\r【授权编号】：添加   HY-CPJ202408-015\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/17 16:45:14 李华伟\r\n\r【分销商】：添加   上海瑞康\r\r\n【经销商】：添加   上海瀚网智能科技有限公司\r\r\n【授权编号】：改变成   HY-CPJ202408-015\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r	CPJ202408-015	2025-02-25	0	\N	\N	2025-02-25 00:00:00	2025-02-25 15:34:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
239	连云港花果山总部研发中心	2023-07-19	channel_follow	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	朗高科技有限公司	paused	2024/12/7 范敬\r\n\r【阶段变更】招标前->招标中\r\r\n\r\n\r2024/12/7 花伟\r\n\r【阶段变更】招标前->招标中\r\r\n\r\n\r2024/7/18 07:45:49 范敬\r\n\r【消息】「」项目进入招投标准备阶段\r\n\r2024/7/18 07:45:49 花伟\r\n\r【消息】「」项目进入招投标准备阶段\r\n\r2024/7/18 07:45:29 范敬\r\n\r【阶段变更】品牌植入->招标前\r\n\r2024/7/18 07:45:29 花伟\r\n\r【阶段变更】品牌植入->招标前\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n前期规划设计标已通过，东大院中标设计。讨论后期平面图、系统图、清单、品牌等合作事宜\r\n\r2023/11/1 花伟\r\n\r「阶段变更」\r\r\n前期规划设计标已通过，东大院中标设计。讨论后期平面图、系统图、清单、品牌等合作事宜\r\n\r	CPJ202307-001	2024-12-07	383480	\N	\N	2023-07-19 00:00:00	2025-06-12 11:48:35.187149	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
454	浙商银行科研中心（西安）项目	2024-06-14	channel_follow	channel	qualified	\N	\N	上海瑞康通信科技有限公司	\N	\N	pre_tender	2025/3/19 16:36:33 李冬\r\n\r【当前阶段】：改变成   招标前\r\r\n【当前阶段情况说明】：改变成   未招标，品牌围标\r\r\n\r\n\r45592 李冬\r\n\r【出现困难】项目暂停中。\r\r\n\r\n\r2024/10/27 周裔锦\r\n\r【出现困难】项目暂停中。\r\r\n\r\n\r	CPJ202406-006	2025-03-19	0	\N	\N	2024-06-14 00:00:00	2025-03-19 16:36:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
249	中集集团前海总部	2024-11-08	sales_focus	sales	unqualified	\N	筑博设计集团股份有限公司	\N	\N	\N	discover	2024/11/8 周裔锦\r\n\r【出现困难】设计院介绍，目前项目在做土建设计，智能化部分要稍后，下回介绍智能化的同事来对接配合设计无线对讲系统。\r\r\n\r\n\r	SPJ202411-007	2024-11-08	0	\N	\N	2024-11-08 00:00:00	2024-11-08 15:46:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
252	深圳市体育中心配套酒店项目	2024-11-01	sales_focus	sales	unqualified	\N	深圳市建筑设计研究总院有限公司	\N	\N	\N	discover	\N	SPJ202411-002	2024-11-01	0	\N	\N	2024-11-01 00:00:00	2024-11-01 16:13:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
253	前海深港创新产业园	2024-11-01	sales_focus	sales	unqualified	\N	奥意建筑工程设计有限公司	\N	\N	\N	discover	\N	SPJ202411-003	2024-11-01	0	\N	\N	2024-11-01 00:00:00	2024-11-01 15:44:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
452	青春云社智能化项目	2024-06-21	channel_follow	sales	qualified	\N	\N	上海瑞康通信科技有限公司	\N	深圳三图建设集团有限公司	lost	2025/3/19 16:38:26 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   集成商未中标\r\r\n\r\n\r45464 李冬\r\n\r【提案】:  配合集成商投标\r\n\r2024/6/21 庄海鑫\r\n\r【提案】:  配合集成商投标\r\n\r	CPJ202406-014	2025-03-19	0	\N	\N	2024-06-21 00:00:00	2025-03-19 16:38:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
460	张江B306地块	2022-11-25	channel_follow	sales	controlled	\N	\N	上海瑞康通信科技有限公司	\N	上海壹杰信息技术有限公司	lost	2025/3/19 16:22:23 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   配合集成商未中标\r\r\n\r\n\r2025/2/17 16:01:20 李华伟\r\n\r【完善价格】 110288\r\n\r45343.5386342593 李冬\r\n\r分销商改编为   上海瑞康 类型改变为  渠道跟进     \r\n\r2024/2/21 12:55:38 李华伟\r\n\r分销商改编为   上海瑞康 类型改变为  渠道跟进     \r\n\r45231 李冬\r\n\r品牌围标，配合康悦、壹杰投标，后续跟进结果。\r\n\r2023/11/1 李华伟\r\n\r品牌围标，配合康悦、壹杰投标，后续跟进结果。\r\n\r	CPJ202211-012	2025-03-19	0	\N	\N	2022-11-25 00:00:00	2025-03-19 16:22:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
552	浦东浦兴社区Y000901单元02-01A地块商办-聚峰中心	2024-12-10	channel_follow	channel	qualified			上海瑞康通信科技有限公司		上海源和智能科技股份有限公司	awarded	项目品牌入围和源烈龙，存在竞争，预计在下半年10月份左右进场。代理商在跟进客户商务环节，后续拜访源和老板周志超看看能不能敲定掉最终价格。	CPJ202410-006	2025-11-28	312647	yes	\N	2025-05-16 06:45:01.308644	2025-06-03 02:09:12.447338	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
565	创新药产业园项目A04C-01地块	2024-11-25	channel_follow	channel	qualified			上海瑞康通信科技有限公司		同方股份有限公司-上海光大会展分公司	embed	目前客户询价前期预算，基本同方在操作项目，预计正式招标在26年。	CPJ202411-011	\N	139038	yes	\N	2025-05-16 07:24:57.391466	2025-06-03 02:20:26.582404	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
197	曼氏（中国）香精香料厂房	2023-02-27	channel_follow	sales	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海信业智能科技股份有限公司	lost	2025/2/17 16:06:05 李华伟\r\n\r【当前阶段】：改变成   失败\r\r\n\r\n\r2025/1/11 14:35:52 李华伟\r\n\r【当前阶段情况说明】：添加   跟进的代理商反馈客户最终没有谈拢改造项目，甲方找了其他分包单位。\r\r\n\r\n\r2024/12/30 李华伟\r\n\r【阶段变更】品牌植入->搁置\r\r\n类型改变为渠道跟进 \r\n\r2024/2/21 13:06:55 李华伟\r\n\r分销商改编为   上海瑞康 经销商改变为   上海瀚网智能科技有限公司 类型改变为  渠道管理    \r\n\r2023/11/1 李华伟\r\n\r项目改造设计，安排公司技术对接设计和代理商配合。\r\n\r	CPJ202302-003	2025-02-28	206038	\N	\N	2023-02-27 00:00:00	2025-05-11 00:59:24.476988	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
422	张江中区卓闻路一期	2025-02-25	channel_follow	sales	qualified	\N	\N	上海瑞康通信科技有限公司	\N	上海行余信息技术有限公司	signed	2025/4/7 17:30:36 李冬\r\n\r【当前阶段】：改变成   签约\r\r\n\r\n\r2025/2/25 14:52:01 李冬\r\n\r【授权编号】：改变成   HY-CPJ202304-009\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/25 14:51:15 李冬\r\n\r【授权编号】：添加   HY-202304-009\r\r\n\r\n\r2024/12/16 李华伟\r\n\r【阶段变更】中标->签约\r\r\n\r\n\r2024/12/9 16:14:52 李华伟\r\n\r【完善价格】 84992\r\n\r2024/12/9 15:49:13 李华伟\r\n\r【完善价格】 94159\r\n\r2024/12/9 15:47:39 李华伟\r\n\r【完善价格】 103326\r\n\r2024/12/9 13:47:52 李华伟\r\n\r【完善价格】 84999\r\n\r2024/11/26 19:42:09 李华伟\r\n\r【完善价格】 74335\r\n\r2024/2/21 12:54:51 李华伟\r\n\r分销商改编为   上海淳泊  类型改变为  渠道管理    \r\n\r2023/11/1 李华伟\r\n\r目前品牌无要求，瀚网和淳泊配合凯通行余投标。\r\n\r	CPJ202304-009	2025-04-07	0	\N	\N	2025-02-25 00:00:00	2025-04-07 17:30:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	2
584	东部中心广深科技创新项目	2025-05-18	channel_follow	channel	qualified			上海瀚网智能科技有限公司		汕头市晖信电器科技有限公司	pre_tender		CPJ202408-007	\N	0	yes	\N	2025-05-18 12:56:12.259205	2025-05-22 07:37:16.154722	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
456	永润丰大厦项目	2024-03-22	channel_follow	sales	qualified	\N	\N	上海瑞康通信科技有限公司	\N	深圳市华红工程有限公司	paused	2025/3/19 16:32:18 李冬\r\n\r【当前阶段】：改变成   搁置\r\r\n【当前阶段情况说明】：改变成   项目暂停\r\r\n\r\n\r45592 李冬\r\n\r【出现困难】项目暂停中。\r\r\n\r\n\r2024/10/27 周裔锦\r\n\r【出现困难】项目暂停中。\r\r\n\r\n\r45373.58125 李冬\r\n\r【阶段变更】\r\n\r集成商已经中标，配合选定品牌\r\n\r2024/3/22 13:57:00 庄海鑫\r\n\r【阶段变更】\r\n\r集成商已经中标，配合选定品牌\r\n\r	CPJ202403-009	2025-03-19	0	\N	\N	2024-03-22 00:00:00	2025-03-19 16:32:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
489	易瑞生物 宝安生物监测于诊断产业园项目	2025-02-25	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳市旗云智能科技有限公司	embed	2025/2/25 14:54:56 李冬\r\n\r【授权编号】：添加   HY-CPJ202401-001\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/3/22 14:22:15 庄海鑫\r\n\r【阶段变更】\r\n\r2023/11/1 庄海鑫\r\n\r1、项目处于招标阶段，已让代理商配合报价给到集成商。\r\n\r	CPJ202401-001	2025-02-25	0	\N	\N	2025-02-25 00:00:00	2025-02-25 14:54:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
418	武汉综合实验平台	2024-11-01	channel_follow	sales	qualified	\N	\N	上海瑞康通信科技有限公司	\N	江苏华瑞克科技有限公司	lost	2025/4/7 17:35:55 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   项目在当地采购\r\r\n\r\n\r45597.694525463 李冬\r\n\r【完善价格】 131009\r\n\r2024/11/1 16:40:07 李华伟\r\n\r【完善价格】 131009\r\n\r	CPJ202411-001	2025-04-07	0	\N	\N	2024-11-01 00:00:00	2025-04-07 17:35:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
455	无锡清名桥英迪格酒店	2024-05-17	channel_follow	channel	qualified	\N	\N	上海瑞康通信科技有限公司	\N	江苏通贝智能科技有限公司	lost	2025/3/19 16:34:22 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   配合集成商未中标\r\r\n\r\n\r2025/2/25 14:00:48 李冬\r\n\r【系统集成商】：添加   江苏通贝智能科技有限公司\r\r\n\r\n\r45429 李冬\r\n\r【提案】:  瀚网配合集成商设计方案，植入和源产品。\r\n\r2024/5/17 李华伟\r\n\r【提案】:  瀚网配合集成商设计方案，植入和源产品。\r\n\r	CPJ202405-008	2025-03-19	0	\N	\N	2024-05-17 00:00:00	2025-03-19 16:34:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
450	网易上海国际文创科技园项目（南区）	2025-02-25	channel_follow	sales	\N	\N	\N	\N	\N	上海恒能电子科技有限公司	lost	2025/3/19 16:45:23 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：改变成   集成商未中标\r\r\n\r\n\r2025/2/25 16:01:10 李冬\r\n\r【授权编号】：添加   HY-CPJ202410-010\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r45615.6548958333 李冬\r\n\r【完善价格】 225088\r\n\r2024/11/19 15:43:03 周裔锦\r\n\r【完善价格】 225088\r\n\r45592 李冬\r\n\r【出现困难】三局智能邹翔龙已把招标要求和图纸发来，让我们配合优化，参数可以根据我们的优势来修改，由于是包干项目，需要把数量帮忙核算准确。最快下个月在云筑网挂网招标。目前交由张兴还在优化中，尚无报价。\r\r\n\r\n\r2024/10/27 周裔锦\r\n\r【出现困难】三局智能邹翔龙已把招标要求和图纸发来，让我们配合优化，参数可以根据我们的优势来修改，由于是包干项目，需要把数量帮忙核算准确。最快下个月在云筑网挂网招标。目前交由张兴还在优化中，尚无报价。\r\r\n\r\n\r45592 李冬\r\n\r【出现困难】三局智能邹翔龙已把招标要求和图纸发来，让我们配合优化，参数可以根据我们的优势来修改，由于是包干项目，需要把数量帮忙核算准确。最快下个月在云筑网挂网招标。目前还在优化中，尚无报价。\r\r\n\r\n\r2024/10/27 周裔锦\r\n\r【出现困难】三局智能邹翔龙已把招标要求和图纸发来，让我们配合优化，参数可以根据我们的优势来修改，由于是包干项目，需要把数量帮忙核算准确。最快下个月在云筑网挂网招标。目前还在优化中，尚无报价。\r\r\n\r\n\r	CPJ202410-010	2025-03-19	0	\N	\N	2025-02-25 00:00:00	2025-03-19 16:45:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
457	上海周浦医院二期	2024-03-21	channel_follow	channel	qualified	\N	\N	上海瑞康通信科技有限公司	\N	江苏达海智能系统股份有限公司	lost	2025/3/19 16:31:56 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：改变成   配合集成商未中标\r\r\n\r\n\r2025/2/28 10:13:45 李冬\r\n\r【当前阶段】：改变成   招标中\r\r\n【当前阶段情况说明】：添加   项目投标结果未出，关注后续中标结果\r\r\n\r\n\r45380.5646875 李冬\r\n\r「阶段变更」\r\n\r2024/3/29 13:33:09 李华伟\r\n\r「阶段变更」\r\n\r45372.5074421296 李冬\r\n\r「提案」  :  瀚网配合集成商设计方案植入，目前品牌还没到推荐阶段，后续推动跟进品牌。\r\n\r2024/3/21 12:10:43 李华伟\r\n\r「提案」  :  瀚网配合集成商设计方案植入，目前品牌还没到推荐阶段，后续推动跟进品牌。\r\n\r45372 李冬\r\n\r「提案」  :  \r\n\r2024/3/21 李华伟\r\n\r「提案」  :  \r\n\r	CPJ202403-008	2025-03-19	0	\N	\N	2024-03-21 00:00:00	2025-03-19 16:31:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
473	上海外高桥森兰连通道	2023-10-23	channel_follow	sales	not_required	\N	\N	上海瑞康通信科技有限公司	\N	上海东元信息科技发展有限公司	paused	2025/2/28 10:07:23 李冬\r\n\r【当前阶段】：改变成   搁置\r\r\n【当前阶段情况说明】：添加   项目暂停\r\r\n\r\n\r45343.5378587963 李冬\r\n\r集成商改变为  上海东元信息科技发展有限公司    \r\n\r2024/2/21 12:54:31 李华伟\r\n\r集成商改变为  上海东元信息科技发展有限公司    \r\n\r45343.5369675926 李冬\r\n\r类型改变为  渠道跟进     \r\n\r2024/2/21 12:53:14 李华伟\r\n\r类型改变为  渠道跟进     \r\n\r45231 李冬\r\n\r目前品牌无要求，需要接入原来老的系统，品牌为摩托。瀚网配合投标。\r\n\r2023/11/1 李华伟\r\n\r目前品牌无要求，需要接入原来老的系统，品牌为摩托。瀚网配合投标。\r\n\r	CPJ202310-002	2025-02-28	0	\N	\N	2023-10-23 00:00:00	2025-02-28 10:07:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
251	深圳市龙华区博雅学校项目	2024-11-01	sales_focus	sales	unqualified	\N	深圳市建筑设计研究总院有限公司	\N	\N	\N	discover	\N	SPJ202411-001	2024-11-01	0	\N	\N	2024-11-01 00:00:00	2024-11-01 16:17:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
150	上海东站站前区A3-01地块	2025-03-13	channel_follow	sales	qualified	\N	上海现代建筑设计研究院有限公司	上海艾亿智能科技有限公司	\N	\N	embed	2025/3/21 11:01:47 杨俊杰\r\n\r【设计院及顾问】：添加   上海现代建筑设计研究院有限公司\r\n\r\r\n\r2025/3/13 14:08:03 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202502-019\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r	CPJ202502-019	2025-03-21	0	\N	\N	2025-03-13 00:00:00	2025-03-21 11:01:00	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	\N
619	双碳项目82地块D1-D1-智能化	2025-06-12	channel_follow	channel	unqualified			上海瀚网智能科技有限公司		中建三局智能技术有限公司	discover		\N	\N	326937	\N	\N	2025-06-12 15:16:16.351374	2025-06-12 15:24:30.185731	17	f	\N	\N	\N	t	2025-06-12 15:16:16.351374	\N	17	1
459	上海闵行安缦二期	2023-02-27	channel_follow	sales	qualified	\N	\N	上海瑞康通信科技有限公司	\N	\N	paused	2025/3/19 16:23:06 李冬\r\n\r【当前阶段】：改变成   搁置\r\r\n【当前阶段情况说明】：添加   项目暂停，重启时间未知\r\r\n\r\n\r45343.5435532407 李冬\r\n\r类型改变为  渠道跟进     \r\n\r2024/2/21 13:02:43 李华伟\r\n\r类型改变为  渠道跟进     \r\n\r45231 李冬\r\n\r项目设计植入和源产品，安排配合设计。\r\n\r2023/11/1 李华伟\r\n\r项目设计植入和源产品，安排配合设计。\r\n\r	CPJ202302-004	2025-03-19	0	\N	\N	2023-02-27 00:00:00	2025-03-19 16:23:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
247	万科左岸项目	2024-11-15	sales_focus	sales	unqualified	\N	深圳市麦驰物联股份有限公司上海分公司	\N	\N	\N	discover	\N	SPJ202411-011	2024-11-15	0	\N	\N	2024-11-15 00:00:00	2024-11-15 09:12:00	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	\N
230	谈家渡苏河坊	2023-02-28	sales_focus	sales	qualified	\N	华东建筑设计研究院有限公司	\N	\N	\N	discover	2024/12/27 杨俊杰\r\n\r类型改变为销售重点 \r\n\r2024/3/20 16:41:07 杨俊杰\r\n\r「阶段变更」\r\n\r2023/11/1 杨俊杰\r\n\r该项目华东院反馈上海报业退出，由兴业银行接手，现阶段重新汇报智能化方案，跟进了解项目设计进度\r\n\r	SPJ202302-002	2024-12-27	0	\N	\N	2023-02-28 00:00:00	2024-12-27 13:42:00	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	\N
414	上海市松江区洞泾镇工业区DJ-21-002号「SJS30002单元07-08」地块	2024-03-28	channel_follow	channel	qualified	\N	\N	上海瑞康通信科技有限公司	\N	上海华虹智联信息科技有限公司	awarded	2025/4/10 李冬\r\n\r「朱」 上海华虹计通智能系统股份有限公司  申购单还没有提交，目前在穿线了，桥架目前还没有全部通，预计四月中旬桥架通，申购单也是那个时间点提交\r\n\r2025/4/8 李冬\r\n\r「朱」 上海华虹计通智能系统股份有限公司  申购单还没有提交，目前在穿线了，桥架目前还没有全部通，预计四月中旬桥架通，申购单也是那个时间点提交\r\n\r2025/2/28 14:44:41 杨俊杰\r\n\r【出货时间预测】：改变成   2025年二季度\r\n\r\r\n\r2025/2/21 16:38:28 杨俊杰\r\n\r【完善价格】 152431\r\n\r45555.670775463 李冬\r\n\r【完善价格】 152861\r\n\r2024/9/20 16:05:55 杨俊杰\r\n\r【完善价格】 152861\r\n\r45534.5477083333 李冬\r\n\r【消息】「」该项目渠道反馈华虹计通中标，但因为用户资金问题，现在华虹计通在和业主确认弱电各子系统哪些保留，哪些取消，渠道在跟进给予支持，希望华虹计通能够配合说服用户保留无线对讲系统，具体商务和实施进度有待确认\r\r\n【阶段变更】招标中->中标\r\n\r2024/8/30 13:08:42 杨俊杰\r\n\r【消息】「」该项目渠道反馈华虹计通中标，但因为用户资金问题，现在华虹计通在和业主确认弱电各子系统哪些保留，哪些取消，渠道在跟进给予支持，希望华虹计通能够配合说服用户保留无线对讲系统，具体商务和实施进度有待确认\r\r\n【阶段变更】招标中->中标\r\n\r45379 李冬\r\n\r渠道反馈该项目配套华虹计通付海涛参与项目投标。目前了解到华虹计通内部系统成本测算为报价17.5万，他们会选用和源品牌参与投标，另外上海湘辉也参与其中在询价\r\n\r2024/3/28 杨俊杰\r\n\r渠道反馈该项目配套华虹计通付海涛参与项目投标。目前了解到华虹计通内部系统成本测算为报价17.5万，他们会选用和源品牌参与投标，另外上海湘辉也参与其中在询价\r\n\r	CPJ202403-011	2025-04-10	0	\N	\N	2024-03-28 00:00:00	2025-04-10 00:00:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
496	上海市嘉定区中医医院迁建	2025-01-11	channel_follow	channel	qualified	\N	\N	上海瑞康通信科技有限公司	\N	同方股份有限公司-上海光大会展分公司	tendering	45668.6014236111 李冬\r\n\r【授权编号】：改变成   HY-CPJ202409-007\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/1/11 14:26:03 李华伟\r\n\r【授权编号】：改变成   HY-CPJ202409-007\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/9/16 10:46:56 郭小会\r\n\r【完善价格】 132640\r\n\r45551.4492592593 邹娟\r\n\r【完善价格】 132640\r\n\r	CPJ202409-007	2025-01-11	0	\N	\N	2025-01-11 00:00:00	2025-01-11 14:26:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
494	星河盛境都荟大厦智能化工程	2025-02-13	channel_follow	sales	qualified	\N	\N	上海瑞康通信科技有限公司	\N	深圳市泰英通信工程有限公司	awarded	45701.4313541667 李冬\r\n\r【授权编号】：添加   HY-CPJ202502-009\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/13 10:21:09 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202502-009\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202502-009	2025-02-13	0	\N	\N	2025-02-13 00:00:00	2025-02-13 10:21:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
620	恒力三亚YGHA06-03-11、12、13、15地块（办公）智能化工程	2025-06-12	channel_follow	channel	not_required			上海瀚网智能科技有限公司		深圳市智宇实业发展有限公司	discover		\N	\N	120808	\N	\N	2025-06-12 15:31:01.999926	2025-06-12 15:36:18.666829	17	f	\N	\N	\N	t	2025-06-12 15:31:01.999926	\N	17	1
491	宁波甬江实验室研究院集居区A1A2A3地块	2023-03-07	channel_follow	sales	unqualified	\N	\N	上海瑞康通信科技有限公司	\N	\N	lost	2025/2/25 13:42:07 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   产品未能顺利植入，项目机会丢失\r\r\n\r\n\r45343.5469907407 李冬\r\n\r经销商改变为   上海瀚网智能科技有限公司    \r\n\r2024/2/21 13:07:40 李华伟\r\n\r经销商改变为   上海瀚网智能科技有限公司    \r\n\r45343.546724537 李冬\r\n\r类型改变为  渠道跟进     \r\n\r2024/2/21 13:07:17 李华伟\r\n\r类型改变为  渠道跟进     \r\n\r45231 李冬\r\n\r客户前期方案扩粗阶段，后续配合设计植入。还没有出具方案和图纸清单。\r\n\r2023/11/1 李华伟\r\n\r客户前期方案扩粗阶段，后续配合设计植入。还没有出具方案和图纸清单。\r\n\r	CPJ202303-001	2025-02-25	0	\N	\N	2023-03-07 00:00:00	2025-02-25 13:42:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
492	南京西路1038号商办用房改建	2025-02-08	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	同方股份有限公司-上海光大会展分公司	embed	2025/2/25 13:35:18 李冬\r\n\r【当前阶段】：添加   品牌植入\r\r\n【经销商】：改变成   上海瀚网智能科技有限公司\r\r\n【当前阶段情况说明】：添加   经过集成商协助推进，产品品牌已入围对讲系统品牌表\r\r\n\r\n\r2025/2/17 16:55:32 李华伟\r\n\r【当前阶段】：添加   招标中\r\r\n\r\n\r2025/2/17 16:55:22 李华伟\r\n\r【当前阶段情况说明】：添加   目前代理商配合同方投标，品牌入围。\r\r\n\r\n\r45696.4533680556 李冬\r\n\r【授权编号】：添加   HY-CPJ202501-011\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/8 10:52:51 李华伟\r\n\r【授权编号】：添加   HY-CPJ202501-011\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202501-011	2025-02-25	0	\N	\N	2025-02-08 00:00:00	2025-02-25 13:35:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
413	南京G98项目 JMS地块	2025-03-10	channel_follow	channel	qualified	\N	\N	\N	\N	上海恒能电子科技有限公司	lost	2025/4/10 09:48:53 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：改变成   客户预算有限同时对手恶意低价。差距过大\r\r\n\r\n\r2025/3/10 16:33:30 李冬\r\n\r【授权编号】：添加   HY-CPJ202503-006\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202503-006	2025-04-10	0	\N	\N	2025-03-10 00:00:00	2025-04-10 09:48:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
408	梅川社区 W060901 单元 A12a-02 地块建设项目	2025-03-07	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海索杰电子信息系统有限公司	pre_tender	2025/4/10 14:16:54 李冬\r\n\r【完善价格】 238090\r\n\r2025/4/3 23:38:59 李冬\r\n\r【经销商】：添加   上海瀚网智能科技有限公司\r\r\n\r\n\r2025/4/3 23:38:21 李冬\r\n\r【分销商】：添加   上海瑞康\r\r\n\r\n\r2025/4/3 李冬\r\n\r「李」 上海索杰电子信息系统有限公司  项目推迟到节后两天投标，还需了解有多少集成商投标\r\n\r2025/3/10 15:36:18 李冬\r\n\r【品牌情况】：添加   入围\r\r\n【面价金额】：添加   101550\r\r\n\r\n\r2025/3/7 10:36:23 李冬\r\n\r【授权编号】：添加   HY-CPJ202503-003\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202503-003	2025-04-10	0	\N	\N	2025-03-07 00:00:00	2025-04-10 14:16:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
421	临空 12 号地块国际商务花园四期	2025-02-25	channel_follow	sales	qualified	\N	\N	上海瑞康通信科技有限公司	\N	上海银欣高新技术发展股份有限公司	signed	2025/4/7 17:30:49 李冬\r\n\r【当前阶段】：改变成   签约\r\r\n\r\n\r2025/2/25 14:51:34 李冬\r\n\r【品牌情况】：添加   入围\r\r\n\r\n\r2025/2/25 14:41:02 李冬\r\n\r【授权编号】：添加   HY-CPJ202304-005\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/8/20 12:36:09 杨俊杰\r\n\r【消息】「」代理商与集成商商务合同落地，代理商与我们渠道批价也已完成\r\r\n【阶段变更】中标->签约\r\n\r2024/8/18 15:15:54 杨俊杰\r\n\r【消息】「」该项目渠道与银欣商务合同落实，与渠道确认批价订单，发起渠道批价\r\n\r2024/6/7 12:57:30 杨俊杰\r\n\r【消息】「」该项目样板层启动实施工作，代理商在配合现场推动品牌送审，商务初步启动，预计7，8月份会落地\r\n\r2024/5/7 14:05:18 杨俊杰\r\n\r【消息】「」该项目现场邹健反馈他们与甲方合同签订，无线对讲系统穿线预计5，6月份随时会启动，一旦牵涉封顶就需要提前把穿线工作完成\r\n\r2024/3/20 16:25:07 杨俊杰\r\n\r渠道反馈银欣与总包合同还在流程，目前现场在做管线预埋，提供样品用于样板层，项目要求竣工节点为10月份，预计下半年会启动商务。现阶段与技术复核确认深化方案，品牌主要与常森竞争\r\n\r2024/3/20 16:23:50 杨俊杰\r\n\r渠道反馈银欣与总包合同还在流程，目前现场在做管线预埋，提供样品用于样板层，项目要求竣工节点为10月份，预计下半年会启动商务\r\n\r2024/3/11 11:43:50 杨俊杰\r\n\r该项目品牌入围，主要与尚岛竞争，投标选用和源品牌，目前银欣中标。渠道反馈已经提供材料样品\r\n\r2024/3/11 11:41:45 杨俊杰\r\n\r「阶段变更」\r\n\r2023/11/1 杨俊杰\r\n\r该项目招标，代理商配合参与项目投标，跟踪银欣反馈投标选用和源品牌\r\n项目前期设计，无线对讲系统新增，配合提供设计方案，并给予品牌推荐\r\n\r	CPJ202304-005	2025-04-07	0	\N	\N	2025-02-25 00:00:00	2025-04-07 17:30:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	2
621	测试用项目	2025-06-13	channel_follow	channel	qualified			测试用***有限公司			quoted		CPJ202506-019	2025-06-30	426	\N	\N	2025-06-13 02:56:31.850829	2025-06-13 08:37:55.177913	18	t	批价审批流程进行中	18	2025-06-13 08:37:55.171869	t	2025-06-13 02:56:31.850829	\N	18	2
449	临港西岛金融中心商办部分	2025-02-25	channel_follow	sales	qualified	\N	\N	\N	\N	上海源和智能科技股份有限公司	lost	2025/3/19 16:49:48 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：改变成   项目重复\r\r\n\r\n\r2025/2/25 16:05:41 李冬\r\n\r【授权编号】：添加   HY-CPJ202411-009\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/12/16 周裔锦\r\n\r【阶段变更】中标->失败\r\r\n\r\n\r2024/11/19 15:51:49 周裔锦\r\n\r【完善价格】 33584\r\n\r	CPJ202411-009	2025-03-19	0	\N	\N	2025-02-25 00:00:00	2025-03-19 16:49:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
265	南方电网大湾区数字产业基地项目	2024-08-18	sales_focus	sales	unqualified	\N	广东南方电信规划咨询设计院有限公司 	\N	\N	鼎熙国讯科技有限公司	discover	2024/10/9 周裔锦\r\n\r类型改变为销售重点 \r\n\r2024/10/8 周裔锦\r\n\r【阶段变更】品牌植入->发现\r\r\n\r\n\r2024/8/23 15:43:03 周裔锦\r\n\r【出现困难】本次拜访鼎熙国讯，业主方南网大数据公司了解到，本项目会在下一阶段把无线对讲这一块定下来，品牌推荐主要由专家推荐，专家是由系统随机抽取的。个人判断需要从总包方和设计院深入做工作，总包有一定的建议权，以及设计院能配合提专业的技术要求。\r\r\n\r\n\r2024/8/18 13:30:41 周裔锦\r\n\r【阶段变更】发现->品牌植入\r\r\n\r\n\r2024/8/18 11:22:51 周裔锦\r\n\r【出现困难】本项目采用EPC模式承建，后期运营方为“中国移动”，智能化总包为“鼎熙国讯”，设计方为“广东南方电信设计院”。已拜访总包和设计院，初步沟通得知，专网无线对讲系统可能没有在前期智能化设计里，后面可能会让运营方从运营费用里面出资建设，或者要跟业主沟通本系统是否要划到本次项目内建设。\r\r\n\r\n\r	SPJ202408-002	2024-10-09	0	\N	\N	2024-08-18 00:00:00	2024-10-09 18:19:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
268	华发冰雪世界项目	2024-09-20	sales_focus	sales	unqualified	\N	珠海华发实业股份有限公司	\N	\N	\N	discover	2024/10/8 周裔锦\r\n\r【阶段变更】品牌植入->发现\r\r\n\r\n\r	SPJ202409-010	2024-10-08	0	\N	\N	2024-09-20 00:00:00	2024-10-08 14:56:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
406	联赢大厦	2025-03-21	channel_follow	sales	qualified	\N	\N	\N	\N	深圳达实智能股份有限公司	pre_tender	2025/4/10 14:43:35 李冬\r\n\r【完善价格】 287418\r\n\r2025/3/21 09:07:41 李冬\r\n\r【授权编号】：添加   HY-CPJ202501-002\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/25 16:21:14 李冬\r\n\r【授权编号】：添加   HY-CPJ202501-002\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202501-002	2025-04-10	0	\N	\N	2025-03-21 00:00:00	2025-04-10 14:43:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
411	临港新片区103顶科社区J05-01地块	2025-03-21	channel_follow	sales	qualified	\N	\N	\N	\N	上海执讯智能科技有限公司	tendering	2025/4/10 11:09:45 李冬\r\n\r【完善价格】 125271\r\n\r2025/4/10 10:56:23 李冬\r\n\r【完善价格】 101567\r\n\r2025/3/21 09:07:56 李冬\r\n\r【授权编号】：添加   HY-CPJ202502-013\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/3/7 11:34:56 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202502-013\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r	CPJ202502-013	2025-04-10	0	\N	\N	2025-03-21 00:00:00	2025-04-10 11:09:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
424	临港西岛金融中心项目	2025-02-25	channel_follow	sales	qualified	\N	\N	上海瑞康通信科技有限公司	\N	上海银欣高新技术发展股份有限公司	awarded	2025/4/7 11:01:18 李冬\r\n\r【完善价格】 564349\r\n\r2025/3/31 李冬\r\n\r「蒋佩佩」 上海银欣高新技术发展股份有限公司  目前需要把每个品牌的封样提交到业主，并通过设计院提交选型和资料，集成商和业主那边走完这些资料后才会签合同，但目前还在走流程，都系比较多，流程比较慢。目前持续了解项目状态，有问题会及时和对应销售沟通\r\n\r2025/2/25 14:13:21 李冬\r\n\r【授权编号】：添加   HY-CPJ202211-010\r\r\n【当前阶段情况说明】：改变成   项目已于去年完成批价\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/12/27 杨俊杰\r\n\r【阶段变更】中标->签约\r\n\r\r\n\r2024/11/1 杨俊杰\r\n\r类型改变为渠道跟进 \r\n\r2024/9/20 16:23:55 杨俊杰\r\n\r【完善价格】 546365\r\n\r2024/8/30 12:56:57 杨俊杰\r\n\r【消息】「」该项目渠道反馈样板层已经实施，在等确认，现场更换项目经理，主设备品牌又需要重新推进，按目前集成商现场负责人反馈只能从摩托罗拉，建伍，海能达中选择，计划推进项目经理工作，商务预计9-10月份会启动\r\n\r2024/6/17 16:11:50 杨俊杰\r\n\r【消息】「」渠道反馈该项目银欣现场反馈目前地上塔楼部分和地下室水平桥架基本完成，具备穿线条件，现阶段主要是样板层精装还未得到确认，所以现场施工才没启动，目前预测时间方面无法准确预计，商务方面现场也在和公司确认系统品牌及供应商，需等确认后才会启动材料送审。至于对讲机品牌替换，现场还不了解情况，和其沟通了海能达存在风险及采用全和源产品的优势，后续跟进对讲机品牌替换工作\r\n\r2024/5/7 14:06:49 杨俊杰\r\n\r【消息】「」该项目渠道瑞康李冬与采购蒋佩佩联系，采购单已经提交到老板，还没审批通过。现场反馈他们总包精装还未确认，预计最快也要到6，7月份才会启动\r\n\r2024/3/20 15:55:54 杨俊杰\r\n\r渠道反馈目前现场还在做管线预埋，办公区域部分楼层可以穿线，酒店区域还需要在等等，主要酒店管理公司还未确认。商务方面已经初步对接，与采购经理傅宏伟也表达私下合作，但最终需要看银欣总经理是否会介入，需要进一步跟进\r\n\r2023/11/1 杨俊杰\r\n\r该项目上海银欣中标，现场项目经理陈威负责，深化设计由奚志坚负责，据银欣反馈现场在做管线预埋，设备进场预计明年，代理商李冬在跟进\r\n\r	CPJ202211-010	2025-04-07	0	\N	\N	2025-02-25 00:00:00	2025-04-07 11:01:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
75	深圳中信金融中心	2025-03-13	channel_follow	sales	qualified	\N	华东建筑设计研究院有限公司	\N	\N	\N	embed	2025/4/13 15:49:52 杨俊杰\r\n\r【完善价格】 706126\r\n\r2025/3/13 14:07:40 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202502-017\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r	CPJ202502-017	2025-04-13	706126	\N	\N	2025-03-13 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
38	金华双龙洞凯悦酒店	2025-04-21	channel_follow	channel	qualified	\N	\N	浙江航博智能工程有限公司	\N	\N	embed	2025/4/21 14:32:29 李华伟\r\n\r【授权编号】：添加   HY-CPJ202504-022\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/18 14:07:15 李博\r\n\r【授权编号】：添加   HY-CPJ202504-022\r\r\n\r\n\r2025/4/18 13:24:25 李华伟\r\n\r【当前阶段】：添加   品牌植入\r\r\n\r\n\r2025/4/18 13:12:44 李华伟\r\n\r【完善价格】 267910\r\n\r	CPJ202504-022	2025-04-21	267910	\N	\N	2025-04-21 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
67	上海工业博览会	2025-01-11	sales_focus	sales	qualified	\N	华东建筑设计研究院有限公司	\N	\N	\N	embed	2025/4/15 杨俊杰\r\n\r「韩翌」 华东建筑设计研究院有限公司  拜访韩翌，目前他们调整到建筑一所，主要在忙着配合建筑一所参与投标，结构上调整意味着以后建筑一所业务一旦拿下，智能化业务基本都会在他和殷平手上负责，除非忙不过来后才有可能会转移到其他部门。至于工业博览会项目，因为进度原因还是比较慢，现在在等精装图出来后才会启动智能化施工图，业主方面现在还没具体负责人，侧边了解是原先国展业主负责人\r\n\r2025/1/11 15:54:50 杨俊杰\r\n\r【授权编号】：添加   HY-SPJ202408-010\r\n\r\r\n\r	SPJ202408-010	2025-04-15	815019	\N	\N	2025-01-11 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
417	京津冀近零碳生态产业园基础设施建设项目	2025-04-07	channel_follow	marketing	unqualified	\N	中国建筑上海设计研究院有限公司	上海瀚网智能科技有限公司	\N	\N	embed	2025/4/7 17:45:02 李冬\r\n\r【授权编号】：添加   HY-CPJ202504-007\r\r\n\r\n\r2025/4/7 17:19:38 李冬\r\n\r提交报备\r\n\r2025/4/7 17:16:29 李冬\r\n\r提交报备\r\n\r2025/4/7 17:16:13 李冬\r\n\r【品牌情况】：添加   不确定\r\r\n【设计院及顾问】：添加   中国建筑上海设计研究院有限公司\r\r\n【当前阶段】：添加   品牌植入\r\r\n【分销商】：添加   上海瑞康\r\r\n【经销商】：添加   上海瀚网智能科技有限公司\r\r\n【当前阶段情况说明】：添加   推品牌，目前是摩托，海能达，建伍，天馈没有。建伍让替换，然后推了品牌\r\n中继台对讲机品牌：摩托罗拉，海能达，和源\r\n天馈部分品牌：和源，瀚网，诺斯杰\r\r\n\r\n\r2025/4/7 李冬\r\n\r「尹」 中国建筑上海设计研究院有限公司  项目是上海院的，现在再推品牌，目前是摩托，海能达，建伍，天馈没有。和设计沟通，建伍让换掉，然后推了品牌\r\n中继台对讲机品牌：摩托罗拉，海能达，和源\r\n天馈部分品牌：和源，瀚网，诺斯杰\r\n\r	CPJ202504-007	2025-04-07	0	\N	\N	2025-04-07 00:00:00	2025-04-07 17:45:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
451	黄浦区南延伸段WS3单元xh130E街坊	2024-08-07	channel_follow	channel	qualified	\N	\N	\N	\N	上海恒能电子科技有限公司	paused	2025/3/19 16:40:01 李冬\r\n\r【当前阶段】：改变成   搁置\r\r\n【当前阶段情况说明】：改变成   该项目因价格原因和付款方式没有和客户达成协议，项目推迟\r\r\n\r\n\r2025/2/24 15:24:43 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n\r\n\r2025/2/24 15:24:34 李冬\r\n\r【当前阶段情况说明】：添加   该项目因价格原因和付款方式没有和客户达成协议\r\r\n\r\n\r2025/2/21 17:05:38 杨俊杰\r\n\r【完善价格】 463749\r\n\r45573 李冬\r\n\r【阶段变更】招标中->中标\r\n\r\r\n\r2024/10/8 杨俊杰\r\n\r【阶段变更】招标中->中标\r\n\r\r\n\r跟进记录 李冬\r\n\r【阶段变更】->招标中\r\n\r跟进记录 杨俊杰\r\n\r【阶段变更】->招标中\r\n\r	CPJ202408-001	2025-03-19	0	\N	\N	2024-08-07 00:00:00	2025-03-19 16:40:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
461	黄浦区半淞园社区C010501单元338-02地块	2022-11-04	channel_follow	marketing	qualified	\N	\N	上海瑞康通信科技有限公司	\N	上海梵华信息技术有限公司	pre_tender	2025/3/19 16:18:48 李冬\r\n\r【系统集成商】：添加   上海梵华信息技术有限公司\r\r\n\r\n\r2025/3/19 16:15:12 李冬\r\n\r【当前阶段】：改变成   招标前\r\r\n【当前阶段情况说明】：改变成   项目还未招标\r\r\n\r\n\r2025/2/28 09:58:32 李冬\r\n\r【当前阶段】：改变成   招标中\r\r\n【当前阶段情况说明】：添加   投标还未出结果\r\r\n\r\n\r45343.5471412037 李冬\r\n\r设计方改变为   分销商改编为   上海瑞康 经销商改变为   上海瀚网智能科技有限公司 类型改变为  渠道管理 集成商改变为  上海梵华信息技术有限公司    \r\n\r2024/2/21 13:07:53 李华伟\r\n\r设计方改变为   分销商改编为   上海瑞康 经销商改变为   上海瀚网智能科技有限公司 类型改变为  渠道管理 集成商改变为  上海梵华信息技术有限公司    \r\n\r45231 李冬\r\n\r目前配合设计植入和源设备，品牌植入和源。\r\n\r2023/11/1 李华伟\r\n\r目前配合设计植入和源设备，品牌植入和源。\r\n\r	CPJ202211-001	2025-03-19	0	\N	\N	2022-11-04 00:00:00	2025-03-19 16:18:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
480	杭政工出8号浙江东富龙生物技术有限公司生命科学产业化基地	2023-04-17	channel_follow	channel	qualified	\N	\N	上海瑞康通信科技有限公司	\N	上海华虹智联信息科技有限公司	lost	2025/2/27 09:14:45 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   联系华虹技术，项目未中标\r\r\n\r\n\r45371.6930555556 李冬\r\n\r「阶段变更」\r\n\r2024/3/20 16:38:00 杨俊杰\r\n\r「阶段变更」\r\n\r45231 李冬\r\n\r项目前期设计，配合客户提供方案，用于系统概算\r\n\r2023/11/1 杨俊杰\r\n\r项目前期设计，配合客户提供方案，用于系统概算\r\n\r	CPJ202304-003	2025-02-27	0	\N	\N	2023-04-17 00:00:00	2025-02-27 09:14:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
92	润世华大厦智能化工程	2025-04-11	channel_follow	channel	unqualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳达实智能股份有限公司	pre_tender	2025/4/11 11:12:22 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-004\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/11 09:17:46 李冬\r\n\r【授权编号】：添加   HY-CPJ202504-004\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/11 09:17:00 李冬\r\n\r【完善价格】 114655\r\n\r2025/4/8 周裔锦\r\n\r「帅进」 深圳达实智能股份有限公司  本项目招标授权资料提报。本项目的中标概率较大。\r\n\r2025/4/6 10:16:10 周裔锦\r\n\r【完善价格】 108606\r\n\r2025/4/1 周裔锦\r\n\r「帅进」 深圳达实智能股份有限公司  帅总介绍本项目下周投标，需要下周一前出厂家授权文件。中继台和对讲机有品牌要求，我们配合天馈部分。\r\n\r	CPJ202504-004	2025-04-11	108606	\N	\N	2025-04-11 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
85	上海空铁联运	2024-10-24	sales_focus	sales	qualified	\N	华东建筑设计研究院有限公司	上海艾亿智能科技有限公司	\N	上海市安装工程集团有限公司-第九分公司	awarded	2025/4/13 15:07:05 杨俊杰\r\n\r【分销商】：添加   上海瑞康\r\n\r【系统集成商】：改变成   上海市安装工程集团有限公司-第九分公司\r\n\r\r\n\r2025/2/21 13:59:37 杨俊杰\r\n\r【系统集成商】：改变成   上海建工四建集团有限公司\r\n\r\r\n\r2025/2/21 13:57:15 杨俊杰\r\n\r【经销商】：添加   上海艾亿智能科技有限公司\r\n\r\r\n\r2025/2/21 13:57:01 杨俊杰\r\n\r【系统集成商】：改变成   上海市安装工程集团有限公司-第四分公司\r\n\r【当前阶段情况说明】：添加   该项目与浦东东站地下同时招标，招标范围包括装饰、机电和智能化，招标结果公布建工四建安装中标。按招标情况判断项目后续与浦东东站地下一致，计划和建工四建安装跟进确认\r\n\r\r\n\r2024/12/27 杨俊杰\r\n\r【阶段变更】招标中->中标\r\n\r\r\n\r2024/12/6 杨俊杰\r\n\r【阶段变更】品牌植入->招标中\r\n\r类型改变为销售重点 \r\n\r2024/10/24 15:57:16 杨俊杰\r\n\r【完善价格】 153335\r\n\r	SPJ202410-004	2025-04-13	153335	\N	\N	2024-10-24 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
622	嘉兴第二医院（长三角国际医学中心）	2025-06-13	channel_follow	channel	not_required		浙江省建筑设计院	浙江航博智能工程有限公司			awarded	品牌无要求，目前挂靠中通服当地分包中标，预计9月份进场。人员找到已经对接上。	\N	\N	296909	\N	\N	2025-06-13 07:09:56.10595	2025-06-13 07:14:26.308195	15	f	\N	\N	\N	t	2025-06-13 07:09:56.10595	\N	15	1
448	广州中医药大学顺德医院建设项目（易地新建）智能化工程	2025-02-25	channel_follow	channel	qualified	\N	\N	\N	\N	深圳达实智能股份有限公司	lost	2025/3/19 16:59:32 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：改变成   集成商未中标\r\r\n\r\n\r2025/2/25 16:22:54 李冬\r\n\r【授权编号】：添加   HY-CPJ202501-003\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202501-003	2025-03-19	0	\N	\N	2025-02-25 00:00:00	2025-03-19 16:59:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
270	厦门翔安新机场项目	2024-09-27	sales_focus	sales	unqualified	\N	\N	\N	\N	厦门纵横集团科技股份有限公司	discover	2024/10/8 周裔锦\r\n\r【阶段变更】品牌植入->发现\r\r\n\r\n\r2024/9/27 周裔锦\r\n\r【阶段变更】->品牌植入\r\r\n\r\n\r	SPJ202409-014	2024-10-08	0	\N	\N	2024-09-27 00:00:00	2024-10-08 14:41:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
271	厦门天马第6代柔性AM-OLED生产线项目	2024-09-27	sales_focus	sales	unqualified	\N	\N	\N	\N	厦门中智达信息科技有限公司	discover	2024/10/8 周裔锦\r\n\r【阶段变更】品牌植入->发现\r\r\n\r\n\r	SPJ202409-015	2024-10-08	0	\N	\N	2024-09-27 00:00:00	2024-10-08 14:40:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
481	登封市总医院暨公卫应急救治中心建设项目-弱电智能化工程	2025-02-25	channel_follow	sales	\N	\N	\N	\N	\N	\N	pre_tender	2025/2/25 16:26:05 李冬\r\n\r【授权编号】：添加   HY-CPJ202501-014\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/13 10:18:59 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202501-014\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202501-014	2025-02-25	0	\N	\N	2025-02-25 00:00:00	2025-02-25 16:26:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
483	1946水厂项目	2025-02-25	channel_follow	channel	\N	\N	\N	\N	\N	\N	embed	2025/2/25 16:14:40 李冬\r\n\r【授权编号】：添加   HY-CPJ202412-005\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202412-005	2025-02-25	0	\N	\N	2025-02-25 00:00:00	2025-02-25 16:14:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
131	骏景北商业地块	2024-11-10	channel_follow	sales	qualified	\N	\N	广州宇洪科技股份有限公司	\N	深圳中电瑞达智能技术有限公司	awarded	2025/3/31 周裔锦\r\n\r\n「邹莉」 深圳中电瑞达智能技术有限公司  邹经理介绍，虽然我们配合投标，但他们的中标价格比较低，本周会进行品牌报审前询价沟通。\r\n已通知宇洪，本项目涉及竞品：海能达、上海曙腾。\r\n\r\n2025/3/24 10:54:10 周裔锦\r\n\r\n【出货时间预测】：添加   2025年二季度6月份\r\n\r\n\r\n\r\n2025/1/3 周裔锦\r\n\r\n【阶段变更】招标中->中标\r\n\r\n类型改变为渠道跟进 \r\n\r\n2024/11/29 周裔锦\r\n\r\n【阶段变更】招标前->招标中\r\n\r\n\r\n\r\n2024/11/19 10:47:14 周裔锦\r\n\r\n【完善价格】 117392\r\n\r\n	CPJ202411-004	2025-06-01	117392	\N	\N	2024-11-10 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
211	三林楔形绿地39号、40号、41号、42号、43号、44 号地块	2025-01-17	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海行余信息技术有限公司	tendering	2025/1/17 11:49:46 李华伟\r\n\r【完善价格】 207824\r\n\r45674.4928935185 邹飞\r\n\r【完善价格】 207824\r\n\r2025/1/17 11:46:41 李华伟\r\n\r【完善价格】 197182\r\n\r45674.4907523148 邹飞\r\n\r【完善价格】 197182\r\n\r2025/1/17 11:20:19 李华伟\r\n\r【授权编号】：添加   HY-CPJ202501-10\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r45674.4724421296 邹飞\r\n\r【授权编号】：添加   HY-CPJ202501-10\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202501-010	2025-01-17	207824	\N	\N	2025-01-17 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
93	宝安区中医院扩建工程（二期）智能化工程	2025-04-11	channel_follow	channel	unqualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳达实智能股份有限公司	awarded	2025/4/11 11:11:01 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-006\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/11 09:11:48 李冬\r\n\r【授权编号】：添加   HY-CPJ202504-006\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/10 17:39:40 李冬\r\n\r【完善价格】 131529\r\n\r2025/4/10 17:36:27 李冬\r\n\r【当前阶段】：添加   中标\r\r\n【当前阶段情况说明】：添加   集成商中标，配合下一步深化\r\r\n\r\n\r2025/4/6 10:05:42 周裔锦\r\n\r【完善价格】 123548\r\n\r2025/4/3 周裔锦\r\n\r「李莹」 深圳达实智能股份有限公司  李工介绍本项已经中标，当时用的是昊天配合投标，和源报价合适可以配合变更，目前还没到品牌确认阶段。预计最快第三季度会涉及到我们系统的采购。\r\n\r	CPJ202504-006	2025-04-11	123548	\N	\N	2025-04-11 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
112	浦东机场卫星厅无线对讲系统维护	2025-04-02	business_opportunity	sales	qualified	上海国际机场股份有限公司	\N	\N	\N	\N	pre_tender	2025/4/2 13:36:15 徐昊\r\n\r【授权编号】：添加   HY-APJ-202503-013\r\r\n\r\n\r2025/3/28 11:17:54 徐昊\r\n\r【面价金额】：添加   800000\r\r\n\r\n\r2025/3/20 10:08:21 徐昊\r\n\r【当前阶段】：添加   招标前\r\r\n\r\n\r	APJ202503-013	2025-04-02	800000	\N	\N	2025-04-02 00:00:00	2025-05-11 00:59:24.476988	7	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	7	1
509	奉贤住宅07-01&04-02	2024-01-15	channel_follow	channel	qualified	\N	\N	上海瑞康通信科技有限公司	\N	上海沐东机电设备有限公司	tendering	45231 李冬\r\n\r渠道反馈沐东采购询价，应该是配合项目招投标，项目为住宅，采用全系列和源产品。安排渠道复核项目是否为招标阶段\r\n\r2023/11/1 杨俊杰\r\n\r渠道反馈沐东采购询价，应该是配合项目招投标，项目为住宅，采用全系列和源产品。安排渠道复核项目是否为招标阶段\r\n\r	CPJ202401-010	2024-03-11	0	\N	\N	2024-01-15 00:00:00	2024-03-11 11:31:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
623	杭州华东医药一二期项目改造	2025-06-13	channel_follow	channel	not_required			浙江航博智能工程有限公司			embed	项目原来做了系统，现在要改造代理商航博配合出改造方案，对讲机沿用原来的海能达，防爆天馈采用和源产品。后续辅助配合代理商与业主交流方案和造价预算问题。	\N	\N	419480	\N	\N	2025-06-13 07:16:59.827963	2025-06-13 07:19:01.37629	15	f	\N	\N	\N	t	2025-06-13 07:16:59.827963	\N	15	1
99	合肥新桥机场配套用房（综合楼和货运楼）	2025-01-03	sales_focus	sales	qualified	合肥新桥国际机场有限公司	上海远菁工程项目管理有限公司	合肥兴和通讯设备有限公司	\N	南京禄口国际机场空港科技有限公司6	tendering	2025/4/10 17:09:26 郭小会\r\n\r【当前阶段】：改变成   招标中\r\r\n【当前阶段情况说明】：添加   项目品牌延用航站楼部分品牌，此次设计了解到是安徽省院的设计，没有完全参考航站楼的设计\r\r\n\r\n\r2025/4/10 17:06:58 郭小会\r\n\r【经销商】：添加   合肥兴和通讯设备有限公司\r\r\n【系统集成商】：添加   南京禄口国际机场空港科技有限公司6\r\r\n\r\n\r2025/4/10 郭小会\r\n\r「付强」 南京禄口国际机场空港科技有限公司6  和付工沟通货运楼招标文件中的问题，原清单的缺失的设备，付工建议我们先列出来，他们和商务沟通投标策略\r\n\r2025/4/10 郭小会\r\n\r「尤力」 合肥兴和通讯设备有限公司  和尤总沟通货运楼投标参与的集成商情况，商务投标的策略\r\n\r2025/1/3 郭小会\r\n\r类型改变为销售重点 \r\n\r2025/1/3 09:34:31 郭小会\r\n\r【完善价格】 117440\r\n\r	SPJ202501-001	2025-04-10	117440	\N	\N	2025-01-03 00:00:00	2025-02-21 19:00:00	13	f	\N	\N	\N	f	\N	\N	13	2
444	浙江天目山希尔顿酒店	2024-07-19	channel_follow	channel	qualified	\N	\N	浙江航博智能工程有限公司	\N	\N	lost	2025/3/20 14:11:43 李博\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   集成商未中标，项目丢失\r\r\n\r\n\r	CPJ202407-008	2025-03-20	0	\N	\N	2024-07-19 00:00:00	2025-03-20 14:11:00	23	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	\N
508	江西南昌轨交产业园	2024-01-10	channel_follow	sales	qualified	\N	华建集团EPC总承包部	浙江航博智能工程有限公司	\N	\N	embed	45343.5255555556 李博\r\n\r设计方改变为  华建集团EPC总承包部 集成商改变为      \r\n\r2024/2/21 12:36:48 李华伟\r\n\r设计方改变为  华建集团EPC总承包部 集成商改变为      \r\n\r45343.5214236111 李博\r\n\r类型改变为  渠道管理    \r\n\r2024/2/21 12:30:51 李华伟\r\n\r类型改变为  渠道管理    \r\n\r45231 李博\r\n\r目前代理商浙江航博配合华建浙江分公司做预算，品牌无要求，初步沟通选用和源对讲机，后续和客户确认整体预算。\r\n\r2023/11/1 李华伟\r\n\r目前代理商浙江航博配合华建浙江分公司做预算，品牌无要求，初步沟通选用和源对讲机，后续和客户确认整体预算。\r\n\r	CPJ202401-004	2024-03-29	0	\N	\N	2024-01-10 00:00:00	2024-03-29 13:39:00	23	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	\N
538	徐州德基广场	2022-11-19	channel_follow	channel	qualified		北京信诚百年工程技术有限公司上海分公司	上海瑞康通信科技有限公司			awarded	品牌入围，客户中标后一直搁置停工，预计下半年启动进场。	\N	2025-11-29	139038	\N	\N	2025-05-16 05:32:02.666967	2025-06-03 02:15:38.885919	15	t	授权编号审批锁定: 渠道项目报备流程	15	2025-06-03 03:26:31.741336	t	2025-05-24 05:20:56.993177	\N	15	2
147	名创优品项目	2024-08-09	channel_follow	sales	qualified	\N	\N	广州宇洪科技股份有限公司	\N	厦门万安智能有限公司	awarded	2025/3/24 10:53:17 周裔锦\r\n\r\n【出货时间预测】：添加   2025年二季度6月份\r\n\r\n\r\n\r\n2024/12/6 周裔锦\r\n\r\n【阶段变更】招标中->中标\r\n\r\n\r\n\r\n2024/11/29 周裔锦\r\n\r\n【出现困难】宇洪和瀚网都有各自配合的集成商参与投标。\r\n\r\n\r\n\r\n	CPJ202408-005	2025-06-01	170288	\N	\N	2024-08-09 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
148	羊城晚报	2024-07-05	channel_follow	sales	qualified	\N	\N	\N	\N	中建三局智能技术有限公司	awarded	2025/3/24 10:52:56 周裔锦\r\n\r\n【出货时间预测】：添加   2025年二季度6月份\r\n\r\n\r\n\r\n2025/1/3 周裔锦\r\n\r\n【阶段变更】招标中->中标\r\n\r\n\r\n\r\n2024/11/29 周裔锦\r\n\r\n【阶段变更】招标前->招标中\r\n\r\n\r\n\r\n2024/10/27 周裔锦\r\n\r\n【出现困难】三局智能已中标，预计明年5/6月份在云筑网招标。\r\n\r\n\r\n\r\n2024/7/5 16:10:15 庄海鑫\r\n\r\n【提案】「」:  配合集成商对配置进行确定\r\n\r\n	CPJ202407-004	2025-06-01	56173	\N	\N	2024-07-05 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
204	广州黄埔暹岗社区旧村改造项目二期复建区住宅智能化工程	2025-02-13	channel_follow	sales	qualified	\N	\N	广州洪昇智能科技有限公司	\N	\N	pre_tender	2025/2/13 10:19:31 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202502-008\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202502-008	2025-02-13	350236	\N	\N	2025-02-13 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
214	徐汇区华泾镇XHPO-0001单元D5D-1地块	2025-01-11	sales_focus	sales	qualified	\N	华东建筑设计研究院有限公司	\N	\N	\N	embed	2025/1/11 15:56:20 杨俊杰\r\n\r【授权编号】：添加   HY-SPJ202406-004\r\n\r\r\n\r	SPJ202406-004	2025-01-11	1332931	\N	\N	2025-01-11 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
559	杭政储出2023-161号临安区青山湖国际科创中心城市客厅	2025-03-24	channel_follow	channel	qualified			浙江航博智能工程有限公司		中建三局智能技术有限公司	embed	项目同济院设计分包给中建三局在做方案，目前配合三局设计，预算业主还在审核。	CPJ202503-021	\N	575616	yes	\N	2025-05-16 07:17:35.699895	2025-06-03 02:19:15.165578	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
560	杭政储出【2023】34号杭州资本云城科创中心	2024-06-09	channel_follow	channel	qualified		浙江省建筑设计院	浙江航博智能工程有限公司			embed	航博引荐业主认识，通过业主接触设计院负责人，预计下半年招标，后续配合方案设计。	CPJ202409-002	\N	145456	yes	\N	2025-05-16 07:19:19.346181	2025-06-03 02:19:46.400128	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
1	郑州机场配套工程	2025-01-11	sales_focus	marketing	unqualified	\N	中国航空规划设计院	\N	\N	山西云时代技术有限公司	embed	2025/4/26 13:29:13 郭小会\r\n\r\n【当前阶段】：改变成   中标\r\n\r\n【当前阶段情况说明】：添加   山西云时代已中标\r\n\r\n\r\n\r\n2025/4/26 13:28:23 郭小会\r\n\r\n【系统集成商】：添加   山西云时代技术有限公司\r\n\r\n\r\n\r\n2025/1/18 09:27:53 郭小会\r\n\r\n【完善价格】 421273\r\n\r\n2025/1/11 郭小会\r\n\r\n【阶段变更】发现->品牌植入\r\n\r\n类型改变为销售重点 \r\n\r\n2025/4/26 13:29:29 郭小会\r\n\r\n【品牌情况】：改变成   入围\r\n\r\n\r\n\r\n	SPJ202501-002	2025-04-26	421273	\N	\N	2025-01-11 00:00:00	2025-05-16 07:48:12.177119	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
273	长沙机场改扩建配套地下遂道工程	2024-07-14	sales_focus	sales	unqualified	\N	上海市政工程设计研究总院（集团）有限公司	\N	\N	湖南安众智能科技有限公司	pre_tender	2024/9/27 郭小会\r\n\r【阶段变更】招标中->招标前\r\r\n\r\n\r2024/7/14 郭小会\r\n\r湖南长规院许总介绍安众的杨总，参与长沙机场地下隧道项目，给安众杨总介绍我们公司的情况，可以尝试合作\r\n\r	SPJ202407-002	2024-09-27	380417	\N	\N	2024-07-14 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
245	玉佛寺二期	2024-09-27	sales_focus	sales	qualified	\N	同济大学建筑设计研究院(集团)有限公司	\N	\N	\N	embed	2024/11/15 22:06:21 郭小会\r\n\r【完善价格】 1479510\r\n\r	SPJ202409-012	2024-11-15	1479510	\N	\N	2024-09-27 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
510	先进半导体及新型显示用光热固化体系材料项目	2025-05-11	sales_focus	sales	unqualified		中国电子系统工程第二建设有限公司				embed	配合设计院前期规划设计	SPJ202505-001	\N	350108	\N	\N	2025-05-11 14:14:54.4923	2025-05-14 01:07:43.739202	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
143	西部股权投资基金基地弱电工程项目	2024-09-09	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	中建四局智控与数字科技事业部	lost	2025/3/25 14:31:52 郭小会\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   代理商关系不到位，项目失败\r\r\n\r\n\r2024/9/9 13:34:43 郭小会\r\n\r【消息】「」福玛报备，配合集成商\r\r\n【阶段变更】招标中->中标\r\n\r45544.565775463 邹飞\r\n\r【消息】「」福玛报备，配合集成商\r\r\n【阶段变更】招标中->中标\r\n\r	CPJ202409-003	2025-03-25	0	\N	\N	2024-09-09 00:00:00	2025-03-25 14:31:00	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	\N
216	西安咸阳国际机场三期扩建工程口岸货运区项目	2023-07-03	sales_focus	sales	qualified	\N	民航机场成都电子工程设计有限责任公司	陕西无线电通信服务中心	\N	民航成都电子技术有限责任公司	signed	2025/1/3 16:36:13 郭小会\r\n\r【完善价格】 51958\r\n\r2024/7/14 09:25:15 郭小会\r\n\r【消息】「」安排设备交付，设备已交付到陕西无线电，协调好航站楼坏的设备替换问题\r\n\r2024/6/30 07:44:21 郭小会\r\n\r【消息】「」预付款已付，交给董禕处理\r\r\n【阶段变更】中标->签约\r\n\r2024/6/15 09:09:23 郭小会\r\n\r【消息】「」催收预付款，和供应链协调好了订货问题\r\n\r2024/6/9 09:58:22 郭小会\r\n\r【消息】「」西安咸阳机场口岸货站楼区域的光端直放站，陕西无线电已配合总包完成变更，我们双合约已签定\r\n\r2024/4/23 08:32:33 郭小会\r\n\r【消息】「」代理商张总已通过业主找到相应的集成商，进行对接，集成商现场天线和器件已安装完成，张总和集成商进行沟通洽谈，光端机采用和源品牌接入到机场系统，已在走品牌变更流程，统计光端机2近5远\r\n\r2024/3/8 13:28:00 郭小会\r\n\r总包这边之前选用的中原的设备，代理商张总和总包在沟通确认采用和源的光端设备，接入到航站楼\r\n\r2024/2/20 12:09:16 郭小会\r\n\r设计方改变为  民航机场成都电子工程设计有限责任公司 出货时间预测改变为  2024-04-30 当前阶段改变为   中标 类型改变为  销售重点    \r\r\n和陕西无线电沟通询价问题，进行价格保护\r\n\r2023/11/1 郭小会\r\n\r1、项目投标\r\n2、需确认代理商\r\n\r	SPJ202307-001	2025-01-03	51958	\N	\N	2023-07-03 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
196	深圳国际交流中心一期	2025-01-10	channel_follow	sales	qualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳市和一实业有限公司	awarded	2025/2/17 22:16:44 周裔锦\r\n\r【完善价格】 602329\r\n\r45667.7046064815 李冬\r\n\r【授权编号】：改变成   HY-CPJ202501-008\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/1/10 16:54:38 周裔锦\r\n\r【授权编号】：改变成   HY-CPJ202501-008\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202501-008	2025-02-17	602329	\N	\N	2025-01-10 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
136	上海嘉定集成电路研发中心增补	2025-02-28	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海谌亚智能化系统有限公司	signed	2025/3/29 12:56:14 杨俊杰\r\n\r[阶段变更] ->签约\r\n\r2025/3/4 11:31:06 杨俊杰\r\n\r【完善价格】 117500\r\n\r2025/2/28 13:40:11 杨俊杰\r\n\r【完善价格】 142501\r\n\r2025/2/28 13:37:16 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202502-012\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r	CPJ202502-012	2025-03-29	52875	\N	\N	2025-02-28 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
199	上海市皮肤病医院科研综合楼	2024-03-15	channel_follow	sales	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海行余信息技术有限公司	lost	2025/2/17 16:02:05 李华伟\r\n\r【完善价格】 165569\r\n\r2024/3/15 15:16:19 李华伟\r\n\r「阶段变更」\r\r\n「提案」  :  配合集成商设计方案和品牌推荐，目前是按照我们的品牌来植入，后续复核确认。\r\n\r45366.6363310185 邹飞\r\n\r「阶段变更」\r\r\n「提案」  :  配合集成商设计方案和品牌推荐，目前是按照我们的品牌来植入，后续复核确认。\r\n\r2024/3/15 李华伟\r\n\r「拜访」  :  \r\n\r45366 邹飞\r\n\r「拜访」  :  \r\n\r	CPJ202403-005	2025-02-17	165569	\N	\N	2024-03-15 00:00:00	2025-05-16 09:50:19.690242	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
110	西安泰信大厦	2023-07-24	channel_follow	channel	qualified	\N	\N	\N	\N	\N	paused	2025/4/5 郭小会\r\n\r「邹茹飞」 西安瑞林达通信技术有限公司  西安泰信大厦项目资金有问题，项目搁置。和邹总介绍我们公司的产品优势，寻找合作点\r\n\r2025/3/25 14:05:54 郭小会\r\n\r【当前阶段】：改变成   搁置\r\r\n【当前阶段情况说明】：添加   项目资金有问题，搁置了\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r2024/3/9 15:31:38 郭小会\r\n\r项目投标后，总包一直未确定，代理商在跟进着\r\n\r2023/11/1 郭小会\r\n\r代理商报备，西安瑞林达\r\n\r	CPJ202307-002	2025-04-05	141627	\N	\N	2023-07-24 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
155	中江国际集团公司总部新办公园区	2024-03-15	sales_focus	sales	qualified	\N	中国江苏国际经济技术合作集团有限公司建筑设计院	\N	\N	\N	lost	2025/3/14 14:52:22 范敬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   因投资资金减少，取消该系统。\r\r\n\r\n\r2024/6/9 13:07:04 范敬\r\n\r【提案】「」:  目前已完成园区A栋自用办公楼的初步图纸设计，选用MA12定位功能\r\n\r2024/4/25 14:44:25 范敬\r\n\r「消息」「」配合业主及设计方前期设计\r\n\r2024/4/25 14:44:06 范敬\r\n\r「阶段变更」品牌植入->发现\r\n\r2024/3/15 范敬\r\n\r「拜访」  :  约见业主建设部门相关技术负责人，了解项目情况同时介绍公司及产品，提出项目解决方案。\r\n\r	SPJ202403-001	2025-03-14	528356	\N	\N	2024-03-15 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
624	测试批价单项目	2025-06-13	sales_focus	channel	qualified			上海大展通信电子设备有限公司			quoted		\N	\N	3901	\N	\N	2025-06-13 09:32:28.329824	2025-06-13 09:42:00.503535	15	t	批价审批流程进行中	5	2025-06-13 09:42:00.498245	t	2025-06-13 09:32:28.329824	\N	15	\N
209	阿联酋料场	2025-01-18	sales_focus	sales	qualified	\N	中国船舶重工集团国际工程有限公司	上海福玛通信信息科技有限公司	\N	中国中钢股份有限公司	tendering	2025/2/7 09:01:25 郭小会\r\n\r\n【完善价格】 1069048\r\n\r\n2025/1/18 09:51:34 郭小会\r\n\r\n【完善价格】 975738\r\n\r\n2025/1/18 郭小会\r\n\r\n类型改变为销售重点 \r\n\r\n	SPJ202501-003	2025-02-07	1069048	\N	\N	2025-01-18 00:00:00	2025-06-11 15:59:43.129663	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
207	五粮液技术研究中心	2025-02-10	channel_follow	sales	qualified	\N	华东建筑设计研究院有限公司	\N	\N	\N	embed	2025/2/10 11:03:48 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202502-004\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r	CPJ202502-004	2025-02-10	145547	\N	\N	2025-02-10 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
217	芜湖长飞半导体项目	2023-11-02	sales_focus	sales	qualified	安徽长飞先进半导体有限公司	\N	\N	\N	\N	signed	2025/1/3 15:47:12 郭小会\r\n\r【完善价格】 430000\r\n\r2025/1/3 15:42:36 郭小会\r\n\r【完善价格】 427000\r\n\r2025/1/3 15:35:47 郭小会\r\n\r【完善价格】 389000\r\n\r2025/1/3 15:16:49 郭小会\r\n\r【完善价格】 158507\r\n\r2024/8/24 11:03:53 郭小会\r\n\r【消息】「」沟通跟进预付款，预付款上周五已到帐\r\n\r跟进记录 郭小会\r\n\r【阶段变更】中标->签约\r\n\r2024/7/14 09:26:57 郭小会\r\n\r【消息】「」和业主沟通投标中的问题，采购从市场上寻了多家价格进行对比，想重新招标，业主IT负责人从中协调，调整报价，现在基本可以确定我们中标了，下周提交相关资质资料和商谈合同细节\r\r\n【阶段变更】招标中->中标\r\n\r2024/6/15 09:19:26 郭小会\r\n\r【消息】「」现场和业主沟通其公司内部情况和相应节点，和业主合约部门进行商务沟通和谈判\r\r\n【阶段变更】招标前->招标中\r\n\r2024/6/9 09:32:23 郭小会\r\n\r【消息】「」和业主沟通方案和报价问题，下周采购邀请三家去现场谈判，协调福玛和淳泊下周出差，现场谈判\r\n\r2024/5/30 22:24:03 郭小会\r\n\r【消息】「」业主打算自己招标，由IT部门负责招标工作，和业主沟通好入围三家供应商进行投标，IT负责人将其推荐 给采购，选择福玛、淳泊入围 ，计划我们公司中标，分包给淳泊，由淳泊负责实施交付\r\r\n【阶段变更】品牌植入->招标前\r\n\r2024/5/18 10:55:19 郭小会\r\n\r【消息】「」配合长飞业主IT负责人提交方案汇报的的PPT,提交招标技术规格书\r\n\r2024/2/21 12:43:38 郭小会\r\n\r用户改变为   安徽长飞先进半导体有限公司 类型改变为  销售重点    \r\r\n根据业主的需求，将方案和预算提交上去，等待业主内部上会讨论\r\n\r	SPJ202311-001	2025-01-03	339000	\N	\N	2023-11-02 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
226	苏州工业园区20230499地块	2024-06-20	sales_focus	sales	qualified	\N	科进柏城咨询有限公司-上海分公司	\N	\N	\N	embed	2024/12/27 杨俊杰\r\n\r类型改变为销售重点 \r\n\r2024/11/11 16:02:40 杨俊杰\r\n\r【完善价格】 745483\r\n\r2024/6/20 杨俊杰\r\n\r该项目配合华东院陈未参与设计配套，项目分为两个地块，陈未是负责其中一个，另一个由毛晶轶负责，总体设计负责人为王小安。经了解甲方有自己品牌库，和源入围，主要与中瀚竞争\r\n\r	SPJ202406-003	2024-12-27	745483	\N	\N	2024-06-20 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
159	国际旅游度假区北片区01-06地块	2025-03-07	channel_follow	sales	qualified	\N	华东建筑设计研究院有限公司	\N	\N	\N	embed	2025/3/7 11:32:39 杨俊杰\r\n\r【授权编号】：改变成   HY-CPJ202405-015\r\n\r【类型】：改变成   渠道跟进\r\n\r\r\n\r	CPJ202405-015	2025-03-07	284794	\N	\N	2025-03-07 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
276	中国五冶集团有限公司五冶集团临港总部基地	2024-08-26	sales_focus	sales	qualified	\N	\N	\N	\N	\N	discover	\N	SPJ202408-007	2024-09-24	132867	\N	\N	2024-08-26 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
200	董家渡18-01地块	2024-07-26	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海东元信息科技发展有限公司	tendering	2025/2/17 16:00:08 李华伟\r\n\r【完善价格】 72982\r\n\r	CPJ202407-010	2025-02-17	72982	\N	\N	2024-07-26 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
279	上海长宁区天山路街道113街坊34丘E2-03地块办公铁狮门	2023-04-27	channel_follow	sales	qualified	\N	迈进工程设计咨询(上海)有限公司	上海福玛通信信息科技有限公司	\N	上海灵一建筑配套工程有限公司	awarded	2024/3/25 15:03:09 李华伟\r\n\r「阶段变更」\r\r\n「拜访」  :  目前上海福玛配合中建八局中标，刚进场，预计进场在9月份左右。\r\n\r45376.6271875 邹飞\r\n\r「阶段变更」\r\r\n「拜访」  :  目前上海福玛配合中建八局中标，刚进场，预计进场在9月份左右。\r\n\r2024/2/21 12:52:31 李华伟\r\n\r设计方改变为  迈进工程设计咨询(上海)有限公司 类型改变为  渠道跟进     \r\n\r45343.5364699074 邹飞\r\n\r设计方改变为  迈进工程设计咨询(上海)有限公司 类型改变为  渠道跟进     \r\n\r2023/11/1 李华伟\r\n\r目前品牌入围，瀚网配合投标。\r\n\r45231 邹飞\r\n\r目前品牌入围，瀚网配合投标。\r\n\r	CPJ202304-010	2024-09-20	182336	\N	\N	2023-04-27 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
142	湖南绿之韵酒店项目	2024-09-10	channel_follow	sales	unqualified	\N	\N	福淳智能科技(四川)有限公司	\N	湖南悟意信息技术有限公司	lost	2025/3/25 14:37:59 郭小会\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   代理商配合的集成商未中标\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r2024/11/30 郭小会\r\n\r【阶段变更】招标前->招标中\r\r\n类型改变为渠道管理 \r\n\r45626 邹娟\r\n\r【阶段变更】招标前->招标中\r\r\n类型改变为渠道管理 \r\n\r2024/9/10 18:36:43 郭小会\r\n\r【完善价格】 118106\r\n\r45545.7754976852 邹娟\r\n\r【完善价格】 118106\r\n\r	CPJ202409-005	2025-03-25	118106	\N	\N	2024-09-10 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
284	合肥新桥机场一期合路平台改造	2024-08-24	sales_focus	channel	qualified	\N	\N	合肥兴和通讯设备有限公司	\N	\N	signed	2024/8/30 11:36:31 郭小会\r\n\r【消息】「」合肥兴和已从公司拿货，消掉公司库存\r\r\n【阶段变更】中标->签约\r\n\r2024/8/24 11:12:05 郭小会\r\n\r【消息】「」合肥兴和就本次机场对讲系统出现问题，推动合肥机场一期对讲系统更换合路平台，实现逐步替换和源产品，加强用户对和源产品的了解\r\n\r	SPJ202408-006	2024-08-30	9135	\N	\N	2024-08-24 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
107	合肥新桥机场二期新建	2023-11-02	sales_focus	sales	qualified	\N	民航机场成都电子工程设计有限责任公司	合肥兴和通讯设备有限公司	\N	北京京航安机场工程有限公司	awarded	2025/4/10 郭小会\r\n\r「尤力」 合肥兴和通讯设备有限公司  和尤总沟通目前合肥机场的最新情况，尤总已推动业主在会议上明确提出系统方案确定过程中需要现场提供设备，搭建平台进行测试，也通知到集成商，尤总了解到集成商的中标价格和竞争对手的报价，和尤总商量好报价策略，和尤总调整报价发给总包，看总包反应\r\n\r2024/8/24 11:14:20 郭小会\r\n\r【消息】「合肥兴和通讯设备有限公司」和设计院沟通了解到总包这边针对无线对讲系统还没有开始深化设计，没有提交任何资料，设计院会对方案进行把控，要求提交的方案完全满足招标要求；尤总也进一步和用户进行了沟通，用户也会坚持按招标要求来实施\r\n\r2024/5/25 10:25:28 郭小会\r\n\r【消息】「」代理商尤总已安排运营部门的负责人张总参观我们新换数字光端机，介绍了我们光端机的优势和特点，我们一起整理了我们这次投标的系统以及产品亮点，下周尤总和张总详细介绍一下，试图了解新的指挥部的负责人，准备接触影响指挥部的负责人\r\n\r2024/4/24 14:52:01 郭小会\r\n\r【消息】「」已了解到北京京航安中标，出乎意料，之前业主和设计院了解到内定的是西安悦泰，近期想办法确认京航安是否用的我司品牌进行投标\r\r\n【阶段变更】中标->招标中\r\n\r2024/5/18 10:41:19 郭小会\r\n\r【消息】「」合肥出差，和代理商尤总沟通针对合肥机场项目接下来的策略，计划在合肥机场搭建平台，增强业主对我司产品的认可；拜访民航电子设计单位的现场项目经理易总，介绍我们公司的产品和合肥机场我们系统的情况，影响其关注我们系统中存在的问题\r\n\r2024/5/12 09:58:51 郭小会\r\n\r【消息】「」合肥机场通过代理商以及设计院的关系，了解到京航安传输设备采用了中兴高达进行投标，近期要整理相关信息和代理商一起想办法推动更换我司品牌\r\n\r2024/4/13 09:37:17 郭小会\r\n\r配合沈阳汇通、云南机场、京航安几家公司授权及投标文件制作\r\n\r2024/4/6 20:54:37 郭小会\r\n\r协调尤总配合北京中航弱电、南京禄口、云南机场、新疆网信几家集成商投标\r\n\r2024/3/28 07:42:51 郭小会\r\n\r【阶段变更】\r\r\n项目进入投标阶段，和合肥兴和一起配合集成商投标，目前找到了西安悦泰、京航安两家集成商\r\n\r2024/2/20 14:05:02 郭小会\r\n\r围标状况改变为   入围 设计方改变为  民航机场成都电子工程设计有限责任公司 经销商改变为   合肥兴和通讯设备有限公司 用户改变为   合肥新桥国际机场有限公司 类型改变为  渠道管理    \r\r\n已从设计院方面把我们的品牌推上去了，兴和的尤总也将我司品牌推给业主，配合兴和进行前期方案报价\r\n\r	SPJ202311-002	2025-04-10	3301056	\N	\N	2023-11-02 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
98	海南新能源汽车体验中心国际赛车场(一期)	2025-02-19	sales_focus	sales	unqualified	\N	华东建筑设计研究院有限公司	\N	\N	\N	embed	2025/4/11 郭小会\r\n\r「王小安」 华东建筑设计研究院有限公司  和王总沟通最近配合他们三院的项目情况，组织下周和他们组和黄他们组聚餐活动，加强合作，海南新能源汽车项目预算还没有最终确定，目前我们系统还在保留，有些系统已砍掉。待情况明确后，业主负责人明朗后，安排我们对接\r\n\r2025/3/18 17:19:28 郭小会\r\n\r【完善价格】 515277\r\n\r2025/2/19 09:04:40 郭小会\r\n\r【设计院及顾问】：添加   华东建筑设计研究院有限公司\r\r\n【类型】：添加   销售重点\r\r\n\r\n\r2025/2/19 08:57:35 郭小会\r\n\r【授权编号】：添加   HY-SPJ202501-007\r\r\n\r\n\r	SPJ202501-007	2025-04-11	515277	\N	\N	2025-02-19 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
219	浦东机场四期配套能源中心	2024-12-27	sales_focus	sales	unqualified	\N	华东建筑设计研究院有限公司	\N	\N	\N	embed	2024/12/30 郭小会\r\n\r类型改变为 \r\n\r	SPJ202412-005	2024-12-30	441335	\N	\N	2024-12-27 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
152	成都音乐文创总部基地	2025-03-18	channel_follow	marketing	qualified	\N	\N	福淳智能科技(四川)有限公司	\N	安徽数安桥数据科技有限公司	tendering	2025/3/18 17:03:55 郭小会\r\n\r【授权编号】：添加   HY-CPJ202503-007\r\r\n\r\n\r	CPJ202503-007	2025-03-18	473622	\N	\N	2025-03-18 00:00:00	2025-05-16 07:43:41.062048	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
301	成都一带一路大厦	2022-11-27	sales_focus	sales	qualified	\N	中国建筑西南设计研究院有限公司	\N	\N	\N	embed	2024/5/12 10:08:44 郭小会\r\n\r【消息】「」项目近期重启了，业主内部要设计单位进行系统重新审报，和延华的蔡总沟通后，配合蔡总准备相关的PPT汇报文件，修改技术规格\r\n\r2023/11/1 郭小会\r\n\r1、此项目西南院设计，延华是顾问，方案和品牌已植入，招标时间还没有确定\r\n\r	SPJ202211-007	2024-05-12	5783799	\N	\N	2022-11-27 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
512	东航空港总部保障基地项目	2025-06-11	channel_follow	channel	qualified			西安瑞林达通信技术有限公司			awarded	经销商配合集成商报价	CPJ202506-014	\N	124837	\N	申请备注: 经销商配合集成商深化设计和报价	2025-05-14 01:35:43.76431	2025-06-11 11:12:22.831247	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
242	成都市彭州全名健身中心	2024-09-12	channel_follow	channel	unqualified	\N	中国建筑西南设计研究院有限公司	福淳智能科技(四川)有限公司	\N	\N	pre_tender	2024/11/30 郭小会\r\n\r类型改变为渠道管理 \r\n\r45626 邹娟\r\n\r类型改变为渠道管理 \r\n\r	CPJ202409-006	2024-11-30	0	\N	\N	2024-09-12 00:00:00	2024-11-30 20:51:00	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	\N
12	小东门2套公网对讲机	2025-04-25	business_opportunity	\N	\N	上海市黄浦区人民政府小东门街道办事处	\N	\N	\N	\N	signed	2025/4/25 13:24:03 方玲\r\n\r【授权编号】：添加   HY-APJ-202504-009\r\r\n\r\n\r2025/4/25 10:19:20 方玲\r\n\r【完善价格】 1700\r\n\r2025/4/25 方玲\r\n\r「俞麟」 上海市黄浦区人民政府小东门街道办事处  客户确认再购2套公网机器，节后拿货及付款。\r\n\r	APJ202504-009	2025-04-25	0	\N	\N	2025-04-25 00:00:00	2025-05-15 06:40:20.447684	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
123	文华酒店2025年无线对讲维保合同	2025-04-02	business_opportunity	\N	qualified	上海瑞明置业有限公司	\N	\N	\N	\N	signed	2025/4/2 10:06:39 方玲\r\n\r【授权编号】：改变成   HY-APJ-202502-005\r\r\n\r\n\r2025/4/2 10:06:06 方玲\r\n\r【授权编号】：添加   HY-APJ-202502-006\r\r\n\r\n\r2025/2/25 13:39:18 方玲\r\n\r【完善价格】 82596\r\n\r	APJ202502-005	2025-04-02	82595.82	\N	\N	2025-04-02 00:00:00	2025-05-15 06:45:25.85243	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
121	松江站-微型消防站对讲机采购	2025-04-02	business_opportunity	\N	qualified	\N	\N	\N	\N	上海赢安实业有限公司	embed	2025/4/2 10:08:06 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-002\r\r\n\r\n\r2025/4/2 方玲\r\n\r「李方军」 上海赢安实业有限公司  与客户沟通10套对讲机事宜，告知在等业主流程。\r\n\r2025/3/5 11:34:19 方玲\r\n\r【完善价格】 14000\r\n\r	APJ202503-002	2025-04-02	14000	\N	\N	2025-04-02 00:00:00	2025-05-11 00:59:24.476988	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	1
114	市政大厦 远端机及放大器替换	2025-04-02	business_opportunity	\N	qualified	上海市机关事务管理局	\N	\N	\N	\N	pre_tender	2025/4/2 10:16:01 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-010\r\r\n\r\n\r2025/3/21 10:18:58 方玲\r\n\r【完善价格】 34000\r\n\r	APJ202503-010	2025-04-02	34000	\N	\N	2025-04-02 00:00:00	2025-05-11 00:59:24.476988	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	1
37	三亚太古里（国际免税城三期）	2025-04-14	channel_follow	channel	controlled	\N	\N	上海瀚网智能科技有限公司	\N	上海文讯电子有限公司	embed	2025/4/21 14:34:51 李华伟\r\n\r【完善价格】 153238\r\n\r2025/4/14 15:43:15 李华伟\r\n\r【授权编号】：添加   HY-CPJ202412-006\r\r\n\r\n\r2025/4/11 14:07:20 李华伟\r\n\r提交报备\r\n\r2025/4/11 14:06:46 李华伟\r\n\r【当前阶段】：添加   品牌植入\r\r\n【系统集成商】：添加   上海文讯电子有限公司\r\r\n【当前阶段情况说明】：添加   代理商瑞康报备配合文讯植入和源天馈品牌围标，预计下半年招标。\r\r\n\r\n\r2025/2/25 16:16:15 李冬\r\n\r【授权编号】：添加   HY-CPJ202412-006\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202412-006	2025-04-21	153238	\N	\N	2025-04-14 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
56	上海中心 350M远端机替换	2025-04-18	business_opportunity	\N	qualified	上海中心大厦世邦魏理仕物业管理有限公司	\N	\N	\N	\N	pre_tender	2025/4/18 09:17:21 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-014\r\r\n\r\n\r2025/4/14 徐昊\r\n\r「吴恺」 上海中心大厦世邦魏理仕物业管理有限公司  根据拿到的浦东消防救援支队上海中心大厦350兆消防用无线对讲系统的测试报告，与上海中心大厦业主及物业管理部门沟通整改工作，已安排人员把系统内所有故障设备拆除并运输至和源，和源出具设备维修检测报告，根据报告的内容会在后续与物业管理部门沟通，推动下一步设备维修/更换/升级的工作；\r\n\r2025/4/10 14:07:43 方玲\r\n\r【完善价格】 115000\r\n\r2025/4/10 14:04:47 方玲\r\n\r【品牌情况】：添加   入围\r\r\n【当前阶段】：添加   招标前\r\r\n【直接用户】：添加   上海中心大厦世邦魏理仕物业管理有限公司\r\r\n\r\n\r2025/4/10 徐昊\r\n\r「吴恺」 上海中心大厦世邦魏理仕物业管理有限公司  至浦东消防支队，与支队通信负责人余启源对上海中心大厦350兆消防用无线对讲系统测试的结果进行了沟通，拿到支队测试报告的原件，在后续推动上海中心大厦350兆系统设备维修更新的事宜上进行了初步的沟通，并且谈及了系统内设备的数字化提升；\r\n\r2025/4/9 方玲\r\n\r「吴恺」 上海中心大厦世邦魏理仕物业管理有限公司  现场故障的350M设备已拆除完成，后续先安排检测，完成后安排更换新设备\r\n\r2025/4/8 徐昊\r\n\r「吴恺」 上海中心大厦世邦魏理仕物业管理有限公司  与上海中心大厦物业管理公司负责人沟通350兆消防用无线对讲系统测试报告事宜，已安排把盖章版电子档以邮件形式发给物业部门领导，并且安排工程师周三把所有350故障设备拆除运输回和源，对所有设备进行检测，出具维修检测报告，后续以维修检测报告为基础提出设备维修和更新的需求，并且根据报告确定提交上海中心大厦业主实施建议及预算；\r\n\r2025/4/2 13:38:24 徐昊\r\n\r【授权编号】：添加   HY-APJ-202503-014\r\r\n\r\n\r2025/3/31 徐昊\r\n\r「吴恺」 上海中心大厦世邦魏理仕物业管理有限公司  根据浦东新区消防救援支队关于上海中心大厦消防用无线对讲系统的测试报告与业主方沟通350兆光端机更新事宜，安排将所有故障设备寄回检测并出具检测报告，报告内体现设备工作年限维修状况及需要换新的内容，然后设备检测报告结合消防检测报告推进后续工作；\r\n\r2025/3/28 11:16:55 徐昊\r\n\r【面价金额】：添加   100000\r\r\n\r\n\r2025/3/20 10:36:20 徐昊\r\n\r【当前阶段】：添加   发现\r\r\n【当前阶段情况说明】：添加   根据上海市消防总队和浦东支队在现场对于350兆消防用无线对讲系统测试的结果提出设备更新的需求\r\r\n\r\n\r	APJ202503-014	2025-04-18	115000	\N	\N	2025-04-18 00:00:00	2025-05-11 00:59:24.476988	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	1
561	成都五粮液集团新经济中心	2024-09-26	channel_follow	channel	qualified			福淳智能科技(四川)有限公司			tendering		CPJ202409-007	2025-05-16	127600	yes	\N	2025-05-16 07:20:33.179001	2025-05-16 07:30:30.469256	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
126	上海金融交易广场400M无线对讲系统优化项目	2025-04-02	business_opportunity	\N	qualified	\N	\N	\N	\N	\N	signed	2025/4/2 09:43:13 方玲\r\n\r【授权编号】：添加   HY-APJ-202502-001\r\r\n\r\n\r2025/2/20 14:31:45 方玲\r\n\r【完善价格】 76025\r\n\r	APJ202502-001	2025-04-02	0	\N	\N	2025-04-02 00:00:00	2025-05-15 06:46:45.568803	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
419	复旦大学附属中山医院国家医学中心	2024-08-26	channel_follow	channel	controlled	\N	\N	上海瑞康通信科技有限公司	\N	上海慧谷多高信息工程有限公司	lost	2025/4/7 17:34:42 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   配合集成商未中标\r\r\n\r\n\r	CPJ202408-012	2025-04-07	0	\N	\N	2024-08-26 00:00:00	2025-04-07 17:34:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
14	赛车场-F1学院赛及F1方程式	2025-04-25	business_opportunity	\N	\N	上海国际赛车场经营发展有限公司	\N	\N	\N	\N	signed	2025/4/25 13:22:52 方玲\r\n\r【授权编号】：添加   HY-APJ-202504-007\r\r\n\r\n\r2025/4/23 21:48:43 方玲\r\n\r【完善价格】 15500\r\n\r2025/4/23 方玲\r\n\r「黄周迪」 上海国际赛车场经营发展有限公司  服务已完成，客户确认不用三方审价，直接签订合同开票。\r\n\r	APJ202504-007	2025-04-25	15500	\N	\N	2025-04-25 00:00:00	2025-05-15 06:40:38.895781	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
15	赛车场-4月CTCC赛事服务	2025-04-25	business_opportunity	\N	\N	\t上海久事国际体育中心有限公司	\N	\N	\N	\N	signed	2025/4/25 13:22:21 方玲\r\n\r【授权编号】：添加   HY-APJ-202504-006\r\r\n\r\n\r2025/4/23 21:47:16 方玲\r\n\r【完善价格】 7008\r\n\r2025/4/23 方玲\r\n\r「黄周迪」 \t上海久事国际体育中心有限公司  确认赛事服务时间，需要人员保障，保障安排工作。\r\n\r	APJ202504-006	2025-04-25	7008	\N	\N	2025-04-25 00:00:00	2025-05-15 06:42:03.256662	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
119	科思创写频线采购	2025-04-02	business_opportunity	\N	qualified	科思创聚合物(中国)有限公司	\N	\N	\N	\N	signed	2025/4/2 10:09:36 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-004\r\r\n\r\n\r2025/3/11 13:28:20 方玲\r\n\r【完善价格】 360\r\n\r	APJ202503-004	2025-04-02	359.98	\N	\N	2025-04-02 00:00:00	2025-05-15 06:43:54.763764	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
243	新疆库尔勒万丽万怡酒店	2024-11-22	channel_follow	channel	qualified	\N	\N	广州宇洪科技股份有限公司	\N	\N	awarded	2024/11/22 16:10:09 周裔锦\r\n\r【完善价格】 23990\r\n\r	CPJ202411-010	2024-11-29	23990	\N	\N	2024-11-22 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
285	上海波克中心	2023-03-09	channel_follow	channel	qualified	\N	\N	上海鑫桉信息工程有限公司	\N	上海擎天电子科技有限公司	awarded	2024/2/21 13:05:03 李华伟\r\n\r分销商改编为   上海淳泊  经销商改变为   上海鑫桉信息工程有限公司    \r\n\r2024/2/21 13:03:36 李华伟\r\n\r类型改变为  渠道跟进     \r\n\r2023/11/1 李华伟\r\n\r品牌入围，代理商瀚网配合书柏，鑫桉配合上海擎天投标。\r\n\r	CPJ202303-003	2024-08-16	49560	\N	\N	2023-03-09 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
501	张江集团·周浦医疗器械总部园	2024-04-09	channel_follow	channel	controlled	上海张江国信安地产有限公司	\N	上海瑞康通信科技有限公司	\N	上海壹杰信息技术有限公司	tendering	45391 李冬\r\n\r渠道报备，配合集成商壹杰参与投标\r\n\r2024/4/9 杨俊杰\r\n\r渠道报备，配合集成商壹杰参与投标\r\n\r	CPJ202404-003	2024-12-27	0	\N	\N	2024-04-09 00:00:00	2024-12-27 13:42:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
260	浦东东站地道工程	2024-02-26	sales_focus	sales	controlled	\N	上海市政工程设计研究总院（集团）有限公司	\N	\N	\N	embed	2024/3/20 16:00:18 杨俊杰\r\n\r市政院王微微反馈施工图已经送审，下一阶段进入招标前准备，但这部分由招标代理完成，按她所述招标代理会咨询他们建议，与其沟通是否可以引荐招标代理，锁定和源品牌，并提供技术要求\r\n\r2024/2/26 12:04:15 杨俊杰\r\n\r面价金额改变为   1215837    \r\n\r2024/2/26 11:03:47 杨俊杰\r\n\r设计方改变为  上海市政工程设计研究总院「集团」有限公司    \r\r\n该项目市政院王微微负责设计，项目分为站东路和站前路两条隧道，配套参与项目设计\r\n\r	SPJ202402-003	2024-10-24	1215837	\N	\N	2024-02-26 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
35	文山州妇女儿童医院	2025-04-21	sales_focus	sales	unqualified	\N	\N	\N	\N	\N	embed	2025/4/21 23:26:14 郭小会\r\n\r【授权编号】：添加   HY-SPJ202504-003\r\r\n【类型】：添加   销售重点\r\r\n\r\n\r2025/4/20 08:36:10 郭小会\r\n\r【完善价格】 257186\r\n\r2025/4/20 08:34:54 郭小会\r\n\r【完善价格】 200826\r\n\r2025/4/20 08:27:17 郭小会\r\n\r【完善价格】 265263\r\n\r	SPJ202504-003	2025-04-21	257186	\N	\N	2025-04-21 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
124	科思创40套GP338D+防爆对讲机	2025-04-02	business_opportunity	\N	\N	科思创聚合物(中国)有限公司	\N	\N	\N	\N	signed	2025/4/2 10:05:15 方玲\r\n\r【授权编号】：添加   HY-APJ-202502-004\r\r\n\r\n\r	APJ202502-004	2025-04-02	210000	\N	\N	2025-04-02 00:00:00	2025-05-15 06:42:57.194611	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
97	科思创1套防爆机	2025-04-11	business_opportunity	\N	\N	科思创聚合物(中国)有限公司	\N	\N	\N	\N	signed	2025/4/11 09:23:57 方玲\r\n\r【授权编号】：添加   HY-APJ-202504-001\r\r\n\r\n\r2025/4/7 11:14:39 方玲\r\n\r【完善价格】 5250\r\n\r2025/4/7 方玲\r\n\r「liguo.ren」 科思创聚合物(中国)有限公司  客户需采购1套防爆对讲机，下单P8668i ,沟通此款机器供货问题，协商更换GP338D+防爆机器；客户重新更换型号下单。\r\n\r	APJ202504-001	2025-04-11	0	\N	\N	2025-04-11 00:00:00	2025-05-15 06:46:29.468511	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
42	科思创-150套防爆对讲机	2025-04-18	business_opportunity	\N	\N	科思创聚合物(中国)有限公司	\N	\N	\N	\N	pre_tender	2025/4/21 方玲\r\n\r「Kevien」 科思创聚合物(中国)有限公司  与客户确认预计二季度下订单，要先确认可供设备型号，一次性供货；目前等待供应链给可供型号。\r\n\r2025/4/18 09:16:06 方玲\r\n\r【授权编号】：添加   HY-APJ-202504-005\r\r\n\r\n\r2025/4/17 14:41:35 方玲\r\n\r【完善价格】 750000\r\n\r2025/4/17 方玲\r\n\r「Kevien」 科思创聚合物(中国)有限公司  预订购防爆对讲机，数量150套，沟通目前使用型号，先询供货期，用户8月底前要收到。\r\n\r	APJ202504-005	2025-04-21	750000	\N	\N	2025-04-18 00:00:00	2025-05-11 00:59:24.476988	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	1
57	科思创10套防爆机	2025-04-18	business_opportunity	\N	\N	科思创聚合物(中国)有限公司	\N	\N	\N	\N	signed	2025/4/18 09:15:14 方玲\r\n\r【授权编号】：添加   HY-APJ-202504-004\r\r\n\r\n\r2025/4/17 10:26:22 方玲\r\n\r【当前阶段】：改变成   中标\r\r\n\r\n\r2025/4/17 10:25:10 方玲\r\n\r【完善价格】 36750\r\n\r2025/4/16 15:32:12 方玲\r\n\r【完善价格】 52500\r\n\r	APJ202504-004	2025-04-18	36750	\N	\N	2025-04-18 00:00:00	2025-05-15 06:44:23.285258	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
232	浦东机场假日酒店	2023-10-23	channel_follow	sales	qualified	\N	上海德恳设计咨询顾问有限公司	上海瀚网智能科技有限公司	\N	上海信业智能科技股份有限公司	lost	2024/12/16 李华伟\r\n\r【出现困难】中标方信业退出，由于资金全垫资，业主找了南京一家公司信息打听不到。\r\r\n\r\n\r2024/2/21 12:50:48 李华伟\r\n\r围标状况改变为   入围 设计方改变为  上海德恳设计咨询顾问有限公司 分销商改编为   上海瑞康 经销商改变为   上海瀚网智能科技有限公司 类型改变为  渠道管理 集成商改变为  上海信业智能科技股份有限公司    \r\n\r2023/11/1 李华伟\r\n\r目前品牌配合植入和源、中兴、海能达。预计23年底左右招标。\r\n\r	CPJ202310-003	2024-12-16	144710	\N	\N	2023-10-23 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
308	合肥新桥机场一期改造	2023-04-19	sales_focus	channel	qualified	\N	民航机场成都电子工程设计有限责任公司	合肥兴和通讯设备有限公司	\N	\N	signed	2024/4/12 23:36:32 郭小会\r\n\r【阶段变更】\r\n\r2024/2/20 14:57:42 郭小会\r\n\r当前阶段改变为   中标 面价金额改变为   120834 用户改变为       \r\n\r2024/2/20 13:49:35 郭小会\r\n\r设计方改变为  民航机场成都电子工程设计有限责任公司 出货时间预测改变为  2024-04-30 用户改变为   合肥新桥国际机场有限公司 类型改变为  渠道管理    \r\r\n已确定本次改造替换我们最新的数字光端机，一近两远，订单已确定，货已下。借用库存模拟光端机临时现场使用\r\n\r2023/11/1 郭小会\r\n\r合肥新桥机场一期业主现场通信去年出现过应急通信问题，武总他们在配合业主进行升级改造。配合其提供相关资料和报价\r\n\r	SPJ202304-001	2024-04-12	120834	\N	\N	2023-04-19 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
113	科思创10防爆机	2025-04-02	business_opportunity	\N	\N	科思创聚合物(中国)有限公司	\N	\N	\N	\N	signed	2025/4/2 10:19:22 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-011\r\r\n\r\n\r2025/3/25 20:49:51 方玲\r\n\r【当前阶段】：改变成   中标\r\r\n\r\n\r2025/3/21 10:12:57 方玲\r\n\r【完善价格】 52500\r\n\r	APJ202503-011	2025-04-02	52500	\N	\N	2025-04-02 00:00:00	2025-05-15 06:45:04.418985	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
58	金山乐高  软件布署	2025-04-18	business_opportunity	\N	qualified	\N	\N	\t上海瑞康通信科技有限公司	\N	\N	signed	2025/4/18 09:13:57 方玲\r\n\r【授权编号】：添加   HY-APJ-202504-003\r\r\n\r\n\r2025/4/16 15:33:00 方玲\r\n\r【完善价格】 2600\r\n\r	APJ202504-003	2025-04-18	2600	\N	\N	2025-04-18 00:00:00	2025-05-15 06:44:42.010651	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
60	上海龙旗项目	2024-01-15	channel_follow	sales	qualified	上海龙旗科技股份有限公司	卓展工程顾问(北京)有限公司-上海分公司	上海瀚网智能科技有限公司	\N	上海云赛智联信息科技有限公司	awarded	2025/4/18 杨俊杰\r\n\r\n「周杰」 上海云赛智联科技有限公司  帮助渠道拜访周杰，了解到他们中标，项目进度比较着急，他们原先是由沅亢郭鹏配合，用的科立讯，按周杰意思主要还是在于价格，重新分析设备成本，提供清单报价，在给予跟进\r\n\r\n2025/4/13 15:08:52 杨俊杰\r\n\r\n【分销商】：添加   上海瑞康\r\n\r\n【经销商】：添加   上海瀚网智能科技有限公司\r\n\r\n【系统集成商】：添加   上海云赛智联科技有限公司\r\n\r\n\r\n\r\n2025/4/10 15:03:33 杨俊杰\r\n\r\n【当前阶段】：改变成   中标\r\n\r\n【当前阶段情况说明】：改变成   该项目云赛智联中标，他们是通过用户IT部门负责人关系最后进入，低价中标，经了解他们投标当时选用科立讯，提供清单报价，通过用户及顾问看是否能够扭转局势，从而拉回与集成商谈判在平等条件下\r\n\r\n\r\n\r\n2025/4/10 10:40:01 李冬\r\n\r\n【完善价格】 438705\r\n\r\n2025/4/10 09:51:23 李冬\r\n\r\n【当前阶段】：改变成   中标\r\n\r\n【当前阶段情况说明】：改变成   云赛中标，品牌和源，瀚网，科立讯\r\n\r\n\r\n\r\n2025/4/10 09:41:30 李冬\r\n\r\n【经销商】：添加   上海瀚网智能科技有限公司\r\n\r\n【系统集成商】：改变成   上海云赛智联信息科技有限公司\r\n\r\n\r\n\r\n2025/4/10 李冬\r\n\r\n「倪刚」 上海云赛智联信息科技有限公司  向几家配合过得集成商打听了中标情况，得知云赛中标，最后向销售证实云赛确定中标。目前和集成商沟通。目前品牌和源瀚网科立讯，存在不确定因素。希望和源可以在业主那边把品牌把控。\r\n\r\n2025/4/9 杨俊杰\r\n\r\n「李霄云」 卓展工程顾问(北京)有限公司-上海分公司  拜访卓展李霄云，反馈九星城项目，了解龙旗项目及新增业务情况。有关龙旗该项目，得到反馈云赛智联中标，他们是通过用户IT部门负责人关系最后进入，低价中标，经了解他们投标当时选用科立讯。后续计划通过用户及顾问看是否能够扭转局势，从而拉回与集成商谈判在平等条件下\r\n\r\n2025/3/13 14:37:01 杨俊杰\r\n\r\n【直接用户】：添加   上海龙旗科技股份有限公司\r\n\r\n【当前阶段情况说明】：添加   该项目经了解投标还未有最终结果，主要是云思和云赛在最后竞争\r\n\r\n\r\n\r\n2025/2/27 09:21:08 李冬\r\n\r\n【系统集成商】：添加   上海延华智能科技（集团）股份有限公司\r\n\r\n\r\n\r\n2025/2/25 14:56:46 李冬\r\n\r\n【授权编号】：添加   HY-CPJ202401-008\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n2025/2/21 17:19:42 杨俊杰\r\n\r\n【完善价格】 1029081\r\n\r\n2024/12/27 杨俊杰\r\n\r\n类型改变为销售重点 \r\n\r\n2024/12/6 杨俊杰\r\n\r\n【阶段变更】品牌植入->招标中\r\n\r\n\r\n\r\n2024/5/20 15:23:19 杨俊杰\r\n\r\n【消息】「」该项目与机电顾问卓展李霄云沟通，项目即将启动智能化施工图设计，初步达成合作意向，后续推进业务技术配套，植入核心产品\r\n\r\n2024/2/26 17:33:14 杨俊杰\r\n\r\n设计方改变为  卓展工程顾问「北京」有限公司-上海分公司    \r\n\r\n2024/2/26 17:32:58 杨俊杰\r\n\r\n类型改变为  销售重点    \r\n\r\n2024/2/26 12:03:37 杨俊杰\r\n\r\n面价金额改变为   660081    \r\n\r\n该项目卓展史伟杰告知，目前他们仅提供业主一版项目概算，图纸设计由于设计院还未全部完成，所以还没定稿，设计院负责机电设计，他们负责弱电智能化，现阶段还不确定设计进度，一直在催促设计院完成图纸设计\r\n\r\n2023/11/1 杨俊杰\r\n\r\n该项目卓展李霄云负责智能化设计，咨询我们配套设计方案。计划跟进了解项目设计进度，确认设计方案，推动招标品牌入围\r\n\r\n	CPJ202401-008	2025-07-10	1029081	\N	\N	2024-01-15 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
22	中国民生银行金融科技研发中心项目	2023-11-20	sales_focus	sales	qualified	\N	中元国际工程设计研究院有限公司	敦力(南京)科技有限公司	\N	\N	embed	2025/4/24 范敬\r\n\r「钱澄雨」 中元国际工程设计研究院有限公司  沟通了该项目的推进情况，目前该项目已从原落地合肥变更为福州；同时沟通了目前其负责的贵州项目。\r\n\r2024/7/29 10:12:48 范敬\r\n\r【消息】「」指导代理商敦力进行图纸和方案设计\r\n\r2024/7/18 07:47:30 范敬\r\n\r【消息】「」进入施工图设计阶段\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、配合设计院规划技术参数要求，提出推荐品牌；\r\n2、设计院出图阶段；\r\n\r	SPJ202311-004	2025-04-24	0	\N	\N	2023-11-20 00:00:00	2025-04-24 00:00:00	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	\N
220	上海曙光医院肝病中心	2022-12-27	channel_follow	sales	controlled	\N	悉地国际设计顾问(深圳)有限公司上海分公司	上海瀚网智能科技有限公司	\N	\N	lost	2024/12/30 李华伟\r\n\r【出现困难】系统取消\r\r\n类型改变为渠道跟进 \r\n\r2024/2/21 13:01:55 李华伟\r\n\r类型改变为  渠道跟进     \r\n\r2023/11/1 李华伟\r\n\r项目配合设计，植入和源设备，预计年后招标。\r\n\r	CPJ202212-003	2024-12-30	81378	\N	\N	2022-12-27 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
309	上海御桥12C-18地块	2024-03-29	channel_follow	sales	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海行余信息技术有限公司	embed	\N	CPJ202403-013	2024-03-29	82798	\N	\N	2024-03-29 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
118	基美电子-防爆天线	2025-04-02	business_opportunity	\N	qualified	\N	\N	\N	\N	上海先景电子科技有限公司	embed	2025/4/2 10:12:38 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-005\r\r\n\r\n\r2025/3/11 13:30:22 方玲\r\n\r【完善价格】 34800\r\n\r2025/3/5 11:31:45 方玲\r\n\r【完善价格】 22800\r\n\r2025/3/5 11:26:21 方玲\r\n\r【系统集成商】：添加   上海先景电子科技有限公司\r\r\n\r\n\r	APJ202503-005	2025-04-02	34800	\N	\N	2025-04-02 00:00:00	2025-05-11 00:59:24.476988	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	1
96	国金3套干放	2025-04-11	business_opportunity	\N	qualified	\N	\N	\N	\N	上海置根智能电子技术有限公司	signed	2025/4/11 09:26:22 方玲\r\n\r【授权编号】：添加   HY-APJ-202504-002\r\r\n\r\n\r2025/4/10 14:15:13 方玲\r\n\r【完善价格】 25350\r\n\r2025/4/10 方玲\r\n\r「舒俊」 上海置根智能电子技术有限公司  新订购3套干放，走订单流程\r\n\r	APJ202504-002	2025-04-11	25350	\N	\N	2025-04-11 00:00:00	2025-05-15 06:40:56.510575	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
115	赤通2套防爆对讲机	2025-04-02	business_opportunity	\N	\N	\N	\N	\N	\N	上海赤通冷链物流有限公司	signed	2025/4/2 10:15:14 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-009\r\r\n\r\n\r2025/3/21 10:06:15 方玲\r\n\r【完善价格】 3900\r\n\r	APJ202503-009	2025-04-02	3900	\N	\N	2025-04-02 00:00:00	2025-05-15 06:43:14.938076	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
106	2025赛车场对讲机采购	2025-04-02	business_opportunity	\N	\N	\t上海久事国际体育中心有限公司	\N	\N	\N	\N	awarded	2025/4/10 方玲\r\n\r「黄周迪」 \t上海久事国际体育中心有限公司  对讲机的三方协议已全部盖章完成，等第三方核价。\r\n\r2025/4/2 10:04:16 方玲\r\n\r【授权编号】：添加   HY-APJ-202502-003\r\r\n\r\n\r2025/2/24 16:02:39 方玲\r\n\r【面价金额】：添加   198000\r\r\n\r\n\r	APJ202502-003	2025-04-10	198000	\N	\N	2025-04-02 00:00:00	2025-05-15 06:41:43.831185	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
125	2024 NF 对讲机系统改善项目	2025-04-02	business_opportunity	\N	qualified	中芯南方集成电路制造有限公司	\N	\N	\N	中芯南方集成电路制造有限公司	signed	2025/4/2 09:48:56 方玲\r\n\r【授权编号】：添加   HY-APJ-202502-002\r\r\n\r\n\r2025/3/27 22:08:50 方玲\r\n\r【完善价格】 313516\r\n\r2025/3/27 21:43:33 方玲\r\n\r【当前阶段】：改变成   中标\r\r\n【当前阶段情况说明】：改变成   第一次报价完成，已入围；进入议价；\r\n订单已确认，已收到PO。\r\r\n\r\n\r2025/2/20 15:40:29 方玲\r\n\r【完善价格】 184023\r\n\r	APJ202502-002	2025-04-02	299265.62	\N	\N	2025-04-02 00:00:00	2025-05-15 06:45:42.219464	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
231	中原高铁港数字展贸城	2024-12-07	channel_follow	channel	qualified	河南空港建设发展有限公司	同济大学建筑设计研究院（集团）有限公司	敦力(南京)科技有限公司	\N	\N	embed	2024/12/21 19:35:52 范敬\r\n\r【完善价格】 720113\r\n\r2024/12/21 19:35:52 花伟\r\n\r【完善价格】 720113\r\n\r2024/12/16 范敬\r\n\r类型改变为渠道管理 \r\n\r2024/12/16 花伟\r\n\r类型改变为渠道管理 \r\n\r	CPJ202412-003	2024-12-21	720113	\N	\N	2024-12-07 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
563	中国电信北京信息科技创新园项目-A4研发楼	2025-05-13	channel_follow	channel	qualified		中通服咨询设计研究院有限公司	敦力(南京)科技有限公司			discover	配合设计院完成方案与清单编制	\N	2025-11-13	208904	pending	申请备注: 是同一项目，不同标段	2025-05-16 07:23:10.345634	2025-05-16 08:26:22.646597	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
555	中国电信北京信息科技创新园项目-A1创新验证中心	2025-05-13	channel_follow	channel	qualified		中通服咨询设计研究院有限公司	敦力(南京)科技有限公司			embed	代理商配合设计院完成初步设计	\N	2025-11-13	162921	pending	\N	2025-05-16 07:09:38.290508	2025-05-16 08:24:16.139003	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
542	雄安国贸中心（D03-04-41/42/43/44号地块）项目--航站楼及地下空间	2025-05-10	sales_focus	sales	qualified		北京博易基业工程顾问有限公司				embed	目前配合设计院初步规划方案	\N	2026-06-16	602561	pending	\N	2025-05-16 06:02:19.974189	2025-05-29 07:49:50.316482	16	t	授权编号审批锁定: 渠道项目报备流程	16	2025-06-12 03:35:04.411762	t	2025-05-24 05:20:56.993177	\N	16	1
172	阳澄湖健康颐养酒店	2023-06-30	channel_follow	sales	qualified	\N	\N	苏州邦耀电子	\N	\N	embed	2025/2/25 15:32:06 范敬\r\n\r【完善价格】 272060\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n配合集成商修改调整方案\r\n\r	CPJ202306-004	2025-02-25	272060	\N	\N	2023-06-30 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
236	徐州市睢宁县医院院区智能化工程项目	2024-05-09	channel_follow	sales	qualified	\N	南京市建筑设计研究院有限责任公司	敦力(南京)科技有限公司	\N	\N	embed	2024/5/9 范敬\r\n\r配合设计院完成方案清单设计\r\n\r2024/5/9 花伟\r\n\r配合设计院完成方案清单设计\r\n\r	CPJ202405-003	2024-12-13	175868	\N	\N	2024-05-09 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
292	江宁九龙湖国际企业总部园二期项目	2023-03-09	channel_follow	sales	qualified	\N	华东建筑设计研究院有限公司	敦力(南京)科技有限公司	\N	\N	embed	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n目前处于项目前期规划设计\r\n\r2023/11/1 花伟\r\n\r「阶段变更」\r\r\n目前处于项目前期规划设计\r\n\r	CPJ202303-002	2024-07-11	301086	\N	\N	2023-03-09 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
206	兴化天宝皇冠酒店智能化项目	2025-02-11	channel_follow	channel	qualified	\N	\N	敦力(南京)科技有限公司	\N	苏州中亿丰科技有限公司	embed	2025/2/11 10:17:54 范敬\r\n\r【授权编号】：添加   HY-CPJ202502-006\r\r\n\r\n\r2025/2/11 10:17:54 花伟\r\n\r【授权编号】：添加   HY-CPJ202502-006\r\r\n\r\n\r	CPJ202502-006	2025-02-11	176468	\N	\N	2025-02-11 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
225	芜湖梦溪科创走廊一期项目	2024-11-09	channel_follow	channel	qualified	\N	\N	敦力(南京)科技有限公司	\N	江苏锐泽思通信技术有限公司	lost	2024/12/28 范敬\r\n\r【阶段变更】招标中->失败\r\r\n\r\n\r2024/12/7 范敬\r\n\r【阶段变更】招标前->招标中\r\r\n\r\n\r2024/12/1 范敬\r\n\r【阶段变更】品牌植入->招标前\r\r\n\r\n\r2024/11/9 09:56:49 范敬\r\n\r【完善价格】 852209\r\n\r	CPJ202411-003	2024-12-28	852209	\N	\N	2024-11-09 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
289	芜湖第四人民医院（安定医院）	2024-07-05	sales_focus	sales	qualified	\N	东南大学建筑设计研究院	\N	\N	\N	embed	2024/7/5 范敬\r\n\r【提案】:  配合设计院在做前期方案规划初设。\r\n\r	SPJ202407-001	2024-07-18	518741	\N	\N	2024-07-05 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
174	无锡国家软件园五期项目	2023-09-05	channel_follow	sales	unqualified	\N	\N	敦力(南京)科技有限公司	\N	\N	embed	2025/2/25 15:26:36 范敬\r\n\r【完善价格】 374246\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n前期配合设计品牌植入\r\n\r2023/11/1 花伟\r\n\r「阶段变更」\r\r\n前期配合设计品牌植入\r\n\r	CPJ202309-004	2025-02-25	374246	\N	\N	2023-09-05 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
213	天津梅江国际会展中心（改建）	2024-11-09	sales_focus	channel	\N	\N	\N	北京联航迅达通信技术有限公司	\N	中建八局-华北分公司	discover	2025/1/12 19:33:01 范敬\r\n\r【当前阶段情况说明】：添加   原渠道来源填写有误\r\r\n\r\n\r	SPJ202411-008	2025-01-12	0	\N	\N	2024-11-09 00:00:00	2025-01-12 19:33:00	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	\N
195	温州国际博览中心	2022-11-08	sales_focus	sales	qualified	\N	\N	\N	\N	\N	paused	2025/2/21 10:58:46 范敬\r\n\r【当前阶段】：改变成   搁置\r\r\n【当前阶段情况说明】：添加   项目因资金问题，暂时处于停工阶段。\r\r\n\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、项目已设计完成，目前推荐品牌海能达、科立讯、和源通信。现阶段已配合咨询公司编制预算。甲方具体负责弱电的还没有问到。\r\n2、目前设计院正在根据甲方要求调整智能化整体设计方案。\r\n\r\n\r	SPJ202211-006	2025-02-21	3649725	\N	\N	2022-11-08 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
89	四川农村商业联合银行股份有限公司黄舣数\r\n据中心机房	2025-03-29	sales_focus	channel	qualified	\N	中国建筑设计研究院有限公司	敦力(南京)科技有限公司	\N	\N	embed	2025/4/12 09:17:52 范敬\r\n\r【完善价格】 229911\r\n\r2025/4/2 09:34:11 范敬\r\n\r【品牌情况】：添加   入围\r\r\n【类型】：添加   销售重点\r\r\n\r\n\r2025/3/29 07:58:58 范敬\r\n\r【授权编号】：添加   HY-SPJ202503-003\r\r\n\r\n\r2025/3/24 13:20:07 范敬\r\n\r【经销商】：添加   敦力(南京)科技有限公司\r\r\n\r\n\r2025/3/22 10:13:48 范敬\r\n\r【分销商】：添加   上海淳泊\r\r\n\r\n\r2025/3/22 10:13:26 范敬\r\n\r【设计院及顾问】：添加   中国建筑设计研究院有限公司\r\r\n\r\n\r	SPJ202503-003	\N	229911	\N	\N	2025-03-29 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
215	深圳乐高乐园度假区项目	2025-01-07	sales_focus	sales	unqualified	\N	\N	\N	\N	\N	paused	2025/1/7 08:52:46 范敬\r\n\r【授权编号】：改变成   HY-SPJ202211-008\r\r\n【类型】：添加   销售重点\r\r\n\r\n\r\n[阶段变更] 搁置  → 搁置 (更新者: admin, 时间: 2025-05-09 09:25:57)	SPJ202211-008	2025-01-07	3050914	\N	\N	2025-01-07 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
130	上海静安太保家园	2024-03-27	channel_follow	channel	qualified	\N	\N	敦力(南京)科技有限公司	\N	泽宇科技工程有限公司	signed	2025/3/31 范敬\r\n\r「花伟」 敦力(南京)科技有限公司  完成批价流程\r\n\r2025/3/29 08:23:40 范敬\r\n\r[阶段变更] ->签约\r\n\r2025/3/25 16:12:03 范敬\r\n\r【完善价格】 117016\r\n\r2025/2/14 17:36:25 范敬\r\n\r【出货时间预测】：添加   2025年一季度3月份\r\r\n\r\n\r2025/2/14 17:36:25 花伟\r\n\r【出货时间预测】：添加   2025年一季度3月份\r\r\n\r\n\r2025/1/14 12:07:52 范敬\r\n\r【完善价格】 232024\r\n\r2025/1/14 12:07:52 花伟\r\n\r【完善价格】 232024\r\n\r2024/12/1 范敬\r\n\r【阶段变更】招标前->中标\r\r\n\r\n\r2024/12/1 花伟\r\n\r【阶段变更】招标前->中标\r\r\n\r\n\r2024/7/11 16:43:05 范敬\r\n\r【提案】「」:  经销商已配合集成商投标，结果未出。\r\n\r2024/7/11 16:43:05 花伟\r\n\r【提案】「」:  经销商已配合集成商投标，结果未出。\r\n\r2024/3/27 15:10:19 范敬\r\n\r「提案」  :  配合代理商完成招标前的项目清单及预算\r\n\r2024/3/27 15:10:19 花伟\r\n\r「提案」  :  配合代理商完成招标前的项目清单及预算\r\n\r	CPJ202403-010	2025-03-31	52657.200000000004	\N	\N	2024-03-27 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
553	苏州工业园区桑田科学岛科创中心（DK20230478/20240047地块）项目	2025-03-29	sales_focus	sales	qualified			苏州邦耀电子科技有限公司		苏州沸点科技有限公司	awarded		\N	2025-07-16	140127	pending	\N	2025-05-16 06:50:29.763808	2025-05-28 08:26:01.278384	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
173	武汉阳逻国际冷链产业园区项目	2023-09-05	channel_follow	sales	unqualified	\N	\N	\N	\N	\N	embed	2025/2/25 15:29:07 范敬\r\n\r【完善价格】 153598\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n配合方案设计，品牌植入\r\n\r	CPJ202309-003	2025-02-25	153598	\N	\N	2023-09-05 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
176	麒麟科创园3-3地块2号楼智能化工程	2024-11-16	channel_follow	channel	qualified	\N	\N	敦力(南京)科技有限公司	\N	盛云科技有限公司南京分公司	pre_tender	2025/2/25 15:16:06 范敬\r\n\r【完善价格】 193868\r\n\r2024/11/16 17:15:56 范敬\r\n\r【完善价格】 193872\r\n\r	CPJ202411-007	2025-02-25	193868	\N	\N	2024-11-16 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
298	南通昱景希尔顿酒店	2023-11-29	channel_follow	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	苏州朗捷通智能科技有限公司	signed	2024/6/9 13:09:41 范敬\r\n\r【阶段变更】中标->签约\r\n\r2024/5/29 14:20:28 范敬\r\n\r【阶段变更】签约->中标\r\n\r2024/5/28 14:33:34 范敬\r\n\r【提案采纳】「」:  已签约\r\r\n【阶段变更】中标->签约\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、该项目目前集成商苏州朗捷通智能科技有限公司中标，据了解该项目只对中继台及对讲机有品牌要求（摩托罗拉、建伍），天馈系统未有要求；目前正在通过关系找到业主，看有无可能进行品牌调整修改；\r\n2、目前有较多供应商正在报价，等待业主选择。\r\n3、正在进行第二轮报价。\r\n\r	CPJ202311-006	2024-06-09	20275.199999999997	\N	\N	2023-11-29 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
571	石景山区中关村科技园区石景山园北1区1605-650地块B23研发设计用地项目	2025-04-27	channel_follow	sales	qualified						embed	目前配合集成商设计方案	CPJ202504-030	2025-09-24	212746	yes	\N	2025-05-16 08:56:38.676176	2025-05-28 06:41:31.432295	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
295	南京燕子矶新城医院工程	2023-01-30	sales_focus	sales	qualified	\N	东南大学建筑设计研究院	敦力(南京)科技有限公司	\N	\N	paused	2024/7/5 10:41:56 范敬\r\n\r【阶段变更】品牌植入->招标前\r\n\r2024/7/5 10:32:56 范敬\r\n\r【提案】「」:  与设计方及预算编制方进行了方案沟通，在清单参数编制中设置了M11馈电型天线参数要求，主机推荐品牌：摩托、海能达、和源；天馈系统品牌：和源、淳泊、瀚网\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n施工图图纸深化设计阶段\r\n\r	SPJ202301-001	2024-07-05	643544	\N	\N	2023-01-30 00:00:00	2025-06-12 03:44:29.015091	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
263	南京悦柳酒店	2022-11-08	channel_follow	sales	controlled	\N	\N	敦力(南京)科技有限公司	\N	盛云科技有限公司南京分公司	pre_tender	2024/6/29 11:19:38 范敬\r\n\r【消息】「」该项目总包单位已进场，智能化系统已进入招标准备阶段。\r\r\n【阶段变更】品牌植入->招标前\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、项目由集成商负责前期设计，品牌围标。\r\n2、已进入招标代理机构编制预算中。\r\n3、该项目预计11月会进入招投标阶段。\r\n4、已和郭总所发“中策项目信息”核对。\r\n\r	CPJ202211-002	2024-10-19	408340	\N	\N	2022-11-08 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
171	南京市鼓楼区2019G61地块项目（中信泰富江苏总部）	2022-12-28	channel_follow	sales	qualified	\N	南京长江都市建筑设计院	敦力(南京)科技有限公司	\N	南京熊猫信息产业有限公司	awarded	2025/2/25 15:39:17 范敬\r\n\r【当前阶段】：改变成   中标\r\r\n\r\n\r2025/2/25 15:11:14 范敬\r\n\r【系统集成商】：添加   南京熊猫信息产业有限公司\r\r\n【当前阶段情况说明】：添加   目前智能化中标单位已进场\r\r\n\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n项目现在处于设计阶段（具体设计师：吴玥群）\r\n\r2023/11/1 花伟\r\n\r「阶段变更」\r\r\n项目现在处于设计阶段（具体设计师：吴玥群）\r\n\r	CPJ202212-004	2025-02-25	644950	\N	\N	2022-12-28 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
145	南京江北新金融中心一期项目DFG地块弱电智能化工程	2024-12-01	sales_focus	sales	qualified	\N	华东建筑设计研究院有限公司	敦力(南京)科技有限公司	\N	中国江苏国际经济技术合作有限公司	awarded	2025/3/24 13:14:01 范敬\r\n\r【出货时间预测】：添加   2025年三季度\r\r\n\r\n\r2025/2/14 09:25:58 范敬\r\n\r【完善价格】 1506548\r\n\r2025/1/6 14:44:12 范敬\r\n\r【当前阶段】：改变成   中标\r\r\n【当前阶段情况说明】：添加   目前中标公示已结束，集成商正在与业主沟通中\r\r\n\r\n\r2024/12/7 19:08:17 范敬\r\n\r【完善价格】 1257796\r\n\r	SPJ202412-001	2025-03-24	1506548	\N	\N	2024-12-01 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
146	桑田科学岛科创中心项目东片区实验室项目（行政楼）	2024-11-16	sales_focus	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	苏州宏凡信息科技有限公司	awarded	2025/3/24 13:12:35 范敬\r\n\r\n【出货时间预测】：添加   2025年二季度\r\n\r\n\r\n\r\n2024/11/16 范敬\r\n\r\n【出现困难】需要与苏州地产品牌：邦耀电子和苏州中瀚两个品牌PK；\r\n\r\n\r\n\r\n2024/11/16 17:46:23 范敬\r\n\r\n【完善价格】 184100\r\n\r\n	SPJ202411-012	2025-06-24	116960	\N	\N	2024-11-16 00:00:00	2025-05-16 06:56:22.647226	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
160	开封火车站前综合交通枢纽工程勘查设计商业	2025-03-07	channel_follow	sales	qualified	\N	上海市政工程设计研究总院（集团）有限公司	\N	\N	\N	embed	2025/3/7 11:31:09 杨俊杰\r\n\r【授权编号】：改变成   HY-CPJ202408-017\r\n\r【类型】：改变成   渠道跟进\r\n\r\r\n\r	CPJ202408-017	2025-03-07	362566	\N	\N	2025-03-07 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
193	南京建宁西路隧道东延段项目	2022-11-08	sales_focus	sales	qualified	\N	苏交科集团股份有限公司南京设计中心	敦力(南京)科技有限公司	\N	\N	pre_tender	2025/2/21 11:59:49 范敬\r\n\r【当前阶段】：改变成   招标前\r\r\n【当前阶段情况说明】：添加   目前机电分包意向性中标人已确定，但还未进场。\r\r\n\r\n\r2024/7/20 14:09:31 范敬\r\n\r【消息】「」项目目前还处于土建阶段，预计2024年底土建结构完成；计划2025年机电开始招标，计划2025年底建成。目前土建总包，一标段：中铁十二局；二标段：中建三局；三标段：中建八局；四标段：中铁上海工程局集团有限公司。\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n项目初步设计已完成，按和源品牌设计。\r\n\r	SPJ202211-005	2025-02-21	645204	\N	\N	2022-11-08 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
570	晋城职业技术学院迁建项目	2025-04-27	channel_follow	channel	controlled		中通服咨询设计研究院有限公司	敦力(南京)科技有限公司			embed	代理商配合集成商设计图纸及编制清单	CPJ202504-029	2025-08-20	563513.556	yes	\N	2025-05-16 08:53:15.663419	2025-05-28 07:02:07.828086	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
264	常州建科股份大楼	2023-12-25	sales_focus	sales	qualified	\N	南京长江都市建筑设计院	敦力(南京)科技有限公司	\N	\N	lost	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、配合设计院完成初步设计图纸，\r\n\r	SPJ202312-002	2024-10-19	367785	\N	\N	2023-12-25 00:00:00	2025-06-12 11:47:21.098572	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
205	广州纺织博览中心	2025-02-13	channel_follow	sales	qualified	\N	\N	广州洪昇智能科技有限公司	\N	\N	pre_tender	2025/2/13 10:18:24 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202502-007\r\r\n\r\n\r	CPJ202502-007	2025-02-13	149764	\N	\N	2025-02-13 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
177	江山汇项目 D 地块弱电智能化工程项目	2024-05-17	channel_follow	channel	qualified	\N	\N	敦力(南京)科技有限公司	\N	\N	embed	2025/2/25 14:45:12 范敬\r\n\r【完善价格】 205651\r\n\r2024/9/21 16:12:56 范敬\r\n\r【完善价格】 205653\r\n\r2024/9/21 16:12:56 花伟\r\n\r【完善价格】 205653\r\n\r2024/5/17 范敬\r\n\r【提案】:  配合集成商出设计、方案及清单\r\n\r2024/5/17 花伟\r\n\r【提案】:  配合集成商出设计、方案及清单\r\n\r	CPJ202405-006	2025-02-25	205651	\N	\N	2024-05-17 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
290	集创北方总部暨显示驱动芯片设计和先进测试基地项目	2023-05-18	channel_follow	sales	qualified	\N	\N	北京联航迅达通信技术有限公司	\N	北京泰豪智能工程有限公司	pre_tender	2024/7/18 07:58:02 范敬\r\n\r【提案】「」:  正在编标中，预计8月底或9月初进入招标。\r\r\n【阶段变更】品牌植入->招标前\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n配合集成商出方案和配置\r\n\r	CPJ202305-001	2024-07-18	97202	\N	\N	2023-05-18 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
287	杭州阿里巴巴总部西溪七期	2024-07-29	channel_follow	sales	qualified	\N	南京长江都市建筑设计院	敦力(南京)科技有限公司	\N	\N	embed	2024/7/29 范敬\r\n\r配合设计院完成初步设计\r\n\r2024/7/29 花伟\r\n\r配合设计院完成初步设计\r\n\r	CPJ202407-011	2024-07-29	148433	\N	\N	2024-07-29 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
169	国家会展中心(北区)厨房工程项目（天津）	2025-02-11	channel_follow	sales	qualified	\N	\N	天津比信科技股份有限公司	\N	清华同方股份有限公司同方智慧建筑与园区公司	tendering	2025/2/28 08:51:20 范敬\r\n\r【当前阶段】：改变成   招标中\r\r\n【系统集成商】：改变成   清华同方股份有限公司同方智慧建筑与园区公司\r\r\n【当前阶段情况说明】：改变成   项目已进入招投标阶段，目前总包方及业主方意向性中标方为清华同方。\r\r\n\r\n\r2025/2/14 09:12:01 范敬\r\n\r【完善价格】 476420\r\n\r2025/2/11 09:28:45 范敬\r\n\r【授权编号】：添加   HY-CPJ202502-005\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202502-005	2025-02-28	476420	\N	\N	2025-02-11 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
128	国家会议中心二期配套项目（酒店项目）	2025-03-25	channel_follow	sales	\N	\N	\N	\N	\N	北京时代凌宇科技股份有限公司	awarded	2025/4/2 09:20:33 范敬\r\n\r【分销商】：添加   上海淳泊\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/3/25 15:16:30 范敬\r\n\r【授权编号】：添加   HY-CPJ202503-022\r\r\n\r\n\r	CPJ202503-022	2025-04-02	0	\N	\N	2025-03-25 00:00:00	2025-04-02 09:20:00	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
238	北京颐缇港二期627地块项目	2024-08-31	sales_focus	sales	unqualified	\N	\N	北京联航迅达通信技术有限公司	\N	北京国隆信达通信技术有限公司	embed	2024/12/9 范敬\r\n\r【阶段变更】中标->品牌植入\r\r\n\r\n\r2024/9/7 10:47:41 范敬\r\n\r【消息】「」目前设计的技术标准设计院及顾问公司参考的和源产品参数，经了解目前业主方没有目前品牌要求；集成商正在找不同品牌厂家询价。\r\n\r	SPJ202408-009	2024-12-09	1987305	\N	\N	2024-08-31 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
21	北京新首钢园东南区1612-(774-779-784)地块项目	2024-02-28	sales_focus	sales	qualified	\N	\N	北京联航迅达通信技术有限公司	\N	中建三局智能技术有限公司	signed	2025/4/25 范敬\r\n\r「吴会从」 中建三局智能技术有限公司  拜访了项目部吴总，沟通了后续项目实施中的问题；包括软件部署等问题。\r\n\r2025/4/22 范敬\r\n\r「吴会从」 中建三局智能技术有限公司  拜访了项目部吴总，沟通了后续项目实施中的问题；包括软件部署等问题。\r\n\r2024/8/31 15:23:11 范敬\r\n\r【阶段变更】中标->签约\r\r\n\r\n\r2024/8/18 14:14:38 范敬\r\n\r【消息】「」与代理商沟通批价事宜\r\n\r2024/7/20 14:22:50 范敬\r\n\r【消息】「」779地块计划2025年6月完工\r\n\r2024/7/18 07:49:05 范敬\r\n\r【一致行动人】「」:  经销商联航迅达中标，进入合同签订阶段。784、774地块年底完工。\r\n\r2024/7/12 范敬\r\n\r【提案采纳】「」:  本项目基本确定和源提供的方案；未中标单位已收到消息；中标通知书暂未发出。\r\n\r2024/7/5 10:46:01 范敬\r\n\r【消息】「」第一轮投标结束，进入第二轮投标。二轮投标单位：北京联航迅达、雄安雄然、瀚网（共三家）；投标品牌：全部和源。\r\n\r2024/6/29 12:09:38 范敬\r\n\r【消息】「」该项目已于2024年6月25日完成招标资格预审，目前共有5家入围：淳泊、福玛、联航迅达、瀚网、雄安雄然电子；7月1日第一轮投标截止。\r\n\r2024/6/22 12:15:28 范敬\r\n\r【消息】「」本周集成商开始进行供应商招标工作，现已安排4-5家供应商报名进行资格预审，报名工作6.25中午结束。\r\n\r2024/6/11 10:48:59 范敬\r\n\r【阶段变更】品牌植入->中标\r\n\r2024/6/9 13:15:13 范敬\r\n\r【提案】「」:  配合集成商完成招采前的询价工作\r\n\r2024/5/31 21:34:30 范敬\r\n\r【提案】「」:  配合业主方要求做了系统优化\r\n\r2024/4/20 11:02:02 范敬\r\n\r沟通了最新的项目进展，774地块今年10月计划完工，779地块计划明年上半年完工。\r\n\r2024/4/15 17:00:34 范敬\r\n\r「提案」  :  更新了新的配置清单\r\n\r2024/3/22 14:06:07 范敬\r\n\r「提案」  :  向总包提交了新方案及报价\r\n\r	SPJ202402-004	2025-04-25	347690.84	\N	\N	2024-02-28 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
208	白下都市工业园项目	2025-02-07	channel_follow	channel	qualified	\N	\N	敦力(南京)科技有限公司	\N	朗高科技有限公司	embed	2025/2/7 14:01:11 范敬\r\n\r【系统集成商】：改变成   朗高科技有限公司\r\r\n【授权编号】：添加   HY-CPJ202501-013\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/7 14:01:11 花伟\r\n\r【系统集成商】：改变成   朗高科技有限公司\r\r\n【授权编号】：添加   HY-CPJ202501-013\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202501-013	2025-02-07	480197	\N	\N	2025-02-07 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
261	安吉“两山”未来科技城文化艺术中心项目	2023-09-05	channel_follow	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	朗高科技有限公司	embed	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n前期设计，品牌植入\r\n\r2023/11/1 花伟\r\n\r「阶段变更」\r\r\n前期设计，品牌植入\r\n\r	CPJ202309-001	2024-10-19	271226	\N	\N	2023-09-05 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
293	安徽黄山市徽州体育馆	2023-09-05	channel_follow	channel	qualified	\N	\N	敦力(南京)科技有限公司	\N	\N	embed	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n前期设计，品牌植入\r\n\r2023/11/1 花伟\r\n\r「阶段变更」\r\r\n前期设计，品牌植入\r\n\r	CPJ202309-002	2024-07-11	84108	\N	\N	2023-09-05 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
302	阿里江苏总部园区C地块项目	2023-03-27	channel_follow	sales	qualified	\N	南京长江都市建筑设计院	敦力(南京)科技有限公司	\N	\N	embed	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、配合设计院初步设计，品牌(技术)植入\r\n2、本周拜访了业主在项目上的负责人，目前对于对讲系统的政策主机品牌为摩托罗拉唯一指定，其他不做指定；集成商为2021年选中集成商库中选择；\r\n\r2023/11/1 花伟\r\n\r「阶段变更」\r\r\n1、配合设计院初步设计，品牌(技术)植入\r\n2、本周拜访了业主在项目上的负责人，目前对于对讲系统的政策主机品牌为摩托罗拉唯一指定，其他不做指定；集成商为2021年选中集成商库中选择；\r\n\r	CPJ202303-004	2024-05-04	476348	\N	\N	2023-03-27 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
178	MY07 Dragonfly 总包项目	2024-12-21	channel_follow	channel	qualified	\N	\N	敦力(南京)科技有限公司	\N	\N	embed	2025/2/25 14:23:51 范敬\r\n\r【完善价格】 524616\r\n\r2025/1/3 范敬\r\n\r类型改变为渠道跟进 \r\n\r2025/1/3 花伟\r\n\r类型改变为渠道跟进 \r\n\r	CPJ202412-008	2025-02-25	524616	\N	\N	2024-12-21 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
569	北京新首钢园东南区1612-(769)地块项目-软件增补	2025-05-12	sales_focus	sales	qualified						embed	集成商正在上报业主，等待批复	\N	2025-06-25	57900	\N	\N	2025-05-16 08:50:50.456594	2025-05-28 07:17:35.065842	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
277	哔哩哔哩上海总部大楼	2024-09-14	sales_focus	sales	qualified	\N	思迈建筑咨询(上海)有限公司	\N	\N	\N	embed	2024/9/18 11:43:42 李华伟\r\n\r【完善价格】 421627\r\n\r	SPJ202409-008	2024-09-24	421627	\N	\N	2024-09-14 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
281	江阴澄星广场及大厦办公区域智能化项目	2024-08-09	channel_follow	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	江苏智威信息工程有限公司	pre_tender	2024/8/23 15:08:14 范敬\r\n\r类型改变为  渠道跟进 \r\n\r	CPJ202408-004	2024-09-07	229944	\N	\N	2024-08-09 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
470	北京天科合达项目	2025-02-28	channel_follow	channel	qualified	\N	\N	北京联航迅达通信技术有限公司	\N	\N	embed	2025/2/28 11:38:13 邹飞\r\n\r【授权编号】：添加   HY-CPJ202405-002\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/7/18 08:36:06 范敬\r\n\r【消息】「」集成商预算已上报，目前没有新进展\r\n\r2024/5/9 09:47:01 范敬\r\n\r【消息】「」配合集成商完成系统设计及方案清单配置\r\n\r	CPJ202405-002	2025-02-28	0	\N	\N	2025-02-28 00:00:00	2025-02-28 11:38:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	\N
191	河套深港科技创新合作区协同创新区（皇岗口岸片区协同创新区）	2025-02-13	sales_focus	sales	unqualified	\N	香港华艺设计顾问（深圳）有限公司	\N	\N	\N	discover	2025/2/21 13:24:22 周裔锦\r\n\r【当前阶段】：改变成   发现\r\r\n【当前阶段情况说明】：添加   由于项目刚中设计部，智能化设计尚未启动，改为发现阶段。\r\r\n\r\n\r2025/2/13 10:22:03 周裔锦\r\n\r【授权编号】：改变成   HY-SPJ202412-004\r\r\n【类型】：添加   销售重点\r\r\n\r\n\r2024/12/30 郭小会\r\n\r类型改变为 \r\n\r	SPJ202412-004	2025-02-21	0	\N	\N	2025-02-13 00:00:00	2025-02-21 13:24:00	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	\N
158	嘉兴圆通货运机场	2025-03-10	channel_follow	sales	qualified	\N	浙江省建筑设计院	浙江航博智能工程有限公司	\N	\N	discover	2025/3/10 09:52:29 李华伟\r\n\r【授权编号】：改变成   HY-CPJ202404-007\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r	CPJ202404-007	2025-03-10	63216	\N	\N	2025-03-10 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
310	西安咸阳国际机场三期扩建工程	2023-02-14	sales_focus	sales	qualified	\N	民航机场成都电子工程设计有限责任公司	陕西无线电服务中心	\N	中国移动通信集团陕西有限公司西安分公司	signed	2024/3/17 14:19:05 郭小会\r\n\r【阶段变更】\r\n\r2024/2/20 12:05:31 郭小会\r\n\r设计方改变为  民航机场成都电子工程设计有限责任公司 出货时间预测改变为  2024-04-30 当前阶段改变为   中标 类型改变为  销售重点 集成商改变为  中国移动通信集团陕西有限公司西安分公司    \r\r\n沟通、安排项目深化，核成本，推动合约流程\r\n\r2023/11/1 郭小会\r\n\r前期设计\r\n\r	SPJ202302-001	2024-03-17	3639451	\N	\N	2023-02-14 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
311	河南省确山县人民医院新区医院建设项目	2023-06-09	channel_follow	sales	qualified	\N	\N	河南天际达实业有限公司	\N	浪朝软件科技有限公司	tendering	2023/11/1 郭小会\r\n\r1、集成商投标，暂时还没有消息，需要继续跟进\r\n\r	CPJ202306-002	2024-03-06	68160	\N	\N	2023-06-09 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
305	苏州工业园区20200118地块智能化项目	2023-01-04	channel_follow	sales	qualified	\N	\N	苏州邦耀电子科技有限公司	\N	\N	signed	2024/4/21 19:59:17 范敬\r\n\r[阶段变更] ->签约\r\n\r2024/4/12 15:49:24 范敬\r\n\r「阶段变更」\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、招投标询价阶段\r\n2、下周一确认清单和预测时间\r\n3、下周集成商开始询价，代理商需要公司渠道予以关注此时，做好价格保护。\r\n4、代理商目前正在与集成商商务谈判及合同流程，但需要协调先行提供部分产品（天线、功分耦合器）；\r\n5、目前已协调分销商先行借货40套天线及功分耦合器；\r\n6、苏州代理商（邦耀）提供最终深化清单；\r\n7、批价沟通中；\r\n8、代理商提交相关资料，对项目申请特价；\r\n\r	CPJ202301-002	2024-04-21	65620	\N	\N	2023-01-04 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
304	上海光通信有限公司集成电路厂房	2023-04-06	channel_follow	sales	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海书柏智能科技有限公司	signed	2024/4/30 17:26:02 李华伟\r\n\r[阶段变更] ->签约\r\n\r2024/4/26 13:32:01 李华伟\r\n\r「阶段变更」签约->中标\r\n\r2024/2/21 13:03:20 李华伟\r\n\r分销商改编为   上海瑞康 类型改变为  渠道跟进     \r\n\r2023/11/1 李华伟\r\n\r配合永峻、书柏投标，品牌围标。\r\n项目配合未中标，杨俊杰配合客户上海谌亚中标其他代理商在对接。\r\n\r	CPJ202304-001	2024-04-30	85524.75	\N	\N	2023-04-06 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
312	御桥10A02地块	2022-11-25	channel_follow	sales	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海行余信息技术有限公司	signed	2024/3/1 17:30:19 李华伟\r\n\r[阶段变更] ->签约\r\n\r2024/2/26 14:01:55 李华伟\r\n\r当前阶段改变为   签约    \r\n\r2024/2/21 12:56:11 李华伟\r\n\r分销商改编为   上海淳泊  面价金额改变为   239084 类型改变为  渠道管理    \r\n\r2023/11/1 李华伟\r\n\r品牌入围，代理商配合凯通行余投标。2023.7.31 李华伟提供信息  已中标\r\n\r	CPJ202211-014	2024-03-01	175792.05	\N	\N	2022-11-25 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
507	常州建筑科学研究院检验检测总部大楼	2024-06-07	channel_follow	channel	controlled	\N	常州电信工程有限公司	浙江航博智能工程有限公司	\N	\N	lost	45450 李博\r\n\r【提案】:  航博配合电信设计，植入和源品牌，对讲机品牌还在沟通是否能进去。\r\n\r2024/6/7 李华伟\r\n\r【提案】:  航博配合电信设计，植入和源品牌，对讲机品牌还在沟通是否能进去。\r\n\r	CPJ202406-003	2024-06-07	0	\N	\N	2024-06-07 00:00:00	2025-06-03 02:23:16.46438	23	f	\N	\N	\N	f	2025-05-24 05:20:56.993177	\N	15	\N
319	茂名中央公园	2023-04-14	channel_follow	sales	qualified	\N	上海邮电设计咨询研究院有限公司	广州宇洪智能技术有限公司	\N	杰创智能科技股份有限公司	tendering	2024/2/21 21:08:22 郭小会\r\n\r集成商改变为  杰创智能科技股份有限公司    \r\r\n代理商配合集成沟通方案和报价，总承包还未确定弱电分包\r\n\r2024/2/21 20:54:57 郭小会\r\n\r设计方改变为  上海邮电设计咨询研究院有限公司 分销商改编为   上海瑞康 经销商改变为   广州宇洪智能技术有限公司 类型改变为  渠道管理    \r\n\r2023/11/1 郭小会\r\n\r1、项目初设\r\n2、品牌已入围 ，大总包开始询价，安排宇洪对接\r\n\r	CPJ202304-002	2024-02-21	155220	\N	\N	2023-04-14 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
120	赛车场保时捷赛事	2025-04-02	business_opportunity	\N	\N	\t上海久事国际体育中心有限公司	\N	\N	\N	\N	signed	2025/4/2 10:09:02 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-003\r\r\n\r\n\r2025/3/11 13:20:33 方玲\r\n\r【完善价格】 7008\r\n\r	APJ202503-003	2025-04-02	7008	\N	\N	2025-04-02 00:00:00	2025-05-15 06:46:04.122016	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	2
315	浙中新能源汽车城市广场	2023-04-18	channel_follow	sales	qualified	\N	\N	\N	\N	\N	embed	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n配合设计院进行项目初期设计\r\n\r	CPJ202304-004	2024-03-01	391058	\N	\N	2023-04-18 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
316	上海打浦桥社区文化活动中心	2023-03-30	channel_follow	channel	qualified	\N	\N	苏州邦耀电子	\N	\N	embed	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n配合集成商进行方案设计及品牌植入\r\n\r	CPJ202303-006	2024-03-01	33503	\N	\N	2023-03-30 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
314	山东青岛创意文化综合体建设项目	2022-11-08	channel_follow	sales	qualified	\N	\N	\N	\N	上海宝冶集团有限公司	embed	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n项目为EPC项目，目前与中标方宝冶项目部安装经理联系沟通此项目。\r\n\r	CPJ202211-006	2024-03-01	305198	\N	\N	2022-11-08 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
313	青岛市山东路立交地下空间	2022-11-08	channel_follow	sales	qualified	\N	\N	\N	\N	\N	embed	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n配合设计院完成设计，按和源品牌推荐。\r\n\r	CPJ202211-005	2024-03-01	69716	\N	\N	2022-11-08 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
317	东台市金融广场	2023-04-19	channel_follow	sales	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	\N	embed	2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、配合项目系统设计、预算及品牌\r\n2、该项目目前已和分销商沟通，有淳泊进行配合跟踪；\r\n\r45231 邹飞\r\n\r「阶段变更」\r\r\n1、配合项目系统设计、预算及品牌\r\n2、该项目目前已和分销商沟通，有淳泊进行配合跟踪；\r\n\r	CPJ202304-006	2024-03-01	304490	\N	\N	2023-04-19 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
9	龙舟计划二期--增补	2025-04-25	channel_follow	channel	qualified	\N	\N	北京联航迅达通信技术有限公司	\N	北京航天星桥科技股份有限公司	signed	2025/4/25 14:49:15 范敬\r\n\r申请项目批价\r\n\r2025/4/25 14:48:14 范敬\r\n\r【授权编号】：添加   HY-CPJ202504-028\r\r\n\r\n\r2025/4/25 范敬\r\n\r「王超」 北京联航迅达通信技术有限公司  该部分对讲机已启动批价流程\r\n\r2025/4/22 范敬\r\n\r「马经理」 北京航天星桥科技股份有限公司  该部分对讲机已返回工厂调整功率。\r\n\r2025/4/17 09:15:39 范敬\r\n\r提交报备\r\n\r2025/4/16 09:23:11 范敬\r\n\r【完善价格】 58652\r\n\r	CPJ202504-028	2025-04-25	26393.4	\N	\N	2025-04-25 00:00:00	2025-06-03 02:19:15.981056	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
280	上海瑞明星产业化及研发中心	2024-09-14	sales_focus	sales	controlled	\N	\N	\N	\N	北京真视通科技有限公司	embed	2024/9/18 11:27:55 李华伟\r\n\r【完善价格】 115210\r\n\r2024/9/18 11:27:06 李华伟\r\n\r【完善价格】 106530\r\n\r	SPJ202409-009	2025-04-03	115210	\N	\N	2024-09-14 00:00:00	2025-06-03 02:21:33.712136	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
250	上海惠柏新材研发总部大楼	2024-11-01	sales_focus	sales	qualified	\N	\N	\N	\N	上海书柏智能科技有限公司	lost	2024/11/1 16:38:58 李华伟\r\n\r【完善价格】 130256\r\n\r	SPJ202411-005	2025-02-25	130256	\N	\N	2024-11-01 00:00:00	2025-06-03 02:22:14.316332	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
529	学院路科技园东升园（H地块）项目	2025-06-12	channel_follow	sales	qualified		清华大学建筑设计研究院有限公司	北京联航迅达通信技术有限公司		仁恩格（北京）科技有限公司	quoted	项目已招标完毕，目前该标段中标方已联系上。	CPJ202506-016	2025-06-24	68846	\N	申请备注: 同一项目，不同标段	2025-05-16 04:17:39.088179	2025-06-12 03:58:31.919438	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
27	招商银行深圳总部大厦（增补）	2025-04-23	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳达实智能股份有限公司	signed	2025/4/23 16:47:08 周裔锦\r\n\r申请项目批价\r\n\r2025/4/23 16:45:58 周裔锦\r\n\r申请项目批价\r\n\r2025/4/23 16:12:02 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202504-034\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/23 13:24:06 周裔锦\r\n\r【完善价格】 118512\r\n\r	CPJ202504-034	2025-04-23	53330.4	\N	\N	2025-04-23 00:00:00	2025-06-03 02:31:29.132262	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
605	海宁经开智创园增补	2025-06-03	channel_follow	channel	qualified			上海瑞康通信科技有限公司		华维星电技术有限公司	signed	客户增补天线	\N	2025-05-25	57600	\N	\N	2025-06-03 02:14:48.244692	2025-06-03 02:29:35.463787	15	t	授权编号审批锁定: 渠道项目报备流程	15	2025-06-03 03:21:34.870751	t	2025-06-03 02:14:48.244692	\N	15	2
556	金桥南区WH4A-1金谷通用厂房二期	2025-06-03	channel_follow	channel	qualified			上海福玛通信信息科技有限公司		中电科数字技术股份有限公司	tendering	品牌和源朔通，目前配合客户投标。预计近期出结果，中电科几率较大。	CPJ202506-001	\N	310398	\N	\N	2025-05-16 07:10:32.747666	2025-06-03 06:58:41.009371	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
26	海灏生物创新港	2025-03-21	channel_follow	channel	qualified	\N	广东省建筑设计研究院有限公司	上海瀚网智能科技有限公司	\N	广东宏景科技股份有限公司	signed	2025/4/23 17:01:36 周裔锦\r\n\r【完善价格】 122873\r\n\r2025/4/23 16:59:58 周裔锦\r\n\r申请项目批价\r\n\r2025/4/23 13:58:05 周裔锦\r\n\r申请项目批价\r\n\r2025/4/23 13:51:41 周裔锦\r\n\r【完善价格】 30517\r\n\r2025/4/23 13:43:46 周裔锦\r\n\r申请项目批价\r\n\r2025/4/23 13:28:27 周裔锦\r\n\r【完善价格】 26277\r\n\r2025/4/17 周裔锦\r\n\r「张经理」 广东宏景科技股份有限公司  张经理给出指导价格，我方配合做了调整。代理商已经提交企业资料，对方审核没有问题，下周可以签合同。\r\n其余的项目暂时都没有进展。\r\n\r2025/4/11 09:03:07 李冬\r\n\r【授权编号】：添加   HY-CPJ202503-013\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/11 09:02:10 李冬\r\n\r【系统集成商】：改变成   广东宏景科技股份有限公司\r\r\n\r\n\r2025/4/10 16:31:20 李冬\r\n\r【当前阶段情况说明】：改变成   配合集成商中标，跟进项目情况.\r\r\n\r\n\r2025/4/10 16:27:50 李冬\r\n\r【完善价格】 120979\r\n\r2025/4/10 16:24:02 李冬\r\n\r【品牌情况】：添加   入围\r\r\n【当前阶段】：添加   中标\r\r\n【分销商】：添加   上海瑞康\r\r\n【经销商】：添加   上海瀚网智能科技有限公司\r\r\n【系统集成商】：添加   广州宏景房地产开发有限公司\r\r\n【当前阶段情况说明】：添加   配合集成商中标，跟进项目情况\r\r\n\r\n\r2025/3/26 19:49:59 周裔锦\r\n\r【完善价格】 118633\r\n\r2025/3/24 10:50:00 周裔锦\r\n\r【出货时间预测】：改变成   2025年二季度4月份\r\r\n\r\n\r2025/3/21 13:45:13 周裔锦\r\n\r【当前阶段】：添加   中标\r\r\n【授权编号】：添加   HY-CPJ202503-013\r\r\n【当前阶段情况说明】：添加   宏景已经中标，目前跟技术已经确认了参数，采购确认品牌没有问题就给业主报审，最快本月底签采购合同。\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202503-013	2025-04-23	55292.84999999999	\N	\N	2025-03-21 00:00:00	2025-06-03 02:29:35.24278	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
606	温江健康医疗创新中心A区项目 	2025-06-04	channel_follow	channel	qualified			福淳智能科技(四川)有限公司			pre_tender	此项目EPC项目，邹娟在配合总包报价	CPJ202506-007	\N	198556	\N	\N	2025-06-03 10:08:17.185982	2025-06-04 07:28:46.356301	13	f	\N	\N	\N	t	2025-06-03 10:08:17.185982	\N	13	1
71	太保家园成都国际颐养社区项目	2024-08-22	channel_follow	channel	qualified	\N	\N	成都市天皓科技有限公司	\N	\N	signed	2025/4/14 14:16:31 郭小会\r\n\r申请项目批价\r\n\r2025/4/14 14:11:17 郭小会\r\n\r【完善价格】 69706\r\n\r2025/4/11 14:56:21 郭小会\r\n\r【完善价格】 159320\r\n\r2025/3/8 10:04:04 郭小会\r\n\r【出货时间预测】：改变成   2025年二季度\r\r\n\r\n\r2024/9/27 郭小会\r\n\r【阶段变更】招标中->中标\r\r\n\r\n\r2024/8/22 12:15:13 郭小会\r\n\r【消息】「」成都天皓科技报备，协调淳泊进行配合，分布产品和源品牌入围，现在推动天皓科技说服总包采用全和源产品，提供相关产品资料\r\n\r	CPJ202408-010	2025-04-14	42037.200000000004	\N	\N	2024-08-22 00:00:00	2025-06-03 10:45:06.212106	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
153	金桥南区WH4A-1金谷通用厂房项目实验室专业分包工程7#8#楼	2025-03-17	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	中电科数字技术股份有限公司	quoted	2025/3/17 15:34:35 李华伟\r\n\r\n【当前阶段】：添加   招标中\r\n\r\n【授权编号】：添加   HY-CPJ202503-005\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n	CPJ202503-005	2025-06-17	203117	\N	\N	2025-03-17 00:00:00	2025-06-06 01:51:21.807641	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
523	学院路科技园东升园（G地块）项目	2025-04-28	channel_follow	sales	qualified		清华大学建筑设计研究院有限公司	北京佰沃信通科技有限公司		北京安维创时科技有限公司	quoted	集成商已中标	CPJ202504-040	2025-06-20	117402	yes	申请备注: 同一项目，不同标段	2025-05-16 03:50:47.641049	2025-06-09 13:35:11.85814	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
608	同济大学四平路校区南区新建宿舍楼项目	2025-06-04	channel_follow	channel				上海瀚网智能科技有限公司			discover	项目品牌植入工作推进中	CPJ202506-004	\N	0	\N	\N	2025-06-04 01:07:43.015848	2025-06-04 01:07:43.023003	19	f	\N	\N	\N	t	2025-06-04 01:07:43.015848	\N	19	\N
604	海南省海岛中国丝绸文化创意园项目	2025-06-02	channel_follow	sales	unqualified		AECOM（深圳）	上海瀚网智能科技有限公司			discover		\N	\N	0	\N	\N	2025-06-02 14:27:27.028735	2025-06-02 23:17:26.64827	17	f	\N	\N	\N	t	2025-06-02 14:27:27.028735	\N	17	\N
607	长沙黄花机场B1管廊增补	2025-06-03	sales_focus	sales	qualified		民航机场成都电子工程设计有限责任公司			四川中科航建信息技术有限公司	awarded	中标阶段，管廊信号增补	SPJ202506-002	\N	140071	\N	\N	2025-06-03 10:52:53.686274	2025-06-03 10:56:47.167865	13	f	\N	\N	\N	t	2025-06-03 10:52:53.686274	\N	13	2
609	雄安国贸中心（D03-04-41/42/43/44号地块）项目--43#楼精装修工程及弱电智能化工程	2025-06-09	channel_follow	sales	qualified		北京博易基业工程顾问有限公司	上海淳泊信息科技有限公司		江苏方德信息技术有限公司	quoted	前期已通过顾问公司植入品牌，目前配合北京集成商参与投标。	CPJ202506-013	2025-06-27	62376	\N	\N	2025-06-04 01:23:39.966742	2025-06-09 01:04:51.92158	16	f	\N	\N	\N	t	2025-06-04 01:23:39.966742	\N	16	2
593	中国电气装备集团总部园区	2025-06-04	channel_follow	sales	qualified		同济大学建筑设计研究院（集团）有限公司	上海淳泊信息科技有限公司			embed	配套同济院施国平前期方案植入，项目具体情况及细节还需进一步沟通了解	CPJ202506-006	\N	1140022	\N	\N	2025-05-21 05:43:23.808855	2025-06-04 01:33:30.650511	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
595	深圳市第三儿童医院项目	2025-05-22	channel_follow	channel	not_required		筑博设计集团股份有限公司	上海瀚网智能科技有限公司		浙江洲之宇建设有限公司	awarded	当前已确认分包系统集成商	\N	\N	0	\N	\N	2025-05-22 07:32:16.292281	2025-06-02 23:27:12.970968	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
165	深圳歌剧院项目	2024-11-10	sales_focus	sales	qualified	\N	\N	上海瀚网智能科技有限公司	\N	中建科工集团有限公司	awarded	2025/2/28 16:53:25 周裔锦\r\n\r【当前阶段】：改变成   中标\r\r\n\r\n\r2025/2/28 16:53:13 周裔锦\r\n\r【经销商】：添加   上海瀚网智能科技有限公司\r\r\n【系统集成商】：添加   中建科工集团有限公司\r\r\n【当前阶段情况说明】：添加   中建科工已中总包。项目尚在挖基坑。\r\r\n\r\n\r2024/11/19 11:27:56 周裔锦\r\n\r【完善价格】 1413480\r\n\r	SPJ202411-009	2025-02-28	1413196	\N	\N	2024-11-10 00:00:00	2025-06-02 23:36:34.252729	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
562	复旦大学附属中山医院国家医学中心青浦新城院区一期	2025-02-08	channel_follow	channel	qualified			上海福玛通信信息科技有限公司		中电科数字技术股份有限公司	awarded	前期配合集成商设计方案品牌植入，目前中电科中标预计11月份左右进场，配合深化。	CPJ202501-012	2025-12-29	277966	yes	\N	2025-05-16 07:21:08.418723	2025-05-16 08:26:18.905066	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
534	国电四川公司本部事务服务中心2025年生产运营综合楼	2025-04-28	channel_follow	channel	qualified			成都市天皓科技有限公司			pre_tender	代理商配合客户前期规划	CPJ202504-033	2025-05-16	264299	yes	\N	2025-05-16 05:15:18.001679	2025-05-16 05:18:40.547434	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
568	京东2025-京东集团总部7号园区二期弱电工程	2025-05-28	channel_follow	channel	qualified			国隆信达通信技术有限公司			tendering	配合集成商投标	CPJ202504-041	2025-05-16	225718	yes	\N	2025-05-16 08:48:26.395677	2025-05-28 08:42:08.48587	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
599	深圳市星河智善科技有限公司集采-东湾复建	2025-05-29	channel_follow	channel	qualified			上海瀚网智能科技有限公司		深圳市星河智善科技有限公司	signed		\N	2025-05-30	91914.35	\N	\N	2025-05-29 07:03:15.378341	2025-06-03 02:51:00.385981	17	f	\N	\N	\N	t	2025-05-29 07:03:15.378341	\N	17	2
516	宁波中心丽思卡尔顿酒店	2025-05-16	channel_follow	sales	controlled		沈麦韦(上海)商务咨询有限公司	上海福玛通信信息科技有限公司		上海博电诺恒数码科技有限公司	pre_tender	该项目沈麦韦负责智能化顾问，目前招标设计方案基本确认，品牌通过沈麦韦推动，经沟通了解大概率集成商中标单位仍旧是上安九分，但项目后续可能会分包给予博电科技，目前博电科技已经提前发起询价复核成本	CPJ202502-001	2026-03-01	290569	yes	申请备注: 该项目沈麦韦负责智能化顾问，目前招标设计方案基本确认，品牌通过沈麦韦推动，经沟通了解大概率集成商中标单位仍旧是上安九分，但项目后续可能会分包给予博电科技，目前博电科技已经提前发起询价复核成本	2025-05-16 02:34:03.55754	2025-05-16 02:49:04.583177	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
25	河套深港科技创新合作区东翼-1项目	2025-01-10	channel_follow	sales	unqualified	\N	香港华艺设计顾问（深圳）有限公司	上海瀚网智能科技有限公司	\N	深圳市金证科技股份有限公司	awarded	2025/4/24 周裔锦\r\n\r\n「徐道锦」 深圳达实智能股份有限公司  东翼-1项目已经配合售前过配置清单，目前有：达实、金证、智宇、英飞拓、万安、北电正光已询价。\r\n本项目有可能最后采取抽签形式，暂时没有办法准确评估哪一家比较稳妥中标。\r\n\r\n2025/4/11 14:29:18 周裔锦\r\n\r\n【系统集成商】：添加   深圳达实智能股份有限公司\r\n\r\n【当前阶段情况说明】：添加   公建项目，没有品牌要求，26号开标。当前需要找到参与集成商配合投标。\r\n\r\n\r\n\r\n2025/4/7 10:47:11 周裔锦\r\n\r\n【完善价格】 455261\r\n\r\n2025/2/25 16:24:26 李冬\r\n\r\n【授权编号】：添加   HY-CPJ202501-007\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n2025/1/10 17:03:00 周裔锦\r\n\r\n【授权编号】：添加   HY-CPJ202501-007\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n2025/1/3 周裔锦\r\n\r\n类型改变为 \r\n\r\n	CPJ202501-007	2025-04-24	455261	\N	\N	2025-01-10 00:00:00	2025-06-08 21:56:43.152774	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
610	三亚保利悦雅酒店智能化项目	2025-06-04	channel_follow	sales	qualified			北京联航迅达通信技术有限公司		中建三局智能技术有限公司	embed	配合集成商配置‘方案与清单预算’	CPJ202506-008	\N	72133	\N	\N	2025-06-04 01:45:01.249308	2025-06-09 05:37:29.770156	16	f	\N	\N	\N	t	2025-06-04 01:45:01.249308	\N	16	1
572	中交集团南京公司总部办公楼项目	2024-12-21	channel_follow	sales	qualified			敦力(南京)科技有限公司			embed		CPJ202412-009	2025-07-22	70888	yes	\N	2025-05-16 09:03:09.543868	2025-05-28 06:35:48.964502	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
533	正佳食品新都生产基地项目	2024-08-13	channel_follow	channel				福淳智能科技(四川)有限公司			embed	代理商配合集成商进行前期设计	CPJ202408-008	2025-05-16	0	yes	\N	2025-05-16 04:55:58.125297	2025-05-16 05:12:42.966389	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	\N
524	张江创新药基地A04C-01地块	2025-05-16	channel_follow	channel	controlled	上海张江国信安地产有限公司		上海瀚网智能科技有限公司		上海九谷科技发展有限公司	awarded	该项目通过张江国信安植入招标品牌，通过用户了解九谷中标，原先九谷内部销售李华伟负责，投标时有找到李华伟及代理商瀚网在配套，但项目进度还早，智能化提前招标，目前地基才刚挖	CPJ202410-005	2026-06-30	111360	yes	\N	2025-05-16 03:54:31.608326	2025-05-16 04:01:31.211322	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
579	鹏峰项目弱电智能化工程	2025-05-18	channel_follow	channel	qualified			上海瀚网智能科技有限公司		深圳达实智能股份有限公司	awarded		CPJ202408-016	\N	0	yes	\N	2025-05-18 12:43:09.792232	2025-05-22 07:38:48.000945	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
544	上海塘桥04-01地块	2023-02-27	channel_follow	channel	qualified			上海福玛通信信息科技有限公司		上海行余信息技术有限公司	awarded	品牌入围，配合行余中标，代理商在配合深化，预计下半年进场。	CPJ202302-002	2025-11-29	266458	yes	\N	2025-05-16 06:17:29.510174	2025-05-16 09:23:53.400227	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
525	张江创新药基地 A04B-02 地块	2025-05-16	channel_follow	sales	controlled	上海张江国信安地产有限公司					awarded	该项目应该与张江创新药基地A04C-01地块同时期招标，因超哥负责，仅了解到张江创新药基地A04C-01地块九谷中标，计划跟进了解中标单位信息	CPJ202410-001	2025-05-16	107952	yes	\N	2025-05-16 04:03:23.695086	2025-05-16 04:07:45.412741	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
527	长三角一体化温州理工学院乐清产学研基地一期	2025-04-27	channel_follow	channel	qualified		浙江省建筑设计院	浙江航博智能工程有限公司			tendering	前期配合设计院植入品牌，目前已经招标代理商航博配合集成商投标。	CPJ202504-039	\N	187171	yes	\N	2025-05-16 04:09:56.527696	2025-05-16 09:59:31.26324	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
574	中铁十一局汉阳总部智能化项目	2025-05-18	channel_follow	channel	qualified			上海瀚网智能科技有限公司		广东宏景科技股份有限公司	tendering		CPJ202503-029	\N	0	yes	\N	2025-05-18 12:35:51.827845	2025-05-22 07:39:44.433335	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
537	张江人工智能岛二期	2023-11-13	channel_follow	channel	qualified			上海瑞康通信科技有限公司		上海壹杰信息技术有限公司	awarded	品牌前期植入，目前客户中标，预计11月份左右进场。	CPJ202311-002	2025-12-31	360422	yes	\N	2025-05-16 05:30:01.096714	2025-06-03 02:09:39.193739	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
539	徐汇区华泾镇 XHPO-0001单元D5B-1地块	2024-06-21	channel_follow	channel	qualified			上海福玛通信信息科技有限公司		上海凯通实业有限公司	awarded	前期品牌柏诚植入，目前凯通中标还没进场，预计下半年进场。	CPJ202406-013	2025-12-31	234896	yes	\N	2025-05-16 05:41:34.473518	2025-06-03 02:10:01.905914	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
530	张江中区单元41-12地块水泥厂	2024-12-04	channel_follow	channel	qualified			上海瑞康通信科技有限公司		上海源和智能科技股份有限公司	awarded	品牌代理商配合植入，目前客户中标，预计12月左右进场。	CPJ202404-004	2025-12-30	308049	yes	\N	2025-05-16 04:21:23.452089	2025-06-03 02:16:06.76753	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
526	浙江绍兴银行大厦	2024-07-05	channel_follow	channel	qualified		浙江省建筑设计院	浙江航博智能工程有限公司			embed	配合设计院植入品牌，目前品牌植入完成预计25年7月份左右招标。	CPJ202407-003	\N	223660	yes	\N	2025-05-16 04:03:55.41774	2025-06-03 02:16:26.935972	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
522	浙江省智能船舶创新中心	2025-05-16	channel_follow	channel	qualified		浙江省建筑设计院	浙江航博智能工程有限公司			embed	配合设计院设计方案，品牌入围。	CPJ202502-003	\N	95454	yes	\N	2025-05-16 03:49:18.856844	2025-06-03 02:16:49.095194	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
541	温州鹿城广场	2024-11-21	sales_focus	sales	qualified		上海德恳设计咨询顾问有限公司	浙江航博智能工程有限公司			embed	配合顾问设计植入方案，目前公寓和商业已经完成设计，预计下半年招标。业主接触下来品牌愿意帮忙把控。	CPJ202411-006	\N	615260	yes	\N	2025-05-16 05:48:47.231221	2025-06-03 02:17:18.430861	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
548	浦东医院临港院区	2023-12-01	channel_follow	channel	qualified			上海瑞康通信科技有限公司		上海天跃科技股份有限公司	awarded	前期代理商瑞康植入品牌，配合的客户中标，预计年底左右进场。	CPJ202312-001	2026-01-16	376069	yes	\N	2025-05-16 06:34:37.671193	2025-06-03 02:17:49.433218	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
550	青浦市民中心	2024-06-21	channel_follow	channel	qualified		悉地国际设计顾问(深圳)有限公司上海分公司	上海瑞康通信科技有限公司			pre_tender	代理商瑞康发现机会，共同推进配合方案品牌植入。预计年底左右招标。	CPJ202406-012	\N	276892	yes	\N	2025-05-16 06:37:49.12208	2025-06-03 02:18:51.487906	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
613	乐山机场新建项目	2025-06-07	channel_follow	channel	qualified		民航机场建设集团西南设计研究院有限公司	福淳智能科技(四川)有限公司		北京中电力泰科有限公司	pre_tender	福淳在跟进民航西南院 ，项目是EPC，西南院介绍总包，邹娟已联系上总包，进行配合	CPJ202506-011	\N	0	\N	\N	2025-06-05 06:35:45.456811	2025-06-11 15:53:07.627131	13	f	\N	\N	\N	t	2025-06-05 06:35:45.456811	\N	13	\N
612	剑门关蜀道大酒店项目	2025-06-07	channel_follow	channel	qualified		四川省建筑设计研究院有限公司	成都市天皓科技有限公司			pre_tender	项目EPC，福淳在跟进设计院 ，有总包前期询价到成都天浩	CPJ202506-010	\N	182317	\N	\N	2025-06-05 06:10:29.316785	2025-06-07 06:29:19.285128	13	f	\N	\N	\N	t	2025-06-05 06:10:29.316785	\N	13	1
611	柬埔寨国际会议中心城市综合体项目（EPC）	2025-06-05	sales_focus	channel	qualified			敦力(南京)科技有限公司		南京天溯自动化控制系统有限公司	embed	配合集成商进行方案投标	SPJ202506-003	\N	8814755.6	\N	\N	2025-06-04 02:07:17.861995	2025-06-12 11:42:32.38118	16	f	\N	\N	\N	t	2025-06-04 02:07:17.861995	\N	16	1
614	广船国际8600车大型汽车运输船	2025-06-05	channel_follow	sales	not_required			上海瀚网智能科技有限公司		广州希耐特船舶科技有限公司	pre_tender	前期设计 	CPJ202506-009	\N	0	\N	\N	2025-06-05 06:59:03.680215	2025-06-05 15:15:44.177731	13	f	\N	\N	\N	t	2025-06-05 06:59:03.680215	\N	13	\N
2	太原武宿国际机场三期停车楼项目	2025-03-04	sales_focus	marketing	qualified	\N	\N	\N	\N	山西云时代技术有限公司	awarded	2025/4/26 郭小会\r\n\r「王文」 山西云时代技术有限公司  针对新提供的招标文件，调整好清单报价给到王文，待其确认。项目是采用800M定制化产品，和赵沟通好产品需求，初步对产品成本进行评估报价，待客户明确回复采用我司产品后，再进行定制化处理\r\n\r2025/3/4 13:27:56 郭小会\r\n\r【完善价格】 124171\r\n\r2025/3/4 13:25:05 郭小会\r\n\r【系统集成商】：添加   山西云时代技术有限公司\r\r\n【授权编号】：添加   HY-SPJ202503-001\r\r\n【类型】：添加   销售重点\r\r\n\r\n\r	SPJ202503-001	2025-04-26	241671	\N	\N	2025-03-04 00:00:00	2025-06-05 14:20:06.511405	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
615	马来西亚及印尼业务	2025-06-07	channel_follow	channel	qualified			上海福玛通信信息科技有限公司			quoted	该项目与付言新沟通了解马来西亚项目NTP-DE、印尼巴淡岛万国数据中心ABC楼业务与客户签单，可以发起批价确认	CPJ202506-012	\N	95630.85	\N	\N	2025-06-06 02:35:29.438424	2025-06-12 04:27:22.440595	14	f	\N	\N	\N	t	2025-06-06 02:35:29.438424	\N	14	2
78	滴水湖地铁站	2025-03-29	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海电科智能系统股份有限公司	awarded	2025/4/13 15:38:57 杨俊杰\r\n\r\n【完善价格】 101134\r\n\r\n2025/3/29 12:53:17 杨俊杰\r\n\r\n【出货时间预测】：添加   2025年二季度\r\n\r\n【当前阶段】：改变成   中标\r\n\r\n【分销商】：添加   上海淳泊\r\n\r\n【授权编号】：添加   HY-CPJ202503-015\r\n\r\n【当前阶段情况说明】：改变成   该项目电科智能中标，已经进场，在等待与总包合同，商务预计5月份启动\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n	CPJ202503-015	2025-07-10	74474	\N	\N	2025-03-29 00:00:00	2025-06-06 10:28:32.067505	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
88	黄浦区广场社区C010102单元064-01、065-01地块「嘉里金陵东路」	2025-01-11	channel_follow	channel	qualified	\N	科进柏城咨询有限公司-上海分公司	上海瀚网智能科技有限公司	\N	上海永天科技股份有限公司	awarded	2025/4/13 14:57:00 杨俊杰\r\n\r【当前阶段】：改变成   中标\r\n\r【分销商】：添加   上海瑞康\r\n\r【经销商】：改变成   上海瀚网智能科技有限公司\r\n\r【系统集成商】：改变成   上海永天科技股份有限公司\r\n\r【当前阶段情况说明】：改变成   该项目经了解上海永天中标，目前采购在询价，瀚网张国东在跟进。初步了解通过系统品牌，主要与烈龙在竞争，而永天原先主要合作对象是徐小青，项目方案上没有好的手段，只能通过低价竞争\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r2025/1/11 15:53:52 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202410-009\r\n\r\r\n\r2025/1/8 12:12:28 杨俊杰\r\n\r【完善价格】 699054\r\n\r2025/1/8 11:48:50 杨俊杰\r\n\r【经销商】：添加   上海福玛通信信息科技有限公司\r\n\r【系统集成商】：添加   上海申源电子工程技术设备有限公司\r\n\r【当前阶段情况说明】：添加   该项目渠道福玛陈刘祥报备，配合申源电子参与项目投标。项目入围，主要与烈龙竞争\r\n\r\r\n\r2024/12/27 杨俊杰\r\n\r【阶段变更】招标中->失败\r\n\r\r\n\r2024/12/2 杨俊杰\r\n\r【阶段变更】->招标中\r\n\r类型改变为渠道跟进 \r\n\r2024/12/2 杨俊杰\r\n\r【阶段变更】品牌植入->\r\n\r类型改变为 \r\n\r2024/10/18 10:08:04 杨俊杰\r\n\r【完善价格】 42304\r\n\r2024/4/7 杨俊杰\r\n\r该项目配合柏诚吴恺翔参与招标图设计，项目分为多个地块，本次先启动64和65两个地块，每个地块分为商办和住宅2个业态，有独立运维团队。需要了解设计阶段，邀约业主，推进业务合作，了解招标时间及参与集成商情况\r\n\r	CPJ202410-009	2025-04-13	699054	\N	\N	2025-01-11 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
133	华兴新城项目8-01地块	2024-06-20	channel_follow	channel	controlled	\N	\N	上海艾亿智能科技有限公司	\N	上海银欣高新技术发展股份有限公司	awarded	2025/3/29 13:00:23 杨俊杰\r\n\r\n【出货时间预测】：改变成   2025年四季度\r\n\r\n\r\n\r\n2025/2/21 17:12:25 杨俊杰\r\n\r\n【完善价格】 450368\r\n\r\n2025/2/21 15:16:34 杨俊杰\r\n\r\n【出货时间预测】：改变成   2025年二季度\r\n\r\n\r\n\r\n2024/9/20 杨俊杰\r\n\r\n【阶段变更】招标中->中标\r\n\r\n\r\n\r\n2024/6/20 14:02:54 杨俊杰\r\n\r\n【消息】「」该项目梅小好作为合作伙伴，与业主建立合作，植入招标品牌。奥雅纳作为机电顾问，智能化设计由江森负责，项目招标，品牌入围，经合作伙伴梅小好反馈项目预计有6-7家报名参与,目前已配合两家在参与项目投标\r\n\r\n	CPJ202406-009	2025-07-10	450368	\N	\N	2024-06-20 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
31	长沙橘州诺雅酒店项目	2025-03-21	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳市旗云智能科技有限公司	quoted	2025/4/23 周裔锦\r\n\r\n「张坤成」 深圳市旗云智能科技有限公司  张总说我们需要跟瑞斯通比价，竞品（科立讯、海能达、瑞斯通）希望我们尽力配合价格。\r\n当前已经报了一版常规价格给采购，接下来还要找张总争取议价机会。\r\n\r\n2025/4/11 09:03:40 李冬\r\n\r\n【授权编号】：添加   HY-CPJ202503-014\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n2025/4/10 16:49:37 李冬\r\n\r\n【完善价格】 75632\r\n\r\n2025/3/21 13:46:54 周裔锦\r\n\r\n【当前阶段】：添加   中标\r\n\r\n【授权编号】：添加   HY-CPJ202503-014\r\n\r\n【当前阶段情况说明】：添加   集成商已经中标，目前长沙当地的技术负责深化，张坤成让我们和技术紧密配合\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n	CPJ202503-014	2025-06-01	67375	\N	\N	2025-03-21 00:00:00	2025-06-08 22:31:00.567376	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
183	虹桥天合光能总部	2024-01-15	sales_focus	sales	qualified	天合光能股份有限公司	华东建筑设计研究院有限公司	\N	\N	\N	embed	2025/2/21 17:07:22 杨俊杰\r\n\r【完善价格】 587550\r\n\r2024/12/27 杨俊杰\r\n\r类型改变为销售重点 \r\n\r2024/7/4 14:33:20 杨俊杰\r\n\r【消息】「」该项目配合华东院周天文设计，计划植入全系列和源产品。招标文件及品牌预计9-10月份启动\r\r\n【阶段变更】发现->品牌植入\r\n\r2024/3/20 16:18:00 杨俊杰\r\n\r该项目华东院周天文负责智能化专项，项目整体为12万方，分为六栋建筑，与虹桥希尔顿为同一个业主负责。目前再平台搭建，项目预计6月份启动招标图设计。需要跟进推动设计配套，推动消防系统、平台服务方案和全系列品牌入围\r\n\r2024/3/20 16:15:29 杨俊杰\r\n\r「阶段变更」\r\n\r2023/11/1 杨俊杰\r\n\r该项目与华东院周天文沟通了解现在还在方案汇报，预计春节后启动图纸设计，此项目与虹桥希尔顿的业主为同一个\r\n\r	SPJ202401-002	2025-02-21	587550	\N	\N	2024-01-15 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
102	张江创新药基地B03C-02&B03K-03	2024-01-29	channel_follow	sales	controlled	上海张江国信安地产有限公司	\N	上海福玛通信信息科技有限公司	\N	上海派汇网络科技有限公司	awarded	2025/4/10 13:59:46 杨俊杰\r\n\r\n【出货时间预测】：改变成   2025年三季度\r\n\r\n【直接用户】：改变成   庄彦「上海张江国信安地产有限公司」\r\n\r\n【当前阶段情况说明】：改变成   经沟通了解，集成商派汇与总包仪电有关智能化合同还在签订，目前他们还没进场实施，待进场后也是先启动管线桥架预埋工作，但项目按照用户交付计划在今年底要完成，所以预计今年三季度会启动设备采购\r\n\r\n\r\n\r\n2025/4/10 杨俊杰\r\n\r\n「范佳顺」 上海派汇网络科技有限公司  经沟通了解，集成商派汇与总包仪电有关智能化合同还在签订，目前他们还没进场实施，待进场后也是先启动管线桥架预埋工作，但项目按照用户交付计划在今年底要完成，所以预计今年三季度会启动设备采购\r\n\r\n2025/3/19 16:30:41 李冬\r\n\r\n【出货时间预测】：改变成   上海张江国信安地产有限公司「2025年二季度」\r\n\r\n【当前阶段】：改变成   转移\r\n\r\n【当前阶段情况说明】：添加   项目转移到其他代理商\r\n\r\n\r\n\r\n2025/2/25 11:05:49 杨俊杰\r\n\r\n【直接用户】：改变成   庄彦「上海张江国信安地产有限公司」\r\n\r\n\r\n\r\n2025/2/21 13:09:23 杨俊杰\r\n\r\n【分销商】：改变成   上海淳泊\r\n\r\n【经销商】：改变成   陈刘祥「上海福玛通信信息科技有限公司」\r\n\r\n【直接用户】：改变成   庄彦「上海张江国信安地产有限公司」\r\n\r\n【当前阶段情况说明】：改变成   复核项目中标情况。通过渠道与派汇网络负责人范佳顺沟通了解，张江创新药基地分为B03C-02和B03K-03两个地块。他们跟踪的是B03K-03，另一个B03C-02是益邦中标。其中B03K-03实际中标单位为仪电鑫森，现阶段他们在与仪电鑫森洽谈智能化分包商务合同。项目现场实施计划今年3，4月份做管线预埋，无线对讲系统天馈实施最快也要到5月份。现阶段计划复核深化方案，确认实施清单，跟踪渠道推进项目采购进度\r\n\r\n\r\n\r\n2025/2/17 14:42:59 杨俊杰\r\n\r\n【直接用户】：改变成   庄彦「上海张江国信安地产有限公司」\r\n\r\n【当前阶段情况说明】：添加   该项目分为两个地块，张江创新药基B03K-03中标单位上海仪电，智能化分包负责派汇网络。现阶段福玛在跟进。目前仅了解到项目今年会启动，但具体时间还需要确认。只能询价复核项目实施方案，确认项目采购清单，推进洽谈商务价格\r\n\r\n\r\n\r\n45653 李冬\r\n\r\n【阶段变更】招投标->中标\r\n\r\n\r\n\r\n2024/12/27 杨俊杰\r\n\r\n【阶段变更】招投标->中标\r\n\r\n\r\n\r\n45371.6763425926 李冬\r\n\r\n近期跟进通过渠道了解投标结果\r\n\r\n2024/3/20 16:13:56 杨俊杰\r\n\r\n近期跟进通过渠道了解投标结果\r\n\r\n45342.6328935185 李冬\r\n\r\n经销商改变为   上海瀚网智能科技有限公司 用户改变为   上海张江国信安地产有限公司    \r\n\r\n配合戴卓莹与孙明显招标设计，与戴卓莹沟通了解甲方直接大总包招标，弱电基本内定益邦，挂靠在大总包下面。益邦贾雪凤询价，提供清单报价\r\n\r\n2024/2/20 15:11:22 杨俊杰\r\n\r\n经销商改变为   上海瀚网智能科技有限公司 用户改变为   上海张江国信安地产有限公司    \r\n\r\n配合戴卓莹与孙明显招标设计，与戴卓莹沟通了解甲方直接大总包招标，弱电基本内定益邦，挂靠在大总包下面。益邦贾雪凤询价，提供清单报价\r\n\r\n45342.6287268518 李冬\r\n\r\n集成商改变为  上海益邦智能技术股份有限公司    \r\n\r\n2024/2/20 15:05:22 杨俊杰\r\n\r\n集成商改变为  上海益邦智能技术股份有限公司    \r\n\r\n45342.6247800926 李冬\r\n\r\n设计方改变为      \r\n\r\n2024/2/20 14:59:41 杨俊杰\r\n\r\n设计方改变为      \r\n\r\n45342.6222337963 李冬\r\n\r\n围标状况改变为   围标 分销商改编为   上海瑞康 类型改变为  渠道管理    \r\n\r\n2024/2/20 14:56:01 杨俊杰\r\n\r\n围标状况改变为   围标 分销商改编为   上海瑞康 类型改变为  渠道管理    \r\n\r\n45231 李冬\r\n\r\n该项目瀚网报备，经了解集成商上海益邦询价，品牌和源入围\r\n\r\n2023/11/1 杨俊杰\r\n\r\n该项目瀚网报备，经了解集成商上海益邦询价，品牌和源入围\r\n\r\n	CPJ202401-011	2025-08-10	207732	\N	\N	2024-01-29 00:00:00	2025-06-09 15:07:55.809001	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
34	西安咸阳机场南北过夜楼	2025-04-08	channel_follow	sales	qualified	\N	\N	\N	\N	西安悦泰科技有限责任公司	pre_tender	2025/4/21 23:39:36 郭小会\r\n\r【完善价格】 253534\r\n\r2025/4/8 14:34:36 郭小会\r\n\r【授权编号】：添加   HY-CPJ202504-008\r\r\n\r\n\r2025/4/8 13:54:23 郭小会\r\n\r提交报备\r\n\r2025/4/5 11:52:39 郭小会\r\n\r【完善价格】 236742\r\n\r2025/4/5 11:19:23 郭小会\r\n\r【系统集成商】：添加   西安悦泰科技有限责任公司\r\r\n\r\n\r2025/4/5 郭小会\r\n\r「张晓龙」 西安悦泰科技有限责任公司  项目已完成设计，北京顾问放在天馈品牌，悦泰前期参与询价，拜访悦泰采购经理，介绍公司的情况和产品优势，了解项目具体情况\r\n\r	CPJ202504-008	2025-04-21	253534	\N	\N	2025-04-08 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
531	学院路科技园东升园（I地块）项目	2025-06-12	channel_follow	sales	qualified		清华大学建筑设计研究院有限公司	北京佰沃信通科技有限公司		清华同方股份有限公司同方智慧建筑与园区公司	quoted	集成商已中标，代理商已对接	CPJ202506-017	2025-06-16	36198	\N	\N	2025-05-16 04:33:26.683483	2025-06-12 04:00:18.72728	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
617	广州天河珠江新城地块项目	2025-06-08	channel_follow	sales	not_required			上海瀚网智能科技有限公司		深圳英飞拓科技股份有限公司	awarded		\N	\N	0	\N	\N	2025-06-08 13:43:01.101387	2025-06-08 13:49:59.213978	17	f	\N	\N	\N	t	2025-06-08 13:43:01.101387	\N	17	1
404	华南区域危险废物环境风险防控技术中心	2025-04-11	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	广东宏景科技股份有限公司	tendering	2025/4/11 09:05:00 李冬\r\n\r【当前阶段情况说明】：改变成   配合集成商投标..\r\r\n\r\n\r2025/4/11 09:04:50 李冬\r\n\r【系统集成商】：改变成   广东宏景科技股份有限公司\r\r\n【授权编号】：添加   HY-CPJ202503-026\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/10 16:56:34 李冬\r\n\r【当前阶段情况说明】：改变成   配合集成商投标.\r\r\n\r\n\r2025/4/10 16:56:12 李冬\r\n\r【完善价格】 102423\r\n\r2025/3/25 21:45:06 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202503-026\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202503-026	2025-04-11	0	\N	\N	2025-04-11 00:00:00	2025-04-11 09:05:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
91	中芯国际（深圳）厂FAB6二层三层CUB地下一层信号增补	2025-04-02	business_opportunity	sales	qualified	中芯国际集成电路制造(深圳)有限公司	\N	\N	\N	\N	discover	2025/4/11 11:12:28 徐昊\r\n\r【完善价格】 74529\r\n\r2025/4/10 徐昊\r\n\r「石维」 中芯国际集成电路制造(深圳)有限公司  与深圳中芯国际ERC负责人沟通改造方案与2025系统维护测试两个方案的最终确认，对方根据方案报价向采购部门正式提出采购申请，预算通过后制作PO单；\r\n\r2025/4/2 13:34:43 徐昊\r\n\r【授权编号】：添加   HY-APJ-202503-012\r\r\n\r\n\r2025/3/28 11:21:29 徐昊\r\n\r【面价金额】：添加   120000\r\r\n\r\n\r2025/3/20 10:21:13 徐昊\r\n\r【当前阶段】：添加   发现\r\r\n\r\n\r	APJ202503-012	2025-04-11	74529	\N	\N	2025-04-02 00:00:00	2025-05-11 00:59:24.476988	7	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	7	1
95	科思创193区域信号增补	2025-04-02	business_opportunity	sales	qualified	科思创聚合物(中国)有限公司	\N	\N	\N	\N	discover	2025/4/11 10:37:00 徐昊\r\n\r【完善价格】 10337\r\n\r2025/4/8 徐昊\r\n\r「吴天杰」 科思创聚合物(中国)有限公司  沟通B193区域的实施方案，业主提出在是否能在B193一楼CCR控制室增加一副天线，复核设计图纸进行确认，方案其他业主已认可；\r\n\r2025/4/3 徐昊\r\n\r「吴天杰」 科思创聚合物(中国)有限公司  设计师已经完成B193区域的信号覆盖的方案和清单，商务在填写好清单价格后发给客户确认；\r\n\r2025/4/2 13:30:31 徐昊\r\n\r【授权编号】：添加   HY-APJ-202502-007\r\r\n\r\n\r2025/2/28 10:47:10 徐昊\r\n\r【当前阶段情况说明】：改变成   193区域茶水间信号较差，通话有断续，在提供茶水间信号增补的方案后，业主方表示由于193未做过室内信号覆盖，以前主要依靠室外信号的延申，所以希望这次能够把该楼宇做室内信号覆盖，已经安排设计师对193楼宇进行室内信号覆盖提供增补方案和清单，然后提交给业主\r\r\n\r\n\r	APJ202502-007	2025-04-11	10337.3	\N	\N	2025-04-02 00:00:00	2025-05-11 00:59:24.476988	7	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	7	1
103	龙阳路04地块	2025-03-13	channel_follow	channel	qualified	\N	奥雅纳工程咨询(上海)有限公司	上海艾亿智能科技有限公司	\N	\N	embed	2025/4/10 13:36:43 杨俊杰\r\n\r【完善价格】 1284277\r\n\r2025/4/10 杨俊杰\r\n\r「梅小好」 上海艾亿智能科技有限公司  与梅小好沟通反馈有集成商挂靠九分资质，通过初步复核品牌的确可控，但参与集成商通过九分关系了解到并没有参考招标品牌，用的是浙江尧起，将次情况让梅小好复核集成商信息，判断用户除了品牌招标在可控范围内以外，是否有能力可以掌控集成商。项目预计二季度招标，潜在参与集成商：信业、中建电子、益邦及万安都有可能参与，待项目正式招标，了解参与集成商具体情况\r\n\r2025/3/13 14:08:22 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202502-018\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r	CPJ202502-018	2025-04-10	1177637	\N	\N	2025-03-13 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
30	北京新首钢园东南区1612-(769)地块项目-调整增补	2025-03-07	sales_focus	sales	qualified	\N	\N	上海淳泊信息科技有限公司	\N	中建电子工程有限公司-北京分公司	signed	2025/4/23 范敬\r\n\r\n「冯子煜」 中建电子工程有限公司-北京分公司  沟通了该地块系统调整问题，经沟通增加了软件平台管理系统；后续需协助进行批价审价。\r\n\r\n2025/3/7 14:27:30 范敬\r\n\r\n【授权编号】：添加   HY-SPJ202502-001\r\n\r\n【类型】：添加   销售重点\r\n\r\n\r\n\r\n	SPJ202502-001	2025-05-30	43743	\N	\N	2025-03-07 00:00:00	2025-06-06 15:19:09.118679	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
180	湖州西凤漾智创湾	2025-02-24	sales_focus	sales	qualified	\N	浙江省建筑设计院	浙江航博智能工程有限公司	\N	\N	embed	2025/2/24 13:27:59 李华伟\r\n\r【授权编号】：改变成   HY-SPJ-202404-007\r\r\n【类型】：改变成   销售重点\r\r\n\r\n\r	SPJ-202404-007	2025-02-24	248547	\N	\N	2025-02-24 00:00:00	2025-06-13 10:52:04.488957	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
43	新皇岗口岸联检大楼	2024-07-19	sales_focus	sales	unqualified	\N	厦门万安智能有限公司深圳分公司	上海瀚网智能科技有限公司	\N	\N	embed	2025/4/21 周裔锦\r\n\r「方奕广」 厦门万安智能有限公司深圳分公司  交流蓝牙信标巡检方案，方经理介绍业主希望打卡能有声音反馈，不然信息不闭环，不知道能不能打上，从而给工作造成不便。\r\n\r2025/4/16 周裔锦\r\n\r「方奕广」 厦门万安智能有限公司深圳分公司  和方经理重新核对招标技术文档，他介绍地下室的摄像头是内置蓝牙的，业主出于成本考虑，也避免重复建设。提到蓝牙巡检能否使用摄像头里的蓝牙信号，以及蓝牙打卡的时候，能否在对讲机上有打上卡的提示音。我们最好出具一份关于蓝牙信标巡检的技术方案。\r\n目前已经让刘威在配合整理。\r\n\r2025/4/10 周裔锦\r\n\r「方奕广」 厦门万安智能有限公司深圳分公司  方总反馈，业主方不同意把软件部分在技术参数里体现出来，所以需要想方法变通一下。调整后的频段以及对讲机含蓝牙功能基本没有问题。\r\n\r2025/4/1 周裔锦\r\n\r「方奕广」 厦门万安智能有限公司深圳分公司  方工介绍，项目调整为5月招标。上周已经把含有我们调整后的初版技术文档提交给代建方，最快节后回来会有结果。\r\n\r2025/2/16 19:44:33 周裔锦\r\n\r【设计院及顾问】：改变成   厦门万安智能有限公司深圳分公司\r\r\n【经销商】：添加   上海瀚网智能科技有限公司\r\r\n\r\n\r	SPJ202407-003	2025-04-21	1677454	\N	\N	2024-07-19 00:00:00	2025-06-08 22:09:44.036719	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
161	大唐三亚总部基地办公楼项目	2025-01-10	channel_follow	sales	unqualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳市万睿智能科技有限公司	pre_tender	2025/3/7 00:04:00 周裔锦\r\n\r【完善价格】 238478\r\n\r45667.703900463 李冬\r\n\r【分销商】：添加   上海瑞康\r\r\n【经销商】：添加   上海瀚网智能科技有限公司\r\r\n【授权编号】：添加   HY-CPJ202501-005\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/1/10 16:53:37 周裔锦\r\n\r【分销商】：添加   上海瑞康\r\r\n【经销商】：添加   上海瀚网智能科技有限公司\r\r\n【授权编号】：添加   HY-CPJ202501-005\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202501-005	2025-03-07	238478	\N	\N	2025-01-10 00:00:00	2025-06-09 01:20:57.780821	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
577	三亚海棠湾免税城三期	2025-05-18	channel_follow	sales	qualified		AECOM（深圳）	上海瀚网智能科技有限公司			tendering	当前顾问公司已经询价，具体招标时间未定。	CPJ202503-004	\N	299045	yes	\N	2025-05-18 12:40:07.308656	2025-06-09 01:21:28.086832	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
549	苏州工业园区桑田科学岛科创中心（DK20230415/20240020地块）项目	2025-06-11	sales_focus	sales	qualified			敦力(南京)科技有限公司		中宏恒大智能科技工程有限公司	awarded	集成商已中标	SPJ202506-005	2025-06-25	162184	\N	申请备注: 同一项目，不同标段	2025-05-16 06:35:22.818216	2025-06-11 01:40:13.958447	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
149	集成电路设计产业园3C-10地块	2024-05-11	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	同方股份有限公司-上海光大会展分公司	awarded	2025/3/24 10:00:55 李华伟\r\n\r【出货时间预测】：改变成   2025年四季度\r\r\n\r\n\r2025/2/17 14:37:16 李华伟\r\n\r【当前阶段情况说明】：添加   据代理商反馈，现场进度预计在8月份左右进场穿线，目前在做桥架。品牌资料报审已经完成。安排代理商7月份左右跟进客户合同谈判确认。\r\r\n\r\n\r45674.4749884259 李冬\r\n\r【完善价格】 348300\r\n\r2025/1/17 11:23:59 李华伟\r\n\r【完善价格】 348300\r\n\r45674.4653587963 李冬\r\n\r【完善价格】 312942\r\n\r2025/1/17 11:10:07 李华伟\r\n\r【完善价格】 312942\r\n\r45429.5617824074 李冬\r\n\r【阶段变更】招标中->中标\r\n\r2024/5/17 13:28:58 李华伟\r\n\r【阶段变更】招标中->中标\r\n\r45423 李冬\r\n\r【拜访】:  代理商配合客户投标，品牌入围。\r\n\r2024/5/11 李华伟\r\n\r【拜访】:  代理商配合客户投标，品牌入围。\r\n\r	CPJ202405-004	2025-03-24	348300	\N	\N	2024-05-11 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
567	南京江北新金融中心二期项目地块弱电智能化工程	2025-06-09	sales_focus	sales				敦力(南京)科技有限公司		南京聚立科技股份有限公司	discover		SPJ202506-004	2025-05-16	0	\N	\N	2025-05-16 07:54:36.807775	2025-05-28 16:38:50.944377	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	\N
111	西安咸阳国际机场三期扩建工程下穿通道项目	2024-06-09	sales_focus	channel	qualified	\N	\N	陕西无线电通信服务中心	\N	\N	signed	2025/4/5 郭小会\r\n\r「张士彦」 陕西无线电通信服务中心  拜访陕西无线电张总，了解西安咸阳机场项目系统试用期的情况，后续安排系统最终联调和软件升级。针对张总他们化工业务的情况进行了深入的沟通和交流，介绍我们行业产品的优势，寻求行业项目的合作。\r\n\r2025/1/3 16:44:50 郭小会\r\n\r【完善价格】 72562\r\n\r2024/8/24 11:05:09 郭小会\r\n\r【消息】「」下穿通道陕西无线电已和对方确定合同意向，设备已向分司下单，并支付了预付款。本周配合陕西无线电提交资料，陕西无线电和总包走个投标流程\r\r\n【阶段变更】中标->签约\r\n\r2024/6/9 郭小会\r\n\r下穿通道中标商原采用的是中原的产品，考虑到将来要接入到我们的系统，陕西无线电张总他们和指挥部及总包在做相应的沟通，要求光纤直入站变更为和源通信产品，目前在直审批变更流程\r\n\r	SPJ202406-001	2025-04-05	72562	\N	\N	2024-06-09 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
16	上海中芯国际干放设备更换	2025-04-25	business_opportunity	\N	qualified	中芯国际集成电路制造(上海)有限公司	\N	\N	\N	\N	pre_tender	2025/4/25 13:21:19 方玲\r\n\r【授权编号】：添加   HY-APJ-202503-016\r\r\n\r\n\r2025/4/25 徐昊\r\n\r「袁邓多」 中芯国际集成电路制造(上海)有限公司  与业主方负责人沟通中芯国际今年常规射频直放站更新事宜，听取业主方想法和意见；\r\n\r2025/4/23 21:45:31 方玲\r\n\r【完善价格】 150000\r\n\r2025/4/3 09:55:21 徐昊\r\n\r【直接用户】：添加   中芯国际集成电路制造(上海)有限公司\r\r\n\r\n\r2025/4/3 09:52:10 徐昊\r\n\r【授权编号】：添加   HY-APJ-202503-016\r\r\n\r\n\r	APJ202503-016	2025-04-25	150000	\N	\N	2025-04-25 00:00:00	2025-06-09 11:39:13.893397	2	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	2	1
3	北京中芯京城二期12英寸芯片生产线厂房建设项目	2025-04-25	sales_focus	sales	qualified	\N	\N	北京联航迅达通信技术有限公司	\N	北京航天星桥科技股份有限公司	embed	2025/4/25 19:07:38 范敬\r\n\r\n【授权编号】：添加   HY-SPJ202504-001\r\n\r\n\r\n\r\n2025/4/24 范敬\r\n\r\n「马经理」 北京航天星桥科技股份有限公司  项目目前正处于前期方案清单配置中，土建已在施工中，预计三季度进行智能化招标，项目计划明年一季度结束。\r\n\r\n2025/4/17 09:28:23 范敬\r\n\r\n提交报备\r\n\r\n	SPJ202504-001	2025-09-25	501609	\N	\N	2025-04-25 00:00:00	2025-06-09 13:39:34.358739	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
32	上海浦东东站	2023-10-17	sales_focus	sales	qualified	\N	华东建筑设计研究院有限公司	上海艾亿智能科技有限公司	\N	上海市安装工程集团有限公司-第九分公司	awarded	该项目与上安九分龚俊瑜就目前清单初步确认最终价格，通过了解上安九分内部也基本确认，有关品牌及供应商提交到项目部，项目实际负责人为蒯乃骏。与蒯乃骏沟通了解现阶段他们与四建安装合同还未签订，现场在与甲方地下部分负责人李继栋汇报智能化各子系统品牌，和源初步确认，进一步计划就是各子系统进行方案汇报，最终先把品牌给予确认，同时沟通过程中了解，无线对讲系统确定地上、地下为同一个品牌，至于航空模块部分因为牵涉机场，所以后续可能还需要待机场相关负责人确认后还需要进行汇报。现场实施确认为明年年中以后，今年至多完成方案深化，确认采购清单。目前所存在的风险即为机房核心设备是否能够保留在上安，因从系统原先规划及招标上核心设备在地上部分，如果这样就可能需要通号明确是否也选用和源品牌，不一定以上安建议为主\r\n2025/4/22 杨俊杰\r\n\r\n「龚俊瑜」 上海市安装工程集团有限公司-第九分公司  拜访龚俊瑜和滕思宇，赠送茶叶慰问客户。跟进浦东东站地下标段业务，目前了解浦东东站地下标段近期上安内部会初步确认系统供应商，按龚总给与价格进行调整，先稳定上安，后续继续跟进了解目前上安这边的情况。同时龚俊瑜告知E2商务区最终价格和邹飞那边已经确认，由于他们合同还没下来，让我们提前配合\r\n\r\n2025/4/18 杨俊杰\r\n\r\n「丁愉豪」 上海市安装工程集团有限公司-第九分公司  拜访丁愉豪，经了解无线对讲中标价格不含税为270万，这个价格是四建安装中标价格，等于智能化分包的话四建安装还要收取管理费。按现在九分内部想法是各系统有关技术要求及价格确认，然后再内部讨论，调整报价后跟进九分龚俊瑜，拜访梁栋之，表示给予支持，稳定九分关系\r\n\r\n2025/4/16 杨俊杰\r\n\r\n「黄辰赟」 华东建筑设计研究院有限公司  拜访黄辰贇，跟进浦东东站地下标段情况。复核上安九分反馈情况，基本一致，待上安提交方案及品牌，尤其品牌方面让其把关。至于用户方面，经了解从申通地铁掉过来李继栋后续负责，但没有联系方式，看是否有需要去提前接触\r\n\r\n2025/4/13 15:24:30 杨俊杰\r\n\r\n【系统集成商】：改变成   上海市安装工程集团有限公司-第九分公司\r\n\r\n\r\n\r\n2025/4/8 杨俊杰\r\n\r\n「梁晓君」 上海市安装工程集团有限公司-第九分公司  浦东东站地下及空铁联运基本确认上安九分负责智能化实施及设备采购，项目现场张东伟负责，与张东伟初步建立沟通，今年他们主要计划是项目整体实施方案深化，与业主确认，具体进场实施要到明年\r\n\r\n2025/2/25 11:21:40 杨俊杰\r\n\r\n【经销商】：添加   上海艾亿智能科技有限公司\r\n\r\n\r\n\r\n2025/2/21 17:15:01 杨俊杰\r\n\r\n【完善价格】 4978015\r\n\r\n2025/2/21 14:03:26 杨俊杰\r\n\r\n【系统集成商】：改变成   上海建工四建集团有限公司\r\n\r\n【当前阶段情况说明】：改变成   浦东东站分为地上、地下分开招标，其中地上部分经了解对讲系统在信息包内，中标单位：通号，由于招标形式按铁路要求，没有品牌限定，现阶段还未找到有关负责人。地下部分中标单位：建工四建安装，品牌为摩托罗拉、中兴高达、和源通信。现阶段计划跟进建工四建安装，找到智能化专业主要负责人，通过技术招标要求，及借用合作伙伴艾亿智能与用户关系，锁定品牌，从而在建立地上部分合作\r\n\r\n\r\n\r\n2025/2/21 13:54:28 杨俊杰\r\n\r\n【当前阶段情况说明】：添加   拜访建工四建安装投标部赵展鹏，经沟通由于年前刚宣布中标结果，原定中铁由于个别资质原因由他们中标，现阶段他们可能与甲方合同还未最终签订，由于他们原先主要以机电业务为主，智能化可能会分包，具体需要与他们经营部负责人沟通了解。同时上安九分询价，经了解他们可能会作为智能化分包，按上安九分反馈目前建工四建给予的无线对讲系统预算和当时我们投标报价对比差了230万，让我们先按清单复核，调整优惠一版价格。计划后续通过赵展鹏引荐，了解项目中标情况。\r\n\r\n\r\n\r\n2024/12/27 杨俊杰\r\n\r\n【阶段变更】招标中->中标\r\n\r\n\r\n\r\n2024/12/6 杨俊杰\r\n\r\n【阶段变更】品牌植入->招标中\r\n\r\n\r\n\r\n2024/5/20 15:30:01 杨俊杰\r\n\r\n【消息】「」与华东院及上安重新复核设计方案，据了解地上、地下部分预算已经批复，且地下施工图已经提交给予用户，除非外部因素，否则设计院不太好再做修改，地上部分预计本月提交确认。目前建设方东方枢纽还未了解到具体负责人，按华东院黄辰赟的意思，东方枢纽先等铁道部确认后可能才会有所动作\r\n\r\n2024/3/20 16:19:02 杨俊杰\r\n\r\n施工图设计初版基本完成，与黄辰赟沟通了解目前没有任何消息。上安在提前询价，进一步跟进了解项目后续情况\r\n\r\n2023/11/1 杨俊杰\r\n\r\n该项目高铁站台内由国铁下属中铁设计院负责，站台外由华东院负责，另外还有个隧道由隧道院负责，目前配合华东院提交初设方案，用于项目预算审批。整个项目地下部分由上海市政府审批预算，地上站台内由北京负责审批预算，10月底11月初地上、地下预算审批确认后就会启动施工图设计，计划要求今年底完成施工图设计。目前业主没有具象负责人，有关品牌方面还需确认由谁发起，由谁确认\r\n\r\n	SPJ202310-001	2026-06-30	4978015	\N	\N	2023-10-17 00:00:00	2025-06-09 13:49:22.930169	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
602	赛车场-FE方程式赛事保障	2025-05-30	business_opportunity	sales	qualified	\t上海久事国际体育中心有限公司					embed	赛事保障：2025.5.30-2025.6.1	\N	\N	7008	\N	\N	2025-05-30 06:18:38.682923	2025-06-09 16:16:25.096014	2	t	授权编号审批锁定: 销售机会授权审批	2	2025-05-30 06:19:06.117764	t	2025-05-30 06:18:38.682923	\N	2	1
33	罗湖妇幼保健院智能化项目	2025-04-11	channel_follow	channel	unqualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳市电信工程有限公司	awarded	2025/4/22 周裔锦\r\n\r\n「林嘉豪」 深圳市电信工程有限公司  林总介绍了负责本项目的项目经理对接，胡经理说他这边已经根据我们给的资料了解过了我们品牌，他们现在一个一个系统在过，暂时还没有过到无线对讲系统，等到了再通知我们参与线上竞价。\r\n项目经理在本环节占有选择权，需要进一步做深项目经理的工作。\r\n\r\n2025/4/15 周裔锦\r\n\r\n「林嘉豪」 深圳市电信工程有限公司  林经理介绍，已经将我们品牌补录进罗湖妇幼的招标名单，等通知到线上招标。\r\n\r\n2025/4/11 11:30:43 周裔锦\r\n\r\n【完善价格】 85597\r\n\r\n2025/4/11 11:11:38 周裔锦\r\n\r\n【授权编号】：添加   HY-CPJ202504-003\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n2025/4/11 09:28:13 李冬\r\n\r\n【授权编号】：添加   HY-CPJ202504-003\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n2025/4/11 09:27:04 李冬\r\n\r\n【完善价格】 90631\r\n\r\n2025/4/9 周裔锦\r\n\r\n「林嘉豪」 深圳市电信工程有限公司  配合梳理清单，以及报价。接下来等通知在平台邀标。没有回复报价的情况，到时候招标会给一个上限价格。\r\n\r\n2025/4/2 周裔锦\r\n\r\n「林嘉豪」 深圳市电信工程有限公司  林总介绍当前有罗湖妇幼项目，之前已经询过两轮价格，如果价格合适就直接使用。\r\n新皇岗口岸联检大楼项目，他们也会去参与，跟进这个项目的时间比较长，而且比较深，如果没有意外，他们的优势比较大。\r\n\r\n	CPJ202504-003	2025-06-01	85597	\N	\N	2025-04-11 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
5	杭州博览会议中心二期	2023-12-01	sales_focus	sales	qualified	\N	华东建筑设计研究院有限公司	浙江航博智能工程有限公司	\N	浙江微风智能科技有限公司	signed	2025/4/25 18:29:00 李华伟\r\n\r\n【出货时间预测】：改变成   2025年5月20\r\n\r\n\r\n\r\n2025/4/25 李华伟\r\n\r\n「田经理」 浙江微风智能科技有限公司  预计5月签约合同，推动现场采购下单，博物馆有部分天线取消，价格层面一直在谈判让我们给与支持，虽然品牌用了我们但是价格相差中标成本价格有15个点的区间。\r\n\r\n2025/3/24 10:59:04 李华伟\r\n\r\n【出货时间预测】：改变成   2025年二季度\r\n\r\n\r\n\r\n2025/3/24 09:55:41 李华伟\r\n\r\n【完善价格】 1025244\r\n\r\n2025/3/21 16:01:31 李华伟\r\n\r\n【完善价格】 978924\r\n\r\n2025/3/21 15:46:05 李华伟\r\n\r\n【完善价格】 892340\r\n\r\n2025/2/17 14:38:29 李华伟\r\n\r\n【当前阶段情况说明】：添加   目前在做桥架，样板层天线代理商提供给现场确认，预计3-4月份进行穿线，近期会安排拜访客户采购确认合同事宜。\r\n\r\n\r\n\r\n2025/1/17 11:11:22 李华伟\r\n\r\n【出货时间预测】：添加   2025年一季度\r\n\r\n\r\n\r\n2024/8/26 10:51:23 李华伟\r\n\r\n【拜访】「」:  本周同李波拜访微风，实际科大讯飞分包微风来做，分包管理费比较高，后面会有深化和价格问题。然后安排代理商航博先把采购层面关系做扎实。预计年后三四月份穿线。\r\n\r\n2024/8/16 14:25:06 李华伟\r\n\r\n【阶段变更】招标中->中标\r\n\r\n\r\n\r\n跟进记录 李华伟\r\n\r\n【阶段变更】品牌植入->招标中\r\n\r\n2024/4/29 15:31:10 李华伟\r\n\r\n【一致行动人】「」:  通过代理商李波认识介绍集成商采购和技术，一同对接分工。\r\n\r\n2024/3/15 13:58:51 李华伟\r\n\r\n「拜访」  :  目前品牌华东院给到微风，微风这边已经接洽上，围标品牌他们没有意见，表示价格不能虚高不然他们反而被动，绑定关键人合作。下周关注品牌情况。\r\n\r\n2024/2/21 12:45:50 李华伟\r\n\r\n集成商改变为  浙江微风智能科技有限公司    \r\n\r\n2024/2/21 12:45:34 李华伟\r\n\r\n设计方改变为  华东建筑设计研究院有限公司 类型改变为  销售重点    \r\n\r\n2023/11/1 李华伟\r\n\r\n前期设计配合目前华东院出图，当地集成商微风智能参与设计。\r\n\r\n	SPJ202312-001	2025-05-25	1092731	\N	\N	2023-12-01 00:00:00	2025-05-30 03:15:15.629585	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
64	上实北外滩480米	2023-10-17	sales_focus	sales	qualified	\N	华东建筑设计研究院有限公司	\N	\N	上海市安装工程集团有限公司-第九分公司	embed	2025/4/16 杨俊杰\r\n\r「黄辰赟」 华东建筑设计研究院有限公司  拜访黄辰贇，沟通了解目前北外滩91号地块，业主计划本月底完成商办部分招标图设计，下月确认观光区域，业主有想法计划弱电也在今年完成招标。有关品牌方面目前负责的暖通业主刘工，因智能化不太了解，加上性格问题，所以不太会插手品牌，所以很有可能会结合多方意见，主要是华东院和WSP。华东院内部可能参与的有张晓波和黄辰贇及毛晶轶。目前计划先把整体方案进行复核，待方案确认后结合概算统一来看。至于品牌上，做好各方关系，确保品牌入围同时能争取有利情况\r\n\r2025/4/14 杨俊杰\r\n\r「毛晶轶」 华东建筑设计研究院有限公司  与毛晶轶沟通，了解有关业主及品牌情况。按毛晶轶反馈目前业主那边不用太过担心，基本都会听他的，让我们先去和黄辰贇沟通，给予黄辰贇一版品牌建议，待黄辰贇确认后他这边会去看是否合理\r\n\r2025/4/10 13:18:13 杨俊杰\r\n\r【设计院及顾问】：改变成   华东建筑设计研究院有限公司\r\n\r\r\n\r2024/9/5 12:48:09 杨俊杰\r\n\r【消息】「」该项目目前配合黄辰赟提供图纸设计，项目属于施工图报审阶段，地下室部分经沟通了解图纸审核通过，地上部分开始启动。黄辰赟仅负责地上商业裙房部分，其余的由周天文和毛晶轶共同完成。现在他们内部也比较混乱，主负责交给王小安，按黄辰赟意思她会带着我们去和王小安沟通，看下一步如何推进\r\n\r2024/3/15 16:39:08 杨俊杰\r\n\r目前地下室配套菁峰参与设计，据了解是黄辰赟委托上安，上安再委托菁峰，提供地下室点位图和系统图，项目分为商业和酒店两套系统\r\n\r2023/11/1 杨俊杰\r\n\r该项目机电顾问为WSP，整个项目PM团队由华东院负责，弱电负责人为张晓波，同时业主聘请了专家，其中包括瞿二然，项目深化设计目前初步订地下部分由华东院黄辰赟负责，地上部分由李欣负责。需要了解施工图启动时间，推动施工图深化设计。\r\n\r	SPJ202310-002	2025-04-16	3371652	\N	\N	2023-10-17 00:00:00	2025-05-30 06:11:07.591893	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
61	华虹张江工厂配套用房	2024-08-08	channel_follow	channel	qualified	上海华虹(集团)有限公司 	上海华虹智联信息科技有限公司	上海瀚网智能科技有限公司	\N	上海华虹智联信息科技有限公司	signed	2025/4/18 杨俊杰\r\n\r「周心一」 上海华虹智联信息科技有限公司  与采购周心一及项目经理确认最终方案及价格，渠道配合提供最终报价，待采购确认后，发起合约商务流程\r\n\r2025/4/7 17:25:45 李冬\r\n\r【当前阶段】：改变成   重复\r\r\n\r\n\r2025/4/3 23:48:29 李冬\r\n\r【分销商】：添加   上海瑞康\r\r\n\r\n\r2025/2/21 16:38:59 杨俊杰\r\n\r【完善价格】 148069\r\n\r2025/2/21 15:15:04 杨俊杰\r\n\r【出货时间预测】：添加   2025年二季度\r\n\r【分销商】：添加   上海瑞康\r\n\r\r\n\r45704.657349537 李冬\r\n\r【当前阶段】：改变成   中标\r\n\r【当前阶段情况说明】：添加   该项目华虹计通中标，品牌入围，主要与凌越竞争。现阶段华虹计通采购三方询价，分别找到瑞康和凌越。拜访业主负责人王炜，希望通过业务合作锁定系统品牌\r\n\r\r\n\r2025/2/16 15:46:35 杨俊杰\r\n\r【当前阶段】：改变成   中标\r\n\r【当前阶段情况说明】：添加   该项目华虹计通中标，品牌入围，主要与凌越竞争。现阶段华虹计通采购三方询价，分别找到瑞康和凌越。拜访业主负责人王炜，希望通过业务合作锁定系统品牌\r\n\r\r\n\r45704.6564236111 李冬\r\n\r【直接用户】：添加   上海华虹(集团)有限公司 \r\n\r\r\n\r2025/2/16 15:45:15 杨俊杰\r\n\r【直接用户】：添加   上海华虹(集团)有限公司 \r\n\r\r\n\r45653 李冬\r\n\r类型改变为渠道跟进 \r\n\r2024/12/27 杨俊杰\r\n\r类型改变为渠道跟进 \r\n\r45653 李冬\r\n\r类型改变为销售重点 \r\n\r2024/12/27 杨俊杰\r\n\r类型改变为销售重点 \r\n\r45597 李冬\r\n\r【阶段变更】品牌植入->招标中\r\n\r\r\n\r2024/11/1 杨俊杰\r\n\r【阶段变更】品牌植入->招标中\r\n\r\r\n\r45540.5734027778 李冬\r\n\r【消息】「」该项目设计院反馈图纸设计已经完成，等待招标，品牌由业主指定，在跟踪确认。设计院反馈无线对讲概算50万+，项目一共7万方。\r\n\r2024/9/5 13:45:42 杨俊杰\r\n\r【消息】「」该项目设计院反馈图纸设计已经完成，等待招标，品牌由业主指定，在跟踪确认。设计院反馈无线对讲概算50万+，项目一共7万方。\r\n\r	CPJ202408-003	2025-04-18	148069	\N	\N	2024-08-08 00:00:00	2025-05-30 06:29:02.604463	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	3
187	九星城项目	2022-11-14	channel_follow	sales	controlled	\N	卓展工程顾问(北京)有限公司-上海分公司	上海福玛通信信息科技有限公司	\N	上海蓝极星智能科技有限公司	signed	2025/2/21 15:02:33 杨俊杰\r\n\r【出货时间预测】：添加   2025年二季度\r\n\r【系统集成商】：改变成   宋治军「上海蓝极星智能科技有限公司」\r\n\r【当前阶段情况说明】：添加   该项目分为三个标段，其中一标段中标单位：江苏金鼎，二标段中标单位：蓝极星（景文同安拆分的专做智能化），三标段中标单位：中邮建，品牌为天馈入围，和源通信，瀚网及威升。目前二标段在渠道付言新引荐下与蓝极星负责人宋总有过沟通，借用付言新与宋治军关系，初步达成合作意向，提交推进品牌锁定。一、三标段由于公开招标，中标单位投了超低价格，一直没有任何消息。同时通过蓝极星及其他渠道了解，苏州中瀚和杨顺凯在合作，以苏州威升名义在与我们竞争，通过蓝极星宋治军了解价格很低，同时三标段有个圆信询价至李冬，经了解在此之前就是有人用威升再配合。与卓展李霄云了解，业主还是希望各个标段品牌同一，目前再配合付言新提供各个标段接口要求统一说明。计划先推进二标段锁定品牌后在跟进一三标段，看商务如何报价。项目原定计划延迟至今年底，预计二标段2季度，3季度才会落实商务\r\n\r\r\n\r2024/12/27 杨俊杰\r\n\r类型改变为渠道跟进 \r\n\r45653 邹飞\r\n\r类型改变为渠道跟进 \r\n\r2024/10/8 杨俊杰\r\n\r【阶段变更】招标中->中标\r\n\r\r\n\r45573 邹飞\r\n\r【阶段变更】招标中->中标\r\n\r\r\n\r2024/9/5 12:53:06 杨俊杰\r\n\r【消息】「」本项目正式招标，目前拆分为三个标段，其中一，三标段为公开招标，渠道及我们都在配合，而二标段在集成商上有一定限制要求，所以仅7家参与，主要是上安。所有标段都是本月开标，核心抓住二标段机房部分，其余都需接入至二标段\r\r\n【阶段变更】招标前->招标中\r\n\r45540.536875 邹飞\r\n\r【消息】「」本项目正式招标，目前拆分为三个标段，其中一，三标段为公开招标，渠道及我们都在配合，而二标段在集成商上有一定限制要求，所以仅7家参与，主要是上安。所有标段都是本月开标，核心抓住二标段机房部分，其余都需接入至二标段\r\r\n【阶段变更】招标前->招标中\r\n\r2024/3/20 16:42:24 杨俊杰\r\n\r「阶段变更」\r\n\r45371.6961111111 邹飞\r\n\r「阶段变更」\r\n\r2023/11/1 杨俊杰\r\n\r前期方案阶段前期设计，配套设计方案\r\n\r45231 邹飞\r\n\r前期方案阶段前期设计，配套设计方案\r\n\r	CPJ202211-009	2025-02-21	2134545	\N	\N	2022-11-14 00:00:00	2025-05-30 06:34:27.347715	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
7	深圳市星河智善科技有限公司集采	2025-03-25	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳市星河智善科技有限公司	awarded	2025/4/25 16:31:24 周裔锦\r\n\r【当前阶段】：改变成   中标\r\r\n\r\n\r2025/4/25 16:30:49 周裔锦\r\n\r【当前阶段情况说明】：改变成   业主介绍，最快5月份会有部分产品采购。\r\r\n\r\n\r2025/4/25 14:58:07 周裔锦\r\n\r【出货时间预测】：添加   2025年二季度5月份\r\r\n【当前阶段情况说明】：改变成   科技介绍，最快5月份会有部分产品采购。\r\r\n\r\n\r2025/3/25 21:52:33 周裔锦\r\n\r【当前阶段情况说明】：改变成   本次参与集采品牌：英智源、侨讯、京昊丰科、和源。以邀标形式招标，目前还在议价中。\r\r\n\r\n\r2025/3/25 21:52:00 周裔锦\r\n\r【当前阶段】：改变成   招标中\r\r\n【授权编号】：添加   HY-CPJ202503-025\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/22 02:28:26 周裔锦\r\n\r【完善价格】 2215227\r\n\r2025/2/22 02:16:00 周裔锦\r\n\r【系统集成商】：添加   深圳市星河智善科技有限公司\r\r\n\r\n\r	CPJ202503-025	2025-04-25	2215227	\N	\N	2025-03-25 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
48	哔哩哔哩新世代产业园项目	2025-04-14	channel_follow	channel	unqualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳达实智能股份有限公司	pre_tender	2025/4/18 15:23:16 周裔锦\r\n\r【完善价格】 1200960\r\n\r2025/4/18 周裔锦\r\n\r「帅进」 深圳达实智能股份有限公司  帅总要求尽快梳理出本项目的配置，要求尽量精准，本项目对成本比较关注。具体招标时间还没有定下来。\r\n目前已经梳理出来了配置和成本清单。\r\n\r2025/4/14 10:53:59 周裔锦\r\n\r【授权编号】：添加   HY-CPJ202503-034\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/14 花伟\r\n\r「花伟」 敦力(南京)科技有限公司  B站的项目提供集成商投标时的报价，等待最终的中标单位。\r\n\r2025/4/3 14:55:55 花伟\r\n\r【经销商】：添加   花伟「敦力(南京)科技有限公司」\r\r\n【授权编号】：添加   HY-CPJ202503-034\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202503-034	2025-04-18	1200960	\N	\N	2025-04-14 00:00:00	2025-05-11 00:59:24.476988	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
11	永寿路88号（新黄浦酒店公寓）	2025-04-21	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海云思智慧信息技术有限公司	tendering	2025/4/25 13:47:22 杨俊杰\r\n\r【完善价格】 128362\r\n\r2025/4/23 杨俊杰\r\n\r「刘宗怡」 上海云思智慧信息技术有限公司  渠道报备，云思参与此业务投标，品牌虽然未入围，但可以使用同档次，云思咨询价格合适后，还是会考虑知名品牌\r\n\r2025/4/21 14:33:31 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202504-027\r\n\r\r\n\r2025/4/21 11:54:26 杨俊杰\r\n\r提交报备\r\n\r	CPJ202504-027	2025-04-25	128362	\N	\N	2025-04-21 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
79	沈阳市沈河区金廊22-1	2025-03-29	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海东大金智信息系统有限公司	tendering	2025/4/13 15:33:44 杨俊杰\r\n\r【完善价格】 252498\r\n\r2025/4/13 15:12:47 杨俊杰\r\n\r【当前阶段】：改变成   招标中\r\n\r\r\n\r2025/4/13 15:12:32 杨俊杰\r\n\r【当前阶段】：改变成   失败\r\n\r【当前阶段情况说明】：改变成   渠道反馈，配合集成商未中标\r\n\r\r\n\r2025/4/10 10:42:07 李冬\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：改变成   渠道报备，配合东大参与项目投标，品牌入围，主要竞争品牌:锐河、畅博、英智源\r\n客户投标，跟踪结果，客户反馈没有中标，具体中标单位未知\r\r\n\r\n\r2025/4/10 李冬\r\n\r「李兵」 上海东大金智信息系统有限公司  客户反馈没有中标，具体中标单位未知\r\n\r2025/3/29 12:50:40 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202503-017\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r2025/3/21 11:52:32 李冬\r\n\r【授权编号】：添加   HY-CPJ202503-017\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/3/21 11:18:02 李冬\r\n\r【完善价格】 188131\r\n\r2025/3/21 11:14:26 李冬\r\n\r【分销商】：添加   上海瑞康\r\r\n\r\n\r	CPJ202503-017	2025-04-13	252498	\N	\N	2025-03-29 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
17	上海名人苑	2024-08-07	channel_follow	channel	qualified	\N	\N	上海福玛通信信息科技有限公司	\N	上海秋煜电力工程有限公司	signed	2025/4/25 12:42:39 杨俊杰\r\n\r[阶段变更] ->签约\r\n\r2025/4/21 14:27:18 杨俊杰\r\n\r申请项目批价\r\n\r2025/4/21 14:26:07 杨俊杰\r\n\r【完善价格】 456293\r\n\r2025/4/21 14:22:34 杨俊杰\r\n\r【完善价格】 455377\r\n\r2025/4/21 杨俊杰\r\n\r「冯一」 上海秋煜电力工程有限公司  跟踪渠道，确认商务合同已经确认，发起渠道业务批价确认\r\n\r2025/4/18 邹飞\r\n\r「冯一」 上海秋煜电力工程有限公司  预计下周先供货10#楼天馈部分的材料\r\n\r2025/4/11 邹飞\r\n\r「冯一」 上海秋煜电力工程有限公司  现场部分已具备施工条件，预计5月份启动\r\n\r2025/2/21 13:30:42 杨俊杰\r\n\r【出货时间预测】：添加   2025年二季度\r\n\r【当前阶段情况说明】：添加   该项目跟进确认，现场实施具备施工条件，项目现场负责人计划3月份提交采购计划。待项目现场提交采购计划后，会组织供应商与他们商务负责人洽谈价格机合约。现阶段与项目现场复核确认深化方案，商务方面因与现场达成合作意向，品牌已经提交确认\r\n\r\r\n\r2024/12/6 杨俊杰\r\n\r【阶段变更】失败->中标\r\n\r\r\n\r45632 邹飞\r\n\r【阶段变更】失败->中标\r\n\r\r\n\r2024/12/6 杨俊杰\r\n\r【阶段变更】中标->失败\r\n\r\r\n\r45632 邹飞\r\n\r【阶段变更】中标->失败\r\n\r\r\n\r2024/8/30 12:40:08 杨俊杰\r\n\r【消息】「」该项目帮助渠道与弱电分包单位推进信道机及对讲机替换为全和源产品，目前说服弱电单位现场负责人，提供产品资料及样品，给予项目现场，让项目现场提交资料报验，等待结果，预计9月份会有结果。商务进度按弱电分包现场负责人计划今年底会有部分区域启动穿线\r\n\r45534.5278703704 邹飞\r\n\r【消息】「」该项目帮助渠道与弱电分包单位推进信道机及对讲机替换为全和源产品，目前说服弱电单位现场负责人，提供产品资料及样品，给予项目现场，让项目现场提交资料报验，等待结果，预计9月份会有结果。商务进度按弱电分包现场负责人计划今年底会有部分区域启动穿线\r\n\r2024/8/18 13:36:31 杨俊杰\r\n\r【消息】「」该项目与渠道沟通了解，中标单位上海秋煜在内部复核成本，比选价格，目前主要与率衍在PK价格，但福玛与现场负责人商务关系有过合作，通过信道机、对讲机品牌由摩托罗拉替换为和源策略，现阶段还在沟通调整整体报价，推进锁定和源品牌\r\n\r45522.567025463 邹飞\r\n\r【消息】「」该项目与渠道沟通了解，中标单位上海秋煜在内部复核成本，比选价格，目前主要与率衍在PK价格，但福玛与现场负责人商务关系有过合作，通过信道机、对讲机品牌由摩托罗拉替换为和源策略，现阶段还在沟通调整整体报价，推进锁定和源品牌\r\n\r2024/7/4 杨俊杰\r\n\r该项目渠道报备，福玛付言新的客户中标，和源品牌入围，项目实施预计要明年一季度，目前在方案深化配套，并推进采用全系列和源产品\r\n\r45477 邹飞\r\n\r该项目渠道报备，福玛付言新的客户中标，和源品牌入围，项目实施预计要明年一季度，目前在方案深化配套，并推进采用全系列和源产品\r\n\r	CPJ202408-002	2025-04-25	205331.85000000003	\N	\N	2024-08-07 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
478	杨树浦路670号优秀历史建筑装修	2025-02-27	channel_follow	channel	qualified	\N	华东建筑设计研究院有限公司	\N	\N	上海益邦智能技术股份有限公司	awarded	2025/2/27 10:22:08 邹飞\r\n\r【设计院及顾问】：添加   华东建筑设计研究院有限公司\r\r\n【系统集成商】：添加   上海益邦智能技术股份有限公司\r\r\n【授权编号】：添加   HY-CPJ202401-009\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/3/25 14:03:37 杨俊杰\r\n\r「阶段变更」\r\n\r2024/3/11 10:03:51 杨俊杰\r\n\r「阶段变更」\r\r\n该项目据了解是煦华挂靠中标，目前询价至大展及福玛，预计二季度会落实供应商采购\r\n\r2024/3/4 16:56:40 杨俊杰\r\n\r围标状况改变为   入围 设计方改变为  华东建筑设计研究院有限公司 分销商改编为   上海淳泊     \r\r\n该项目与华东院余杰沟通了解招标品牌为正禄、和源、汉界，其中正禄是余杰放的品牌，而汉界说是大总包放的品牌，通过大总包投标文件上了解到选的是和源品牌，但具体弱电智能化单位情况不清楚。渠道大展报备说是有一家煦华询价。计划3月中旬通过大展确认是否煦华为中标\r\n\r2023/11/1 杨俊杰\r\n\r该项目华东院余杰找到我报备，经了解此项目基本锁定和源品牌，届时会有弱电单位与我们联系\r\n\r	CPJ202401-009	2025-02-27	0	\N	\N	2025-02-27 00:00:00	2025-02-27 10:22:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
69	张家浜楔形绿地C1B-02地块办工	2025-04-14	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	上海壹杰信息技术有限公司	tendering	2025/4/14 15:43:39 李华伟\r\n\r【授权编号】：添加   HY-CPJ202504-012\r\r\n\r\n\r2025/4/11 14:07:33 李华伟\r\n\r提交报备\r\n\r2025/4/11 13:49:04 李华伟\r\n\r【完善价格】 179289\r\n\r	CPJ202504-012	2025-04-14	179289	\N	\N	2025-04-14 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	1
212	洋泾西区EO8-4、E10-2、E12-1地块	2024-09-29	channel_follow	channel	qualified	\N	AECOM	上海福玛通信信息科技有限公司	\N	上海行余信息技术有限公司	awarded	2025/1/17 11:16:28 李华伟\r\n\r【出货时间预测】：改变成   2025年三季度\r\r\n\r\n\r45674.4697685185 邹飞\r\n\r【出货时间预测】：改变成   2025年三季度\r\r\n\r\n\r2024/10/10 李华伟\r\n\r【阶段变更】招标中->中标\r\r\n\r\n\r45575 邹飞\r\n\r【阶段变更】招标中->中标\r\r\n\r\n\r2024/10/10 13:56:39 李华伟\r\n\r【完善价格】 238818\r\n\r45575.5810069444 邹飞\r\n\r【完善价格】 238818\r\n\r2024/10/10 13:56:23 李华伟\r\n\r【完善价格】 272898\r\n\r45575.5808217593 邹飞\r\n\r【完善价格】 272898\r\n\r	CPJ202409-014	2025-01-17	238818	\N	\N	2024-09-29 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
306	嘉兴云帆大厦	2024-03-21	channel_follow	channel	qualified	\N	\N	浙江航博智能工程有限公司	\N	浙江众诚智能	signed	2024/4/1 10:53:49 李华伟\r\n\r【完善价格】 57982\r\n\r2024/4/1 09:34:18 李华伟\r\n\r「阶段变更」\r\n\r2024/3/21 李华伟\r\n\r「提案采纳」  :  品牌天馈无要求，目前航博配合投标的客户中标，在确认商务价格阶段。预计月底前签约。\r\n\r2024/3/1 17:25:56 李华伟\r\n\r[阶段变更] ->签约\r\n\r	CPJ202403-006	2024-04-20	26091.899999999998	\N	\N	2024-03-21 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
36	海宁经开智创园	2025-02-17	channel_follow	channel	qualified	\N	\N	上海瀚网智能科技有限公司	\N	华维星电技术有限公司	signed	2025/4/21 15:06:19 李华伟\r\n\r[阶段变更] ->签约\r\n\r2025/3/24 10:00:14 李华伟\r\n\r【出货时间预测】：改变成   2025年二季度\r\r\n\r\n\r2025/3/10 14:49:30 李华伟\r\n\r【出货时间预测】：添加   2025年一季度\r\r\n【当前阶段】：改变成   中标\r\r\n\r\n\r2025/3/10 10:00:05 李华伟\r\n\r【完善价格】 213627\r\n\r2025/2/25 16:29:25 李冬\r\n\r【授权编号】：添加   HY-CPJ202502-010\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/2/17 13:30:15 李华伟\r\n\r【完善价格】 151017\r\n\r2025/2/17 12:54:10 李华伟\r\n\r【当前阶段】：添加   招标中\r\r\n【授权编号】：添加   HY-CPJ202502-010\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202502-010	2025-04-21	96122.25	\N	\N	2025-02-17 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
405	郑州大学第一附属医院惠济院区	2024-06-14	channel_follow	channel	qualified	\N	\N	上海瑞康通信科技有限公司	\N	河南佰邦电子科技有限公司	tendering	2025/4/10 15:05:23 李冬\r\n\r【完善价格】 794578\r\n\r2025/4/10 15:00:02 李冬\r\n\r【系统集成商】：添加   河南佰邦电子科技有限公司\r\r\n\r\n\r2025/3/19 16:36:58 李冬\r\n\r【当前阶段情况说明】：添加   投标中，5月份出结果\r\r\n\r\n\r45592 李冬\r\n\r【阶段变更】招标中\r\n\r\n\r2024/10/27 庄海鑫\r\n\r【阶段变更】招标中\r\n\r\n\r45457 李冬\r\n\r项目由经销商提供，目前在配合投标工作\r\n\r2024/6/14 庄海鑫\r\n\r项目由经销商提供，目前在配合投标工作\r\n\r	CPJ202406-007	2025-04-10	0	\N	\N	2024-06-14 00:00:00	2025-04-10 15:05:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
479	中芯国际-创新技术中芯项目（龙舟计划配套项目）	2025-02-27	channel_follow	sales	qualified	\N	\N	北京联航迅达通信技术有限公司	\N	\N	awarded	2025/2/27 10:16:15 邹飞\r\n\r【授权编号】：添加   HY-CPJ202311-004\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/7/18 08:27:00 范敬\r\n\r【消息】「」目前业主正在上报总部，批复后邀请招标\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、配合出配置清单，目前中继台、对讲机品牌和源不在内；\r\n2、配合北京代理商（联航讯达）给北京航天丽华科技有限公司报价；\r\n3、正在进行第二轮报价；\r\n\r	CPJ202311-004	2025-02-27	0	\N	\N	2025-02-27 00:00:00	2025-02-27 10:16:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
409	上海冠龙公司新办公大楼暨智慧水务孵化基地	2025-02-25	channel_follow	marketing	qualified	\N	\N	\N	\N	上海众频网络系统工程有限公司	tendering	2025/4/10 14:06:00 李冬\r\n\r【完善价格】 127861\r\n\r2025/4/10 14:02:09 李冬\r\n\r【当前阶段】：改变成   招标中\r\r\n【当前阶段情况说明】：改变成   历史报备项目结转，近况跟进中\r\n众频可能中标，需要去沟通确定\r\r\n\r\n\r2025/4/10 10:46:41 李冬\r\n\r【当前阶段】：改变成   中标\r\r\n【当前阶段情况说明】：改变成   历史报备项目结转，近况跟进中\r\n众频中标\r\r\n\r\n\r2025/4/10 10:16:55 李冬\r\n\r【当前阶段】：改变成   重复\r\r\n\r\n\r2025/4/3 23:42:27 李冬\r\n\r【分销商】：添加   上海瑞康\r\r\n【授权编号】：添加   HY-CPJ202412-019\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/4/3 李冬\r\n\r「赵」 上海众频网络系统工程有限公司  项目他们中标，和李华伟沟通下来邀约好一起去聊一下\r\n\r2025/2/25 16:19:36 李冬\r\n\r【授权编号】：添加   HY-CPJ202412-019\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/1/17 11:23:24 李华伟\r\n\r【完善价格】 102620\r\n\r2025/1/17 11:21:00 李华伟\r\n\r【授权编号】：添加   HY-CPJ202412-019\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r	CPJ202412-019	2025-04-10	0	\N	\N	2025-02-25 00:00:00	2025-04-10 14:06:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
500	山樾湾花园	2024-05-11	channel_follow	channel	qualified	\N	\N	上海瑞康通信科技有限公司	\N	深圳市坐标建筑装饰工程股份有限公司	awarded	45660 李冬\r\n\r【阶段变更】招标前->中标\r\r\n\r\n\r2025/1/3 周裔锦\r\n\r【阶段变更】招标前->中标\r\r\n\r\n\r45625 李冬\r\n\r【阶段变更】签约->招标前\r\r\n\r\n\r2024/11/29 周裔锦\r\n\r【阶段变更】签约->招标前\r\r\n\r\n\r45620.9508101852 李冬\r\n\r【完善价格】 603482\r\n\r2024/11/24 22:49:10 周裔锦\r\n\r【完善价格】 603482\r\n\r45618 李冬\r\n\r【出现困难】深圳坐标建筑装饰工程股份有限公司中标智能化分包，目前已和李工报价，发射设备：摩托罗拉、建伍、海能达。合路平台和天馈系统：瀚网、威升、和源、浩天通信。\r\r\n\r\n\r2024/11/22 周裔锦\r\n\r【出现困难】深圳坐标建筑装饰工程股份有限公司中标智能化分包，目前已和李工报价，发射设备：摩托罗拉、建伍、海能达。合路平台和天馈系统：瀚网、威升、和源、浩天通信。\r\r\n\r\n\r45592 李冬\r\n\r【阶段变更】招标中->签约\r\r\n\r\n\r2024/10/27 庄海鑫\r\n\r【阶段变更】招标中->签约\r\r\n\r\n\r45423 李冬\r\n\r【提案】:  目前集成商深圳旗云、广东畅想参与投标\r\n\r2024/5/11 庄海鑫\r\n\r【提案】:  目前集成商深圳旗云、广东畅想参与投标\r\n\r	CPJ202405-005	2025-01-03	0	\N	\N	2024-05-11 00:00:00	2025-01-03 15:37:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
420	派米雷科技园	2025-02-25	channel_follow	\N	qualified	\N	\N	上海瑞康通信科技有限公司	\N	上海华虹智联信息科技有限公司	signed	2025/4/7 17:31:05 李冬\r\n\r【当前阶段】：改变成   签约\r\r\n\r\n\r2025/2/25 14:47:00 李冬\r\n\r【授权编号】：添加   HY-CPJ202304-008\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2024/10/21 杨俊杰\r\n\r【阶段变更】中标->签约\r\n\r\r\n\r2024/10/21 13:52:30 杨俊杰\r\n\r【完善价格】 57844\r\n\r2024/10/21 13:50:07 杨俊杰\r\n\r【完善价格】 57990\r\n\r2024/10/21 13:48:55 杨俊杰\r\n\r【完善价格】 58277\r\n\r2024/9/20 16:29:44 杨俊杰\r\n\r【完善价格】 66673\r\n\r2024/8/30 13:01:37 杨俊杰\r\n\r【消息】「」该项目据现场反馈即将启动，商务方面渠道已经在跟进，和渠道确认商务节点\r\n\r2024/7/4 14:30:35 杨俊杰\r\n\r【消息】「」渠道反馈与现场项目负责人沟通，了解目前现场大部分区域桥架还未完成，这部分由大总包负责，预计需要1-2个月，设备进场预估在9月份。商务方面投标选用和源品牌，采购发起需等待现场通知，现场方面在确认实施清单\r\n\r2024/5/7 12:49:33 杨俊杰\r\n\r【消息】「」渠道与吴昊沟通反馈得知具体决定由周心一负责，具体项目现场负责人周羽反馈已经提交采购计划，但正式进场需要等到6月份，具体穿线时间还要看现场进度\r\n\r2024/3/20 16:35:21 杨俊杰\r\n\r该项目还早，集成商还未进场，等进场后跟进确认方案，了解实施进度，预估采购时间\r\n\r2023/11/1 杨俊杰\r\n\r华虹计通中标，投标当时选用和源品牌。目前现场周羽负责，在做管线预埋，设备预计明年春节以后\r\n\r	CPJ202304-008	2025-04-07	0	\N	\N	2025-02-25 00:00:00	2025-04-07 17:31:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	2
59	上海党校	2025-02-08	sales_focus	sales	qualified	\N	上海现代建筑设计研究院有限公司	\N	\N	上海仪电鑫森科技发展有限公司	embed	2025/4/18 杨俊杰\r\n\r「闻锋」 上海现代建筑设计研究院有限公司  拜访闻锋，沟通上海党校，目前还在方案阔粗，用户希望搭建上层平台，所以找了3家，华为、联通及仪电鑫森，待方案阔粗好了之后才会启动智能化设计。至于915项目，经沟通确认，仪电鑫森已经报了和源的品牌，但因为项目特殊性，所以进度比较慢\r\n\r2025/4/13 15:05:41 杨俊杰\r\n\r【系统集成商】：添加   上海仪电鑫森科技发展有限公司\r\n\r\r\n\r2025/2/8 11:08:29 杨俊杰\r\n\r【授权编号】：添加   HY-SPJ202501-004\r\n\r【类型】：添加   销售重点\r\n\r\r\n\r2025/2/6 14:26:42 杨俊杰\r\n\r【完善价格】 422224\r\n\r2025/2/6 11:51:36 杨俊杰\r\n\r【设计院及顾问】：改变成   闻锋「上海现代建筑设计研究院有限公司」\r\n\r【当前阶段】：添加   品牌植入\r\n\r\r\n\r	SPJ202501-004	2025-04-18	422224	\N	\N	2025-02-08 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
428	临港新片区滴水湖金融湾二期29-01地块	2025-02-10	channel_follow	channel	qualified	\N	\N	上海瑞康通信科技有限公司	\N	上海市建设工程机电设备有限公司	awarded	2025/4/3 23:40:31 李冬\r\n\r【分销商】：添加   上海瑞康\r\r\n\r\n\r2025/3/19 16:54:55 李冬\r\n\r【当前阶段】：改变成   中标\r\r\n【当前阶段情况说明】：改变成   该项目渠道瀚网张国栋报备，配合上海市建设工程机电工程、启伟实业参与项目投标。经了解设计方是上海益邦，品牌入围，主要竞争烈龙、曙腾，项目于1月16号投标，光大中标\r\r\n\r\n\r45698.4615046296 李冬\r\n\r【授权编号】：添加   HY-CPJ202501-009\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r2025/2/10 11:04:34 杨俊杰\r\n\r【授权编号】：添加   HY-CPJ202501-009\r\n\r【类型】：添加   渠道跟进\r\n\r\r\n\r45663.5827662037 李冬\r\n\r【完善价格】 14193\r\n\r45663.5815162037 李冬\r\n\r【当前阶段】：添加   招标中\r\n\r\r\n\r	CPJ202501-009	2025-04-03	0	\N	\N	2025-02-10 00:00:00	2025-04-03 23:40:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
495	静安区养老院	2023-11-13	channel_follow	sales	not_required	\N	\N	上海瑞康通信科技有限公司	\N	上海昊蕾信息技术有限公司	tendering	45670.7125810185 李冬\r\n\r【当前阶段】：改变成   招标中\r\r\n\r\n\r2025/1/13 17:06:07 李华伟\r\n\r【当前阶段】：改变成   招标中\r\r\n\r\n\r45642 李冬\r\n\r【出现困难】业主取消无线对讲系统。\r\r\n\r\n\r2024/12/16 李华伟\r\n\r【出现困难】业主取消无线对讲系统。\r\r\n\r\n\r45343.5347800926 李冬\r\n\r分销商改编为   上海瑞康 类型改变为  渠道管理 集成商改变为  上海昊蕾信息技术有限公司    \r\n\r2024/2/21 12:50:05 李华伟\r\n\r分销商改编为   上海瑞康 类型改变为  渠道管理 集成商改变为  上海昊蕾信息技术有限公司    \r\n\r45231 李冬\r\n\r对方配合设计院参与前期设计，我方配合客户做方案，计划植入和源对讲机。\r\n\r2023/11/1 李华伟\r\n\r对方配合设计院参与前期设计，我方配合客户做方案，计划植入和源对讲机。\r\n\r	CPJ202311-003	2025-01-13	0	\N	\N	2023-11-13 00:00:00	2025-01-13 17:06:00	3	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
109	上海浦东国际机场四期扩建工程	2024-02-21	sales_focus	marketing	unqualified	上海机场(集团)有限公司	华东建筑设计研究院有限公司	\N	\N	上海市安装工程集团的限公司	embed	2025/4/5 郭小会\r\n\r「吴文芳」 华东建筑设计研究院有限公司  和吴老师沟通浦东机场四期的最新情况，现在浦东机场四期项目招标在小木桥路进行，公开招标，甚至不可以推荐品牌，看不清楚后面如何操作。吴老师建议待前面的安防标招好了后，看指挥部是如何操作的，我们的对讲系统招标计划在今年年底和明年年初。\r\n\r2025/3/21 13:55:50 郭小会\r\n\r【直接用户】：添加   上海机场(集团)有限公司\r\r\n\r\n\r2025/3/11 14:08:52 郭小会\r\n\r【系统集成商】：添加   上海市安装工程集团的限公司\r\r\n\r\n\r2024/5/25 10:30:31 郭小会\r\n\r【消息】「」浦东机场四期停车楼部分图纸已完成初步深化，交给华东院，近期再跟进时，了解最新进展以及业主的情况，徐昊给到业主顾婷婷近期也准备接触了解情况\r\n\r2024/4/24 10:38:31 郭小会\r\n\r【消息】「」建工通过上安九分反馈浦东机场四期建筑会采用新材料，可能信号屏蔽加强，对所有通信系统会有影响 ，要求相关通信厂家去嘉兴搭建的临时模型区域去测试评估，已协调安排可以杨和赵去现场测试，后续出具评估报告\r\n\r2024/4/24 10:35:02 郭小会\r\n\r【消息】「」浦东机场四期项目启动深化设计，带刘威参加华东院关于项目中停车楼部分的深化设计要求，本次深化设计主要是用于建筑招标，根据深化设计图纸，造价公司评估管材用量\r\n\r2024/2/23 09:12:39 郭小会\r\n\r面价金额改变为   10171807    \r\n\r2024/2/21 郭小会\r\n\r配合华东院吴老师进行前期设计规划，本次设计范围包括T3航站楼、南北车库和交通中心，系统包含消防对讲和公安对讲，边防对讲独立建设\r\n\r	SPJ202402-002	2025-04-05	10171807	\N	\N	2024-02-21 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
151	青岛芯恩一期和二期系统整合	2025-03-18	channel_follow	marketing	qualified	\N	\N	\N	\N	上海竞拓数码信息技术有限公司	tendering	2025/3/18 17:04:33 郭小会\r\n\r【授权编号】：添加   HY-CPJ202503-008\r\r\n\r\n\r	CPJ202503-008	2025-03-18	31126	\N	\N	2025-03-18 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
141	京东合作伙伴大厦	2023-08-29	channel_follow	channel	qualified	\N	\N	广州宇洪智能技术有限公司	\N	\N	lost	2025/3/25 15:19:06 郭小会\r\n\r【当前阶段】：改变成   失败\r\r\n【当前阶段情况说明】：添加   代理商配合的总包未中标\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r2024/9/7 22:19:25 郭小会\r\n\r【消息】「」厦门万安已中标，宇洪在配合跟进\r\r\n【阶段变更】招投标->中标\r\n\r2023/11/1 郭小会\r\n\r1、集成商投标，配合代理商提供资料\r\n2、当前清单待敦力提供\r\n3、待技术提供规定模板的清单\r\n4、品牌和源、威升、京信，宇洪配合万安投标\r\n\r	CPJ202308-001	2025-03-25	162766	\N	\N	2023-08-29 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
241	湖南长沙机场改扩建工程	2022-11-07	sales_focus	sales	qualified	\N	民航机场成都电子工程设计有限责任公司	\N	\N	四川中科航建信息技术有限公司	signed	2024/11/30 郭小会\r\n\r【阶段变更】中标->签约\r\r\n\r\n\r2024/7/14 09:34:01 郭小会\r\n\r【消息】「」带董禕去现场，现场勘察，和总包对接，了解项目的实际进度和节点，近期开始启动设备材料报审工作，预计8月初ITC的前端设备要进厂。和总包沟通线缆的问题，核好价重新进行报价，线缆厂家不能变，型号变化提交申请，问题不大\r\n\r2024/6/21 13:05:53 郭小会\r\n\r【消息】「」和李冬一起整理好合同初稿发给四川中航建，进行沟通跟进\r\n\r2024/6/9 09:55:43 郭小会\r\n\r【消息】「」和李冬一起去成都对接四川中航建的相关领导，项目由代理商签约和相关价格及付款进行了沟通，下周和李冬一起商定相关合约条款后再和总包进一步沟通\r\n\r2024/5/12 09:56:38 郭小会\r\n\r【消息】「」长沙机场深化方案调整的相关图纸进行了提交，和李冬沟通长沙机场的合作方式，双方达成一致，接下来可以进一步推进和总包的商务谈判\r\n\r2024/4/23 08:55:10 郭小会\r\n\r【消息】「」组织相关人员参加长沙机场深化设计成果汇报，根据为业主和总包方的意见进行深化设计方案调整\r\n\r2024/4/13 09:46:09 郭小会\r\n\r对接新的分包负责人，了解其公司的情况，进行初步的商务洽谈\r\n\r2024/3/8 13:49:38 郭小会\r\n\r总包已确定我们系统的分包单位四川中科航建，拿到联系方式，尽快对接\r\n\r2024/3/8 13:48:21 郭小会\r\n\r配合总包沟通汇报本次方案的亮点，安排技术整理相关文件，提交给总包\r\n\r2024/2/20 15:44:48 郭小会\r\n\r设计方改变为  民航机场成都电子工程设计有限责任公司 类型改变为  销售重点 集成商改变为  民航成都电子技术有限责任公司    \r\r\n配合总包进行方案调整和深化设计，针对调研需求，进行清单报价变更申请\r\n\r2023/11/1 郭小会\r\n\r1、项目前期配合设计院和业主进行了方案植入，近期会招投标，目前招采中心有对外进行询价，重庆畅博在配合\r\n2、李冬下周出差长沙进一步了解情况\r\n3、需确认产品清单\r\n4、项目需求调研已结束，下一步需要根据需求调整方安案给总包进行确认\r\n5、配合总包进行方案深化\r\n\r	SPJ202211-001	2024-11-30	7651333	\N	\N	2022-11-07 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	2
164	成都高投高新区福田站TOD片区综合开发项目	2024-07-14	channel_follow	channel	qualified	\N	四川省建筑设计研究院有限公司	福淳智能科技(四川)有限公司	\N	四川倍智数能信息工程有限公司	pre_tender	2025/3/3 10:24:27 郭小会\r\n\r【出货时间预测】：改变成   2025年二季度\r\r\n\r\n\r2025/2/7 09:12:40 郭小会\r\n\r【系统集成商】：添加   四川倍智数能信息工程有限公司\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r45695.3837962963 邹娟\r\n\r【系统集成商】：添加   四川倍智数能信息工程有限公司\r\r\n【类型】：改变成   渠道跟进\r\r\n\r\n\r2024/11/29 郭小会\r\n\r类型改变为渠道管理 \r\n\r45625 邹娟\r\n\r类型改变为渠道管理 \r\n\r2024/10/19 21:44:56 郭小会\r\n\r【完善价格】 984824\r\n\r45584.9062037037 邹娟\r\n\r【完善价格】 984824\r\n\r2024/7/14 郭小会\r\n\r邹娟拜访四川省院，了解到成都高投高新区福田站TOD片区综合开发项目省院在设计，项目是EPC的，总包成都高投，内定的集成商是成都倍智，和邹娟沟通后，安排接触倍智进一步了解情况，计划8月中旬安排省院交流\r\n\r45487 邹娟\r\n\r邹娟拜访四川省院，了解到成都高投高新区福田站TOD片区综合开发项目省院在设计，项目是EPC的，总包成都高投，内定的集成商是成都倍智，和邹娟沟通后，安排接触倍智进一步了解情况，计划8月中旬安排省院交流\r\n\r	CPJ202407-005	2025-03-03	984824	\N	\N	2024-07-14 00:00:00	2025-05-11 00:59:24.476988	13	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	13	1
430	嘉华上海P18	2024-06-20	channel_follow	sales	controlled	\N	\N	上海淳泊信息科技有限公司	\N	上海宵远信息技术有限公司	awarded	2025/4/3 23:27:40 邹飞\r\n\r【分销商】：添加   上海淳泊\r\r\n\r\n\r2025/2/28 14:40:01 杨俊杰\r\n\r【设计院及顾问】：添加   科进柏城咨询有限公司-上海分公司\r\n\r【当前阶段】：改变成   转移\r\n\r【分销商】：添加   上海淳泊\r\n\r【当前阶段情况说明】：添加   该项目转移，李华伟负责，辅助代理商跟进\r\n\r\r\n\r2025/2/21 17:08:26 杨俊杰\r\n\r【完善价格】 214892\r\n\r2024/12/27 杨俊杰\r\n\r【阶段变更】招标中->中标\r\n\r\r\n\r45653 邹飞\r\n\r【阶段变更】招标中->中标\r\n\r\r\n\r2024/6/20 杨俊杰\r\n\r该项目WSP作为机电顾问，负责招标及品牌，图纸设计由集成商擎天设计。项目招标，经销商报备，配合参与投标\r\n\r45463 邹飞\r\n\r该项目WSP作为机电顾问，负责招标及品牌，图纸设计由集成商擎天设计。项目招标，经销商报备，配合参与投标\r\n\r	CPJ202406-010	2025-04-03	0	\N	\N	2024-06-20 00:00:00	2025-04-03 23:27:00	24	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	\N	1
66	虹桥机场东片区T1南地块	2024-01-15	sales_focus	sales	controlled	\N	华东建筑设计研究院有限公司	上海瀚网智能科技有限公司	\N	上海电信科技发展有限公司	awarded	2025/4/15 杨俊杰\r\n\r「余杰」 华东建筑设计研究院有限公司  拜访余杰，沟通了解现在他调整到建筑三所，原先项目主要在负责的就是虹桥商务区项目及南京江北地上、地下，至于虹桥商务区项目现场进度比较缓慢，还有一栋建筑结构未封顶，桥架由总包完成，预估智能化今年下半年肯定会启动，至于电信方面通过了解的确各系统都没有完全去配合，可能还是因为现场进度原因\r\n\r2025/2/21 17:15:33 杨俊杰\r\n\r【完善价格】 531170\r\n\r2025/1/8 12:02:39 杨俊杰\r\n\r【出货时间预测】：添加   2025年三季度\r\n\r【当前阶段】：改变成   中标\r\n\r【分销商】：添加   上海瑞康\r\n\r【经销商】：添加   上海瀚网智能科技有限公司\r\n\r\r\n\r2025/1/6 14:18:59 杨俊杰\r\n\r【当前阶段情况说明】：添加   该项目通过设计院告知上海电信中标，当时上海瀚网报备，通过上海瀚网与电信复核确认中标结果。同时瀚网与电信沟通过程中希望我们价格调整，与瀚网商议共同拜访集成商，沟通后再根据情况考虑如何调整报价\r\n\r\r\n\r2025/1/6 14:16:38 杨俊杰\r\n\r【系统集成商】：改变成   上海电信科技发展有限公司\r\n\r\r\n\r2024/12/27 杨俊杰\r\n\r类型改变为销售重点 \r\n\r2024/12/2 杨俊杰\r\n\r【阶段变更】品牌植入->招标中\r\n\r\r\n\r2024/3/26 17:10:25 杨俊杰\r\n\r该项目与华东院余杰沟通了解4月初提交招标图设计确认，随后就启动招标文件，项目预计6月份招标，待招标前他会找云思李坚沟通。目前与余杰基本达成合作，提供全系列品牌，他会帮助我们推动锁定。计划待招标资料配套完成后，复核招标品牌，并提前安排对接云思销售负责人李坚。\r\n\r2023/11/1 杨俊杰\r\n\r该项目与华东院余杰沟通了解智能化设计进度提前，预计春节前后就要完成招标图设计，项目由临空负责建设，分为商业和办公，办公由临空自己负责后期运营，商业计划外包运营\r\n\r	SPJ202401-001	2025-04-15	531170	\N	\N	2024-01-15 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
135	张江人工智能岛	2022-11-10	channel_follow	sales	controlled	\N	上海现代建筑设计研究院有限公司	上海瀚网智能科技有限公司	\N	上海壹杰信息技术有限公司	awarded	2025/3/29 12:57:11 杨俊杰\r\n\r【设计院及顾问】：改变成   上海现代建筑设计研究院有限公司\r\n\r\r\n\r2025/2/28 14:50:48 杨俊杰\r\n\r【出货时间预测】：添加   2025年四季度\r\n\r\r\n\r2025/2/21 16:36:50 杨俊杰\r\n\r【完善价格】 1273122\r\n\r45653 李冬\r\n\r类型改变为销售重点 \r\n\r2024/12/27 杨俊杰\r\n\r类型改变为销售重点 \r\n\r45555.6808680556 李冬\r\n\r【完善价格】 1283599\r\n\r2024/9/20 16:20:27 杨俊杰\r\n\r【完善价格】 1283599\r\n\r45534.5383912037 李冬\r\n\r【消息】「」该项目进度缓慢，目前渠道在跟进配套深化方案，按集成商反馈项目要到明年才会启动，与渠道商议推进主设备品牌由摩托罗拉替换为和源\r\n\r2024/8/30 12:55:17 杨俊杰\r\n\r【消息】「」该项目进度缓慢，目前渠道在跟进配套深化方案，按集成商反馈项目要到明年才会启动，与渠道商议推进主设备品牌由摩托罗拉替换为和源\r\n\r45419.5715162037 李冬\r\n\r【消息】「」该项目渠道瑞康反馈他通过奂源现场的关系了解到无线对讲系统中标价格含施工200万+，目前还没决定系统到底如何分配\r\n\r2024/5/7 13:42:59 杨俊杰\r\n\r【消息】「」该项目渠道瑞康反馈他通过奂源现场的关系了解到无线对讲系统中标价格含施工200万+，目前还没决定系统到底如何分配\r\n\r45362.5043634259 李冬\r\n\r该项目据业主反馈壹杰中标，经了解壹杰与另外两家计划共同消化，目前具体如何分配还未定夺\r\n\r2024/3/11 12:06:17 杨俊杰\r\n\r该项目据业主反馈壹杰中标，经了解壹杰与另外两家计划共同消化，目前具体如何分配还未定夺\r\n\r45362.5021990741 李冬\r\n\r「阶段变更」\r\n\r2024/3/11 12:03:10 杨俊杰\r\n\r「阶段变更」\r\n\r45231 李冬\r\n\r项目为办公园区，建筑面积6.6万方，业主方为张江国信安，庄彦负责智能化设计，设计单位：上海院，负责图纸设计，机电顾问：奥雅纳，负责招标技术要求和品牌推荐\r\n\r2023/11/1 杨俊杰\r\n\r项目为办公园区，建筑面积6.6万方，业主方为张江国信安，庄彦负责智能化设计，设计单位：上海院，负责图纸设计，机电顾问：奥雅纳，负责招标技术要求和品牌推荐\r\n\r	CPJ202211-008	2025-03-29	1273122	\N	\N	2022-11-10 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
82	港城广场	2025-03-07	channel_follow	sales	qualified	\N	上海现代建筑设计研究院有限公司	\N	\N	\N	paused	2025/4/13 15:19:10 杨俊杰\r\n\r【设计院及顾问】：改变成   闻锋「上海现代建筑设计研究院有限公司」\r\n\r\r\n\r2025/3/7 11:30:44 杨俊杰\r\n\r【授权编号】：改变成   HY-CPJ202308-003\r\n\r【类型】：改变成   渠道跟进\r\n\r\r\n\r2025/2/21 15:52:23 杨俊杰\r\n\r【当前阶段】：改变成   搁置\r\n\r【当前阶段情况说明】：添加   该项目属于三期，因为资金问题，二期实施进度就有所搁置\r\n\r\r\n\r2024/12/27 杨俊杰\r\n\r类型改变为销售重点 \r\n\r2024/12/6 杨俊杰\r\n\r类型改变为渠道跟进 \r\n\r2024/6/24 16:47:28 杨俊杰\r\n\r【消息】「」该项目属于三期，原先二期代理商福玛已经推进落地，但了解项目实施进度缓慢，业主资金存在问题。三期与闻峰沟通目前没有任何消息，智能化设计完成，具体招标时间不确定，大概率还是原先二期弱电分包单位\r\n\r2023/11/1 杨俊杰\r\n\r上海院闻峰负责智能化设计，配套提供设计方案\r\n\r	CPJ202308-003	2025-04-13	181538	\N	\N	2025-03-07 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
163	静安工人文化宫	2025-01-06	channel_follow	channel	qualified	\N	华东建筑设计研究院有限公司	上海瀚网智能科技有限公司	\N	同方股份有限公司-上海光大会展分公司	awarded	2025/3/3 13:32:51 李华伟\r\n\r【出货时间预测】：改变成   2025年三季度\r\r\n\r\n\r2025/2/21 16:09:02 杨俊杰\r\n\r【当前阶段】：改变成   转移\r\n\r\r\n\r2025/2/21 16:08:51 杨俊杰\r\n\r【当前阶段】：改变成   中标\r\n\r\r\n\r2025/2/21 16:07:43 杨俊杰\r\n\r【当前阶段】：改变成   转移\r\n\r【当前阶段情况说明】：添加   该项目销售负责人改为李华伟，有李华伟配合渠道跟进\r\n\r\r\n\r45699.5797685185 李冬\r\n\r【完善价格】 46322\r\n\r2025/2/11 13:54:52 李华伟\r\n\r【完善价格】 46322\r\n\r45674.4665509259 李冬\r\n\r【出货时间预测】：添加   2025年一季度\r\r\n\r\n\r2025/1/17 11:11:50 李华伟\r\n\r【出货时间预测】：添加   2025年一季度\r\r\n\r\n\r45663.5790509259 李冬\r\n\r【授权编号】：改变成   HY-CPJ202401-007\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r2025/1/6 13:53:50 李华伟\r\n\r【授权编号】：改变成   HY-CPJ202401-007\r\r\n【类型】：添加   渠道跟进\r\r\n\r\n\r45597 李冬\r\n\r【阶段变更】招标中->中标\r\n\r\r\n\r2024/11/1 杨俊杰\r\n\r【阶段变更】招标中->中标\r\n\r\r\n\r45416.5425694444 李冬\r\n\r【阶段变更】招标前->招标中\r\n\r2024/5/4 13:01:18 杨俊杰\r\n\r【阶段变更】招标前->招标中\r\n\r45377.7035648148 李冬\r\n\r该项目与华东院陈允强沟通了解项目计划3月底4月初挂网招标，弱电智能化基本锁定九谷，安排渠道跟进集成商投标。\r\n\r2024/3/26 16:53:08 杨俊杰\r\n\r该项目与华东院陈允强沟通了解项目计划3月底4月初挂网招标，弱电智能化基本锁定九谷，安排渠道跟进集成商投标。\r\n\r45362.4933217593 李冬\r\n\r该项目华东院负责智能化设计，但业主引荐九谷参与配其中，技术规格书和品牌直接由九谷负责，渠道配合\r\n\r2024/3/11 11:50:23 杨俊杰\r\n\r该项目华东院负责智能化设计，但业主引荐九谷参与配其中，技术规格书和品牌直接由九谷负责，渠道配合\r\n\r45362.4920717593 李冬\r\n\r「阶段变更」\r\n\r2024/3/11 11:48:35 杨俊杰\r\n\r「阶段变更」\r\n\r45231 李冬\r\n\r该项目华东院陈允强告知他们负责智能化设计，但业主引荐了上海九谷配套他们做招标文件。计划跟进了解项目设计进度，植入招标品牌，了解招标时间\r\n\r2023/11/1 杨俊杰\r\n\r该项目华东院陈允强告知他们负责智能化设计，但业主引荐了上海九谷配套他们做招标文件。计划跟进了解项目设计进度，植入招标品牌，了解招标时间\r\n\r	CPJ202401-007	2025-03-03	46322	\N	\N	2025-01-06 00:00:00	2025-05-11 00:59:24.476988	15	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
84	上海东方枢纽国际商务合作区综合查验场工程（E3南）	2024-11-26	channel_follow	sales	qualified	\N	华东建筑设计研究院有限公司	上海福玛通信信息科技有限公司	\N	上海市安装工程集团有限公司-第九分公司	embed	2025/4/13 15:09:36 杨俊杰\r\n\r【分销商】：添加   上海淳泊\r\n\r\r\n\r2025/4/3 23:26:16 邹飞\r\n\r【分销商】：添加   上海淳泊\r\r\n\r\n\r2025/2/21 16:25:38 杨俊杰\r\n\r【完善价格】 282640\r\n\r2024/12/27 杨俊杰\r\n\r类型改变为渠道跟进 \r\n\r45653 邹飞\r\n\r类型改变为渠道跟进 \r\n\r2024/12/6 杨俊杰\r\n\r类型改变为渠道管理 \r\n\r45632 邹飞\r\n\r类型改变为渠道管理 \r\n\r2024/11/27 12:15:28 杨俊杰\r\n\r【完善价格】 282642\r\n\r45623.5107407407 邹飞\r\n\r【完善价格】 282642\r\n\r	CPJ202411-013	2025-04-13	282640	\N	\N	2024-11-26 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	1
286	无锡锡东新城高铁商务区地下车行通道工程	2023-04-23	channel_follow	sales	qualified	\N	中邮建技术有限公司无锡分公司	敦力(南京)科技有限公司	\N	中邮建技术有限公司无锡分公司	signed	2024/7/20 14:25:47 范敬\r\n\r【消息】「」代理商已提交批价申请\r\n\r2024/6/22 12:20:23 范敬\r\n\r【消息】「」具体商务谈判中，等待集成商与总包单位合同流程。\r\n\r2024/6/19 18:03:57 范敬\r\n\r【提案采纳】「」:  清单确定，进入商务谈判流程\r\r\n【阶段变更】中标->签约\r\n\r2024/6/11 10:50:18 范敬\r\n\r【消息】「」因集成商合同未签，下单延迟到6月\r\n\r2024/6/11 10:49:37 范敬\r\n\r【阶段变更】招投标->中标\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、目前配合前期系统清单配置、品牌推荐及预算\r\n2、清单中有特殊频段产品\r\n3、10月18日已通过集成商与业主见面，目前根据项目实际情况设计方案后期会有变动，详细要求下周业主会给到集成商。\r\n4、目前新技术要求调整已发出，预计本周末或下周初可收到总包方发出的方案；\r\n5、按照集成商最终确定的方案（因业主资金减少取消了部分功能及施工界面调整，主机因统一要求调整为摩托罗拉）；调整完成了清单。\r\n\r	CPJ202304-007	2024-08-09	60936.75	\N	\N	2023-04-23 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
63	无锡奥林匹克体育产业中心一期项目	2024-04-28	sales_focus	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	南京聚立科技股份有限公司	signed	2025/4/16 范敬\r\n\r「花伟」 敦力(南京)科技有限公司  指导代理商技术进行项目图纸深化。\r\n\r2025/4/14 范敬\r\n\r「花伟」 敦力(南京)科技有限公司  督促支付该项目软件订单款项\r\n\r2025/4/10 范敬\r\n\r「花伟」 敦力(南京)科技有限公司  督促代理商完成软件项目的订单签署机付款。\r\n\r2025/4/2 09:26:42 范敬\r\n\r[阶段变更] ->签约\r\n\r2025/4/2 范敬\r\n\r「花伟」 敦力(南京)科技有限公司  启动并与公司完成了项目软件的直接订单工作\r\n\r2025/4/1 范敬\r\n\r「花伟」 敦力(南京)科技有限公司  补充了相关品牌报审资料\r\n\r2025/3/25 16:21:29 范敬\r\n\r【完善价格】 171020\r\n\r2025/3/25 15:31:45 范敬\r\n\r【完善价格】 421171\r\n\r2025/3/24 11:56:16 范敬\r\n\r【完善价格】 293985\r\n\r2025/2/21 14:45:31 范敬\r\n\r【完善价格】 291433\r\n\r2024/12/1 范敬\r\n\r【出现困难】与施工单位推荐的海能达+侨讯竞争；我们有技术优势，但价格没有竞争力。\r\r\n\r\n\r2024/11/20 12:31:15 范敬\r\n\r【完善价格】 345379\r\n\r2024/9/13 15:13:14 范敬\r\n\r【完善价格】 452964\r\n\r2024/8/18 13:47:47 范敬\r\n\r【消息】「」目前已和中标集成商建立沟通关系，该项目处于一期管线阶段，后续将进入设备招采阶段。\r\r\n【阶段变更】品牌植入->中标\r\n\r2024/4/28 11:24:56 范敬\r\n\r【消息】「」包含一场两馆（体育场、体育馆和游泳馆）及配套商业与全民健身中心，目前为“一场两馆”及中央地库区域。\r\n\r2024/4/28 范敬\r\n\r【提案】:  配合集成商出清单及方案\r\n\r	SPJ202404-005	2025-04-16	122449.05	\N	\N	2024-04-28 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
127	无锡奥林匹克体育产业中心二期项目	2024-09-13	sales_focus	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	南京聚立科技股份有限公司	signed	2025/4/2 09:39:29 范敬\r\n\r[阶段变更] ->签约\r\n\r2025/3/25 16:23:25 范敬\r\n\r【完善价格】 403944\r\n\r2025/3/25 15:35:25 范敬\r\n\r【完善价格】 712203\r\n\r2025/2/21 14:51:34 范敬\r\n\r【完善价格】 719722\r\n\r2024/11/20 12:36:31 范敬\r\n\r【完善价格】 1065122\r\n\r2024/9/13 15:57:41 范敬\r\n\r【完善价格】 1520896\r\n\r	SPJ202409-004	2025-04-02	320491.35	\N	\N	2024-09-13 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
129	上海市松江区巨人科技园B楼项目弱电智能化投标项目	2023-04-20	channel_follow	channel	qualified	\N	\N	敦力(南京)科技有限公司	\N	苏州朗捷通智能科技有限公司	signed	2025/3/31 范敬\r\n\r「花伟」 敦力(南京)科技有限公司  完成批价流程\r\n\r2025/3/28 11:00:33 范敬\r\n\r[阶段变更] ->签约\r\n\r2025/3/20 13:52:20 李博\r\n\r【设计院及顾问】：改变成   浙江省建筑设计院\r\r\n【当前阶段情况说明】：添加   目前设计阶段，项目刚刚土建阶段，持续跟踪中\r\r\n\r\n\r2025/2/14 17:34:56 范敬\r\n\r【出货时间预测】：添加   2025年一季度3月份\r\r\n\r\n\r2025/2/14 17:34:56 花伟\r\n\r【出货时间预测】：添加   2025年一季度3月份\r\r\n\r\n\r2025/2/14 17:23:19 范敬\r\n\r【完善价格】 86873\r\n\r2025/2/14 17:23:19 花伟\r\n\r【完善价格】 86873\r\n\r2025/1/3 范敬\r\n\r类型改变为渠道跟进 \r\n\r2025/1/3 花伟\r\n\r类型改变为渠道跟进 \r\n\r45642 李博\r\n\r类型改变为销售重点 \r\n\r2024/12/16 李华伟\r\n\r类型改变为销售重点 \r\n\r45635 李博\r\n\r类型改变为渠道管理 \r\n\r2024/12/9 李华伟\r\n\r类型改变为渠道管理 \r\n\r45408 李博\r\n\r「拜访」:  接触了EPC分包四川本宇建设，目前他们在确认整体方案和预算品牌，目前接触下来让我们配合出一稿预算，后续跟进情况。\r\n\r2024/4/26 李华伟\r\n\r「拜访」:  接触了EPC分包四川本宇建设，目前他们在确认整体方案和预算品牌，目前接触下来让我们配合出一稿预算，后续跟进情况。\r\n\r	CPJ202404-006	2025-03-31	39092.85	\N	\N	2023-04-20 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
262	南通炜赋华邑酒店项目	2023-06-06	channel_follow	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	南通盛云电子科技有限公司	pre_tender	2024/6/29 11:16:45 范敬\r\n\r【消息】「」项目预计7月开始招标\r\r\n【阶段变更】品牌植入->招标前\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、系统设计、品牌植入，\r\n2、本周与相关人员碰面，目前进入品牌入围阶段，计划24年1月前完成装修方招标工作，智能化包含在装修标段内，目前有13家入围单位；\r\n\r	CPJ202306-001	2024-10-19	502526	\N	\N	2023-06-06 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
73	南京建宁西路过江隧道项目	2022-11-08	sales_focus	sales	qualified	\N	苏交科集团股份有限公司南京设计中心	敦力(南京)科技有限公司	\N	南京中建安装集团	tendering	2025/4/14 范敬\r\n\r「陈华」 敦力(南京)科技有限公司  约见拜访项目机电总包方项目经理（总），沟通项目合作事宜。目前海能达通过南京广电公司在参与该项目，现在争取除350M公安系统外的系统。\r\n\r2024/9/28 范敬\r\n\r【阶段变更】品牌植入->招标中\r\r\n\r\n\r2024/7/20 14:12:52 范敬\r\n\r【消息】「」项目现阶段处于土建结构施工阶段，争取年底完成隧道土建工作；计划2025年转入配套工程的招投标和施工，计划争取2025年底建成。土建总包方中铁十四局。\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n项目已设计完成，目前审图阶段，按和源品牌设计。\r\n\r	SPJ202211-003	2025-04-14	2771088	\N	\N	2022-11-08 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
303	江苏省中医院牛首山分院一期项目智能化系统工程	2022-11-08	channel_follow	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	朗高科技有限公司	signed	2024/4/30 19:59:02 范敬\r\n\r[阶段变更] ->签约\r\n\r2024/4/25 14:06:02 范敬\r\n\r「阶段变更」签约->中标\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、项目整体为EPC方式，目前集成商已中标进场施工。项目现阶段处于管线预埋阶段；品牌已入围。项目后期会交于代理商跟踪。\r\n2、经销商需要低于41%折的价格，并且账期很长；信道机对讲机其他院区是用摩托的，所以可能性不大；总包给的工期为项目12份结束。\r\n3、因资金问题采购时间延迟，预计2024年2月，目前集成商给出的采购价约为面价的40%折，账期无预付，到货后6个月支付货款；如果可以的话预计2024年1月可以批价；\r\n4、因集成商调整，对系统清单做了调整；\r\n\r	CPJ202211-004	2024-04-30	14637.599999999999	\N	\N	2022-11-08 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
154	荡口古镇太师府酒店建设项目智能化工程	2024-01-11	channel_follow	sales	qualified	\N	\N	敦力(南京)科技有限公司	\N	天威虎建设集团有限公司	signed	2025/3/14 16:08:56 范敬\r\n\r[阶段变更] ->签约\r\n\r2025/3/10 15:42:05 范敬\r\n\r【完善价格】 202248\r\n\r2025/3/10 14:51:53 范敬\r\n\r【完善价格】 200808\r\n\r2025/3/10 14:49:00 范敬\r\n\r【完善价格】 114408\r\n\r2025/3/7 14:31:20 范敬\r\n\r【完善价格】 244452\r\n\r2025/2/19 11:25:13 花伟\r\n\r【完善价格】 96450\r\n\r2025/2/14 17:38:04 范敬\r\n\r【出货时间预测】：添加   2025年一季度3月份\r\r\n\r\n\r2025/2/14 17:38:04 花伟\r\n\r【出货时间预测】：添加   2025年一季度3月份\r\r\n\r\n\r2024/7/14 09:55:15 范敬\r\n\r【消息】「」等待集成商通知商务谈判\r\n\r2024/7/14 09:55:15 花伟\r\n\r【消息】「」等待集成商通知商务谈判\r\n\r2024/6/19 17:16:41 范敬\r\n\r【提案】「」:  与集成商技术经理、采购经理沟通确定了方案与清单\r\n\r2024/6/19 17:16:41 花伟\r\n\r【提案】「」:  与集成商技术经理、采购经理沟通确定了方案与清单\r\n\r2024/6/11 12:17:01 范敬\r\n\r【阶段变更】招投标->中标\r\n\r2024/6/11 12:17:01 花伟\r\n\r【阶段变更】招投标->中标\r\n\r2024/3/15 15:20:51 范敬\r\n\r「拜访」  :  汇同南京代理商（敦力）约见预中标集成商（天威虎）沟通项目后续合作事宜。\r\n\r2024/3/15 15:20:51 花伟\r\n\r「拜访」  :  汇同南京代理商（敦力）约见预中标集成商（天威虎）沟通项目后续合作事宜。\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、配合集成商投标；\r\n\r2023/11/1 花伟\r\n\r「阶段变更」\r\r\n1、配合集成商投标；\r\n\r	CPJ202401-006	2025-03-14	85594.73999999998	\N	\N	2024-01-11 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
29	北京新首钢园东南区1612-(775-778--769-783-786)地块项目	2024-04-28	sales_focus	sales	qualified	\N	\N	北京联航迅达通信技术有限公司	\N	中建电子工程有限公司-北京分公司	signed	2025/4/23 范敬\r\n\r「冯子煜」 中建电子工程有限公司-北京分公司  沟通项目实施情况，协助经销商沟通了合同回款事宜。\r\n\r2024/12/7 范敬\r\n\r【阶段变更】中标->签约\r\r\n\r\n\r2024/12/5 11:39:04 范敬\r\n\r【完善价格】 703335\r\n\r2024/12/5 11:38:09 范敬\r\n\r【完善价格】 679263\r\n\r2024/12/4 15:12:03 范敬\r\n\r【完善价格】 1002335\r\n\r2024/12/4 15:10:10 范敬\r\n\r【完善价格】 1004381\r\n\r2024/9/7 14:09:58 范敬\r\n\r【消息】「」集成商计划中秋节前启动招采的招投标工作；9月份完成采购招标工作。\r\n\r2024/8/31 15:31:41 范敬\r\n\r【消息】「」目前正在做招采前期准备工作，安排代理商及配合单位入库。\r\n\r2024/8/18 14:15:32 范敬\r\n\r【消息】「」与集成商沟通招采计划时间\r\n\r2024/7/20 14:24:07 范敬\r\n\r【消息】「」769地块计划竣工时间11月底；\r\n775地块计划竣工时间12月底；\r\n778地块没进场施工，估计要明年开始。\r\n\r2024/7/18 07:51:40 范敬\r\n\r【提案】「」:  等待业主变更流程批复，进行招标。\r\n\r2024/6/29 12:06:40 范敬\r\n\r【消息】「」该项目的目前等待774-779地块招标的结果，确定品牌进行采购招标。\r\n\r2024/6/19 17:21:45 范敬\r\n\r【提案】「」:  整个项目划分为775-778-769地块和774-779地块两个标段，本项目只包含775-778-769地块的天馈、传输及对讲机产品。\r\n\r2024/6/11 11:59:33 范敬\r\n\r【消息】「」目前只保留775-778-769三个地块的内容，与774-779地块合用一个系统。\r\r\n【阶段变更】品牌植入->中标\r\n\r2024/5/17 13:34:27 范敬\r\n\r【提案】「」:  根据项目要求调整方案。\r\n\r2024/4/28 10:09:00 范敬\r\n\r【提案】「」:  根据要求，配合集成商提交方案\r\r\n【阶段变更】品牌植入->\r\n\r	SPJ202404-004	2025-04-23	302434.05	\N	\N	2024-04-28 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	2
297	阿里江苏总部园区B地块	2022-11-08	channel_follow	sales	qualified	\N	南京长江都市建筑设计院	敦力(南京)科技有限公司	\N	\N	tendering	2024/4/25 14:18:11 范敬\r\n\r「阶段变更」招标中->品牌植入\r\n\r2024/4/25 14:18:11 花伟\r\n\r「阶段变更」招标中->品牌植入\r\n\r2023/11/1 范敬\r\n\r「阶段变更」\r\r\n1、项目设计中，目前和源通信产品配合设计。\r\n2、本周拜访了业主在项目上的负责人，目前对于对讲系统的政策主机品牌为摩托罗拉唯一指定，其他不做指定；集成商为2021年选中集成商库中选择；\r\n\r2023/11/1 花伟\r\n\r「阶段变更」\r\r\n1、项目设计中，目前和源通信产品配合设计。\r\n2、本周拜访了业主在项目上的负责人，目前对于对讲系统的政策主机品牌为摩托罗拉唯一指定，其他不做指定；集成商为2021年选中集成商库中选择；\r\n\r	CPJ202211-003	2024-06-24	415910	\N	\N	2022-11-08 00:00:00	2025-05-11 00:59:24.476988	16	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	16	1
227	联影智慧医疗园	2022-12-12	channel_follow	sales	controlled	\N	\N	上海鑫桉信息工程有限公司	\N	上海云思智慧信息技术有限公司	signed	2024/12/27 杨俊杰\r\n\r【阶段变更】中标->签约\r\n\r\r\n\r2024/8/30 12:43:14 杨俊杰\r\n\r【消息】「」该项目配套云思推进信道机及对讲机锁定和源品牌，按云思现场反馈现阶段在和业主确认方案和所选品牌，并和云思商议在锁定品牌的情况，增补对讲机数量\r\n\r2024/8/18 12:46:00 杨俊杰\r\n\r【消息】「」云思中标，项目经理已经进场，目前主要在深化方案确认，渠道福玛在跟进对接。商务方面根据云思内部业务流程，需根据投标报价优惠一轮价格给到销售，商务方面根据现场沟通反馈的实施进度，预计今年年底会发起采购流程\r\n\r跟进记录 杨俊杰\r\n\r【阶段变更】招标中->中标\r\n\r2024/3/20 16:38:36 杨俊杰\r\n\r「阶段变更」\r\r\n该项目招标，渠道配合提供投标\r\n\r2023/11/1 杨俊杰\r\n\r项目位于长宁临空，总建设面积约17万平方米。云思与建筑合作，负责智能化设计\r\n\r	CPJ202212-002	2024-12-27	359462.25	\N	\N	2022-12-12 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
134	虹口区117街坊HK366-01地块\r\n新建学校项目（不含桩基）	2024-08-20	channel_follow	sales	controlled	\N	\N	上海瀚网智能科技有限公司	\N	上海仪电鑫森科技发展有限公司	awarded	2025/3/29 12:58:06 杨俊杰\r\n\r【出货时间预测】：改变成   2026年一季度\r\n\r\r\n\r2025/2/28 14:43:54 杨俊杰\r\n\r【出货时间预测】：改变成   2025年三季度\r\n\r\r\n\r2025/2/21 16:37:48 杨俊杰\r\n\r【完善价格】 176058\r\n\r45555.6761342593 李冬\r\n\r【完善价格】 180358\r\n\r2024/9/20 16:13:38 杨俊杰\r\n\r【完善价格】 180358\r\n\r45555.6737037037 李冬\r\n\r【完善价格】 176034\r\n\r2024/9/20 16:10:08 杨俊杰\r\n\r【完善价格】 176034\r\n\r45540.5781018519 李冬\r\n\r【消息】「」该项目渠道反馈目前在配合仪电鑫森初步深化，深化方案需大总包及设计院确认。项目整体进度较早，现在还在打桩，项目计划2026年9月开学，预计明年弱电才会启动施工\r\r\n类型改变为  渠道跟进 \r\n\r2024/9/5 13:52:28 杨俊杰\r\n\r【消息】「」该项目渠道反馈目前在配合仪电鑫森初步深化，深化方案需大总包及设计院确认。项目整体进度较早，现在还在打桩，项目计划2026年9月开学，预计明年弱电才会启动施工\r\r\n类型改变为  渠道跟进 \r\n\r45540.5775 李冬\r\n\r类型改变为  销售重点 \r\n\r2024/9/5 13:51:36 杨俊杰\r\n\r类型改变为  销售重点 \r\n\r45534.5524189815 李冬\r\n\r【消息】「」该项目渠道反馈仪电鑫森中标，但项目进度较早，还在土建阶段，他们与仪电鑫森沟通确认设备采购需要到明年\r\r\n【阶段变更】招标中->中标\r\n\r2024/8/30 13:15:29 杨俊杰\r\n\r【消息】「」该项目渠道反馈仪电鑫森中标，但项目进度较早，还在土建阶段，他们与仪电鑫森沟通确认设备采购需要到明年\r\r\n【阶段变更】招标中->中标\r\n\r45441.6149189815 李冬\r\n\r【消息】「」与渠道建议对讲机品牌替换为和源，经确认目前品牌已经替换成功，将摩托罗拉、海能达、建伍改为和源、瀚网及福玛。项目于下月开标，基本仪电鑫森中标\r\n\r2024/5/29 14:45:29 杨俊杰\r\n\r【消息】「」与渠道建议对讲机品牌替换为和源，经确认目前品牌已经替换成功，将摩托罗拉、海能达、建伍改为和源、瀚网及福玛。项目于下月开标，基本仪电鑫森中标\r\n\r45436 李冬\r\n\r渠道反馈该项目仪电鑫森范荃报备，配合清单报价，品牌按其所述为摩托、建伍及海能达，与其沟通建议替换为和源\r\n\r2024/5/24 杨俊杰\r\n\r渠道反馈该项目仪电鑫森范荃报备，配合清单报价，品牌按其所述为摩托、建伍及海能达，与其沟通建议替换为和源\r\n\r	CPJ202408-009	\N	176058	\N	\N	2024-08-20 00:00:00	2025-05-11 00:59:24.476988	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
416	台泥公亮大楼酒店	2024-03-29	channel_follow	sales	qualified	\N	\N	浙江航博智能工程有限公司	\N	浙江微风智能科技有限公司	signed	2025/4/8 李博\r\n\r「田经理」 浙江微风智能科技有限公司  台泥公亮项目签约与供货节奏跟踪，与金牌代理商的协议完成，项目备货启动\r\n\r2025/4/6 09:59:23 李华伟\r\n\r[阶段变更] ->签约\r\n\r2025/4/6 09:34:22 李华伟\r\n\r【完善价格】 129189\r\n\r2025/3/31 15:22:19 李博\r\n\r【完善价格】 129189\r\n\r2025/3/24 10:55:19 李华伟\r\n\r【当前阶段】：改变成   中标\r\r\n\r\n\r2025/3/24 10:55:08 李华伟\r\n\r【当前阶段情况说明】：添加   目前集成商中标，代理商航博配合沟通对讲机品牌换成和源产品，预计近期确认合约进行批价。\r\r\n\r\n\r2025/3/24 10:00:03 李华伟\r\n\r【出货时间预测】：改变成   2025年二季度\r\r\n\r\n\r2025/3/21 15:29:04 李华伟\r\n\r【完善价格】 129191\r\n\r2025/3/21 10:54:08 李博\r\n\r【当前阶段】：改变成   中标\r\r\n【当前阶段情况说明】：添加   项目清单已确认，进入议价环节，客户采购对接沟通良好，即将敲定并走入签约环节\r\r\n\r\n\r2025/3/3 13:31:59 李华伟\r\n\r【出货时间预测】：添加   2025年一季度\r\r\n\r\n\r45380 李博\r\n\r「提案」  :  配合设计方案，项目只有4层楼，按照常规项目全套和源产品设计。\r\n\r2024/3/29 李华伟\r\n\r「提案」  :  配合设计方案，项目只有4层楼，按照常规项目全套和源产品设计。\r\n\r	CPJ202403-012	2025-04-08	0	\N	\N	2024-03-29 00:00:00	2025-06-03 02:22:36.22584	23	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	15	2
415	重庆芯联微电子	2025-02-28	channel_follow	channel		\N	\N	重庆大鹏鸟科技有限公司	\N	\N	awarded	2025/4/9 邹飞\r\n\r\n「唐明勇」 重庆大鹏鸟科技有限公司  FAB1图纸改动完成，现场确认中\r\n\r\n2025/4/3 23:20:44 邹飞\r\n\r\n【类型】：添加   渠道跟进\r\n\r\n\r\n\r\n2025/4/2 邹飞\r\n\r\n「唐明勇」 重庆大鹏鸟科技有限公司  由于现场FAB1桥架有变动，重新设计图纸及确认设备数量\r\n\r\n2025/3/29 13:29:23 郭小会\r\n\r\n[阶段变更] ->签约\r\n\r\n2025/3/21 14:20:32 郭小会\r\n\r\n【完善价格】 310851\r\n\r\n2025/3/8 10:02:59 郭小会\r\n\r\n【经销商】：改变成   重庆大鹏鸟科技有限公司\r\n\r\n\r\n\r\n2025/3/8 10:02:41 郭小会\r\n\r\n【经销商】：改变成   福淳智能科技(四川)有限公司\r\n\r\n\r\n\r\n2025/3/8 10:02:01 郭小会\r\n\r\n【出货时间预测】：添加   2025年一季度3月份\r\n\r\n\r\n\r\n2025/2/28 11:50:50 邹飞\r\n\r\n【授权编号】：添加   HY-CPJ202405-014\r\n\r\n\r\n\r\n2025/2/7 09:53:20 郭小会\r\n\r\n【完善价格】 493711\r\n\r\n2025/2/7 09:03:15 郭小会\r\n\r\n【当前阶段】：改变成   中标\r\n\r\n【当前阶段情况说明】：添加   项目重启，大鹏鸟配合的重庆赛迪中标\r\n\r\n\r\n\r\n2025/2/6 10:52:49 郭小会\r\n\r\n【经销商】：改变成   重庆大鹏鸟科技有限公司\r\n\r\n【授权编号】：改变成   HY-CPJ202405-014\r\n\r\n【类型】：改变成   渠道跟进\r\n\r\n\r\n\r\n	CPJ202405-014	2025-04-09	0	yes	\N	2025-02-28 00:00:00	2025-04-09 00:00:00	24	f	\N	\N	\N	f	2025-05-24 05:20:56.993177	\N	13	1
108	浦江永久实验室	2024-05-20	channel_follow	sales	controlled	\N	同济大学建筑设计研究院（集团）有限公司	上海瀚网智能科技有限公司	\N	上海奔逸智能科技有限公司	awarded	2025/4/8 杨俊杰\r\n\r\n「徐良健」 上海奔逸智能科技有限公司  与代理商一同拜访奔逸总经理徐良健，沟通浦江永久实验室，判断代理商与集成商商务合作关系。目前项目建筑结构部分还未封顶，现场仅在做管线预埋，设备进场预计在今年三季度，整体交付要到明年。商务方面给与总价控制范围，基本双方合作没有太大问题\r\n\r\n2025/3/28 15:52:32 李冬\r\n\r\n【面价金额】：改变成   855371\r\n\r\n\r\n\r\n2025/2/28 14:41:59 杨俊杰\r\n\r\n【出货时间预测】：添加   2025年四季度\r\n\r\n\r\n\r\n45704.6501967593 李冬\r\n\r\n【设计院及顾问】：改变成   唐平「同济大学建筑设计研究院（集团）有限公司」\r\n\r\n\r\n\r\n2025/2/16 15:36:17 杨俊杰\r\n\r\n【设计院及顾问】：改变成   唐平「同济大学建筑设计研究院（集团）有限公司」\r\n\r\n\r\n\r\n45653 李冬\r\n\r\n类型改变为销售重点 \r\n\r\n2024/12/27 杨俊杰\r\n\r\n类型改变为销售重点 \r\n\r\n45632 李冬\r\n\r\n类型改变为渠道管理 \r\n\r\n2024/12/6 杨俊杰\r\n\r\n类型改变为渠道管理 \r\n\r\n45555.6786458333 李冬\r\n\r\n【完善价格】 1169105\r\n\r\n2024/9/20 16:17:15 杨俊杰\r\n\r\n【完善价格】 1169105\r\n\r\n45534.5502314815 李冬\r\n\r\n【阶段变更】招标前->中标\r\n\r\n\r\n\r\n2024/8/30 13:12:20 杨俊杰\r\n\r\n【阶段变更】招标前->中标\r\n\r\n\r\n\r\n45534.5495486111 李冬\r\n\r\n【消息】「」该项目渠道反馈华融以上安九分的身份中标，目前在对外询价复核成本，项目进度还早，土建还未完成，项目预计明年才会启动设备采购\r\n\r\n2024/8/30 13:11:21 杨俊杰\r\n\r\n【消息】「」该项目渠道反馈华融以上安九分的身份中标，目前在对外询价复核成本，项目进度还早，土建还未完成，项目预计明年才会启动设备采购\r\n\r\n45441.640462963 李冬\r\n\r\n【消息】「」与渠道沟通了解项目基本上安中标，项目负责人余智飞，另外上安提到业主引荐一家弱电单位华融，我们的系统由他们负责采购\r\n\r\n2024/5/29 15:22:16 杨俊杰\r\n\r\n【消息】「」与渠道沟通了解项目基本上安中标，项目负责人余智飞，另外上安提到业主引荐一家弱电单位华融，我们的系统由他们负责采购\r\n\r\n45432 李冬\r\n\r\n与上安梁晓君沟通了解品牌目前按我们所推动的方向，和源围标，主设备品牌入围，项目预计本月底下月初招标，弱电参与单位按上安反馈他们全部掌控\r\n\r\n2024/5/20 杨俊杰\r\n\r\n与上安梁晓君沟通了解品牌目前按我们所推动的方向，和源围标，主设备品牌入围，项目预计本月底下月初招标，弱电参与单位按上安反馈他们全部掌控\r\n\r\n	CPJ202405-009	2025-08-10	1169105	\N	\N	2024-05-20 00:00:00	2025-06-06 10:31:44.76686	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
202	佛山平安中心建设项目	2024-09-13	sales_focus	sales	qualified	\N	\N	上海瀚网智能科技有限公司	\N	深圳达实智能股份有限公司	quoted	2025/2/14 16:02:16 周裔锦\r\n\r\n【系统集成商】：改变成   中通服咨询设计研究院有限公司\r\n\r\n\r\n\r\n2025/2/10 17:40:20 周裔锦\r\n\r\n【当前阶段】：改变成   中标\r\n\r\n【当前阶段情况说明】：改变成   中通服已中标，目前在核对采购成本。\r\n\r\n\r\n\r\n2024/10/27 周裔锦\r\n\r\n【出现困难】投标结果还没有出来。\r\n\r\n\r\n\r\n2024/10/27 周裔锦\r\n\r\n【出现困难】三局智能说投标时竞争太激烈，最后没有中标。\r\n\r\n\r\n\r\n2024/10/9 18:14:05 周裔锦\r\n\r\n【完善价格】 331156\r\n\r\n2024/10/8 周裔锦\r\n\r\n【阶段变更】招标前->招标中\r\n\r\n\r\n\r\n2024/9/13 周裔锦\r\n\r\n【出现困难】本项目配合三局智能和中通服两家报价投标，当前让瀚网张兴配合三局智能报价，我已按照中通服清单报价358968元。\r\n\r\n\r\n\r\n	SPJ202409-005	2025-06-01	494471	\N	\N	2024-09-13 00:00:00	2025-06-08 22:27:43.444001	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	2
55	深圳国际综合部物流枢纽中心	2024-08-30	sales_focus	sales	unqualified	深圳市深国铁路物流发展有限公司	广东省电信规划设计院有限公司	上海瀚网智能科技有限公司	\N	\N	embed	2025/4/18 09:29:04 周裔锦\r\n\r【完善价格】 2787052\r\n\r2025/4/11 11:52:29 周裔锦\r\n\r【完善价格】 2626909\r\n\r2025/4/11 11:39:24 周裔锦\r\n\r【完善价格】 55605\r\n\r2025/4/8 周裔锦\r\n\r「肖阳陵」 深圳市深国铁路物流发展有限公司  张兴配合一同拜访，现场根据客户点位图配置清单，整个系统报价暂定在390万，暂定为4组通话需求。如果业主方要求使用B1线缆，或者线缆套管，价格会增加。\r\n将深圳万睿的销售经理李应介绍给业主，李应做过深国际的项目，他表示有一定把握能操盘下来。\r\n当前配合设计方给出方案的工作已经取得业主方认可，加上系统预算不占比过大，设计院透露业主把无线对讲系统作为智能化的重点系统，但目前还是有运营商来推公网对讲，所以需要推动尽快上会争取拍板建设，解除后顾之忧。\r\n\r2025/4/3 周裔锦\r\n\r「肖阳陵」 深圳市深国铁路物流发展有限公司  本周设计院还没有把按照我方给我设计规则出的点位图，下周再约，到时候和设计院一起过点位图。\r\n\r2025/3/24 10:51:41 周裔锦\r\n\r【分销商】：添加   上海瑞康\r\r\n\r\n\r2025/3/24 10:51:27 周裔锦\r\n\r【当前阶段】：改变成   品牌植入\r\r\n【当前阶段情况说明】：改变成   目前项目已经由省院中标设计，业主方已同意先设计，后再根据整体成本讨论是否保留建设。\r\r\n\r\n\r2025/3/8 10:46:33 周裔锦\r\n\r【当前阶段】：改变成   发现\r\r\n\r\n\r2025/3/8 10:46:22 周裔锦\r\n\r【设计院及顾问】：改变成   广东省电信规划设计院有限公司\r\r\n\r\n\r2025/2/28 17:55:53 周裔锦\r\n\r【设计院及顾问】：添加   广东省建筑设计研究院有限公司\r\r\n【当前阶段】：改变成   品牌植入\r\r\n【经销商】：添加   上海瀚网智能科技有限公司\r\r\n【当前阶段情况说明】：改变成   目前项目已经由省院中标设计。\r\r\n\r\n\r2025/2/21 13:29:42 周裔锦\r\n\r【当前阶段】：改变成   发现\r\r\n【当前阶段情况说明】：添加   设计招标阶段，属于项目发现。\r\r\n\r\n\r	SPJ202408-008	2025-04-18	2787052	\N	\N	2024-08-30 00:00:00	2025-06-08 22:21:28.544707	17	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	17	1
101	国际商务合作区E2联检及商务酒店综合体(1366-E2)	2025-03-07	channel_follow	channel	controlled	\N	\N	上海福玛通信信息科技有限公司	\N	上海市安装工程集团有限公司-第九分公司	awarded	2025/4/10 14:22:39 杨俊杰\r\n\r【出货时间预测】：添加   2025年二季度\r\n\r【当前阶段】：改变成   招标中\r\n\r【分销商】：添加   上海淳泊\r\n\r【经销商】：添加   上海福玛通信信息科技有限公司\r\n\r【当前阶段情况说明】：添加   该项目分为联检及酒店两个部分，其中联检目前上安九分参与建工平台投标，预计5-6月份完成投标，并与总包建工合同签订，酒店预计本月底启动投标，预计合同签订时间与联检相差不会太多。现场反馈项目实施进度较急，联检及酒店需要提前协助，把天馈有关隐蔽工程提前完成。现阶段深化方案基本确认，价格与上安采购有过初步沟通和确认，代理商在跟进并提前配合执行\r\n\r\r\n\r2025/4/9 杨俊杰\r\n\r「张东伟」 上海市安装工程集团有限公司-第九分公司  该项目分为联检及酒店两个部分，其中联检目前上安九分参与建工平台投标，预计5-6月份完成投标，并与总包建工合同签订，酒店预计本月底启动投标，预计合同签订时间与联检相差不会太多。现场反馈项目实施进度较急，联检及酒店需要提前协助，把天馈有关隐蔽工程提前完成。现阶段深化方案基本确认，价格与上安采购有过初步沟通和确认，代理商在跟进并提前配合执行\r\n\r2025/3/7 11:32:12 杨俊杰\r\n\r【授权编号】：改变成   HY-CPJ202406-017\r\n\r【类型】：改变成   渠道跟进\r\n\r\r\n\r2025/2/21 17:11:13 杨俊杰\r\n\r【完善价格】 383859\r\n\r2024/12/27 杨俊杰\r\n\r类型改变为渠道跟进 \r\n\r2024/12/6 杨俊杰\r\n\r类型改变为渠道管理 \r\n\r2024/6/17 杨俊杰\r\n\r渠道陈刘祥反馈该项目上安参与项目设计，配套提供设计方案，并与上安沟通他们已经帮助提交系统品牌，主设备为摩托罗拉、海能达及和源，天馈分布为和源、瀚网及淳泊。经了解设计院为华东院，张航负责智能化设计。计划通过张航了解项目情况，跟踪招标品牌\r\n\r	CPJ202406-017	2025-04-10	383859	\N	\N	2025-03-07 00:00:00	2025-06-09 03:06:43.649579	14	f	\N	\N	\N	t	2025-05-24 05:20:56.993177	\N	14	2
\.


--
-- TOC entry 4081 (class 0 OID 19737)
-- Dependencies: 306
-- Data for Name: purchase_order_details; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.purchase_order_details (id, order_id, product_id, product_name, product_model, product_desc, brand, quantity, unit, unit_price, discount, total_price, received_quantity, notes) FROM stdin;
\.


--
-- TOC entry 4037 (class 0 OID 19461)
-- Dependencies: 262
-- Data for Name: purchase_orders; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.purchase_orders (id, order_number, company_id, order_type, order_date, expected_date, status, total_amount, total_quantity, currency, payment_terms, delivery_address, description, created_by_id, approved_by_id, approved_at, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4083 (class 0 OID 19743)
-- Dependencies: 308
-- Data for Name: quotation_details; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.quotation_details (id, quotation_id, product_name, product_model, product_desc, brand, unit, quantity, discount, market_price, unit_price, total_price, product_mn, created_at, updated_at, implant_subtotal) FROM stdin;
5190	427	馈电定向耦合器	MADC-6	频率范围：351-470MHz 承载功率：100W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信		20	1	246	246	4920	HYCCF34Y	2025-01-03 00:00:00	2025-05-09 07:38:14.235912	4920
5191	427	馈电功率分配器	MAPD-2	频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信		22	1	208	208	4576	HYCDF24Y	2025-01-03 00:00:00	2025-05-09 07:38:14.236153	4576
5192	427	智能室内全向吸顶天线	MA11	频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65 应用：指示灯	和源通信		43	1	208	208	8944	HYAIOCL4Y	2025-01-03 00:00:00	2025-05-09 07:38:14.236383	8944
5193	427	数字智能光纤远端直放站	DRFT-BDA410/M	频率范围：410-414/420-424MHz 数字带宽：≤4M 输出：10W 数字型 功能：触摸屏/网讯平台 扩展：馈电	和源通信	套	2	1	47917	47917	95834	HYR3DI340	2025-01-03 00:00:00	2025-05-09 07:38:14.236617	95834
5194	427	馈电模组	FDPower400	馈电功能模组    需搭配可扩展远端机;内置远端内向天馈提供电力;	和源通信	套	2	1	1583	1583	3166	HYGF20000	2025-01-03 00:00:00	2025-05-09 07:38:14.236838	3166
1	694	智能信道交换机	S1024	端口数量：24个  网线类型：3、4、5类双绞线   防雷等级：4级（6KV） 用途：CP、IP、LCP、系统监控配件/信道机	华三	套	1	1	780	780	780	OBJSVOTXQ01	2025-06-13 09:32:48.664658	2025-06-13 09:32:48.66466	0
2	694	馈电功率分配器	MAPD-2	频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信	套	1	1	208	208	208	HYCDF24Y	2025-06-13 09:32:48.664661	2025-06-13 09:32:48.664661	208
3	694	分路器	E-JF150-4	频率范围：130-170MHz 单端口承载功率：1W;插入损耗：≤7.0dB接入端口数量：4;安装方式：机柜式;	和源通信	套	1	1	2913	2913	2913	HYMJC4010	2025-06-13 09:32:48.664662	2025-06-13 09:32:48.664662	2913
\.


--
-- TOC entry 4019 (class 0 OID 18338)
-- Dependencies: 244
-- Data for Name: quotations; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.quotations (id, quotation_number, project_id, contact_id, amount, project_stage, project_type, created_at, updated_at, owner_id, approval_status, approved_stages, approval_history, is_locked, lock_reason, locked_by, locked_at, confirmed_at, confirmation_badge_color, product_signature, confirmed_by, confirmation_badge_status, implant_total_amount) FROM stdin;
693	QU202506-016	623	\N	419480	\N	\N	2025-06-13 07:19:01.374683+00	2025-06-13 07:19:01.373801	15	pending	[]	[]	f	\N	\N	\N	\N	\N	6a8671998b4377c4378ab9afbc88c2db	\N	none	419480
422	QU202503-042	2	\N	241671	awarded	\N	2025-03-03 00:00:00+00	2025-06-05 06:17:57.503324	13	pending	\N	\N	f	\N	\N	\N	\N	\N	dfa5df5aa0c8d2f3380293ab491b6b58	\N	none	124171
686	QU202506-009	612	\N	182317	pre_tender	channel_follow	2025-06-05 06:15:12.855965+00	2025-06-05 06:15:12.853988	13	pending	[]	[]	f	\N	\N	\N	\N	\N	eb719304e098f91062e84aa9169bb7df	\N	none	182317
575	QU202503-053	161	\N	238478	pre_tender	channel_follow	2025-03-06 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	435974
427	QU202501-026	99	\N	117440	tendering	\N	2025-01-02 00:00:00+00	2025-05-09 08:00:00	13	pending	{}	{}	f	\N	\N	\N	\N	\N	\N	\N	none	117440
685	QU202506-008	611	\N	8814755.6	embed	sales_focus	2025-06-04 02:52:25.316819+00	2025-06-12 03:02:21.25766	16	pending	[]	[]	f	\N	\N	\N	\N	\N	3f1462604a826c51a0dffea5aa34b5a0	\N	none	4080460
692	QU202506-015	622	\N	296909	\N	\N	2025-06-13 07:14:26.30098+00	2025-06-13 07:14:26.300254	15	pending	[]	[]	f	\N	\N	\N	\N	\N	48df929e80a9a1b28a36947e3781104d	\N	none	296909
561	QU202503-050	31	\N	67375	quoted	channel_follow	2025-03-19 00:00:00+00	2025-06-06 01:37:12.122805	17	pending	\N	\N	f	\N	\N	\N	2025-06-06 07:29:44.940066	#28a745	ccfc6b1d041a81e1cc9f28ccc7c3cfde	12	confirmed	67376
529	QU202406-021	101	\N	383859	awarded	channel_follow	2024-06-16 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	431628
694	QU202506-017	624	\N	3901	quoted	sales_focus	2025-06-13 09:32:48.660164+00	2025-06-13 09:32:48.65869	15	pending	[]	[]	t	批价审批流程进行中	5	2025-06-13 09:42:00.502006	2025-06-13 09:41:20.422732	#28a745	307bc76f089edfde58923410a38d4f0d	5	confirmed	3121
341	QU202502-023	30	\N	43743	signed	sales_focus	2025-02-23 00:00:00+00	2025-05-28 06:25:38.039345	16	pending	\N	\N	f	\N	\N	\N	2025-06-06 01:52:56.123976	#28a745	8297dbcc46b1e176622f6f21fdae60a6	12	confirmed	43187
688	QU202506-011	618	\N	26920	awarded	channel_follow	2025-06-12 02:40:13.963626+00	2025-06-12 02:40:13.962477	13	pending	[]	[]	f	\N	\N	\N	\N	\N	3e940eb050f11bc3d39f54a7386b0615	\N	none	26920
687	QU202506-010	615	\N	95630.85	quoted	channel_follow	2025-06-06 02:38:15.216755+00	2025-06-12 04:27:22.431011	14	pending	[]	[]	f	\N	\N	\N	2025-06-09 11:29:07.145794	#28a745	9d5c641fb817100f16b60b242370b758	12	confirmed	268907
689	QU202506-012	619	\N	326937	\N	\N	2025-06-12 15:24:30.183407+00	2025-06-12 15:24:30.182824	17	pending	[]	[]	f	\N	\N	\N	\N	\N	f5d3f2eaa79aae43fc54b14366f49881	\N	none	326937
640	QU202505-050	539	\N	234896	\N	\N	2025-05-16 10:12:42.247888+00	2025-05-16 10:12:42.247437	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	273780
641	QU202505-051	537	\N	360422	\N	\N	2025-05-16 10:16:45.140973+00	2025-05-16 10:16:45.140453	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	404495
656	QU202505-066	594	\N	261096	pre_tender	channel_follow	2025-05-22 07:15:01.121545+00	2025-05-22 07:15:11.487336	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	261096
665	QU202505-075	553	\N	140127	\N	\N	2025-05-28 08:26:01.276929+00	2025-05-28 08:26:01.276361	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	140127
663	QU202505-073	568	\N	225718	tendering	channel_follow	2025-05-28 07:56:37.432055+00	2025-05-28 07:56:37.431639	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	225718
607	QU202505-018	542	\N	602561	\N	\N	2025-05-16 06:21:43.33976+00	2025-05-29 07:49:50.305304	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	587513
365	QU202311-073	194	\N	591916	embed	sales_focus	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	591916
454	QU202405-017	6	\N	190200	signed	channel_follow	2024-05-16 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	190200
461	QU202503-046	153	\N	203117	quoted	channel_follow	2025-03-12 00:00:00+00	2025-05-30 03:30:22.427675	15	pending	\N	\N	f	\N	\N	\N	2025-06-06 01:51:21.798781	#28a745	ebc81b75c08660ad2b43c4def113afab	12	confirmed	203117
428	QU202407-017	100	\N	2141633	quoted	sales_focus	2024-07-16 00:00:00+00	2025-05-29 01:42:23.979837	13	quoted_approved	["quoted_approved"]	[{"action": "approve", "stage": "quoted", "approval_status": "quoted_approved", "approver_id": 12, "approver_name": "liuwei", "comment": "\\u4ea7\\u54c1\\u89c4\\u683c\\u6ee1\\u8db3\\u9879\\u76ee\\u4f7f\\u7528\\u9700\\u6c42\\u3002", "timestamp": "2025-06-04T06:49:27.538554", "approval_instance_id": 26}]	f	\N	\N	\N	2025-06-06 05:01:37.847516	#28a745	fe4f3bee066cf78687658ab6f92862af	12	confirmed	2141633
580	QU202502-042	202	\N	494471	quoted	sales_focus	2025-02-13 00:00:00+00	2025-06-04 08:49:59.794965	17	pending	\N	\N	f	\N	\N	\N	2025-06-06 07:32:06.595296	#28a745	492a914154d7faafee1f85b8ca5a1931	12	confirmed	494471
683	QU202506-006	609	\N	62376	quoted	channel_follow	2025-06-04 01:31:18.182616+00	2025-06-04 01:34:02.101517	16	pending	[]	[]	f	\N	\N	\N	2025-06-06 09:06:04.81932	#28a745	9840da9441ecb54e032c098f02d0570d	12	confirmed	62376
664	QU202505-074	549	\N	162184	awarded	sales_focus	2025-05-28 08:22:47.853219+00	2025-05-28 08:22:47.852758	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	162184
690	QU202506-013	620	\N	120808	\N	\N	2025-06-12 15:36:18.665101+00	2025-06-12 15:36:18.664489	17	pending	[]	[]	f	\N	\N	\N	\N	\N	bd7227ed8ea08a8baef19615acf24a5d	\N	none	120808
603	QU202505-014	531	\N	36198	quoted	channel_follow	2025-05-16 04:45:11.369688+00	2025-05-16 04:45:11.369245	16	pending	\N	\N	f	\N	\N	\N	2025-06-06 09:06:54.374699	#28a745	fec4b86c2dd3c278a514f58ad45a682f	12	confirmed	36198
602	QU202505-013	529	\N	68846	quoted	channel_follow	2025-05-16 04:30:25.152019+00	2025-05-16 04:30:25.151408	16	pending	\N	\N	f	\N	\N	\N	2025-06-06 09:07:31.5697	#28a745	fec4b86c2dd3c278a514f58ad45a682f	12	confirmed	68846
599	QU202505-010	523	\N	117402	quoted	channel_follow	2025-05-16 03:59:55.294976+00	2025-05-16 08:02:05.143497	16	pending	\N	\N	f	\N	\N	\N	2025-06-06 09:08:05.216894	#28a745	99a3be602a04996b131b600730e30582	12	confirmed	117402
691	QU202506-014	621	\N	426	quoted	channel_follow	2025-06-13 02:57:22.311151+00	2025-06-13 02:57:22.310355	18	pending	[]	[]	t	批价审批流程进行中	18	2025-06-13 08:37:55.175876	2025-06-13 02:59:55.489616	#28a745	2cee90d6d332930f96d33560f5728152	12	confirmed	426
593	QU202505-004	514	\N	2454599	\N	\N	2025-05-15 12:39:10.591885+00	2025-05-15 12:39:10.589375	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	2454599
608	QU202505-019	536	\N	118460	\N	\N	2025-05-16 07:17:21.687034+00	2025-05-16 07:17:21.686369	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	118744
609	QU202505-020	555	\N	162921	\N	\N	2025-05-16 07:20:31.894712+00	2025-05-16 07:20:31.894197	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	162921
642	QU202505-052	585	\N	474745	\N	\N	2025-05-18 13:10:24.695411+00	2025-05-18 13:10:24.692585	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	474745
646	QU202505-056	580	\N	992765	awarded	sales_focus	2025-05-18 13:49:23.66826+00	2025-05-19 01:35:43.238747	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	992765
657	QU202505-067	595	\N	200462	awarded	channel_follow	2025-05-22 07:35:06.978646+00	2025-05-22 07:35:26.675179	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	200462
644	QU202505-054	582	\N	99271	awarded	channel_follow	2025-05-18 13:33:39.161171+00	2025-05-22 07:36:18.190774	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	99271
643	QU202505-053	584	\N	532329	pre_tender	channel_follow	2025-05-18 13:24:41.567715+00	2025-05-22 07:37:16.168719	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	532329
645	QU202505-055	581	\N	86129	tendering	channel_follow	2025-05-18 13:39:19.866019+00	2025-05-22 07:38:04.984522	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	86129
647	QU202505-057	579	\N	45610	awarded	channel_follow	2025-05-18 13:52:42.653751+00	2025-05-22 07:38:48.014	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	71916
649	QU202505-059	574	\N	37338	tendering	channel_follow	2025-05-18 14:02:56.586884+00	2025-05-22 07:39:44.44572	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	37338
672	QU202505-082	64	\N	3371652	\N	\N	2025-05-30 06:11:07.589077+00	2025-05-30 06:11:07.588246	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	3371652
673	QU202505-083	41	\N	77435	\N	\N	2025-05-30 06:12:55.696301+00	2025-05-30 06:12:55.69574	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	77435
674	QU202505-084	602	\N	7008	\N	\N	2025-05-30 06:21:45.884065+00	2025-05-30 06:22:21.277332	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
678	QU202506-001	307	\N	1999935	\N	\N	2025-06-03 01:10:20.110763+00	2025-06-03 01:10:20.109493	13	pending	[]	[]	f	\N	\N	\N	\N	\N	\N	\N	none	1999935
594	QU202505-005	516	\N	290569	\N	\N	2025-05-16 02:41:48.634195+00	2025-05-16 02:41:48.633661	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	297257
610	QU202505-021	561	\N	127600	\N	\N	2025-05-16 07:30:30.45601+00	2025-05-16 07:30:30.455504	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	127600
650	QU202505-060	40	\N	1207655	\N	\N	2025-05-19 02:12:52.850567+00	2025-05-19 02:12:52.850119	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1230003
558	QU202501-034	25	\N	455261	awarded	channel_follow	2025-01-09 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	480265
595	QU202505-006	517	\N	152502	\N	\N	2025-05-16 03:10:20.423385+00	2025-05-26 14:47:23.035029	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	152502
668	QU202505-078	597	\N	276276.924	\N	\N	2025-05-29 07:10:37.968107+00	2025-05-29 07:10:37.967705	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	267033
669	QU202505-079	600	\N	575344	\N	\N	2025-05-29 07:36:31.265012+00	2025-05-29 07:44:07.606701	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	267986
429	QU202311-092	107	\N	3301056		\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	3301056
432	QU202406-018	111	\N	72562		\N	2024-06-08 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	168751
676	QU202505-086	528	\N	557063	embed	sales_focus	2025-05-30 07:07:51.753408+00	2025-05-30 07:07:51.752811	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	557063
559	QU202503-049	26	\N	55292.84999999999	signed	channel_follow	2025-03-06 00:00:00+00	2025-06-03 02:29:15.136423	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	122873
679	QU202506-002	605	\N	57600	signed	channel_follow	2025-06-03 02:24:15.334786+00	2025-06-03 02:24:15.334167	15	pending	[]	[]	f	\N	\N	\N	\N	\N	\N	\N	none	57600
440	QU202404-010	216	\N	51958		\N	2024-04-15 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	120834
441	QU202311-096	217	\N	339000		\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	234686
442	QU202412-019	219	\N	441335		\N	2024-12-26 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	454915
443	QU202311-097	241	\N	7651333		\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	7651333
444	QU202411-022	245	\N	1479510		\N	2024-11-14 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1514358
446	QU202407-018	273	\N	380417		\N	2024-07-16 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	380417
447	QU202408-016	284	\N	9135		\N	2024-08-29 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	9135
448	QU202311-098	301	\N	5783799		\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	5783799
449	QU202311-099	308	\N	120834		\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	120834
450	QU202311-100	310	\N	3639451		\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	3639451
451	QU202311-101	311	\N	68160		\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	68160
452	QU202311-102	319	\N	155220		\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	155220
667	QU202505-077	599	\N	91914.35	signed	channel_follow	2025-05-29 07:06:59.896672+00	2025-06-03 02:48:01.933401	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	226949
677	QU202505-087	603	\N	149031	discover	channel_follow	2025-05-30 07:24:49.40389+00	2025-05-30 07:24:49.40314	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	149031
675	QU202505-085	593	\N	1140022	embed	channel_follow	2025-05-30 07:02:27.910239+00	2025-05-30 07:02:27.90963	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1140022
681	QU202506-004	606	\N	198556	pre_tender	channel_follow	2025-06-03 10:20:02.582889+00	2025-06-03 10:20:02.57225	13	pending	[]	[]	f	\N	\N	\N	\N	\N	\N	\N	none	198556
414	QU202502-028	119	\N	359.98	awarded	\N	2025-02-24 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
415	QU202503-038	120	\N	7008	awarded	\N	2025-03-10 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
597	QU202505-008	520	\N	38350	\N	\N	2025-05-16 03:43:34.248634+00	2025-05-16 03:43:34.247884	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	38350
598	QU202505-009	521	\N	217007	\N	\N	2025-05-16 03:52:15.725413+00	2025-05-16 03:52:15.724868	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	217007
600	QU202505-011	524	\N	111360	\N	\N	2025-05-16 04:01:31.197916+00	2025-05-16 04:01:31.197439	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	105680
601	QU202505-012	525	\N	107952	\N	\N	2025-05-16 04:07:45.385388+00	2025-05-16 04:07:45.384876	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	104544
612	QU202505-023	70	\N	265434	\N	\N	2025-05-16 07:37:33.09624+00	2025-05-16 07:37:33.09278	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	265434
613	QU202505-024	563	\N	208904	\N	\N	2025-05-16 07:39:38.05725+00	2025-05-16 07:39:38.056791	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	208904
614	QU202505-025	152	\N	473622	\N	\N	2025-05-16 07:43:41.052151+00	2025-05-16 07:43:41.051679	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	473622
615	QU202505-026	4	\N	506728	\N	\N	2025-05-16 08:00:12.856941+00	2025-05-16 08:00:12.856284	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	506728
616	QU202505-027	566	\N	359535	\N	\N	2025-05-16 08:08:15.755046+00	2025-05-16 08:08:15.754616	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	274966
617	QU202505-028	565	\N	139038	\N	\N	2025-05-16 08:17:27.490423+00	2025-05-16 08:17:27.489937	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	145570
618	QU202505-029	564	\N	152298	\N	\N	2025-05-16 08:21:52.384402+00	2025-05-16 08:21:52.383851	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	152298
619	QU202505-030	562	\N	277966	\N	\N	2025-05-16 08:26:18.89553+00	2025-05-16 08:26:18.895091	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	310254
684	QU202506-007	610	\N	72133	embed	channel_follow	2025-06-04 02:02:15.979465+00	2025-06-04 02:02:15.978813	16	pending	[]	[]	f	\N	\N	\N	\N	\N	\N	\N	none	72133
648	QU202505-058	577	\N	299045	tendering	channel_follow	2025-05-18 13:59:37.397518+00	2025-05-22 07:39:07.491669	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	299045
666	QU202505-076	598	\N	254494	embed	channel_follow	2025-05-29 06:28:35.57283+00	2025-05-29 06:28:35.572413	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	254494
620	QU202505-031	560	\N	145456	\N	\N	2025-05-16 08:28:40.495878+00	2025-05-16 08:28:40.495241	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	142616
621	QU202505-032	559	\N	575616	\N	\N	2025-05-16 08:31:36.813529+00	2025-05-16 08:31:36.812821	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	687496
652	QU202505-062	587	\N	601962	\N	\N	2025-05-20 06:20:08.19464+00	2025-05-20 06:20:08.194182	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	601962
670	QU202505-080	105	\N	413864.63699999993	\N	\N	2025-05-30 02:17:42.081302+00	2025-05-30 02:17:42.080856	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	389402
671	QU202505-081	3	\N	501609	\N	\N	2025-05-30 02:37:40.450801+00	2025-05-30 02:37:40.450262	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	501609
596	QU202505-007	518	\N	170570.37	signed	channel_follow	2025-05-16 03:23:38.451828+00	2025-06-03 02:07:39.824309	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	461001
682	QU202506-005	607	\N	140071	awarded	sales_focus	2025-06-03 10:56:16.125795+00	2025-06-03 10:56:16.12518	13	pending	[]	[]	f	\N	\N	\N	\N	\N	\N	\N	none	140036
680	QU202506-003	601	\N	168556	embed	channel_follow	2025-06-03 03:24:12.12314+00	2025-06-03 03:24:12.122659	15	pending	[]	[]	f	\N	\N	\N	\N	\N	\N	\N	none	168556
604	QU202505-015	532	\N	145461	\N	\N	2025-05-16 04:53:44.166733+00	2025-05-16 04:53:44.165762	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	143387
605	QU202505-016	534	\N	264299	\N	\N	2025-05-16 05:18:40.535269+00	2025-05-16 05:18:40.534738	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	264299
352	QU202411-019	146	\N	116960	awarded	\N	2024-11-15 00:00:00+00	2025-05-16 06:56:22.618638	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	116960
421	QU202501-025	1	\N	421273	embed	sales_focus	2025-01-17 00:00:00+00	2025-05-16 07:46:40.815455	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	426953
626	QU202505-037	552	\N	312647	\N	\N	2025-05-16 08:47:24.672862+00	2025-05-30 03:31:00.826027	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	312647
622	QU202505-033	558	\N	493320	\N	\N	2025-05-16 08:35:46.949796+00	2025-05-16 08:35:46.949322	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	679734
590	QU202505-001	510	\N	350108	\N	\N	2025-05-14 01:07:43.716914+00	2025-05-14 01:07:43.712581	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	350108
572	QU202503-052	138	\N	434195	awarded	\N	2025-03-27 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	574773
592	QU202505-003	513	\N	7008	signed	normal	2025-05-14 08:11:24.239946+00	2025-05-21 13:14:04.449679	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
351	QU202412-016	145	\N	1506548	awarded	\N	2024-12-06 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1359836
356	QU202311-068	171	\N	644950	awarded	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	644950
399	QU202504-066	14	\N	15500	awarded	\N	2025-04-22 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
404	QU202504-071	57	\N	36750	awarded	\N	2025-04-15 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
405	QU202504-072	58	\N	2600	awarded	\N	2025-04-15 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
406	QU202504-073	96	\N	25350	awarded	\N	2025-04-09 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	25188
408	QU202503-032	113	\N	52500	awarded	\N	2025-03-20 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
410	QU202503-034	115	\N	3900	awarded	\N	2025-03-20 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
411	QU202503-035	116	\N	95000	awarded	\N	2025-03-16 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
412	QU202503-036	117	\N	660	awarded	\N	2025-03-10 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
418	QU202502-029	123	\N	82595.82	awarded	\N	2025-02-24 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
419	QU202503-041	124	\N	210000	awarded	\N	2025-03-10 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
420	QU202502-030	125	\N	299265.62	awarded	\N	2025-02-19 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	184203
460	QU202405-018	149	\N	348300	awarded	\N	2024-05-10 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	348300
463	QU202405-020	163	\N	46322	awarded	\N	2024-05-23 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	46322
472	QU202410-017	212	\N	238818	awarded	\N	2024-10-09 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	238818
487	QU202311-109	279	\N	182336	awarded	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	182336
490	QU202311-110	285	\N	49560	awarded	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	49560
508	QU202403-018	32	\N	4978015	awarded	\N	2024-03-28 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	4977969
513	QU202402-007	60	\N	1029081	awarded	\N	2024-02-25 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1032105
515	QU202403-019	66	\N	531170	awarded	\N	2024-03-25 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	531168
520	QU202504-093	78	\N	74474	awarded	\N	2025-04-12 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	74474
527	QU202410-019	85	\N	153335	awarded	\N	2024-10-23 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	153335
528	QU202501-032	88	\N	699054	awarded	\N	2025-01-07 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	699054
530	QU202311-114	102	\N	207732	awarded	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	207732
532	QU202405-025	108	\N	1169105	awarded	\N	2024-05-19 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1288487
533	QU202406-022	133	\N	450368	awarded	\N	2024-06-19 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	450364
534	QU202405-026	134	\N	176058	awarded	\N	2024-05-23 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	36625
535	QU202403-020	135	\N	1273122	awarded	\N	2024-03-14 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1273120
541	QU202311-115	167	\N	147944	awarded	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	147944
556	QU202502-032	7	\N	2215227	awarded	\N	2025-02-21 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	2215227
562	QU202408-021	33	\N	85597	awarded	\N	2024-08-26 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	85597
569	QU202408-023	93	\N	123548	awarded	\N	2024-08-26 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	123548
570	QU202411-031	131	\N	117392	awarded	\N	2024-11-18 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	117392
573	QU202502-037	147	\N	170288	awarded	\N	2025-02-25 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	170278
574	QU202502-038	148	\N	56173	awarded	\N	2025-02-09 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	55884
576	QU202502-039	165	\N	1413196	awarded	\N	2025-02-20 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1455660
578	QU202502-041	182	\N	291804	awarded	\N	2025-02-20 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	291804
579	QU202501-035	196	\N	602329	awarded	\N	2025-01-09 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	606082
624	QU202505-035	556	\N	310398	tendering	channel_follow	2025-05-16 08:43:06.226872+00	2025-05-16 08:43:06.226442	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	310398
627	QU202505-038	550	\N	276892	\N	\N	2025-05-16 09:08:25.64681+00	2025-05-16 09:08:25.646163	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	343023
628	QU202505-039	548	\N	376069	\N	\N	2025-05-16 09:12:02.576453+00	2025-05-16 09:12:02.575898	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	283005
630	QU202505-041	545	\N	129924	\N	\N	2025-05-16 09:19:39.846482+00	2025-05-16 09:19:39.845982	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	129924
631	QU202505-042	544	\N	266458	\N	\N	2025-05-16 09:23:53.389954+00	2025-05-16 09:23:53.389326	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	252610
633	QU202505-044	541	\N	615260	\N	\N	2025-05-16 09:32:11.750603+00	2025-05-16 09:32:11.750111	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	476998
654	QU202505-064	590	\N	437667	embed	sales_focus	2025-05-20 06:37:05.868122+00	2025-05-20 06:37:05.867431	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	437667
591	QU202505-002	512	\N	124837	awarded	channel_follow	2025-05-14 01:45:49.354763+00	2025-05-14 01:45:49.354271	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	124837
546	QU202311-116	187	\N	2134545	signed	channel_follow	2023-10-31 00:00:00+00	2025-05-30 06:33:43.623684	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	2134545
659	QU202505-069	572	\N	70888	\N	\N	2025-05-28 06:35:48.961291+00	2025-05-28 06:35:48.960451	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	70888
467	QU202311-105	198	\N	225000	lost	channel_follow	2023-10-31 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	225000
655	QU202505-065	573	\N	191777	tendering	channel_follow	2025-05-22 02:37:10.884937+00	2025-05-28 06:29:07.5927	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	191777
660	QU202505-070	571	\N	212746	\N	\N	2025-05-28 06:41:31.430537+00	2025-05-28 06:41:31.429743	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	212746
661	QU202505-071	570	\N	563513.556	\N	\N	2025-05-28 07:02:07.826258+00	2025-05-28 07:02:07.825681	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	509079
662	QU202505-072	569	\N	57900	\N	\N	2025-05-28 07:17:35.05296+00	2025-05-28 07:17:35.052524	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	57900
514	QU202408-018	61	\N	148069	signed	channel_follow	2024-08-07 00:00:00+00	2025-05-21 06:44:41.164145	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	148065
345	QU202412-015	65	\N	1016951	awarded	\N	2024-12-25 00:00:00+00	2025-05-28 08:15:58.806998	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1013066
453	QU202311-103	5	\N	1092731	signed	sales_focus	2023-10-31 00:00:00+00	2025-05-30 02:48:00.095149	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1092731
509	QU202504-087	39	\N	47586	signed	sales_focus	2025-04-12 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	47586
337	QU202504-062	9	\N	26393.4	signed	channel_follow	2025-04-15 00:00:00+00	2025-06-03 02:17:06.340148	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	58652
560	QU202410-021	27	\N	53330.4	signed	channel_follow	2024-10-17 00:00:00+00	2025-06-03 02:31:14.643534	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	118512
625	QU202505-036	554	\N	54718	\N	\N	2025-05-16 08:44:37.170204+00	2025-06-03 03:50:30.274623	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	54718
629	QU202505-040	546	\N	292672	\N	\N	2025-05-16 09:17:17.282015+00	2025-06-03 04:01:34.846069	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	292672
425	QU202408-015	71	\N	42037.200000000004	signed	channel_follow	2024-08-21 00:00:00+00	2025-06-03 10:44:23.953657	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	93416
585	QU202502-044	243	\N	23990	awarded	\N	2025-02-20 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	23990
462	QU202405-019	158	\N	63216	discover	\N	2024-05-10 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	62646
485	QU202408-017	276	\N	132867	discover	\N	2024-08-29 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	132867
500	QU202504-080	91	\N	74529	discover	\N	2025-04-02 00:00:00+00	2025-05-09 00:00:00	7	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	39921
501	QU202504-081	95	\N	10337.3	discover	\N	2025-04-10 00:00:00+00	2025-05-09 00:00:00	7	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	2840
339	QU202412-013	28	\N	362013	embed	\N	2024-12-27 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	362013
347	QU202504-064	89	\N	229911	embed	\N	2025-04-11 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	82778
357	QU202311-069	172	\N	272060	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	272060
358	QU202311-070	173	\N	153598	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	153598
359	QU202311-071	174	\N	374246	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	374246
360	QU202410-015	175	\N	169599	embed	\N	2024-10-23 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	126235
362	QU202409-016	177	\N	205651	embed	\N	2024-09-20 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	153152
363	QU202412-017	178	\N	524616	embed	\N	2024-12-20 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	440934
367	QU202502-026	206	\N	176468	embed	\N	2025-02-10 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	131333
368	QU202501-023	208	\N	480197	embed	\N	2025-01-09 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	352712
371	QU202412-018	231	\N	720113	embed	\N	2024-12-20 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	575880
372	QU202405-016	236	\N	175868	embed	\N	2024-05-08 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	145546
373	QU202409-017	238	\N	1987305	embed	\N	2024-09-06 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1889081
375	QU202311-077	261	\N	271226	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	271226
381	QU202407-015	287	\N	148433	embed	\N	2024-07-28 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	84101
382	QU202311-080	288	\N	146451	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	146451
383	QU202407-016	289	\N	518741	embed	\N	2024-07-15 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	399348
385	QU202311-082	292	\N	301086	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	301086
386	QU202311-083	293	\N	84108	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	84108
390	QU202311-086	302	\N	476348	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	476348
393	QU202311-087	313	\N	69716	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	69716
394	QU202311-088	314	\N	305198	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	305198
395	QU202311-089	315	\N	391058	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	391058
396	QU202311-090	316	\N	33503	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	33503
397	QU202311-091	317	\N	304490	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	304490
413	QU202503-037	118	\N	34800	embed	\N	2025-03-04 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	43200
416	QU202503-039	121	\N	14000	embed	\N	2025-03-04 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	13330
424	QU202504-075	35	\N	257186	embed	\N	2025-04-19 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	300355
426	QU202503-043	98	\N	515277	embed	\N	2025-03-17 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	574640
430	QU202402-006	109	\N	10171807	embed	\N	2024-02-22 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	29804544
456	QU202504-076	37	\N	153238	embed	\N	2025-04-20 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	153238
457	QU202504-077	38	\N	267910	embed	\N	2025-04-17 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	267910
464	QU202405-021	179	\N	816922	embed	\N	2024-05-30 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	816922
484	QU202403-016	275	\N	1513640	embed	\N	2024-03-14 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1513640
486	QU202409-022	277	\N	421627	embed	\N	2024-09-17 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	421627
488	QU202409-023	280	\N	115210	embed	\N	2024-09-17 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	115210
492	QU202311-111	294	\N	877573	embed	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	877573
378	QU202402-005	264	\N	367785	lost	sales_focus	2024-02-28 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	260292
343	QU202311-066	62	\N	480232	quoted	sales_focus	2023-10-31 00:00:00+00	2025-06-10 02:57:41.328271	16	pending	\N	\N	f	\N	\N	\N	\N	\N	24e02f148e2fe6b4936d5f783b3d12b1	\N	none	1019125
465	QU202405-022	180	\N	248547	embed	\N	2024-05-10 00:00:00+00	2025-06-09 01:48:12.098415	15	pending	\N	\N	f	\N	\N	\N	\N	\N	d97cf60532b08b6a702be6945190cd4e	\N	none	765531
498	QU202403-017	309	\N	82798	embed	\N	2024-03-28 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	82798
512	QU202502-031	59	\N	422224	embed	\N	2025-02-05 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	422224
516	QU202408-019	67	\N	815019	embed	\N	2024-08-19 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	828575
517	QU202504-090	75	\N	706126	embed	\N	2025-04-12 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	706126
526	QU202411-028	84	\N	282640	embed	\N	2024-11-26 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	296220
531	QU202504-096	103	\N	1177637	embed	\N	2025-04-09 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1177637
538	QU202405-027	159	\N	284794	embed	\N	2024-05-23 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	284782
539	QU202408-020	160	\N	362566	embed	\N	2024-08-06 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	504770
543	QU202407-021	183	\N	587550	embed	\N	2024-07-03 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	601126
545	QU202412-021	186	\N	285403	embed	\N	2024-12-26 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	298983
547	QU202412-022	207	\N	145547	embed	\N	2024-12-26 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	159127
548	QU202411-029	210	\N	922634	embed	\N	2024-11-10 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	949794
549	QU202406-023	214	\N	1332931	embed	\N	2024-06-06 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1346493
550	QU202406-024	226	\N	745483	embed	\N	2024-06-19 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	745483
554	QU202402-008	260	\N	1215837	embed	\N	2024-02-25 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1190239
557	QU202412-024	8	\N	273631	embed	\N	2024-12-08 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	273061
563	QU202502-033	43	\N	1677454	embed	\N	2025-02-20 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1677411
567	QU202502-035	55	\N	2787052	embed	\N	2025-02-20 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	2639677
583	QU202501-038	218	\N	1089433	embed	\N	2025-01-09 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1133245
588	QU202403-021	258	\N	395470	embed	\N	2024-03-02 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	395470
361	QU202411-020	176	\N	193868	pre_tender	\N	2024-11-15 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	146196
364	QU202311-072	193	\N	645204	pre_tender	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	645204
376	QU202311-078	262	\N	502526	pre_tender	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	502526
377	QU202311-079	263	\N	408340	pre_tender	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	412500
379	QU202408-014	281	\N	229944	pre_tender	\N	2024-08-08 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	182248
384	QU202311-081	290	\N	97202	pre_tender	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	97202
398	QU202504-065	13	\N	19800	pre_tender	\N	2025-04-23 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
400	QU202504-067	15	\N	7008	pre_tender	\N	2025-04-22 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
401	QU202504-068	16	\N	150000	pre_tender	\N	2025-04-22 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	101200
402	QU202504-069	42	\N	750000	pre_tender	\N	2025-04-16 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
480	QU202411-026	250	\N	130256	lost	sales_focus	2024-10-31 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	130256
403	QU202504-070	56	\N	115000	pre_tender	\N	2025-04-09 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	31126
407	QU202502-027	106	\N	198000	pre_tender	\N	2025-02-19 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
409	QU202503-033	114	\N	34000	pre_tender	\N	2025-03-20 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	29646
423	QU202504-074	34	\N	253534	pre_tender	\N	2025-04-04 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	253534
438	QU202410-016	164	\N	984824	pre_tender	\N	2024-10-18 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	984824
502	QU202504-082	112	\N	800000	pre_tender	\N	2025-04-02 00:00:00+00	2025-05-09 00:00:00	7	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	0
519	QU202504-092	77	\N	293347	pre_tender	\N	2025-04-12 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	293347
564	QU202408-022	48	\N	1200960	pre_tender	\N	2024-08-26 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1200960
565	QU202504-097	49	\N	205591	pre_tender	\N	2025-04-06 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	204941
566	QU202502-034	53	\N	859965	pre_tender	\N	2025-02-20 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	782745
568	QU202502-036	92	\N	108606	pre_tender	\N	2025-02-20 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	108606
577	QU202502-040	170	\N	99399	pre_tender	\N	2025-02-25 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	99399
581	QU202501-036	204	\N	350236	pre_tender	\N	2025-01-09 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	333136
582	QU202501-037	205	\N	149764	pre_tender	\N	2025-01-09 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	149764
584	QU202502-043	235	\N	315624	pre_tender	\N	2025-02-25 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	327471
586	QU202411-032	244	\N	64246	pre_tender	\N	2024-11-28 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	62356
346	QU202311-067	73	\N	2771088	tendering	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	2780226
355	QU202502-025	169	\N	476420	tendering	\N	2025-02-06 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	459288
388	QU202311-085	297	\N	415910	tendering	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	415910
437	QU202503-044	151	\N	31126	tendering	\N	2025-03-12 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	31126
458	QU202504-078	68	\N	121378	tendering	\N	2025-04-13 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	121378
459	QU202504-079	69	\N	179289	tendering	\N	2025-04-10 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	179289
469	QU202407-019	200	\N	72982	tendering	\N	2024-07-25 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	72982
471	QU202501-028	211	\N	207824	tendering	\N	2025-01-16 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	207824
493	QU202311-112	296	\N	605398	tendering	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	605398
503	QU202504-083	10	\N	157618	tendering	\N	2025-04-24 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	157618
504	QU202504-084	11	\N	128362	tendering	\N	2025-04-24 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	128362
439	QU202501-027	209	\N	1069048	tendering	sales_focus	2025-01-17 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1068478
387	QU202311-084	295	\N	643544	paused	sales_focus	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	643544
374	QU202311-076	239	\N	383480	paused	channel_follow	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	383480
507	QU202409-025	24	\N	477632	tendering	\N	2024-09-19 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	477632
510	QU202504-088	45	\N	80097	tendering	\N	2025-04-12 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	80097
511	QU202504-089	46	\N	18904	tendering	\N	2025-04-12 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	18904
518	QU202504-091	76	\N	92446	tendering	\N	2025-04-12 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	92446
521	QU202504-094	79	\N	252498	tendering	\N	2025-04-12 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	252498
522	QU202504-095	80	\N	171215	tendering	\N	2025-04-12 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	171215
544	QU202410-020	185	\N	137091	tendering	\N	2024-10-07 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	137091
589	QU202410-022	266	\N	164492	tendering	\N	2024-10-08 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	164492
338	QU202407-014	21	\N	347690.84	signed	\N	2024-07-10 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	850252
340	QU202412-014	29	\N	302434.05	signed	\N	2024-12-04 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	703335
344	QU202503-028	63	\N	122449.05	signed	\N	2025-03-24 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	272109
348	QU202503-029	127	\N	320491.35	signed	\N	2025-03-24 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	712203
349	QU202502-024	129	\N	39092.85	signed	\N	2025-02-13 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	86873
350	QU202503-030	130	\N	52657.200000000004	signed	\N	2025-03-24 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	117016
353	QU202503-031	154	\N	85594.73999999998	signed	\N	2025-03-09 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	203797
380	QU202406-017	286	\N	60936.75	signed	\N	2024-06-18 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	135415
389	QU202404-008	298	\N	20275.199999999997	signed	\N	2024-04-11 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	45056
391	QU202404-009	303	\N	14637.599999999999	signed	\N	2024-04-24 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	32528
392	QU202501-024	305	\N	65620	signed	\N	2025-01-01 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	164050
455	QU202503-045	36	\N	96122.25	signed	\N	2025-03-09 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	213605
479	QU202411-025	248	\N	22233.6	signed	\N	2024-11-13 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	49408
481	QU202410-018	259	\N	36480.15	signed	\N	2024-10-23 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	81067
482	QU202409-020	272	\N	30217.5	signed	\N	2024-09-23 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	67150
489	QU202409-024	282	\N	54470.09999999999	signed	\N	2024-09-01 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	181567
491	QU202407-020	291	\N	36132.3	signed	\N	2024-07-07 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	80294
494	QU202405-023	299	\N	22569.3	signed	\N	2024-05-18 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	50154
495	QU202405-024	300	\N	76909.95000000001	signed	\N	2024-05-18 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	170911
496	QU202501-029	304	\N	85524.75	signed	\N	2025-01-01 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	190055
497	QU202501-030	306	\N	26091.899999999998	signed	\N	2025-01-01 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	57982
499	QU202501-031	312	\N	175792.05	signed	\N	2025-01-01 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	390649
505	QU202504-085	17	\N	205331.85000000003	signed	\N	2025-04-20 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	456293
506	QU202504-086	18	\N	36492.299999999996	signed	\N	2025-04-12 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	81094
536	QU202503-047	136	\N	52875	signed	\N	2025-03-03 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	117500
537	QU202503-048	156	\N	42860.25	signed	\N	2025-03-10 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	95245
551	QU202412-023	227	\N	359462.25	signed	\N	2024-12-15 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	812385
553	QU202411-030	240	\N	169946.88	signed	\N	2024-11-28 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	531084
555	QU202501-033	278	\N	1002300	signed	\N	2025-01-01 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	1159416
587	QU202405-028	257	\N	39376.34999999999	signed	\N	2024-05-19 00:00:00+00	2025-05-09 00:00:00	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	87503
354	QU202406-016	155	\N	528356	lost	\N	2024-06-21 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	414278
370	QU202411-021	225	\N	852209	lost	\N	2024-11-08 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	659023
433	QU202311-094	140	\N	188550	lost	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	188550
434	QU202311-095	141	\N	162766	lost	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	162766
571	QU202503-051	132	\N	19816.649999999998	signed	\N	2025-03-19 00:00:00+00	2025-05-25 15:40:27.473245	17	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	44037
417	QU202503-040	122	\N	16000	tendering	business_opportunity	2025-03-04 00:00:00+00	2025-05-09 00:00:00	2	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	21250
435	QU202409-018	142	\N	118106	lost	\N	2024-09-09 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	118106
466	QU202311-104	197	\N	206038	lost	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	206038
473	QU202311-106	220	\N	81378	lost	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	81378
474	QU202406-019	221	\N	78088	lost	\N	2024-06-13 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	78088
475	QU202311-107	222	\N	118240	lost	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	118240
476	QU202403-015	223	\N	462240	lost	\N	2024-03-20 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	462240
477	QU202406-020	224	\N	130256	lost	\N	2024-06-06 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	130256
478	QU202311-108	232	\N	144710	lost	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	144710
366	QU202311-074	195	\N	3649725	paused	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	3649725
369	QU202311-075	215	\N	3050914	paused	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	16	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	3050914
431	QU202311-093	110	\N	141627	paused	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	141627
524	QU202311-113	82	\N	181538	paused	\N	2023-10-31 00:00:00+00	2025-05-09 00:00:00	14	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	181538
606	QU202505-017	535	\N	258920	\N	\N	2025-05-16 05:26:34.743949+00	2025-05-16 05:26:34.743439	13	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	258920
468	QU202403-014	199	\N	165569	lost	channel_follow	2024-03-14 00:00:00+00	2025-05-16 09:50:19.725081	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	165569
635	QU202505-045	522	\N	95454	\N	\N	2025-05-16 09:52:00.460222+00	2025-05-16 09:52:00.459818	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	171514
636	QU202505-046	526	\N	223660	\N	\N	2025-05-16 09:55:00.244036+00	2025-05-16 09:55:00.243572	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	203348
637	QU202505-047	527	\N	187171	\N	\N	2025-05-16 09:59:31.248767+00	2025-05-16 09:59:31.247708	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	152789
638	QU202505-048	530	\N	308049	\N	\N	2025-05-16 10:02:36.898459+00	2025-05-16 10:02:36.897806	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	266880
639	QU202505-049	538	\N	139038	\N	\N	2025-05-16 10:07:26.570166+00	2025-05-16 10:07:26.56963	15	pending	\N	\N	f	\N	\N	\N	\N	\N	\N	\N	none	169698
\.


--
-- TOC entry 4085 (class 0 OID 19750)
-- Dependencies: 310
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.role_permissions (id, role, module, can_view, can_create, can_edit, can_delete) FROM stdin;
8	sales	project	t	t	t	t
9	sales	customer	t	t	t	t
10	sales	quotation	t	t	t	t
11	sales	product	t	f	f	f
12	sales	product_code	f	f	f	f
13	sales	user	f	f	f	f
14	sales	permission	f	f	f	f
36	channel_manager	project	t	t	t	t
37	channel_manager	customer	t	t	t	t
38	channel_manager	quotation	t	t	t	t
39	channel_manager	product	t	f	f	f
40	channel_manager	product_code	f	f	f	f
41	channel_manager	user	f	f	f	f
42	channel_manager	permission	f	f	f	f
57	6e7a1ada	project	t	t	t	t
58	6e7a1ada	customer	t	t	t	t
59	6e7a1ada	quotation	t	t	t	t
60	6e7a1ada	product	t	t	t	t
61	6e7a1ada	product_code	f	f	f	f
62	6e7a1ada	user	f	f	f	f
63	6e7a1ada	permission	f	f	f	f
71	service_manager	project	t	t	t	t
72	service_manager	customer	t	t	t	t
73	service_manager	quotation	t	t	t	t
74	service_manager	product	t	f	f	f
75	service_manager	product_code	f	f	f	f
76	service_manager	user	f	f	f	f
77	service_manager	permission	f	f	f	f
78	ceo	project	t	t	t	t
79	ceo	customer	t	t	t	t
80	ceo	quotation	t	t	t	t
81	ceo	product	t	t	t	t
82	ceo	product_code	t	t	t	t
83	ceo	user	f	f	f	f
84	ceo	permission	f	f	f	f
85	finace_director	project	t	t	t	t
86	finace_director	customer	t	t	t	t
87	finace_director	quotation	t	t	t	t
88	finace_director	product	t	f	f	f
89	finace_director	product_code	f	f	f	f
90	finace_director	user	f	f	f	f
91	finace_director	permission	f	f	f	f
92	product_manager	project	t	t	t	t
93	product_manager	customer	t	t	t	t
94	product_manager	quotation	t	t	t	t
95	product_manager	product	t	t	t	t
96	product_manager	product_code	t	t	t	t
97	product_manager	user	f	f	f	f
98	product_manager	permission	f	f	f	f
99	dealer	project	t	t	t	t
100	dealer	customer	t	t	t	t
101	dealer	quotation	t	t	t	t
102	dealer	product	f	f	f	f
103	dealer	product_code	f	f	f	f
104	dealer	user	f	f	f	f
105	dealer	permission	f	f	f	f
106	business_admin	project	t	t	t	t
107	business_admin	customer	t	t	t	t
108	business_admin	quotation	t	t	t	t
109	business_admin	product	t	f	f	f
110	business_admin	product_code	f	f	f	f
111	business_admin	user	f	f	f	f
112	business_admin	permission	f	f	f	f
113	customer_sales	project	t	t	t	t
114	customer_sales	customer	t	t	t	t
115	customer_sales	quotation	t	t	t	t
116	customer_sales	product	t	f	f	f
117	customer_sales	product_code	f	f	f	f
118	customer_sales	user	f	f	f	f
119	customer_sales	permission	f	f	f	f
120	solution_manager	project	t	t	t	t
121	solution_manager	customer	t	t	t	t
122	solution_manager	quotation	t	t	t	t
123	solution_manager	product	t	f	f	f
124	solution_manager	product_code	f	f	f	f
125	solution_manager	user	f	f	f	f
126	solution_manager	permission	f	f	f	f
134	user	project	t	t	t	t
135	user	customer	t	t	t	t
136	user	quotation	t	t	t	t
137	user	product	f	f	f	f
138	user	product_code	f	f	f	f
139	user	user	f	f	f	f
140	user	permission	f	f	f	f
148	sales_director	project	t	t	t	t
149	sales_director	customer	t	t	t	t
150	sales_director	quotation	t	t	t	t
151	sales_director	product	t	f	f	f
152	sales_director	product_code	f	f	f	f
153	sales_director	user	f	f	f	f
154	sales_director	permission	f	f	f	f
155	sales_manager	project	t	t	t	t
156	sales_manager	customer	t	t	t	t
157	sales_manager	quotation	t	t	t	t
158	sales_manager	product	t	f	f	f
159	sales_manager	product_code	f	f	f	f
160	sales_manager	user	f	f	f	f
161	sales_manager	permission	f	f	f	f
162	channel_manager\t	project	t	t	t	t
163	channel_manager\t	customer	t	t	t	t
164	channel_manager\t	quotation	t	t	t	t
165	channel_manager\t	product	t	f	f	f
166	channel_manager\t	product_code	f	f	f	f
167	channel_manager\t	user	f	f	f	f
168	channel_manager\t	permission	f	f	f	f
169	admin	product	t	t	t	t
176	admin	project_rating	t	t	t	t
177	sales_director	project_rating	t	t	t	t
178	service_manager	project_rating	t	t	t	f
179	channel_manager	project_rating	t	t	f	f
180	product_manager	project_rating	t	t	f	f
181	solution_manager	project_rating	t	t	f	f
182	sales	project_rating	t	f	f	f
183	admin	inventory	t	t	t	t
184	solution_manager	inventory	t	t	t	f
185	ceo	inventory	t	t	t	f
186	assistant	inventory	t	f	f	f
187	admin	settlement	t	t	t	t
188	admin	order	t	t	t	t
189	business_admin	inventory	t	t	t	f
190	business_admin	settlement	t	t	t	f
191	business_admin	order	t	t	t	f
192	ceo	settlement	t	t	t	f
193	ceo	order	t	t	t	f
194	solution	inventory	t	f	f	f
195	solution	settlement	t	f	f	f
196	solution	order	t	f	f	f
197	service	inventory	t	f	f	f
198	service	settlement	t	f	f	f
199	service	order	t	f	f	f
200	sales	inventory	t	f	f	f
201	sales	settlement	t	f	f	f
202	sales	order	t	f	f	f
203	assistant	settlement	t	f	f	f
204	assistant	order	t	f	f	f
\.


--
-- TOC entry 4087 (class 0 OID 19754)
-- Dependencies: 312
-- Data for Name: settlement_details; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.settlement_details (id, settlement_id, inventory_id, product_id, quantity_settled, quantity_before, quantity_after, unit, notes) FROM stdin;
\.


--
-- TOC entry 4089 (class 0 OID 19760)
-- Dependencies: 314
-- Data for Name: settlement_order_details; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.settlement_order_details (id, pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_order_id, settlement_company_id, settlement_status, settlement_date, settlement_notes) FROM stdin;
1	1	超薄室内全向吸顶天线	MA10	频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65	和源通信	套	HYAIOCN4Y	142	63.9	1	0.45	63.9	29	\N	\N	pending	\N	\N
2	1	功率分配器	EVPD-2 LT	频率范围：88-430MHz;承载功率：100W;分路端口数量：2;防护等级：IP53;	和源通信	套	HYCDN24Y	142	63.9	1	0.45	63.9	30	\N	\N	pending	\N	\N
3	1	定向耦合器	EVDC-6 LT	频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;	和源通信	套	HYCCN34Y	142	63.9	1	0.45	63.9	31	\N	\N	pending	\N	\N
7	3	智能信道交换机	S1024	端口数量：24个  网线类型：3、4、5类双绞线   防雷等级：4级（6KV） 用途：CP、IP、LCP、系统监控配件/信道机	华三	套	OBJSVOTXQ01	780	312	1	0.4	312	35	\N	\N	pending	\N	\N
8	3	馈电功率分配器	MAPD-2	频率范围：88-866MHz 承载功率：100W 分路端口数量：2 防护等级：IP65 应用：馈电	和源通信	套	HYCDF24Y	208	83.2	1	0.4	83.2	36	\N	\N	pending	\N	\N
9	3	分路器	E-JF150-4	频率范围：130-170MHz 单端口承载功率：1W;插入损耗：≤7.0dB接入端口数量：4;安装方式：机柜式;	和源通信	套	HYMJC4010	2913	1165.2	1	0.4	1165.2	37	\N	\N	pending	\N	\N
\.


--
-- TOC entry 4029 (class 0 OID 19266)
-- Dependencies: 254
-- Data for Name: settlement_orders; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.settlement_orders (id, order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, total_amount, total_discount_rate, status, approved_by, approved_at, created_by, created_at, updated_at) FROM stdin;
1	SO202506-001	1	621	691	472	\N	426	1	draft	\N	\N	18	2025-06-13 03:28:43.564776	2025-06-13 03:28:43.592736
2	SO202506-002	2	100	428	472	\N	2141633	1	draft	\N	\N	13	2025-06-13 05:51:19.784546	2025-06-13 05:51:19.805335
3	SO202506-003	3	624	694	284	284	3901	1	draft	\N	\N	5	2025-06-13 09:41:41.803091	2025-06-13 09:41:41.83048
\.


--
-- TOC entry 4035 (class 0 OID 19435)
-- Dependencies: 260
-- Data for Name: settlements; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.settlements (id, settlement_number, company_id, settlement_date, status, total_items, description, created_by_id, approved_by_id, approved_at, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4091 (class 0 OID 19766)
-- Dependencies: 316
-- Data for Name: solution_manager_email_settings; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.solution_manager_email_settings (id, user_id, quotation_created, quotation_updated, project_created, project_stage_changed, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4093 (class 0 OID 19770)
-- Dependencies: 318
-- Data for Name: system_metrics; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.system_metrics (id, version_id, avg_response_time, max_response_time, error_rate, active_users, total_requests, database_size, cpu_usage, memory_usage, disk_usage, recorded_at) FROM stdin;
\.


--
-- TOC entry 4095 (class 0 OID 19774)
-- Dependencies: 320
-- Data for Name: system_settings; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.system_settings (id, key, value, description, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4097 (class 0 OID 19780)
-- Dependencies: 322
-- Data for Name: upgrade_logs; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.upgrade_logs (id, version_id, from_version, to_version, upgrade_date, upgrade_type, status, upgrade_notes, error_message, duration_seconds, operator_id, operator_name, environment, server_info) FROM stdin;
\.


--
-- TOC entry 4099 (class 0 OID 19786)
-- Dependencies: 324
-- Data for Name: user_event_subscriptions; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.user_event_subscriptions (id, user_id, target_user_id, event_id, enabled, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3997 (class 0 OID 18054)
-- Dependencies: 222
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.users (id, username, password_hash, real_name, company_name, email, phone, department, is_department_manager, role, is_profile_complete, wechat_openid, wechat_nickname, wechat_avatar, is_active, created_at, last_login, updated_at) FROM stdin;
31	caoyx	scrypt:32768:8:1$jSc9sPJdaI0HJ7Wc$e921cef8b9ba306475bf277870016ee917ac62cd6048b185516f448a5b8d1e8b2d3740d50711d905ee7a8b57039e9ce72456643d3725c4548a40c629dfa198ea	曹宇欣	和源通信（上海）股份有限公司	caoyx@evertac.net	+86-17358826712	产品和解决方案部	f	product_manager	f	\N	\N	\N	t	1748319839.6103299	\N	1748320468.7196882
11	wanggang	pbkdf2:sha256:260000$a0WYvnl692CI4BAe$54651eced32adad3b1aed7d32ef959639f38b10ec1d8f701e29f09a4748ee14a	王刚	和源通信（上海）股份有限公司	wanggang@evertac	086-17521028583	产品和解决方案部	f	product_manager	\N	\N	\N	\N	f	\N	\N	\N
5	admin	pbkdf2:sha256:260000$Mp3tpvbN3C9EOGx5$f02b46fae1e3f94c8c85647c0d8e2fb5cee35165b6a2dc826d6b14b0b73cc842	系统管理员	和源通信（上海）股份有限公司	james.ni@evertacsolutions.com	13003258568		f	admin	\N	\N	\N	\N	t	\N	\N	\N
7	xuhao	scrypt:32768:8:1$66iytOSaFpoPCHms$d77c44bad79d385e5f85cae142ff212aac0c20fbf8391632bdb3ef8a14b4e568af42204afaf0bd464bc0cb6239f36a910b8d220ffa5f454754db20cf4ece16a5	徐昊	和源通信（上海）股份有限公司	xuhao@evertac.net	086-13818736483	服务部	t	service_manager	\N	\N	\N	\N	t	\N	\N	\N
16	fanjing	scrypt:32768:8:1$9vxSFR9AmN64WbOX$24750460529049970abbecc8b362f7a7a5991b08b0d7e5ee9bf5496e910d54fe5013a0cd4e361065a842d1e3f1e602030ec1719fdc4bd576bb80ddb42430611a	范敬	和源通信（上海）股份有限公司	fanjing@evertac.net	086-13851869911	销售部	f	sales_manager	\N	\N	\N	\N	t	\N	\N	\N
22	huawei	pbkdf2:sha256:260000$avOW1VO1KwFyPANt$35c9fb9067876a7285cc43c94d57b3622b3960ab679d1592d1249c52e202b5bb	花伟	敦力(南京)科技有限公司	huawei@test.com			t	dealer	f	\N	\N	\N	f	1746783813.3370032	\N	\N
19	linwenguan	scrypt:32768:8:1$MDEVreVLbaVI5gXn$bf8a1e929bdfa40e367639aaa6cdd41396c8b19f7d660c0d249da941ffcb56a9e4f4a10952ef667e2dfb6f656bf1144f5e079669c4ad62028162ea9470e780d9	林文冠	和源通信（上海）股份有限公司	linwenguan@evertac.net	086-13816388363	销售部	f	channel_manager	\N	\N	\N	\N	t	\N	\N	1748250767.8096824
2	fangl	scrypt:32768:8:1$SfB9kVu4xfT5hUUI$2722ce46d8c3052e9a5550c2feaa66d938c4ebe6b60f942a26178fc1b5ab82324e6b903e149a679c19724d4a8e06eb5fc81ceff872777128298da2fe68903667	方玲	和源通信（上海）股份有限公司	fangl@evertac.net		服务部	f	customer_sales	f	\N	\N	\N	t	1746773246.342183	\N	1747208969.8894696
13	gxh	scrypt:32768:8:1$Yd4sfJ8BG5TtW5aY$48b21d2c13755801967438a8e8d393d3d63dca57f9c363690b3f3227740d857dda31806fd15219ea47e04d44009ac1cdfbd78d255988c7087ec4b66f61e2ee05	郭小会	和源通信（上海）股份有限公司	gxh@evertac.net	086-15692111506	销售部	t	sales_director	\N	\N	\N	\N	t	\N	\N	1748827923.6736858
20	shengyh	scrypt:32768:8:1$hX64W4bZYYRT2r7K$35cf55153e32d7ea297ae6bf5de716735b01048248c4f5979a5c95e0edf46ac2823e1f69233cced070a51ecef813f744b08842cdbf5e1190afb9447a13ed50c8	盛雅华	和源通信（上海）股份有限公司	shengyh@evertac.net	086-15800471445	服务部	f	customer_sales	\N	\N	\N	\N	t	\N	\N	\N
3	lidong	pbkdf2:sha256:260000$mwh7XP1TPO4aHpt0$67fb2560e6b1ff8ab00b3206f318a56391f9675b4a788e9f0b70faf8005f7e93	李冬	上海瑞康通信科技有限公司	lidong@test.com			t	dealer	f	\N	\N	\N	f	1746783748.944108	\N	\N
18	tonglei	scrypt:32768:8:1$j0UEawTpawa2Gv7F$a01cf4bd7c56147cd748983a210676245b06227e57a2015e6bfbdde29124a03fe557a3be59bf234e0d0bc3f6ecce841c789adcd8a7c374d03a545fd5e1a2de81	童蕾	和源通信（上海）股份有限公司	tonglei@evertac.net	086-13801862575	销售部	f	business_admin	\N	\N	\N	\N	t	\N	\N	1749800185.2479403
17	zhouyj	scrypt:32768:8:1$iQRQ5prniTjHlSwT$2a675dc429160b923eae1e1eca7d49d35358902116c6ac772b0576762f25462aef37ef3db0983c59bcfbcd159daf1244209d5036e4b9fa9d48694f33091894ea	周裔锦	和源通信（上海）股份有限公司	zhouyj@evertac.net	086-18923456355	销售部	f	sales_manager	\N	\N	\N	\N	t	\N	\N	\N
25	zoujuan	pbkdf2:sha256:260000$E2yMFnbvmfTeAkhU$fada34f6db2a8af217621e2bb41f698acb2d432ca2646ee0a68c217e9c1cf235	邹娟	福淳智能科技(四川)有限公司	zoujuan@test.com			t	dealer	f	\N	\N	\N	f	1746784051.0969346	\N	\N
24	zoufei	pbkdf2:sha256:260000$9m2zqrKWR5o36mfR$81bd96b05416b81694efd0601dd6dcf169082752107565c686acb8bea6b0f8bc	邹飞	上海淳泊信息科技有限公司	zhoufei@test.com			t	dealer	f	\N	\N	\N	f	1746784000.536146	\N	\N
23	libo	pbkdf2:sha256:260000$SwI6BusqW3Chfr7W$457d7f0b3f9dccb8a3b603d6bf533755d9e72308d3917c0793439fe60a5ce3e7	李博	浙江航博智能工程有限公司	libo@test.com			t	dealer	f	\N	\N	\N	f	1746783920.9279294	\N	\N
12	liuwei	scrypt:32768:8:1$Ml5buOitzhhLNSfm$d4528698c2f030b42f236618ae874ed8e9a5948e31c0a56391e0ed61d879a1956b07597d10fabf870d43992d23e519466906904d8d96d161e7472f53f649ae61	刘威	和源通信（上海）股份有限公司	liuwei@evertac.net	086-13361800535	产品和解决方案部	f	solution_manager	\N	\N	\N	\N	t	\N	\N	\N
29	jing	scrypt:32768:8:1$wchvh7lGBVnJ75eB$393caa76dab9ff3640b665d1b6e03c2930c66636aa15261757e17f9217bc09b5b3d16c1dcbedd2322f15a24a6e6aa490cfce7c1773ce9b1ae9cc4a7d05ba9526	倪靖豪	和源通信（上海）股份有限公司	jing19751013@icloud.com		财务部	f	business_admin	f	\N	\N	\N	t	1746889048.0265067	\N	\N
6	nijie	pbkdf2:sha256:260000$NVHnaIJuMEEwHerE$1835e5484358259f860cee10fe6753c94e1c86ffcce9ef40272aff998a31863b	倪捷	和源通信（上海）股份有限公司	james111@evertac.net	086-13003258568	销售部	f	ceo	\N	\N	\N	\N	t	\N	\N	1749802253.0742986
10	zhaoyb	scrypt:32768:8:1$I5zt0R7ghJ8haczs$f7c1ac58fd91e9e6a7174bcd29b378ea1357ae566093a04b3a996d0f0e0eecc185ea5ddcc7b6ec8bfaa6311b69915f533781169f3ef1da9333f8cac6bee55826	赵祎博	和源通信（上海）股份有限公司	zhaoyb@evertac.net	086-13636393979	产品和解决方案部	t	product_manager	\N	\N	\N	\N	t	\N	\N	\N
14	yangjj	scrypt:32768:8:1$aGZzKPEPvwoSfVQp$e48fdac05738a2b54cb22768fbdc11a87e38b3f6c9531cc48a16130dd29d7bb185f57e7a6f0fb053dc6ac9c2102d05d04e6ed34c9b47f9e3e54001006bce1fd4	杨俊杰	和源通信（上海）股份有限公司	yangjj@evertac.net	086-13482779221	销售部	f	sales_manager	\N	\N	\N	\N	t	\N	\N	1749436771.8045018
9	liuq	pbkdf2:sha256:260000$dhaoKgs4gyRsSHZ1$b983e3ece7a926184d18a9068520d6f2c7faab3bc89bec71699ccb820731a6a7	刘倩	和源通信（上海）股份有限公司	liuq@evertac.net	086-18918602455	人事行政部	f	user	\N	\N	\N	\N	f	\N	\N	1748319948.3170862
15	lihuawei	scrypt:32768:8:1$UigftrfiNvs1vDH3$d9b32549c4ecfc7d467529620892da7e24fa6da727b0c288f98b3f4f6db470d9aa7ffc09276bbf2ddfca31181f05bd07dee5cf63966b541b732290dee968a6e9	李华伟	和源通信（上海）股份有限公司	lihuawei@evertac.net	086-15601873096	销售部	f	sales_manager	\N	\N	\N	\N	t	\N	\N	1748573076.4667177
4	vivian	scrypt:32768:8:1$0MPOm0qgnuNxdCwy$067f179bc17951651deddc8b222929088363fce711911ab02a73a446c424ba8ca535eb8026cd5aacf96bc8a12305e7560a61e20e5930b7f66c43648238f31ea9	张琰	和源通信（上海）股份有限公司	vivian@evertac.net	086-15692111122	财务部	t	finace_director	\N	\N	\N	\N	t	\N	\N	1749603299.7443352
\.


--
-- TOC entry 4025 (class 0 OID 18875)
-- Dependencies: 250
-- Data for Name: version_records; Type: TABLE DATA; Schema: public; Owner: pma_db_sp8d_user
--

COPY public.version_records (id, version_number, version_name, release_date, description, is_current, environment, total_features, total_fixes, total_improvements, git_commit, build_number, created_at, updated_at) FROM stdin;
1	1.0.1	PMA项目管理系统	2025-06-02 09:53:57.041063	PMA项目管理系统当前运行版本，包含完整的项目管理、客户管理、报价管理、产品管理等功能。	t	production	0	0	0	\N	\N	2025-06-02 01:53:57.041927	2025-06-02 01:53:57.04193
\.


--
-- TOC entry 4332 (class 0 OID 0)
-- Dependencies: 264
-- Name: action_reply_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.action_reply_id_seq', 1, false);


--
-- TOC entry 4333 (class 0 OID 0)
-- Dependencies: 266
-- Name: actions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.actions_id_seq', 4, true);


--
-- TOC entry 4334 (class 0 OID 0)
-- Dependencies: 268
-- Name: affiliations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.affiliations_id_seq', 158, true);


--
-- TOC entry 4335 (class 0 OID 0)
-- Dependencies: 271
-- Name: approval_instance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.approval_instance_id_seq', 1, true);


--
-- TOC entry 4336 (class 0 OID 0)
-- Dependencies: 247
-- Name: approval_process_template_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.approval_process_template_id_seq', 4, true);


--
-- TOC entry 4337 (class 0 OID 0)
-- Dependencies: 272
-- Name: approval_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.approval_record_id_seq', 2, true);


--
-- TOC entry 4338 (class 0 OID 0)
-- Dependencies: 275
-- Name: approval_step_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.approval_step_id_seq', 3, true);


--
-- TOC entry 4339 (class 0 OID 0)
-- Dependencies: 277
-- Name: change_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.change_logs_id_seq', 8, true);


--
-- TOC entry 4340 (class 0 OID 0)
-- Dependencies: 229
-- Name: companies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.companies_id_seq', 525, true);


--
-- TOC entry 4341 (class 0 OID 0)
-- Dependencies: 235
-- Name: contacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.contacts_id_seq', 721, true);


--
-- TOC entry 4342 (class 0 OID 0)
-- Dependencies: 279
-- Name: dev_product_specs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.dev_product_specs_id_seq', 1, false);


--
-- TOC entry 4343 (class 0 OID 0)
-- Dependencies: 241
-- Name: dev_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.dev_products_id_seq', 1, false);


--
-- TOC entry 4344 (class 0 OID 0)
-- Dependencies: 281
-- Name: dictionaries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.dictionaries_id_seq', 34, true);


--
-- TOC entry 4345 (class 0 OID 0)
-- Dependencies: 283
-- Name: event_registry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.event_registry_id_seq', 1, false);


--
-- TOC entry 4346 (class 0 OID 0)
-- Dependencies: 285
-- Name: feature_changes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.feature_changes_id_seq', 1, false);


--
-- TOC entry 4347 (class 0 OID 0)
-- Dependencies: 257
-- Name: inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.inventory_id_seq', 1, false);


--
-- TOC entry 4348 (class 0 OID 0)
-- Dependencies: 287
-- Name: inventory_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.inventory_transactions_id_seq', 1, false);


--
-- TOC entry 4349 (class 0 OID 0)
-- Dependencies: 289
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.permissions_id_seq', 1, false);


--
-- TOC entry 4350 (class 0 OID 0)
-- Dependencies: 291
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.pricing_order_approval_records_id_seq', 2, true);


--
-- TOC entry 4351 (class 0 OID 0)
-- Dependencies: 255
-- Name: pricing_order_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.pricing_order_details_id_seq', 37, true);


--
-- TOC entry 4352 (class 0 OID 0)
-- Dependencies: 251
-- Name: pricing_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.pricing_orders_id_seq', 3, true);


--
-- TOC entry 4353 (class 0 OID 0)
-- Dependencies: 223
-- Name: product_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.product_categories_id_seq', 1, false);


--
-- TOC entry 4354 (class 0 OID 0)
-- Dependencies: 245
-- Name: product_code_field_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.product_code_field_options_id_seq', 1, false);


--
-- TOC entry 4355 (class 0 OID 0)
-- Dependencies: 293
-- Name: product_code_field_values_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.product_code_field_values_id_seq', 1, false);


--
-- TOC entry 4356 (class 0 OID 0)
-- Dependencies: 237
-- Name: product_code_fields_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.product_code_fields_id_seq', 1, false);


--
-- TOC entry 4357 (class 0 OID 0)
-- Dependencies: 239
-- Name: product_codes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.product_codes_id_seq', 1, false);


--
-- TOC entry 4358 (class 0 OID 0)
-- Dependencies: 225
-- Name: product_regions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.product_regions_id_seq', 1, false);


--
-- TOC entry 4359 (class 0 OID 0)
-- Dependencies: 233
-- Name: product_subcategories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.product_subcategories_id_seq', 1, false);


--
-- TOC entry 4360 (class 0 OID 0)
-- Dependencies: 231
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.products_id_seq', 1, false);


--
-- TOC entry 4361 (class 0 OID 0)
-- Dependencies: 295
-- Name: project_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.project_members_id_seq', 1, false);


--
-- TOC entry 4362 (class 0 OID 0)
-- Dependencies: 297
-- Name: project_rating_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.project_rating_records_id_seq', 1, false);


--
-- TOC entry 4363 (class 0 OID 0)
-- Dependencies: 299
-- Name: project_scoring_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.project_scoring_config_id_seq', 1, false);


--
-- TOC entry 4364 (class 0 OID 0)
-- Dependencies: 301
-- Name: project_scoring_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.project_scoring_records_id_seq', 1, false);


--
-- TOC entry 4365 (class 0 OID 0)
-- Dependencies: 303
-- Name: project_stage_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.project_stage_history_id_seq', 8, true);


--
-- TOC entry 4366 (class 0 OID 0)
-- Dependencies: 305
-- Name: project_total_scores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.project_total_scores_id_seq', 38, true);


--
-- TOC entry 4367 (class 0 OID 0)
-- Dependencies: 227
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.projects_id_seq', 624, true);


--
-- TOC entry 4368 (class 0 OID 0)
-- Dependencies: 307
-- Name: purchase_order_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.purchase_order_details_id_seq', 1, false);


--
-- TOC entry 4369 (class 0 OID 0)
-- Dependencies: 261
-- Name: purchase_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.purchase_orders_id_seq', 1, false);


--
-- TOC entry 4370 (class 0 OID 0)
-- Dependencies: 309
-- Name: quotation_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.quotation_details_id_seq', 3, true);


--
-- TOC entry 4371 (class 0 OID 0)
-- Dependencies: 243
-- Name: quotations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.quotations_id_seq', 694, true);


--
-- TOC entry 4372 (class 0 OID 0)
-- Dependencies: 311
-- Name: role_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.role_permissions_id_seq', 204, true);


--
-- TOC entry 4373 (class 0 OID 0)
-- Dependencies: 313
-- Name: settlement_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.settlement_details_id_seq', 1, false);


--
-- TOC entry 4374 (class 0 OID 0)
-- Dependencies: 315
-- Name: settlement_order_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.settlement_order_details_id_seq', 9, true);


--
-- TOC entry 4375 (class 0 OID 0)
-- Dependencies: 253
-- Name: settlement_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.settlement_orders_id_seq', 3, true);


--
-- TOC entry 4376 (class 0 OID 0)
-- Dependencies: 259
-- Name: settlements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.settlements_id_seq', 1, false);


--
-- TOC entry 4377 (class 0 OID 0)
-- Dependencies: 317
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.solution_manager_email_settings_id_seq', 1, false);


--
-- TOC entry 4378 (class 0 OID 0)
-- Dependencies: 319
-- Name: system_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.system_metrics_id_seq', 1, false);


--
-- TOC entry 4379 (class 0 OID 0)
-- Dependencies: 321
-- Name: system_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.system_settings_id_seq', 1, false);


--
-- TOC entry 4380 (class 0 OID 0)
-- Dependencies: 323
-- Name: upgrade_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.upgrade_logs_id_seq', 1, false);


--
-- TOC entry 4381 (class 0 OID 0)
-- Dependencies: 325
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.user_event_subscriptions_id_seq', 1, false);


--
-- TOC entry 4382 (class 0 OID 0)
-- Dependencies: 221
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.users_id_seq', 31, true);


--
-- TOC entry 4383 (class 0 OID 0)
-- Dependencies: 249
-- Name: version_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pma_db_sp8d_user
--

SELECT pg_catalog.setval('public.version_records_id_seq', 3, true);


--
-- TOC entry 3665 (class 2606 OID 19842)
-- Name: action_reply action_reply_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_pkey PRIMARY KEY (id);


--
-- TOC entry 3667 (class 2606 OID 19844)
-- Name: actions actions_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_pkey PRIMARY KEY (id);


--
-- TOC entry 3669 (class 2606 OID 19846)
-- Name: affiliations affiliations_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_pkey PRIMARY KEY (id);


--
-- TOC entry 3673 (class 2606 OID 19848)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 3675 (class 2606 OID 19850)
-- Name: approval_instance approval_instance_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_pkey PRIMARY KEY (id);


--
-- TOC entry 3637 (class 2606 OID 18727)
-- Name: approval_process_template approval_process_template_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_pkey PRIMARY KEY (id);


--
-- TOC entry 3677 (class 2606 OID 19852)
-- Name: approval_record approval_record_temp_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_temp_pkey PRIMARY KEY (id);


--
-- TOC entry 3679 (class 2606 OID 19854)
-- Name: approval_step approval_step_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_pkey PRIMARY KEY (id);


--
-- TOC entry 3681 (class 2606 OID 19856)
-- Name: change_logs change_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.change_logs
    ADD CONSTRAINT change_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 3609 (class 2606 OID 18186)
-- Name: companies companies_company_code_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_company_code_key UNIQUE (company_code);


--
-- TOC entry 3611 (class 2606 OID 18184)
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- TOC entry 3621 (class 2606 OID 18232)
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (id);


--
-- TOC entry 3683 (class 2606 OID 19858)
-- Name: dev_product_specs dev_product_specs_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dev_product_specs
    ADD CONSTRAINT dev_product_specs_pkey PRIMARY KEY (id);


--
-- TOC entry 3629 (class 2606 OID 18294)
-- Name: dev_products dev_products_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_pkey PRIMARY KEY (id);


--
-- TOC entry 3685 (class 2606 OID 19860)
-- Name: dictionaries dictionaries_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT dictionaries_pkey PRIMARY KEY (id);


--
-- TOC entry 3689 (class 2606 OID 19862)
-- Name: event_registry event_registry_event_key_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_event_key_key UNIQUE (event_key);


--
-- TOC entry 3691 (class 2606 OID 19864)
-- Name: event_registry event_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_pkey PRIMARY KEY (id);


--
-- TOC entry 3693 (class 2606 OID 19866)
-- Name: feature_changes feature_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_pkey PRIMARY KEY (id);


--
-- TOC entry 3653 (class 2606 OID 19416)
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (id);


--
-- TOC entry 3695 (class 2606 OID 19868)
-- Name: inventory_transactions inventory_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_pkey PRIMARY KEY (id);


--
-- TOC entry 3697 (class 2606 OID 19870)
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3701 (class 2606 OID 19872)
-- Name: pricing_order_approval_records pricing_order_approval_records_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3651 (class 2606 OID 19317)
-- Name: pricing_order_details pricing_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_order_details
    ADD CONSTRAINT pricing_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3643 (class 2606 OID 19234)
-- Name: pricing_orders pricing_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 3645 (class 2606 OID 19232)
-- Name: pricing_orders pricing_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 3599 (class 2606 OID 18078)
-- Name: product_categories product_categories_code_letter_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_code_letter_key UNIQUE (code_letter);


--
-- TOC entry 3601 (class 2606 OID 18076)
-- Name: product_categories product_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_pkey PRIMARY KEY (id);


--
-- TOC entry 3635 (class 2606 OID 18369)
-- Name: product_code_field_options product_code_field_options_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_field_options
    ADD CONSTRAINT product_code_field_options_pkey PRIMARY KEY (id);


--
-- TOC entry 3703 (class 2606 OID 19874)
-- Name: product_code_field_values product_code_field_values_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_pkey PRIMARY KEY (id);


--
-- TOC entry 3623 (class 2606 OID 18251)
-- Name: product_code_fields product_code_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_fields
    ADD CONSTRAINT product_code_fields_pkey PRIMARY KEY (id);


--
-- TOC entry 3625 (class 2606 OID 18265)
-- Name: product_codes product_codes_full_code_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_full_code_key UNIQUE (full_code);


--
-- TOC entry 3627 (class 2606 OID 18263)
-- Name: product_codes product_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_pkey PRIMARY KEY (id);


--
-- TOC entry 3603 (class 2606 OID 18087)
-- Name: product_regions product_regions_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_regions
    ADD CONSTRAINT product_regions_pkey PRIMARY KEY (id);


--
-- TOC entry 3617 (class 2606 OID 18216)
-- Name: product_subcategories product_subcategories_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT product_subcategories_pkey PRIMARY KEY (id);


--
-- TOC entry 3613 (class 2606 OID 18200)
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- TOC entry 3615 (class 2606 OID 18202)
-- Name: products products_product_mn_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_product_mn_key UNIQUE (product_mn);


--
-- TOC entry 3705 (class 2606 OID 19876)
-- Name: project_members project_members_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (id);


--
-- TOC entry 3707 (class 2606 OID 19878)
-- Name: project_rating_records project_rating_records_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3711 (class 2606 OID 19880)
-- Name: project_scoring_config project_scoring_config_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_scoring_config
    ADD CONSTRAINT project_scoring_config_pkey PRIMARY KEY (id);


--
-- TOC entry 3715 (class 2606 OID 19882)
-- Name: project_scoring_records project_scoring_records_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3720 (class 2606 OID 19884)
-- Name: project_stage_history project_stage_history_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_stage_history
    ADD CONSTRAINT project_stage_history_pkey PRIMARY KEY (id);


--
-- TOC entry 3722 (class 2606 OID 19886)
-- Name: project_total_scores project_total_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_pkey PRIMARY KEY (id);


--
-- TOC entry 3724 (class 2606 OID 19888)
-- Name: project_total_scores project_total_scores_project_id_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_project_id_key UNIQUE (project_id);


--
-- TOC entry 3607 (class 2606 OID 18168)
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- TOC entry 3726 (class 2606 OID 19890)
-- Name: purchase_order_details purchase_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3661 (class 2606 OID 19470)
-- Name: purchase_orders purchase_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 3663 (class 2606 OID 19468)
-- Name: purchase_orders purchase_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 3728 (class 2606 OID 19892)
-- Name: quotation_details quotation_details_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotation_details
    ADD CONSTRAINT quotation_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3631 (class 2606 OID 18343)
-- Name: quotations quotations_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_pkey PRIMARY KEY (id);


--
-- TOC entry 3633 (class 2606 OID 18345)
-- Name: quotations quotations_quotation_number_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_quotation_number_key UNIQUE (quotation_number);


--
-- TOC entry 3730 (class 2606 OID 19894)
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3734 (class 2606 OID 19896)
-- Name: settlement_details settlement_details_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3736 (class 2606 OID 19898)
-- Name: settlement_order_details settlement_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3647 (class 2606 OID 19273)
-- Name: settlement_orders settlement_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 3649 (class 2606 OID 19271)
-- Name: settlement_orders settlement_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 3657 (class 2606 OID 19442)
-- Name: settlements settlements_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_pkey PRIMARY KEY (id);


--
-- TOC entry 3659 (class 2606 OID 19444)
-- Name: settlements settlements_settlement_number_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_settlement_number_key UNIQUE (settlement_number);


--
-- TOC entry 3738 (class 2606 OID 19900)
-- Name: solution_manager_email_settings solution_manager_email_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT solution_manager_email_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 3742 (class 2606 OID 19902)
-- Name: system_metrics system_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_pkey PRIMARY KEY (id);


--
-- TOC entry 3745 (class 2606 OID 19904)
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 3671 (class 2606 OID 19906)
-- Name: affiliations uix_owner_viewer; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT uix_owner_viewer UNIQUE (owner_id, viewer_id);


--
-- TOC entry 3732 (class 2606 OID 19908)
-- Name: role_permissions uix_role_module; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT uix_role_module UNIQUE (role, module);


--
-- TOC entry 3687 (class 2606 OID 19910)
-- Name: dictionaries uix_type_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT uix_type_key UNIQUE (type, key);


--
-- TOC entry 3699 (class 2606 OID 19912)
-- Name: permissions uix_user_module; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT uix_user_module UNIQUE (user_id, module);


--
-- TOC entry 3655 (class 2606 OID 19418)
-- Name: inventory unique_company_product_inventory; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT unique_company_product_inventory UNIQUE (company_id, product_id);


--
-- TOC entry 3747 (class 2606 OID 19914)
-- Name: upgrade_logs upgrade_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 3709 (class 2606 OID 19916)
-- Name: project_rating_records uq_project_user_rating; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT uq_project_user_rating UNIQUE (project_id, user_id);


--
-- TOC entry 3713 (class 2606 OID 19918)
-- Name: project_scoring_config uq_scoring_config; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_scoring_config
    ADD CONSTRAINT uq_scoring_config UNIQUE (category, field_name);


--
-- TOC entry 3717 (class 2606 OID 19920)
-- Name: project_scoring_records uq_scoring_record_with_user; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT uq_scoring_record_with_user UNIQUE (project_id, category, field_name, awarded_by);


--
-- TOC entry 3740 (class 2606 OID 19922)
-- Name: solution_manager_email_settings uq_solution_manager_email_user; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT uq_solution_manager_email_user UNIQUE (user_id);


--
-- TOC entry 3619 (class 2606 OID 18218)
-- Name: product_subcategories uq_subcategory_code_letter; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT uq_subcategory_code_letter UNIQUE (category_id, code_letter);


--
-- TOC entry 3749 (class 2606 OID 19924)
-- Name: user_event_subscriptions uq_user_target_event; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT uq_user_target_event UNIQUE (user_id, target_user_id, event_id);


--
-- TOC entry 3751 (class 2606 OID 19926)
-- Name: user_event_subscriptions user_event_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_pkey PRIMARY KEY (id);


--
-- TOC entry 3591 (class 2606 OID 18065)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 3593 (class 2606 OID 18061)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 3595 (class 2606 OID 18063)
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- TOC entry 3597 (class 2606 OID 18067)
-- Name: users users_wechat_openid_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_wechat_openid_key UNIQUE (wechat_openid);


--
-- TOC entry 3639 (class 2606 OID 18882)
-- Name: version_records version_records_pkey; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.version_records
    ADD CONSTRAINT version_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3641 (class 2606 OID 18884)
-- Name: version_records version_records_version_number_key; Type: CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.version_records
    ADD CONSTRAINT version_records_version_number_key UNIQUE (version_number);


--
-- TOC entry 3718 (class 1259 OID 19927)
-- Name: ix_project_stage_history_project_id; Type: INDEX; Schema: public; Owner: pma_db_sp8d_user
--

CREATE INDEX ix_project_stage_history_project_id ON public.project_stage_history USING btree (project_id);


--
-- TOC entry 3604 (class 1259 OID 18174)
-- Name: ix_projects_authorization_code; Type: INDEX; Schema: public; Owner: pma_db_sp8d_user
--

CREATE INDEX ix_projects_authorization_code ON public.projects USING btree (authorization_code);


--
-- TOC entry 3605 (class 1259 OID 18175)
-- Name: ix_projects_project_name; Type: INDEX; Schema: public; Owner: pma_db_sp8d_user
--

CREATE INDEX ix_projects_project_name ON public.projects USING btree (project_name);


--
-- TOC entry 3743 (class 1259 OID 19928)
-- Name: ix_system_settings_key; Type: INDEX; Schema: public; Owner: pma_db_sp8d_user
--

CREATE UNIQUE INDEX ix_system_settings_key ON public.system_settings USING btree (key);


--
-- TOC entry 3800 (class 2606 OID 19929)
-- Name: action_reply action_reply_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.actions(id);


--
-- TOC entry 3801 (class 2606 OID 19934)
-- Name: action_reply action_reply_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3802 (class 2606 OID 19939)
-- Name: action_reply action_reply_parent_reply_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_parent_reply_id_fkey FOREIGN KEY (parent_reply_id) REFERENCES public.action_reply(id);


--
-- TOC entry 3803 (class 2606 OID 19944)
-- Name: actions actions_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 3804 (class 2606 OID 19949)
-- Name: actions actions_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- TOC entry 3805 (class 2606 OID 19954)
-- Name: actions actions_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3806 (class 2606 OID 19959)
-- Name: actions actions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3807 (class 2606 OID 19964)
-- Name: affiliations affiliations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3808 (class 2606 OID 19969)
-- Name: affiliations affiliations_viewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_viewer_id_fkey FOREIGN KEY (viewer_id) REFERENCES public.users(id);


--
-- TOC entry 3809 (class 2606 OID 19974)
-- Name: approval_instance approval_instance_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3810 (class 2606 OID 19979)
-- Name: approval_instance approval_instance_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- TOC entry 3776 (class 2606 OID 18728)
-- Name: approval_process_template approval_process_template_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3811 (class 2606 OID 19984)
-- Name: approval_record approval_record_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES public.approval_instance(id);


--
-- TOC entry 3814 (class 2606 OID 19989)
-- Name: approval_step approval_step_approver_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_approver_user_id_fkey FOREIGN KEY (approver_user_id) REFERENCES public.users(id);


--
-- TOC entry 3815 (class 2606 OID 19994)
-- Name: approval_step approval_step_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- TOC entry 3816 (class 2606 OID 19999)
-- Name: change_logs change_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.change_logs
    ADD CONSTRAINT change_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3755 (class 2606 OID 18187)
-- Name: companies companies_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3758 (class 2606 OID 18233)
-- Name: contacts contacts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 3759 (class 2606 OID 18238)
-- Name: contacts contacts_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3817 (class 2606 OID 20004)
-- Name: dev_product_specs dev_product_specs_dev_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dev_product_specs
    ADD CONSTRAINT dev_product_specs_dev_product_id_fkey FOREIGN KEY (dev_product_id) REFERENCES public.dev_products(id);


--
-- TOC entry 3765 (class 2606 OID 18295)
-- Name: dev_products dev_products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 3766 (class 2606 OID 18315)
-- Name: dev_products dev_products_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3767 (class 2606 OID 18310)
-- Name: dev_products dev_products_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3768 (class 2606 OID 18305)
-- Name: dev_products dev_products_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.product_regions(id);


--
-- TOC entry 3769 (class 2606 OID 18300)
-- Name: dev_products dev_products_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 3818 (class 2606 OID 20009)
-- Name: feature_changes feature_changes_developer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_developer_id_fkey FOREIGN KEY (developer_id) REFERENCES public.users(id);


--
-- TOC entry 3819 (class 2606 OID 20014)
-- Name: feature_changes feature_changes_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 3812 (class 2606 OID 20019)
-- Name: approval_record fk_approval_record_approver_id; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT fk_approval_record_approver_id FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- TOC entry 3813 (class 2606 OID 20024)
-- Name: approval_record fk_approval_record_step_id; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT fk_approval_record_step_id FOREIGN KEY (step_id) REFERENCES public.approval_step(id);


--
-- TOC entry 3842 (class 2606 OID 20029)
-- Name: settlement_order_details fk_settlement_order_details_settlement_company; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT fk_settlement_order_details_settlement_company FOREIGN KEY (settlement_company_id) REFERENCES public.companies(id);


--
-- TOC entry 3791 (class 2606 OID 19419)
-- Name: inventory inventory_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 3792 (class 2606 OID 19429)
-- Name: inventory inventory_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 3793 (class 2606 OID 19424)
-- Name: inventory inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 3820 (class 2606 OID 20034)
-- Name: inventory_transactions inventory_transactions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 3821 (class 2606 OID 20039)
-- Name: inventory_transactions inventory_transactions_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- TOC entry 3822 (class 2606 OID 20044)
-- Name: permissions permissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3823 (class 2606 OID 20049)
-- Name: pricing_order_approval_records pricing_order_approval_records_approver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_approver_id_fkey FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- TOC entry 3824 (class 2606 OID 20054)
-- Name: pricing_order_approval_records pricing_order_approval_records_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 3790 (class 2606 OID 19318)
-- Name: pricing_order_details pricing_order_details_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_order_details
    ADD CONSTRAINT pricing_order_details_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 3777 (class 2606 OID 19255)
-- Name: pricing_orders pricing_orders_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 3778 (class 2606 OID 19260)
-- Name: pricing_orders pricing_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3779 (class 2606 OID 19245)
-- Name: pricing_orders pricing_orders_dealer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_dealer_id_fkey FOREIGN KEY (dealer_id) REFERENCES public.companies(id);


--
-- TOC entry 3780 (class 2606 OID 19250)
-- Name: pricing_orders pricing_orders_distributor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_distributor_id_fkey FOREIGN KEY (distributor_id) REFERENCES public.companies(id);


--
-- TOC entry 3781 (class 2606 OID 19235)
-- Name: pricing_orders pricing_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3782 (class 2606 OID 19240)
-- Name: pricing_orders pricing_orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 3775 (class 2606 OID 18370)
-- Name: product_code_field_options product_code_field_options_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_field_options
    ADD CONSTRAINT product_code_field_options_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.product_code_fields(id);


--
-- TOC entry 3825 (class 2606 OID 20059)
-- Name: product_code_field_values product_code_field_values_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.product_code_fields(id);


--
-- TOC entry 3826 (class 2606 OID 20064)
-- Name: product_code_field_values product_code_field_values_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_option_id_fkey FOREIGN KEY (option_id) REFERENCES public.product_code_field_options(id);


--
-- TOC entry 3827 (class 2606 OID 20069)
-- Name: product_code_field_values product_code_field_values_product_code_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_product_code_id_fkey FOREIGN KEY (product_code_id) REFERENCES public.product_codes(id);


--
-- TOC entry 3760 (class 2606 OID 18252)
-- Name: product_code_fields product_code_fields_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_code_fields
    ADD CONSTRAINT product_code_fields_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 3761 (class 2606 OID 18271)
-- Name: product_codes product_codes_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 3762 (class 2606 OID 18281)
-- Name: product_codes product_codes_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3763 (class 2606 OID 18266)
-- Name: product_codes product_codes_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 3764 (class 2606 OID 18276)
-- Name: product_codes product_codes_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 3757 (class 2606 OID 18219)
-- Name: product_subcategories product_subcategories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT product_subcategories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 3756 (class 2606 OID 18203)
-- Name: products products_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3828 (class 2606 OID 20074)
-- Name: project_members project_members_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3829 (class 2606 OID 20079)
-- Name: project_members project_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3830 (class 2606 OID 20084)
-- Name: project_rating_records project_rating_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 3831 (class 2606 OID 20089)
-- Name: project_rating_records project_rating_records_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3832 (class 2606 OID 20094)
-- Name: project_scoring_records project_scoring_records_awarded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_awarded_by_fkey FOREIGN KEY (awarded_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- TOC entry 3833 (class 2606 OID 20099)
-- Name: project_scoring_records project_scoring_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 3834 (class 2606 OID 20104)
-- Name: project_stage_history project_stage_history_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_stage_history
    ADD CONSTRAINT project_stage_history_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3835 (class 2606 OID 20109)
-- Name: project_total_scores project_total_scores_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 3752 (class 2606 OID 18806)
-- Name: projects projects_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- TOC entry 3753 (class 2606 OID 18169)
-- Name: projects projects_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3754 (class 2606 OID 18816)
-- Name: projects projects_vendor_sales_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_vendor_sales_manager_id_fkey FOREIGN KEY (vendor_sales_manager_id) REFERENCES public.users(id);


--
-- TOC entry 3836 (class 2606 OID 20114)
-- Name: purchase_order_details purchase_order_details_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.purchase_orders(id);


--
-- TOC entry 3837 (class 2606 OID 20119)
-- Name: purchase_order_details purchase_order_details_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 3797 (class 2606 OID 19481)
-- Name: purchase_orders purchase_orders_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- TOC entry 3798 (class 2606 OID 19471)
-- Name: purchase_orders purchase_orders_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 3799 (class 2606 OID 19476)
-- Name: purchase_orders purchase_orders_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 3838 (class 2606 OID 20124)
-- Name: quotation_details quotation_details_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotation_details
    ADD CONSTRAINT quotation_details_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 3770 (class 2606 OID 19161)
-- Name: quotations quotations_confirmed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_confirmed_by_fkey FOREIGN KEY (confirmed_by) REFERENCES public.users(id);


--
-- TOC entry 3771 (class 2606 OID 18351)
-- Name: quotations quotations_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- TOC entry 3772 (class 2606 OID 19048)
-- Name: quotations quotations_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- TOC entry 3773 (class 2606 OID 18356)
-- Name: quotations quotations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3774 (class 2606 OID 18346)
-- Name: quotations quotations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3839 (class 2606 OID 20129)
-- Name: settlement_details settlement_details_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- TOC entry 3840 (class 2606 OID 20134)
-- Name: settlement_details settlement_details_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 3841 (class 2606 OID 20139)
-- Name: settlement_details settlement_details_settlement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_settlement_id_fkey FOREIGN KEY (settlement_id) REFERENCES public.settlements(id);


--
-- TOC entry 3843 (class 2606 OID 20144)
-- Name: settlement_order_details settlement_order_details_pricing_detail_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pricing_detail_id_fkey FOREIGN KEY (pricing_detail_id) REFERENCES public.pricing_order_details(id);


--
-- TOC entry 3844 (class 2606 OID 20149)
-- Name: settlement_order_details settlement_order_details_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 3845 (class 2606 OID 20154)
-- Name: settlement_order_details settlement_order_details_settlement_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_settlement_order_id_fkey FOREIGN KEY (settlement_order_id) REFERENCES public.settlement_orders(id);


--
-- TOC entry 3783 (class 2606 OID 19299)
-- Name: settlement_orders settlement_orders_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 3784 (class 2606 OID 19304)
-- Name: settlement_orders settlement_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3785 (class 2606 OID 19294)
-- Name: settlement_orders settlement_orders_dealer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_dealer_id_fkey FOREIGN KEY (dealer_id) REFERENCES public.companies(id);


--
-- TOC entry 3786 (class 2606 OID 19289)
-- Name: settlement_orders settlement_orders_distributor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_distributor_id_fkey FOREIGN KEY (distributor_id) REFERENCES public.companies(id);


--
-- TOC entry 3787 (class 2606 OID 19274)
-- Name: settlement_orders settlement_orders_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 3788 (class 2606 OID 19279)
-- Name: settlement_orders settlement_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3789 (class 2606 OID 19284)
-- Name: settlement_orders settlement_orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 3794 (class 2606 OID 19455)
-- Name: settlements settlements_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- TOC entry 3795 (class 2606 OID 19445)
-- Name: settlements settlements_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 3796 (class 2606 OID 19450)
-- Name: settlements settlements_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 3846 (class 2606 OID 20159)
-- Name: solution_manager_email_settings solution_manager_email_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT solution_manager_email_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3847 (class 2606 OID 20164)
-- Name: system_metrics system_metrics_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 3848 (class 2606 OID 20169)
-- Name: upgrade_logs upgrade_logs_operator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_operator_id_fkey FOREIGN KEY (operator_id) REFERENCES public.users(id);


--
-- TOC entry 3849 (class 2606 OID 20174)
-- Name: upgrade_logs upgrade_logs_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 3850 (class 2606 OID 20179)
-- Name: user_event_subscriptions user_event_subscriptions_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.event_registry(id);


--
-- TOC entry 3851 (class 2606 OID 20184)
-- Name: user_event_subscriptions user_event_subscriptions_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id);


--
-- TOC entry 3852 (class 2606 OID 20189)
-- Name: user_event_subscriptions user_event_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: pma_db_sp8d_user
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 2328 (class 826 OID 16391)
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON SEQUENCES TO pma_db_sp8d_user;


--
-- TOC entry 2330 (class 826 OID 16393)
-- Name: DEFAULT PRIVILEGES FOR TYPES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TYPES TO pma_db_sp8d_user;


--
-- TOC entry 2329 (class 826 OID 16392)
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON FUNCTIONS TO pma_db_sp8d_user;


--
-- TOC entry 2327 (class 826 OID 16390)
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: -; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT ALL ON TABLES TO pma_db_sp8d_user;


-- Completed on 2025-06-13 18:41:54 CST

--
-- PostgreSQL database dump complete
--

