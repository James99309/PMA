--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Debian 16.9-1.pgdg120+1)
-- Dumped by pg_dump version 16.9 (Homebrew)

-- Started on 2025-06-22 18:52:22 +08

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

ALTER TABLE ONLY public.user_event_subscriptions DROP CONSTRAINT user_event_subscriptions_user_id_fkey;
ALTER TABLE ONLY public.user_event_subscriptions DROP CONSTRAINT user_event_subscriptions_target_user_id_fkey;
ALTER TABLE ONLY public.user_event_subscriptions DROP CONSTRAINT user_event_subscriptions_event_id_fkey;
ALTER TABLE ONLY public.upgrade_logs DROP CONSTRAINT upgrade_logs_version_id_fkey;
ALTER TABLE ONLY public.upgrade_logs DROP CONSTRAINT upgrade_logs_operator_id_fkey;
ALTER TABLE ONLY public.system_metrics DROP CONSTRAINT system_metrics_version_id_fkey;
ALTER TABLE ONLY public.solution_manager_email_settings DROP CONSTRAINT solution_manager_email_settings_user_id_fkey;
ALTER TABLE ONLY public.settlements DROP CONSTRAINT settlements_created_by_id_fkey;
ALTER TABLE ONLY public.settlements DROP CONSTRAINT settlements_company_id_fkey;
ALTER TABLE ONLY public.settlements DROP CONSTRAINT settlements_approved_by_id_fkey;
ALTER TABLE ONLY public.settlement_orders DROP CONSTRAINT settlement_orders_quotation_id_fkey;
ALTER TABLE ONLY public.settlement_orders DROP CONSTRAINT settlement_orders_project_id_fkey;
ALTER TABLE ONLY public.settlement_orders DROP CONSTRAINT settlement_orders_pricing_order_id_fkey;
ALTER TABLE ONLY public.settlement_orders DROP CONSTRAINT settlement_orders_distributor_id_fkey;
ALTER TABLE ONLY public.settlement_orders DROP CONSTRAINT settlement_orders_dealer_id_fkey;
ALTER TABLE ONLY public.settlement_orders DROP CONSTRAINT settlement_orders_created_by_fkey;
ALTER TABLE ONLY public.settlement_orders DROP CONSTRAINT settlement_orders_approved_by_fkey;
ALTER TABLE ONLY public.settlement_order_details DROP CONSTRAINT settlement_order_details_settlement_order_id_fkey;
ALTER TABLE ONLY public.settlement_order_details DROP CONSTRAINT settlement_order_details_pricing_order_id_fkey;
ALTER TABLE ONLY public.settlement_order_details DROP CONSTRAINT settlement_order_details_pricing_detail_id_fkey;
ALTER TABLE ONLY public.settlement_details DROP CONSTRAINT settlement_details_settlement_id_fkey;
ALTER TABLE ONLY public.settlement_details DROP CONSTRAINT settlement_details_product_id_fkey;
ALTER TABLE ONLY public.settlement_details DROP CONSTRAINT settlement_details_inventory_id_fkey;
ALTER TABLE ONLY public.quotations DROP CONSTRAINT quotations_project_id_fkey;
ALTER TABLE ONLY public.quotations DROP CONSTRAINT quotations_owner_id_fkey;
ALTER TABLE ONLY public.quotations DROP CONSTRAINT quotations_locked_by_fkey;
ALTER TABLE ONLY public.quotations DROP CONSTRAINT quotations_contact_id_fkey;
ALTER TABLE ONLY public.quotations DROP CONSTRAINT quotations_confirmed_by_fkey;
ALTER TABLE ONLY public.quotation_details DROP CONSTRAINT quotation_details_quotation_id_fkey;
ALTER TABLE ONLY public.purchase_orders DROP CONSTRAINT purchase_orders_created_by_id_fkey;
ALTER TABLE ONLY public.purchase_orders DROP CONSTRAINT purchase_orders_company_id_fkey;
ALTER TABLE ONLY public.purchase_orders DROP CONSTRAINT purchase_orders_approved_by_id_fkey;
ALTER TABLE ONLY public.purchase_order_details DROP CONSTRAINT purchase_order_details_product_id_fkey;
ALTER TABLE ONLY public.purchase_order_details DROP CONSTRAINT purchase_order_details_order_id_fkey;
ALTER TABLE ONLY public.projects DROP CONSTRAINT projects_vendor_sales_manager_id_fkey;
ALTER TABLE ONLY public.projects DROP CONSTRAINT projects_owner_id_fkey;
ALTER TABLE ONLY public.projects DROP CONSTRAINT projects_locked_by_fkey;
ALTER TABLE ONLY public.project_total_scores DROP CONSTRAINT project_total_scores_project_id_fkey;
ALTER TABLE ONLY public.project_stage_history DROP CONSTRAINT project_stage_history_project_id_fkey;
ALTER TABLE ONLY public.project_scoring_records DROP CONSTRAINT project_scoring_records_project_id_fkey;
ALTER TABLE ONLY public.project_scoring_records DROP CONSTRAINT project_scoring_records_awarded_by_fkey;
ALTER TABLE ONLY public.project_rating_records DROP CONSTRAINT project_rating_records_user_id_fkey;
ALTER TABLE ONLY public.project_rating_records DROP CONSTRAINT project_rating_records_project_id_fkey;
ALTER TABLE ONLY public.project_members DROP CONSTRAINT project_members_user_id_fkey;
ALTER TABLE ONLY public.project_members DROP CONSTRAINT project_members_project_id_fkey;
ALTER TABLE ONLY public.products DROP CONSTRAINT products_owner_id_fkey;
ALTER TABLE ONLY public.product_subcategories DROP CONSTRAINT product_subcategories_category_id_fkey;
ALTER TABLE ONLY public.product_codes DROP CONSTRAINT product_codes_subcategory_id_fkey;
ALTER TABLE ONLY public.product_codes DROP CONSTRAINT product_codes_product_id_fkey;
ALTER TABLE ONLY public.product_codes DROP CONSTRAINT product_codes_created_by_fkey;
ALTER TABLE ONLY public.product_codes DROP CONSTRAINT product_codes_category_id_fkey;
ALTER TABLE ONLY public.product_code_fields DROP CONSTRAINT product_code_fields_subcategory_id_fkey;
ALTER TABLE ONLY public.product_code_field_values DROP CONSTRAINT product_code_field_values_product_code_id_fkey;
ALTER TABLE ONLY public.product_code_field_values DROP CONSTRAINT product_code_field_values_option_id_fkey;
ALTER TABLE ONLY public.product_code_field_values DROP CONSTRAINT product_code_field_values_field_id_fkey;
ALTER TABLE ONLY public.product_code_field_options DROP CONSTRAINT product_code_field_options_field_id_fkey;
ALTER TABLE ONLY public.pricing_orders DROP CONSTRAINT pricing_orders_quotation_id_fkey;
ALTER TABLE ONLY public.pricing_orders DROP CONSTRAINT pricing_orders_project_id_fkey;
ALTER TABLE ONLY public.pricing_orders DROP CONSTRAINT pricing_orders_distributor_id_fkey;
ALTER TABLE ONLY public.pricing_orders DROP CONSTRAINT pricing_orders_dealer_id_fkey;
ALTER TABLE ONLY public.pricing_orders DROP CONSTRAINT pricing_orders_created_by_fkey;
ALTER TABLE ONLY public.pricing_orders DROP CONSTRAINT pricing_orders_approved_by_fkey;
ALTER TABLE ONLY public.pricing_order_details DROP CONSTRAINT pricing_order_details_pricing_order_id_fkey;
ALTER TABLE ONLY public.pricing_order_approval_records DROP CONSTRAINT pricing_order_approval_records_pricing_order_id_fkey;
ALTER TABLE ONLY public.pricing_order_approval_records DROP CONSTRAINT pricing_order_approval_records_approver_id_fkey;
ALTER TABLE ONLY public.permissions DROP CONSTRAINT permissions_user_id_fkey;
ALTER TABLE ONLY public.inventory_transactions DROP CONSTRAINT inventory_transactions_inventory_id_fkey;
ALTER TABLE ONLY public.inventory_transactions DROP CONSTRAINT inventory_transactions_created_by_id_fkey;
ALTER TABLE ONLY public.inventory DROP CONSTRAINT inventory_product_id_fkey;
ALTER TABLE ONLY public.inventory DROP CONSTRAINT inventory_created_by_id_fkey;
ALTER TABLE ONLY public.inventory DROP CONSTRAINT inventory_company_id_fkey;
ALTER TABLE ONLY public.settlement_order_details DROP CONSTRAINT fk_settlement_order_details_settlement_company;
ALTER TABLE ONLY public.approval_record DROP CONSTRAINT fk_approval_record_step_id;
ALTER TABLE ONLY public.approval_record DROP CONSTRAINT fk_approval_record_approver_id;
ALTER TABLE ONLY public.feature_changes DROP CONSTRAINT feature_changes_version_id_fkey;
ALTER TABLE ONLY public.feature_changes DROP CONSTRAINT feature_changes_developer_id_fkey;
ALTER TABLE ONLY public.dev_products DROP CONSTRAINT dev_products_subcategory_id_fkey;
ALTER TABLE ONLY public.dev_products DROP CONSTRAINT dev_products_region_id_fkey;
ALTER TABLE ONLY public.dev_products DROP CONSTRAINT dev_products_owner_id_fkey;
ALTER TABLE ONLY public.dev_products DROP CONSTRAINT dev_products_created_by_fkey;
ALTER TABLE ONLY public.dev_products DROP CONSTRAINT dev_products_category_id_fkey;
ALTER TABLE ONLY public.dev_product_specs DROP CONSTRAINT dev_product_specs_dev_product_id_fkey;
ALTER TABLE ONLY public.contacts DROP CONSTRAINT contacts_owner_id_fkey;
ALTER TABLE ONLY public.contacts DROP CONSTRAINT contacts_company_id_fkey;
ALTER TABLE ONLY public.companies DROP CONSTRAINT companies_owner_id_fkey;
ALTER TABLE ONLY public.change_logs DROP CONSTRAINT change_logs_user_id_fkey;
ALTER TABLE ONLY public.approval_step DROP CONSTRAINT approval_step_process_id_fkey;
ALTER TABLE ONLY public.approval_step DROP CONSTRAINT approval_step_approver_user_id_fkey;
ALTER TABLE ONLY public.approval_record DROP CONSTRAINT approval_record_instance_id_fkey;
ALTER TABLE ONLY public.approval_process_template DROP CONSTRAINT approval_process_template_created_by_fkey;
ALTER TABLE ONLY public.approval_instance DROP CONSTRAINT approval_instance_process_id_fkey;
ALTER TABLE ONLY public.approval_instance DROP CONSTRAINT approval_instance_created_by_fkey;
ALTER TABLE ONLY public.affiliations DROP CONSTRAINT affiliations_viewer_id_fkey;
ALTER TABLE ONLY public.affiliations DROP CONSTRAINT affiliations_owner_id_fkey;
ALTER TABLE ONLY public.actions DROP CONSTRAINT actions_project_id_fkey;
ALTER TABLE ONLY public.actions DROP CONSTRAINT actions_owner_id_fkey;
ALTER TABLE ONLY public.actions DROP CONSTRAINT actions_contact_id_fkey;
ALTER TABLE ONLY public.actions DROP CONSTRAINT actions_company_id_fkey;
ALTER TABLE ONLY public.action_reply DROP CONSTRAINT action_reply_parent_reply_id_fkey;
ALTER TABLE ONLY public.action_reply DROP CONSTRAINT action_reply_owner_id_fkey;
ALTER TABLE ONLY public.action_reply DROP CONSTRAINT action_reply_action_id_fkey;
DROP INDEX public.ix_system_settings_key;
DROP INDEX public.ix_projects_project_name;
DROP INDEX public.ix_projects_authorization_code;
DROP INDEX public.ix_project_stage_history_project_id;
ALTER TABLE ONLY public.version_records DROP CONSTRAINT version_records_version_number_key;
ALTER TABLE ONLY public.version_records DROP CONSTRAINT version_records_pkey;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_wechat_openid_key;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_username_key;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
ALTER TABLE ONLY public.users DROP CONSTRAINT users_email_key;
ALTER TABLE ONLY public.user_event_subscriptions DROP CONSTRAINT user_event_subscriptions_pkey;
ALTER TABLE ONLY public.user_event_subscriptions DROP CONSTRAINT uq_user_target_event;
ALTER TABLE ONLY public.product_subcategories DROP CONSTRAINT uq_subcategory_code_letter;
ALTER TABLE ONLY public.solution_manager_email_settings DROP CONSTRAINT uq_solution_manager_email_user;
ALTER TABLE ONLY public.project_scoring_records DROP CONSTRAINT uq_scoring_record_with_user;
ALTER TABLE ONLY public.project_scoring_config DROP CONSTRAINT uq_scoring_config;
ALTER TABLE ONLY public.project_rating_records DROP CONSTRAINT uq_project_user_rating;
ALTER TABLE ONLY public.upgrade_logs DROP CONSTRAINT upgrade_logs_pkey;
ALTER TABLE ONLY public.inventory DROP CONSTRAINT unique_company_product_inventory;
ALTER TABLE ONLY public.permissions DROP CONSTRAINT uix_user_module;
ALTER TABLE ONLY public.dictionaries DROP CONSTRAINT uix_type_key;
ALTER TABLE ONLY public.role_permissions DROP CONSTRAINT uix_role_module;
ALTER TABLE ONLY public.affiliations DROP CONSTRAINT uix_owner_viewer;
ALTER TABLE ONLY public.system_settings DROP CONSTRAINT system_settings_pkey;
ALTER TABLE ONLY public.system_metrics DROP CONSTRAINT system_metrics_pkey;
ALTER TABLE ONLY public.solution_manager_email_settings DROP CONSTRAINT solution_manager_email_settings_pkey;
ALTER TABLE ONLY public.settlements DROP CONSTRAINT settlements_settlement_number_key;
ALTER TABLE ONLY public.settlements DROP CONSTRAINT settlements_pkey;
ALTER TABLE ONLY public.settlement_orders DROP CONSTRAINT settlement_orders_pkey;
ALTER TABLE ONLY public.settlement_orders DROP CONSTRAINT settlement_orders_order_number_key;
ALTER TABLE ONLY public.settlement_order_details DROP CONSTRAINT settlement_order_details_pkey;
ALTER TABLE ONLY public.settlement_details DROP CONSTRAINT settlement_details_pkey;
ALTER TABLE ONLY public.role_permissions DROP CONSTRAINT role_permissions_pkey;
ALTER TABLE ONLY public.quotations DROP CONSTRAINT quotations_quotation_number_key;
ALTER TABLE ONLY public.quotations DROP CONSTRAINT quotations_pkey;
ALTER TABLE ONLY public.quotation_details DROP CONSTRAINT quotation_details_pkey;
ALTER TABLE ONLY public.purchase_orders DROP CONSTRAINT purchase_orders_pkey;
ALTER TABLE ONLY public.purchase_orders DROP CONSTRAINT purchase_orders_order_number_key;
ALTER TABLE ONLY public.purchase_order_details DROP CONSTRAINT purchase_order_details_pkey;
ALTER TABLE ONLY public.projects DROP CONSTRAINT projects_pkey;
ALTER TABLE ONLY public.project_total_scores DROP CONSTRAINT project_total_scores_project_id_key;
ALTER TABLE ONLY public.project_total_scores DROP CONSTRAINT project_total_scores_pkey;
ALTER TABLE ONLY public.project_stage_history DROP CONSTRAINT project_stage_history_pkey;
ALTER TABLE ONLY public.project_scoring_records DROP CONSTRAINT project_scoring_records_pkey;
ALTER TABLE ONLY public.project_scoring_config DROP CONSTRAINT project_scoring_config_pkey;
ALTER TABLE ONLY public.project_rating_records DROP CONSTRAINT project_rating_records_pkey;
ALTER TABLE ONLY public.project_members DROP CONSTRAINT project_members_pkey;
ALTER TABLE ONLY public.products DROP CONSTRAINT products_product_mn_key;
ALTER TABLE ONLY public.products DROP CONSTRAINT products_pkey;
ALTER TABLE ONLY public.product_subcategories DROP CONSTRAINT product_subcategories_pkey;
ALTER TABLE ONLY public.product_regions DROP CONSTRAINT product_regions_pkey;
ALTER TABLE ONLY public.product_codes DROP CONSTRAINT product_codes_pkey;
ALTER TABLE ONLY public.product_codes DROP CONSTRAINT product_codes_full_code_key;
ALTER TABLE ONLY public.product_code_fields DROP CONSTRAINT product_code_fields_pkey;
ALTER TABLE ONLY public.product_code_field_values DROP CONSTRAINT product_code_field_values_pkey;
ALTER TABLE ONLY public.product_code_field_options DROP CONSTRAINT product_code_field_options_pkey;
ALTER TABLE ONLY public.product_categories DROP CONSTRAINT product_categories_pkey;
ALTER TABLE ONLY public.product_categories DROP CONSTRAINT product_categories_code_letter_key;
ALTER TABLE ONLY public.pricing_orders DROP CONSTRAINT pricing_orders_pkey;
ALTER TABLE ONLY public.pricing_orders DROP CONSTRAINT pricing_orders_order_number_key;
ALTER TABLE ONLY public.pricing_order_details DROP CONSTRAINT pricing_order_details_pkey;
ALTER TABLE ONLY public.pricing_order_approval_records DROP CONSTRAINT pricing_order_approval_records_pkey;
ALTER TABLE ONLY public.permissions DROP CONSTRAINT permissions_pkey;
ALTER TABLE ONLY public.inventory_transactions DROP CONSTRAINT inventory_transactions_pkey;
ALTER TABLE ONLY public.inventory DROP CONSTRAINT inventory_pkey;
ALTER TABLE ONLY public.feature_changes DROP CONSTRAINT feature_changes_pkey;
ALTER TABLE ONLY public.event_registry DROP CONSTRAINT event_registry_pkey;
ALTER TABLE ONLY public.event_registry DROP CONSTRAINT event_registry_event_key_key;
ALTER TABLE ONLY public.dictionaries DROP CONSTRAINT dictionaries_pkey;
ALTER TABLE ONLY public.dev_products DROP CONSTRAINT dev_products_pkey;
ALTER TABLE ONLY public.dev_product_specs DROP CONSTRAINT dev_product_specs_pkey;
ALTER TABLE ONLY public.contacts DROP CONSTRAINT contacts_pkey;
ALTER TABLE ONLY public.companies DROP CONSTRAINT companies_pkey;
ALTER TABLE ONLY public.companies DROP CONSTRAINT companies_company_code_key;
ALTER TABLE ONLY public.change_logs DROP CONSTRAINT change_logs_pkey;
ALTER TABLE ONLY public.approval_step DROP CONSTRAINT approval_step_pkey;
ALTER TABLE ONLY public.approval_record DROP CONSTRAINT approval_record_temp_pkey;
ALTER TABLE ONLY public.approval_process_template DROP CONSTRAINT approval_process_template_pkey;
ALTER TABLE ONLY public.approval_instance DROP CONSTRAINT approval_instance_pkey;
ALTER TABLE ONLY public.alembic_version DROP CONSTRAINT alembic_version_pkc;
ALTER TABLE ONLY public.affiliations DROP CONSTRAINT affiliations_pkey;
ALTER TABLE ONLY public.actions DROP CONSTRAINT actions_pkey;
ALTER TABLE ONLY public.action_reply DROP CONSTRAINT action_reply_pkey;
ALTER TABLE public.version_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.user_event_subscriptions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.upgrade_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.system_settings ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.system_metrics ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.solution_manager_email_settings ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.settlements ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.settlement_orders ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.settlement_order_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.settlement_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.role_permissions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.quotations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.quotation_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.purchase_orders ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.purchase_order_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.projects ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.project_total_scores ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.project_stage_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.project_scoring_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.project_scoring_config ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.project_rating_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.project_members ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.products ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.product_subcategories ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.product_regions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.product_codes ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.product_code_fields ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.product_code_field_values ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.product_code_field_options ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.product_categories ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.pricing_orders ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.pricing_order_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.pricing_order_approval_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.permissions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.inventory_transactions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.inventory ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.feature_changes ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.event_registry ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.dictionaries ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.dev_products ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.dev_product_specs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.contacts ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.companies ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.change_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.approval_step ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.approval_process_template ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.approval_instance ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.affiliations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.actions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.action_reply ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE public.version_records_id_seq;
DROP TABLE public.version_records;
DROP SEQUENCE public.users_id_seq;
DROP TABLE public.users;
DROP SEQUENCE public.user_event_subscriptions_id_seq;
DROP TABLE public.user_event_subscriptions;
DROP SEQUENCE public.upgrade_logs_id_seq;
DROP TABLE public.upgrade_logs;
DROP SEQUENCE public.system_settings_id_seq;
DROP TABLE public.system_settings;
DROP SEQUENCE public.system_metrics_id_seq;
DROP TABLE public.system_metrics;
DROP SEQUENCE public.solution_manager_email_settings_id_seq;
DROP TABLE public.solution_manager_email_settings;
DROP SEQUENCE public.settlements_id_seq;
DROP TABLE public.settlements;
DROP SEQUENCE public.settlement_orders_id_seq;
DROP TABLE public.settlement_orders;
DROP SEQUENCE public.settlement_order_details_id_seq;
DROP TABLE public.settlement_order_details;
DROP SEQUENCE public.settlement_details_id_seq;
DROP TABLE public.settlement_details;
DROP SEQUENCE public.role_permissions_id_seq;
DROP TABLE public.role_permissions;
DROP SEQUENCE public.quotations_id_seq;
DROP TABLE public.quotations;
DROP SEQUENCE public.quotation_details_id_seq;
DROP TABLE public.quotation_details;
DROP SEQUENCE public.purchase_orders_id_seq;
DROP TABLE public.purchase_orders;
DROP SEQUENCE public.purchase_order_details_id_seq;
DROP TABLE public.purchase_order_details;
DROP SEQUENCE public.projects_id_seq;
DROP TABLE public.projects;
DROP SEQUENCE public.project_total_scores_id_seq;
DROP TABLE public.project_total_scores;
DROP SEQUENCE public.project_stage_history_id_seq;
DROP TABLE public.project_stage_history;
DROP SEQUENCE public.project_scoring_records_id_seq;
DROP TABLE public.project_scoring_records;
DROP SEQUENCE public.project_scoring_config_id_seq;
DROP TABLE public.project_scoring_config;
DROP SEQUENCE public.project_rating_records_id_seq;
DROP TABLE public.project_rating_records;
DROP SEQUENCE public.project_members_id_seq;
DROP TABLE public.project_members;
DROP SEQUENCE public.products_id_seq;
DROP TABLE public.products;
DROP SEQUENCE public.product_subcategories_id_seq;
DROP TABLE public.product_subcategories;
DROP SEQUENCE public.product_regions_id_seq;
DROP TABLE public.product_regions;
DROP SEQUENCE public.product_codes_id_seq;
DROP TABLE public.product_codes;
DROP SEQUENCE public.product_code_fields_id_seq;
DROP TABLE public.product_code_fields;
DROP SEQUENCE public.product_code_field_values_id_seq;
DROP TABLE public.product_code_field_values;
DROP SEQUENCE public.product_code_field_options_id_seq;
DROP TABLE public.product_code_field_options;
DROP SEQUENCE public.product_categories_id_seq;
DROP TABLE public.product_categories;
DROP SEQUENCE public.pricing_orders_id_seq;
DROP TABLE public.pricing_orders;
DROP SEQUENCE public.pricing_order_details_id_seq;
DROP TABLE public.pricing_order_details;
DROP SEQUENCE public.pricing_order_approval_records_id_seq;
DROP TABLE public.pricing_order_approval_records;
DROP SEQUENCE public.permissions_id_seq;
DROP TABLE public.permissions;
DROP SEQUENCE public.inventory_transactions_id_seq;
DROP TABLE public.inventory_transactions;
DROP SEQUENCE public.inventory_id_seq;
DROP TABLE public.inventory;
DROP SEQUENCE public.feature_changes_id_seq;
DROP TABLE public.feature_changes;
DROP SEQUENCE public.event_registry_id_seq;
DROP TABLE public.event_registry;
DROP SEQUENCE public.dictionaries_id_seq;
DROP TABLE public.dictionaries;
DROP SEQUENCE public.dev_products_id_seq;
DROP TABLE public.dev_products;
DROP SEQUENCE public.dev_product_specs_id_seq;
DROP TABLE public.dev_product_specs;
DROP SEQUENCE public.contacts_id_seq;
DROP TABLE public.contacts;
DROP SEQUENCE public.companies_id_seq;
DROP TABLE public.companies;
DROP SEQUENCE public.change_logs_id_seq;
DROP TABLE public.change_logs;
DROP SEQUENCE public.approval_step_id_seq;
DROP TABLE public.approval_step;
DROP TABLE public.approval_record;
DROP SEQUENCE public.approval_record_id_seq;
DROP SEQUENCE public.approval_process_template_id_seq;
DROP TABLE public.approval_process_template;
DROP SEQUENCE public.approval_instance_id_seq;
DROP TABLE public.approval_instance;
DROP TABLE public.alembic_version;
DROP SEQUENCE public.affiliations_id_seq;
DROP TABLE public.affiliations;
DROP SEQUENCE public.actions_id_seq;
DROP TABLE public.actions;
DROP SEQUENCE public.action_reply_id_seq;
DROP TABLE public.action_reply;
DROP TYPE public.settlementorderstatus;
DROP TYPE public.pricingorderstatus;
DROP TYPE public.pricingorderapprovalflowtype;
DROP TYPE public.approvalstatus;
DROP TYPE public.approvalinstancestatus;
DROP TYPE public.approvalaction;
DROP TYPE public.approval_status;
DROP TYPE public.approval_action;
-- *not* dropping schema, since initdb creates it
--
-- TOC entry 5 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- TOC entry 944 (class 1247 OID 19359)
-- Name: approval_action; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_action AS ENUM (
    'approve',
    'reject'
);


--
-- TOC entry 947 (class 1247 OID 19364)
-- Name: approval_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);


--
-- TOC entry 950 (class 1247 OID 19372)
-- Name: approvalaction; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalaction AS ENUM (
    'approve',
    'reject'
);


--
-- TOC entry 953 (class 1247 OID 19378)
-- Name: approvalinstancestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalinstancestatus AS ENUM (
    'pending',
    'approved',
    'rejected'
);


--
-- TOC entry 956 (class 1247 OID 19386)
-- Name: approvalstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalstatus AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- TOC entry 959 (class 1247 OID 19394)
-- Name: pricingorderapprovalflowtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricingorderapprovalflowtype AS ENUM (
    'CHANNEL_FOLLOW',
    'SALES_KEY',
    'SALES_OPPORTUNITY'
);


--
-- TOC entry 962 (class 1247 OID 19402)
-- Name: pricingorderstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricingorderstatus AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- TOC entry 965 (class 1247 OID 19412)
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
-- TOC entry 215 (class 1259 OID 19421)
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
-- TOC entry 216 (class 1259 OID 19426)
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
-- TOC entry 4099 (class 0 OID 0)
-- Dependencies: 216
-- Name: action_reply_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.action_reply_id_seq OWNED BY public.action_reply.id;


--
-- TOC entry 217 (class 1259 OID 19427)
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
-- TOC entry 218 (class 1259 OID 19432)
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
-- TOC entry 4100 (class 0 OID 0)
-- Dependencies: 218
-- Name: actions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.actions_id_seq OWNED BY public.actions.id;


--
-- TOC entry 219 (class 1259 OID 19433)
-- Name: affiliations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.affiliations (
    id integer NOT NULL,
    owner_id integer NOT NULL,
    viewer_id integer NOT NULL,
    created_at double precision
);


--
-- TOC entry 220 (class 1259 OID 19436)
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
-- TOC entry 4101 (class 0 OID 0)
-- Dependencies: 220
-- Name: affiliations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.affiliations_id_seq OWNED BY public.affiliations.id;


--
-- TOC entry 221 (class 1259 OID 19437)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- TOC entry 222 (class 1259 OID 19440)
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
-- TOC entry 4102 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN approval_instance.object_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_id IS '对应单据ID';


--
-- TOC entry 4103 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN approval_instance.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_type IS '单据类型（如 project）';


--
-- TOC entry 4104 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN approval_instance.current_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.current_step IS '当前步骤序号';


--
-- TOC entry 4105 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN approval_instance.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.status IS '状态';


--
-- TOC entry 4106 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN approval_instance.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.started_at IS '流程发起时间';


--
-- TOC entry 4107 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN approval_instance.ended_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.ended_at IS '审批完成时间';


--
-- TOC entry 4108 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN approval_instance.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.process_id IS '流程模板ID';


--
-- TOC entry 4109 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN approval_instance.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.created_by IS '发起人ID';


--
-- TOC entry 4110 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN approval_instance.template_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_snapshot IS '创建时的模板快照';


--
-- TOC entry 4111 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN approval_instance.template_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_version IS '模板版本号';


--
-- TOC entry 223 (class 1259 OID 19445)
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
-- TOC entry 4112 (class 0 OID 0)
-- Dependencies: 223
-- Name: approval_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_instance_id_seq OWNED BY public.approval_instance.id;


--
-- TOC entry 224 (class 1259 OID 19446)
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
-- TOC entry 4113 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN approval_process_template.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.name IS '流程名称';


--
-- TOC entry 4114 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN approval_process_template.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.object_type IS '适用对象（如 quotation）';


--
-- TOC entry 4115 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN approval_process_template.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.is_active IS '是否启用';


--
-- TOC entry 4116 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN approval_process_template.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_by IS '创建人账号ID';


--
-- TOC entry 4117 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN approval_process_template.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_at IS '创建时间';


--
-- TOC entry 4118 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN approval_process_template.required_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.required_fields IS '发起审批时必填字段列表';


--
-- TOC entry 4119 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN approval_process_template.lock_object_on_start; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_object_on_start IS '发起审批后是否锁定对象编辑';


--
-- TOC entry 4120 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN approval_process_template.lock_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_reason IS '锁定原因说明';


--
-- TOC entry 225 (class 1259 OID 19454)
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
-- TOC entry 4121 (class 0 OID 0)
-- Dependencies: 225
-- Name: approval_process_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_process_template_id_seq OWNED BY public.approval_process_template.id;


--
-- TOC entry 226 (class 1259 OID 19455)
-- Name: approval_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.approval_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 227 (class 1259 OID 19456)
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
-- TOC entry 4122 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN approval_record.instance_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.instance_id IS '审批流程实例';


--
-- TOC entry 4123 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN approval_record.step_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.step_id IS '流程步骤ID';


--
-- TOC entry 4124 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN approval_record.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.approver_id IS '审批人ID';


--
-- TOC entry 4125 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN approval_record.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.action IS '同意/拒绝';


--
-- TOC entry 4126 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN approval_record.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.comment IS '审批意见';


--
-- TOC entry 4127 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN approval_record."timestamp"; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record."timestamp" IS '审批时间';


--
-- TOC entry 228 (class 1259 OID 19462)
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
-- TOC entry 4128 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN approval_step.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.process_id IS '所属流程模板';


--
-- TOC entry 4129 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN approval_step.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_order IS '流程顺序';


--
-- TOC entry 4130 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN approval_step.approver_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.approver_user_id IS '审批人账号ID';


--
-- TOC entry 4131 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN approval_step.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_name IS '步骤说明（如"财务审批"）';


--
-- TOC entry 4132 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN approval_step.send_email; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.send_email IS '是否发送邮件通知';


--
-- TOC entry 4133 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN approval_step.action_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_type IS '步骤动作类型，如 authorization, quotation_approval';


--
-- TOC entry 4134 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN approval_step.action_params; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_params IS '动作参数，JSON格式';


--
-- TOC entry 4135 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN approval_step.editable_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.editable_fields IS '在此步骤可编辑的字段列表';


--
-- TOC entry 4136 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN approval_step.cc_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_users IS '邮件抄送用户ID列表';


--
-- TOC entry 4137 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN approval_step.cc_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_enabled IS '是否启用邮件抄送';


--
-- TOC entry 229 (class 1259 OID 19470)
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
-- TOC entry 4138 (class 0 OID 0)
-- Dependencies: 229
-- Name: approval_step_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_step_id_seq OWNED BY public.approval_step.id;


--
-- TOC entry 230 (class 1259 OID 19471)
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
-- TOC entry 231 (class 1259 OID 19476)
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
-- TOC entry 4139 (class 0 OID 0)
-- Dependencies: 231
-- Name: change_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.change_logs_id_seq OWNED BY public.change_logs.id;


--
-- TOC entry 232 (class 1259 OID 19477)
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
-- TOC entry 233 (class 1259 OID 19482)
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
-- TOC entry 4140 (class 0 OID 0)
-- Dependencies: 233
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- TOC entry 234 (class 1259 OID 19483)
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
-- TOC entry 235 (class 1259 OID 19488)
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
-- TOC entry 4141 (class 0 OID 0)
-- Dependencies: 235
-- Name: contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contacts_id_seq OWNED BY public.contacts.id;


--
-- TOC entry 236 (class 1259 OID 19489)
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
-- TOC entry 237 (class 1259 OID 19492)
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
-- TOC entry 4142 (class 0 OID 0)
-- Dependencies: 237
-- Name: dev_product_specs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_product_specs_id_seq OWNED BY public.dev_product_specs.id;


--
-- TOC entry 238 (class 1259 OID 19493)
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
-- TOC entry 239 (class 1259 OID 19498)
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
-- TOC entry 4143 (class 0 OID 0)
-- Dependencies: 239
-- Name: dev_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_products_id_seq OWNED BY public.dev_products.id;


--
-- TOC entry 240 (class 1259 OID 19499)
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
-- TOC entry 241 (class 1259 OID 19502)
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
-- TOC entry 4144 (class 0 OID 0)
-- Dependencies: 241
-- Name: dictionaries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dictionaries_id_seq OWNED BY public.dictionaries.id;


--
-- TOC entry 242 (class 1259 OID 19503)
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
-- TOC entry 4145 (class 0 OID 0)
-- Dependencies: 242
-- Name: COLUMN event_registry.event_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.event_key IS '事件唯一键';


--
-- TOC entry 4146 (class 0 OID 0)
-- Dependencies: 242
-- Name: COLUMN event_registry.label_zh; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.label_zh IS '中文名称';


--
-- TOC entry 4147 (class 0 OID 0)
-- Dependencies: 242
-- Name: COLUMN event_registry.label_en; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.label_en IS '英文名称';


--
-- TOC entry 4148 (class 0 OID 0)
-- Dependencies: 242
-- Name: COLUMN event_registry.default_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.default_enabled IS '是否默认开启';


--
-- TOC entry 4149 (class 0 OID 0)
-- Dependencies: 242
-- Name: COLUMN event_registry.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.enabled IS '是否在通知中心展示';


--
-- TOC entry 243 (class 1259 OID 19506)
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
-- TOC entry 4150 (class 0 OID 0)
-- Dependencies: 243
-- Name: event_registry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_registry_id_seq OWNED BY public.event_registry.id;


--
-- TOC entry 244 (class 1259 OID 19507)
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
-- TOC entry 4151 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.version_id IS '版本ID';


--
-- TOC entry 4152 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.change_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.change_type IS '变更类型：feature/fix/improvement/security';


--
-- TOC entry 4153 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.module_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.module_name IS '模块名称';


--
-- TOC entry 4154 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.title; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.title IS '变更标题';


--
-- TOC entry 4155 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.description IS '详细描述';


--
-- TOC entry 4156 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.priority IS '优先级：low/medium/high/critical';


--
-- TOC entry 4157 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.impact_level; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.impact_level IS '影响级别：minor/major/breaking';


--
-- TOC entry 4158 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.affected_files; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.affected_files IS '影响的文件列表（JSON格式）';


--
-- TOC entry 4159 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.git_commits; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.git_commits IS '相关Git提交（JSON格式）';


--
-- TOC entry 4160 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.test_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.test_status IS '测试状态：pending/passed/failed';


--
-- TOC entry 4161 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.test_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.test_notes IS '测试说明';


--
-- TOC entry 4162 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.developer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.developer_id IS '开发人员ID';


--
-- TOC entry 4163 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.developer_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.developer_name IS '开发人员姓名';


--
-- TOC entry 4164 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.created_at IS '创建时间';


--
-- TOC entry 4165 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN feature_changes.completed_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.completed_at IS '完成时间';


--
-- TOC entry 245 (class 1259 OID 19512)
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
-- TOC entry 4166 (class 0 OID 0)
-- Dependencies: 245
-- Name: feature_changes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.feature_changes_id_seq OWNED BY public.feature_changes.id;


--
-- TOC entry 246 (class 1259 OID 19513)
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
-- TOC entry 247 (class 1259 OID 19518)
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
-- TOC entry 4167 (class 0 OID 0)
-- Dependencies: 247
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- TOC entry 248 (class 1259 OID 19519)
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
-- TOC entry 249 (class 1259 OID 19524)
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
-- TOC entry 4168 (class 0 OID 0)
-- Dependencies: 249
-- Name: inventory_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_transactions_id_seq OWNED BY public.inventory_transactions.id;


--
-- TOC entry 250 (class 1259 OID 19525)
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
-- TOC entry 251 (class 1259 OID 19528)
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
-- TOC entry 4169 (class 0 OID 0)
-- Dependencies: 251
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- TOC entry 252 (class 1259 OID 19529)
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
-- TOC entry 4170 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_order_approval_records.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.pricing_order_id IS '批价单ID';


--
-- TOC entry 4171 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_order_approval_records.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_order IS '审批步骤顺序';


--
-- TOC entry 4172 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_order_approval_records.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_name IS '审批步骤名称';


--
-- TOC entry 4173 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_order_approval_records.approver_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_role IS '审批人角色';


--
-- TOC entry 4174 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_order_approval_records.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_id IS '审批人ID';


--
-- TOC entry 4175 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_order_approval_records.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.action IS '审批动作：approve/reject';


--
-- TOC entry 4176 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_order_approval_records.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.comment IS '审批意见';


--
-- TOC entry 4177 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_order_approval_records.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approved_at IS '审批时间';


--
-- TOC entry 4178 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_order_approval_records.is_fast_approval; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.is_fast_approval IS '是否快速通过';


--
-- TOC entry 4179 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN pricing_order_approval_records.fast_approval_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.fast_approval_reason IS '快速通过原因';


--
-- TOC entry 253 (class 1259 OID 19534)
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
-- TOC entry 4180 (class 0 OID 0)
-- Dependencies: 253
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_order_approval_records_id_seq OWNED BY public.pricing_order_approval_records.id;


--
-- TOC entry 254 (class 1259 OID 19535)
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
-- TOC entry 4181 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.pricing_order_id IS '批价单ID';


--
-- TOC entry 4182 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_name IS '产品名称';


--
-- TOC entry 4183 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_model IS '产品型号';


--
-- TOC entry 4184 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_desc IS '产品描述';


--
-- TOC entry 4185 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.brand IS '品牌';


--
-- TOC entry 4186 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.unit IS '单位';


--
-- TOC entry 4187 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_mn IS '产品MN编码';


--
-- TOC entry 4188 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.market_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.market_price IS '市场价';


--
-- TOC entry 4189 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.unit_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.unit_price IS '单价';


--
-- TOC entry 4190 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.quantity IS '数量';


--
-- TOC entry 4191 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.discount_rate IS '折扣率';


--
-- TOC entry 4192 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.total_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.total_price IS '小计金额';


--
-- TOC entry 4193 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.source_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.source_type IS '数据来源：quotation/manual';


--
-- TOC entry 4194 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN pricing_order_details.source_quotation_detail_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.source_quotation_detail_id IS '来源报价单明细ID';


--
-- TOC entry 255 (class 1259 OID 19540)
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
-- TOC entry 4195 (class 0 OID 0)
-- Dependencies: 255
-- Name: pricing_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_order_details_id_seq OWNED BY public.pricing_order_details.id;


--
-- TOC entry 256 (class 1259 OID 19541)
-- Name: pricing_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pricing_orders (
    id integer NOT NULL,
    order_number character varying(64) NOT NULL,
    project_id integer NOT NULL,
    quotation_id integer NOT NULL,
    distributor_id integer,
    dealer_id integer,
    pricing_total_amount double precision,
    pricing_total_discount_rate double precision,
    settlement_total_amount double precision,
    settlement_total_discount_rate double precision,
    approval_flow_type character varying(32) NOT NULL,
    status character varying(20),
    current_approval_step integer,
    approved_by integer,
    approved_at timestamp without time zone,
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_direct_contract boolean DEFAULT false,
    is_factory_pickup boolean DEFAULT false
);


--
-- TOC entry 4196 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.order_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.order_number IS '批价单号';


--
-- TOC entry 4197 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.project_id IS '项目ID';


--
-- TOC entry 4198 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.quotation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.quotation_id IS '报价单ID';


--
-- TOC entry 4199 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.distributor_id IS '分销商ID';


--
-- TOC entry 4200 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.dealer_id IS '经销商ID';


--
-- TOC entry 4201 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.pricing_total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_amount IS '批价单总金额';


--
-- TOC entry 4202 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.pricing_total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_discount_rate IS '批价单总折扣率';


--
-- TOC entry 4203 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.settlement_total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_amount IS '结算单总金额';


--
-- TOC entry 4204 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.settlement_total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_discount_rate IS '结算单总折扣率';


--
-- TOC entry 4205 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.approval_flow_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approval_flow_type IS '审批流程类型';


--
-- TOC entry 4206 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.status IS '批价单状态';


--
-- TOC entry 4207 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.current_approval_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.current_approval_step IS '当前审批步骤';


--
-- TOC entry 4208 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.approved_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approved_by IS '最终批准人';


--
-- TOC entry 4209 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approved_at IS '批准时间';


--
-- TOC entry 4210 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.created_by IS '创建人';


--
-- TOC entry 4211 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.created_at IS '创建时间';


--
-- TOC entry 4212 (class 0 OID 0)
-- Dependencies: 256
-- Name: COLUMN pricing_orders.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.updated_at IS '更新时间';


--
-- TOC entry 257 (class 1259 OID 19546)
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
-- TOC entry 4213 (class 0 OID 0)
-- Dependencies: 257
-- Name: pricing_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_orders_id_seq OWNED BY public.pricing_orders.id;


--
-- TOC entry 258 (class 1259 OID 19547)
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
-- TOC entry 259 (class 1259 OID 19552)
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
-- TOC entry 4214 (class 0 OID 0)
-- Dependencies: 259
-- Name: product_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_categories_id_seq OWNED BY public.product_categories.id;


--
-- TOC entry 260 (class 1259 OID 19553)
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
-- TOC entry 261 (class 1259 OID 19558)
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
-- TOC entry 4215 (class 0 OID 0)
-- Dependencies: 261
-- Name: product_code_field_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_field_options_id_seq OWNED BY public.product_code_field_options.id;


--
-- TOC entry 262 (class 1259 OID 19559)
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
-- TOC entry 263 (class 1259 OID 19562)
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
-- TOC entry 4216 (class 0 OID 0)
-- Dependencies: 263
-- Name: product_code_field_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_field_values_id_seq OWNED BY public.product_code_field_values.id;


--
-- TOC entry 264 (class 1259 OID 19563)
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
-- TOC entry 265 (class 1259 OID 19568)
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
-- TOC entry 4217 (class 0 OID 0)
-- Dependencies: 265
-- Name: product_code_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_fields_id_seq OWNED BY public.product_code_fields.id;


--
-- TOC entry 266 (class 1259 OID 19569)
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
-- TOC entry 267 (class 1259 OID 19572)
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
-- TOC entry 4218 (class 0 OID 0)
-- Dependencies: 267
-- Name: product_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_codes_id_seq OWNED BY public.product_codes.id;


--
-- TOC entry 268 (class 1259 OID 19573)
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
-- TOC entry 269 (class 1259 OID 19578)
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
-- TOC entry 4219 (class 0 OID 0)
-- Dependencies: 269
-- Name: product_regions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_regions_id_seq OWNED BY public.product_regions.id;


--
-- TOC entry 270 (class 1259 OID 19579)
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
-- TOC entry 271 (class 1259 OID 19584)
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
-- TOC entry 4220 (class 0 OID 0)
-- Dependencies: 271
-- Name: product_subcategories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_subcategories_id_seq OWNED BY public.product_subcategories.id;


--
-- TOC entry 272 (class 1259 OID 19585)
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
-- TOC entry 273 (class 1259 OID 19590)
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
-- TOC entry 4221 (class 0 OID 0)
-- Dependencies: 273
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- TOC entry 274 (class 1259 OID 19591)
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
-- TOC entry 275 (class 1259 OID 19594)
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
-- TOC entry 4222 (class 0 OID 0)
-- Dependencies: 275
-- Name: project_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_members_id_seq OWNED BY public.project_members.id;


--
-- TOC entry 276 (class 1259 OID 19595)
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
-- TOC entry 277 (class 1259 OID 19599)
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
-- TOC entry 4223 (class 0 OID 0)
-- Dependencies: 277
-- Name: project_rating_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_rating_records_id_seq OWNED BY public.project_rating_records.id;


--
-- TOC entry 278 (class 1259 OID 19600)
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
-- TOC entry 279 (class 1259 OID 19609)
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
-- TOC entry 4224 (class 0 OID 0)
-- Dependencies: 279
-- Name: project_scoring_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_scoring_config_id_seq OWNED BY public.project_scoring_config.id;


--
-- TOC entry 280 (class 1259 OID 19610)
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
-- TOC entry 281 (class 1259 OID 19619)
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
-- TOC entry 4225 (class 0 OID 0)
-- Dependencies: 281
-- Name: project_scoring_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_scoring_records_id_seq OWNED BY public.project_scoring_records.id;


--
-- TOC entry 282 (class 1259 OID 19620)
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
-- TOC entry 283 (class 1259 OID 19626)
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
-- TOC entry 4226 (class 0 OID 0)
-- Dependencies: 283
-- Name: project_stage_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_stage_history_id_seq OWNED BY public.project_stage_history.id;


--
-- TOC entry 284 (class 1259 OID 19627)
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
-- TOC entry 285 (class 1259 OID 19639)
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
-- TOC entry 4227 (class 0 OID 0)
-- Dependencies: 285
-- Name: project_total_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_total_scores_id_seq OWNED BY public.project_total_scores.id;


--
-- TOC entry 286 (class 1259 OID 19640)
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
    rating integer
);


--
-- TOC entry 287 (class 1259 OID 19650)
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
-- TOC entry 4228 (class 0 OID 0)
-- Dependencies: 287
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- TOC entry 288 (class 1259 OID 19651)
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
-- TOC entry 289 (class 1259 OID 19656)
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
-- TOC entry 4229 (class 0 OID 0)
-- Dependencies: 289
-- Name: purchase_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_order_details_id_seq OWNED BY public.purchase_order_details.id;


--
-- TOC entry 290 (class 1259 OID 19657)
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
-- TOC entry 291 (class 1259 OID 19662)
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
-- TOC entry 4230 (class 0 OID 0)
-- Dependencies: 291
-- Name: purchase_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_orders_id_seq OWNED BY public.purchase_orders.id;


--
-- TOC entry 292 (class 1259 OID 19663)
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
-- TOC entry 293 (class 1259 OID 19669)
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
-- TOC entry 4231 (class 0 OID 0)
-- Dependencies: 293
-- Name: quotation_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotation_details_id_seq OWNED BY public.quotation_details.id;


--
-- TOC entry 294 (class 1259 OID 19670)
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
    confirmation_badge_status character varying(20) DEFAULT 'none'::character varying,
    confirmation_badge_color character varying(20) DEFAULT NULL::character varying,
    confirmed_by integer,
    confirmed_at timestamp without time zone,
    product_signature character varying(64) DEFAULT NULL::character varying,
    implant_total_amount double precision DEFAULT 0.00
);


--
-- TOC entry 295 (class 1259 OID 19683)
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
-- TOC entry 4232 (class 0 OID 0)
-- Dependencies: 295
-- Name: quotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotations_id_seq OWNED BY public.quotations.id;


--
-- TOC entry 296 (class 1259 OID 19684)
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
-- TOC entry 297 (class 1259 OID 19687)
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
-- TOC entry 4233 (class 0 OID 0)
-- Dependencies: 297
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- TOC entry 298 (class 1259 OID 19688)
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
-- TOC entry 299 (class 1259 OID 19693)
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
-- TOC entry 4234 (class 0 OID 0)
-- Dependencies: 299
-- Name: settlement_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_details_id_seq OWNED BY public.settlement_details.id;


--
-- TOC entry 300 (class 1259 OID 19694)
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
-- TOC entry 4235 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.pricing_order_id IS '批价单ID';


--
-- TOC entry 4236 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_name IS '产品名称';


--
-- TOC entry 4237 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_model IS '产品型号';


--
-- TOC entry 4238 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_desc IS '产品描述';


--
-- TOC entry 4239 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.brand IS '品牌';


--
-- TOC entry 4240 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.unit IS '单位';


--
-- TOC entry 4241 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_mn IS '产品MN编码';


--
-- TOC entry 4242 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.market_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.market_price IS '市场价';


--
-- TOC entry 4243 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.unit_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.unit_price IS '单价';


--
-- TOC entry 4244 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.quantity IS '数量';


--
-- TOC entry 4245 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.discount_rate IS '折扣率';


--
-- TOC entry 4246 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.total_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.total_price IS '小计金额';


--
-- TOC entry 4247 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.pricing_detail_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.pricing_detail_id IS '关联批价单明细ID';


--
-- TOC entry 4248 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.settlement_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_order_id IS '结算单ID';


--
-- TOC entry 4249 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.settlement_company_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_company_id IS '结算目标公司ID';


--
-- TOC entry 4250 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.settlement_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_status IS '结算状态: pending, completed';


--
-- TOC entry 4251 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.settlement_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_date IS '结算完成时间';


--
-- TOC entry 4252 (class 0 OID 0)
-- Dependencies: 300
-- Name: COLUMN settlement_order_details.settlement_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_notes IS '结算备注';


--
-- TOC entry 301 (class 1259 OID 19699)
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
-- TOC entry 4253 (class 0 OID 0)
-- Dependencies: 301
-- Name: settlement_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_order_details_id_seq OWNED BY public.settlement_order_details.id;


--
-- TOC entry 302 (class 1259 OID 19700)
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
-- TOC entry 4254 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.order_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.order_number IS '结算单号';


--
-- TOC entry 4255 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.pricing_order_id IS '关联批价单ID';


--
-- TOC entry 4256 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.project_id IS '项目ID';


--
-- TOC entry 4257 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.quotation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.quotation_id IS '报价单ID';


--
-- TOC entry 4258 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.distributor_id IS '分销商ID';


--
-- TOC entry 4259 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.dealer_id IS '经销商ID（辅助信息）';


--
-- TOC entry 4260 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.total_amount IS '结算总金额';


--
-- TOC entry 4261 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.total_discount_rate IS '结算总折扣率';


--
-- TOC entry 4262 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.status IS '结算单状态';


--
-- TOC entry 4263 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.approved_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.approved_by IS '批准人';


--
-- TOC entry 4264 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.approved_at IS '批准时间';


--
-- TOC entry 4265 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.created_by IS '创建人';


--
-- TOC entry 4266 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.created_at IS '创建时间';


--
-- TOC entry 4267 (class 0 OID 0)
-- Dependencies: 302
-- Name: COLUMN settlement_orders.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.updated_at IS '更新时间';


--
-- TOC entry 303 (class 1259 OID 19703)
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
-- TOC entry 4268 (class 0 OID 0)
-- Dependencies: 303
-- Name: settlement_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_orders_id_seq OWNED BY public.settlement_orders.id;


--
-- TOC entry 304 (class 1259 OID 19704)
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
-- TOC entry 305 (class 1259 OID 19709)
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
-- TOC entry 4269 (class 0 OID 0)
-- Dependencies: 305
-- Name: settlements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlements_id_seq OWNED BY public.settlements.id;


--
-- TOC entry 306 (class 1259 OID 19710)
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
-- TOC entry 4270 (class 0 OID 0)
-- Dependencies: 306
-- Name: COLUMN solution_manager_email_settings.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.user_id IS '解决方案经理用户ID';


--
-- TOC entry 4271 (class 0 OID 0)
-- Dependencies: 306
-- Name: COLUMN solution_manager_email_settings.quotation_created; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_created IS '报价单新建通知';


--
-- TOC entry 4272 (class 0 OID 0)
-- Dependencies: 306
-- Name: COLUMN solution_manager_email_settings.quotation_updated; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_updated IS '报价单更新通知';


--
-- TOC entry 4273 (class 0 OID 0)
-- Dependencies: 306
-- Name: COLUMN solution_manager_email_settings.project_created; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_created IS '项目新建通知';


--
-- TOC entry 4274 (class 0 OID 0)
-- Dependencies: 306
-- Name: COLUMN solution_manager_email_settings.project_stage_changed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_stage_changed IS '项目阶段推进通知';


--
-- TOC entry 307 (class 1259 OID 19713)
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
-- TOC entry 4275 (class 0 OID 0)
-- Dependencies: 307
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.solution_manager_email_settings_id_seq OWNED BY public.solution_manager_email_settings.id;


--
-- TOC entry 308 (class 1259 OID 19714)
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
-- TOC entry 4276 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.version_id IS '版本ID';


--
-- TOC entry 4277 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.avg_response_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.avg_response_time IS '平均响应时间（毫秒）';


--
-- TOC entry 4278 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.max_response_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.max_response_time IS '最大响应时间（毫秒）';


--
-- TOC entry 4279 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.error_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.error_rate IS '错误率（百分比）';


--
-- TOC entry 4280 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.active_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.active_users IS '活跃用户数';


--
-- TOC entry 4281 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.total_requests; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.total_requests IS '总请求数';


--
-- TOC entry 4282 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.database_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.database_size IS '数据库大小（字节）';


--
-- TOC entry 4283 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.cpu_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.cpu_usage IS 'CPU使用率（百分比）';


--
-- TOC entry 4284 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.memory_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.memory_usage IS '内存使用率（百分比）';


--
-- TOC entry 4285 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.disk_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.disk_usage IS '磁盘使用率（百分比）';


--
-- TOC entry 4286 (class 0 OID 0)
-- Dependencies: 308
-- Name: COLUMN system_metrics.recorded_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.recorded_at IS '记录时间';


--
-- TOC entry 309 (class 1259 OID 19717)
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
-- TOC entry 4287 (class 0 OID 0)
-- Dependencies: 309
-- Name: system_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_metrics_id_seq OWNED BY public.system_metrics.id;


--
-- TOC entry 310 (class 1259 OID 19718)
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
-- TOC entry 311 (class 1259 OID 19723)
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
-- TOC entry 4288 (class 0 OID 0)
-- Dependencies: 311
-- Name: system_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_settings_id_seq OWNED BY public.system_settings.id;


--
-- TOC entry 312 (class 1259 OID 19724)
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
-- TOC entry 4289 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.version_id IS '版本ID';


--
-- TOC entry 4290 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.from_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.from_version IS '升级前版本';


--
-- TOC entry 4291 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.to_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.to_version IS '升级后版本';


--
-- TOC entry 4292 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.upgrade_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_date IS '升级时间';


--
-- TOC entry 4293 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.upgrade_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_type IS '升级类型：manual/automatic';


--
-- TOC entry 4294 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.status IS '升级状态：success/failed/rollback';


--
-- TOC entry 4295 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.upgrade_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_notes IS '升级说明';


--
-- TOC entry 4296 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.error_message IS '错误信息（如果升级失败）';


--
-- TOC entry 4297 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.duration_seconds; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.duration_seconds IS '升级耗时（秒）';


--
-- TOC entry 4298 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.operator_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.operator_id IS '操作人员ID';


--
-- TOC entry 4299 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.operator_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.operator_name IS '操作人员姓名';


--
-- TOC entry 4300 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.environment IS '升级环境';


--
-- TOC entry 4301 (class 0 OID 0)
-- Dependencies: 312
-- Name: COLUMN upgrade_logs.server_info; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.server_info IS '服务器信息';


--
-- TOC entry 313 (class 1259 OID 19729)
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
-- TOC entry 4302 (class 0 OID 0)
-- Dependencies: 313
-- Name: upgrade_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.upgrade_logs_id_seq OWNED BY public.upgrade_logs.id;


--
-- TOC entry 314 (class 1259 OID 19730)
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
-- TOC entry 4303 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN user_event_subscriptions.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.user_id IS '订阅者用户ID';


--
-- TOC entry 4304 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN user_event_subscriptions.target_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.target_user_id IS '被订阅的用户ID';


--
-- TOC entry 4305 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN user_event_subscriptions.event_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.event_id IS '事件ID';


--
-- TOC entry 4306 (class 0 OID 0)
-- Dependencies: 314
-- Name: COLUMN user_event_subscriptions.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.enabled IS '是否启用订阅';


--
-- TOC entry 315 (class 1259 OID 19733)
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
-- TOC entry 4307 (class 0 OID 0)
-- Dependencies: 315
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_event_subscriptions_id_seq OWNED BY public.user_event_subscriptions.id;


--
-- TOC entry 316 (class 1259 OID 19734)
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
-- TOC entry 317 (class 1259 OID 19739)
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
-- TOC entry 4308 (class 0 OID 0)
-- Dependencies: 317
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 318 (class 1259 OID 19740)
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
-- TOC entry 4309 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.version_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.version_number IS '版本号，如1.0.0';


--
-- TOC entry 4310 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.version_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.version_name IS '版本名称';


--
-- TOC entry 4311 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.release_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.release_date IS '发布日期';


--
-- TOC entry 4312 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.description IS '版本描述';


--
-- TOC entry 4313 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.is_current; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.is_current IS '是否为当前版本';


--
-- TOC entry 4314 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.environment IS '环境：development/production';


--
-- TOC entry 4315 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.total_features; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_features IS '新增功能数量';


--
-- TOC entry 4316 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.total_fixes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_fixes IS '修复问题数量';


--
-- TOC entry 4317 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.total_improvements; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_improvements IS '改进数量';


--
-- TOC entry 4318 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.git_commit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.git_commit IS 'Git提交哈希';


--
-- TOC entry 4319 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.build_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.build_number IS '构建号';


--
-- TOC entry 4320 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.created_at IS '创建时间';


--
-- TOC entry 4321 (class 0 OID 0)
-- Dependencies: 318
-- Name: COLUMN version_records.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.updated_at IS '更新时间';


--
-- TOC entry 319 (class 1259 OID 19745)
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
-- TOC entry 4322 (class 0 OID 0)
-- Dependencies: 319
-- Name: version_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.version_records_id_seq OWNED BY public.version_records.id;


--
-- TOC entry 3490 (class 2604 OID 19746)
-- Name: action_reply id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply ALTER COLUMN id SET DEFAULT nextval('public.action_reply_id_seq'::regclass);


--
-- TOC entry 3491 (class 2604 OID 19747)
-- Name: actions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions ALTER COLUMN id SET DEFAULT nextval('public.actions_id_seq'::regclass);


--
-- TOC entry 3492 (class 2604 OID 19748)
-- Name: affiliations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations ALTER COLUMN id SET DEFAULT nextval('public.affiliations_id_seq'::regclass);


--
-- TOC entry 3493 (class 2604 OID 19749)
-- Name: approval_instance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance ALTER COLUMN id SET DEFAULT nextval('public.approval_instance_id_seq'::regclass);


--
-- TOC entry 3494 (class 2604 OID 19750)
-- Name: approval_process_template id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template ALTER COLUMN id SET DEFAULT nextval('public.approval_process_template_id_seq'::regclass);


--
-- TOC entry 3499 (class 2604 OID 19751)
-- Name: approval_step id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step ALTER COLUMN id SET DEFAULT nextval('public.approval_step_id_seq'::regclass);


--
-- TOC entry 3503 (class 2604 OID 19752)
-- Name: change_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs ALTER COLUMN id SET DEFAULT nextval('public.change_logs_id_seq'::regclass);


--
-- TOC entry 3504 (class 2604 OID 19753)
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- TOC entry 3505 (class 2604 OID 19754)
-- Name: contacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts ALTER COLUMN id SET DEFAULT nextval('public.contacts_id_seq'::regclass);


--
-- TOC entry 3506 (class 2604 OID 19755)
-- Name: dev_product_specs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs ALTER COLUMN id SET DEFAULT nextval('public.dev_product_specs_id_seq'::regclass);


--
-- TOC entry 3507 (class 2604 OID 19756)
-- Name: dev_products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products ALTER COLUMN id SET DEFAULT nextval('public.dev_products_id_seq'::regclass);


--
-- TOC entry 3508 (class 2604 OID 19757)
-- Name: dictionaries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries ALTER COLUMN id SET DEFAULT nextval('public.dictionaries_id_seq'::regclass);


--
-- TOC entry 3509 (class 2604 OID 19758)
-- Name: event_registry id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry ALTER COLUMN id SET DEFAULT nextval('public.event_registry_id_seq'::regclass);


--
-- TOC entry 3510 (class 2604 OID 19759)
-- Name: feature_changes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes ALTER COLUMN id SET DEFAULT nextval('public.feature_changes_id_seq'::regclass);


--
-- TOC entry 3511 (class 2604 OID 19760)
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- TOC entry 3512 (class 2604 OID 19761)
-- Name: inventory_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions ALTER COLUMN id SET DEFAULT nextval('public.inventory_transactions_id_seq'::regclass);


--
-- TOC entry 3513 (class 2604 OID 19762)
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- TOC entry 3514 (class 2604 OID 19763)
-- Name: pricing_order_approval_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_approval_records_id_seq'::regclass);


--
-- TOC entry 3515 (class 2604 OID 19764)
-- Name: pricing_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_details_id_seq'::regclass);


--
-- TOC entry 3516 (class 2604 OID 19765)
-- Name: pricing_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders ALTER COLUMN id SET DEFAULT nextval('public.pricing_orders_id_seq'::regclass);


--
-- TOC entry 3519 (class 2604 OID 19766)
-- Name: product_categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories ALTER COLUMN id SET DEFAULT nextval('public.product_categories_id_seq'::regclass);


--
-- TOC entry 3520 (class 2604 OID 19767)
-- Name: product_code_field_options id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_options_id_seq'::regclass);


--
-- TOC entry 3521 (class 2604 OID 19768)
-- Name: product_code_field_values id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_values_id_seq'::regclass);


--
-- TOC entry 3522 (class 2604 OID 19769)
-- Name: product_code_fields id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields ALTER COLUMN id SET DEFAULT nextval('public.product_code_fields_id_seq'::regclass);


--
-- TOC entry 3523 (class 2604 OID 19770)
-- Name: product_codes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes ALTER COLUMN id SET DEFAULT nextval('public.product_codes_id_seq'::regclass);


--
-- TOC entry 3524 (class 2604 OID 19771)
-- Name: product_regions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_regions ALTER COLUMN id SET DEFAULT nextval('public.product_regions_id_seq'::regclass);


--
-- TOC entry 3525 (class 2604 OID 19772)
-- Name: product_subcategories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories ALTER COLUMN id SET DEFAULT nextval('public.product_subcategories_id_seq'::regclass);


--
-- TOC entry 3526 (class 2604 OID 19773)
-- Name: products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- TOC entry 3527 (class 2604 OID 19774)
-- Name: project_members id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members ALTER COLUMN id SET DEFAULT nextval('public.project_members_id_seq'::regclass);


--
-- TOC entry 3528 (class 2604 OID 19775)
-- Name: project_rating_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records ALTER COLUMN id SET DEFAULT nextval('public.project_rating_records_id_seq'::regclass);


--
-- TOC entry 3529 (class 2604 OID 19776)
-- Name: project_scoring_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_config_id_seq'::regclass);


--
-- TOC entry 3534 (class 2604 OID 19777)
-- Name: project_scoring_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_records_id_seq'::regclass);


--
-- TOC entry 3539 (class 2604 OID 19778)
-- Name: project_stage_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history ALTER COLUMN id SET DEFAULT nextval('public.project_stage_history_id_seq'::regclass);


--
-- TOC entry 3541 (class 2604 OID 19779)
-- Name: project_total_scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores ALTER COLUMN id SET DEFAULT nextval('public.project_total_scores_id_seq'::regclass);


--
-- TOC entry 3551 (class 2604 OID 19780)
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- TOC entry 3557 (class 2604 OID 19781)
-- Name: purchase_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details ALTER COLUMN id SET DEFAULT nextval('public.purchase_order_details_id_seq'::regclass);


--
-- TOC entry 3558 (class 2604 OID 19782)
-- Name: purchase_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders ALTER COLUMN id SET DEFAULT nextval('public.purchase_orders_id_seq'::regclass);


--
-- TOC entry 3559 (class 2604 OID 19783)
-- Name: quotation_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details ALTER COLUMN id SET DEFAULT nextval('public.quotation_details_id_seq'::regclass);


--
-- TOC entry 3561 (class 2604 OID 19784)
-- Name: quotations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations ALTER COLUMN id SET DEFAULT nextval('public.quotations_id_seq'::regclass);


--
-- TOC entry 3570 (class 2604 OID 19785)
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- TOC entry 3571 (class 2604 OID 19786)
-- Name: settlement_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_details_id_seq'::regclass);


--
-- TOC entry 3572 (class 2604 OID 19787)
-- Name: settlement_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_order_details_id_seq'::regclass);


--
-- TOC entry 3573 (class 2604 OID 19788)
-- Name: settlement_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders ALTER COLUMN id SET DEFAULT nextval('public.settlement_orders_id_seq'::regclass);


--
-- TOC entry 3574 (class 2604 OID 19789)
-- Name: settlements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements ALTER COLUMN id SET DEFAULT nextval('public.settlements_id_seq'::regclass);


--
-- TOC entry 3575 (class 2604 OID 19790)
-- Name: solution_manager_email_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings ALTER COLUMN id SET DEFAULT nextval('public.solution_manager_email_settings_id_seq'::regclass);


--
-- TOC entry 3576 (class 2604 OID 19791)
-- Name: system_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics ALTER COLUMN id SET DEFAULT nextval('public.system_metrics_id_seq'::regclass);


--
-- TOC entry 3577 (class 2604 OID 19792)
-- Name: system_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings ALTER COLUMN id SET DEFAULT nextval('public.system_settings_id_seq'::regclass);


--
-- TOC entry 3578 (class 2604 OID 19793)
-- Name: upgrade_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs ALTER COLUMN id SET DEFAULT nextval('public.upgrade_logs_id_seq'::regclass);


--
-- TOC entry 3579 (class 2604 OID 19794)
-- Name: user_event_subscriptions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions ALTER COLUMN id SET DEFAULT nextval('public.user_event_subscriptions_id_seq'::regclass);


--
-- TOC entry 3580 (class 2604 OID 19795)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 3581 (class 2604 OID 19796)
-- Name: version_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records ALTER COLUMN id SET DEFAULT nextval('public.version_records_id_seq'::regclass);


--
-- TOC entry 3989 (class 0 OID 19421)
-- Dependencies: 215
-- Data for Name: action_reply; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.action_reply (id, action_id, parent_reply_id, content, owner_id, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3991 (class 0 OID 19427)
-- Dependencies: 217
-- Data for Name: actions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.actions (id, date, contact_id, company_id, project_id, communication, created_at, owner_id) FROM stdin;
\.


--
-- TOC entry 3993 (class 0 OID 19433)
-- Dependencies: 219
-- Data for Name: affiliations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.affiliations (id, owner_id, viewer_id, created_at) FROM stdin;
\.


--
-- TOC entry 3995 (class 0 OID 19437)
-- Dependencies: 221
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
\.


--
-- TOC entry 3996 (class 0 OID 19440)
-- Dependencies: 222
-- Data for Name: approval_instance; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_instance (id, object_id, object_type, current_step, status, started_at, ended_at, process_id, created_by, template_snapshot, template_version) FROM stdin;
\.


--
-- TOC entry 3998 (class 0 OID 19446)
-- Dependencies: 224
-- Data for Name: approval_process_template; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_process_template (id, name, object_type, is_active, created_by, created_at, required_fields, lock_object_on_start, lock_reason) FROM stdin;
\.


--
-- TOC entry 4001 (class 0 OID 19456)
-- Dependencies: 227
-- Data for Name: approval_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_record (id, instance_id, step_id, approver_id, action, comment, "timestamp") FROM stdin;
\.


--
-- TOC entry 4002 (class 0 OID 19462)
-- Dependencies: 228
-- Data for Name: approval_step; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_step (id, process_id, step_order, approver_user_id, step_name, send_email, action_type, action_params, editable_fields, cc_users, cc_enabled) FROM stdin;
\.


--
-- TOC entry 4004 (class 0 OID 19471)
-- Dependencies: 230
-- Data for Name: change_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.change_logs (id, module_name, table_name, record_id, operation_type, field_name, old_value, new_value, user_id, user_name, created_at, description, ip_address, user_agent, record_info) FROM stdin;
1	user	users	3	CREATE	\N	\N	\N	1	admin	2025-06-15 14:04:41.609016	\N	127.0.0.1	\N	公司: evertac solutions
2	user	users	3	UPDATE	部门		sales_dept	1	admin	2025-06-15 14:06:05.876135	\N	127.0.0.1	\N	公司: evertac solutions
3	user	users	3	UPDATE	角色	user	region_sales	1	admin	2025-06-15 14:06:05.87614	\N	127.0.0.1	\N	公司: evertac solutions
4	user	users	3	UPDATE	updated_at	1749996280.8795583	1749996365.8652391	1	admin	2025-06-15 14:06:05.876142	\N	127.0.0.1	\N	公司: evertac solutions
5	user	users	4	CREATE	\N	\N	\N	1	admin	2025-06-15 14:06:48.311258	\N	127.0.0.1	\N	公司: evertac solutions
6	user	users	5	CREATE	\N	\N	\N	1	admin	2025-06-15 14:08:43.414696	\N	127.0.0.1	\N	公司: evertac solutions
\.


--
-- TOC entry 4006 (class 0 OID 19477)
-- Dependencies: 232
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.companies (id, company_code, company_name, country, region, address, industry, company_type, status, created_at, updated_at, notes, is_deleted, owner_id, shared_with_users, share_contacts) FROM stdin;
\.


--
-- TOC entry 4008 (class 0 OID 19483)
-- Dependencies: 234
-- Data for Name: contacts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contacts (id, company_id, name, department, "position", phone, email, is_primary, created_at, updated_at, notes, owner_id, override_share, shared_disabled) FROM stdin;
\.


--
-- TOC entry 4010 (class 0 OID 19489)
-- Dependencies: 236
-- Data for Name: dev_product_specs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dev_product_specs (id, dev_product_id, field_name, field_value, field_code) FROM stdin;
\.


--
-- TOC entry 4012 (class 0 OID 19493)
-- Dependencies: 238
-- Data for Name: dev_products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dev_products (id, category_id, subcategory_id, region_id, name, model, status, unit, retail_price, description, image_path, created_at, updated_at, owner_id, created_by, mn_code, pdf_path) FROM stdin;
\.


--
-- TOC entry 4014 (class 0 OID 19499)
-- Dependencies: 240
-- Data for Name: dictionaries; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dictionaries (id, type, key, value, is_active, sort_order, created_at, updated_at) FROM stdin;
1	role	admin	系统管理员	t	10	1745667318.529633	1745723213.991283
2	role	user	普通用户	t	20	1745716772.6006558	1745716772.600658
10	role	dealer	代理商	t	100	1745716772.6010182	1745716772.6010182
12	role	business_admin	商务助理	t	120	1745716772.603283	1746443802.069152
13	role	solution_manager	解决方案经理	t	130	1745716772.6038039	1745716963.2245371
14	role	sales_director	营销总监	t	140	1745716772.604226	1745717015.457986
16	role	sales_manager	销售经理	t	160	1745716772.6050391	1746440616.621388
17	role	product_manager	产品经理	t	170	1745716772.6054158	1745717037.573678
18	role	customer_sales	客户销售	t	180	1745716772.605782	1746440605.527481
19	role	channel_manager	渠道经理	t	190	1745716772.60614	1748071365.134846
20	role	service_manager	服务经理	t	200	1745716772.606497	1745717151.156446
21	role	finace_director	财务总监	t	210	1745716772.606807	1746440593.9798028
24	department	sales_dep	销售部	t	10	1746443555.595523	1746443555.595524
25	department	rd_dep	产品和解决方案部	t	20	1746443615.569504	1746443615.569506
26	department	service_dep	服务部	t	30	1746443643.629589	1746443643.629589
27	company	evertacsh_company	和源通信（上海）股份有限公司	t	10	1746443714.853514	1746443714.853515
28	role	ceo	总经理	t	220	1746443836.45206	1746443836.452061
29	department	finance_dep	财务部	t	40	1746489399.2419264	1746489399.2419312
30	company	recoo_company	上海瑞康通信科技有限公司	t	20	1746783363.4526942	1746783363.452697
31	company	dunli_company	敦力(南京)科技有限公司	t	30	1746783506.5529208	1746783506.552924
32	company	hangbo_company	浙江航博智能工程有限公司	t	40	1746783587.0208042	1746783587.0208097
33	company	focus_company	福淳智能科技(四川)有限公司	t	50	1746783704.9451404	1746783704.9451442
34	company	chunbo_company	上海淳泊信息科技有限公司	t	60	1746784102.0071158	1746784102.0071204
\.


--
-- TOC entry 4016 (class 0 OID 19503)
-- Dependencies: 242
-- Data for Name: event_registry; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_registry (id, event_key, label_zh, label_en, default_enabled, enabled, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4018 (class 0 OID 19507)
-- Dependencies: 244
-- Data for Name: feature_changes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feature_changes (id, version_id, change_type, module_name, title, description, priority, impact_level, affected_files, git_commits, test_status, test_notes, developer_id, developer_name, created_at, completed_at) FROM stdin;
\.


--
-- TOC entry 4020 (class 0 OID 19513)
-- Dependencies: 246
-- Data for Name: inventory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) FROM stdin;
\.


--
-- TOC entry 4022 (class 0 OID 19519)
-- Dependencies: 248
-- Data for Name: inventory_transactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) FROM stdin;
\.


--
-- TOC entry 4024 (class 0 OID 19525)
-- Dependencies: 250
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.permissions (id, user_id, module, can_view, can_create, can_edit, can_delete) FROM stdin;
\.


--
-- TOC entry 4026 (class 0 OID 19529)
-- Dependencies: 252
-- Data for Name: pricing_order_approval_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pricing_order_approval_records (id, pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval, fast_approval_reason) FROM stdin;
\.


--
-- TOC entry 4028 (class 0 OID 19535)
-- Dependencies: 254
-- Data for Name: pricing_order_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pricing_order_details (id, pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, source_quotation_detail_id) FROM stdin;
\.


--
-- TOC entry 4030 (class 0 OID 19541)
-- Dependencies: 256
-- Data for Name: pricing_orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pricing_orders (id, order_number, project_id, quotation_id, distributor_id, dealer_id, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approval_flow_type, status, current_approval_step, approved_by, approved_at, created_by, created_at, updated_at, is_direct_contract, is_factory_pickup) FROM stdin;
\.


--
-- TOC entry 4032 (class 0 OID 19547)
-- Dependencies: 258
-- Data for Name: product_categories; Type: TABLE DATA; Schema: public; Owner: -
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
-- TOC entry 4034 (class 0 OID 19553)
-- Dependencies: 260
-- Data for Name: product_code_field_options; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_code_field_options (id, field_id, value, code, description, is_active, "position", created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4036 (class 0 OID 19559)
-- Dependencies: 262
-- Data for Name: product_code_field_values; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_code_field_values (id, product_code_id, field_id, option_id, custom_value) FROM stdin;
\.


--
-- TOC entry 4038 (class 0 OID 19563)
-- Dependencies: 264
-- Data for Name: product_code_fields; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_code_fields (id, subcategory_id, name, code, description, field_type, "position", max_length, is_required, use_in_code, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4040 (class 0 OID 19569)
-- Dependencies: 266
-- Data for Name: product_codes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_codes (id, product_id, category_id, subcategory_id, full_code, status, created_by, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4042 (class 0 OID 19573)
-- Dependencies: 268
-- Data for Name: product_regions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_regions (id, name, code_letter, description, created_at) FROM stdin;
\.


--
-- TOC entry 4044 (class 0 OID 19579)
-- Dependencies: 270
-- Data for Name: product_subcategories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_subcategories (id, category_id, name, code_letter, description, display_order, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4046 (class 0 OID 19585)
-- Dependencies: 272
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.products (id, type, category, product_mn, product_name, model, specification, brand, unit, retail_price, status, image_path, created_at, updated_at, owner_id, pdf_path) FROM stdin;
1	channel	Basestation	PS4MS2NN	Repeater	Mark1000 MAX	Frequency range: 400-470MHz    Channel spacing: 12.5kHz/25kHz    Max channel: 16    Max Power: 25W    Mode: DMR    NetFunction: NetFlex Cloud	Evertac Solutions	set	3290.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
2	channel	Combiner	SGM1B022CZ1	RF Combiner	E-FH400-2	UHF2   440-470MHz   2-Port   Insertion loss≤ 4.0 dB  IP40  N-Female  2U	Evertac Solutions	set	1000.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
3	channel	Combiner	SGCM1B042CZ1	RF Combiner	E-FH400-4	UHF2   440-470MHz   4-Port   Insertion loss≤ 7.5 dB  IP40  N-Female  2U	Evertac Solutions	set	1380.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
4	channel	Combiner	SGCM1B062CZ1	RF Combiner	E-FH400-6	UHF2   440-470MHz   6-Port   Insertion loss≤ 9.5 dB  IP40  N-Female  2U	Evertac Solutions	set	2250.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
5	channel	Combiner	SGCM1B082CZ1	RF Combiner	E-FH400-8	UHF2   440-470MHz   8-Port   Insertion loss≤11.0 dB  IP40  N-Female  2U	Evertac Solutions	set	2950.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
6	channel	Combiner	SGDE1BU2XCZ1	RF Multi-Coupler	E-JF350/400-2	UHF   350-470MHz   2-Port   Insertion loss≤ 3.5dB  IP40  N-Female  1U	Evertac Solutions	set	509.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
7	channel	Combiner	SGDE1BU4XCZ1	RF Multi-Coupler	E-JF350/400-4	UHF   350-470MHz   4-Port   Insertion loss≤ 6.5dB  IP40  N-Female  1U	Evertac Solutions	set	620.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
8	channel	Combiner	SGDE1BU6XCZ1	RF Multi-Coupler	E-JF350/400-6	UHF   350-470MHz   6-Port   Insertion loss≤ 8.5dB  IP40  N-Female  1U	Evertac Solutions	set	750.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
9	channel	Combiner	SGDE1BU8XCZ1	RF Multi-Coupler	E-JF350/400-8	UHF   350-470MHz   8-Port   Insertion loss≤ 9.5dB  IP40  N-Female  1U	Evertac Solutions	set	1020.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
10	channel	Combiner	SGDULB4H1CZ1	Duplex	E-SGQ400D	UHF2   440-470MHz   2-5MHz   2U	Evertac Solutions	set	1460.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
11	channel	Combiner	SGULN4N1CZ1	Duplex	E-SGQ400N	UFH2   440-470MHz   0.5Mhz   1U	Evertac Solutions	set	700.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
12	channel	Combiner	SGE1AD6xCZ1	DownLink Multi-Splitter	R-EVDC-BLST-D	UHF1  350-470MHz    6+1-Port   Max Input Power 50W   Insertion loss≤0.5dB  N-Female  1U	Evertac Solutions	set	800.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
13	channel	Combiner	SGE1AU6xCZ1	UpLink Multi-Splitter	R-EVDC-BLST-U	UHF1   350-470MHz   6+1-Port   Max Input Power 50W   Insertion loss≤ 0.5dB  N-Female  1U	Evertac Solutions	set	800.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
14	channel	BDA	SGR2SI030	OMU	RFS-400 LT/M	350-470MHz   BW 15MHz   4FP   NetFLEX 	Evertac Solutions	set	1890.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
15	channel	BDA	SGR3SI14S	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 5MHz   33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	2640.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
16	channel	BDA	SGR3SI140	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 10MHz  33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	2640.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
17	channel	BDA	SGR3SI340	ORU	RFT-BDA410 LT/M	440-470MHz   BW 1M   40dBm/10W   REMOTE   NetFLEX	Evertac Solutions	set	4636.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
18	channel	BDA	SGR2DI040	OMU	DRFS-400/M	400-470MHz   BW 20M   32OP   2U   Digital transmit   NetFLEX	Evertac Solutions	set	5455.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
19	channel	BDA	SGR3DI340	ORU	DRFT-BDA410/M	400-470MHz   BW 4M   40dBm/10W   2U   Digital transimit   NetFLEX	Evertac Solutions	set	10455.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
20	channel	BDA	SGGF20000	Cable Feed Modular	FDPower400	modular install in ORU via RF cable to feed power	Evertac Solutions	set	345.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
21	channel	Antenna	SGAIOCN4Y	Indoor Antenna	MA10	UHF   350-470MHz   Max Input Power 50W   0dBi	Evertac Solutions	set	25.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
22	channel	Antenna	SGAIOCB4Y	Smart Indoor Antenna	MA12	UHF   350-470MHz   Max Input Power 50W   Gain 0dBi   Signal detection   iBeacon 	Evertac Solutions	set	95.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
23	channel	Antenna	SGAIOCL4Y	Smart Indoor Antenna	MA11	UHF   350-470MHz   Max Input Power 50W   Gain 0dBi   Signal detection 	Evertac Solutions	set	45.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
24	channel	Antenna	EAN2ICO2FZ1	Integrated explosion-proof antenna	E-ANTO EX	UHF   350-470MHz   50W   Gain 0dBi   IP65 IICA21	Evertac Solutions	set	1030.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
25	channel	Antenna	SGAN2OFD2TE2	Panel Antenna	E-ANTD 400	UHF   450-470MHz   Max Input Power 50W   Gain 2dBi	Evertac Solutions	set	80.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
26	channel	Antenna	SGANLOMO5HR1	Fiber Glass Omni Antenna	E-ANTG 400	UHF   450-470MHz   Max Input Power 50W   5dBi	Evertac Solutions	set	100.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
27	channel	Antenna	SGCDN24Y	Splitter	EVPD-2 LT	80-470MHz   MIP 50W	Evertac Solutions	set	25.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
28	channel	Antenna	SGCCN34Y	Coupler	EVDC-6 LT	350-470MHz   MIP 50W   CP 6dB	Evertac Solutions	set	25.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
29	channel	Antenna	SGCCN44Y	Coupler	EVDC-10 LT	350-470MHz   MIP 50W   CP 10dB	Evertac Solutions	set	25.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
30	channel	Antenna	SGCCN54Y	Coupler	EVDC-15 LT	350-470MHz   MIP 50W   CP 15dB	Evertac Solutions	set	25.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
31	channel	Antenna	SGCCN64Y	Coupler	EVDC-20 LT	350-470MHz   MIP 50W   CP 20dB	Evertac Solutions	set	25.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
32	channel	Antenna	SGCCN74Y	Coupler	EVDC-30 LT	350-470MHz   MIP 50W   CP 30dB	Evertac Solutions	set	25.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
33	channel	Antenna	SGCDF24Y	Splitter	MAPD-2	350-470MHz   MIP 50W   CFP	Evertac Solutions	set	55.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
34	channel	Antenna	SGCCF34Y	Coupler	MADC-6	350-470MHz   MIP 50W   CP 6dB   CFP	Evertac Solutions	set	55.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
35	channel	Antenna	SGCCF44Y	Coupler	MADC-10	350-470MHz   MIP 50W   CP 10dB   CFP	Evertac Solutions	set	55.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
36	channel	Antenna	SGCCF54Y	Coupler	MADC-15	350-470MHz   MIP 50W   CP 15dB   CFP	Evertac Solutions	set	55.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
37	channel	Antenna	SGCCF64Y	Coupler	MADC-20	350-470MHz   MIP 50W   CP 20dB   CFP	Evertac Solutions	set	55.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
38	channel	Application	HYWSTNB1	Access License	LS-NFX-RAD	Two-way radio access to NetFLEX License	Evertac Solutions	unit	45.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
39	channel	Application	HYWSRNB1	Access License	LS-NFX-BDA	ORU access to NetFLEX License	Evertac Solutions	unit	360.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
40	channel	Application	HYWSPNB1	Access License	LS-NFX-RPT	Repeater access to NetFLex License	Evertac Solutions	unit	600.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
41	channel	Application	HYWG0NB1	Gateway application	NFX_GATW	Synchronize setup configure system managment driver update online	Evertac Solutions	set	3050.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
42	channel	Application	HYWP0NC1	NetFLEX Platform 	NFX_MAST_OPETN	Account management System Backup and Recover System structure diagram	Evertac Solutions	set	25500.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
43	channel	Application	EHYW521066	Driver	GW-MOT-RPT	MOTOROLA to NetFLEX Gateway Protocal	Evertac Solutions	unit	6540.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
44	channel	Application	HYWF0NA1	Operation DashBoard	ACC-CWT	System Health analyz   System diagram online Fault Notification  Equipment location 	Evertac Solutions	unit	1600.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
45	channel	Application	HYWT0NA1	Service Operation Tool	ACC-NUT	Tracking and notification system faults to the app   providing standard maintenance process	Evertac Solutions	unit	780.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.00432	1	\N
46	third-party	Application	NDILMOT10	Network Data Interface License	AP_REPEATER__NAI_DATA_ONLY_LIC_KEY	nan	nan	set	0.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
47	third-party	Accessories	PER3RSV	Rack Server	PowerEdge R350 Rack Server	Windows Server Intel® 4 core   8G Cache   4C/8T   Turbo (65W)   3200 MT/s Gateway	DELL	set	2650.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
48	third-party	Accessories	RER7RSV	Rack Server	PowerEdge R740 Rack Server	Windows Server Intel® 6 core   16G Cache   4C/8T   Turbo (65W)   3200 MT/s NetFLex platform 	DELL	set	3840.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
49	third-party	Accessories	W000163	Coaxial Dummy Load	E-TF50	50w 300-1000MHz dummy load  N male connector	nan	unit	41.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
50	third-party	Accessories	EDFWYFC24W	Fiber rack	ST/FC  24口	Standard FC type 24 port cabinet installation	nan	set	96.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
51	third-party	Accessories	EDFWYFC04O	Fiber rack	ST/FC  4口	Standard FC type 4 port wall-mounted installation	nan	set	42.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
52	third-party	Accessories	EJUWY05A40LC	Optical Fiber Jumper Cable Patch Cord	MNOFHC-SMD-50	LC to LC UPC Duplex Single Mode Fiber Patch Cable   5m (16ft)	nan	unit	4.10	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
53	third-party	Accessories	ECAWYGYXTH0401	Optical Fiber	GYXTH-4B1 4芯	4 core outdoor single mode smoke flame retardant	nan	meter	1.23	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
54	third-party	Accessories	OBJANOTHS01	Light arrestor	CA-23RS	0-1000MHz 700W 50Ω N-Female	nan	unit	58.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
55	third-party	Accessories	OBJANOTGR01	Mounting brackets	MONT80	50cm L type	nan	unit	54.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
56	third-party	Accessories	OZCH221035	RF cable	HCAAYZ -50-12	1/2＂50Ω	nan	meter	2.80	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
57	third-party	Accessories	OCIN5JZALC1	Connector adapter	N-J1/2	1/2＂N-J	nan	unit	2.50	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
58	third-party	Accessories	OCIN5KZALC1	Connector adapter	N-50KK	N-KK	nan	unit	2.50	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
59	third-party	Accessories	OCIN5JWALC1	Connector adapter	N-50JKW	90 Degree N-JK	nan	unit	2.50	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
60	third-party	Accessories	OISKHB1JLC1	Jumper Cable	E-JP50-7	0.5m/1.6ft  N-JJ for Antenna	nan	set	9.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
61	third-party	Accessories	EJUMJK4315NJNJ	Jumper Cable	NJ/NJ-3 	1.5m/4.7ft N-JJ for Cabinet	nan	set	6.80	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
62	third-party	Accessories	EJUMJK4315NJQJ	Cabinet	Standard	19 -inch standard 42U with cooling	nan	set	500.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
63	third-party	Accessories	EJUMJK4314NJQJ	Cabinet 	Standard	RS PRO 6U-Rack Server Cabinet	nan	ser	260.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
64	third-party	Accessories	W000166	Explosion-proof box	FZ HH 1012	Explosion-proof rating is Class II B   with steel plate for splitter	nan	set	710.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
65	third-party	Accessories	W000170	Explosion-proof box	FZ HH 1016	Explosion-proof rating is Class II B   with steel plate for ORU	nan	set	1600.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
66	third-party	Radio	TS4D3NMK	Two-way radio	PNR2000	Frequency range: 400MHz    Mode: DMR    Voltage: 3.8V    Function: BlueTooth/iBeacon    Interface.: No-keyboard screen	nan	set	290.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
67	third-party	Radio	YSTSTH	Battery	YSTSTH	Capacity: 3800 mAh    Voltage: 3.8 V    Function: Capacity testing online    Compatibility: PNR2000	nan	set	41.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
68	third-party	Charge	ZSTCN3T	Multi-Charging/Storge cabinet	CRCAB2000	27U charging cabinet   three sets of charging stacks are used   providing the capability to simultaneously charge or store up to 18 two-way radios or battery packs	nan	set	1740.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
69	third-party	Charge	ZSTSN0N	Multi-Charging Stack	CRSTC1000	Comprising a single multi-channel charger and a 19-inch tray   it facilitates the assembly of multiple stacks into a charging cabinet.	nan	set	450.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
70	third-party	Charge	ZSTZN0N	Multi-Charging Hub	CMP2600	6-way walkie-talkie/battery charging combination   featuring battery management and NetFlex cloud management capabilities	nan	set	320.00	1	\N	2025-06-15 22:33:38.18411	2025-06-15 22:44:09.024263	1	\N
\.


--
-- TOC entry 4048 (class 0 OID 19591)
-- Dependencies: 274
-- Data for Name: project_members; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_members (id, project_id, user_id, role, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4050 (class 0 OID 19595)
-- Dependencies: 276
-- Data for Name: project_rating_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_rating_records (id, project_id, user_id, rating, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4052 (class 0 OID 19600)
-- Dependencies: 278
-- Data for Name: project_scoring_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_scoring_config (id, category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4054 (class 0 OID 19610)
-- Dependencies: 280
-- Data for Name: project_scoring_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_scoring_records (id, project_id, category, field_name, score_value, awarded_by, auto_calculated, notes, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4056 (class 0 OID 19620)
-- Dependencies: 282
-- Data for Name: project_stage_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_stage_history (id, project_id, from_stage, to_stage, change_date, change_week, change_month, change_year, account_id, remarks, created_at) FROM stdin;
\.


--
-- TOC entry 4058 (class 0 OID 19627)
-- Dependencies: 284
-- Data for Name: project_total_scores; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_total_scores (id, project_id, information_score, quotation_score, stage_score, manual_score, total_score, star_rating, last_calculated, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4060 (class 0 OID 19640)
-- Dependencies: 286
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.projects (id, project_name, report_time, project_type, report_source, product_situation, end_user, design_issues, dealer, contractor, system_integrator, current_stage, stage_description, authorization_code, delivery_forecast, quotation_customer, authorization_status, feedback, created_at, updated_at, owner_id, is_locked, locked_reason, locked_by, locked_at, is_active, last_activity_date, activity_reason, vendor_sales_manager_id, rating) FROM stdin;
\.


--
-- TOC entry 4062 (class 0 OID 19651)
-- Dependencies: 288
-- Data for Name: purchase_order_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.purchase_order_details (id, order_id, product_id, product_name, product_model, product_desc, brand, quantity, unit, unit_price, discount, total_price, received_quantity, notes) FROM stdin;
\.


--
-- TOC entry 4064 (class 0 OID 19657)
-- Dependencies: 290
-- Data for Name: purchase_orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.purchase_orders (id, order_number, company_id, order_type, order_date, expected_date, status, total_amount, total_quantity, currency, payment_terms, delivery_address, description, created_by_id, approved_by_id, approved_at, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4066 (class 0 OID 19663)
-- Dependencies: 292
-- Data for Name: quotation_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.quotation_details (id, quotation_id, product_name, product_model, product_desc, brand, unit, quantity, discount, market_price, unit_price, total_price, product_mn, created_at, updated_at, implant_subtotal) FROM stdin;
\.


--
-- TOC entry 4068 (class 0 OID 19670)
-- Dependencies: 294
-- Data for Name: quotations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.quotations (id, quotation_number, project_id, contact_id, amount, project_stage, project_type, created_at, updated_at, owner_id, approval_status, approved_stages, approval_history, is_locked, lock_reason, locked_by, locked_at, confirmation_badge_status, confirmation_badge_color, confirmed_by, confirmed_at, product_signature, implant_total_amount) FROM stdin;
\.


--
-- TOC entry 4070 (class 0 OID 19684)
-- Dependencies: 296
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_permissions (id, role, module, can_view, can_create, can_edit, can_delete) FROM stdin;
1	region_sales	project	t	t	t	t
2	region_sales	customer	t	t	t	t
3	region_sales	quotation	t	t	t	t
4	region_sales	product	t	f	f	f
5	region_sales	product_code	f	f	f	f
6	region_sales	inventory	f	f	f	f
7	region_sales	settlement	f	f	f	f
8	region_sales	order	f	f	f	f
9	region_sales	user	f	f	f	f
10	region_sales	permission	f	f	f	f
11	region_sales	project_rating	f	f	f	f
\.


--
-- TOC entry 4072 (class 0 OID 19688)
-- Dependencies: 298
-- Data for Name: settlement_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.settlement_details (id, settlement_id, inventory_id, product_id, quantity_settled, quantity_before, quantity_after, unit, notes) FROM stdin;
\.


--
-- TOC entry 4074 (class 0 OID 19694)
-- Dependencies: 300
-- Data for Name: settlement_order_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.settlement_order_details (id, pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_order_id, settlement_company_id, settlement_status, settlement_date, settlement_notes) FROM stdin;
\.


--
-- TOC entry 4076 (class 0 OID 19700)
-- Dependencies: 302
-- Data for Name: settlement_orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.settlement_orders (id, order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, total_amount, total_discount_rate, status, approved_by, approved_at, created_by, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4078 (class 0 OID 19704)
-- Dependencies: 304
-- Data for Name: settlements; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.settlements (id, settlement_number, company_id, settlement_date, status, total_items, description, created_by_id, approved_by_id, approved_at, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4080 (class 0 OID 19710)
-- Dependencies: 306
-- Data for Name: solution_manager_email_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solution_manager_email_settings (id, user_id, quotation_created, quotation_updated, project_created, project_stage_changed, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4082 (class 0 OID 19714)
-- Dependencies: 308
-- Data for Name: system_metrics; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.system_metrics (id, version_id, avg_response_time, max_response_time, error_rate, active_users, total_requests, database_size, cpu_usage, memory_usage, disk_usage, recorded_at) FROM stdin;
\.


--
-- TOC entry 4084 (class 0 OID 19718)
-- Dependencies: 310
-- Data for Name: system_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.system_settings (id, key, value, description, created_at, updated_at) FROM stdin;
1	customer_activity_threshold	1	客户活跃度阈值（天）- 超过指定天数无活动则标记为不活跃	2025-06-15 06:48:47.236899	2025-06-15 06:48:47.236903
2	project_activity_threshold	7	项目活跃度阈值（天）- 超过指定天数无活动则标记为不活跃	2025-06-15 06:48:47.247261	2025-06-15 06:48:47.247265
\.


--
-- TOC entry 4086 (class 0 OID 19724)
-- Dependencies: 312
-- Data for Name: upgrade_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.upgrade_logs (id, version_id, from_version, to_version, upgrade_date, upgrade_type, status, upgrade_notes, error_message, duration_seconds, operator_id, operator_name, environment, server_info) FROM stdin;
\.


--
-- TOC entry 4088 (class 0 OID 19730)
-- Dependencies: 314
-- Data for Name: user_event_subscriptions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_event_subscriptions (id, user_id, target_user_id, event_id, enabled, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4090 (class 0 OID 19734)
-- Dependencies: 316
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, password_hash, real_name, company_name, email, phone, department, is_department_manager, role, is_profile_complete, wechat_openid, wechat_nickname, wechat_avatar, is_active, created_at, last_login, updated_at) FROM stdin;
1	admin	scrypt:32768:8:1$uq2wnCsTx8LAMWyD$7c2dda60b418450997827c900f0c4b6860e99486891a3137cda79f113784d583ef28dac511d1dba6c3b7e693dc63ed84ccd71bb3b49c475606aaee750d22d40b	系统管理员	和源通信（上海）股份有限公司	james.ni@evertacsolutions.com	13003258568		f	admin	\N	\N	\N	\N	t	\N	\N	1749741952.043801
3	roy	scrypt:32768:8:1$Cb4uOc9gIaRn5zIg$e1d052d695321230d1bfff4f1aff0fb77750c4984f581d73e2597eb4a7afb773a2f6b389950cf03bc1a0267d5ade4e5ebf2107b3eaa64510f26b983f38a2b1cf	Roy Lim	evertac solutions	roy@evertacsolutions.com	+60176033453	sales_dept	f	region_sales	f	\N	\N	\N	f	1749996280.8795562	\N	1749996365.8652391
4	quah	scrypt:32768:8:1$cB3IxLAX8O9PGFBy$911028bf478b2032270eb0904188f43cb0870b458638e901c654943b0291b83ae23307c4bcdae6654e33c15fd4c4b6ff5856c1ebf2e9f327b952d936112f60dc	quah	evertac solutions	quah@evertacsolution		sales_dept	f	region_sales	f	\N	\N	\N	f	1749996407.6163986	\N	1749996407.6164007
5	patrick	scrypt:32768:8:1$IvzNkvfI5imeh8Vq$7a1b0b863cd1dce37c9b2a1f2c81315302df060d094ca3f7912cb7321c1426931614a6e22afd5f5775e0bdcedd4cfad9519c8ab5e67e71fac4ca350dc4ddd4da	patrick ku	evertac solutions	patrick@evertacsolutions	+60123692826	sales_dept	f	region_sales	f	\N	\N	\N	f	1749996522.7424405	\N	1749996522.7424426
\.


--
-- TOC entry 4092 (class 0 OID 19740)
-- Dependencies: 318
-- Data for Name: version_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.version_records (id, version_number, version_name, release_date, description, is_current, environment, total_features, total_fixes, total_improvements, git_commit, build_number, created_at, updated_at) FROM stdin;
1	1.0.1	PMA项目管理系统	2025-06-15 06:48:47.20926	PMA项目管理系统当前运行版本，包含完整的项目管理、客户管理、报价管理、产品管理等功能。	t	production	0	0	0	\N	\N	2025-06-15 06:48:47.210719	2025-06-15 06:48:47.210723
\.


--
-- TOC entry 4323 (class 0 OID 0)
-- Dependencies: 216
-- Name: action_reply_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.action_reply_id_seq', 1, false);


--
-- TOC entry 4324 (class 0 OID 0)
-- Dependencies: 218
-- Name: actions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.actions_id_seq', 1, false);


--
-- TOC entry 4325 (class 0 OID 0)
-- Dependencies: 220
-- Name: affiliations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.affiliations_id_seq', 1, false);


--
-- TOC entry 4326 (class 0 OID 0)
-- Dependencies: 223
-- Name: approval_instance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_instance_id_seq', 1, false);


--
-- TOC entry 4327 (class 0 OID 0)
-- Dependencies: 225
-- Name: approval_process_template_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_process_template_id_seq', 1, false);


--
-- TOC entry 4328 (class 0 OID 0)
-- Dependencies: 226
-- Name: approval_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_record_id_seq', 1, false);


--
-- TOC entry 4329 (class 0 OID 0)
-- Dependencies: 229
-- Name: approval_step_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_step_id_seq', 1, false);


--
-- TOC entry 4330 (class 0 OID 0)
-- Dependencies: 231
-- Name: change_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.change_logs_id_seq', 6, true);


--
-- TOC entry 4331 (class 0 OID 0)
-- Dependencies: 233
-- Name: companies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.companies_id_seq', 1, false);


--
-- TOC entry 4332 (class 0 OID 0)
-- Dependencies: 235
-- Name: contacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contacts_id_seq', 1, false);


--
-- TOC entry 4333 (class 0 OID 0)
-- Dependencies: 237
-- Name: dev_product_specs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dev_product_specs_id_seq', 1, false);


--
-- TOC entry 4334 (class 0 OID 0)
-- Dependencies: 239
-- Name: dev_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dev_products_id_seq', 1, false);


--
-- TOC entry 4335 (class 0 OID 0)
-- Dependencies: 241
-- Name: dictionaries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dictionaries_id_seq', 6, true);


--
-- TOC entry 4336 (class 0 OID 0)
-- Dependencies: 243
-- Name: event_registry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.event_registry_id_seq', 1, false);


--
-- TOC entry 4337 (class 0 OID 0)
-- Dependencies: 245
-- Name: feature_changes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.feature_changes_id_seq', 1, false);


--
-- TOC entry 4338 (class 0 OID 0)
-- Dependencies: 247
-- Name: inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_id_seq', 1, false);


--
-- TOC entry 4339 (class 0 OID 0)
-- Dependencies: 249
-- Name: inventory_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_transactions_id_seq', 1, false);


--
-- TOC entry 4340 (class 0 OID 0)
-- Dependencies: 251
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.permissions_id_seq', 1, false);


--
-- TOC entry 4341 (class 0 OID 0)
-- Dependencies: 253
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pricing_order_approval_records_id_seq', 1, false);


--
-- TOC entry 4342 (class 0 OID 0)
-- Dependencies: 255
-- Name: pricing_order_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pricing_order_details_id_seq', 1, false);


--
-- TOC entry 4343 (class 0 OID 0)
-- Dependencies: 257
-- Name: pricing_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pricing_orders_id_seq', 1, false);


--
-- TOC entry 4344 (class 0 OID 0)
-- Dependencies: 259
-- Name: product_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_categories_id_seq', 1, false);


--
-- TOC entry 4345 (class 0 OID 0)
-- Dependencies: 261
-- Name: product_code_field_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_code_field_options_id_seq', 1, false);


--
-- TOC entry 4346 (class 0 OID 0)
-- Dependencies: 263
-- Name: product_code_field_values_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_code_field_values_id_seq', 1, false);


--
-- TOC entry 4347 (class 0 OID 0)
-- Dependencies: 265
-- Name: product_code_fields_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_code_fields_id_seq', 1, false);


--
-- TOC entry 4348 (class 0 OID 0)
-- Dependencies: 267
-- Name: product_codes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_codes_id_seq', 1, false);


--
-- TOC entry 4349 (class 0 OID 0)
-- Dependencies: 269
-- Name: product_regions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_regions_id_seq', 1, false);


--
-- TOC entry 4350 (class 0 OID 0)
-- Dependencies: 271
-- Name: product_subcategories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_subcategories_id_seq', 1, false);


--
-- TOC entry 4351 (class 0 OID 0)
-- Dependencies: 273
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.products_id_seq', 70, true);


--
-- TOC entry 4352 (class 0 OID 0)
-- Dependencies: 275
-- Name: project_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_members_id_seq', 1, false);


--
-- TOC entry 4353 (class 0 OID 0)
-- Dependencies: 277
-- Name: project_rating_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_rating_records_id_seq', 1, false);


--
-- TOC entry 4354 (class 0 OID 0)
-- Dependencies: 279
-- Name: project_scoring_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_scoring_config_id_seq', 1, false);


--
-- TOC entry 4355 (class 0 OID 0)
-- Dependencies: 281
-- Name: project_scoring_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_scoring_records_id_seq', 1, false);


--
-- TOC entry 4356 (class 0 OID 0)
-- Dependencies: 283
-- Name: project_stage_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_stage_history_id_seq', 1, false);


--
-- TOC entry 4357 (class 0 OID 0)
-- Dependencies: 285
-- Name: project_total_scores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_total_scores_id_seq', 1, false);


--
-- TOC entry 4358 (class 0 OID 0)
-- Dependencies: 287
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.projects_id_seq', 1, false);


--
-- TOC entry 4359 (class 0 OID 0)
-- Dependencies: 289
-- Name: purchase_order_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.purchase_order_details_id_seq', 1, false);


--
-- TOC entry 4360 (class 0 OID 0)
-- Dependencies: 291
-- Name: purchase_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.purchase_orders_id_seq', 1, false);


--
-- TOC entry 4361 (class 0 OID 0)
-- Dependencies: 293
-- Name: quotation_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.quotation_details_id_seq', 1, false);


--
-- TOC entry 4362 (class 0 OID 0)
-- Dependencies: 295
-- Name: quotations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.quotations_id_seq', 1, false);


--
-- TOC entry 4363 (class 0 OID 0)
-- Dependencies: 297
-- Name: role_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.role_permissions_id_seq', 11, true);


--
-- TOC entry 4364 (class 0 OID 0)
-- Dependencies: 299
-- Name: settlement_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.settlement_details_id_seq', 1, false);


--
-- TOC entry 4365 (class 0 OID 0)
-- Dependencies: 301
-- Name: settlement_order_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.settlement_order_details_id_seq', 1, false);


--
-- TOC entry 4366 (class 0 OID 0)
-- Dependencies: 303
-- Name: settlement_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.settlement_orders_id_seq', 1, false);


--
-- TOC entry 4367 (class 0 OID 0)
-- Dependencies: 305
-- Name: settlements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.settlements_id_seq', 1, false);


--
-- TOC entry 4368 (class 0 OID 0)
-- Dependencies: 307
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solution_manager_email_settings_id_seq', 1, false);


--
-- TOC entry 4369 (class 0 OID 0)
-- Dependencies: 309
-- Name: system_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.system_metrics_id_seq', 1, false);


--
-- TOC entry 4370 (class 0 OID 0)
-- Dependencies: 311
-- Name: system_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.system_settings_id_seq', 2, true);


--
-- TOC entry 4371 (class 0 OID 0)
-- Dependencies: 313
-- Name: upgrade_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.upgrade_logs_id_seq', 1, false);


--
-- TOC entry 4372 (class 0 OID 0)
-- Dependencies: 315
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_event_subscriptions_id_seq', 1, false);


--
-- TOC entry 4373 (class 0 OID 0)
-- Dependencies: 317
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 5, true);


--
-- TOC entry 4374 (class 0 OID 0)
-- Dependencies: 319
-- Name: version_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.version_records_id_seq', 1, true);


--
-- TOC entry 3584 (class 2606 OID 19798)
-- Name: action_reply action_reply_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_pkey PRIMARY KEY (id);


--
-- TOC entry 3586 (class 2606 OID 19800)
-- Name: actions actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_pkey PRIMARY KEY (id);


--
-- TOC entry 3588 (class 2606 OID 19802)
-- Name: affiliations affiliations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_pkey PRIMARY KEY (id);


--
-- TOC entry 3592 (class 2606 OID 19804)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 3594 (class 2606 OID 19806)
-- Name: approval_instance approval_instance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_pkey PRIMARY KEY (id);


--
-- TOC entry 3596 (class 2606 OID 19808)
-- Name: approval_process_template approval_process_template_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_pkey PRIMARY KEY (id);


--
-- TOC entry 3598 (class 2606 OID 19810)
-- Name: approval_record approval_record_temp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_temp_pkey PRIMARY KEY (id);


--
-- TOC entry 3600 (class 2606 OID 19812)
-- Name: approval_step approval_step_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_pkey PRIMARY KEY (id);


--
-- TOC entry 3602 (class 2606 OID 19814)
-- Name: change_logs change_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs
    ADD CONSTRAINT change_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 3604 (class 2606 OID 19816)
-- Name: companies companies_company_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_company_code_key UNIQUE (company_code);


--
-- TOC entry 3606 (class 2606 OID 19818)
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- TOC entry 3608 (class 2606 OID 19820)
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (id);


--
-- TOC entry 3610 (class 2606 OID 19822)
-- Name: dev_product_specs dev_product_specs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs
    ADD CONSTRAINT dev_product_specs_pkey PRIMARY KEY (id);


--
-- TOC entry 3612 (class 2606 OID 19824)
-- Name: dev_products dev_products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_pkey PRIMARY KEY (id);


--
-- TOC entry 3614 (class 2606 OID 19826)
-- Name: dictionaries dictionaries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT dictionaries_pkey PRIMARY KEY (id);


--
-- TOC entry 3618 (class 2606 OID 19828)
-- Name: event_registry event_registry_event_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_event_key_key UNIQUE (event_key);


--
-- TOC entry 3620 (class 2606 OID 19830)
-- Name: event_registry event_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_pkey PRIMARY KEY (id);


--
-- TOC entry 3622 (class 2606 OID 19832)
-- Name: feature_changes feature_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_pkey PRIMARY KEY (id);


--
-- TOC entry 3624 (class 2606 OID 19834)
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (id);


--
-- TOC entry 3628 (class 2606 OID 19836)
-- Name: inventory_transactions inventory_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_pkey PRIMARY KEY (id);


--
-- TOC entry 3630 (class 2606 OID 19838)
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3634 (class 2606 OID 19840)
-- Name: pricing_order_approval_records pricing_order_approval_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3636 (class 2606 OID 19842)
-- Name: pricing_order_details pricing_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details
    ADD CONSTRAINT pricing_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3638 (class 2606 OID 19844)
-- Name: pricing_orders pricing_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 3640 (class 2606 OID 19846)
-- Name: pricing_orders pricing_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 3642 (class 2606 OID 19848)
-- Name: product_categories product_categories_code_letter_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_code_letter_key UNIQUE (code_letter);


--
-- TOC entry 3644 (class 2606 OID 19850)
-- Name: product_categories product_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_pkey PRIMARY KEY (id);


--
-- TOC entry 3646 (class 2606 OID 19852)
-- Name: product_code_field_options product_code_field_options_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options
    ADD CONSTRAINT product_code_field_options_pkey PRIMARY KEY (id);


--
-- TOC entry 3648 (class 2606 OID 19854)
-- Name: product_code_field_values product_code_field_values_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_pkey PRIMARY KEY (id);


--
-- TOC entry 3650 (class 2606 OID 19856)
-- Name: product_code_fields product_code_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields
    ADD CONSTRAINT product_code_fields_pkey PRIMARY KEY (id);


--
-- TOC entry 3652 (class 2606 OID 19858)
-- Name: product_codes product_codes_full_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_full_code_key UNIQUE (full_code);


--
-- TOC entry 3654 (class 2606 OID 19860)
-- Name: product_codes product_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_pkey PRIMARY KEY (id);


--
-- TOC entry 3656 (class 2606 OID 19862)
-- Name: product_regions product_regions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_regions
    ADD CONSTRAINT product_regions_pkey PRIMARY KEY (id);


--
-- TOC entry 3658 (class 2606 OID 19864)
-- Name: product_subcategories product_subcategories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT product_subcategories_pkey PRIMARY KEY (id);


--
-- TOC entry 3662 (class 2606 OID 19866)
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- TOC entry 3664 (class 2606 OID 19868)
-- Name: products products_product_mn_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_product_mn_key UNIQUE (product_mn);


--
-- TOC entry 3666 (class 2606 OID 19870)
-- Name: project_members project_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (id);


--
-- TOC entry 3668 (class 2606 OID 19872)
-- Name: project_rating_records project_rating_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3672 (class 2606 OID 19874)
-- Name: project_scoring_config project_scoring_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config
    ADD CONSTRAINT project_scoring_config_pkey PRIMARY KEY (id);


--
-- TOC entry 3676 (class 2606 OID 19876)
-- Name: project_scoring_records project_scoring_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3681 (class 2606 OID 19878)
-- Name: project_stage_history project_stage_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history
    ADD CONSTRAINT project_stage_history_pkey PRIMARY KEY (id);


--
-- TOC entry 3683 (class 2606 OID 19880)
-- Name: project_total_scores project_total_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_pkey PRIMARY KEY (id);


--
-- TOC entry 3685 (class 2606 OID 19882)
-- Name: project_total_scores project_total_scores_project_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_project_id_key UNIQUE (project_id);


--
-- TOC entry 3689 (class 2606 OID 19884)
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- TOC entry 3691 (class 2606 OID 19886)
-- Name: purchase_order_details purchase_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3693 (class 2606 OID 19888)
-- Name: purchase_orders purchase_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 3695 (class 2606 OID 19890)
-- Name: purchase_orders purchase_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 3697 (class 2606 OID 19892)
-- Name: quotation_details quotation_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details
    ADD CONSTRAINT quotation_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3699 (class 2606 OID 19894)
-- Name: quotations quotations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_pkey PRIMARY KEY (id);


--
-- TOC entry 3701 (class 2606 OID 19896)
-- Name: quotations quotations_quotation_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_quotation_number_key UNIQUE (quotation_number);


--
-- TOC entry 3703 (class 2606 OID 19898)
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3707 (class 2606 OID 19900)
-- Name: settlement_details settlement_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3709 (class 2606 OID 19902)
-- Name: settlement_order_details settlement_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3711 (class 2606 OID 19904)
-- Name: settlement_orders settlement_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 3713 (class 2606 OID 19906)
-- Name: settlement_orders settlement_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 3715 (class 2606 OID 19908)
-- Name: settlements settlements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_pkey PRIMARY KEY (id);


--
-- TOC entry 3717 (class 2606 OID 19910)
-- Name: settlements settlements_settlement_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_settlement_number_key UNIQUE (settlement_number);


--
-- TOC entry 3719 (class 2606 OID 19912)
-- Name: solution_manager_email_settings solution_manager_email_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT solution_manager_email_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 3723 (class 2606 OID 19914)
-- Name: system_metrics system_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_pkey PRIMARY KEY (id);


--
-- TOC entry 3726 (class 2606 OID 19916)
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 3590 (class 2606 OID 19918)
-- Name: affiliations uix_owner_viewer; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT uix_owner_viewer UNIQUE (owner_id, viewer_id);


--
-- TOC entry 3705 (class 2606 OID 19920)
-- Name: role_permissions uix_role_module; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT uix_role_module UNIQUE (role, module);


--
-- TOC entry 3616 (class 2606 OID 19922)
-- Name: dictionaries uix_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT uix_type_key UNIQUE (type, key);


--
-- TOC entry 3632 (class 2606 OID 19924)
-- Name: permissions uix_user_module; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT uix_user_module UNIQUE (user_id, module);


--
-- TOC entry 3626 (class 2606 OID 19926)
-- Name: inventory unique_company_product_inventory; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT unique_company_product_inventory UNIQUE (company_id, product_id);


--
-- TOC entry 3728 (class 2606 OID 19928)
-- Name: upgrade_logs upgrade_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 3670 (class 2606 OID 19930)
-- Name: project_rating_records uq_project_user_rating; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT uq_project_user_rating UNIQUE (project_id, user_id);


--
-- TOC entry 3674 (class 2606 OID 19932)
-- Name: project_scoring_config uq_scoring_config; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config
    ADD CONSTRAINT uq_scoring_config UNIQUE (category, field_name);


--
-- TOC entry 3678 (class 2606 OID 19934)
-- Name: project_scoring_records uq_scoring_record_with_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT uq_scoring_record_with_user UNIQUE (project_id, category, field_name, awarded_by);


--
-- TOC entry 3721 (class 2606 OID 19936)
-- Name: solution_manager_email_settings uq_solution_manager_email_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT uq_solution_manager_email_user UNIQUE (user_id);


--
-- TOC entry 3660 (class 2606 OID 19938)
-- Name: product_subcategories uq_subcategory_code_letter; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT uq_subcategory_code_letter UNIQUE (category_id, code_letter);


--
-- TOC entry 3730 (class 2606 OID 19940)
-- Name: user_event_subscriptions uq_user_target_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT uq_user_target_event UNIQUE (user_id, target_user_id, event_id);


--
-- TOC entry 3732 (class 2606 OID 19942)
-- Name: user_event_subscriptions user_event_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_pkey PRIMARY KEY (id);


--
-- TOC entry 3734 (class 2606 OID 19944)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 3736 (class 2606 OID 19946)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 3738 (class 2606 OID 19948)
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- TOC entry 3740 (class 2606 OID 19950)
-- Name: users users_wechat_openid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_wechat_openid_key UNIQUE (wechat_openid);


--
-- TOC entry 3742 (class 2606 OID 19952)
-- Name: version_records version_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records
    ADD CONSTRAINT version_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3744 (class 2606 OID 19954)
-- Name: version_records version_records_version_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records
    ADD CONSTRAINT version_records_version_number_key UNIQUE (version_number);


--
-- TOC entry 3679 (class 1259 OID 19955)
-- Name: ix_project_stage_history_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_stage_history_project_id ON public.project_stage_history USING btree (project_id);


--
-- TOC entry 3686 (class 1259 OID 19956)
-- Name: ix_projects_authorization_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_authorization_code ON public.projects USING btree (authorization_code);


--
-- TOC entry 3687 (class 1259 OID 19957)
-- Name: ix_projects_project_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_project_name ON public.projects USING btree (project_name);


--
-- TOC entry 3724 (class 1259 OID 19958)
-- Name: ix_system_settings_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_system_settings_key ON public.system_settings USING btree (key);


--
-- TOC entry 3745 (class 2606 OID 19959)
-- Name: action_reply action_reply_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.actions(id);


--
-- TOC entry 3746 (class 2606 OID 19964)
-- Name: action_reply action_reply_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3747 (class 2606 OID 19969)
-- Name: action_reply action_reply_parent_reply_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_parent_reply_id_fkey FOREIGN KEY (parent_reply_id) REFERENCES public.action_reply(id);


--
-- TOC entry 3748 (class 2606 OID 19974)
-- Name: actions actions_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 3749 (class 2606 OID 19979)
-- Name: actions actions_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- TOC entry 3750 (class 2606 OID 19984)
-- Name: actions actions_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3751 (class 2606 OID 19989)
-- Name: actions actions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3752 (class 2606 OID 19994)
-- Name: affiliations affiliations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3753 (class 2606 OID 19999)
-- Name: affiliations affiliations_viewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_viewer_id_fkey FOREIGN KEY (viewer_id) REFERENCES public.users(id);


--
-- TOC entry 3754 (class 2606 OID 20004)
-- Name: approval_instance approval_instance_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3755 (class 2606 OID 20009)
-- Name: approval_instance approval_instance_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- TOC entry 3756 (class 2606 OID 20014)
-- Name: approval_process_template approval_process_template_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3757 (class 2606 OID 20019)
-- Name: approval_record approval_record_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES public.approval_instance(id);


--
-- TOC entry 3760 (class 2606 OID 20024)
-- Name: approval_step approval_step_approver_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_approver_user_id_fkey FOREIGN KEY (approver_user_id) REFERENCES public.users(id);


--
-- TOC entry 3761 (class 2606 OID 20029)
-- Name: approval_step approval_step_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- TOC entry 3762 (class 2606 OID 20034)
-- Name: change_logs change_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs
    ADD CONSTRAINT change_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3763 (class 2606 OID 20039)
-- Name: companies companies_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3764 (class 2606 OID 20044)
-- Name: contacts contacts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 3765 (class 2606 OID 20049)
-- Name: contacts contacts_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3766 (class 2606 OID 20054)
-- Name: dev_product_specs dev_product_specs_dev_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs
    ADD CONSTRAINT dev_product_specs_dev_product_id_fkey FOREIGN KEY (dev_product_id) REFERENCES public.dev_products(id);


--
-- TOC entry 3767 (class 2606 OID 20059)
-- Name: dev_products dev_products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 3768 (class 2606 OID 20064)
-- Name: dev_products dev_products_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3769 (class 2606 OID 20069)
-- Name: dev_products dev_products_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3770 (class 2606 OID 20074)
-- Name: dev_products dev_products_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.product_regions(id);


--
-- TOC entry 3771 (class 2606 OID 20079)
-- Name: dev_products dev_products_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 3772 (class 2606 OID 20084)
-- Name: feature_changes feature_changes_developer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_developer_id_fkey FOREIGN KEY (developer_id) REFERENCES public.users(id);


--
-- TOC entry 3773 (class 2606 OID 20089)
-- Name: feature_changes feature_changes_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 3758 (class 2606 OID 20094)
-- Name: approval_record fk_approval_record_approver_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT fk_approval_record_approver_id FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- TOC entry 3759 (class 2606 OID 20099)
-- Name: approval_record fk_approval_record_step_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT fk_approval_record_step_id FOREIGN KEY (step_id) REFERENCES public.approval_step(id);


--
-- TOC entry 3825 (class 2606 OID 20104)
-- Name: settlement_order_details fk_settlement_order_details_settlement_company; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT fk_settlement_order_details_settlement_company FOREIGN KEY (settlement_company_id) REFERENCES public.companies(id);


--
-- TOC entry 3774 (class 2606 OID 20109)
-- Name: inventory inventory_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 3775 (class 2606 OID 20114)
-- Name: inventory inventory_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 3776 (class 2606 OID 20119)
-- Name: inventory inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 3777 (class 2606 OID 20124)
-- Name: inventory_transactions inventory_transactions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 3778 (class 2606 OID 20129)
-- Name: inventory_transactions inventory_transactions_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- TOC entry 3779 (class 2606 OID 20134)
-- Name: permissions permissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3780 (class 2606 OID 20139)
-- Name: pricing_order_approval_records pricing_order_approval_records_approver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_approver_id_fkey FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- TOC entry 3781 (class 2606 OID 20144)
-- Name: pricing_order_approval_records pricing_order_approval_records_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 3782 (class 2606 OID 20149)
-- Name: pricing_order_details pricing_order_details_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details
    ADD CONSTRAINT pricing_order_details_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 3783 (class 2606 OID 20154)
-- Name: pricing_orders pricing_orders_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 3784 (class 2606 OID 20159)
-- Name: pricing_orders pricing_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3785 (class 2606 OID 20164)
-- Name: pricing_orders pricing_orders_dealer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_dealer_id_fkey FOREIGN KEY (dealer_id) REFERENCES public.companies(id);


--
-- TOC entry 3786 (class 2606 OID 20169)
-- Name: pricing_orders pricing_orders_distributor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_distributor_id_fkey FOREIGN KEY (distributor_id) REFERENCES public.companies(id);


--
-- TOC entry 3787 (class 2606 OID 20174)
-- Name: pricing_orders pricing_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3788 (class 2606 OID 20179)
-- Name: pricing_orders pricing_orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 3789 (class 2606 OID 20184)
-- Name: product_code_field_options product_code_field_options_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options
    ADD CONSTRAINT product_code_field_options_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.product_code_fields(id);


--
-- TOC entry 3790 (class 2606 OID 20189)
-- Name: product_code_field_values product_code_field_values_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.product_code_fields(id);


--
-- TOC entry 3791 (class 2606 OID 20194)
-- Name: product_code_field_values product_code_field_values_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_option_id_fkey FOREIGN KEY (option_id) REFERENCES public.product_code_field_options(id);


--
-- TOC entry 3792 (class 2606 OID 20199)
-- Name: product_code_field_values product_code_field_values_product_code_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_product_code_id_fkey FOREIGN KEY (product_code_id) REFERENCES public.product_codes(id);


--
-- TOC entry 3793 (class 2606 OID 20204)
-- Name: product_code_fields product_code_fields_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields
    ADD CONSTRAINT product_code_fields_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 3794 (class 2606 OID 20209)
-- Name: product_codes product_codes_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 3795 (class 2606 OID 20214)
-- Name: product_codes product_codes_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3796 (class 2606 OID 20219)
-- Name: product_codes product_codes_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 3797 (class 2606 OID 20224)
-- Name: product_codes product_codes_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 3798 (class 2606 OID 20229)
-- Name: product_subcategories product_subcategories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT product_subcategories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 3799 (class 2606 OID 20234)
-- Name: products products_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3800 (class 2606 OID 20239)
-- Name: project_members project_members_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3801 (class 2606 OID 20244)
-- Name: project_members project_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3802 (class 2606 OID 20249)
-- Name: project_rating_records project_rating_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 3803 (class 2606 OID 20254)
-- Name: project_rating_records project_rating_records_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3804 (class 2606 OID 20259)
-- Name: project_scoring_records project_scoring_records_awarded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_awarded_by_fkey FOREIGN KEY (awarded_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- TOC entry 3805 (class 2606 OID 20264)
-- Name: project_scoring_records project_scoring_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 3806 (class 2606 OID 20269)
-- Name: project_stage_history project_stage_history_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history
    ADD CONSTRAINT project_stage_history_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3807 (class 2606 OID 20274)
-- Name: project_total_scores project_total_scores_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 3808 (class 2606 OID 20279)
-- Name: projects projects_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- TOC entry 3809 (class 2606 OID 20284)
-- Name: projects projects_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3810 (class 2606 OID 20289)
-- Name: projects projects_vendor_sales_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_vendor_sales_manager_id_fkey FOREIGN KEY (vendor_sales_manager_id) REFERENCES public.users(id);


--
-- TOC entry 3811 (class 2606 OID 20294)
-- Name: purchase_order_details purchase_order_details_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.purchase_orders(id);


--
-- TOC entry 3812 (class 2606 OID 20299)
-- Name: purchase_order_details purchase_order_details_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 3813 (class 2606 OID 20304)
-- Name: purchase_orders purchase_orders_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- TOC entry 3814 (class 2606 OID 20309)
-- Name: purchase_orders purchase_orders_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 3815 (class 2606 OID 20314)
-- Name: purchase_orders purchase_orders_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 3816 (class 2606 OID 20319)
-- Name: quotation_details quotation_details_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details
    ADD CONSTRAINT quotation_details_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 3817 (class 2606 OID 20324)
-- Name: quotations quotations_confirmed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_confirmed_by_fkey FOREIGN KEY (confirmed_by) REFERENCES public.users(id);


--
-- TOC entry 3818 (class 2606 OID 20329)
-- Name: quotations quotations_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- TOC entry 3819 (class 2606 OID 20334)
-- Name: quotations quotations_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- TOC entry 3820 (class 2606 OID 20339)
-- Name: quotations quotations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 3821 (class 2606 OID 20344)
-- Name: quotations quotations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3822 (class 2606 OID 20349)
-- Name: settlement_details settlement_details_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- TOC entry 3823 (class 2606 OID 20354)
-- Name: settlement_details settlement_details_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 3824 (class 2606 OID 20359)
-- Name: settlement_details settlement_details_settlement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_settlement_id_fkey FOREIGN KEY (settlement_id) REFERENCES public.settlements(id);


--
-- TOC entry 3826 (class 2606 OID 20364)
-- Name: settlement_order_details settlement_order_details_pricing_detail_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pricing_detail_id_fkey FOREIGN KEY (pricing_detail_id) REFERENCES public.pricing_order_details(id);


--
-- TOC entry 3827 (class 2606 OID 20369)
-- Name: settlement_order_details settlement_order_details_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 3828 (class 2606 OID 20374)
-- Name: settlement_order_details settlement_order_details_settlement_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_settlement_order_id_fkey FOREIGN KEY (settlement_order_id) REFERENCES public.settlement_orders(id);


--
-- TOC entry 3829 (class 2606 OID 20379)
-- Name: settlement_orders settlement_orders_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 3830 (class 2606 OID 20384)
-- Name: settlement_orders settlement_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3831 (class 2606 OID 20389)
-- Name: settlement_orders settlement_orders_dealer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_dealer_id_fkey FOREIGN KEY (dealer_id) REFERENCES public.companies(id);


--
-- TOC entry 3832 (class 2606 OID 20394)
-- Name: settlement_orders settlement_orders_distributor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_distributor_id_fkey FOREIGN KEY (distributor_id) REFERENCES public.companies(id);


--
-- TOC entry 3833 (class 2606 OID 20399)
-- Name: settlement_orders settlement_orders_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 3834 (class 2606 OID 20404)
-- Name: settlement_orders settlement_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 3835 (class 2606 OID 20409)
-- Name: settlement_orders settlement_orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 3836 (class 2606 OID 20414)
-- Name: settlements settlements_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- TOC entry 3837 (class 2606 OID 20419)
-- Name: settlements settlements_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 3838 (class 2606 OID 20424)
-- Name: settlements settlements_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 3839 (class 2606 OID 20429)
-- Name: solution_manager_email_settings solution_manager_email_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT solution_manager_email_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3840 (class 2606 OID 20434)
-- Name: system_metrics system_metrics_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 3841 (class 2606 OID 20439)
-- Name: upgrade_logs upgrade_logs_operator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_operator_id_fkey FOREIGN KEY (operator_id) REFERENCES public.users(id);


--
-- TOC entry 3842 (class 2606 OID 20444)
-- Name: upgrade_logs upgrade_logs_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 3843 (class 2606 OID 20449)
-- Name: user_event_subscriptions user_event_subscriptions_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.event_registry(id);


--
-- TOC entry 3844 (class 2606 OID 20454)
-- Name: user_event_subscriptions user_event_subscriptions_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id);


--
-- TOC entry 3845 (class 2606 OID 20459)
-- Name: user_event_subscriptions user_event_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


-- Completed on 2025-06-22 18:52:25 +08

--
-- PostgreSQL database dump complete
--

