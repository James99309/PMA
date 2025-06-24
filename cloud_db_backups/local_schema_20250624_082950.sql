--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Homebrew)
-- Dumped by pg_dump version 16.9 (Homebrew)

-- Started on 2025-06-24 08:29:50 +08

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

ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_target_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_event_id_fkey;
ALTER TABLE IF EXISTS ONLY public.upgrade_logs DROP CONSTRAINT IF EXISTS upgrade_logs_version_id_fkey;
ALTER TABLE IF EXISTS ONLY public.upgrade_logs DROP CONSTRAINT IF EXISTS upgrade_logs_operator_id_fkey;
ALTER TABLE IF EXISTS ONLY public.system_metrics DROP CONSTRAINT IF EXISTS system_metrics_version_id_fkey;
ALTER TABLE IF EXISTS ONLY public.solution_manager_email_settings DROP CONSTRAINT IF EXISTS solution_manager_email_settings_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlements DROP CONSTRAINT IF EXISTS settlements_created_by_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlements DROP CONSTRAINT IF EXISTS settlements_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlements DROP CONSTRAINT IF EXISTS settlements_approved_by_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_orders DROP CONSTRAINT IF EXISTS settlement_orders_quotation_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_orders DROP CONSTRAINT IF EXISTS settlement_orders_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_orders DROP CONSTRAINT IF EXISTS settlement_orders_pricing_order_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_orders DROP CONSTRAINT IF EXISTS settlement_orders_distributor_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_orders DROP CONSTRAINT IF EXISTS settlement_orders_dealer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_orders DROP CONSTRAINT IF EXISTS settlement_orders_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_orders DROP CONSTRAINT IF EXISTS settlement_orders_approved_by_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_order_details DROP CONSTRAINT IF EXISTS settlement_order_details_settlement_order_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_order_details DROP CONSTRAINT IF EXISTS settlement_order_details_pricing_order_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_order_details DROP CONSTRAINT IF EXISTS settlement_order_details_pricing_detail_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_details DROP CONSTRAINT IF EXISTS settlement_details_settlement_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_details DROP CONSTRAINT IF EXISTS settlement_details_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_details DROP CONSTRAINT IF EXISTS settlement_details_inventory_id_fkey;
ALTER TABLE IF EXISTS ONLY public.quotations DROP CONSTRAINT IF EXISTS quotations_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.quotations DROP CONSTRAINT IF EXISTS quotations_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.quotations DROP CONSTRAINT IF EXISTS quotations_locked_by_fkey;
ALTER TABLE IF EXISTS ONLY public.quotations DROP CONSTRAINT IF EXISTS quotations_contact_id_fkey;
ALTER TABLE IF EXISTS ONLY public.quotations DROP CONSTRAINT IF EXISTS quotations_confirmed_by_fkey;
ALTER TABLE IF EXISTS ONLY public.quotation_details DROP CONSTRAINT IF EXISTS quotation_details_quotation_id_fkey;
ALTER TABLE IF EXISTS ONLY public.purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_created_by_id_fkey;
ALTER TABLE IF EXISTS ONLY public.purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_approved_by_id_fkey;
ALTER TABLE IF EXISTS ONLY public.purchase_order_details DROP CONSTRAINT IF EXISTS purchase_order_details_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.purchase_order_details DROP CONSTRAINT IF EXISTS purchase_order_details_order_id_fkey;
ALTER TABLE IF EXISTS ONLY public.projects DROP CONSTRAINT IF EXISTS projects_vendor_sales_manager_id_fkey;
ALTER TABLE IF EXISTS ONLY public.projects DROP CONSTRAINT IF EXISTS projects_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.projects DROP CONSTRAINT IF EXISTS projects_locked_by_fkey;
ALTER TABLE IF EXISTS ONLY public.project_total_scores DROP CONSTRAINT IF EXISTS project_total_scores_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_stage_history DROP CONSTRAINT IF EXISTS project_stage_history_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_scoring_records DROP CONSTRAINT IF EXISTS project_scoring_records_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_scoring_records DROP CONSTRAINT IF EXISTS project_scoring_records_awarded_by_fkey;
ALTER TABLE IF EXISTS ONLY public.project_rating_records DROP CONSTRAINT IF EXISTS project_rating_records_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_rating_records DROP CONSTRAINT IF EXISTS project_rating_records_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_members DROP CONSTRAINT IF EXISTS project_members_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_members DROP CONSTRAINT IF EXISTS project_members_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.products DROP CONSTRAINT IF EXISTS products_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.product_subcategories DROP CONSTRAINT IF EXISTS product_subcategories_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.product_codes DROP CONSTRAINT IF EXISTS product_codes_subcategory_id_fkey;
ALTER TABLE IF EXISTS ONLY public.product_codes DROP CONSTRAINT IF EXISTS product_codes_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.product_codes DROP CONSTRAINT IF EXISTS product_codes_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.product_codes DROP CONSTRAINT IF EXISTS product_codes_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.product_code_fields DROP CONSTRAINT IF EXISTS product_code_fields_subcategory_id_fkey;
ALTER TABLE IF EXISTS ONLY public.product_code_field_values DROP CONSTRAINT IF EXISTS product_code_field_values_product_code_id_fkey;
ALTER TABLE IF EXISTS ONLY public.product_code_field_values DROP CONSTRAINT IF EXISTS product_code_field_values_option_id_fkey;
ALTER TABLE IF EXISTS ONLY public.product_code_field_values DROP CONSTRAINT IF EXISTS product_code_field_values_field_id_fkey;
ALTER TABLE IF EXISTS ONLY public.product_code_field_options DROP CONSTRAINT IF EXISTS product_code_field_options_field_id_fkey;
ALTER TABLE IF EXISTS ONLY public.pricing_orders DROP CONSTRAINT IF EXISTS pricing_orders_quotation_id_fkey;
ALTER TABLE IF EXISTS ONLY public.pricing_orders DROP CONSTRAINT IF EXISTS pricing_orders_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.pricing_orders DROP CONSTRAINT IF EXISTS pricing_orders_distributor_id_fkey;
ALTER TABLE IF EXISTS ONLY public.pricing_orders DROP CONSTRAINT IF EXISTS pricing_orders_dealer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.pricing_orders DROP CONSTRAINT IF EXISTS pricing_orders_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.pricing_orders DROP CONSTRAINT IF EXISTS pricing_orders_approved_by_fkey;
ALTER TABLE IF EXISTS ONLY public.pricing_order_details DROP CONSTRAINT IF EXISTS pricing_order_details_pricing_order_id_fkey;
ALTER TABLE IF EXISTS ONLY public.pricing_order_approval_records DROP CONSTRAINT IF EXISTS pricing_order_approval_records_pricing_order_id_fkey;
ALTER TABLE IF EXISTS ONLY public.pricing_order_approval_records DROP CONSTRAINT IF EXISTS pricing_order_approval_records_approver_id_fkey;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS permissions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_inventory_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_created_by_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_created_by_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_order_details DROP CONSTRAINT IF EXISTS fk_settlement_order_details_settlement_company;
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS fk_approval_record_step_id;
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS fk_approval_record_approver_id;
ALTER TABLE IF EXISTS ONLY public.feature_changes DROP CONSTRAINT IF EXISTS feature_changes_version_id_fkey;
ALTER TABLE IF EXISTS ONLY public.feature_changes DROP CONSTRAINT IF EXISTS feature_changes_developer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_subcategory_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_region_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_product_specs DROP CONSTRAINT IF EXISTS dev_product_specs_dev_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.contacts DROP CONSTRAINT IF EXISTS contacts_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.contacts DROP CONSTRAINT IF EXISTS contacts_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.companies DROP CONSTRAINT IF EXISTS companies_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.change_logs DROP CONSTRAINT IF EXISTS change_logs_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_step DROP CONSTRAINT IF EXISTS approval_step_process_id_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_step DROP CONSTRAINT IF EXISTS approval_step_approver_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS approval_record_instance_id_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_process_template DROP CONSTRAINT IF EXISTS approval_process_template_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_instance DROP CONSTRAINT IF EXISTS approval_instance_process_id_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_instance DROP CONSTRAINT IF EXISTS approval_instance_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.affiliations DROP CONSTRAINT IF EXISTS affiliations_viewer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.affiliations DROP CONSTRAINT IF EXISTS affiliations_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.actions DROP CONSTRAINT IF EXISTS actions_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.actions DROP CONSTRAINT IF EXISTS actions_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.actions DROP CONSTRAINT IF EXISTS actions_contact_id_fkey;
ALTER TABLE IF EXISTS ONLY public.actions DROP CONSTRAINT IF EXISTS actions_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.action_reply DROP CONSTRAINT IF EXISTS action_reply_parent_reply_id_fkey;
ALTER TABLE IF EXISTS ONLY public.action_reply DROP CONSTRAINT IF EXISTS action_reply_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.action_reply DROP CONSTRAINT IF EXISTS action_reply_action_id_fkey;
DROP INDEX IF EXISTS public.ix_system_settings_key;
DROP INDEX IF EXISTS public.ix_projects_project_name;
DROP INDEX IF EXISTS public.ix_projects_authorization_code;
DROP INDEX IF EXISTS public.ix_project_stage_history_project_id;
ALTER TABLE IF EXISTS ONLY public.version_records DROP CONSTRAINT IF EXISTS version_records_version_number_key;
ALTER TABLE IF EXISTS ONLY public.version_records DROP CONSTRAINT IF EXISTS version_records_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_wechat_openid_key;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_username_key;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_email_key;
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_pkey;
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS uq_user_target_event;
ALTER TABLE IF EXISTS ONLY public.product_subcategories DROP CONSTRAINT IF EXISTS uq_subcategory_code_letter;
ALTER TABLE IF EXISTS ONLY public.solution_manager_email_settings DROP CONSTRAINT IF EXISTS uq_solution_manager_email_user;
ALTER TABLE IF EXISTS ONLY public.project_scoring_records DROP CONSTRAINT IF EXISTS uq_scoring_record;
ALTER TABLE IF EXISTS ONLY public.project_scoring_config DROP CONSTRAINT IF EXISTS uq_scoring_config;
ALTER TABLE IF EXISTS ONLY public.project_rating_records DROP CONSTRAINT IF EXISTS uq_project_user_rating;
ALTER TABLE IF EXISTS ONLY public.upgrade_logs DROP CONSTRAINT IF EXISTS upgrade_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS unique_company_product_inventory;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS uix_user_module;
ALTER TABLE IF EXISTS ONLY public.dictionaries DROP CONSTRAINT IF EXISTS uix_type_key;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS uix_role_module;
ALTER TABLE IF EXISTS ONLY public.affiliations DROP CONSTRAINT IF EXISTS uix_owner_viewer;
ALTER TABLE IF EXISTS ONLY public.system_settings DROP CONSTRAINT IF EXISTS system_settings_pkey;
ALTER TABLE IF EXISTS ONLY public.system_metrics DROP CONSTRAINT IF EXISTS system_metrics_pkey;
ALTER TABLE IF EXISTS ONLY public.solution_manager_email_settings DROP CONSTRAINT IF EXISTS solution_manager_email_settings_pkey;
ALTER TABLE IF EXISTS ONLY public.settlements DROP CONSTRAINT IF EXISTS settlements_settlement_number_key;
ALTER TABLE IF EXISTS ONLY public.settlements DROP CONSTRAINT IF EXISTS settlements_pkey;
ALTER TABLE IF EXISTS ONLY public.settlement_orders DROP CONSTRAINT IF EXISTS settlement_orders_pkey;
ALTER TABLE IF EXISTS ONLY public.settlement_orders DROP CONSTRAINT IF EXISTS settlement_orders_order_number_key;
ALTER TABLE IF EXISTS ONLY public.settlement_order_details DROP CONSTRAINT IF EXISTS settlement_order_details_pkey;
ALTER TABLE IF EXISTS ONLY public.settlement_details DROP CONSTRAINT IF EXISTS settlement_details_pkey;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS role_permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.quotations DROP CONSTRAINT IF EXISTS quotations_quotation_number_key;
ALTER TABLE IF EXISTS ONLY public.quotations DROP CONSTRAINT IF EXISTS quotations_pkey;
ALTER TABLE IF EXISTS ONLY public.quotation_details DROP CONSTRAINT IF EXISTS quotation_details_pkey;
ALTER TABLE IF EXISTS ONLY public.purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_pkey;
ALTER TABLE IF EXISTS ONLY public.purchase_orders DROP CONSTRAINT IF EXISTS purchase_orders_order_number_key;
ALTER TABLE IF EXISTS ONLY public.purchase_order_details DROP CONSTRAINT IF EXISTS purchase_order_details_pkey;
ALTER TABLE IF EXISTS ONLY public.projects DROP CONSTRAINT IF EXISTS projects_pkey;
ALTER TABLE IF EXISTS ONLY public.project_total_scores DROP CONSTRAINT IF EXISTS project_total_scores_project_id_key;
ALTER TABLE IF EXISTS ONLY public.project_total_scores DROP CONSTRAINT IF EXISTS project_total_scores_pkey;
ALTER TABLE IF EXISTS ONLY public.project_stage_history DROP CONSTRAINT IF EXISTS project_stage_history_pkey;
ALTER TABLE IF EXISTS ONLY public.project_scoring_records DROP CONSTRAINT IF EXISTS project_scoring_records_pkey;
ALTER TABLE IF EXISTS ONLY public.project_scoring_config DROP CONSTRAINT IF EXISTS project_scoring_config_pkey;
ALTER TABLE IF EXISTS ONLY public.project_rating_records DROP CONSTRAINT IF EXISTS project_rating_records_pkey;
ALTER TABLE IF EXISTS ONLY public.project_members DROP CONSTRAINT IF EXISTS project_members_pkey;
ALTER TABLE IF EXISTS ONLY public.products DROP CONSTRAINT IF EXISTS products_product_mn_key;
ALTER TABLE IF EXISTS ONLY public.products DROP CONSTRAINT IF EXISTS products_pkey;
ALTER TABLE IF EXISTS ONLY public.product_subcategories DROP CONSTRAINT IF EXISTS product_subcategories_pkey;
ALTER TABLE IF EXISTS ONLY public.product_regions DROP CONSTRAINT IF EXISTS product_regions_pkey;
ALTER TABLE IF EXISTS ONLY public.product_codes DROP CONSTRAINT IF EXISTS product_codes_pkey;
ALTER TABLE IF EXISTS ONLY public.product_codes DROP CONSTRAINT IF EXISTS product_codes_full_code_key;
ALTER TABLE IF EXISTS ONLY public.product_code_fields DROP CONSTRAINT IF EXISTS product_code_fields_pkey;
ALTER TABLE IF EXISTS ONLY public.product_code_field_values DROP CONSTRAINT IF EXISTS product_code_field_values_pkey;
ALTER TABLE IF EXISTS ONLY public.product_code_field_options DROP CONSTRAINT IF EXISTS product_code_field_options_pkey;
ALTER TABLE IF EXISTS ONLY public.product_categories DROP CONSTRAINT IF EXISTS product_categories_pkey;
ALTER TABLE IF EXISTS ONLY public.product_categories DROP CONSTRAINT IF EXISTS product_categories_code_letter_key;
ALTER TABLE IF EXISTS ONLY public.pricing_orders DROP CONSTRAINT IF EXISTS pricing_orders_pkey;
ALTER TABLE IF EXISTS ONLY public.pricing_orders DROP CONSTRAINT IF EXISTS pricing_orders_order_number_key;
ALTER TABLE IF EXISTS ONLY public.pricing_order_details DROP CONSTRAINT IF EXISTS pricing_order_details_pkey;
ALTER TABLE IF EXISTS ONLY public.pricing_order_approval_records DROP CONSTRAINT IF EXISTS pricing_order_approval_records_pkey;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_pkey;
ALTER TABLE IF EXISTS ONLY public.feature_changes DROP CONSTRAINT IF EXISTS feature_changes_pkey;
ALTER TABLE IF EXISTS ONLY public.event_registry DROP CONSTRAINT IF EXISTS event_registry_pkey;
ALTER TABLE IF EXISTS ONLY public.event_registry DROP CONSTRAINT IF EXISTS event_registry_event_key_key;
ALTER TABLE IF EXISTS ONLY public.dictionaries DROP CONSTRAINT IF EXISTS dictionaries_pkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_pkey;
ALTER TABLE IF EXISTS ONLY public.dev_product_specs DROP CONSTRAINT IF EXISTS dev_product_specs_pkey;
ALTER TABLE IF EXISTS ONLY public.contacts DROP CONSTRAINT IF EXISTS contacts_pkey;
ALTER TABLE IF EXISTS ONLY public.companies DROP CONSTRAINT IF EXISTS companies_pkey;
ALTER TABLE IF EXISTS ONLY public.companies DROP CONSTRAINT IF EXISTS companies_company_code_key;
ALTER TABLE IF EXISTS ONLY public.change_logs DROP CONSTRAINT IF EXISTS change_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.approval_step DROP CONSTRAINT IF EXISTS approval_step_pkey;
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS approval_record_temp_pkey;
ALTER TABLE IF EXISTS ONLY public.approval_process_template DROP CONSTRAINT IF EXISTS approval_process_template_pkey;
ALTER TABLE IF EXISTS ONLY public.approval_instance DROP CONSTRAINT IF EXISTS approval_instance_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS ONLY public.affiliations DROP CONSTRAINT IF EXISTS affiliations_pkey;
ALTER TABLE IF EXISTS ONLY public.actions DROP CONSTRAINT IF EXISTS actions_pkey;
ALTER TABLE IF EXISTS ONLY public.action_reply DROP CONSTRAINT IF EXISTS action_reply_pkey;
ALTER TABLE IF EXISTS public.version_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.user_event_subscriptions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.upgrade_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.system_settings ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.system_metrics ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.solution_manager_email_settings ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.settlements ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.settlement_orders ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.settlement_order_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.settlement_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.role_permissions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.quotations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.quotation_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.purchase_orders ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.purchase_order_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.projects ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.project_total_scores ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.project_stage_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.project_scoring_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.project_scoring_config ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.project_rating_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.project_members ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.products ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.product_subcategories ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.product_regions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.product_codes ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.product_code_fields ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.product_code_field_values ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.product_code_field_options ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.product_categories ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.pricing_orders ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.pricing_order_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.pricing_order_approval_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.permissions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.inventory_transactions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.inventory ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.feature_changes ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.event_registry ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dictionaries ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dev_products ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dev_product_specs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.contacts ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.companies ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.change_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_step ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_process_template ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_instance ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.affiliations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.actions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.action_reply ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.version_records_id_seq;
DROP TABLE IF EXISTS public.version_records;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.user_event_subscriptions_id_seq;
DROP TABLE IF EXISTS public.user_event_subscriptions;
DROP SEQUENCE IF EXISTS public.upgrade_logs_id_seq;
DROP TABLE IF EXISTS public.upgrade_logs;
DROP SEQUENCE IF EXISTS public.system_settings_id_seq;
DROP TABLE IF EXISTS public.system_settings;
DROP SEQUENCE IF EXISTS public.system_metrics_id_seq;
DROP TABLE IF EXISTS public.system_metrics;
DROP SEQUENCE IF EXISTS public.solution_manager_email_settings_id_seq;
DROP TABLE IF EXISTS public.solution_manager_email_settings;
DROP SEQUENCE IF EXISTS public.settlements_id_seq;
DROP TABLE IF EXISTS public.settlements;
DROP SEQUENCE IF EXISTS public.settlement_orders_id_seq;
DROP TABLE IF EXISTS public.settlement_orders;
DROP SEQUENCE IF EXISTS public.settlement_order_details_id_seq;
DROP TABLE IF EXISTS public.settlement_order_details;
DROP SEQUENCE IF EXISTS public.settlement_details_id_seq;
DROP TABLE IF EXISTS public.settlement_details;
DROP SEQUENCE IF EXISTS public.role_permissions_id_seq;
DROP TABLE IF EXISTS public.role_permissions;
DROP SEQUENCE IF EXISTS public.quotations_id_seq;
DROP TABLE IF EXISTS public.quotations;
DROP SEQUENCE IF EXISTS public.quotation_details_id_seq;
DROP TABLE IF EXISTS public.quotation_details;
DROP SEQUENCE IF EXISTS public.purchase_orders_id_seq;
DROP TABLE IF EXISTS public.purchase_orders;
DROP SEQUENCE IF EXISTS public.purchase_order_details_id_seq;
DROP TABLE IF EXISTS public.purchase_order_details;
DROP SEQUENCE IF EXISTS public.projects_id_seq;
DROP TABLE IF EXISTS public.projects;
DROP SEQUENCE IF EXISTS public.project_total_scores_id_seq;
DROP TABLE IF EXISTS public.project_total_scores;
DROP SEQUENCE IF EXISTS public.project_stage_history_id_seq;
DROP TABLE IF EXISTS public.project_stage_history;
DROP SEQUENCE IF EXISTS public.project_scoring_records_id_seq;
DROP TABLE IF EXISTS public.project_scoring_records;
DROP SEQUENCE IF EXISTS public.project_scoring_config_id_seq;
DROP TABLE IF EXISTS public.project_scoring_config;
DROP SEQUENCE IF EXISTS public.project_rating_records_id_seq;
DROP TABLE IF EXISTS public.project_rating_records;
DROP SEQUENCE IF EXISTS public.project_members_id_seq;
DROP TABLE IF EXISTS public.project_members;
DROP SEQUENCE IF EXISTS public.products_id_seq;
DROP TABLE IF EXISTS public.products;
DROP SEQUENCE IF EXISTS public.product_subcategories_id_seq;
DROP TABLE IF EXISTS public.product_subcategories;
DROP SEQUENCE IF EXISTS public.product_regions_id_seq;
DROP TABLE IF EXISTS public.product_regions;
DROP SEQUENCE IF EXISTS public.product_codes_id_seq;
DROP TABLE IF EXISTS public.product_codes;
DROP SEQUENCE IF EXISTS public.product_code_fields_id_seq;
DROP TABLE IF EXISTS public.product_code_fields;
DROP SEQUENCE IF EXISTS public.product_code_field_values_id_seq;
DROP TABLE IF EXISTS public.product_code_field_values;
DROP SEQUENCE IF EXISTS public.product_code_field_options_id_seq;
DROP TABLE IF EXISTS public.product_code_field_options;
DROP SEQUENCE IF EXISTS public.product_categories_id_seq;
DROP TABLE IF EXISTS public.product_categories;
DROP SEQUENCE IF EXISTS public.pricing_orders_id_seq;
DROP TABLE IF EXISTS public.pricing_orders;
DROP SEQUENCE IF EXISTS public.pricing_order_details_id_seq;
DROP TABLE IF EXISTS public.pricing_order_details;
DROP SEQUENCE IF EXISTS public.pricing_order_approval_records_id_seq;
DROP TABLE IF EXISTS public.pricing_order_approval_records;
DROP SEQUENCE IF EXISTS public.permissions_id_seq;
DROP TABLE IF EXISTS public.permissions;
DROP SEQUENCE IF EXISTS public.inventory_transactions_id_seq;
DROP TABLE IF EXISTS public.inventory_transactions;
DROP SEQUENCE IF EXISTS public.inventory_id_seq;
DROP TABLE IF EXISTS public.inventory;
DROP SEQUENCE IF EXISTS public.feature_changes_id_seq;
DROP TABLE IF EXISTS public.feature_changes;
DROP SEQUENCE IF EXISTS public.event_registry_id_seq;
DROP TABLE IF EXISTS public.event_registry;
DROP SEQUENCE IF EXISTS public.dictionaries_id_seq;
DROP TABLE IF EXISTS public.dictionaries;
DROP SEQUENCE IF EXISTS public.dev_products_id_seq;
DROP TABLE IF EXISTS public.dev_products;
DROP SEQUENCE IF EXISTS public.dev_product_specs_id_seq;
DROP TABLE IF EXISTS public.dev_product_specs;
DROP SEQUENCE IF EXISTS public.contacts_id_seq;
DROP TABLE IF EXISTS public.contacts;
DROP SEQUENCE IF EXISTS public.companies_id_seq;
DROP TABLE IF EXISTS public.companies;
DROP SEQUENCE IF EXISTS public.change_logs_id_seq;
DROP TABLE IF EXISTS public.change_logs;
DROP SEQUENCE IF EXISTS public.approval_step_id_seq;
DROP TABLE IF EXISTS public.approval_step;
DROP TABLE IF EXISTS public.approval_record;
DROP SEQUENCE IF EXISTS public.approval_record_id_seq;
DROP SEQUENCE IF EXISTS public.approval_process_template_id_seq;
DROP TABLE IF EXISTS public.approval_process_template;
DROP SEQUENCE IF EXISTS public.approval_instance_id_seq;
DROP TABLE IF EXISTS public.approval_instance;
DROP TABLE IF EXISTS public.alembic_version;
DROP SEQUENCE IF EXISTS public.affiliations_id_seq;
DROP TABLE IF EXISTS public.affiliations;
DROP SEQUENCE IF EXISTS public.actions_id_seq;
DROP TABLE IF EXISTS public.actions;
DROP SEQUENCE IF EXISTS public.action_reply_id_seq;
DROP TABLE IF EXISTS public.action_reply;
DROP TYPE IF EXISTS public.settlementorderstatus;
DROP TYPE IF EXISTS public.pricingorderstatus;
DROP TYPE IF EXISTS public.pricingorderapprovalflowtype;
DROP TYPE IF EXISTS public.approvalstatus;
DROP TYPE IF EXISTS public.approvalinstancestatus;
DROP TYPE IF EXISTS public.approvalaction;
DROP TYPE IF EXISTS public.approval_status;
DROP TYPE IF EXISTS public.approval_action;
-- *not* dropping schema, since initdb creates it
--
-- TOC entry 4 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- TOC entry 1018 (class 1247 OID 20058)
-- Name: approval_action; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_action AS ENUM (
    'approve',
    'reject'
);


--
-- TOC entry 1015 (class 1247 OID 20050)
-- Name: approval_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);


--
-- TOC entry 1024 (class 1247 OID 20086)
-- Name: approvalaction; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalaction AS ENUM (
    'approve',
    'reject'
);


--
-- TOC entry 1021 (class 1247 OID 20079)
-- Name: approvalinstancestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalinstancestatus AS ENUM (
    'pending',
    'approved',
    'rejected'
);


--
-- TOC entry 1027 (class 1247 OID 20096)
-- Name: approvalstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalstatus AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- TOC entry 1081 (class 1247 OID 20840)
-- Name: pricingorderapprovalflowtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricingorderapprovalflowtype AS ENUM (
    'CHANNEL_FOLLOW',
    'SALES_KEY',
    'SALES_OPPORTUNITY'
);


--
-- TOC entry 1084 (class 1247 OID 20848)
-- Name: pricingorderstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricingorderstatus AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- TOC entry 1087 (class 1247 OID 20858)
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
-- TOC entry 258 (class 1259 OID 19855)
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
-- TOC entry 257 (class 1259 OID 19854)
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
-- TOC entry 4430 (class 0 OID 0)
-- Dependencies: 257
-- Name: action_reply_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.action_reply_id_seq OWNED BY public.action_reply.id;


--
-- TOC entry 211 (class 1259 OID 19389)
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
-- TOC entry 212 (class 1259 OID 19394)
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
-- TOC entry 4431 (class 0 OID 0)
-- Dependencies: 212
-- Name: actions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.actions_id_seq OWNED BY public.actions.id;


--
-- TOC entry 213 (class 1259 OID 19395)
-- Name: affiliations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.affiliations (
    id integer NOT NULL,
    owner_id integer NOT NULL,
    viewer_id integer NOT NULL,
    created_at double precision
);


--
-- TOC entry 214 (class 1259 OID 19398)
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
-- TOC entry 4432 (class 0 OID 0)
-- Dependencies: 214
-- Name: affiliations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.affiliations_id_seq OWNED BY public.affiliations.id;


--
-- TOC entry 273 (class 1259 OID 20306)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- TOC entry 266 (class 1259 OID 20000)
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
-- TOC entry 4433 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN approval_instance.object_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_id IS '对应单据ID';


--
-- TOC entry 4434 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN approval_instance.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_type IS '单据类型（如 project）';


--
-- TOC entry 4435 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN approval_instance.current_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.current_step IS '当前步骤序号';


--
-- TOC entry 4436 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN approval_instance.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.status IS '状态';


--
-- TOC entry 4437 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN approval_instance.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.started_at IS '流程发起时间';


--
-- TOC entry 4438 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN approval_instance.ended_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.ended_at IS '审批完成时间';


--
-- TOC entry 4439 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN approval_instance.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.process_id IS '流程模板ID';


--
-- TOC entry 4440 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN approval_instance.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.created_by IS '发起人ID';


--
-- TOC entry 4441 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN approval_instance.template_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_snapshot IS '创建时的模板快照';


--
-- TOC entry 4442 (class 0 OID 0)
-- Dependencies: 266
-- Name: COLUMN approval_instance.template_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_version IS '模板版本号';


--
-- TOC entry 265 (class 1259 OID 19999)
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
-- TOC entry 4443 (class 0 OID 0)
-- Dependencies: 265
-- Name: approval_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_instance_id_seq OWNED BY public.approval_instance.id;


--
-- TOC entry 264 (class 1259 OID 19988)
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
-- TOC entry 4444 (class 0 OID 0)
-- Dependencies: 264
-- Name: COLUMN approval_process_template.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.name IS '流程名称';


--
-- TOC entry 4445 (class 0 OID 0)
-- Dependencies: 264
-- Name: COLUMN approval_process_template.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.object_type IS '适用对象（如 quotation）';


--
-- TOC entry 4446 (class 0 OID 0)
-- Dependencies: 264
-- Name: COLUMN approval_process_template.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.is_active IS '是否启用';


--
-- TOC entry 4447 (class 0 OID 0)
-- Dependencies: 264
-- Name: COLUMN approval_process_template.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_by IS '创建人账号ID';


--
-- TOC entry 4448 (class 0 OID 0)
-- Dependencies: 264
-- Name: COLUMN approval_process_template.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_at IS '创建时间';


--
-- TOC entry 4449 (class 0 OID 0)
-- Dependencies: 264
-- Name: COLUMN approval_process_template.required_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.required_fields IS '发起审批时必填字段列表';


--
-- TOC entry 4450 (class 0 OID 0)
-- Dependencies: 264
-- Name: COLUMN approval_process_template.lock_object_on_start; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_object_on_start IS '发起审批后是否锁定对象编辑';


--
-- TOC entry 4451 (class 0 OID 0)
-- Dependencies: 264
-- Name: COLUMN approval_process_template.lock_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_reason IS '锁定原因说明';


--
-- TOC entry 263 (class 1259 OID 19987)
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
-- TOC entry 4452 (class 0 OID 0)
-- Dependencies: 263
-- Name: approval_process_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_process_template_id_seq OWNED BY public.approval_process_template.id;


--
-- TOC entry 270 (class 1259 OID 20202)
-- Name: approval_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.approval_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 269 (class 1259 OID 20180)
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
-- TOC entry 4453 (class 0 OID 0)
-- Dependencies: 269
-- Name: COLUMN approval_record.instance_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.instance_id IS '审批流程实例';


--
-- TOC entry 4454 (class 0 OID 0)
-- Dependencies: 269
-- Name: COLUMN approval_record.step_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.step_id IS '流程步骤ID';


--
-- TOC entry 4455 (class 0 OID 0)
-- Dependencies: 269
-- Name: COLUMN approval_record.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.approver_id IS '审批人ID';


--
-- TOC entry 4456 (class 0 OID 0)
-- Dependencies: 269
-- Name: COLUMN approval_record.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.action IS '同意/拒绝';


--
-- TOC entry 4457 (class 0 OID 0)
-- Dependencies: 269
-- Name: COLUMN approval_record.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.comment IS '审批意见';


--
-- TOC entry 4458 (class 0 OID 0)
-- Dependencies: 269
-- Name: COLUMN approval_record."timestamp"; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record."timestamp" IS '审批时间';


--
-- TOC entry 268 (class 1259 OID 20007)
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
    approver_type character varying(20) DEFAULT 'user'::character varying,
    description text
);


--
-- TOC entry 4459 (class 0 OID 0)
-- Dependencies: 268
-- Name: COLUMN approval_step.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.process_id IS '所属流程模板';


--
-- TOC entry 4460 (class 0 OID 0)
-- Dependencies: 268
-- Name: COLUMN approval_step.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_order IS '流程顺序';


--
-- TOC entry 4461 (class 0 OID 0)
-- Dependencies: 268
-- Name: COLUMN approval_step.approver_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.approver_user_id IS '审批人账号ID';


--
-- TOC entry 4462 (class 0 OID 0)
-- Dependencies: 268
-- Name: COLUMN approval_step.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_name IS '步骤说明（如"财务审批"）';


--
-- TOC entry 4463 (class 0 OID 0)
-- Dependencies: 268
-- Name: COLUMN approval_step.send_email; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.send_email IS '是否发送邮件通知';


--
-- TOC entry 4464 (class 0 OID 0)
-- Dependencies: 268
-- Name: COLUMN approval_step.action_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_type IS '步骤动作类型，如 authorization, quotation_approval';


--
-- TOC entry 4465 (class 0 OID 0)
-- Dependencies: 268
-- Name: COLUMN approval_step.action_params; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_params IS '动作参数，JSON格式';


--
-- TOC entry 4466 (class 0 OID 0)
-- Dependencies: 268
-- Name: COLUMN approval_step.editable_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.editable_fields IS '在此步骤可编辑的字段列表';


--
-- TOC entry 4467 (class 0 OID 0)
-- Dependencies: 268
-- Name: COLUMN approval_step.cc_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_users IS '邮件抄送用户ID列表';


--
-- TOC entry 4468 (class 0 OID 0)
-- Dependencies: 268
-- Name: COLUMN approval_step.cc_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_enabled IS '是否启用邮件抄送';


--
-- TOC entry 267 (class 1259 OID 20006)
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
-- TOC entry 4469 (class 0 OID 0)
-- Dependencies: 267
-- Name: approval_step_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_step_id_seq OWNED BY public.approval_step.id;


--
-- TOC entry 283 (class 1259 OID 20509)
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
-- TOC entry 282 (class 1259 OID 20508)
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
-- TOC entry 4470 (class 0 OID 0)
-- Dependencies: 282
-- Name: change_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.change_logs_id_seq OWNED BY public.change_logs.id;


--
-- TOC entry 215 (class 1259 OID 19402)
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
-- TOC entry 216 (class 1259 OID 19407)
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
-- TOC entry 4471 (class 0 OID 0)
-- Dependencies: 216
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- TOC entry 217 (class 1259 OID 19408)
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
-- TOC entry 218 (class 1259 OID 19413)
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
-- TOC entry 4472 (class 0 OID 0)
-- Dependencies: 218
-- Name: contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contacts_id_seq OWNED BY public.contacts.id;


--
-- TOC entry 219 (class 1259 OID 19418)
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
-- TOC entry 220 (class 1259 OID 19421)
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
-- TOC entry 4473 (class 0 OID 0)
-- Dependencies: 220
-- Name: dev_product_specs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_product_specs_id_seq OWNED BY public.dev_product_specs.id;


--
-- TOC entry 221 (class 1259 OID 19422)
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
    pdf_path character varying(255),
    currency character varying(3) DEFAULT 'CNY'::character varying NOT NULL
);


--
-- TOC entry 222 (class 1259 OID 19427)
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
-- TOC entry 4474 (class 0 OID 0)
-- Dependencies: 222
-- Name: dev_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_products_id_seq OWNED BY public.dev_products.id;


--
-- TOC entry 223 (class 1259 OID 19428)
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
    updated_at double precision,
    is_vendor boolean DEFAULT false
);


--
-- TOC entry 224 (class 1259 OID 19431)
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
-- TOC entry 4475 (class 0 OID 0)
-- Dependencies: 224
-- Name: dictionaries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dictionaries_id_seq OWNED BY public.dictionaries.id;


--
-- TOC entry 260 (class 1259 OID 19901)
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
-- TOC entry 4476 (class 0 OID 0)
-- Dependencies: 260
-- Name: COLUMN event_registry.event_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.event_key IS '事件唯一键';


--
-- TOC entry 4477 (class 0 OID 0)
-- Dependencies: 260
-- Name: COLUMN event_registry.label_zh; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.label_zh IS '中文名称';


--
-- TOC entry 4478 (class 0 OID 0)
-- Dependencies: 260
-- Name: COLUMN event_registry.label_en; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.label_en IS '英文名称';


--
-- TOC entry 4479 (class 0 OID 0)
-- Dependencies: 260
-- Name: COLUMN event_registry.default_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.default_enabled IS '是否默认开启';


--
-- TOC entry 4480 (class 0 OID 0)
-- Dependencies: 260
-- Name: COLUMN event_registry.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.enabled IS '是否在通知中心展示';


--
-- TOC entry 259 (class 1259 OID 19900)
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
-- TOC entry 4481 (class 0 OID 0)
-- Dependencies: 259
-- Name: event_registry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_registry_id_seq OWNED BY public.event_registry.id;


--
-- TOC entry 289 (class 1259 OID 20566)
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
-- TOC entry 4482 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.version_id IS '版本ID';


--
-- TOC entry 4483 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.change_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.change_type IS '变更类型：feature/fix/improvement/security';


--
-- TOC entry 4484 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.module_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.module_name IS '模块名称';


--
-- TOC entry 4485 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.title; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.title IS '变更标题';


--
-- TOC entry 4486 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.description IS '详细描述';


--
-- TOC entry 4487 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.priority IS '优先级：low/medium/high/critical';


--
-- TOC entry 4488 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.impact_level; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.impact_level IS '影响级别：minor/major/breaking';


--
-- TOC entry 4489 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.affected_files; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.affected_files IS '影响的文件列表（JSON格式）';


--
-- TOC entry 4490 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.git_commits; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.git_commits IS '相关Git提交（JSON格式）';


--
-- TOC entry 4491 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.test_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.test_status IS '测试状态：pending/passed/failed';


--
-- TOC entry 4492 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.test_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.test_notes IS '测试说明';


--
-- TOC entry 4493 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.developer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.developer_id IS '开发人员ID';


--
-- TOC entry 4494 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.developer_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.developer_name IS '开发人员姓名';


--
-- TOC entry 4495 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.created_at IS '创建时间';


--
-- TOC entry 4496 (class 0 OID 0)
-- Dependencies: 289
-- Name: COLUMN feature_changes.completed_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.completed_at IS '完成时间';


--
-- TOC entry 288 (class 1259 OID 20565)
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
-- TOC entry 4497 (class 0 OID 0)
-- Dependencies: 288
-- Name: feature_changes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.feature_changes_id_seq OWNED BY public.feature_changes.id;


--
-- TOC entry 305 (class 1259 OID 28878)
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
-- TOC entry 304 (class 1259 OID 28877)
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
-- TOC entry 4498 (class 0 OID 0)
-- Dependencies: 304
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- TOC entry 311 (class 1259 OID 28956)
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
-- TOC entry 310 (class 1259 OID 28955)
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
-- TOC entry 4499 (class 0 OID 0)
-- Dependencies: 310
-- Name: inventory_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_transactions_id_seq OWNED BY public.inventory_transactions.id;


--
-- TOC entry 225 (class 1259 OID 19432)
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
-- TOC entry 226 (class 1259 OID 19435)
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
-- TOC entry 4500 (class 0 OID 0)
-- Dependencies: 226
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- TOC entry 299 (class 1259 OID 20763)
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
-- TOC entry 4501 (class 0 OID 0)
-- Dependencies: 299
-- Name: COLUMN pricing_order_approval_records.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.pricing_order_id IS '批价单ID';


--
-- TOC entry 4502 (class 0 OID 0)
-- Dependencies: 299
-- Name: COLUMN pricing_order_approval_records.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_order IS '审批步骤顺序';


--
-- TOC entry 4503 (class 0 OID 0)
-- Dependencies: 299
-- Name: COLUMN pricing_order_approval_records.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_name IS '审批步骤名称';


--
-- TOC entry 4504 (class 0 OID 0)
-- Dependencies: 299
-- Name: COLUMN pricing_order_approval_records.approver_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_role IS '审批人角色';


--
-- TOC entry 4505 (class 0 OID 0)
-- Dependencies: 299
-- Name: COLUMN pricing_order_approval_records.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_id IS '审批人ID';


--
-- TOC entry 4506 (class 0 OID 0)
-- Dependencies: 299
-- Name: COLUMN pricing_order_approval_records.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.action IS '审批动作：approve/reject';


--
-- TOC entry 4507 (class 0 OID 0)
-- Dependencies: 299
-- Name: COLUMN pricing_order_approval_records.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.comment IS '审批意见';


--
-- TOC entry 4508 (class 0 OID 0)
-- Dependencies: 299
-- Name: COLUMN pricing_order_approval_records.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approved_at IS '审批时间';


--
-- TOC entry 4509 (class 0 OID 0)
-- Dependencies: 299
-- Name: COLUMN pricing_order_approval_records.is_fast_approval; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.is_fast_approval IS '是否快速通过';


--
-- TOC entry 4510 (class 0 OID 0)
-- Dependencies: 299
-- Name: COLUMN pricing_order_approval_records.fast_approval_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.fast_approval_reason IS '快速通过原因';


--
-- TOC entry 298 (class 1259 OID 20762)
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
-- TOC entry 4511 (class 0 OID 0)
-- Dependencies: 298
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_order_approval_records_id_seq OWNED BY public.pricing_order_approval_records.id;


--
-- TOC entry 297 (class 1259 OID 20744)
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
    source_quotation_detail_id integer,
    currency character varying(10) DEFAULT 'CNY'::character varying
);


--
-- TOC entry 4512 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.pricing_order_id IS '批价单ID';


--
-- TOC entry 4513 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_name IS '产品名称';


--
-- TOC entry 4514 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_model IS '产品型号';


--
-- TOC entry 4515 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_desc IS '产品描述';


--
-- TOC entry 4516 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.brand IS '品牌';


--
-- TOC entry 4517 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.unit IS '单位';


--
-- TOC entry 4518 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_mn IS '产品MN编码';


--
-- TOC entry 4519 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.market_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.market_price IS '市场价';


--
-- TOC entry 4520 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.unit_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.unit_price IS '单价';


--
-- TOC entry 4521 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.quantity IS '数量';


--
-- TOC entry 4522 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.discount_rate IS '折扣率';


--
-- TOC entry 4523 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.total_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.total_price IS '小计金额';


--
-- TOC entry 4524 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.source_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.source_type IS '数据来源：quotation/manual';


--
-- TOC entry 4525 (class 0 OID 0)
-- Dependencies: 297
-- Name: COLUMN pricing_order_details.source_quotation_detail_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.source_quotation_detail_id IS '来源报价单明细ID';


--
-- TOC entry 296 (class 1259 OID 20743)
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
-- TOC entry 4526 (class 0 OID 0)
-- Dependencies: 296
-- Name: pricing_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_order_details_id_seq OWNED BY public.pricing_order_details.id;


--
-- TOC entry 295 (class 1259 OID 20706)
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
    is_factory_pickup boolean DEFAULT false,
    currency character varying(10) DEFAULT 'CNY'::character varying
);


--
-- TOC entry 4527 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.order_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.order_number IS '批价单号';


--
-- TOC entry 4528 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.project_id IS '项目ID';


--
-- TOC entry 4529 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.quotation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.quotation_id IS '报价单ID';


--
-- TOC entry 4530 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.distributor_id IS '分销商ID';


--
-- TOC entry 4531 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.dealer_id IS '经销商ID';


--
-- TOC entry 4532 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.pricing_total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_amount IS '批价单总金额';


--
-- TOC entry 4533 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.pricing_total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_discount_rate IS '批价单总折扣率';


--
-- TOC entry 4534 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.settlement_total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_amount IS '结算单总金额';


--
-- TOC entry 4535 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.settlement_total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_discount_rate IS '结算单总折扣率';


--
-- TOC entry 4536 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.approval_flow_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approval_flow_type IS '审批流程类型';


--
-- TOC entry 4537 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.status IS '批价单状态';


--
-- TOC entry 4538 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.current_approval_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.current_approval_step IS '当前审批步骤';


--
-- TOC entry 4539 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.approved_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approved_by IS '最终批准人';


--
-- TOC entry 4540 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approved_at IS '批准时间';


--
-- TOC entry 4541 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.created_by IS '创建人';


--
-- TOC entry 4542 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.created_at IS '创建时间';


--
-- TOC entry 4543 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.updated_at IS '更新时间';


--
-- TOC entry 4544 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.is_direct_contract; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.is_direct_contract IS '厂商直签';


--
-- TOC entry 4545 (class 0 OID 0)
-- Dependencies: 295
-- Name: COLUMN pricing_orders.is_factory_pickup; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.is_factory_pickup IS '厂家提货';


--
-- TOC entry 294 (class 1259 OID 20705)
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
-- TOC entry 4546 (class 0 OID 0)
-- Dependencies: 294
-- Name: pricing_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_orders_id_seq OWNED BY public.pricing_orders.id;


--
-- TOC entry 227 (class 1259 OID 19436)
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
-- TOC entry 228 (class 1259 OID 19441)
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
-- TOC entry 4547 (class 0 OID 0)
-- Dependencies: 228
-- Name: product_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_categories_id_seq OWNED BY public.product_categories.id;


--
-- TOC entry 229 (class 1259 OID 19442)
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
-- TOC entry 230 (class 1259 OID 19447)
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
-- TOC entry 4548 (class 0 OID 0)
-- Dependencies: 230
-- Name: product_code_field_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_field_options_id_seq OWNED BY public.product_code_field_options.id;


--
-- TOC entry 231 (class 1259 OID 19448)
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
-- TOC entry 232 (class 1259 OID 19451)
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
-- TOC entry 4549 (class 0 OID 0)
-- Dependencies: 232
-- Name: product_code_field_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_field_values_id_seq OWNED BY public.product_code_field_values.id;


--
-- TOC entry 233 (class 1259 OID 19452)
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
-- TOC entry 234 (class 1259 OID 19457)
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
-- TOC entry 4550 (class 0 OID 0)
-- Dependencies: 234
-- Name: product_code_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_fields_id_seq OWNED BY public.product_code_fields.id;


--
-- TOC entry 235 (class 1259 OID 19458)
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
-- TOC entry 236 (class 1259 OID 19461)
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
-- TOC entry 4551 (class 0 OID 0)
-- Dependencies: 236
-- Name: product_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_codes_id_seq OWNED BY public.product_codes.id;


--
-- TOC entry 237 (class 1259 OID 19462)
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
-- TOC entry 238 (class 1259 OID 19467)
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
-- TOC entry 4552 (class 0 OID 0)
-- Dependencies: 238
-- Name: product_regions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_regions_id_seq OWNED BY public.product_regions.id;


--
-- TOC entry 239 (class 1259 OID 19468)
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
-- TOC entry 240 (class 1259 OID 19473)
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
-- TOC entry 4553 (class 0 OID 0)
-- Dependencies: 240
-- Name: product_subcategories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_subcategories_id_seq OWNED BY public.product_subcategories.id;


--
-- TOC entry 241 (class 1259 OID 19474)
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
    pdf_path character varying(255),
    currency character varying(3) DEFAULT 'CNY'::character varying NOT NULL,
    is_vendor_product boolean DEFAULT false
);


--
-- TOC entry 242 (class 1259 OID 19479)
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
-- TOC entry 4554 (class 0 OID 0)
-- Dependencies: 242
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- TOC entry 243 (class 1259 OID 19480)
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
-- TOC entry 244 (class 1259 OID 19483)
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
-- TOC entry 4555 (class 0 OID 0)
-- Dependencies: 244
-- Name: project_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_members_id_seq OWNED BY public.project_members.id;


--
-- TOC entry 293 (class 1259 OID 20678)
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
-- TOC entry 292 (class 1259 OID 20677)
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
-- TOC entry 4556 (class 0 OID 0)
-- Dependencies: 292
-- Name: project_rating_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_rating_records_id_seq OWNED BY public.project_rating_records.id;


--
-- TOC entry 277 (class 1259 OID 20402)
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
-- TOC entry 276 (class 1259 OID 20401)
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
-- TOC entry 4557 (class 0 OID 0)
-- Dependencies: 276
-- Name: project_scoring_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_scoring_config_id_seq OWNED BY public.project_scoring_config.id;


--
-- TOC entry 279 (class 1259 OID 20417)
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
-- TOC entry 278 (class 1259 OID 20416)
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
-- TOC entry 4558 (class 0 OID 0)
-- Dependencies: 278
-- Name: project_scoring_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_scoring_records_id_seq OWNED BY public.project_scoring_records.id;


--
-- TOC entry 245 (class 1259 OID 19484)
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
-- TOC entry 246 (class 1259 OID 19490)
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
-- TOC entry 4559 (class 0 OID 0)
-- Dependencies: 246
-- Name: project_stage_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_stage_history_id_seq OWNED BY public.project_stage_history.id;


--
-- TOC entry 281 (class 1259 OID 20442)
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
-- TOC entry 280 (class 1259 OID 20441)
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
-- TOC entry 4560 (class 0 OID 0)
-- Dependencies: 280
-- Name: project_total_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_total_scores_id_seq OWNED BY public.project_total_scores.id;


--
-- TOC entry 247 (class 1259 OID 19491)
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
-- TOC entry 248 (class 1259 OID 19498)
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
-- TOC entry 4561 (class 0 OID 0)
-- Dependencies: 248
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- TOC entry 315 (class 1259 OID 28999)
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
-- TOC entry 314 (class 1259 OID 28998)
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
-- TOC entry 4562 (class 0 OID 0)
-- Dependencies: 314
-- Name: purchase_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_order_details_id_seq OWNED BY public.purchase_order_details.id;


--
-- TOC entry 309 (class 1259 OID 28930)
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
-- TOC entry 308 (class 1259 OID 28929)
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
-- TOC entry 4563 (class 0 OID 0)
-- Dependencies: 308
-- Name: purchase_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_orders_id_seq OWNED BY public.purchase_orders.id;


--
-- TOC entry 249 (class 1259 OID 19499)
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
    implant_subtotal double precision DEFAULT 0.00,
    currency character varying(3),
    original_market_price double precision,
    converted_market_price double precision
);


--
-- TOC entry 250 (class 1259 OID 19504)
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
-- TOC entry 4564 (class 0 OID 0)
-- Dependencies: 250
-- Name: quotation_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotation_details_id_seq OWNED BY public.quotation_details.id;


--
-- TOC entry 251 (class 1259 OID 19505)
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
    implant_total_amount double precision DEFAULT 0.00,
    currency character varying(3) DEFAULT 'CNY'::character varying NOT NULL,
    exchange_rate numeric(10,6) DEFAULT 1.000000 NOT NULL,
    original_currency character varying(3)
);


--
-- TOC entry 252 (class 1259 OID 19508)
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
-- TOC entry 4565 (class 0 OID 0)
-- Dependencies: 252
-- Name: quotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotations_id_seq OWNED BY public.quotations.id;


--
-- TOC entry 253 (class 1259 OID 19509)
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_permissions (
    id integer NOT NULL,
    role character varying(50) NOT NULL,
    module character varying(50) NOT NULL,
    can_view boolean,
    can_create boolean,
    can_edit boolean,
    can_delete boolean,
    pricing_discount_limit double precision,
    settlement_discount_limit double precision
);


--
-- TOC entry 254 (class 1259 OID 19512)
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
-- TOC entry 4566 (class 0 OID 0)
-- Dependencies: 254
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- TOC entry 313 (class 1259 OID 28975)
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
-- TOC entry 312 (class 1259 OID 28974)
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
-- TOC entry 4567 (class 0 OID 0)
-- Dependencies: 312
-- Name: settlement_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_details_id_seq OWNED BY public.settlement_details.id;


--
-- TOC entry 301 (class 1259 OID 20782)
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
    settlement_notes text,
    currency character varying(10) DEFAULT 'CNY'::character varying
);


--
-- TOC entry 4568 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.pricing_order_id IS '批价单ID';


--
-- TOC entry 4569 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_name IS '产品名称';


--
-- TOC entry 4570 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_model IS '产品型号';


--
-- TOC entry 4571 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_desc IS '产品描述';


--
-- TOC entry 4572 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.brand IS '品牌';


--
-- TOC entry 4573 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.unit IS '单位';


--
-- TOC entry 4574 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_mn IS '产品MN编码';


--
-- TOC entry 4575 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.market_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.market_price IS '市场价';


--
-- TOC entry 4576 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.unit_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.unit_price IS '单价';


--
-- TOC entry 4577 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.quantity IS '数量';


--
-- TOC entry 4578 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.discount_rate IS '折扣率';


--
-- TOC entry 4579 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.total_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.total_price IS '小计金额';


--
-- TOC entry 4580 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.pricing_detail_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.pricing_detail_id IS '关联批价单明细ID';


--
-- TOC entry 4581 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.settlement_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_order_id IS '结算单ID';


--
-- TOC entry 4582 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.settlement_company_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_company_id IS '结算目标公司ID';


--
-- TOC entry 4583 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.settlement_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_status IS '结算状态: pending, completed';


--
-- TOC entry 4584 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.settlement_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_date IS '结算完成时间';


--
-- TOC entry 4585 (class 0 OID 0)
-- Dependencies: 301
-- Name: COLUMN settlement_order_details.settlement_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_notes IS '结算备注';


--
-- TOC entry 300 (class 1259 OID 20781)
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
-- TOC entry 4586 (class 0 OID 0)
-- Dependencies: 300
-- Name: settlement_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_order_details_id_seq OWNED BY public.settlement_order_details.id;


--
-- TOC entry 303 (class 1259 OID 20868)
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
-- TOC entry 4587 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.order_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.order_number IS '结算单号';


--
-- TOC entry 4588 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.pricing_order_id IS '关联批价单ID';


--
-- TOC entry 4589 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.project_id IS '项目ID';


--
-- TOC entry 4590 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.quotation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.quotation_id IS '报价单ID';


--
-- TOC entry 4591 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.distributor_id IS '分销商ID';


--
-- TOC entry 4592 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.dealer_id IS '经销商ID（辅助信息）';


--
-- TOC entry 4593 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.total_amount IS '结算总金额';


--
-- TOC entry 4594 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.total_discount_rate IS '结算总折扣率';


--
-- TOC entry 4595 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.status IS '结算单状态';


--
-- TOC entry 4596 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.approved_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.approved_by IS '批准人';


--
-- TOC entry 4597 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.approved_at IS '批准时间';


--
-- TOC entry 4598 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.created_by IS '创建人';


--
-- TOC entry 4599 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.created_at IS '创建时间';


--
-- TOC entry 4600 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN settlement_orders.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.updated_at IS '更新时间';


--
-- TOC entry 302 (class 1259 OID 20867)
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
-- TOC entry 4601 (class 0 OID 0)
-- Dependencies: 302
-- Name: settlement_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_orders_id_seq OWNED BY public.settlement_orders.id;


--
-- TOC entry 307 (class 1259 OID 28904)
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
-- TOC entry 306 (class 1259 OID 28903)
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
-- TOC entry 4602 (class 0 OID 0)
-- Dependencies: 306
-- Name: settlements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlements_id_seq OWNED BY public.settlements.id;


--
-- TOC entry 275 (class 1259 OID 20362)
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
-- TOC entry 4603 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN solution_manager_email_settings.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.user_id IS '解决方案经理用户ID';


--
-- TOC entry 4604 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN solution_manager_email_settings.quotation_created; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_created IS '报价单新建通知';


--
-- TOC entry 4605 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN solution_manager_email_settings.quotation_updated; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_updated IS '报价单更新通知';


--
-- TOC entry 4606 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN solution_manager_email_settings.project_created; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_created IS '项目新建通知';


--
-- TOC entry 4607 (class 0 OID 0)
-- Dependencies: 275
-- Name: COLUMN solution_manager_email_settings.project_stage_changed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_stage_changed IS '项目阶段推进通知';


--
-- TOC entry 274 (class 1259 OID 20361)
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
-- TOC entry 4608 (class 0 OID 0)
-- Dependencies: 274
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.solution_manager_email_settings_id_seq OWNED BY public.solution_manager_email_settings.id;


--
-- TOC entry 291 (class 1259 OID 20585)
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
-- TOC entry 4609 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.version_id IS '版本ID';


--
-- TOC entry 4610 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.avg_response_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.avg_response_time IS '平均响应时间（毫秒）';


--
-- TOC entry 4611 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.max_response_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.max_response_time IS '最大响应时间（毫秒）';


--
-- TOC entry 4612 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.error_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.error_rate IS '错误率（百分比）';


--
-- TOC entry 4613 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.active_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.active_users IS '活跃用户数';


--
-- TOC entry 4614 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.total_requests; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.total_requests IS '总请求数';


--
-- TOC entry 4615 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.database_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.database_size IS '数据库大小（字节）';


--
-- TOC entry 4616 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.cpu_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.cpu_usage IS 'CPU使用率（百分比）';


--
-- TOC entry 4617 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.memory_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.memory_usage IS '内存使用率（百分比）';


--
-- TOC entry 4618 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.disk_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.disk_usage IS '磁盘使用率（百分比）';


--
-- TOC entry 4619 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN system_metrics.recorded_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.recorded_at IS '记录时间';


--
-- TOC entry 290 (class 1259 OID 20584)
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
-- TOC entry 4620 (class 0 OID 0)
-- Dependencies: 290
-- Name: system_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_metrics_id_seq OWNED BY public.system_metrics.id;


--
-- TOC entry 272 (class 1259 OID 20256)
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
-- TOC entry 271 (class 1259 OID 20255)
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
-- TOC entry 4621 (class 0 OID 0)
-- Dependencies: 271
-- Name: system_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_settings_id_seq OWNED BY public.system_settings.id;


--
-- TOC entry 287 (class 1259 OID 20547)
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
-- TOC entry 4622 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.version_id IS '版本ID';


--
-- TOC entry 4623 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.from_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.from_version IS '升级前版本';


--
-- TOC entry 4624 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.to_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.to_version IS '升级后版本';


--
-- TOC entry 4625 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.upgrade_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_date IS '升级时间';


--
-- TOC entry 4626 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.upgrade_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_type IS '升级类型：manual/automatic';


--
-- TOC entry 4627 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.status IS '升级状态：success/failed/rollback';


--
-- TOC entry 4628 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.upgrade_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_notes IS '升级说明';


--
-- TOC entry 4629 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.error_message IS '错误信息（如果升级失败）';


--
-- TOC entry 4630 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.duration_seconds; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.duration_seconds IS '升级耗时（秒）';


--
-- TOC entry 4631 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.operator_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.operator_id IS '操作人员ID';


--
-- TOC entry 4632 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.operator_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.operator_name IS '操作人员姓名';


--
-- TOC entry 4633 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.environment IS '升级环境';


--
-- TOC entry 4634 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN upgrade_logs.server_info; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.server_info IS '服务器信息';


--
-- TOC entry 286 (class 1259 OID 20546)
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
-- TOC entry 4635 (class 0 OID 0)
-- Dependencies: 286
-- Name: upgrade_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.upgrade_logs_id_seq OWNED BY public.upgrade_logs.id;


--
-- TOC entry 262 (class 1259 OID 19963)
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
-- TOC entry 4636 (class 0 OID 0)
-- Dependencies: 262
-- Name: COLUMN user_event_subscriptions.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.user_id IS '订阅者用户ID';


--
-- TOC entry 4637 (class 0 OID 0)
-- Dependencies: 262
-- Name: COLUMN user_event_subscriptions.target_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.target_user_id IS '被订阅的用户ID';


--
-- TOC entry 4638 (class 0 OID 0)
-- Dependencies: 262
-- Name: COLUMN user_event_subscriptions.event_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.event_id IS '事件ID';


--
-- TOC entry 4639 (class 0 OID 0)
-- Dependencies: 262
-- Name: COLUMN user_event_subscriptions.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.enabled IS '是否启用订阅';


--
-- TOC entry 261 (class 1259 OID 19962)
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
-- TOC entry 4640 (class 0 OID 0)
-- Dependencies: 261
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_event_subscriptions_id_seq OWNED BY public.user_event_subscriptions.id;


--
-- TOC entry 255 (class 1259 OID 19513)
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
    updated_at double precision,
    language_preference character varying(10)
);


--
-- TOC entry 256 (class 1259 OID 19518)
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
-- TOC entry 4641 (class 0 OID 0)
-- Dependencies: 256
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 285 (class 1259 OID 20536)
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
-- TOC entry 4642 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.version_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.version_number IS '版本号，如1.0.0';


--
-- TOC entry 4643 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.version_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.version_name IS '版本名称';


--
-- TOC entry 4644 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.release_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.release_date IS '发布日期';


--
-- TOC entry 4645 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.description IS '版本描述';


--
-- TOC entry 4646 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.is_current; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.is_current IS '是否为当前版本';


--
-- TOC entry 4647 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.environment IS '环境：development/production';


--
-- TOC entry 4648 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.total_features; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_features IS '新增功能数量';


--
-- TOC entry 4649 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.total_fixes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_fixes IS '修复问题数量';


--
-- TOC entry 4650 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.total_improvements; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_improvements IS '改进数量';


--
-- TOC entry 4651 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.git_commit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.git_commit IS 'Git提交哈希';


--
-- TOC entry 4652 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.build_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.build_number IS '构建号';


--
-- TOC entry 4653 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.created_at IS '创建时间';


--
-- TOC entry 4654 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN version_records.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.updated_at IS '更新时间';


--
-- TOC entry 284 (class 1259 OID 20535)
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
-- TOC entry 4655 (class 0 OID 0)
-- Dependencies: 284
-- Name: version_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.version_records_id_seq OWNED BY public.version_records.id;


--
-- TOC entry 3964 (class 2604 OID 20602)
-- Name: action_reply id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply ALTER COLUMN id SET DEFAULT nextval('public.action_reply_id_seq'::regclass);


--
-- TOC entry 3920 (class 2604 OID 20603)
-- Name: actions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions ALTER COLUMN id SET DEFAULT nextval('public.actions_id_seq'::regclass);


--
-- TOC entry 3921 (class 2604 OID 20604)
-- Name: affiliations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations ALTER COLUMN id SET DEFAULT nextval('public.affiliations_id_seq'::regclass);


--
-- TOC entry 3971 (class 2604 OID 20605)
-- Name: approval_instance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance ALTER COLUMN id SET DEFAULT nextval('public.approval_instance_id_seq'::regclass);


--
-- TOC entry 3967 (class 2604 OID 20606)
-- Name: approval_process_template id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template ALTER COLUMN id SET DEFAULT nextval('public.approval_process_template_id_seq'::regclass);


--
-- TOC entry 3972 (class 2604 OID 20607)
-- Name: approval_step id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step ALTER COLUMN id SET DEFAULT nextval('public.approval_step_id_seq'::regclass);


--
-- TOC entry 4000 (class 2604 OID 20608)
-- Name: change_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs ALTER COLUMN id SET DEFAULT nextval('public.change_logs_id_seq'::regclass);


--
-- TOC entry 3922 (class 2604 OID 20609)
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- TOC entry 3923 (class 2604 OID 20610)
-- Name: contacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts ALTER COLUMN id SET DEFAULT nextval('public.contacts_id_seq'::regclass);


--
-- TOC entry 3924 (class 2604 OID 20611)
-- Name: dev_product_specs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs ALTER COLUMN id SET DEFAULT nextval('public.dev_product_specs_id_seq'::regclass);


--
-- TOC entry 3925 (class 2604 OID 20612)
-- Name: dev_products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products ALTER COLUMN id SET DEFAULT nextval('public.dev_products_id_seq'::regclass);


--
-- TOC entry 3927 (class 2604 OID 20613)
-- Name: dictionaries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries ALTER COLUMN id SET DEFAULT nextval('public.dictionaries_id_seq'::regclass);


--
-- TOC entry 3965 (class 2604 OID 20614)
-- Name: event_registry id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry ALTER COLUMN id SET DEFAULT nextval('public.event_registry_id_seq'::regclass);


--
-- TOC entry 4003 (class 2604 OID 20615)
-- Name: feature_changes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes ALTER COLUMN id SET DEFAULT nextval('public.feature_changes_id_seq'::regclass);


--
-- TOC entry 4016 (class 2604 OID 28881)
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- TOC entry 4019 (class 2604 OID 28959)
-- Name: inventory_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions ALTER COLUMN id SET DEFAULT nextval('public.inventory_transactions_id_seq'::regclass);


--
-- TOC entry 3929 (class 2604 OID 20616)
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- TOC entry 4012 (class 2604 OID 20766)
-- Name: pricing_order_approval_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_approval_records_id_seq'::regclass);


--
-- TOC entry 4010 (class 2604 OID 20747)
-- Name: pricing_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_details_id_seq'::regclass);


--
-- TOC entry 4006 (class 2604 OID 20709)
-- Name: pricing_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders ALTER COLUMN id SET DEFAULT nextval('public.pricing_orders_id_seq'::regclass);


--
-- TOC entry 3930 (class 2604 OID 20617)
-- Name: product_categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories ALTER COLUMN id SET DEFAULT nextval('public.product_categories_id_seq'::regclass);


--
-- TOC entry 3931 (class 2604 OID 20618)
-- Name: product_code_field_options id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_options_id_seq'::regclass);


--
-- TOC entry 3932 (class 2604 OID 20619)
-- Name: product_code_field_values id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_values_id_seq'::regclass);


--
-- TOC entry 3933 (class 2604 OID 20620)
-- Name: product_code_fields id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields ALTER COLUMN id SET DEFAULT nextval('public.product_code_fields_id_seq'::regclass);


--
-- TOC entry 3934 (class 2604 OID 20621)
-- Name: product_codes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes ALTER COLUMN id SET DEFAULT nextval('public.product_codes_id_seq'::regclass);


--
-- TOC entry 3935 (class 2604 OID 20622)
-- Name: product_regions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_regions ALTER COLUMN id SET DEFAULT nextval('public.product_regions_id_seq'::regclass);


--
-- TOC entry 3936 (class 2604 OID 20623)
-- Name: product_subcategories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories ALTER COLUMN id SET DEFAULT nextval('public.product_subcategories_id_seq'::regclass);


--
-- TOC entry 3937 (class 2604 OID 20624)
-- Name: products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- TOC entry 3940 (class 2604 OID 20625)
-- Name: project_members id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members ALTER COLUMN id SET DEFAULT nextval('public.project_members_id_seq'::regclass);


--
-- TOC entry 4005 (class 2604 OID 20681)
-- Name: project_rating_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records ALTER COLUMN id SET DEFAULT nextval('public.project_rating_records_id_seq'::regclass);


--
-- TOC entry 3980 (class 2604 OID 20627)
-- Name: project_scoring_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_config_id_seq'::regclass);


--
-- TOC entry 3985 (class 2604 OID 20628)
-- Name: project_scoring_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_records_id_seq'::regclass);


--
-- TOC entry 3941 (class 2604 OID 20629)
-- Name: project_stage_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history ALTER COLUMN id SET DEFAULT nextval('public.project_stage_history_id_seq'::regclass);


--
-- TOC entry 3990 (class 2604 OID 20630)
-- Name: project_total_scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores ALTER COLUMN id SET DEFAULT nextval('public.project_total_scores_id_seq'::regclass);


--
-- TOC entry 3943 (class 2604 OID 20631)
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- TOC entry 4021 (class 2604 OID 29002)
-- Name: purchase_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details ALTER COLUMN id SET DEFAULT nextval('public.purchase_order_details_id_seq'::regclass);


--
-- TOC entry 4018 (class 2604 OID 28933)
-- Name: purchase_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders ALTER COLUMN id SET DEFAULT nextval('public.purchase_orders_id_seq'::regclass);


--
-- TOC entry 3949 (class 2604 OID 20632)
-- Name: quotation_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details ALTER COLUMN id SET DEFAULT nextval('public.quotation_details_id_seq'::regclass);


--
-- TOC entry 3951 (class 2604 OID 20633)
-- Name: quotations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations ALTER COLUMN id SET DEFAULT nextval('public.quotations_id_seq'::regclass);


--
-- TOC entry 3962 (class 2604 OID 20634)
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- TOC entry 4020 (class 2604 OID 28978)
-- Name: settlement_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_details_id_seq'::regclass);


--
-- TOC entry 4013 (class 2604 OID 20785)
-- Name: settlement_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_order_details_id_seq'::regclass);


--
-- TOC entry 4015 (class 2604 OID 20871)
-- Name: settlement_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders ALTER COLUMN id SET DEFAULT nextval('public.settlement_orders_id_seq'::regclass);


--
-- TOC entry 4017 (class 2604 OID 28907)
-- Name: settlements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements ALTER COLUMN id SET DEFAULT nextval('public.settlements_id_seq'::regclass);


--
-- TOC entry 3979 (class 2604 OID 20635)
-- Name: solution_manager_email_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings ALTER COLUMN id SET DEFAULT nextval('public.solution_manager_email_settings_id_seq'::regclass);


--
-- TOC entry 4004 (class 2604 OID 20636)
-- Name: system_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics ALTER COLUMN id SET DEFAULT nextval('public.system_metrics_id_seq'::regclass);


--
-- TOC entry 3978 (class 2604 OID 20637)
-- Name: system_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings ALTER COLUMN id SET DEFAULT nextval('public.system_settings_id_seq'::regclass);


--
-- TOC entry 4002 (class 2604 OID 20638)
-- Name: upgrade_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs ALTER COLUMN id SET DEFAULT nextval('public.upgrade_logs_id_seq'::regclass);


--
-- TOC entry 3966 (class 2604 OID 20639)
-- Name: user_event_subscriptions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions ALTER COLUMN id SET DEFAULT nextval('public.user_event_subscriptions_id_seq'::regclass);


--
-- TOC entry 3963 (class 2604 OID 20640)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4001 (class 2604 OID 20641)
-- Name: version_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records ALTER COLUMN id SET DEFAULT nextval('public.version_records_id_seq'::regclass);


--
-- TOC entry 4099 (class 2606 OID 19862)
-- Name: action_reply action_reply_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_pkey PRIMARY KEY (id);


--
-- TOC entry 4024 (class 2606 OID 19548)
-- Name: actions actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_pkey PRIMARY KEY (id);


--
-- TOC entry 4026 (class 2606 OID 19550)
-- Name: affiliations affiliations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_pkey PRIMARY KEY (id);


--
-- TOC entry 4120 (class 2606 OID 20310)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 4111 (class 2606 OID 20005)
-- Name: approval_instance approval_instance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_pkey PRIMARY KEY (id);


--
-- TOC entry 4109 (class 2606 OID 19993)
-- Name: approval_process_template approval_process_template_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_pkey PRIMARY KEY (id);


--
-- TOC entry 4115 (class 2606 OID 20186)
-- Name: approval_record approval_record_temp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_temp_pkey PRIMARY KEY (id);


--
-- TOC entry 4113 (class 2606 OID 20012)
-- Name: approval_step approval_step_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_pkey PRIMARY KEY (id);


--
-- TOC entry 4138 (class 2606 OID 20516)
-- Name: change_logs change_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs
    ADD CONSTRAINT change_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 4030 (class 2606 OID 19554)
-- Name: companies companies_company_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_company_code_key UNIQUE (company_code);


--
-- TOC entry 4032 (class 2606 OID 19556)
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- TOC entry 4034 (class 2606 OID 19558)
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (id);


--
-- TOC entry 4036 (class 2606 OID 19562)
-- Name: dev_product_specs dev_product_specs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs
    ADD CONSTRAINT dev_product_specs_pkey PRIMARY KEY (id);


--
-- TOC entry 4038 (class 2606 OID 19564)
-- Name: dev_products dev_products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_pkey PRIMARY KEY (id);


--
-- TOC entry 4040 (class 2606 OID 19566)
-- Name: dictionaries dictionaries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT dictionaries_pkey PRIMARY KEY (id);


--
-- TOC entry 4101 (class 2606 OID 20048)
-- Name: event_registry event_registry_event_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_event_key_key UNIQUE (event_key);


--
-- TOC entry 4103 (class 2606 OID 19906)
-- Name: event_registry event_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_pkey PRIMARY KEY (id);


--
-- TOC entry 4146 (class 2606 OID 20573)
-- Name: feature_changes feature_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_pkey PRIMARY KEY (id);


--
-- TOC entry 4168 (class 2606 OID 28885)
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (id);


--
-- TOC entry 4180 (class 2606 OID 28963)
-- Name: inventory_transactions inventory_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_pkey PRIMARY KEY (id);


--
-- TOC entry 4044 (class 2606 OID 19568)
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 4160 (class 2606 OID 20770)
-- Name: pricing_order_approval_records pricing_order_approval_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_pkey PRIMARY KEY (id);


--
-- TOC entry 4158 (class 2606 OID 20751)
-- Name: pricing_order_details pricing_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details
    ADD CONSTRAINT pricing_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4154 (class 2606 OID 20991)
-- Name: pricing_orders pricing_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 4156 (class 2606 OID 20711)
-- Name: pricing_orders pricing_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 4048 (class 2606 OID 19570)
-- Name: product_categories product_categories_code_letter_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_code_letter_key UNIQUE (code_letter);


--
-- TOC entry 4050 (class 2606 OID 19572)
-- Name: product_categories product_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_pkey PRIMARY KEY (id);


--
-- TOC entry 4052 (class 2606 OID 19574)
-- Name: product_code_field_options product_code_field_options_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options
    ADD CONSTRAINT product_code_field_options_pkey PRIMARY KEY (id);


--
-- TOC entry 4054 (class 2606 OID 19576)
-- Name: product_code_field_values product_code_field_values_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_pkey PRIMARY KEY (id);


--
-- TOC entry 4056 (class 2606 OID 19578)
-- Name: product_code_fields product_code_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields
    ADD CONSTRAINT product_code_fields_pkey PRIMARY KEY (id);


--
-- TOC entry 4058 (class 2606 OID 19580)
-- Name: product_codes product_codes_full_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_full_code_key UNIQUE (full_code);


--
-- TOC entry 4060 (class 2606 OID 19582)
-- Name: product_codes product_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_pkey PRIMARY KEY (id);


--
-- TOC entry 4062 (class 2606 OID 19584)
-- Name: product_regions product_regions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_regions
    ADD CONSTRAINT product_regions_pkey PRIMARY KEY (id);


--
-- TOC entry 4064 (class 2606 OID 19586)
-- Name: product_subcategories product_subcategories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT product_subcategories_pkey PRIMARY KEY (id);


--
-- TOC entry 4068 (class 2606 OID 19588)
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- TOC entry 4070 (class 2606 OID 19590)
-- Name: products products_product_mn_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_product_mn_key UNIQUE (product_mn);


--
-- TOC entry 4072 (class 2606 OID 19592)
-- Name: project_members project_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (id);


--
-- TOC entry 4150 (class 2606 OID 20684)
-- Name: project_rating_records project_rating_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_pkey PRIMARY KEY (id);


--
-- TOC entry 4126 (class 2606 OID 20413)
-- Name: project_scoring_config project_scoring_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config
    ADD CONSTRAINT project_scoring_config_pkey PRIMARY KEY (id);


--
-- TOC entry 4130 (class 2606 OID 20428)
-- Name: project_scoring_records project_scoring_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_pkey PRIMARY KEY (id);


--
-- TOC entry 4075 (class 2606 OID 19594)
-- Name: project_stage_history project_stage_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history
    ADD CONSTRAINT project_stage_history_pkey PRIMARY KEY (id);


--
-- TOC entry 4134 (class 2606 OID 20456)
-- Name: project_total_scores project_total_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_pkey PRIMARY KEY (id);


--
-- TOC entry 4136 (class 2606 OID 20458)
-- Name: project_total_scores project_total_scores_project_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_project_id_key UNIQUE (project_id);


--
-- TOC entry 4079 (class 2606 OID 19596)
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- TOC entry 4184 (class 2606 OID 29006)
-- Name: purchase_order_details purchase_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4176 (class 2606 OID 28939)
-- Name: purchase_orders purchase_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 4178 (class 2606 OID 28937)
-- Name: purchase_orders purchase_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 4081 (class 2606 OID 19598)
-- Name: quotation_details quotation_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details
    ADD CONSTRAINT quotation_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4083 (class 2606 OID 19600)
-- Name: quotations quotations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_pkey PRIMARY KEY (id);


--
-- TOC entry 4085 (class 2606 OID 19602)
-- Name: quotations quotations_quotation_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_quotation_number_key UNIQUE (quotation_number);


--
-- TOC entry 4087 (class 2606 OID 19604)
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 4182 (class 2606 OID 28982)
-- Name: settlement_details settlement_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4162 (class 2606 OID 20789)
-- Name: settlement_order_details settlement_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4164 (class 2606 OID 20875)
-- Name: settlement_orders settlement_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 4166 (class 2606 OID 20873)
-- Name: settlement_orders settlement_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 4172 (class 2606 OID 28911)
-- Name: settlements settlements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_pkey PRIMARY KEY (id);


--
-- TOC entry 4174 (class 2606 OID 28913)
-- Name: settlements settlements_settlement_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_settlement_number_key UNIQUE (settlement_number);


--
-- TOC entry 4122 (class 2606 OID 20367)
-- Name: solution_manager_email_settings solution_manager_email_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT solution_manager_email_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 4148 (class 2606 OID 20590)
-- Name: system_metrics system_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_pkey PRIMARY KEY (id);


--
-- TOC entry 4118 (class 2606 OID 20263)
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 4028 (class 2606 OID 19608)
-- Name: affiliations uix_owner_viewer; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT uix_owner_viewer UNIQUE (owner_id, viewer_id);


--
-- TOC entry 4089 (class 2606 OID 19610)
-- Name: role_permissions uix_role_module; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT uix_role_module UNIQUE (role, module);


--
-- TOC entry 4042 (class 2606 OID 19612)
-- Name: dictionaries uix_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT uix_type_key UNIQUE (type, key);


--
-- TOC entry 4046 (class 2606 OID 19614)
-- Name: permissions uix_user_module; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT uix_user_module UNIQUE (user_id, module);


--
-- TOC entry 4170 (class 2606 OID 28887)
-- Name: inventory unique_company_product_inventory; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT unique_company_product_inventory UNIQUE (company_id, product_id);


--
-- TOC entry 4144 (class 2606 OID 20554)
-- Name: upgrade_logs upgrade_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 4152 (class 2606 OID 20686)
-- Name: project_rating_records uq_project_user_rating; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT uq_project_user_rating UNIQUE (project_id, user_id);


--
-- TOC entry 4128 (class 2606 OID 20661)
-- Name: project_scoring_config uq_scoring_config; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config
    ADD CONSTRAINT uq_scoring_config UNIQUE (category, field_name);


--
-- TOC entry 4132 (class 2606 OID 30035)
-- Name: project_scoring_records uq_scoring_record; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT uq_scoring_record UNIQUE (project_id, category, field_name);


--
-- TOC entry 4124 (class 2606 OID 20369)
-- Name: solution_manager_email_settings uq_solution_manager_email_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT uq_solution_manager_email_user UNIQUE (user_id);


--
-- TOC entry 4066 (class 2606 OID 19616)
-- Name: product_subcategories uq_subcategory_code_letter; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT uq_subcategory_code_letter UNIQUE (category_id, code_letter);


--
-- TOC entry 4105 (class 2606 OID 19970)
-- Name: user_event_subscriptions uq_user_target_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT uq_user_target_event UNIQUE (user_id, target_user_id, event_id);


--
-- TOC entry 4107 (class 2606 OID 19968)
-- Name: user_event_subscriptions user_event_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_pkey PRIMARY KEY (id);


--
-- TOC entry 4091 (class 2606 OID 19618)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4093 (class 2606 OID 19620)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4095 (class 2606 OID 19622)
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- TOC entry 4097 (class 2606 OID 19624)
-- Name: users users_wechat_openid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_wechat_openid_key UNIQUE (wechat_openid);


--
-- TOC entry 4140 (class 2606 OID 20543)
-- Name: version_records version_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records
    ADD CONSTRAINT version_records_pkey PRIMARY KEY (id);


--
-- TOC entry 4142 (class 2606 OID 20545)
-- Name: version_records version_records_version_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records
    ADD CONSTRAINT version_records_version_number_key UNIQUE (version_number);


--
-- TOC entry 4073 (class 1259 OID 19625)
-- Name: ix_project_stage_history_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_stage_history_project_id ON public.project_stage_history USING btree (project_id);


--
-- TOC entry 4076 (class 1259 OID 19627)
-- Name: ix_projects_authorization_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_authorization_code ON public.projects USING btree (authorization_code);


--
-- TOC entry 4077 (class 1259 OID 19628)
-- Name: ix_projects_project_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_project_name ON public.projects USING btree (project_name);


--
-- TOC entry 4116 (class 1259 OID 20264)
-- Name: ix_system_settings_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_system_settings_key ON public.system_settings USING btree (key);


--
-- TOC entry 4224 (class 2606 OID 19863)
-- Name: action_reply action_reply_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.actions(id);


--
-- TOC entry 4225 (class 2606 OID 19873)
-- Name: action_reply action_reply_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4226 (class 2606 OID 19868)
-- Name: action_reply action_reply_parent_reply_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_parent_reply_id_fkey FOREIGN KEY (parent_reply_id) REFERENCES public.action_reply(id);


--
-- TOC entry 4185 (class 2606 OID 19629)
-- Name: actions actions_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 4186 (class 2606 OID 19634)
-- Name: actions actions_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- TOC entry 4187 (class 2606 OID 19639)
-- Name: actions actions_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4188 (class 2606 OID 20311)
-- Name: actions actions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4189 (class 2606 OID 19649)
-- Name: affiliations affiliations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4190 (class 2606 OID 19654)
-- Name: affiliations affiliations_viewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_viewer_id_fkey FOREIGN KEY (viewer_id) REFERENCES public.users(id);


--
-- TOC entry 4231 (class 2606 OID 20126)
-- Name: approval_instance approval_instance_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4232 (class 2606 OID 20121)
-- Name: approval_instance approval_instance_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- TOC entry 4230 (class 2606 OID 19994)
-- Name: approval_process_template approval_process_template_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4235 (class 2606 OID 20323)
-- Name: approval_record approval_record_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES public.approval_instance(id);


--
-- TOC entry 4233 (class 2606 OID 20018)
-- Name: approval_step approval_step_approver_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_approver_user_id_fkey FOREIGN KEY (approver_user_id) REFERENCES public.users(id);


--
-- TOC entry 4234 (class 2606 OID 20013)
-- Name: approval_step approval_step_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- TOC entry 4242 (class 2606 OID 20517)
-- Name: change_logs change_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs
    ADD CONSTRAINT change_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 4191 (class 2606 OID 19659)
-- Name: companies companies_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4192 (class 2606 OID 19664)
-- Name: contacts contacts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 4193 (class 2606 OID 19669)
-- Name: contacts contacts_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4194 (class 2606 OID 19684)
-- Name: dev_product_specs dev_product_specs_dev_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs
    ADD CONSTRAINT dev_product_specs_dev_product_id_fkey FOREIGN KEY (dev_product_id) REFERENCES public.dev_products(id);


--
-- TOC entry 4195 (class 2606 OID 19689)
-- Name: dev_products dev_products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 4196 (class 2606 OID 19694)
-- Name: dev_products dev_products_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4197 (class 2606 OID 19699)
-- Name: dev_products dev_products_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4198 (class 2606 OID 19704)
-- Name: dev_products dev_products_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.product_regions(id);


--
-- TOC entry 4199 (class 2606 OID 19709)
-- Name: dev_products dev_products_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 4245 (class 2606 OID 20579)
-- Name: feature_changes feature_changes_developer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_developer_id_fkey FOREIGN KEY (developer_id) REFERENCES public.users(id);


--
-- TOC entry 4246 (class 2606 OID 20574)
-- Name: feature_changes feature_changes_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 4236 (class 2606 OID 20197)
-- Name: approval_record fk_approval_record_approver_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT fk_approval_record_approver_id FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- TOC entry 4237 (class 2606 OID 20192)
-- Name: approval_record fk_approval_record_step_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT fk_approval_record_step_id FOREIGN KEY (step_id) REFERENCES public.approval_step(id);


--
-- TOC entry 4259 (class 2606 OID 29017)
-- Name: settlement_order_details fk_settlement_order_details_settlement_company; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT fk_settlement_order_details_settlement_company FOREIGN KEY (settlement_company_id) REFERENCES public.companies(id);


--
-- TOC entry 4270 (class 2606 OID 28888)
-- Name: inventory inventory_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 4271 (class 2606 OID 28898)
-- Name: inventory inventory_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 4272 (class 2606 OID 28893)
-- Name: inventory inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 4279 (class 2606 OID 28969)
-- Name: inventory_transactions inventory_transactions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 4280 (class 2606 OID 28964)
-- Name: inventory_transactions inventory_transactions_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- TOC entry 4200 (class 2606 OID 19714)
-- Name: permissions permissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 4257 (class 2606 OID 20776)
-- Name: pricing_order_approval_records pricing_order_approval_records_approver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_approver_id_fkey FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- TOC entry 4258 (class 2606 OID 20771)
-- Name: pricing_order_approval_records pricing_order_approval_records_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 4256 (class 2606 OID 20752)
-- Name: pricing_order_details pricing_order_details_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details
    ADD CONSTRAINT pricing_order_details_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 4250 (class 2606 OID 20732)
-- Name: pricing_orders pricing_orders_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 4251 (class 2606 OID 20737)
-- Name: pricing_orders pricing_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4252 (class 2606 OID 20727)
-- Name: pricing_orders pricing_orders_dealer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_dealer_id_fkey FOREIGN KEY (dealer_id) REFERENCES public.companies(id);


--
-- TOC entry 4253 (class 2606 OID 20722)
-- Name: pricing_orders pricing_orders_distributor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_distributor_id_fkey FOREIGN KEY (distributor_id) REFERENCES public.companies(id);


--
-- TOC entry 4254 (class 2606 OID 20712)
-- Name: pricing_orders pricing_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4255 (class 2606 OID 20717)
-- Name: pricing_orders pricing_orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 4201 (class 2606 OID 19719)
-- Name: product_code_field_options product_code_field_options_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options
    ADD CONSTRAINT product_code_field_options_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.product_code_fields(id);


--
-- TOC entry 4202 (class 2606 OID 19724)
-- Name: product_code_field_values product_code_field_values_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.product_code_fields(id);


--
-- TOC entry 4203 (class 2606 OID 19729)
-- Name: product_code_field_values product_code_field_values_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_option_id_fkey FOREIGN KEY (option_id) REFERENCES public.product_code_field_options(id);


--
-- TOC entry 4204 (class 2606 OID 19734)
-- Name: product_code_field_values product_code_field_values_product_code_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_product_code_id_fkey FOREIGN KEY (product_code_id) REFERENCES public.product_codes(id);


--
-- TOC entry 4205 (class 2606 OID 19739)
-- Name: product_code_fields product_code_fields_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields
    ADD CONSTRAINT product_code_fields_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 4206 (class 2606 OID 19744)
-- Name: product_codes product_codes_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 4207 (class 2606 OID 19749)
-- Name: product_codes product_codes_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4208 (class 2606 OID 19754)
-- Name: product_codes product_codes_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 4209 (class 2606 OID 19759)
-- Name: product_codes product_codes_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 4210 (class 2606 OID 19764)
-- Name: product_subcategories product_subcategories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT product_subcategories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 4211 (class 2606 OID 19769)
-- Name: products products_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4212 (class 2606 OID 20328)
-- Name: project_members project_members_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4213 (class 2606 OID 19779)
-- Name: project_members project_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 4248 (class 2606 OID 20687)
-- Name: project_rating_records project_rating_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 4249 (class 2606 OID 20692)
-- Name: project_rating_records project_rating_records_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4239 (class 2606 OID 20436)
-- Name: project_scoring_records project_scoring_records_awarded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_awarded_by_fkey FOREIGN KEY (awarded_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- TOC entry 4240 (class 2606 OID 20431)
-- Name: project_scoring_records project_scoring_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 4214 (class 2606 OID 20333)
-- Name: project_stage_history project_stage_history_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history
    ADD CONSTRAINT project_stage_history_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4241 (class 2606 OID 20459)
-- Name: project_total_scores project_total_scores_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 4215 (class 2606 OID 20175)
-- Name: projects projects_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- TOC entry 4216 (class 2606 OID 19794)
-- Name: projects projects_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4217 (class 2606 OID 20348)
-- Name: projects projects_vendor_sales_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_vendor_sales_manager_id_fkey FOREIGN KEY (vendor_sales_manager_id) REFERENCES public.users(id);


--
-- TOC entry 4284 (class 2606 OID 29007)
-- Name: purchase_order_details purchase_order_details_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.purchase_orders(id);


--
-- TOC entry 4285 (class 2606 OID 29012)
-- Name: purchase_order_details purchase_order_details_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 4276 (class 2606 OID 28950)
-- Name: purchase_orders purchase_orders_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- TOC entry 4277 (class 2606 OID 28940)
-- Name: purchase_orders purchase_orders_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 4278 (class 2606 OID 28945)
-- Name: purchase_orders purchase_orders_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 4218 (class 2606 OID 19799)
-- Name: quotation_details quotation_details_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details
    ADD CONSTRAINT quotation_details_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 4219 (class 2606 OID 20648)
-- Name: quotations quotations_confirmed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_confirmed_by_fkey FOREIGN KEY (confirmed_by) REFERENCES public.users(id);


--
-- TOC entry 4220 (class 2606 OID 19804)
-- Name: quotations quotations_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- TOC entry 4221 (class 2606 OID 20528)
-- Name: quotations quotations_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- TOC entry 4222 (class 2606 OID 19809)
-- Name: quotations quotations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4223 (class 2606 OID 20343)
-- Name: quotations quotations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4281 (class 2606 OID 28988)
-- Name: settlement_details settlement_details_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- TOC entry 4282 (class 2606 OID 28993)
-- Name: settlement_details settlement_details_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 4283 (class 2606 OID 28983)
-- Name: settlement_details settlement_details_settlement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_settlement_id_fkey FOREIGN KEY (settlement_id) REFERENCES public.settlements(id);


--
-- TOC entry 4260 (class 2606 OID 20795)
-- Name: settlement_order_details settlement_order_details_pricing_detail_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pricing_detail_id_fkey FOREIGN KEY (pricing_detail_id) REFERENCES public.pricing_order_details(id);


--
-- TOC entry 4261 (class 2606 OID 20790)
-- Name: settlement_order_details settlement_order_details_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 4262 (class 2606 OID 21004)
-- Name: settlement_order_details settlement_order_details_settlement_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_settlement_order_id_fkey FOREIGN KEY (settlement_order_id) REFERENCES public.settlement_orders(id);


--
-- TOC entry 4263 (class 2606 OID 20901)
-- Name: settlement_orders settlement_orders_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 4264 (class 2606 OID 20906)
-- Name: settlement_orders settlement_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4265 (class 2606 OID 20896)
-- Name: settlement_orders settlement_orders_dealer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_dealer_id_fkey FOREIGN KEY (dealer_id) REFERENCES public.companies(id);


--
-- TOC entry 4266 (class 2606 OID 20891)
-- Name: settlement_orders settlement_orders_distributor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_distributor_id_fkey FOREIGN KEY (distributor_id) REFERENCES public.companies(id);


--
-- TOC entry 4267 (class 2606 OID 20876)
-- Name: settlement_orders settlement_orders_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 4268 (class 2606 OID 20881)
-- Name: settlement_orders settlement_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4269 (class 2606 OID 20886)
-- Name: settlement_orders settlement_orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 4273 (class 2606 OID 28924)
-- Name: settlements settlements_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- TOC entry 4274 (class 2606 OID 28914)
-- Name: settlements settlements_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 4275 (class 2606 OID 28919)
-- Name: settlements settlements_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 4238 (class 2606 OID 20370)
-- Name: solution_manager_email_settings solution_manager_email_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT solution_manager_email_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 4247 (class 2606 OID 20591)
-- Name: system_metrics system_metrics_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 4243 (class 2606 OID 20560)
-- Name: upgrade_logs upgrade_logs_operator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_operator_id_fkey FOREIGN KEY (operator_id) REFERENCES public.users(id);


--
-- TOC entry 4244 (class 2606 OID 20555)
-- Name: upgrade_logs upgrade_logs_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 4227 (class 2606 OID 19981)
-- Name: user_event_subscriptions user_event_subscriptions_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.event_registry(id);


--
-- TOC entry 4228 (class 2606 OID 19976)
-- Name: user_event_subscriptions user_event_subscriptions_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id);


--
-- TOC entry 4229 (class 2606 OID 19971)
-- Name: user_event_subscriptions user_event_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


-- Completed on 2025-06-24 08:29:50 +08

--
-- PostgreSQL database dump complete
--

