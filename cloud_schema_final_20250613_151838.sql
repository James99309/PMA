--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Debian 16.9-1.pgdg120+1)
-- Dumped by pg_dump version 16.9 (Homebrew)

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
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: approval_action; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_action AS ENUM (
    'approve',
    'reject'
);


--
-- Name: approval_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);


--
-- Name: approvalaction; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalaction AS ENUM (
    'approve',
    'reject'
);


--
-- Name: approvalinstancestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalinstancestatus AS ENUM (
    'pending',
    'approved',
    'rejected'
);


--
-- Name: approvalstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalstatus AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- Name: pricingorderapprovalflowtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricingorderapprovalflowtype AS ENUM (
    'CHANNEL_FOLLOW',
    'SALES_KEY',
    'SALES_OPPORTUNITY'
);


--
-- Name: pricingorderstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricingorderstatus AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- Name: settlementorderstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.settlementorderstatus AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: action_reply; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: action_reply_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.action_reply_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: action_reply_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.action_reply_id_seq OWNED BY public.action_reply.id;


--
-- Name: actions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: actions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.actions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: actions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.actions_id_seq OWNED BY public.actions.id;


--
-- Name: affiliations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.affiliations (
    id integer NOT NULL,
    owner_id integer NOT NULL,
    viewer_id integer NOT NULL,
    created_at double precision
);


--
-- Name: affiliations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.affiliations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: affiliations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.affiliations_id_seq OWNED BY public.affiliations.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: approval_instance; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN approval_instance.object_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_id IS '对应单据ID';


--
-- Name: COLUMN approval_instance.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_type IS '单据类型（如 project）';


--
-- Name: COLUMN approval_instance.current_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.current_step IS '当前步骤序号';


--
-- Name: COLUMN approval_instance.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.status IS '状态';


--
-- Name: COLUMN approval_instance.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.started_at IS '流程发起时间';


--
-- Name: COLUMN approval_instance.ended_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.ended_at IS '审批完成时间';


--
-- Name: COLUMN approval_instance.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.process_id IS '流程模板ID';


--
-- Name: COLUMN approval_instance.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.created_by IS '发起人ID';


--
-- Name: COLUMN approval_instance.template_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_snapshot IS '创建时的模板快照';


--
-- Name: COLUMN approval_instance.template_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_version IS '模板版本号';


--
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
-- Name: approval_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_instance_id_seq OWNED BY public.approval_instance.id;


--
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
-- Name: COLUMN approval_process_template.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.name IS '流程名称';


--
-- Name: COLUMN approval_process_template.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.object_type IS '适用对象（如 quotation）';


--
-- Name: COLUMN approval_process_template.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.is_active IS '是否启用';


--
-- Name: COLUMN approval_process_template.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_by IS '创建人账号ID';


--
-- Name: COLUMN approval_process_template.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_at IS '创建时间';


--
-- Name: COLUMN approval_process_template.required_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.required_fields IS '发起审批时必填字段列表';


--
-- Name: COLUMN approval_process_template.lock_object_on_start; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_object_on_start IS '发起审批后是否锁定对象编辑';


--
-- Name: COLUMN approval_process_template.lock_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_reason IS '锁定原因说明';


--
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
-- Name: approval_process_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_process_template_id_seq OWNED BY public.approval_process_template.id;


--
-- Name: approval_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.approval_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: approval_record; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN approval_record.instance_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.instance_id IS '审批流程实例';


--
-- Name: COLUMN approval_record.step_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.step_id IS '流程步骤ID';


--
-- Name: COLUMN approval_record.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.approver_id IS '审批人ID';


--
-- Name: COLUMN approval_record.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.action IS '同意/拒绝';


--
-- Name: COLUMN approval_record.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.comment IS '审批意见';


--
-- Name: COLUMN approval_record."timestamp"; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record."timestamp" IS '审批时间';


--
-- Name: approval_step; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN approval_step.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.process_id IS '所属流程模板';


--
-- Name: COLUMN approval_step.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_order IS '流程顺序';


--
-- Name: COLUMN approval_step.approver_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.approver_user_id IS '审批人账号ID';


--
-- Name: COLUMN approval_step.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_name IS '步骤说明（如"财务审批"）';


--
-- Name: COLUMN approval_step.send_email; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.send_email IS '是否发送邮件通知';


--
-- Name: COLUMN approval_step.action_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_type IS '步骤动作类型，如 authorization, quotation_approval';


--
-- Name: COLUMN approval_step.action_params; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_params IS '动作参数，JSON格式';


--
-- Name: COLUMN approval_step.editable_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.editable_fields IS '在此步骤可编辑的字段列表';


--
-- Name: COLUMN approval_step.cc_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_users IS '邮件抄送用户ID列表';


--
-- Name: COLUMN approval_step.cc_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_enabled IS '是否启用邮件抄送';


--
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
-- Name: approval_step_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_step_id_seq OWNED BY public.approval_step.id;


--
-- Name: change_logs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: change_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.change_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: change_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.change_logs_id_seq OWNED BY public.change_logs.id;


--
-- Name: companies; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: companies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.companies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- Name: contacts; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: contacts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contacts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contacts_id_seq OWNED BY public.contacts.id;


--
-- Name: dev_product_specs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_product_specs (
    id integer NOT NULL,
    dev_product_id integer,
    field_name character varying(100),
    field_value character varying(255),
    field_code character varying(10)
);


--
-- Name: dev_product_specs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_product_specs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_product_specs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_product_specs_id_seq OWNED BY public.dev_product_specs.id;


--
-- Name: dev_products; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: dev_products_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_products_id_seq OWNED BY public.dev_products.id;


--
-- Name: dictionaries; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: dictionaries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dictionaries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dictionaries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dictionaries_id_seq OWNED BY public.dictionaries.id;


--
-- Name: event_registry; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN event_registry.event_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.event_key IS '事件唯一键';


--
-- Name: COLUMN event_registry.label_zh; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.label_zh IS '中文名称';


--
-- Name: COLUMN event_registry.label_en; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.label_en IS '英文名称';


--
-- Name: COLUMN event_registry.default_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.default_enabled IS '是否默认开启';


--
-- Name: COLUMN event_registry.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.enabled IS '是否在通知中心展示';


--
-- Name: event_registry_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.event_registry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: event_registry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_registry_id_seq OWNED BY public.event_registry.id;


--
-- Name: feature_changes; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN feature_changes.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.version_id IS '版本ID';


--
-- Name: COLUMN feature_changes.change_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.change_type IS '变更类型：feature/fix/improvement/security';


--
-- Name: COLUMN feature_changes.module_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.module_name IS '模块名称';


--
-- Name: COLUMN feature_changes.title; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.title IS '变更标题';


--
-- Name: COLUMN feature_changes.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.description IS '详细描述';


--
-- Name: COLUMN feature_changes.priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.priority IS '优先级：low/medium/high/critical';


--
-- Name: COLUMN feature_changes.impact_level; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.impact_level IS '影响级别：minor/major/breaking';


--
-- Name: COLUMN feature_changes.affected_files; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.affected_files IS '影响的文件列表（JSON格式）';


--
-- Name: COLUMN feature_changes.git_commits; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.git_commits IS '相关Git提交（JSON格式）';


--
-- Name: COLUMN feature_changes.test_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.test_status IS '测试状态：pending/passed/failed';


--
-- Name: COLUMN feature_changes.test_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.test_notes IS '测试说明';


--
-- Name: COLUMN feature_changes.developer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.developer_id IS '开发人员ID';


--
-- Name: COLUMN feature_changes.developer_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.developer_name IS '开发人员姓名';


--
-- Name: COLUMN feature_changes.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.created_at IS '创建时间';


--
-- Name: COLUMN feature_changes.completed_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.completed_at IS '完成时间';


--
-- Name: feature_changes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.feature_changes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: feature_changes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.feature_changes_id_seq OWNED BY public.feature_changes.id;


--
-- Name: inventory; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inventory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- Name: inventory_transactions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: inventory_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inventory_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_transactions_id_seq OWNED BY public.inventory_transactions.id;


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- Name: pricing_order_approval_records; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN pricing_order_approval_records.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.pricing_order_id IS '批价单ID';


--
-- Name: COLUMN pricing_order_approval_records.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_order IS '审批步骤顺序';


--
-- Name: COLUMN pricing_order_approval_records.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_name IS '审批步骤名称';


--
-- Name: COLUMN pricing_order_approval_records.approver_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_role IS '审批人角色';


--
-- Name: COLUMN pricing_order_approval_records.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_id IS '审批人ID';


--
-- Name: COLUMN pricing_order_approval_records.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.action IS '审批动作：approve/reject';


--
-- Name: COLUMN pricing_order_approval_records.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.comment IS '审批意见';


--
-- Name: COLUMN pricing_order_approval_records.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approved_at IS '审批时间';


--
-- Name: COLUMN pricing_order_approval_records.is_fast_approval; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.is_fast_approval IS '是否快速通过';


--
-- Name: COLUMN pricing_order_approval_records.fast_approval_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.fast_approval_reason IS '快速通过原因';


--
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pricing_order_approval_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_order_approval_records_id_seq OWNED BY public.pricing_order_approval_records.id;


--
-- Name: pricing_order_details; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN pricing_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.pricing_order_id IS '批价单ID';


--
-- Name: COLUMN pricing_order_details.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_name IS '产品名称';


--
-- Name: COLUMN pricing_order_details.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_model IS '产品型号';


--
-- Name: COLUMN pricing_order_details.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_desc IS '产品描述';


--
-- Name: COLUMN pricing_order_details.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.brand IS '品牌';


--
-- Name: COLUMN pricing_order_details.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.unit IS '单位';


--
-- Name: COLUMN pricing_order_details.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_mn IS '产品MN编码';


--
-- Name: COLUMN pricing_order_details.market_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.market_price IS '市场价';


--
-- Name: COLUMN pricing_order_details.unit_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.unit_price IS '单价';


--
-- Name: COLUMN pricing_order_details.quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.quantity IS '数量';


--
-- Name: COLUMN pricing_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.discount_rate IS '折扣率';


--
-- Name: COLUMN pricing_order_details.total_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.total_price IS '小计金额';


--
-- Name: COLUMN pricing_order_details.source_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.source_type IS '数据来源：quotation/manual';


--
-- Name: COLUMN pricing_order_details.source_quotation_detail_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.source_quotation_detail_id IS '来源报价单明细ID';


--
-- Name: pricing_order_details_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pricing_order_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pricing_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_order_details_id_seq OWNED BY public.pricing_order_details.id;


--
-- Name: pricing_orders; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN pricing_orders.order_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.order_number IS '批价单号';


--
-- Name: COLUMN pricing_orders.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.project_id IS '项目ID';


--
-- Name: COLUMN pricing_orders.quotation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.quotation_id IS '报价单ID';


--
-- Name: COLUMN pricing_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.dealer_id IS '经销商ID';


--
-- Name: COLUMN pricing_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.distributor_id IS '分销商ID';


--
-- Name: COLUMN pricing_orders.is_direct_contract; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.is_direct_contract IS '厂商直签';


--
-- Name: COLUMN pricing_orders.is_factory_pickup; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.is_factory_pickup IS '厂家提货';


--
-- Name: COLUMN pricing_orders.approval_flow_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approval_flow_type IS '审批流程类型';


--
-- Name: COLUMN pricing_orders.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.status IS '批价单状态';


--
-- Name: COLUMN pricing_orders.current_approval_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.current_approval_step IS '当前审批步骤';


--
-- Name: COLUMN pricing_orders.pricing_total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_amount IS '批价单总金额';


--
-- Name: COLUMN pricing_orders.pricing_total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_discount_rate IS '批价单总折扣率';


--
-- Name: COLUMN pricing_orders.settlement_total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_amount IS '结算单总金额';


--
-- Name: COLUMN pricing_orders.settlement_total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_discount_rate IS '结算单总折扣率';


--
-- Name: COLUMN pricing_orders.approved_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approved_by IS '最终批准人';


--
-- Name: COLUMN pricing_orders.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approved_at IS '批准时间';


--
-- Name: COLUMN pricing_orders.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.created_by IS '创建人';


--
-- Name: COLUMN pricing_orders.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.created_at IS '创建时间';


--
-- Name: COLUMN pricing_orders.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.updated_at IS '更新时间';


--
-- Name: pricing_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pricing_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pricing_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_orders_id_seq OWNED BY public.pricing_orders.id;


--
-- Name: product_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code_letter character varying(1) NOT NULL,
    description text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: product_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_categories_id_seq OWNED BY public.product_categories.id;


--
-- Name: product_code_field_options; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: product_code_field_options_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_code_field_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_code_field_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_field_options_id_seq OWNED BY public.product_code_field_options.id;


--
-- Name: product_code_field_values; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_code_field_values (
    id integer NOT NULL,
    product_code_id integer NOT NULL,
    field_id integer NOT NULL,
    option_id integer,
    custom_value character varying(100)
);


--
-- Name: product_code_field_values_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_code_field_values_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_code_field_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_field_values_id_seq OWNED BY public.product_code_field_values.id;


--
-- Name: product_code_fields; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: product_code_fields_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_code_fields_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_code_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_fields_id_seq OWNED BY public.product_code_fields.id;


--
-- Name: product_codes; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: product_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_codes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_codes_id_seq OWNED BY public.product_codes.id;


--
-- Name: product_regions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product_regions (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code_letter character varying(1) NOT NULL,
    description text,
    created_at timestamp without time zone
);


--
-- Name: product_regions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_regions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_regions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_regions_id_seq OWNED BY public.product_regions.id;


--
-- Name: product_subcategories; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: product_subcategories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_subcategories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_subcategories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_subcategories_id_seq OWNED BY public.product_subcategories.id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: project_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_members (
    id integer NOT NULL,
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    role character varying(50) NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: project_members_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_members_id_seq OWNED BY public.project_members.id;


--
-- Name: project_rating_records; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: project_rating_records_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_rating_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_rating_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_rating_records_id_seq OWNED BY public.project_rating_records.id;


--
-- Name: project_scoring_config; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: project_scoring_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_scoring_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_scoring_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_scoring_config_id_seq OWNED BY public.project_scoring_config.id;


--
-- Name: project_scoring_records; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: project_scoring_records_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_scoring_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_scoring_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_scoring_records_id_seq OWNED BY public.project_scoring_records.id;


--
-- Name: project_stage_history; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: project_stage_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_stage_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_stage_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_stage_history_id_seq OWNED BY public.project_stage_history.id;


--
-- Name: project_total_scores; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: project_total_scores_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_total_scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_total_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_total_scores_id_seq OWNED BY public.project_total_scores.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: purchase_order_details; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: purchase_order_details_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.purchase_order_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: purchase_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_order_details_id_seq OWNED BY public.purchase_order_details.id;


--
-- Name: purchase_orders; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: purchase_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.purchase_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: purchase_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_orders_id_seq OWNED BY public.purchase_orders.id;


--
-- Name: quotation_details; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: quotation_details_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quotation_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quotation_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotation_details_id_seq OWNED BY public.quotation_details.id;


--
-- Name: quotations; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: quotations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quotations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotations_id_seq OWNED BY public.quotations.id;


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: role_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.role_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- Name: settlement_details; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: settlement_details_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.settlement_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: settlement_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_details_id_seq OWNED BY public.settlement_details.id;


--
-- Name: settlement_order_details; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN settlement_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.pricing_order_id IS '批价单ID';


--
-- Name: COLUMN settlement_order_details.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_name IS '产品名称';


--
-- Name: COLUMN settlement_order_details.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_model IS '产品型号';


--
-- Name: COLUMN settlement_order_details.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_desc IS '产品描述';


--
-- Name: COLUMN settlement_order_details.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.brand IS '品牌';


--
-- Name: COLUMN settlement_order_details.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.unit IS '单位';


--
-- Name: COLUMN settlement_order_details.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_mn IS '产品MN编码';


--
-- Name: COLUMN settlement_order_details.market_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.market_price IS '市场价';


--
-- Name: COLUMN settlement_order_details.unit_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.unit_price IS '单价';


--
-- Name: COLUMN settlement_order_details.quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.quantity IS '数量';


--
-- Name: COLUMN settlement_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.discount_rate IS '折扣率';


--
-- Name: COLUMN settlement_order_details.total_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.total_price IS '小计金额';


--
-- Name: COLUMN settlement_order_details.pricing_detail_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.pricing_detail_id IS '关联批价单明细ID';


--
-- Name: COLUMN settlement_order_details.settlement_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_order_id IS '结算单ID';


--
-- Name: COLUMN settlement_order_details.settlement_company_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_company_id IS '结算目标公司ID';


--
-- Name: COLUMN settlement_order_details.settlement_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_status IS '结算状态: pending, completed';


--
-- Name: COLUMN settlement_order_details.settlement_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_date IS '结算完成时间';


--
-- Name: COLUMN settlement_order_details.settlement_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_notes IS '结算备注';


--
-- Name: settlement_order_details_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.settlement_order_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: settlement_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_order_details_id_seq OWNED BY public.settlement_order_details.id;


--
-- Name: settlement_orders; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN settlement_orders.order_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.order_number IS '结算单号';


--
-- Name: COLUMN settlement_orders.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.pricing_order_id IS '关联批价单ID';


--
-- Name: COLUMN settlement_orders.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.project_id IS '项目ID';


--
-- Name: COLUMN settlement_orders.quotation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.quotation_id IS '报价单ID';


--
-- Name: COLUMN settlement_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.distributor_id IS '分销商ID';


--
-- Name: COLUMN settlement_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.dealer_id IS '经销商ID（辅助信息）';


--
-- Name: COLUMN settlement_orders.total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.total_amount IS '结算总金额';


--
-- Name: COLUMN settlement_orders.total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.total_discount_rate IS '结算总折扣率';


--
-- Name: COLUMN settlement_orders.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.status IS '结算单状态';


--
-- Name: COLUMN settlement_orders.approved_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.approved_by IS '批准人';


--
-- Name: COLUMN settlement_orders.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.approved_at IS '批准时间';


--
-- Name: COLUMN settlement_orders.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.created_by IS '创建人';


--
-- Name: COLUMN settlement_orders.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.created_at IS '创建时间';


--
-- Name: COLUMN settlement_orders.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.updated_at IS '更新时间';


--
-- Name: settlement_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.settlement_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: settlement_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_orders_id_seq OWNED BY public.settlement_orders.id;


--
-- Name: settlements; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: settlements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.settlements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: settlements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlements_id_seq OWNED BY public.settlements.id;


--
-- Name: solution_manager_email_settings; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN solution_manager_email_settings.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.user_id IS '解决方案经理用户ID';


--
-- Name: COLUMN solution_manager_email_settings.quotation_created; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_created IS '报价单新建通知';


--
-- Name: COLUMN solution_manager_email_settings.quotation_updated; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_updated IS '报价单更新通知';


--
-- Name: COLUMN solution_manager_email_settings.project_created; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_created IS '项目新建通知';


--
-- Name: COLUMN solution_manager_email_settings.project_stage_changed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_stage_changed IS '项目阶段推进通知';


--
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.solution_manager_email_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.solution_manager_email_settings_id_seq OWNED BY public.solution_manager_email_settings.id;


--
-- Name: system_metrics; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN system_metrics.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.version_id IS '版本ID';


--
-- Name: COLUMN system_metrics.avg_response_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.avg_response_time IS '平均响应时间（毫秒）';


--
-- Name: COLUMN system_metrics.max_response_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.max_response_time IS '最大响应时间（毫秒）';


--
-- Name: COLUMN system_metrics.error_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.error_rate IS '错误率（百分比）';


--
-- Name: COLUMN system_metrics.active_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.active_users IS '活跃用户数';


--
-- Name: COLUMN system_metrics.total_requests; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.total_requests IS '总请求数';


--
-- Name: COLUMN system_metrics.database_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.database_size IS '数据库大小（字节）';


--
-- Name: COLUMN system_metrics.cpu_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.cpu_usage IS 'CPU使用率（百分比）';


--
-- Name: COLUMN system_metrics.memory_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.memory_usage IS '内存使用率（百分比）';


--
-- Name: COLUMN system_metrics.disk_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.disk_usage IS '磁盘使用率（百分比）';


--
-- Name: COLUMN system_metrics.recorded_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.recorded_at IS '记录时间';


--
-- Name: system_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.system_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: system_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_metrics_id_seq OWNED BY public.system_metrics.id;


--
-- Name: system_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_settings (
    id integer NOT NULL,
    key character varying(100) NOT NULL,
    value text,
    description character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: system_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.system_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: system_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_settings_id_seq OWNED BY public.system_settings.id;


--
-- Name: upgrade_logs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN upgrade_logs.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.version_id IS '版本ID';


--
-- Name: COLUMN upgrade_logs.from_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.from_version IS '升级前版本';


--
-- Name: COLUMN upgrade_logs.to_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.to_version IS '升级后版本';


--
-- Name: COLUMN upgrade_logs.upgrade_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_date IS '升级时间';


--
-- Name: COLUMN upgrade_logs.upgrade_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_type IS '升级类型：manual/automatic';


--
-- Name: COLUMN upgrade_logs.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.status IS '升级状态：success/failed/rollback';


--
-- Name: COLUMN upgrade_logs.upgrade_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_notes IS '升级说明';


--
-- Name: COLUMN upgrade_logs.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.error_message IS '错误信息（如果升级失败）';


--
-- Name: COLUMN upgrade_logs.duration_seconds; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.duration_seconds IS '升级耗时（秒）';


--
-- Name: COLUMN upgrade_logs.operator_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.operator_id IS '操作人员ID';


--
-- Name: COLUMN upgrade_logs.operator_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.operator_name IS '操作人员姓名';


--
-- Name: COLUMN upgrade_logs.environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.environment IS '升级环境';


--
-- Name: COLUMN upgrade_logs.server_info; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.server_info IS '服务器信息';


--
-- Name: upgrade_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.upgrade_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: upgrade_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.upgrade_logs_id_seq OWNED BY public.upgrade_logs.id;


--
-- Name: user_event_subscriptions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN user_event_subscriptions.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.user_id IS '订阅者用户ID';


--
-- Name: COLUMN user_event_subscriptions.target_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.target_user_id IS '被订阅的用户ID';


--
-- Name: COLUMN user_event_subscriptions.event_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.event_id IS '事件ID';


--
-- Name: COLUMN user_event_subscriptions.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.enabled IS '是否启用订阅';


--
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_event_subscriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_event_subscriptions_id_seq OWNED BY public.user_event_subscriptions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: version_records; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN version_records.version_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.version_number IS '版本号，如1.0.0';


--
-- Name: COLUMN version_records.version_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.version_name IS '版本名称';


--
-- Name: COLUMN version_records.release_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.release_date IS '发布日期';


--
-- Name: COLUMN version_records.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.description IS '版本描述';


--
-- Name: COLUMN version_records.is_current; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.is_current IS '是否为当前版本';


--
-- Name: COLUMN version_records.environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.environment IS '环境：development/production';


--
-- Name: COLUMN version_records.total_features; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_features IS '新增功能数量';


--
-- Name: COLUMN version_records.total_fixes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_fixes IS '修复问题数量';


--
-- Name: COLUMN version_records.total_improvements; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_improvements IS '改进数量';


--
-- Name: COLUMN version_records.git_commit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.git_commit IS 'Git提交哈希';


--
-- Name: COLUMN version_records.build_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.build_number IS '构建号';


--
-- Name: COLUMN version_records.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.created_at IS '创建时间';


--
-- Name: COLUMN version_records.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.updated_at IS '更新时间';


--
-- Name: version_records_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.version_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: version_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.version_records_id_seq OWNED BY public.version_records.id;


--
-- Name: action_reply id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply ALTER COLUMN id SET DEFAULT nextval('public.action_reply_id_seq'::regclass);


--
-- Name: actions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions ALTER COLUMN id SET DEFAULT nextval('public.actions_id_seq'::regclass);


--
-- Name: affiliations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations ALTER COLUMN id SET DEFAULT nextval('public.affiliations_id_seq'::regclass);


--
-- Name: approval_instance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance ALTER COLUMN id SET DEFAULT nextval('public.approval_instance_id_seq'::regclass);


--
-- Name: approval_process_template id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template ALTER COLUMN id SET DEFAULT nextval('public.approval_process_template_id_seq'::regclass);


--
-- Name: approval_step id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step ALTER COLUMN id SET DEFAULT nextval('public.approval_step_id_seq'::regclass);


--
-- Name: change_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs ALTER COLUMN id SET DEFAULT nextval('public.change_logs_id_seq'::regclass);


--
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- Name: contacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts ALTER COLUMN id SET DEFAULT nextval('public.contacts_id_seq'::regclass);


--
-- Name: dev_product_specs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs ALTER COLUMN id SET DEFAULT nextval('public.dev_product_specs_id_seq'::regclass);


--
-- Name: dev_products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products ALTER COLUMN id SET DEFAULT nextval('public.dev_products_id_seq'::regclass);


--
-- Name: dictionaries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries ALTER COLUMN id SET DEFAULT nextval('public.dictionaries_id_seq'::regclass);


--
-- Name: event_registry id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry ALTER COLUMN id SET DEFAULT nextval('public.event_registry_id_seq'::regclass);


--
-- Name: feature_changes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes ALTER COLUMN id SET DEFAULT nextval('public.feature_changes_id_seq'::regclass);


--
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- Name: inventory_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions ALTER COLUMN id SET DEFAULT nextval('public.inventory_transactions_id_seq'::regclass);


--
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- Name: pricing_order_approval_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_approval_records_id_seq'::regclass);


--
-- Name: pricing_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_details_id_seq'::regclass);


--
-- Name: pricing_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders ALTER COLUMN id SET DEFAULT nextval('public.pricing_orders_id_seq'::regclass);


--
-- Name: product_categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories ALTER COLUMN id SET DEFAULT nextval('public.product_categories_id_seq'::regclass);


--
-- Name: product_code_field_options id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_options_id_seq'::regclass);


--
-- Name: product_code_field_values id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_values_id_seq'::regclass);


--
-- Name: product_code_fields id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields ALTER COLUMN id SET DEFAULT nextval('public.product_code_fields_id_seq'::regclass);


--
-- Name: product_codes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes ALTER COLUMN id SET DEFAULT nextval('public.product_codes_id_seq'::regclass);


--
-- Name: product_regions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_regions ALTER COLUMN id SET DEFAULT nextval('public.product_regions_id_seq'::regclass);


--
-- Name: product_subcategories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories ALTER COLUMN id SET DEFAULT nextval('public.product_subcategories_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: project_members id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members ALTER COLUMN id SET DEFAULT nextval('public.project_members_id_seq'::regclass);


--
-- Name: project_rating_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records ALTER COLUMN id SET DEFAULT nextval('public.project_rating_records_id_seq'::regclass);


--
-- Name: project_scoring_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_config_id_seq'::regclass);


--
-- Name: project_scoring_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_records_id_seq'::regclass);


--
-- Name: project_stage_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history ALTER COLUMN id SET DEFAULT nextval('public.project_stage_history_id_seq'::regclass);


--
-- Name: project_total_scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores ALTER COLUMN id SET DEFAULT nextval('public.project_total_scores_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: purchase_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details ALTER COLUMN id SET DEFAULT nextval('public.purchase_order_details_id_seq'::regclass);


--
-- Name: purchase_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders ALTER COLUMN id SET DEFAULT nextval('public.purchase_orders_id_seq'::regclass);


--
-- Name: quotation_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details ALTER COLUMN id SET DEFAULT nextval('public.quotation_details_id_seq'::regclass);


--
-- Name: quotations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations ALTER COLUMN id SET DEFAULT nextval('public.quotations_id_seq'::regclass);


--
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- Name: settlement_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_details_id_seq'::regclass);


--
-- Name: settlement_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_order_details_id_seq'::regclass);


--
-- Name: settlement_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders ALTER COLUMN id SET DEFAULT nextval('public.settlement_orders_id_seq'::regclass);


--
-- Name: settlements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements ALTER COLUMN id SET DEFAULT nextval('public.settlements_id_seq'::regclass);


--
-- Name: solution_manager_email_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings ALTER COLUMN id SET DEFAULT nextval('public.solution_manager_email_settings_id_seq'::regclass);


--
-- Name: system_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics ALTER COLUMN id SET DEFAULT nextval('public.system_metrics_id_seq'::regclass);


--
-- Name: system_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings ALTER COLUMN id SET DEFAULT nextval('public.system_settings_id_seq'::regclass);


--
-- Name: upgrade_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs ALTER COLUMN id SET DEFAULT nextval('public.upgrade_logs_id_seq'::regclass);


--
-- Name: user_event_subscriptions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions ALTER COLUMN id SET DEFAULT nextval('public.user_event_subscriptions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: version_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records ALTER COLUMN id SET DEFAULT nextval('public.version_records_id_seq'::regclass);


--
-- Name: action_reply action_reply_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_pkey PRIMARY KEY (id);


--
-- Name: actions actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_pkey PRIMARY KEY (id);


--
-- Name: affiliations affiliations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: approval_instance approval_instance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_pkey PRIMARY KEY (id);


--
-- Name: approval_process_template approval_process_template_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_pkey PRIMARY KEY (id);


--
-- Name: approval_record approval_record_temp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_temp_pkey PRIMARY KEY (id);


--
-- Name: approval_step approval_step_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_pkey PRIMARY KEY (id);


--
-- Name: change_logs change_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs
    ADD CONSTRAINT change_logs_pkey PRIMARY KEY (id);


--
-- Name: companies companies_company_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_company_code_key UNIQUE (company_code);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (id);


--
-- Name: dev_product_specs dev_product_specs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs
    ADD CONSTRAINT dev_product_specs_pkey PRIMARY KEY (id);


--
-- Name: dev_products dev_products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_pkey PRIMARY KEY (id);


--
-- Name: dictionaries dictionaries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT dictionaries_pkey PRIMARY KEY (id);


--
-- Name: event_registry event_registry_event_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_event_key_key UNIQUE (event_key);


--
-- Name: event_registry event_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_pkey PRIMARY KEY (id);


--
-- Name: feature_changes feature_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_pkey PRIMARY KEY (id);


--
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (id);


--
-- Name: inventory_transactions inventory_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: pricing_order_approval_records pricing_order_approval_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_pkey PRIMARY KEY (id);


--
-- Name: pricing_order_details pricing_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details
    ADD CONSTRAINT pricing_order_details_pkey PRIMARY KEY (id);


--
-- Name: pricing_orders pricing_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_order_number_key UNIQUE (order_number);


--
-- Name: pricing_orders pricing_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_pkey PRIMARY KEY (id);


--
-- Name: product_categories product_categories_code_letter_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_code_letter_key UNIQUE (code_letter);


--
-- Name: product_categories product_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_pkey PRIMARY KEY (id);


--
-- Name: product_code_field_options product_code_field_options_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options
    ADD CONSTRAINT product_code_field_options_pkey PRIMARY KEY (id);


--
-- Name: product_code_field_values product_code_field_values_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_pkey PRIMARY KEY (id);


--
-- Name: product_code_fields product_code_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields
    ADD CONSTRAINT product_code_fields_pkey PRIMARY KEY (id);


--
-- Name: product_codes product_codes_full_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_full_code_key UNIQUE (full_code);


--
-- Name: product_codes product_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_pkey PRIMARY KEY (id);


--
-- Name: product_regions product_regions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_regions
    ADD CONSTRAINT product_regions_pkey PRIMARY KEY (id);


--
-- Name: product_subcategories product_subcategories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT product_subcategories_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: products products_product_mn_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_product_mn_key UNIQUE (product_mn);


--
-- Name: project_members project_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (id);


--
-- Name: project_rating_records project_rating_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_pkey PRIMARY KEY (id);


--
-- Name: project_scoring_config project_scoring_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config
    ADD CONSTRAINT project_scoring_config_pkey PRIMARY KEY (id);


--
-- Name: project_scoring_records project_scoring_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_pkey PRIMARY KEY (id);


--
-- Name: project_stage_history project_stage_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history
    ADD CONSTRAINT project_stage_history_pkey PRIMARY KEY (id);


--
-- Name: project_total_scores project_total_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_pkey PRIMARY KEY (id);


--
-- Name: project_total_scores project_total_scores_project_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_project_id_key UNIQUE (project_id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: purchase_order_details purchase_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_pkey PRIMARY KEY (id);


--
-- Name: purchase_orders purchase_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_order_number_key UNIQUE (order_number);


--
-- Name: purchase_orders purchase_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_pkey PRIMARY KEY (id);


--
-- Name: quotation_details quotation_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details
    ADD CONSTRAINT quotation_details_pkey PRIMARY KEY (id);


--
-- Name: quotations quotations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_pkey PRIMARY KEY (id);


--
-- Name: quotations quotations_quotation_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_quotation_number_key UNIQUE (quotation_number);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- Name: settlement_details settlement_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_pkey PRIMARY KEY (id);


--
-- Name: settlement_order_details settlement_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pkey PRIMARY KEY (id);


--
-- Name: settlement_orders settlement_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_order_number_key UNIQUE (order_number);


--
-- Name: settlement_orders settlement_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_pkey PRIMARY KEY (id);


--
-- Name: settlements settlements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_pkey PRIMARY KEY (id);


--
-- Name: settlements settlements_settlement_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_settlement_number_key UNIQUE (settlement_number);


--
-- Name: solution_manager_email_settings solution_manager_email_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT solution_manager_email_settings_pkey PRIMARY KEY (id);


--
-- Name: system_metrics system_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (id);


--
-- Name: affiliations uix_owner_viewer; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT uix_owner_viewer UNIQUE (owner_id, viewer_id);


--
-- Name: role_permissions uix_role_module; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT uix_role_module UNIQUE (role, module);


--
-- Name: dictionaries uix_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT uix_type_key UNIQUE (type, key);


--
-- Name: permissions uix_user_module; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT uix_user_module UNIQUE (user_id, module);


--
-- Name: inventory unique_company_product_inventory; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT unique_company_product_inventory UNIQUE (company_id, product_id);


--
-- Name: upgrade_logs upgrade_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_pkey PRIMARY KEY (id);


--
-- Name: project_rating_records uq_project_user_rating; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT uq_project_user_rating UNIQUE (project_id, user_id);


--
-- Name: project_scoring_config uq_scoring_config; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config
    ADD CONSTRAINT uq_scoring_config UNIQUE (category, field_name);


--
-- Name: project_scoring_records uq_scoring_record_with_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT uq_scoring_record_with_user UNIQUE (project_id, category, field_name, awarded_by);


--
-- Name: solution_manager_email_settings uq_solution_manager_email_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT uq_solution_manager_email_user UNIQUE (user_id);


--
-- Name: product_subcategories uq_subcategory_code_letter; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT uq_subcategory_code_letter UNIQUE (category_id, code_letter);


--
-- Name: user_event_subscriptions uq_user_target_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT uq_user_target_event UNIQUE (user_id, target_user_id, event_id);


--
-- Name: user_event_subscriptions user_event_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: users users_wechat_openid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_wechat_openid_key UNIQUE (wechat_openid);


--
-- Name: version_records version_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records
    ADD CONSTRAINT version_records_pkey PRIMARY KEY (id);


--
-- Name: version_records version_records_version_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records
    ADD CONSTRAINT version_records_version_number_key UNIQUE (version_number);


--
-- Name: ix_project_stage_history_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_stage_history_project_id ON public.project_stage_history USING btree (project_id);


--
-- Name: ix_projects_authorization_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_authorization_code ON public.projects USING btree (authorization_code);


--
-- Name: ix_projects_project_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_project_name ON public.projects USING btree (project_name);


--
-- Name: ix_system_settings_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_system_settings_key ON public.system_settings USING btree (key);


--
-- Name: action_reply action_reply_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.actions(id);


--
-- Name: action_reply action_reply_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: action_reply action_reply_parent_reply_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_parent_reply_id_fkey FOREIGN KEY (parent_reply_id) REFERENCES public.action_reply(id);


--
-- Name: actions actions_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: actions actions_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- Name: actions actions_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: actions actions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: affiliations affiliations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: affiliations affiliations_viewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_viewer_id_fkey FOREIGN KEY (viewer_id) REFERENCES public.users(id);


--
-- Name: approval_instance approval_instance_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: approval_instance approval_instance_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- Name: approval_process_template approval_process_template_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: approval_record approval_record_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES public.approval_instance(id);


--
-- Name: approval_step approval_step_approver_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_approver_user_id_fkey FOREIGN KEY (approver_user_id) REFERENCES public.users(id);


--
-- Name: approval_step approval_step_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- Name: change_logs change_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs
    ADD CONSTRAINT change_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: companies companies_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: contacts contacts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: contacts contacts_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: dev_product_specs dev_product_specs_dev_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs
    ADD CONSTRAINT dev_product_specs_dev_product_id_fkey FOREIGN KEY (dev_product_id) REFERENCES public.dev_products(id);


--
-- Name: dev_products dev_products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- Name: dev_products dev_products_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: dev_products dev_products_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: dev_products dev_products_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.product_regions(id);


--
-- Name: dev_products dev_products_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- Name: feature_changes feature_changes_developer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_developer_id_fkey FOREIGN KEY (developer_id) REFERENCES public.users(id);


--
-- Name: feature_changes feature_changes_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- Name: approval_record fk_approval_record_approver_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT fk_approval_record_approver_id FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- Name: approval_record fk_approval_record_step_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT fk_approval_record_step_id FOREIGN KEY (step_id) REFERENCES public.approval_step(id);


--
-- Name: settlement_order_details fk_settlement_order_details_settlement_company; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT fk_settlement_order_details_settlement_company FOREIGN KEY (settlement_company_id) REFERENCES public.companies(id);


--
-- Name: inventory inventory_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: inventory inventory_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: inventory inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: inventory_transactions inventory_transactions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: inventory_transactions inventory_transactions_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- Name: permissions permissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: pricing_order_approval_records pricing_order_approval_records_approver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_approver_id_fkey FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- Name: pricing_order_approval_records pricing_order_approval_records_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- Name: pricing_order_details pricing_order_details_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details
    ADD CONSTRAINT pricing_order_details_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- Name: pricing_orders pricing_orders_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: pricing_orders pricing_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: pricing_orders pricing_orders_dealer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_dealer_id_fkey FOREIGN KEY (dealer_id) REFERENCES public.companies(id);


--
-- Name: pricing_orders pricing_orders_distributor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_distributor_id_fkey FOREIGN KEY (distributor_id) REFERENCES public.companies(id);


--
-- Name: pricing_orders pricing_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: pricing_orders pricing_orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- Name: product_code_field_options product_code_field_options_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options
    ADD CONSTRAINT product_code_field_options_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.product_code_fields(id);


--
-- Name: product_code_field_values product_code_field_values_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.product_code_fields(id);


--
-- Name: product_code_field_values product_code_field_values_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_option_id_fkey FOREIGN KEY (option_id) REFERENCES public.product_code_field_options(id);


--
-- Name: product_code_field_values product_code_field_values_product_code_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_product_code_id_fkey FOREIGN KEY (product_code_id) REFERENCES public.product_codes(id);


--
-- Name: product_code_fields product_code_fields_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields
    ADD CONSTRAINT product_code_fields_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- Name: product_codes product_codes_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- Name: product_codes product_codes_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: product_codes product_codes_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: product_codes product_codes_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- Name: product_subcategories product_subcategories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT product_subcategories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- Name: products products_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: project_members project_members_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: project_members project_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: project_rating_records project_rating_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_rating_records project_rating_records_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: project_scoring_records project_scoring_records_awarded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_awarded_by_fkey FOREIGN KEY (awarded_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: project_scoring_records project_scoring_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_stage_history project_stage_history_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history
    ADD CONSTRAINT project_stage_history_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: project_total_scores project_total_scores_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: projects projects_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- Name: projects projects_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: projects projects_vendor_sales_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_vendor_sales_manager_id_fkey FOREIGN KEY (vendor_sales_manager_id) REFERENCES public.users(id);


--
-- Name: purchase_order_details purchase_order_details_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.purchase_orders(id);


--
-- Name: purchase_order_details purchase_order_details_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: purchase_orders purchase_orders_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- Name: purchase_orders purchase_orders_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: purchase_orders purchase_orders_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: quotation_details quotation_details_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details
    ADD CONSTRAINT quotation_details_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- Name: quotations quotations_confirmed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_confirmed_by_fkey FOREIGN KEY (confirmed_by) REFERENCES public.users(id);


--
-- Name: quotations quotations_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- Name: quotations quotations_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- Name: quotations quotations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: quotations quotations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: settlement_details settlement_details_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- Name: settlement_details settlement_details_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: settlement_details settlement_details_settlement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_settlement_id_fkey FOREIGN KEY (settlement_id) REFERENCES public.settlements(id);


--
-- Name: settlement_order_details settlement_order_details_pricing_detail_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pricing_detail_id_fkey FOREIGN KEY (pricing_detail_id) REFERENCES public.pricing_order_details(id);


--
-- Name: settlement_order_details settlement_order_details_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- Name: settlement_order_details settlement_order_details_settlement_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_settlement_order_id_fkey FOREIGN KEY (settlement_order_id) REFERENCES public.settlement_orders(id);


--
-- Name: settlement_orders settlement_orders_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: settlement_orders settlement_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: settlement_orders settlement_orders_dealer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_dealer_id_fkey FOREIGN KEY (dealer_id) REFERENCES public.companies(id);


--
-- Name: settlement_orders settlement_orders_distributor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_distributor_id_fkey FOREIGN KEY (distributor_id) REFERENCES public.companies(id);


--
-- Name: settlement_orders settlement_orders_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- Name: settlement_orders settlement_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: settlement_orders settlement_orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- Name: settlements settlements_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- Name: settlements settlements_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: settlements settlements_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: solution_manager_email_settings solution_manager_email_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT solution_manager_email_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: system_metrics system_metrics_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- Name: upgrade_logs upgrade_logs_operator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_operator_id_fkey FOREIGN KEY (operator_id) REFERENCES public.users(id);


--
-- Name: upgrade_logs upgrade_logs_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- Name: user_event_subscriptions user_event_subscriptions_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.event_registry(id);


--
-- Name: user_event_subscriptions user_event_subscriptions_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id);


--
-- Name: user_event_subscriptions user_event_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

