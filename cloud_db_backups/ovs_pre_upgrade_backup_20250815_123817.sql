--
-- PostgreSQL database dump
--

\restrict IN9a0T1cfHtKglbquWA5EgtrBLizrxqybzGccgGW22is8ZcXXAi461fgv71wEAH

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.6 (Homebrew)

-- Started on 2025-08-15 12:38:25 +08

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP EVENT TRIGGER IF EXISTS pgrst_drop_watch;
DROP EVENT TRIGGER IF EXISTS pgrst_ddl_watch;
DROP EVENT TRIGGER IF EXISTS issue_pg_net_access;
DROP EVENT TRIGGER IF EXISTS issue_pg_graphql_access;
DROP EVENT TRIGGER IF EXISTS issue_pg_cron_access;
DROP EVENT TRIGGER IF EXISTS issue_graphql_placeholder;
DROP PUBLICATION IF EXISTS supabase_realtime;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads_parts DROP CONSTRAINT IF EXISTS s3_multipart_uploads_parts_upload_id_fkey;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads_parts DROP CONSTRAINT IF EXISTS s3_multipart_uploads_parts_bucket_id_fkey;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads DROP CONSTRAINT IF EXISTS s3_multipart_uploads_bucket_id_fkey;
ALTER TABLE IF EXISTS ONLY storage.objects DROP CONSTRAINT IF EXISTS "objects_bucketId_fkey";
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_target_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_event_id_fkey;
ALTER TABLE IF EXISTS ONLY public.upgrade_logs DROP CONSTRAINT IF EXISTS upgrade_logs_version_id_fkey;
ALTER TABLE IF EXISTS ONLY public.upgrade_logs DROP CONSTRAINT IF EXISTS upgrade_logs_operator_id_fkey;
ALTER TABLE IF EXISTS ONLY public.temp_products DROP CONSTRAINT IF EXISTS temp_products_created_by_fkey;
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
ALTER TABLE IF EXISTS ONLY public.role_performance_items DROP CONSTRAINT IF EXISTS role_performance_items_role_config_id_fkey;
ALTER TABLE IF EXISTS ONLY public.role_performance_items DROP CONSTRAINT IF EXISTS role_performance_items_metric_id_fkey;
ALTER TABLE IF EXISTS ONLY public.role_performance_config DROP CONSTRAINT IF EXISTS role_performance_config_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.role_performance_config DROP CONSTRAINT IF EXISTS role_performance_config_created_by_fkey;
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
ALTER TABLE IF EXISTS ONLY public.formula_templates_extended DROP CONSTRAINT IF EXISTS formula_templates_extended_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.settlement_order_details DROP CONSTRAINT IF EXISTS fk_settlement_order_details_settlement_company;
ALTER TABLE IF EXISTS ONLY public.project_customer_associations DROP CONSTRAINT IF EXISTS fk_project_customer_associations_project_id;
ALTER TABLE IF EXISTS ONLY public.project_customer_associations DROP CONSTRAINT IF EXISTS fk_project_customer_associations_created_by;
ALTER TABLE IF EXISTS ONLY public.project_customer_associations DROP CONSTRAINT IF EXISTS fk_project_customer_associations_company_id;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS fk_expenses_paid_by;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS fk_expenses_contact_id;
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS fk_approval_record_step_id;
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS fk_approval_record_approver_id;
ALTER TABLE IF EXISTS ONLY public.feature_changes DROP CONSTRAINT IF EXISTS feature_changes_version_id_fkey;
ALTER TABLE IF EXISTS ONLY public.feature_changes DROP CONSTRAINT IF EXISTS feature_changes_developer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_customer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_approved_by_fkey;
ALTER TABLE IF EXISTS ONLY public.expense_details DROP CONSTRAINT IF EXISTS expense_details_expense_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_subcategory_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_region_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_product_specs DROP CONSTRAINT IF EXISTS dev_product_specs_dev_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.departments DROP CONSTRAINT IF EXISTS departments_parent_id_fkey;
ALTER TABLE IF EXISTS ONLY public.departments DROP CONSTRAINT IF EXISTS departments_manager_id_fkey;
ALTER TABLE IF EXISTS ONLY public.data_table_config DROP CONSTRAINT IF EXISTS data_table_config_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.data_table_config DROP CONSTRAINT IF EXISTS data_table_config_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.data_field_config DROP CONSTRAINT IF EXISTS data_field_config_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.data_field_config DROP CONSTRAINT IF EXISTS data_field_config_table_config_id_fkey;
ALTER TABLE IF EXISTS ONLY public.data_field_config DROP CONSTRAINT IF EXISTS data_field_config_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.contacts DROP CONSTRAINT IF EXISTS contacts_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.contacts DROP CONSTRAINT IF EXISTS contacts_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.company_assets DROP CONSTRAINT IF EXISTS company_assets_created_by_id_fkey;
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
ALTER TABLE IF EXISTS ONLY auth.sso_domains DROP CONSTRAINT IF EXISTS sso_domains_sso_provider_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.sessions DROP CONSTRAINT IF EXISTS sessions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.saml_relay_states DROP CONSTRAINT IF EXISTS saml_relay_states_sso_provider_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.saml_relay_states DROP CONSTRAINT IF EXISTS saml_relay_states_flow_state_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.saml_providers DROP CONSTRAINT IF EXISTS saml_providers_sso_provider_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_session_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.one_time_tokens DROP CONSTRAINT IF EXISTS one_time_tokens_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_factors DROP CONSTRAINT IF EXISTS mfa_factors_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_challenges DROP CONSTRAINT IF EXISTS mfa_challenges_auth_factor_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_amr_claims DROP CONSTRAINT IF EXISTS mfa_amr_claims_session_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.identities DROP CONSTRAINT IF EXISTS identities_user_id_fkey;
DROP TRIGGER IF EXISTS update_objects_updated_at ON storage.objects;
DROP TRIGGER IF EXISTS tr_check_filters ON realtime.subscription;
DROP INDEX IF EXISTS storage.name_prefix_search;
DROP INDEX IF EXISTS storage.idx_objects_bucket_id_name;
DROP INDEX IF EXISTS storage.idx_multipart_uploads_list;
DROP INDEX IF EXISTS storage.bucketid_objname;
DROP INDEX IF EXISTS storage.bname;
DROP INDEX IF EXISTS realtime.subscription_subscription_id_entity_filters_key;
DROP INDEX IF EXISTS realtime.ix_realtime_subscription_entity;
DROP INDEX IF EXISTS public.ix_system_settings_key;
DROP INDEX IF EXISTS public.ix_role_performance_config_role;
DROP INDEX IF EXISTS public.ix_role_performance_access_role;
DROP INDEX IF EXISTS public.ix_projects_project_name;
DROP INDEX IF EXISTS public.ix_projects_authorization_code;
DROP INDEX IF EXISTS public.ix_project_stage_history_project_id;
DROP INDEX IF EXISTS public.ix_performance_metrics_definition_metric_code;
DROP INDEX IF EXISTS public.ix_expenses_expense_number;
DROP INDEX IF EXISTS public.idx_temp_product_usage;
DROP INDEX IF EXISTS public.idx_temp_product_model_creator;
DROP INDEX IF EXISTS public.idx_temp_product_deleted;
DROP INDEX IF EXISTS public.idx_temp_product_creator;
DROP INDEX IF EXISTS public.idx_temp_product_category;
DROP INDEX IF EXISTS public.idx_role_items_metric;
DROP INDEX IF EXISTS public.idx_role_items_config;
DROP INDEX IF EXISTS public.idx_role_access;
DROP INDEX IF EXISTS public.idx_quotations_updated_at;
DROP INDEX IF EXISTS public.idx_quotations_project_owner;
DROP INDEX IF EXISTS public.idx_quotations_project_id;
DROP INDEX IF EXISTS public.idx_quotations_owner_id;
DROP INDEX IF EXISTS public.idx_quotations_created_at;
DROP INDEX IF EXISTS public.idx_quotations_amount;
DROP INDEX IF EXISTS public.idx_projects_vendor_sales_manager;
DROP INDEX IF EXISTS public.idx_projects_type_stage;
DROP INDEX IF EXISTS public.idx_projects_project_type;
DROP INDEX IF EXISTS public.idx_projects_owner_id;
DROP INDEX IF EXISTS public.idx_projects_current_stage;
DROP INDEX IF EXISTS public.idx_project_customer_associations_project_id;
DROP INDEX IF EXISTS public.idx_project_customer_associations_created_by;
DROP INDEX IF EXISTS public.idx_project_customer_associations_company_id;
DROP INDEX IF EXISTS public.idx_expenses_currency;
DROP INDEX IF EXISTS public.idx_expense_details_expense_currency;
DROP INDEX IF EXISTS public.idx_expense_details_currency;
DROP INDEX IF EXISTS auth.users_is_anonymous_idx;
DROP INDEX IF EXISTS auth.users_instance_id_idx;
DROP INDEX IF EXISTS auth.users_instance_id_email_idx;
DROP INDEX IF EXISTS auth.users_email_partial_key;
DROP INDEX IF EXISTS auth.user_id_created_at_idx;
DROP INDEX IF EXISTS auth.unique_phone_factor_per_user;
DROP INDEX IF EXISTS auth.sso_providers_resource_id_idx;
DROP INDEX IF EXISTS auth.sso_domains_sso_provider_id_idx;
DROP INDEX IF EXISTS auth.sso_domains_domain_idx;
DROP INDEX IF EXISTS auth.sessions_user_id_idx;
DROP INDEX IF EXISTS auth.sessions_not_after_idx;
DROP INDEX IF EXISTS auth.saml_relay_states_sso_provider_id_idx;
DROP INDEX IF EXISTS auth.saml_relay_states_for_email_idx;
DROP INDEX IF EXISTS auth.saml_relay_states_created_at_idx;
DROP INDEX IF EXISTS auth.saml_providers_sso_provider_id_idx;
DROP INDEX IF EXISTS auth.refresh_tokens_updated_at_idx;
DROP INDEX IF EXISTS auth.refresh_tokens_session_id_revoked_idx;
DROP INDEX IF EXISTS auth.refresh_tokens_parent_idx;
DROP INDEX IF EXISTS auth.refresh_tokens_instance_id_user_id_idx;
DROP INDEX IF EXISTS auth.refresh_tokens_instance_id_idx;
DROP INDEX IF EXISTS auth.recovery_token_idx;
DROP INDEX IF EXISTS auth.reauthentication_token_idx;
DROP INDEX IF EXISTS auth.one_time_tokens_user_id_token_type_key;
DROP INDEX IF EXISTS auth.one_time_tokens_token_hash_hash_idx;
DROP INDEX IF EXISTS auth.one_time_tokens_relates_to_hash_idx;
DROP INDEX IF EXISTS auth.mfa_factors_user_id_idx;
DROP INDEX IF EXISTS auth.mfa_factors_user_friendly_name_unique;
DROP INDEX IF EXISTS auth.mfa_challenge_created_at_idx;
DROP INDEX IF EXISTS auth.idx_user_id_auth_method;
DROP INDEX IF EXISTS auth.idx_auth_code;
DROP INDEX IF EXISTS auth.identities_user_id_idx;
DROP INDEX IF EXISTS auth.identities_email_idx;
DROP INDEX IF EXISTS auth.flow_state_created_at_idx;
DROP INDEX IF EXISTS auth.factor_id_created_at_idx;
DROP INDEX IF EXISTS auth.email_change_token_new_idx;
DROP INDEX IF EXISTS auth.email_change_token_current_idx;
DROP INDEX IF EXISTS auth.confirmation_token_idx;
DROP INDEX IF EXISTS auth.audit_logs_instance_id_idx;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads DROP CONSTRAINT IF EXISTS s3_multipart_uploads_pkey;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads_parts DROP CONSTRAINT IF EXISTS s3_multipart_uploads_parts_pkey;
ALTER TABLE IF EXISTS ONLY storage.objects DROP CONSTRAINT IF EXISTS objects_pkey;
ALTER TABLE IF EXISTS ONLY storage.migrations DROP CONSTRAINT IF EXISTS migrations_pkey;
ALTER TABLE IF EXISTS ONLY storage.migrations DROP CONSTRAINT IF EXISTS migrations_name_key;
ALTER TABLE IF EXISTS ONLY storage.buckets DROP CONSTRAINT IF EXISTS buckets_pkey;
ALTER TABLE IF EXISTS ONLY realtime.schema_migrations DROP CONSTRAINT IF EXISTS schema_migrations_pkey;
ALTER TABLE IF EXISTS ONLY realtime.subscription DROP CONSTRAINT IF EXISTS pk_subscription;
ALTER TABLE IF EXISTS ONLY realtime.messages DROP CONSTRAINT IF EXISTS messages_pkey;
ALTER TABLE IF EXISTS ONLY public.version_records DROP CONSTRAINT IF EXISTS version_records_version_number_key;
ALTER TABLE IF EXISTS ONLY public.version_records DROP CONSTRAINT IF EXISTS version_records_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_wechat_openid_key;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_username_key;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_email_key;
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_pkey;
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS uq_user_target_event;
ALTER TABLE IF EXISTS ONLY public.data_field_config DROP CONSTRAINT IF EXISTS uq_table_field;
ALTER TABLE IF EXISTS ONLY public.product_subcategories DROP CONSTRAINT IF EXISTS uq_subcategory_code_letter;
ALTER TABLE IF EXISTS ONLY public.solution_manager_email_settings DROP CONSTRAINT IF EXISTS uq_solution_manager_email_user;
ALTER TABLE IF EXISTS ONLY public.project_scoring_records DROP CONSTRAINT IF EXISTS uq_scoring_record;
ALTER TABLE IF EXISTS ONLY public.project_scoring_config DROP CONSTRAINT IF EXISTS uq_scoring_config;
ALTER TABLE IF EXISTS ONLY public.role_performance_items DROP CONSTRAINT IF EXISTS uq_role_item_code;
ALTER TABLE IF EXISTS ONLY public.role_performance_access DROP CONSTRAINT IF EXISTS uq_role_access_scope;
ALTER TABLE IF EXISTS ONLY public.project_rating_records DROP CONSTRAINT IF EXISTS uq_project_user_rating;
ALTER TABLE IF EXISTS ONLY public.project_customer_associations DROP CONSTRAINT IF EXISTS uq_project_company_customer_type;
ALTER TABLE IF EXISTS ONLY public.upgrade_logs DROP CONSTRAINT IF EXISTS upgrade_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS unique_company_product_inventory;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS uix_user_module;
ALTER TABLE IF EXISTS ONLY public.dictionaries DROP CONSTRAINT IF EXISTS uix_type_key;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS uix_role_module;
ALTER TABLE IF EXISTS ONLY public.affiliations DROP CONSTRAINT IF EXISTS uix_owner_viewer;
ALTER TABLE IF EXISTS ONLY public.temp_products DROP CONSTRAINT IF EXISTS temp_products_pkey;
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
ALTER TABLE IF EXISTS ONLY public.role_performance_items DROP CONSTRAINT IF EXISTS role_performance_items_pkey;
ALTER TABLE IF EXISTS ONLY public.role_performance_config DROP CONSTRAINT IF EXISTS role_performance_config_pkey;
ALTER TABLE IF EXISTS ONLY public.role_performance_access DROP CONSTRAINT IF EXISTS role_performance_access_pkey;
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
ALTER TABLE IF EXISTS ONLY public.project_customer_associations DROP CONSTRAINT IF EXISTS project_customer_associations_pkey;
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
ALTER TABLE IF EXISTS ONLY public.performance_targets DROP CONSTRAINT IF EXISTS performance_targets_pkey;
ALTER TABLE IF EXISTS ONLY public.performance_statistics DROP CONSTRAINT IF EXISTS performance_statistics_pkey;
ALTER TABLE IF EXISTS ONLY public.performance_metrics_definition DROP CONSTRAINT IF EXISTS performance_metrics_definition_pkey;
ALTER TABLE IF EXISTS ONLY public.performance_formula_templates DROP CONSTRAINT IF EXISTS performance_formula_templates_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_pkey;
ALTER TABLE IF EXISTS ONLY public.formula_templates_extended DROP CONSTRAINT IF EXISTS formula_templates_extended_pkey;
ALTER TABLE IF EXISTS ONLY public.five_star_project_baselines DROP CONSTRAINT IF EXISTS five_star_project_baselines_pkey;
ALTER TABLE IF EXISTS ONLY public.feature_changes DROP CONSTRAINT IF EXISTS feature_changes_pkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_pkey;
ALTER TABLE IF EXISTS ONLY public.expense_details DROP CONSTRAINT IF EXISTS expense_details_pkey;
ALTER TABLE IF EXISTS ONLY public.event_registry DROP CONSTRAINT IF EXISTS event_registry_pkey;
ALTER TABLE IF EXISTS ONLY public.event_registry DROP CONSTRAINT IF EXISTS event_registry_event_key_key;
ALTER TABLE IF EXISTS ONLY public.dictionaries DROP CONSTRAINT IF EXISTS dictionaries_pkey;
ALTER TABLE IF EXISTS ONLY public.dev_products DROP CONSTRAINT IF EXISTS dev_products_pkey;
ALTER TABLE IF EXISTS ONLY public.dev_product_specs DROP CONSTRAINT IF EXISTS dev_product_specs_pkey;
ALTER TABLE IF EXISTS ONLY public.departments DROP CONSTRAINT IF EXISTS departments_pkey;
ALTER TABLE IF EXISTS ONLY public.departments DROP CONSTRAINT IF EXISTS departments_name_key;
ALTER TABLE IF EXISTS ONLY public.departments DROP CONSTRAINT IF EXISTS departments_code_key;
ALTER TABLE IF EXISTS ONLY public.data_table_config DROP CONSTRAINT IF EXISTS data_table_config_table_name_key;
ALTER TABLE IF EXISTS ONLY public.data_table_config DROP CONSTRAINT IF EXISTS data_table_config_pkey;
ALTER TABLE IF EXISTS ONLY public.data_field_config DROP CONSTRAINT IF EXISTS data_field_config_pkey;
ALTER TABLE IF EXISTS ONLY public.contacts DROP CONSTRAINT IF EXISTS contacts_pkey;
ALTER TABLE IF EXISTS ONLY public.company_assets DROP CONSTRAINT IF EXISTS company_assets_pkey;
ALTER TABLE IF EXISTS ONLY public.company_assets DROP CONSTRAINT IF EXISTS company_assets_asset_key_key;
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
ALTER TABLE IF EXISTS ONLY auth.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY auth.users DROP CONSTRAINT IF EXISTS users_phone_key;
ALTER TABLE IF EXISTS ONLY auth.sso_providers DROP CONSTRAINT IF EXISTS sso_providers_pkey;
ALTER TABLE IF EXISTS ONLY auth.sso_domains DROP CONSTRAINT IF EXISTS sso_domains_pkey;
ALTER TABLE IF EXISTS ONLY auth.sessions DROP CONSTRAINT IF EXISTS sessions_pkey;
ALTER TABLE IF EXISTS ONLY auth.schema_migrations DROP CONSTRAINT IF EXISTS schema_migrations_pkey;
ALTER TABLE IF EXISTS ONLY auth.saml_relay_states DROP CONSTRAINT IF EXISTS saml_relay_states_pkey;
ALTER TABLE IF EXISTS ONLY auth.saml_providers DROP CONSTRAINT IF EXISTS saml_providers_pkey;
ALTER TABLE IF EXISTS ONLY auth.saml_providers DROP CONSTRAINT IF EXISTS saml_providers_entity_id_key;
ALTER TABLE IF EXISTS ONLY auth.refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_token_unique;
ALTER TABLE IF EXISTS ONLY auth.refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_pkey;
ALTER TABLE IF EXISTS ONLY auth.one_time_tokens DROP CONSTRAINT IF EXISTS one_time_tokens_pkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_factors DROP CONSTRAINT IF EXISTS mfa_factors_pkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_factors DROP CONSTRAINT IF EXISTS mfa_factors_last_challenged_at_key;
ALTER TABLE IF EXISTS ONLY auth.mfa_challenges DROP CONSTRAINT IF EXISTS mfa_challenges_pkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_amr_claims DROP CONSTRAINT IF EXISTS mfa_amr_claims_session_id_authentication_method_pkey;
ALTER TABLE IF EXISTS ONLY auth.instances DROP CONSTRAINT IF EXISTS instances_pkey;
ALTER TABLE IF EXISTS ONLY auth.identities DROP CONSTRAINT IF EXISTS identities_provider_id_provider_unique;
ALTER TABLE IF EXISTS ONLY auth.identities DROP CONSTRAINT IF EXISTS identities_pkey;
ALTER TABLE IF EXISTS ONLY auth.flow_state DROP CONSTRAINT IF EXISTS flow_state_pkey;
ALTER TABLE IF EXISTS ONLY auth.audit_log_entries DROP CONSTRAINT IF EXISTS audit_log_entries_pkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_amr_claims DROP CONSTRAINT IF EXISTS amr_id_pk;
ALTER TABLE IF EXISTS public.version_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.user_event_subscriptions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.upgrade_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.temp_products ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.system_settings ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.system_metrics ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.solution_manager_email_settings ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.settlements ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.settlement_orders ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.settlement_order_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.settlement_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.role_permissions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.role_performance_items ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.role_performance_config ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.role_performance_access ALTER COLUMN id DROP DEFAULT;
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
ALTER TABLE IF EXISTS public.project_customer_associations ALTER COLUMN id DROP DEFAULT;
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
ALTER TABLE IF EXISTS public.performance_targets ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.performance_statistics ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.performance_metrics_definition ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.performance_formula_templates ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.inventory_transactions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.inventory ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.formula_templates_extended ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.five_star_project_baselines ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.feature_changes ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.expenses ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.expense_details ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.event_registry ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dictionaries ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dev_products ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dev_product_specs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.departments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.data_table_config ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.data_field_config ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.contacts ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.company_assets ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.companies ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.change_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_step ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_process_template ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_instance ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.affiliations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.actions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.action_reply ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS auth.refresh_tokens ALTER COLUMN id DROP DEFAULT;
DROP TABLE IF EXISTS storage.s3_multipart_uploads_parts;
DROP TABLE IF EXISTS storage.s3_multipart_uploads;
DROP TABLE IF EXISTS storage.objects;
DROP TABLE IF EXISTS storage.migrations;
DROP TABLE IF EXISTS storage.buckets;
DROP TABLE IF EXISTS realtime.subscription;
DROP TABLE IF EXISTS realtime.schema_migrations;
DROP TABLE IF EXISTS realtime.messages;
DROP SEQUENCE IF EXISTS public.version_records_id_seq;
DROP TABLE IF EXISTS public.version_records;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.user_event_subscriptions_id_seq;
DROP TABLE IF EXISTS public.user_event_subscriptions;
DROP SEQUENCE IF EXISTS public.upgrade_logs_id_seq;
DROP TABLE IF EXISTS public.upgrade_logs;
DROP SEQUENCE IF EXISTS public.temp_products_id_seq;
DROP TABLE IF EXISTS public.temp_products;
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
DROP SEQUENCE IF EXISTS public.role_performance_items_id_seq;
DROP TABLE IF EXISTS public.role_performance_items;
DROP SEQUENCE IF EXISTS public.role_performance_config_id_seq;
DROP TABLE IF EXISTS public.role_performance_config;
DROP SEQUENCE IF EXISTS public.role_performance_access_id_seq;
DROP TABLE IF EXISTS public.role_performance_access;
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
DROP SEQUENCE IF EXISTS public.project_customer_associations_id_seq;
DROP TABLE IF EXISTS public.project_customer_associations;
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
DROP SEQUENCE IF EXISTS public.performance_targets_id_seq;
DROP TABLE IF EXISTS public.performance_targets;
DROP SEQUENCE IF EXISTS public.performance_statistics_id_seq;
DROP TABLE IF EXISTS public.performance_statistics;
DROP SEQUENCE IF EXISTS public.performance_metrics_definition_id_seq;
DROP TABLE IF EXISTS public.performance_metrics_definition;
DROP SEQUENCE IF EXISTS public.performance_formula_templates_id_seq;
DROP TABLE IF EXISTS public.performance_formula_templates;
DROP SEQUENCE IF EXISTS public.inventory_transactions_id_seq;
DROP TABLE IF EXISTS public.inventory_transactions;
DROP SEQUENCE IF EXISTS public.inventory_id_seq;
DROP TABLE IF EXISTS public.inventory;
DROP SEQUENCE IF EXISTS public.formula_templates_extended_id_seq;
DROP TABLE IF EXISTS public.formula_templates_extended;
DROP SEQUENCE IF EXISTS public.five_star_project_baselines_id_seq;
DROP TABLE IF EXISTS public.five_star_project_baselines;
DROP SEQUENCE IF EXISTS public.feature_changes_id_seq;
DROP TABLE IF EXISTS public.feature_changes;
DROP SEQUENCE IF EXISTS public.expenses_id_seq;
DROP TABLE IF EXISTS public.expenses;
DROP SEQUENCE IF EXISTS public.expense_details_id_seq;
DROP TABLE IF EXISTS public.expense_details;
DROP SEQUENCE IF EXISTS public.event_registry_id_seq;
DROP TABLE IF EXISTS public.event_registry;
DROP SEQUENCE IF EXISTS public.dictionaries_id_seq;
DROP TABLE IF EXISTS public.dictionaries;
DROP SEQUENCE IF EXISTS public.dev_products_id_seq;
DROP TABLE IF EXISTS public.dev_products;
DROP SEQUENCE IF EXISTS public.dev_product_specs_id_seq;
DROP TABLE IF EXISTS public.dev_product_specs;
DROP SEQUENCE IF EXISTS public.departments_id_seq;
DROP TABLE IF EXISTS public.departments;
DROP SEQUENCE IF EXISTS public.data_table_config_id_seq;
DROP TABLE IF EXISTS public.data_table_config;
DROP SEQUENCE IF EXISTS public.data_field_config_id_seq;
DROP TABLE IF EXISTS public.data_field_config;
DROP SEQUENCE IF EXISTS public.contacts_id_seq;
DROP TABLE IF EXISTS public.contacts;
DROP SEQUENCE IF EXISTS public.company_assets_id_seq;
DROP TABLE IF EXISTS public.company_assets;
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
DROP TABLE IF EXISTS auth.users;
DROP TABLE IF EXISTS auth.sso_providers;
DROP TABLE IF EXISTS auth.sso_domains;
DROP TABLE IF EXISTS auth.sessions;
DROP TABLE IF EXISTS auth.schema_migrations;
DROP TABLE IF EXISTS auth.saml_relay_states;
DROP TABLE IF EXISTS auth.saml_providers;
DROP SEQUENCE IF EXISTS auth.refresh_tokens_id_seq;
DROP TABLE IF EXISTS auth.refresh_tokens;
DROP TABLE IF EXISTS auth.one_time_tokens;
DROP TABLE IF EXISTS auth.mfa_factors;
DROP TABLE IF EXISTS auth.mfa_challenges;
DROP TABLE IF EXISTS auth.mfa_amr_claims;
DROP TABLE IF EXISTS auth.instances;
DROP TABLE IF EXISTS auth.identities;
DROP TABLE IF EXISTS auth.flow_state;
DROP TABLE IF EXISTS auth.audit_log_entries;
DROP FUNCTION IF EXISTS storage.update_updated_at_column();
DROP FUNCTION IF EXISTS storage.search(prefix text, bucketname text, limits integer, levels integer, offsets integer, search text, sortcolumn text, sortorder text);
DROP FUNCTION IF EXISTS storage.operation();
DROP FUNCTION IF EXISTS storage.list_objects_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer, start_after text, next_token text);
DROP FUNCTION IF EXISTS storage.list_multipart_uploads_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer, next_key_token text, next_upload_token text);
DROP FUNCTION IF EXISTS storage.get_size_by_bucket();
DROP FUNCTION IF EXISTS storage.foldername(name text);
DROP FUNCTION IF EXISTS storage.filename(name text);
DROP FUNCTION IF EXISTS storage.extension(name text);
DROP FUNCTION IF EXISTS storage.can_insert_object(bucketid text, name text, owner uuid, metadata jsonb);
DROP FUNCTION IF EXISTS realtime.topic();
DROP FUNCTION IF EXISTS realtime.to_regrole(role_name text);
DROP FUNCTION IF EXISTS realtime.subscription_check_filters();
DROP FUNCTION IF EXISTS realtime.send(payload jsonb, event text, topic text, private boolean);
DROP FUNCTION IF EXISTS realtime.quote_wal2json(entity regclass);
DROP FUNCTION IF EXISTS realtime.list_changes(publication name, slot_name name, max_changes integer, max_record_bytes integer);
DROP FUNCTION IF EXISTS realtime.is_visible_through_filters(columns realtime.wal_column[], filters realtime.user_defined_filter[]);
DROP FUNCTION IF EXISTS realtime.check_equality_op(op realtime.equality_op, type_ regtype, val_1 text, val_2 text);
DROP FUNCTION IF EXISTS realtime."cast"(val text, type_ regtype);
DROP FUNCTION IF EXISTS realtime.build_prepared_statement_sql(prepared_statement_name text, entity regclass, columns realtime.wal_column[]);
DROP FUNCTION IF EXISTS realtime.broadcast_changes(topic_name text, event_name text, operation text, table_name text, table_schema text, new record, old record, level text);
DROP FUNCTION IF EXISTS realtime.apply_rls(wal jsonb, max_record_bytes integer);
DROP FUNCTION IF EXISTS pgbouncer.get_auth(p_usename text);
DROP FUNCTION IF EXISTS extensions.set_graphql_placeholder();
DROP FUNCTION IF EXISTS extensions.pgrst_drop_watch();
DROP FUNCTION IF EXISTS extensions.pgrst_ddl_watch();
DROP FUNCTION IF EXISTS extensions.grant_pg_net_access();
DROP FUNCTION IF EXISTS extensions.grant_pg_graphql_access();
DROP FUNCTION IF EXISTS extensions.grant_pg_cron_access();
DROP FUNCTION IF EXISTS auth.uid();
DROP FUNCTION IF EXISTS auth.role();
DROP FUNCTION IF EXISTS auth.jwt();
DROP FUNCTION IF EXISTS auth.email();
DROP TYPE IF EXISTS realtime.wal_rls;
DROP TYPE IF EXISTS realtime.wal_column;
DROP TYPE IF EXISTS realtime.user_defined_filter;
DROP TYPE IF EXISTS realtime.equality_op;
DROP TYPE IF EXISTS realtime.action;
DROP TYPE IF EXISTS public.settlementorderstatus;
DROP TYPE IF EXISTS public.pricingorderstatus;
DROP TYPE IF EXISTS public.pricingorderapprovalflowtype;
DROP TYPE IF EXISTS public.approvalstatus;
DROP TYPE IF EXISTS public.approvalinstancestatus;
DROP TYPE IF EXISTS public.approvalaction;
DROP TYPE IF EXISTS public.approval_status;
DROP TYPE IF EXISTS public.approval_action;
DROP TYPE IF EXISTS auth.one_time_token_type;
DROP TYPE IF EXISTS auth.factor_type;
DROP TYPE IF EXISTS auth.factor_status;
DROP TYPE IF EXISTS auth.code_challenge_method;
DROP TYPE IF EXISTS auth.aal_level;
DROP EXTENSION IF EXISTS "uuid-ossp";
DROP EXTENSION IF EXISTS supabase_vault;
DROP EXTENSION IF EXISTS pgcrypto;
DROP EXTENSION IF EXISTS pg_stat_statements;
DROP EXTENSION IF EXISTS pg_graphql;
DROP SCHEMA IF EXISTS vault;
DROP SCHEMA IF EXISTS storage;
DROP SCHEMA IF EXISTS realtime;
DROP SCHEMA IF EXISTS pgbouncer;
DROP SCHEMA IF EXISTS graphql_public;
DROP SCHEMA IF EXISTS graphql;
DROP SCHEMA IF EXISTS extensions;
DROP SCHEMA IF EXISTS auth;
--
-- TOC entry 19 (class 2615 OID 16492)
-- Name: auth; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA auth;


--
-- TOC entry 13 (class 2615 OID 16388)
-- Name: extensions; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA extensions;


--
-- TOC entry 17 (class 2615 OID 16622)
-- Name: graphql; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA graphql;


--
-- TOC entry 16 (class 2615 OID 16611)
-- Name: graphql_public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA graphql_public;


--
-- TOC entry 11 (class 2615 OID 16386)
-- Name: pgbouncer; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA pgbouncer;


--
-- TOC entry 9 (class 2615 OID 16603)
-- Name: realtime; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA realtime;


--
-- TOC entry 20 (class 2615 OID 16540)
-- Name: storage; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA storage;


--
-- TOC entry 14 (class 2615 OID 16651)
-- Name: vault; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA vault;


--
-- TOC entry 6 (class 3079 OID 16687)
-- Name: pg_graphql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_graphql WITH SCHEMA graphql;


--
-- TOC entry 4890 (class 0 OID 0)
-- Dependencies: 6
-- Name: EXTENSION pg_graphql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_graphql IS 'pg_graphql: GraphQL support';


--
-- TOC entry 2 (class 3079 OID 16389)
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA extensions;


--
-- TOC entry 4891 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


--
-- TOC entry 4 (class 3079 OID 16441)
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;


--
-- TOC entry 4892 (class 0 OID 0)
-- Dependencies: 4
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- TOC entry 5 (class 3079 OID 16652)
-- Name: supabase_vault; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS supabase_vault WITH SCHEMA vault;


--
-- TOC entry 4893 (class 0 OID 0)
-- Dependencies: 5
-- Name: EXTENSION supabase_vault; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION supabase_vault IS 'Supabase Vault Extension';


--
-- TOC entry 3 (class 3079 OID 16430)
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;


--
-- TOC entry 4894 (class 0 OID 0)
-- Dependencies: 3
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- TOC entry 1177 (class 1247 OID 16780)
-- Name: aal_level; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.aal_level AS ENUM (
    'aal1',
    'aal2',
    'aal3'
);


--
-- TOC entry 1201 (class 1247 OID 16921)
-- Name: code_challenge_method; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.code_challenge_method AS ENUM (
    's256',
    'plain'
);


--
-- TOC entry 1174 (class 1247 OID 16774)
-- Name: factor_status; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.factor_status AS ENUM (
    'unverified',
    'verified'
);


--
-- TOC entry 1171 (class 1247 OID 16769)
-- Name: factor_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.factor_type AS ENUM (
    'totp',
    'webauthn',
    'phone'
);


--
-- TOC entry 1207 (class 1247 OID 16963)
-- Name: one_time_token_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.one_time_token_type AS ENUM (
    'confirmation_token',
    'reauthentication_token',
    'recovery_token',
    'email_change_token_new',
    'email_change_token_current',
    'phone_change_token'
);


--
-- TOC entry 1243 (class 1247 OID 23925)
-- Name: approval_action; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_action AS ENUM (
    'approve',
    'reject'
);


--
-- TOC entry 1246 (class 1247 OID 23930)
-- Name: approval_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);


--
-- TOC entry 1249 (class 1247 OID 23938)
-- Name: approvalaction; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalaction AS ENUM (
    'approve',
    'reject'
);


--
-- TOC entry 1252 (class 1247 OID 23944)
-- Name: approvalinstancestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalinstancestatus AS ENUM (
    'pending',
    'approved',
    'rejected'
);


--
-- TOC entry 1255 (class 1247 OID 23952)
-- Name: approvalstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalstatus AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED',
    'RECALLED'
);


--
-- TOC entry 1258 (class 1247 OID 23962)
-- Name: pricingorderapprovalflowtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricingorderapprovalflowtype AS ENUM (
    'CHANNEL_FOLLOW',
    'SALES_KEY',
    'SALES_OPPORTUNITY'
);


--
-- TOC entry 1261 (class 1247 OID 23970)
-- Name: pricingorderstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricingorderstatus AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- TOC entry 1264 (class 1247 OID 23980)
-- Name: settlementorderstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.settlementorderstatus AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- TOC entry 1225 (class 1247 OID 17046)
-- Name: action; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.action AS ENUM (
    'INSERT',
    'UPDATE',
    'DELETE',
    'TRUNCATE',
    'ERROR'
);


--
-- TOC entry 1216 (class 1247 OID 17006)
-- Name: equality_op; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.equality_op AS ENUM (
    'eq',
    'neq',
    'lt',
    'lte',
    'gt',
    'gte',
    'in'
);


--
-- TOC entry 1219 (class 1247 OID 17021)
-- Name: user_defined_filter; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.user_defined_filter AS (
	column_name text,
	op realtime.equality_op,
	value text
);


--
-- TOC entry 1231 (class 1247 OID 17088)
-- Name: wal_column; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.wal_column AS (
	name text,
	type_name text,
	type_oid oid,
	value jsonb,
	is_pkey boolean,
	is_selectable boolean
);


--
-- TOC entry 1228 (class 1247 OID 17059)
-- Name: wal_rls; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.wal_rls AS (
	wal jsonb,
	is_rls_enabled boolean,
	subscription_ids uuid[],
	errors text[]
);


--
-- TOC entry 474 (class 1255 OID 16538)
-- Name: email(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.email() RETURNS text
    LANGUAGE sql STABLE
    AS $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.email', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'email')
  )::text
$$;


--
-- TOC entry 4895 (class 0 OID 0)
-- Dependencies: 474
-- Name: FUNCTION email(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.email() IS 'Deprecated. Use auth.jwt() -> ''email'' instead.';


--
-- TOC entry 493 (class 1255 OID 16751)
-- Name: jwt(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.jwt() RETURNS jsonb
    LANGUAGE sql STABLE
    AS $$
  select 
    coalesce(
        nullif(current_setting('request.jwt.claim', true), ''),
        nullif(current_setting('request.jwt.claims', true), '')
    )::jsonb
$$;


--
-- TOC entry 473 (class 1255 OID 16537)
-- Name: role(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.role() RETURNS text
    LANGUAGE sql STABLE
    AS $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.role', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role')
  )::text
$$;


--
-- TOC entry 4896 (class 0 OID 0)
-- Dependencies: 473
-- Name: FUNCTION role(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.role() IS 'Deprecated. Use auth.jwt() -> ''role'' instead.';


--
-- TOC entry 472 (class 1255 OID 16536)
-- Name: uid(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.uid() RETURNS uuid
    LANGUAGE sql STABLE
    AS $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$$;


--
-- TOC entry 4897 (class 0 OID 0)
-- Dependencies: 472
-- Name: FUNCTION uid(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.uid() IS 'Deprecated. Use auth.jwt() -> ''sub'' instead.';


--
-- TOC entry 475 (class 1255 OID 16595)
-- Name: grant_pg_cron_access(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.grant_pg_cron_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF EXISTS (
    SELECT
    FROM pg_event_trigger_ddl_commands() AS ev
    JOIN pg_extension AS ext
    ON ev.objid = ext.oid
    WHERE ext.extname = 'pg_cron'
  )
  THEN
    grant usage on schema cron to postgres with grant option;

    alter default privileges in schema cron grant all on tables to postgres with grant option;
    alter default privileges in schema cron grant all on functions to postgres with grant option;
    alter default privileges in schema cron grant all on sequences to postgres with grant option;

    alter default privileges for user supabase_admin in schema cron grant all
        on sequences to postgres with grant option;
    alter default privileges for user supabase_admin in schema cron grant all
        on tables to postgres with grant option;
    alter default privileges for user supabase_admin in schema cron grant all
        on functions to postgres with grant option;

    grant all privileges on all tables in schema cron to postgres with grant option;
    revoke all on table cron.job from postgres;
    grant select on table cron.job to postgres with grant option;
  END IF;
END;
$$;


--
-- TOC entry 4898 (class 0 OID 0)
-- Dependencies: 475
-- Name: FUNCTION grant_pg_cron_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_cron_access() IS 'Grants access to pg_cron';


--
-- TOC entry 479 (class 1255 OID 16616)
-- Name: grant_pg_graphql_access(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.grant_pg_graphql_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $_$
DECLARE
    func_is_graphql_resolve bool;
BEGIN
    func_is_graphql_resolve = (
        SELECT n.proname = 'resolve'
        FROM pg_event_trigger_ddl_commands() AS ev
        LEFT JOIN pg_catalog.pg_proc AS n
        ON ev.objid = n.oid
    );

    IF func_is_graphql_resolve
    THEN
        -- Update public wrapper to pass all arguments through to the pg_graphql resolve func
        DROP FUNCTION IF EXISTS graphql_public.graphql;
        create or replace function graphql_public.graphql(
            "operationName" text default null,
            query text default null,
            variables jsonb default null,
            extensions jsonb default null
        )
            returns jsonb
            language sql
        as $$
            select graphql.resolve(
                query := query,
                variables := coalesce(variables, '{}'),
                "operationName" := "operationName",
                extensions := extensions
            );
        $$;

        -- This hook executes when `graphql.resolve` is created. That is not necessarily the last
        -- function in the extension so we need to grant permissions on existing entities AND
        -- update default permissions to any others that are created after `graphql.resolve`
        grant usage on schema graphql to postgres, anon, authenticated, service_role;
        grant select on all tables in schema graphql to postgres, anon, authenticated, service_role;
        grant execute on all functions in schema graphql to postgres, anon, authenticated, service_role;
        grant all on all sequences in schema graphql to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on tables to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on functions to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on sequences to postgres, anon, authenticated, service_role;

        -- Allow postgres role to allow granting usage on graphql and graphql_public schemas to custom roles
        grant usage on schema graphql_public to postgres with grant option;
        grant usage on schema graphql to postgres with grant option;
    END IF;

END;
$_$;


--
-- TOC entry 4899 (class 0 OID 0)
-- Dependencies: 479
-- Name: FUNCTION grant_pg_graphql_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_graphql_access() IS 'Grants access to pg_graphql';


--
-- TOC entry 476 (class 1255 OID 16597)
-- Name: grant_pg_net_access(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.grant_pg_net_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_event_trigger_ddl_commands() AS ev
    JOIN pg_extension AS ext
    ON ev.objid = ext.oid
    WHERE ext.extname = 'pg_net'
  )
  THEN
    IF NOT EXISTS (
      SELECT 1
      FROM pg_roles
      WHERE rolname = 'supabase_functions_admin'
    )
    THEN
      CREATE USER supabase_functions_admin NOINHERIT CREATEROLE LOGIN NOREPLICATION;
    END IF;

    GRANT USAGE ON SCHEMA net TO supabase_functions_admin, postgres, anon, authenticated, service_role;

    IF EXISTS (
      SELECT FROM pg_extension
      WHERE extname = 'pg_net'
      -- all versions in use on existing projects as of 2025-02-20
      -- version 0.12.0 onwards don't need these applied
      AND extversion IN ('0.2', '0.6', '0.7', '0.7.1', '0.8', '0.10.0', '0.11.0')
    ) THEN
      ALTER function net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) SECURITY DEFINER;
      ALTER function net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) SECURITY DEFINER;

      ALTER function net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) SET search_path = net;
      ALTER function net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) SET search_path = net;

      REVOKE ALL ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) FROM PUBLIC;
      REVOKE ALL ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) FROM PUBLIC;

      GRANT EXECUTE ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) TO supabase_functions_admin, postgres, anon, authenticated, service_role;
      GRANT EXECUTE ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) TO supabase_functions_admin, postgres, anon, authenticated, service_role;
    END IF;
  END IF;
END;
$$;


--
-- TOC entry 4900 (class 0 OID 0)
-- Dependencies: 476
-- Name: FUNCTION grant_pg_net_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_net_access() IS 'Grants access to pg_net';


--
-- TOC entry 477 (class 1255 OID 16607)
-- Name: pgrst_ddl_watch(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.pgrst_ddl_watch() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN SELECT * FROM pg_event_trigger_ddl_commands()
  LOOP
    IF cmd.command_tag IN (
      'CREATE SCHEMA', 'ALTER SCHEMA'
    , 'CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO', 'ALTER TABLE'
    , 'CREATE FOREIGN TABLE', 'ALTER FOREIGN TABLE'
    , 'CREATE VIEW', 'ALTER VIEW'
    , 'CREATE MATERIALIZED VIEW', 'ALTER MATERIALIZED VIEW'
    , 'CREATE FUNCTION', 'ALTER FUNCTION'
    , 'CREATE TRIGGER'
    , 'CREATE TYPE', 'ALTER TYPE'
    , 'CREATE RULE'
    , 'COMMENT'
    )
    -- don't notify in case of CREATE TEMP table or other objects created on pg_temp
    AND cmd.schema_name is distinct from 'pg_temp'
    THEN
      NOTIFY pgrst, 'reload schema';
    END IF;
  END LOOP;
END; $$;


--
-- TOC entry 478 (class 1255 OID 16608)
-- Name: pgrst_drop_watch(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.pgrst_drop_watch() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  obj record;
BEGIN
  FOR obj IN SELECT * FROM pg_event_trigger_dropped_objects()
  LOOP
    IF obj.object_type IN (
      'schema'
    , 'table'
    , 'foreign table'
    , 'view'
    , 'materialized view'
    , 'function'
    , 'trigger'
    , 'type'
    , 'rule'
    )
    AND obj.is_temporary IS false -- no pg_temp objects
    THEN
      NOTIFY pgrst, 'reload schema';
    END IF;
  END LOOP;
END; $$;


--
-- TOC entry 480 (class 1255 OID 16618)
-- Name: set_graphql_placeholder(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.set_graphql_placeholder() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $_$
    DECLARE
    graphql_is_dropped bool;
    BEGIN
    graphql_is_dropped = (
        SELECT ev.schema_name = 'graphql_public'
        FROM pg_event_trigger_dropped_objects() AS ev
        WHERE ev.schema_name = 'graphql_public'
    );

    IF graphql_is_dropped
    THEN
        create or replace function graphql_public.graphql(
            "operationName" text default null,
            query text default null,
            variables jsonb default null,
            extensions jsonb default null
        )
            returns jsonb
            language plpgsql
        as $$
            DECLARE
                server_version float;
            BEGIN
                server_version = (SELECT (SPLIT_PART((select version()), ' ', 2))::float);

                IF server_version >= 14 THEN
                    RETURN jsonb_build_object(
                        'errors', jsonb_build_array(
                            jsonb_build_object(
                                'message', 'pg_graphql extension is not enabled.'
                            )
                        )
                    );
                ELSE
                    RETURN jsonb_build_object(
                        'errors', jsonb_build_array(
                            jsonb_build_object(
                                'message', 'pg_graphql is only available on projects running Postgres 14 onwards.'
                            )
                        )
                    );
                END IF;
            END;
        $$;
    END IF;

    END;
$_$;


--
-- TOC entry 4901 (class 0 OID 0)
-- Dependencies: 480
-- Name: FUNCTION set_graphql_placeholder(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.set_graphql_placeholder() IS 'Reintroduces placeholder function for graphql_public.graphql';


--
-- TOC entry 422 (class 1255 OID 16387)
-- Name: get_auth(text); Type: FUNCTION; Schema: pgbouncer; Owner: -
--

CREATE FUNCTION pgbouncer.get_auth(p_usename text) RETURNS TABLE(username text, password text)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $_$
begin
    raise debug 'PgBouncer auth request: %', p_usename;

    return query
    select 
        rolname::text, 
        case when rolvaliduntil < now() 
            then null 
            else rolpassword::text 
        end 
    from pg_authid 
    where rolname=$1 and rolcanlogin;
end;
$_$;


--
-- TOC entry 499 (class 1255 OID 17081)
-- Name: apply_rls(jsonb, integer); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.apply_rls(wal jsonb, max_record_bytes integer DEFAULT (1024 * 1024)) RETURNS SETOF realtime.wal_rls
    LANGUAGE plpgsql
    AS $$
declare
-- Regclass of the table e.g. public.notes
entity_ regclass = (quote_ident(wal ->> 'schema') || '.' || quote_ident(wal ->> 'table'))::regclass;

-- I, U, D, T: insert, update ...
action realtime.action = (
    case wal ->> 'action'
        when 'I' then 'INSERT'
        when 'U' then 'UPDATE'
        when 'D' then 'DELETE'
        else 'ERROR'
    end
);

-- Is row level security enabled for the table
is_rls_enabled bool = relrowsecurity from pg_class where oid = entity_;

subscriptions realtime.subscription[] = array_agg(subs)
    from
        realtime.subscription subs
    where
        subs.entity = entity_;

-- Subscription vars
roles regrole[] = array_agg(distinct us.claims_role::text)
    from
        unnest(subscriptions) us;

working_role regrole;
claimed_role regrole;
claims jsonb;

subscription_id uuid;
subscription_has_access bool;
visible_to_subscription_ids uuid[] = '{}';

-- structured info for wal's columns
columns realtime.wal_column[];
-- previous identity values for update/delete
old_columns realtime.wal_column[];

error_record_exceeds_max_size boolean = octet_length(wal::text) > max_record_bytes;

-- Primary jsonb output for record
output jsonb;

begin
perform set_config('role', null, true);

columns =
    array_agg(
        (
            x->>'name',
            x->>'type',
            x->>'typeoid',
            realtime.cast(
                (x->'value') #>> '{}',
                coalesce(
                    (x->>'typeoid')::regtype, -- null when wal2json version <= 2.4
                    (x->>'type')::regtype
                )
            ),
            (pks ->> 'name') is not null,
            true
        )::realtime.wal_column
    )
    from
        jsonb_array_elements(wal -> 'columns') x
        left join jsonb_array_elements(wal -> 'pk') pks
            on (x ->> 'name') = (pks ->> 'name');

old_columns =
    array_agg(
        (
            x->>'name',
            x->>'type',
            x->>'typeoid',
            realtime.cast(
                (x->'value') #>> '{}',
                coalesce(
                    (x->>'typeoid')::regtype, -- null when wal2json version <= 2.4
                    (x->>'type')::regtype
                )
            ),
            (pks ->> 'name') is not null,
            true
        )::realtime.wal_column
    )
    from
        jsonb_array_elements(wal -> 'identity') x
        left join jsonb_array_elements(wal -> 'pk') pks
            on (x ->> 'name') = (pks ->> 'name');

for working_role in select * from unnest(roles) loop

    -- Update `is_selectable` for columns and old_columns
    columns =
        array_agg(
            (
                c.name,
                c.type_name,
                c.type_oid,
                c.value,
                c.is_pkey,
                pg_catalog.has_column_privilege(working_role, entity_, c.name, 'SELECT')
            )::realtime.wal_column
        )
        from
            unnest(columns) c;

    old_columns =
            array_agg(
                (
                    c.name,
                    c.type_name,
                    c.type_oid,
                    c.value,
                    c.is_pkey,
                    pg_catalog.has_column_privilege(working_role, entity_, c.name, 'SELECT')
                )::realtime.wal_column
            )
            from
                unnest(old_columns) c;

    if action <> 'DELETE' and count(1) = 0 from unnest(columns) c where c.is_pkey then
        return next (
            jsonb_build_object(
                'schema', wal ->> 'schema',
                'table', wal ->> 'table',
                'type', action
            ),
            is_rls_enabled,
            -- subscriptions is already filtered by entity
            (select array_agg(s.subscription_id) from unnest(subscriptions) as s where claims_role = working_role),
            array['Error 400: Bad Request, no primary key']
        )::realtime.wal_rls;

    -- The claims role does not have SELECT permission to the primary key of entity
    elsif action <> 'DELETE' and sum(c.is_selectable::int) <> count(1) from unnest(columns) c where c.is_pkey then
        return next (
            jsonb_build_object(
                'schema', wal ->> 'schema',
                'table', wal ->> 'table',
                'type', action
            ),
            is_rls_enabled,
            (select array_agg(s.subscription_id) from unnest(subscriptions) as s where claims_role = working_role),
            array['Error 401: Unauthorized']
        )::realtime.wal_rls;

    else
        output = jsonb_build_object(
            'schema', wal ->> 'schema',
            'table', wal ->> 'table',
            'type', action,
            'commit_timestamp', to_char(
                ((wal ->> 'timestamp')::timestamptz at time zone 'utc'),
                'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'
            ),
            'columns', (
                select
                    jsonb_agg(
                        jsonb_build_object(
                            'name', pa.attname,
                            'type', pt.typname
                        )
                        order by pa.attnum asc
                    )
                from
                    pg_attribute pa
                    join pg_type pt
                        on pa.atttypid = pt.oid
                where
                    attrelid = entity_
                    and attnum > 0
                    and pg_catalog.has_column_privilege(working_role, entity_, pa.attname, 'SELECT')
            )
        )
        -- Add "record" key for insert and update
        || case
            when action in ('INSERT', 'UPDATE') then
                jsonb_build_object(
                    'record',
                    (
                        select
                            jsonb_object_agg(
                                -- if unchanged toast, get column name and value from old record
                                coalesce((c).name, (oc).name),
                                case
                                    when (c).name is null then (oc).value
                                    else (c).value
                                end
                            )
                        from
                            unnest(columns) c
                            full outer join unnest(old_columns) oc
                                on (c).name = (oc).name
                        where
                            coalesce((c).is_selectable, (oc).is_selectable)
                            and ( not error_record_exceeds_max_size or (octet_length((c).value::text) <= 64))
                    )
                )
            else '{}'::jsonb
        end
        -- Add "old_record" key for update and delete
        || case
            when action = 'UPDATE' then
                jsonb_build_object(
                        'old_record',
                        (
                            select jsonb_object_agg((c).name, (c).value)
                            from unnest(old_columns) c
                            where
                                (c).is_selectable
                                and ( not error_record_exceeds_max_size or (octet_length((c).value::text) <= 64))
                        )
                    )
            when action = 'DELETE' then
                jsonb_build_object(
                    'old_record',
                    (
                        select jsonb_object_agg((c).name, (c).value)
                        from unnest(old_columns) c
                        where
                            (c).is_selectable
                            and ( not error_record_exceeds_max_size or (octet_length((c).value::text) <= 64))
                            and ( not is_rls_enabled or (c).is_pkey ) -- if RLS enabled, we can't secure deletes so filter to pkey
                    )
                )
            else '{}'::jsonb
        end;

        -- Create the prepared statement
        if is_rls_enabled and action <> 'DELETE' then
            if (select 1 from pg_prepared_statements where name = 'walrus_rls_stmt' limit 1) > 0 then
                deallocate walrus_rls_stmt;
            end if;
            execute realtime.build_prepared_statement_sql('walrus_rls_stmt', entity_, columns);
        end if;

        visible_to_subscription_ids = '{}';

        for subscription_id, claims in (
                select
                    subs.subscription_id,
                    subs.claims
                from
                    unnest(subscriptions) subs
                where
                    subs.entity = entity_
                    and subs.claims_role = working_role
                    and (
                        realtime.is_visible_through_filters(columns, subs.filters)
                        or (
                          action = 'DELETE'
                          and realtime.is_visible_through_filters(old_columns, subs.filters)
                        )
                    )
        ) loop

            if not is_rls_enabled or action = 'DELETE' then
                visible_to_subscription_ids = visible_to_subscription_ids || subscription_id;
            else
                -- Check if RLS allows the role to see the record
                perform
                    -- Trim leading and trailing quotes from working_role because set_config
                    -- doesn't recognize the role as valid if they are included
                    set_config('role', trim(both '"' from working_role::text), true),
                    set_config('request.jwt.claims', claims::text, true);

                execute 'execute walrus_rls_stmt' into subscription_has_access;

                if subscription_has_access then
                    visible_to_subscription_ids = visible_to_subscription_ids || subscription_id;
                end if;
            end if;
        end loop;

        perform set_config('role', null, true);

        return next (
            output,
            is_rls_enabled,
            visible_to_subscription_ids,
            case
                when error_record_exceeds_max_size then array['Error 413: Payload Too Large']
                else '{}'
            end
        )::realtime.wal_rls;

    end if;
end loop;

perform set_config('role', null, true);
end;
$$;


--
-- TOC entry 505 (class 1255 OID 17160)
-- Name: broadcast_changes(text, text, text, text, text, record, record, text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.broadcast_changes(topic_name text, event_name text, operation text, table_name text, table_schema text, new record, old record, level text DEFAULT 'ROW'::text) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    -- Declare a variable to hold the JSONB representation of the row
    row_data jsonb := '{}'::jsonb;
BEGIN
    IF level = 'STATEMENT' THEN
        RAISE EXCEPTION 'function can only be triggered for each row, not for each statement';
    END IF;
    -- Check the operation type and handle accordingly
    IF operation = 'INSERT' OR operation = 'UPDATE' OR operation = 'DELETE' THEN
        row_data := jsonb_build_object('old_record', OLD, 'record', NEW, 'operation', operation, 'table', table_name, 'schema', table_schema);
        PERFORM realtime.send (row_data, event_name, topic_name);
    ELSE
        RAISE EXCEPTION 'Unexpected operation type: %', operation;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Failed to process the row: %', SQLERRM;
END;

$$;


--
-- TOC entry 501 (class 1255 OID 17093)
-- Name: build_prepared_statement_sql(text, regclass, realtime.wal_column[]); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.build_prepared_statement_sql(prepared_statement_name text, entity regclass, columns realtime.wal_column[]) RETURNS text
    LANGUAGE sql
    AS $$
      /*
      Builds a sql string that, if executed, creates a prepared statement to
      tests retrive a row from *entity* by its primary key columns.
      Example
          select realtime.build_prepared_statement_sql('public.notes', '{"id"}'::text[], '{"bigint"}'::text[])
      */
          select
      'prepare ' || prepared_statement_name || ' as
          select
              exists(
                  select
                      1
                  from
                      ' || entity || '
                  where
                      ' || string_agg(quote_ident(pkc.name) || '=' || quote_nullable(pkc.value #>> '{}') , ' and ') || '
              )'
          from
              unnest(columns) pkc
          where
              pkc.is_pkey
          group by
              entity
      $$;


--
-- TOC entry 497 (class 1255 OID 17043)
-- Name: cast(text, regtype); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime."cast"(val text, type_ regtype) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
    declare
      res jsonb;
    begin
      execute format('select to_jsonb(%L::'|| type_::text || ')', val)  into res;
      return res;
    end
    $$;


--
-- TOC entry 496 (class 1255 OID 17038)
-- Name: check_equality_op(realtime.equality_op, regtype, text, text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.check_equality_op(op realtime.equality_op, type_ regtype, val_1 text, val_2 text) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
      /*
      Casts *val_1* and *val_2* as type *type_* and check the *op* condition for truthiness
      */
      declare
          op_symbol text = (
              case
                  when op = 'eq' then '='
                  when op = 'neq' then '!='
                  when op = 'lt' then '<'
                  when op = 'lte' then '<='
                  when op = 'gt' then '>'
                  when op = 'gte' then '>='
                  when op = 'in' then '= any'
                  else 'UNKNOWN OP'
              end
          );
          res boolean;
      begin
          execute format(
              'select %L::'|| type_::text || ' ' || op_symbol
              || ' ( %L::'
              || (
                  case
                      when op = 'in' then type_::text || '[]'
                      else type_::text end
              )
              || ')', val_1, val_2) into res;
          return res;
      end;
      $$;


--
-- TOC entry 500 (class 1255 OID 17089)
-- Name: is_visible_through_filters(realtime.wal_column[], realtime.user_defined_filter[]); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.is_visible_through_filters(columns realtime.wal_column[], filters realtime.user_defined_filter[]) RETURNS boolean
    LANGUAGE sql IMMUTABLE
    AS $_$
    /*
    Should the record be visible (true) or filtered out (false) after *filters* are applied
    */
        select
            -- Default to allowed when no filters present
            $2 is null -- no filters. this should not happen because subscriptions has a default
            or array_length($2, 1) is null -- array length of an empty array is null
            or bool_and(
                coalesce(
                    realtime.check_equality_op(
                        op:=f.op,
                        type_:=coalesce(
                            col.type_oid::regtype, -- null when wal2json version <= 2.4
                            col.type_name::regtype
                        ),
                        -- cast jsonb to text
                        val_1:=col.value #>> '{}',
                        val_2:=f.value
                    ),
                    false -- if null, filter does not match
                )
            )
        from
            unnest(filters) f
            join unnest(columns) col
                on f.column_name = col.name;
    $_$;


--
-- TOC entry 502 (class 1255 OID 17100)
-- Name: list_changes(name, name, integer, integer); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.list_changes(publication name, slot_name name, max_changes integer, max_record_bytes integer) RETURNS SETOF realtime.wal_rls
    LANGUAGE sql
    SET log_min_messages TO 'fatal'
    AS $$
      with pub as (
        select
          concat_ws(
            ',',
            case when bool_or(pubinsert) then 'insert' else null end,
            case when bool_or(pubupdate) then 'update' else null end,
            case when bool_or(pubdelete) then 'delete' else null end
          ) as w2j_actions,
          coalesce(
            string_agg(
              realtime.quote_wal2json(format('%I.%I', schemaname, tablename)::regclass),
              ','
            ) filter (where ppt.tablename is not null and ppt.tablename not like '% %'),
            ''
          ) w2j_add_tables
        from
          pg_publication pp
          left join pg_publication_tables ppt
            on pp.pubname = ppt.pubname
        where
          pp.pubname = publication
        group by
          pp.pubname
        limit 1
      ),
      w2j as (
        select
          x.*, pub.w2j_add_tables
        from
          pub,
          pg_logical_slot_get_changes(
            slot_name, null, max_changes,
            'include-pk', 'true',
            'include-transaction', 'false',
            'include-timestamp', 'true',
            'include-type-oids', 'true',
            'format-version', '2',
            'actions', pub.w2j_actions,
            'add-tables', pub.w2j_add_tables
          ) x
      )
      select
        xyz.wal,
        xyz.is_rls_enabled,
        xyz.subscription_ids,
        xyz.errors
      from
        w2j,
        realtime.apply_rls(
          wal := w2j.data::jsonb,
          max_record_bytes := max_record_bytes
        ) xyz(wal, is_rls_enabled, subscription_ids, errors)
      where
        w2j.w2j_add_tables <> ''
        and xyz.subscription_ids[1] is not null
    $$;


--
-- TOC entry 495 (class 1255 OID 17037)
-- Name: quote_wal2json(regclass); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.quote_wal2json(entity regclass) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT
    AS $$
      select
        (
          select string_agg('' || ch,'')
          from unnest(string_to_array(nsp.nspname::text, null)) with ordinality x(ch, idx)
          where
            not (x.idx = 1 and x.ch = '"')
            and not (
              x.idx = array_length(string_to_array(nsp.nspname::text, null), 1)
              and x.ch = '"'
            )
        )
        || '.'
        || (
          select string_agg('' || ch,'')
          from unnest(string_to_array(pc.relname::text, null)) with ordinality x(ch, idx)
          where
            not (x.idx = 1 and x.ch = '"')
            and not (
              x.idx = array_length(string_to_array(nsp.nspname::text, null), 1)
              and x.ch = '"'
            )
          )
      from
        pg_class pc
        join pg_namespace nsp
          on pc.relnamespace = nsp.oid
      where
        pc.oid = entity
    $$;


--
-- TOC entry 504 (class 1255 OID 17159)
-- Name: send(jsonb, text, text, boolean); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.send(payload jsonb, event text, topic text, private boolean DEFAULT true) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  BEGIN
    -- Set the topic configuration
    EXECUTE format('SET LOCAL realtime.topic TO %L', topic);

    -- Attempt to insert the message
    INSERT INTO realtime.messages (payload, event, topic, private, extension)
    VALUES (payload, event, topic, private, 'broadcast');
  EXCEPTION
    WHEN OTHERS THEN
      -- Capture and notify the error
      RAISE WARNING 'ErrorSendingBroadcastMessage: %', SQLERRM;
  END;
END;
$$;


--
-- TOC entry 494 (class 1255 OID 17035)
-- Name: subscription_check_filters(); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.subscription_check_filters() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    /*
    Validates that the user defined filters for a subscription:
    - refer to valid columns that the claimed role may access
    - values are coercable to the correct column type
    */
    declare
        col_names text[] = coalesce(
                array_agg(c.column_name order by c.ordinal_position),
                '{}'::text[]
            )
            from
                information_schema.columns c
            where
                format('%I.%I', c.table_schema, c.table_name)::regclass = new.entity
                and pg_catalog.has_column_privilege(
                    (new.claims ->> 'role'),
                    format('%I.%I', c.table_schema, c.table_name)::regclass,
                    c.column_name,
                    'SELECT'
                );
        filter realtime.user_defined_filter;
        col_type regtype;

        in_val jsonb;
    begin
        for filter in select * from unnest(new.filters) loop
            -- Filtered column is valid
            if not filter.column_name = any(col_names) then
                raise exception 'invalid column for filter %', filter.column_name;
            end if;

            -- Type is sanitized and safe for string interpolation
            col_type = (
                select atttypid::regtype
                from pg_catalog.pg_attribute
                where attrelid = new.entity
                      and attname = filter.column_name
            );
            if col_type is null then
                raise exception 'failed to lookup type for column %', filter.column_name;
            end if;

            -- Set maximum number of entries for in filter
            if filter.op = 'in'::realtime.equality_op then
                in_val = realtime.cast(filter.value, (col_type::text || '[]')::regtype);
                if coalesce(jsonb_array_length(in_val), 0) > 100 then
                    raise exception 'too many values for `in` filter. Maximum 100';
                end if;
            else
                -- raises an exception if value is not coercable to type
                perform realtime.cast(filter.value, col_type);
            end if;

        end loop;

        -- Apply consistent order to filters so the unique constraint on
        -- (subscription_id, entity, filters) can't be tricked by a different filter order
        new.filters = coalesce(
            array_agg(f order by f.column_name, f.op, f.value),
            '{}'
        ) from unnest(new.filters) f;

        return new;
    end;
    $$;


--
-- TOC entry 498 (class 1255 OID 17070)
-- Name: to_regrole(text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.to_regrole(role_name text) RETURNS regrole
    LANGUAGE sql IMMUTABLE
    AS $$ select role_name::regrole $$;


--
-- TOC entry 503 (class 1255 OID 17153)
-- Name: topic(); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.topic() RETURNS text
    LANGUAGE sql STABLE
    AS $$
select nullif(current_setting('realtime.topic', true), '')::text;
$$;


--
-- TOC entry 512 (class 1255 OID 17207)
-- Name: can_insert_object(text, text, uuid, jsonb); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.can_insert_object(bucketid text, name text, owner uuid, metadata jsonb) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  INSERT INTO "storage"."objects" ("bucket_id", "name", "owner", "metadata") VALUES (bucketid, name, owner, metadata);
  -- hack to rollback the successful insert
  RAISE sqlstate 'PT200' using
  message = 'ROLLBACK',
  detail = 'rollback successful insert';
END
$$;


--
-- TOC entry 508 (class 1255 OID 17181)
-- Name: extension(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.extension(name text) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
_parts text[];
_filename text;
BEGIN
	select string_to_array(name, '/') into _parts;
	select _parts[array_length(_parts,1)] into _filename;
	-- @todo return the last part instead of 2
	return reverse(split_part(reverse(_filename), '.', 1));
END
$$;


--
-- TOC entry 507 (class 1255 OID 17180)
-- Name: filename(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.filename(name text) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
_parts text[];
BEGIN
	select string_to_array(name, '/') into _parts;
	return _parts[array_length(_parts,1)];
END
$$;


--
-- TOC entry 506 (class 1255 OID 17179)
-- Name: foldername(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.foldername(name text) RETURNS text[]
    LANGUAGE plpgsql
    AS $$
DECLARE
_parts text[];
BEGIN
	select string_to_array(name, '/') into _parts;
	return _parts[1:array_length(_parts,1)-1];
END
$$;


--
-- TOC entry 509 (class 1255 OID 17193)
-- Name: get_size_by_bucket(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_size_by_bucket() RETURNS TABLE(size bigint, bucket_id text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    return query
        select sum((metadata->>'size')::int) as size, obj.bucket_id
        from "storage".objects as obj
        group by obj.bucket_id;
END
$$;


--
-- TOC entry 514 (class 1255 OID 17246)
-- Name: list_multipart_uploads_with_delimiter(text, text, text, integer, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.list_multipart_uploads_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer DEFAULT 100, next_key_token text DEFAULT ''::text, next_upload_token text DEFAULT ''::text) RETURNS TABLE(key text, id text, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $_$
BEGIN
    RETURN QUERY EXECUTE
        'SELECT DISTINCT ON(key COLLATE "C") * from (
            SELECT
                CASE
                    WHEN position($2 IN substring(key from length($1) + 1)) > 0 THEN
                        substring(key from 1 for length($1) + position($2 IN substring(key from length($1) + 1)))
                    ELSE
                        key
                END AS key, id, created_at
            FROM
                storage.s3_multipart_uploads
            WHERE
                bucket_id = $5 AND
                key ILIKE $1 || ''%'' AND
                CASE
                    WHEN $4 != '''' AND $6 = '''' THEN
                        CASE
                            WHEN position($2 IN substring(key from length($1) + 1)) > 0 THEN
                                substring(key from 1 for length($1) + position($2 IN substring(key from length($1) + 1))) COLLATE "C" > $4
                            ELSE
                                key COLLATE "C" > $4
                            END
                    ELSE
                        true
                END AND
                CASE
                    WHEN $6 != '''' THEN
                        id COLLATE "C" > $6
                    ELSE
                        true
                    END
            ORDER BY
                key COLLATE "C" ASC, created_at ASC) as e order by key COLLATE "C" LIMIT $3'
        USING prefix_param, delimiter_param, max_keys, next_key_token, bucket_id, next_upload_token;
END;
$_$;


--
-- TOC entry 513 (class 1255 OID 17209)
-- Name: list_objects_with_delimiter(text, text, text, integer, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.list_objects_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer DEFAULT 100, start_after text DEFAULT ''::text, next_token text DEFAULT ''::text) RETURNS TABLE(name text, id uuid, metadata jsonb, updated_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $_$
BEGIN
    RETURN QUERY EXECUTE
        'SELECT DISTINCT ON(name COLLATE "C") * from (
            SELECT
                CASE
                    WHEN position($2 IN substring(name from length($1) + 1)) > 0 THEN
                        substring(name from 1 for length($1) + position($2 IN substring(name from length($1) + 1)))
                    ELSE
                        name
                END AS name, id, metadata, updated_at
            FROM
                storage.objects
            WHERE
                bucket_id = $5 AND
                name ILIKE $1 || ''%'' AND
                CASE
                    WHEN $6 != '''' THEN
                    name COLLATE "C" > $6
                ELSE true END
                AND CASE
                    WHEN $4 != '''' THEN
                        CASE
                            WHEN position($2 IN substring(name from length($1) + 1)) > 0 THEN
                                substring(name from 1 for length($1) + position($2 IN substring(name from length($1) + 1))) COLLATE "C" > $4
                            ELSE
                                name COLLATE "C" > $4
                            END
                    ELSE
                        true
                END
            ORDER BY
                name COLLATE "C" ASC) as e order by name COLLATE "C" LIMIT $3'
        USING prefix_param, delimiter_param, max_keys, next_token, bucket_id, start_after;
END;
$_$;


--
-- TOC entry 515 (class 1255 OID 17262)
-- Name: operation(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.operation() RETURNS text
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN current_setting('storage.operation', true);
END;
$$;


--
-- TOC entry 510 (class 1255 OID 17196)
-- Name: search(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $_$
declare
  v_order_by text;
  v_sort_order text;
begin
  case
    when sortcolumn = 'name' then
      v_order_by = 'name';
    when sortcolumn = 'updated_at' then
      v_order_by = 'updated_at';
    when sortcolumn = 'created_at' then
      v_order_by = 'created_at';
    when sortcolumn = 'last_accessed_at' then
      v_order_by = 'last_accessed_at';
    else
      v_order_by = 'name';
  end case;

  case
    when sortorder = 'asc' then
      v_sort_order = 'asc';
    when sortorder = 'desc' then
      v_sort_order = 'desc';
    else
      v_sort_order = 'asc';
  end case;

  v_order_by = v_order_by || ' ' || v_sort_order;

  return query execute
    'with folders as (
       select path_tokens[$1] as folder
       from storage.objects
         where objects.name ilike $2 || $3 || ''%''
           and bucket_id = $4
           and array_length(objects.path_tokens, 1) <> $1
       group by folder
       order by folder ' || v_sort_order || '
     )
     (select folder as "name",
            null as id,
            null as updated_at,
            null as created_at,
            null as last_accessed_at,
            null as metadata from folders)
     union all
     (select path_tokens[$1] as "name",
            id,
            updated_at,
            created_at,
            last_accessed_at,
            metadata
     from storage.objects
     where objects.name ilike $2 || $3 || ''%''
       and bucket_id = $4
       and array_length(objects.path_tokens, 1) = $1
     order by ' || v_order_by || ')
     limit $5
     offset $6' using levels, prefix, search, bucketname, limits, offsets;
end;
$_$;


--
-- TOC entry 511 (class 1255 OID 17197)
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW; 
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 244 (class 1259 OID 16523)
-- Name: audit_log_entries; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.audit_log_entries (
    instance_id uuid,
    id uuid NOT NULL,
    payload json,
    created_at timestamp with time zone,
    ip_address character varying(64) DEFAULT ''::character varying NOT NULL
);


--
-- TOC entry 4902 (class 0 OID 0)
-- Dependencies: 244
-- Name: TABLE audit_log_entries; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.audit_log_entries IS 'Auth: Audit trail for user actions.';


--
-- TOC entry 261 (class 1259 OID 16925)
-- Name: flow_state; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.flow_state (
    id uuid NOT NULL,
    user_id uuid,
    auth_code text NOT NULL,
    code_challenge_method auth.code_challenge_method NOT NULL,
    code_challenge text NOT NULL,
    provider_type text NOT NULL,
    provider_access_token text,
    provider_refresh_token text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    authentication_method text NOT NULL,
    auth_code_issued_at timestamp with time zone
);


--
-- TOC entry 4903 (class 0 OID 0)
-- Dependencies: 261
-- Name: TABLE flow_state; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.flow_state IS 'stores metadata for pkce logins';


--
-- TOC entry 252 (class 1259 OID 16723)
-- Name: identities; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.identities (
    provider_id text NOT NULL,
    user_id uuid NOT NULL,
    identity_data jsonb NOT NULL,
    provider text NOT NULL,
    last_sign_in_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    email text GENERATED ALWAYS AS (lower((identity_data ->> 'email'::text))) STORED,
    id uuid DEFAULT gen_random_uuid() NOT NULL
);


--
-- TOC entry 4904 (class 0 OID 0)
-- Dependencies: 252
-- Name: TABLE identities; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.identities IS 'Auth: Stores identities associated to a user.';


--
-- TOC entry 4905 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN identities.email; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.identities.email IS 'Auth: Email is a generated column that references the optional email property in the identity_data';


--
-- TOC entry 243 (class 1259 OID 16516)
-- Name: instances; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.instances (
    id uuid NOT NULL,
    uuid uuid,
    raw_base_config text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- TOC entry 4906 (class 0 OID 0)
-- Dependencies: 243
-- Name: TABLE instances; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.instances IS 'Auth: Manages users across multiple sites.';


--
-- TOC entry 256 (class 1259 OID 16812)
-- Name: mfa_amr_claims; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.mfa_amr_claims (
    session_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    authentication_method text NOT NULL,
    id uuid NOT NULL
);


--
-- TOC entry 4907 (class 0 OID 0)
-- Dependencies: 256
-- Name: TABLE mfa_amr_claims; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_amr_claims IS 'auth: stores authenticator method reference claims for multi factor authentication';


--
-- TOC entry 255 (class 1259 OID 16800)
-- Name: mfa_challenges; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.mfa_challenges (
    id uuid NOT NULL,
    factor_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    verified_at timestamp with time zone,
    ip_address inet NOT NULL,
    otp_code text,
    web_authn_session_data jsonb
);


--
-- TOC entry 4908 (class 0 OID 0)
-- Dependencies: 255
-- Name: TABLE mfa_challenges; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_challenges IS 'auth: stores metadata about challenge requests made';


--
-- TOC entry 254 (class 1259 OID 16787)
-- Name: mfa_factors; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.mfa_factors (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    friendly_name text,
    factor_type auth.factor_type NOT NULL,
    status auth.factor_status NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    secret text,
    phone text,
    last_challenged_at timestamp with time zone,
    web_authn_credential jsonb,
    web_authn_aaguid uuid
);


--
-- TOC entry 4909 (class 0 OID 0)
-- Dependencies: 254
-- Name: TABLE mfa_factors; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_factors IS 'auth: stores metadata about factors';


--
-- TOC entry 262 (class 1259 OID 16975)
-- Name: one_time_tokens; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.one_time_tokens (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    token_type auth.one_time_token_type NOT NULL,
    token_hash text NOT NULL,
    relates_to text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT one_time_tokens_token_hash_check CHECK ((char_length(token_hash) > 0))
);


--
-- TOC entry 242 (class 1259 OID 16505)
-- Name: refresh_tokens; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.refresh_tokens (
    instance_id uuid,
    id bigint NOT NULL,
    token character varying(255),
    user_id character varying(255),
    revoked boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    parent character varying(255),
    session_id uuid
);


--
-- TOC entry 4910 (class 0 OID 0)
-- Dependencies: 242
-- Name: TABLE refresh_tokens; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.refresh_tokens IS 'Auth: Store of tokens used to refresh JWT tokens once they expire.';


--
-- TOC entry 241 (class 1259 OID 16504)
-- Name: refresh_tokens_id_seq; Type: SEQUENCE; Schema: auth; Owner: -
--

CREATE SEQUENCE auth.refresh_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4911 (class 0 OID 0)
-- Dependencies: 241
-- Name: refresh_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: -
--

ALTER SEQUENCE auth.refresh_tokens_id_seq OWNED BY auth.refresh_tokens.id;


--
-- TOC entry 259 (class 1259 OID 16854)
-- Name: saml_providers; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.saml_providers (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    entity_id text NOT NULL,
    metadata_xml text NOT NULL,
    metadata_url text,
    attribute_mapping jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    name_id_format text,
    CONSTRAINT "entity_id not empty" CHECK ((char_length(entity_id) > 0)),
    CONSTRAINT "metadata_url not empty" CHECK (((metadata_url = NULL::text) OR (char_length(metadata_url) > 0))),
    CONSTRAINT "metadata_xml not empty" CHECK ((char_length(metadata_xml) > 0))
);


--
-- TOC entry 4912 (class 0 OID 0)
-- Dependencies: 259
-- Name: TABLE saml_providers; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.saml_providers IS 'Auth: Manages SAML Identity Provider connections.';


--
-- TOC entry 260 (class 1259 OID 16872)
-- Name: saml_relay_states; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.saml_relay_states (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    request_id text NOT NULL,
    for_email text,
    redirect_to text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    flow_state_id uuid,
    CONSTRAINT "request_id not empty" CHECK ((char_length(request_id) > 0))
);


--
-- TOC entry 4913 (class 0 OID 0)
-- Dependencies: 260
-- Name: TABLE saml_relay_states; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.saml_relay_states IS 'Auth: Contains SAML Relay State information for each Service Provider initiated login.';


--
-- TOC entry 245 (class 1259 OID 16531)
-- Name: schema_migrations; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.schema_migrations (
    version character varying(255) NOT NULL
);


--
-- TOC entry 4914 (class 0 OID 0)
-- Dependencies: 245
-- Name: TABLE schema_migrations; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.schema_migrations IS 'Auth: Manages updates to the auth system.';


--
-- TOC entry 253 (class 1259 OID 16753)
-- Name: sessions; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    factor_id uuid,
    aal auth.aal_level,
    not_after timestamp with time zone,
    refreshed_at timestamp without time zone,
    user_agent text,
    ip inet,
    tag text
);


--
-- TOC entry 4915 (class 0 OID 0)
-- Dependencies: 253
-- Name: TABLE sessions; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sessions IS 'Auth: Stores session data associated to a user.';


--
-- TOC entry 4916 (class 0 OID 0)
-- Dependencies: 253
-- Name: COLUMN sessions.not_after; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.not_after IS 'Auth: Not after is a nullable column that contains a timestamp after which the session should be regarded as expired.';


--
-- TOC entry 258 (class 1259 OID 16839)
-- Name: sso_domains; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.sso_domains (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    domain text NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    CONSTRAINT "domain not empty" CHECK ((char_length(domain) > 0))
);


--
-- TOC entry 4917 (class 0 OID 0)
-- Dependencies: 258
-- Name: TABLE sso_domains; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sso_domains IS 'Auth: Manages SSO email address domain mapping to an SSO Identity Provider.';


--
-- TOC entry 257 (class 1259 OID 16830)
-- Name: sso_providers; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.sso_providers (
    id uuid NOT NULL,
    resource_id text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    CONSTRAINT "resource_id not empty" CHECK (((resource_id = NULL::text) OR (char_length(resource_id) > 0)))
);


--
-- TOC entry 4918 (class 0 OID 0)
-- Dependencies: 257
-- Name: TABLE sso_providers; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sso_providers IS 'Auth: Manages SSO identity provider information; see saml_providers for SAML.';


--
-- TOC entry 4919 (class 0 OID 0)
-- Dependencies: 257
-- Name: COLUMN sso_providers.resource_id; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sso_providers.resource_id IS 'Auth: Uniquely identifies a SSO provider according to a user-chosen resource ID (case insensitive), useful in infrastructure as code.';


--
-- TOC entry 240 (class 1259 OID 16493)
-- Name: users; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.users (
    instance_id uuid,
    id uuid NOT NULL,
    aud character varying(255),
    role character varying(255),
    email character varying(255),
    encrypted_password character varying(255),
    email_confirmed_at timestamp with time zone,
    invited_at timestamp with time zone,
    confirmation_token character varying(255),
    confirmation_sent_at timestamp with time zone,
    recovery_token character varying(255),
    recovery_sent_at timestamp with time zone,
    email_change_token_new character varying(255),
    email_change character varying(255),
    email_change_sent_at timestamp with time zone,
    last_sign_in_at timestamp with time zone,
    raw_app_meta_data jsonb,
    raw_user_meta_data jsonb,
    is_super_admin boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    phone text DEFAULT NULL::character varying,
    phone_confirmed_at timestamp with time zone,
    phone_change text DEFAULT ''::character varying,
    phone_change_token character varying(255) DEFAULT ''::character varying,
    phone_change_sent_at timestamp with time zone,
    confirmed_at timestamp with time zone GENERATED ALWAYS AS (LEAST(email_confirmed_at, phone_confirmed_at)) STORED,
    email_change_token_current character varying(255) DEFAULT ''::character varying,
    email_change_confirm_status smallint DEFAULT 0,
    banned_until timestamp with time zone,
    reauthentication_token character varying(255) DEFAULT ''::character varying,
    reauthentication_sent_at timestamp with time zone,
    is_sso_user boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    is_anonymous boolean DEFAULT false NOT NULL,
    CONSTRAINT users_email_change_confirm_status_check CHECK (((email_change_confirm_status >= 0) AND (email_change_confirm_status <= 2)))
);


--
-- TOC entry 4920 (class 0 OID 0)
-- Dependencies: 240
-- Name: TABLE users; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.users IS 'Auth: Stores user login data within a secure schema.';


--
-- TOC entry 4921 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN users.is_sso_user; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.users.is_sso_user IS 'Auth: Set this column to true when the account comes from SSO. These accounts can have duplicate emails.';


--
-- TOC entry 272 (class 1259 OID 23989)
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
-- TOC entry 273 (class 1259 OID 23994)
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
-- TOC entry 4922 (class 0 OID 0)
-- Dependencies: 273
-- Name: action_reply_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.action_reply_id_seq OWNED BY public.action_reply.id;


--
-- TOC entry 274 (class 1259 OID 23995)
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
    owner_id integer,
    is_shared boolean NOT NULL
);


--
-- TOC entry 275 (class 1259 OID 24000)
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
-- TOC entry 4923 (class 0 OID 0)
-- Dependencies: 275
-- Name: actions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.actions_id_seq OWNED BY public.actions.id;


--
-- TOC entry 276 (class 1259 OID 24001)
-- Name: affiliations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.affiliations (
    id integer NOT NULL,
    owner_id integer NOT NULL,
    viewer_id integer NOT NULL,
    created_at double precision
);


--
-- TOC entry 277 (class 1259 OID 24004)
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
-- TOC entry 4924 (class 0 OID 0)
-- Dependencies: 277
-- Name: affiliations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.affiliations_id_seq OWNED BY public.affiliations.id;


--
-- TOC entry 278 (class 1259 OID 24005)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- TOC entry 279 (class 1259 OID 24008)
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
-- TOC entry 4925 (class 0 OID 0)
-- Dependencies: 279
-- Name: COLUMN approval_instance.object_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_id IS '对应单据ID';


--
-- TOC entry 4926 (class 0 OID 0)
-- Dependencies: 279
-- Name: COLUMN approval_instance.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_type IS '单据类型（如 project）';


--
-- TOC entry 4927 (class 0 OID 0)
-- Dependencies: 279
-- Name: COLUMN approval_instance.current_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.current_step IS '当前步骤序号';


--
-- TOC entry 4928 (class 0 OID 0)
-- Dependencies: 279
-- Name: COLUMN approval_instance.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.status IS '状态';


--
-- TOC entry 4929 (class 0 OID 0)
-- Dependencies: 279
-- Name: COLUMN approval_instance.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.started_at IS '流程发起时间';


--
-- TOC entry 4930 (class 0 OID 0)
-- Dependencies: 279
-- Name: COLUMN approval_instance.ended_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.ended_at IS '审批完成时间';


--
-- TOC entry 4931 (class 0 OID 0)
-- Dependencies: 279
-- Name: COLUMN approval_instance.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.process_id IS '流程模板ID';


--
-- TOC entry 4932 (class 0 OID 0)
-- Dependencies: 279
-- Name: COLUMN approval_instance.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.created_by IS '发起人ID';


--
-- TOC entry 4933 (class 0 OID 0)
-- Dependencies: 279
-- Name: COLUMN approval_instance.template_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_snapshot IS '创建时的模板快照';


--
-- TOC entry 4934 (class 0 OID 0)
-- Dependencies: 279
-- Name: COLUMN approval_instance.template_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_version IS '模板版本号';


--
-- TOC entry 280 (class 1259 OID 24013)
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
-- TOC entry 4935 (class 0 OID 0)
-- Dependencies: 280
-- Name: approval_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_instance_id_seq OWNED BY public.approval_instance.id;


--
-- TOC entry 281 (class 1259 OID 24014)
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
    lock_reason character varying(200) DEFAULT '审批流程进行中，暂时锁定编辑'::character varying,
    visual_data json
);


--
-- TOC entry 4936 (class 0 OID 0)
-- Dependencies: 281
-- Name: COLUMN approval_process_template.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.name IS '流程名称';


--
-- TOC entry 4937 (class 0 OID 0)
-- Dependencies: 281
-- Name: COLUMN approval_process_template.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.object_type IS '适用对象（如 quotation）';


--
-- TOC entry 4938 (class 0 OID 0)
-- Dependencies: 281
-- Name: COLUMN approval_process_template.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.is_active IS '是否启用';


--
-- TOC entry 4939 (class 0 OID 0)
-- Dependencies: 281
-- Name: COLUMN approval_process_template.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_by IS '创建人账号ID';


--
-- TOC entry 4940 (class 0 OID 0)
-- Dependencies: 281
-- Name: COLUMN approval_process_template.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_at IS '创建时间';


--
-- TOC entry 4941 (class 0 OID 0)
-- Dependencies: 281
-- Name: COLUMN approval_process_template.required_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.required_fields IS '发起审批时必填字段列表';


--
-- TOC entry 4942 (class 0 OID 0)
-- Dependencies: 281
-- Name: COLUMN approval_process_template.lock_object_on_start; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_object_on_start IS '发起审批后是否锁定对象编辑';


--
-- TOC entry 4943 (class 0 OID 0)
-- Dependencies: 281
-- Name: COLUMN approval_process_template.lock_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_reason IS '锁定原因说明';


--
-- TOC entry 282 (class 1259 OID 24022)
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
-- TOC entry 4944 (class 0 OID 0)
-- Dependencies: 282
-- Name: approval_process_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_process_template_id_seq OWNED BY public.approval_process_template.id;


--
-- TOC entry 283 (class 1259 OID 24023)
-- Name: approval_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.approval_record_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 284 (class 1259 OID 24024)
-- Name: approval_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.approval_record (
    id integer DEFAULT nextval('public.approval_record_id_seq'::regclass) NOT NULL,
    instance_id integer NOT NULL,
    step_id integer,
    approver_id integer NOT NULL,
    action character varying(50) NOT NULL,
    comment text,
    "timestamp" timestamp without time zone
);


--
-- TOC entry 4945 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN approval_record.instance_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.instance_id IS '审批流程实例';


--
-- TOC entry 4946 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN approval_record.step_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.step_id IS '流程步骤ID';


--
-- TOC entry 4947 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN approval_record.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.approver_id IS '审批人ID';


--
-- TOC entry 4948 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN approval_record.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.action IS '同意/拒绝';


--
-- TOC entry 4949 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN approval_record.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.comment IS '审批意见';


--
-- TOC entry 4950 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN approval_record."timestamp"; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record."timestamp" IS '审批时间';


--
-- TOC entry 285 (class 1259 OID 24030)
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
    description text,
    condition_config json,
    is_conditional boolean DEFAULT false,
    branch_on_reject integer,
    skip_conditions json,
    condition_type character varying(50),
    branch_on_approve integer
);


--
-- TOC entry 4951 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN approval_step.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.process_id IS '所属流程模板';


--
-- TOC entry 4952 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN approval_step.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_order IS '流程顺序';


--
-- TOC entry 4953 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN approval_step.approver_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.approver_user_id IS '审批人账号ID';


--
-- TOC entry 4954 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN approval_step.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_name IS '步骤说明（如"财务审批"）';


--
-- TOC entry 4955 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN approval_step.send_email; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.send_email IS '是否发送邮件通知';


--
-- TOC entry 4956 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN approval_step.action_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_type IS '步骤动作类型，如 authorization, quotation_approval';


--
-- TOC entry 4957 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN approval_step.action_params; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_params IS '动作参数，JSON格式';


--
-- TOC entry 4958 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN approval_step.editable_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.editable_fields IS '在此步骤可编辑的字段列表';


--
-- TOC entry 4959 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN approval_step.cc_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_users IS '邮件抄送用户ID列表';


--
-- TOC entry 4960 (class 0 OID 0)
-- Dependencies: 285
-- Name: COLUMN approval_step.cc_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_enabled IS '是否启用邮件抄送';


--
-- TOC entry 286 (class 1259 OID 24040)
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
-- TOC entry 4961 (class 0 OID 0)
-- Dependencies: 286
-- Name: approval_step_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_step_id_seq OWNED BY public.approval_step.id;


--
-- TOC entry 287 (class 1259 OID 24041)
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
-- TOC entry 288 (class 1259 OID 24046)
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
-- TOC entry 4962 (class 0 OID 0)
-- Dependencies: 288
-- Name: change_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.change_logs_id_seq OWNED BY public.change_logs.id;


--
-- TOC entry 289 (class 1259 OID 24047)
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
    share_contacts boolean,
    share_enabled boolean NOT NULL
);


--
-- TOC entry 290 (class 1259 OID 24052)
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
-- TOC entry 4963 (class 0 OID 0)
-- Dependencies: 290
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- TOC entry 291 (class 1259 OID 24053)
-- Name: company_assets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.company_assets (
    id integer NOT NULL,
    asset_type character varying(50) NOT NULL,
    asset_name character varying(100) NOT NULL,
    asset_key character varying(50) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_type character varying(50) NOT NULL,
    file_size integer NOT NULL,
    file_content text NOT NULL,
    description text,
    is_active boolean NOT NULL,
    is_default boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    created_by_id integer
);


--
-- TOC entry 4964 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN company_assets.asset_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.asset_type IS '资产类型: logo, seal, etc.';


--
-- TOC entry 4965 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN company_assets.asset_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.asset_name IS '资产名称';


--
-- TOC entry 4966 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN company_assets.asset_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.asset_key IS '资产唯一标识';


--
-- TOC entry 4967 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN company_assets.file_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_name IS '原始文件名';


--
-- TOC entry 4968 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN company_assets.file_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_type IS '文件类型: image/png, image/svg+xml, etc.';


--
-- TOC entry 4969 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN company_assets.file_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_size IS '文件大小(字节)';


--
-- TOC entry 4970 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN company_assets.file_content; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_content IS 'Base64编码的文件内容';


--
-- TOC entry 4971 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN company_assets.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.description IS '资产描述';


--
-- TOC entry 4972 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN company_assets.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.is_active IS '是否启用';


--
-- TOC entry 4973 (class 0 OID 0)
-- Dependencies: 291
-- Name: COLUMN company_assets.is_default; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.is_default IS '是否为默认资产';


--
-- TOC entry 292 (class 1259 OID 24058)
-- Name: company_assets_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.company_assets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4974 (class 0 OID 0)
-- Dependencies: 292
-- Name: company_assets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.company_assets_id_seq OWNED BY public.company_assets.id;


--
-- TOC entry 293 (class 1259 OID 24059)
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
-- TOC entry 294 (class 1259 OID 24064)
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
-- TOC entry 4975 (class 0 OID 0)
-- Dependencies: 294
-- Name: contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contacts_id_seq OWNED BY public.contacts.id;


--
-- TOC entry 410 (class 1259 OID 26535)
-- Name: data_field_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_field_config (
    id integer NOT NULL,
    table_config_id integer NOT NULL,
    field_name character varying(100) NOT NULL,
    display_name character varying(200) NOT NULL,
    description text,
    data_type character varying(50) NOT NULL,
    is_nullable boolean,
    is_primary_key boolean,
    is_foreign_key boolean,
    foreign_table character varying(100),
    foreign_field character varying(100),
    is_numeric boolean,
    is_monetary boolean,
    is_date boolean,
    is_aggregatable boolean,
    is_filterable boolean,
    is_performance_metric boolean,
    performance_category character varying(50),
    calculation_priority integer,
    display_format character varying(50),
    default_unit character varying(20),
    decimal_places integer,
    sample_values text,
    value_range text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by integer,
    updated_by integer
);


--
-- TOC entry 4976 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.field_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.field_name IS '字段名';


--
-- TOC entry 4977 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.display_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.display_name IS '显示名称';


--
-- TOC entry 4978 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.description IS '字段描述';


--
-- TOC entry 4979 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.data_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.data_type IS '数据类型';


--
-- TOC entry 4980 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.is_nullable; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_nullable IS '是否可为空';


--
-- TOC entry 4981 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.is_primary_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_primary_key IS '是否主键';


--
-- TOC entry 4982 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.is_foreign_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_foreign_key IS '是否外键';


--
-- TOC entry 4983 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.foreign_table; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.foreign_table IS '外键关联表';


--
-- TOC entry 4984 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.foreign_field; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.foreign_field IS '外键关联字段';


--
-- TOC entry 4985 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.is_numeric; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_numeric IS '是否数值字段';


--
-- TOC entry 4986 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.is_monetary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_monetary IS '是否金额字段';


--
-- TOC entry 4987 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.is_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_date IS '是否日期字段';


--
-- TOC entry 4988 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.is_aggregatable; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_aggregatable IS '是否可聚合统计';


--
-- TOC entry 4989 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.is_filterable; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_filterable IS '是否可过滤';


--
-- TOC entry 4990 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.is_performance_metric; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_performance_metric IS '是否绩效指标';


--
-- TOC entry 4991 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.performance_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.performance_category IS '绩效分类：sales/customer/project/quality';


--
-- TOC entry 4992 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.calculation_priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.calculation_priority IS '计算优先级';


--
-- TOC entry 4993 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.display_format; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.display_format IS '显示格式';


--
-- TOC entry 4994 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.default_unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.default_unit IS '默认单位';


--
-- TOC entry 4995 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.decimal_places; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.decimal_places IS '小数位数';


--
-- TOC entry 4996 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.sample_values; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.sample_values IS '样本值JSON';


--
-- TOC entry 4997 (class 0 OID 0)
-- Dependencies: 410
-- Name: COLUMN data_field_config.value_range; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.value_range IS '值范围JSON';


--
-- TOC entry 409 (class 1259 OID 26534)
-- Name: data_field_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_field_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4998 (class 0 OID 0)
-- Dependencies: 409
-- Name: data_field_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_field_config_id_seq OWNED BY public.data_field_config.id;


--
-- TOC entry 404 (class 1259 OID 26477)
-- Name: data_table_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_table_config (
    id integer NOT NULL,
    table_name character varying(100) NOT NULL,
    display_name character varying(200) NOT NULL,
    description text,
    category character varying(50),
    is_active boolean,
    is_performance_source boolean,
    total_records integer,
    last_updated timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by integer,
    updated_by integer
);


--
-- TOC entry 4999 (class 0 OID 0)
-- Dependencies: 404
-- Name: COLUMN data_table_config.table_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.table_name IS '数据表名';


--
-- TOC entry 5000 (class 0 OID 0)
-- Dependencies: 404
-- Name: COLUMN data_table_config.display_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.display_name IS '显示名称';


--
-- TOC entry 5001 (class 0 OID 0)
-- Dependencies: 404
-- Name: COLUMN data_table_config.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.description IS '表描述';


--
-- TOC entry 5002 (class 0 OID 0)
-- Dependencies: 404
-- Name: COLUMN data_table_config.category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.category IS '表分类：business/system/reference';


--
-- TOC entry 5003 (class 0 OID 0)
-- Dependencies: 404
-- Name: COLUMN data_table_config.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.is_active IS '是否启用';


--
-- TOC entry 5004 (class 0 OID 0)
-- Dependencies: 404
-- Name: COLUMN data_table_config.is_performance_source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.is_performance_source IS '是否可用作绩效数据源';


--
-- TOC entry 5005 (class 0 OID 0)
-- Dependencies: 404
-- Name: COLUMN data_table_config.total_records; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.total_records IS '记录总数';


--
-- TOC entry 5006 (class 0 OID 0)
-- Dependencies: 404
-- Name: COLUMN data_table_config.last_updated; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.last_updated IS '数据最后更新时间';


--
-- TOC entry 403 (class 1259 OID 26476)
-- Name: data_table_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_table_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5007 (class 0 OID 0)
-- Dependencies: 403
-- Name: data_table_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_table_config_id_seq OWNED BY public.data_table_config.id;


--
-- TOC entry 295 (class 1259 OID 24065)
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(20) NOT NULL,
    parent_id integer,
    manager_id integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- TOC entry 296 (class 1259 OID 24068)
-- Name: departments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.departments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5008 (class 0 OID 0)
-- Dependencies: 296
-- Name: departments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.departments_id_seq OWNED BY public.departments.id;


--
-- TOC entry 297 (class 1259 OID 24069)
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
-- TOC entry 298 (class 1259 OID 24072)
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
-- TOC entry 5009 (class 0 OID 0)
-- Dependencies: 298
-- Name: dev_product_specs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_product_specs_id_seq OWNED BY public.dev_product_specs.id;


--
-- TOC entry 299 (class 1259 OID 24073)
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
-- TOC entry 300 (class 1259 OID 24079)
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
-- TOC entry 5010 (class 0 OID 0)
-- Dependencies: 300
-- Name: dev_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_products_id_seq OWNED BY public.dev_products.id;


--
-- TOC entry 301 (class 1259 OID 24080)
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
    is_vendor boolean DEFAULT false,
    email_signature_content text,
    website character varying(200),
    postal_code character varying(20),
    logo_filename character varying(100),
    email character varying(100),
    email_signature_type character varying(50),
    email_signature_size integer,
    address character varying(500),
    logo_content text,
    email_signature_filename character varying(100),
    logo_size integer,
    phone character varying(50),
    fax character varying(50),
    logo_type character varying(50)
);


--
-- TOC entry 302 (class 1259 OID 24086)
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
-- TOC entry 5011 (class 0 OID 0)
-- Dependencies: 302
-- Name: dictionaries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dictionaries_id_seq OWNED BY public.dictionaries.id;


--
-- TOC entry 303 (class 1259 OID 24087)
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
-- TOC entry 5012 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN event_registry.event_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.event_key IS '事件唯一键';


--
-- TOC entry 5013 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN event_registry.label_zh; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.label_zh IS '中文名称';


--
-- TOC entry 5014 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN event_registry.label_en; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.label_en IS '英文名称';


--
-- TOC entry 5015 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN event_registry.default_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.default_enabled IS '是否默认开启';


--
-- TOC entry 5016 (class 0 OID 0)
-- Dependencies: 303
-- Name: COLUMN event_registry.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.enabled IS '是否在通知中心展示';


--
-- TOC entry 304 (class 1259 OID 24090)
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
-- TOC entry 5017 (class 0 OID 0)
-- Dependencies: 304
-- Name: event_registry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_registry_id_seq OWNED BY public.event_registry.id;


--
-- TOC entry 305 (class 1259 OID 24091)
-- Name: expense_details; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expense_details (
    id integer NOT NULL,
    expense_id integer NOT NULL,
    expense_date date NOT NULL,
    expense_category character varying(50) NOT NULL,
    description text NOT NULL,
    document_count integer,
    amount double precision NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    invoice_images text,
    currency character varying(10) DEFAULT 'CNY'::character varying,
    invoice_amount numeric(15,2) DEFAULT 0.00,
    current_amount numeric(15,2) DEFAULT 0.00,
    exchange_rate numeric(10,4) DEFAULT 1.0000
);


--
-- TOC entry 306 (class 1259 OID 24100)
-- Name: expense_details_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.expense_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5018 (class 0 OID 0)
-- Dependencies: 306
-- Name: expense_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expense_details_id_seq OWNED BY public.expense_details.id;


--
-- TOC entry 307 (class 1259 OID 24101)
-- Name: expenses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expenses (
    id integer NOT NULL,
    expense_number character varying(20) NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    customer_id integer,
    project_id integer,
    total_amount double precision NOT NULL,
    status character varying(20) NOT NULL,
    is_locked boolean NOT NULL,
    approved_by integer,
    approved_at timestamp without time zone,
    approval_notes text,
    owner_id integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_deleted boolean,
    contact_id integer,
    currency character varying(10) DEFAULT 'CNY'::character varying,
    payment_status character varying(20) DEFAULT 'unpaid'::character varying NOT NULL,
    payment_amount double precision,
    payment_date timestamp without time zone,
    payment_method character varying(50),
    payment_reference character varying(100),
    payment_notes text,
    paid_by integer
);


--
-- TOC entry 308 (class 1259 OID 24108)
-- Name: expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5019 (class 0 OID 0)
-- Dependencies: 308
-- Name: expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expenses_id_seq OWNED BY public.expenses.id;


--
-- TOC entry 309 (class 1259 OID 24109)
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
-- TOC entry 5020 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.version_id IS '版本ID';


--
-- TOC entry 5021 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.change_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.change_type IS '变更类型：feature/fix/improvement/security';


--
-- TOC entry 5022 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.module_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.module_name IS '模块名称';


--
-- TOC entry 5023 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.title; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.title IS '变更标题';


--
-- TOC entry 5024 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.description IS '详细描述';


--
-- TOC entry 5025 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.priority IS '优先级：low/medium/high/critical';


--
-- TOC entry 5026 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.impact_level; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.impact_level IS '影响级别：minor/major/breaking';


--
-- TOC entry 5027 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.affected_files; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.affected_files IS '影响的文件列表（JSON格式）';


--
-- TOC entry 5028 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.git_commits; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.git_commits IS '相关Git提交（JSON格式）';


--
-- TOC entry 5029 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.test_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.test_status IS '测试状态：pending/passed/failed';


--
-- TOC entry 5030 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.test_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.test_notes IS '测试说明';


--
-- TOC entry 5031 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.developer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.developer_id IS '开发人员ID';


--
-- TOC entry 5032 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.developer_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.developer_name IS '开发人员姓名';


--
-- TOC entry 5033 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.created_at IS '创建时间';


--
-- TOC entry 5034 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN feature_changes.completed_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.completed_at IS '完成时间';


--
-- TOC entry 310 (class 1259 OID 24114)
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
-- TOC entry 5035 (class 0 OID 0)
-- Dependencies: 310
-- Name: feature_changes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.feature_changes_id_seq OWNED BY public.feature_changes.id;


--
-- TOC entry 311 (class 1259 OID 24115)
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
-- TOC entry 312 (class 1259 OID 24118)
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
-- TOC entry 5036 (class 0 OID 0)
-- Dependencies: 312
-- Name: five_star_project_baselines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.five_star_project_baselines_id_seq OWNED BY public.five_star_project_baselines.id;


--
-- TOC entry 406 (class 1259 OID 26498)
-- Name: formula_templates_extended; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.formula_templates_extended (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    template_category character varying(50),
    description text,
    formula_expression text NOT NULL,
    required_tables text,
    required_fields text,
    result_type character varying(50),
    result_unit character varying(20),
    is_system_template boolean,
    is_active boolean,
    usage_count integer,
    last_used_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by integer
);


--
-- TOC entry 5037 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.template_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.template_name IS '模板名称';


--
-- TOC entry 5038 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.template_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.template_category IS '模板分类';


--
-- TOC entry 5039 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.description IS '模板描述';


--
-- TOC entry 5040 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.formula_expression; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.formula_expression IS '公式表达式';


--
-- TOC entry 5041 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.required_tables; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.required_tables IS '需要的数据表JSON';


--
-- TOC entry 5042 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.required_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.required_fields IS '需要的字段JSON';


--
-- TOC entry 5043 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.result_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.result_type IS '结果类型：numeric/percentage/count';


--
-- TOC entry 5044 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.result_unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.result_unit IS '结果单位';


--
-- TOC entry 5045 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.is_system_template; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.is_system_template IS '是否系统模板';


--
-- TOC entry 5046 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.is_active IS '是否启用';


--
-- TOC entry 5047 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.usage_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.usage_count IS '使用次数';


--
-- TOC entry 5048 (class 0 OID 0)
-- Dependencies: 406
-- Name: COLUMN formula_templates_extended.last_used_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.last_used_at IS '最后使用时间';


--
-- TOC entry 405 (class 1259 OID 26497)
-- Name: formula_templates_extended_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.formula_templates_extended_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5049 (class 0 OID 0)
-- Dependencies: 405
-- Name: formula_templates_extended_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.formula_templates_extended_id_seq OWNED BY public.formula_templates_extended.id;


--
-- TOC entry 313 (class 1259 OID 24119)
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
-- TOC entry 314 (class 1259 OID 24124)
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
-- TOC entry 5050 (class 0 OID 0)
-- Dependencies: 314
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- TOC entry 315 (class 1259 OID 24125)
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
-- TOC entry 316 (class 1259 OID 24130)
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
-- TOC entry 5051 (class 0 OID 0)
-- Dependencies: 316
-- Name: inventory_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_transactions_id_seq OWNED BY public.inventory_transactions.id;


--
-- TOC entry 400 (class 1259 OID 26455)
-- Name: performance_formula_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performance_formula_templates (
    id integer NOT NULL,
    template_name character varying(100) NOT NULL,
    template_category character varying(50),
    formula_expression text NOT NULL,
    description text,
    variables_definition json,
    example_usage text,
    is_system_template boolean,
    created_at timestamp without time zone
);


--
-- TOC entry 399 (class 1259 OID 26454)
-- Name: performance_formula_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.performance_formula_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5052 (class 0 OID 0)
-- Dependencies: 399
-- Name: performance_formula_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_formula_templates_id_seq OWNED BY public.performance_formula_templates.id;


--
-- TOC entry 396 (class 1259 OID 26425)
-- Name: performance_metrics_definition; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performance_metrics_definition (
    id integer NOT NULL,
    metric_code character varying(50) NOT NULL,
    metric_name character varying(100) NOT NULL,
    metric_category character varying(50),
    data_type character varying(20) NOT NULL,
    default_unit character varying(20),
    description text,
    available_sources json,
    is_system_metric boolean,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- TOC entry 395 (class 1259 OID 26424)
-- Name: performance_metrics_definition_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.performance_metrics_definition_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5053 (class 0 OID 0)
-- Dependencies: 395
-- Name: performance_metrics_definition_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_metrics_definition_id_seq OWNED BY public.performance_metrics_definition.id;


--
-- TOC entry 317 (class 1259 OID 24131)
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
-- TOC entry 318 (class 1259 OID 24138)
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
-- TOC entry 5054 (class 0 OID 0)
-- Dependencies: 318
-- Name: performance_statistics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_statistics_id_seq OWNED BY public.performance_statistics.id;


--
-- TOC entry 319 (class 1259 OID 24139)
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
    updated_by integer,
    customers_rate integer DEFAULT 0,
    implant_rate integer DEFAULT 0,
    sales_rate integer DEFAULT 0,
    projects_rate integer DEFAULT 0
);


--
-- TOC entry 320 (class 1259 OID 24146)
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
-- TOC entry 5055 (class 0 OID 0)
-- Dependencies: 320
-- Name: performance_targets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_targets_id_seq OWNED BY public.performance_targets.id;


--
-- TOC entry 321 (class 1259 OID 24147)
-- Name: permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    module character varying(50) NOT NULL,
    can_view boolean,
    can_create boolean,
    can_edit boolean,
    can_delete boolean,
    permission_level character varying(20) DEFAULT 'personal'::character varying NOT NULL,
    permission_level_description text,
    pricing_discount_limit double precision,
    settlement_discount_limit double precision,
    can_change_owner boolean DEFAULT false
);


--
-- TOC entry 322 (class 1259 OID 24153)
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
-- TOC entry 5056 (class 0 OID 0)
-- Dependencies: 322
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- TOC entry 323 (class 1259 OID 24154)
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
-- TOC entry 5057 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN pricing_order_approval_records.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.pricing_order_id IS '批价单ID';


--
-- TOC entry 5058 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN pricing_order_approval_records.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_order IS '审批步骤顺序';


--
-- TOC entry 5059 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN pricing_order_approval_records.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_name IS '审批步骤名称';


--
-- TOC entry 5060 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN pricing_order_approval_records.approver_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_role IS '审批人角色';


--
-- TOC entry 5061 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN pricing_order_approval_records.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_id IS '审批人ID';


--
-- TOC entry 5062 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN pricing_order_approval_records.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.action IS '审批动作：approve/reject';


--
-- TOC entry 5063 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN pricing_order_approval_records.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.comment IS '审批意见';


--
-- TOC entry 5064 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN pricing_order_approval_records.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approved_at IS '审批时间';


--
-- TOC entry 5065 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN pricing_order_approval_records.is_fast_approval; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.is_fast_approval IS '是否快速通过';


--
-- TOC entry 5066 (class 0 OID 0)
-- Dependencies: 323
-- Name: COLUMN pricing_order_approval_records.fast_approval_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.fast_approval_reason IS '快速通过原因';


--
-- TOC entry 324 (class 1259 OID 24159)
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
-- TOC entry 5067 (class 0 OID 0)
-- Dependencies: 324
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_order_approval_records_id_seq OWNED BY public.pricing_order_approval_records.id;


--
-- TOC entry 325 (class 1259 OID 24160)
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
-- TOC entry 5068 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.pricing_order_id IS '批价单ID';


--
-- TOC entry 5069 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_name IS '产品名称';


--
-- TOC entry 5070 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_model IS '产品型号';


--
-- TOC entry 5071 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_desc IS '产品描述';


--
-- TOC entry 5072 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.brand IS '品牌';


--
-- TOC entry 5073 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.unit IS '单位';


--
-- TOC entry 5074 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_mn IS '产品MN编码';


--
-- TOC entry 5075 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.market_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.market_price IS '市场价';


--
-- TOC entry 5076 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.unit_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.unit_price IS '单价';


--
-- TOC entry 5077 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.quantity IS '数量';


--
-- TOC entry 5078 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.discount_rate IS '折扣率';


--
-- TOC entry 5079 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.total_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.total_price IS '小计金额';


--
-- TOC entry 5080 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.source_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.source_type IS '数据来源：quotation/manual';


--
-- TOC entry 5081 (class 0 OID 0)
-- Dependencies: 325
-- Name: COLUMN pricing_order_details.source_quotation_detail_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.source_quotation_detail_id IS '来源报价单明细ID';


--
-- TOC entry 326 (class 1259 OID 24166)
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
-- TOC entry 5082 (class 0 OID 0)
-- Dependencies: 326
-- Name: pricing_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_order_details_id_seq OWNED BY public.pricing_order_details.id;


--
-- TOC entry 327 (class 1259 OID 24167)
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
-- TOC entry 5083 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.order_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.order_number IS '批价单号';


--
-- TOC entry 5084 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.project_id IS '项目ID';


--
-- TOC entry 5085 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.quotation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.quotation_id IS '报价单ID';


--
-- TOC entry 5086 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.distributor_id IS '分销商ID';


--
-- TOC entry 5087 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.dealer_id IS '经销商ID';


--
-- TOC entry 5088 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.pricing_total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_amount IS '批价单总金额';


--
-- TOC entry 5089 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.pricing_total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_discount_rate IS '批价单总折扣率';


--
-- TOC entry 5090 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.settlement_total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_amount IS '结算单总金额';


--
-- TOC entry 5091 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.settlement_total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_discount_rate IS '结算单总折扣率';


--
-- TOC entry 5092 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.approval_flow_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approval_flow_type IS '审批流程类型';


--
-- TOC entry 5093 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.status IS '批价单状态';


--
-- TOC entry 5094 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.current_approval_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.current_approval_step IS '当前审批步骤';


--
-- TOC entry 5095 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.approved_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approved_by IS '最终批准人';


--
-- TOC entry 5096 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approved_at IS '批准时间';


--
-- TOC entry 5097 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.created_by IS '创建人';


--
-- TOC entry 5098 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.created_at IS '创建时间';


--
-- TOC entry 5099 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.updated_at IS '更新时间';


--
-- TOC entry 5100 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.is_direct_contract; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.is_direct_contract IS '厂商直签';


--
-- TOC entry 5101 (class 0 OID 0)
-- Dependencies: 327
-- Name: COLUMN pricing_orders.is_factory_pickup; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.is_factory_pickup IS '厂家提货';


--
-- TOC entry 328 (class 1259 OID 24173)
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
-- TOC entry 5102 (class 0 OID 0)
-- Dependencies: 328
-- Name: pricing_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_orders_id_seq OWNED BY public.pricing_orders.id;


--
-- TOC entry 329 (class 1259 OID 24174)
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
-- TOC entry 330 (class 1259 OID 24179)
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
-- TOC entry 5103 (class 0 OID 0)
-- Dependencies: 330
-- Name: product_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_categories_id_seq OWNED BY public.product_categories.id;


--
-- TOC entry 331 (class 1259 OID 24180)
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
-- TOC entry 332 (class 1259 OID 24185)
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
-- TOC entry 5104 (class 0 OID 0)
-- Dependencies: 332
-- Name: product_code_field_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_field_options_id_seq OWNED BY public.product_code_field_options.id;


--
-- TOC entry 333 (class 1259 OID 24186)
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
-- TOC entry 334 (class 1259 OID 24189)
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
-- TOC entry 5105 (class 0 OID 0)
-- Dependencies: 334
-- Name: product_code_field_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_field_values_id_seq OWNED BY public.product_code_field_values.id;


--
-- TOC entry 335 (class 1259 OID 24190)
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
-- TOC entry 336 (class 1259 OID 24195)
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
-- TOC entry 5106 (class 0 OID 0)
-- Dependencies: 336
-- Name: product_code_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_fields_id_seq OWNED BY public.product_code_fields.id;


--
-- TOC entry 337 (class 1259 OID 24196)
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
-- TOC entry 338 (class 1259 OID 24199)
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
-- TOC entry 5107 (class 0 OID 0)
-- Dependencies: 338
-- Name: product_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_codes_id_seq OWNED BY public.product_codes.id;


--
-- TOC entry 339 (class 1259 OID 24200)
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
-- TOC entry 340 (class 1259 OID 24205)
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
-- TOC entry 5108 (class 0 OID 0)
-- Dependencies: 340
-- Name: product_regions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_regions_id_seq OWNED BY public.product_regions.id;


--
-- TOC entry 341 (class 1259 OID 24206)
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
-- TOC entry 342 (class 1259 OID 24211)
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
-- TOC entry 5109 (class 0 OID 0)
-- Dependencies: 342
-- Name: product_subcategories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_subcategories_id_seq OWNED BY public.product_subcategories.id;


--
-- TOC entry 343 (class 1259 OID 24212)
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
-- TOC entry 344 (class 1259 OID 24219)
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
-- TOC entry 5110 (class 0 OID 0)
-- Dependencies: 344
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- TOC entry 345 (class 1259 OID 24220)
-- Name: project_customer_associations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_customer_associations (
    id integer NOT NULL,
    project_id integer NOT NULL,
    company_id integer NOT NULL,
    customer_type character varying NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by integer
);


--
-- TOC entry 5111 (class 0 OID 0)
-- Dependencies: 345
-- Name: TABLE project_customer_associations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.project_customer_associations IS '项目客户关联表';


--
-- TOC entry 5112 (class 0 OID 0)
-- Dependencies: 345
-- Name: COLUMN project_customer_associations.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.id IS '主键ID';


--
-- TOC entry 5113 (class 0 OID 0)
-- Dependencies: 345
-- Name: COLUMN project_customer_associations.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.project_id IS '关联的项目ID';


--
-- TOC entry 5114 (class 0 OID 0)
-- Dependencies: 345
-- Name: COLUMN project_customer_associations.company_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.company_id IS '关联的公司ID';


--
-- TOC entry 5115 (class 0 OID 0)
-- Dependencies: 345
-- Name: COLUMN project_customer_associations.customer_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.customer_type IS '客户类型（end_user等）';


--
-- TOC entry 5116 (class 0 OID 0)
-- Dependencies: 345
-- Name: COLUMN project_customer_associations.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.created_at IS '创建时间';


--
-- TOC entry 5117 (class 0 OID 0)
-- Dependencies: 345
-- Name: COLUMN project_customer_associations.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.updated_at IS '更新时间';


--
-- TOC entry 5118 (class 0 OID 0)
-- Dependencies: 345
-- Name: COLUMN project_customer_associations.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.created_by IS '创建者用户ID';


--
-- TOC entry 346 (class 1259 OID 24225)
-- Name: project_customer_associations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_customer_associations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5119 (class 0 OID 0)
-- Dependencies: 346
-- Name: project_customer_associations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_customer_associations_id_seq OWNED BY public.project_customer_associations.id;


--
-- TOC entry 347 (class 1259 OID 24226)
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
-- TOC entry 348 (class 1259 OID 24229)
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
-- TOC entry 5120 (class 0 OID 0)
-- Dependencies: 348
-- Name: project_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_members_id_seq OWNED BY public.project_members.id;


--
-- TOC entry 349 (class 1259 OID 24230)
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
-- TOC entry 350 (class 1259 OID 24234)
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
-- TOC entry 5121 (class 0 OID 0)
-- Dependencies: 350
-- Name: project_rating_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_rating_records_id_seq OWNED BY public.project_rating_records.id;


--
-- TOC entry 351 (class 1259 OID 24235)
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
-- TOC entry 352 (class 1259 OID 24244)
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
-- TOC entry 5122 (class 0 OID 0)
-- Dependencies: 352
-- Name: project_scoring_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_scoring_config_id_seq OWNED BY public.project_scoring_config.id;


--
-- TOC entry 353 (class 1259 OID 24245)
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
-- TOC entry 354 (class 1259 OID 24254)
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
-- TOC entry 5123 (class 0 OID 0)
-- Dependencies: 354
-- Name: project_scoring_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_scoring_records_id_seq OWNED BY public.project_scoring_records.id;


--
-- TOC entry 355 (class 1259 OID 24255)
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
-- TOC entry 356 (class 1259 OID 24261)
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
-- TOC entry 5124 (class 0 OID 0)
-- Dependencies: 356
-- Name: project_stage_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_stage_history_id_seq OWNED BY public.project_stage_history.id;


--
-- TOC entry 357 (class 1259 OID 24262)
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
-- TOC entry 358 (class 1259 OID 24274)
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
-- TOC entry 5125 (class 0 OID 0)
-- Dependencies: 358
-- Name: project_total_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_total_scores_id_seq OWNED BY public.project_total_scores.id;


--
-- TOC entry 359 (class 1259 OID 24275)
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
    industry character varying(50),
    shared_with_users jsonb,
    share_enabled boolean NOT NULL
);


--
-- TOC entry 360 (class 1259 OID 24285)
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
-- TOC entry 5126 (class 0 OID 0)
-- Dependencies: 360
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- TOC entry 361 (class 1259 OID 24286)
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
-- TOC entry 362 (class 1259 OID 24291)
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
-- TOC entry 5127 (class 0 OID 0)
-- Dependencies: 362
-- Name: purchase_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_order_details_id_seq OWNED BY public.purchase_order_details.id;


--
-- TOC entry 363 (class 1259 OID 24292)
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
-- TOC entry 364 (class 1259 OID 24297)
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
-- TOC entry 5128 (class 0 OID 0)
-- Dependencies: 364
-- Name: purchase_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_orders_id_seq OWNED BY public.purchase_orders.id;


--
-- TOC entry 365 (class 1259 OID 24298)
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
-- TOC entry 366 (class 1259 OID 24304)
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
-- TOC entry 5129 (class 0 OID 0)
-- Dependencies: 366
-- Name: quotation_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotation_details_id_seq OWNED BY public.quotation_details.id;


--
-- TOC entry 367 (class 1259 OID 24305)
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
-- TOC entry 368 (class 1259 OID 24320)
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
-- TOC entry 5130 (class 0 OID 0)
-- Dependencies: 368
-- Name: quotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotations_id_seq OWNED BY public.quotations.id;


--
-- TOC entry 402 (class 1259 OID 26464)
-- Name: role_performance_access; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_performance_access (
    id integer NOT NULL,
    role character varying(50) NOT NULL,
    access_scope character varying(20) NOT NULL,
    access_conditions json,
    description text,
    created_at timestamp without time zone
);


--
-- TOC entry 401 (class 1259 OID 26463)
-- Name: role_performance_access_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.role_performance_access_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5131 (class 0 OID 0)
-- Dependencies: 401
-- Name: role_performance_access_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_performance_access_id_seq OWNED BY public.role_performance_access.id;


--
-- TOC entry 398 (class 1259 OID 26435)
-- Name: role_performance_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_performance_config (
    id integer NOT NULL,
    role character varying(50) NOT NULL,
    config_name character varying(100),
    description text,
    is_active boolean,
    created_by integer,
    updated_by integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- TOC entry 397 (class 1259 OID 26434)
-- Name: role_performance_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.role_performance_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5132 (class 0 OID 0)
-- Dependencies: 397
-- Name: role_performance_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_performance_config_id_seq OWNED BY public.role_performance_config.id;


--
-- TOC entry 408 (class 1259 OID 26512)
-- Name: role_performance_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_performance_items (
    id integer NOT NULL,
    role_config_id integer NOT NULL,
    metric_id integer,
    item_name character varying(100) NOT NULL,
    item_code character varying(50) NOT NULL,
    sort_order integer,
    is_enabled boolean,
    stat_scope character varying(20) NOT NULL,
    stat_scope_description text,
    calculation_method character varying(20),
    calculation_formula text,
    data_source_config json,
    qualification_rate numeric(5,2),
    excellent_threshold numeric(15,2),
    good_threshold numeric(15,2),
    qualified_threshold numeric(15,2),
    display_unit character varying(20),
    decimal_places integer,
    color_config json,
    weight numeric(5,2),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- TOC entry 407 (class 1259 OID 26511)
-- Name: role_performance_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.role_performance_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5133 (class 0 OID 0)
-- Dependencies: 407
-- Name: role_performance_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_performance_items_id_seq OWNED BY public.role_performance_items.id;


--
-- TOC entry 369 (class 1259 OID 24321)
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
    settlement_discount_limit double precision,
    permission_level character varying DEFAULT 'personal'::character varying,
    permission_level_description text,
    can_change_owner boolean DEFAULT false
);


--
-- TOC entry 370 (class 1259 OID 24327)
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
-- TOC entry 5134 (class 0 OID 0)
-- Dependencies: 370
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- TOC entry 371 (class 1259 OID 24328)
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
-- TOC entry 372 (class 1259 OID 24333)
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
-- TOC entry 5135 (class 0 OID 0)
-- Dependencies: 372
-- Name: settlement_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_details_id_seq OWNED BY public.settlement_details.id;


--
-- TOC entry 373 (class 1259 OID 24334)
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
-- TOC entry 5136 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.pricing_order_id IS '批价单ID';


--
-- TOC entry 5137 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_name IS '产品名称';


--
-- TOC entry 5138 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_model IS '产品型号';


--
-- TOC entry 5139 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_desc IS '产品描述';


--
-- TOC entry 5140 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.brand IS '品牌';


--
-- TOC entry 5141 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.unit IS '单位';


--
-- TOC entry 5142 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_mn IS '产品MN编码';


--
-- TOC entry 5143 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.market_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.market_price IS '市场价';


--
-- TOC entry 5144 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.unit_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.unit_price IS '单价';


--
-- TOC entry 5145 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.quantity IS '数量';


--
-- TOC entry 5146 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.discount_rate IS '折扣率';


--
-- TOC entry 5147 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.total_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.total_price IS '小计金额';


--
-- TOC entry 5148 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.pricing_detail_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.pricing_detail_id IS '关联批价单明细ID';


--
-- TOC entry 5149 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.settlement_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_order_id IS '结算单ID';


--
-- TOC entry 5150 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.settlement_company_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_company_id IS '结算目标公司ID';


--
-- TOC entry 5151 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.settlement_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_status IS '结算状态: pending, completed';


--
-- TOC entry 5152 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.settlement_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_date IS '结算完成时间';


--
-- TOC entry 5153 (class 0 OID 0)
-- Dependencies: 373
-- Name: COLUMN settlement_order_details.settlement_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_notes IS '结算备注';


--
-- TOC entry 374 (class 1259 OID 24340)
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
-- TOC entry 5154 (class 0 OID 0)
-- Dependencies: 374
-- Name: settlement_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_order_details_id_seq OWNED BY public.settlement_order_details.id;


--
-- TOC entry 375 (class 1259 OID 24341)
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
    updated_at timestamp without time zone,
    settlement_status character varying(20) DEFAULT '''pending'''::character varying
);


--
-- TOC entry 5155 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.order_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.order_number IS '结算单号';


--
-- TOC entry 5156 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.pricing_order_id IS '关联批价单ID';


--
-- TOC entry 5157 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.project_id IS '项目ID';


--
-- TOC entry 5158 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.quotation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.quotation_id IS '报价单ID';


--
-- TOC entry 5159 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.distributor_id IS '分销商ID';


--
-- TOC entry 5160 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.dealer_id IS '经销商ID（辅助信息）';


--
-- TOC entry 5161 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.total_amount IS '结算总金额';


--
-- TOC entry 5162 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.total_discount_rate IS '结算总折扣率';


--
-- TOC entry 5163 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.status IS '结算单状态';


--
-- TOC entry 5164 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.approved_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.approved_by IS '批准人';


--
-- TOC entry 5165 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.approved_at IS '批准时间';


--
-- TOC entry 5166 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.created_by IS '创建人';


--
-- TOC entry 5167 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.created_at IS '创建时间';


--
-- TOC entry 5168 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN settlement_orders.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.updated_at IS '更新时间';


--
-- TOC entry 376 (class 1259 OID 24345)
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
-- TOC entry 5169 (class 0 OID 0)
-- Dependencies: 376
-- Name: settlement_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_orders_id_seq OWNED BY public.settlement_orders.id;


--
-- TOC entry 377 (class 1259 OID 24346)
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
-- TOC entry 378 (class 1259 OID 24351)
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
-- TOC entry 5170 (class 0 OID 0)
-- Dependencies: 378
-- Name: settlements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlements_id_seq OWNED BY public.settlements.id;


--
-- TOC entry 379 (class 1259 OID 24352)
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
-- TOC entry 5171 (class 0 OID 0)
-- Dependencies: 379
-- Name: COLUMN solution_manager_email_settings.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.user_id IS '解决方案经理用户ID';


--
-- TOC entry 5172 (class 0 OID 0)
-- Dependencies: 379
-- Name: COLUMN solution_manager_email_settings.quotation_created; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_created IS '报价单新建通知';


--
-- TOC entry 5173 (class 0 OID 0)
-- Dependencies: 379
-- Name: COLUMN solution_manager_email_settings.quotation_updated; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_updated IS '报价单更新通知';


--
-- TOC entry 5174 (class 0 OID 0)
-- Dependencies: 379
-- Name: COLUMN solution_manager_email_settings.project_created; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_created IS '项目新建通知';


--
-- TOC entry 5175 (class 0 OID 0)
-- Dependencies: 379
-- Name: COLUMN solution_manager_email_settings.project_stage_changed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_stage_changed IS '项目阶段推进通知';


--
-- TOC entry 380 (class 1259 OID 24355)
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
-- TOC entry 5176 (class 0 OID 0)
-- Dependencies: 380
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.solution_manager_email_settings_id_seq OWNED BY public.solution_manager_email_settings.id;


--
-- TOC entry 381 (class 1259 OID 24356)
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
-- TOC entry 5177 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.version_id IS '版本ID';


--
-- TOC entry 5178 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.avg_response_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.avg_response_time IS '平均响应时间（毫秒）';


--
-- TOC entry 5179 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.max_response_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.max_response_time IS '最大响应时间（毫秒）';


--
-- TOC entry 5180 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.error_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.error_rate IS '错误率（百分比）';


--
-- TOC entry 5181 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.active_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.active_users IS '活跃用户数';


--
-- TOC entry 5182 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.total_requests; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.total_requests IS '总请求数';


--
-- TOC entry 5183 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.database_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.database_size IS '数据库大小（字节）';


--
-- TOC entry 5184 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.cpu_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.cpu_usage IS 'CPU使用率（百分比）';


--
-- TOC entry 5185 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.memory_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.memory_usage IS '内存使用率（百分比）';


--
-- TOC entry 5186 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.disk_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.disk_usage IS '磁盘使用率（百分比）';


--
-- TOC entry 5187 (class 0 OID 0)
-- Dependencies: 381
-- Name: COLUMN system_metrics.recorded_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.recorded_at IS '记录时间';


--
-- TOC entry 382 (class 1259 OID 24359)
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
-- TOC entry 5188 (class 0 OID 0)
-- Dependencies: 382
-- Name: system_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_metrics_id_seq OWNED BY public.system_metrics.id;


--
-- TOC entry 383 (class 1259 OID 24360)
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
-- TOC entry 384 (class 1259 OID 24365)
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
-- TOC entry 5189 (class 0 OID 0)
-- Dependencies: 384
-- Name: system_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_settings_id_seq OWNED BY public.system_settings.id;


--
-- TOC entry 385 (class 1259 OID 24366)
-- Name: temp_products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_products (
    id integer NOT NULL,
    product_name character varying(100) NOT NULL,
    product_model character varying(100) NOT NULL,
    product_desc text,
    brand character varying(50),
    unit character varying(20),
    product_mn character varying(50),
    category character varying(50),
    category_path character varying(200),
    created_by integer NOT NULL,
    reference_price double precision,
    usage_count integer,
    last_used_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_deleted boolean
);


--
-- TOC entry 5190 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_name IS '产品名称';


--
-- TOC entry 5191 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_model IS '产品型号';


--
-- TOC entry 5192 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_desc IS '产品描述/规格';


--
-- TOC entry 5193 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.brand IS '品牌';


--
-- TOC entry 5194 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.unit IS '单位';


--
-- TOC entry 5195 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_mn IS '临时产品MN号，格式为TEMP-{8位随机码}';


--
-- TOC entry 5196 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.category IS '关联的三级分类';


--
-- TOC entry 5197 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.category_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.category_path IS '完整分类路径，如：基站/近端设备/室内型';


--
-- TOC entry 5198 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.created_by IS '创建用户ID';


--
-- TOC entry 5199 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.reference_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.reference_price IS '参考价格（保存时的单价）';


--
-- TOC entry 5200 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.usage_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.usage_count IS '使用次数';


--
-- TOC entry 5201 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.last_used_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.last_used_at IS '最后使用时间';


--
-- TOC entry 5202 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.created_at IS '创建时间';


--
-- TOC entry 5203 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.updated_at IS '更新时间';


--
-- TOC entry 5204 (class 0 OID 0)
-- Dependencies: 385
-- Name: COLUMN temp_products.is_deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.is_deleted IS '是否已删除';


--
-- TOC entry 386 (class 1259 OID 24371)
-- Name: temp_products_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.temp_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5205 (class 0 OID 0)
-- Dependencies: 386
-- Name: temp_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.temp_products_id_seq OWNED BY public.temp_products.id;


--
-- TOC entry 387 (class 1259 OID 24372)
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
-- TOC entry 5206 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.version_id IS '版本ID';


--
-- TOC entry 5207 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.from_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.from_version IS '升级前版本';


--
-- TOC entry 5208 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.to_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.to_version IS '升级后版本';


--
-- TOC entry 5209 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.upgrade_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_date IS '升级时间';


--
-- TOC entry 5210 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.upgrade_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_type IS '升级类型：manual/automatic';


--
-- TOC entry 5211 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.status IS '升级状态：success/failed/rollback';


--
-- TOC entry 5212 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.upgrade_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_notes IS '升级说明';


--
-- TOC entry 5213 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.error_message IS '错误信息（如果升级失败）';


--
-- TOC entry 5214 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.duration_seconds; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.duration_seconds IS '升级耗时（秒）';


--
-- TOC entry 5215 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.operator_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.operator_id IS '操作人员ID';


--
-- TOC entry 5216 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.operator_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.operator_name IS '操作人员姓名';


--
-- TOC entry 5217 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.environment IS '升级环境';


--
-- TOC entry 5218 (class 0 OID 0)
-- Dependencies: 387
-- Name: COLUMN upgrade_logs.server_info; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.server_info IS '服务器信息';


--
-- TOC entry 388 (class 1259 OID 24377)
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
-- TOC entry 5219 (class 0 OID 0)
-- Dependencies: 388
-- Name: upgrade_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.upgrade_logs_id_seq OWNED BY public.upgrade_logs.id;


--
-- TOC entry 389 (class 1259 OID 24378)
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
-- TOC entry 5220 (class 0 OID 0)
-- Dependencies: 389
-- Name: COLUMN user_event_subscriptions.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.user_id IS '订阅者用户ID';


--
-- TOC entry 5221 (class 0 OID 0)
-- Dependencies: 389
-- Name: COLUMN user_event_subscriptions.target_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.target_user_id IS '被订阅的用户ID';


--
-- TOC entry 5222 (class 0 OID 0)
-- Dependencies: 389
-- Name: COLUMN user_event_subscriptions.event_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.event_id IS '事件ID';


--
-- TOC entry 5223 (class 0 OID 0)
-- Dependencies: 389
-- Name: COLUMN user_event_subscriptions.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.enabled IS '是否启用订阅';


--
-- TOC entry 390 (class 1259 OID 24381)
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
-- TOC entry 5224 (class 0 OID 0)
-- Dependencies: 390
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_event_subscriptions_id_seq OWNED BY public.user_event_subscriptions.id;


--
-- TOC entry 391 (class 1259 OID 24382)
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
-- TOC entry 392 (class 1259 OID 24387)
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
-- TOC entry 5225 (class 0 OID 0)
-- Dependencies: 392
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 393 (class 1259 OID 24388)
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
-- TOC entry 5226 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.version_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.version_number IS '版本号，如1.0.0';


--
-- TOC entry 5227 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.version_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.version_name IS '版本名称';


--
-- TOC entry 5228 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.release_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.release_date IS '发布日期';


--
-- TOC entry 5229 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.description IS '版本描述';


--
-- TOC entry 5230 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.is_current; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.is_current IS '是否为当前版本';


--
-- TOC entry 5231 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.environment IS '环境：development/production';


--
-- TOC entry 5232 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.total_features; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_features IS '新增功能数量';


--
-- TOC entry 5233 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.total_fixes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_fixes IS '修复问题数量';


--
-- TOC entry 5234 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.total_improvements; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_improvements IS '改进数量';


--
-- TOC entry 5235 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.git_commit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.git_commit IS 'Git提交哈希';


--
-- TOC entry 5236 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.build_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.build_number IS '构建号';


--
-- TOC entry 5237 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.created_at IS '创建时间';


--
-- TOC entry 5238 (class 0 OID 0)
-- Dependencies: 393
-- Name: COLUMN version_records.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.updated_at IS '更新时间';


--
-- TOC entry 394 (class 1259 OID 24393)
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
-- TOC entry 5239 (class 0 OID 0)
-- Dependencies: 394
-- Name: version_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.version_records_id_seq OWNED BY public.version_records.id;


--
-- TOC entry 269 (class 1259 OID 17163)
-- Name: messages; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.messages (
    topic text NOT NULL,
    extension text NOT NULL,
    payload jsonb,
    event text,
    private boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    inserted_at timestamp without time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL
)
PARTITION BY RANGE (inserted_at);


--
-- TOC entry 263 (class 1259 OID 17000)
-- Name: schema_migrations; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);


--
-- TOC entry 266 (class 1259 OID 17023)
-- Name: subscription; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.subscription (
    id bigint NOT NULL,
    subscription_id uuid NOT NULL,
    entity regclass NOT NULL,
    filters realtime.user_defined_filter[] DEFAULT '{}'::realtime.user_defined_filter[] NOT NULL,
    claims jsonb NOT NULL,
    claims_role regrole GENERATED ALWAYS AS (realtime.to_regrole((claims ->> 'role'::text))) STORED NOT NULL,
    created_at timestamp without time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);


--
-- TOC entry 265 (class 1259 OID 17022)
-- Name: subscription_id_seq; Type: SEQUENCE; Schema: realtime; Owner: -
--

ALTER TABLE realtime.subscription ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME realtime.subscription_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 246 (class 1259 OID 16544)
-- Name: buckets; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.buckets (
    id text NOT NULL,
    name text NOT NULL,
    owner uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    public boolean DEFAULT false,
    avif_autodetection boolean DEFAULT false,
    file_size_limit bigint,
    allowed_mime_types text[],
    owner_id text
);


--
-- TOC entry 5240 (class 0 OID 0)
-- Dependencies: 246
-- Name: COLUMN buckets.owner; Type: COMMENT; Schema: storage; Owner: -
--

COMMENT ON COLUMN storage.buckets.owner IS 'Field is deprecated, use owner_id instead';


--
-- TOC entry 248 (class 1259 OID 16586)
-- Name: migrations; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.migrations (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    hash character varying(40) NOT NULL,
    executed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- TOC entry 247 (class 1259 OID 16559)
-- Name: objects; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.objects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bucket_id text,
    name text,
    owner uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_accessed_at timestamp with time zone DEFAULT now(),
    metadata jsonb,
    path_tokens text[] GENERATED ALWAYS AS (string_to_array(name, '/'::text)) STORED,
    version text,
    owner_id text,
    user_metadata jsonb
);


--
-- TOC entry 5241 (class 0 OID 0)
-- Dependencies: 247
-- Name: COLUMN objects.owner; Type: COMMENT; Schema: storage; Owner: -
--

COMMENT ON COLUMN storage.objects.owner IS 'Field is deprecated, use owner_id instead';


--
-- TOC entry 270 (class 1259 OID 17211)
-- Name: s3_multipart_uploads; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.s3_multipart_uploads (
    id text NOT NULL,
    in_progress_size bigint DEFAULT 0 NOT NULL,
    upload_signature text NOT NULL,
    bucket_id text NOT NULL,
    key text NOT NULL COLLATE pg_catalog."C",
    version text NOT NULL,
    owner_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    user_metadata jsonb
);


--
-- TOC entry 271 (class 1259 OID 17225)
-- Name: s3_multipart_uploads_parts; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.s3_multipart_uploads_parts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    upload_id text NOT NULL,
    size bigint DEFAULT 0 NOT NULL,
    part_number integer NOT NULL,
    bucket_id text NOT NULL,
    key text NOT NULL COLLATE pg_catalog."C",
    etag text NOT NULL,
    owner_id text,
    version text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- TOC entry 3878 (class 2604 OID 16508)
-- Name: refresh_tokens id; Type: DEFAULT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('auth.refresh_tokens_id_seq'::regclass);


--
-- TOC entry 3911 (class 2604 OID 24394)
-- Name: action_reply id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply ALTER COLUMN id SET DEFAULT nextval('public.action_reply_id_seq'::regclass);


--
-- TOC entry 3912 (class 2604 OID 24395)
-- Name: actions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions ALTER COLUMN id SET DEFAULT nextval('public.actions_id_seq'::regclass);


--
-- TOC entry 3913 (class 2604 OID 24396)
-- Name: affiliations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations ALTER COLUMN id SET DEFAULT nextval('public.affiliations_id_seq'::regclass);


--
-- TOC entry 3914 (class 2604 OID 24397)
-- Name: approval_instance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance ALTER COLUMN id SET DEFAULT nextval('public.approval_instance_id_seq'::regclass);


--
-- TOC entry 3915 (class 2604 OID 24398)
-- Name: approval_process_template id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template ALTER COLUMN id SET DEFAULT nextval('public.approval_process_template_id_seq'::regclass);


--
-- TOC entry 3920 (class 2604 OID 24399)
-- Name: approval_step id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step ALTER COLUMN id SET DEFAULT nextval('public.approval_step_id_seq'::regclass);


--
-- TOC entry 3926 (class 2604 OID 24400)
-- Name: change_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs ALTER COLUMN id SET DEFAULT nextval('public.change_logs_id_seq'::regclass);


--
-- TOC entry 3927 (class 2604 OID 24401)
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- TOC entry 3928 (class 2604 OID 24402)
-- Name: company_assets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_assets ALTER COLUMN id SET DEFAULT nextval('public.company_assets_id_seq'::regclass);


--
-- TOC entry 3929 (class 2604 OID 24403)
-- Name: contacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts ALTER COLUMN id SET DEFAULT nextval('public.contacts_id_seq'::regclass);


--
-- TOC entry 4047 (class 2604 OID 26538)
-- Name: data_field_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_field_config ALTER COLUMN id SET DEFAULT nextval('public.data_field_config_id_seq'::regclass);


--
-- TOC entry 4044 (class 2604 OID 26480)
-- Name: data_table_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_table_config ALTER COLUMN id SET DEFAULT nextval('public.data_table_config_id_seq'::regclass);


--
-- TOC entry 3930 (class 2604 OID 24404)
-- Name: departments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments ALTER COLUMN id SET DEFAULT nextval('public.departments_id_seq'::regclass);


--
-- TOC entry 3931 (class 2604 OID 24405)
-- Name: dev_product_specs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs ALTER COLUMN id SET DEFAULT nextval('public.dev_product_specs_id_seq'::regclass);


--
-- TOC entry 3932 (class 2604 OID 24406)
-- Name: dev_products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products ALTER COLUMN id SET DEFAULT nextval('public.dev_products_id_seq'::regclass);


--
-- TOC entry 3934 (class 2604 OID 24407)
-- Name: dictionaries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries ALTER COLUMN id SET DEFAULT nextval('public.dictionaries_id_seq'::regclass);


--
-- TOC entry 3936 (class 2604 OID 24408)
-- Name: event_registry id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry ALTER COLUMN id SET DEFAULT nextval('public.event_registry_id_seq'::regclass);


--
-- TOC entry 3937 (class 2604 OID 24409)
-- Name: expense_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense_details ALTER COLUMN id SET DEFAULT nextval('public.expense_details_id_seq'::regclass);


--
-- TOC entry 3942 (class 2604 OID 24410)
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.expenses_id_seq'::regclass);


--
-- TOC entry 3945 (class 2604 OID 24411)
-- Name: feature_changes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes ALTER COLUMN id SET DEFAULT nextval('public.feature_changes_id_seq'::regclass);


--
-- TOC entry 3946 (class 2604 OID 24412)
-- Name: five_star_project_baselines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.five_star_project_baselines ALTER COLUMN id SET DEFAULT nextval('public.five_star_project_baselines_id_seq'::regclass);


--
-- TOC entry 4045 (class 2604 OID 26501)
-- Name: formula_templates_extended id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formula_templates_extended ALTER COLUMN id SET DEFAULT nextval('public.formula_templates_extended_id_seq'::regclass);


--
-- TOC entry 3947 (class 2604 OID 24413)
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- TOC entry 3948 (class 2604 OID 24414)
-- Name: inventory_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions ALTER COLUMN id SET DEFAULT nextval('public.inventory_transactions_id_seq'::regclass);


--
-- TOC entry 4042 (class 2604 OID 26458)
-- Name: performance_formula_templates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_formula_templates ALTER COLUMN id SET DEFAULT nextval('public.performance_formula_templates_id_seq'::regclass);


--
-- TOC entry 4040 (class 2604 OID 26428)
-- Name: performance_metrics_definition id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_metrics_definition ALTER COLUMN id SET DEFAULT nextval('public.performance_metrics_definition_id_seq'::regclass);


--
-- TOC entry 3949 (class 2604 OID 24415)
-- Name: performance_statistics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_statistics ALTER COLUMN id SET DEFAULT nextval('public.performance_statistics_id_seq'::regclass);


--
-- TOC entry 3952 (class 2604 OID 24416)
-- Name: performance_targets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_targets ALTER COLUMN id SET DEFAULT nextval('public.performance_targets_id_seq'::regclass);


--
-- TOC entry 3957 (class 2604 OID 24417)
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- TOC entry 3960 (class 2604 OID 24418)
-- Name: pricing_order_approval_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_approval_records_id_seq'::regclass);


--
-- TOC entry 3961 (class 2604 OID 24419)
-- Name: pricing_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_details_id_seq'::regclass);


--
-- TOC entry 3963 (class 2604 OID 24420)
-- Name: pricing_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders ALTER COLUMN id SET DEFAULT nextval('public.pricing_orders_id_seq'::regclass);


--
-- TOC entry 3967 (class 2604 OID 24421)
-- Name: product_categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories ALTER COLUMN id SET DEFAULT nextval('public.product_categories_id_seq'::regclass);


--
-- TOC entry 3968 (class 2604 OID 24422)
-- Name: product_code_field_options id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_options_id_seq'::regclass);


--
-- TOC entry 3969 (class 2604 OID 24423)
-- Name: product_code_field_values id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_values_id_seq'::regclass);


--
-- TOC entry 3970 (class 2604 OID 24424)
-- Name: product_code_fields id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields ALTER COLUMN id SET DEFAULT nextval('public.product_code_fields_id_seq'::regclass);


--
-- TOC entry 3971 (class 2604 OID 24425)
-- Name: product_codes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes ALTER COLUMN id SET DEFAULT nextval('public.product_codes_id_seq'::regclass);


--
-- TOC entry 3972 (class 2604 OID 24426)
-- Name: product_regions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_regions ALTER COLUMN id SET DEFAULT nextval('public.product_regions_id_seq'::regclass);


--
-- TOC entry 3973 (class 2604 OID 24427)
-- Name: product_subcategories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories ALTER COLUMN id SET DEFAULT nextval('public.product_subcategories_id_seq'::regclass);


--
-- TOC entry 3974 (class 2604 OID 24428)
-- Name: products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- TOC entry 3977 (class 2604 OID 24429)
-- Name: project_customer_associations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_customer_associations ALTER COLUMN id SET DEFAULT nextval('public.project_customer_associations_id_seq'::regclass);


--
-- TOC entry 3978 (class 2604 OID 24430)
-- Name: project_members id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members ALTER COLUMN id SET DEFAULT nextval('public.project_members_id_seq'::regclass);


--
-- TOC entry 3979 (class 2604 OID 24431)
-- Name: project_rating_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records ALTER COLUMN id SET DEFAULT nextval('public.project_rating_records_id_seq'::regclass);


--
-- TOC entry 3980 (class 2604 OID 24432)
-- Name: project_scoring_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_config_id_seq'::regclass);


--
-- TOC entry 3985 (class 2604 OID 24433)
-- Name: project_scoring_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_records_id_seq'::regclass);


--
-- TOC entry 3990 (class 2604 OID 24434)
-- Name: project_stage_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history ALTER COLUMN id SET DEFAULT nextval('public.project_stage_history_id_seq'::regclass);


--
-- TOC entry 3992 (class 2604 OID 24435)
-- Name: project_total_scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores ALTER COLUMN id SET DEFAULT nextval('public.project_total_scores_id_seq'::regclass);


--
-- TOC entry 4002 (class 2604 OID 24436)
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- TOC entry 4008 (class 2604 OID 24437)
-- Name: purchase_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details ALTER COLUMN id SET DEFAULT nextval('public.purchase_order_details_id_seq'::regclass);


--
-- TOC entry 4009 (class 2604 OID 24438)
-- Name: purchase_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders ALTER COLUMN id SET DEFAULT nextval('public.purchase_orders_id_seq'::regclass);


--
-- TOC entry 4010 (class 2604 OID 24439)
-- Name: quotation_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details ALTER COLUMN id SET DEFAULT nextval('public.quotation_details_id_seq'::regclass);


--
-- TOC entry 4012 (class 2604 OID 24440)
-- Name: quotations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations ALTER COLUMN id SET DEFAULT nextval('public.quotations_id_seq'::regclass);


--
-- TOC entry 4043 (class 2604 OID 26467)
-- Name: role_performance_access id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_access ALTER COLUMN id SET DEFAULT nextval('public.role_performance_access_id_seq'::regclass);


--
-- TOC entry 4041 (class 2604 OID 26438)
-- Name: role_performance_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_config ALTER COLUMN id SET DEFAULT nextval('public.role_performance_config_id_seq'::regclass);


--
-- TOC entry 4046 (class 2604 OID 26515)
-- Name: role_performance_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_items ALTER COLUMN id SET DEFAULT nextval('public.role_performance_items_id_seq'::regclass);


--
-- TOC entry 4023 (class 2604 OID 24441)
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- TOC entry 4026 (class 2604 OID 24442)
-- Name: settlement_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_details_id_seq'::regclass);


--
-- TOC entry 4027 (class 2604 OID 24443)
-- Name: settlement_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_order_details_id_seq'::regclass);


--
-- TOC entry 4029 (class 2604 OID 24444)
-- Name: settlement_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders ALTER COLUMN id SET DEFAULT nextval('public.settlement_orders_id_seq'::regclass);


--
-- TOC entry 4031 (class 2604 OID 24445)
-- Name: settlements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements ALTER COLUMN id SET DEFAULT nextval('public.settlements_id_seq'::regclass);


--
-- TOC entry 4032 (class 2604 OID 24446)
-- Name: solution_manager_email_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings ALTER COLUMN id SET DEFAULT nextval('public.solution_manager_email_settings_id_seq'::regclass);


--
-- TOC entry 4033 (class 2604 OID 24447)
-- Name: system_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics ALTER COLUMN id SET DEFAULT nextval('public.system_metrics_id_seq'::regclass);


--
-- TOC entry 4034 (class 2604 OID 24448)
-- Name: system_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings ALTER COLUMN id SET DEFAULT nextval('public.system_settings_id_seq'::regclass);


--
-- TOC entry 4035 (class 2604 OID 24449)
-- Name: temp_products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temp_products ALTER COLUMN id SET DEFAULT nextval('public.temp_products_id_seq'::regclass);


--
-- TOC entry 4036 (class 2604 OID 24450)
-- Name: upgrade_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs ALTER COLUMN id SET DEFAULT nextval('public.upgrade_logs_id_seq'::regclass);


--
-- TOC entry 4037 (class 2604 OID 24451)
-- Name: user_event_subscriptions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions ALTER COLUMN id SET DEFAULT nextval('public.user_event_subscriptions_id_seq'::regclass);


--
-- TOC entry 4038 (class 2604 OID 24452)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4039 (class 2604 OID 24453)
-- Name: version_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records ALTER COLUMN id SET DEFAULT nextval('public.version_records_id_seq'::regclass);


--
-- TOC entry 4725 (class 0 OID 16523)
-- Dependencies: 244
-- Data for Name: audit_log_entries; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.audit_log_entries (instance_id, id, payload, created_at, ip_address) FROM stdin;
\.


--
-- TOC entry 4739 (class 0 OID 16925)
-- Dependencies: 261
-- Data for Name: flow_state; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.flow_state (id, user_id, auth_code, code_challenge_method, code_challenge, provider_type, provider_access_token, provider_refresh_token, created_at, updated_at, authentication_method, auth_code_issued_at) FROM stdin;
\.


--
-- TOC entry 4730 (class 0 OID 16723)
-- Dependencies: 252
-- Data for Name: identities; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.identities (provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at, id) FROM stdin;
\.


--
-- TOC entry 4724 (class 0 OID 16516)
-- Dependencies: 243
-- Data for Name: instances; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.instances (id, uuid, raw_base_config, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4734 (class 0 OID 16812)
-- Dependencies: 256
-- Data for Name: mfa_amr_claims; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.mfa_amr_claims (session_id, created_at, updated_at, authentication_method, id) FROM stdin;
\.


--
-- TOC entry 4733 (class 0 OID 16800)
-- Dependencies: 255
-- Data for Name: mfa_challenges; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.mfa_challenges (id, factor_id, created_at, verified_at, ip_address, otp_code, web_authn_session_data) FROM stdin;
\.


--
-- TOC entry 4732 (class 0 OID 16787)
-- Dependencies: 254
-- Data for Name: mfa_factors; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.mfa_factors (id, user_id, friendly_name, factor_type, status, created_at, updated_at, secret, phone, last_challenged_at, web_authn_credential, web_authn_aaguid) FROM stdin;
\.


--
-- TOC entry 4740 (class 0 OID 16975)
-- Dependencies: 262
-- Data for Name: one_time_tokens; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.one_time_tokens (id, user_id, token_type, token_hash, relates_to, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4723 (class 0 OID 16505)
-- Dependencies: 242
-- Data for Name: refresh_tokens; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.refresh_tokens (instance_id, id, token, user_id, revoked, created_at, updated_at, parent, session_id) FROM stdin;
\.


--
-- TOC entry 4737 (class 0 OID 16854)
-- Dependencies: 259
-- Data for Name: saml_providers; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.saml_providers (id, sso_provider_id, entity_id, metadata_xml, metadata_url, attribute_mapping, created_at, updated_at, name_id_format) FROM stdin;
\.


--
-- TOC entry 4738 (class 0 OID 16872)
-- Dependencies: 260
-- Data for Name: saml_relay_states; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.saml_relay_states (id, sso_provider_id, request_id, for_email, redirect_to, created_at, updated_at, flow_state_id) FROM stdin;
\.


--
-- TOC entry 4726 (class 0 OID 16531)
-- Dependencies: 245
-- Data for Name: schema_migrations; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.schema_migrations (version) FROM stdin;
20171026211738
20171026211808
20171026211834
20180103212743
20180108183307
20180119214651
20180125194653
00
20210710035447
20210722035447
20210730183235
20210909172000
20210927181326
20211122151130
20211124214934
20211202183645
20220114185221
20220114185340
20220224000811
20220323170000
20220429102000
20220531120530
20220614074223
20220811173540
20221003041349
20221003041400
20221011041400
20221020193600
20221021073300
20221021082433
20221027105023
20221114143122
20221114143410
20221125140132
20221208132122
20221215195500
20221215195800
20221215195900
20230116124310
20230116124412
20230131181311
20230322519590
20230402418590
20230411005111
20230508135423
20230523124323
20230818113222
20230914180801
20231027141322
20231114161723
20231117164230
20240115144230
20240214120130
20240306115329
20240314092811
20240427152123
20240612123726
20240729123726
20240802193726
20240806073726
20241009103726
\.


--
-- TOC entry 4731 (class 0 OID 16753)
-- Dependencies: 253
-- Data for Name: sessions; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.sessions (id, user_id, created_at, updated_at, factor_id, aal, not_after, refreshed_at, user_agent, ip, tag) FROM stdin;
\.


--
-- TOC entry 4736 (class 0 OID 16839)
-- Dependencies: 258
-- Data for Name: sso_domains; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.sso_domains (id, sso_provider_id, domain, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4735 (class 0 OID 16830)
-- Dependencies: 257
-- Data for Name: sso_providers; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.sso_providers (id, resource_id, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4721 (class 0 OID 16493)
-- Dependencies: 240
-- Data for Name: users; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at, invited_at, confirmation_token, confirmation_sent_at, recovery_token, recovery_sent_at, email_change_token_new, email_change, email_change_sent_at, last_sign_in_at, raw_app_meta_data, raw_user_meta_data, is_super_admin, created_at, updated_at, phone, phone_confirmed_at, phone_change, phone_change_token, phone_change_sent_at, email_change_token_current, email_change_confirm_status, banned_until, reauthentication_token, reauthentication_sent_at, is_sso_user, deleted_at, is_anonymous) FROM stdin;
\.


--
-- TOC entry 4746 (class 0 OID 23989)
-- Dependencies: 272
-- Data for Name: action_reply; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.action_reply (id, action_id, parent_reply_id, content, owner_id, created_at, updated_at) FROM stdin;
1	4	\N	Ms. Cindy say they will drop the project as the end user not agree to increase the budget for whole security system.	2	2025-08-05 09:28:33.954493	2025-08-05 09:28:33.954499
2	44	\N	We had open an WeChat group with BHJ's engineering team and had include Fu Zhong in the group. \nFu Zhong will be our representative to continue liaison with the team for project design and boom list update.	2	2025-08-05 09:36:38.233996	2025-08-05 09:36:38.234002
3	36	\N	目前N地块采用全新技术方案数字远端机重新提交给EPG向下的6家系统集成商，目前还未确定是哪家中标。	12	2025-08-11 03:40:37.501837	2025-08-11 03:40:37.501842
4	39	\N	已确定朗茂中标，设计暂时未开始！G\\M 交付压力比较大，他们暂时没有时间推进J地块	12	2025-08-11 03:41:39.601367	2025-08-11 03:41:39.601373
\.


--
-- TOC entry 4748 (class 0 OID 23995)
-- Dependencies: 274
-- Data for Name: actions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.actions (id, date, contact_id, company_id, project_id, communication, created_at, owner_id, is_shared) FROM stdin;
31	2025-07-23	\N	46	19	FMTCS Mr. Fu told project still in planning stage.	2025-07-23 05:50:17.562049	3	t
35	2025-07-23	\N	44	17	FMTCS Mr. Fu told these 3 projects still in bidding stages and seems like Longmotive having higher chance to secure.	2025-07-23 06:03:41.309965	3	t
36	2025-07-24	\N	44	12	EPG Secured this GDS NTP Block N but installer have not appoint yet and estimate delivery will be this year September. (FMTCS Mr. Fu told NTP - Block F still in assessment and Trac Consult's Eric rejected EPG T&C submission due to supporting rooms & cabins still lack of antennas. /NTP - H ready delivery to EPG's installer YSC.)	2025-07-24 02:00:43.94942	3	t
4	2025-06-30	\N	16	6	Followed up the status with Ms. Cindy and the end user Jabil had feedback budgetary price for security system not included RF system are 500K USD. \r\nBHJ's own quoted system was already ~700K USD thus they will revised back their own quotation. \r\nRF system is still keep in references on owner site. 	2025-06-30 08:07:17.243446	2	t
5	2025-07-01	22	31	\N	Understand from Mr. Fairs in the past for ICT and Security system project they are involve on CCTV,  Door / Entrance Access , Gate Barrier, PA , Alarm system more. \r\nThey do use walkie talkie but is just for their internal team communication purpose. \r\nHad brief him the fundamental how walkie-talkie system setup inside a building and shared him few projects references in difference application. \r\nNext we will organize a presentation with his team.  	2025-07-01 01:50:31.679603	2	t
6	2025-07-01	23	14	\N	Mr. How had shared us the layout plan for Exsim DC, EX1 & EX2 which want us to propose our system. \r\nCurrently the client is only using point-to-point type only. \r\nMymeta would like us to do propose with our system for improvement and 	2025-07-01 02:26:37.589509	2	t
7	2025-02-27	26	30	\N	27/2/2025: Asked TA favor to check their quoted companies and found Asalcom support SKA to secured this Yondr DC @ Kulai and highlight to Sunway Mr. Tan & Chong that necessary to request radio equipment type approval from supplier.                                                                                                                                                                                      250226: Walk in visit and follow up the Tondr DC progress and Tan told that these 2 days just confirmed the proposal with end-user and will award to SKA Tech. One of the important reason that Oconner's can not comply project completion end of April and quoted higher price.  	2025-07-08 01:44:33.106621	3	t
8	2025-02-16	21	30	\N	16/2/25: Visit to meet project manager Mr. Chong to follow up Yondr Data Centre @ KIDEX, Kulai, Johor and this hyperscale 300 MW DC will complete in this year and receive Motorola proposal Radio over IP (RoIP) solutions to this DC requirement. 	2025-07-08 01:51:15.452018	3	t
9	2025-03-06	18	29	\N	250306: Courtesy visit to check NextDC status and told they succeed as a maincon for phase 1 but their package only building infra and C&S. HVAC package under Progress Centre Eng & Electrical & ELV package will award to MCC Technique. Plan for Phase 2 to P4 to offer all M&E into thier packages. Interested to our RFoF DAS System due to no resource and support to RF and future will call us for design support once project receive RF inquiry.	2025-07-08 01:55:47.627126	3	t
10	2025-03-10	17	27	\N	250310: Follow up the NextDC and check any RF inquiry from their new projects. Told recently running few residential projects which no RF inquiry in design and the NextDC only secured the electrical, ELV & ICT cable trunking & tray package. RF will park under surveillance security package and recommend to contact SKA Tech & project manger name Mr. Selvarajah.      	2025-07-08 01:57:19.265362	3	t
11	2025-03-13	11	26	\N	250313: Courtesy visit to present RFoF DAS system and checked their projects status. Told that B-Global was DC specialist for project management and design consultant and KL team handle YTL DC phase 1 for 80 MW DC & total projects will separate to 6 phase. Told RF design probably under security consultant Trac Consult due to they are new team in Malaysia and interested to work with us if their top management want to include security design for YTL phase 2. Told another Yondr DC handle by Johor team and will check with the PIC and update me later.	2025-07-08 01:58:34.574701	3	t
12	2025-03-26	9	25	\N	250409: Proposed our solution to support design & provide budget for future project bidding and future support them to training their existing team for RFoF DAS system installation.                                                                                                                                                                            250326: Teatime discussion to follow up his on hand projects and told we lost the opportunity to bid Customs, Immigration and Quarantine (CIQ) facilities building for RTS Link project and mid of last year already purchased 4 mil RF equipment with Hytera. Told SKA Tech was pioneer company to participate Malaysia DC projects and had a good profile to secure MNC Data Centre. Like Sunway's Yondr DC project that secured the surveillance package and RF sub to Asalcom. NextDC submission already approved by end-user and initial spec already brand binded to Kenwood & Motorola and not accept China products. The Airtrunk DC (JHB 1) surveillance package already supplied by SKA and new JHB 2 already on hand but the security consultant Control Risks exclude RF design in these 2 projects. Checked Sunway secured projects for Amazon & Microsoft DC and told not participate due to limited profit margin for all equipment brand and model binded & request global vendor accreditation to these 2 projects.	2025-07-08 02:00:25.327957	3	t
13	2025-04-18	8	24	\N	250418: Courtesy visit and checked the INV Lithium Battery plant and told this overall design from China. Building structural design and lithium battery processing equipment same as enduser China plant. His roles only submission consultant and without RF in design and told RF system will not under CCYR package that enduser will appoint existing China contractors for their processing & plant operation system. Highlighted the RF equipment type approval to Kong.	2025-07-08 02:01:30.642637	3	t
14	2025-04-15	7	23	\N	250415: Courtesy visit to present our RFoF DAS and checked their project status to Exsim Data Centre @ Bukit Jalil. Told that total 2 phases to this project and phase 1 structural almost complete and estimate completion end of year 2025. Phase 2 waiting for owner Exsim's greenlight ro proceed due to their anchor tenant cancelled the contract. Told not notice this two-way radio or DAS system in their contract and we can follow up with their subcon DCD Technology to check any inquiry to the system.	2025-07-08 02:02:50.57238	3	t
15	2025-07-09	24	14	\N	Had send out our offer and drawing to Mr. Chong. \r\nAs per their request our quoted system is with advance model OMU and ORU for redundancy feature. \r\nDiscussed with Mr. Chong, we will prepare another quotation with basic model for price and features comparison.\r\nThe plan were are already built up and currently they are using point to point walkie-talkie system only thus we are preparing new PPT to explain why and the advantages of using walkie-talkie system in datacenter.\r\n \r\n	2025-07-09 01:27:44.420283	2	t
16	2025-06-30	28	32	\N	Ms. Hu told some prominent brand like Motorola already spec in contract for repeaters & two-way radios during tender call and not allow to amend. And recommend maincon CCYR contact Mr. Zhao to let us follow for Thailand BDC project.	2025-07-09 07:08:58.009366	3	t
37	2025-07-24	\N	44	14	FMTCS Mr. Fu told order was issued and now waiting for delivery arrangement.	2025-07-24 02:03:35.425203	3	t
38	2025-07-24	\N	44	21	NTP - K & L still in bidding stage between Longmotive & EPG.	2025-07-24 02:07:37.751282	3	t
17	2025-07-03	29	33	\N	Met with L J Wong to present our proposal for Bridge DC MY02 @ Cyberjaya and told that already submitted to end-user Ms. 胡 for approval but haven't receive any comments from BDC Beijing team. Checked CCIE's submission and brands submit Evertac & Motorola as per our design, but exclude any uplink & downlink model. Explained importancy for signal power distribution & enable to add OMU for future expansion as per Ms. 胡 concerned. Wong told will follow up with CCIE because future operation not allow this system to stop & add on uplink & downlink for OMU expansion. Wong told started planning for MY02 2nd phase but haven't confirm will add on new basestation or link from phase 1.                                                                                                                                               Courtesy visit to checked PIC to handle Bridge DC MY02 @ Cyberjaya Mr. Teo told they are submission consultant and overall design came from China's end-user & maincon CCIE team. Briefed our Evertac's background and capabilities that can support them for RF system in BDC 02 & future project. Follow up RFoF DAS design with Mr. Wong and informed BDC 02 will start T&C end of July and we have to support CCIE team for equipment delivery on time and arrange online discussion with CCIE's Bijing technical Ms. 胡桂霞 to clarify their question to the design part.	2025-07-09 07:16:16.42389	3	t
18	2025-07-02	32	37	\N	Follow up YTL DC @ Kulai with Azri and told this 275 acre land reserve for solar power & data centre campus. Planning for 12 DC buildings with total 500MW capacity. YTL JC1 & 2 already completed and JDC3 Hyperscale AI facility & JDC6 Colocation facility will handover in next quater. Told this project that totally no RF in design and will depends on operation team request. 	2025-07-10 01:48:21.270241	3	t
19	2025-07-11	35	20	\N	Sharing with her the new opportunities of feasibility study Kuching new airport  by Netherland Airport Consult partnership with Jasa Consult ( Sawarak ) locally. \r\nDiscussed with Ms. Doreen , we will organize an training section with her technical team on 22th July morning. \r\nBeside we also had shared her another opportunities in upgrading Walkie-Talkie System on Mercure Miri City Centre, Miri Sarawak. \r\nPassed her the PIC contact number and she will approach the opportunities locally. 	2025-07-11 09:22:29.766706	2	t
20	2025-07-16	51	40	\N	Chat with Mr. Lai and understand from him that they previously won the MY06 & 07 from YSC. \r\nThe project still on going and not yet pass the test and commissioning stage. \r\nHe are using RFoF DAS system also but not disclose the brand. \r\nBelieve the DAS system is from Hytera. \r\n\r\nHe had one inquiries for ORU low watt replacement and we had recommend RFT-BDA400B LT/M model to him. \r\nHad request him to bring the existing OMU / ORU to Triple Access to test the compatibility. \r\n	2025-07-16 07:21:29.916913	2	t
21	2025-07-16	52	41	\N	Contacted Ms. Amelia for introduction of our company. \r\nMs. Amelia know Triple Access for many year and she had good relationship with Mr. Clayton also. \r\nWe had understand from SKA Technology previously NEXT DC data center projects which using RFoF DAS system had awarded to Ms. Amelia company. \r\nTry to approach her to understand what brand of RFoF DAS system they are using but Ms. Amelia do not disclose it to us. \r\nWill try to build up relationship with her to explore more how to co-operate in future. 	2025-07-16 07:32:54.471554	2	t
23	2025-07-16	55	43	\N	They have an opportunity replacement of OMU and ORU for KLCC. \r\nThese opportunity will be handle directly by Triple Access Mr. Yusry. 	2025-07-16 08:47:52.010232	2	t
24	2025-07-16	54	42	\N	They have an opportunity to supply radio system for Google Data Center located at Elmina Business Park through main contractor Gamuda DC Infrastructure.\r\nAs understand from Mr. Yusry the repeater and walkie talkie require and fix by Google through agreement by TCE are Motorola. \r\nThe distribute antenna system are design by Google and want their supplier to follow their designed coverage drawing. \r\nCurrently pending to receive Google's design for further study.  	2025-07-16 09:05:18.375013	2	t
25	2025-07-18	4	7	\N	Received tender inquiries from Mr. Ihsan and the products requested mainly for outdoor application.\r\nThe requested repeater and walkie talkie (PoC 4G LTE) are Motorola brand thus we can support on the outdoor omni antenna and accessories only. 	2025-07-18 01:42:26.325085	2	t
26	2025-07-18	23	14	\N	Do presentation for the team why we need radio system instead point to point for walkie talkie in datacenter. \r\nTheir engineer are new with the audio system and we have shared the schematic diagram with tropology setup for audio system.\r\nThey are query is that possible our walkie talkie to replace wall mount as fixed station in their control room. \r\nExplain to them walkie talkie are half duplex and the can accept it. \r\n	2025-07-18 01:52:08.083794	2	t
27	2025-07-22	59	21	\N	Do the RFoF DAS system presentation with the team. \r\nPreviously using PBE Axel wireless BDA for their project like KLIA but having problem for support service and lead time. \r\nRecently they just bought EYECOM wireless BDA for testing and upcoming there are one opportunities in Penang Airport which need the wireless BDA.\r\nThey had request if any wireless BDA locally we can bring to their company for demonstration / testing purpose.\r\nBeside they are also now testing EYECOM RFoF OMU & ORU for train application.\r\nQuestion point out are our ORU can be adjustable output voltage or not? \r\n	2025-07-22 09:46:55.468179	2	t
28	2025-07-22	60	48	\N	Approaching Mr. Nadason as we know they are doing radio system. \r\nMeet Mr. Nadason and know from him that they are currently support for PNB 118 project as well. \r\nUnderstand from him currently they are using FUJITSU and Airbus products for the project. 	2025-07-22 09:52:26.194402	2	t
29	2025-07-15	9	25	\N	Lunch meeting with SKA William and recommend Quah to follow their incoming projects. Told Googgle @ Penanf was Googgle office and hopefully can use this chance penetrate to Google's accreditation. Told YTL DC no RF in design & surveilance system used not prominent China brand for cost saving. NextDC already sub to Asalcom for DAS system. Told recently submitted few western project bidding but not specify RF in spec.   	2025-07-22 14:54:00.098135	3	t
30	2025-07-23	\N	49	20	Total 5 blocks DC on this site and SKA secured block 1 with RFoF DAS package sub to Asalcom. MCC Technique Mr. Chu told this block 3 beside the block 1 and probably will share the same repeater. Planning to bid these block 4 & 5 once the design details come out and will need our support for RFoF DAS system.      	2025-07-23 05:45:18.136283	3	t
32	2025-07-23	\N	46	13	Info from FMTCS Mr. Fu told that Longmotive secured this CTP-B project and estimte delivery in Oct 2025.	2025-07-23 05:52:59.494534	3	t
33	2025-07-23	\N	46	18	FMTCS Mr. Fu told EPG having higher opportunity to secure this project and estimate delivery in this year October time.	2025-07-23 05:56:14.010894	3	t
34	2025-07-23	\N	44	16	FMTCS Mr. Fu told already supplied Longmotive for KTP - A, D & E with no issue to these projects. /And now Longmotive secured this KTP - B & C projects with the stage of discussion to preparation the BOM list.	2025-07-23 06:00:31.4603	3	t
39	2025-07-24	\N	44	15	FMTCS Mr. Fu told Longmotive had higher chance to win this NTP - J and estimate delivery in this year September time. 	2025-07-24 02:09:27.068176	3	t
40	2025-07-29	64	50	\N	Having lunch with Mr. Norman the new sale engineer replacing Mr. Yap. \r\nShared our products information and track records in local project with him. \r\nAs understand from him, PNB 118 project they are using SCAN Antenna brand (from Denmark) and deployment via conventionally RF DAS system only. \r\nHe had introduce me Mr. Yeo the sale manager and had get in touch with Mr. Yeo to explore more business cooperation opportunities.	2025-07-29 07:24:06.38093	2	t
41	2025-07-29	57	21	\N	Quoted of our Wireless BDA WD-410 to Mr. Yoga for his tender in Penang Airport. \r\nThey are requesting to preset Uplink = 417-420MHz,  Downlink = 427-430MHz frequency range and had confirm with Mr. Liu Wei we can support that. \r\nNow they are evaluating technically compatibility with their design system. \r\nWill follow up again with the team. 	2025-07-29 07:32:40.575935	2	t
42	2025-07-29	65	51	\N	Meet up Ms. Lina the end user of MY02 project to discuss on the application of MCMC AA frequency. \r\nPreviously Mr. Lai from Stream Communication are help to apply via email for MY06 & MY07. \r\nExplain to her now all application must go through e-Spectra online dashboard instead of email traditionally. \r\nHad check with MCMC officer Ms. Nurfarah do they have existing account or not and if not we will guide the company for new registrations.\r\n\r\nBeside we explore the local P.I.C in-charge locally for next expansion block and phase 2 development. \r\nMs. Lina will help us to find out the P.I.C locally as explain to her we are the local support team and after sale service can be directed to us. \r\n	2025-07-29 07:43:56.544482	2	t
43	2025-07-29	66	52	\N	Meet up Mr. Irwin the director together with MyMeta team. \r\nMyMeta are pushing our proposal to upgrade RF Coverage DAS's system to DcD (their mother company). \r\nShared with Mr. Irwin the importance of RF coverage in their datacenter building and upcoming Mr. Irwin shared there will be CJ12 new building. \r\nMyMeta in-charge for their overall securities and surveillance system. \r\nWill work closely with My-Meta for next new projects.  	2025-07-29 07:59:37.953924	2	t
44	2025-07-29	25	16	\N	Quoted Ms. Cindy for GDS NTP-N project where the inquiries requested by EPG. \r\nEPG had awarded the project and now sourcing for sub-contractor to support them. \r\nEPG also request quote for CTP-A and now pending to receive the floor plan to evaluate the design and system requirement. \r\nBeside understand from Ms. Cindy they are also now bidding for EDGNEX Data Centers by DAMAC in Indonesia. \r\nNo clear information yet are Radio Audio System under their tender scope or not? \r\nWill follow up closely with Ms. Cindy again\r\n 	2025-07-29 08:10:05.156754	2	t
45	2025-07-29	54	42	22	Attended Tender briefing on 25th October 2024, Vertex to request floor plan on official channel - 28 Oct 2024\r\nCompany that participated the tender : Sole Engineering, SLW, OCK, Vertex\r\nSLW is parent company to Sole Engineering proposing AirBus system\r\nOCK is a telco company, working with RADII proposing Hytera\r\nVertex works with TA proposing EVERTAC Solutions and Motorola (TETRA)\r\nO'Connors Engineering approached TA to propose EVERTAC Solution and Motorola (DMR)\r\nO'Connors Engineering is working with new vendor TM (Telekom Malaysia)\r\nSubmitted Evertac's quote to O'Connors \r\n	2025-07-29 08:32:28.90364	2	t
46	2025-07-24	11	26	\N	Provide RFoF DAS system training to Liyana's team and checked their projects status. Told they are lead consultant specialist for Data Centre and their oversea team will provide design concept to support end-user. Recently completed Aims DC @ Cyberjaya & Yondr DC @ Kulai. Follow up the YTL DC project and told our RF will under Trac consult's design but seem like end-user already omitted this RF parts and leave to DC hall tenant or operation demand.        	2025-08-01 05:10:45.051458	3	t
47	2025-07-25	65	51	\N	Met BDC Malaysia team Ms. Lina to let Quah explained the procedure to apply MCMC frequency for MY02 DC and knowing that Lina was administrator and request her to update us MY02 project manager that we can direct support for design & project.	2025-08-01 05:24:40.020946	3	t
48	2025-08-01	67	53	\N	Ms. Hu (Bridge Data Centre @ Beijing) recommend Thailand BDC project that we can follow up with maincon CCYR Mr. Zhao and direct me to ELV SI Ms. Han (Timesfly @ Beijing). Ms. Han told Malaysia BDC MY07B2 already issued PO to local supplier but no idea about the progress and performance. Thailand BDC still wait for the spec & white list to request us to prepare proposal. Highlighted the type approval & frequency apply to comply Thailand authority.	2025-08-04 08:45:28.666109	3	t
49	2025-08-05	65	51	\N	Had share the Authorization Letter template & Application Letter template to Ms. Lina for the team to fill in to fulfill the MCMC application requirement. \r\nBeside had follow up with her to introduce us the PM of the project to discuss and planning together the future expansion and phase 2 new building. 	2025-08-05 08:43:13.418231	2	t
50	2025-08-05	69	54	22	Mr. Woo are now pushing DMR with Evertac's DAS system together with our NetFlex to the main contractor. \r\nThe NetFlex basically to monitor the ORU status only as Mr. Woo commented they have their own way to monitor the repeater status. \r\nOverall Mr. Woo commented the NetFlex package are bit high and we had advise him to push the end user first then only we discuss about package offer for the project. \r\n	2025-08-05 09:55:13.848575	2	t
22	2025-07-16	53	12	\N	Follow up with Mr. Lee for the MCMC application status. \r\nExplain to him the procedure and documents needed for application and he will be the main window to communicate directly with the end user. \r\nWill keep follow up with him again the status . 	2025-07-16 07:39:36.462694	2	t
54	2025-08-06	29	33	9	Meeting with LJ Wong to assist him for MY02 submission approval and told CCIE there still delayed without any resubmission for RF part, although enduser accepted 2 repeaters with 4 chnnels instead of early request for 5 repeaters. Briefed again our RFoF DAS system and highlights the Uplink & downlink for system expansion. Advice Wong to request CCIE BOM list for verification before issue approval. Told 2nd phase still in planning stage and not convenient to disclose details.     	2025-08-12 03:09:40.569303	3	t
55	2025-08-07	85	37	16	Invited Alesandro to visit security consultant Reena and guide him to approach project consultant. Help Reena to check her KTP Block C2 and explained our T&C technical items to let her prepare check list for acceptance approval. Told recently handle block C & D and others KTP block has not pass to her yet and mentioned they do not have manpower and office in Indonesia to support Thailand GDS and no idea which consultant handle to this project. 	2025-08-12 03:17:55.611918	3	t
56	2025-08-08	86	70	\N	Invited Alesandro to visit this M&E consultant for GDS project. Ms. Mimi told KTP block B & E will include security & RF design, other blocks will exlude security package due to short of manpower. Told only support GDS DC in Malaysia and do not involve in Thailand or Indonesia projects due to no counterparts support in these countries. Invite their team to visit KLCC ENGINEER Exhibition.                    	2025-08-12 03:35:47.859437	3	t
57	2025-08-12	91	54	22	Discussed with Mr. Johnson regarding their design technically and our products specification/programming. \r\nMr. Johnson keen to know more about our products detail especially in programming setting side. \r\nBeside the request for data specification for Outdoor and Wall-Mount digital type ORU, they want to know possibility to do redundancy by 2 ORUs supporting same set of antennas system. \r\nReason why the outdoor system are supporting up to 70% of coverage area and not allow to mulfunction. \r\n\r\nBeside they also query about our VSWR threshold setting in ORU and request an demonstration/training of it.\r\nWe are requesting the team to summarize all their query and write us an email directly. \r\nWill discuss accordingly with our tech-support team and plan a on-line training section with the engineer. \r\nTentatively set on coming Tuesday.  	2025-08-12 05:59:26.176803	2	t
58	2025-08-12	84	69	12	Had quoted Bandway Engineering for their tender with EPG. \r\nTheir core business are Building Automation System (BAS) which include supply and install. \r\nCurrently EPG haven't send out the new revised MTO with Digital Type system to them yet thus we are still quoting with the Analog system first.  	2025-08-12 06:22:27.368622	2	t
59	2025-08-12	53	12	8	Mr. Lee had help to get the owner endorsement for MCMC's application form and letter of consent for our frequency application. \r\nNow pending the information of site coordinate. 	2025-08-12 06:44:45.07513	2	t
60	2025-08-12	83	65	22	Talk to Mr. Zanirul and his team are now handling with PNB 118 project. \r\nHe had many experiences on land / on air application of audio system with strong technical know how knowledge. \r\nHe share his challenges facing in industries that many user also tend to have device only for communication not system. \r\nHe like to know more what we can help him in proposing solution for his customer and will set face-to-face appointment with him next week.	2025-08-12 07:46:11.462575	2	t
62	2025-08-12	92	65	31	Mr. Zaimi are in charge for their TM Iskandar Puteri Data Centre (IPDC) and currently the project are in the tier-end. \r\nShared our success story in DayOne with him and he know the project very well also. \r\nThese week he are at the site and will help to find out more information what audio system they are using. \r\n\r\n	2025-08-12 08:01:16.428118	2	t
\.


--
-- TOC entry 4750 (class 0 OID 24001)
-- Dependencies: 276
-- Data for Name: affiliations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.affiliations (id, owner_id, viewer_id, created_at) FROM stdin;
2	9	5	1754470674.2665598
3	3	5	1754470674.2730565
4	2	5	1754470674.2774239
5	6	5	1754470674.2812474
6	4	5	1754470674.2845933
7	7	8	1754470738.6517096
9	2	3	1754558396.914684
10	5	3	1754558396.9188194
11	6	3	1754558396.9226649
12	9	3	1754558396.925952
13	4	3	1754558396.9291391
14	7	3	1754558396.9321384
15	7	2	1754558427.1724126
16	9	2	1754558427.1753733
\.


--
-- TOC entry 4752 (class 0 OID 24005)
-- Dependencies: 278
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
e75c868b86a3
\.


--
-- TOC entry 4753 (class 0 OID 24008)
-- Dependencies: 279
-- Data for Name: approval_instance; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_instance (id, object_id, object_type, current_step, status, started_at, ended_at, process_id, created_by, template_snapshot, template_version) FROM stdin;
4	8	project	1	APPROVED	2025-07-09 02:08:14.634093	2025-07-14 00:58:19.767314	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-07-09T02:08:14.625617", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "\\u7cfb\\u7edf\\u7ba1\\u7406\\u5458", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true}]}	v20250709_020814
3	4	project	1	APPROVED	2025-06-22 15:39:13.876777	2025-06-22 15:39:58.052442	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-22T15:39:13.874943", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "\\u7cfb\\u7edf\\u7ba1\\u7406\\u5458", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true}]}	v20250622_153913
2	3	project	1	APPROVED	2025-06-22 15:38:29.21562	2025-06-22 15:40:16.182924	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-22T15:38:29.213923", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "\\u7cfb\\u7edf\\u7ba1\\u7406\\u5458", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true}]}	v20250622_153829
6	7	project	1	APPROVED	2025-07-09 03:13:45.458661	2025-07-14 00:57:51.921138	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-07-09T03:13:45.448806", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "\\u7cfb\\u7edf\\u7ba1\\u7406\\u5458", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true}]}	v20250709_031345
7	1	expense	3	APPROVED	2025-08-06 06:48:14.800669	2025-08-06 06:49:57.252071	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-08-06T06:48:14.794929", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "\\u7cfb\\u7edf\\u7ba1\\u7406\\u5458", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250806_064814
8	6	expense	1	PENDING	2025-08-12 04:13:40.313311	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-08-12T04:13:40.307183", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250812_041340
9	2	expense	1	PENDING	2025-08-12 04:16:29.86015	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-08-12T04:16:29.853127", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250812_041629
10	7	expense	1	PENDING	2025-08-12 04:52:06.863764	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-08-12T04:52:06.858726", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250812_045206
11	8	expense	1	PENDING	2025-08-12 04:57:47.408637	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-08-12T04:57:47.404009", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250812_045747
\.


--
-- TOC entry 4755 (class 0 OID 24014)
-- Dependencies: 281
-- Data for Name: approval_process_template; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_process_template (id, name, object_type, is_active, created_by, created_at, required_fields, lock_object_on_start, lock_reason, visual_data) FROM stdin;
1	授权备案	project	t	1	2025-06-22 15:34:43.794919	["project_name", "project_type", "report_source"]	t	审批流程进行中，暂时锁定编辑	\N
5	Expense Claim	expense	t	1	2025-08-06 14:32:25.764934	["expense_number"]	t	审批流程进行中，暂时锁定编辑	\N
\.


--
-- TOC entry 4758 (class 0 OID 24024)
-- Dependencies: 284
-- Data for Name: approval_record; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_record (id, instance_id, step_id, approver_id, action, comment, "timestamp") FROM stdin;
2	3	1	1	approve		2025-06-22 15:39:58.035615
3	2	1	1	approve		2025-06-22 15:40:16.16519
9	6	\N	1	approve		2025-07-14 00:57:51.903498
10	4	\N	1	approve		2025-07-14 00:58:19.750648
11	7	5	5	approve		2025-08-06 06:49:01.702384
12	7	6	1	approve		2025-08-06 06:49:29.420637
13	7	7	5	approve		2025-08-06 06:49:57.251956
\.


--
-- TOC entry 4759 (class 0 OID 24030)
-- Dependencies: 285
-- Data for Name: approval_step; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_step (id, process_id, step_order, approver_user_id, step_name, send_email, action_type, action_params, editable_fields, cc_users, cc_enabled, approver_type, description, condition_config, is_conditional, branch_on_reject, skip_conditions, condition_type, branch_on_approve) FROM stdin;
1	1	1	1	申请备案	t	authorization	\N	[]	[1]	t	user	\N	\N	f	\N	\N	\N	\N
5	5	1	5	Finance Review	t	\N	\N	["exchange_rate"]	[]	f	user	\N	\N	f	\N	\N	\N	\N
6	5	2	1	Supervisor Review	t	\N	\N	[]	[]	f	user	\N	\N	f	\N	\N	\N	\N
7	5	3	5	Reimbursement Payment	t	payment_processing	\N	[]	[]	f	user	\N	\N	f	\N	\N	\N	\N
\.


--
-- TOC entry 4761 (class 0 OID 24041)
-- Dependencies: 287
-- Data for Name: change_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.change_logs (id, module_name, table_name, record_id, operation_type, field_name, old_value, new_value, user_id, user_name, created_at, description, ip_address, user_agent, record_info) FROM stdin;
1	user	users	2	CREATE	\N	\N	\N	1	admin	2025-06-22 12:06:52.209732	\N	127.0.0.1	\N	公司: evertacsolutions
2	user	users	3	CREATE	\N	\N	\N	1	admin	2025-06-22 12:07:29.509733	\N	127.0.0.1	\N	公司: evertacsolutions
3	user	users	2	UPDATE	是否激活	False	True	1	admin	2025-06-22 12:07:41.936296	\N	127.0.0.1	\N	公司: evertacsolutions
4	user	users	2	UPDATE	updated_at	1750594011.3797174	1750594061.9256482	1	admin	2025-06-22 12:07:41.936302	\N	127.0.0.1	\N	公司: evertacsolutions
5	user	users	3	UPDATE	是否激活	False	True	1	admin	2025-06-22 12:07:50.902262	\N	127.0.0.1	\N	公司: evertacsolutions
6	user	users	3	UPDATE	updated_at	1750594048.811315	1750594070.8917122	1	admin	2025-06-22 12:07:50.902267	\N	127.0.0.1	\N	公司: evertacsolutions
7	customer	companies	1	CREATE	\N	\N	\N	1	admin	2025-06-22 13:06:59.232455	\N	10.210.81.55	\N	公司: TCE
8	customer	contacts	1	CREATE	\N	\N	\N	1	admin	2025-06-22 13:07:16.885796	\N	10.210.151.204	\N	记录: kelven
9	user	users	1	UPDATE	公司名称	PMA系统	evertacsolutions	1	admin	2025-06-22 13:15:36.306209	\N	10.210.151.204	\N	公司: evertacsolutions
10	user	users	1	UPDATE	电话	\N	None	1	admin	2025-06-22 13:15:36.306215	\N	10.210.151.204	\N	公司: evertacsolutions
11	user	users	1	UPDATE	部门	\N		1	admin	2025-06-22 13:15:36.306219	\N	10.210.151.204	\N	公司: evertacsolutions
12	user	users	1	UPDATE	is_department_manager	\N	False	1	admin	2025-06-22 13:15:36.306222	\N	10.210.151.204	\N	公司: evertacsolutions
13	user	users	1	UPDATE	updated_at	1750597559.7142627	1750598136.2872016	1	admin	2025-06-22 13:15:36.306225	\N	10.210.151.204	\N	公司: evertacsolutions
14	project	projects	1	CREATE	\N	\N	\N	1	admin	2025-06-22 13:50:12.572295	\N	10.210.81.55	\N	项目: UMCD
15	quotation	quotations	1	CREATE	\N	\N	\N	1	admin	2025-06-22 14:52:04.427241	\N	10.210.124.62	\N	报价单: QU202506-001
16	customer	companies	2	CREATE	\N	\N	\N	2	quah	2025-06-22 14:53:23.369939	\N	10.210.151.204	\N	公司: Triple Access
17	customer	companies	3	CREATE	\N	\N	\N	2	quah	2025-06-22 15:04:04.823757	\N	10.210.124.62	\N	公司: Triple Access
18	customer	companies	4	CREATE	\N	\N	\N	2	quah	2025-06-22 15:04:40.910063	\N	10.210.139.124	\N	公司: TDS
19	customer	contacts	2	CREATE	\N	\N	\N	2	quah	2025-06-22 15:05:18.571603	\N	10.210.139.124	\N	记录: JAMEs
20	project	projects	2	CREATE	\N	\N	\N	2	quah	2025-06-22 15:05:42.971552	\N	10.210.139.124	\N	项目: JDMD
21	quotation	quotations	2	CREATE	\N	\N	\N	2	quah	2025-06-22 15:06:16.075001	\N	10.210.166.134	\N	报价单: QU202506-002
22	customer	contacts	2	DELETE	\N	\N	\N	2	quah	2025-06-22 15:31:56.029141	\N	10.210.151.204	\N	记录: JAMEs
23	project	projects	2	DELETE	\N	\N	\N	2	quah	2025-06-22 15:38:02.50613	\N	10.210.151.204	\N	项目: JDMD
24	project	projects	3	CREATE	\N	\N	\N	2	quah	2025-06-22 15:38:23.832979	\N	10.210.151.204	\N	项目: TSED
25	project	projects	4	CREATE	\N	\N	\N	2	quah	2025-06-22 15:39:03.374326	\N	10.210.151.204	\N	项目: UDD D 
26	project	projects	1	DELETE	\N	\N	\N	1	admin	2025-06-22 15:40:28.985859	\N	10.210.166.134	\N	项目: UMCD
27	quotation	quotations	3	CREATE	\N	\N	\N	1	admin	2025-06-22 15:41:09.584433	\N	10.210.151.204	\N	报价单: QU202506-001
28	quotation	quotations	3	UPDATE	currency	MYR	CNY	1	admin	2025-06-22 16:58:05.036031	\N	10.210.124.62	\N	报价单: QU202506-001
29	quotation	quotations	3	UPDATE	updated_at	2025-06-22 15:41:09.561543	2025-06-22 16:58:05.004613	1	admin	2025-06-22 16:58:05.036036	\N	10.210.124.62	\N	报价单: QU202506-001
30	quotation	quotations	4	CREATE	\N	\N	\N	1	admin	2025-06-22 16:58:56.983626	\N	10.210.124.62	\N	报价单: QU202506-001
31	quotation	quotations	4	UPDATE	amount	21933.83	15353.68	1	admin	2025-06-22 16:59:20.490942	\N	10.210.81.55	\N	报价单: QU202506-001
32	quotation	quotations	4	UPDATE	currency	MYR	CNY	1	admin	2025-06-22 16:59:20.490949	\N	10.210.81.55	\N	报价单: QU202506-001
33	quotation	quotations	4	UPDATE	updated_at	2025-06-22 16:58:56.965397	2025-06-22 16:59:20.464586	1	admin	2025-06-22 16:59:20.490953	\N	10.210.81.55	\N	报价单: QU202506-001
34	quotation	quotations	5	CREATE	\N	\N	\N	1	admin	2025-06-22 17:10:56.128838	\N	10.210.81.55	\N	报价单: QU202506-001
35	quotation	quotations	5	UPDATE	amount	61329.520000000004	14400.0	1	admin	2025-06-22 17:41:50.805429	\N	10.210.81.55	\N	报价单: QU202506-001
36	quotation	quotations	5	UPDATE	currency	MYR	USD	1	admin	2025-06-22 17:41:50.805434	\N	10.210.81.55	\N	报价单: QU202506-001
37	quotation	quotations	5	UPDATE	updated_at	2025-06-22 17:10:56.103035	2025-06-22 17:41:50.773059	1	admin	2025-06-22 17:41:50.805436	\N	10.210.81.55	\N	报价单: QU202506-001
38	quotation	quotations	5	UPDATE	amount	14400.0	3290.0	1	admin	2025-06-22 17:42:10.426729	\N	10.210.151.204	\N	报价单: QU202506-001
39	quotation	quotations	5	UPDATE	product_signature	fb1b39b8715f3d9643801859c2b9dc1f	a0179ce456b21ef33a8d90796ee52d58	1	admin	2025-06-22 17:42:10.426735	\N	10.210.151.204	\N	报价单: QU202506-001
40	quotation	quotations	5	UPDATE	updated_at	2025-06-22 17:41:50.773059	2025-06-22 17:42:10.402031	1	admin	2025-06-22 17:42:10.426738	\N	10.210.151.204	\N	报价单: QU202506-001
41	quotation	quotations	5	UPDATE	amount	3290.0	4236.76	1	admin	2025-06-22 17:42:19.476943	\N	10.210.81.55	\N	报价单: QU202506-001
42	quotation	quotations	5	UPDATE	currency	USD	SGD	1	admin	2025-06-22 17:42:19.476947	\N	10.210.81.55	\N	报价单: QU202506-001
43	quotation	quotations	5	UPDATE	updated_at	2025-06-22 17:42:10.402031	2025-06-22 17:42:19.447737	1	admin	2025-06-22 17:42:19.476949	\N	10.210.81.55	\N	报价单: QU202506-001
44	quotation	quotations	5	UPDATE	updated_at	2025-06-22 17:42:19.447737	2025-06-22 17:42:33.604350	1	admin	2025-06-22 17:42:33.628729	\N	10.210.81.55	\N	报价单: QU202506-001
45	quotation	quotations	5	DELETE	\N	\N	\N	1	admin	2025-06-22 17:42:40.631803	\N	10.210.136.236	\N	报价单: QU202506-001
46	quotation	quotations	6	CREATE	\N	\N	\N	1	admin	2025-06-22 17:43:06.569824	\N	10.210.81.55	\N	报价单: QU202506-001
47	quotation	quotations	6	UPDATE	amount	3290.0	4236.76	1	admin	2025-06-22 17:43:17.300618	\N	10.210.136.236	\N	报价单: QU202506-001
48	quotation	quotations	6	UPDATE	currency	USD	SGD	1	admin	2025-06-22 17:43:17.300622	\N	10.210.136.236	\N	报价单: QU202506-001
49	quotation	quotations	6	UPDATE	updated_at	2025-06-22 17:43:06.538653	2025-06-22 17:43:17.279967	1	admin	2025-06-22 17:43:17.300625	\N	10.210.136.236	\N	报价单: QU202506-001
50	quotation	quotations	6	UPDATE	amount	4236.76	14012.08	1	admin	2025-06-22 17:43:35.393798	\N	10.210.151.204	\N	报价单: QU202506-001
51	quotation	quotations	6	UPDATE	currency	SGD	MYR	1	admin	2025-06-22 17:43:35.393802	\N	10.210.151.204	\N	报价单: QU202506-001
52	quotation	quotations	6	UPDATE	updated_at	2025-06-22 17:43:17.279967	2025-06-22 17:43:35.342585	1	admin	2025-06-22 17:43:35.393805	\N	10.210.151.204	\N	报价单: QU202506-001
53	quotation	quotations	7	CREATE	\N	\N	\N	1	admin	2025-06-23 01:20:09.365963	\N	10.210.185.72	\N	报价单: QU202506-001
54	quotation	quotations	7	UPDATE	amount	4636.0	19744.69	1	admin	2025-06-23 01:20:24.572659	\N	10.210.185.72	\N	报价单: QU202506-001
55	quotation	quotations	7	UPDATE	currency	USD	MYR	1	admin	2025-06-23 01:20:24.572663	\N	10.210.185.72	\N	报价单: QU202506-001
56	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:20:09.340186	2025-06-23 01:20:24.535631	1	admin	2025-06-23 01:20:24.572665	\N	10.210.185.72	\N	报价单: QU202506-001
57	quotation	quotations	7	UPDATE	amount	19744.69	4636.0	1	admin	2025-06-23 01:20:49.303565	\N	10.210.106.238	\N	报价单: QU202506-001
58	quotation	quotations	7	UPDATE	currency	MYR	USD	1	admin	2025-06-23 01:20:49.30357	\N	10.210.106.238	\N	报价单: QU202506-001
59	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:20:24.535631	2025-06-23 01:20:49.276568	1	admin	2025-06-23 01:20:49.303572	\N	10.210.106.238	\N	报价单: QU202506-001
60	quotation	quotations	7	UPDATE	amount	4636.0	19744.69	1	admin	2025-06-23 01:20:56.223535	\N	10.210.106.238	\N	报价单: QU202506-001
61	quotation	quotations	7	UPDATE	currency	USD	MYR	1	admin	2025-06-23 01:20:56.223539	\N	10.210.106.238	\N	报价单: QU202506-001
62	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:20:49.276568	2025-06-23 01:20:56.196596	1	admin	2025-06-23 01:20:56.223541	\N	10.210.106.238	\N	报价单: QU202506-001
63	quotation	quotations	7	UPDATE	amount	19744.69	5970.1	1	admin	2025-06-23 01:21:03.622207	\N	10.210.106.238	\N	报价单: QU202506-001
64	quotation	quotations	7	UPDATE	currency	MYR	SGD	1	admin	2025-06-23 01:21:03.622211	\N	10.210.106.238	\N	报价单: QU202506-001
65	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:20:56.196596	2025-06-23 01:21:03.597002	1	admin	2025-06-23 01:21:03.622213	\N	10.210.106.238	\N	报价单: QU202506-001
66	quotation	quotations	7	UPDATE	amount	5970.1	33352.51	1	admin	2025-06-23 01:21:12.643962	\N	10.210.106.238	\N	报价单: QU202506-001
67	quotation	quotations	7	UPDATE	currency	SGD	CNY	1	admin	2025-06-23 01:21:12.643966	\N	10.210.106.238	\N	报价单: QU202506-001
68	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:21:03.597002	2025-06-23 01:21:12.607244	1	admin	2025-06-23 01:21:12.643969	\N	10.210.106.238	\N	报价单: QU202506-001
69	quotation	quotations	7	UPDATE	amount	33352.51	5970.1	1	admin	2025-06-23 01:21:19.979484	\N	10.210.106.238	\N	报价单: QU202506-001
70	quotation	quotations	7	UPDATE	currency	CNY	SGD	1	admin	2025-06-23 01:21:19.979488	\N	10.210.106.238	\N	报价单: QU202506-001
71	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:21:12.607244	2025-06-23 01:21:19.956471	1	admin	2025-06-23 01:21:19.979491	\N	10.210.106.238	\N	报价单: QU202506-001
72	quotation	quotations	7	UPDATE	amount	5970.1	4636.0	1	admin	2025-06-23 01:21:27.126998	\N	10.210.106.238	\N	报价单: QU202506-001
73	quotation	quotations	7	UPDATE	currency	SGD	USD	1	admin	2025-06-23 01:21:27.127002	\N	10.210.106.238	\N	报价单: QU202506-001
74	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:21:19.956471	2025-06-23 01:21:27.103821	1	admin	2025-06-23 01:21:27.127005	\N	10.210.106.238	\N	报价单: QU202506-001
75	quotation	quotations	7	UPDATE	amount	4636.0	33352.52	1	admin	2025-06-23 01:21:33.582042	\N	10.210.106.238	\N	报价单: QU202506-001
76	quotation	quotations	7	UPDATE	currency	USD	CNY	1	admin	2025-06-23 01:21:33.582048	\N	10.210.106.238	\N	报价单: QU202506-001
77	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:21:27.103821	2025-06-23 01:21:33.557582	1	admin	2025-06-23 01:21:33.582053	\N	10.210.106.238	\N	报价单: QU202506-001
78	quotation	quotations	7	UPDATE	amount	33352.52	5970.1	1	admin	2025-06-23 01:21:39.226895	\N	10.210.106.238	\N	报价单: QU202506-001
79	quotation	quotations	7	UPDATE	currency	CNY	SGD	1	admin	2025-06-23 01:21:39.226899	\N	10.210.106.238	\N	报价单: QU202506-001
80	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:21:33.557582	2025-06-23 01:21:39.157663	1	admin	2025-06-23 01:21:39.226902	\N	10.210.106.238	\N	报价单: QU202506-001
81	quotation	quotations	7	UPDATE	amount	5970.1	76126779.6	1	admin	2025-06-23 01:21:45.495548	\N	10.210.106.238	\N	报价单: QU202506-001
82	quotation	quotations	7	UPDATE	currency	SGD	IDR	1	admin	2025-06-23 01:21:45.495552	\N	10.210.106.238	\N	报价单: QU202506-001
83	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:21:39.157663	2025-06-23 01:21:45.472947	1	admin	2025-06-23 01:21:45.495555	\N	10.210.106.238	\N	报价单: QU202506-001
84	quotation	quotations	7	UPDATE	updated_at	2025-06-23 01:21:45.472947	2025-06-23 02:05:43.424047	1	admin	2025-06-23 02:05:43.452358	\N	10.210.151.227	\N	报价单: QU202506-001
85	quotation	quotations	7	UPDATE	implant_total_amount	4636.0	76126788.78	1	admin	2025-06-23 02:09:20.401416	\N	10.210.152.13	\N	报价单: QU202506-001
86	quotation	quotations	7	UPDATE	updated_at	2025-06-23 02:05:43.424047	2025-06-23 02:09:20.363410	1	admin	2025-06-23 02:09:20.401424	\N	10.210.152.13	\N	报价单: QU202506-001
87	quotation	quotations	7	UPDATE	amount	76126779.6	33352.51	1	admin	2025-06-23 02:09:34.388346	\N	10.210.152.13	\N	报价单: QU202506-001
88	quotation	quotations	7	UPDATE	implant_total_amount	76126788.78	33352.52	1	admin	2025-06-23 02:09:34.388355	\N	10.210.152.13	\N	报价单: QU202506-001
89	quotation	quotations	7	UPDATE	currency	IDR	CNY	1	admin	2025-06-23 02:09:34.38836	\N	10.210.152.13	\N	报价单: QU202506-001
90	quotation	quotations	7	UPDATE	updated_at	2025-06-23 02:09:20.363410	2025-06-23 02:09:34.346694	1	admin	2025-06-23 02:09:34.388363	\N	10.210.152.13	\N	报价单: QU202506-001
91	customer	contacts	1	DELETE	\N	\N	\N	1	admin	2025-06-23 02:10:19.861129	\N	10.210.152.13	\N	记录: kelven
92	customer	companies	1	DELETE	\N	\N	\N	1	admin	2025-06-23 02:10:21.037856	\N	10.210.152.13	\N	公司: TCE
93	project	projects	4	DELETE	\N	\N	\N	1	admin	2025-06-23 02:10:41.113056	\N	10.210.152.13	\N	项目: UDD D 
94	project	projects	3	DELETE	\N	\N	\N	1	admin	2025-06-23 02:10:41.166205	\N	10.210.152.13	\N	项目: TSED
95	user	users	3	UPDATE	邮箱	roy.lim@evertacsolutions	roy.lim@evertacsolutions.com	1	admin	2025-06-23 02:11:11.941902	\N	10.210.152.13	\N	公司: evertacsolutions
96	user	users	3	UPDATE	updated_at	1750594070.8917122	1750644671.929452	1	admin	2025-06-23 02:11:11.941909	\N	10.210.152.13	\N	公司: evertacsolutions
97	user	users	2	UPDATE	邮箱	chinyeong.quah@evertacsolutions	chinyeong.quah@evertacsolutions.com	1	admin	2025-06-23 02:11:23.564471	\N	10.210.152.13	\N	公司: evertacsolutions
98	user	users	2	UPDATE	updated_at	1750594061.9256482	1750644683.550111	1	admin	2025-06-23 02:11:23.564478	\N	10.210.152.13	\N	公司: evertacsolutions
99	user	users	2	UPDATE	是否激活	True	False	1	admin	2025-06-23 02:12:08.504365	\N	10.210.152.13	\N	公司: evertacsolutions
100	user	users	2	UPDATE	updated_at	1750644683.550111	1750644728.4865594	1	admin	2025-06-23 02:12:08.504374	\N	10.210.152.13	\N	公司: evertacsolutions
101	user	users	3	UPDATE	是否激活	True	False	1	admin	2025-06-23 02:12:16.245992	\N	10.210.152.13	\N	公司: evertacsolutions
102	user	users	3	UPDATE	updated_at	1750644671.929452	1750644736.2297974	1	admin	2025-06-23 02:12:16.245996	\N	10.210.152.13	\N	公司: evertacsolutions
103	customer	companies	5	CREATE	\N	\N	\N	2	quah	2025-06-25 02:56:55.906403	\N	10.210.139.96	\N	公司: Axis Technology
104	customer	contacts	3	CREATE	\N	\N	\N	2	quah	2025-06-25 02:57:49.348039	\N	10.210.113.204	\N	记录: Nurhamin
105	project	projects	5	CREATE	\N	\N	\N	2	quah	2025-06-25 03:04:19.918738	\N	10.210.81.223	\N	项目: abc
106	quotation	quotations	8	CREATE	\N	\N	\N	2	quah	2025-06-25 03:08:48.113765	\N	10.210.139.96	\N	报价单: QU202506-001
107	customer	companies	6	CREATE	\N	\N	\N	2	quah	2025-06-30 03:18:59.938204	\N	10.210.123.11	\N	公司: Reach Integrated Sdn Bhd
108	customer	companies	7	CREATE	\N	\N	\N	2	quah	2025-06-30 03:23:36.779694	\N	10.210.115.241	\N	公司: Strato Solutions Sdn Bhd
109	customer	contacts	4	CREATE	\N	\N	\N	2	quah	2025-06-30 03:28:12.122787	\N	10.210.123.11	\N	记录: Muhammad Ihsan
110	customer	companies	8	CREATE	\N	\N	\N	2	quah	2025-06-30 03:35:46.309834	\N	10.210.65.241	\N	公司: Synergy Oil & Gas Engineering Sdn Bhd
111	customer	companies	9	CREATE	\N	\N	\N	2	quah	2025-06-30 03:44:33.755065	\N	10.210.115.241	\N	公司: Tactical Communications Sdn Bhd
112	customer	companies	5	UPDATE	公司名称	Axis Technology	Axis Technology Resources (M) Sdn Bhd	2	quah	2025-06-30 03:48:39.702942	\N	10.210.136.236	\N	公司: Axis Technology Resources (M) Sdn Bhd
113	customer	contacts	3	DELETE	\N	\N	\N	2	quah	2025-06-30 03:53:32.836599	\N	10.210.65.241	\N	记录: Nurhamin
114	customer	companies	5	DELETE	\N	\N	\N	2	quah	2025-06-30 03:53:35.888696	\N	10.210.115.241	\N	公司: Axis Technology Resources (M) Sdn Bhd
115	customer	companies	10	CREATE	\N	\N	\N	2	quah	2025-06-30 04:24:23.129766	\N	10.210.87.89	\N	公司: Technip FMC
116	customer	companies	11	CREATE	\N	\N	\N	2	quah	2025-06-30 04:26:20.748777	\N	10.210.87.89	\N	公司: Axis Technology Resources (M) Sdn Bhd
117	customer	companies	12	CREATE	\N	\N	\N	2	quah	2025-06-30 06:12:43.500632	\N	10.210.65.241	\N	公司: YSC TECHNOLOGY ENGINEERING Sdn Bhd
118	customer	companies	13	CREATE	\N	\N	\N	2	quah	2025-06-30 06:16:11.815002	\N	10.210.115.241	\N	公司: Electcoms Berhad
119	customer	companies	14	CREATE	\N	\N	\N	2	quah	2025-06-30 06:22:44.009491	\N	10.210.123.11	\N	公司: mymeta solution
120	customer	companies	15	CREATE	\N	\N	\N	2	quah	2025-06-30 06:27:31.427957	\N	10.210.115.241	\N	公司: MCS Management Sdn Bhd
121	customer	companies	14	UPDATE	公司名称	mymeta solution	Mymeta Solution Sdn Bhd	2	quah	2025-06-30 06:33:46.472645	\N	10.210.65.241	\N	公司: Mymeta Solution Sdn Bhd
122	customer	companies	16	CREATE	\N	\N	\N	2	quah	2025-06-30 06:36:50.6943	\N	10.210.136.236	\N	公司: BHJ Security Technology Sdn Bhd
123	customer	companies	17	CREATE	\N	\N	\N	2	quah	2025-06-30 06:38:47.594542	\N	10.210.136.236	\N	公司: Engenious Solutions Sdn Bhd
124	customer	companies	18	CREATE	\N	\N	\N	2	quah	2025-06-30 06:41:30.659607	\N	10.210.136.236	\N	公司: Unique Arena Sdn Bhd
125	customer	companies	19	CREATE	\N	\N	\N	2	quah	2025-06-30 06:44:09.492269	\N	10.210.123.11	\N	公司: Ace Sonic Communications Sdn Bhd
126	customer	companies	20	CREATE	\N	\N	\N	2	quah	2025-06-30 06:46:35.014532	\N	10.210.137.211	\N	公司: Digital Two Way Communications Sdn Bhd
127	customer	companies	21	CREATE	\N	\N	\N	2	quah	2025-06-30 06:54:10.065133	\N	10.210.123.11	\N	公司: Comintel Sdn Bhd
128	customer	companies	22	CREATE	\N	\N	\N	3	roy	2025-06-30 06:59:16.699412	\N	10.210.136.236	\N	公司: MEG Consult Sdn. Bhd.
129	customer	contacts	5	CREATE	\N	\N	\N	3	roy	2025-06-30 07:02:50.85623	\N	10.210.123.11	\N	记录: Ir. Ong
130	customer	companies	22	UPDATE	备注	Electrical engineer handle for northern Malaysia projects and told the Open Data Centre @ Bukit Kayu, Kedah there the construstion will complete end of this year but only ICT in design with not specify for two-way radio system. Recommend to meet with his colleague Ms. Atiqah to check the design details.		3	roy	2025-06-30 07:03:11.354065	\N	10.210.115.241	\N	公司: MEG Consult Sdn. Bhd.
131	customer	contacts	6	CREATE	\N	\N	\N	3	roy	2025-06-30 07:11:45.433503	\N	10.210.123.11	\N	记录: Ferdinand Ngan
132	customer	companies	23	CREATE	\N	\N	\N	3	roy	2025-06-30 07:16:04.800115	\N	10.210.65.241	\N	公司: Binastra Corporation Bhd
133	customer	contacts	7	CREATE	\N	\N	\N	3	roy	2025-06-30 07:23:04.573419	\N	10.210.115.241	\N	记录: Lim Zen Yang
134	customer	companies	24	CREATE	\N	\N	\N	3	roy	2025-06-30 07:25:29.797298	\N	10.210.87.89	\N	公司: Jurutera Perunding Gen Sdn. Bhd.
135	customer	contacts	8	CREATE	\N	\N	\N	3	roy	2025-06-30 07:28:01.025182	\N	10.210.87.89	\N	记录: Kong Choong Chien
136	customer	companies	25	CREATE	\N	\N	\N	3	roy	2025-06-30 07:30:08.93397	\N	10.210.136.236	\N	公司: SKA Technology Sdn Bhd
137	customer	contacts	9	CREATE	\N	\N	\N	3	roy	2025-06-30 07:31:00.290741	\N	10.210.137.211	\N	记录: William Khor
138	customer	contacts	10	CREATE	\N	\N	\N	3	roy	2025-06-30 07:34:37.295278	\N	10.210.115.241	\N	记录: Selvarajah
139	customer	companies	26	CREATE	\N	\N	\N	3	roy	2025-06-30 07:37:08.132585	\N	10.210.115.241	\N	公司: B-Global Tech
140	customer	contacts	11	CREATE	\N	\N	\N	3	roy	2025-06-30 07:40:01.493576	\N	10.210.65.241	\N	记录: Nur Liyana Idzreen
141	customer	contacts	12	CREATE	\N	\N	\N	3	roy	2025-06-30 07:41:59.442682	\N	10.210.115.241	\N	记录: Farah Anuar
142	customer	companies	27	CREATE	\N	\N	\N	3	roy	2025-06-30 07:43:59.246704	\N	10.210.87.89	\N	公司: MCC Technique Sdn. Bhd.
143	customer	contacts	13	CREATE	\N	\N	\N	3	roy	2025-06-30 07:45:25.290907	\N	10.210.65.241	\N	记录: JW Chu
144	customer	contacts	14	CREATE	\N	\N	\N	3	roy	2025-06-30 07:46:44.240653	\N	10.210.65.241	\N	记录: John Goh
145	customer	companies	28	CREATE	\N	\N	\N	2	quah	2025-06-30 07:52:55.710725	\N	10.210.137.211	\N	公司: FMTCS SOLUTIONS PTE. LTD
146	project	projects	5	DELETE	\N	\N	\N	2	quah	2025-06-30 07:53:53.523487	\N	10.210.87.89	\N	项目: abc
147	project	projects	6	CREATE	\N	\N	\N	2	quah	2025-06-30 08:02:39.702678	\N	10.210.123.11	\N	项目: Jabil's Vietnam
148	quotation	quotations	9	CREATE	\N	\N	\N	2	quah	2025-06-30 08:22:51.764097	\N	10.210.123.11	\N	报价单: QU202506-001
149	quotation	quotations	9	UPDATE	amount	14183.329999999998	13854.329999999998	2	quah	2025-06-30 08:23:21.740478	\N	10.210.123.11	\N	报价单: QU202506-001
150	quotation	quotations	9	UPDATE	updated_at	2025-06-30 08:22:51.743214	2025-06-30 08:23:21.447638	2	quah	2025-06-30 08:23:21.740482	\N	10.210.123.11	\N	报价单: QU202506-001
151	quotation	quotations	9	UPDATE	amount	13854.329999999998	66469.83000000002	2	quah	2025-06-30 08:26:31.080319	\N	10.210.136.236	\N	报价单: QU202506-001
152	quotation	quotations	9	UPDATE	product_signature	7082fe402e3141decf6d547eb78104c8	5a9f6923e631f7c9ea966d658df4820a	2	quah	2025-06-30 08:26:31.080324	\N	10.210.136.236	\N	报价单: QU202506-001
153	quotation	quotations	9	UPDATE	implant_total_amount	12090.0	63130.0	2	quah	2025-06-30 08:26:31.080327	\N	10.210.136.236	\N	报价单: QU202506-001
154	quotation	quotations	9	UPDATE	updated_at	2025-06-30 08:23:21.447638	2025-06-30 08:26:30.854809	2	quah	2025-06-30 08:26:31.08033	\N	10.210.136.236	\N	报价单: QU202506-001
159	quotation	quotations	9	UPDATE	amount	24274.829999999998	24354.829999999998	2	quah	2025-06-30 08:30:19.869776	\N	10.210.137.211	\N	报价单: QU202506-001
160	quotation	quotations	9	UPDATE	updated_at	2025-06-30 08:28:27.481477	2025-06-30 08:30:19.615894	2	quah	2025-06-30 08:30:19.86978	\N	10.210.137.211	\N	报价单: QU202506-001
161	customer	contacts	14	DELETE	\N	\N	\N	3	roy	2025-06-30 08:30:29.077325	\N	10.210.87.89	\N	记录: John Goh
162	customer	contacts	13	DELETE	\N	\N	\N	3	roy	2025-06-30 08:30:45.492662	\N	10.210.87.89	\N	记录: JW Chu
165	customer	contacts	16	CREATE	\N	\N	\N	3	roy	2025-06-30 08:36:08.549581	\N	10.210.137.211	\N	记录: John Goh
166	customer	contacts	17	CREATE	\N	\N	\N	3	roy	2025-06-30 08:39:26.545434	\N	10.210.136.236	\N	记录: JW Chu
168	customer	contacts	18	CREATE	\N	\N	\N	3	roy	2025-06-30 08:43:39.906925	\N	10.210.123.11	\N	记录: Ellen Wong
169	customer	companies	30	CREATE	\N	\N	\N	3	roy	2025-06-30 08:44:54.963179	\N	10.210.123.11	\N	公司: Sunway Engineering Sdn. Bhd.
155	quotation	quotations	9	UPDATE	amount	66469.83000000002	24274.829999999998	2	quah	2025-06-30 08:28:27.735353	\N	10.210.123.11	\N	报价单: QU202506-001
156	quotation	quotations	9	UPDATE	product_signature	5a9f6923e631f7c9ea966d658df4820a	7082fe402e3141decf6d547eb78104c8	2	quah	2025-06-30 08:28:27.735359	\N	10.210.123.11	\N	报价单: QU202506-001
157	quotation	quotations	9	UPDATE	implant_total_amount	63130.0	20500.0	2	quah	2025-06-30 08:28:27.735363	\N	10.210.123.11	\N	报价单: QU202506-001
158	quotation	quotations	9	UPDATE	updated_at	2025-06-30 08:26:30.854809	2025-06-30 08:28:27.481477	2	quah	2025-06-30 08:28:27.735367	\N	10.210.123.11	\N	报价单: QU202506-001
163	customer	contacts	15	CREATE	\N	\N	\N	3	roy	2025-06-30 08:32:07.648557	\N	10.210.136.236	\N	记录: John Goh
164	customer	contacts	15	DELETE	\N	\N	\N	3	roy	2025-06-30 08:33:36.082507	\N	10.210.87.89	\N	记录: John Goh
167	customer	companies	29	CREATE	\N	\N	\N	3	roy	2025-06-30 08:41:24.492946	\N	10.210.87.89	\N	公司: Pembinaan Mitrajaya Sdn. Bhd.
170	customer	contacts	19	CREATE	\N	\N	\N	3	roy	2025-06-30 08:49:24.881359	\N	10.210.137.211	\N	记录: Procurement & Contracts
171	customer	contacts	20	CREATE	\N	\N	\N	3	roy	2025-06-30 08:52:47.557122	\N	10.210.65.241	\N	记录: Yap Siew Ling
172	customer	contacts	21	CREATE	\N	\N	\N	3	roy	2025-06-30 08:54:49.601477	\N	10.210.137.211	\N	记录: Chong Yih Lip
173	quotation	quotations	9	UPDATE	amount	24354.829999999998	36076.39	2	quah	2025-06-30 09:23:34.517743	\N	10.210.136.236	\N	报价单: QU202506-001
174	quotation	quotations	9	UPDATE	implant_total_amount	20500.0	25130.0	2	quah	2025-06-30 09:23:34.517748	\N	10.210.136.236	\N	报价单: QU202506-001
175	quotation	quotations	9	UPDATE	updated_at	2025-06-30 08:30:19.615894	2025-06-30 09:23:34.115947	2	quah	2025-06-30 09:23:34.51775	\N	10.210.136.236	\N	报价单: QU202506-001
176	quotation	quotations	9	UPDATE	updated_at	2025-06-30 09:23:34.115947	2025-06-30 09:41:02.338957	2	quah	2025-06-30 09:41:02.560139	\N	10.210.115.241	\N	报价单: QU202506-001
177	customer	companies	31	CREATE	\N	\N	\N	2	quah	2025-07-01 01:39:40.322588	\N	10.210.157.255	\N	公司: Electrica Technology Sdn Bhd
178	customer	contacts	22	CREATE	\N	\N	\N	2	quah	2025-07-01 01:40:25.322633	\N	10.210.218.16	\N	记录: Fairs
179	customer	contacts	23	CREATE	\N	\N	\N	2	quah	2025-07-01 01:54:53.579979	\N	10.210.41.230	\N	记录: How 
180	customer	contacts	24	CREATE	\N	\N	\N	2	quah	2025-07-01 01:55:30.096987	\N	10.210.137.233	\N	记录: Chong
181	customer	contacts	25	CREATE	\N	\N	\N	2	quah	2025-07-01 02:40:11.093075	\N	10.210.150.86	\N	记录: Cindy 
182	customer	contacts	19	DELETE	\N	\N	\N	3	roy	2025-07-01 06:19:56.641965	\N	10.210.137.233	\N	记录: Procurement & Contracts
183	customer	contacts	26	CREATE	\N	\N	\N	3	roy	2025-07-08 01:42:23.433749	\N	10.210.123.42	\N	记录: Tan Chao Zhi
184	project	projects	7	CREATE	\N	\N	\N	2	quah	2025-07-09 00:27:33.766044	\N	10.210.41.230	\N	项目: Exsim DC, EX1 & EX2
185	quotation	quotations	10	CREATE	\N	\N	\N	2	quah	2025-07-09 00:34:53.304282	\N	10.210.157.255	\N	报价单: QU202507-001
186	quotation	quotations	10	UPDATE	amount	19496.0	139715.76000000004	2	quah	2025-07-09 00:49:40.294577	\N	10.210.123.42	\N	报价单: QU202507-001
187	quotation	quotations	10	UPDATE	product_signature	ab7e67bfcb30e36cb6ddd5f2532cd252	3eefd98876c4fc8e5d8592a0730f7e78	2	quah	2025-07-09 00:49:40.294581	\N	10.210.123.42	\N	报价单: QU202507-001
188	quotation	quotations	10	UPDATE	implant_total_amount	18180.0	100684.0	2	quah	2025-07-09 00:49:40.294583	\N	10.210.123.42	\N	报价单: QU202507-001
189	quotation	quotations	10	UPDATE	updated_at	2025-07-09 00:34:53.283932	2025-07-09 00:49:39.979766	2	quah	2025-07-09 00:49:40.294585	\N	10.210.123.42	\N	报价单: QU202507-001
190	quotation	quotations	10	UPDATE	amount	139715.76000000004	139715.75999999998	2	quah	2025-07-09 00:50:32.262366	\N	10.210.157.255	\N	报价单: QU202507-001
191	quotation	quotations	10	UPDATE	updated_at	2025-07-09 00:49:39.979766	2025-07-09 00:50:32.039558	2	quah	2025-07-09 00:50:32.262371	\N	10.210.157.255	\N	报价单: QU202507-001
192	quotation	quotations	10	UPDATE	updated_at	2025-07-09 00:50:32.039558	2025-07-09 00:51:25.604889	2	quah	2025-07-09 00:51:25.874285	\N	10.210.123.42	\N	报价单: QU202507-001
193	customer	contacts	27	CREATE	\N	\N	\N	2	quah	2025-07-09 01:32:17.706249	\N	10.210.218.16	\N	记录: 邹先生
194	project	projects	8	CREATE	\N	\N	\N	2	quah	2025-07-09 01:33:32.268622	\N	10.210.41.230	\N	项目: MyO2
195	quotation	quotations	11	CREATE	\N	\N	\N	2	quah	2025-07-09 01:39:38.727545	\N	10.210.157.255	\N	报价单: QU202507-002
196	quotation	quotations	11	UPDATE	amount	9680.8	9731.7	2	quah	2025-07-09 01:40:05.802752	\N	10.210.157.255	\N	报价单: QU202507-002
197	quotation	quotations	11	UPDATE	updated_at	2025-07-09 01:39:38.707520	2025-07-09 01:40:05.750108	2	quah	2025-07-09 01:40:05.802756	\N	10.210.157.255	\N	报价单: QU202507-002
198	quotation	quotations	11	UPDATE	amount	9731.7	10356.61	2	quah	2025-07-09 01:41:07.402626	\N	10.210.150.86	\N	报价单: QU202507-002
199	quotation	quotations	11	UPDATE	updated_at	2025-07-09 01:40:05.750108	2025-07-09 01:41:07.298946	2	quah	2025-07-09 01:41:07.40263	\N	10.210.150.86	\N	报价单: QU202507-002
200	quotation	quotations	11	UPDATE	amount	10356.61	10925.39	2	quah	2025-07-09 01:42:03.844982	\N	10.210.157.255	\N	报价单: QU202507-002
201	quotation	quotations	11	UPDATE	updated_at	2025-07-09 01:41:07.298946	2025-07-09 01:42:03.785885	2	quah	2025-07-09 01:42:03.844986	\N	10.210.157.255	\N	报价单: QU202507-002
202	quotation	quotations	11	UPDATE	amount	10925.39	11647.61	2	quah	2025-07-09 01:43:38.639968	\N	10.210.137.233	\N	报价单: QU202507-002
203	quotation	quotations	11	UPDATE	updated_at	2025-07-09 01:42:03.785885	2025-07-09 01:43:38.570552	2	quah	2025-07-09 01:43:38.639972	\N	10.210.137.233	\N	报价单: QU202507-002
204	quotation	quotations	11	UPDATE	amount	11647.61	11748.119999999999	2	quah	2025-07-09 01:46:53.331846	\N	10.210.150.86	\N	报价单: QU202507-002
205	quotation	quotations	11	UPDATE	updated_at	2025-07-09 01:43:38.570552	2025-07-09 01:46:53.276624	2	quah	2025-07-09 01:46:53.331852	\N	10.210.150.86	\N	报价单: QU202507-002
206	project	projects	7	UPDATE	项目类型	channel_follow	sales_focus	2	quah	2025-07-09 03:13:24.329776	\N	10.210.123.42	\N	项目: Exsim DC, EX1 & EX2
207	project	projects	7	UPDATE	industry		other	2	quah	2025-07-09 03:13:24.329781	\N	10.210.123.42	\N	项目: Exsim DC, EX1 & EX2
208	customer	companies	32	CREATE	\N	\N	\N	3	roy	2025-07-09 06:53:03.269788	\N	10.210.41.230	\N	公司: Bridge Data Centres -  (Subsidiary of Chindata Group @ Beijing)
209	customer	contacts	28	CREATE	\N	\N	\N	3	roy	2025-07-09 07:00:31.18296	\N	10.210.137.233	\N	记录: 胡桂霞
210	customer	companies	33	CREATE	\N	\N	\N	3	roy	2025-07-09 07:12:20.259527	\N	10.210.157.255	\N	公司: Dynast Consult Sdn. Bhd.
211	customer	contacts	29	CREATE	\N	\N	\N	3	roy	2025-07-09 07:14:09.655637	\N	10.210.157.255	\N	记录: Wong Liang Jun
213	customer	contacts	30	CREATE	\N	\N	\N	3	roy	2025-07-09 07:21:47.359397	\N	10.210.150.86	\N	记录: Bruce Wang
212	customer	companies	34	CREATE	\N	\N	\N	3	roy	2025-07-09 07:19:24.69069	\N	10.210.123.42	\N	公司: CCIE Engineering (M) Sdn. Bhd.
214	customer	companies	35	CREATE	\N	\N	\N	3	roy	2025-07-09 07:26:57.532241	\N	10.210.41.230	\N	公司: YSC Technology Engineering Sdn. Bhd.
215	customer	contacts	31	CREATE	\N	\N	\N	3	roy	2025-07-09 07:28:50.848969	\N	10.210.150.86	\N	记录: Mr. 邹
216	project	projects	9	CREATE	\N	\N	\N	3	roy	2025-07-09 07:33:08.069023	\N	10.210.218.16	\N	项目: Bridge Data Centre MY02 @ Cyberjaya - Phase 2
217	project	projects	10	CREATE	\N	\N	\N	3	roy	2025-07-10 01:30:50.229591	\N	10.210.36.212	\N	项目: YTL Data Centre @ Kulai
218	customer	companies	36	CREATE	\N	\N	\N	3	roy	2025-07-10 01:34:51.573117	\N	10.210.36.212	\N	公司: SIPP Power Sdn Bhd (subsidiary of YTL Corporation Bhd)
219	customer	companies	37	CREATE	\N	\N	\N	3	roy	2025-07-10 01:44:32.426256	\N	10.210.95.118	\N	公司: TRAC Consulting & Engineering Sdn Bhd
220	customer	companies	37	UPDATE	备注	Parent company is AIP Risk Consulting Pte. Ltd. @ Singapore.	Security consultant & parent company is AIP Risk Consulting Pte. Ltd. @ Singapore.	3	roy	2025-07-10 01:45:53.828804	\N	10.210.95.118	\N	公司: TRAC Consulting & Engineering Sdn Bhd
221	customer	contacts	32	CREATE	\N	\N	\N	3	roy	2025-07-10 01:47:21.128945	\N	10.210.220.83	\N	记录: Ahmad Azri
222	customer	companies	38	CREATE	\N	\N	\N	3	roy	2025-07-10 01:50:59.607464	\N	10.210.95.118	\N	公司:  Syarikat Pembenaan Yeoh Tiong Lay Sdn Bhd (YTL Construction) 
223	project	projects	10	UPDATE	产品情况	not_required		3	roy	2025-07-10 01:53:43.439741	\N	10.210.95.118	\N	项目: YTL Data Centre @ Kulai
224	project	projects	10	UPDATE	最终用户		SIPP Power Sdn Bhd (subsidiary of YTL Corporation Bhd)	3	roy	2025-07-10 01:53:43.439747	\N	10.210.95.118	\N	项目: YTL Data Centre @ Kulai
225	project	projects	10	UPDATE	设计院		TRAC Consulting & Engineering Sdn Bhd	3	roy	2025-07-10 01:53:43.439751	\N	10.210.95.118	\N	项目: YTL Data Centre @ Kulai
226	project	projects	10	UPDATE	总承包商		 Syarikat Pembenaan Yeoh Tiong Lay Sdn Bhd (YTL Construction) 	3	roy	2025-07-10 01:53:43.439755	\N	10.210.95.118	\N	项目: YTL Data Centre @ Kulai
227	project	projects	10	UPDATE	industry	technology	other	3	roy	2025-07-10 01:53:43.439759	\N	10.210.95.118	\N	项目: YTL Data Centre @ Kulai
228	project	projects	10	UPDATE	阶段描述		Azri and told this 275 acre land reserve for solar power & data centre campus. Planning for 12 DC buildings with total 500MW capacity. YTL JC1 & 2 already completed and JDC3 Hyperscale AI facility & JDC6 Colocation facility will handover in next quater. Told this project that totally no RF in design and will depends on operation team request. 	3	roy	2025-07-10 01:54:37.002756	\N	10.210.95.118	\N	项目: YTL Data Centre @ Kulai
229	project	projects	11	CREATE	\N	\N	\N	3	roy	2025-07-10 02:12:50.230227	\N	10.210.60.237	\N	项目: Bridge Data Centre @ Chonburi, Thailand
230	project	projects	11	UPDATE	项目类型	\N	sales_focus	3	roy	2025-07-10 02:15:40.514351	\N	10.210.7.144	\N	项目: Bridge Data Centre @ Chonburi, Thailand
231	project	projects	11	UPDATE	报备来源		marketing	3	roy	2025-07-10 02:15:40.514355	\N	10.210.7.144	\N	项目: Bridge Data Centre @ Chonburi, Thailand
232	project	projects	11	UPDATE	产品情况		unqualified	3	roy	2025-07-10 02:15:40.514357	\N	10.210.7.144	\N	项目: Bridge Data Centre @ Chonburi, Thailand
233	project	projects	11	UPDATE	最终用户		Bridge Data Centres -  (Subsidiary of Chindata Group @ Beijing)	3	roy	2025-07-10 02:15:40.514359	\N	10.210.7.144	\N	项目: Bridge Data Centre @ Chonburi, Thailand
234	project	projects	11	UPDATE	阶段描述		Info from end-user Ms. 胡桂霞 (Technical team) to recommend follow up with maincon PIC Mr.赵剑波 @ CCYR China.\r\n	3	roy	2025-07-10 02:15:40.514361	\N	10.210.7.144	\N	项目: Bridge Data Centre @ Chonburi, Thailand
235	customer	companies	39	CREATE	\N	\N	\N	3	roy	2025-07-10 02:30:58.328612	\N	10.210.36.212	\N	公司: China Construction Yangtze River (Malaysia) Sdn. Bhd. (Subsidiary of CSCEC)
236	project	projects	11	UPDATE	总承包商		China Construction Yangtze River (Malaysia) Sdn. Bhd. (Subsidiary of CSCEC)	3	roy	2025-07-10 02:32:20.119016	\N	10.210.60.237	\N	项目: Bridge Data Centre @ Chonburi, Thailand
237	customer	contacts	33	CREATE	\N	\N	\N	2	quah	2025-07-11 08:05:30.148909	\N	10.210.7.144	\N	记录: 付总
238	customer	contacts	34	CREATE	\N	\N	\N	2	quah	2025-07-11 08:08:15.997649	\N	10.210.95.118	\N	记录: Leer
239	customer	contacts	35	CREATE	\N	\N	\N	2	quah	2025-07-11 08:09:32.831038	\N	10.210.202.154	\N	记录: Doreen
240	customer	contacts	36	CREATE	\N	\N	\N	2	quah	2025-07-11 09:25:19.711362	\N	10.210.60.237	\N	记录: Azura
241	customer	contacts	37	CREATE	\N	\N	\N	2	quah	2025-07-11 09:28:08.973407	\N	10.210.220.83	\N	记录: Jet Chin
242	customer	contacts	38	CREATE	\N	\N	\N	2	quah	2025-07-11 09:31:12.84613	\N	10.210.220.83	\N	记录: Zulhilmi 
243	customer	contacts	39	CREATE	\N	\N	\N	2	quah	2025-07-11 09:33:46.108474	\N	10.210.202.154	\N	记录: Ir. Teo Chuun Ben
244	customer	contacts	40	CREATE	\N	\N	\N	2	quah	2025-07-11 09:35:40.794027	\N	10.210.36.212	\N	记录: Kim
245	customer	contacts	41	CREATE	\N	\N	\N	2	quah	2025-07-11 09:37:05.790563	\N	10.210.220.83	\N	记录: Suhaimi
246	customer	contacts	42	CREATE	\N	\N	\N	2	quah	2025-07-11 09:49:05.045259	\N	10.210.60.237	\N	记录: Nurhamin
247	customer	contacts	43	CREATE	\N	\N	\N	2	quah	2025-07-11 09:50:04.50022	\N	10.210.36.212	\N	记录: Nor Wahidah Misran
248	customer	contacts	44	CREATE	\N	\N	\N	2	quah	2025-07-11 09:50:44.790619	\N	10.210.7.144	\N	记录: Shiqeen
249	customer	contacts	45	CREATE	\N	\N	\N	2	quah	2025-07-11 09:52:27.398852	\N	10.210.60.237	\N	记录: Chung
250	customer	contacts	46	CREATE	\N	\N	\N	2	quah	2025-07-11 09:56:12.197821	\N	10.210.220.83	\N	记录: Zakaria Dahili
251	customer	contacts	47	CREATE	\N	\N	\N	2	quah	2025-07-11 09:57:22.642831	\N	10.210.137.254	\N	记录: Puteri Maryam
252	customer	contacts	48	CREATE	\N	\N	\N	2	quah	2025-07-11 09:59:19.359463	\N	10.210.36.212	\N	记录: Hanini Mohd Zaki
253	customer	contacts	49	CREATE	\N	\N	\N	2	quah	2025-07-11 10:00:28.863291	\N	10.210.202.154	\N	记录: Nur Jahidah
254	user	users	3	UPDATE	is_department_manager	False	True	1	admin	2025-07-14 00:51:15.967232	\N	10.210.220.83	\N	公司: evertacsolutions
255	user	users	3	UPDATE	updated_at	1751266364.330672	1752454275.954173	1	admin	2025-07-14 00:51:15.96724	\N	10.210.220.83	\N	公司: evertacsolutions
256	customer	contacts	50	CREATE	\N	\N	\N	2	quah	2025-07-14 02:29:32.036945	\N	10.210.7.144	\N	记录: Alyaa
257	customer	companies	40	CREATE	\N	\N	\N	2	quah	2025-07-16 07:05:46.278539	\N	10.210.220.83	\N	公司: Stream Communication System Sdn Bhd
258	customer	contacts	51	CREATE	\N	\N	\N	2	quah	2025-07-16 07:06:24.835751	\N	10.210.137.254	\N	记录: Lai
259	customer	companies	41	CREATE	\N	\N	\N	2	quah	2025-07-16 07:23:09.250055	\N	10.210.137.254	\N	公司: Asalcom Sdn Bhd
260	customer	contacts	52	CREATE	\N	\N	\N	2	quah	2025-07-16 07:23:54.047585	\N	10.210.95.118	\N	记录: Amelia
261	customer	contacts	53	CREATE	\N	\N	\N	2	quah	2025-07-16 07:33:49.508659	\N	10.210.7.144	\N	记录: 李工
262	customer	companies	42	CREATE	\N	\N	\N	2	quah	2025-07-16 08:38:28.611182	\N	10.210.60.237	\N	公司: Triple Access Sdn Bhd
263	customer	contacts	54	CREATE	\N	\N	\N	2	quah	2025-07-16 08:41:27.313942	\N	10.210.137.254	\N	记录: Yusry
264	customer	companies	43	CREATE	\N	\N	\N	2	quah	2025-07-16 08:43:41.220411	\N	10.210.158.33	\N	公司: Vertex Communication Sdn Bhd
265	customer	contacts	55	CREATE	\N	\N	\N	2	quah	2025-07-16 08:44:23.20086	\N	10.210.158.33	\N	记录: Matthew
266	customer	companies	35	UPDATE	备注		test	1	admin	2025-07-18 01:41:09.109374	\N	10.210.137.254	\N	公司: YSC Technology Engineering Sdn. Bhd.
267	customer	companies	35	UPDATE	备注	test		1	admin	2025-07-18 01:41:15.154665	\N	10.210.7.144	\N	公司: YSC Technology Engineering Sdn. Bhd.
268	user	users	4	CREATE	\N	\N	\N	1	admin	2025-07-18 01:43:56.0117	\N	10.210.7.144	\N	公司: evertacsolutions
269	user	users	5	CREATE	\N	\N	\N	1	admin	2025-07-18 01:46:19.076336	\N	10.210.220.83	\N	公司: evertacsolutions
270	user	users	6	CREATE	\N	\N	\N	1	admin	2025-07-18 01:47:12.872289	\N	10.210.220.83	\N	公司: evertacsolutions
271	customer	companies	44	CREATE	\N	\N	\N	3	roy	2025-07-22 02:43:28.631513	\N	10.210.36.212	\N	公司: GDS IDC SERVICES III (MALAYSIA) SDN BHD
272	customer	companies	45	CREATE	\N	\N	\N	3	roy	2025-07-22 03:03:45.888805	\N	10.210.7.144	\N	公司: EPG Data Center Module Sdn. Bhd.
273	customer	contacts	56	CREATE	\N	\N	\N	3	roy	2025-07-22 03:04:37.263608	\N	10.210.137.254	\N	记录: Mr. Yang
274	project	projects	12	CREATE	\N	\N	\N	3	roy	2025-07-22 03:27:05.549684	\N	10.210.7.144	\N	项目: GDS Data Center @ Nusajaya Tech Park (NTP) - Block N
275	customer	companies	45	UPDATE	公司名称	EPG Data Center Module Sdn. Bhd.	EPG Engineering System Sdn. Bhd.	3	roy	2025-07-22 03:34:36.075457	\N	10.210.220.83	\N	公司: EPG Engineering System Sdn. Bhd.
276	customer	companies	45	UPDATE	region	Johor	Kuala Lumpur	3	roy	2025-07-22 03:34:36.075461	\N	10.210.220.83	\N	公司: EPG Engineering System Sdn. Bhd.
277	customer	companies	45	UPDATE	address	12, Jalan SiLC 1/3, Kawasan Perindustrian SILC, 79200 Iskandar Puteri, Johor Darul Ta'zim	Level 41, Vista Tower,The Intermark,348 Jalan Tun Razak,50400, Kuala Lumpur, Malaysia	3	roy	2025-07-22 03:34:36.075464	\N	10.210.220.83	\N	公司: EPG Engineering System Sdn. Bhd.
278	project	projects	12	UPDATE	阶段描述		EPG Secured this GDS NTP Block N & installer will be YSC Technology. Estimate delivery will be September time.	3	roy	2025-07-22 03:50:20.949109	\N	10.210.36.212	\N	项目: GDS Data Center @ Nusajaya Tech Park (NTP) - Block N
279	quotation	quotations	12	CREATE	\N	\N	\N	3	roy	2025-07-22 04:08:45.718693	\N	10.210.60.237	\N	报价单: QU202507-003
280	quotation	quotations	12	UPDATE	amount	12505.29	65964.42	3	roy	2025-07-22 07:01:18.689411	\N	10.210.95.118	\N	报价单: QU202507-003
281	quotation	quotations	12	UPDATE	product_signature	a0179ce456b21ef33a8d90796ee52d58	008db7c832da69fa507ed889966fd81c	3	roy	2025-07-22 07:01:18.689418	\N	10.210.95.118	\N	报价单: QU202507-003
282	quotation	quotations	12	UPDATE	implant_total_amount	9870.0	63339.0	3	roy	2025-07-22 07:01:18.689423	\N	10.210.95.118	\N	报价单: QU202507-003
283	quotation	quotations	12	UPDATE	updated_at	2025-07-22 04:08:45.694073	2025-07-22 07:01:18.574251	3	roy	2025-07-22 07:01:18.689427	\N	10.210.95.118	\N	报价单: QU202507-003
284	quotation	quotations	12	UPDATE	amount	65964.42	75573.29	3	roy	2025-07-22 07:12:16.999008	\N	10.210.7.144	\N	报价单: QU202507-003
285	quotation	quotations	12	UPDATE	updated_at	2025-07-22 07:01:18.574251	2025-07-22 07:12:16.848342	3	roy	2025-07-22 07:12:16.999014	\N	10.210.7.144	\N	报价单: QU202507-003
286	quotation	quotations	12	UPDATE	amount	75573.29	82335.68999999999	3	roy	2025-07-22 07:14:37.559786	\N	10.210.220.83	\N	报价单: QU202507-003
287	quotation	quotations	12	UPDATE	updated_at	2025-07-22 07:12:16.848342	2025-07-22 07:14:37.445900	3	roy	2025-07-22 07:14:37.55979	\N	10.210.220.83	\N	报价单: QU202507-003
288	customer	companies	46	CREATE	\N	\N	\N	3	roy	2025-07-22 07:26:18.413364	\N	10.210.137.254	\N	公司: GDS Data Center @ Thailand
289	project	projects	13	CREATE	\N	\N	\N	3	roy	2025-07-22 07:35:34.647668	\N	10.210.60.237	\N	项目: GDS Data Centre @  Thailand CTP - B
290	customer	companies	47	CREATE	\N	\N	\N	3	roy	2025-07-22 07:42:11.611712	\N	10.210.220.83	\N	公司: Longmotive (M) Sdn. Bhd.
291	project	projects	13	UPDATE	项目名称	GDS Data Centre @  Thailand CTP - B	GDS Data Centre @  Chonburi Thailand CTP - B	3	roy	2025-07-22 07:46:13.069303	\N	10.210.36.212	\N	项目: GDS Data Centre @  Chonburi Thailand CTP - B
292	project	projects	13	UPDATE	系统集成商		Longmotive (M) Sdn. Bhd.	3	roy	2025-07-22 07:46:13.069309	\N	10.210.36.212	\N	项目: GDS Data Centre @  Chonburi Thailand CTP - B
293	project	projects	13	UPDATE	阶段描述		Info from FMTCS Mr. Fu told that Longmotive secured this CTP-B project and estimte delivery in Oct 2025.	3	roy	2025-07-22 07:46:13.069313	\N	10.210.36.212	\N	项目: GDS Data Centre @  Chonburi Thailand CTP - B
294	quotation	quotations	13	CREATE	\N	\N	\N	3	roy	2025-07-22 08:07:54.510768	\N	10.210.7.144	\N	报价单: QU202507-004
295	quotation	quotations	13	UPDATE	amount	123609.0	129313.54999999999	3	roy	2025-07-22 08:13:33.518927	\N	10.210.7.144	\N	报价单: QU202507-004
296	quotation	quotations	13	UPDATE	updated_at	2025-07-22 08:07:54.457921	2025-07-22 08:13:33.274873	3	roy	2025-07-22 08:13:33.518932	\N	10.210.7.144	\N	报价单: QU202507-004
297	quotation	quotations	13	UPDATE	amount	129313.54999999999	147801.63999999996	3	roy	2025-07-22 08:21:52.574626	\N	10.210.7.144	\N	报价单: QU202507-004
474	user	users	12	CREATE	\N	\N	\N	1	admin	2025-08-11 02:03:34.621192	\N	10.210.170.0	\N	公司: FMTCS SOLUTIONS PTE. LTD
298	quotation	quotations	13	UPDATE	updated_at	2025-07-22 08:13:33.274873	2025-07-22 08:21:52.393924	3	roy	2025-07-22 08:21:52.574632	\N	10.210.7.144	\N	报价单: QU202507-004
299	quotation	quotations	13	UPDATE	amount	147801.63999999996	147841.24	3	roy	2025-07-22 08:22:26.967889	\N	10.210.137.254	\N	报价单: QU202507-004
300	quotation	quotations	13	UPDATE	updated_at	2025-07-22 08:21:52.393924	2025-07-22 08:22:26.780871	3	roy	2025-07-22 08:22:26.967895	\N	10.210.137.254	\N	报价单: QU202507-004
301	quotation	quotations	13	UPDATE	amount	147841.24	148603.74	3	roy	2025-07-22 08:23:02.590442	\N	10.210.220.83	\N	报价单: QU202507-004
302	quotation	quotations	13	UPDATE	updated_at	2025-07-22 08:22:26.780871	2025-07-22 08:23:02.365626	3	roy	2025-07-22 08:23:02.590447	\N	10.210.220.83	\N	报价单: QU202507-004
303	quotation	quotations	13	UPDATE	amount	148603.74	152585.3	3	roy	2025-07-22 08:25:41.667299	\N	10.210.7.144	\N	报价单: QU202507-004
304	quotation	quotations	13	UPDATE	updated_at	2025-07-22 08:23:02.365626	2025-07-22 08:25:41.483086	3	roy	2025-07-22 08:25:41.667303	\N	10.210.7.144	\N	报价单: QU202507-004
305	project	projects	12	UPDATE	项目名称	GDS Data Center @ Nusajaya Tech Park (NTP) - Block N	NTP - Block N - GDS Data Center @ Nusajaya Tech Park 	3	roy	2025-07-22 09:07:56.014653	\N	10.210.60.237	\N	项目: NTP - Block N - GDS Data Center @ Nusajaya Tech Park 
306	project	projects	12	UPDATE	阶段描述	EPG Secured this GDS NTP Block N & installer will be YSC Technology. Estimate delivery will be September time.	FMTCS Mr. Fu told NTP - Block F still in assessment and Trac Consult's Eric rejected EPG T&C submission due to supporting rooms & cabins still lack of antennas. /NTP - H ready delivery to EPG's installer YSC. /EPG Secured this GDS NTP Block N but installer have not appoint yet and estimate delivery will be this year September.	3	roy	2025-07-22 09:07:56.014657	\N	10.210.60.237	\N	项目: NTP - Block N - GDS Data Center @ Nusajaya Tech Park 
307	project	projects	13	UPDATE	项目名称	GDS Data Centre @  Chonburi Thailand CTP - B	CTP - B - GDS Data Centre @ Chonburi Thailand 	3	roy	2025-07-22 09:11:09.102779	\N	10.210.36.212	\N	项目: CTP - B - GDS Data Centre @ Chonburi Thailand 
309	project	projects	15	CREATE	\N	\N	\N	3	roy	2025-07-22 09:19:47.744465	\N	10.210.7.144	\N	项目: NTP - J, K & L - GDS DC @ Nusajaya Tech Park
308	project	projects	14	CREATE	\N	\N	\N	3	roy	2025-07-22 09:15:27.123756	\N	10.210.137.254	\N	项目: NTP - G & M - GDS DC @ Nusaya Tech Park
310	project	projects	15	UPDATE	项目类型	\N	channel_follow	3	roy	2025-07-22 09:28:47.767567	\N	10.210.60.237	\N	项目: NTP - J, K & L - GDS DC @ Nusajaya Tech Park
311	project	projects	15	UPDATE	报备来源		channel	3	roy	2025-07-22 09:28:47.767572	\N	10.210.60.237	\N	项目: NTP - J, K & L - GDS DC @ Nusajaya Tech Park
312	project	projects	15	UPDATE	产品情况		controlled	3	roy	2025-07-22 09:28:47.767574	\N	10.210.60.237	\N	项目: NTP - J, K & L - GDS DC @ Nusajaya Tech Park
313	project	projects	15	UPDATE	最终用户		GDS IDC SERVICES III (MALAYSIA) SDN BHD	3	roy	2025-07-22 09:28:47.767576	\N	10.210.60.237	\N	项目: NTP - J, K & L - GDS DC @ Nusajaya Tech Park
314	project	projects	15	UPDATE	设计院		TRAC Consulting & Engineering Sdn Bhd	3	roy	2025-07-22 09:28:47.767578	\N	10.210.60.237	\N	项目: NTP - J, K & L - GDS DC @ Nusajaya Tech Park
315	project	projects	15	UPDATE	当前阶段	discover	embed	3	roy	2025-07-22 09:28:47.767581	\N	10.210.60.237	\N	项目: NTP - J, K & L - GDS DC @ Nusajaya Tech Park
316	project	projects	15	UPDATE	阶段描述		FMTCS Mr. Fu told Longmotive had higher chance to win this NTP - J and estimate delivery in this year September time. / NTP - K & L still in bidding stage between Longmotive & EPG.	3	roy	2025-07-22 09:28:47.767583	\N	10.210.60.237	\N	项目: NTP - J, K & L - GDS DC @ Nusajaya Tech Park
317	project	projects	15	UPDATE	updated_at	2025-07-22 17:19:47.732085	2025-07-22 09:28:47.753853	3	roy	2025-07-22 09:28:47.767585	\N	10.210.60.237	\N	项目: NTP - J, K & L - GDS DC @ Nusajaya Tech Park
318	project	projects	12	UPDATE	项目名称	NTP - Block N - GDS Data Center @ Nusajaya Tech Park 	NTP - Block N - GDS DC @ Nusajaya Tech Park 	3	roy	2025-07-22 09:29:52.452753	\N	10.210.123.239	\N	项目: NTP - Block N - GDS DC @ Nusajaya Tech Park 
319	customer	contacts	57	CREATE	\N	\N	\N	2	quah	2025-07-22 09:36:08.908896	\N	10.210.7.144	\N	记录: Yogasingam Vallipuram
320	customer	contacts	58	CREATE	\N	\N	\N	2	quah	2025-07-22 09:37:38.475689	\N	10.210.140.182	\N	记录: Muhammad Mussaddiq Bin Samsudin
321	customer	contacts	34	DELETE	\N	\N	\N	2	quah	2025-07-22 09:38:02.821808	\N	10.210.220.83	\N	记录: Leer
322	customer	contacts	59	CREATE	\N	\N	\N	2	quah	2025-07-22 09:39:02.218803	\N	10.210.220.83	\N	记录: Lee Hoong Fatt
323	project	projects	16	CREATE	\N	\N	\N	3	roy	2025-07-22 09:42:21.584734	\N	10.210.137.254	\N	项目: KTP - B & C - GDS DC @ Kempas Tech Park
324	project	projects	17	CREATE	\N	\N	\N	3	roy	2025-07-22 09:46:33.411645	\N	10.210.7.144	\N	项目: KTP - G, N & J - GDS DC @ Kempas Tech Park
325	customer	companies	48	CREATE	\N	\N	\N	2	quah	2025-07-22 09:48:37.046592	\N	10.210.123.239	\N	公司: Wire & Wireless Sdn Bhd
326	customer	contacts	60	CREATE	\N	\N	\N	2	quah	2025-07-22 09:49:22.52005	\N	10.210.7.144	\N	记录: Nadason
327	project	projects	18	CREATE	\N	\N	\N	3	roy	2025-07-22 09:51:48.223759	\N	10.210.60.237	\N	项目: CTP - A - GDS DC @ Chonburi Thailand
328	project	projects	19	CREATE	\N	\N	\N	3	roy	2025-07-22 13:28:47.519907	\N	10.210.123.239	\N	项目: CTP - C - GDS DC @ Chonburi Thailand
329	project	projects	12	UPDATE	项目名称	NTP - Block N - GDS DC @ Nusajaya Tech Park 	NTP - N - GDS DC @ Nusajaya Tech Park 	3	roy	2025-07-22 13:31:18.470571	\N	10.210.95.118	\N	项目: NTP - N - GDS DC @ Nusajaya Tech Park 
330	project	projects	9	UPDATE	项目名称	Bridge Data Centre MY02 @ Cyberjaya - Phase 2	MY02 - Phase 2 - Bridge DC @ Cyberjaya 	3	roy	2025-07-22 13:36:46.986549	\N	10.210.123.239	\N	项目: MY02 - Phase 2 - Bridge DC @ Cyberjaya 
331	project	projects	9	UPDATE	industry	technology	datacenter	3	roy	2025-07-22 13:36:46.986553	\N	10.210.123.239	\N	项目: MY02 - Phase 2 - Bridge DC @ Cyberjaya 
332	project	projects	16	UPDATE	阶段描述	FMTCS Mr. Fu told Longmotive secured this KTP - B & C projects and now in the stage to complete the design & prepare the BOM list.	FMTCS Mr. Fu told KTP - A, D & E there already completed. /Longmotive secured this KTP - B & C projects and now in the stage of preparation the BOM list.	3	roy	2025-07-22 13:58:17.638399	\N	10.210.220.83	\N	项目: KTP - B & C - GDS DC @ Kempas Tech Park
333	project	projects	16	UPDATE	阶段描述	FMTCS Mr. Fu told KTP - A, D & E there already completed. /Longmotive secured this KTP - B & C projects and now in the stage of preparation the BOM list.	FMTCS Mr. Fu told already supplied Longmotive for KTP - A, D & E with no issue to these projects. /And now Longmotive secured this KTP - B & C projects with the stage of discussion to preparation the BOM list.	3	roy	2025-07-22 14:01:49.112637	\N	10.210.7.144	\N	项目: KTP - B & C - GDS DC @ Kempas Tech Park
334	project	projects	20	CREATE	\N	\N	\N	3	roy	2025-07-22 14:42:28.351604	\N	10.210.137.254	\N	项目: NextDC KL1 @ PJ
335	customer	companies	49	CREATE	\N	\N	\N	3	roy	2025-07-22 14:44:43.476652	\N	10.210.220.83	\N	公司: NextDC Sdn. Bhd.
336	project	projects	20	UPDATE	最终用户		NextDC Sdn. Bhd.	3	roy	2025-07-22 14:52:48.314753	\N	10.210.137.254	\N	项目: NextDC KL1 @ PJ
337	project	projects	20	UPDATE	设计院		TRAC Consulting & Engineering Sdn Bhd	3	roy	2025-07-22 14:52:48.314759	\N	10.210.137.254	\N	项目: NextDC KL1 @ PJ
338	project	projects	20	UPDATE	总承包商		Pembinaan Mitrajaya Sdn. Bhd.	3	roy	2025-07-22 14:52:48.314763	\N	10.210.137.254	\N	项目: NextDC KL1 @ PJ
339	project	projects	20	UPDATE	系统集成商		SKA Technology Sdn Bhd	3	roy	2025-07-22 14:52:48.314767	\N	10.210.137.254	\N	项目: NextDC KL1 @ PJ
340	project	projects	20	UPDATE	阶段描述		Total 5 blocks DC on this site and SKA secured block 1 with RFoF DAS package sub to Asalcom. MCC Technique Mr. Chu told this block 3 beside the block 1 and probably will share the same repeater. Planning to bid these block 4 & 5 once the design details come out and will need our support for RFoF DAS system.            	3	roy	2025-07-22 14:52:48.314771	\N	10.210.137.254	\N	项目: NextDC KL1 @ PJ
341	project	projects	20	UPDATE	项目名称	NextDC KL1 @ PJ	NextDC KL1 - Block 4 & 5 @ PJ	3	roy	2025-07-23 05:44:17.423748	\N	10.210.7.144	\N	项目: NextDC KL1 - Block 4 & 5 @ PJ
342	project	projects	20	UPDATE	阶段描述	Total 5 blocks DC on this site and SKA secured block 1 with RFoF DAS package sub to Asalcom. MCC Technique Mr. Chu told this block 3 beside the block 1 and probably will share the same repeater. Planning to bid these block 4 & 5 once the design details come out and will need our support for RFoF DAS system.            	      	3	roy	2025-07-23 05:44:17.423755	\N	10.210.7.144	\N	项目: NextDC KL1 - Block 4 & 5 @ PJ
343	project	projects	19	UPDATE	阶段描述	FMTCS Mr. Fu told project still in planning stage.		3	roy	2025-07-23 05:49:34.718664	\N	10.210.7.144	\N	项目: CTP - C - GDS DC @ Chonburi Thailand
344	project	projects	19	UPDATE	当前阶段	discover	embed	3	roy	2025-07-23 05:50:01.942322	\N	10.210.220.83	\N	项目: CTP - C - GDS DC @ Chonburi Thailand
345	project	projects	19	UPDATE	updated_at	2025-07-22 21:28:47.509632	2025-07-23 05:50:01.929891	3	roy	2025-07-23 05:50:01.942329	\N	10.210.220.83	\N	项目: CTP - C - GDS DC @ Chonburi Thailand
346	project	projects	13	UPDATE	阶段描述	Info from FMTCS Mr. Fu told that Longmotive secured this CTP-B project and estimte delivery in Oct 2025.		3	roy	2025-07-23 05:52:40.328152	\N	10.210.142.141	\N	项目: CTP - B - GDS Data Centre @ Chonburi Thailand 
352	project	projects	17	UPDATE	设计院		TRAC Consulting & Engineering Sdn Bhd	3	roy	2025-07-23 06:03:26.520101	\N	10.210.95.118	\N	项目: KTP - G, N & J - GDS DC @ Kempas Tech Park
353	project	projects	17	UPDATE	系统集成商		Longmotive (M) Sdn. Bhd.	3	roy	2025-07-23 06:03:26.520108	\N	10.210.95.118	\N	项目: KTP - G, N & J - GDS DC @ Kempas Tech Park
354	project	projects	17	UPDATE	当前阶段	embed	tendering	3	roy	2025-07-23 06:03:26.520113	\N	10.210.95.118	\N	项目: KTP - G, N & J - GDS DC @ Kempas Tech Park
355	project	projects	17	UPDATE	阶段描述	FMTCS Mr. Fu told these 3 projects still in bidding stages and seems like Longmotive having higher chance to secure.		3	roy	2025-07-23 06:03:26.520117	\N	10.210.95.118	\N	项目: KTP - G, N & J - GDS DC @ Kempas Tech Park
356	project	projects	17	UPDATE	updated_at	2025-07-22 17:46:33.395909	2025-07-23 06:03:26.506594	3	roy	2025-07-23 06:03:26.52012	\N	10.210.95.118	\N	项目: KTP - G, N & J - GDS DC @ Kempas Tech Park
347	project	projects	18	UPDATE	当前阶段	pre_tender	tendering	3	roy	2025-07-23 05:55:31.364165	\N	10.210.220.83	\N	项目: CTP - A - GDS DC @ Chonburi Thailand
348	project	projects	18	UPDATE	阶段描述	FMTCS Mr. Fu told EPG having higher opportunity to secure this project and estimate delivery in this year October time.		3	roy	2025-07-23 05:55:31.36417	\N	10.210.220.83	\N	项目: CTP - A - GDS DC @ Chonburi Thailand
349	project	projects	18	UPDATE	updated_at	2025-07-22 17:51:48.211897	2025-07-23 05:55:31.352162	3	roy	2025-07-23 05:55:31.364172	\N	10.210.220.83	\N	项目: CTP - A - GDS DC @ Chonburi Thailand
350	project	projects	16	UPDATE	设计院		TRAC Consulting & Engineering Sdn Bhd	3	roy	2025-07-23 06:00:16.773551	\N	10.210.36.212	\N	项目: KTP - B & C - GDS DC @ Kempas Tech Park
351	project	projects	16	UPDATE	阶段描述	FMTCS Mr. Fu told already supplied Longmotive for KTP - A, D & E with no issue to these projects. /And now Longmotive secured this KTP - B & C projects with the stage of discussion to preparation the BOM list.		3	roy	2025-07-23 06:00:16.773555	\N	10.210.36.212	\N	项目: KTP - B & C - GDS DC @ Kempas Tech Park
357	customer	companies	28	UPDATE	公司类型	integrator	dealer	2	quah	2025-07-24 01:18:24.946629	\N	10.210.7.144	\N	公司: FMTCS SOLUTIONS PTE. LTD
358	project	projects	19	UPDATE	经销商		FMTCS SOLUTIONS PTE. LTD	3	roy	2025-07-24 01:54:26.609392	\N	10.210.7.144	\N	项目: CTP - C - GDS DC @ Chonburi Thailand
359	project	projects	19	UPDATE	当前阶段	pre_tender	embed	3	roy	2025-07-24 01:54:26.609399	\N	10.210.7.144	\N	项目: CTP - C - GDS DC @ Chonburi Thailand
360	project	projects	19	UPDATE	updated_at	2025-07-24 01:53:18.086096	2025-07-24 01:54:26.597443	3	roy	2025-07-24 01:54:26.609403	\N	10.210.7.144	\N	项目: CTP - C - GDS DC @ Chonburi Thailand
361	project	projects	13	UPDATE	经销商		FMTCS SOLUTIONS PTE. LTD	3	roy	2025-07-24 01:55:25.566551	\N	10.210.60.237	\N	项目: CTP - B - GDS Data Centre @ Chonburi Thailand 
362	project	projects	18	UPDATE	经销商		FMTCS SOLUTIONS PTE. LTD	3	roy	2025-07-24 01:56:33.071084	\N	10.210.230.80	\N	项目: CTP - A - GDS DC @ Chonburi Thailand
363	project	projects	17	UPDATE	经销商		FMTCS SOLUTIONS PTE. LTD	3	roy	2025-07-24 01:57:59.839428	\N	10.210.60.237	\N	项目: KTP - G, N & J - GDS DC @ Kempas Tech Park
364	project	projects	12	UPDATE	经销商		FMTCS SOLUTIONS PTE. LTD	3	roy	2025-07-24 01:58:58.610012	\N	10.210.7.144	\N	项目: NTP - N - GDS DC @ Nusajaya Tech Park 
365	project	projects	12	UPDATE	阶段描述	FMTCS Mr. Fu told NTP - Block F still in assessment and Trac Consult's Eric rejected EPG T&C submission due to supporting rooms & cabins still lack of antennas. /NTP - H ready delivery to EPG's installer YSC. /EPG Secured this GDS NTP Block N but installer have not appoint yet and estimate delivery will be this year September.		3	roy	2025-07-24 01:58:58.610016	\N	10.210.7.144	\N	项目: NTP - N - GDS DC @ Nusajaya Tech Park 
366	project	projects	14	UPDATE	经销商		FMTCS SOLUTIONS PTE. LTD	3	roy	2025-07-24 02:03:23.240471	\N	10.210.220.83	\N	项目: NTP - G & M - GDS DC @ Nusaya Tech Park
367	project	projects	14	UPDATE	阶段描述	FMTCS Mr. Fu told order was issued and now waiting for delivery arrangement.		3	roy	2025-07-24 02:03:23.240475	\N	10.210.220.83	\N	项目: NTP - G & M - GDS DC @ Nusaya Tech Park
368	project	projects	14	UPDATE	交付预测	\N	2025-08-15	3	roy	2025-07-24 02:03:23.240477	\N	10.210.220.83	\N	项目: NTP - G & M - GDS DC @ Nusaya Tech Park
369	project	projects	21	CREATE	\N	\N	\N	3	roy	2025-07-24 02:06:49.929448	\N	10.210.230.80	\N	项目: NTP - K & L - GDS DC @ Nusajaya Tech Park
370	project	projects	15	UPDATE	项目名称	NTP - J, K & L - GDS DC @ Nusajaya Tech Park	NTP - J - GDS DC @ Nusajaya Tech Park	3	roy	2025-07-24 02:09:11.591722	\N	10.210.230.80	\N	项目: NTP - J - GDS DC @ Nusajaya Tech Park
371	project	projects	15	UPDATE	经销商		FMTCS SOLUTIONS PTE. LTD	3	roy	2025-07-24 02:09:11.591732	\N	10.210.230.80	\N	项目: NTP - J - GDS DC @ Nusajaya Tech Park
372	project	projects	15	UPDATE	系统集成商		Longmotive (M) Sdn. Bhd.	3	roy	2025-07-24 02:09:11.591736	\N	10.210.230.80	\N	项目: NTP - J - GDS DC @ Nusajaya Tech Park
373	project	projects	15	UPDATE	当前阶段	embed	tendering	3	roy	2025-07-24 02:09:11.59174	\N	10.210.230.80	\N	项目: NTP - J - GDS DC @ Nusajaya Tech Park
374	project	projects	15	UPDATE	阶段描述	FMTCS Mr. Fu told Longmotive had higher chance to win this NTP - J and estimate delivery in this year September time. / NTP - K & L still in bidding stage between Longmotive & EPG.		3	roy	2025-07-24 02:09:11.591743	\N	10.210.230.80	\N	项目: NTP - J - GDS DC @ Nusajaya Tech Park
375	project	projects	15	UPDATE	交付预测	\N	2025-09-15	3	roy	2025-07-24 02:09:11.591746	\N	10.210.230.80	\N	项目: NTP - J - GDS DC @ Nusajaya Tech Park
376	project	projects	15	UPDATE	updated_at	2025-07-22 09:28:47.785776	2025-07-24 02:09:11.578548	3	roy	2025-07-24 02:09:11.591749	\N	10.210.230.80	\N	项目: NTP - J - GDS DC @ Nusajaya Tech Park
377	project	projects	16	UPDATE	经销商		FMTCS SOLUTIONS PTE. LTD	3	roy	2025-07-24 02:11:26.019211	\N	10.210.95.118	\N	项目: KTP - B & C - GDS DC @ Kempas Tech Park
378	quotation	quotations	14	CREATE	\N	\N	\N	1	admin	2025-07-29 01:32:45.22446	\N	10.210.17.27	\N	报价单: QU202507-005
379	quotation	quotations	14	UPDATE	amount	112310.0	63959.0	1	admin	2025-07-29 01:35:37.34185	\N	10.210.137.234	\N	报价单: QU202507-005
380	quotation	quotations	14	UPDATE	product_signature	78efda304c194617b629b7fcedb9b8cd	f7c2aebb5b75587f2e182d1ea20fc4b4	1	admin	2025-07-29 01:35:37.341857	\N	10.210.137.234	\N	报价单: QU202507-005
381	quotation	quotations	14	UPDATE	implant_total_amount	112310.0	63959.0	1	admin	2025-07-29 01:35:37.341861	\N	10.210.137.234	\N	报价单: QU202507-005
382	quotation	quotations	14	UPDATE	updated_at	2025-07-29 01:32:45.168162	2025-07-29 01:35:37.227872	1	admin	2025-07-29 01:35:37.341865	\N	10.210.137.234	\N	报价单: QU202507-005
383	customer	companies	50	CREATE	\N	\N	\N	2	quah	2025-07-29 07:12:50.833149	\N	10.210.147.87	\N	公司: Supreme Landmobile & Wireless Corporation Sdn. Bhd. (SLW)
384	customer	contacts	61	CREATE	\N	\N	\N	2	quah	2025-07-29 07:13:01.237165	\N	10.210.11.57	\N	记录: Andrew
385	customer	contacts	61	DELETE	\N	\N	\N	2	quah	2025-07-29 07:14:37.917272	\N	10.210.17.27	\N	记录: Andrew
386	customer	contacts	62	CREATE	\N	\N	\N	2	quah	2025-07-29 07:15:35.475843	\N	10.210.17.27	\N	记录: Andrew
387	customer	contacts	63	CREATE	\N	\N	\N	2	quah	2025-07-29 07:17:43.8594	\N	10.210.147.87	\N	记录: Yeo SJ
388	customer	contacts	64	CREATE	\N	\N	\N	2	quah	2025-07-29 07:18:40.938998	\N	10.210.17.27	\N	记录: Norman Anslem
389	customer	companies	51	CREATE	\N	\N	\N	2	quah	2025-07-29 07:35:57.197683	\N	10.210.11.57	\N	公司: Bridge Data Centres Malaysia Sdn Bhd 
390	customer	contacts	65	CREATE	\N	\N	\N	2	quah	2025-07-29 07:37:21.172876	\N	10.210.56.186	\N	记录: Lina Khalida Binti Azhar
391	customer	companies	52	CREATE	\N	\N	\N	2	quah	2025-07-29 07:48:09.940974	\N	10.210.106.165	\N	公司: DcD Technology Sdn Bhd 
392	customer	contacts	66	CREATE	\N	\N	\N	2	quah	2025-07-29 07:49:01.649579	\N	10.210.137.234	\N	记录: Irwin Hon
393	project	projects	22	CREATE	\N	\N	\N	2	quah	2025-07-29 08:15:01.155245	\N	10.210.17.27	\N	项目: PNB 118 
394	quotation	quotations	15	CREATE	\N	\N	\N	2	quah	2025-07-29 08:28:50.042742	\N	10.210.147.87	\N	报价单: QU202507-006
395	customer	companies	53	CREATE	\N	\N	\N	3	roy	2025-08-04 08:25:47.506777	\N	10.210.99.195	\N	公司: Timesfly Engineering Services 时代飞扬
396	customer	contacts	67	CREATE	\N	\N	\N	3	roy	2025-08-04 08:27:57.383966	\N	10.210.85.58	\N	记录: 韩丹丹
397	project	projects	11	UPDATE	系统集成商		Timesfly Engineering Services 时代飞扬	3	roy	2025-08-04 08:46:36.618454	\N	10.210.51.137	\N	项目: Bridge Data Centre @ Chonburi, Thailand
398	project	projects	11	UPDATE	industry		datacenter	3	roy	2025-08-04 08:46:36.618461	\N	10.210.51.137	\N	项目: Bridge Data Centre @ Chonburi, Thailand
399	customer	companies	54	CREATE	\N	\N	\N	2	quah	2025-08-05 09:42:29.556874	\N	10.210.148.17	\N	公司: O'Connor's Engineering Sdn Bhd
400	customer	contacts	68	CREATE	\N	\N	\N	2	quah	2025-08-05 09:44:14.216252	\N	10.210.51.137	\N	记录: Khey Heng Soon
401	customer	contacts	69	CREATE	\N	\N	\N	2	quah	2025-08-05 09:45:39.377519	\N	10.210.148.17	\N	记录: Woo Siew Wai
402	project	projects	22	UPDATE	系统集成商	Vertex Communication Sdn Bhd	O'Connor's Engineering Sdn Bhd	2	quah	2025-08-05 09:47:28.92366	\N	10.210.85.58	\N	项目: PNB 118 
403	customer	companies	55	CREATE	\N	\N	\N	2	quah	2025-08-06 01:37:25.986117	\N	10.210.141.114	\N	公司: Mot Smart Solutions Company Limited (Head office)
404	customer	contacts	70	CREATE	\N	\N	\N	2	quah	2025-08-06 01:38:29.532983	\N	10.210.51.137	\N	记录: Surasak J. (Paul)
405	user	users	7	CREATE	\N	\N	\N	1	admin	2025-08-06 06:40:17.101306	\N	10.210.51.137	\N	公司: Triple Access
406	user	users	8	CREATE	\N	\N	\N	1	admin	2025-08-06 06:41:23.518214	\N	10.210.99.195	\N	公司: Technics Communication & Electronics Pte Ltd
407	user	users	9	CREATE	\N	\N	\N	1	admin	2025-08-06 06:43:16.576845	\N	10.210.141.114	\N	公司: evertacsolutions
408	user	users	5	UPDATE	is_department_manager	False	True	1	admin	2025-08-06 08:57:54.24994	\N	10.210.148.17	\N	公司: evertacsolutions
409	user	users	5	UPDATE	updated_at	1754462987.1851716	1754470674.22961	1	admin	2025-08-06 08:57:54.249947	\N	10.210.148.17	\N	公司: evertacsolutions
410	customer	companies	58	CREATE	\N	\N	\N	1	admin	2025-08-07 04:16:57.408776	\N	10.210.223.98	\N	公司: 11
411	customer	companies	58	DELETE	\N	\N	\N	1	admin	2025-08-07 04:17:13.053886	\N	10.210.51.160	\N	公司: 11
412	customer	companies	59	CREATE	\N	\N	\N	7	yusry	2025-08-07 06:15:30.859602	\N	10.210.223.98	\N	公司: Yusry
413	customer	contacts	71	CREATE	\N	\N	\N	7	yusry	2025-08-07 06:16:01.33588	\N	10.210.40.47	\N	记录: Yusry
414	project	projects	23	CREATE	\N	\N	\N	7	yusry	2025-08-07 06:20:22.0801	\N	10.210.182.164	\N	项目: Yusry
415	quotation	quotations	16	CREATE	\N	\N	\N	7	yusry	2025-08-07 06:22:39.507399	\N	10.210.207.209	\N	报价单: QU202508-001
416	customer	companies	59	DELETE	\N	\N	\N	7	yusry	2025-08-07 06:28:02.129666	\N	10.210.223.98	\N	公司: Yusry
417	project	projects	23	DELETE	\N	\N	\N	7	yusry	2025-08-07 06:28:14.334504	\N	10.210.51.160	\N	项目: Yusry
418	project	projects	24	CREATE	\N	\N	\N	7	yusry	2025-08-07 06:32:52.922911	\N	10.210.40.47	\N	项目: PNB 118
419	project	projects	25	CREATE	\N	\N	\N	7	yusry	2025-08-07 06:36:58.918813	\N	10.210.81.164	\N	项目: MyO2
420	project	projects	25	DELETE	\N	\N	\N	7	yusry	2025-08-07 06:38:17.246441	\N	10.210.51.160	\N	项目: MyO2
421	quotation	quotations	17	CREATE	\N	\N	\N	7	yusry	2025-08-07 06:39:57.739338	\N	10.210.182.164	\N	报价单: QU202508-001
422	quotation	quotations	17	DELETE	\N	\N	\N	7	yusry	2025-08-07 06:42:26.375556	\N	10.210.40.47	\N	报价单: QU202508-001
423	project	projects	24	DELETE	\N	\N	\N	7	yusry	2025-08-07 06:42:34.730348	\N	10.210.51.160	\N	项目: PNB 118
424	project	projects	26	CREATE	\N	\N	\N	7	yusry	2025-08-07 06:44:26.603849	\N	10.210.223.98	\N	项目: PNB 118
425	customer	companies	60	CREATE	\N	\N	\N	7	yusry	2025-08-07 06:58:16.87728	\N	10.210.51.160	\N	公司: RADII Teknologi Sdn Bhd
426	customer	contacts	72	CREATE	\N	\N	\N	7	yusry	2025-08-07 06:59:19.626787	\N	10.210.207.209	\N	记录: Tan Siew Chen
427	customer	contacts	73	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:03:25.827316	\N	10.210.40.47	\N	记录: Tan Wee Meng
428	customer	contacts	72	DELETE	\N	\N	\N	7	yusry	2025-08-07 07:04:16.42862	\N	10.210.51.160	\N	记录: Tan Siew Chen
429	customer	contacts	74	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:05:04.493371	\N	10.210.207.209	\N	记录: Tan Siew Chen
430	customer	companies	61	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:11:35.311628	\N	10.210.40.47	\N	公司: SP Infocomm Solutions Sdn Bhd
431	customer	contacts	75	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:12:51.080464	\N	10.210.40.47	\N	记录: Yeoh Por Sie
432	customer	contacts	76	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:13:51.98896	\N	10.210.223.98	\N	记录: SP Yeoh
433	customer	companies	62	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:20:53.085727	\N	10.210.81.164	\N	公司: OGX Industrial Supplies Sdn Bhd (OIS)
434	customer	contacts	77	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:23:26.811647	\N	10.210.182.164	\N	记录: Alvin Chang
435	customer	contacts	78	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:25:08.6325	\N	10.210.40.47	\N	记录: Owen Lam
436	customer	contacts	77	DELETE	\N	\N	\N	7	yusry	2025-08-07 07:25:15.307884	\N	10.210.223.98	\N	记录: Alvin Chang
437	customer	companies	63	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:27:47.489254	\N	10.210.223.98	\N	公司: iOi MALLS
438	customer	contacts	79	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:28:45.222802	\N	10.210.182.164	\N	记录: Mohd Asri Bin Bakar
439	customer	contacts	80	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:29:32.818205	\N	10.210.40.47	\N	记录: Richard Chu
440	customer	contacts	81	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:30:15.348775	\N	10.210.51.160	\N	记录: Mohammad Riduan Bin Mat Ali
441	project	projects	27	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:33:04.823936	\N	10.210.182.164	\N	项目: AirTrunk
442	customer	companies	64	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:43:10.561365	\N	10.210.51.160	\N	公司: AirTrunk Malaysia Sdn Bhd
443	customer	contacts	82	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:44:45.624614	\N	10.210.51.160	\N	记录: Au Yong Wai Yee
444	project	projects	27	UPDATE	最终用户		AirTrunk Malaysia Sdn Bhd	7	yusry	2025-08-07 07:45:27.696585	\N	10.210.182.164	\N	项目: AirTrunk
445	quotation	quotations	18	CREATE	\N	\N	\N	7	yusry	2025-08-07 07:55:30.641237	\N	10.210.207.209	\N	报价单: QU202508-001
446	quotation	quotations	18	UPDATE	updated_at	2025-08-07 07:55:30.623950	2025-08-07 07:56:02.238232	7	yusry	2025-08-07 07:56:02.238964	\N	10.210.40.47	\N	报价单: QU202508-001
447	quotation	quotations	18	UPDATE	amount	10040.0	10160.0	7	yusry	2025-08-07 07:58:29.986304	\N	10.210.81.164	\N	报价单: QU202508-001
448	quotation	quotations	18	UPDATE	product_signature	3965bda1f3b96d7cac83a85ed4fededc	1f8ebee5054be74259db6c53ea16c90f	7	yusry	2025-08-07 07:58:29.986308	\N	10.210.81.164	\N	报价单: QU202508-001
449	quotation	quotations	18	UPDATE	implant_total_amount	8770.0	9240.0	7	yusry	2025-08-07 07:58:29.986311	\N	10.210.81.164	\N	报价单: QU202508-001
450	quotation	quotations	18	UPDATE	updated_at	2025-08-07 07:56:02.238232	2025-08-07 07:58:29.984445	7	yusry	2025-08-07 07:58:29.986313	\N	10.210.81.164	\N	报价单: QU202508-001
455	quotation	quotations	18	UPDATE	amount	12829.039999999999	12240.039999999999	7	yusry	2025-08-07 08:03:22.14978	\N	10.210.182.164	\N	报价单: QU202508-001
456	quotation	quotations	18	UPDATE	updated_at	2025-08-07 08:02:11.971541	2025-08-07 08:03:22.148275	7	yusry	2025-08-07 08:03:22.149785	\N	10.210.182.164	\N	报价单: QU202508-001
459	quotation	quotations	18	UPDATE	amount	18130.04	18890.0	7	yusry	2025-08-07 08:07:03.986213	\N	10.210.81.164	\N	报价单: QU202508-001
460	quotation	quotations	18	UPDATE	product_signature	d7df424396b52ff74712274a146ff572	6c1e6922aee1644ef7762f96670144b7	7	yusry	2025-08-07 08:07:03.986219	\N	10.210.81.164	\N	报价单: QU202508-001
461	quotation	quotations	18	UPDATE	implant_total_amount	11130.0	11820.0	7	yusry	2025-08-07 08:07:03.986222	\N	10.210.81.164	\N	报价单: QU202508-001
462	quotation	quotations	18	UPDATE	updated_at	2025-08-07 08:03:58.726484	2025-08-07 08:07:03.985031	7	yusry	2025-08-07 08:07:03.986224	\N	10.210.81.164	\N	报价单: QU202508-001
451	quotation	quotations	18	UPDATE	amount	10160.0	12829.039999999999	7	yusry	2025-08-07 08:02:11.973225	\N	10.210.182.164	\N	报价单: QU202508-001
452	quotation	quotations	18	UPDATE	product_signature	1f8ebee5054be74259db6c53ea16c90f	d7df424396b52ff74712274a146ff572	7	yusry	2025-08-07 08:02:11.973231	\N	10.210.182.164	\N	报价单: QU202508-001
453	quotation	quotations	18	UPDATE	implant_total_amount	9240.0	11130.0	7	yusry	2025-08-07 08:02:11.973235	\N	10.210.182.164	\N	报价单: QU202508-001
454	quotation	quotations	18	UPDATE	updated_at	2025-08-07 07:58:29.984445	2025-08-07 08:02:11.971541	7	yusry	2025-08-07 08:02:11.973238	\N	10.210.182.164	\N	报价单: QU202508-001
457	quotation	quotations	18	UPDATE	amount	12240.039999999999	18130.04	7	yusry	2025-08-07 08:03:58.727809	\N	10.210.223.98	\N	报价单: QU202508-001
458	quotation	quotations	18	UPDATE	updated_at	2025-08-07 08:03:22.148275	2025-08-07 08:03:58.726484	7	yusry	2025-08-07 08:03:58.727814	\N	10.210.223.98	\N	报价单: QU202508-001
463	quotation	quotations	18	UPDATE	amount	18890.0	21590.0	7	yusry	2025-08-07 08:08:51.111238	\N	10.210.207.209	\N	报价单: QU202508-001
464	quotation	quotations	18	UPDATE	product_signature	6c1e6922aee1644ef7762f96670144b7	2e1d0e381902641a90eb230def1a47a8	7	yusry	2025-08-07 08:08:51.111244	\N	10.210.207.209	\N	报价单: QU202508-001
465	quotation	quotations	18	UPDATE	updated_at	2025-08-07 08:07:03.985031	2025-08-07 08:08:51.109802	7	yusry	2025-08-07 08:08:51.111248	\N	10.210.207.209	\N	报价单: QU202508-001
466	project	projects	26	DELETE	\N	\N	\N	7	yusry	2025-08-07 08:26:09.427027	\N	10.210.40.47	\N	项目: PNB 118
467	customer	companies	65	CREATE	\N	\N	\N	2	quah	2025-08-07 08:37:01.878884	\N	10.210.51.160	\N	公司: TM Technology Service Sdn Bhd 
468	project	projects	22	UPDATE	厂商负责人	\N	2	1	admin	2025-08-07 08:38:01.939634	\N	10.210.182.164	\N	项目: PNB 118 
469	customer	contacts	83	CREATE	\N	\N	\N	2	quah	2025-08-07 08:58:51.408465	\N	10.210.51.160	\N	记录: Zanirul Akhmal Bin Zanirun 
470	customer	companies	66	CREATE	\N	\N	\N	1	admin	2025-08-09 15:25:40.200918	\N	10.210.179.93	\N	公司: test new database
471	customer	companies	66	DELETE	\N	\N	\N	1	admin	2025-08-09 15:26:02.336974	\N	10.210.179.93	\N	公司: test new database
472	user	users	10	CREATE	\N	\N	\N	1	admin	2025-08-11 01:53:33.325955	\N	10.210.122.254	\N	公司: evertacsolutions
473	user	users	11	CREATE	\N	\N	\N	1	admin	2025-08-11 01:54:20.316619	\N	10.210.170.0	\N	公司: evertacsolutions
475	customer	companies	67	CREATE	\N	\N	\N	12	fuyan	2025-08-11 02:34:35.616445	\N	10.210.60.154	\N	公司: EPG
476	customer	companies	68	CREATE	\N	\N	\N	12	fuyan	2025-08-11 02:36:06.269947	\N	10.210.75.183	\N	公司: ysc
477	project	projects	28	CREATE	\N	\N	\N	12	fuyan	2025-08-11 02:49:30.468967	\N	10.210.179.93	\N	项目: NTP-N
478	customer	companies	68	DELETE	\N	\N	\N	1	admin	2025-08-11 02:56:09.228162	\N	10.210.75.183	\N	公司: ysc
479	customer	companies	67	DELETE	\N	\N	\N	1	admin	2025-08-11 02:56:14.709971	\N	10.210.179.93	\N	公司: EPG
480	project	projects	29	CREATE	\N	\N	\N	12	fuyan	2025-08-11 03:03:18.832556	\N	10.210.179.93	\N	项目: CTP-A
481	project	projects	29	UPDATE	项目名称	CTP-A	CTP-B1/B2	12	fuyan	2025-08-11 03:19:45.875656	\N	10.210.106.114	\N	项目: CTP-B1/B2
482	project	projects	29	UPDATE	阶段描述	目前EPG确认中标机电总包，EPG往下寻找系统集成商，目前配合了YSC、郎泽两家在参与配合。	目前宏远确认中标机电总包，宏远往下寻找系统集成商，目前配合了曹磊、仵磊两家在参与配合。	12	fuyan	2025-08-11 03:21:43.689478	\N	10.210.179.93	\N	项目: CTP-B1/B2
483	project	projects	30	CREATE	\N	\N	\N	12	fuyan	2025-08-11 03:32:43.755152	\N	10.210.60.154	\N	项目: CTP-A
484	project	projects	29	DELETE	\N	\N	\N	12	fuyan	2025-08-11 03:34:53.602613	\N	10.210.106.114	\N	项目: CTP-B1/B2
485	project	projects	30	DELETE	\N	\N	\N	12	fuyan	2025-08-11 03:35:17.221367	\N	10.210.106.114	\N	项目: CTP-A
486	project	projects	13	UPDATE	项目名称	CTP - B - GDS Data Centre @ Chonburi Thailand 	CTP - B1\\B2 - GDS Data Centre @ Chonburi Thailand 	12	fuyan	2025-08-11 03:38:09.05616	\N	10.210.179.93	\N	项目: CTP - B1\\B2 - GDS Data Centre @ Chonburi Thailand 
487	project	projects	13	UPDATE	阶段描述		目前已经确认朗茂中标，向下寻找系统集成商，目前配合了曹磊和仵磊两家单位	12	fuyan	2025-08-11 03:38:09.056168	\N	10.210.179.93	\N	项目: CTP - B1\\B2 - GDS Data Centre @ Chonburi Thailand 
488	project	projects	13	UPDATE	shared_with_users	[]	[1, 2, 3, 5, 10, 11]	12	fuyan	2025-08-11 03:38:09.056171	\N	10.210.179.93	\N	项目: CTP - B1\\B2 - GDS Data Centre @ Chonburi Thailand 
489	project	projects	13	UPDATE	share_enabled	False	True	12	fuyan	2025-08-11 03:38:09.056174	\N	10.210.179.93	\N	项目: CTP - B1\\B2 - GDS Data Centre @ Chonburi Thailand 
490	project	projects	28	UPDATE	报备来源	sales	channel	12	fuyan	2025-08-11 04:03:38.80864	\N	10.210.75.183	\N	项目: NTP-N
491	customer	companies	69	CREATE	\N	\N	\N	2	quah	2025-08-11 05:16:15.708372	\N	10.210.106.114	\N	公司: Bandway Engineering (M) Sdn Bhd
492	customer	contacts	84	CREATE	\N	\N	\N	2	quah	2025-08-11 05:32:37.024251	\N	10.210.179.93	\N	记录: Chua Lee Lee
493	customer	contacts	85	CREATE	\N	\N	\N	3	roy	2025-08-12 03:16:39.689542	\N	10.210.106.114	\N	记录: Reena Chow
494	customer	companies	70	CREATE	\N	\N	\N	3	roy	2025-08-12 03:20:52.645661	\N	10.210.122.254	\N	公司: Duriane Professionals Sdn Bhd
495	customer	contacts	86	CREATE	\N	\N	\N	3	roy	2025-08-12 03:22:48.963199	\N	10.210.179.93	\N	记录: Ms. Mimi Afifah
496	user	users	1	UPDATE	real_name	系统管理员	james.ni	1	admin	2025-08-12 04:12:35.392303	\N	10.210.122.254	\N	公司: evertacsolutions
497	user	users	1	UPDATE	updated_at	1754969991.34636	1754971955.37563	1	admin	2025-08-12 04:12:35.392307	\N	10.210.122.254	\N	公司: evertacsolutions
498	customer	companies	71	CREATE	\N	\N	\N	1	admin	2025-08-12 04:29:07.459788	\N	10.210.170.0	\N	公司: PT. CITRADATA INDONUSA
499	customer	contacts	87	CREATE	\N	\N	\N	1	admin	2025-08-12 04:31:23.675842	\N	10.210.60.154	\N	记录: Gama Waney
500	customer	contacts	88	CREATE	\N	\N	\N	1	admin	2025-08-12 04:33:04.487703	\N	10.210.179.93	\N	记录: Mario Lukman
501	customer	companies	72	CREATE	\N	\N	\N	1	admin	2025-08-12 05:02:01.801698	\N	10.210.75.183	\N	公司: COMMUTRONICS ENTERPRISE CO., LTD
502	customer	contacts	89	CREATE	\N	\N	\N	1	admin	2025-08-12 05:04:49.876082	\N	10.210.75.183	\N	记录: Nelson.曾国栋
503	customer	companies	73	CREATE	\N	\N	\N	1	admin	2025-08-12 05:10:38.753431	\N	10.210.60.154	\N	公司: C.A. Sheimer (HK) Ltd
504	customer	contacts	90	CREATE	\N	\N	\N	1	admin	2025-08-12 05:11:55.994027	\N	10.210.179.93	\N	记录: Michael Ho
505	customer	contacts	91	CREATE	\N	\N	\N	2	quah	2025-08-12 05:45:04.691187	\N	10.210.75.183	\N	记录: Johnson
506	customer	contacts	92	CREATE	\N	\N	\N	2	quah	2025-08-12 07:39:30.860277	\N	10.210.106.114	\N	记录: Mohd Zaimi 
507	project	projects	31	CREATE	\N	\N	\N	2	quah	2025-08-12 08:00:26.681937	\N	10.210.179.93	\N	项目: TM Iskandar Puteri Data Centre (IPDC)
508	customer	contacts	70	UPDATE	updated_at	2025-08-06 09:38:29.521511	2025-08-12 17:44:47.427545	2	quah	2025-08-12 09:44:47.447665	\N	10.210.179.93	\N	记录: Surasak J. (Paul)
509	customer	contacts	70	UPDATE	备注		Had share our general presentation slide and sale training slide with Mr. Surask for their in-house training. \r\nBeside requesting the NBTC guidelines what is the frequency allow use in Thailand and procedure / fee to apply it, pending the information from him now. 	2	quah	2025-08-12 09:44:47.44767	\N	10.210.179.93	\N	记录: Surasak J. (Paul)
510	quotation	quotations	18	UPDATE	amount	21590.0	21707.0	7	yusry	2025-08-13 02:25:04.348708	\N	10.210.23.23	\N	报价单: QU202508-001
511	quotation	quotations	18	UPDATE	product_signature	2e1d0e381902641a90eb230def1a47a8	05881cc3ba66f5c0e2ac415d2c778089	7	yusry	2025-08-13 02:25:04.348713	\N	10.210.23.23	\N	报价单: QU202508-001
512	quotation	quotations	18	UPDATE	updated_at	2025-08-07 08:08:51.109802	2025-08-13 02:25:04.347177	7	yusry	2025-08-13 02:25:04.348716	\N	10.210.23.23	\N	报价单: QU202508-001
513	quotation	quotations	18	UPDATE	amount	21707.0	22505.997	7	yusry	2025-08-13 02:38:39.232482	\N	10.210.179.122	\N	报价单: QU202508-001
514	quotation	quotations	18	UPDATE	product_signature	05881cc3ba66f5c0e2ac415d2c778089	2ee12474f988798745024e8962ebb148	7	yusry	2025-08-13 02:38:39.232486	\N	10.210.179.122	\N	报价单: QU202508-001
515	quotation	quotations	18	UPDATE	updated_at	2025-08-13 02:25:04.347177	2025-08-13 02:38:39.231170	7	yusry	2025-08-13 02:38:39.232489	\N	10.210.179.122	\N	报价单: QU202508-001
516	project	projects	32	CREATE	\N	\N	\N	2	quah	2025-08-14 07:48:22.956152	\N	10.210.205.21	\N	项目: Demonstration Set
517	customer	contacts	93	CREATE	\N	\N	\N	1	admin	2025-08-15 01:48:23.541471	\N	10.210.167.141	\N	记录: Adrian Bany Kansil
518	quotation	quotations	19	CREATE	\N	\N	\N	2	quah	2025-08-15 02:03:00.735523	\N	10.210.172.229	\N	报价单: QU202508-002
519	quotation	quotations	19	UPDATE	product_signature	125008580b9f31fe	bde7b7a43b04330328b919a66d551273	2	quah	2025-08-15 02:05:11.95047	\N	10.210.172.229	\N	报价单: QU202508-002
520	quotation	quotations	19	UPDATE	updated_at	2025-08-15 02:03:00.704345	2025-08-15 02:05:11.949107	2	quah	2025-08-15 02:05:11.950475	\N	10.210.172.229	\N	报价单: QU202508-002
521	quotation	quotations	19	UPDATE	amount	3290.0	31194.0	2	quah	2025-08-15 02:22:27.254167	\N	10.210.172.229	\N	报价单: QU202508-002
522	quotation	quotations	19	UPDATE	product_signature	bde7b7a43b04330328b919a66d551273	bff43007b7bbeb1792df3bbae2651bdf	2	quah	2025-08-15 02:22:27.254171	\N	10.210.172.229	\N	报价单: QU202508-002
523	quotation	quotations	19	UPDATE	implant_total_amount	3290.0	28544.0	2	quah	2025-08-15 02:22:27.254174	\N	10.210.172.229	\N	报价单: QU202508-002
524	quotation	quotations	19	UPDATE	updated_at	2025-08-15 02:05:11.949107	2025-08-15 02:22:27.252753	2	quah	2025-08-15 02:22:27.254175	\N	10.210.172.229	\N	报价单: QU202508-002
525	quotation	quotations	19	UPDATE	amount	31194.0	32060.899999999998	2	quah	2025-08-15 02:28:10.142649	\N	10.210.172.229	\N	报价单: QU202508-002
526	quotation	quotations	19	UPDATE	product_signature	bff43007b7bbeb1792df3bbae2651bdf	54bbd12cc6f9a9ebf905218150643f40	2	quah	2025-08-15 02:28:10.142659	\N	10.210.172.229	\N	报价单: QU202508-002
527	quotation	quotations	19	UPDATE	updated_at	2025-08-15 02:22:27.252753	2025-08-15 02:28:10.139042	2	quah	2025-08-15 02:28:10.142663	\N	10.210.172.229	\N	报价单: QU202508-002
\.


--
-- TOC entry 4763 (class 0 OID 24047)
-- Dependencies: 289
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.companies (id, company_code, company_name, country, region, address, industry, company_type, status, created_at, updated_at, notes, is_deleted, owner_id, shared_with_users, share_contacts, share_enabled) FROM stdin;
15	25F30010	MCS Management Sdn Bhd	MY	Selangor	X32, X, 9-G & 9-1, Jalan Sungai Burung 32/68, Bukit Rimau, 40460 Shah Alam, Selangor	health	designer	active	2025-06-30 06:27:31.418087	2025-07-11 17:33:46.118162		f	2	[3]	t	f
38	25G10003	 Syarikat Pembenaan Yeoh Tiong Lay Sdn Bhd (YTL Construction) 	MY	Kuala Lumpur	19 - 24th Floor, Menara YTL, 205, Jalan Bukit Bintang , 55100 , Kuala Lumpur	other	contractor	active	2025-07-10 01:50:59.596652	2025-07-10 09:50:59.611157		f	3	[]	t	f
60	25H07001	RADII Teknologi Sdn Bhd	MY	Selangor	No. 327, Jalan Teluk Gadong / KS1, off, Persiaran Raja Muda Musa, 42000 Pelabuhan Klang, Selangor	other	dealer	active	2025-08-07 14:58:16.859039	2025-08-07 15:05:04.49676		f	7	[]	t	f
40	25G16001	Stream Communication System Sdn Bhd	MY	Kuala Lumpur	12-2, Jalan Kuchai Maju 19, Kuchai Entrepreneurs Park, 58200 Kuala Lumpur, Wilayah Persekutuan Kuala Lumpur	datacenter	integrator	active	2025-07-16 15:05:46.267793	2025-07-16 15:21:29.922262		f	2	[]	t	f
61	25H07002	SP Infocomm Solutions Sdn Bhd	MY	Selangor	CT-01-05, Corporate Tower, Subang Square Business Centre, 47500 Subang Jaya, Selangor	other	dealer	active	2025-08-07 15:11:35.302137	2025-08-07 15:13:51.991965		f	7	[]	t	f
62	25H07003	OGX Industrial Supplies Sdn Bhd (OIS)	MY	Selangor	20, Jalan Astaka U8/84A, Taman Perindustrian Bukit Jelutong, Seksyen, U8 Shah Alam, 40150 Shah Alam, Selangor	other	dealer	active	2025-08-07 15:20:53.075649	2025-08-07 15:25:08.635927		f	7	[]	t	f
63	25H07004	iOi MALLS	MY	Selangor	Management Office, Unit T2-3A-3 & Unit T2-3A-3A Level 3A, IOI City Tower Two, Lbh IRC, Ioi Resort, 62502 Putrajaya, Selangor	hospitality	user	active	2025-08-07 15:27:47.475331	2025-08-07 15:30:15.355639		f	7	[]	t	f
64	25H07005	AirTrunk Malaysia Sdn Bhd	MY	Johor	Jalan Bioteknologi 3, Johor, Malaysia	datacenter	user	active	2025-08-07 15:43:10.551844	2025-08-07 15:44:45.628382		f	7	[]	t	f
51	25G29002	Bridge Data Centres Malaysia Sdn Bhd 	MY	Selangor	MY02, Jalan Cyber Point 2, Cyber 12, 63000 Seremban Negeri Sembilan	datacenter	user	active	2025-07-29 15:35:57.187786	2025-08-05 16:43:13.42398		f	2	[]	t	f
41	25G16002	Asalcom Sdn Bhd	MY	Kuala Lumpur	Suite 16-1, Menara Mutiara Sentral, 2, Jalan Desa Aman 1, Cheras Business Centre, 56000 Kuala Lumpur, Federal Territory of Kuala Lumpur	datacenter	integrator	active	2025-07-16 15:23:09.237429	2025-07-16 15:32:54.477481		f	2	[]	t	f
17	25F30012	Engenious Solutions Sdn Bhd	MY	Selangor	Sekitar 26, No 25, Level, 1, Jalan Serendah 26/41, Seksyen 26, 40400 Shah Alam, Selangor	real_estate	contractor	active	2025-06-30 06:38:47.585461	2025-07-11 17:31:12.850498		f	2	[3]	t	f
18	25F30013	Unique Arena Sdn Bhd	MY	Selangor	12, Jalan Layang - Layang 5A, Bandar Puchong Jaya, 47170 Puchong, Selangor	real_estate	integrator	active	2025-06-30 06:41:30.650289	2025-07-11 17:28:08.977939		f	2	[3]	t	f
19	25F30014	Ace Sonic Communications Sdn Bhd	MY	Johor	No. 19 & 19-1, Jalan Sagu 16, Taman Daya, 81100 Johor Bahru, Johor Darul Takzim	transport	dealer	active	2025-06-30 06:44:09.482517	2025-07-11 17:25:19.715348		f	2	[3]	t	f
6	25F30001	Reach Integrated Sdn Bhd	MY	Kuala Lumpur	No. 35-3, Block 1D, Jalan Wangsa Delima 12, Wangsa Link / D’wangsa, 53300 Wangsa Maju, Kuala Lumpur, Malaysia.	energy	integrator	active	2025-06-30 03:18:59.917753	2025-07-11 18:00:28.875275		f	2	[3]	t	f
13	25F30008	Electcoms Berhad	MY	Selangor	12 A, Jalan 13/4, Seksyen 13, 46200 Petaling Jaya, Selangor	manufacturing	integrator	active	2025-06-30 06:16:11.805567	2025-07-11 17:37:05.79411		f	2	[3]	t	f
14	25F30009	Mymeta Solution Sdn Bhd	MY	Selangor	Suite 1-12, CJ1 Centre, No. 1, Jalan Cyber Point 4, Cyber 8, 63000 Cyberjaya, Selangor Darul Ehsan. 	other	integrator	active	2025-06-30 06:22:43.998319	2025-07-18 09:52:08.08993		f	2	[3]	t	f
22	25F30017	MEG Consult Sdn. Bhd.	MY	Kuala Lumpur	 46-1, Jln Metro Perdana Barat 2, Taman Usahawan Kepong, 52100 Kuala Lumpur.	other	designer	active	2025-06-30 06:59:16.688945	2025-06-30 15:11:45.437156		f	3	[2, 4, 5]	t	f
8	25F30003	Synergy Oil & Gas Engineering Sdn Bhd	MY	Selangor	No. 31, Jalan Serendah 26/41,  Kawasan Perindustrian Hicom,  Seksyen 26, 40400 Shah Alam,  Selangor, Malaysia	other	designer	active	2025-06-30 03:35:46.277694	2025-07-14 10:29:32.040236		f	2	[3]	t	f
10	25F30005	Technip FMC	MY	Kuala Lumpur	Tower, 19, TSLAW, 03, Jalan Kamuning, Imbi, 55100 Kuala Lumpur, Federal Territory of Kuala Lumpur	energy	designer	active	2025-06-30 04:24:23.119513	2025-07-11 17:52:27.402466		f	2	[3]	t	f
11	25F30006	Axis Technology Resources (M) Sdn Bhd	MY	Selangor	G-23, MKH Boulevard, Jalan Bukit, Bandar Kajang, 43000 Kajang, Selangor	energy	contractor	active	2025-06-30 04:26:20.730197	2025-07-11 17:50:44.796265		f	2	[3]	t	f
25	25F30020	SKA Technology Sdn Bhd	MY	Kuala Lumpur	No 26, Jalan Siput Akek, Taman Billion, 56000 Kuala Lumpur, Wilayah Persekutuan Kuala Lumpur	real_estate	integrator	active	2025-06-30 07:30:08.910648	2025-07-22 22:54:00.101942		f	3	[2, 4, 5]	t	f
48	25G22005	Wire & Wireless Sdn Bhd	MY	Selangor	42, Jalan TP 7/1, Taman Perindustrian Uep, 47620 Subang Jaya, Selangor	other	integrator	active	2025-07-22 17:48:37.037535	2025-07-22 17:52:26.198536		f	2	[]	t	f
9	25F30004	Tactical Communications Sdn Bhd	MY	Selangor	20, Jalan PP 20, Taman Pinggiran Putra, 43300 Seri Kembangan, Selangor	government	contractor	active	2025-06-30 03:44:33.745339	2025-07-11 17:57:22.64966		f	2	[3]	t	f
36	25G10001	SIPP Power Sdn Bhd (subsidiary of YTL Corporation Bhd)	MY	Kuala Lumpur	33rd Floor, Menara YTL, 205 Jalan Bukit Bintang , 55100 , Kuala Lumpur , Malaysia	real_estate	user	active	2025-07-10 01:34:51.562963	2025-07-10 09:34:51.577917		f	3	[2, 4, 5]	t	f
29	25F30024	Pembinaan Mitrajaya Sdn. Bhd.	MY	Selangor	No. 9, Block D, Pusat Perdagangan Puchong Prima, Persiaran Prima Utama, Taman Puchong Prima, 47150 Puchong, Selangor	other	contractor	active	2025-06-30 08:41:24.483104	2025-07-08 09:55:47.631153		f	3	[2, 4, 5]	t	f
31	25G01001	Electrica Technology Sdn Bhd	MY	Selangor	1-3, JALAN PUTERI 3A/1, ENIGMA SQUARE, BANDAR PUTERI BANGI, 43000 KAJANG, SELANGOR.	real_estate	contractor	active	2025-07-01 01:39:40.299777	2025-07-01 09:50:31.687504		f	2	[3]	t	f
34	25G09003	CCIE Engineering (M) Sdn. Bhd.	MY	Kuala Lumpur	Wisma Uoa Centre, Kuala Lumpur, 50450 Kuala Lumpur.	other	contractor	inactive	2025-07-09 07:19:24.678782	2025-07-09 15:21:47.367079		f	3	[2, 4, 5]	t	f
23	25F30018	Binastra Corporation Bhd	MY	Kuala Lumpur	No 1 & 3, Jalan Jalil Jaya 3, Jalil Link, Bukit Jalil, 57000 Kuala Lumpur.	other	contractor	active	2025-06-30 07:16:04.787779	2025-07-08 10:02:50.577268		f	3	[2, 1]	t	f
32	25G09001	Bridge Data Centres -  (Subsidiary of Chindata Group @ Beijing)	CN	北京市	Building 8, Wangjing Chengying Center, Chaoyang District, Beijing, China	other	user	inactive	2025-07-09 06:53:03.259073	2025-07-09 15:08:58.013676		f	3	[2, 3, 4, 5, 9, 10, 11, 12]	t	t
33	25G09002	Dynast Consult Sdn. Bhd.	MY	Selangor	20, Jln Sungai Burung AA32/AA, Bukit Rimau, 40460 Shah Alam, Selangor	other	designer	active	2025-07-09 07:12:20.248078	2025-08-12 11:09:40.578777		f	3	[2, 4, 5]	t	f
37	25G10002	TRAC Consulting & Engineering Sdn Bhd	MY	Selangor	E1-05-08, Tamarind Square, Persiaran Multimedia, Cyber 10, 63000 Cyberjaya, Selangor	other	designer	active	2025-07-10 01:44:32.414258	2025-08-12 11:17:55.62137	Security consultant & parent company is AIP Risk Consulting Pte. Ltd. @ Singapore.	f	3	[2, 4, 5]	t	f
65	25H07006	TM Technology Service Sdn Bhd 	MY	Kuala Lumpur	Level 30, TM Annexe 2, Jalan Pantai Jaya, 59200 Kuala Lumpur, Malaysia 	other	integrator	active	2025-08-07 16:37:01.866881	2025-08-12 15:50:33.165359		f	2	[]	t	f
27	25F30022	MCC Technique Sdn. Bhd.	MY	Selangor	12, Jalan PPU 2A, Taman Perindustrian Puchong Utama, 47100 Puchong, Selangor	real_estate	integrator	active	2025-06-30 07:43:59.217899	2025-07-08 09:57:19.26978		f	3	[2, 4, 5]	t	f
16	25F30011	BHJ Security Technology Sdn Bhd	MY	Kuala Lumpur	1-31-1, Menara Bangkok Bank | Berjaya Central Park, Menara Bangkok Bank, Jln Ampang, City Centre, 50450 Kuala Lumpur, Wilayah Persekutuan Kuala Lumpur	manufacturing	contractor	active	2025-06-30 06:36:50.683932	2025-07-29 16:10:05.160632		f	2	[3]	t	f
28	25F30023	FMTCS SOLUTIONS PTE. LTD	SG	Singapore	18 Boon Lay Way, #03-117 Tradehub 21, Singapore 609966   Tel No: (65) 65681543	other	dealer	active	2025-06-30 07:52:55.698312	2025-07-11 16:05:30.153078		f	2	[3]	t	f
24	25F30019	Jurutera Perunding Gen Sdn. Bhd.	MY	Kuala Lumpur	Taman Cheras, 24-4-1 & 26-4-2, Jalan 2/101c, Cheras Business Centre, 56100 Kuala Lumpur	other	designer	active	2025-06-30 07:25:29.787654	2025-07-08 10:01:30.647771		f	3	[2, 4, 5]	t	f
7	25F30002	Strato Solutions Sdn Bhd	MY	Selangor	C-09-06, Sunway Nexis, Kota Damansara, 47810 Petaling Jaya, Selangor	energy	integrator	active	2025-06-30 03:23:36.761819	2025-07-18 09:42:26.329867		f	2	[]	t	f
20	25F30015	Digital Two Way Communications Sdn Bhd	MY	Sarawak	No.139A 1st Floor, Jalan Rock, 93200 Kuching, Sarawak.	other	integrator	active	2025-06-30 06:46:34.999153	2025-07-11 17:22:29.771241		f	2	[3]	t	f
30	25F30025	Sunway Engineering Sdn. Bhd.	MY	Selangor	Level 9, Menara Sunway, Jalan Lagoon Timur, Bandar Sunway, 47500 Subang Jaya, Selangor	real_estate	contractor	active	2025-06-30 08:44:54.952054	2025-07-08 09:51:15.456573		f	3	[2, 4, 5]	t	f
21	25F30016	Comintel Sdn Bhd	MY	Selangor	22, Jalan Nilam 2, Taman Perindustrian Teknologi Tinggi, 47500 Subang Jaya, Selangor	transport	contractor	active	2025-06-30 06:54:10.056536	2025-07-29 15:32:40.579115		f	2	[3]	t	f
42	25G16003	Triple Access Sdn Bhd	MY	Selangor	A-03-16, Kompleks Perindustrian EmHub, Seksyen 3, Persiaran Surian, Taman Sains Selangor, 47810 Petaling Jaya, Selangor	other	dealer	active	2025-07-16 16:38:28.602616	2025-07-16 17:05:18.378284		f	2	[]	t	f
49	25G22006	NextDC Sdn. Bhd.	MY	Selangor	Axis Technology Centre, Level 5, Jalan 51a/225, Seksyen 51a, 46100 Petaling Jaya, Selangor	datacenter	user	active	2025-07-22 22:44:43.466513	2025-07-22 22:44:43.480828		f	3	[2, 4, 5]	t	f
52	25G29003	DcD Technology Sdn Bhd 	MY	Selangor	 Level 3, CJ11, Jalan Impact, Cyberjaya, 63000 Cyberjaya, Selangor	datacenter	contractor	active	2025-07-29 15:48:09.928998	2025-07-29 15:59:37.957623		f	2	[]	t	f
44	25G22001	GDS IDC SERVICES III (MALAYSIA) SDN BHD	MY	Johor	Unit 20-01 Teega Tower No 1 Jalan Laksamana Puteri Harbour Iskandar Puteri, Johor, 79250 Malaysia.	datacenter	user	active	2025-07-22 10:43:28.61806	2025-07-22 10:43:28.635674		f	3	[2, 4]	t	f
26	25F30021	B-Global Tech	MY	Kuala Lumpur	Level 19, Boutique Office (B01-C), Menara 2, Jalan Bangsar, 59200 Kuala Lumpur	other	designer	active	2025-06-30 07:37:08.12148	2025-08-01 13:10:45.057373		f	3	[2, 4, 5]	t	f
50	25G29001	Supreme Landmobile & Wireless Corporation Sdn. Bhd. (SLW)	MY	Selangor	No 2. Jalan Salung 33/26, Shah Alam Technology Park, Section 33, 40400 Shah Alam, Selangor Darul Ehsan, Malaysia	other	integrator	active	2025-07-29 15:12:50.816036	2025-07-29 15:24:06.38515		f	2	[8, 7]	t	t
43	25G16004	Vertex Communication Sdn Bhd	MY	Kuala Lumpur	G-0-6, Pusat Perdagangan Kuchai,, No. 2, Jalan 1/127, Off Jalan Kuchai Lama,, 58200 Kuala Lumpur, Wilayah Persekutuan Kuala Lumpur	other	integrator	active	2025-07-16 16:43:41.112862	2025-07-16 16:47:52.01355		f	2	[8, 7]	t	t
35	25G09004	YSC Technology Engineering Sdn. Bhd.	MY	Johor	B1-2404 Starview bay Property Management Service Centre, Teluk Bintang, Jalan Forest City 5, Pulau Satu, 81550 Gelang Patah, Johor	other	integrator	inactive	2025-07-09 07:26:57.517255	2025-07-16 15:39:36.466209		t	3	[2, 3, 4, 5, 9, 10, 11, 12]	t	t
71	25H12002	PT. CITRADATA INDONUSA	ID	Jakarta	Taman Pegangsaan Indah Blok T/No. 26 Jl. Pegangsaan Dua, Kelapa Gading Jakarta 14250	other	dealer	active	2025-08-12 12:29:07.445738	2025-08-15 09:48:23.550048		f	1	[2, 3, 4, 5, 8, 9, 10, 11]	t	t
47	25G22004	Longmotive (M) Sdn. Bhd.	MY	Johor	No. 9, Jalan Teknologi Perintis 1/2, Taman Teknologi Nusajaya, 79250 Iskandar Puteri, Johor.	datacenter	integrator	active	2025-07-22 15:42:11.601047	2025-07-22 15:42:11.615391		f	3	[2, 4, 12, 5]	t	t
46	25G22003	GDS Data Center @ Thailand	TH	Chonburi	Amata City Chonburi Industrial Park	datacenter	user	active	2025-07-22 15:26:18.403245	2025-07-22 15:26:18.419088		f	3	[2, 4, 12, 5]	t	t
45	25G22002	EPG Engineering System Sdn. Bhd.	MY	Kuala Lumpur	Level 41, Vista Tower,The Intermark,348 Jalan Tun Razak,50400, Kuala Lumpur, Malaysia	datacenter	integrator	active	2025-07-22 11:03:45.879688	2025-07-22 11:04:37.266505		f	3	[2, 3, 4, 5, 9, 10, 11, 12]	t	t
39	25G10004	China Construction Yangtze River (Malaysia) Sdn. Bhd. (Subsidiary of CSCEC)	MY	Kuala Lumpur	Level 1, Suite 1-5, Vertical Corporate Tower B, Avenue 10, Bangsar South, Kuala Lumpur	other	contractor	active	2025-07-10 02:30:58.317204	2025-07-10 10:30:58.332784		f	3	[2, 3, 4, 5, 9, 10, 11, 12]	t	t
12	25F30007	YSC TECHNOLOGY ENGINEERING Sdn Bhd	MY	Johor	B1-2404 Starview bay Property Management Service Centre, Teluk Bintang, Jalan Forest City 5, Pulau Satu, 81550 Gelang Patah, Johor Darul Takzim,Malaysia	other	integrator	active	2025-06-30 06:12:43.490939	2025-08-11 10:55:33.416846		f	2	[2, 3, 4, 5, 9, 10, 11, 12]	t	t
53	25H04001	Timesfly Engineering Services 时代飞扬	CN	Beijing	北京市朝阳区霄云路甲26号海航大厦10层	datacenter	integrator	active	2025-08-04 16:25:47.493076	2025-08-04 16:45:28.670292		f	3	[2, 3, 4, 5, 9, 10, 11, 12]	t	t
70	25H12001	Duriane Professionals Sdn Bhd	MY	Selangor	26-1 & 26-3, Jalan Puteri 2/4, Bandar Puteri, 47100 Puchong, Selangor	datacenter	designer	active	2025-08-12 11:20:52.625367	2025-08-12 11:35:47.867667		f	3	[]	t	f
55	25H06001	Mot Smart Solutions Company Limited (Head office)	TH	Bangkok	39/14 NAWONGPRACHAPATTANA ROAD  SIKUN SUBDISTRICT, KHET DONMUEANG BANGKOK. 10210	other	dealer	active	2025-08-06 09:37:25.976557	2025-08-06 09:38:29.538311		f	2	[2, 4, 5, 8, 10, 11]	t	t
72	25H12003	COMMUTRONICS ENTERPRISE CO., LTD	CN	Shanghai	台北市复兴南路二段237号10楼-6室,1 0F.-6, No. 237, Sec. 2, Fuxing S.Rd.,  Daan Dist., Taipei City 10667, Taiwan	other	dealer	active	2025-08-12 13:02:01.778949	2025-08-12 13:04:49.882041		f	1	[4, 5, 8, 10, 11]	t	t
73	25H12004	C.A. Sheimer (HK) Ltd	CN	Hong Kong Special Administrative Region	Hop Hing Industrial Building, Cheung Sha Wan, Hong Kong	government	dealer	active	2025-08-12 13:10:38.731391	2025-08-12 13:11:56.000465		f	1	[4, 5, 8, 10, 11, 12]	t	t
69	25H11001	Bandway Engineering (M) Sdn Bhd	MY	Kuala Lumpur	D-1-3, MEGAN AVENUE 1 NO, 189, 50400 Kuala Lumpur	other	dealer	active	2025-08-11 13:16:15.694493	2025-08-11 13:32:37.029543		f	2	[1, 3, 4, 5, 9, 10, 11, 12]	t	t
54	25H05001	O'Connor's Engineering Sdn Bhd	MY	Selangor	Bangunan O'Connor, 13, Jalan 51a/223, Seksyen 51a, 46100 Petaling Jaya, Selangor	other	integrator	active	2025-08-05 17:42:29.535306	2025-08-12 13:59:26.184804		f	2	[8, 7]	t	t
\.


--
-- TOC entry 4765 (class 0 OID 24053)
-- Dependencies: 291
-- Data for Name: company_assets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.company_assets (id, asset_type, asset_name, asset_key, file_name, file_type, file_size, file_content, description, is_active, is_default, created_at, updated_at, created_by_id) FROM stdin;
\.


--
-- TOC entry 4767 (class 0 OID 24059)
-- Dependencies: 293
-- Data for Name: contacts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contacts (id, company_id, name, department, "position", phone, email, is_primary, created_at, updated_at, notes, owner_id, override_share, shared_disabled) FROM stdin;
4	7	Muhammad Ihsan	Project	Telco Engineer 	019-720 0787	ihsan.malek@stratosolutions.com.my	f	2025-06-30 03:28:12.111138	2025-06-30 03:28:12.111145		2	f	f
5	22	Ir. Ong	Project Management	Electrical Engineer	6012-4211840		f	2025-06-30 07:02:50.844825	2025-06-30 07:02:50.844831	Electrical engineer handle for northern Malaysia projects and told the Open Data Centre @ Bukit Kayu, Kedah there the construstion will complete end of this year but only ICT in design with not specify for two-way radio system. Recommend to meet with his colleague Ms. Atiqah to check the design details.	3	f	f
6	22	Ferdinand Ngan	Project Management	Senior Electrical Engineer	6014-3274914	ferdinand@meg.com.my	f	2025-06-30 07:11:45.42346	2025-06-30 07:11:45.423464	Courtesy visit and highlight the importancy of type approval for radio equipment to Yondr Data Centre as we follow up with Sunway Engineering. And checked the Shanghai DC Science Data Centre @ Sedenak Tech Park progress and told end-user not request for RF design and his ELV design part only provide the network & backbone cabling layout for sufficient single mode fiber optic coverage points to ICT & surveillance system.	3	f	f
7	23	Lim Zen Yang	Procurement & Contracts	Senior Contract Executive	603-89987666		f	2025-06-30 07:23:04.564192	2025-06-30 07:23:04.564196	Courtesy visit to present our RFoF DAS and checked their project status to Exsim Data Centre @ Bukit Jalil. Told that total 2 phases to this project and phase 1 structural almost complete and estimate completion end of year 2025. Phase 2 waiting for owner Exsim's greenlight ro proceed due to their anchor tenant cancelled the contract. Told not notice this two-way radio or DAS system in their contract and we can follow up with their subcon DCD Technology to check any inquiry to the system.	3	f	f
8	24	Kong Choong Chien	Project management	General Manager	6016-7523519		f	2025-06-30 07:28:01.014118	2025-06-30 07:28:01.014123	Courtesy visit and checked the INV Lithium Battery plant and told this overall design from China. Building structural design and lithium battery processing equipment same as enduser China plant. His roles only submission consultant and without RF in design and told RF system will not under CCYR package that enduser will appoint existing China contractors for their processing & plant operation system. Highlighted the RF equipment type approval to Kong.	3	f	f
9	25	William Khor	Sales		Sales Manager		f	2025-06-30 07:31:00.281676	2025-06-30 07:31:00.28168		3	f	f
10	25	Selvarajah	Project management	Project Engineer	6017-633 8583		f	2025-06-30 07:34:37.285799	2025-06-30 07:34:37.285804		3	f	f
11	26	Nur Liyana Idzreen	Technical Department	Electrical Engineer	6016-844 4915	nliyana@b-global.tech	f	2025-06-30 07:40:01.48381	2025-06-30 07:40:01.483816	Courtesy visit to present RFoF DAS system and checked their projects status. Told that B-Global was DC specialist for project management and design consultant and KL team handle YTL DC phase 1 for 80 MW DC & total projects will separate to 6 phase. Told RF design probably under security consultant Trac Consult due to they are new team in Malaysia and interested to work with us if their top management want to include security design for YTL phase 2. Told another Yondr DC handle by Johor team and will check with the PIC and update me later.	3	f	f
12	26	Farah Anuar	Technical Department	BIM Specialist	6012-258 6246	farah@b-global.tech	f	2025-06-30 07:41:59.428101	2025-06-30 07:41:59.428106		3	f	f
16	27	John Goh	Project management	Business Development Director	6016-9170128	johngohks@gmail.com	f	2025-06-30 08:36:08.539486	2025-06-30 08:36:08.539491	Visited this M&E contractor company to check their projects status and told Hospital Sabah & Sarawak extension works already completed and recently only some apartment projects. Recommend his ELV manager Mr. Chu and told they will use Hikvision or project listed brand for CCTV and two-way radio will sub to other contractor.	3	f	f
17	27	JW Chu	Project management	Project Manager	6014-265 4615		f	2025-06-30 08:39:26.534009	2025-06-30 08:39:26.534014	Follow up the NextDC and check any RF inquiry from their new projects. Told recently running few residential projects which no RF inquiry in design and the NextDC only secured the electrical, ELV & ICT cable trunking & tray package. RF will park under surveillance security package and recommend to contact SKA Tech & project manger name Mr. Selvarajah.  	3	f	f
18	29	Ellen Wong	Project management	Senior Project Manager	6019-257 1319	ellen.wong@mitrajaya.com.my	f	2025-06-30 08:43:39.894953	2025-06-30 08:43:39.894959	Courtesy visit to check NextDC status and told they succeed as a maincon for phase 1 but their package only building infra and C&S. HVAC package under Progress Centre Eng & Electrical & ELV package will award to MCC Technique. Plan for Phase 2 to P4 to offer all M&E into thier packages. Interested to our RFoF DAS System due to no resource and support to RF and future will call us for design support once project receive RF inquiry.	3	f	f
20	30	Yap Siew Ling	Procurement & Contracts	Senior Manager	6012-384 7671	yapsl@sunway.com.my	f	2025-06-30 08:52:47.547975	2025-06-30 08:52:47.547981		3	f	f
21	30	Chong Yih Lip	Procurement & Contracts	Procurement Manager	6016-552 0686	chongyl@sunway.com.my	f	2025-06-30 08:54:49.587314	2025-06-30 08:54:49.58732		3	f	f
22	31	Fairs	Project		03 - 9202 0479		f	2025-07-01 01:40:25.305947	2025-07-01 01:40:25.305953		2	f	f
23	14	How 	Project	Director	012-676 7699		f	2025-07-01 01:54:53.570313	2025-07-01 01:54:53.570317		2	f	f
24	14	Chong	Project	Director	016-773 8922		f	2025-07-01 01:55:30.085758	2025-07-01 01:55:30.085764		2	f	f
25	16	Cindy 					f	2025-07-01 02:40:11.081949	2025-07-01 02:40:11.081956		2	f	f
26	30	Tan Chao Zhi	Procurement & Contracts	Project Engineer	6011-1192 0059	tancz@sunway.com.my	f	2025-07-08 01:42:23.422793	2025-07-08 01:42:23.4228		3	f	f
27	12	邹先生		Director	+86 13138861119		f	2025-07-09 01:32:17.690473	2025-07-09 01:32:17.690479		2	f	f
28	32	胡桂霞	Project Technical Team				f	2025-07-09 07:00:31.171532	2025-07-09 07:00:31.171537	Communication through Wechat & her Wechat ID: yunxiaoduan776655	3	f	f
29	33	Wong Liang Jun	Project Management	Electrical Engineer	6018-908 9098	ljwong@dynast.com.my	f	2025-07-09 07:14:09.644782	2025-07-09 07:14:09.644789		3	f	f
30	34	Bruce Wang	Project Management		6010-701 6907		f	2025-07-09 07:21:47.342934	2025-07-09 07:21:47.342941	Maincon & PIC for Bridge Data Centre MY02.	3	f	f
32	37	Ahmad Azri	Project Management	Project Manager	6019-613 6775	ahmad.azri@trac-consulting.co	f	2025-07-10 01:47:21.117029	2025-07-10 01:47:21.117034		3	f	f
33	28	付总		Director			f	2025-07-11 08:05:30.137919	2025-07-11 08:05:30.137923		2	f	f
35	20	Doreen	Sale			dtsy80.digitaltwc7980@gmail.com	f	2025-07-11 08:09:32.819672	2025-07-11 08:09:32.819678		2	f	f
36	19	Azura	Sale	Manager	012-212 9919	info@acesonic.com.my	f	2025-07-11 09:25:19.701491	2025-07-11 09:25:19.701494		2	f	f
37	18	Jet Chin	Project	Manager	0358806363	jet@uniquearena.com.my	f	2025-07-11 09:28:08.962334	2025-07-11 09:28:08.962339		2	f	f
38	17	Zulhilmi 	Procurement	Senior Procurement 	018-3976886	zulhilmi@engenious.com.my	f	2025-07-11 09:31:12.832774	2025-07-11 09:31:12.832782		2	f	f
39	15	Ir. Teo Chuun Ben	Project	M&E Coordinator	017 305 3210	mcsmsb.hq@gmail.com	f	2025-07-11 09:33:46.095505	2025-07-11 09:33:46.095509		2	f	f
40	13	Kim	Sale	Manager	012 296 8335		f	2025-07-11 09:35:40.783396	2025-07-11 09:35:40.7834		2	f	f
41	13	Suhaimi	Engineering		012 369 2238		f	2025-07-11 09:37:05.780283	2025-07-11 09:37:05.780287		2	f	f
42	11	Nurhamin	System Department	System Engineer	0129505773	nurhanim@axis-tek.com	f	2025-07-11 09:49:05.03595	2025-07-11 09:49:05.035954		2	f	f
43	11	Nor Wahidah Misran	System Department	Manager	019 213 3524	wahidah.misran@axis-tek.com	f	2025-07-11 09:50:04.483585	2025-07-11 09:50:04.483589		2	f	f
44	11	Shiqeen	System Department	System Engineer		shiqeen@axis-tek.com	f	2025-07-11 09:50:44.77589	2025-07-11 09:50:44.775896		2	f	f
45	10	Chung	Engineering	Senior Engineer	0 12-500 7742		f	2025-07-11 09:52:27.388591	2025-07-11 09:52:27.388598		2	f	f
46	9	Zakaria Dahili	Project	Founder	019 334 9271	zak@tacticom.com.my	f	2025-07-11 09:56:12.18193	2025-07-11 09:56:12.181935		2	f	f
47	9	Puteri Maryam	Project	Chief Executive Officer	019 383 9271	maryam@tactical.com.my	f	2025-07-11 09:57:22.626188	2025-07-11 09:57:22.626193		2	f	f
48	8	Hanini Mohd Zaki	Business Development 	Business Development Enginee	0 17200 8303	hanini.zaki@synergyengineering.com	f	2025-07-11 09:59:19.349251	2025-07-11 09:59:19.349255		2	f	f
49	6	Nur Jahidah	Sale	Manager	0 17-314 5646		f	2025-07-11 10:00:28.841674	2025-07-11 10:00:28.841678		2	f	f
50	8	Alyaa		Engineer 	011 1057 302	alyaa.najihah@synergyengineering.com	f	2025-07-14 10:29:32.02487	2025-07-14 10:29:32.024888		2	f	f
51	40	Lai	Project		019 380 9008		f	2025-07-16 15:06:24.826861	2025-07-16 15:06:24.826868		2	f	f
52	41	Amelia	Project	Manager	011 5959 3513		f	2025-07-16 15:23:54.037815	2025-07-16 15:23:54.037822		2	f	f
54	42	Yusry		Presale	018 902 3933	yusrylee@tripleaccess.com.my	f	2025-07-16 16:41:27.304949	2025-07-16 16:41:27.304956		2	f	f
55	43	Matthew			03-7980 0910		f	2025-07-16 16:44:23.19205	2025-07-16 16:44:23.192057		2	f	f
56	45	Mr. Yang	Project Management	Project Engineer	017-7475827		f	2025-07-22 11:04:37.253531	2025-07-22 11:04:37.253537		3	f	f
57	21	Yogasingam Vallipuram	Project	Senior Manager Sales & Marketing	012 277 8010	yoga@comintel.com.my	f	2025-07-22 17:36:08.8975	2025-07-22 17:36:08.897509		2	f	f
58	21	Muhammad Mussaddiq Bin Samsudin	System 	Senior System Engineer	016 673 6795	musaddiq@comintel.com.my	f	2025-07-22 17:37:38.466092	2025-07-22 17:37:38.466098		2	f	f
59	21	Lee Hoong Fatt	Service	Director	017 363 5988	leehf@comintel.com.my	f	2025-07-22 17:39:02.20917	2025-07-22 17:39:02.209177		2	f	f
60	48	Nadason	Engineering	Manager	014 373 0559	nadason@wnwless.com	f	2025-07-22 17:49:22.473863	2025-07-22 17:49:22.473871		2	f	f
62	50	Andrew		Director	019 375 1495		f	2025-07-29 15:15:35.467535	2025-07-29 15:15:35.467542		2	f	f
63	50	Yeo SJ		Sale Manager	016 211 3178		f	2025-07-29 15:17:43.847582	2025-07-29 15:17:43.847588		2	f	f
64	50	Norman Anslem		Sale Engineer	012 295 1925	norman@slwholdings.com.my	f	2025-07-29 15:18:40.924562	2025-07-29 15:18:40.924569		2	f	f
65	51	Lina Khalida Binti Azhar	Operation	Executive	019 380 3180	linakhalida.azhar@bridgedatacentres.com	f	2025-07-29 15:37:21.161514	2025-07-29 15:37:21.161519		2	f	f
66	52	Irwin Hon		Director		irwin_hon@dcdtech.com.my	f	2025-07-29 15:49:01.64069	2025-07-29 15:49:01.640695		2	f	f
67	53	韩丹丹	Project Management				f	2025-08-04 16:27:57.373424	2025-08-04 16:27:57.37343	Wechat ID: h468683	3	f	f
68	54	Khey Heng Soon	Sale	Sale Manager	012 268 4562	kheyhs@oconnors.com.my	f	2025-08-05 17:44:14.203738	2025-08-05 17:44:14.203745		2	f	f
69	54	Woo Siew Wai	Radio Communication	Business Consultant	019 222 6148	woosw@oce.com.my	f	2025-08-05 17:45:39.367908	2025-08-05 17:45:39.367914		2	f	f
73	60	Tan Wee Meng	Sales	Sales Manager	+60163361822	wmtan@radii.com.my	f	2025-08-07 15:03:25.817636	2025-08-07 15:05:04.512788		7	f	f
74	60	Tan Siew Chen	Sales	Channel Sales Assistant Manager	+60163321372	sctan@radii.com.my	t	2025-08-07 15:05:04.48465	2025-08-07 15:05:04.514379		7	f	f
75	61	Yeoh Por Sie	Technical	Technical Support Engineer	+60162913201	porsie@sp-infocomm.com	f	2025-08-07 15:12:51.071629	2025-08-07 15:12:51.071635		7	f	f
76	61	SP Yeoh	Sales	General Manager	+60122913201	spyeoh@sp-infocomm.com	f	2025-08-07 15:13:51.980441	2025-08-07 15:13:51.980446		7	f	f
78	62	Owen Lam	Sales	Business Development Manager	+60122194128	sales02@oissb.com.my	f	2025-08-07 15:25:08.622498	2025-08-07 15:25:08.622506		7	f	f
79	63	Mohd Asri Bin Bakar	Security	Head of Department	+60176548469	mohd.asri@ioigroup.com	f	2025-08-07 15:28:45.213894	2025-08-07 15:28:45.2139		7	f	f
80	63	Richard Chu	Procurement	Executive	+60123718292	skchu@ioigroup.com	f	2025-08-07 15:29:32.808614	2025-08-07 15:29:32.808622		7	f	f
81	63	Mohammad Riduan Bin Mat Ali	Security	Inspector	+60133886312	Mohd.riduan@ioigroup.com	f	2025-08-07 15:30:15.336805	2025-08-07 15:30:15.336812		7	f	f
82	64	Au Yong Wai Yee	Building Service	Building Service Manager	+60102816052	waiyee.auyong@airtrunk.com	t	2025-08-07 15:44:45.61397	2025-08-07 15:44:45.645039		7	f	f
83	65	Zanirul Akhmal Bin Zanirun 	Security Defense, Security, Aviation & Maritime	Account Manager	013 394 0011	zanirul@tm.com.my	f	2025-08-07 16:58:51.397014	2025-08-07 16:58:51.397019		2	f	f
31	12	Mr. 邹	Project Management		6017-915 2868		f	2025-07-09 07:28:50.837726	2025-08-11 10:55:33.395884		3	f	f
53	12	李工	Project				f	2025-07-16 15:33:49.415495	2025-08-11 10:55:33.395891		2	f	f
84	69	Chua Lee Lee		Senior Quantity Surveyor	012 945 4870	chualily26@gmail.com	f	2025-08-11 13:32:37.003819	2025-08-11 13:32:37.003826		2	f	f
85	37	Reena Chow	Project Procurement & Design	Senior Design Manager	6012-505 3713	reena.chow@trac-consulting.com	f	2025-08-12 11:16:39.664723	2025-08-12 11:16:39.664731		3	f	f
86	70	Ms. Mimi Afifah	Project Management	Senior Electrical Engineer	6010-575 9740	mimi@duriane.com	f	2025-08-12 11:22:48.942248	2025-08-12 11:22:48.942254		3	f	f
87	71	Gama Waney		Director			t	2025-08-12 12:31:23.661658	2025-08-12 12:31:23.710151		1	f	f
88	71	Mario Lukman			+62 811 195 638	mario_lukman@citradata.id	f	2025-08-12 12:33:04.469971	2025-08-12 12:33:04.469977		1	f	f
89	72	Nelson.曾国栋			+886227013743	nelson.tseng@commutronics.com.tw	f	2025-08-12 13:04:49.856726	2025-08-12 13:04:49.856732		1	f	f
90	73	Michael Ho		Sales Director	(852) 6343-3799	mho@casheimer.com.hk	f	2025-08-12 13:11:55.969563	2025-08-12 13:11:55.969568		1	f	f
91	54	Johnson		Engineer	016 684 0553		f	2025-08-12 13:45:04.675969	2025-08-12 13:45:04.675976		2	f	f
92	65	Mohd Zaimi 			013 388 1091		f	2025-08-12 15:39:30.841558	2025-08-12 15:39:30.841565		2	f	f
70	55	Surasak J. (Paul)	Project	International Project Manager	+66 (0) 86 460-0454	surasak.j@mot.co.th	f	2025-08-06 09:38:29.521504	2025-08-12 17:44:47.427545	Had share our general presentation slide and sale training slide with Mr. Surask for their in-house training. \r\nBeside requesting the NBTC guidelines what is the frequency allow use in Thailand and procedure / fee to apply it, pending the information from him now. 	2	f	f
93	71	Adrian Bany Kansil		Vice Director	0628111774415	adrian@citradata.id	f	2025-08-15 09:48:23.520572	2025-08-15 09:48:23.520578		1	f	f
\.


--
-- TOC entry 4884 (class 0 OID 26535)
-- Dependencies: 410
-- Data for Name: data_field_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.data_field_config (id, table_config_id, field_name, display_name, description, data_type, is_nullable, is_primary_key, is_foreign_key, foreign_table, foreign_field, is_numeric, is_monetary, is_date, is_aggregatable, is_filterable, is_performance_metric, performance_category, calculation_priority, display_format, default_unit, decimal_places, sample_values, value_range, created_at, updated_at, created_by, updated_by) FROM stdin;
1	1	amount	报价金额	报价单的总金额	decimal	\N	\N	\N	\N	\N	t	t	\N	t	\N	t	sales	\N	\N	元	\N	\N	\N	\N	\N	\N	\N
2	1	implant_total_amount	植入总金额	植入项目的总金额	decimal	\N	\N	\N	\N	\N	t	t	\N	t	\N	t	sales	\N	\N	元	\N	\N	\N	\N	\N	\N	\N
3	1	created_at	创建时间	报价单创建时间	timestamp	\N	\N	\N	\N	\N	\N	\N	t	\N	t	t	general	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
4	1	approval_status	审批状态	报价单的审批状态	varchar	\N	\N	\N	\N	\N	\N	\N	\N	\N	t	t	quality	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
5	4	id	客户ID	客户公司的唯一标识	integer	\N	\N	\N	\N	\N	\N	\N	\N	t	\N	t	customer	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
6	4	created_at	创建时间	客户公司创建时间	timestamp	\N	\N	\N	\N	\N	\N	\N	t	\N	t	t	customer	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
\.


--
-- TOC entry 4878 (class 0 OID 26477)
-- Dependencies: 404
-- Data for Name: data_table_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.data_table_config (id, table_name, display_name, description, category, is_active, is_performance_source, total_records, last_updated, created_at, updated_at, created_by, updated_by) FROM stdin;
1	quotations	报价单	项目报价单信息，包含金额和审批状态	business	t	t	\N	\N	\N	\N	\N	\N
2	pricing_orders	批价单	批价订单信息，包含批价金额和结算金额	business	t	t	\N	\N	\N	\N	\N	\N
3	projects	项目	项目基础信息，包含项目类型和阶段	business	t	t	\N	\N	\N	\N	\N	\N
4	companies	公司客户	客户公司信息，包含行业和地区	business	t	t	\N	\N	\N	\N	\N	\N
5	contacts	联系人	客户联系人信息	business	t	t	\N	\N	\N	\N	\N	\N
6	products	产品	产品信息	reference	t	t	\N	\N	\N	\N	\N	\N
7	users	用户	系统用户信息	system	t	f	\N	\N	\N	\N	\N	\N
8	expenses	费用	费用记录	business	t	t	\N	\N	\N	\N	\N	\N
9	settlements	结算	结算信息	business	t	t	\N	\N	\N	\N	\N	\N
\.


--
-- TOC entry 4769 (class 0 OID 24065)
-- Dependencies: 295
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.departments (id, name, code, parent_id, manager_id, is_active, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4771 (class 0 OID 24069)
-- Dependencies: 297
-- Data for Name: dev_product_specs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dev_product_specs (id, dev_product_id, field_name, field_value, field_code) FROM stdin;
\.


--
-- TOC entry 4773 (class 0 OID 24073)
-- Dependencies: 299
-- Data for Name: dev_products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dev_products (id, category_id, subcategory_id, region_id, name, model, status, unit, retail_price, description, image_path, created_at, updated_at, owner_id, created_by, mn_code, pdf_path, currency) FROM stdin;
\.


--
-- TOC entry 4775 (class 0 OID 24080)
-- Dependencies: 301
-- Data for Name: dictionaries; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dictionaries (id, type, key, value, is_active, sort_order, created_at, updated_at, is_vendor, email_signature_content, website, postal_code, logo_filename, email, email_signature_type, email_signature_size, address, logo_content, email_signature_filename, logo_size, phone, fax, logo_type) FROM stdin;
1	company	evertacsolutions_ company	evertacsolutions	t	10	1750593860.4367523	1750593860.4367568	t	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
2	role	admin	system_admin	t	10	1750593904.8159275	1750593904.8159285	f	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
3	role	sales_manager	sales_manager	t	20	1750593933.0504632	1750593933.0504649	f	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
4	role	business_admin	business_admin	t	30	1750593952.4229052	1750593952.4229064	f	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
5	department	sales_dep	sales_dep	t	10	1750593978.0146508	1750593978.014652	f	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
6	currency	USD	美元	t	10	1750595738.561086	1750595738.561086	f	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
7	company	triple_access	Triple Access	t	20	1754462303.8433397	1754462303.8433409	f	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
8	company	TCE_company	Technics Communication & Electronics Pte Ltd	t	30	1754462348.7911747	1754462348.791176	f	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
9	role	solution_manager	solutions_manager	t	40	1754877146.4656339	1754877146.4656346	f	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
10	role	product_manager	product_manager	t	50	1754877165.784533	1754877165.7845345	f	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
11	company	fmtcs_company	FMTCS SOLUTIONS PTE. LTD	t	40	1754877649.5168748	1754877649.5168757	f	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N
\.


--
-- TOC entry 4777 (class 0 OID 24087)
-- Dependencies: 303
-- Data for Name: event_registry; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_registry (id, event_key, label_zh, label_en, default_enabled, enabled, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4779 (class 0 OID 24091)
-- Dependencies: 305
-- Data for Name: expense_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.expense_details (id, expense_id, expense_date, expense_category, description, document_count, amount, status, created_at, updated_at, invoice_images, currency, invoice_amount, current_amount, exchange_rate) FROM stdin;
42	3	2025-08-08	entertainment	11	2	143.8	draft	2025-08-08 18:17:36.183264	2025-08-08 18:17:36.183268	\N	USD	20.00	143.80	7.1900
1	1	2025-08-06	travel_accommodation	flight to Johor	1	250	draft	2025-08-06 14:48:03.222302	2025-08-06 14:48:04.265002	[{"filename": "Screenshot 2025-08-04 at 00.11.01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/expense_invoices/1/expense_invoice_1_05d9477e.png", "size": 70592}]	MYR	250.00	250.00	1.0000
45	6	2025-07-28	travel_accommodation	Round-trip air ticket between Singapore and Bangkok	2	414.56	draft	2025-08-12 11:57:56.626628	2025-08-12 11:57:57.385065	[{"filename": "PMA-SA_BX2025081201_01_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_01_01.heic", "size": 200412}, {"filename": "PMA-SA_BX2025081201_01_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_01_02.heic", "size": 202910}]	CNY	2316.00	414.56	0.1790
35	2	2025-08-06	local_transport	office to  airport	1	30.7	draft	2025-08-08 18:13:32.640802	2025-08-08 19:39:21.962351	[{"filename": "tempImageDKNEZ4.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/expense_invoices/35/expense_invoice_35_830963c4.heic", "size": 47977}]	CNY	30.70	30.70	1.0000
36	2	2025-08-06	local_transport	airport to hotel	1	24.17	draft	2025-08-08 18:13:32.644487	2025-08-08 19:39:21.962352	[{"filename": "tempImageB7v9h6.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/expense_invoices/36/expense_invoice_36_f5a54ff8.heic", "size": 119857}]	MYR	79.65	24.17	0.3035
37	2	2025-08-08	entertainment	team building dinner	2	119.1	draft	2025-08-08 18:13:32.648202	2025-08-08 19:39:21.962354	[{"filename": "IMG_8639.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/expense_invoices/37/expense_invoice_37_7ad22409.heic", "size": 811524}, {"filename": "IMG_8638.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/expense_invoices/37/expense_invoice_37_2cdfc71c.heic", "size": 612614}]	MYR	397.00	119.10	0.3000
38	2	2025-08-08	local_transport	airport to home	1	29.3	draft	2025-08-08 18:13:32.652096	2025-08-08 19:39:21.966848	[{"filename": "tempImageJn0Erc.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/expense_invoices/38/expense_invoice_38_91e4b11a.heic", "size": 50717}]	CNY	29.30	29.30	1.0000
39	2	2025-08-08	local_transport	office to airport	1	24.57	draft	2025-08-08 18:13:32.655916	2025-08-08 19:39:21.966851	[{"filename": "tempImage86qL1W.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/expense_invoices/15/expense_invoice_15_68530fe9.heic", "size": 37004}]	MYR	81.90	24.57	0.3000
43	3	2025-08-08	entertainment	1212	1	20	draft	2025-08-08 18:17:36.187366	2025-08-08 18:17:36.396378	[{"filename": "tempImageSuNZjs.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/expense_invoices/43/expense_invoice_43_25ee8c3b.heic", "size": 208221, "uploaded_at": "2025-08-08T10:17:36.393388"}]	CNY	20.00	20.00	1.0000
44	5	2025-08-08	entertainment	的	1	111	draft	2025-08-08 22:53:41.424744	2025-08-08 22:53:42.335153	[{"filename": "tempImageUJHpmF.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/expense_invoices/44/expense_invoice_44_4a0d68ed.heic", "size": 119857}]	USD	111.00	111.00	1.0000
50	7	2025-06-25	travel_accommodation	Hotel in Jakarta 2 night	1	194.04	draft	2025-08-12 12:51:35.347609	2025-08-12 12:51:35.523915	[{"filename": "PMA-SA_BX2025081202_02_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_02_01.heic", "size": 69013}]	CNY	1084.00	194.04	0.1790
46	6	2025-07-31	local_transport	Grab between Bangkok airport, client's office and hotel	3	58.4	draft	2025-08-12 11:57:57.387543	2025-08-12 11:57:57.839194	[{"filename": "PMA-SA_BX2025081201_02_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_02_01.heic", "size": 66061}, {"filename": "PMA-SA_BX2025081201_02_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_02_02.heic", "size": 62493}, {"filename": "PMA-SA_BX2025081201_02_03.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_02_03.heic", "size": 67751}]	THB	1460.00	58.40	0.0400
47	6	2025-08-12	local_transport	Grab between Singapore office to airport and back to home	2	54.1	draft	2025-08-12 11:57:57.84143	2025-08-12 11:57:58.109582	[{"filename": "PMA-SA_BX2025081201_03_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_03_01.heic", "size": 78220}, {"filename": "PMA-SA_BX2025081201_03_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_03_02.heic", "size": 78729}]	CNY	54.10	54.10	1.0000
48	6	2025-07-30	other	Gift for Mot surasak	1	58.72	draft	2025-08-12 11:57:58.111905	2025-08-12 11:57:58.372398	[{"filename": "PMA-SA_BX2025081201_04_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_04_01.heic", "size": 1049359}]	CNY	58.72	58.72	1.0000
34	2	2025-08-06	travel_accommodation	Flight to KL and Back to Singapore	2	211.76	draft	2025-08-08 18:13:32.63661	2025-08-12 12:16:09.828296	[{"filename": "PMA-SA_BX2025080801_01_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025080801/PMA-SA_BX2025080801_01_01.heic", "size": 140562, "uploaded_at": "2025-08-12T04:16:09.606326"}, {"filename": "PMA-SA_BX2025080801_01_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025080801/PMA-SA_BX2025080801_01_02.heic", "size": 228819, "uploaded_at": "2025-08-12T04:16:09.825561"}]	CNY	1183.00	211.76	0.1790
49	7	2025-06-25	travel_accommodation	Round trip between Jakarta and singapore	2	294.84	draft	2025-08-12 12:51:34.666083	2025-08-12 12:51:35.345155	[{"filename": "PMA-SA_BX2025081202_01_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_01_01.heic", "size": 215660}, {"filename": "PMA-SA_BX2025081202_01_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_01_02.heic", "size": 216023}]	CNY	1638.00	294.84	0.1800
51	7	2025-06-25	local_transport	grab in Jakarta hotel to pt citradata and airport	4	37.57	draft	2025-08-12 12:51:35.526254	2025-08-12 12:51:36.130346	[{"filename": "PMA-SA_BX2025081202_03_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_01.heic", "size": 70942}, {"filename": "PMA-SA_BX2025081202_03_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_02.heic", "size": 75150}, {"filename": "PMA-SA_BX2025081202_03_03.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_03.heic", "size": 75402}, {"filename": "PMA-SA_BX2025081202_03_04.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_04.heic", "size": 75018}]	IDR	474800.00	37.57	0.0001
52	7	2025-06-25	local_transport	grab office to airport and back to home	2	55.5	draft	2025-08-12 12:51:36.132765	2025-08-12 12:51:36.410043	[{"filename": "PMA-SA_BX2025081202_04_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_04_01.heic", "size": 77270}, {"filename": "PMA-SA_BX2025081202_04_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_04_02.heic", "size": 78051}]	CNY	55.50	55.50	1.0000
53	8	2025-08-12	entertainment	dinner for xu and his family	1	568.93	draft	2025-08-12 12:57:38.859894	2025-08-12 12:57:39.290384	[{"filename": "PMA-SA_BX2025081203_01_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081203/PMA-SA_BX2025081203_01_01.heic", "size": 1168148}]	CNY	568.93	568.93	1.0000
54	9	2025-08-12	travel_accommodation	hotel in Taibei 3 night	1	482.03999999999996	draft	2025-08-12 13:17:00.514231	2025-08-12 13:17:00.953175	[{"filename": "PMA-SA_BX2025081204_01_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081204/PMA-SA_BX2025081204_01_01.heic", "size": 136454}]	CNY	2678.00	482.04	0.1800
55	9	2025-08-12	travel_accommodation	trip air from HK to Taibei	1	221.94	draft	2025-08-12 13:17:00.956248	2025-08-12 13:17:01.15043	[{"filename": "PMA-SA_BX2025081204_02_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081204/PMA-SA_BX2025081204_02_01.heic", "size": 141151}]	CNY	1233.00	221.94	0.1800
56	10	2025-06-25	travel_accommodation	trip air singapore to HK	1	149.76	draft	2025-08-12 13:18:32.930493	2025-08-12 13:19:09.980207	[{"filename": "PMA-SA_BX2025081205_01_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081205/PMA-SA_BX2025081205_01_01.heic", "size": 252022, "uploaded_at": "2025-08-12T05:19:09.979024"}]	CNY	832.00	149.76	0.1800
57	11	2025-08-12	travel_accommodation	Trip flight to Jakarta and back singapore	0	193.14	draft	2025-08-15 09:56:50.505104	2025-08-15 09:56:50.50511	\N	CNY	1079.00	193.14	0.1790
58	11	2025-08-12	travel_accommodation	Hotel in Jakarta 2 nights	0	265.7304	draft	2025-08-15 09:56:50.519829	2025-08-15 09:56:50.519834	\N	CNY	1476.28	265.73	0.1800
59	11	2025-08-12	local_transport	Jakarta airport to hotel garb	0	18.18	draft	2025-08-15 09:56:50.531335	2025-08-15 09:56:50.531341	\N	IDR	181800.00	18.18	0.0001
60	11	2025-08-12	travel_accommodation	Changi airport to home	0	27.6	draft	2025-08-15 09:56:50.544434	2025-08-15 09:56:50.544441	\N	CNY	27.60	27.60	1.0000
61	11	2025-08-13	entertainment	dinner with Pt citradata	0	103.96000000000001	draft	2025-08-15 09:56:50.557154	2025-08-15 09:56:50.557161	\N	IDR	1039600.00	103.96	0.0001
\.


--
-- TOC entry 4781 (class 0 OID 24101)
-- Dependencies: 307
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.expenses (id, expense_number, title, description, customer_id, project_id, total_amount, status, is_locked, approved_by, approved_at, approval_notes, owner_id, created_at, updated_at, is_deleted, contact_id, currency, payment_status, payment_amount, payment_date, payment_method, payment_reference, payment_notes, paid_by) FROM stdin;
5	BX2025080803	测试非关联客-admin-2508082202	测试非关联客户	\N	\N	111	draft	f	\N	\N	\N	1	2025-08-08 22:53:41.42094	2025-08-08 22:54:01.484482	t	\N	USD	unpaid	\N	\N	\N	\N	\N	\N
1	BX2025080601	MCS Management Sdn Bhd-quah-2508060603		15	\N	250	paid	t	\N	\N	\N	2	2025-08-06 14:48:03.218555	2025-08-06 14:49:57.258183	f	39	MYR	paid	\N	2025-08-06 06:49:57.257434	\N	\N	\N	5
3	BX2025080802	TM Technology Service Sdn Bhd -admin-2508081047		65	\N	163.8	draft	f	\N	\N	\N	1	2025-08-08 18:16:47.173281	2025-08-08 19:40:09.126971	t	83	CNY	unpaid	\N	\N	\N	\N	\N	\N
2	BX2025080801	Triple Access Sdn Bhd-admin-2508080034	Training New staff Alesandro and visit customer	42	\N	439.6	pending	t	\N	\N	\N	1	2025-08-08 08:36:34.344676	2025-08-12 12:16:29.88339	f	54	SGD	unpaid	\N	\N	\N	\N	\N	\N
11	BX2025081501	PT. CITRADATA INDONUSA-admin-2508150150		71	\N	608.6104	draft	f	\N	\N	\N	1	2025-08-15 09:56:50.496393	2025-08-15 09:56:50.570602	f	87	SGD	unpaid	\N	\N	\N	\N	\N	\N
7	BX2025081202	PT. CITRADATA INDONUSA-admin-2508120434		71	\N	581.95	pending	t	\N	\N	\N	1	2025-08-12 12:51:34.661811	2025-08-12 12:52:06.885776	f	87	SGD	unpaid	\N	\N	\N	\N	\N	\N
6	BX2025081201	Mot Smart Solutions Company Limited (Head office)-admin-2508120356	First visit to the Thai partner MOT, conduct technical training on Evertac Solutions, discuss frequency application and certification matters in Thailand, and sign the MOT memorandum.	55	\N	585.78	pending	t	\N	\N	\N	1	2025-08-12 11:57:56.619171	2025-08-12 12:13:40.341757	f	70	SGD	unpaid	\N	\N	\N	\N	\N	\N
8	BX2025081203	china'-admin-2508121259	china's suppler xu and his family	\N	\N	568.93	pending	t	\N	\N	\N	1	2025-08-12 12:57:38.856494	2025-08-12 12:57:47.428752	f	\N	SGD	unpaid	\N	\N	\N	\N	\N	\N
9	BX2025081204	COMMUTRONICS ENTERPRISE CO., LTD-admin-2508120500		72	\N	703.98	draft	f	\N	\N	\N	1	2025-08-12 13:17:00.509173	2025-08-12 13:17:01.156103	f	89	SGD	unpaid	\N	\N	\N	\N	\N	\N
10	BX2025081205	C.A. Sheimer (HK) Ltd-admin-2508120532		73	\N	149.76	draft	f	\N	\N	\N	1	2025-08-12 13:18:32.927008	2025-08-12 13:19:09.987899	f	90	SGD	unpaid	\N	\N	\N	\N	\N	\N
\.


--
-- TOC entry 4783 (class 0 OID 24109)
-- Dependencies: 309
-- Data for Name: feature_changes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feature_changes (id, version_id, change_type, module_name, title, description, priority, impact_level, affected_files, git_commits, test_status, test_notes, developer_id, developer_name, created_at, completed_at) FROM stdin;
1	1	fix	system	修复: 修改拥有者的规则	修改拥有者的规则	medium	minor	\N	0855a70	passed	\N	\N	开发团队	2025-08-07 17:07:23	2025-08-07 17:07:23
2	2	fix	\N	修复版本自动更新机制：检测到新Git提交时自动创建版本记录	修复版本自动更新机制：检测到新Git提交时自动创建版本记录	medium	minor	\N	9981a32c	pending	\N	\N	开发团队	2025-08-08 14:47:51.920055	2025-08-08 14:47:51.920057
3	3	fix	\N	项目多重客户关联	项目多重客户关联	medium	minor	\N	6c441130	pending	\N	\N	开发团队	2025-08-09 09:19:59.789008	2025-08-09 09:19:59.789009
4	4	fix	\N	更新发票上传问题	更新发票上传问题	medium	minor	\N	1d4ded8e	pending	\N	\N	开发团队	2025-08-10 21:39:44.294845	2025-08-10 21:39:44.294849
5	5	fix	\N	更新发序号问题	更新发序号问题	medium	minor	\N	229883b2	pending	\N	\N	开发团队	2025-08-10 15:34:17.999949	2025-08-10 15:34:17.99995
6	6	fix	\N	修复Supabase数据库db.create_all()的schema问题\n\n关键问题:\n- SQLAlchemy的db.create_all()尝试创建ENUM类型时找不到schema\n- OVS 	修复Supabase数据库db.create_all()的schema问题\n\n关键问题:\n- SQLAlchemy的db.create_all()尝试创建ENUM类型时找不到schema\n- OVS Supabase数据库的search_path为空，导致"no schema has been selected"错误\n- 之前的修复只覆盖了Alembic迁移，但没有覆盖SQLAlchemy直接表创建\n\n解决方案:\n- 在db.create_all()调用前检测Supabase环境\n- 自动设置search_path为public\n- 确保ENUM类型和表结构能正确创建\n\n适用场景:\n- 解决云端OVS数据库部署时的启动错误\n- 兼容所有Supabase数据库实例\n- 不影响Render或其他数据库环境\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>	medium	minor	\N	d9fa9bb1	pending	\N	\N	开发团队	2025-08-11 00:43:47.746011	2025-08-11 00:43:47.746013
7	7	fix	\N	修研发产品库的销售地区问题	修研发产品库的销售地区问题	medium	minor	\N	806d4a41	pending	\N	\N	开发团队	2025-08-11 19:15:05.60682	2025-08-11 19:15:05.606821
8	8	fix	\N	更新服务器冷启数据库连接问题	更新服务器冷启数据库连接问题	medium	minor	\N	8a04ff3a	pending	\N	\N	开发团队	2025-08-12 00:53:44.499334	2025-08-12 00:53:44.499335
9	9	fix	\N	更新批价单问题	更新批价单问题	medium	minor	\N	ffb0f3de	pending	\N	\N	开发团队	2025-08-12 01:20:10.438673	2025-08-12 01:20:10.438674
10	10	fix	\N	修复检验缺乏检查的漏洞	修复检验缺乏检查的漏洞	medium	minor	\N	25b7fcb4	pending	\N	\N	开发团队	2025-08-12 08:11:09.911692	2025-08-12 08:11:09.911694
11	11	fix	\N	修复行动记录的展示问题	修复行动记录的展示问题	medium	minor	\N	17f3aa2d	pending	\N	\N	开发团队	2025-08-15 04:21:08.000904	2025-08-15 04:21:08.000905
\.


--
-- TOC entry 4785 (class 0 OID 24115)
-- Dependencies: 311
-- Data for Name: five_star_project_baselines; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.five_star_project_baselines (id, user_id, baseline_year, baseline_month, baseline_count, created_at, created_by) FROM stdin;
1	2	2025	1	0	2025-07-01 06:29:23.78746	\N
\.


--
-- TOC entry 4880 (class 0 OID 26498)
-- Dependencies: 406
-- Data for Name: formula_templates_extended; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.formula_templates_extended (id, template_name, template_category, description, formula_expression, required_tables, required_fields, result_type, result_unit, is_system_template, is_active, usage_count, last_used_at, created_at, updated_at, created_by) FROM stdin;
1	销售总金额统计	sales	统计指定时间范围内的销售总金额	SUM({quotations.amount}) WHERE {quotations.created_at} BETWEEN :start_date AND :end_date	["quotations"]	["quotations.amount", "quotations.created_at"]	numeric	元	t	t	\N	\N	\N	\N	\N
2	新增客户数量	customer	统计指定时间范围内新增的客户数量	COUNT({companies.id}) WHERE {companies.created_at} BETWEEN :start_date AND :end_date	["companies"]	["companies.id", "companies.created_at"]	count	个	t	t	\N	\N	\N	\N	\N
3	植入金额统计	sales	统计指定时间范围内的植入总金额	SUM({quotations.implant_total_amount}) WHERE {quotations.approval_status} = 'approved' AND {quotations.created_at} BETWEEN :start_date AND :end_date	["quotations"]	["quotations.implant_total_amount", "quotations.approval_status", "quotations.created_at"]	numeric	元	t	t	\N	\N	\N	\N	\N
\.


--
-- TOC entry 4787 (class 0 OID 24119)
-- Dependencies: 313
-- Data for Name: inventory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory (id, company_id, product_id, quantity, unit, location, min_stock, max_stock, notes, created_at, updated_at, created_by_id) FROM stdin;
\.


--
-- TOC entry 4789 (class 0 OID 24125)
-- Dependencies: 315
-- Data for Name: inventory_transactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory_transactions (id, inventory_id, transaction_type, quantity, quantity_before, quantity_after, reference_type, reference_id, description, transaction_date, created_by_id) FROM stdin;
\.


--
-- TOC entry 4874 (class 0 OID 26455)
-- Dependencies: 400
-- Data for Name: performance_formula_templates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.performance_formula_templates (id, template_name, template_category, formula_expression, description, variables_definition, example_usage, is_system_template, created_at) FROM stdin;
\.


--
-- TOC entry 4870 (class 0 OID 26425)
-- Dependencies: 396
-- Data for Name: performance_metrics_definition; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.performance_metrics_definition (id, metric_code, metric_name, metric_category, data_type, default_unit, description, available_sources, is_system_metric, is_active, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4791 (class 0 OID 24131)
-- Dependencies: 317
-- Data for Name: performance_statistics; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.performance_statistics (id, user_id, year, month, implant_amount_actual, sales_amount_actual, new_customers_actual, new_projects_actual, five_star_projects_actual, industry_statistics, calculated_at, created_at, updated_at) FROM stdin;
1	2	2025	1	0	0	0	0	0	{}	2025-07-01 06:29:23.808646	2025-07-01 06:29:23.810809	2025-07-01 06:29:23.810815
2	2	2025	2	0	0	0	0	0	{}	2025-07-01 06:29:23.837678	2025-07-01 06:29:23.837962	2025-07-01 06:29:23.837966
3	2	2025	3	0	0	0	0	0	{}	2025-07-01 06:29:23.858977	2025-07-01 06:29:23.859251	2025-07-01 06:29:23.859255
4	2	2025	4	0	0	0	0	0	{}	2025-07-01 06:29:23.881493	2025-07-01 06:29:23.881768	2025-07-01 06:29:23.881772
5	2	2025	5	0	0	0	0	0	{}	2025-07-01 06:29:23.902395	2025-07-01 06:29:23.902658	2025-07-01 06:29:23.902665
6	2	2025	6	206150.74	0	0	1	0	{"manufacturing": 1}	2025-07-01 06:29:24.443745	2025-07-01 06:29:24.444037	2025-07-01 06:29:24.444041
7	2	2025	7	0	0	0	0	0	{}	2025-07-01 06:29:24.467826	2025-07-01 06:29:24.46814	2025-07-01 06:29:24.468145
8	2	2025	8	0	0	0	0	0	{}	2025-07-01 06:29:24.488163	2025-07-01 06:29:24.488491	2025-07-01 06:29:24.488499
9	2	2025	9	0	0	0	0	0	{}	2025-07-01 06:29:24.508177	2025-07-01 06:29:24.508414	2025-07-01 06:29:24.508419
10	2	2025	10	0	0	0	0	0	{}	2025-07-01 06:29:24.528955	2025-07-01 06:29:24.529258	2025-07-01 06:29:24.529263
11	2	2025	11	0	0	0	0	0	{}	2025-07-01 06:29:24.551547	2025-07-01 06:29:24.551809	2025-07-01 06:29:24.551813
12	2	2025	12	0	0	0	0	0	{}	2025-07-01 06:29:24.572409	2025-07-01 06:29:24.572638	2025-07-01 06:29:24.572643
\.


--
-- TOC entry 4793 (class 0 OID 24139)
-- Dependencies: 319
-- Data for Name: performance_targets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.performance_targets (id, user_id, year, month, implant_amount_target, sales_amount_target, new_customers_target, new_projects_target, five_star_projects_target, display_currency, created_by, created_at, updated_at, updated_by, customers_rate, implant_rate, sales_rate, projects_rate) FROM stdin;
\.


--
-- TOC entry 4795 (class 0 OID 24147)
-- Dependencies: 321
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.permissions (id, user_id, module, can_view, can_create, can_edit, can_delete, permission_level, permission_level_description, pricing_discount_limit, settlement_discount_limit, can_change_owner) FROM stdin;
1	1	user	t	t	t	t	personal	\N	\N	\N	f
2	1	customer	t	t	t	t	personal	\N	\N	\N	f
3	1	project	t	t	t	t	personal	\N	\N	\N	f
4	1	quotation	t	t	t	t	personal	\N	\N	\N	f
5	1	product	t	t	t	t	personal	\N	\N	\N	f
6	1	admin	t	t	t	t	personal	\N	\N	\N	f
7	1	inventory	t	t	t	t	personal	\N	\N	\N	f
8	1	pricing_order	t	t	t	t	personal	\N	\N	\N	f
9	1	approval	t	t	t	t	personal	\N	\N	\N	f
10	1	backup	t	t	t	t	personal	\N	\N	\N	f
11	1	system	t	t	t	t	personal	\N	\N	\N	f
12	2	customer	t	t	t	t	personal	\N	\N	\N	f
13	2	project	t	t	t	t	personal	\N	\N	\N	f
14	2	quotation	t	t	t	t	personal	\N	\N	\N	f
15	2	product	t	f	f	f	personal	\N	\N	\N	f
16	3	customer	t	t	t	t	personal	\N	\N	\N	f
17	3	project	t	t	t	t	personal	\N	\N	\N	f
18	3	quotation	t	t	t	t	personal	\N	\N	\N	f
19	3	product	t	f	f	f	personal	\N	\N	\N	f
\.


--
-- TOC entry 4797 (class 0 OID 24154)
-- Dependencies: 323
-- Data for Name: pricing_order_approval_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pricing_order_approval_records (id, pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval, fast_approval_reason) FROM stdin;
\.


--
-- TOC entry 4799 (class 0 OID 24160)
-- Dependencies: 325
-- Data for Name: pricing_order_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pricing_order_details (id, pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, source_quotation_detail_id, currency) FROM stdin;
\.


--
-- TOC entry 4801 (class 0 OID 24167)
-- Dependencies: 327
-- Data for Name: pricing_orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pricing_orders (id, order_number, project_id, quotation_id, distributor_id, dealer_id, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approval_flow_type, status, current_approval_step, approved_by, approved_at, created_by, created_at, updated_at, is_direct_contract, is_factory_pickup, currency) FROM stdin;
\.


--
-- TOC entry 4803 (class 0 OID 24174)
-- Dependencies: 329
-- Data for Name: product_categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_categories (id, name, code_letter, description, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4805 (class 0 OID 24180)
-- Dependencies: 331
-- Data for Name: product_code_field_options; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_code_field_options (id, field_id, value, code, description, is_active, "position", created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4807 (class 0 OID 24186)
-- Dependencies: 333
-- Data for Name: product_code_field_values; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_code_field_values (id, product_code_id, field_id, option_id, custom_value) FROM stdin;
\.


--
-- TOC entry 4809 (class 0 OID 24190)
-- Dependencies: 335
-- Data for Name: product_code_fields; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_code_fields (id, subcategory_id, name, code, description, field_type, "position", max_length, is_required, use_in_code, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4811 (class 0 OID 24196)
-- Dependencies: 337
-- Data for Name: product_codes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_codes (id, product_id, category_id, subcategory_id, full_code, status, created_by, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4813 (class 0 OID 24200)
-- Dependencies: 339
-- Data for Name: product_regions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_regions (id, name, code_letter, description, created_at) FROM stdin;
\.


--
-- TOC entry 4815 (class 0 OID 24206)
-- Dependencies: 341
-- Data for Name: product_subcategories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.product_subcategories (id, category_id, name, code_letter, description, display_order, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4817 (class 0 OID 24212)
-- Dependencies: 343
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.products (id, type, category, product_mn, product_name, model, specification, brand, unit, retail_price, status, image_path, created_at, updated_at, owner_id, pdf_path, currency, is_vendor_product) FROM stdin;
1	渠道产品	Basestation	PS4MS2NN	Repeater	Mark1000 MAX	Frequency range: 400-470MHz    Channel spacing: 12.5kHz/25kHz    Max channel: 16    Max Power: 25W    Mode: DMR    NetFunction: NetFlex Cloud	Evertac Solutions	set	3290.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 16:53:10.160422	1	\N	USD	t
2	channel	Combiner	SGM1B022CZ1	RF Combiner	E-FH400-2	UHF2   440-470MHz   2-Port   Insertion loss≤ 4.0 dB  IP40  N-Female  2U	Evertac Solutions	set	1000.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
49	third_party	Accessories	W000163	Coaxial Dummy Load	E-TF50	50w 300-1000MHz dummy load  N male connector	Third party	set	41.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
50	third_party	Accessories	EDFWYFC24W	Fiber rack	ST/FC  24口	Standard FC type 24 port cabinet installation	Third party	set	96.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
51	third_party	Accessories	EDFWYFC04O	Fiber rack	ST/FC  4口	Standard FC type 4 port wall-mounted installation	Third party	set	42.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
52	third_party	Accessories	EJUWY05A40LC	Optical Fiber Jumper Cable Patch Cord	MNOFHC-SMD-50	LC to LC UPC Duplex Single Mode Fiber Patch Cable   5m (16ft)	Third party	set	4.10	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
53	third_party	Accessories	ECAWYGYXTH0401	Optical Fiber	GYXTH-4B1 4芯	4 core outdoor single mode smoke flame retardant	Third party	meter	1.23	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
54	third_party	Accessories	OBJANOTHS01	Light arrestor	CA-23RS	0-1000MHz 700W 50Ω N-Female	Third party	set	58.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
55	third_party	Accessories	OBJANOTGR01	Mounting brackets	MONT80	50cm L type	Third party	set	54.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
56	third_party	Accessories	OZCH221035	RF cable	HCAAYZ -50-12	1/2＂50Ω	Third party	meter	2.80	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
57	third_party	Accessories	OCIN5JZALC1	Connector adapter	N-J1/2	1/2＂N-J	Third party	set	2.50	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
58	third_party	Accessories	OCIN5KZALC1	Connector adapter	N-50KK	N-KK	Third party	set	2.50	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
59	third_party	Accessories	OCIN5JWALC1	Connector adapter	N-50JKW	90 Degree N-JK	Third party	set	2.50	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
60	third_party	Accessories	OISKHB1JLC1	Jumper Cable	E-JP50-7	0.5m/1.6ft  N-JJ for Antenna	Third party	set	9.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
61	third_party	Accessories	EJUMJK4315NJNJ	Jumper Cable	NJ/NJ-3 	1.5m/4.7ft N-JJ for Cabinet	Third party	set	6.80	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
62	third_party	Accessories	EJUMJK4315NJQJ	Cabinet	Standard	19 -inch standard 42U with cooling	Third party	set	500.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
63	third_party	Accessories	EJUMJK4314NJQJ	Cabinet 	Standard	RS PRO 6U-Rack Server Cabinet	Third party	set	260.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
6	channel	Combiner	SGDE1BU2XCZ1	RF Multi-Coupler	E-JF350/400-2	UHF   350-470MHz   2-Port   Insertion loss≤ 3.5dB  IP40  N-Female  1U	Evertac Solutions	set	509.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
7	channel	Combiner	SGDE1BU4XCZ1	RF Multi-Coupler	E-JF350/400-4	UHF   350-470MHz   4-Port   Insertion loss≤ 6.5dB  IP40  N-Female  1U	Evertac Solutions	set	620.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
8	channel	Combiner	SGDE1BU6XCZ1	RF Multi-Coupler	E-JF350/400-6	UHF   350-470MHz   6-Port   Insertion loss≤ 8.5dB  IP40  N-Female  1U	Evertac Solutions	set	750.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
9	channel	Combiner	SGDE1BU8XCZ1	RF Multi-Coupler	E-JF350/400-8	UHF   350-470MHz   8-Port   Insertion loss≤ 9.5dB  IP40  N-Female  1U	Evertac Solutions	set	1020.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
10	channel	Combiner	SGDULB4H1CZ1	Duplex	E-SGQ400D	UHF2   440-470MHz   2-5MHz   2U	Evertac Solutions	set	1460.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
11	channel	Combiner	SGULN4N1CZ1	Duplex	E-SGQ400N	UFH2   440-470MHz   0.5Mhz   1U	Evertac Solutions	set	700.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
3	channel	Combiner	SGCM1B042CZ1	RF Combiner	E-FH400-4	UHF2   440-470MHz   4-Port   Insertion loss≤ 7.5 dB  IP40  N-Female  2U	Evertac Solutions	set	1380.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
4	channel	Combiner	SGCM1B062CZ1	RF Combiner	E-FH400-6	UHF2   440-470MHz   6-Port   Insertion loss≤ 9.5 dB  IP40  N-Female  2U	Evertac Solutions	set	2250.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
5	channel	Combiner	SGCM1B082CZ1	RF Combiner	E-FH400-8	UHF2   440-470MHz   8-Port   Insertion loss≤11.0 dB  IP40  N-Female  2U	Evertac Solutions	set	2950.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
40	channel	Application	HYWSPNB1	Access License	LS-NFX-RPT	Repeater access to NetFLex License	Evertac Solutions	set	600.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
45	channel	Application	HYWT0NA1	Service Operation Tool	ACC-NUT	Tracking and notification system faults to the app   providing standard maintenance process	Evertac Solutions	set	780.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
47	third_party	Accessories	PER3RSV	Rack Server	PowerEdge R350 Rack Server	Windows Server Intel® 4 core   8G Cache   4C/8T   Turbo (65W)   3200 MT/s Gateway	DELL	set	2650.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
48	third_party	Accessories	RER7RSV	Rack Server	PowerEdge R740 Rack Server	Windows Server Intel® 6 core   16G Cache   4C/8T   Turbo (65W)   3200 MT/s NetFLex platform 	DELL	set	3840.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	f
46	channel	Application	NDILMOT10	Network Data Interface License	AP_REPEATER__NAI_DATA_ONLY_LIC_KEY	\N	Evertac Solutions	set	0.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
64	channel	Accessories	W000166	Explosion-proof box	FZ HH 1012	Explosion-proof rating is Class II B   with steel plate for splitter	Evertac Solutions	set	710.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
65	channel	Accessories	W000170	Explosion-proof box	FZ HH 1016	Explosion-proof rating is Class II B   with steel plate for ORU	Evertac Solutions	set	1600.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
66	channel	Radio	TS4D3NMK	Two-way radio	PNR2000	Frequency range: 400MHz    Mode: DMR    Voltage: 3.8V    Function: BlueTooth/iBeacon    Interface.: No-keyboard screen	Evertac Solutions	set	290.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
67	channel	Radio	YSTSTH	Battery	YSTSTH	Capacity: 3800 mAh    Voltage: 3.8 V    Function: Capacity testing online    Compatibility: PNR2000	Evertac Solutions	set	41.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
68	channel	Charge	ZSTCN3T	Multi-Charging/Storge cabinet	CRCAB2000	27U charging cabinet   three sets of charging stacks are used   providing the capability to simultaneously charge or store up to 18 two-way radios or battery packs	Evertac Solutions	set	1740.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
69	channel	Charge	ZSTSN0N	Multi-Charging Stack	CRSTC1000	Comprising a single multi-channel charger and a 19-inch tray   it facilitates the assembly of multiple stacks into a charging cabinet.	Evertac Solutions	set	450.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
70	channel	Charge	ZSTZN0N	Multi-Charging Hub	CMP2600	6-way walkie-talkie/battery charging combination   featuring battery management and NetFlex cloud management capabilities	Evertac Solutions	set	320.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
12	channel	Combiner	SGE1AD6xCZ1	DownLink Multi-Splitter	R-EVDC-BLST-D	UHF1  350-470MHz    6+1-Port   Max Input Power 50W   Insertion loss≤0.5dB  N-Female  1U	Evertac Solutions	set	800.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
13	channel	Combiner	SGE1AU6xCZ1	UpLink Multi-Splitter	R-EVDC-BLST-U	UHF1   350-470MHz   6+1-Port   Max Input Power 50W   Insertion loss≤ 0.5dB  N-Female  1U	Evertac Solutions	set	800.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
14	channel	BDA	SGR2SI030	OMU	RFS-400 LT/M	350-470MHz   BW 15MHz   4FP   NetFLEX 	Evertac Solutions	set	1890.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
15	channel	BDA	SGR3SI14S	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 5MHz   33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	2640.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
16	channel	BDA	SGR3SI140	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 10MHz  33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	2640.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
17	channel	BDA	SGR3SI340	ORU	RFT-BDA410 LT/M	440-470MHz   BW 1M   40dBm/10W   REMOTE   NetFLEX	Evertac Solutions	set	4636.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
18	channel	BDA	SGR2DI040	OMU	DRFS-400/M	400-470MHz   BW 20M   32OP   2U   Digital transmit   NetFLEX	Evertac Solutions	set	5455.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
19	channel	BDA	SGR3DI340	ORU	DRFT-BDA410/M	400-470MHz   BW 4M   40dBm/10W   2U   Digital transimit   NetFLEX	Evertac Solutions	set	10455.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
20	channel	BDA	SGGF20000	Cable Feed Modular	FDPower400	modular install in ORU via RF cable to feed power	Evertac Solutions	set	345.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
21	channel	Antenna	SGAIOCN4Y	Indoor Antenna	MA10	UHF   350-470MHz   Max Input Power 50W   0dBi	Evertac Solutions	set	25.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
22	channel	Antenna	SGAIOCB4Y	Smart Indoor Antenna	MA12	UHF   350-470MHz   Max Input Power 50W   Gain 0dBi   Signal detection   iBeacon 	Evertac Solutions	set	95.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
23	channel	Antenna	SGAIOCL4Y	Smart Indoor Antenna	MA11	UHF   350-470MHz   Max Input Power 50W   Gain 0dBi   Signal detection 	Evertac Solutions	set	45.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
24	channel	Antenna	EAN2ICO2FZ1	Integrated explosion-proof antenna	E-ANTO EX	UHF   350-470MHz   50W   Gain 0dBi   IP65 IICA21	Evertac Solutions	set	1030.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
25	channel	Antenna	SGAN2OFD2TE2	Panel Antenna	E-ANTD 400	UHF   450-470MHz   Max Input Power 50W   Gain 2dBi	Evertac Solutions	set	80.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
26	channel	Antenna	SGANLOMO5HR1	Fiber Glass Omni Antenna	E-ANTG 400	UHF   450-470MHz   Max Input Power 50W   5dBi	Evertac Solutions	set	100.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
27	channel	Antenna	SGCDN24Y	Splitter	EVPD-2 LT	80-470MHz   MIP 50W	Evertac Solutions	set	25.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
28	channel	Antenna	SGCCN34Y	Coupler	EVDC-6 LT	350-470MHz   MIP 50W   CP 6dB	Evertac Solutions	set	25.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
29	channel	Antenna	SGCCN44Y	Coupler	EVDC-10 LT	350-470MHz   MIP 50W   CP 10dB	Evertac Solutions	set	25.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
30	channel	Antenna	SGCCN54Y	Coupler	EVDC-15 LT	350-470MHz   MIP 50W   CP 15dB	Evertac Solutions	set	25.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
31	channel	Antenna	SGCCN64Y	Coupler	EVDC-20 LT	350-470MHz   MIP 50W   CP 20dB	Evertac Solutions	set	25.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
32	channel	Antenna	SGCCN74Y	Coupler	EVDC-30 LT	350-470MHz   MIP 50W   CP 30dB	Evertac Solutions	set	25.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
33	channel	Antenna	SGCDF24Y	Splitter	MAPD-2	350-470MHz   MIP 50W   CFP	Evertac Solutions	set	55.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
34	channel	Antenna	SGCCF34Y	Coupler	MADC-6	350-470MHz   MIP 50W   CP 6dB   CFP	Evertac Solutions	set	55.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
35	channel	Antenna	SGCCF44Y	Coupler	MADC-10	350-470MHz   MIP 50W   CP 10dB   CFP	Evertac Solutions	set	55.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
36	channel	Antenna	SGCCF54Y	Coupler	MADC-15	350-470MHz   MIP 50W   CP 15dB   CFP	Evertac Solutions	set	55.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
37	channel	Antenna	SGCCF64Y	Coupler	MADC-20	350-470MHz   MIP 50W   CP 20dB   CFP	Evertac Solutions	set	55.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
38	channel	Application	HYWSTNB1	Access License	LS-NFX-RAD	Two-way radio access to NetFLEX License	Evertac Solutions	set	45.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
39	channel	Application	HYWSRNB1	Access License	LS-NFX-BDA	ORU access to NetFLEX License	Evertac Solutions	set	360.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
41	channel	Application	HYWG0NB1	Gateway application	NFX_GATW	Synchronize setup configure system managment driver update online	Evertac Solutions	set	3050.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
42	channel	Application	HYWP0NC1	NetFLEX Platform 	NFX_MAST_OPETN	Account management System Backup and Recover System structure diagram	Evertac Solutions	set	25500.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
43	channel	Application	EHYW521066	Driver	GW-MOT-RPT	MOTOROLA to NetFLEX Gateway Protocal	Evertac Solutions	set	6540.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
44	channel	Application	HYWF0NA1	Operation DashBoard	ACC-CWT	System Health analyz   System diagram online Fault Notification  Equipment location 	Evertac Solutions	set	1600.00	active	\N	2025-06-22 20:36:02.699629	2025-06-22 20:36:02.699629	1	\N	USD	t
\.


--
-- TOC entry 4819 (class 0 OID 24220)
-- Dependencies: 345
-- Data for Name: project_customer_associations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_customer_associations (id, project_id, company_id, customer_type, created_at, updated_at, created_by) FROM stdin;
1	12	28	dealer	2025-07-22 03:27:05.532266	2025-07-24 10:00:43.956286	3
2	13	28	dealer	2025-07-22 07:35:34.62831	2025-07-23 13:52:59.498377	3
3	14	28	dealer	2025-07-22 09:15:27.105584	2025-07-24 10:03:35.429082	3
4	15	28	dealer	2025-07-22 09:19:47.72111	2025-07-29 01:35:37.329752	3
5	16	28	dealer	2025-07-22 09:42:21.567443	2025-07-23 14:00:31.468069	3
6	17	28	dealer	2025-07-22 09:46:33.384082	2025-07-23 14:03:41.313731	3
7	18	28	dealer	2025-07-22 09:51:48.203263	2025-07-23 13:56:14.110744	3
8	19	28	dealer	2025-07-22 13:28:47.502992	2025-07-24 01:54:26.627892	3
9	21	28	dealer	2025-07-24 02:06:49.912688	2025-07-24 10:07:37.754484	3
10	22	42	dealer	2025-07-29 08:15:01.134333	2025-08-07 08:37:47.968243	7
11	7	14	system_integrator	2025-07-09 00:27:33.743568	2025-07-14 00:57:51.917492	2
12	8	28	system_integrator	2025-07-09 01:33:32.244617	2025-07-14 00:58:19.764323	2
13	11	53	system_integrator	2025-07-10 02:12:50.210828	2025-08-04 08:46:58.823346	3
14	13	47	system_integrator	2025-07-22 07:35:34.62831	2025-07-23 13:52:59.498377	3
15	14	47	system_integrator	2025-07-22 09:15:27.105584	2025-07-24 10:03:35.429082	3
16	15	47	system_integrator	2025-07-22 09:19:47.72111	2025-07-29 01:35:37.329752	3
17	16	47	system_integrator	2025-07-22 09:42:21.567443	2025-07-23 14:00:31.468069	3
18	17	47	system_integrator	2025-07-22 09:46:33.384082	2025-07-23 14:03:41.313731	3
19	18	45	system_integrator	2025-07-22 09:51:48.203263	2025-07-23 13:56:14.110744	3
20	20	25	system_integrator	2025-07-22 14:42:28.332855	2025-07-23 13:45:18.140599	3
21	22	54	system_integrator	2025-07-29 08:15:01.134333	2025-08-07 08:37:47.968243	7
22	9	32	end_user	2025-07-09 07:33:08.034525	2025-07-09 07:33:08.041262	3
23	10	36	end_user	2025-07-10 01:30:50.209716	2025-07-10 01:30:50.217486	3
24	11	32	end_user	2025-07-10 02:12:50.210828	2025-08-04 08:46:58.823346	3
25	12	44	end_user	2025-07-22 03:27:05.532266	2025-07-24 10:00:43.956286	3
26	13	46	end_user	2025-07-22 07:35:34.62831	2025-07-23 13:52:59.498377	3
27	14	44	end_user	2025-07-22 09:15:27.105584	2025-07-24 10:03:35.429082	3
28	15	44	end_user	2025-07-22 09:19:47.72111	2025-07-29 01:35:37.329752	3
29	16	44	end_user	2025-07-22 09:42:21.567443	2025-07-23 14:00:31.468069	3
30	17	44	end_user	2025-07-22 09:46:33.384082	2025-07-23 14:03:41.313731	3
31	18	46	end_user	2025-07-22 09:51:48.203263	2025-07-23 13:56:14.110744	3
32	19	46	end_user	2025-07-22 13:28:47.502992	2025-07-24 01:54:26.627892	3
33	20	49	end_user	2025-07-22 14:42:28.332855	2025-07-23 13:45:18.140599	3
34	21	44	end_user	2025-07-24 02:06:49.912688	2025-07-24 10:07:37.754484	3
35	27	64	end_user	2025-08-07 07:33:04.807869	2025-08-07 08:08:51.115224	7
36	9	33	design_issues	2025-07-09 07:33:08.034525	2025-07-09 07:33:08.041262	3
37	10	37	design_issues	2025-07-10 01:30:50.209716	2025-07-10 01:30:50.217486	3
38	12	37	design_issues	2025-07-22 03:27:05.532266	2025-07-24 10:00:43.956286	3
39	14	37	design_issues	2025-07-22 09:15:27.105584	2025-07-24 10:03:35.429082	3
40	15	37	design_issues	2025-07-22 09:19:47.72111	2025-07-29 01:35:37.329752	3
41	16	37	design_issues	2025-07-22 09:42:21.567443	2025-07-23 14:00:31.468069	3
42	17	37	design_issues	2025-07-22 09:46:33.384082	2025-07-23 14:03:41.313731	3
43	20	37	design_issues	2025-07-22 14:42:28.332855	2025-07-23 13:45:18.140599	3
44	21	37	design_issues	2025-07-24 02:06:49.912688	2025-07-24 10:07:37.754484	3
45	6	16	contractor	2025-06-30 08:02:39.685586	2025-08-06 03:12:12.703022	2
46	9	34	contractor	2025-07-09 07:33:08.034525	2025-07-09 07:33:08.041262	3
47	10	38	contractor	2025-07-10 01:30:50.209716	2025-07-10 01:30:50.217486	3
48	11	39	contractor	2025-07-10 02:12:50.210828	2025-08-04 08:46:58.823346	3
49	20	29	contractor	2025-07-22 14:42:28.332855	2025-07-23 13:45:18.140599	3
52	8	12	end_user	2025-08-12 09:23:59.349916	2025-08-12 09:23:59.349932	2
53	12	69	end_user	2025-08-12 14:00:48.555431	2025-08-12 14:00:48.555437	2
54	22	65	end_user	2025-08-12 15:41:53.99433	2025-08-12 15:41:53.994336	2
55	31	65	end_user	2025-08-12 16:00:36.977237	2025-08-12 16:00:36.977243	2
\.


--
-- TOC entry 4821 (class 0 OID 24226)
-- Dependencies: 347
-- Data for Name: project_members; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_members (id, project_id, user_id, role, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4823 (class 0 OID 24230)
-- Dependencies: 349
-- Data for Name: project_rating_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_rating_records (id, project_id, user_id, rating, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4825 (class 0 OID 24235)
-- Dependencies: 351
-- Data for Name: project_scoring_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_scoring_config (id, category, field_name, field_label, score_value, prerequisite, is_active, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4827 (class 0 OID 24245)
-- Dependencies: 353
-- Data for Name: project_scoring_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_scoring_records (id, project_id, category, field_name, score_value, awarded_by, auto_calculated, notes, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4829 (class 0 OID 24255)
-- Dependencies: 355
-- Data for Name: project_stage_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_stage_history (id, project_id, from_stage, to_stage, change_date, change_week, change_month, change_year, account_id, remarks, created_at) FROM stdin;
13	6	discover	embed	2025-06-30 08:02:56.570368	202526	202506	2025	\N	API推进: quah	2025-06-30 08:02:56.553791
14	6	discover	embed	2025-06-30 08:02:56.598198	202526	202506	2025	\N	自动记录: discover → embed	2025-06-30 08:02:56.584143
15	6	embed	pre_tender	2025-06-30 08:03:09.805955	202526	202506	2025	\N	API推进: quah	2025-06-30 08:03:09.795205
16	6	embed	pre_tender	2025-06-30 08:03:09.827758	202526	202506	2025	\N	自动记录: embed → pre_tender	2025-06-30 08:03:09.816301
17	6	pre_tender	tendering	2025-06-30 08:03:18.615025	202526	202506	2025	\N	API推进: quah	2025-06-30 08:03:18.584186
18	6	pre_tender	tendering	2025-06-30 08:03:18.652317	202526	202506	2025	\N	自动记录: pre_tender → tendering	2025-06-30 08:03:18.629837
19	7	discover	embed	2025-07-09 00:31:12.306265	202527	202507	2025	\N	API推进: quah	2025-07-09 00:31:12.29606
20	7	discover	embed	2025-07-09 00:31:12.329383	202527	202507	2025	\N	自动记录: discover → embed	2025-07-09 00:31:12.316752
21	8	discover	embed	2025-07-09 01:33:37.50973	202527	202507	2025	\N	API推进: quah	2025-07-09 01:33:37.497952
22	8	discover	embed	2025-07-09 01:33:37.534402	202527	202507	2025	\N	自动记录: discover → embed	2025-07-09 01:33:37.520212
23	8	embed	pre_tender	2025-07-09 01:33:38.982252	202527	202507	2025	\N	API推进: quah	2025-07-09 01:33:38.971459
24	8	embed	pre_tender	2025-07-09 01:33:39.004431	202527	202507	2025	\N	自动记录: embed → pre_tender	2025-07-09 01:33:38.992889
25	8	pre_tender	tendering	2025-07-09 01:33:40.012024	202527	202507	2025	\N	API推进: quah	2025-07-09 01:33:40.000736
26	8	pre_tender	tendering	2025-07-09 01:33:40.032759	202527	202507	2025	\N	自动记录: pre_tender → tendering	2025-07-09 01:33:40.02143
27	8	tendering	awarded	2025-07-09 01:33:41.239455	202527	202507	2025	\N	API推进: quah	2025-07-09 01:33:41.229105
28	8	tendering	awarded	2025-07-09 01:33:41.262567	202527	202507	2025	\N	自动记录: tendering → awarded	2025-07-09 01:33:41.250165
29	8	awarded	quoted	2025-07-09 01:33:42.769415	202527	202507	2025	\N	API推进: quah	2025-07-09 01:33:42.759486
30	8	awarded	quoted	2025-07-09 01:33:42.79473	202527	202507	2025	\N	自动记录: awarded → quoted	2025-07-09 01:33:42.779011
31	15	discover	embed	2025-07-22 09:28:47.751042	202529	202507	2025	\N	自动记录: discover → embed	2025-07-22 09:28:47.740665
32	15	discover	embed	2025-07-22 09:28:47.78556	202529	202507	2025	\N	自动记录: discover → embed	2025-07-22 09:28:47.773543
33	19	discover	embed	2025-07-23 05:50:01.929643	202529	202507	2025	\N	自动记录: discover → embed	2025-07-23 05:50:01.917382
34	19	discover	embed	2025-07-23 05:50:01.960611	202529	202507	2025	\N	自动记录: discover → embed	2025-07-23 05:50:01.946682
35	18	pre_tender	tendering	2025-07-23 05:55:31.351947	202529	202507	2025	\N	自动记录: pre_tender → tendering	2025-07-23 05:55:31.339593
36	18	pre_tender	tendering	2025-07-23 05:55:31.382629	202529	202507	2025	\N	自动记录: pre_tender → tendering	2025-07-23 05:55:31.368382
37	17	embed	tendering	2025-07-23 06:03:26.506292	202529	202507	2025	\N	自动记录: embed → tendering	2025-07-23 06:03:26.492691
38	17	embed	tendering	2025-07-23 06:03:26.539072	202529	202507	2025	\N	自动记录: embed → tendering	2025-07-23 06:03:26.523655
39	19	embed	pre_tender	2025-07-24 01:53:18.035224	202529	202507	2025	\N	API推进: roy	2025-07-24 01:53:18.018998
40	19	embed	pre_tender	2025-07-24 01:53:18.085744	202529	202507	2025	\N	自动记录: embed → pre_tender	2025-07-24 01:53:18.04678
41	19	pre_tender	embed	2025-07-24 01:54:26.597168	202529	202507	2025	\N	自动记录: pre_tender → embed	2025-07-24 01:54:26.586643
42	19	pre_tender	embed	2025-07-24 01:54:26.627689	202529	202507	2025	\N	自动记录: pre_tender → embed	2025-07-24 01:54:26.615588
43	15	embed	tendering	2025-07-24 02:09:11.578272	202529	202507	2025	\N	自动记录: embed → tendering	2025-07-24 02:09:11.566695
44	15	embed	tendering	2025-07-24 02:09:11.618844	202529	202507	2025	\N	自动记录: embed → tendering	2025-07-24 02:09:11.602219
45	11	discover	embed	2025-08-04 08:46:58.784094	202531	202508	2025	\N	API推进: roy	2025-08-04 08:46:58.768381
46	11	discover	embed	2025-08-04 08:46:58.800383	202531	202508	2025	\N	自动记录: discover → embed	2025-08-04 08:46:58.794805
47	11	discover	embed	2025-08-04 08:46:58.82311	202531	202508	2025	\N	自动记录: discover → embed	2025-08-04 08:46:58.809654
48	6	tendering	lost	2025-08-06 03:12:12.659039	202531	202508	2025	\N	API推进: quah	2025-08-06 03:12:12.642833
49	6	tendering	lost	2025-08-06 03:12:12.702703	202531	202508	2025	\N	自动记录: tendering → lost	2025-08-06 03:12:12.673428
68	27	discover	embed	2025-08-07 07:45:32.029691	202531	202508	2025	\N	API推进: yusry	2025-08-07 07:45:32.019066
69	27	discover	embed	2025-08-07 07:45:32.052637	202531	202508	2025	\N	自动记录: discover → embed	2025-08-07 07:45:32.038323
70	27	embed	pre_tender	2025-08-07 07:45:33.253415	202531	202508	2025	\N	API推进: yusry	2025-08-07 07:45:33.242037
71	27	embed	pre_tender	2025-08-07 07:45:33.274618	202531	202508	2025	\N	自动记录: embed → pre_tender	2025-08-07 07:45:33.260697
72	27	pre_tender	tendering	2025-08-07 07:45:34.253006	202531	202508	2025	\N	API推进: yusry	2025-08-07 07:45:34.242272
73	27	pre_tender	tendering	2025-08-07 07:45:34.274688	202531	202508	2025	\N	自动记录: pre_tender → tendering	2025-08-07 07:45:34.260532
74	27	tendering	awarded	2025-08-07 07:45:35.286746	202531	202508	2025	\N	API推进: yusry	2025-08-07 07:45:35.276862
75	27	tendering	awarded	2025-08-07 07:45:35.307123	202531	202508	2025	\N	自动记录: tendering → awarded	2025-08-07 07:45:35.293992
76	13	tendering	awarded	2025-08-11 03:38:16.360332	202532	202508	2025	\N	API推进: fuyan	2025-08-11 03:38:16.299555
77	13	tendering	awarded	2025-08-11 03:38:16.410477	202532	202508	2025	\N	自动记录: tendering → awarded	2025-08-11 03:38:16.344012
78	13	awarded	paused	2025-08-11 03:45:26.31732	202532	202508	2025	\N	API推进: fuyan	2025-08-11 03:45:26.258829
79	13	awarded	paused	2025-08-11 03:45:26.360067	202532	202508	2025	\N	自动记录: awarded → paused	2025-08-11 03:45:26.298123
\.


--
-- TOC entry 4831 (class 0 OID 24262)
-- Dependencies: 357
-- Data for Name: project_total_scores; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_total_scores (id, project_id, information_score, quotation_score, stage_score, manual_score, total_score, star_rating, last_calculated, created_at, updated_at) FROM stdin;
9	9	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-22 13:36:47.013795	2025-07-09 07:33:08.089559	2025-07-22 13:36:47.014427
20	20	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-23 05:44:17.443726	2025-07-22 14:42:28.367334	2025-07-23 05:44:17.444604
19	19	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-24 01:54:26.627195	2025-07-22 13:28:47.531318	2025-07-24 01:54:26.629238
18	18	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-24 01:56:33.087174	2025-07-22 09:51:48.237105	2025-07-24 01:56:33.087903
17	17	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-24 01:57:59.854591	2025-07-22 09:46:33.430297	2025-07-24 01:57:59.855083
12	12	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-24 01:58:58.627056	2025-07-22 03:27:05.560719	2025-07-24 01:58:58.627828
14	14	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-24 02:03:23.256697	2025-07-22 09:15:27.134787	2025-07-24 02:03:23.257236
21	21	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-24 02:06:49.946381	2025-07-24 02:06:49.9393	2025-07-24 02:06:49.948264
15	15	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-24 02:09:11.618175	2025-07-22 09:19:47.763487	2025-07-24 02:09:11.622852
16	16	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-24 02:11:26.116649	2025-07-22 09:42:21.598892	2025-07-24 02:11:26.11742
8	8	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-09 01:33:42.794102	2025-07-09 01:33:32.285769	2025-07-09 01:33:42.797562
7	7	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-09 03:13:24.351814	2025-07-09 00:27:33.780483	2025-07-09 03:13:24.352725
10	10	0.00	0.00	0.00	0.00	0.00	0.0	2025-07-10 01:54:37.019721	2025-07-10 01:30:50.241065	2025-07-10 01:54:37.020377
11	11	0.00	0.00	0.00	0.00	0.00	0.0	2025-08-04 08:46:58.822491	2025-07-10 02:12:50.241851	2025-08-04 08:46:58.825066
6	6	0.00	0.00	0.00	0.00	0.00	0.0	2025-08-06 03:12:12.700023	2025-06-30 08:02:39.715799	2025-08-06 03:12:12.704945
27	27	0.00	0.00	0.00	0.00	0.00	0.0	2025-08-07 07:45:35.306657	2025-08-07 07:33:04.918283	2025-08-07 07:45:35.308584
22	22	0.00	0.00	0.00	0.00	0.00	0.0	2025-08-07 08:38:01.980177	2025-07-29 08:15:01.17116	2025-08-07 08:38:01.981227
13	13	0.00	0.00	0.00	0.00	0.00	0.0	2025-08-11 03:45:26.359331	2025-07-22 07:35:34.660642	2025-08-11 03:45:26.362977
28	28	0.00	0.00	0.00	0.00	0.00	0.0	2025-08-11 04:03:38.845629	2025-08-11 02:49:30.497252	2025-08-11 04:03:38.846777
31	31	0.00	0.00	0.00	0.00	0.00	0.0	2025-08-12 08:00:26.730132	2025-08-12 08:00:26.707548	2025-08-12 08:00:26.733814
32	32	0.00	0.00	0.00	0.00	0.00	0.0	2025-08-14 07:48:22.997571	2025-08-14 07:48:22.976527	2025-08-14 07:48:23.001921
\.


--
-- TOC entry 4833 (class 0 OID 24275)
-- Dependencies: 359
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.projects (id, project_name, report_time, project_type, report_source, product_situation, end_user, design_issues, dealer, contractor, system_integrator, current_stage, stage_description, authorization_code, delivery_forecast, quotation_customer, authorization_status, feedback, created_at, updated_at, owner_id, is_locked, locked_reason, locked_by, locked_at, is_active, last_activity_date, activity_reason, vendor_sales_manager_id, rating, industry, shared_with_users, share_enabled) FROM stdin;
10	YTL Data Centre @ Kulai	\N	sales_focus	marketing		SIPP Power Sdn Bhd (subsidiary of YTL Corporation Bhd)	TRAC Consulting & Engineering Sdn Bhd		 Syarikat Pembenaan Yeoh Tiong Lay Sdn Bhd (YTL Construction) 		discover	Azri and told this 275 acre land reserve for solar power & data centre campus. Planning for 12 DC buildings with total 500MW capacity. YTL JC1 & 2 already completed and JDC3 Hyperscale AI facility & JDC6 Colocation facility will handover in next quater. Told this project that totally no RF in design and will depends on operation team request. 	\N	\N	0	\N	\N	2025-07-10 01:30:50.209716	2025-07-10 01:30:50.217486	3	f	\N	\N	\N	t	2025-07-10 01:30:50.209716	\N	3	0	other	[]	f
7	Exsim DC, EX1 & EX2	2025-07-14	sales_focus	sales	unqualified					Mymeta Solution Sdn Bhd	embed		SPJ202507-001	\N	139715.75999999998	\N	\N	2025-07-09 00:27:33.743568	2025-07-14 00:57:51.917492	2	f	\N	\N	\N	t	2025-07-09 00:27:33.743568	\N	2	0	other	[]	f
6	Jabil's Vietnam	\N	business_opportunity	sales	unqualified				BHJ Security Technology Sdn Bhd		lost	Submitted initial budgetary tender together with BHJ's security system for 1st round	\N	\N	36076.39	\N	\N	2025-06-30 08:02:39.685586	2025-08-06 03:12:12.703022	2	f	\N	\N	\N	t	2025-06-30 08:02:39.685586	\N	2	0	manufacturing	[]	f
20	NextDC KL1 - Block 4 & 5 @ PJ	\N	sales_focus	marketing	qualified	NextDC Sdn. Bhd.	TRAC Consulting & Engineering Sdn Bhd		Pembinaan Mitrajaya Sdn. Bhd.	SKA Technology Sdn Bhd	discover	      	\N	\N	0	\N	\N	2025-07-22 14:42:28.332855	2025-07-23 13:45:18.140599	3	f	\N	\N	\N	t	2025-07-22 14:42:28.332855	\N	3	0	datacenter	[]	f
9	MY02 - Phase 2 - Bridge DC @ Cyberjaya 	\N	sales_focus	marketing	qualified	Bridge Data Centres -  (Subsidiary of Chindata Group @ Beijing)	Dynast Consult Sdn. Bhd.		CCIE Engineering (M) Sdn. Bhd.		discover	Consultant Mr. Wong told this MY02 2nd phase still in planning stage and haven't confirm will add on a new basestation or link from phase 1.         	\N	\N	0	\N	\N	2025-07-09 07:33:08.034525	2025-07-09 07:33:08.041262	3	f	\N	\N	\N	f	2025-07-09 07:33:08.034525	\N	3	0	datacenter	[]	f
21	NTP - K & L - GDS DC @ Nusajaya Tech Park	\N	channel_follow	channel	controlled	GDS IDC SERVICES III (MALAYSIA) SDN BHD	TRAC Consulting & Engineering Sdn Bhd	FMTCS SOLUTIONS PTE. LTD			tendering		\N	\N	0	\N	\N	2025-07-24 02:06:49.912688	2025-07-24 10:07:37.754484	12	f	\N	\N	\N	t	2025-07-24 02:06:49.912688	\N	3	0	datacenter	[]	f
15	NTP - J - GDS DC @ Nusajaya Tech Park	\N	channel_follow	channel	controlled	GDS IDC SERVICES III (MALAYSIA) SDN BHD	TRAC Consulting & Engineering Sdn Bhd	FMTCS SOLUTIONS PTE. LTD		Longmotive (M) Sdn. Bhd.	tendering		\N	2025-09-15	63959	\N	\N	2025-07-22 09:19:47.72111	2025-08-11 02:58:21.621048	12	f	\N	\N	\N	t	2025-07-22 09:19:47.72111	\N	3	0	datacenter	[2, 3, 4, 5, 9, 10, 11, 12]	t
12	NTP - N - GDS DC @ Nusajaya Tech Park 	\N	channel_follow	channel	controlled	GDS IDC SERVICES III (MALAYSIA) SDN BHD	TRAC Consulting & Engineering Sdn Bhd	FMTCS SOLUTIONS PTE. LTD		EPG Data Center Module Sdn. Bhd.	tendering		\N	2025-09-15	82335.68999999999	\N	\N	2025-07-22 03:27:05.532266	2025-08-12 14:22:27.378864	12	f	\N	\N	\N	t	2025-07-22 03:27:05.532266	\N	3	0	datacenter	[2, 3, 4, 5, 9, 10, 11, 12]	t
14	NTP - G & M - GDS DC @ Nusaya Tech Park	\N	channel_follow	channel	controlled	GDS IDC SERVICES III (MALAYSIA) SDN BHD	TRAC Consulting & Engineering Sdn Bhd	FMTCS SOLUTIONS PTE. LTD		Longmotive (M) Sdn. Bhd.	signed		\N	2025-08-15	0	\N	\N	2025-07-22 09:15:27.105584	2025-07-24 10:03:35.429082	3	t	项目已签约，自动锁定	1	2025-07-29 16:33:12.312753	t	2025-07-22 09:15:27.105584	\N	3	0	datacenter	[2, 3, 4, 5, 9, 10, 11, 12]	t
19	CTP - C - GDS DC @ Chonburi Thailand	\N	channel_follow	channel	qualified	GDS Data Center @ Thailand		FMTCS SOLUTIONS PTE. LTD			embed		\N	\N	0	\N	\N	2025-07-22 13:28:47.502992	2025-07-24 01:54:26.627892	12	f	\N	\N	\N	t	2025-07-22 13:28:47.502992	\N	3	0	datacenter	[]	f
22	PNB 118 	\N	channel_follow	channel	not_required			Triple Access Sdn Bhd		O'Connor's Engineering Sdn Bhd	tendering		\N	\N	294553.88	\N	\N	2025-07-29 08:15:01.134333	2025-08-12 15:46:11.46849	7	f	\N	\N	\N	t	2025-07-29 08:15:01.134333	\N	2	0	other	[8, 7]	t
17	KTP - G, N & J - GDS DC @ Kempas Tech Park	\N	channel_follow	channel	controlled	GDS IDC SERVICES III (MALAYSIA) SDN BHD	TRAC Consulting & Engineering Sdn Bhd	FMTCS SOLUTIONS PTE. LTD		Longmotive (M) Sdn. Bhd.	tendering		\N	\N	0	\N	\N	2025-07-22 09:46:33.384082	2025-07-23 14:03:41.313731	12	f	\N	\N	\N	t	2025-07-22 09:46:33.384082	\N	3	0	datacenter	[]	f
16	KTP - B & C - GDS DC @ Kempas Tech Park	\N	channel_follow	channel	controlled	GDS IDC SERVICES III (MALAYSIA) SDN BHD	TRAC Consulting & Engineering Sdn Bhd	FMTCS SOLUTIONS PTE. LTD		Longmotive (M) Sdn. Bhd.	tendering		\N	2025-12-15	0	\N	\N	2025-07-22 09:42:21.567443	2025-07-23 14:00:31.468069	12	f	\N	\N	\N	t	2025-07-22 09:42:21.567443	\N	3	0	datacenter	[]	f
18	CTP - A - GDS DC @ Chonburi Thailand	\N	channel_follow	channel	qualified	GDS Data Center @ Thailand		FMTCS SOLUTIONS PTE. LTD		EPG Engineering System Sdn. Bhd.	tendering		\N	2025-10-15	0	\N	\N	2025-07-22 09:51:48.203263	2025-07-23 13:56:14.110744	12	f	\N	\N	\N	t	2025-07-22 09:51:48.203263	\N	3	0	datacenter	[]	f
11	Bridge Data Centre @ Chonburi, Thailand	\N	sales_focus	marketing	unqualified	Bridge Data Centres -  (Subsidiary of Chindata Group @ Beijing)			China Construction Yangtze River (Malaysia) Sdn. Bhd. (Subsidiary of CSCEC)	Timesfly Engineering Services 时代飞扬	embed	Info from end-user Ms. 胡桂霞 (Technical team) to recommend follow up with maincon PIC Mr.赵剑波 @ CCYR China.\r\n	\N	\N	0	\N	\N	2025-07-10 02:12:50.210828	2025-08-04 08:46:58.823346	3	f	\N	\N	\N	t	2025-07-10 02:12:50.210828	\N	3	0	datacenter	[2, 3, 4, 5, 9, 10, 11, 12]	t
28	NTP-N	\N	sales_focus	channel	controlled	GDS Data Center @ Thailand		FMTCS SOLUTIONS PTE. LTD	EPG		discover	目前已经确认EPG中标机电总承包，EPG向下招标目前系统集成商有6家单位分别是;YSC、郎泽、EXQ、BHJ、百科建筑、瑞康（渠道商）	\N	2025-09-30	0	\N	\N	2025-08-11 02:49:30.383232	2025-08-11 10:49:30.433884	12	f	\N	\N	\N	t	2025-08-11 02:49:30.383232	\N	2	0	datacenter	[]	f
8	MyO2	2025-07-14	sales_focus	sales	controlled					FMTCS SOLUTIONS PTE. LTD	quoted		SPJ202507-002	\N	11748.119999999999	\N	\N	2025-07-09 01:33:32.244617	2025-08-12 14:44:45.085284	12	f	\N	\N	\N	t	2025-07-09 01:33:32.244617	\N	2	0		[]	f
31	TM Iskandar Puteri Data Centre (IPDC)	\N	business_opportunity	sales	not_required					TM Technology Service Sdn Bhd 	discover		\N	\N	0	\N	\N	2025-08-12 08:00:26.602643	2025-08-12 16:01:16.436319	2	f	\N	\N	\N	t	2025-08-12 08:00:26.602643	\N	2	0	datacenter	[]	f
13	CTP - B1\\B2 - GDS Data Centre @ Chonburi Thailand 	\N	channel_follow	channel	qualified	GDS Data Center @ Thailand		FMTCS SOLUTIONS PTE. LTD		Longmotive (M) Sdn. Bhd.	paused	目前已经确认朗茂中标，向下寻找系统集成商，目前配合了曹磊和仵磊两家单位	\N	2025-10-15	152585.3	\N	\N	2025-07-22 07:35:34.62831	2025-08-11 03:45:26.360397	12	f	\N	\N	\N	t	2025-07-22 07:35:34.62831	\N	3	0	datacenter	[1, 2, 3, 5, 10, 11]	t
27	AirTrunk	\N	sales_focus	sales	qualified	AirTrunk Malaysia Sdn Bhd					awarded		\N	\N	22505.997	\N	\N	2025-08-07 07:33:04.807869	2025-08-13 02:38:39.238309	7	f	\N	\N	\N	t	2025-08-07 07:33:04.807869	\N	1	0	datacenter	[]	f
32	Demonstration Set	\N	sales_focus	sales				Mot Smart Solutions Company Limited (Head office)			discover		\N	\N	32060.899999999998	\N	\N	2025-08-14 07:48:22.924461	2025-08-15 02:28:10.149544	2	f	\N	\N	\N	t	2025-08-14 07:48:22.924461	\N	2	0	other	[]	f
\.


--
-- TOC entry 4835 (class 0 OID 24286)
-- Dependencies: 361
-- Data for Name: purchase_order_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.purchase_order_details (id, order_id, product_id, product_name, product_model, product_desc, brand, quantity, unit, unit_price, discount, total_price, received_quantity, notes) FROM stdin;
\.


--
-- TOC entry 4837 (class 0 OID 24292)
-- Dependencies: 363
-- Data for Name: purchase_orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.purchase_orders (id, order_number, company_id, order_type, order_date, expected_date, status, total_amount, total_quantity, currency, payment_terms, delivery_address, description, created_by_id, approved_by_id, approved_at, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4839 (class 0 OID 24298)
-- Dependencies: 365
-- Data for Name: quotation_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.quotation_details (id, quotation_id, product_name, product_model, product_desc, brand, unit, quantity, discount, market_price, unit_price, total_price, product_mn, created_at, updated_at, implant_subtotal, currency, original_market_price, converted_market_price) FROM stdin;
273	10	Repeater	Mark1000 MAX	Frequency range: 400-470MHz    Channel spacing: 12.5kHz/25kHz    Max channel: 16    Max Power: 25W    Mode: DMR    NetFunction: NetFlex Cloud	Evertac Solutions	set	2	1.2	3290	3948	7896	PS4MS2NN	2025-07-09 00:51:25.646284	2025-07-09 00:51:25.646286	6580	USD	\N	\N
274	10	RF Combiner	E-FH400-2	UHF2   440-470MHz   2-Port   Insertion loss≤ 4.0 dB  IP40  N-Female  2U	Evertac Solutions	set	1	1.2	1000	1200	1200	SGM1B022CZ1	2025-07-09 00:51:25.652153	2025-07-09 00:51:25.652155	1000	USD	\N	\N
275	10	RF Multi-Coupler	E-JF350/400-2	UHF   350-470MHz   2-Port   Insertion loss≤ 3.5dB  IP40  N-Female  1U	Evertac Solutions	set	1	1.2	509	610.8	610.8	SGDE1BU2XCZ1	2025-07-09 00:51:25.657056	2025-07-09 00:51:25.657058	509	USD	\N	\N
276	10	Duplex	E-SGQ400D	UHF2   440-470MHz   2-5MHz   2U	Evertac Solutions	set	1	1.2	1460	1752	1752	SGDULB4H1CZ1	2025-07-09 00:51:25.661712	2025-07-09 00:51:25.661714	1460	USD	\N	\N
277	10	DownLink Multi-Splitter	R-EVDC-BLST-D	UHF1  350-470MHz    6+1-Port   Max Input Power 50W   Insertion loss≤0.5dB  N-Female  1U	Evertac Solutions	set	1	1.2	800	960	960	SGE1AD6xCZ1	2025-07-09 00:51:25.705957	2025-07-09 00:51:25.705959	800	USD	\N	\N
278	10	UpLink Multi-Splitter	R-EVDC-BLST-U	UHF1   350-470MHz   6+1-Port   Max Input Power 50W   Insertion loss≤ 0.5dB  N-Female  1U	Evertac Solutions	set	1	1.2	800	960	960	SGE1AU6xCZ1	2025-07-09 00:51:25.711464	2025-07-09 00:51:25.711466	800	USD	\N	\N
279	10	OMU	DRFS-400/M	400-470MHz   BW 20M   32OP   2U   Digital transmit   NetFLEX	Evertac Solutions	set	1	1.2	5455	6546	6546	SGR2DI040	2025-07-09 00:51:25.718032	2025-07-09 00:51:25.718034	5455	USD	\N	\N
280	10	ORU	DRFT-BDA410/M	400-470MHz   BW 4M   40dBm/10W   2U   Digital transimit   NetFLEX	Evertac Solutions	set	6	1.2	10455	12546	75276	SGR3DI340	2025-07-09 00:51:25.725366	2025-07-09 00:51:25.725368	62730	USD	\N	\N
281	10	Cable Feed Modular	FDPower400	modular install in ORU via RF cable to feed power	Evertac Solutions	set	6	1.2	345	414	2484	SGGF20000	2025-07-09 00:51:25.731197	2025-07-09 00:51:25.731199	2070	USD	\N	\N
282	10	Smart Indoor Antenna	MA11	UHF   350-470MHz   Max Input Power 50W   Gain 0dBi   Signal detection 	Evertac Solutions	set	78	1.2	45	54	4212	SGAIOCL4Y	2025-07-09 00:51:25.736932	2025-07-09 00:51:25.736934	3510	USD	\N	\N
283	10	Fiber Glass Omni Antenna	E-ANTG 400	UHF   450-470MHz   Max Input Power 50W   5dBi	Evertac Solutions	set	1	1.2	100	120	120	SGANLOMO5HR1	2025-07-09 00:51:25.745072	2025-07-09 00:51:25.745073	100	USD	\N	\N
284	10	Splitter	MAPD-2	350-470MHz   MIP 50W   CFP	Evertac Solutions	set	34	1.2	55	66	2244	SGCDF24Y	2025-07-09 00:51:25.750093	2025-07-09 00:51:25.750094	1870	USD	\N	\N
285	10	Coupler	MADC-6	350-470MHz   MIP 50W   CP 6dB   CFP	Evertac Solutions	set	40	1.2	55	66	2640	SGCCF34Y	2025-07-09 00:51:25.757092	2025-07-09 00:51:25.757094	2200	USD	\N	\N
286	10	Coaxial Dummy Load	E-TF50	50w 300-1000MHz dummy load  N male connector	Third party	set	2	1.2	41	49.199999999999996	98.39999999999999	W000163	2025-07-09 00:51:25.761532	2025-07-09 00:51:25.761533	0	USD	\N	\N
287	10	Fiber rack	ST/FC  24口	Standard FC type 24 port cabinet installation	Third party	set	1	1.2	96	115.19999999999999	115.19999999999999	EDFWYFC24W	2025-07-09 00:51:25.766322	2025-07-09 00:51:25.766323	0	USD	\N	\N
288	10	Fiber rack	ST/FC  4口	Standard FC type 4 port wall-mounted installation	Third party	set	6	1.2	42	50.4	302.4	EDFWYFC04O	2025-07-09 00:51:25.805142	2025-07-09 00:51:25.805144	0	USD	\N	\N
289	10	Optical Fiber Jumper Cable Patch Cord	MNOFHC-SMD-50	LC to LC UPC Duplex Single Mode Fiber Patch Cable   5m (16ft)	Third party	set	12	1.2	4.1	4.919999999999999	59.03999999999999	EJUWY05A40LC	2025-07-09 00:51:25.809933	2025-07-09 00:51:25.809935	0	USD	\N	\N
290	10	Optical Fiber	GYXTH-4B1 4芯	4 core outdoor single mode smoke flame retardant	Third party	meter	2400	1.2	1.23	1.476	3542.4	ECAWYGYXTH0401	2025-07-09 00:51:25.814446	2025-07-09 00:51:25.814447	0	USD	\N	\N
291	10	Light arrestor	CA-23RS	0-1000MHz 700W 50Ω N-Female	Third party	set	1	1.2	58	69.6	69.6	OBJANOTHS01	2025-07-09 00:51:25.819079	2025-07-09 00:51:25.81908	0	USD	\N	\N
292	10	RF cable	HCAAYZ -50-12	1/2＂50Ω	Third party	meter	3200	1.2	2.8	3.36	10752	OZCH221035	2025-07-09 00:51:25.824643	2025-07-09 00:51:25.824645	0	USD	\N	\N
293	10	Connector adapter	N-J1/2	1/2＂N-J	Third party	set	320	1.2	2.5	3	960	OCIN5JZALC1	2025-07-09 00:51:25.829168	2025-07-09 00:51:25.829169	0	USD	\N	\N
294	10	Connector adapter	N-50KK	N-KK	Third party	set	20	1.2	2.5	3	60	OCIN5KZALC1	2025-07-09 00:51:25.835539	2025-07-09 00:51:25.835542	0	USD	\N	\N
295	10	Connector adapter	N-50JKW	90 Degree N-JK	Third party	set	50	1.2	2.5	3	150	OCIN5JWALC1	2025-07-09 00:51:25.840692	2025-07-09 00:51:25.840694	0	USD	\N	\N
296	10	Jumper Cable	E-JP50-7	0.5m/1.6ft  N-JJ for Antenna	Third party	set	20	1.2	9	10.799999999999999	215.99999999999997	OISKHB1JLC1	2025-07-09 00:51:25.846122	2025-07-09 00:51:25.846124	0	USD	\N	\N
297	10	Jumper Cable	NJ/NJ-3 	1.5m/4.7ft N-JJ for Cabinet	Third party	set	12	1.2	6.8	8.16	97.92	EJUMJK4315NJNJ	2025-07-09 00:51:25.850636	2025-07-09 00:51:25.850637	0	USD	\N	\N
298	10	Cabinet	Standard	19 -inch standard 42U with cooling	Third party	set	1	1.2	500	600	600	EJUMJK4315NJQJ	2025-07-09 00:51:25.855165	2025-07-09 00:51:25.855166	0	USD	\N	\N
299	10	Cabinet	Standard	RS PRO 6U-Rack Server Cabinet	Third party	set	6	1.2	260	312	1872	EJUMJK4314NJQJ	2025-07-09 00:51:25.859483	2025-07-09 00:51:25.859484	0	USD	\N	\N
300	10	Two-way radio	PNR2000	Frequency range: 400MHz    Mode: DMR    Voltage: 3.8V    Function: BlueTooth/iBeacon    Interface.: No-keyboard screen	Evertac Solutions	set	40	1.2	290	348	13920	TS4D3NMK	2025-07-09 00:51:25.864234	2025-07-09 00:51:25.864236	11600	USD	\N	\N
335	11	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 10MHz  33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	2	1.15	2640	3035.9999999999995	6071.999999999999	SGR3SI140	2025-07-09 01:46:53.315631	2025-07-09 01:46:53.315633	5280	USD	\N	\N
336	11	Fiber Glass Omni Antenna	E-ANTG 400	UHF   450-470MHz   Max Input Power 50W   5dBi	Evertac Solutions	set	2	1.15	100	114.99999999999999	229.99999999999997	SGANLOMO5HR1	2025-07-09 01:46:53.320928	2025-07-09 01:46:53.32093	200	USD	\N	\N
368	12	Repeater	Mark1000 MAX	Frequency range: 400-470MHz    Channel spacing: 12.5kHz/25kHz    Max channel: 16    Max Power: 25W    Mode: DMR    NetFunction: NetFlex Cloud	Evertac Solutions	set	3	1.266	3290	4165.14	12495.420000000002	PS4MS2NN	2025-07-22 07:14:37.482693	2025-07-22 07:14:37.482695	9870	USD	\N	\N
369	12	RF Combiner	E-FH400-2	UHF2   440-470MHz   2-Port   Insertion loss≤ 4.0 dB  IP40  N-Female  2U	Evertac Solutions	set	1	1.7480000000000002	1000	1748.0000000000002	1748.0000000000002	SGM1B022CZ1	2025-07-22 07:14:37.487964	2025-07-22 07:14:37.487966	1000	USD	\N	\N
370	12	RF Multi-Coupler	E-JF350/400-2	UHF   350-470MHz   2-Port   Insertion loss≤ 3.5dB  IP40  N-Female  1U	Evertac Solutions	set	1	2.377	509	1209.8929999999998	1209.8929999999998	SGDE1BU2XCZ1	2025-07-22 07:14:37.492959	2025-07-22 07:14:37.492961	509	USD	\N	\N
371	12	Duplex	E-SGQ400N	UFH2   440-470MHz   0.5Mhz   1U	Evertac Solutions	set	1	1.7990000000000002	700	1259.3000000000002	1259.3000000000002	SGULN4N1CZ1	2025-07-22 07:14:37.497934	2025-07-22 07:14:37.497936	700	USD	\N	\N
372	12	DownLink Multi-Splitter	R-EVDC-BLST-D	UHF1  350-470MHz    6+1-Port   Max Input Power 50W   Insertion loss≤0.5dB  N-Female  1U	Evertac Solutions	set	2	1.246	800	996.8	1993.6	SGE1AD6xCZ1	2025-07-22 07:14:37.503033	2025-07-22 07:14:37.503034	1600	USD	\N	\N
190	9	Repeater	Mark1000 MAX	Frequency range: 400-470MHz    Channel spacing: 12.5kHz/25kHz    Max channel: 16    Max Power: 25W    Mode: DMR    NetFunction: NetFlex Cloud	Evertac Solutions	set	1	1.25	3290	4112.5	4112.5	PS4MS2NN	2025-06-30 09:41:02.37764	2025-06-30 09:41:02.377643	3290	USD	\N	\N
191	9	Duplex	E-SGQ400D	UHF2   440-470MHz   2-5MHz   2U	Evertac Solutions	set	1	1.25	1460	1825	1825	SGDULB4H1CZ1	2025-06-30 09:41:02.382885	2025-06-30 09:41:02.382888	1460	USD	\N	\N
192	9	DownLink Multi-Splitter	R-EVDC-BLST-D	UHF1  350-470MHz    6+1-Port   Max Input Power 50W   Insertion loss≤0.5dB  N-Female  1U	Evertac Solutions	set	1	1.25	800	1000	1000	SGE1AD6xCZ1	2025-06-30 09:41:02.387836	2025-06-30 09:41:02.387838	800	USD	\N	\N
193	9	UpLink Multi-Splitter	R-EVDC-BLST-U	UHF1   350-470MHz   6+1-Port   Max Input Power 50W   Insertion loss≤ 0.5dB  N-Female  1U	Evertac Solutions	set	1	1.25	800	1000	1000	SGE1AU6xCZ1	2025-06-30 09:41:02.401305	2025-06-30 09:41:02.401307	800	USD	\N	\N
194	9	OMU	RFS-400 LT/M	350-470MHz   BW 15MHz   4FP   NetFLEX 	Evertac Solutions	set	1	1.25	1890	2362.5	2362.5	SGR2SI030	2025-06-30 09:41:02.407076	2025-06-30 09:41:02.407079	1890	USD	\N	\N
195	9	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 5MHz   33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	2	1.25	2640	3300	6600	SGR3SI14S	2025-06-30 09:41:02.413112	2025-06-30 09:41:02.413115	5280	USD	\N	\N
196	9	Cable Feed Modular	FDPower400	modular install in ORU via RF cable to feed power	Evertac Solutions	set	2	1.25	345	431.25	862.5	SGGF20000	2025-06-30 09:41:02.418833	2025-06-30 09:41:02.418835	690	USD	\N	\N
197	9	Smart Indoor Antenna	MA11	UHF   350-470MHz   Max Input Power 50W   Gain 0dBi   Signal detection 	Evertac Solutions	set	17	1.25	45	56.25	956.25	SGAIOCL4Y	2025-06-30 09:41:02.424959	2025-06-30 09:41:02.424961	765	USD	\N	\N
198	9	Fiber Glass Omni Antenna	E-ANTG 400	UHF   450-470MHz   Max Input Power 50W   5dBi	Evertac Solutions	set	2	1.25	100	125	250	SGANLOMO5HR1	2025-06-30 09:41:02.430696	2025-06-30 09:41:02.430698	200	USD	\N	\N
199	9	Splitter	MAPD-2	350-470MHz   MIP 50W   CFP	Evertac Solutions	set	5	1.25	55	68.75	343.75	SGCDF24Y	2025-06-30 09:41:02.437743	2025-06-30 09:41:02.437745	275	USD	\N	\N
200	9	Coupler	MADC-6	350-470MHz   MIP 50W   CP 6dB   CFP	Evertac Solutions	set	12	1.25	55	68.75	825	SGCCF34Y	2025-06-30 09:41:02.447951	2025-06-30 09:41:02.447954	660	USD	\N	\N
201	9	Fiber rack	ST/FC  24口	Standard FC type 24 port cabinet installation	Third party	set	1	1.25	96	120	120	EDFWYFC24W	2025-06-30 09:41:02.45646	2025-06-30 09:41:02.456464	0	USD	\N	\N
202	9	Fiber rack	ST/FC  4口	Standard FC type 4 port wall-mounted installation	Third party	set	1	1.25	42	52.5	52.5	EDFWYFC04O	2025-06-30 09:41:02.463929	2025-06-30 09:41:02.463932	0	USD	\N	\N
203	9	Optical Fiber	GYXTH-4B1 4芯	4 core outdoor single mode smoke flame retardant	Third party	meter	250	1.25	1.23	1.5375	384.375	ECAWYGYXTH0401	2025-06-30 09:41:02.470947	2025-06-30 09:41:02.47095	0	USD	\N	\N
204	9	Light arrestor	CA-23RS	0-1000MHz 700W 50Ω N-Female	Third party	set	1	1.25	58	72.5	72.5	OBJANOTHS01	2025-06-30 09:41:02.476822	2025-06-30 09:41:02.476825	0	USD	\N	\N
205	9	Mounting brackets	MONT80	50cm L type	Third party	set	1	1.25	54	67.5	67.5	OBJANOTGR01	2025-06-30 09:41:02.482225	2025-06-30 09:41:02.482227	0	USD	\N	\N
206	9	RF cable	HCAAYZ -50-12	1/2＂50Ω	Third party	meter	850	1.25	2.8	3.5	2975	OZCH221035	2025-06-30 09:41:02.489407	2025-06-30 09:41:02.48941	0	USD	\N	\N
207	9	Connector adapter	N-J1/2	1/2＂N-J	Third party	set	68	1.25	2.5	3.125	212.5	OCIN5JZALC1	2025-06-30 09:41:02.497413	2025-06-30 09:41:02.497415	0	USD	\N	\N
208	9	Connector adapter	N-50KK	N-KK	Third party	set	5	1.25	2.5	3.125	15.625	OCIN5KZALC1	2025-06-30 09:41:02.505379	2025-06-30 09:41:02.505381	0	USD	\N	\N
209	9	Connector adapter	N-50JKW	90 Degree N-JK	Third party	set	11	1.25	2.5	3.125	34.375	OCIN5JWALC1	2025-06-30 09:41:02.512307	2025-06-30 09:41:02.512309	0	USD	\N	\N
210	9	Jumper Cable	E-JP50-7	0.5m/1.6ft  N-JJ for Antenna	Third party	set	4	1.25	9	11.25	45	OISKHB1JLC1	2025-06-30 09:41:02.517764	2025-06-30 09:41:02.517766	0	USD	\N	\N
211	9	Jumper Cable	NJ/NJ-3 	1.5m/4.7ft N-JJ for Cabinet	Third party	set	7	1.25	6.8	8.5	59.5	EJUMJK4315NJNJ	2025-06-30 09:41:02.523487	2025-06-30 09:41:02.523489	0	USD	\N	\N
212	9	Cabinet	Standard	19 -inch standard 42U with cooling	Third party	set	1	1.25	500	625	625	EJUMJK4315NJQJ	2025-06-30 09:41:02.532238	2025-06-30 09:41:02.53224	0	USD	\N	\N
213	9	Two-way radio	PNR2000	Frequency range: 400MHz    Mode: DMR    Voltage: 3.8V    Function: BlueTooth/iBeacon    Interface.: No-keyboard screen	Evertac Solutions	set	30	1.25	290	362.5	10875	TS4D3NMK	2025-06-30 09:41:02.540707	2025-06-30 09:41:02.540709	8700	USD	\N	\N
214	9	Multi-Charging Hub	CMP2600	6-way walkie-talkie/battery charging combination   featuring battery management and NetFlex cloud management capabilities	Evertac Solutions	set	1	1.25	320	400	400	ZSTZN0N	2025-06-30 09:41:02.548074	2025-06-30 09:41:02.548076	320	USD	\N	\N
373	12	UpLink Multi-Splitter	R-EVDC-BLST-U	UHF1   350-470MHz   6+1-Port   Max Input Power 50W   Insertion loss≤ 0.5dB  N-Female  1U	Evertac Solutions	set	2	1.2209999999999999	800	976.7999999999998	1953.5999999999997	SGE1AU6xCZ1	2025-07-22 07:14:37.507528	2025-07-22 07:14:37.50753	1600	USD	\N	\N
374	12	OMU	RFS-400 LT/M	350-470MHz   BW 15MHz   4FP   NetFLEX 	Evertac Solutions	set	2	1.208	1890	2283.12	4566.24	SGR2SI030	2025-07-22 07:14:37.512009	2025-07-22 07:14:37.51201	3780	USD	\N	\N
375	12	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 10MHz  33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	7	1.27	2640	3352.8	23469.600000000002	SGR3SI140	2025-07-22 07:14:37.516373	2025-07-22 07:14:37.516375	18480	USD	\N	\N
376	12	Indoor Antenna	MA10	UHF   350-470MHz   Max Input Power 50W   0dBi	Evertac Solutions	set	150	1.256	25	31.4	4710	SGAIOCN4Y	2025-07-22 07:14:37.521047	2025-07-22 07:14:37.521049	3750	USD	\N	\N
377	12	Panel Antenna	E-ANTD 400	UHF   450-470MHz   Max Input Power 50W   Gain 2dBi	Evertac Solutions	set	2	1.374	80	109.92000000000002	219.84000000000003	SGAN2OFD2TE2	2025-07-22 07:14:37.525477	2025-07-22 07:14:37.525479	160	USD	\N	\N
378	12	Fiber Glass Omni Antenna	E-ANTG 400	UHF   450-470MHz   Max Input Power 50W   5dBi	Evertac Solutions	set	1	1.578	100	157.8	157.8	SGANLOMO5HR1	2025-07-22 07:14:37.530027	2025-07-22 07:14:37.530028	100	USD	\N	\N
379	12	Splitter	EVPD-2 LT	80-470MHz   MIP 50W	Evertac Solutions	set	50	1.232	25	30.8	1540	SGCDN24Y	2025-07-22 07:14:37.534731	2025-07-22 07:14:37.534733	1250	USD	\N	\N
380	12	Coupler	EVDC-6 LT	350-470MHz   MIP 50W   CP 6dB	Evertac Solutions	set	100	1.232	25	30.8	3080	SGCCN34Y	2025-07-22 07:14:37.539661	2025-07-22 07:14:37.539662	2500	USD	\N	\N
381	12	Two-way radio	PNR2000	Frequency range: 400MHz    Mode: DMR    Voltage: 3.8V    Function: BlueTooth/iBeacon    Interface.: No-keyboard screen	Evertac Solutions	set	60	1.33	290	385.70000000000005	23142.000000000004	TS4D3NMK	2025-07-22 07:14:37.544773	2025-07-22 07:14:37.544775	17400	USD	\N	\N
382	12	Multi-Charging Hub	CMP2600	6-way walkie-talkie/battery charging combination   featuring battery management and NetFlex cloud management capabilities	Evertac Solutions	set	2	1.235	320	395.20000000000005	790.4000000000001	ZSTZN0N	2025-07-22 07:14:37.549758	2025-07-22 07:14:37.54976	640	USD	\N	\N
493	13	Repeater	Mark1000 MAX	Frequency range: 400-470MHz    Channel spacing: 12.5kHz/25kHz    Max channel: 16    Max Power: 25W    Mode: DMR    NetFunction: NetFlex Cloud	Evertac Solutions	set	2	1.266	3290	4165.14	8330.28	PS4MS2NN	2025-07-22 08:25:41.517802	2025-07-22 08:25:41.517804	6580	USD	\N	\N
494	13	RF Combiner	E-FH400-2	UHF2   440-470MHz   2-Port   Insertion loss≤ 4.0 dB  IP40  N-Female  2U	Evertac Solutions	set	1	1.7480000000000002	1000	1748.0000000000002	1748.0000000000002	SGM1B022CZ1	2025-07-22 08:25:41.522893	2025-07-22 08:25:41.522895	1000	USD	\N	\N
495	13	RF Multi-Coupler	E-JF350/400-2	UHF   350-470MHz   2-Port   Insertion loss≤ 3.5dB  IP40  N-Female  1U	Evertac Solutions	set	1	2.377	509	1209.8929999999998	1209.8929999999998	SGDE1BU2XCZ1	2025-07-22 08:25:41.528144	2025-07-22 08:25:41.528146	509	USD	\N	\N
496	13	Duplex	E-SGQ400N	UFH2   440-470MHz   0.5Mhz   1U	Evertac Solutions	set	1	1.7990000000000002	700	1259.3000000000002	1259.3000000000002	SGULN4N1CZ1	2025-07-22 08:25:41.533236	2025-07-22 08:25:41.533238	700	USD	\N	\N
497	13	DownLink Multi-Splitter	R-EVDC-BLST-D	UHF1  350-470MHz    6+1-Port   Max Input Power 50W   Insertion loss≤0.5dB  N-Female  1U	Evertac Solutions	set	1	1.246	800	996.8	996.8	SGE1AD6xCZ1	2025-07-22 08:25:41.538217	2025-07-22 08:25:41.538219	800	USD	\N	\N
498	13	UpLink Multi-Splitter	R-EVDC-BLST-U	UHF1   350-470MHz   6+1-Port   Max Input Power 50W   Insertion loss≤ 0.5dB  N-Female  1U	Evertac Solutions	set	1	1.2209999999999999	800	976.7999999999998	976.7999999999998	SGE1AU6xCZ1	2025-07-22 08:25:41.543198	2025-07-22 08:25:41.543201	800	USD	\N	\N
499	13	OMU	RFS-400 LT/M	350-470MHz   BW 15MHz   4FP   NetFLEX 	Evertac Solutions	set	4	1.208	1890	2283.12	9132.48	SGR2SI030	2025-07-22 08:25:41.54832	2025-07-22 08:25:41.548322	7560	USD	\N	\N
500	13	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 10MHz  33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	15	1.27	2640	3352.8	50292	SGR3SI140	2025-07-22 08:25:41.553465	2025-07-22 08:25:41.553467	39600	USD	\N	\N
501	13	Cable Feed Modular	FDPower400	modular install in ORU via RF cable to feed power	Evertac Solutions	set	18	1.25	345	431.25	7762.5	SGGF20000	2025-07-22 08:25:41.558625	2025-07-22 08:25:41.558628	6210	USD	\N	\N
502	13	Smart Indoor Antenna	MA11	UHF   350-470MHz   Max Input Power 50W   Gain 0dBi   Signal detection 	Evertac Solutions	set	331	1.166	45	52.47	17367.57	SGAIOCL4Y	2025-07-22 08:25:41.563961	2025-07-22 08:25:41.563963	14895	USD	\N	\N
503	13	Panel Antenna	E-ANTD 400	UHF   450-470MHz   Max Input Power 50W   Gain 2dBi	Evertac Solutions	set	2	1.374	80	109.92000000000002	219.84000000000003	SGAN2OFD2TE2	2025-07-22 08:25:41.569183	2025-07-22 08:25:41.569185	160	USD	\N	\N
504	13	Fiber Glass Omni Antenna	E-ANTG 400	UHF   450-470MHz   Max Input Power 50W   5dBi	Evertac Solutions	set	3	1.578	100	157.8	473.40000000000003	SGANLOMO5HR1	2025-07-22 08:25:41.574454	2025-07-22 08:25:41.574456	300	USD	\N	\N
505	13	Splitter	MAPD-2	350-470MHz   MIP 50W   CFP	Evertac Solutions	set	135	1.1909999999999998	55	65.505	8843.175	SGCDF24Y	2025-07-22 08:25:41.579493	2025-07-22 08:25:41.579495	7425	USD	\N	\N
506	13	Coupler	MADC-6	350-470MHz   MIP 50W   CP 6dB   CFP	Evertac Solutions	set	200	1.1909999999999998	55	65.505	13101	SGCCF34Y	2025-07-22 08:25:41.611715	2025-07-22 08:25:41.611717	11000	USD	\N	\N
507	13	Access License	LS-NFX-BDA	ORU access to NetFLEX License	Evertac Solutions	set	15	1.003	360	361.08	5416.2	HYWSRNB1	2025-07-22 08:25:41.619717	2025-07-22 08:25:41.619719	5400	USD	\N	\N
508	13	Access License	LS-NFX-RPT	Repeater access to NetFLex License	Evertac Solutions	set	2	1.002	600	601.2	1202.4	HYWSPNB1	2025-07-22 08:25:41.626194	2025-07-22 08:25:41.626197	1200	USD	\N	\N
509	13	Access License	LS-NFX-RAD	Two-way radio access to NetFLEX License	Evertac Solutions	set	40	1.022	45	45.99	1839.6000000000001	HYWSTNB1	2025-07-22 08:25:41.631985	2025-07-22 08:25:41.631988	1800	USD	\N	\N
510	13	Gateway application	NFX_GATW	Synchronize setup configure system managment driver update online	Evertac Solutions	set	1	1.25	3050	3812.5	3812.5	HYWG0NB1	2025-07-22 08:25:41.637123	2025-07-22 08:25:41.637125	3050	USD	\N	\N
511	13	Operation DashBoard	ACC-CWT	System Health analyz   System diagram online Fault Notification  Equipment location 	Evertac Solutions	set	1	1.001	1600	1601.6	1601.6	HYWF0NA1	2025-07-22 08:25:41.642112	2025-07-22 08:25:41.642113	1600	USD	\N	\N
512	13	Service Operation Tool	ACC-NUT	Tracking and notification system faults to the app   providing standard maintenance process	Evertac Solutions	set	1	1.002	780	781.56	781.56	HYWT0NA1	2025-07-22 08:25:41.646864	2025-07-22 08:25:41.646865	780	USD	\N	\N
513	13	Two-way radio	PNR2000	Frequency range: 400MHz    Mode: DMR    Voltage: 3.8V    Function: BlueTooth/iBeacon    Interface.: No-keyboard screen	Evertac Solutions	set	40	1.33	290	385.70000000000005	15428.000000000002	TS4D3NMK	2025-07-22 08:25:41.651941	2025-07-22 08:25:41.651944	11600	USD	\N	\N
514	13	Multi-Charging Hub	CMP2600	6-way walkie-talkie/battery charging combination   featuring battery management and NetFlex cloud management capabilities	Evertac Solutions	set	2	1.235	320	395.20000000000005	790.4000000000001	ZSTZN0N	2025-07-22 08:25:41.65688	2025-07-22 08:25:41.656882	640	USD	\N	\N
532	14	Duplex	E-SGQ400N	UFH2   440-470MHz   0.5Mhz   1U	Evertac Solutions	set	1	1	700	700	700	SGULN4N1CZ1	2025-07-29 01:35:37.315166	2025-07-29 01:35:37.315167	700	USD	\N	\N
533	14	DownLink Multi-Splitter	R-EVDC-BLST-D	UHF1  350-470MHz    6+1-Port   Max Input Power 50W   Insertion loss≤0.5dB  N-Female  1U	Evertac Solutions	set	1	1	800	800	800	SGE1AD6xCZ1	2025-07-29 01:35:37.319974	2025-07-29 01:35:37.319975	800	USD	\N	\N
534	14	UpLink Multi-Splitter	R-EVDC-BLST-U	UHF1   350-470MHz   6+1-Port   Max Input Power 50W   Insertion loss≤ 0.5dB  N-Female  1U	Evertac Solutions	set	1	1	800	800	800	SGE1AU6xCZ1	2025-07-29 01:35:37.324802	2025-07-29 01:35:37.324804	800	USD	\N	\N
535	14	OMU	RFS-400 LT/M	350-470MHz   BW 15MHz   4FP   NetFLEX 	Evertac Solutions	set	2	1	1890	1890	3780	SGR2SI030	2025-07-29 01:35:37.331241	2025-07-29 01:35:37.331242	3780	USD	\N	\N
536	15	RF Combiner	E-FH400-8	UHF2   440-470MHz   8-Port   Insertion loss≤11.0 dB  IP40  N-Female  2U	Evertac Solutions	set	1	1	2950	1917.5	1917.5	SGCM1B082CZ1	2025-07-29 08:28:49.710402	2025-07-29 08:28:49.710404	2950	USD	\N	\N
537	15	RF Multi-Coupler	E-JF350/400-8	UHF   350-470MHz   8-Port   Insertion loss≤ 9.5dB  IP40  N-Female  1U	Evertac Solutions	set	1	1	1020	663	663	SGDE1BU8XCZ1	2025-07-29 08:28:49.811746	2025-07-29 08:28:49.811749	1020	USD	\N	\N
538	15	DownLink Multi-Splitter	R-EVDC-BLST-D	UHF1  350-470MHz    6+1-Port   Max Input Power 50W   Insertion loss≤0.5dB  N-Female  1U	Evertac Solutions	set	1	1	800	520	520	SGE1AD6xCZ1	2025-07-29 08:28:49.821837	2025-07-29 08:28:49.821839	800	USD	\N	\N
539	15	UpLink Multi-Splitter	R-EVDC-BLST-U	UHF1   350-470MHz   6+1-Port   Max Input Power 50W   Insertion loss≤ 0.5dB  N-Female  1U	Evertac Solutions	set	1	1	800	520	520	SGE1AU6xCZ1	2025-07-29 08:28:49.831223	2025-07-29 08:28:49.831225	800	USD	\N	\N
540	15	OMU	DRFS-400/M	400-470MHz   BW 20M   32OP   2U   Digital transmit   NetFLEX	Evertac Solutions	set	2	1	5455	3545.75	7091.5	SGR2DI040	2025-07-29 08:28:49.839806	2025-07-29 08:28:49.839807	10910	USD	\N	\N
541	15	ORU	DRFT-BDA410/M	400-470MHz   BW 4M   40dBm/10W   2U   Digital transimit   NetFLEX	Evertac Solutions	set	36	1	10455	6795.75	244647	SGR3DI340	2025-07-29 08:28:49.848178	2025-07-29 08:28:49.84818	376380	USD	\N	\N
542	15	Indoor Antenna	MA10	UHF   350-470MHz   Max Input Power 50W   0dBi	Evertac Solutions	set	528	1	25	16.25	8580	SGAIOCN4Y	2025-07-29 08:28:49.856492	2025-07-29 08:28:49.856493	13200	USD	\N	\N
543	15	Splitter	MAPD-2	350-470MHz   MIP 50W   CFP	Evertac Solutions	set	176	1	55	35.75	6292	SGCDF24Y	2025-07-29 08:28:49.864959	2025-07-29 08:28:49.864961	9680	USD	\N	\N
544	15	Coupler	MADC-6	350-470MHz   MIP 50W   CP 6dB   CFP	Evertac Solutions	set	352	1	55	35.75	12584	SGCCF34Y	2025-07-29 08:28:49.914115	2025-07-29 08:28:49.914117	19360	USD	\N	\N
545	15	Connector adapter	N-J1/2	1/2＂N-J	Third party	set	2112	1	2.5	3	6336	OCIN5JZALC1	2025-07-29 08:28:49.925545	2025-07-29 08:28:49.925546	0	USD	\N	\N
546	15	Connector adapter	N-50KK	N-KK	Third party	set	111	1	2.5	3	333	OCIN5KZALC1	2025-07-29 08:28:49.936169	2025-07-29 08:28:49.936172	0	USD	\N	\N
547	15	Connector adapter	N-50JKW	90 Degree N-JK	Third party	set	317	1	2.5	3	951	OCIN5JWALC1	2025-07-29 08:28:49.945064	2025-07-29 08:28:49.945066	0	USD	\N	\N
548	15	Jumper Cable	E-JP50-7	0.5m/1.6ft  N-JJ for Antenna	Third party	set	106	1	9	10.799999999999999	1144.8	OISKHB1JLC1	2025-07-29 08:28:49.953897	2025-07-29 08:28:49.953898	0	USD	\N	\N
549	15	Jumper Cable	NJ/NJ-3 	1.5m/4.7ft N-JJ for Cabinet	Third party	set	14	1	6.8	8.16	114.24000000000001	EJUMJK4315NJNJ	2025-07-29 08:28:49.962403	2025-07-29 08:28:49.962405	0	USD	\N	\N
550	15	Fiber rack	ST/FC  24口	Standard FC type 24 port cabinet installation	Third party	set	6	1	96	115.19999999999999	691.1999999999999	EDFWYFC24W	2025-07-29 08:28:49.971893	2025-07-29 08:28:49.971894	0	USD	\N	\N
551	15	Fiber rack	ST/FC  4口	Standard FC type 4 port wall-mounted installation	Third party	set	36	1	42	50.4	1814.3999999999999	EDFWYFC04O	2025-07-29 08:28:50.018379	2025-07-29 08:28:50.018382	0	USD	\N	\N
552	15	Optical Fiber Jumper Cable Patch Cord	MNOFHC-SMD-50	LC to LC UPC Duplex Single Mode Fiber Patch Cable   5m (16ft)	Third party	set	72	1	4.1	4.919999999999999	354.23999999999995	EJUWY05A40LC	2025-07-29 08:28:50.029201	2025-07-29 08:28:50.029203	0	USD	\N	\N
331	11	RF Combiner	E-FH400-2	UHF2   440-470MHz   2-Port   Insertion loss≤ 4.0 dB  IP40  N-Female  2U	Evertac Solutions	set	1	1.1	1000	1100	1100	SGM1B022CZ1	2025-07-09 01:46:53.294942	2025-07-09 01:46:53.294945	1000	USD	\N	\N
332	11	RF Multi-Coupler	E-JF350/400-2	UHF   350-470MHz   2-Port   Insertion loss≤ 3.5dB  IP40  N-Female  1U	Evertac Solutions	set	1	1.291	509	657.1189999999999	657.1189999999999	SGDE1BU2XCZ1	2025-07-09 01:46:53.30009	2025-07-09 01:46:53.300092	509	USD	\N	\N
333	11	Duplex	E-SGQ400N	UFH2   440-470MHz   0.5Mhz   1U	Evertac Solutions	set	1	2.3	700	1609.9999999999998	1609.9999999999998	SGULN4N1CZ1	2025-07-09 01:46:53.305204	2025-07-09 01:46:53.305206	700	USD	\N	\N
334	11	OMU	RFS-400 LT/M	350-470MHz   BW 15MHz   4FP   NetFLEX 	Evertac Solutions	set	1	1.1	1890	2079	2079	SGR2SI030	2025-07-09 01:46:53.310419	2025-07-09 01:46:53.310422	1890	USD	\N	\N
522	14	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 5MHz   33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	8	1	2640	2640	21120	SGR3SI14S	2025-07-29 01:35:37.251397	2025-07-29 01:35:37.251399	21120	USD	\N	\N
523	14	Indoor Antenna	MA10	UHF   350-470MHz   Max Input Power 50W   0dBi	Evertac Solutions	set	214	1	25	25	5350	SGAIOCN4Y	2025-07-29 01:35:37.257546	2025-07-29 01:35:37.257548	5350	USD	\N	\N
524	14	Panel Antenna	E-ANTD 400	UHF   450-470MHz   Max Input Power 50W   Gain 2dBi	Evertac Solutions	set	4	1	80	80	320	SGAN2OFD2TE2	2025-07-29 01:35:37.266159	2025-07-29 01:35:37.266161	320	USD	\N	\N
525	14	Fiber Glass Omni Antenna	E-ANTG 400	UHF   450-470MHz   Max Input Power 50W   5dBi	Evertac Solutions	set	1	1	100	100	100	SGANLOMO5HR1	2025-07-29 01:35:37.275672	2025-07-29 01:35:37.275674	100	USD	\N	\N
526	14	Splitter	EVPD-2 LT	80-470MHz   MIP 50W	Evertac Solutions	set	60	1	25	25	1500	SGCDN24Y	2025-07-29 01:35:37.285053	2025-07-29 01:35:37.285056	1500	USD	\N	\N
527	14	Coupler	EVDC-6 LT	350-470MHz   MIP 50W   CP 6dB	Evertac Solutions	set	160	1	25	25	4000	SGCCN34Y	2025-07-29 01:35:37.290654	2025-07-29 01:35:37.290656	4000	USD	\N	\N
528	14	Two-way radio	PNR2000	Frequency range: 400MHz    Mode: DMR    Voltage: 3.8V    Function: BlueTooth/iBeacon    Interface.: No-keyboard screen	Evertac Solutions	set	60	1	290	290	17400	TS4D3NMK	2025-07-29 01:35:37.295857	2025-07-29 01:35:37.295858	17400	USD	\N	\N
529	14	RF Combiner	E-FH400-2	UHF2   440-470MHz   2-Port   Insertion loss≤ 4.0 dB  IP40  N-Female  2U	Evertac Solutions	set	1	1	1000	1000	1000	SGM1B022CZ1	2025-07-29 01:35:37.300753	2025-07-29 01:35:37.300754	1000	USD	\N	\N
659	18	Connector adapter	N-50JKW	90 Degree N-JK	Third party	set	5	1.43	2.5	3.575	17.875	OCIN5JWALC1	2025-08-13 02:38:39.185087	2025-08-13 02:38:39.185089	0	USD	\N	\N
660	18	Jumper Cable	E-JP50-7	0.5m/1.6ft  N-JJ for Antenna	Third party	set	2	1.444	9	12.995999999999999	25.991999999999997	OISKHB1JLC1	2025-08-13 02:38:39.194666	2025-08-13 02:38:39.194668	0	USD	\N	\N
661	18	Jumper Cable	NJ/NJ-3	1.5m/4.7ft N-JJ for Cabinet	Third party	set	5	1.5290000000000001	6.8	10.3972	51.986	EJUMJK4315NJNJ	2025-08-13 02:38:39.202803	2025-08-13 02:38:39.202804	0	USD	\N	\N
662	18	Fiber rack	ST/FC  24口	Standard FC type 24 port cabinet installation	Third party	set	1	1.422	96	136.5	136.5	EDFWYFC24W	2025-08-13 02:38:39.21063	2025-08-13 02:38:39.210632	0	USD	\N	\N
663	18	Fiber rack	ST/FC  4口	Standard FC type 4 port wall-mounted installation	Third party	set	2	1.4240000000000002	42	59.8	119.6	EDFWYFC04O	2025-08-13 02:38:39.218487	2025-08-13 02:38:39.218489	0	USD	\N	\N
664	18	Optical Fiber Jumper Cable Patch Cord	MNOFHC-SMD-50	LC to LC UPC Duplex Single Mode Fiber Patch Cable   5m (16ft)	Third party	set	4	1.585	4.1	6.498499999999999	25.993999999999996	EJUWY05A40LC	2025-08-13 02:38:39.226518	2025-08-13 02:38:39.22652	0	USD	\N	\N
665	18	Optical Fiber	GYXTH-4B1 4芯	4 core outdoor single mode smoke flame retardant	Third party	meter	150	1.585	1.23	1.95	292.5	ECAWYGYXTH0401	2025-08-13 02:38:39.240809	2025-08-13 02:38:39.240812	0	USD	\N	\N
530	14	Repeater	Mark1000 MAX	Frequency range: 400-470MHz    Channel spacing: 12.5kHz/25kHz    Max channel: 16    Max Power: 25W    Mode: DMR    NetFunction: NetFlex Cloud	Evertac Solutions	set	2	1	3290	3290	6580	PS4MS2NN	2025-07-29 01:35:37.305575	2025-07-29 01:35:37.305577	6580	USD	\N	\N
531	14	RF Multi-Coupler	E-JF350/400-2	UHF   350-470MHz   2-Port   Insertion loss≤ 3.5dB  IP40  N-Female  1U	Evertac Solutions	set	1	1	509	509	509	SGDE1BU2XCZ1	2025-07-29 01:35:37.310288	2025-07-29 01:35:37.31029	509	USD	\N	\N
643	18	Repeater	SLR 5300	Repeater 64CH 1-50watt UHF 403-470mhz\n- Power cord option\n- User Manual	Motorola	set	1	1	0	2700	2700	TP2508071608	2025-08-13 02:38:39.051849	2025-08-13 02:38:39.051852	0	USD	\N	\N
644	18	Duplex	E-SGQ400D	UHF2   440-470MHz   2-5MHz   2U	Evertac Solutions	set	1	1.103	1460	1610	1610	SGDULB4H1CZ1	2025-08-13 02:38:39.061033	2025-08-13 02:38:39.061036	1460	USD	\N	\N
645	18	DownLink Multi-Splitter	R-EVDC-BLST-D	UHF1  350-470MHz    6+1-Port   Max Input Power 50W   Insertion loss≤0.5dB  N-Female  1U	Evertac Solutions	set	1	1	800	880	880	SGE1AD6xCZ1	2025-08-13 02:38:39.069043	2025-08-13 02:38:39.069045	800	USD	\N	\N
646	18	UpLink Multi-Splitter	R-EVDC-BLST-U	UHF1   350-470MHz   6+1-Port   Max Input Power 50W   Insertion loss≤ 0.5dB  N-Female  1U	Evertac Solutions	set	1	1	800	880	880	SGE1AU6xCZ1	2025-08-13 02:38:39.076751	2025-08-13 02:38:39.076753	800	USD	\N	\N
647	18	OMU	RFS-400 LT/M	350-470MHz   BW 15MHz   4FP   NetFLEX	Evertac Solutions	set	1	1.101	1890	2080	2080	SGR2SI030	2025-08-13 02:38:39.084737	2025-08-13 02:38:39.084739	1890	USD	\N	\N
648	18	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 10MHz  33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	2	1	2640	2900	5800	SGR3SI140	2025-08-13 02:38:39.093235	2025-08-13 02:38:39.093237	5280	USD	\N	\N
649	18	Cable Feed Modular	FDPower400	modular install in ORU via RF cable to feed power	Evertac Solutions	set	2	1.101	345	380	760	SGGF20000	2025-08-13 02:38:39.101178	2025-08-13 02:38:39.10118	690	USD	\N	\N
650	18	Smart Indoor Antenna	MA11	UHF   350-470MHz   Max Input Power 50W   Gain 0dBi   Signal detection	Evertac Solutions	set	8	1	45	50	400	SGAIOCL4Y	2025-08-13 02:38:39.109727	2025-08-13 02:38:39.10973	360	USD	\N	\N
651	18	Fiber Glass Omni Antenna	E-ANTG 400	UHF   450-470MHz   Max Input Power 50W   5dBi	Evertac Solutions	set	1	1.1	100	110	110	SGANLOMO5HR1	2025-08-13 02:38:39.118255	2025-08-13 02:38:39.118257	100	USD	\N	\N
652	18	Splitter	MAPD-2	350-470MHz   MIP 50W   CFP	Evertac Solutions	set	3	1.091	55	60	180	SGCDF24Y	2025-08-13 02:38:39.126853	2025-08-13 02:38:39.126855	165	USD	\N	\N
653	18	Coupler	MADC-6	350-470MHz   MIP 50W   CP 6dB   CFP	Evertac Solutions	set	5	1.091	55	60	300	SGCCF34Y	2025-08-13 02:38:39.135113	2025-08-13 02:38:39.135115	275	USD	\N	\N
654	18	Light arrestor	CA-23RS	0-1000MHz 700W 50Ω N-Female	Third party	set	1	1.103	58	64	64	OBJANOTHS01	2025-08-13 02:38:39.143518	2025-08-13 02:38:39.14352	0	USD	\N	\N
655	18	Mounting brackets	MONT80	50cm L type	Third party	set	1	1.111	54	60	60	OBJANOTGR01	2025-08-13 02:38:39.152049	2025-08-13 02:38:39.152052	0	USD	\N	\N
656	18	Two-way radio	R7	SINGLE UNIT IMPRES CHARGER WITH UK POWER SUPPLY 207 V - 253 V (PMPN4572A)UHF WHIP ANTENNA 15CM(400-527 MHz) (PMAE4079A)BELT CLIP (PMLN4651A)DUST COVER OPTION (PMHN4429A)Essential 5 yr (HW & SW) WITHOUT Accidental Damage	Motorola	set	10	1	0	589	5890	TP2508071601	2025-08-13 02:38:39.160462	2025-08-13 02:38:39.160464	0	USD	\N	\N
657	18	Connector adapter	N-J1/2	1/2＂N-J	Third party	set	32	1.43	2.5	3.575	114.4	OCIN5JZALC1	2025-08-13 02:38:39.168646	2025-08-13 02:38:39.168648	0	USD	\N	\N
658	18	Connector adapter	N-50KK	N-KK	Third party	set	2	1.43	2.5	3.575	7.15	OCIN5KZALC1	2025-08-13 02:38:39.176866	2025-08-13 02:38:39.176869	0	USD	\N	\N
714	19	Connector adapter	N-J1/2	1/2＂N-J	Third party	set	1	1	2.5	2.5	2.5	OCIN5JZALC1	2025-08-15 02:28:10.096635	2025-08-15 02:28:10.096636	0	USD	\N	\N
715	19	Connector adapter	N-50KK	N-KK	Third party	set	1	1	2.5	2.5	2.5	OCIN5KZALC1	2025-08-15 02:28:10.105281	2025-08-15 02:28:10.105284	0	USD	\N	\N
716	19	Connector adapter	N-50JKW	90 Degree N-JK	Third party	set	1	1	2.5	2.5	2.5	OCIN5JWALC1	2025-08-15 02:28:10.114546	2025-08-15 02:28:10.114548	0	USD	\N	\N
717	19	Jumper Cable	E-JP50-7	0.5m/1.6ft  N-JJ for Antenna	Third party	set	1	1	9	9	9	OISKHB1JLC1	2025-08-15 02:28:10.124457	2025-08-15 02:28:10.12446	0	USD	\N	\N
718	19	Jumper Cable	NJ/NJ-3	1.5m/4.7ft N-JJ for Cabinet	Third party	set	1	1	6.8	6.8	6.8	EJUMJK4315NJNJ	2025-08-15 02:28:10.133929	2025-08-15 02:28:10.133931	0	USD	\N	\N
689	19	Repeater	Mark1000 MAX	Frequency range: 400-470MHz    Channel spacing: 12.5kHz/25kHz    Max channel: 16    Max Power: 25W    Mode: DMR    NetFunction: NetFlex Cloud	Evertac Solutions	set	1	1	3290	3290	3290	PS4MS2NN	2025-08-15 02:28:09.875786	2025-08-15 02:28:09.875789	3290	USD	\N	\N
690	19	Repeater	Motorola SLR 5300 UHF	400-470Mhz	Motorola	个	1	1	0	0	0	TP2508151005	2025-08-15 02:28:09.88606	2025-08-15 02:28:09.886061	0	USD	\N	\N
691	19	RF Combiner	E-FH400-2	UHF2   440-470MHz   2-Port   Insertion loss≤ 4.0 dB  IP40  N-Female  2U	Evertac Solutions	set	1	1	1000	1000	1000	SGM1B022CZ1	2025-08-15 02:28:09.895568	2025-08-15 02:28:09.895571	1000	USD	\N	\N
692	19	RF Multi-Coupler	E-JF350/400-2	UHF   350-470MHz   2-Port   Insertion loss≤ 3.5dB  IP40  N-Female  1U	Evertac Solutions	set	1	1	509	509	509	SGDE1BU2XCZ1	2025-08-15 02:28:09.904248	2025-08-15 02:28:09.90425	509	USD	\N	\N
693	19	DownLink Multi-Splitter	R-EVDC-BLST-D	UHF1  350-470MHz    6+1-Port   Max Input Power 50W   Insertion loss≤0.5dB  N-Female  1U	Evertac Solutions	set	1	1	800	800	800	SGE1AD6xCZ1	2025-08-15 02:28:09.914631	2025-08-15 02:28:09.914633	800	USD	\N	\N
694	19	UpLink Multi-Splitter	R-EVDC-BLST-U	UHF1   350-470MHz   6+1-Port   Max Input Power 50W   Insertion loss≤ 0.5dB  N-Female  1U	Evertac Solutions	set	1	1	800	800	800	SGE1AU6xCZ1	2025-08-15 02:28:09.923413	2025-08-15 02:28:09.923415	800	USD	\N	\N
695	19	OMU	RFS-400 LT/M	350-470MHz   BW 15MHz   4FP   NetFLEX	Evertac Solutions	set	2	1	1890	1890	3780	SGR2SI030	2025-08-15 02:28:09.933707	2025-08-15 02:28:09.93371	3780	USD	\N	\N
696	19	ORU	RFT-BDA400B LT/M	440-470MHz   BW 1M   Spacing 10MHz  33dBm/2W   WMD   REMOTE   NetFLEX	Evertac Solutions	set	2	1	2640	2640	5280	SGR3SI140	2025-08-15 02:28:09.942914	2025-08-15 02:28:09.942917	5280	USD	\N	\N
697	19	Cable Feed Modular	FDPower400	modular install in ORU via RF cable to feed power	Evertac Solutions	set	2	1	345	345	690	SGGF20000	2025-08-15 02:28:09.951208	2025-08-15 02:28:09.95121	690	USD	\N	\N
698	19	Indoor Antenna	MA10	UHF   350-470MHz   Max Input Power 50W   0dBi	Evertac Solutions	set	1	1	25	25	25	SGAIOCN4Y	2025-08-15 02:28:09.961042	2025-08-15 02:28:09.961045	25	USD	\N	\N
699	19	Smart Indoor Antenna	MA11	UHF   350-470MHz   Max Input Power 50W   Gain 0dBi   Signal detection	Evertac Solutions	set	1	1	45	45	45	SGAIOCL4Y	2025-08-15 02:28:09.970739	2025-08-15 02:28:09.970742	45	USD	\N	\N
700	19	Smart Indoor Antenna	MA12	UHF   350-470MHz   Max Input Power 50W   Gain 0dBi   Signal detection   iBeacon	Evertac Solutions	set	1	1	95	95	95	SGAIOCB4Y	2025-08-15 02:28:09.9791	2025-08-15 02:28:09.979103	95	USD	\N	\N
701	19	Splitter	MAPD-2	350-470MHz   MIP 50W   CFP	Evertac Solutions	set	1	1	55	55	55	SGCDF24Y	2025-08-15 02:28:09.987643	2025-08-15 02:28:09.987645	55	USD	\N	\N
702	19	Coupler	EVDC-6 LT	350-470MHz   MIP 50W   CP 6dB	Evertac Solutions	set	1	1	25	25	25	SGCCN34Y	2025-08-15 02:28:09.996499	2025-08-15 02:28:09.996501	25	USD	\N	\N
703	19	Access License	LS-NFX-BDA	ORU access to NetFLEX License	Evertac Solutions	set	1	1	360	360	360	HYWSRNB1	2025-08-15 02:28:10.005665	2025-08-15 02:28:10.005668	360	USD	\N	\N
704	19	Access License	LS-NFX-RPT	Repeater access to NetFLex License	Evertac Solutions	set	1	1	600	600	600	HYWSPNB1	2025-08-15 02:28:10.014405	2025-08-15 02:28:10.014407	600	USD	\N	\N
705	19	Gateway application	NFX_GATW	Synchronize setup configure system managment driver update online	Evertac Solutions	set	1	1	3050	3050	3050	HYWG0NB1	2025-08-15 02:28:10.022965	2025-08-15 02:28:10.022967	3050	USD	\N	\N
706	19	Driver	GW-MOT-RPT	MOTOROLA to NetFLEX Gateway Protocal	Evertac Solutions	set	1	1	6540	6540	6540	EHYW521066	2025-08-15 02:28:10.033545	2025-08-15 02:28:10.033548	6540	USD	\N	\N
707	19	Operation DashBoard	ACC-CWT	System Health analyz   System diagram online Fault Notification  Equipment location	Evertac Solutions	set	1	1	1600	1600	1600	HYWF0NA1	2025-08-15 02:28:10.042415	2025-08-15 02:28:10.042418	1600	USD	\N	\N
708	19	Rack Server	PowerEdge R350 Rack Server	Windows Server Intel® 4 core   8G Cache   4C/8T   Turbo (65W)   3200 MT/s Gateway	DELL	set	1	1	2650	2650	2650	PER3RSV	2025-08-15 02:28:10.050831	2025-08-15 02:28:10.050833	0	USD	\N	\N
709	19	Fiber rack	ST/FC  24口	Standard FC type 24 port cabinet installation	Third party	set	1	1	96	96	96	EDFWYFC24W	2025-08-15 02:28:10.058816	2025-08-15 02:28:10.058818	0	USD	\N	\N
710	19	Fiber rack	ST/FC  4口	Standard FC type 4 port wall-mounted installation	Third party	set	1	1	42	42	42	EDFWYFC04O	2025-08-15 02:28:10.066161	2025-08-15 02:28:10.066163	0	USD	\N	\N
711	19	Optical Fiber Jumper Cable Patch Cord	MNOFHC-SMD-50	LC to LC UPC Duplex Single Mode Fiber Patch Cable   5m (16ft)	Third party	set	1	1	4.1	4.1	4.1	EJUWY05A40LC	2025-08-15 02:28:10.073552	2025-08-15 02:28:10.073554	0	USD	\N	\N
712	19	Optical Fiber	GYXTH-4B1 4芯	4 core outdoor single mode smoke flame retardant	Third party	meter	50	1	1.23	1.23	61.5	ECAWYGYXTH0401	2025-08-15 02:28:10.081181	2025-08-15 02:28:10.081183	0	USD	\N	\N
713	19	RF cable	HCAAYZ -50-12	1/2＂50Ω	Third party	meter	50	1	2.8	2.8	140	OZCH221035	2025-08-15 02:28:10.089069	2025-08-15 02:28:10.089071	0	USD	\N	\N
719	19	Cabinet	Standard	19 -inch standard 42U with cooling	Third party	set	1	1	500	500	500	EJUMJK4315NJQJ	2025-08-15 02:28:10.152606	2025-08-15 02:28:10.152608	0	USD	\N	\N
\.


--
-- TOC entry 4841 (class 0 OID 24305)
-- Dependencies: 367
-- Data for Name: quotations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.quotations (id, quotation_number, project_id, contact_id, amount, project_stage, project_type, created_at, updated_at, owner_id, approval_status, approved_stages, approval_history, is_locked, lock_reason, locked_by, locked_at, confirmation_badge_status, confirmation_badge_color, confirmed_by, confirmed_at, product_signature, implant_total_amount, currency, exchange_rate, original_currency) FROM stdin;
10	QU202507-001	7	\N	139715.75999999998	embed	sales_focus	2025-07-09 00:34:53.263457+00	2025-07-09 00:51:25.604889	2	pending	[]	[]	f	\N	\N	\N	none	\N	\N	\N	3eefd98876c4fc8e5d8592a0730f7e78	100684	USD	1.000000	\N
9	QU202506-001	6	\N	36076.39	lost	business_opportunity	2025-06-30 08:22:51.383218+00	2025-06-30 09:41:02.338957	2	pending	[]	[]	f	\N	\N	\N	none	\N	\N	\N	7082fe402e3141decf6d547eb78104c8	25130	USD	1.000000	\N
15	QU202507-006	22	\N	294553.88	tendering	channel_follow	2025-07-29 08:28:49.612372+00	2025-07-29 08:28:50.025215	7	pending	[]	[]	f	\N	\N	\N	none	\N	\N	\N	cce9f1c486fe3ff6d57e6a411cc5d46a	435100	USD	1.000000	\N
14	QU202507-005	15	\N	63959	\N	\N	2025-07-29 01:32:45.105588+00	2025-07-29 01:35:37.227872	12	pending	[]	[]	f	\N	\N	\N	none	\N	\N	\N	f7c2aebb5b75587f2e182d1ea20fc4b4	63959	USD	1.000000	\N
12	QU202507-003	12	\N	82335.68999999999	\N	\N	2025-07-22 04:08:45.682848+00	2025-07-22 07:14:37.4459	12	pending	[]	[]	f	\N	\N	\N	none	\N	\N	\N	008db7c832da69fa507ed889966fd81c	63339	USD	1.000000	\N
11	QU202507-002	8	\N	11748.119999999999	quoted	sales_focus	2025-07-09 01:39:38.629404+00	2025-07-09 01:46:53.276624	12	pending	[]	[]	f	\N	\N	\N	none	\N	\N	\N	09336c18a29e7e863e1b4fdbb8b17b69	9579	USD	1.000000	\N
13	QU202507-004	13	\N	152585.3	paused	channel_follow	2025-07-22 08:07:54.185111+00	2025-07-22 08:25:41.483086	12	pending	[]	[]	f	\N	\N	\N	none	\N	\N	\N	05e4e23cd00f87c32a3c726816dd4710	123609	USD	1.000000	\N
18	QU202508-001	27	\N	22505.997	awarded	sales_focus	2025-08-07 07:55:30.581931+00	2025-08-13 02:38:39.23117	7	pending	[]	[]	f	\N	\N	\N	none	\N	\N	\N	2ee12474f988798745024e8962ebb148	11820	USD	1.000000	\N
19	QU202508-002	32	\N	32060.899999999998	discover	sales_focus	2025-08-15 02:03:00.683835+00	2025-08-15 02:28:10.139042	2	pending	[]	[]	f	\N	\N	\N	none	\N	\N	\N	54bbd12cc6f9a9ebf905218150643f40	28544	USD	1.000000	\N
\.


--
-- TOC entry 4876 (class 0 OID 26464)
-- Dependencies: 402
-- Data for Name: role_performance_access; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_performance_access (id, role, access_scope, access_conditions, description, created_at) FROM stdin;
\.


--
-- TOC entry 4872 (class 0 OID 26435)
-- Dependencies: 398
-- Data for Name: role_performance_config; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_performance_config (id, role, config_name, description, is_active, created_by, updated_by, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4882 (class 0 OID 26512)
-- Dependencies: 408
-- Data for Name: role_performance_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_performance_items (id, role_config_id, metric_id, item_name, item_code, sort_order, is_enabled, stat_scope, stat_scope_description, calculation_method, calculation_formula, data_source_config, qualification_rate, excellent_threshold, good_threshold, qualified_threshold, display_unit, decimal_places, color_config, weight, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4843 (class 0 OID 24321)
-- Dependencies: 369
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_permissions (id, role, module, can_view, can_create, can_edit, can_delete, pricing_discount_limit, settlement_discount_limit, permission_level, permission_level_description, can_change_owner) FROM stdin;
145	sales_manager	project	t	t	t	t	\N	\N	personal	\N	f
146	sales_manager	customer	t	t	t	t	\N	\N	personal	\N	f
147	sales_manager	quotation	t	t	t	t	\N	\N	personal	\N	f
148	sales_manager	product	t	f	f	f	\N	\N	system	\N	f
149	sales_manager	product_code	f	f	f	f	\N	\N	personal	\N	f
150	sales_manager	inventory	f	f	f	f	\N	\N	personal	\N	f
151	sales_manager	settlement	f	f	f	f	\N	\N	personal	\N	f
152	sales_manager	order	f	f	f	f	\N	\N	personal	\N	f
153	sales_manager	expense	t	t	t	t	\N	\N	personal	\N	f
154	sales_manager	pricing_order	f	f	f	f	70	65	personal	\N	f
155	sales_manager	settlement_order	f	f	f	f	70	65	personal	\N	f
156	sales_manager	user_management	f	f	f	f	\N	\N	personal	\N	f
157	sales_manager	permission_management	f	f	f	f	\N	\N	personal	\N	f
158	sales_manager	dictionary_management	f	f	f	f	\N	\N	personal	\N	f
159	sales_manager	performance_management	t	f	f	f	\N	\N	personal	\N	f
160	sales_manager	project_rating	f	f	f	f	\N	\N	personal	\N	f
129	business_admin	project	t	f	f	f	\N	\N	system	\N	f
130	business_admin	customer	t	f	f	f	\N	\N	personal	\N	f
131	business_admin	quotation	t	f	f	f	\N	\N	system	\N	f
132	business_admin	product	t	f	f	f	\N	\N	system	\N	f
133	business_admin	product_code	f	f	f	f	\N	\N	personal	\N	f
134	business_admin	inventory	f	f	f	f	\N	\N	personal	\N	f
135	business_admin	settlement	f	f	f	f	\N	\N	personal	\N	f
136	business_admin	order	f	f	f	f	\N	\N	personal	\N	f
137	business_admin	expense	t	t	t	t	\N	\N	company	\N	f
138	business_admin	pricing_order	f	f	f	f	\N	\N	personal	\N	f
139	business_admin	settlement_order	f	f	f	f	\N	\N	personal	\N	f
140	business_admin	user_management	f	f	f	f	\N	\N	personal	\N	f
141	business_admin	permission_management	f	f	f	f	\N	\N	personal	\N	f
142	business_admin	dictionary_management	f	f	f	f	\N	\N	personal	\N	f
143	business_admin	performance_management	t	f	f	f	\N	\N	company	\N	f
144	business_admin	project_rating	f	f	f	f	\N	\N	personal	\N	f
161	solution_manager	project	t	f	f	f	\N	\N	system	\N	f
162	solution_manager	customer	t	t	t	t	\N	\N	personal	\N	f
163	solution_manager	quotation	t	t	t	f	\N	\N	system	\N	f
164	solution_manager	product	t	f	f	f	\N	\N	system	\N	f
165	solution_manager	product_code	f	f	f	f	\N	\N	personal	\N	f
166	solution_manager	inventory	f	f	f	f	\N	\N	personal	\N	f
167	solution_manager	settlement	f	f	f	f	\N	\N	personal	\N	f
168	solution_manager	order	f	f	f	f	\N	\N	personal	\N	f
169	solution_manager	expense	f	f	f	f	\N	\N	personal	\N	f
170	solution_manager	pricing_order	f	f	f	f	\N	\N	personal	\N	f
171	solution_manager	settlement_order	f	f	f	f	\N	\N	personal	\N	f
172	solution_manager	user_management	f	f	f	f	\N	\N	personal	\N	f
173	solution_manager	permission_management	f	f	f	f	\N	\N	personal	\N	f
174	solution_manager	dictionary_management	f	f	f	f	\N	\N	personal	\N	f
175	solution_manager	performance_management	f	f	f	f	\N	\N	personal	\N	f
176	solution_manager	project_rating	f	t	f	f	\N	\N	system	\N	f
177	product_manager	project	t	f	f	f	\N	\N	system	\N	f
178	product_manager	customer	t	f	f	f	\N	\N	personal	\N	f
179	product_manager	quotation	t	f	f	f	\N	\N	system	\N	f
180	product_manager	product	t	t	t	t	\N	\N	system	\N	f
181	product_manager	product_code	t	t	t	t	\N	\N	system	\N	f
182	product_manager	inventory	f	f	f	f	\N	\N	personal	\N	f
183	product_manager	settlement	f	f	f	f	\N	\N	personal	\N	f
184	product_manager	order	f	f	f	f	\N	\N	personal	\N	f
185	product_manager	expense	f	f	f	f	\N	\N	personal	\N	f
186	product_manager	pricing_order	f	f	f	f	\N	\N	personal	\N	f
187	product_manager	settlement_order	f	f	f	f	\N	\N	personal	\N	f
188	product_manager	user_management	f	f	f	f	\N	\N	personal	\N	f
189	product_manager	permission_management	f	f	f	f	\N	\N	personal	\N	f
190	product_manager	dictionary_management	f	f	f	f	\N	\N	personal	\N	f
191	product_manager	performance_management	f	f	f	f	\N	\N	personal	\N	f
192	product_manager	project_rating	f	t	f	f	\N	\N	system	\N	f
\.


--
-- TOC entry 4845 (class 0 OID 24328)
-- Dependencies: 371
-- Data for Name: settlement_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.settlement_details (id, settlement_id, inventory_id, product_id, quantity_settled, quantity_before, quantity_after, unit, notes) FROM stdin;
\.


--
-- TOC entry 4847 (class 0 OID 24334)
-- Dependencies: 373
-- Data for Name: settlement_order_details; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.settlement_order_details (id, pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_order_id, settlement_company_id, settlement_status, settlement_date, settlement_notes, currency) FROM stdin;
\.


--
-- TOC entry 4849 (class 0 OID 24341)
-- Dependencies: 375
-- Data for Name: settlement_orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.settlement_orders (id, order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, total_amount, total_discount_rate, status, approved_by, approved_at, created_by, created_at, updated_at, settlement_status) FROM stdin;
\.


--
-- TOC entry 4851 (class 0 OID 24346)
-- Dependencies: 377
-- Data for Name: settlements; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.settlements (id, settlement_number, company_id, settlement_date, status, total_items, description, created_by_id, approved_by_id, approved_at, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4853 (class 0 OID 24352)
-- Dependencies: 379
-- Data for Name: solution_manager_email_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solution_manager_email_settings (id, user_id, quotation_created, quotation_updated, project_created, project_stage_changed, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4855 (class 0 OID 24356)
-- Dependencies: 381
-- Data for Name: system_metrics; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.system_metrics (id, version_id, avg_response_time, max_response_time, error_rate, active_users, total_requests, database_size, cpu_usage, memory_usage, disk_usage, recorded_at) FROM stdin;
\.


--
-- TOC entry 4857 (class 0 OID 24360)
-- Dependencies: 383
-- Data for Name: system_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.system_settings (id, key, value, description, created_at, updated_at) FROM stdin;
1	customer_activity_threshold	1	客户活跃度阈值（天）- 超过指定天数无活动则标记为不活跃	2025-06-22 11:20:46.222595	2025-06-22 11:20:46.222599
2	project_activity_threshold	7	项目活跃度阈值（天）- 超过指定天数无活动则标记为不活跃	2025-06-22 11:20:46.231417	2025-06-22 11:20:46.231421
\.


--
-- TOC entry 4859 (class 0 OID 24366)
-- Dependencies: 385
-- Data for Name: temp_products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.temp_products (id, product_name, product_model, product_desc, brand, unit, product_mn, category, category_path, created_by, reference_price, usage_count, last_used_at, created_at, updated_at, is_deleted) FROM stdin;
1	Repeater	Motorola SLR 5300 UHF	400-470Mhz	Motorola	个	TP2508141620	Basestation	Basestation	2	1	3	2025-08-14 08:21:09.300994	2025-08-14 08:20:43.978142	2025-08-14 08:21:09.301003	f
\.


--
-- TOC entry 4861 (class 0 OID 24372)
-- Dependencies: 387
-- Data for Name: upgrade_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.upgrade_logs (id, version_id, from_version, to_version, upgrade_date, upgrade_type, status, upgrade_notes, error_message, duration_seconds, operator_id, operator_name, environment, server_info) FROM stdin;
1	2	1.3.5	1.3.6	2025-08-08 14:47:51.906484	automatic	success	基于Git提交自动升级\n提交: 9981a32c\n信息: 修复版本自动更新机制：检测到新Git提交时自动创建版本记录	\N	\N	\N	系统自动	production	\N
2	3	1.3.6	1.3.7	2025-08-09 09:19:59.780404	automatic	success	基于Git提交自动升级\n提交: 6c441130\n信息: 项目多重客户关联	\N	\N	\N	系统自动	production	\N
3	4	1.3.7	1.3.8	2025-08-10 13:39:44.24475	automatic	success	基于Git提交自动升级\n提交: 1d4ded8e\n信息: 更新发票上传问题	\N	\N	\N	系统自动	production	\N
4	5	1.3.8	1.3.9	2025-08-10 15:34:17.988814	automatic	success	基于Git提交自动升级\n提交: 229883b2\n信息: 更新发序号问题	\N	\N	\N	系统自动	production	\N
5	6	1.3.9	1.3.10	2025-08-11 00:43:47.728606	automatic	success	基于Git提交自动升级\n提交: d9fa9bb1\n信息: 修复Supabase数据库db.create_all()的schema问题\n\n关键问题:\n- SQLAlchemy的db.create_all()尝试创建ENUM类型时找不到schema\n- OVS Supabase数据库的search_path为空，导致"no schema has been selected"错误\n- 之前的修复只覆盖了Alembic迁移，但没有覆盖SQLAlchemy直接表创建\n\n解决方案:\n- 在db.create_all()调用前检测Supabase环境\n- 自动设置search_path为public\n- 确保ENUM类型和表结构能正确创建\n\n适用场景:\n- 解决云端OVS数据库部署时的启动错误\n- 兼容所有Supabase数据库实例\n- 不影响Render或其他数据库环境\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>	\N	\N	\N	系统自动	production	\N
6	7	1.3.10	1.3.11	2025-08-11 11:15:05.570078	automatic	success	基于Git提交自动升级\n提交: 806d4a41\n信息: 修研发产品库的销售地区问题	\N	\N	\N	系统自动	production	\N
7	8	1.3.11	1.3.12	2025-08-12 00:53:44.484312	automatic	success	基于Git提交自动升级\n提交: 8a04ff3a\n信息: 更新服务器冷启数据库连接问题	\N	\N	\N	系统自动	production	\N
8	9	1.3.12	1.3.13	2025-08-12 01:20:10.422597	automatic	success	基于Git提交自动升级\n提交: ffb0f3de\n信息: 更新批价单问题	\N	\N	\N	系统自动	production	\N
9	10	1.3.13	1.3.14	2025-08-12 08:11:09.899601	automatic	success	基于Git提交自动升级\n提交: 25b7fcb4\n信息: 修复检验缺乏检查的漏洞	\N	\N	\N	系统自动	production	\N
10	11	1.3.14	1.3.15	2025-08-15 04:21:07.98159	automatic	success	基于Git提交自动升级\n提交: 17f3aa2d\n信息: 修复行动记录的展示问题	\N	\N	\N	系统自动	production	\N
\.


--
-- TOC entry 4863 (class 0 OID 24378)
-- Dependencies: 389
-- Data for Name: user_event_subscriptions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_event_subscriptions (id, user_id, target_user_id, event_id, enabled, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4865 (class 0 OID 24382)
-- Dependencies: 391
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, password_hash, real_name, company_name, email, phone, department, is_department_manager, role, is_profile_complete, wechat_openid, wechat_nickname, wechat_avatar, is_active, created_at, last_login, updated_at, language_preference) FROM stdin;
7	yusry	scrypt:32768:8:1$BTKWChnUHLRTWWbp$9616e2a5eb6825b03f0a524e7d649f670bd5591e4f2208f2f76467fa7153a77f6de3bffc6411436c33570382b10431e65e42f137f2f05946c91049a17eafb475	yusry.lee	Triple Access	yusrylee@tripleaccess.com.my		sales_dep	f	sales_manager	f	\N	\N	\N	t	1754462416.8864582	\N	1754554370.4195	en
3	roy	scrypt:32768:8:1$Rs0enqypTpPiZxk3$47acd1c730bfcd0e7adf450718894025669d05ee9609f634eac09faa315aaf68608674ce2b70ecae9ffb815f03a8a6cd2881788209ac1cef9ce9298ef936ada8	roy.lim	evertacsolutions	roy.lim@evertacsolutions.com		sales_dep	t	sales_manager	f	\N	\N	\N	t	1750594048.8113122	\N	1752454275.954173	en
8	clayton	scrypt:32768:8:1$0XWIg6Lirs2K468z$08649e027e582b9b72ba83ecd346f66faacec2db851ee8864bd5581360334f2f1fd71defd7e7376f6df64a98ff209ef14a75d6d4ed87f3a0447413837341c091	clayton.yaw	Technics Communication & Electronics Pte Ltd	clayton.yaw@tce.com.sg		sales_dep	f	sales_manager	f	\N	\N	\N	t	1754462483.3012388	\N	1754471817.154164	en
2	quah	scrypt:32768:8:1$7pfylvxXwrCdaRxe$7312afda97de9ef3e380a81ef15e01b002ee35d60be50bf1802f8b990b17c417ac6903fa16bbfd724c6da5f7a294c4839c8bc23bd9f21a98fecca60ffd12c638	quah	evertacsolutions	chinyeong.quah@evertacsolutions.com		sales_dep	f	sales_manager	f	\N	\N	\N	t	1750594011.3797135	\N	1750646724.1965456	en
6	vivian	scrypt:32768:8:1$XMwgCmfKKA1cUbcM$31775f5cb0aa14b28ce148c25960531bd1c300f337336bb0c0c8722d627136305a24e2948554cd4709e0037cd5ae816aba30b815c3ffb5dc5e02f0dcf339b615	vivian.zh	evertacsolutions	vivian@evertac.net		sales_dep	f	business_admin	f	\N	\N	\N	f	1752803232.6621337	\N	1752803232.6621382	zh
9	alesandro	scrypt:32768:8:1$rrB2CoPLI9CqaFcE$8cf14deab2731ee1ae78dc1afd1985e748de083747e3a440312e52474e5ce31030ffa28d8279c25b376fa3c3c1a781c34d71d1d3dd218b6e1c782e8f7065e20f	alesandro	evertacsolutions	alesandro@evertacsolutions.com		sales_dep	f	sales_manager	f	\N	\N	\N	t	1754462596.380189	\N	1754535149.0009017	en
4	Patrick	scrypt:32768:8:1$tTTdCyYf1CiLRo2k$f862a65c03c9071d01b9d1b4ccdc4279914199307fe40836a0ad66ea73316419bacd5ff4593fc7275cef22b68d1646d354b1d7902fec097b62fe6909464aa1a8	Patrick.ku	evertacsolutions	patrick.ku@evertacsolutions.com		sales_dep	t	sales_manager	f	\N	\N	\N	t	1752803035.8285267	\N	1754535169.9219673	en
11	zhaoyb	scrypt:32768:8:1$uHxXbhvLooRHbVRG$b34a02cb2deae1cfcf3fc9c4794879dce76cf4486430628c624a748148f1e888be078b635ba89ef795f84c9cc0e76e1d6a53f6ba96c65f7df918c82ae70cbdfa	zhaoyibo	evertacsolutions	zhaoyb@evertac.net		sales_dep	f	product_manager	f	\N	\N	\N	t	1754877260.1116912	\N	1754877849.8941834	zh
10	liuwei	scrypt:32768:8:1$FjRQdNdV3sTcDMGV$52fdcf786abff72c1a1b4c445fa7c8b4d9b899c68efdfe7f479647c577e8524e8ae356eaa74b1cec9150166ccbcd2ad29e1fefb8c56f86f5fc2a76d90ef1e146	liuwei	evertacsolutions	liuwei@evertac.net		sales_dep	f	solution_manager	f	\N	\N	\N	t	1754877213.1164532	\N	1754877857.9052918	zh
12	fuyan	scrypt:32768:8:1$Q7vALK0hjRqIPNWC$fa798d000e1a69834a81cda0aaa64be14aba674f0ad8863a6cb17604e501174b930977443ff2b11a80ad0615fdaa5bd847db89d39bbbe5dded77187faef87146	fuyanxin	FMTCS SOLUTIONS PTE. LTD	fuyan1004@163.com	+86-18616029812		f	sales_manager	f	\N	\N	\N	t	1754877814.4048924	\N	1755064476.6829937	zh
1	admin	scrypt:32768:8:1$16hyEj82QT4yuzKS$1ea95ec3f25acf280d53c359e355b00944b955481243132db99edc7183b54e6e90821469fe9ba85f09ae5c252e3415dd1c7dedb2b32ffa1d07af4ac4867a2ea6	james.ni	evertacsolutions	admin@pma.com	None		f	admin	t	\N	\N	\N	t	1750593175.572287	\N	1754971955.3756306	en
5	peizhen	scrypt:32768:8:1$Fx6ADtBVkPo4lrQX$3b9098f05e8423d2250c65d4c7a56f16e88c1c5c0355e7fa3645d532a0f2f7e118958831b54c8679f57cbc1044b0625f41e2c150a5c123d47c7aba534229d618	Pei Zhen	evertacsolutions	tohpei.z@evertacsolutions.com		sales_dep	t	business_admin	f	\N	\N	\N	t	1752803178.8786478	\N	1754992038.653635	en
\.


--
-- TOC entry 4867 (class 0 OID 24388)
-- Dependencies: 393
-- Data for Name: version_records; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.version_records (id, version_number, version_name, release_date, description, is_current, environment, total_features, total_fixes, total_improvements, git_commit, build_number, created_at, updated_at) FROM stdin;
1	1.3.5	PMA项目管理系统	2025-08-07 17:07:23	PMA项目管理系统 v1.3.5，基于315个Git提交的稳定版本。	f	production	0	1	0	0855a70	\N	2025-06-02 09:24:21.968651	2025-08-15 04:21:07.91659
2	1.3.6	问题修复版本	2025-08-08 14:47:51.879766	## 问题修复版本\n\n本次更新主要修复了系统中的问题，提升系统稳定性。\n\n**主要改进**: 修复版本自动更新机制：检测到新Git提交时自动创建版本记录	f	production	0	0	1	9981a32c	\N	2025-08-08 14:47:51.879775	2025-08-15 04:21:07.91659
3	1.3.7	常规更新版本	2025-08-09 09:19:59.765269	## 常规更新版本\n\n系统常规更新维护。\n\n**更新内容**: 项目多重客户关联	f	production	0	0	1	6c441130	\N	2025-08-09 09:19:59.765274	2025-08-15 04:21:07.91659
4	1.3.8	常规更新版本	2025-08-10 13:39:44.187315	## 常规更新版本\n\n系统常规更新维护。\n\n**更新内容**: 更新发票上传问题	f	production	0	0	1	1d4ded8e	\N	2025-08-10 13:39:44.187319	2025-08-15 04:21:07.91659
5	1.3.9	常规更新版本	2025-08-10 15:34:17.970633	## 常规更新版本\n\n系统常规更新维护。\n\n**更新内容**: 更新发序号问题	f	production	0	0	1	229883b2	\N	2025-08-10 15:34:17.970639	2025-08-15 04:21:07.91659
6	1.3.10	问题修复版本	2025-08-11 00:43:47.704153	## 问题修复版本\n\n本次更新主要修复了系统中的问题，提升系统稳定性。\n\n**主要改进**: 修复Supabase数据库db.create_all()的schema问题\n\n关键问题:\n- SQLAlchemy的db.create_all()尝试创建ENUM类型时找不到schema\n- OVS Supabase数据库的search_path为空，导致"no schema has been selected"错误\n- 之前的修复只覆盖了Alembic迁移，但没有覆盖SQLAlchemy直接表创建\n\n解决方案:\n- 在db.create_all()调用前检测Supabase环境\n- 自动设置search_path为public\n- 确保ENUM类型和表结构能正确创建\n\n适用场景:\n- 解决云端OVS数据库部署时的启动错误\n- 兼容所有Supabase数据库实例\n- 不影响Render或其他数据库环境\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>	f	production	0	0	1	d9fa9bb1	\N	2025-08-11 00:43:47.704163	2025-08-15 04:21:07.91659
7	1.3.11	常规更新版本	2025-08-11 11:15:05.523594	## 常规更新版本\n\n系统常规更新维护。\n\n**更新内容**: 修研发产品库的销售地区问题	f	production	0	0	1	806d4a41	\N	2025-08-11 11:15:05.523596	2025-08-15 04:21:07.91659
8	1.3.12	常规更新版本	2025-08-12 00:53:44.462971	## 常规更新版本\n\n系统常规更新维护。\n\n**更新内容**: 更新服务器冷启数据库连接问题	f	production	0	0	1	8a04ff3a	\N	2025-08-12 00:53:44.462977	2025-08-15 04:21:07.91659
9	1.3.13	常规更新版本	2025-08-12 01:20:10.399963	## 常规更新版本\n\n系统常规更新维护。\n\n**更新内容**: 更新批价单问题	f	production	0	0	1	ffb0f3de	\N	2025-08-12 01:20:10.39997	2025-08-15 04:21:07.91659
10	1.3.14	问题修复版本	2025-08-12 08:11:09.881349	## 问题修复版本\n\n本次更新主要修复了系统中的问题，提升系统稳定性。\n\n**主要改进**: 修复检验缺乏检查的漏洞	f	production	0	0	1	25b7fcb4	\N	2025-08-12 08:11:09.881356	2025-08-15 04:21:07.91659
11	1.3.15	问题修复版本	2025-08-15 04:21:07.922059	## 问题修复版本\n\n本次更新主要修复了系统中的问题，提升系统稳定性。\n\n**主要改进**: 修复行动记录的展示问题	t	production	0	0	1	17f3aa2d	\N	2025-08-15 04:21:07.922066	2025-08-15 04:21:08.020214
\.


--
-- TOC entry 4741 (class 0 OID 17000)
-- Dependencies: 263
-- Data for Name: schema_migrations; Type: TABLE DATA; Schema: realtime; Owner: -
--

COPY realtime.schema_migrations (version, inserted_at) FROM stdin;
20211116024918	2025-08-03 02:59:32
20211116045059	2025-08-03 02:59:32
20211116050929	2025-08-03 02:59:32
20211116051442	2025-08-03 02:59:32
20211116212300	2025-08-03 02:59:32
20211116213355	2025-08-03 02:59:32
20211116213934	2025-08-03 02:59:32
20211116214523	2025-08-03 02:59:32
20211122062447	2025-08-03 02:59:32
20211124070109	2025-08-03 02:59:32
20211202204204	2025-08-03 02:59:32
20211202204605	2025-08-03 02:59:32
20211210212804	2025-08-03 02:59:32
20211228014915	2025-08-03 02:59:32
20220107221237	2025-08-03 02:59:32
20220228202821	2025-08-03 02:59:32
20220312004840	2025-08-03 02:59:32
20220603231003	2025-08-03 02:59:32
20220603232444	2025-08-03 02:59:32
20220615214548	2025-08-03 02:59:32
20220712093339	2025-08-03 02:59:32
20220908172859	2025-08-03 02:59:32
20220916233421	2025-08-03 02:59:32
20230119133233	2025-08-03 02:59:32
20230128025114	2025-08-03 02:59:32
20230128025212	2025-08-03 02:59:32
20230227211149	2025-08-03 02:59:32
20230228184745	2025-08-03 02:59:32
20230308225145	2025-08-03 02:59:32
20230328144023	2025-08-03 02:59:32
20231018144023	2025-08-03 02:59:32
20231204144023	2025-08-03 02:59:32
20231204144024	2025-08-03 02:59:32
20231204144025	2025-08-03 02:59:32
20240108234812	2025-08-03 02:59:32
20240109165339	2025-08-03 02:59:32
20240227174441	2025-08-03 02:59:32
20240311171622	2025-08-03 02:59:32
20240321100241	2025-08-03 02:59:32
20240401105812	2025-08-03 02:59:32
20240418121054	2025-08-03 02:59:32
20240523004032	2025-08-03 02:59:32
20240618124746	2025-08-03 02:59:33
20240801235015	2025-08-03 02:59:33
20240805133720	2025-08-03 02:59:33
20240827160934	2025-08-03 02:59:33
20240919163303	2025-08-03 02:59:33
20240919163305	2025-08-03 02:59:33
20241019105805	2025-08-03 02:59:33
20241030150047	2025-08-03 02:59:33
20241108114728	2025-08-03 02:59:33
20241121104152	2025-08-03 02:59:33
20241130184212	2025-08-03 02:59:33
20241220035512	2025-08-03 02:59:33
20241220123912	2025-08-03 02:59:33
20241224161212	2025-08-03 02:59:33
20250107150512	2025-08-03 02:59:33
20250110162412	2025-08-03 02:59:33
20250123174212	2025-08-03 02:59:33
20250128220012	2025-08-03 02:59:33
20250506224012	2025-08-03 02:59:33
20250523164012	2025-08-03 02:59:33
20250714121412	2025-08-03 02:59:33
\.


--
-- TOC entry 4743 (class 0 OID 17023)
-- Dependencies: 266
-- Data for Name: subscription; Type: TABLE DATA; Schema: realtime; Owner: -
--

COPY realtime.subscription (id, subscription_id, entity, filters, claims, created_at) FROM stdin;
\.


--
-- TOC entry 4727 (class 0 OID 16544)
-- Dependencies: 246
-- Data for Name: buckets; Type: TABLE DATA; Schema: storage; Owner: -
--

COPY storage.buckets (id, name, owner, created_at, updated_at, public, avif_autodetection, file_size_limit, allowed_mime_types, owner_id) FROM stdin;
product-images	product-images	\N	2025-08-03 03:18:07.923323+00	2025-08-03 03:18:07.923323+00	t	f	\N	\N	\N
rd-product-images	rd-product-images	\N	2025-08-10 04:30:46.928639+00	2025-08-10 04:30:46.928639+00	t	f	\N	\N	\N
invoice-images	invoice-images	\N	2025-08-10 04:30:28.22586+00	2025-08-10 04:30:28.22586+00	t	f	\N	\N	\N
\.


--
-- TOC entry 4729 (class 0 OID 16586)
-- Dependencies: 248
-- Data for Name: migrations; Type: TABLE DATA; Schema: storage; Owner: -
--

COPY storage.migrations (id, name, hash, executed_at) FROM stdin;
0	create-migrations-table	e18db593bcde2aca2a408c4d1100f6abba2195df	2025-08-03 02:59:33.6235
1	initialmigration	6ab16121fbaa08bbd11b712d05f358f9b555d777	2025-08-03 02:59:33.630534
2	storage-schema	5c7968fd083fcea04050c1b7f6253c9771b99011	2025-08-03 02:59:33.635984
3	pathtoken-column	2cb1b0004b817b29d5b0a971af16bafeede4b70d	2025-08-03 02:59:33.655984
4	add-migrations-rls	427c5b63fe1c5937495d9c635c263ee7a5905058	2025-08-03 02:59:33.66715
5	add-size-functions	79e081a1455b63666c1294a440f8ad4b1e6a7f84	2025-08-03 02:59:33.673169
6	change-column-name-in-get-size	f93f62afdf6613ee5e7e815b30d02dc990201044	2025-08-03 02:59:33.686644
7	add-rls-to-buckets	e7e7f86adbc51049f341dfe8d30256c1abca17aa	2025-08-03 02:59:33.695426
8	add-public-to-buckets	fd670db39ed65f9d08b01db09d6202503ca2bab3	2025-08-03 02:59:33.701154
9	fix-search-function	3a0af29f42e35a4d101c259ed955b67e1bee6825	2025-08-03 02:59:33.706917
10	search-files-search-function	68dc14822daad0ffac3746a502234f486182ef6e	2025-08-03 02:59:33.713394
11	add-trigger-to-auto-update-updated_at-column	7425bdb14366d1739fa8a18c83100636d74dcaa2	2025-08-03 02:59:33.719813
12	add-automatic-avif-detection-flag	8e92e1266eb29518b6a4c5313ab8f29dd0d08df9	2025-08-03 02:59:33.726669
13	add-bucket-custom-limits	cce962054138135cd9a8c4bcd531598684b25e7d	2025-08-03 02:59:33.732996
14	use-bytes-for-max-size	941c41b346f9802b411f06f30e972ad4744dad27	2025-08-03 02:59:33.739005
15	add-can-insert-object-function	934146bc38ead475f4ef4b555c524ee5d66799e5	2025-08-03 02:59:33.76214
16	add-version	76debf38d3fd07dcfc747ca49096457d95b1221b	2025-08-03 02:59:33.767887
17	drop-owner-foreign-key	f1cbb288f1b7a4c1eb8c38504b80ae2a0153d101	2025-08-03 02:59:33.77363
18	add_owner_id_column_deprecate_owner	e7a511b379110b08e2f214be852c35414749fe66	2025-08-03 02:59:33.779792
19	alter-default-value-objects-id	02e5e22a78626187e00d173dc45f58fa66a4f043	2025-08-03 02:59:33.78862
20	list-objects-with-delimiter	cd694ae708e51ba82bf012bba00caf4f3b6393b7	2025-08-03 02:59:33.794427
21	s3-multipart-uploads	8c804d4a566c40cd1e4cc5b3725a664a9303657f	2025-08-03 02:59:33.802668
22	s3-multipart-uploads-big-ints	9737dc258d2397953c9953d9b86920b8be0cdb73	2025-08-03 02:59:33.819671
23	optimize-search-function	9d7e604cddc4b56a5422dc68c9313f4a1b6f132c	2025-08-03 02:59:33.83156
24	operation-function	8312e37c2bf9e76bbe841aa5fda889206d2bf8aa	2025-08-03 02:59:33.837546
25	custom-metadata	d974c6057c3db1c1f847afa0e291e6165693b990	2025-08-03 02:59:33.843363
\.


--
-- TOC entry 4728 (class 0 OID 16559)
-- Dependencies: 247
-- Data for Name: objects; Type: TABLE DATA; Schema: storage; Owner: -
--

COPY storage.objects (id, bucket_id, name, owner, created_at, updated_at, last_accessed_at, metadata, version, owner_id, user_metadata) FROM stdin;
08e63da9-9b0e-49ad-8b2b-bc3e968c007a	invoice-images	invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_01_01.heic	\N	2025-08-12 03:57:57.173241+00	2025-08-12 03:57:57.173241+00	2025-08-12 03:57:57.173241+00	{"eTag": "\\"268431324f5b87a66d18960c6dca6f5d\\"", "size": 200412, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T03:57:58.000Z", "contentLength": 200412, "httpStatusCode": 200}	aa84be06-9fd0-460f-a913-1596432a3ee9	\N	{}
08e9d97d-58cc-42e4-9ca5-8e27de2e40b9	invoice-images	invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_01_02.heic	\N	2025-08-12 03:57:57.354937+00	2025-08-12 03:57:57.354937+00	2025-08-12 03:57:57.354937+00	{"eTag": "\\"ea241f7e0293a1c0ae7526914ea71f60\\"", "size": 202910, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T03:57:58.000Z", "contentLength": 202910, "httpStatusCode": 200}	a95bf356-301e-4ac5-9a4e-bd86be8d611e	\N	{}
6c2f482d-f922-4784-a250-f60ac50fb563	invoice-images	invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_02_01.heic	\N	2025-08-12 03:57:57.532472+00	2025-08-12 03:57:57.532472+00	2025-08-12 03:57:57.532472+00	{"eTag": "\\"bbe7c875905c5f98802e818e5ad639c9\\"", "size": 66061, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T03:57:58.000Z", "contentLength": 66061, "httpStatusCode": 200}	236b515d-c942-4548-bc70-a3767f45746b	\N	{}
34439e73-18b9-47cf-87dd-5ca5f5b48e3c	invoice-images	invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_02_02.heic	\N	2025-08-12 03:57:57.692223+00	2025-08-12 03:57:57.692223+00	2025-08-12 03:57:57.692223+00	{"eTag": "\\"d4890a91fa9eb69fc7ad077e876920dc\\"", "size": 62493, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T03:57:58.000Z", "contentLength": 62493, "httpStatusCode": 200}	0688610a-cc1b-4ae3-8f1e-9a4978d5634a	\N	{}
ad4b2f74-556e-486a-a482-40eb5b0f890e	invoice-images	invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_02_03.heic	\N	2025-08-12 03:57:57.81622+00	2025-08-12 03:57:57.81622+00	2025-08-12 03:57:57.81622+00	{"eTag": "\\"b86db059cae0b9133ca2944994019a50\\"", "size": 67751, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T03:57:58.000Z", "contentLength": 67751, "httpStatusCode": 200}	67207841-d4e5-4584-b3b6-53759578fb19	\N	{}
d4dfcc17-2369-449f-8991-f63d976e6df9	invoice-images	invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_03_01.heic	\N	2025-08-12 03:57:57.981539+00	2025-08-12 03:57:57.981539+00	2025-08-12 03:57:57.981539+00	{"eTag": "\\"78ea2f6fc304c2d82a66248006f51585\\"", "size": 78220, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T03:57:58.000Z", "contentLength": 78220, "httpStatusCode": 200}	c61e980b-d737-41af-8592-6613af66483d	\N	{}
9f5584f1-2479-44d0-a06f-663ef10a896b	invoice-images	invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_03_02.heic	\N	2025-08-12 03:57:58.090583+00	2025-08-12 03:57:58.090583+00	2025-08-12 03:57:58.090583+00	{"eTag": "\\"4d37fb8a4095b960039ad82e129c4149\\"", "size": 78729, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T03:57:59.000Z", "contentLength": 78729, "httpStatusCode": 200}	a4858454-f909-4e53-bf9c-56599e361858	\N	{}
67f2ca15-3b8e-4e4f-95c3-cf7f913b6547	invoice-images	invoice_files/PMA-SA/BX2025081201/PMA-SA_BX2025081201_04_01.heic	\N	2025-08-12 03:57:58.351928+00	2025-08-12 03:57:58.351928+00	2025-08-12 03:57:58.351928+00	{"eTag": "\\"34181fb5a12a393d6a69e46327e09ade\\"", "size": 1049359, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T03:57:59.000Z", "contentLength": 1049359, "httpStatusCode": 200}	7b62c58e-e635-4e5f-9e21-3d923f6636c6	\N	{}
793e6479-62cc-4ddd-84b1-b760666ea0d9	invoice-images	invoice_files/PMA-SA/BX2025080801/PMA-SA_BX2025080801_01_01.heic	\N	2025-08-12 04:16:09.589981+00	2025-08-12 04:16:09.589981+00	2025-08-12 04:16:09.589981+00	{"eTag": "\\"5d1d364f886998b012873ec4150ae839\\"", "size": 140562, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:16:10.000Z", "contentLength": 140562, "httpStatusCode": 200}	a40e6fd0-7aa6-4556-b279-4037352f45f8	\N	{}
c23b510a-b060-40fe-96df-dda6bbd8c446	invoice-images	invoice_files/PMA-SA/BX2025080801/PMA-SA_BX2025080801_01_02.heic	\N	2025-08-12 04:16:09.790054+00	2025-08-12 04:16:09.790054+00	2025-08-12 04:16:09.790054+00	{"eTag": "\\"9f43290d6e7a7984fb07138d7941f2a6\\"", "size": 228819, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:16:10.000Z", "contentLength": 228819, "httpStatusCode": 200}	f001ced7-63de-4c49-8970-dc0468c475dc	\N	{}
5a1c07db-db35-4a08-afb8-1d371bcc1c9a	invoice-images	invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_01_01.heic	\N	2025-08-12 04:51:35.041619+00	2025-08-12 04:51:35.041619+00	2025-08-12 04:51:35.041619+00	{"eTag": "\\"c56231dd7a16a8168829c787f476ba67\\"", "size": 215660, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:51:35.000Z", "contentLength": 215660, "httpStatusCode": 200}	f8f657a7-2ed2-4e0a-946b-70f2f83d9a28	\N	{}
cc91f1aa-a661-4ab1-b926-695b9f48d630	invoice-images	invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_01_02.heic	\N	2025-08-12 04:51:35.279551+00	2025-08-12 04:51:35.279551+00	2025-08-12 04:51:35.279551+00	{"eTag": "\\"2ec67cec3381a78efe50ddf6a16e1b82\\"", "size": 216023, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:51:36.000Z", "contentLength": 216023, "httpStatusCode": 200}	edaeb1ee-a67d-43fa-94fc-ee6260ea635d	\N	{}
4da70c70-b7a0-4937-835f-f81a0aa389ab	invoice-images	invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_02_01.heic	\N	2025-08-12 04:51:35.449916+00	2025-08-12 04:51:35.449916+00	2025-08-12 04:51:35.449916+00	{"eTag": "\\"2be3d8d133181562cc0f8c9d82519b13\\"", "size": 69013, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:51:36.000Z", "contentLength": 69013, "httpStatusCode": 200}	af59c612-b4af-4d54-98dc-fbb71fed5d4e	\N	{}
b4025822-e74d-41c1-8111-9d63c5aeffd3	invoice-images	invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_01.heic	\N	2025-08-12 04:51:35.620067+00	2025-08-12 04:51:35.620067+00	2025-08-12 04:51:35.620067+00	{"eTag": "\\"716c25d5216da36095632e9bf24b5889\\"", "size": 70942, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:51:36.000Z", "contentLength": 70942, "httpStatusCode": 200}	ac3e358b-8b99-4123-b793-fccca346f31f	\N	{}
7164039d-4914-4e75-a485-d58a9b40fb68	invoice-images	invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_02.heic	\N	2025-08-12 04:51:35.766699+00	2025-08-12 04:51:35.766699+00	2025-08-12 04:51:35.766699+00	{"eTag": "\\"b0eab5e2ab0deecc8b8fd37473b7660e\\"", "size": 75150, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:51:36.000Z", "contentLength": 75150, "httpStatusCode": 200}	70a78b3f-6325-4cf1-8645-4c5a3f020421	\N	{}
b1b04aab-ec72-4d88-b688-716eebedbd19	invoice-images	invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_03.heic	\N	2025-08-12 04:51:35.924442+00	2025-08-12 04:51:35.924442+00	2025-08-12 04:51:35.924442+00	{"eTag": "\\"3ed1dff06bef14d3af7e34feaca6bbae\\"", "size": 75402, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:51:36.000Z", "contentLength": 75402, "httpStatusCode": 200}	8c3fe9f0-7b43-4e65-b5a3-e709ee339f71	\N	{}
a56a8d97-f489-4237-a2a5-36bc0d1c82b3	invoice-images	invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_04.heic	\N	2025-08-12 04:51:36.063098+00	2025-08-12 04:51:36.063098+00	2025-08-12 04:51:36.063098+00	{"eTag": "\\"ad368d7632246d0f194bbf4171e44df9\\"", "size": 75018, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:51:37.000Z", "contentLength": 75018, "httpStatusCode": 200}	dfc563f3-9ae2-437c-981e-ce07423b72d6	\N	{}
e1d39f46-bba5-4df5-b807-3c134f43bf4b	invoice-images	invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_04_01.heic	\N	2025-08-12 04:51:36.219136+00	2025-08-12 04:51:36.219136+00	2025-08-12 04:51:36.219136+00	{"eTag": "\\"b2a59c20bf25695fef807782326f9781\\"", "size": 77270, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:51:37.000Z", "contentLength": 77270, "httpStatusCode": 200}	4020c67d-bb6f-4ae5-9c19-3817501dee24	\N	{}
33b8e184-491b-4360-8ce0-4ad83d5ea5c9	invoice-images	invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_04_02.heic	\N	2025-08-12 04:51:36.350747+00	2025-08-12 04:51:36.350747+00	2025-08-12 04:51:36.350747+00	{"eTag": "\\"f9000b065d60d31fa3b119c336da350b\\"", "size": 78051, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:51:37.000Z", "contentLength": 78051, "httpStatusCode": 200}	38db2611-7e55-4ca4-97e8-1d1d9c8117d5	\N	{}
7a0fc56e-ea77-4d3c-abb8-2e09bbc3e6a0	invoice-images	invoice_files/PMA-SA/BX2025081203/PMA-SA_BX2025081203_01_01.heic	\N	2025-08-12 04:57:39.220285+00	2025-08-12 04:57:39.220285+00	2025-08-12 04:57:39.220285+00	{"eTag": "\\"fb90c0ccd0a8de6816c63d4a42815613\\"", "size": 1168148, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T04:57:40.000Z", "contentLength": 1168148, "httpStatusCode": 200}	ba4f78a1-57f5-4441-b3c2-cda82ab4c8ad	\N	{}
15f1e759-975b-4798-8261-8b69bdc0a712	invoice-images	.emptyFolderPlaceholder	\N	2025-08-10 04:41:22.320277+00	2025-08-10 04:41:22.320277+00	2025-08-10 04:41:22.320277+00	{"eTag": "\\"d41d8cd98f00b204e9800998ecf8427e\\"", "size": 0, "mimetype": "application/octet-stream", "cacheControl": "max-age=3600", "lastModified": "2025-08-10T04:41:22.314Z", "contentLength": 0, "httpStatusCode": 200}	c7c2d35a-af6d-4974-b68f-dcec42963a8f	\N	{}
585e746b-fb85-4347-89f5-e44adef9c502	invoice-images	expense_invoices/1/expense_invoice_1_05d9477e.png	\N	2025-08-10 05:06:21.899406+00	2025-08-10 05:06:21.899406+00	2025-08-10 05:06:21.899406+00	{"eTag": "\\"97a518226f6943bea4d310fb79feea7b\\"", "size": 18857, "mimetype": "image/png", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:06:22.000Z", "contentLength": 18857, "httpStatusCode": 200}	3f4552e9-8cab-4a1c-81e1-a6e37dd50ac4	\N	{}
f4755b83-17d5-4027-8f0d-a361790dcaa7	invoice-images	expense_invoices/15/expense_invoice_15_68530fe9.heic	\N	2025-08-10 05:07:58.592963+00	2025-08-10 05:07:58.592963+00	2025-08-10 05:07:58.592963+00	{"eTag": "\\"4879fef0a104afb2b576f47287e79f3b\\"", "size": 37004, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:07:59.000Z", "contentLength": 37004, "httpStatusCode": 200}	f86d19c3-34c5-4ebd-bc96-65ba39de7940	\N	{}
aad5c40f-a16f-4948-b477-e1b4e34d113e	invoice-images	invoice_files/PMA-SA/BX2025081204/PMA-SA_BX2025081204_01_01.heic	\N	2025-08-12 05:17:00.886545+00	2025-08-12 05:17:00.886545+00	2025-08-12 05:17:00.886545+00	{"eTag": "\\"cad5afd29891d00648691fef218011d2\\"", "size": 136454, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T05:17:01.000Z", "contentLength": 136454, "httpStatusCode": 200}	b8910536-c71c-41bd-8d88-6060488e20d7	\N	{}
d7460b55-64c8-4631-8279-b6ab631a6c22	invoice-images	invoice_files/PMA-SA/BX2025081204/PMA-SA_BX2025081204_02_01.heic	\N	2025-08-12 05:17:01.086281+00	2025-08-12 05:17:01.086281+00	2025-08-12 05:17:01.086281+00	{"eTag": "\\"b1820d2619cf16728842da56d7df5306\\"", "size": 141151, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T05:17:02.000Z", "contentLength": 141151, "httpStatusCode": 200}	97f4f18a-c935-47a5-869c-f1f6634dec4f	\N	{}
ee5deceb-1159-40af-b369-2234019b3925	invoice-images	invoice_files/PMA-SA/BX2025081205/PMA-SA_BX2025081205_01_01.heic	\N	2025-08-12 05:19:09.919448+00	2025-08-12 05:19:09.919448+00	2025-08-12 05:19:09.919448+00	{"eTag": "\\"d9321e8537bc7325afc81a52ef21abe4\\"", "size": 252022, "mimetype": "image/jpeg", "cacheControl": "no-cache", "lastModified": "2025-08-12T05:19:10.000Z", "contentLength": 252022, "httpStatusCode": 200}	deaea26b-adad-4c09-b2b4-e23031dcccd8	\N	{}
24aa44e5-3a1e-4463-9d0d-d7d8869fd955	invoice-images	expense_invoices/34/expense_invoice_34_59ee03d5.heic	\N	2025-08-10 05:08:07.73707+00	2025-08-10 05:08:07.73707+00	2025-08-10 05:08:07.73707+00	{"eTag": "\\"f964818aa4bdcef72e09c945e4687b7d\\"", "size": 208221, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:08.000Z", "contentLength": 208221, "httpStatusCode": 200}	27048b25-4c42-4383-8c5b-7f1c52d5c8c1	\N	{}
bd04fade-3938-49ff-8d08-8bbf83290a9d	invoice-images	expense_invoices/34/expense_invoice_34_87c594aa.heic	\N	2025-08-10 05:08:08.597151+00	2025-08-10 05:08:08.597151+00	2025-08-10 05:08:08.597151+00	{"eTag": "\\"8a8f5bb39b0381d862734f07ad256c36\\"", "size": 68961, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:09.000Z", "contentLength": 68961, "httpStatusCode": 200}	6b5da670-9d55-4ae5-8c43-66944deb5ee1	\N	{}
43830a2a-9455-464c-8b8f-94b5e7ee6abe	invoice-images	expense_invoices/35/expense_invoice_35_830963c4.heic	\N	2025-08-10 05:08:11.198255+00	2025-08-10 05:08:11.198255+00	2025-08-10 05:08:11.198255+00	{"eTag": "\\"d1fc87adaf6e484889a21d813ba4c6b1\\"", "size": 47977, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:12.000Z", "contentLength": 47977, "httpStatusCode": 200}	73ab80a6-fe2f-437f-8bc5-35fbfa0532c8	\N	{}
45ad8570-d9f1-4a0f-b9b8-3ea4c94bea27	invoice-images	expense_invoices/36/expense_invoice_36_f5a54ff8.heic	\N	2025-08-10 05:08:13.362732+00	2025-08-10 05:08:13.362732+00	2025-08-10 05:08:13.362732+00	{"eTag": "\\"52e81ecb5fe81d3eccde6148cbe65fb1\\"", "size": 119857, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:14.000Z", "contentLength": 119857, "httpStatusCode": 200}	79114d3d-aa36-44bf-8c57-27ca11f41f4e	\N	{}
5ddb3bd7-389f-46cd-98c6-68ab1d06f757	invoice-images	expense_invoices/37/expense_invoice_37_2cdfc71c.heic	\N	2025-08-10 05:08:14.398093+00	2025-08-10 05:08:14.398093+00	2025-08-10 05:08:14.398093+00	{"eTag": "\\"19ad13b2aef58a1c2dd73c2025f5825d\\"", "size": 612614, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:15.000Z", "contentLength": 612614, "httpStatusCode": 200}	d40e8395-063d-4264-9b1d-4ebdf392ac7a	\N	{}
c7264559-87c3-41fb-9a29-ff72e7cbd5f2	invoice-images	expense_invoices/37/expense_invoice_37_7ad22409.heic	\N	2025-08-10 05:08:15.351475+00	2025-08-10 05:08:15.351475+00	2025-08-10 05:08:15.351475+00	{"eTag": "\\"c918b62c8be220793d8fb5ccbfc9c4bc\\"", "size": 811524, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:16.000Z", "contentLength": 811524, "httpStatusCode": 200}	948b0c99-816a-4bba-b649-de649657abe8	\N	{}
d305fed3-3f96-4a60-b488-60d5e8190b55	invoice-images	expense_invoices/38/expense_invoice_38_91e4b11a.heic	\N	2025-08-10 05:08:18.179308+00	2025-08-10 05:08:18.179308+00	2025-08-10 05:08:18.179308+00	{"eTag": "\\"f15a9e9c4928e2568258aa9a451f5757\\"", "size": 50717, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:19.000Z", "contentLength": 50717, "httpStatusCode": 200}	e0d5732b-f78f-4339-8621-c0ca22183cb9	\N	{}
0fba58a9-6d41-48e8-bb27-0afa24f46801	invoice-images	expense_invoices/40/expense_invoice_40_6bea3174.heic	\N	2025-08-10 05:08:19.109919+00	2025-08-10 05:08:19.109919+00	2025-08-10 05:08:19.109919+00	{"eTag": "\\"ec191c121feb93addf889f17381e2f85\\"", "size": 19159, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:20.000Z", "contentLength": 19159, "httpStatusCode": 200}	3edec8f2-0b71-40b6-89eb-00cf2265816d	\N	{}
b7528a79-c39b-459e-be2c-2d0b693c205d	invoice-images	expense_invoices/41/expense_invoice_41_cbe9076d.heic	\N	2025-08-10 05:08:20.044218+00	2025-08-10 05:08:20.044218+00	2025-08-10 05:08:20.044218+00	{"eTag": "\\"f15a9e9c4928e2568258aa9a451f5757\\"", "size": 50717, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:21.000Z", "contentLength": 50717, "httpStatusCode": 200}	7f1dc389-5bec-4490-8ef9-c48d1abde205	\N	{}
047e46da-ea6e-4cae-a1d0-a0b3bc02a58d	invoice-images	expense_invoices/41/expense_invoice_41_cd9c2b1a.png	\N	2025-08-10 05:08:20.978454+00	2025-08-10 05:08:20.978454+00	2025-08-10 05:08:20.978454+00	{"eTag": "\\"97a518226f6943bea4d310fb79feea7b\\"", "size": 18857, "mimetype": "image/png", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:21.000Z", "contentLength": 18857, "httpStatusCode": 200}	4784af62-cbe3-498d-b32f-370e1fb96ab4	\N	{}
bea85dcc-ec87-4203-9b0e-b9bd9380d3ea	invoice-images	expense_invoices/42/expense_invoice_42_414d6b96.png	\N	2025-08-10 05:08:21.924402+00	2025-08-10 05:08:21.924402+00	2025-08-10 05:08:21.924402+00	{"eTag": "\\"97a518226f6943bea4d310fb79feea7b\\"", "size": 18857, "mimetype": "image/png", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:22.000Z", "contentLength": 18857, "httpStatusCode": 200}	18d56b38-e8e6-4528-909d-ddd731379eae	\N	{}
7697d78b-f9e6-4120-929d-6274bd6375af	invoice-images	expense_invoices/43/expense_invoice_43_25ee8c3b.heic	\N	2025-08-10 05:08:22.924154+00	2025-08-10 05:08:22.924154+00	2025-08-10 05:08:22.924154+00	{"eTag": "\\"f964818aa4bdcef72e09c945e4687b7d\\"", "size": 208221, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:23.000Z", "contentLength": 208221, "httpStatusCode": 200}	da0dc99a-e384-4056-88c7-27f534ba11b8	\N	{}
8e83ddf2-0c0f-4dd2-abf8-f85fdeade4f1	invoice-images	expense_invoices/43/expense_invoice_43_68b16fc0.png	\N	2025-08-10 05:08:23.763595+00	2025-08-10 05:08:23.763595+00	2025-08-10 05:08:23.763595+00	{"eTag": "\\"16817241a065328b83a44b32416e867c\\"", "size": 45044, "mimetype": "image/png", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:24.000Z", "contentLength": 45044, "httpStatusCode": 200}	2b249282-17fb-4def-b845-5d8c4d463353	\N	{}
135e3065-bbdb-4679-b530-8422b3f79594	invoice-images	expense_invoices/44/expense_invoice_44_4a0d68ed.heic	\N	2025-08-10 05:08:24.769256+00	2025-08-10 05:08:24.769256+00	2025-08-10 05:08:24.769256+00	{"eTag": "\\"52e81ecb5fe81d3eccde6148cbe65fb1\\"", "size": 119857, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:25.000Z", "contentLength": 119857, "httpStatusCode": 200}	46a9486f-2d72-4502-a883-670831342072	\N	{}
7734a20a-1fd6-46d4-9ea2-e19cb71779a4	invoice-images	expense_invoices/49/expense_invoice_49_85c850f7.png	\N	2025-08-10 05:08:25.681315+00	2025-08-10 05:08:25.681315+00	2025-08-10 05:08:25.681315+00	{"eTag": "\\"97a518226f6943bea4d310fb79feea7b\\"", "size": 18857, "mimetype": "image/png", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:26.000Z", "contentLength": 18857, "httpStatusCode": 200}	8a851580-4d58-4f55-ab8a-84c7ae07fffa	\N	{}
b6058553-4e30-4523-bb2b-02da4a37aa15	invoice-images	expense_invoices/50/expense_invoice_50_c7182457.png	\N	2025-08-10 05:08:26.549946+00	2025-08-10 05:08:26.549946+00	2025-08-10 05:08:26.549946+00	{"eTag": "\\"97a518226f6943bea4d310fb79feea7b\\"", "size": 18857, "mimetype": "image/png", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:27.000Z", "contentLength": 18857, "httpStatusCode": 200}	e0955a55-ee26-4e7b-a913-b81a04d55962	\N	{}
d4be3d5e-496f-4e71-abb8-898d152593b1	invoice-images	expense_invoices/51/expense_invoice_51_5c31ddf3.png	\N	2025-08-10 05:08:27.464008+00	2025-08-10 05:08:27.464008+00	2025-08-10 05:08:27.464008+00	{"eTag": "\\"97a518226f6943bea4d310fb79feea7b\\"", "size": 18857, "mimetype": "image/png", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:28.000Z", "contentLength": 18857, "httpStatusCode": 200}	03cc47bd-454e-42bd-92c1-31eac0ceb8db	\N	{}
1a7ae9f4-438d-4f04-bd3c-757f98c1e474	invoice-images	expense_invoices/53/expense_invoice_53_302cfdfa.heic	\N	2025-08-10 05:08:28.538236+00	2025-08-10 05:08:28.538236+00	2025-08-10 05:08:28.538236+00	{"eTag": "\\"c918b62c8be220793d8fb5ccbfc9c4bc\\"", "size": 811524, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:29.000Z", "contentLength": 811524, "httpStatusCode": 200}	d68c6a4b-ed22-4c08-a4bb-0f387b49a8dd	\N	{}
18eba52c-cb60-40f0-b50d-34c3ee3d5ab5	invoice-images	expense_invoices/53/expense_invoice_53_5fa1e174.heic	\N	2025-08-10 05:08:29.815848+00	2025-08-10 05:08:29.815848+00	2025-08-10 05:08:29.815848+00	{"eTag": "\\"19ad13b2aef58a1c2dd73c2025f5825d\\"", "size": 612614, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:30.000Z", "contentLength": 612614, "httpStatusCode": 200}	d0fe551e-9bff-4030-98c7-d911a81629d6	\N	{}
873989cb-76d9-47bd-84bc-3a9ae3ab0ac0	invoice-images	expense_invoices/54/expense_invoice_54_7cfefb23.heic	\N	2025-08-10 05:08:30.905869+00	2025-08-10 05:08:30.905869+00	2025-08-10 05:08:30.905869+00	{"eTag": "\\"f15a9e9c4928e2568258aa9a451f5757\\"", "size": 50717, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:31.000Z", "contentLength": 50717, "httpStatusCode": 200}	117b7ffe-8024-4e15-aab7-e65c26040516	\N	{}
b8182034-8de3-480d-aa26-25b5eceee64d	invoice-images	expense_invoices/56/expense_invoice_56_3fceaaad.heic	\N	2025-08-10 05:08:32.134884+00	2025-08-10 05:08:32.134884+00	2025-08-10 05:08:32.134884+00	{"eTag": "\\"f15a9e9c4928e2568258aa9a451f5757\\"", "size": 50717, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:33.000Z", "contentLength": 50717, "httpStatusCode": 200}	3cacce45-7c14-41ab-a1ac-aa04b33a032e	\N	{}
230c1a8f-a37f-41b5-a684-b5ba326a4979	invoice-images	expense_invoices/61/expense_invoice_61_3c93f4c5.heic	\N	2025-08-10 05:08:33.075094+00	2025-08-10 05:08:33.075094+00	2025-08-10 05:08:33.075094+00	{"eTag": "\\"ec191c121feb93addf889f17381e2f85\\"", "size": 19159, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:34.000Z", "contentLength": 19159, "httpStatusCode": 200}	6e2e5ea1-33c3-4e60-af9d-86c54e87ae72	\N	{}
34d9485f-863d-425f-8c3b-36817cea314f	invoice-images	expense_invoices/62/expense_invoice_62_41e3b5e5.heic	\N	2025-08-10 05:08:34.281144+00	2025-08-10 05:08:34.281144+00	2025-08-10 05:08:34.281144+00	{"eTag": "\\"4879fef0a104afb2b576f47287e79f3b\\"", "size": 37004, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:35.000Z", "contentLength": 37004, "httpStatusCode": 200}	8367b464-d633-4632-b46f-3bc0b8334e88	\N	{}
d2ca56c9-a717-4906-911e-b9938d2f0a2e	invoice-images	expense_invoices/62/expense_invoice_62_e3e46d67.heic	\N	2025-08-10 05:08:35.1426+00	2025-08-10 05:08:35.1426+00	2025-08-10 05:08:35.1426+00	{"eTag": "\\"f15a9e9c4928e2568258aa9a451f5757\\"", "size": 50717, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:36.000Z", "contentLength": 50717, "httpStatusCode": 200}	6b96497f-7090-46b4-9b54-b14d87e60d83	\N	{}
7e784f6d-3754-4b6c-bcfa-e1a8564f3375	invoice-images	expense_invoices/63/expense_invoice_63_395321ef.heic	\N	2025-08-10 05:08:36.111545+00	2025-08-10 05:08:36.111545+00	2025-08-10 05:08:36.111545+00	{"eTag": "\\"f15a9e9c4928e2568258aa9a451f5757\\"", "size": 50717, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:37.000Z", "contentLength": 50717, "httpStatusCode": 200}	72708cf2-5f85-4292-bf33-07ff3728226a	\N	{}
f705362d-32bb-42c6-8a11-0618324f486f	invoice-images	expense_invoices/64/expense_invoice_64_06637d55.heic	\N	2025-08-10 05:08:37.1054+00	2025-08-10 05:08:37.1054+00	2025-08-10 05:08:37.1054+00	{"eTag": "\\"ec27d09dc3ed6edb8a8de083cfa58586\\"", "size": 72030, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:38.000Z", "contentLength": 72030, "httpStatusCode": 200}	534954e9-d0a9-4a8a-825e-6f164e9570fa	\N	{}
923d9aaf-897c-4484-9fba-d18f6277f233	invoice-images	expense_invoices/64/expense_invoice_64_207b97d5.heic	\N	2025-08-10 05:08:38.099806+00	2025-08-10 05:08:38.099806+00	2025-08-10 05:08:38.099806+00	{"eTag": "\\"f964818aa4bdcef72e09c945e4687b7d\\"", "size": 208221, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:39.000Z", "contentLength": 208221, "httpStatusCode": 200}	2b97cec5-98a4-4f08-bda2-d02dd77ba474	\N	{}
fb4fbd91-4aee-4ae5-85ff-de9c309f5ae1	invoice-images	expense_invoices/64/expense_invoice_64_eb4509d3.heic	\N	2025-08-10 05:08:39.048685+00	2025-08-10 05:08:39.048685+00	2025-08-10 05:08:39.048685+00	{"eTag": "\\"8a8f5bb39b0381d862734f07ad256c36\\"", "size": 68961, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:40.000Z", "contentLength": 68961, "httpStatusCode": 200}	a3180744-02cb-49a0-9321-313ed0791231	\N	{}
8cd921f8-85d0-4163-a316-fe9773320327	invoice-images	expense_invoices/64/expense_invoice_64_fe1c4c72.heic	\N	2025-08-10 05:08:40.345873+00	2025-08-10 05:08:40.345873+00	2025-08-10 05:08:40.345873+00	{"eTag": "\\"f964818aa4bdcef72e09c945e4687b7d\\"", "size": 208221, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:41.000Z", "contentLength": 208221, "httpStatusCode": 200}	bef41744-dc6c-4a31-8521-82a19e7b9ab6	\N	{}
858ea470-61f3-46ef-b01f-0bedca5ebd82	invoice-images	expense_invoices/65/expense_invoice_65_46147d44.heic	\N	2025-08-10 05:08:41.60553+00	2025-08-10 05:08:41.60553+00	2025-08-10 05:08:41.60553+00	{"eTag": "\\"19ad13b2aef58a1c2dd73c2025f5825d\\"", "size": 612614, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:42.000Z", "contentLength": 612614, "httpStatusCode": 200}	383af0c1-1426-4031-8a3b-cb7c24379f13	\N	{}
db07a6f6-d5ed-4206-b68f-6c27e1e8c57f	invoice-images	expense_invoices/65/expense_invoice_65_8e0ce237.heic	\N	2025-08-10 05:08:42.817437+00	2025-08-10 05:08:42.817437+00	2025-08-10 05:08:42.817437+00	{"eTag": "\\"c918b62c8be220793d8fb5ccbfc9c4bc\\"", "size": 811524, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:43.000Z", "contentLength": 811524, "httpStatusCode": 200}	d104e103-bc28-43e6-94af-8831f1ee9786	\N	{}
5b5e0311-575f-40eb-b296-eb5f01318bea	invoice-images	expense_invoices/65/expense_invoice_65_baf7db35.heic	\N	2025-08-10 05:08:43.756267+00	2025-08-10 05:08:43.756267+00	2025-08-10 05:08:43.756267+00	{"eTag": "\\"52e81ecb5fe81d3eccde6148cbe65fb1\\"", "size": 119857, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:44.000Z", "contentLength": 119857, "httpStatusCode": 200}	46c6ce0e-4544-431c-a1e1-663d3cab322a	\N	{}
01cfc761-d0a6-4f44-8725-a6670a17fb4f	invoice-images	expense_invoices/66/expense_invoice_66_77e7a254.heic	\N	2025-08-10 05:08:44.833349+00	2025-08-10 05:08:44.833349+00	2025-08-10 05:08:44.833349+00	{"eTag": "\\"19ad13b2aef58a1c2dd73c2025f5825d\\"", "size": 612614, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:45.000Z", "contentLength": 612614, "httpStatusCode": 200}	49676b0d-f059-4115-91d9-11b24d8c6ff7	\N	{}
5904165b-662a-44dc-bd6c-216e1066a0c5	invoice-images	expense_invoices/66/expense_invoice_66_7c05e6f8.heic	\N	2025-08-10 05:08:45.895377+00	2025-08-10 05:08:45.895377+00	2025-08-10 05:08:45.895377+00	{"eTag": "\\"c918b62c8be220793d8fb5ccbfc9c4bc\\"", "size": 811524, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:46.000Z", "contentLength": 811524, "httpStatusCode": 200}	c2152e54-7d68-4be0-a44e-967172b2b423	\N	{}
14a73d16-d40a-4aa8-bdcd-836af5e926f1	invoice-images	expense_invoices/67/expense_invoice_67_864886d2.heic	\N	2025-08-10 05:08:46.956375+00	2025-08-10 05:08:46.956375+00	2025-08-10 05:08:46.956375+00	{"eTag": "\\"c918b62c8be220793d8fb5ccbfc9c4bc\\"", "size": 811524, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:47.000Z", "contentLength": 811524, "httpStatusCode": 200}	7304634b-4f87-4baa-b296-8cc8d51737f2	\N	{}
715eecd3-2dbd-40da-9180-6fe6b348ad34	invoice-images	expense_invoices/67/expense_invoice_67_a88872eb.heic	\N	2025-08-10 05:08:47.929383+00	2025-08-10 05:08:47.929383+00	2025-08-10 05:08:47.929383+00	{"eTag": "\\"19ad13b2aef58a1c2dd73c2025f5825d\\"", "size": 612614, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:48.000Z", "contentLength": 612614, "httpStatusCode": 200}	de914bae-03d3-493b-a0f6-eab2da827834	\N	{}
c8390767-4b58-48a9-b406-6799511bf0c8	invoice-images	expense_invoices/68/expense_invoice_68_2450c9c1.heic	\N	2025-08-10 05:08:49.019027+00	2025-08-10 05:08:49.019027+00	2025-08-10 05:08:49.019027+00	{"eTag": "\\"c918b62c8be220793d8fb5ccbfc9c4bc\\"", "size": 811524, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:49.000Z", "contentLength": 811524, "httpStatusCode": 200}	6306e5de-e7fc-4e5e-ba0f-621e71933d2a	\N	{}
09157f01-a1c5-47f2-b115-b19aab79f732	invoice-images	expense_invoices/68/expense_invoice_68_6285fb01.heic	\N	2025-08-10 05:08:49.873204+00	2025-08-10 05:08:49.873204+00	2025-08-10 05:08:49.873204+00	{"eTag": "\\"52e81ecb5fe81d3eccde6148cbe65fb1\\"", "size": 119857, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:50.000Z", "contentLength": 119857, "httpStatusCode": 200}	5073c212-0bc1-4709-982c-3f9024346ec5	\N	{}
cbdbd88c-54c1-4587-a3ba-6cddc8272212	invoice-images	expense_invoices/69/expense_invoice_69_52152bcc.heic	\N	2025-08-10 05:08:51.061883+00	2025-08-10 05:08:51.061883+00	2025-08-10 05:08:51.061883+00	{"eTag": "\\"19ad13b2aef58a1c2dd73c2025f5825d\\"", "size": 612614, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:52.000Z", "contentLength": 612614, "httpStatusCode": 200}	c8cca83a-0b02-429a-8d3c-0eb27885fc2e	\N	{}
e7e77bfe-b454-4fa5-8552-2ccdebddd7d9	invoice-images	expense_invoices/69/expense_invoice_69_c8c50459.heic	\N	2025-08-10 05:08:52.010053+00	2025-08-10 05:08:52.010053+00	2025-08-10 05:08:52.010053+00	{"eTag": "\\"c918b62c8be220793d8fb5ccbfc9c4bc\\"", "size": 811524, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:52.000Z", "contentLength": 811524, "httpStatusCode": 200}	505d9772-9e74-4cd9-b74c-9f41b839a889	\N	{}
73422653-4ea2-42af-886c-f07579bb0aae	invoice-images	expense_invoices/69/expense_invoice_69_f20fed5d.heic	\N	2025-08-10 05:08:52.847484+00	2025-08-10 05:08:52.847484+00	2025-08-10 05:08:52.847484+00	{"eTag": "\\"52e81ecb5fe81d3eccde6148cbe65fb1\\"", "size": 119857, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:53.000Z", "contentLength": 119857, "httpStatusCode": 200}	35b778af-825f-41a8-9a59-fc3029e11a16	\N	{}
a1f1451c-11c0-4cb9-b5be-01daa1bc92ec	invoice-images	expense_invoices/70/expense_invoice_70_6034f46e.heic	\N	2025-08-10 05:08:53.892134+00	2025-08-10 05:08:53.892134+00	2025-08-10 05:08:53.892134+00	{"eTag": "\\"19ad13b2aef58a1c2dd73c2025f5825d\\"", "size": 612614, "mimetype": "application/octet-stream", "cacheControl": "no-cache", "lastModified": "2025-08-10T05:08:54.000Z", "contentLength": 612614, "httpStatusCode": 200}	55ae7a68-5d43-4320-a618-877ea995cdee	\N	{}
\.


--
-- TOC entry 4744 (class 0 OID 17211)
-- Dependencies: 270
-- Data for Name: s3_multipart_uploads; Type: TABLE DATA; Schema: storage; Owner: -
--

COPY storage.s3_multipart_uploads (id, in_progress_size, upload_signature, bucket_id, key, version, owner_id, created_at, user_metadata) FROM stdin;
\.


--
-- TOC entry 4745 (class 0 OID 17225)
-- Dependencies: 271
-- Data for Name: s3_multipart_uploads_parts; Type: TABLE DATA; Schema: storage; Owner: -
--

COPY storage.s3_multipart_uploads_parts (id, upload_id, size, part_number, bucket_id, key, etag, owner_id, version, created_at) FROM stdin;
\.


--
-- TOC entry 3868 (class 0 OID 16656)
-- Dependencies: 249
-- Data for Name: secrets; Type: TABLE DATA; Schema: vault; Owner: -
--

COPY vault.secrets (id, name, description, secret, key_id, nonce, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 5242 (class 0 OID 0)
-- Dependencies: 241
-- Name: refresh_tokens_id_seq; Type: SEQUENCE SET; Schema: auth; Owner: -
--

SELECT pg_catalog.setval('auth.refresh_tokens_id_seq', 1, false);


--
-- TOC entry 5243 (class 0 OID 0)
-- Dependencies: 273
-- Name: action_reply_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.action_reply_id_seq', 4, true);


--
-- TOC entry 5244 (class 0 OID 0)
-- Dependencies: 275
-- Name: actions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.actions_id_seq', 62, true);


--
-- TOC entry 5245 (class 0 OID 0)
-- Dependencies: 277
-- Name: affiliations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.affiliations_id_seq', 16, true);


--
-- TOC entry 5246 (class 0 OID 0)
-- Dependencies: 280
-- Name: approval_instance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_instance_id_seq', 11, true);


--
-- TOC entry 5247 (class 0 OID 0)
-- Dependencies: 282
-- Name: approval_process_template_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_process_template_id_seq', 5, true);


--
-- TOC entry 5248 (class 0 OID 0)
-- Dependencies: 283
-- Name: approval_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_record_id_seq', 13, true);


--
-- TOC entry 5249 (class 0 OID 0)
-- Dependencies: 286
-- Name: approval_step_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.approval_step_id_seq', 7, true);


--
-- TOC entry 5250 (class 0 OID 0)
-- Dependencies: 288
-- Name: change_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.change_logs_id_seq', 527, true);


--
-- TOC entry 5251 (class 0 OID 0)
-- Dependencies: 290
-- Name: companies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.companies_id_seq', 73, true);


--
-- TOC entry 5252 (class 0 OID 0)
-- Dependencies: 292
-- Name: company_assets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.company_assets_id_seq', 1, false);


--
-- TOC entry 5253 (class 0 OID 0)
-- Dependencies: 294
-- Name: contacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contacts_id_seq', 93, true);


--
-- TOC entry 5254 (class 0 OID 0)
-- Dependencies: 409
-- Name: data_field_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.data_field_config_id_seq', 6, true);


--
-- TOC entry 5255 (class 0 OID 0)
-- Dependencies: 403
-- Name: data_table_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.data_table_config_id_seq', 9, true);


--
-- TOC entry 5256 (class 0 OID 0)
-- Dependencies: 296
-- Name: departments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.departments_id_seq', 1, false);


--
-- TOC entry 5257 (class 0 OID 0)
-- Dependencies: 298
-- Name: dev_product_specs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dev_product_specs_id_seq', 1, false);


--
-- TOC entry 5258 (class 0 OID 0)
-- Dependencies: 300
-- Name: dev_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dev_products_id_seq', 1, false);


--
-- TOC entry 5259 (class 0 OID 0)
-- Dependencies: 302
-- Name: dictionaries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dictionaries_id_seq', 11, true);


--
-- TOC entry 5260 (class 0 OID 0)
-- Dependencies: 304
-- Name: event_registry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.event_registry_id_seq', 1, false);


--
-- TOC entry 5261 (class 0 OID 0)
-- Dependencies: 306
-- Name: expense_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.expense_details_id_seq', 61, true);


--
-- TOC entry 5262 (class 0 OID 0)
-- Dependencies: 308
-- Name: expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.expenses_id_seq', 11, true);


--
-- TOC entry 5263 (class 0 OID 0)
-- Dependencies: 310
-- Name: feature_changes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.feature_changes_id_seq', 11, true);


--
-- TOC entry 5264 (class 0 OID 0)
-- Dependencies: 312
-- Name: five_star_project_baselines_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.five_star_project_baselines_id_seq', 1, true);


--
-- TOC entry 5265 (class 0 OID 0)
-- Dependencies: 405
-- Name: formula_templates_extended_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.formula_templates_extended_id_seq', 3, true);


--
-- TOC entry 5266 (class 0 OID 0)
-- Dependencies: 314
-- Name: inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_id_seq', 1, false);


--
-- TOC entry 5267 (class 0 OID 0)
-- Dependencies: 316
-- Name: inventory_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inventory_transactions_id_seq', 1, false);


--
-- TOC entry 5268 (class 0 OID 0)
-- Dependencies: 399
-- Name: performance_formula_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.performance_formula_templates_id_seq', 1, false);


--
-- TOC entry 5269 (class 0 OID 0)
-- Dependencies: 395
-- Name: performance_metrics_definition_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.performance_metrics_definition_id_seq', 1, false);


--
-- TOC entry 5270 (class 0 OID 0)
-- Dependencies: 318
-- Name: performance_statistics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.performance_statistics_id_seq', 12, true);


--
-- TOC entry 5271 (class 0 OID 0)
-- Dependencies: 320
-- Name: performance_targets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.performance_targets_id_seq', 1, false);


--
-- TOC entry 5272 (class 0 OID 0)
-- Dependencies: 322
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.permissions_id_seq', 19, true);


--
-- TOC entry 5273 (class 0 OID 0)
-- Dependencies: 324
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pricing_order_approval_records_id_seq', 1, false);


--
-- TOC entry 5274 (class 0 OID 0)
-- Dependencies: 326
-- Name: pricing_order_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pricing_order_details_id_seq', 1, false);


--
-- TOC entry 5275 (class 0 OID 0)
-- Dependencies: 328
-- Name: pricing_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pricing_orders_id_seq', 1, false);


--
-- TOC entry 5276 (class 0 OID 0)
-- Dependencies: 330
-- Name: product_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_categories_id_seq', 1, false);


--
-- TOC entry 5277 (class 0 OID 0)
-- Dependencies: 332
-- Name: product_code_field_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_code_field_options_id_seq', 1, false);


--
-- TOC entry 5278 (class 0 OID 0)
-- Dependencies: 334
-- Name: product_code_field_values_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_code_field_values_id_seq', 1, false);


--
-- TOC entry 5279 (class 0 OID 0)
-- Dependencies: 336
-- Name: product_code_fields_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_code_fields_id_seq', 1, false);


--
-- TOC entry 5280 (class 0 OID 0)
-- Dependencies: 338
-- Name: product_codes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_codes_id_seq', 1, false);


--
-- TOC entry 5281 (class 0 OID 0)
-- Dependencies: 340
-- Name: product_regions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_regions_id_seq', 1, false);


--
-- TOC entry 5282 (class 0 OID 0)
-- Dependencies: 342
-- Name: product_subcategories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_subcategories_id_seq', 1, false);


--
-- TOC entry 5283 (class 0 OID 0)
-- Dependencies: 344
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.products_id_seq', 70, true);


--
-- TOC entry 5284 (class 0 OID 0)
-- Dependencies: 346
-- Name: project_customer_associations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_customer_associations_id_seq', 55, true);


--
-- TOC entry 5285 (class 0 OID 0)
-- Dependencies: 348
-- Name: project_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_members_id_seq', 1, false);


--
-- TOC entry 5286 (class 0 OID 0)
-- Dependencies: 350
-- Name: project_rating_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_rating_records_id_seq', 1, false);


--
-- TOC entry 5287 (class 0 OID 0)
-- Dependencies: 352
-- Name: project_scoring_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_scoring_config_id_seq', 1, false);


--
-- TOC entry 5288 (class 0 OID 0)
-- Dependencies: 354
-- Name: project_scoring_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_scoring_records_id_seq', 1, false);


--
-- TOC entry 5289 (class 0 OID 0)
-- Dependencies: 356
-- Name: project_stage_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_stage_history_id_seq', 79, true);


--
-- TOC entry 5290 (class 0 OID 0)
-- Dependencies: 358
-- Name: project_total_scores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_total_scores_id_seq', 32, true);


--
-- TOC entry 5291 (class 0 OID 0)
-- Dependencies: 360
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.projects_id_seq', 32, true);


--
-- TOC entry 5292 (class 0 OID 0)
-- Dependencies: 362
-- Name: purchase_order_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.purchase_order_details_id_seq', 1, false);


--
-- TOC entry 5293 (class 0 OID 0)
-- Dependencies: 364
-- Name: purchase_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.purchase_orders_id_seq', 1, false);


--
-- TOC entry 5294 (class 0 OID 0)
-- Dependencies: 366
-- Name: quotation_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.quotation_details_id_seq', 719, true);


--
-- TOC entry 5295 (class 0 OID 0)
-- Dependencies: 368
-- Name: quotations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.quotations_id_seq', 19, true);


--
-- TOC entry 5296 (class 0 OID 0)
-- Dependencies: 401
-- Name: role_performance_access_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.role_performance_access_id_seq', 1, false);


--
-- TOC entry 5297 (class 0 OID 0)
-- Dependencies: 397
-- Name: role_performance_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.role_performance_config_id_seq', 1, false);


--
-- TOC entry 5298 (class 0 OID 0)
-- Dependencies: 407
-- Name: role_performance_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.role_performance_items_id_seq', 1, false);


--
-- TOC entry 5299 (class 0 OID 0)
-- Dependencies: 370
-- Name: role_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.role_permissions_id_seq', 192, true);


--
-- TOC entry 5300 (class 0 OID 0)
-- Dependencies: 372
-- Name: settlement_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.settlement_details_id_seq', 1, false);


--
-- TOC entry 5301 (class 0 OID 0)
-- Dependencies: 374
-- Name: settlement_order_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.settlement_order_details_id_seq', 1, false);


--
-- TOC entry 5302 (class 0 OID 0)
-- Dependencies: 376
-- Name: settlement_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.settlement_orders_id_seq', 1, false);


--
-- TOC entry 5303 (class 0 OID 0)
-- Dependencies: 378
-- Name: settlements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.settlements_id_seq', 1, false);


--
-- TOC entry 5304 (class 0 OID 0)
-- Dependencies: 380
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solution_manager_email_settings_id_seq', 1, false);


--
-- TOC entry 5305 (class 0 OID 0)
-- Dependencies: 382
-- Name: system_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.system_metrics_id_seq', 1, false);


--
-- TOC entry 5306 (class 0 OID 0)
-- Dependencies: 384
-- Name: system_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.system_settings_id_seq', 2, true);


--
-- TOC entry 5307 (class 0 OID 0)
-- Dependencies: 386
-- Name: temp_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.temp_products_id_seq', 1, true);


--
-- TOC entry 5308 (class 0 OID 0)
-- Dependencies: 388
-- Name: upgrade_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.upgrade_logs_id_seq', 10, true);


--
-- TOC entry 5309 (class 0 OID 0)
-- Dependencies: 390
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_event_subscriptions_id_seq', 1, false);


--
-- TOC entry 5310 (class 0 OID 0)
-- Dependencies: 392
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 12, true);


--
-- TOC entry 5311 (class 0 OID 0)
-- Dependencies: 394
-- Name: version_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.version_records_id_seq', 11, true);


--
-- TOC entry 5312 (class 0 OID 0)
-- Dependencies: 265
-- Name: subscription_id_seq; Type: SEQUENCE SET; Schema: realtime; Owner: -
--

SELECT pg_catalog.setval('realtime.subscription_id_seq', 1, false);


--
-- TOC entry 4124 (class 2606 OID 16825)
-- Name: mfa_amr_claims amr_id_pk; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT amr_id_pk PRIMARY KEY (id);


--
-- TOC entry 4082 (class 2606 OID 16529)
-- Name: audit_log_entries audit_log_entries_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.audit_log_entries
    ADD CONSTRAINT audit_log_entries_pkey PRIMARY KEY (id);


--
-- TOC entry 4146 (class 2606 OID 16931)
-- Name: flow_state flow_state_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.flow_state
    ADD CONSTRAINT flow_state_pkey PRIMARY KEY (id);


--
-- TOC entry 4103 (class 2606 OID 16949)
-- Name: identities identities_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_pkey PRIMARY KEY (id);


--
-- TOC entry 4105 (class 2606 OID 16959)
-- Name: identities identities_provider_id_provider_unique; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_provider_id_provider_unique UNIQUE (provider_id, provider);


--
-- TOC entry 4080 (class 2606 OID 16522)
-- Name: instances instances_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.instances
    ADD CONSTRAINT instances_pkey PRIMARY KEY (id);


--
-- TOC entry 4126 (class 2606 OID 16818)
-- Name: mfa_amr_claims mfa_amr_claims_session_id_authentication_method_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT mfa_amr_claims_session_id_authentication_method_pkey UNIQUE (session_id, authentication_method);


--
-- TOC entry 4122 (class 2606 OID 16806)
-- Name: mfa_challenges mfa_challenges_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_challenges
    ADD CONSTRAINT mfa_challenges_pkey PRIMARY KEY (id);


--
-- TOC entry 4114 (class 2606 OID 16999)
-- Name: mfa_factors mfa_factors_last_challenged_at_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_last_challenged_at_key UNIQUE (last_challenged_at);


--
-- TOC entry 4116 (class 2606 OID 16793)
-- Name: mfa_factors mfa_factors_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_pkey PRIMARY KEY (id);


--
-- TOC entry 4150 (class 2606 OID 16984)
-- Name: one_time_tokens one_time_tokens_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.one_time_tokens
    ADD CONSTRAINT one_time_tokens_pkey PRIMARY KEY (id);


--
-- TOC entry 4074 (class 2606 OID 16512)
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- TOC entry 4077 (class 2606 OID 16736)
-- Name: refresh_tokens refresh_tokens_token_unique; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_token_unique UNIQUE (token);


--
-- TOC entry 4135 (class 2606 OID 16865)
-- Name: saml_providers saml_providers_entity_id_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_entity_id_key UNIQUE (entity_id);


--
-- TOC entry 4137 (class 2606 OID 16863)
-- Name: saml_providers saml_providers_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_pkey PRIMARY KEY (id);


--
-- TOC entry 4142 (class 2606 OID 16879)
-- Name: saml_relay_states saml_relay_states_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_pkey PRIMARY KEY (id);


--
-- TOC entry 4085 (class 2606 OID 16535)
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- TOC entry 4109 (class 2606 OID 16757)
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- TOC entry 4132 (class 2606 OID 16846)
-- Name: sso_domains sso_domains_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sso_domains
    ADD CONSTRAINT sso_domains_pkey PRIMARY KEY (id);


--
-- TOC entry 4128 (class 2606 OID 16837)
-- Name: sso_providers sso_providers_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sso_providers
    ADD CONSTRAINT sso_providers_pkey PRIMARY KEY (id);


--
-- TOC entry 4067 (class 2606 OID 16919)
-- Name: users users_phone_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_phone_key UNIQUE (phone);


--
-- TOC entry 4069 (class 2606 OID 16499)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4168 (class 2606 OID 24464)
-- Name: action_reply action_reply_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_pkey PRIMARY KEY (id);


--
-- TOC entry 4170 (class 2606 OID 24466)
-- Name: actions actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_pkey PRIMARY KEY (id);


--
-- TOC entry 4172 (class 2606 OID 24468)
-- Name: affiliations affiliations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_pkey PRIMARY KEY (id);


--
-- TOC entry 4176 (class 2606 OID 24470)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 4178 (class 2606 OID 24472)
-- Name: approval_instance approval_instance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_pkey PRIMARY KEY (id);


--
-- TOC entry 4180 (class 2606 OID 24474)
-- Name: approval_process_template approval_process_template_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_pkey PRIMARY KEY (id);


--
-- TOC entry 4182 (class 2606 OID 24476)
-- Name: approval_record approval_record_temp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_temp_pkey PRIMARY KEY (id);


--
-- TOC entry 4184 (class 2606 OID 24478)
-- Name: approval_step approval_step_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_pkey PRIMARY KEY (id);


--
-- TOC entry 4186 (class 2606 OID 24480)
-- Name: change_logs change_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs
    ADD CONSTRAINT change_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 4188 (class 2606 OID 24482)
-- Name: companies companies_company_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_company_code_key UNIQUE (company_code);


--
-- TOC entry 4190 (class 2606 OID 24484)
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- TOC entry 4192 (class 2606 OID 24486)
-- Name: company_assets company_assets_asset_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_assets
    ADD CONSTRAINT company_assets_asset_key_key UNIQUE (asset_key);


--
-- TOC entry 4194 (class 2606 OID 24488)
-- Name: company_assets company_assets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_assets
    ADD CONSTRAINT company_assets_pkey PRIMARY KEY (id);


--
-- TOC entry 4196 (class 2606 OID 24490)
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (id);


--
-- TOC entry 4405 (class 2606 OID 26542)
-- Name: data_field_config data_field_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_field_config
    ADD CONSTRAINT data_field_config_pkey PRIMARY KEY (id);


--
-- TOC entry 4393 (class 2606 OID 26484)
-- Name: data_table_config data_table_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_table_config
    ADD CONSTRAINT data_table_config_pkey PRIMARY KEY (id);


--
-- TOC entry 4395 (class 2606 OID 26486)
-- Name: data_table_config data_table_config_table_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_table_config
    ADD CONSTRAINT data_table_config_table_name_key UNIQUE (table_name);


--
-- TOC entry 4198 (class 2606 OID 24492)
-- Name: departments departments_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_code_key UNIQUE (code);


--
-- TOC entry 4200 (class 2606 OID 24494)
-- Name: departments departments_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_name_key UNIQUE (name);


--
-- TOC entry 4202 (class 2606 OID 24496)
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);


--
-- TOC entry 4204 (class 2606 OID 24498)
-- Name: dev_product_specs dev_product_specs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs
    ADD CONSTRAINT dev_product_specs_pkey PRIMARY KEY (id);


--
-- TOC entry 4206 (class 2606 OID 24500)
-- Name: dev_products dev_products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_pkey PRIMARY KEY (id);


--
-- TOC entry 4208 (class 2606 OID 24502)
-- Name: dictionaries dictionaries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT dictionaries_pkey PRIMARY KEY (id);


--
-- TOC entry 4212 (class 2606 OID 24504)
-- Name: event_registry event_registry_event_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_event_key_key UNIQUE (event_key);


--
-- TOC entry 4214 (class 2606 OID 24506)
-- Name: event_registry event_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry
    ADD CONSTRAINT event_registry_pkey PRIMARY KEY (id);


--
-- TOC entry 4216 (class 2606 OID 24508)
-- Name: expense_details expense_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense_details
    ADD CONSTRAINT expense_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4220 (class 2606 OID 24510)
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- TOC entry 4224 (class 2606 OID 24512)
-- Name: feature_changes feature_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_pkey PRIMARY KEY (id);


--
-- TOC entry 4226 (class 2606 OID 24514)
-- Name: five_star_project_baselines five_star_project_baselines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.five_star_project_baselines
    ADD CONSTRAINT five_star_project_baselines_pkey PRIMARY KEY (id);


--
-- TOC entry 4397 (class 2606 OID 26505)
-- Name: formula_templates_extended formula_templates_extended_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formula_templates_extended
    ADD CONSTRAINT formula_templates_extended_pkey PRIMARY KEY (id);


--
-- TOC entry 4228 (class 2606 OID 24516)
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (id);


--
-- TOC entry 4232 (class 2606 OID 24518)
-- Name: inventory_transactions inventory_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_pkey PRIMARY KEY (id);


--
-- TOC entry 4385 (class 2606 OID 26462)
-- Name: performance_formula_templates performance_formula_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_formula_templates
    ADD CONSTRAINT performance_formula_templates_pkey PRIMARY KEY (id);


--
-- TOC entry 4380 (class 2606 OID 26432)
-- Name: performance_metrics_definition performance_metrics_definition_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_metrics_definition
    ADD CONSTRAINT performance_metrics_definition_pkey PRIMARY KEY (id);


--
-- TOC entry 4234 (class 2606 OID 24520)
-- Name: performance_statistics performance_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_statistics
    ADD CONSTRAINT performance_statistics_pkey PRIMARY KEY (id);


--
-- TOC entry 4236 (class 2606 OID 24522)
-- Name: performance_targets performance_targets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_targets
    ADD CONSTRAINT performance_targets_pkey PRIMARY KEY (id);


--
-- TOC entry 4238 (class 2606 OID 24524)
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 4242 (class 2606 OID 24526)
-- Name: pricing_order_approval_records pricing_order_approval_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_pkey PRIMARY KEY (id);


--
-- TOC entry 4244 (class 2606 OID 24528)
-- Name: pricing_order_details pricing_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details
    ADD CONSTRAINT pricing_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4246 (class 2606 OID 24530)
-- Name: pricing_orders pricing_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 4248 (class 2606 OID 24532)
-- Name: pricing_orders pricing_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 4250 (class 2606 OID 24534)
-- Name: product_categories product_categories_code_letter_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_code_letter_key UNIQUE (code_letter);


--
-- TOC entry 4252 (class 2606 OID 24536)
-- Name: product_categories product_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_pkey PRIMARY KEY (id);


--
-- TOC entry 4254 (class 2606 OID 24538)
-- Name: product_code_field_options product_code_field_options_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options
    ADD CONSTRAINT product_code_field_options_pkey PRIMARY KEY (id);


--
-- TOC entry 4256 (class 2606 OID 24540)
-- Name: product_code_field_values product_code_field_values_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_pkey PRIMARY KEY (id);


--
-- TOC entry 4258 (class 2606 OID 24542)
-- Name: product_code_fields product_code_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields
    ADD CONSTRAINT product_code_fields_pkey PRIMARY KEY (id);


--
-- TOC entry 4260 (class 2606 OID 24544)
-- Name: product_codes product_codes_full_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_full_code_key UNIQUE (full_code);


--
-- TOC entry 4262 (class 2606 OID 24546)
-- Name: product_codes product_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_pkey PRIMARY KEY (id);


--
-- TOC entry 4264 (class 2606 OID 24548)
-- Name: product_regions product_regions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_regions
    ADD CONSTRAINT product_regions_pkey PRIMARY KEY (id);


--
-- TOC entry 4266 (class 2606 OID 24550)
-- Name: product_subcategories product_subcategories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT product_subcategories_pkey PRIMARY KEY (id);


--
-- TOC entry 4270 (class 2606 OID 24552)
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- TOC entry 4272 (class 2606 OID 24554)
-- Name: products products_product_mn_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_product_mn_key UNIQUE (product_mn);


--
-- TOC entry 4277 (class 2606 OID 24556)
-- Name: project_customer_associations project_customer_associations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_customer_associations
    ADD CONSTRAINT project_customer_associations_pkey PRIMARY KEY (id);


--
-- TOC entry 4281 (class 2606 OID 24558)
-- Name: project_members project_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (id);


--
-- TOC entry 4283 (class 2606 OID 24560)
-- Name: project_rating_records project_rating_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_pkey PRIMARY KEY (id);


--
-- TOC entry 4287 (class 2606 OID 24562)
-- Name: project_scoring_config project_scoring_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config
    ADD CONSTRAINT project_scoring_config_pkey PRIMARY KEY (id);


--
-- TOC entry 4291 (class 2606 OID 24564)
-- Name: project_scoring_records project_scoring_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_pkey PRIMARY KEY (id);


--
-- TOC entry 4296 (class 2606 OID 24566)
-- Name: project_stage_history project_stage_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history
    ADD CONSTRAINT project_stage_history_pkey PRIMARY KEY (id);


--
-- TOC entry 4298 (class 2606 OID 24568)
-- Name: project_total_scores project_total_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_pkey PRIMARY KEY (id);


--
-- TOC entry 4300 (class 2606 OID 24570)
-- Name: project_total_scores project_total_scores_project_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_project_id_key UNIQUE (project_id);


--
-- TOC entry 4309 (class 2606 OID 24572)
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- TOC entry 4311 (class 2606 OID 24574)
-- Name: purchase_order_details purchase_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4313 (class 2606 OID 24576)
-- Name: purchase_orders purchase_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 4315 (class 2606 OID 24578)
-- Name: purchase_orders purchase_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 4317 (class 2606 OID 24580)
-- Name: quotation_details quotation_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details
    ADD CONSTRAINT quotation_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4325 (class 2606 OID 24582)
-- Name: quotations quotations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_pkey PRIMARY KEY (id);


--
-- TOC entry 4327 (class 2606 OID 24584)
-- Name: quotations quotations_quotation_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_quotation_number_key UNIQUE (quotation_number);


--
-- TOC entry 4389 (class 2606 OID 26471)
-- Name: role_performance_access role_performance_access_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_access
    ADD CONSTRAINT role_performance_access_pkey PRIMARY KEY (id);


--
-- TOC entry 4383 (class 2606 OID 26442)
-- Name: role_performance_config role_performance_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_config
    ADD CONSTRAINT role_performance_config_pkey PRIMARY KEY (id);


--
-- TOC entry 4401 (class 2606 OID 26519)
-- Name: role_performance_items role_performance_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_items
    ADD CONSTRAINT role_performance_items_pkey PRIMARY KEY (id);


--
-- TOC entry 4329 (class 2606 OID 24586)
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 4333 (class 2606 OID 24588)
-- Name: settlement_details settlement_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4335 (class 2606 OID 24590)
-- Name: settlement_order_details settlement_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pkey PRIMARY KEY (id);


--
-- TOC entry 4337 (class 2606 OID 24592)
-- Name: settlement_orders settlement_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_order_number_key UNIQUE (order_number);


--
-- TOC entry 4339 (class 2606 OID 24594)
-- Name: settlement_orders settlement_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_pkey PRIMARY KEY (id);


--
-- TOC entry 4341 (class 2606 OID 24596)
-- Name: settlements settlements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_pkey PRIMARY KEY (id);


--
-- TOC entry 4343 (class 2606 OID 24598)
-- Name: settlements settlements_settlement_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_settlement_number_key UNIQUE (settlement_number);


--
-- TOC entry 4345 (class 2606 OID 24600)
-- Name: solution_manager_email_settings solution_manager_email_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT solution_manager_email_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 4349 (class 2606 OID 24602)
-- Name: system_metrics system_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_pkey PRIMARY KEY (id);


--
-- TOC entry 4352 (class 2606 OID 24604)
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 4359 (class 2606 OID 24606)
-- Name: temp_products temp_products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temp_products
    ADD CONSTRAINT temp_products_pkey PRIMARY KEY (id);


--
-- TOC entry 4174 (class 2606 OID 24608)
-- Name: affiliations uix_owner_viewer; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT uix_owner_viewer UNIQUE (owner_id, viewer_id);


--
-- TOC entry 4331 (class 2606 OID 24610)
-- Name: role_permissions uix_role_module; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT uix_role_module UNIQUE (role, module);


--
-- TOC entry 4210 (class 2606 OID 24612)
-- Name: dictionaries uix_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries
    ADD CONSTRAINT uix_type_key UNIQUE (type, key);


--
-- TOC entry 4240 (class 2606 OID 24614)
-- Name: permissions uix_user_module; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT uix_user_module UNIQUE (user_id, module);


--
-- TOC entry 4230 (class 2606 OID 24616)
-- Name: inventory unique_company_product_inventory; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT unique_company_product_inventory UNIQUE (company_id, product_id);


--
-- TOC entry 4361 (class 2606 OID 24618)
-- Name: upgrade_logs upgrade_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 4279 (class 2606 OID 24620)
-- Name: project_customer_associations uq_project_company_customer_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_customer_associations
    ADD CONSTRAINT uq_project_company_customer_type UNIQUE (project_id, company_id, customer_type);


--
-- TOC entry 4285 (class 2606 OID 24622)
-- Name: project_rating_records uq_project_user_rating; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT uq_project_user_rating UNIQUE (project_id, user_id);


--
-- TOC entry 4391 (class 2606 OID 26473)
-- Name: role_performance_access uq_role_access_scope; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_access
    ADD CONSTRAINT uq_role_access_scope UNIQUE (role, access_scope);


--
-- TOC entry 4403 (class 2606 OID 26521)
-- Name: role_performance_items uq_role_item_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_items
    ADD CONSTRAINT uq_role_item_code UNIQUE (role_config_id, item_code);


--
-- TOC entry 4289 (class 2606 OID 24624)
-- Name: project_scoring_config uq_scoring_config; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config
    ADD CONSTRAINT uq_scoring_config UNIQUE (category, field_name);


--
-- TOC entry 4293 (class 2606 OID 24626)
-- Name: project_scoring_records uq_scoring_record; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT uq_scoring_record UNIQUE (project_id, category, field_name);


--
-- TOC entry 4347 (class 2606 OID 24628)
-- Name: solution_manager_email_settings uq_solution_manager_email_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT uq_solution_manager_email_user UNIQUE (user_id);


--
-- TOC entry 4268 (class 2606 OID 24630)
-- Name: product_subcategories uq_subcategory_code_letter; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT uq_subcategory_code_letter UNIQUE (category_id, code_letter);


--
-- TOC entry 4407 (class 2606 OID 26544)
-- Name: data_field_config uq_table_field; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_field_config
    ADD CONSTRAINT uq_table_field UNIQUE (table_config_id, field_name);


--
-- TOC entry 4363 (class 2606 OID 24632)
-- Name: user_event_subscriptions uq_user_target_event; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT uq_user_target_event UNIQUE (user_id, target_user_id, event_id);


--
-- TOC entry 4365 (class 2606 OID 24634)
-- Name: user_event_subscriptions user_event_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_pkey PRIMARY KEY (id);


--
-- TOC entry 4367 (class 2606 OID 24636)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4369 (class 2606 OID 24638)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4371 (class 2606 OID 24640)
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- TOC entry 4373 (class 2606 OID 24642)
-- Name: users users_wechat_openid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_wechat_openid_key UNIQUE (wechat_openid);


--
-- TOC entry 4375 (class 2606 OID 24644)
-- Name: version_records version_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records
    ADD CONSTRAINT version_records_pkey PRIMARY KEY (id);


--
-- TOC entry 4377 (class 2606 OID 24646)
-- Name: version_records version_records_version_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records
    ADD CONSTRAINT version_records_version_number_key UNIQUE (version_number);


--
-- TOC entry 4161 (class 2606 OID 17177)
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id, inserted_at);


--
-- TOC entry 4158 (class 2606 OID 17031)
-- Name: subscription pk_subscription; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.subscription
    ADD CONSTRAINT pk_subscription PRIMARY KEY (id);


--
-- TOC entry 4155 (class 2606 OID 17004)
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- TOC entry 4088 (class 2606 OID 16552)
-- Name: buckets buckets_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.buckets
    ADD CONSTRAINT buckets_pkey PRIMARY KEY (id);


--
-- TOC entry 4095 (class 2606 OID 16593)
-- Name: migrations migrations_name_key; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.migrations
    ADD CONSTRAINT migrations_name_key UNIQUE (name);


--
-- TOC entry 4097 (class 2606 OID 16591)
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (id);


--
-- TOC entry 4093 (class 2606 OID 16569)
-- Name: objects objects_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT objects_pkey PRIMARY KEY (id);


--
-- TOC entry 4166 (class 2606 OID 17234)
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_pkey PRIMARY KEY (id);


--
-- TOC entry 4164 (class 2606 OID 17219)
-- Name: s3_multipart_uploads s3_multipart_uploads_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads
    ADD CONSTRAINT s3_multipart_uploads_pkey PRIMARY KEY (id);


--
-- TOC entry 4083 (class 1259 OID 16530)
-- Name: audit_logs_instance_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX audit_logs_instance_id_idx ON auth.audit_log_entries USING btree (instance_id);


--
-- TOC entry 4057 (class 1259 OID 16746)
-- Name: confirmation_token_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX confirmation_token_idx ON auth.users USING btree (confirmation_token) WHERE ((confirmation_token)::text !~ '^[0-9 ]*$'::text);


--
-- TOC entry 4058 (class 1259 OID 16748)
-- Name: email_change_token_current_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX email_change_token_current_idx ON auth.users USING btree (email_change_token_current) WHERE ((email_change_token_current)::text !~ '^[0-9 ]*$'::text);


--
-- TOC entry 4059 (class 1259 OID 16749)
-- Name: email_change_token_new_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX email_change_token_new_idx ON auth.users USING btree (email_change_token_new) WHERE ((email_change_token_new)::text !~ '^[0-9 ]*$'::text);


--
-- TOC entry 4112 (class 1259 OID 16827)
-- Name: factor_id_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX factor_id_created_at_idx ON auth.mfa_factors USING btree (user_id, created_at);


--
-- TOC entry 4144 (class 1259 OID 16935)
-- Name: flow_state_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX flow_state_created_at_idx ON auth.flow_state USING btree (created_at DESC);


--
-- TOC entry 4101 (class 1259 OID 16915)
-- Name: identities_email_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX identities_email_idx ON auth.identities USING btree (email text_pattern_ops);


--
-- TOC entry 5313 (class 0 OID 0)
-- Dependencies: 4101
-- Name: INDEX identities_email_idx; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON INDEX auth.identities_email_idx IS 'Auth: Ensures indexed queries on the email column';


--
-- TOC entry 4106 (class 1259 OID 16743)
-- Name: identities_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX identities_user_id_idx ON auth.identities USING btree (user_id);


--
-- TOC entry 4147 (class 1259 OID 16932)
-- Name: idx_auth_code; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX idx_auth_code ON auth.flow_state USING btree (auth_code);


--
-- TOC entry 4148 (class 1259 OID 16933)
-- Name: idx_user_id_auth_method; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX idx_user_id_auth_method ON auth.flow_state USING btree (user_id, authentication_method);


--
-- TOC entry 4120 (class 1259 OID 16938)
-- Name: mfa_challenge_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX mfa_challenge_created_at_idx ON auth.mfa_challenges USING btree (created_at DESC);


--
-- TOC entry 4117 (class 1259 OID 16799)
-- Name: mfa_factors_user_friendly_name_unique; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX mfa_factors_user_friendly_name_unique ON auth.mfa_factors USING btree (friendly_name, user_id) WHERE (TRIM(BOTH FROM friendly_name) <> ''::text);


--
-- TOC entry 4118 (class 1259 OID 16944)
-- Name: mfa_factors_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX mfa_factors_user_id_idx ON auth.mfa_factors USING btree (user_id);


--
-- TOC entry 4151 (class 1259 OID 16991)
-- Name: one_time_tokens_relates_to_hash_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX one_time_tokens_relates_to_hash_idx ON auth.one_time_tokens USING hash (relates_to);


--
-- TOC entry 4152 (class 1259 OID 16990)
-- Name: one_time_tokens_token_hash_hash_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX one_time_tokens_token_hash_hash_idx ON auth.one_time_tokens USING hash (token_hash);


--
-- TOC entry 4153 (class 1259 OID 16992)
-- Name: one_time_tokens_user_id_token_type_key; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX one_time_tokens_user_id_token_type_key ON auth.one_time_tokens USING btree (user_id, token_type);


--
-- TOC entry 4060 (class 1259 OID 16750)
-- Name: reauthentication_token_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX reauthentication_token_idx ON auth.users USING btree (reauthentication_token) WHERE ((reauthentication_token)::text !~ '^[0-9 ]*$'::text);


--
-- TOC entry 4061 (class 1259 OID 16747)
-- Name: recovery_token_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX recovery_token_idx ON auth.users USING btree (recovery_token) WHERE ((recovery_token)::text !~ '^[0-9 ]*$'::text);


--
-- TOC entry 4070 (class 1259 OID 16513)
-- Name: refresh_tokens_instance_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_instance_id_idx ON auth.refresh_tokens USING btree (instance_id);


--
-- TOC entry 4071 (class 1259 OID 16514)
-- Name: refresh_tokens_instance_id_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_instance_id_user_id_idx ON auth.refresh_tokens USING btree (instance_id, user_id);


--
-- TOC entry 4072 (class 1259 OID 16742)
-- Name: refresh_tokens_parent_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_parent_idx ON auth.refresh_tokens USING btree (parent);


--
-- TOC entry 4075 (class 1259 OID 16829)
-- Name: refresh_tokens_session_id_revoked_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_session_id_revoked_idx ON auth.refresh_tokens USING btree (session_id, revoked);


--
-- TOC entry 4078 (class 1259 OID 16934)
-- Name: refresh_tokens_updated_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_updated_at_idx ON auth.refresh_tokens USING btree (updated_at DESC);


--
-- TOC entry 4138 (class 1259 OID 16871)
-- Name: saml_providers_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_providers_sso_provider_id_idx ON auth.saml_providers USING btree (sso_provider_id);


--
-- TOC entry 4139 (class 1259 OID 16936)
-- Name: saml_relay_states_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_relay_states_created_at_idx ON auth.saml_relay_states USING btree (created_at DESC);


--
-- TOC entry 4140 (class 1259 OID 16886)
-- Name: saml_relay_states_for_email_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_relay_states_for_email_idx ON auth.saml_relay_states USING btree (for_email);


--
-- TOC entry 4143 (class 1259 OID 16885)
-- Name: saml_relay_states_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_relay_states_sso_provider_id_idx ON auth.saml_relay_states USING btree (sso_provider_id);


--
-- TOC entry 4107 (class 1259 OID 16937)
-- Name: sessions_not_after_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sessions_not_after_idx ON auth.sessions USING btree (not_after DESC);


--
-- TOC entry 4110 (class 1259 OID 16828)
-- Name: sessions_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sessions_user_id_idx ON auth.sessions USING btree (user_id);


--
-- TOC entry 4130 (class 1259 OID 16853)
-- Name: sso_domains_domain_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX sso_domains_domain_idx ON auth.sso_domains USING btree (lower(domain));


--
-- TOC entry 4133 (class 1259 OID 16852)
-- Name: sso_domains_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sso_domains_sso_provider_id_idx ON auth.sso_domains USING btree (sso_provider_id);


--
-- TOC entry 4129 (class 1259 OID 16838)
-- Name: sso_providers_resource_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX sso_providers_resource_id_idx ON auth.sso_providers USING btree (lower(resource_id));


--
-- TOC entry 4119 (class 1259 OID 16997)
-- Name: unique_phone_factor_per_user; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX unique_phone_factor_per_user ON auth.mfa_factors USING btree (user_id, phone);


--
-- TOC entry 4111 (class 1259 OID 16826)
-- Name: user_id_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX user_id_created_at_idx ON auth.sessions USING btree (user_id, created_at);


--
-- TOC entry 4062 (class 1259 OID 16906)
-- Name: users_email_partial_key; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX users_email_partial_key ON auth.users USING btree (email) WHERE (is_sso_user = false);


--
-- TOC entry 5314 (class 0 OID 0)
-- Dependencies: 4062
-- Name: INDEX users_email_partial_key; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON INDEX auth.users_email_partial_key IS 'Auth: A partial unique index that applies only when is_sso_user is false';


--
-- TOC entry 4063 (class 1259 OID 16744)
-- Name: users_instance_id_email_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX users_instance_id_email_idx ON auth.users USING btree (instance_id, lower((email)::text));


--
-- TOC entry 4064 (class 1259 OID 16503)
-- Name: users_instance_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX users_instance_id_idx ON auth.users USING btree (instance_id);


--
-- TOC entry 4065 (class 1259 OID 16961)
-- Name: users_is_anonymous_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX users_is_anonymous_idx ON auth.users USING btree (is_anonymous);


--
-- TOC entry 4217 (class 1259 OID 24647)
-- Name: idx_expense_details_currency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_expense_details_currency ON public.expense_details USING btree (currency);


--
-- TOC entry 4218 (class 1259 OID 24648)
-- Name: idx_expense_details_expense_currency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_expense_details_expense_currency ON public.expense_details USING btree (expense_id, currency);


--
-- TOC entry 4221 (class 1259 OID 24649)
-- Name: idx_expenses_currency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_expenses_currency ON public.expenses USING btree (currency);


--
-- TOC entry 4273 (class 1259 OID 24650)
-- Name: idx_project_customer_associations_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_customer_associations_company_id ON public.project_customer_associations USING btree (company_id);


--
-- TOC entry 4274 (class 1259 OID 24651)
-- Name: idx_project_customer_associations_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_customer_associations_created_by ON public.project_customer_associations USING btree (created_by);


--
-- TOC entry 4275 (class 1259 OID 24652)
-- Name: idx_project_customer_associations_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_customer_associations_project_id ON public.project_customer_associations USING btree (project_id);


--
-- TOC entry 4301 (class 1259 OID 24653)
-- Name: idx_projects_current_stage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_current_stage ON public.projects USING btree (current_stage);


--
-- TOC entry 4302 (class 1259 OID 24654)
-- Name: idx_projects_owner_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_owner_id ON public.projects USING btree (owner_id);


--
-- TOC entry 4303 (class 1259 OID 24655)
-- Name: idx_projects_project_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_project_type ON public.projects USING btree (project_type);


--
-- TOC entry 4304 (class 1259 OID 24656)
-- Name: idx_projects_type_stage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_type_stage ON public.projects USING btree (project_type, current_stage);


--
-- TOC entry 4305 (class 1259 OID 24657)
-- Name: idx_projects_vendor_sales_manager; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_vendor_sales_manager ON public.projects USING btree (vendor_sales_manager_id);


--
-- TOC entry 4318 (class 1259 OID 24658)
-- Name: idx_quotations_amount; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quotations_amount ON public.quotations USING btree (amount);


--
-- TOC entry 4319 (class 1259 OID 24659)
-- Name: idx_quotations_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quotations_created_at ON public.quotations USING btree (created_at);


--
-- TOC entry 4320 (class 1259 OID 24660)
-- Name: idx_quotations_owner_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quotations_owner_id ON public.quotations USING btree (owner_id);


--
-- TOC entry 4321 (class 1259 OID 24661)
-- Name: idx_quotations_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quotations_project_id ON public.quotations USING btree (project_id);


--
-- TOC entry 4322 (class 1259 OID 24662)
-- Name: idx_quotations_project_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quotations_project_owner ON public.quotations USING btree (project_id, owner_id);


--
-- TOC entry 4323 (class 1259 OID 24663)
-- Name: idx_quotations_updated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_quotations_updated_at ON public.quotations USING btree (updated_at);


--
-- TOC entry 4386 (class 1259 OID 26475)
-- Name: idx_role_access; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_access ON public.role_performance_access USING btree (role, access_scope);


--
-- TOC entry 4398 (class 1259 OID 26533)
-- Name: idx_role_items_config; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_items_config ON public.role_performance_items USING btree (role_config_id);


--
-- TOC entry 4399 (class 1259 OID 26532)
-- Name: idx_role_items_metric; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_items_metric ON public.role_performance_items USING btree (metric_id);


--
-- TOC entry 4353 (class 1259 OID 24664)
-- Name: idx_temp_product_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_product_category ON public.temp_products USING btree (category);


--
-- TOC entry 4354 (class 1259 OID 24665)
-- Name: idx_temp_product_creator; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_product_creator ON public.temp_products USING btree (created_by);


--
-- TOC entry 4355 (class 1259 OID 24666)
-- Name: idx_temp_product_deleted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_product_deleted ON public.temp_products USING btree (is_deleted);


--
-- TOC entry 4356 (class 1259 OID 24667)
-- Name: idx_temp_product_model_creator; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_product_model_creator ON public.temp_products USING btree (product_model, created_by);


--
-- TOC entry 4357 (class 1259 OID 24668)
-- Name: idx_temp_product_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_product_usage ON public.temp_products USING btree (usage_count);


--
-- TOC entry 4222 (class 1259 OID 24669)
-- Name: ix_expenses_expense_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_expenses_expense_number ON public.expenses USING btree (expense_number);


--
-- TOC entry 4378 (class 1259 OID 26433)
-- Name: ix_performance_metrics_definition_metric_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_performance_metrics_definition_metric_code ON public.performance_metrics_definition USING btree (metric_code);


--
-- TOC entry 4294 (class 1259 OID 24670)
-- Name: ix_project_stage_history_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_stage_history_project_id ON public.project_stage_history USING btree (project_id);


--
-- TOC entry 4306 (class 1259 OID 24671)
-- Name: ix_projects_authorization_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_authorization_code ON public.projects USING btree (authorization_code);


--
-- TOC entry 4307 (class 1259 OID 24672)
-- Name: ix_projects_project_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_projects_project_name ON public.projects USING btree (project_name);


--
-- TOC entry 4387 (class 1259 OID 26474)
-- Name: ix_role_performance_access_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_role_performance_access_role ON public.role_performance_access USING btree (role);


--
-- TOC entry 4381 (class 1259 OID 26453)
-- Name: ix_role_performance_config_role; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_role_performance_config_role ON public.role_performance_config USING btree (role);


--
-- TOC entry 4350 (class 1259 OID 24673)
-- Name: ix_system_settings_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_system_settings_key ON public.system_settings USING btree (key);


--
-- TOC entry 4156 (class 1259 OID 17178)
-- Name: ix_realtime_subscription_entity; Type: INDEX; Schema: realtime; Owner: -
--

CREATE INDEX ix_realtime_subscription_entity ON realtime.subscription USING btree (entity);


--
-- TOC entry 4159 (class 1259 OID 17080)
-- Name: subscription_subscription_id_entity_filters_key; Type: INDEX; Schema: realtime; Owner: -
--

CREATE UNIQUE INDEX subscription_subscription_id_entity_filters_key ON realtime.subscription USING btree (subscription_id, entity, filters);


--
-- TOC entry 4086 (class 1259 OID 16558)
-- Name: bname; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX bname ON storage.buckets USING btree (name);


--
-- TOC entry 4089 (class 1259 OID 16580)
-- Name: bucketid_objname; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX bucketid_objname ON storage.objects USING btree (bucket_id, name);


--
-- TOC entry 4162 (class 1259 OID 17245)
-- Name: idx_multipart_uploads_list; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX idx_multipart_uploads_list ON storage.s3_multipart_uploads USING btree (bucket_id, key, created_at);


--
-- TOC entry 4090 (class 1259 OID 17210)
-- Name: idx_objects_bucket_id_name; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX idx_objects_bucket_id_name ON storage.objects USING btree (bucket_id, name COLLATE "C");


--
-- TOC entry 4091 (class 1259 OID 16581)
-- Name: name_prefix_search; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX name_prefix_search ON storage.objects USING btree (name text_pattern_ops);


--
-- TOC entry 4549 (class 2620 OID 17036)
-- Name: subscription tr_check_filters; Type: TRIGGER; Schema: realtime; Owner: -
--

CREATE TRIGGER tr_check_filters BEFORE INSERT OR UPDATE ON realtime.subscription FOR EACH ROW EXECUTE FUNCTION realtime.subscription_check_filters();


--
-- TOC entry 4548 (class 2620 OID 17198)
-- Name: objects update_objects_updated_at; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER update_objects_updated_at BEFORE UPDATE ON storage.objects FOR EACH ROW EXECUTE FUNCTION storage.update_updated_at_column();


--
-- TOC entry 4410 (class 2606 OID 16730)
-- Name: identities identities_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- TOC entry 4414 (class 2606 OID 16819)
-- Name: mfa_amr_claims mfa_amr_claims_session_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT mfa_amr_claims_session_id_fkey FOREIGN KEY (session_id) REFERENCES auth.sessions(id) ON DELETE CASCADE;


--
-- TOC entry 4413 (class 2606 OID 16807)
-- Name: mfa_challenges mfa_challenges_auth_factor_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_challenges
    ADD CONSTRAINT mfa_challenges_auth_factor_id_fkey FOREIGN KEY (factor_id) REFERENCES auth.mfa_factors(id) ON DELETE CASCADE;


--
-- TOC entry 4412 (class 2606 OID 16794)
-- Name: mfa_factors mfa_factors_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- TOC entry 4419 (class 2606 OID 16985)
-- Name: one_time_tokens one_time_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.one_time_tokens
    ADD CONSTRAINT one_time_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- TOC entry 4408 (class 2606 OID 16763)
-- Name: refresh_tokens refresh_tokens_session_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_session_id_fkey FOREIGN KEY (session_id) REFERENCES auth.sessions(id) ON DELETE CASCADE;


--
-- TOC entry 4416 (class 2606 OID 16866)
-- Name: saml_providers saml_providers_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- TOC entry 4417 (class 2606 OID 16939)
-- Name: saml_relay_states saml_relay_states_flow_state_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_flow_state_id_fkey FOREIGN KEY (flow_state_id) REFERENCES auth.flow_state(id) ON DELETE CASCADE;


--
-- TOC entry 4418 (class 2606 OID 16880)
-- Name: saml_relay_states saml_relay_states_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- TOC entry 4411 (class 2606 OID 16758)
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- TOC entry 4415 (class 2606 OID 16847)
-- Name: sso_domains sso_domains_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sso_domains
    ADD CONSTRAINT sso_domains_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- TOC entry 4423 (class 2606 OID 24674)
-- Name: action_reply action_reply_action_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_action_id_fkey FOREIGN KEY (action_id) REFERENCES public.actions(id);


--
-- TOC entry 4424 (class 2606 OID 24679)
-- Name: action_reply action_reply_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4425 (class 2606 OID 24684)
-- Name: action_reply action_reply_parent_reply_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply
    ADD CONSTRAINT action_reply_parent_reply_id_fkey FOREIGN KEY (parent_reply_id) REFERENCES public.action_reply(id);


--
-- TOC entry 4426 (class 2606 OID 24689)
-- Name: actions actions_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 4427 (class 2606 OID 24694)
-- Name: actions actions_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- TOC entry 4428 (class 2606 OID 24699)
-- Name: actions actions_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4429 (class 2606 OID 24704)
-- Name: actions actions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4430 (class 2606 OID 24709)
-- Name: affiliations affiliations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4431 (class 2606 OID 24714)
-- Name: affiliations affiliations_viewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_viewer_id_fkey FOREIGN KEY (viewer_id) REFERENCES public.users(id);


--
-- TOC entry 4432 (class 2606 OID 24719)
-- Name: approval_instance approval_instance_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4433 (class 2606 OID 24724)
-- Name: approval_instance approval_instance_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance
    ADD CONSTRAINT approval_instance_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- TOC entry 4434 (class 2606 OID 24729)
-- Name: approval_process_template approval_process_template_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template
    ADD CONSTRAINT approval_process_template_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4435 (class 2606 OID 24734)
-- Name: approval_record approval_record_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES public.approval_instance(id);


--
-- TOC entry 4438 (class 2606 OID 24739)
-- Name: approval_step approval_step_approver_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_approver_user_id_fkey FOREIGN KEY (approver_user_id) REFERENCES public.users(id);


--
-- TOC entry 4439 (class 2606 OID 24744)
-- Name: approval_step approval_step_process_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step
    ADD CONSTRAINT approval_step_process_id_fkey FOREIGN KEY (process_id) REFERENCES public.approval_process_template(id);


--
-- TOC entry 4440 (class 2606 OID 24749)
-- Name: change_logs change_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs
    ADD CONSTRAINT change_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 4441 (class 2606 OID 24754)
-- Name: companies companies_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4442 (class 2606 OID 24759)
-- Name: company_assets company_assets_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_assets
    ADD CONSTRAINT company_assets_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 4443 (class 2606 OID 24764)
-- Name: contacts contacts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 4444 (class 2606 OID 24769)
-- Name: contacts contacts_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4545 (class 2606 OID 26550)
-- Name: data_field_config data_field_config_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_field_config
    ADD CONSTRAINT data_field_config_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4546 (class 2606 OID 26545)
-- Name: data_field_config data_field_config_table_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_field_config
    ADD CONSTRAINT data_field_config_table_config_id_fkey FOREIGN KEY (table_config_id) REFERENCES public.data_table_config(id);


--
-- TOC entry 4547 (class 2606 OID 26555)
-- Name: data_field_config data_field_config_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_field_config
    ADD CONSTRAINT data_field_config_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- TOC entry 4540 (class 2606 OID 26487)
-- Name: data_table_config data_table_config_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_table_config
    ADD CONSTRAINT data_table_config_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4541 (class 2606 OID 26492)
-- Name: data_table_config data_table_config_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_table_config
    ADD CONSTRAINT data_table_config_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- TOC entry 4445 (class 2606 OID 24774)
-- Name: departments departments_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_manager_id_fkey FOREIGN KEY (manager_id) REFERENCES public.users(id);


--
-- TOC entry 4446 (class 2606 OID 24779)
-- Name: departments departments_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.departments(id);


--
-- TOC entry 4447 (class 2606 OID 24784)
-- Name: dev_product_specs dev_product_specs_dev_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs
    ADD CONSTRAINT dev_product_specs_dev_product_id_fkey FOREIGN KEY (dev_product_id) REFERENCES public.dev_products(id);


--
-- TOC entry 4448 (class 2606 OID 24789)
-- Name: dev_products dev_products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 4449 (class 2606 OID 24794)
-- Name: dev_products dev_products_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4450 (class 2606 OID 24799)
-- Name: dev_products dev_products_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4451 (class 2606 OID 24804)
-- Name: dev_products dev_products_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.product_regions(id);


--
-- TOC entry 4452 (class 2606 OID 24809)
-- Name: dev_products dev_products_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products
    ADD CONSTRAINT dev_products_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 4453 (class 2606 OID 24814)
-- Name: expense_details expense_details_expense_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense_details
    ADD CONSTRAINT expense_details_expense_id_fkey FOREIGN KEY (expense_id) REFERENCES public.expenses(id);


--
-- TOC entry 4454 (class 2606 OID 24819)
-- Name: expenses expenses_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 4455 (class 2606 OID 24824)
-- Name: expenses expenses_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.companies(id);


--
-- TOC entry 4456 (class 2606 OID 24829)
-- Name: expenses expenses_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4457 (class 2606 OID 24834)
-- Name: expenses expenses_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4460 (class 2606 OID 24839)
-- Name: feature_changes feature_changes_developer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_developer_id_fkey FOREIGN KEY (developer_id) REFERENCES public.users(id);


--
-- TOC entry 4461 (class 2606 OID 24844)
-- Name: feature_changes feature_changes_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes
    ADD CONSTRAINT feature_changes_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 4436 (class 2606 OID 24849)
-- Name: approval_record fk_approval_record_approver_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT fk_approval_record_approver_id FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- TOC entry 4437 (class 2606 OID 24854)
-- Name: approval_record fk_approval_record_step_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT fk_approval_record_step_id FOREIGN KEY (step_id) REFERENCES public.approval_step(id);


--
-- TOC entry 4458 (class 2606 OID 24859)
-- Name: expenses fk_expenses_contact_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT fk_expenses_contact_id FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- TOC entry 4459 (class 2606 OID 24864)
-- Name: expenses fk_expenses_paid_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT fk_expenses_paid_by FOREIGN KEY (paid_by) REFERENCES public.users(id);


--
-- TOC entry 4488 (class 2606 OID 24869)
-- Name: project_customer_associations fk_project_customer_associations_company_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_customer_associations
    ADD CONSTRAINT fk_project_customer_associations_company_id FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- TOC entry 4489 (class 2606 OID 24874)
-- Name: project_customer_associations fk_project_customer_associations_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_customer_associations
    ADD CONSTRAINT fk_project_customer_associations_created_by FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- TOC entry 4490 (class 2606 OID 24879)
-- Name: project_customer_associations fk_project_customer_associations_project_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_customer_associations
    ADD CONSTRAINT fk_project_customer_associations_project_id FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 4516 (class 2606 OID 24884)
-- Name: settlement_order_details fk_settlement_order_details_settlement_company; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT fk_settlement_order_details_settlement_company FOREIGN KEY (settlement_company_id) REFERENCES public.companies(id);


--
-- TOC entry 4542 (class 2606 OID 26506)
-- Name: formula_templates_extended formula_templates_extended_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formula_templates_extended
    ADD CONSTRAINT formula_templates_extended_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4462 (class 2606 OID 24889)
-- Name: inventory inventory_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 4463 (class 2606 OID 24894)
-- Name: inventory inventory_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 4464 (class 2606 OID 24899)
-- Name: inventory inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 4465 (class 2606 OID 24904)
-- Name: inventory_transactions inventory_transactions_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 4466 (class 2606 OID 24909)
-- Name: inventory_transactions inventory_transactions_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- TOC entry 4467 (class 2606 OID 24914)
-- Name: permissions permissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 4468 (class 2606 OID 24919)
-- Name: pricing_order_approval_records pricing_order_approval_records_approver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_approver_id_fkey FOREIGN KEY (approver_id) REFERENCES public.users(id);


--
-- TOC entry 4469 (class 2606 OID 24924)
-- Name: pricing_order_approval_records pricing_order_approval_records_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records
    ADD CONSTRAINT pricing_order_approval_records_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 4470 (class 2606 OID 24929)
-- Name: pricing_order_details pricing_order_details_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details
    ADD CONSTRAINT pricing_order_details_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 4471 (class 2606 OID 24934)
-- Name: pricing_orders pricing_orders_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 4472 (class 2606 OID 24939)
-- Name: pricing_orders pricing_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4473 (class 2606 OID 24944)
-- Name: pricing_orders pricing_orders_dealer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_dealer_id_fkey FOREIGN KEY (dealer_id) REFERENCES public.companies(id);


--
-- TOC entry 4474 (class 2606 OID 24949)
-- Name: pricing_orders pricing_orders_distributor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_distributor_id_fkey FOREIGN KEY (distributor_id) REFERENCES public.companies(id);


--
-- TOC entry 4475 (class 2606 OID 24954)
-- Name: pricing_orders pricing_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4476 (class 2606 OID 24959)
-- Name: pricing_orders pricing_orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders
    ADD CONSTRAINT pricing_orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 4477 (class 2606 OID 24964)
-- Name: product_code_field_options product_code_field_options_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options
    ADD CONSTRAINT product_code_field_options_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.product_code_fields(id);


--
-- TOC entry 4478 (class 2606 OID 24969)
-- Name: product_code_field_values product_code_field_values_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.product_code_fields(id);


--
-- TOC entry 4479 (class 2606 OID 24974)
-- Name: product_code_field_values product_code_field_values_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_option_id_fkey FOREIGN KEY (option_id) REFERENCES public.product_code_field_options(id);


--
-- TOC entry 4480 (class 2606 OID 24979)
-- Name: product_code_field_values product_code_field_values_product_code_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values
    ADD CONSTRAINT product_code_field_values_product_code_id_fkey FOREIGN KEY (product_code_id) REFERENCES public.product_codes(id);


--
-- TOC entry 4481 (class 2606 OID 24984)
-- Name: product_code_fields product_code_fields_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields
    ADD CONSTRAINT product_code_fields_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 4482 (class 2606 OID 24989)
-- Name: product_codes product_codes_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 4483 (class 2606 OID 24994)
-- Name: product_codes product_codes_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4484 (class 2606 OID 24999)
-- Name: product_codes product_codes_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 4485 (class 2606 OID 25004)
-- Name: product_codes product_codes_subcategory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_subcategory_id_fkey FOREIGN KEY (subcategory_id) REFERENCES public.product_subcategories(id);


--
-- TOC entry 4486 (class 2606 OID 25009)
-- Name: product_subcategories product_subcategories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories
    ADD CONSTRAINT product_subcategories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.product_categories(id);


--
-- TOC entry 4487 (class 2606 OID 25014)
-- Name: products products_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4491 (class 2606 OID 25019)
-- Name: project_members project_members_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4492 (class 2606 OID 25024)
-- Name: project_members project_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 4493 (class 2606 OID 25029)
-- Name: project_rating_records project_rating_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 4494 (class 2606 OID 25034)
-- Name: project_rating_records project_rating_records_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records
    ADD CONSTRAINT project_rating_records_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4495 (class 2606 OID 25039)
-- Name: project_scoring_records project_scoring_records_awarded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_awarded_by_fkey FOREIGN KEY (awarded_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- TOC entry 4496 (class 2606 OID 25044)
-- Name: project_scoring_records project_scoring_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records
    ADD CONSTRAINT project_scoring_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 4497 (class 2606 OID 25049)
-- Name: project_stage_history project_stage_history_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history
    ADD CONSTRAINT project_stage_history_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4498 (class 2606 OID 25054)
-- Name: project_total_scores project_total_scores_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores
    ADD CONSTRAINT project_total_scores_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- TOC entry 4499 (class 2606 OID 25059)
-- Name: projects projects_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- TOC entry 4500 (class 2606 OID 25064)
-- Name: projects projects_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4501 (class 2606 OID 25069)
-- Name: projects projects_vendor_sales_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_vendor_sales_manager_id_fkey FOREIGN KEY (vendor_sales_manager_id) REFERENCES public.users(id);


--
-- TOC entry 4502 (class 2606 OID 25074)
-- Name: purchase_order_details purchase_order_details_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.purchase_orders(id);


--
-- TOC entry 4503 (class 2606 OID 25079)
-- Name: purchase_order_details purchase_order_details_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details
    ADD CONSTRAINT purchase_order_details_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 4504 (class 2606 OID 25084)
-- Name: purchase_orders purchase_orders_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- TOC entry 4505 (class 2606 OID 25089)
-- Name: purchase_orders purchase_orders_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 4506 (class 2606 OID 25094)
-- Name: purchase_orders purchase_orders_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 4507 (class 2606 OID 25099)
-- Name: quotation_details quotation_details_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details
    ADD CONSTRAINT quotation_details_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 4508 (class 2606 OID 25104)
-- Name: quotations quotations_confirmed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_confirmed_by_fkey FOREIGN KEY (confirmed_by) REFERENCES public.users(id);


--
-- TOC entry 4509 (class 2606 OID 25109)
-- Name: quotations quotations_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_contact_id_fkey FOREIGN KEY (contact_id) REFERENCES public.contacts(id);


--
-- TOC entry 4510 (class 2606 OID 25114)
-- Name: quotations quotations_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id);


--
-- TOC entry 4511 (class 2606 OID 25119)
-- Name: quotations quotations_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4512 (class 2606 OID 25124)
-- Name: quotations quotations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4538 (class 2606 OID 26443)
-- Name: role_performance_config role_performance_config_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_config
    ADD CONSTRAINT role_performance_config_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4539 (class 2606 OID 26448)
-- Name: role_performance_config role_performance_config_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_config
    ADD CONSTRAINT role_performance_config_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- TOC entry 4543 (class 2606 OID 26527)
-- Name: role_performance_items role_performance_items_metric_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_items
    ADD CONSTRAINT role_performance_items_metric_id_fkey FOREIGN KEY (metric_id) REFERENCES public.performance_metrics_definition(id);


--
-- TOC entry 4544 (class 2606 OID 26522)
-- Name: role_performance_items role_performance_items_role_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_items
    ADD CONSTRAINT role_performance_items_role_config_id_fkey FOREIGN KEY (role_config_id) REFERENCES public.role_performance_config(id);


--
-- TOC entry 4513 (class 2606 OID 25129)
-- Name: settlement_details settlement_details_inventory_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_inventory_id_fkey FOREIGN KEY (inventory_id) REFERENCES public.inventory(id);


--
-- TOC entry 4514 (class 2606 OID 25134)
-- Name: settlement_details settlement_details_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- TOC entry 4515 (class 2606 OID 25139)
-- Name: settlement_details settlement_details_settlement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details
    ADD CONSTRAINT settlement_details_settlement_id_fkey FOREIGN KEY (settlement_id) REFERENCES public.settlements(id);


--
-- TOC entry 4517 (class 2606 OID 25144)
-- Name: settlement_order_details settlement_order_details_pricing_detail_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pricing_detail_id_fkey FOREIGN KEY (pricing_detail_id) REFERENCES public.pricing_order_details(id);


--
-- TOC entry 4518 (class 2606 OID 25149)
-- Name: settlement_order_details settlement_order_details_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 4519 (class 2606 OID 25154)
-- Name: settlement_order_details settlement_order_details_settlement_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details
    ADD CONSTRAINT settlement_order_details_settlement_order_id_fkey FOREIGN KEY (settlement_order_id) REFERENCES public.settlement_orders(id);


--
-- TOC entry 4520 (class 2606 OID 25159)
-- Name: settlement_orders settlement_orders_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- TOC entry 4521 (class 2606 OID 25164)
-- Name: settlement_orders settlement_orders_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4522 (class 2606 OID 25169)
-- Name: settlement_orders settlement_orders_dealer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_dealer_id_fkey FOREIGN KEY (dealer_id) REFERENCES public.companies(id);


--
-- TOC entry 4523 (class 2606 OID 25174)
-- Name: settlement_orders settlement_orders_distributor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_distributor_id_fkey FOREIGN KEY (distributor_id) REFERENCES public.companies(id);


--
-- TOC entry 4524 (class 2606 OID 25179)
-- Name: settlement_orders settlement_orders_pricing_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_pricing_order_id_fkey FOREIGN KEY (pricing_order_id) REFERENCES public.pricing_orders(id);


--
-- TOC entry 4525 (class 2606 OID 25184)
-- Name: settlement_orders settlement_orders_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- TOC entry 4526 (class 2606 OID 25189)
-- Name: settlement_orders settlement_orders_quotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders
    ADD CONSTRAINT settlement_orders_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);


--
-- TOC entry 4527 (class 2606 OID 25194)
-- Name: settlements settlements_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- TOC entry 4528 (class 2606 OID 25199)
-- Name: settlements settlements_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- TOC entry 4529 (class 2606 OID 25204)
-- Name: settlements settlements_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- TOC entry 4530 (class 2606 OID 25209)
-- Name: solution_manager_email_settings solution_manager_email_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings
    ADD CONSTRAINT solution_manager_email_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 4531 (class 2606 OID 25214)
-- Name: system_metrics system_metrics_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics
    ADD CONSTRAINT system_metrics_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 4532 (class 2606 OID 25219)
-- Name: temp_products temp_products_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temp_products
    ADD CONSTRAINT temp_products_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 4533 (class 2606 OID 25224)
-- Name: upgrade_logs upgrade_logs_operator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_operator_id_fkey FOREIGN KEY (operator_id) REFERENCES public.users(id);


--
-- TOC entry 4534 (class 2606 OID 25229)
-- Name: upgrade_logs upgrade_logs_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs
    ADD CONSTRAINT upgrade_logs_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.version_records(id);


--
-- TOC entry 4535 (class 2606 OID 25234)
-- Name: user_event_subscriptions user_event_subscriptions_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.event_registry(id);


--
-- TOC entry 4536 (class 2606 OID 25239)
-- Name: user_event_subscriptions user_event_subscriptions_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id);


--
-- TOC entry 4537 (class 2606 OID 25244)
-- Name: user_event_subscriptions user_event_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions
    ADD CONSTRAINT user_event_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 4409 (class 2606 OID 16570)
-- Name: objects objects_bucketId_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT "objects_bucketId_fkey" FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- TOC entry 4420 (class 2606 OID 17220)
-- Name: s3_multipart_uploads s3_multipart_uploads_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads
    ADD CONSTRAINT s3_multipart_uploads_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- TOC entry 4421 (class 2606 OID 17240)
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- TOC entry 4422 (class 2606 OID 17235)
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_upload_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_upload_id_fkey FOREIGN KEY (upload_id) REFERENCES storage.s3_multipart_uploads(id) ON DELETE CASCADE;


--
-- TOC entry 4701 (class 0 OID 16523)
-- Dependencies: 244
-- Name: audit_log_entries; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.audit_log_entries ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4715 (class 0 OID 16925)
-- Dependencies: 261
-- Name: flow_state; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.flow_state ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4706 (class 0 OID 16723)
-- Dependencies: 252
-- Name: identities; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.identities ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4700 (class 0 OID 16516)
-- Dependencies: 243
-- Name: instances; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.instances ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4710 (class 0 OID 16812)
-- Dependencies: 256
-- Name: mfa_amr_claims; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.mfa_amr_claims ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4709 (class 0 OID 16800)
-- Dependencies: 255
-- Name: mfa_challenges; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.mfa_challenges ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4708 (class 0 OID 16787)
-- Dependencies: 254
-- Name: mfa_factors; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.mfa_factors ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4716 (class 0 OID 16975)
-- Dependencies: 262
-- Name: one_time_tokens; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.one_time_tokens ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4699 (class 0 OID 16505)
-- Dependencies: 242
-- Name: refresh_tokens; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.refresh_tokens ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4713 (class 0 OID 16854)
-- Dependencies: 259
-- Name: saml_providers; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.saml_providers ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4714 (class 0 OID 16872)
-- Dependencies: 260
-- Name: saml_relay_states; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.saml_relay_states ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4702 (class 0 OID 16531)
-- Dependencies: 245
-- Name: schema_migrations; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.schema_migrations ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4707 (class 0 OID 16753)
-- Dependencies: 253
-- Name: sessions; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.sessions ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4712 (class 0 OID 16839)
-- Dependencies: 258
-- Name: sso_domains; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.sso_domains ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4711 (class 0 OID 16830)
-- Dependencies: 257
-- Name: sso_providers; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.sso_providers ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4698 (class 0 OID 16493)
-- Dependencies: 240
-- Name: users; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4717 (class 0 OID 17163)
-- Dependencies: 269
-- Name: messages; Type: ROW SECURITY; Schema: realtime; Owner: -
--

ALTER TABLE realtime.messages ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4703 (class 0 OID 16544)
-- Dependencies: 246
-- Name: buckets; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.buckets ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4705 (class 0 OID 16586)
-- Dependencies: 248
-- Name: migrations; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.migrations ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4704 (class 0 OID 16559)
-- Dependencies: 247
-- Name: objects; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4718 (class 0 OID 17211)
-- Dependencies: 270
-- Name: s3_multipart_uploads; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.s3_multipart_uploads ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4719 (class 0 OID 17225)
-- Dependencies: 271
-- Name: s3_multipart_uploads_parts; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.s3_multipart_uploads_parts ENABLE ROW LEVEL SECURITY;

--
-- TOC entry 4720 (class 6104 OID 16426)
-- Name: supabase_realtime; Type: PUBLICATION; Schema: -; Owner: -
--

CREATE PUBLICATION supabase_realtime WITH (publish = 'insert, update, delete, truncate');


--
-- TOC entry 3861 (class 3466 OID 16619)
-- Name: issue_graphql_placeholder; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_graphql_placeholder ON sql_drop
         WHEN TAG IN ('DROP EXTENSION')
   EXECUTE FUNCTION extensions.set_graphql_placeholder();


--
-- TOC entry 3866 (class 3466 OID 16698)
-- Name: issue_pg_cron_access; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_pg_cron_access ON ddl_command_end
         WHEN TAG IN ('CREATE EXTENSION')
   EXECUTE FUNCTION extensions.grant_pg_cron_access();


--
-- TOC entry 3860 (class 3466 OID 16617)
-- Name: issue_pg_graphql_access; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_pg_graphql_access ON ddl_command_end
         WHEN TAG IN ('CREATE FUNCTION')
   EXECUTE FUNCTION extensions.grant_pg_graphql_access();


--
-- TOC entry 3867 (class 3466 OID 16701)
-- Name: issue_pg_net_access; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_pg_net_access ON ddl_command_end
         WHEN TAG IN ('CREATE EXTENSION')
   EXECUTE FUNCTION extensions.grant_pg_net_access();


--
-- TOC entry 3862 (class 3466 OID 16620)
-- Name: pgrst_ddl_watch; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER pgrst_ddl_watch ON ddl_command_end
   EXECUTE FUNCTION extensions.pgrst_ddl_watch();


--
-- TOC entry 3863 (class 3466 OID 16621)
-- Name: pgrst_drop_watch; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER pgrst_drop_watch ON sql_drop
   EXECUTE FUNCTION extensions.pgrst_drop_watch();


-- Completed on 2025-08-15 12:38:46 +08

--
-- PostgreSQL database dump complete
--

\unrestrict IN9a0T1cfHtKglbquWA5EgtrBLizrxqybzGccgGW22is8ZcXXAi461fgv71wEAH

