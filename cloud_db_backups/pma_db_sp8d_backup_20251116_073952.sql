--
-- PostgreSQL database dump
--

\restrict ybeoavQlAfE4fAkXQGXgFeM4sccySoO60WllajyexhHhWGa9TpV5SanbNRpZ9ie

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.6 (Homebrew)

-- Started on 2025-11-16 07:39:58 CST

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
ALTER TABLE IF EXISTS ONLY storage.prefixes DROP CONSTRAINT IF EXISTS "prefixes_bucketId_fkey";
ALTER TABLE IF EXISTS ONLY storage.objects DROP CONSTRAINT IF EXISTS "objects_bucketId_fkey";
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_target_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_event_subscriptions DROP CONSTRAINT IF EXISTS user_event_subscriptions_event_id_fkey;
ALTER TABLE IF EXISTS ONLY public.upgrade_logs DROP CONSTRAINT IF EXISTS upgrade_logs_version_id_fkey;
ALTER TABLE IF EXISTS ONLY public.upgrade_logs DROP CONSTRAINT IF EXISTS upgrade_logs_operator_id_fkey;
ALTER TABLE IF EXISTS ONLY public.temp_products DROP CONSTRAINT IF EXISTS temp_products_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.system_metrics DROP CONSTRAINT IF EXISTS system_metrics_version_id_fkey;
ALTER TABLE IF EXISTS ONLY public.stage_reviews DROP CONSTRAINT IF EXISTS stage_reviews_reviewer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.stage_reviews DROP CONSTRAINT IF EXISTS stage_reviews_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.stage_dependencies DROP CONSTRAINT IF EXISTS stage_dependencies_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.stage_attachments DROP CONSTRAINT IF EXISTS stage_attachments_uploaded_by_fkey;
ALTER TABLE IF EXISTS ONLY public.stage_attachments DROP CONSTRAINT IF EXISTS stage_attachments_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.stage_attachments DROP CONSTRAINT IF EXISTS stage_attachments_milestone_id_fkey;
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
ALTER TABLE IF EXISTS ONLY public.settlement_order_details DROP CONSTRAINT IF EXISTS settlement_order_details_settlement_company_id_fkey;
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
ALTER TABLE IF EXISTS ONLY public.projects DROP CONSTRAINT IF EXISTS projects_created_by_fkey;
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
ALTER TABLE IF EXISTS ONLY public.performance_targets DROP CONSTRAINT IF EXISTS performance_targets_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.performance_targets DROP CONSTRAINT IF EXISTS performance_targets_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.performance_targets DROP CONSTRAINT IF EXISTS performance_targets_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.performance_statistics DROP CONSTRAINT IF EXISTS performance_statistics_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_inventory_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_created_by_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_created_by_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_company_id_fkey;
ALTER TABLE IF EXISTS ONLY public.formula_templates_extended DROP CONSTRAINT IF EXISTS formula_templates_extended_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.quotations DROP CONSTRAINT IF EXISTS fk_quotations_customer_id;
ALTER TABLE IF EXISTS ONLY public.project_rating_records DROP CONSTRAINT IF EXISTS fk_project_rating_user_id;
ALTER TABLE IF EXISTS ONLY public.project_rating_records DROP CONSTRAINT IF EXISTS fk_project_rating_project_id;
ALTER TABLE IF EXISTS ONLY public.project_customer_associations DROP CONSTRAINT IF EXISTS fk_project_customer_associations_project_id;
ALTER TABLE IF EXISTS ONLY public.project_customer_associations DROP CONSTRAINT IF EXISTS fk_project_customer_associations_created_by;
ALTER TABLE IF EXISTS ONLY public.project_customer_associations DROP CONSTRAINT IF EXISTS fk_project_customer_associations_company_id;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS fk_expenses_paid_by;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS fk_expenses_contact_id;
ALTER TABLE IF EXISTS ONLY public.approval_branch_condition DROP CONSTRAINT IF EXISTS fk_branch_condition_step;
ALTER TABLE IF EXISTS ONLY public.approval_branch_condition DROP CONSTRAINT IF EXISTS fk_branch_condition_approver;
ALTER TABLE IF EXISTS ONLY public.five_star_project_baselines DROP CONSTRAINT IF EXISTS five_star_project_baselines_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.five_star_project_baselines DROP CONSTRAINT IF EXISTS five_star_project_baselines_created_by_fkey;
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
ALTER TABLE IF EXISTS ONLY public.dev_product_milestones DROP CONSTRAINT IF EXISTS dev_product_milestones_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dev_product_milestones DROP CONSTRAINT IF EXISTS dev_product_milestones_created_by_fkey;
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
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS approval_record_step_id_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS approval_record_instance_id_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS approval_record_approver_id_fkey;
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
ALTER TABLE IF EXISTS ONLY auth.sessions DROP CONSTRAINT IF EXISTS sessions_oauth_client_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.saml_relay_states DROP CONSTRAINT IF EXISTS saml_relay_states_sso_provider_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.saml_relay_states DROP CONSTRAINT IF EXISTS saml_relay_states_flow_state_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.saml_providers DROP CONSTRAINT IF EXISTS saml_providers_sso_provider_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_session_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.one_time_tokens DROP CONSTRAINT IF EXISTS one_time_tokens_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_consents DROP CONSTRAINT IF EXISTS oauth_consents_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_consents DROP CONSTRAINT IF EXISTS oauth_consents_client_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_authorizations DROP CONSTRAINT IF EXISTS oauth_authorizations_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_authorizations DROP CONSTRAINT IF EXISTS oauth_authorizations_client_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_factors DROP CONSTRAINT IF EXISTS mfa_factors_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_challenges DROP CONSTRAINT IF EXISTS mfa_challenges_auth_factor_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_amr_claims DROP CONSTRAINT IF EXISTS mfa_amr_claims_session_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.identities DROP CONSTRAINT IF EXISTS identities_user_id_fkey;
DROP TRIGGER IF EXISTS update_objects_updated_at ON storage.objects;
DROP TRIGGER IF EXISTS prefixes_delete_hierarchy ON storage.prefixes;
DROP TRIGGER IF EXISTS prefixes_create_hierarchy ON storage.prefixes;
DROP TRIGGER IF EXISTS objects_update_create_prefix ON storage.objects;
DROP TRIGGER IF EXISTS objects_insert_create_prefix ON storage.objects;
DROP TRIGGER IF EXISTS objects_delete_delete_prefix ON storage.objects;
DROP TRIGGER IF EXISTS enforce_bucket_name_length_trigger ON storage.buckets;
DROP TRIGGER IF EXISTS tr_check_filters ON realtime.subscription;
DROP TRIGGER IF EXISTS trigger_branch_condition_updated_at ON public.approval_branch_condition;
DROP INDEX IF EXISTS storage.objects_bucket_id_level_idx;
DROP INDEX IF EXISTS storage.name_prefix_search;
DROP INDEX IF EXISTS storage.idx_prefixes_lower_name;
DROP INDEX IF EXISTS storage.idx_objects_lower_name;
DROP INDEX IF EXISTS storage.idx_objects_bucket_id_name;
DROP INDEX IF EXISTS storage.idx_name_bucket_level_unique;
DROP INDEX IF EXISTS storage.idx_multipart_uploads_list;
DROP INDEX IF EXISTS storage.bucketid_objname;
DROP INDEX IF EXISTS storage.bname;
DROP INDEX IF EXISTS realtime.subscription_subscription_id_entity_filters_key;
DROP INDEX IF EXISTS realtime.ix_realtime_subscription_entity;
DROP INDEX IF EXISTS public.ix_system_settings_key;
DROP INDEX IF EXISTS public.ix_role_performance_config_role;
DROP INDEX IF EXISTS public.ix_role_performance_access_role;
DROP INDEX IF EXISTS public.ix_quotations_customer_id;
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
DROP INDEX IF EXISTS public.idx_purchase_orders_total_amount;
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
DROP INDEX IF EXISTS public.idx_dictionaries_phone;
DROP INDEX IF EXISTS public.idx_dictionaries_email;
DROP INDEX IF EXISTS public.idx_dictionaries_company_phone;
DROP INDEX IF EXISTS public.idx_dictionaries_company_email;
DROP INDEX IF EXISTS public.idx_branch_condition_value;
DROP INDEX IF EXISTS public.idx_branch_condition_step_id;
DROP INDEX IF EXISTS public.idx_branch_condition_order;
DROP INDEX IF EXISTS public.idx_branch_condition_approver;
DROP INDEX IF EXISTS auth.users_is_anonymous_idx;
DROP INDEX IF EXISTS auth.users_instance_id_idx;
DROP INDEX IF EXISTS auth.users_instance_id_email_idx;
DROP INDEX IF EXISTS auth.users_email_partial_key;
DROP INDEX IF EXISTS auth.user_id_created_at_idx;
DROP INDEX IF EXISTS auth.unique_phone_factor_per_user;
DROP INDEX IF EXISTS auth.sso_providers_resource_id_pattern_idx;
DROP INDEX IF EXISTS auth.sso_providers_resource_id_idx;
DROP INDEX IF EXISTS auth.sso_domains_sso_provider_id_idx;
DROP INDEX IF EXISTS auth.sso_domains_domain_idx;
DROP INDEX IF EXISTS auth.sessions_user_id_idx;
DROP INDEX IF EXISTS auth.sessions_oauth_client_id_idx;
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
DROP INDEX IF EXISTS auth.oauth_consents_user_order_idx;
DROP INDEX IF EXISTS auth.oauth_consents_active_user_client_idx;
DROP INDEX IF EXISTS auth.oauth_consents_active_client_idx;
DROP INDEX IF EXISTS auth.oauth_clients_deleted_at_idx;
DROP INDEX IF EXISTS auth.oauth_auth_pending_exp_idx;
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
ALTER TABLE IF EXISTS ONLY storage.prefixes DROP CONSTRAINT IF EXISTS prefixes_pkey;
ALTER TABLE IF EXISTS ONLY storage.objects DROP CONSTRAINT IF EXISTS objects_pkey;
ALTER TABLE IF EXISTS ONLY storage.migrations DROP CONSTRAINT IF EXISTS migrations_pkey;
ALTER TABLE IF EXISTS ONLY storage.migrations DROP CONSTRAINT IF EXISTS migrations_name_key;
ALTER TABLE IF EXISTS ONLY storage.buckets DROP CONSTRAINT IF EXISTS buckets_pkey;
ALTER TABLE IF EXISTS ONLY storage.buckets_analytics DROP CONSTRAINT IF EXISTS buckets_analytics_pkey;
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
ALTER TABLE IF EXISTS ONLY public.project_scoring_records DROP CONSTRAINT IF EXISTS uq_scoring_record_with_user;
ALTER TABLE IF EXISTS ONLY public.project_scoring_records DROP CONSTRAINT IF EXISTS uq_scoring_record;
ALTER TABLE IF EXISTS ONLY public.project_scoring_config DROP CONSTRAINT IF EXISTS uq_scoring_config;
ALTER TABLE IF EXISTS ONLY public.role_performance_items DROP CONSTRAINT IF EXISTS uq_role_item_code;
ALTER TABLE IF EXISTS ONLY public.role_performance_access DROP CONSTRAINT IF EXISTS uq_role_access_scope;
ALTER TABLE IF EXISTS ONLY public.project_rating_records DROP CONSTRAINT IF EXISTS uq_project_user_rating;
ALTER TABLE IF EXISTS ONLY public.project_customer_associations DROP CONSTRAINT IF EXISTS uq_project_company_customer_type;
ALTER TABLE IF EXISTS ONLY public.upgrade_logs DROP CONSTRAINT IF EXISTS upgrade_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.performance_targets DROP CONSTRAINT IF EXISTS unique_user_year_month;
ALTER TABLE IF EXISTS ONLY public.performance_statistics DROP CONSTRAINT IF EXISTS unique_statistics_user_year_month;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS unique_company_product_inventory;
ALTER TABLE IF EXISTS ONLY public.five_star_project_baselines DROP CONSTRAINT IF EXISTS unique_baseline_user;
ALTER TABLE IF EXISTS ONLY public.approval_branch_condition DROP CONSTRAINT IF EXISTS uk_step_operator_value;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS uix_user_module;
ALTER TABLE IF EXISTS ONLY public.dictionaries DROP CONSTRAINT IF EXISTS uix_type_key;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS uix_role_module;
ALTER TABLE IF EXISTS ONLY public.affiliations DROP CONSTRAINT IF EXISTS uix_owner_viewer;
ALTER TABLE IF EXISTS ONLY public.temp_products DROP CONSTRAINT IF EXISTS temp_products_pkey;
ALTER TABLE IF EXISTS ONLY public.system_settings DROP CONSTRAINT IF EXISTS system_settings_pkey;
ALTER TABLE IF EXISTS ONLY public.system_metrics DROP CONSTRAINT IF EXISTS system_metrics_pkey;
ALTER TABLE IF EXISTS ONLY public.stage_reviews DROP CONSTRAINT IF EXISTS stage_reviews_pkey;
ALTER TABLE IF EXISTS ONLY public.stage_dependencies DROP CONSTRAINT IF EXISTS stage_dependencies_pkey;
ALTER TABLE IF EXISTS ONLY public.stage_attachments DROP CONSTRAINT IF EXISTS stage_attachments_pkey;
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
ALTER TABLE IF EXISTS ONLY public.dev_product_milestones DROP CONSTRAINT IF EXISTS dev_product_milestones_pkey;
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
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS approval_record_pkey;
ALTER TABLE IF EXISTS ONLY public.approval_process_template DROP CONSTRAINT IF EXISTS approval_process_template_pkey;
ALTER TABLE IF EXISTS ONLY public.approval_instance DROP CONSTRAINT IF EXISTS approval_instance_pkey;
ALTER TABLE IF EXISTS ONLY public.approval_branch_condition DROP CONSTRAINT IF EXISTS approval_branch_condition_pkey;
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
ALTER TABLE IF EXISTS ONLY auth.oauth_consents DROP CONSTRAINT IF EXISTS oauth_consents_user_client_unique;
ALTER TABLE IF EXISTS ONLY auth.oauth_consents DROP CONSTRAINT IF EXISTS oauth_consents_pkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_clients DROP CONSTRAINT IF EXISTS oauth_clients_pkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_authorizations DROP CONSTRAINT IF EXISTS oauth_authorizations_pkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_authorizations DROP CONSTRAINT IF EXISTS oauth_authorizations_authorization_id_key;
ALTER TABLE IF EXISTS ONLY auth.oauth_authorizations DROP CONSTRAINT IF EXISTS oauth_authorizations_authorization_code_key;
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
ALTER TABLE IF EXISTS public.stage_reviews ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.stage_dependencies ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.stage_attachments ALTER COLUMN id DROP DEFAULT;
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
ALTER TABLE IF EXISTS public.dev_product_milestones ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.departments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.data_table_config ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.data_field_config ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.contacts ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.company_assets ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.companies ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.change_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_step ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_record ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_process_template ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_instance ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.affiliations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.actions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.action_reply ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS auth.refresh_tokens ALTER COLUMN id DROP DEFAULT;
DROP TABLE IF EXISTS storage.s3_multipart_uploads_parts;
DROP TABLE IF EXISTS storage.s3_multipart_uploads;
DROP TABLE IF EXISTS storage.prefixes;
DROP TABLE IF EXISTS storage.objects;
DROP TABLE IF EXISTS storage.migrations;
DROP TABLE IF EXISTS storage.buckets_analytics;
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
DROP SEQUENCE IF EXISTS public.stage_reviews_id_seq;
DROP TABLE IF EXISTS public.stage_reviews;
DROP SEQUENCE IF EXISTS public.stage_dependencies_id_seq;
DROP TABLE IF EXISTS public.stage_dependencies;
DROP SEQUENCE IF EXISTS public.stage_attachments_id_seq;
DROP TABLE IF EXISTS public.stage_attachments;
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
DROP TABLE IF EXISTS public.quotations_customer_backup_20251025_214155;
DROP TABLE IF EXISTS public.quotations_customer_backup_20251025_214040;
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
DROP SEQUENCE IF EXISTS public.dev_product_milestones_id_seq;
DROP TABLE IF EXISTS public.dev_product_milestones;
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
DROP SEQUENCE IF EXISTS public.approval_record_id_seq;
DROP TABLE IF EXISTS public.approval_record;
DROP SEQUENCE IF EXISTS public.approval_process_template_id_seq;
DROP TABLE IF EXISTS public.approval_process_template;
DROP SEQUENCE IF EXISTS public.approval_instance_id_seq;
DROP TABLE IF EXISTS public.approval_instance;
DROP TABLE IF EXISTS public.approval_branch_condition;
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
DROP TABLE IF EXISTS auth.oauth_consents;
DROP TABLE IF EXISTS auth.oauth_clients;
DROP TABLE IF EXISTS auth.oauth_authorizations;
DROP TABLE IF EXISTS auth.mfa_factors;
DROP TABLE IF EXISTS auth.mfa_challenges;
DROP TABLE IF EXISTS auth.mfa_amr_claims;
DROP TABLE IF EXISTS auth.instances;
DROP TABLE IF EXISTS auth.identities;
DROP TABLE IF EXISTS auth.flow_state;
DROP TABLE IF EXISTS auth.audit_log_entries;
DROP FUNCTION IF EXISTS storage.update_updated_at_column();
DROP FUNCTION IF EXISTS storage.search_v2(prefix text, bucket_name text, limits integer, levels integer, start_after text, sort_order text, sort_column text, sort_column_after text);
DROP FUNCTION IF EXISTS storage.search_v1_optimised(prefix text, bucketname text, limits integer, levels integer, offsets integer, search text, sortcolumn text, sortorder text);
DROP FUNCTION IF EXISTS storage.search_legacy_v1(prefix text, bucketname text, limits integer, levels integer, offsets integer, search text, sortcolumn text, sortorder text);
DROP FUNCTION IF EXISTS storage.search(prefix text, bucketname text, limits integer, levels integer, offsets integer, search text, sortcolumn text, sortorder text);
DROP FUNCTION IF EXISTS storage.prefixes_insert_trigger();
DROP FUNCTION IF EXISTS storage.prefixes_delete_cleanup();
DROP FUNCTION IF EXISTS storage.operation();
DROP FUNCTION IF EXISTS storage.objects_update_prefix_trigger();
DROP FUNCTION IF EXISTS storage.objects_update_level_trigger();
DROP FUNCTION IF EXISTS storage.objects_update_cleanup();
DROP FUNCTION IF EXISTS storage.objects_insert_prefix_trigger();
DROP FUNCTION IF EXISTS storage.objects_delete_cleanup();
DROP FUNCTION IF EXISTS storage.lock_top_prefixes(bucket_ids text[], names text[]);
DROP FUNCTION IF EXISTS storage.list_objects_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer, start_after text, next_token text);
DROP FUNCTION IF EXISTS storage.list_multipart_uploads_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer, next_key_token text, next_upload_token text);
DROP FUNCTION IF EXISTS storage.get_size_by_bucket();
DROP FUNCTION IF EXISTS storage.get_prefixes(name text);
DROP FUNCTION IF EXISTS storage.get_prefix(name text);
DROP FUNCTION IF EXISTS storage.get_level(name text);
DROP FUNCTION IF EXISTS storage.foldername(name text);
DROP FUNCTION IF EXISTS storage.filename(name text);
DROP FUNCTION IF EXISTS storage.extension(name text);
DROP FUNCTION IF EXISTS storage.enforce_bucket_name_length();
DROP FUNCTION IF EXISTS storage.delete_prefix_hierarchy_trigger();
DROP FUNCTION IF EXISTS storage.delete_prefix(_bucket_id text, _name text);
DROP FUNCTION IF EXISTS storage.delete_leaf_prefixes(bucket_ids text[], names text[]);
DROP FUNCTION IF EXISTS storage.can_insert_object(bucketid text, name text, owner uuid, metadata jsonb);
DROP FUNCTION IF EXISTS storage.add_prefixes(_bucket_id text, _name text);
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
DROP FUNCTION IF EXISTS public.update_branch_condition_updated_at();
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
DROP TYPE IF EXISTS storage.buckettype;
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
DROP TYPE IF EXISTS auth.oauth_response_type;
DROP TYPE IF EXISTS auth.oauth_registration_type;
DROP TYPE IF EXISTS auth.oauth_client_type;
DROP TYPE IF EXISTS auth.oauth_authorization_status;
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
-- TOC entry 55 (class 2615 OID 16492)
-- Name: auth; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA auth;


--
-- TOC entry 15 (class 2615 OID 16388)
-- Name: extensions; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA extensions;


--
-- TOC entry 18 (class 2615 OID 16622)
-- Name: graphql; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA graphql;


--
-- TOC entry 17 (class 2615 OID 16611)
-- Name: graphql_public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA graphql_public;


--
-- TOC entry 12 (class 2615 OID 16386)
-- Name: pgbouncer; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA pgbouncer;


--
-- TOC entry 9 (class 2615 OID 16603)
-- Name: realtime; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA realtime;


--
-- TOC entry 56 (class 2615 OID 16540)
-- Name: storage; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA storage;


--
-- TOC entry 16 (class 2615 OID 16651)
-- Name: vault; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA vault;


--
-- TOC entry 6 (class 3079 OID 16687)
-- Name: pg_graphql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_graphql WITH SCHEMA graphql;


--
-- TOC entry 5161 (class 0 OID 0)
-- Dependencies: 6
-- Name: EXTENSION pg_graphql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_graphql IS 'pg_graphql: GraphQL support';


--
-- TOC entry 4 (class 3079 OID 16389)
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA extensions;


--
-- TOC entry 5162 (class 0 OID 0)
-- Dependencies: 4
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


--
-- TOC entry 2 (class 3079 OID 16441)
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;


--
-- TOC entry 5163 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- TOC entry 5 (class 3079 OID 16652)
-- Name: supabase_vault; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS supabase_vault WITH SCHEMA vault;


--
-- TOC entry 5164 (class 0 OID 0)
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
-- TOC entry 5165 (class 0 OID 0)
-- Dependencies: 3
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- TOC entry 1246 (class 1247 OID 16780)
-- Name: aal_level; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.aal_level AS ENUM (
    'aal1',
    'aal2',
    'aal3'
);


--
-- TOC entry 1270 (class 1247 OID 16921)
-- Name: code_challenge_method; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.code_challenge_method AS ENUM (
    's256',
    'plain'
);


--
-- TOC entry 1243 (class 1247 OID 16774)
-- Name: factor_status; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.factor_status AS ENUM (
    'unverified',
    'verified'
);


--
-- TOC entry 1240 (class 1247 OID 16769)
-- Name: factor_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.factor_type AS ENUM (
    'totp',
    'webauthn',
    'phone'
);


--
-- TOC entry 1579 (class 1247 OID 96007)
-- Name: oauth_authorization_status; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_authorization_status AS ENUM (
    'pending',
    'approved',
    'denied',
    'expired'
);


--
-- TOC entry 1591 (class 1247 OID 96079)
-- Name: oauth_client_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_client_type AS ENUM (
    'public',
    'confidential'
);


--
-- TOC entry 1312 (class 1247 OID 47142)
-- Name: oauth_registration_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_registration_type AS ENUM (
    'dynamic',
    'manual'
);


--
-- TOC entry 1582 (class 1247 OID 96016)
-- Name: oauth_response_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_response_type AS ENUM (
    'code'
);


--
-- TOC entry 1276 (class 1247 OID 16963)
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
-- TOC entry 1333 (class 1247 OID 17269)
-- Name: approval_action; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_action AS ENUM (
    'approve',
    'reject'
);


--
-- TOC entry 1336 (class 1247 OID 17274)
-- Name: approval_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approval_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);


--
-- TOC entry 1339 (class 1247 OID 17282)
-- Name: approvalaction; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalaction AS ENUM (
    'approve',
    'reject'
);


--
-- TOC entry 1342 (class 1247 OID 17288)
-- Name: approvalinstancestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalinstancestatus AS ENUM (
    'pending',
    'approved',
    'rejected'
);


--
-- TOC entry 1345 (class 1247 OID 17296)
-- Name: approvalstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.approvalstatus AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED',
    'RECALLED'
);


--
-- TOC entry 1348 (class 1247 OID 17306)
-- Name: pricingorderapprovalflowtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricingorderapprovalflowtype AS ENUM (
    'CHANNEL_FOLLOW',
    'SALES_KEY',
    'SALES_OPPORTUNITY'
);


--
-- TOC entry 1351 (class 1247 OID 17314)
-- Name: pricingorderstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricingorderstatus AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- TOC entry 1324 (class 1247 OID 17324)
-- Name: settlementorderstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.settlementorderstatus AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED'
);


--
-- TOC entry 1294 (class 1247 OID 17046)
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
-- TOC entry 1285 (class 1247 OID 17006)
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
-- TOC entry 1288 (class 1247 OID 17021)
-- Name: user_defined_filter; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.user_defined_filter AS (
	column_name text,
	op realtime.equality_op,
	value text
);


--
-- TOC entry 1300 (class 1247 OID 17171)
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
-- TOC entry 1297 (class 1247 OID 17059)
-- Name: wal_rls; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.wal_rls AS (
	wal jsonb,
	is_rls_enabled boolean,
	subscription_ids uuid[],
	errors text[]
);


--
-- TOC entry 1537 (class 1247 OID 18740)
-- Name: buckettype; Type: TYPE; Schema: storage; Owner: -
--

CREATE TYPE storage.buckettype AS ENUM (
    'STANDARD',
    'ANALYTICS'
);


--
-- TOC entry 520 (class 1255 OID 16538)
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
-- TOC entry 5166 (class 0 OID 0)
-- Dependencies: 520
-- Name: FUNCTION email(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.email() IS 'Deprecated. Use auth.jwt() -> ''email'' instead.';


--
-- TOC entry 539 (class 1255 OID 16751)
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
-- TOC entry 519 (class 1255 OID 16537)
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
-- TOC entry 5167 (class 0 OID 0)
-- Dependencies: 519
-- Name: FUNCTION role(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.role() IS 'Deprecated. Use auth.jwt() -> ''role'' instead.';


--
-- TOC entry 518 (class 1255 OID 16536)
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
-- TOC entry 5168 (class 0 OID 0)
-- Dependencies: 518
-- Name: FUNCTION uid(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.uid() IS 'Deprecated. Use auth.jwt() -> ''sub'' instead.';


--
-- TOC entry 521 (class 1255 OID 16595)
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
-- TOC entry 5169 (class 0 OID 0)
-- Dependencies: 521
-- Name: FUNCTION grant_pg_cron_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_cron_access() IS 'Grants access to pg_cron';


--
-- TOC entry 525 (class 1255 OID 16616)
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
-- TOC entry 5170 (class 0 OID 0)
-- Dependencies: 525
-- Name: FUNCTION grant_pg_graphql_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_graphql_access() IS 'Grants access to pg_graphql';


--
-- TOC entry 522 (class 1255 OID 16597)
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
-- TOC entry 5171 (class 0 OID 0)
-- Dependencies: 522
-- Name: FUNCTION grant_pg_net_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_net_access() IS 'Grants access to pg_net';


--
-- TOC entry 523 (class 1255 OID 16607)
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
-- TOC entry 524 (class 1255 OID 16608)
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
-- TOC entry 526 (class 1255 OID 16618)
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
-- TOC entry 5172 (class 0 OID 0)
-- Dependencies: 526
-- Name: FUNCTION set_graphql_placeholder(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.set_graphql_placeholder() IS 'Reintroduces placeholder function for graphql_public.graphql';


--
-- TOC entry 468 (class 1255 OID 16387)
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
-- TOC entry 574 (class 1255 OID 37164)
-- Name: update_branch_condition_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_branch_condition_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- TOC entry 548 (class 1255 OID 17094)
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
-- TOC entry 560 (class 1255 OID 17244)
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
-- TOC entry 556 (class 1255 OID 17177)
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
-- TOC entry 543 (class 1255 OID 17043)
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
-- TOC entry 542 (class 1255 OID 17038)
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
-- TOC entry 554 (class 1255 OID 17172)
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
-- TOC entry 557 (class 1255 OID 17184)
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
-- TOC entry 541 (class 1255 OID 17037)
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
-- TOC entry 559 (class 1255 OID 17243)
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
-- TOC entry 540 (class 1255 OID 17035)
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
-- TOC entry 544 (class 1255 OID 17070)
-- Name: to_regrole(text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.to_regrole(role_name text) RETURNS regrole
    LANGUAGE sql IMMUTABLE
    AS $$ select role_name::regrole $$;


--
-- TOC entry 558 (class 1255 OID 17237)
-- Name: topic(); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.topic() RETURNS text
    LANGUAGE sql STABLE
    AS $$
select nullif(current_setting('realtime.topic', true), '')::text;
$$;


--
-- TOC entry 564 (class 1255 OID 18718)
-- Name: add_prefixes(text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.add_prefixes(_bucket_id text, _name text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    prefixes text[];
BEGIN
    prefixes := "storage"."get_prefixes"("_name");

    IF array_length(prefixes, 1) > 0 THEN
        INSERT INTO storage.prefixes (name, bucket_id)
        SELECT UNNEST(prefixes) as name, "_bucket_id" ON CONFLICT DO NOTHING;
    END IF;
END;
$$;


--
-- TOC entry 551 (class 1255 OID 17111)
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
-- TOC entry 577 (class 1255 OID 71619)
-- Name: delete_leaf_prefixes(text[], text[]); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.delete_leaf_prefixes(bucket_ids text[], names text[]) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_rows_deleted integer;
BEGIN
    LOOP
        WITH candidates AS (
            SELECT DISTINCT
                t.bucket_id,
                unnest(storage.get_prefixes(t.name)) AS name
            FROM unnest(bucket_ids, names) AS t(bucket_id, name)
        ),
        uniq AS (
             SELECT
                 bucket_id,
                 name,
                 storage.get_level(name) AS level
             FROM candidates
             WHERE name <> ''
             GROUP BY bucket_id, name
        ),
        leaf AS (
             SELECT
                 p.bucket_id,
                 p.name,
                 p.level
             FROM storage.prefixes AS p
                  JOIN uniq AS u
                       ON u.bucket_id = p.bucket_id
                           AND u.name = p.name
                           AND u.level = p.level
             WHERE NOT EXISTS (
                 SELECT 1
                 FROM storage.objects AS o
                 WHERE o.bucket_id = p.bucket_id
                   AND o.level = p.level + 1
                   AND o.name COLLATE "C" LIKE p.name || '/%'
             )
             AND NOT EXISTS (
                 SELECT 1
                 FROM storage.prefixes AS c
                 WHERE c.bucket_id = p.bucket_id
                   AND c.level = p.level + 1
                   AND c.name COLLATE "C" LIKE p.name || '/%'
             )
        )
        DELETE
        FROM storage.prefixes AS p
            USING leaf AS l
        WHERE p.bucket_id = l.bucket_id
          AND p.name = l.name
          AND p.level = l.level;

        GET DIAGNOSTICS v_rows_deleted = ROW_COUNT;
        EXIT WHEN v_rows_deleted = 0;
    END LOOP;
END;
$$;


--
-- TOC entry 565 (class 1255 OID 18719)
-- Name: delete_prefix(text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.delete_prefix(_bucket_id text, _name text) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    -- Check if we can delete the prefix
    IF EXISTS(
        SELECT FROM "storage"."prefixes"
        WHERE "prefixes"."bucket_id" = "_bucket_id"
          AND level = "storage"."get_level"("_name") + 1
          AND "prefixes"."name" COLLATE "C" LIKE "_name" || '/%'
        LIMIT 1
    )
    OR EXISTS(
        SELECT FROM "storage"."objects"
        WHERE "objects"."bucket_id" = "_bucket_id"
          AND "storage"."get_level"("objects"."name") = "storage"."get_level"("_name") + 1
          AND "objects"."name" COLLATE "C" LIKE "_name" || '/%'
        LIMIT 1
    ) THEN
    -- There are sub-objects, skip deletion
    RETURN false;
    ELSE
        DELETE FROM "storage"."prefixes"
        WHERE "prefixes"."bucket_id" = "_bucket_id"
          AND level = "storage"."get_level"("_name")
          AND "prefixes"."name" = "_name";
        RETURN true;
    END IF;
END;
$$;


--
-- TOC entry 568 (class 1255 OID 18722)
-- Name: delete_prefix_hierarchy_trigger(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.delete_prefix_hierarchy_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    prefix text;
BEGIN
    prefix := "storage"."get_prefix"(OLD."name");

    IF coalesce(prefix, '') != '' THEN
        PERFORM "storage"."delete_prefix"(OLD."bucket_id", prefix);
    END IF;

    RETURN OLD;
END;
$$;


--
-- TOC entry 573 (class 1255 OID 18737)
-- Name: enforce_bucket_name_length(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.enforce_bucket_name_length() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
    if length(new.name) > 100 then
        raise exception 'bucket name "%" is too long (% characters). Max is 100.', new.name, length(new.name);
    end if;
    return new;
end;
$$;


--
-- TOC entry 547 (class 1255 OID 17083)
-- Name: extension(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.extension(name text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    _parts text[];
    _filename text;
BEGIN
    SELECT string_to_array(name, '/') INTO _parts;
    SELECT _parts[array_length(_parts,1)] INTO _filename;
    RETURN reverse(split_part(reverse(_filename), '.', 1));
END
$$;


--
-- TOC entry 546 (class 1255 OID 17082)
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
-- TOC entry 545 (class 1255 OID 17080)
-- Name: foldername(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.foldername(name text) RETURNS text[]
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    _parts text[];
BEGIN
    -- Split on "/" to get path segments
    SELECT string_to_array(name, '/') INTO _parts;
    -- Return everything except the last segment
    RETURN _parts[1 : array_length(_parts,1) - 1];
END
$$;


--
-- TOC entry 561 (class 1255 OID 18700)
-- Name: get_level(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_level(name text) RETURNS integer
    LANGUAGE sql IMMUTABLE STRICT
    AS $$
SELECT array_length(string_to_array("name", '/'), 1);
$$;


--
-- TOC entry 562 (class 1255 OID 18716)
-- Name: get_prefix(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_prefix(name text) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$
SELECT
    CASE WHEN strpos("name", '/') > 0 THEN
             regexp_replace("name", '[\/]{1}[^\/]+\/?$', '')
         ELSE
             ''
        END;
$_$;


--
-- TOC entry 563 (class 1255 OID 18717)
-- Name: get_prefixes(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_prefixes(name text) RETURNS text[]
    LANGUAGE plpgsql IMMUTABLE STRICT
    AS $$
DECLARE
    parts text[];
    prefixes text[];
    prefix text;
BEGIN
    -- Split the name into parts by '/'
    parts := string_to_array("name", '/');
    prefixes := '{}';

    -- Construct the prefixes, stopping one level below the last part
    FOR i IN 1..array_length(parts, 1) - 1 LOOP
            prefix := array_to_string(parts[1:i], '/');
            prefixes := array_append(prefixes, prefix);
    END LOOP;

    RETURN prefixes;
END;
$$;


--
-- TOC entry 571 (class 1255 OID 18735)
-- Name: get_size_by_bucket(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_size_by_bucket() RETURNS TABLE(size bigint, bucket_id text)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    return query
        select sum((metadata->>'size')::bigint) as size, obj.bucket_id
        from "storage".objects as obj
        group by obj.bucket_id;
END
$$;


--
-- TOC entry 553 (class 1255 OID 17153)
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
-- TOC entry 552 (class 1255 OID 17115)
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
-- TOC entry 576 (class 1255 OID 71618)
-- Name: lock_top_prefixes(text[], text[]); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.lock_top_prefixes(bucket_ids text[], names text[]) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_bucket text;
    v_top text;
BEGIN
    FOR v_bucket, v_top IN
        SELECT DISTINCT t.bucket_id,
            split_part(t.name, '/', 1) AS top
        FROM unnest(bucket_ids, names) AS t(bucket_id, name)
        WHERE t.name <> ''
        ORDER BY 1, 2
        LOOP
            PERFORM pg_advisory_xact_lock(hashtextextended(v_bucket || '/' || v_top, 0));
        END LOOP;
END;
$$;


--
-- TOC entry 578 (class 1255 OID 71620)
-- Name: objects_delete_cleanup(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.objects_delete_cleanup() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_bucket_ids text[];
    v_names      text[];
BEGIN
    IF current_setting('storage.gc.prefixes', true) = '1' THEN
        RETURN NULL;
    END IF;

    PERFORM set_config('storage.gc.prefixes', '1', true);

    SELECT COALESCE(array_agg(d.bucket_id), '{}'),
           COALESCE(array_agg(d.name), '{}')
    INTO v_bucket_ids, v_names
    FROM deleted AS d
    WHERE d.name <> '';

    PERFORM storage.lock_top_prefixes(v_bucket_ids, v_names);
    PERFORM storage.delete_leaf_prefixes(v_bucket_ids, v_names);

    RETURN NULL;
END;
$$;


--
-- TOC entry 567 (class 1255 OID 18721)
-- Name: objects_insert_prefix_trigger(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.objects_insert_prefix_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM "storage"."add_prefixes"(NEW."bucket_id", NEW."name");
    NEW.level := "storage"."get_level"(NEW."name");

    RETURN NEW;
END;
$$;


--
-- TOC entry 579 (class 1255 OID 71621)
-- Name: objects_update_cleanup(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.objects_update_cleanup() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    -- NEW - OLD (destinations to create prefixes for)
    v_add_bucket_ids text[];
    v_add_names      text[];

    -- OLD - NEW (sources to prune)
    v_src_bucket_ids text[];
    v_src_names      text[];
BEGIN
    IF TG_OP <> 'UPDATE' THEN
        RETURN NULL;
    END IF;

    -- 1) Compute NEW−OLD (added paths) and OLD−NEW (moved-away paths)
    WITH added AS (
        SELECT n.bucket_id, n.name
        FROM new_rows n
        WHERE n.name <> '' AND position('/' in n.name) > 0
        EXCEPT
        SELECT o.bucket_id, o.name FROM old_rows o WHERE o.name <> ''
    ),
    moved AS (
         SELECT o.bucket_id, o.name
         FROM old_rows o
         WHERE o.name <> ''
         EXCEPT
         SELECT n.bucket_id, n.name FROM new_rows n WHERE n.name <> ''
    )
    SELECT
        -- arrays for ADDED (dest) in stable order
        COALESCE( (SELECT array_agg(a.bucket_id ORDER BY a.bucket_id, a.name) FROM added a), '{}' ),
        COALESCE( (SELECT array_agg(a.name      ORDER BY a.bucket_id, a.name) FROM added a), '{}' ),
        -- arrays for MOVED (src) in stable order
        COALESCE( (SELECT array_agg(m.bucket_id ORDER BY m.bucket_id, m.name) FROM moved m), '{}' ),
        COALESCE( (SELECT array_agg(m.name      ORDER BY m.bucket_id, m.name) FROM moved m), '{}' )
    INTO v_add_bucket_ids, v_add_names, v_src_bucket_ids, v_src_names;

    -- Nothing to do?
    IF (array_length(v_add_bucket_ids, 1) IS NULL) AND (array_length(v_src_bucket_ids, 1) IS NULL) THEN
        RETURN NULL;
    END IF;

    -- 2) Take per-(bucket, top) locks: ALL prefixes in consistent global order to prevent deadlocks
    DECLARE
        v_all_bucket_ids text[];
        v_all_names text[];
    BEGIN
        -- Combine source and destination arrays for consistent lock ordering
        v_all_bucket_ids := COALESCE(v_src_bucket_ids, '{}') || COALESCE(v_add_bucket_ids, '{}');
        v_all_names := COALESCE(v_src_names, '{}') || COALESCE(v_add_names, '{}');

        -- Single lock call ensures consistent global ordering across all transactions
        IF array_length(v_all_bucket_ids, 1) IS NOT NULL THEN
            PERFORM storage.lock_top_prefixes(v_all_bucket_ids, v_all_names);
        END IF;
    END;

    -- 3) Create destination prefixes (NEW−OLD) BEFORE pruning sources
    IF array_length(v_add_bucket_ids, 1) IS NOT NULL THEN
        WITH candidates AS (
            SELECT DISTINCT t.bucket_id, unnest(storage.get_prefixes(t.name)) AS name
            FROM unnest(v_add_bucket_ids, v_add_names) AS t(bucket_id, name)
            WHERE name <> ''
        )
        INSERT INTO storage.prefixes (bucket_id, name)
        SELECT c.bucket_id, c.name
        FROM candidates c
        ON CONFLICT DO NOTHING;
    END IF;

    -- 4) Prune source prefixes bottom-up for OLD−NEW
    IF array_length(v_src_bucket_ids, 1) IS NOT NULL THEN
        -- re-entrancy guard so DELETE on prefixes won't recurse
        IF current_setting('storage.gc.prefixes', true) <> '1' THEN
            PERFORM set_config('storage.gc.prefixes', '1', true);
        END IF;

        PERFORM storage.delete_leaf_prefixes(v_src_bucket_ids, v_src_names);
    END IF;

    RETURN NULL;
END;
$$;


--
-- TOC entry 581 (class 1255 OID 74944)
-- Name: objects_update_level_trigger(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.objects_update_level_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Ensure this is an update operation and the name has changed
    IF TG_OP = 'UPDATE' AND (NEW."name" <> OLD."name" OR NEW."bucket_id" <> OLD."bucket_id") THEN
        -- Set the new level
        NEW."level" := "storage"."get_level"(NEW."name");
    END IF;
    RETURN NEW;
END;
$$;


--
-- TOC entry 572 (class 1255 OID 18736)
-- Name: objects_update_prefix_trigger(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.objects_update_prefix_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    old_prefixes TEXT[];
BEGIN
    -- Ensure this is an update operation and the name has changed
    IF TG_OP = 'UPDATE' AND (NEW."name" <> OLD."name" OR NEW."bucket_id" <> OLD."bucket_id") THEN
        -- Retrieve old prefixes
        old_prefixes := "storage"."get_prefixes"(OLD."name");

        -- Remove old prefixes that are only used by this object
        WITH all_prefixes as (
            SELECT unnest(old_prefixes) as prefix
        ),
        can_delete_prefixes as (
             SELECT prefix
             FROM all_prefixes
             WHERE NOT EXISTS (
                 SELECT 1 FROM "storage"."objects"
                 WHERE "bucket_id" = OLD."bucket_id"
                   AND "name" <> OLD."name"
                   AND "name" LIKE (prefix || '%')
             )
         )
        DELETE FROM "storage"."prefixes" WHERE name IN (SELECT prefix FROM can_delete_prefixes);

        -- Add new prefixes
        PERFORM "storage"."add_prefixes"(NEW."bucket_id", NEW."name");
    END IF;
    -- Set the new level
    NEW."level" := "storage"."get_level"(NEW."name");

    RETURN NEW;
END;
$$;


--
-- TOC entry 555 (class 1255 OID 17173)
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
-- TOC entry 580 (class 1255 OID 71622)
-- Name: prefixes_delete_cleanup(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.prefixes_delete_cleanup() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_bucket_ids text[];
    v_names      text[];
BEGIN
    IF current_setting('storage.gc.prefixes', true) = '1' THEN
        RETURN NULL;
    END IF;

    PERFORM set_config('storage.gc.prefixes', '1', true);

    SELECT COALESCE(array_agg(d.bucket_id), '{}'),
           COALESCE(array_agg(d.name), '{}')
    INTO v_bucket_ids, v_names
    FROM deleted AS d
    WHERE d.name <> '';

    PERFORM storage.lock_top_prefixes(v_bucket_ids, v_names);
    PERFORM storage.delete_leaf_prefixes(v_bucket_ids, v_names);

    RETURN NULL;
END;
$$;


--
-- TOC entry 566 (class 1255 OID 18720)
-- Name: prefixes_insert_trigger(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.prefixes_insert_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM "storage"."add_prefixes"(NEW."bucket_id", NEW."name");
    RETURN NEW;
END;
$$;


--
-- TOC entry 549 (class 1255 OID 17100)
-- Name: search(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql
    AS $$
declare
    can_bypass_rls BOOLEAN;
begin
    SELECT rolbypassrls
    INTO can_bypass_rls
    FROM pg_roles
    WHERE rolname = coalesce(nullif(current_setting('role', true), 'none'), current_user);

    IF can_bypass_rls THEN
        RETURN QUERY SELECT * FROM storage.search_v1_optimised(prefix, bucketname, limits, levels, offsets, search, sortcolumn, sortorder);
    ELSE
        RETURN QUERY SELECT * FROM storage.search_legacy_v1(prefix, bucketname, limits, levels, offsets, search, sortcolumn, sortorder);
    END IF;
end;
$$;


--
-- TOC entry 570 (class 1255 OID 18733)
-- Name: search_legacy_v1(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search_legacy_v1(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
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
-- TOC entry 569 (class 1255 OID 18732)
-- Name: search_v1_optimised(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search_v1_optimised(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
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
           select (string_to_array(name, ''/''))[level] as name
           from storage.prefixes
             where lower(prefixes.name) like lower($2 || $3) || ''%''
               and bucket_id = $4
               and level = $1
           order by name ' || v_sort_order || '
     )
     (select name,
            null as id,
            null as updated_at,
            null as created_at,
            null as last_accessed_at,
            null as metadata from folders)
     union all
     (select path_tokens[level] as "name",
            id,
            updated_at,
            created_at,
            last_accessed_at,
            metadata
     from storage.objects
     where lower(objects.name) like lower($2 || $3) || ''%''
       and bucket_id = $4
       and level = $1
     order by ' || v_order_by || ')
     limit $5
     offset $6' using levels, prefix, search, bucketname, limits, offsets;
end;
$_$;


--
-- TOC entry 575 (class 1255 OID 71617)
-- Name: search_v2(text, text, integer, integer, text, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search_v2(prefix text, bucket_name text, limits integer DEFAULT 100, levels integer DEFAULT 1, start_after text DEFAULT ''::text, sort_order text DEFAULT 'asc'::text, sort_column text DEFAULT 'name'::text, sort_column_after text DEFAULT ''::text) RETURNS TABLE(key text, name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $_$
DECLARE
    sort_col text;
    sort_ord text;
    cursor_op text;
    cursor_expr text;
    sort_expr text;
BEGIN
    -- Validate sort_order
    sort_ord := lower(sort_order);
    IF sort_ord NOT IN ('asc', 'desc') THEN
        sort_ord := 'asc';
    END IF;

    -- Determine cursor comparison operator
    IF sort_ord = 'asc' THEN
        cursor_op := '>';
    ELSE
        cursor_op := '<';
    END IF;
    
    sort_col := lower(sort_column);
    -- Validate sort column  
    IF sort_col IN ('updated_at', 'created_at') THEN
        cursor_expr := format(
            '($5 = '''' OR ROW(date_trunc(''milliseconds'', %I), name COLLATE "C") %s ROW(COALESCE(NULLIF($6, '''')::timestamptz, ''epoch''::timestamptz), $5))',
            sort_col, cursor_op
        );
        sort_expr := format(
            'COALESCE(date_trunc(''milliseconds'', %I), ''epoch''::timestamptz) %s, name COLLATE "C" %s',
            sort_col, sort_ord, sort_ord
        );
    ELSE
        cursor_expr := format('($5 = '''' OR name COLLATE "C" %s $5)', cursor_op);
        sort_expr := format('name COLLATE "C" %s', sort_ord);
    END IF;

    RETURN QUERY EXECUTE format(
        $sql$
        SELECT * FROM (
            (
                SELECT
                    split_part(name, '/', $4) AS key,
                    name,
                    NULL::uuid AS id,
                    updated_at,
                    created_at,
                    NULL::timestamptz AS last_accessed_at,
                    NULL::jsonb AS metadata
                FROM storage.prefixes
                WHERE name COLLATE "C" LIKE $1 || '%%'
                    AND bucket_id = $2
                    AND level = $4
                    AND %s
                ORDER BY %s
                LIMIT $3
            )
            UNION ALL
            (
                SELECT
                    split_part(name, '/', $4) AS key,
                    name,
                    id,
                    updated_at,
                    created_at,
                    last_accessed_at,
                    metadata
                FROM storage.objects
                WHERE name COLLATE "C" LIKE $1 || '%%'
                    AND bucket_id = $2
                    AND level = $4
                    AND %s
                ORDER BY %s
                LIMIT $3
            )
        ) obj
        ORDER BY %s
        LIMIT $3
        $sql$,
        cursor_expr,    -- prefixes WHERE
        sort_expr,      -- prefixes ORDER BY
        cursor_expr,    -- objects WHERE
        sort_expr,      -- objects ORDER BY
        sort_expr       -- final ORDER BY
    )
    USING prefix, bucket_name, limits, levels, start_after, sort_column_after;
END;
$_$;


--
-- TOC entry 550 (class 1255 OID 17101)
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
-- TOC entry 274 (class 1259 OID 16523)
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
-- TOC entry 5173 (class 0 OID 0)
-- Dependencies: 274
-- Name: TABLE audit_log_entries; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.audit_log_entries IS 'Auth: Audit trail for user actions.';


--
-- TOC entry 291 (class 1259 OID 16925)
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
-- TOC entry 5174 (class 0 OID 0)
-- Dependencies: 291
-- Name: TABLE flow_state; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.flow_state IS 'stores metadata for pkce logins';


--
-- TOC entry 282 (class 1259 OID 16723)
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
-- TOC entry 5175 (class 0 OID 0)
-- Dependencies: 282
-- Name: TABLE identities; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.identities IS 'Auth: Stores identities associated to a user.';


--
-- TOC entry 5176 (class 0 OID 0)
-- Dependencies: 282
-- Name: COLUMN identities.email; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.identities.email IS 'Auth: Email is a generated column that references the optional email property in the identity_data';


--
-- TOC entry 273 (class 1259 OID 16516)
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
-- TOC entry 5177 (class 0 OID 0)
-- Dependencies: 273
-- Name: TABLE instances; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.instances IS 'Auth: Manages users across multiple sites.';


--
-- TOC entry 286 (class 1259 OID 16812)
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
-- TOC entry 5178 (class 0 OID 0)
-- Dependencies: 286
-- Name: TABLE mfa_amr_claims; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_amr_claims IS 'auth: stores authenticator method reference claims for multi factor authentication';


--
-- TOC entry 285 (class 1259 OID 16800)
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
-- TOC entry 5179 (class 0 OID 0)
-- Dependencies: 285
-- Name: TABLE mfa_challenges; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_challenges IS 'auth: stores metadata about challenge requests made';


--
-- TOC entry 284 (class 1259 OID 16787)
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
    web_authn_aaguid uuid,
    last_webauthn_challenge_data jsonb
);


--
-- TOC entry 5180 (class 0 OID 0)
-- Dependencies: 284
-- Name: TABLE mfa_factors; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_factors IS 'auth: stores metadata about factors';


--
-- TOC entry 5181 (class 0 OID 0)
-- Dependencies: 284
-- Name: COLUMN mfa_factors.last_webauthn_challenge_data; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.mfa_factors.last_webauthn_challenge_data IS 'Stores the latest WebAuthn challenge data including attestation/assertion for customer verification';


--
-- TOC entry 453 (class 1259 OID 96019)
-- Name: oauth_authorizations; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.oauth_authorizations (
    id uuid NOT NULL,
    authorization_id text NOT NULL,
    client_id uuid NOT NULL,
    user_id uuid,
    redirect_uri text NOT NULL,
    scope text NOT NULL,
    state text,
    resource text,
    code_challenge text,
    code_challenge_method auth.code_challenge_method,
    response_type auth.oauth_response_type DEFAULT 'code'::auth.oauth_response_type NOT NULL,
    status auth.oauth_authorization_status DEFAULT 'pending'::auth.oauth_authorization_status NOT NULL,
    authorization_code text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone DEFAULT (now() + '00:03:00'::interval) NOT NULL,
    approved_at timestamp with time zone,
    CONSTRAINT oauth_authorizations_authorization_code_length CHECK ((char_length(authorization_code) <= 255)),
    CONSTRAINT oauth_authorizations_code_challenge_length CHECK ((char_length(code_challenge) <= 128)),
    CONSTRAINT oauth_authorizations_expires_at_future CHECK ((expires_at > created_at)),
    CONSTRAINT oauth_authorizations_redirect_uri_length CHECK ((char_length(redirect_uri) <= 2048)),
    CONSTRAINT oauth_authorizations_resource_length CHECK ((char_length(resource) <= 2048)),
    CONSTRAINT oauth_authorizations_scope_length CHECK ((char_length(scope) <= 4096)),
    CONSTRAINT oauth_authorizations_state_length CHECK ((char_length(state) <= 4096))
);


--
-- TOC entry 444 (class 1259 OID 47147)
-- Name: oauth_clients; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.oauth_clients (
    id uuid NOT NULL,
    client_secret_hash text,
    registration_type auth.oauth_registration_type NOT NULL,
    redirect_uris text NOT NULL,
    grant_types text NOT NULL,
    client_name text,
    client_uri text,
    logo_uri text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    client_type auth.oauth_client_type DEFAULT 'confidential'::auth.oauth_client_type NOT NULL,
    CONSTRAINT oauth_clients_client_name_length CHECK ((char_length(client_name) <= 1024)),
    CONSTRAINT oauth_clients_client_uri_length CHECK ((char_length(client_uri) <= 2048)),
    CONSTRAINT oauth_clients_logo_uri_length CHECK ((char_length(logo_uri) <= 2048))
);


--
-- TOC entry 454 (class 1259 OID 96052)
-- Name: oauth_consents; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.oauth_consents (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    client_id uuid NOT NULL,
    scopes text NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone,
    CONSTRAINT oauth_consents_revoked_after_granted CHECK (((revoked_at IS NULL) OR (revoked_at >= granted_at))),
    CONSTRAINT oauth_consents_scopes_length CHECK ((char_length(scopes) <= 2048)),
    CONSTRAINT oauth_consents_scopes_not_empty CHECK ((char_length(TRIM(BOTH FROM scopes)) > 0))
);


--
-- TOC entry 292 (class 1259 OID 16975)
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
-- TOC entry 272 (class 1259 OID 16505)
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
-- TOC entry 5182 (class 0 OID 0)
-- Dependencies: 272
-- Name: TABLE refresh_tokens; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.refresh_tokens IS 'Auth: Store of tokens used to refresh JWT tokens once they expire.';


--
-- TOC entry 271 (class 1259 OID 16504)
-- Name: refresh_tokens_id_seq; Type: SEQUENCE; Schema: auth; Owner: -
--

CREATE SEQUENCE auth.refresh_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5183 (class 0 OID 0)
-- Dependencies: 271
-- Name: refresh_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: -
--

ALTER SEQUENCE auth.refresh_tokens_id_seq OWNED BY auth.refresh_tokens.id;


--
-- TOC entry 289 (class 1259 OID 16854)
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
-- TOC entry 5184 (class 0 OID 0)
-- Dependencies: 289
-- Name: TABLE saml_providers; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.saml_providers IS 'Auth: Manages SAML Identity Provider connections.';


--
-- TOC entry 290 (class 1259 OID 16872)
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
-- TOC entry 5185 (class 0 OID 0)
-- Dependencies: 290
-- Name: TABLE saml_relay_states; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.saml_relay_states IS 'Auth: Contains SAML Relay State information for each Service Provider initiated login.';


--
-- TOC entry 275 (class 1259 OID 16531)
-- Name: schema_migrations; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.schema_migrations (
    version character varying(255) NOT NULL
);


--
-- TOC entry 5186 (class 0 OID 0)
-- Dependencies: 275
-- Name: TABLE schema_migrations; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.schema_migrations IS 'Auth: Manages updates to the auth system.';


--
-- TOC entry 283 (class 1259 OID 16753)
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
    tag text,
    oauth_client_id uuid,
    refresh_token_hmac_key text,
    refresh_token_counter bigint
);


--
-- TOC entry 5187 (class 0 OID 0)
-- Dependencies: 283
-- Name: TABLE sessions; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sessions IS 'Auth: Stores session data associated to a user.';


--
-- TOC entry 5188 (class 0 OID 0)
-- Dependencies: 283
-- Name: COLUMN sessions.not_after; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.not_after IS 'Auth: Not after is a nullable column that contains a timestamp after which the session should be regarded as expired.';


--
-- TOC entry 5189 (class 0 OID 0)
-- Dependencies: 283
-- Name: COLUMN sessions.refresh_token_hmac_key; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.refresh_token_hmac_key IS 'Holds a HMAC-SHA256 key used to sign refresh tokens for this session.';


--
-- TOC entry 5190 (class 0 OID 0)
-- Dependencies: 283
-- Name: COLUMN sessions.refresh_token_counter; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.refresh_token_counter IS 'Holds the ID (counter) of the last issued refresh token.';


--
-- TOC entry 288 (class 1259 OID 16839)
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
-- TOC entry 5191 (class 0 OID 0)
-- Dependencies: 288
-- Name: TABLE sso_domains; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sso_domains IS 'Auth: Manages SSO email address domain mapping to an SSO Identity Provider.';


--
-- TOC entry 287 (class 1259 OID 16830)
-- Name: sso_providers; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.sso_providers (
    id uuid NOT NULL,
    resource_id text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    disabled boolean,
    CONSTRAINT "resource_id not empty" CHECK (((resource_id = NULL::text) OR (char_length(resource_id) > 0)))
);


--
-- TOC entry 5192 (class 0 OID 0)
-- Dependencies: 287
-- Name: TABLE sso_providers; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sso_providers IS 'Auth: Manages SSO identity provider information; see saml_providers for SAML.';


--
-- TOC entry 5193 (class 0 OID 0)
-- Dependencies: 287
-- Name: COLUMN sso_providers.resource_id; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sso_providers.resource_id IS 'Auth: Uniquely identifies a SSO provider according to a user-chosen resource ID (case insensitive), useful in infrastructure as code.';


--
-- TOC entry 270 (class 1259 OID 16493)
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
-- TOC entry 5194 (class 0 OID 0)
-- Dependencies: 270
-- Name: TABLE users; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.users IS 'Auth: Stores user login data within a secure schema.';


--
-- TOC entry 5195 (class 0 OID 0)
-- Dependencies: 270
-- Name: COLUMN users.is_sso_user; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.users.is_sso_user IS 'Auth: Set this column to true when the account comes from SSO. These accounts can have duplicate emails.';


--
-- TOC entry 302 (class 1259 OID 17333)
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
-- TOC entry 303 (class 1259 OID 17338)
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
-- TOC entry 5196 (class 0 OID 0)
-- Dependencies: 303
-- Name: action_reply_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.action_reply_id_seq OWNED BY public.action_reply.id;


--
-- TOC entry 304 (class 1259 OID 17339)
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
-- TOC entry 305 (class 1259 OID 17344)
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
-- TOC entry 5197 (class 0 OID 0)
-- Dependencies: 305
-- Name: actions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.actions_id_seq OWNED BY public.actions.id;


--
-- TOC entry 306 (class 1259 OID 17345)
-- Name: affiliations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.affiliations (
    id integer NOT NULL,
    owner_id integer NOT NULL,
    viewer_id integer NOT NULL,
    created_at double precision
);


--
-- TOC entry 307 (class 1259 OID 17348)
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
-- TOC entry 5198 (class 0 OID 0)
-- Dependencies: 307
-- Name: affiliations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.affiliations_id_seq OWNED BY public.affiliations.id;


--
-- TOC entry 308 (class 1259 OID 17349)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(64) NOT NULL
);


--
-- TOC entry 443 (class 1259 OID 37134)
-- Name: approval_branch_condition; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.approval_branch_condition (
    id character varying(50) NOT NULL,
    step_id integer NOT NULL,
    condition_order integer DEFAULT 0,
    operator character varying(50) NOT NULL,
    field_value character varying(255) NOT NULL,
    approver_id integer,
    approver_type character varying(50) DEFAULT 'user'::character varying,
    action character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_approver_type_valid CHECK (((approver_type)::text = ANY ((ARRAY['user'::character varying, 'next_level'::character varying, 'next_branch'::character varying])::text[]))),
    CONSTRAINT chk_condition_order_positive CHECK ((condition_order >= 0)),
    CONSTRAINT chk_operator_valid CHECK (((operator)::text = ANY ((ARRAY['equals'::character varying, 'not_equals'::character varying, 'contains'::character varying, 'not_contains'::character varying, 'greater_than'::character varying, 'less_than'::character varying, 'in'::character varying, 'not_in'::character varying, 'starts_with'::character varying, 'ends_with'::character varying, 'is_null'::character varying, 'is_not_null'::character varying])::text[])))
);


--
-- TOC entry 309 (class 1259 OID 17352)
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
-- TOC entry 5199 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN approval_instance.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.process_id IS '流程模板ID';


--
-- TOC entry 5200 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN approval_instance.object_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_id IS '对应单据ID';


--
-- TOC entry 5201 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN approval_instance.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.object_type IS '单据类型（如 project）';


--
-- TOC entry 5202 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN approval_instance.current_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.current_step IS '当前步骤序号';


--
-- TOC entry 5203 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN approval_instance.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.status IS '状态';


--
-- TOC entry 5204 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN approval_instance.started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.started_at IS '流程发起时间';


--
-- TOC entry 5205 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN approval_instance.ended_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.ended_at IS '审批完成时间';


--
-- TOC entry 5206 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN approval_instance.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.created_by IS '发起人ID';


--
-- TOC entry 5207 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN approval_instance.template_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_snapshot IS '创建时的模板快照';


--
-- TOC entry 5208 (class 0 OID 0)
-- Dependencies: 309
-- Name: COLUMN approval_instance.template_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_instance.template_version IS '模板版本号';


--
-- TOC entry 310 (class 1259 OID 17357)
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
-- TOC entry 5209 (class 0 OID 0)
-- Dependencies: 310
-- Name: approval_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_instance_id_seq OWNED BY public.approval_instance.id;


--
-- TOC entry 311 (class 1259 OID 17358)
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
-- TOC entry 5210 (class 0 OID 0)
-- Dependencies: 311
-- Name: COLUMN approval_process_template.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.name IS '流程名称';


--
-- TOC entry 5211 (class 0 OID 0)
-- Dependencies: 311
-- Name: COLUMN approval_process_template.object_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.object_type IS '适用对象（如 quotation）';


--
-- TOC entry 5212 (class 0 OID 0)
-- Dependencies: 311
-- Name: COLUMN approval_process_template.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.is_active IS '是否启用';


--
-- TOC entry 5213 (class 0 OID 0)
-- Dependencies: 311
-- Name: COLUMN approval_process_template.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_by IS '创建人账号ID';


--
-- TOC entry 5214 (class 0 OID 0)
-- Dependencies: 311
-- Name: COLUMN approval_process_template.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.created_at IS '创建时间';


--
-- TOC entry 5215 (class 0 OID 0)
-- Dependencies: 311
-- Name: COLUMN approval_process_template.required_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.required_fields IS '发起审批时必填字段列表';


--
-- TOC entry 5216 (class 0 OID 0)
-- Dependencies: 311
-- Name: COLUMN approval_process_template.lock_object_on_start; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_object_on_start IS '发起审批后是否锁定对象编辑';


--
-- TOC entry 5217 (class 0 OID 0)
-- Dependencies: 311
-- Name: COLUMN approval_process_template.lock_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_process_template.lock_reason IS '锁定原因说明';


--
-- TOC entry 312 (class 1259 OID 17366)
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
-- TOC entry 5218 (class 0 OID 0)
-- Dependencies: 312
-- Name: approval_process_template_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_process_template_id_seq OWNED BY public.approval_process_template.id;


--
-- TOC entry 313 (class 1259 OID 17367)
-- Name: approval_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.approval_record (
    id integer NOT NULL,
    instance_id integer NOT NULL,
    step_id integer,
    approver_id integer NOT NULL,
    action character varying(50) NOT NULL,
    comment text,
    "timestamp" timestamp without time zone
);


--
-- TOC entry 5219 (class 0 OID 0)
-- Dependencies: 313
-- Name: COLUMN approval_record.instance_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.instance_id IS '审批流程实例';


--
-- TOC entry 5220 (class 0 OID 0)
-- Dependencies: 313
-- Name: COLUMN approval_record.step_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.step_id IS '流程步骤ID';


--
-- TOC entry 5221 (class 0 OID 0)
-- Dependencies: 313
-- Name: COLUMN approval_record.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.approver_id IS '审批人ID';


--
-- TOC entry 5222 (class 0 OID 0)
-- Dependencies: 313
-- Name: COLUMN approval_record.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.action IS '同意/拒绝';


--
-- TOC entry 5223 (class 0 OID 0)
-- Dependencies: 313
-- Name: COLUMN approval_record.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record.comment IS '审批意见';


--
-- TOC entry 5224 (class 0 OID 0)
-- Dependencies: 313
-- Name: COLUMN approval_record."timestamp"; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_record."timestamp" IS '审批时间';


--
-- TOC entry 314 (class 1259 OID 17372)
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
-- TOC entry 5225 (class 0 OID 0)
-- Dependencies: 314
-- Name: approval_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_record_id_seq OWNED BY public.approval_record.id;


--
-- TOC entry 315 (class 1259 OID 17373)
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
    is_parallel boolean DEFAULT false,
    branch_condition json,
    merge_step_id integer,
    branch_level integer DEFAULT 0,
    parent_step_id integer,
    step_type character varying(20) DEFAULT 'normal'::character varying,
    branch_group_id character varying(50),
    branch_path character varying(100)
);


--
-- TOC entry 5226 (class 0 OID 0)
-- Dependencies: 315
-- Name: COLUMN approval_step.process_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.process_id IS '所属流程模板';


--
-- TOC entry 5227 (class 0 OID 0)
-- Dependencies: 315
-- Name: COLUMN approval_step.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_order IS '流程顺序';


--
-- TOC entry 5228 (class 0 OID 0)
-- Dependencies: 315
-- Name: COLUMN approval_step.approver_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.approver_user_id IS '审批人账号ID';


--
-- TOC entry 5229 (class 0 OID 0)
-- Dependencies: 315
-- Name: COLUMN approval_step.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.step_name IS '步骤说明（如"财务审批"）';


--
-- TOC entry 5230 (class 0 OID 0)
-- Dependencies: 315
-- Name: COLUMN approval_step.send_email; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.send_email IS '是否发送邮件通知';


--
-- TOC entry 5231 (class 0 OID 0)
-- Dependencies: 315
-- Name: COLUMN approval_step.action_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_type IS '步骤动作类型，如 authorization, quotation_approval';


--
-- TOC entry 5232 (class 0 OID 0)
-- Dependencies: 315
-- Name: COLUMN approval_step.action_params; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.action_params IS '动作参数，JSON格式';


--
-- TOC entry 5233 (class 0 OID 0)
-- Dependencies: 315
-- Name: COLUMN approval_step.editable_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.editable_fields IS '在此步骤可编辑的字段列表';


--
-- TOC entry 5234 (class 0 OID 0)
-- Dependencies: 315
-- Name: COLUMN approval_step.cc_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_users IS '邮件抄送用户ID列表';


--
-- TOC entry 5235 (class 0 OID 0)
-- Dependencies: 315
-- Name: COLUMN approval_step.cc_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_step.cc_enabled IS '是否启用邮件抄送';


--
-- TOC entry 316 (class 1259 OID 17382)
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
-- TOC entry 5236 (class 0 OID 0)
-- Dependencies: 316
-- Name: approval_step_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.approval_step_id_seq OWNED BY public.approval_step.id;


--
-- TOC entry 317 (class 1259 OID 17383)
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
    record_info character varying(255),
    description character varying(255),
    ip_address character varying(45),
    user_agent character varying(255)
);


--
-- TOC entry 318 (class 1259 OID 17388)
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
-- TOC entry 5237 (class 0 OID 0)
-- Dependencies: 318
-- Name: change_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.change_logs_id_seq OWNED BY public.change_logs.id;


--
-- TOC entry 319 (class 1259 OID 17389)
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
    shared_with_users json,
    share_contacts boolean,
    owner_id integer,
    share_enabled boolean NOT NULL,
    source character varying(20)
);


--
-- TOC entry 320 (class 1259 OID 17394)
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
-- TOC entry 5238 (class 0 OID 0)
-- Dependencies: 320
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- TOC entry 321 (class 1259 OID 17395)
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
-- TOC entry 5239 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN company_assets.asset_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.asset_type IS '资产类型: logo, seal, etc.';


--
-- TOC entry 5240 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN company_assets.asset_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.asset_name IS '资产名称';


--
-- TOC entry 5241 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN company_assets.asset_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.asset_key IS '资产唯一标识';


--
-- TOC entry 5242 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN company_assets.file_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_name IS '原始文件名';


--
-- TOC entry 5243 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN company_assets.file_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_type IS '文件类型: image/png, image/svg+xml, etc.';


--
-- TOC entry 5244 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN company_assets.file_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_size IS '文件大小(字节)';


--
-- TOC entry 5245 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN company_assets.file_content; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_content IS 'Base64编码的文件内容';


--
-- TOC entry 5246 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN company_assets.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.description IS '资产描述';


--
-- TOC entry 5247 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN company_assets.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.is_active IS '是否启用';


--
-- TOC entry 5248 (class 0 OID 0)
-- Dependencies: 321
-- Name: COLUMN company_assets.is_default; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.is_default IS '是否为默认资产';


--
-- TOC entry 322 (class 1259 OID 17400)
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
-- TOC entry 5249 (class 0 OID 0)
-- Dependencies: 322
-- Name: company_assets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.company_assets_id_seq OWNED BY public.company_assets.id;


--
-- TOC entry 323 (class 1259 OID 17401)
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
    override_share boolean,
    shared_disabled boolean,
    owner_id integer
);


--
-- TOC entry 324 (class 1259 OID 17406)
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
-- TOC entry 5250 (class 0 OID 0)
-- Dependencies: 324
-- Name: contacts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contacts_id_seq OWNED BY public.contacts.id;


--
-- TOC entry 442 (class 1259 OID 21084)
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
-- TOC entry 5251 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.field_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.field_name IS '字段名';


--
-- TOC entry 5252 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.display_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.display_name IS '显示名称';


--
-- TOC entry 5253 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.description IS '字段描述';


--
-- TOC entry 5254 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.data_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.data_type IS '数据类型';


--
-- TOC entry 5255 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.is_nullable; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_nullable IS '是否可为空';


--
-- TOC entry 5256 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.is_primary_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_primary_key IS '是否主键';


--
-- TOC entry 5257 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.is_foreign_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_foreign_key IS '是否外键';


--
-- TOC entry 5258 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.foreign_table; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.foreign_table IS '外键关联表';


--
-- TOC entry 5259 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.foreign_field; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.foreign_field IS '外键关联字段';


--
-- TOC entry 5260 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.is_numeric; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_numeric IS '是否数值字段';


--
-- TOC entry 5261 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.is_monetary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_monetary IS '是否金额字段';


--
-- TOC entry 5262 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.is_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_date IS '是否日期字段';


--
-- TOC entry 5263 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.is_aggregatable; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_aggregatable IS '是否可聚合统计';


--
-- TOC entry 5264 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.is_filterable; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_filterable IS '是否可过滤';


--
-- TOC entry 5265 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.is_performance_metric; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_performance_metric IS '是否绩效指标';


--
-- TOC entry 5266 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.performance_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.performance_category IS '绩效分类：sales/customer/project/quality';


--
-- TOC entry 5267 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.calculation_priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.calculation_priority IS '计算优先级';


--
-- TOC entry 5268 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.display_format; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.display_format IS '显示格式';


--
-- TOC entry 5269 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.default_unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.default_unit IS '默认单位';


--
-- TOC entry 5270 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.decimal_places; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.decimal_places IS '小数位数';


--
-- TOC entry 5271 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.sample_values; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.sample_values IS '样本值JSON';


--
-- TOC entry 5272 (class 0 OID 0)
-- Dependencies: 442
-- Name: COLUMN data_field_config.value_range; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.value_range IS '值范围JSON';


--
-- TOC entry 441 (class 1259 OID 21083)
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
-- TOC entry 5273 (class 0 OID 0)
-- Dependencies: 441
-- Name: data_field_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_field_config_id_seq OWNED BY public.data_field_config.id;


--
-- TOC entry 438 (class 1259 OID 21049)
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
-- TOC entry 5274 (class 0 OID 0)
-- Dependencies: 438
-- Name: COLUMN data_table_config.table_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.table_name IS '数据表名';


--
-- TOC entry 5275 (class 0 OID 0)
-- Dependencies: 438
-- Name: COLUMN data_table_config.display_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.display_name IS '显示名称';


--
-- TOC entry 5276 (class 0 OID 0)
-- Dependencies: 438
-- Name: COLUMN data_table_config.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.description IS '表描述';


--
-- TOC entry 5277 (class 0 OID 0)
-- Dependencies: 438
-- Name: COLUMN data_table_config.category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.category IS '表分类：business/system/reference';


--
-- TOC entry 5278 (class 0 OID 0)
-- Dependencies: 438
-- Name: COLUMN data_table_config.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.is_active IS '是否启用';


--
-- TOC entry 5279 (class 0 OID 0)
-- Dependencies: 438
-- Name: COLUMN data_table_config.is_performance_source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.is_performance_source IS '是否可用作绩效数据源';


--
-- TOC entry 5280 (class 0 OID 0)
-- Dependencies: 438
-- Name: COLUMN data_table_config.total_records; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.total_records IS '记录总数';


--
-- TOC entry 5281 (class 0 OID 0)
-- Dependencies: 438
-- Name: COLUMN data_table_config.last_updated; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.last_updated IS '数据最后更新时间';


--
-- TOC entry 437 (class 1259 OID 21048)
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
-- TOC entry 5282 (class 0 OID 0)
-- Dependencies: 437
-- Name: data_table_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_table_config_id_seq OWNED BY public.data_table_config.id;


--
-- TOC entry 325 (class 1259 OID 17407)
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
-- TOC entry 326 (class 1259 OID 17410)
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
-- TOC entry 5283 (class 0 OID 0)
-- Dependencies: 326
-- Name: departments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.departments_id_seq OWNED BY public.departments.id;


--
-- TOC entry 446 (class 1259 OID 62667)
-- Name: dev_product_milestones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_product_milestones (
    id integer NOT NULL,
    product_id integer NOT NULL,
    stage_key character varying(50) NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    planned_start_date timestamp without time zone,
    planned_end_date timestamp without time zone,
    actual_start_date timestamp without time zone,
    actual_end_date timestamp without time zone,
    status character varying(50),
    progress integer,
    priority integer,
    order_index integer,
    created_by integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- TOC entry 445 (class 1259 OID 62666)
-- Name: dev_product_milestones_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_product_milestones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5284 (class 0 OID 0)
-- Dependencies: 445
-- Name: dev_product_milestones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_product_milestones_id_seq OWNED BY public.dev_product_milestones.id;


--
-- TOC entry 327 (class 1259 OID 17411)
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
-- TOC entry 328 (class 1259 OID 17414)
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
-- TOC entry 5285 (class 0 OID 0)
-- Dependencies: 328
-- Name: dev_product_specs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_product_specs_id_seq OWNED BY public.dev_product_specs.id;


--
-- TOC entry 329 (class 1259 OID 17415)
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
    pdf_path character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    owner_id integer,
    created_by integer,
    mn_code character varying(20),
    currency character varying(3) DEFAULT 'CNY'::character varying NOT NULL,
    planned_duration_days integer,
    actual_duration_days integer,
    risk_level character varying(20) DEFAULT 'medium'::character varying,
    baseline_date timestamp without time zone,
    milestone_count integer DEFAULT 0,
    stage_history json,
    stage_description text,
    stage_records json
);


--
-- TOC entry 330 (class 1259 OID 17421)
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
-- TOC entry 5286 (class 0 OID 0)
-- Dependencies: 330
-- Name: dev_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_products_id_seq OWNED BY public.dev_products.id;


--
-- TOC entry 331 (class 1259 OID 17422)
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
    address text,
    postal_code character varying(20),
    phone character varying(50),
    fax character varying(50),
    email character varying(255),
    website character varying(255),
    logo_content text,
    logo_filename character varying(255),
    logo_type character varying(50),
    logo_size integer,
    email_signature_content text,
    email_signature_filename character varying(255),
    email_signature_type character varying(50),
    email_signature_size integer
);


--
-- TOC entry 5287 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.address; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.address IS '地址';


--
-- TOC entry 5288 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.postal_code; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.postal_code IS '邮政编码';


--
-- TOC entry 5289 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.phone; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.phone IS '电话';


--
-- TOC entry 5290 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.fax; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.fax IS '传真';


--
-- TOC entry 5291 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.email; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.email IS '邮箱';


--
-- TOC entry 5292 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.website; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.website IS '网站';


--
-- TOC entry 5293 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.logo_content; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.logo_content IS 'Logo内容';


--
-- TOC entry 5294 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.logo_filename; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.logo_filename IS 'Logo文件名';


--
-- TOC entry 5295 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.logo_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.logo_type IS 'Logo类型';


--
-- TOC entry 5296 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.logo_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.logo_size IS 'Logo大小';


--
-- TOC entry 5297 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.email_signature_content; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.email_signature_content IS '邮件签名内容';


--
-- TOC entry 5298 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.email_signature_filename; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.email_signature_filename IS '邮件签名文件名';


--
-- TOC entry 5299 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.email_signature_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.email_signature_type IS '邮件签名类型';


--
-- TOC entry 5300 (class 0 OID 0)
-- Dependencies: 331
-- Name: COLUMN dictionaries.email_signature_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.dictionaries.email_signature_size IS '邮件签名大小';


--
-- TOC entry 332 (class 1259 OID 17428)
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
-- TOC entry 5301 (class 0 OID 0)
-- Dependencies: 332
-- Name: dictionaries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dictionaries_id_seq OWNED BY public.dictionaries.id;


--
-- TOC entry 333 (class 1259 OID 17429)
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
-- TOC entry 5302 (class 0 OID 0)
-- Dependencies: 333
-- Name: COLUMN event_registry.event_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.event_key IS '事件唯一键';


--
-- TOC entry 5303 (class 0 OID 0)
-- Dependencies: 333
-- Name: COLUMN event_registry.label_zh; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.label_zh IS '中文名称';


--
-- TOC entry 5304 (class 0 OID 0)
-- Dependencies: 333
-- Name: COLUMN event_registry.label_en; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.label_en IS '英文名称';


--
-- TOC entry 5305 (class 0 OID 0)
-- Dependencies: 333
-- Name: COLUMN event_registry.default_enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.default_enabled IS '是否默认开启';


--
-- TOC entry 5306 (class 0 OID 0)
-- Dependencies: 333
-- Name: COLUMN event_registry.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.event_registry.enabled IS '是否在通知中心展示';


--
-- TOC entry 334 (class 1259 OID 17432)
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
-- TOC entry 5307 (class 0 OID 0)
-- Dependencies: 334
-- Name: event_registry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.event_registry_id_seq OWNED BY public.event_registry.id;


--
-- TOC entry 335 (class 1259 OID 17433)
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
-- TOC entry 336 (class 1259 OID 17442)
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
-- TOC entry 5308 (class 0 OID 0)
-- Dependencies: 336
-- Name: expense_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expense_details_id_seq OWNED BY public.expense_details.id;


--
-- TOC entry 337 (class 1259 OID 17443)
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
-- TOC entry 338 (class 1259 OID 17450)
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
-- TOC entry 5309 (class 0 OID 0)
-- Dependencies: 338
-- Name: expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expenses_id_seq OWNED BY public.expenses.id;


--
-- TOC entry 339 (class 1259 OID 17451)
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
-- TOC entry 5310 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.version_id IS '版本ID';


--
-- TOC entry 5311 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.change_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.change_type IS '变更类型：feature/fix/improvement/security';


--
-- TOC entry 5312 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.module_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.module_name IS '模块名称';


--
-- TOC entry 5313 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.title; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.title IS '变更标题';


--
-- TOC entry 5314 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.description IS '详细描述';


--
-- TOC entry 5315 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.priority IS '优先级：low/medium/high/critical';


--
-- TOC entry 5316 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.impact_level; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.impact_level IS '影响级别：minor/major/breaking';


--
-- TOC entry 5317 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.affected_files; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.affected_files IS '影响的文件列表（JSON格式）';


--
-- TOC entry 5318 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.git_commits; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.git_commits IS '相关Git提交（JSON格式）';


--
-- TOC entry 5319 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.test_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.test_status IS '测试状态：pending/passed/failed';


--
-- TOC entry 5320 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.test_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.test_notes IS '测试说明';


--
-- TOC entry 5321 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.developer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.developer_id IS '开发人员ID';


--
-- TOC entry 5322 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.developer_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.developer_name IS '开发人员姓名';


--
-- TOC entry 5323 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.created_at IS '创建时间';


--
-- TOC entry 5324 (class 0 OID 0)
-- Dependencies: 339
-- Name: COLUMN feature_changes.completed_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.feature_changes.completed_at IS '完成时间';


--
-- TOC entry 340 (class 1259 OID 17456)
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
-- TOC entry 5325 (class 0 OID 0)
-- Dependencies: 340
-- Name: feature_changes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.feature_changes_id_seq OWNED BY public.feature_changes.id;


--
-- TOC entry 341 (class 1259 OID 17457)
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
-- TOC entry 5326 (class 0 OID 0)
-- Dependencies: 341
-- Name: COLUMN five_star_project_baselines.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.five_star_project_baselines.user_id IS '用户ID';


--
-- TOC entry 5327 (class 0 OID 0)
-- Dependencies: 341
-- Name: COLUMN five_star_project_baselines.baseline_year; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.five_star_project_baselines.baseline_year IS '基线年份';


--
-- TOC entry 5328 (class 0 OID 0)
-- Dependencies: 341
-- Name: COLUMN five_star_project_baselines.baseline_month; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.five_star_project_baselines.baseline_month IS '基线月份';


--
-- TOC entry 5329 (class 0 OID 0)
-- Dependencies: 341
-- Name: COLUMN five_star_project_baselines.baseline_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.five_star_project_baselines.baseline_count IS '基线五星项目数量';


--
-- TOC entry 5330 (class 0 OID 0)
-- Dependencies: 341
-- Name: COLUMN five_star_project_baselines.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.five_star_project_baselines.created_at IS '创建时间';


--
-- TOC entry 342 (class 1259 OID 17460)
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
-- TOC entry 5331 (class 0 OID 0)
-- Dependencies: 342
-- Name: five_star_project_baselines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.five_star_project_baselines_id_seq OWNED BY public.five_star_project_baselines.id;


--
-- TOC entry 440 (class 1259 OID 21070)
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
-- TOC entry 5332 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.template_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.template_name IS '模板名称';


--
-- TOC entry 5333 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.template_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.template_category IS '模板分类';


--
-- TOC entry 5334 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.description IS '模板描述';


--
-- TOC entry 5335 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.formula_expression; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.formula_expression IS '公式表达式';


--
-- TOC entry 5336 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.required_tables; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.required_tables IS '需要的数据表JSON';


--
-- TOC entry 5337 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.required_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.required_fields IS '需要的字段JSON';


--
-- TOC entry 5338 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.result_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.result_type IS '结果类型：numeric/percentage/count';


--
-- TOC entry 5339 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.result_unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.result_unit IS '结果单位';


--
-- TOC entry 5340 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.is_system_template; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.is_system_template IS '是否系统模板';


--
-- TOC entry 5341 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.is_active IS '是否启用';


--
-- TOC entry 5342 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.usage_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.usage_count IS '使用次数';


--
-- TOC entry 5343 (class 0 OID 0)
-- Dependencies: 440
-- Name: COLUMN formula_templates_extended.last_used_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.last_used_at IS '最后使用时间';


--
-- TOC entry 439 (class 1259 OID 21069)
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
-- TOC entry 5344 (class 0 OID 0)
-- Dependencies: 439
-- Name: formula_templates_extended_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.formula_templates_extended_id_seq OWNED BY public.formula_templates_extended.id;


--
-- TOC entry 343 (class 1259 OID 17461)
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
-- TOC entry 344 (class 1259 OID 17466)
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
-- TOC entry 5345 (class 0 OID 0)
-- Dependencies: 344
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- TOC entry 345 (class 1259 OID 17467)
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
-- TOC entry 346 (class 1259 OID 17472)
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
-- TOC entry 5346 (class 0 OID 0)
-- Dependencies: 346
-- Name: inventory_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_transactions_id_seq OWNED BY public.inventory_transactions.id;


--
-- TOC entry 432 (class 1259 OID 19899)
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
-- TOC entry 431 (class 1259 OID 19898)
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
-- TOC entry 5347 (class 0 OID 0)
-- Dependencies: 431
-- Name: performance_formula_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_formula_templates_id_seq OWNED BY public.performance_formula_templates.id;


--
-- TOC entry 428 (class 1259 OID 19869)
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
-- TOC entry 427 (class 1259 OID 19868)
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
-- TOC entry 5348 (class 0 OID 0)
-- Dependencies: 427
-- Name: performance_metrics_definition_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_metrics_definition_id_seq OWNED BY public.performance_metrics_definition.id;


--
-- TOC entry 347 (class 1259 OID 17473)
-- Name: performance_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performance_statistics (
    id integer NOT NULL,
    user_id integer NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    implant_amount_actual numeric(15,2),
    sales_amount_actual numeric(15,2),
    new_customers_actual integer,
    new_projects_actual integer,
    five_star_projects_actual integer,
    industry_statistics json,
    calculated_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- TOC entry 5349 (class 0 OID 0)
-- Dependencies: 347
-- Name: COLUMN performance_statistics.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.user_id IS '用户ID';


--
-- TOC entry 5350 (class 0 OID 0)
-- Dependencies: 347
-- Name: COLUMN performance_statistics.year; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.year IS '年份';


--
-- TOC entry 5351 (class 0 OID 0)
-- Dependencies: 347
-- Name: COLUMN performance_statistics.month; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.month IS '月份';


--
-- TOC entry 5352 (class 0 OID 0)
-- Dependencies: 347
-- Name: COLUMN performance_statistics.implant_amount_actual; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.implant_amount_actual IS '植入额实际完成';


--
-- TOC entry 5353 (class 0 OID 0)
-- Dependencies: 347
-- Name: COLUMN performance_statistics.sales_amount_actual; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.sales_amount_actual IS '销售额实际完成';


--
-- TOC entry 5354 (class 0 OID 0)
-- Dependencies: 347
-- Name: COLUMN performance_statistics.new_customers_actual; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.new_customers_actual IS '新增客户数实际完成';


--
-- TOC entry 5355 (class 0 OID 0)
-- Dependencies: 347
-- Name: COLUMN performance_statistics.new_projects_actual; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.new_projects_actual IS '新增项目数实际完成';


--
-- TOC entry 5356 (class 0 OID 0)
-- Dependencies: 347
-- Name: COLUMN performance_statistics.five_star_projects_actual; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.five_star_projects_actual IS '五星项目增量实际完成';


--
-- TOC entry 5357 (class 0 OID 0)
-- Dependencies: 347
-- Name: COLUMN performance_statistics.industry_statistics; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.industry_statistics IS '行业维度统计数据';


--
-- TOC entry 5358 (class 0 OID 0)
-- Dependencies: 347
-- Name: COLUMN performance_statistics.calculated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_statistics.calculated_at IS '统计计算时间';


--
-- TOC entry 348 (class 1259 OID 17480)
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
-- TOC entry 5359 (class 0 OID 0)
-- Dependencies: 348
-- Name: performance_statistics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_statistics_id_seq OWNED BY public.performance_statistics.id;


--
-- TOC entry 349 (class 1259 OID 17481)
-- Name: performance_targets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performance_targets (
    id integer NOT NULL,
    user_id integer NOT NULL,
    year integer NOT NULL,
    month integer NOT NULL,
    implant_amount_target numeric(15,2),
    sales_amount_target numeric(15,2),
    new_customers_target integer,
    new_projects_target integer,
    five_star_projects_target integer,
    display_currency character varying(10),
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    updated_by integer,
    implant_rate integer DEFAULT 0,
    sales_rate integer DEFAULT 0,
    customers_rate integer DEFAULT 0,
    projects_rate integer DEFAULT 0
);


--
-- TOC entry 5360 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.user_id IS '用户ID';


--
-- TOC entry 5361 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.year; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.year IS '年份';


--
-- TOC entry 5362 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.month; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.month IS '月份';


--
-- TOC entry 5363 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.implant_amount_target; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.implant_amount_target IS '植入额目标';


--
-- TOC entry 5364 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.sales_amount_target; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.sales_amount_target IS '销售额目标';


--
-- TOC entry 5365 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.new_customers_target; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.new_customers_target IS '新增客户数目标';


--
-- TOC entry 5366 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.new_projects_target; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.new_projects_target IS '新增项目数目标';


--
-- TOC entry 5367 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.five_star_projects_target; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.five_star_projects_target IS '五星项目增量目标';


--
-- TOC entry 5368 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.display_currency; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.display_currency IS '用户选择的展示货币';


--
-- TOC entry 5369 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.created_by IS '创建人';


--
-- TOC entry 5370 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.created_at IS '创建时间';


--
-- TOC entry 5371 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.updated_at IS '更新时间';


--
-- TOC entry 5372 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.implant_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.implant_rate IS '植入合格值';


--
-- TOC entry 5373 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.sales_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.sales_rate IS '销售合格值';


--
-- TOC entry 5374 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.customers_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.customers_rate IS '客户合格值';


--
-- TOC entry 5375 (class 0 OID 0)
-- Dependencies: 349
-- Name: COLUMN performance_targets.projects_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.performance_targets.projects_rate IS '项目合格值';


--
-- TOC entry 350 (class 1259 OID 17484)
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
-- TOC entry 5376 (class 0 OID 0)
-- Dependencies: 350
-- Name: performance_targets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_targets_id_seq OWNED BY public.performance_targets.id;


--
-- TOC entry 351 (class 1259 OID 17485)
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
    can_change_owner boolean DEFAULT false,
    content_filters json
);


--
-- TOC entry 352 (class 1259 OID 17491)
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
-- TOC entry 5377 (class 0 OID 0)
-- Dependencies: 352
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- TOC entry 353 (class 1259 OID 17492)
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
-- TOC entry 5378 (class 0 OID 0)
-- Dependencies: 353
-- Name: COLUMN pricing_order_approval_records.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.pricing_order_id IS '批价单ID';


--
-- TOC entry 5379 (class 0 OID 0)
-- Dependencies: 353
-- Name: COLUMN pricing_order_approval_records.step_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_order IS '审批步骤顺序';


--
-- TOC entry 5380 (class 0 OID 0)
-- Dependencies: 353
-- Name: COLUMN pricing_order_approval_records.step_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.step_name IS '审批步骤名称';


--
-- TOC entry 5381 (class 0 OID 0)
-- Dependencies: 353
-- Name: COLUMN pricing_order_approval_records.approver_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_role IS '审批人角色';


--
-- TOC entry 5382 (class 0 OID 0)
-- Dependencies: 353
-- Name: COLUMN pricing_order_approval_records.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approver_id IS '审批人ID';


--
-- TOC entry 5383 (class 0 OID 0)
-- Dependencies: 353
-- Name: COLUMN pricing_order_approval_records.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.action IS '审批动作：approve/reject';


--
-- TOC entry 5384 (class 0 OID 0)
-- Dependencies: 353
-- Name: COLUMN pricing_order_approval_records.comment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.comment IS '审批意见';


--
-- TOC entry 5385 (class 0 OID 0)
-- Dependencies: 353
-- Name: COLUMN pricing_order_approval_records.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.approved_at IS '审批时间';


--
-- TOC entry 5386 (class 0 OID 0)
-- Dependencies: 353
-- Name: COLUMN pricing_order_approval_records.is_fast_approval; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.is_fast_approval IS '是否快速通过';


--
-- TOC entry 5387 (class 0 OID 0)
-- Dependencies: 353
-- Name: COLUMN pricing_order_approval_records.fast_approval_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_approval_records.fast_approval_reason IS '快速通过原因';


--
-- TOC entry 354 (class 1259 OID 17497)
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
-- TOC entry 5388 (class 0 OID 0)
-- Dependencies: 354
-- Name: pricing_order_approval_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_order_approval_records_id_seq OWNED BY public.pricing_order_approval_records.id;


--
-- TOC entry 355 (class 1259 OID 17498)
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
-- TOC entry 5389 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.pricing_order_id IS '批价单ID';


--
-- TOC entry 5390 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_name IS '产品名称';


--
-- TOC entry 5391 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_model IS '产品型号';


--
-- TOC entry 5392 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_desc IS '产品描述';


--
-- TOC entry 5393 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.brand IS '品牌';


--
-- TOC entry 5394 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.unit IS '单位';


--
-- TOC entry 5395 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.product_mn IS '产品MN编码';


--
-- TOC entry 5396 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.market_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.market_price IS '市场价';


--
-- TOC entry 5397 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.unit_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.unit_price IS '单价';


--
-- TOC entry 5398 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.quantity IS '数量';


--
-- TOC entry 5399 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.discount_rate IS '折扣率';


--
-- TOC entry 5400 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.total_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.total_price IS '小计金额';


--
-- TOC entry 5401 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.source_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.source_type IS '数据来源：quotation/manual';


--
-- TOC entry 5402 (class 0 OID 0)
-- Dependencies: 355
-- Name: COLUMN pricing_order_details.source_quotation_detail_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_order_details.source_quotation_detail_id IS '来源报价单明细ID';


--
-- TOC entry 356 (class 1259 OID 17504)
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
-- TOC entry 5403 (class 0 OID 0)
-- Dependencies: 356
-- Name: pricing_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_order_details_id_seq OWNED BY public.pricing_order_details.id;


--
-- TOC entry 357 (class 1259 OID 17505)
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
    updated_at timestamp without time zone,
    currency character varying(10) DEFAULT 'CNY'::character varying
);


--
-- TOC entry 5404 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.order_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.order_number IS '批价单号';


--
-- TOC entry 5405 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.project_id IS '项目ID';


--
-- TOC entry 5406 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.quotation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.quotation_id IS '报价单ID';


--
-- TOC entry 5407 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.dealer_id IS '经销商ID';


--
-- TOC entry 5408 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.distributor_id IS '分销商ID';


--
-- TOC entry 5409 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.is_direct_contract; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.is_direct_contract IS '厂商直签';


--
-- TOC entry 5410 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.is_factory_pickup; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.is_factory_pickup IS '厂家提货';


--
-- TOC entry 5411 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.approval_flow_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approval_flow_type IS '审批流程类型';


--
-- TOC entry 5412 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.status IS '批价单状态';


--
-- TOC entry 5413 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.current_approval_step; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.current_approval_step IS '当前审批步骤';


--
-- TOC entry 5414 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.pricing_total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_amount IS '批价单总金额';


--
-- TOC entry 5415 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.pricing_total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.pricing_total_discount_rate IS '批价单总折扣率';


--
-- TOC entry 5416 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.settlement_total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_amount IS '结算单总金额';


--
-- TOC entry 5417 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.settlement_total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.settlement_total_discount_rate IS '结算单总折扣率';


--
-- TOC entry 5418 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.approved_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approved_by IS '最终批准人';


--
-- TOC entry 5419 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.approved_at IS '批准时间';


--
-- TOC entry 5420 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.created_by IS '创建人';


--
-- TOC entry 5421 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.created_at IS '创建时间';


--
-- TOC entry 5422 (class 0 OID 0)
-- Dependencies: 357
-- Name: COLUMN pricing_orders.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.updated_at IS '更新时间';


--
-- TOC entry 358 (class 1259 OID 17511)
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
-- TOC entry 5423 (class 0 OID 0)
-- Dependencies: 358
-- Name: pricing_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pricing_orders_id_seq OWNED BY public.pricing_orders.id;


--
-- TOC entry 359 (class 1259 OID 17512)
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
-- TOC entry 360 (class 1259 OID 17517)
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
-- TOC entry 5424 (class 0 OID 0)
-- Dependencies: 360
-- Name: product_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_categories_id_seq OWNED BY public.product_categories.id;


--
-- TOC entry 361 (class 1259 OID 17518)
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
-- TOC entry 362 (class 1259 OID 17523)
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
-- TOC entry 5425 (class 0 OID 0)
-- Dependencies: 362
-- Name: product_code_field_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_field_options_id_seq OWNED BY public.product_code_field_options.id;


--
-- TOC entry 363 (class 1259 OID 17524)
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
-- TOC entry 364 (class 1259 OID 17527)
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
-- TOC entry 5426 (class 0 OID 0)
-- Dependencies: 364
-- Name: product_code_field_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_field_values_id_seq OWNED BY public.product_code_field_values.id;


--
-- TOC entry 365 (class 1259 OID 17528)
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
-- TOC entry 366 (class 1259 OID 17533)
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
-- TOC entry 5427 (class 0 OID 0)
-- Dependencies: 366
-- Name: product_code_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_code_fields_id_seq OWNED BY public.product_code_fields.id;


--
-- TOC entry 367 (class 1259 OID 17534)
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
-- TOC entry 368 (class 1259 OID 17537)
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
-- TOC entry 5428 (class 0 OID 0)
-- Dependencies: 368
-- Name: product_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_codes_id_seq OWNED BY public.product_codes.id;


--
-- TOC entry 369 (class 1259 OID 17538)
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
-- TOC entry 370 (class 1259 OID 17543)
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
-- TOC entry 5429 (class 0 OID 0)
-- Dependencies: 370
-- Name: product_regions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_regions_id_seq OWNED BY public.product_regions.id;


--
-- TOC entry 371 (class 1259 OID 17544)
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
-- TOC entry 372 (class 1259 OID 17549)
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
-- TOC entry 5430 (class 0 OID 0)
-- Dependencies: 372
-- Name: product_subcategories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_subcategories_id_seq OWNED BY public.product_subcategories.id;


--
-- TOC entry 373 (class 1259 OID 17550)
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
    pdf_path character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    owner_id integer,
    currency character varying(3) DEFAULT 'CNY'::character varying NOT NULL,
    is_vendor_product boolean DEFAULT false
);


--
-- TOC entry 374 (class 1259 OID 17557)
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
-- TOC entry 5431 (class 0 OID 0)
-- Dependencies: 374
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- TOC entry 375 (class 1259 OID 17558)
-- Name: project_customer_associations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_customer_associations (
    id integer NOT NULL,
    project_id integer NOT NULL,
    company_id integer NOT NULL,
    customer_type character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by integer
);


--
-- TOC entry 5432 (class 0 OID 0)
-- Dependencies: 375
-- Name: TABLE project_customer_associations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.project_customer_associations IS '项目客户关联表';


--
-- TOC entry 5433 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN project_customer_associations.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.id IS '主键ID';


--
-- TOC entry 5434 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN project_customer_associations.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.project_id IS '关联的项目ID';


--
-- TOC entry 5435 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN project_customer_associations.company_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.company_id IS '关联的公司ID';


--
-- TOC entry 5436 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN project_customer_associations.customer_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.customer_type IS '客户类型（end_user等）';


--
-- TOC entry 5437 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN project_customer_associations.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.created_at IS '创建时间';


--
-- TOC entry 5438 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN project_customer_associations.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.updated_at IS '更新时间';


--
-- TOC entry 5439 (class 0 OID 0)
-- Dependencies: 375
-- Name: COLUMN project_customer_associations.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.created_by IS '创建者用户ID';


--
-- TOC entry 376 (class 1259 OID 17563)
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
-- TOC entry 5440 (class 0 OID 0)
-- Dependencies: 376
-- Name: project_customer_associations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_customer_associations_id_seq OWNED BY public.project_customer_associations.id;


--
-- TOC entry 377 (class 1259 OID 17564)
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
-- TOC entry 378 (class 1259 OID 17567)
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
-- TOC entry 5441 (class 0 OID 0)
-- Dependencies: 378
-- Name: project_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_members_id_seq OWNED BY public.project_members.id;


--
-- TOC entry 379 (class 1259 OID 17568)
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
-- TOC entry 380 (class 1259 OID 17572)
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
-- TOC entry 5442 (class 0 OID 0)
-- Dependencies: 380
-- Name: project_rating_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_rating_records_id_seq OWNED BY public.project_rating_records.id;


--
-- TOC entry 381 (class 1259 OID 17573)
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
-- TOC entry 382 (class 1259 OID 17582)
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
-- TOC entry 5443 (class 0 OID 0)
-- Dependencies: 382
-- Name: project_scoring_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_scoring_config_id_seq OWNED BY public.project_scoring_config.id;


--
-- TOC entry 383 (class 1259 OID 17583)
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
-- TOC entry 384 (class 1259 OID 17592)
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
-- TOC entry 5444 (class 0 OID 0)
-- Dependencies: 384
-- Name: project_scoring_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_scoring_records_id_seq OWNED BY public.project_scoring_records.id;


--
-- TOC entry 385 (class 1259 OID 17593)
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
-- TOC entry 386 (class 1259 OID 17599)
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
-- TOC entry 5445 (class 0 OID 0)
-- Dependencies: 386
-- Name: project_stage_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_stage_history_id_seq OWNED BY public.project_stage_history.id;


--
-- TOC entry 387 (class 1259 OID 17600)
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
-- TOC entry 388 (class 1259 OID 17612)
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
-- TOC entry 5446 (class 0 OID 0)
-- Dependencies: 388
-- Name: project_total_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_total_scores_id_seq OWNED BY public.project_total_scores.id;


--
-- TOC entry 389 (class 1259 OID 17613)
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
    is_locked boolean DEFAULT false NOT NULL,
    locked_reason character varying(100),
    locked_by integer,
    locked_at timestamp without time zone,
    is_active boolean DEFAULT true NOT NULL,
    last_activity_date timestamp without time zone DEFAULT now(),
    activity_reason character varying(50),
    vendor_sales_manager_id integer,
    rating integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    owner_id integer,
    industry character varying(50),
    shared_with_users jsonb,
    share_enabled boolean NOT NULL,
    status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    created_by integer NOT NULL
);


--
-- TOC entry 5447 (class 0 OID 0)
-- Dependencies: 389
-- Name: COLUMN projects.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.projects.created_by IS '项目发起人/报备人（不可变）';


--
-- TOC entry 390 (class 1259 OID 17623)
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
-- TOC entry 5448 (class 0 OID 0)
-- Dependencies: 390
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- TOC entry 391 (class 1259 OID 17624)
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
-- TOC entry 392 (class 1259 OID 17629)
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
-- TOC entry 5449 (class 0 OID 0)
-- Dependencies: 392
-- Name: purchase_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_order_details_id_seq OWNED BY public.purchase_order_details.id;


--
-- TOC entry 393 (class 1259 OID 17630)
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
    approval_status character varying(20),
    approval_submitted_at timestamp without time zone,
    approval_completed_at timestamp without time zone,
    created_by_id integer NOT NULL,
    approved_by_id integer,
    approved_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- TOC entry 394 (class 1259 OID 17635)
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
-- TOC entry 5450 (class 0 OID 0)
-- Dependencies: 394
-- Name: purchase_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_orders_id_seq OWNED BY public.purchase_orders.id;


--
-- TOC entry 395 (class 1259 OID 17636)
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
    implant_subtotal double precision DEFAULT 0.00,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    converted_market_price double precision,
    currency character varying(3),
    original_market_price double precision
);


--
-- TOC entry 396 (class 1259 OID 17642)
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
-- TOC entry 5451 (class 0 OID 0)
-- Dependencies: 396
-- Name: quotation_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotation_details_id_seq OWNED BY public.quotation_details.id;


--
-- TOC entry 397 (class 1259 OID 17643)
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
    approval_status character varying(50) DEFAULT 'pending'::character varying,
    approved_stages json DEFAULT '[]'::json,
    approval_history json DEFAULT '[]'::json,
    confirmation_badge_status character varying(20) DEFAULT 'none'::character varying,
    confirmation_badge_color character varying(20) DEFAULT NULL::character varying,
    confirmed_by integer,
    confirmed_at timestamp without time zone,
    product_signature character varying(64) DEFAULT NULL::character varying,
    is_locked boolean DEFAULT false,
    lock_reason character varying(200),
    locked_by integer,
    locked_at timestamp without time zone,
    implant_total_amount double precision DEFAULT 0.00,
    created_at timestamp with time zone,
    updated_at timestamp without time zone,
    owner_id integer,
    currency character varying(3) DEFAULT 'CNY'::character varying NOT NULL,
    exchange_rate numeric(10,6) DEFAULT 1.000000 NOT NULL,
    original_currency character varying(3),
    customer_id integer
);


--
-- TOC entry 455 (class 1259 OID 108311)
-- Name: quotations_customer_backup_20251025_214040; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quotations_customer_backup_20251025_214040 (
    id integer,
    quotation_number character varying(20),
    customer_id integer,
    project_id integer,
    contact_id integer,
    created_at timestamp with time zone,
    updated_at timestamp without time zone
);


--
-- TOC entry 456 (class 1259 OID 108314)
-- Name: quotations_customer_backup_20251025_214155; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quotations_customer_backup_20251025_214155 (
    id integer,
    quotation_number character varying(20),
    customer_id integer,
    project_id integer,
    contact_id integer,
    created_at timestamp with time zone,
    updated_at timestamp without time zone
);


--
-- TOC entry 398 (class 1259 OID 17658)
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
-- TOC entry 5452 (class 0 OID 0)
-- Dependencies: 398
-- Name: quotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quotations_id_seq OWNED BY public.quotations.id;


--
-- TOC entry 434 (class 1259 OID 19908)
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
-- TOC entry 433 (class 1259 OID 19907)
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
-- TOC entry 5453 (class 0 OID 0)
-- Dependencies: 433
-- Name: role_performance_access_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_performance_access_id_seq OWNED BY public.role_performance_access.id;


--
-- TOC entry 430 (class 1259 OID 19879)
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
-- TOC entry 429 (class 1259 OID 19878)
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
-- TOC entry 5454 (class 0 OID 0)
-- Dependencies: 429
-- Name: role_performance_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_performance_config_id_seq OWNED BY public.role_performance_config.id;


--
-- TOC entry 436 (class 1259 OID 19921)
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
-- TOC entry 435 (class 1259 OID 19920)
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
-- TOC entry 5455 (class 0 OID 0)
-- Dependencies: 435
-- Name: role_performance_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_performance_items_id_seq OWNED BY public.role_performance_items.id;


--
-- TOC entry 399 (class 1259 OID 17659)
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
    permission_level character varying(20) DEFAULT 'personal'::character varying,
    permission_level_description text,
    can_change_owner boolean DEFAULT false,
    content_filters json
);


--
-- TOC entry 400 (class 1259 OID 17665)
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
-- TOC entry 5456 (class 0 OID 0)
-- Dependencies: 400
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- TOC entry 401 (class 1259 OID 17666)
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
-- TOC entry 402 (class 1259 OID 17671)
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
-- TOC entry 5457 (class 0 OID 0)
-- Dependencies: 402
-- Name: settlement_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_details_id_seq OWNED BY public.settlement_details.id;


--
-- TOC entry 403 (class 1259 OID 17672)
-- Name: settlement_order_details; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.settlement_order_details (
    id integer NOT NULL,
    pricing_order_id integer NOT NULL,
    settlement_order_id integer,
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
    settlement_company_id integer,
    settlement_status character varying(20),
    settlement_date timestamp without time zone,
    settlement_notes text,
    currency character varying(10) DEFAULT 'CNY'::character varying
);


--
-- TOC entry 5458 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.pricing_order_id IS '批价单ID';


--
-- TOC entry 5459 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.settlement_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_order_id IS '结算单ID';


--
-- TOC entry 5460 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_name IS '产品名称';


--
-- TOC entry 5461 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_model IS '产品型号';


--
-- TOC entry 5462 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_desc IS '产品描述';


--
-- TOC entry 5463 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.brand IS '品牌';


--
-- TOC entry 5464 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.unit IS '单位';


--
-- TOC entry 5465 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.product_mn IS '产品MN编码';


--
-- TOC entry 5466 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.market_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.market_price IS '市场价';


--
-- TOC entry 5467 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.unit_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.unit_price IS '单价';


--
-- TOC entry 5468 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.quantity; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.quantity IS '数量';


--
-- TOC entry 5469 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.discount_rate IS '折扣率';


--
-- TOC entry 5470 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.total_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.total_price IS '小计金额';


--
-- TOC entry 5471 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.pricing_detail_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.pricing_detail_id IS '关联批价单明细ID';


--
-- TOC entry 5472 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.settlement_company_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_company_id IS '结算目标公司ID';


--
-- TOC entry 5473 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.settlement_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_status IS '结算状态: pending, completed';


--
-- TOC entry 5474 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.settlement_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_date IS '结算完成时间';


--
-- TOC entry 5475 (class 0 OID 0)
-- Dependencies: 403
-- Name: COLUMN settlement_order_details.settlement_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_order_details.settlement_notes IS '结算备注';


--
-- TOC entry 404 (class 1259 OID 17678)
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
-- TOC entry 5476 (class 0 OID 0)
-- Dependencies: 404
-- Name: settlement_order_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_order_details_id_seq OWNED BY public.settlement_order_details.id;


--
-- TOC entry 405 (class 1259 OID 17679)
-- Name: settlement_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.settlement_orders (
    id integer NOT NULL,
    order_number character varying(64) NOT NULL,
    pricing_order_id integer NOT NULL,
    project_id integer NOT NULL,
    quotation_id integer NOT NULL,
    distributor_id integer,
    dealer_id integer,
    total_amount double precision,
    total_discount_rate double precision,
    status character varying(20),
    approved_by integer,
    approved_at timestamp without time zone,
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    settlement_status character varying(20),
    is_direct_contract boolean DEFAULT false,
    is_factory_pickup boolean DEFAULT false
);


--
-- TOC entry 5477 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.order_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.order_number IS '结算单号';


--
-- TOC entry 5478 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.pricing_order_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.pricing_order_id IS '关联批价单ID';


--
-- TOC entry 5479 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.project_id IS '项目ID';


--
-- TOC entry 5480 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.quotation_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.quotation_id IS '报价单ID';


--
-- TOC entry 5481 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.distributor_id IS '分销商ID';


--
-- TOC entry 5482 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.dealer_id IS '经销商ID（辅助信息）';


--
-- TOC entry 5483 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.total_amount; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.total_amount IS '结算总金额';


--
-- TOC entry 5484 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.total_discount_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.total_discount_rate IS '结算总折扣率';


--
-- TOC entry 5485 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.status IS '结算单状态';


--
-- TOC entry 5486 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.approved_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.approved_by IS '批准人';


--
-- TOC entry 5487 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.approved_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.approved_at IS '批准时间';


--
-- TOC entry 5488 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.created_by IS '创建人';


--
-- TOC entry 5489 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.created_at IS '创建时间';


--
-- TOC entry 5490 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.updated_at IS '更新时间';


--
-- TOC entry 5491 (class 0 OID 0)
-- Dependencies: 405
-- Name: COLUMN settlement_orders.settlement_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.settlement_orders.settlement_status IS '结算状态：pending, processing, completed, cancelled';


--
-- TOC entry 406 (class 1259 OID 17682)
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
-- TOC entry 5492 (class 0 OID 0)
-- Dependencies: 406
-- Name: settlement_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlement_orders_id_seq OWNED BY public.settlement_orders.id;


--
-- TOC entry 407 (class 1259 OID 17683)
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
-- TOC entry 408 (class 1259 OID 17688)
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
-- TOC entry 5493 (class 0 OID 0)
-- Dependencies: 408
-- Name: settlements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.settlements_id_seq OWNED BY public.settlements.id;


--
-- TOC entry 409 (class 1259 OID 17689)
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
-- TOC entry 5494 (class 0 OID 0)
-- Dependencies: 409
-- Name: COLUMN solution_manager_email_settings.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.user_id IS '解决方案经理用户ID';


--
-- TOC entry 5495 (class 0 OID 0)
-- Dependencies: 409
-- Name: COLUMN solution_manager_email_settings.quotation_created; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_created IS '报价单新建通知';


--
-- TOC entry 5496 (class 0 OID 0)
-- Dependencies: 409
-- Name: COLUMN solution_manager_email_settings.quotation_updated; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.quotation_updated IS '报价单更新通知';


--
-- TOC entry 5497 (class 0 OID 0)
-- Dependencies: 409
-- Name: COLUMN solution_manager_email_settings.project_created; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_created IS '项目新建通知';


--
-- TOC entry 5498 (class 0 OID 0)
-- Dependencies: 409
-- Name: COLUMN solution_manager_email_settings.project_stage_changed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.solution_manager_email_settings.project_stage_changed IS '项目阶段推进通知';


--
-- TOC entry 410 (class 1259 OID 17692)
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
-- TOC entry 5499 (class 0 OID 0)
-- Dependencies: 410
-- Name: solution_manager_email_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.solution_manager_email_settings_id_seq OWNED BY public.solution_manager_email_settings.id;


--
-- TOC entry 452 (class 1259 OID 62717)
-- Name: stage_attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stage_attachments (
    id integer NOT NULL,
    product_id integer NOT NULL,
    stage_key character varying(50) NOT NULL,
    milestone_id integer,
    file_name character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_size bigint,
    file_type character varying(50),
    uploaded_by integer,
    uploaded_at timestamp without time zone,
    description text
);


--
-- TOC entry 451 (class 1259 OID 62716)
-- Name: stage_attachments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.stage_attachments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5500 (class 0 OID 0)
-- Dependencies: 451
-- Name: stage_attachments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stage_attachments_id_seq OWNED BY public.stage_attachments.id;


--
-- TOC entry 448 (class 1259 OID 62686)
-- Name: stage_dependencies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stage_dependencies (
    id integer NOT NULL,
    product_id integer NOT NULL,
    predecessor_stage character varying(50) NOT NULL,
    successor_stage character varying(50) NOT NULL,
    dependency_type character varying(30),
    lag_days integer,
    created_at timestamp without time zone
);


--
-- TOC entry 447 (class 1259 OID 62685)
-- Name: stage_dependencies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.stage_dependencies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5501 (class 0 OID 0)
-- Dependencies: 447
-- Name: stage_dependencies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stage_dependencies_id_seq OWNED BY public.stage_dependencies.id;


--
-- TOC entry 450 (class 1259 OID 62698)
-- Name: stage_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stage_reviews (
    id integer NOT NULL,
    product_id integer NOT NULL,
    stage_key character varying(50) NOT NULL,
    review_type character varying(50),
    reviewer_id integer,
    review_result character varying(30),
    review_comments text,
    review_date timestamp without time zone,
    created_at timestamp without time zone
);


--
-- TOC entry 449 (class 1259 OID 62697)
-- Name: stage_reviews_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.stage_reviews_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5502 (class 0 OID 0)
-- Dependencies: 449
-- Name: stage_reviews_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stage_reviews_id_seq OWNED BY public.stage_reviews.id;


--
-- TOC entry 411 (class 1259 OID 17693)
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
-- TOC entry 5503 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.version_id IS '版本ID';


--
-- TOC entry 5504 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.avg_response_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.avg_response_time IS '平均响应时间（毫秒）';


--
-- TOC entry 5505 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.max_response_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.max_response_time IS '最大响应时间（毫秒）';


--
-- TOC entry 5506 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.error_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.error_rate IS '错误率（百分比）';


--
-- TOC entry 5507 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.active_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.active_users IS '活跃用户数';


--
-- TOC entry 5508 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.total_requests; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.total_requests IS '总请求数';


--
-- TOC entry 5509 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.database_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.database_size IS '数据库大小（字节）';


--
-- TOC entry 5510 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.cpu_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.cpu_usage IS 'CPU使用率（百分比）';


--
-- TOC entry 5511 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.memory_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.memory_usage IS '内存使用率（百分比）';


--
-- TOC entry 5512 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.disk_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.disk_usage IS '磁盘使用率（百分比）';


--
-- TOC entry 5513 (class 0 OID 0)
-- Dependencies: 411
-- Name: COLUMN system_metrics.recorded_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.system_metrics.recorded_at IS '记录时间';


--
-- TOC entry 412 (class 1259 OID 17696)
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
-- TOC entry 5514 (class 0 OID 0)
-- Dependencies: 412
-- Name: system_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_metrics_id_seq OWNED BY public.system_metrics.id;


--
-- TOC entry 413 (class 1259 OID 17697)
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
-- TOC entry 414 (class 1259 OID 17702)
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
-- TOC entry 5515 (class 0 OID 0)
-- Dependencies: 414
-- Name: system_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_settings_id_seq OWNED BY public.system_settings.id;


--
-- TOC entry 415 (class 1259 OID 17703)
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
-- TOC entry 5516 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_name IS '产品名称';


--
-- TOC entry 5517 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_model IS '产品型号';


--
-- TOC entry 5518 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_desc IS '产品描述/规格';


--
-- TOC entry 5519 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.brand IS '品牌';


--
-- TOC entry 5520 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.unit IS '单位';


--
-- TOC entry 5521 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_mn IS '临时产品MN号，格式为TEMP-{8位随机码}';


--
-- TOC entry 5522 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.category IS '关联的三级分类';


--
-- TOC entry 5523 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.category_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.category_path IS '完整分类路径，如：基站/近端设备/室内型';


--
-- TOC entry 5524 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.created_by IS '创建用户ID';


--
-- TOC entry 5525 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.reference_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.reference_price IS '参考价格（保存时的单价）';


--
-- TOC entry 5526 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.usage_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.usage_count IS '使用次数';


--
-- TOC entry 5527 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.last_used_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.last_used_at IS '最后使用时间';


--
-- TOC entry 5528 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.created_at IS '创建时间';


--
-- TOC entry 5529 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.updated_at IS '更新时间';


--
-- TOC entry 5530 (class 0 OID 0)
-- Dependencies: 415
-- Name: COLUMN temp_products.is_deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.is_deleted IS '是否已删除';


--
-- TOC entry 416 (class 1259 OID 17708)
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
-- TOC entry 5531 (class 0 OID 0)
-- Dependencies: 416
-- Name: temp_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.temp_products_id_seq OWNED BY public.temp_products.id;


--
-- TOC entry 417 (class 1259 OID 17709)
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
-- TOC entry 5532 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.version_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.version_id IS '版本ID';


--
-- TOC entry 5533 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.from_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.from_version IS '升级前版本';


--
-- TOC entry 5534 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.to_version; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.to_version IS '升级后版本';


--
-- TOC entry 5535 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.upgrade_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_date IS '升级时间';


--
-- TOC entry 5536 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.upgrade_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_type IS '升级类型：manual/automatic';


--
-- TOC entry 5537 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.status IS '升级状态：success/failed/rollback';


--
-- TOC entry 5538 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.upgrade_notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.upgrade_notes IS '升级说明';


--
-- TOC entry 5539 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.error_message; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.error_message IS '错误信息（如果升级失败）';


--
-- TOC entry 5540 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.duration_seconds; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.duration_seconds IS '升级耗时（秒）';


--
-- TOC entry 5541 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.operator_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.operator_id IS '操作人员ID';


--
-- TOC entry 5542 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.operator_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.operator_name IS '操作人员姓名';


--
-- TOC entry 5543 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.environment IS '升级环境';


--
-- TOC entry 5544 (class 0 OID 0)
-- Dependencies: 417
-- Name: COLUMN upgrade_logs.server_info; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.upgrade_logs.server_info IS '服务器信息';


--
-- TOC entry 418 (class 1259 OID 17714)
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
-- TOC entry 5545 (class 0 OID 0)
-- Dependencies: 418
-- Name: upgrade_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.upgrade_logs_id_seq OWNED BY public.upgrade_logs.id;


--
-- TOC entry 419 (class 1259 OID 17715)
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
-- TOC entry 5546 (class 0 OID 0)
-- Dependencies: 419
-- Name: COLUMN user_event_subscriptions.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.user_id IS '订阅者用户ID';


--
-- TOC entry 5547 (class 0 OID 0)
-- Dependencies: 419
-- Name: COLUMN user_event_subscriptions.target_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.target_user_id IS '被订阅的用户ID';


--
-- TOC entry 5548 (class 0 OID 0)
-- Dependencies: 419
-- Name: COLUMN user_event_subscriptions.event_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.event_id IS '事件ID';


--
-- TOC entry 5549 (class 0 OID 0)
-- Dependencies: 419
-- Name: COLUMN user_event_subscriptions.enabled; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_event_subscriptions.enabled IS '是否启用订阅';


--
-- TOC entry 420 (class 1259 OID 17718)
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
-- TOC entry 5550 (class 0 OID 0)
-- Dependencies: 420
-- Name: user_event_subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_event_subscriptions_id_seq OWNED BY public.user_event_subscriptions.id;


--
-- TOC entry 421 (class 1259 OID 17719)
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
    updated_at double precision,
    last_login double precision,
    language_preference character varying(10)
);


--
-- TOC entry 422 (class 1259 OID 17724)
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
-- TOC entry 5551 (class 0 OID 0)
-- Dependencies: 422
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 423 (class 1259 OID 17725)
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
-- TOC entry 5552 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.version_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.version_number IS '版本号，如1.0.0';


--
-- TOC entry 5553 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.version_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.version_name IS '版本名称';


--
-- TOC entry 5554 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.release_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.release_date IS '发布日期';


--
-- TOC entry 5555 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.description IS '版本描述';


--
-- TOC entry 5556 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.is_current; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.is_current IS '是否为当前版本';


--
-- TOC entry 5557 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.environment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.environment IS '环境：development/production';


--
-- TOC entry 5558 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.total_features; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_features IS '新增功能数量';


--
-- TOC entry 5559 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.total_fixes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_fixes IS '修复问题数量';


--
-- TOC entry 5560 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.total_improvements; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.total_improvements IS '改进数量';


--
-- TOC entry 5561 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.git_commit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.git_commit IS 'Git提交哈希';


--
-- TOC entry 5562 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.build_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.build_number IS '构建号';


--
-- TOC entry 5563 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.created_at IS '创建时间';


--
-- TOC entry 5564 (class 0 OID 0)
-- Dependencies: 423
-- Name: COLUMN version_records.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.version_records.updated_at IS '更新时间';


--
-- TOC entry 424 (class 1259 OID 17730)
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
-- TOC entry 5565 (class 0 OID 0)
-- Dependencies: 424
-- Name: version_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.version_records_id_seq OWNED BY public.version_records.id;


--
-- TOC entry 301 (class 1259 OID 17247)
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
-- TOC entry 293 (class 1259 OID 17000)
-- Name: schema_migrations; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);


--
-- TOC entry 296 (class 1259 OID 17023)
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
-- TOC entry 295 (class 1259 OID 17022)
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
-- TOC entry 276 (class 1259 OID 16544)
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
    owner_id text,
    type storage.buckettype DEFAULT 'STANDARD'::storage.buckettype NOT NULL
);


--
-- TOC entry 5566 (class 0 OID 0)
-- Dependencies: 276
-- Name: COLUMN buckets.owner; Type: COMMENT; Schema: storage; Owner: -
--

COMMENT ON COLUMN storage.buckets.owner IS 'Field is deprecated, use owner_id instead';


--
-- TOC entry 426 (class 1259 OID 18746)
-- Name: buckets_analytics; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.buckets_analytics (
    id text NOT NULL,
    type storage.buckettype DEFAULT 'ANALYTICS'::storage.buckettype NOT NULL,
    format text DEFAULT 'ICEBERG'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- TOC entry 278 (class 1259 OID 16586)
-- Name: migrations; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.migrations (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    hash character varying(40) NOT NULL,
    executed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- TOC entry 277 (class 1259 OID 16559)
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
    user_metadata jsonb,
    level integer
);


--
-- TOC entry 5567 (class 0 OID 0)
-- Dependencies: 277
-- Name: COLUMN objects.owner; Type: COMMENT; Schema: storage; Owner: -
--

COMMENT ON COLUMN storage.objects.owner IS 'Field is deprecated, use owner_id instead';


--
-- TOC entry 425 (class 1259 OID 18701)
-- Name: prefixes; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.prefixes (
    bucket_id text NOT NULL,
    name text NOT NULL COLLATE pg_catalog."C",
    level integer GENERATED ALWAYS AS (storage.get_level(name)) STORED NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- TOC entry 298 (class 1259 OID 17117)
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
-- TOC entry 299 (class 1259 OID 17131)
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
-- TOC entry 3995 (class 2604 OID 16508)
-- Name: refresh_tokens id; Type: DEFAULT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('auth.refresh_tokens_id_seq'::regclass);


--
-- TOC entry 4029 (class 2604 OID 17731)
-- Name: action_reply id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_reply ALTER COLUMN id SET DEFAULT nextval('public.action_reply_id_seq'::regclass);


--
-- TOC entry 4030 (class 2604 OID 17732)
-- Name: actions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions ALTER COLUMN id SET DEFAULT nextval('public.actions_id_seq'::regclass);


--
-- TOC entry 4031 (class 2604 OID 17733)
-- Name: affiliations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.affiliations ALTER COLUMN id SET DEFAULT nextval('public.affiliations_id_seq'::regclass);


--
-- TOC entry 4032 (class 2604 OID 17734)
-- Name: approval_instance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_instance ALTER COLUMN id SET DEFAULT nextval('public.approval_instance_id_seq'::regclass);


--
-- TOC entry 4033 (class 2604 OID 17735)
-- Name: approval_process_template id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_process_template ALTER COLUMN id SET DEFAULT nextval('public.approval_process_template_id_seq'::regclass);


--
-- TOC entry 4037 (class 2604 OID 17736)
-- Name: approval_record id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record ALTER COLUMN id SET DEFAULT nextval('public.approval_record_id_seq'::regclass);


--
-- TOC entry 4038 (class 2604 OID 17737)
-- Name: approval_step id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_step ALTER COLUMN id SET DEFAULT nextval('public.approval_step_id_seq'::regclass);


--
-- TOC entry 4046 (class 2604 OID 17738)
-- Name: change_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.change_logs ALTER COLUMN id SET DEFAULT nextval('public.change_logs_id_seq'::regclass);


--
-- TOC entry 4047 (class 2604 OID 17739)
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- TOC entry 4048 (class 2604 OID 17740)
-- Name: company_assets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_assets ALTER COLUMN id SET DEFAULT nextval('public.company_assets_id_seq'::regclass);


--
-- TOC entry 4049 (class 2604 OID 17741)
-- Name: contacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts ALTER COLUMN id SET DEFAULT nextval('public.contacts_id_seq'::regclass);


--
-- TOC entry 4178 (class 2604 OID 21087)
-- Name: data_field_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_field_config ALTER COLUMN id SET DEFAULT nextval('public.data_field_config_id_seq'::regclass);


--
-- TOC entry 4176 (class 2604 OID 21052)
-- Name: data_table_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_table_config ALTER COLUMN id SET DEFAULT nextval('public.data_table_config_id_seq'::regclass);


--
-- TOC entry 4050 (class 2604 OID 17742)
-- Name: departments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments ALTER COLUMN id SET DEFAULT nextval('public.departments_id_seq'::regclass);


--
-- TOC entry 4186 (class 2604 OID 62670)
-- Name: dev_product_milestones id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_milestones ALTER COLUMN id SET DEFAULT nextval('public.dev_product_milestones_id_seq'::regclass);


--
-- TOC entry 4051 (class 2604 OID 17743)
-- Name: dev_product_specs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_specs ALTER COLUMN id SET DEFAULT nextval('public.dev_product_specs_id_seq'::regclass);


--
-- TOC entry 4052 (class 2604 OID 17744)
-- Name: dev_products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_products ALTER COLUMN id SET DEFAULT nextval('public.dev_products_id_seq'::regclass);


--
-- TOC entry 4056 (class 2604 OID 17745)
-- Name: dictionaries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dictionaries ALTER COLUMN id SET DEFAULT nextval('public.dictionaries_id_seq'::regclass);


--
-- TOC entry 4058 (class 2604 OID 17746)
-- Name: event_registry id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_registry ALTER COLUMN id SET DEFAULT nextval('public.event_registry_id_seq'::regclass);


--
-- TOC entry 4059 (class 2604 OID 17747)
-- Name: expense_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense_details ALTER COLUMN id SET DEFAULT nextval('public.expense_details_id_seq'::regclass);


--
-- TOC entry 4064 (class 2604 OID 17748)
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.expenses_id_seq'::regclass);


--
-- TOC entry 4067 (class 2604 OID 17749)
-- Name: feature_changes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes ALTER COLUMN id SET DEFAULT nextval('public.feature_changes_id_seq'::regclass);


--
-- TOC entry 4068 (class 2604 OID 17750)
-- Name: five_star_project_baselines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.five_star_project_baselines ALTER COLUMN id SET DEFAULT nextval('public.five_star_project_baselines_id_seq'::regclass);


--
-- TOC entry 4177 (class 2604 OID 21073)
-- Name: formula_templates_extended id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formula_templates_extended ALTER COLUMN id SET DEFAULT nextval('public.formula_templates_extended_id_seq'::regclass);


--
-- TOC entry 4069 (class 2604 OID 17751)
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- TOC entry 4070 (class 2604 OID 17752)
-- Name: inventory_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions ALTER COLUMN id SET DEFAULT nextval('public.inventory_transactions_id_seq'::regclass);


--
-- TOC entry 4173 (class 2604 OID 19902)
-- Name: performance_formula_templates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_formula_templates ALTER COLUMN id SET DEFAULT nextval('public.performance_formula_templates_id_seq'::regclass);


--
-- TOC entry 4171 (class 2604 OID 19872)
-- Name: performance_metrics_definition id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_metrics_definition ALTER COLUMN id SET DEFAULT nextval('public.performance_metrics_definition_id_seq'::regclass);


--
-- TOC entry 4071 (class 2604 OID 17753)
-- Name: performance_statistics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_statistics ALTER COLUMN id SET DEFAULT nextval('public.performance_statistics_id_seq'::regclass);


--
-- TOC entry 4074 (class 2604 OID 17754)
-- Name: performance_targets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_targets ALTER COLUMN id SET DEFAULT nextval('public.performance_targets_id_seq'::regclass);


--
-- TOC entry 4079 (class 2604 OID 17755)
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- TOC entry 4082 (class 2604 OID 17756)
-- Name: pricing_order_approval_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_approval_records ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_approval_records_id_seq'::regclass);


--
-- TOC entry 4083 (class 2604 OID 17757)
-- Name: pricing_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_order_details ALTER COLUMN id SET DEFAULT nextval('public.pricing_order_details_id_seq'::regclass);


--
-- TOC entry 4085 (class 2604 OID 17758)
-- Name: pricing_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pricing_orders ALTER COLUMN id SET DEFAULT nextval('public.pricing_orders_id_seq'::regclass);


--
-- TOC entry 4089 (class 2604 OID 17759)
-- Name: product_categories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_categories ALTER COLUMN id SET DEFAULT nextval('public.product_categories_id_seq'::regclass);


--
-- TOC entry 4090 (class 2604 OID 17760)
-- Name: product_code_field_options id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_options ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_options_id_seq'::regclass);


--
-- TOC entry 4091 (class 2604 OID 17761)
-- Name: product_code_field_values id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_field_values ALTER COLUMN id SET DEFAULT nextval('public.product_code_field_values_id_seq'::regclass);


--
-- TOC entry 4092 (class 2604 OID 17762)
-- Name: product_code_fields id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_code_fields ALTER COLUMN id SET DEFAULT nextval('public.product_code_fields_id_seq'::regclass);


--
-- TOC entry 4093 (class 2604 OID 17763)
-- Name: product_codes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_codes ALTER COLUMN id SET DEFAULT nextval('public.product_codes_id_seq'::regclass);


--
-- TOC entry 4094 (class 2604 OID 17764)
-- Name: product_regions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_regions ALTER COLUMN id SET DEFAULT nextval('public.product_regions_id_seq'::regclass);


--
-- TOC entry 4095 (class 2604 OID 17765)
-- Name: product_subcategories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product_subcategories ALTER COLUMN id SET DEFAULT nextval('public.product_subcategories_id_seq'::regclass);


--
-- TOC entry 4096 (class 2604 OID 17766)
-- Name: products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- TOC entry 4099 (class 2604 OID 17767)
-- Name: project_customer_associations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_customer_associations ALTER COLUMN id SET DEFAULT nextval('public.project_customer_associations_id_seq'::regclass);


--
-- TOC entry 4100 (class 2604 OID 17768)
-- Name: project_members id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members ALTER COLUMN id SET DEFAULT nextval('public.project_members_id_seq'::regclass);


--
-- TOC entry 4101 (class 2604 OID 17769)
-- Name: project_rating_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_rating_records ALTER COLUMN id SET DEFAULT nextval('public.project_rating_records_id_seq'::regclass);


--
-- TOC entry 4102 (class 2604 OID 17770)
-- Name: project_scoring_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_config ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_config_id_seq'::regclass);


--
-- TOC entry 4107 (class 2604 OID 17771)
-- Name: project_scoring_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_scoring_records ALTER COLUMN id SET DEFAULT nextval('public.project_scoring_records_id_seq'::regclass);


--
-- TOC entry 4112 (class 2604 OID 17772)
-- Name: project_stage_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_stage_history ALTER COLUMN id SET DEFAULT nextval('public.project_stage_history_id_seq'::regclass);


--
-- TOC entry 4114 (class 2604 OID 17773)
-- Name: project_total_scores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_total_scores ALTER COLUMN id SET DEFAULT nextval('public.project_total_scores_id_seq'::regclass);


--
-- TOC entry 4124 (class 2604 OID 17774)
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- TOC entry 4131 (class 2604 OID 17775)
-- Name: purchase_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_details ALTER COLUMN id SET DEFAULT nextval('public.purchase_order_details_id_seq'::regclass);


--
-- TOC entry 4132 (class 2604 OID 17776)
-- Name: purchase_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders ALTER COLUMN id SET DEFAULT nextval('public.purchase_orders_id_seq'::regclass);


--
-- TOC entry 4133 (class 2604 OID 17777)
-- Name: quotation_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotation_details ALTER COLUMN id SET DEFAULT nextval('public.quotation_details_id_seq'::regclass);


--
-- TOC entry 4135 (class 2604 OID 17778)
-- Name: quotations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quotations ALTER COLUMN id SET DEFAULT nextval('public.quotations_id_seq'::regclass);


--
-- TOC entry 4174 (class 2604 OID 19911)
-- Name: role_performance_access id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_access ALTER COLUMN id SET DEFAULT nextval('public.role_performance_access_id_seq'::regclass);


--
-- TOC entry 4172 (class 2604 OID 19882)
-- Name: role_performance_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_config ALTER COLUMN id SET DEFAULT nextval('public.role_performance_config_id_seq'::regclass);


--
-- TOC entry 4175 (class 2604 OID 19924)
-- Name: role_performance_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_items ALTER COLUMN id SET DEFAULT nextval('public.role_performance_items_id_seq'::regclass);


--
-- TOC entry 4146 (class 2604 OID 17779)
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- TOC entry 4149 (class 2604 OID 17780)
-- Name: settlement_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_details_id_seq'::regclass);


--
-- TOC entry 4150 (class 2604 OID 17781)
-- Name: settlement_order_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_order_details ALTER COLUMN id SET DEFAULT nextval('public.settlement_order_details_id_seq'::regclass);


--
-- TOC entry 4152 (class 2604 OID 17782)
-- Name: settlement_orders id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlement_orders ALTER COLUMN id SET DEFAULT nextval('public.settlement_orders_id_seq'::regclass);


--
-- TOC entry 4155 (class 2604 OID 17783)
-- Name: settlements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements ALTER COLUMN id SET DEFAULT nextval('public.settlements_id_seq'::regclass);


--
-- TOC entry 4156 (class 2604 OID 17784)
-- Name: solution_manager_email_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solution_manager_email_settings ALTER COLUMN id SET DEFAULT nextval('public.solution_manager_email_settings_id_seq'::regclass);


--
-- TOC entry 4189 (class 2604 OID 62720)
-- Name: stage_attachments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stage_attachments ALTER COLUMN id SET DEFAULT nextval('public.stage_attachments_id_seq'::regclass);


--
-- TOC entry 4187 (class 2604 OID 62689)
-- Name: stage_dependencies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stage_dependencies ALTER COLUMN id SET DEFAULT nextval('public.stage_dependencies_id_seq'::regclass);


--
-- TOC entry 4188 (class 2604 OID 62701)
-- Name: stage_reviews id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stage_reviews ALTER COLUMN id SET DEFAULT nextval('public.stage_reviews_id_seq'::regclass);


--
-- TOC entry 4157 (class 2604 OID 17785)
-- Name: system_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics ALTER COLUMN id SET DEFAULT nextval('public.system_metrics_id_seq'::regclass);


--
-- TOC entry 4158 (class 2604 OID 17786)
-- Name: system_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings ALTER COLUMN id SET DEFAULT nextval('public.system_settings_id_seq'::regclass);


--
-- TOC entry 4159 (class 2604 OID 17787)
-- Name: temp_products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temp_products ALTER COLUMN id SET DEFAULT nextval('public.temp_products_id_seq'::regclass);


--
-- TOC entry 4160 (class 2604 OID 17788)
-- Name: upgrade_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.upgrade_logs ALTER COLUMN id SET DEFAULT nextval('public.upgrade_logs_id_seq'::regclass);


--
-- TOC entry 4161 (class 2604 OID 17789)
-- Name: user_event_subscriptions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_event_subscriptions ALTER COLUMN id SET DEFAULT nextval('public.user_event_subscriptions_id_seq'::regclass);


--
-- TOC entry 4162 (class 2604 OID 17790)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4163 (class 2604 OID 17791)
-- Name: version_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_records ALTER COLUMN id SET DEFAULT nextval('public.version_records_id_seq'::regclass);


--
-- TOC entry 4980 (class 0 OID 16523)
-- Dependencies: 274
-- Data for Name: audit_log_entries; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.audit_log_entries (instance_id, id, payload, created_at, ip_address) FROM stdin;
\.


--
-- TOC entry 4994 (class 0 OID 16925)
-- Dependencies: 291
-- Data for Name: flow_state; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.flow_state (id, user_id, auth_code, code_challenge_method, code_challenge, provider_type, provider_access_token, provider_refresh_token, created_at, updated_at, authentication_method, auth_code_issued_at) FROM stdin;
\.


--
-- TOC entry 4985 (class 0 OID 16723)
-- Dependencies: 282
-- Data for Name: identities; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.identities (provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at, id) FROM stdin;
\.


--
-- TOC entry 4979 (class 0 OID 16516)
-- Dependencies: 273
-- Data for Name: instances; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.instances (id, uuid, raw_base_config, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4989 (class 0 OID 16812)
-- Dependencies: 286
-- Data for Name: mfa_amr_claims; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.mfa_amr_claims (session_id, created_at, updated_at, authentication_method, id) FROM stdin;
\.


--
-- TOC entry 4988 (class 0 OID 16800)
-- Dependencies: 285
-- Data for Name: mfa_challenges; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.mfa_challenges (id, factor_id, created_at, verified_at, ip_address, otp_code, web_authn_session_data) FROM stdin;
\.


--
-- TOC entry 4987 (class 0 OID 16787)
-- Dependencies: 284
-- Data for Name: mfa_factors; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.mfa_factors (id, user_id, friendly_name, factor_type, status, created_at, updated_at, secret, phone, last_challenged_at, web_authn_credential, web_authn_aaguid, last_webauthn_challenge_data) FROM stdin;
\.


--
-- TOC entry 5152 (class 0 OID 96019)
-- Dependencies: 453
-- Data for Name: oauth_authorizations; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.oauth_authorizations (id, authorization_id, client_id, user_id, redirect_uri, scope, state, resource, code_challenge, code_challenge_method, response_type, status, authorization_code, created_at, expires_at, approved_at) FROM stdin;
\.


--
-- TOC entry 5143 (class 0 OID 47147)
-- Dependencies: 444
-- Data for Name: oauth_clients; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.oauth_clients (id, client_secret_hash, registration_type, redirect_uris, grant_types, client_name, client_uri, logo_uri, created_at, updated_at, deleted_at, client_type) FROM stdin;
\.


--
-- TOC entry 5153 (class 0 OID 96052)
-- Dependencies: 454
-- Data for Name: oauth_consents; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.oauth_consents (id, user_id, client_id, scopes, granted_at, revoked_at) FROM stdin;
\.


--
-- TOC entry 4995 (class 0 OID 16975)
-- Dependencies: 292
-- Data for Name: one_time_tokens; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.one_time_tokens (id, user_id, token_type, token_hash, relates_to, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4978 (class 0 OID 16505)
-- Dependencies: 272
-- Data for Name: refresh_tokens; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.refresh_tokens (instance_id, id, token, user_id, revoked, created_at, updated_at, parent, session_id) FROM stdin;
\.


--
-- TOC entry 4992 (class 0 OID 16854)
-- Dependencies: 289
-- Data for Name: saml_providers; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.saml_providers (id, sso_provider_id, entity_id, metadata_xml, metadata_url, attribute_mapping, created_at, updated_at, name_id_format) FROM stdin;
\.


--
-- TOC entry 4993 (class 0 OID 16872)
-- Dependencies: 290
-- Data for Name: saml_relay_states; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.saml_relay_states (id, sso_provider_id, request_id, for_email, redirect_to, created_at, updated_at, flow_state_id) FROM stdin;
\.


--
-- TOC entry 4981 (class 0 OID 16531)
-- Dependencies: 275
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
20250717082212
20250731150234
20250804100000
20250901200500
20250903112500
20250904133000
20250925093508
20251007112900
\.


--
-- TOC entry 4986 (class 0 OID 16753)
-- Dependencies: 283
-- Data for Name: sessions; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.sessions (id, user_id, created_at, updated_at, factor_id, aal, not_after, refreshed_at, user_agent, ip, tag, oauth_client_id, refresh_token_hmac_key, refresh_token_counter) FROM stdin;
\.


--
-- TOC entry 4991 (class 0 OID 16839)
-- Dependencies: 288
-- Data for Name: sso_domains; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.sso_domains (id, sso_provider_id, domain, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4990 (class 0 OID 16830)
-- Dependencies: 287
-- Data for Name: sso_providers; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.sso_providers (id, resource_id, created_at, updated_at, disabled) FROM stdin;
\.


--
-- TOC entry 4976 (class 0 OID 16493)
-- Dependencies: 270
-- Data for Name: users; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at, invited_at, confirmation_token, confirmation_sent_at, recovery_token, recovery_sent_at, email_change_token_new, email_change, email_change_sent_at, last_sign_in_at, raw_app_meta_data, raw_user_meta_data, is_super_admin, created_at, updated_at, phone, phone_confirmed_at, phone_change, phone_change_token, phone_change_sent_at, email_change_token_current, email_change_confirm_status, banned_until, reauthentication_token, reauthentication_sent_at, is_sso_user, deleted_at, is_anonymous) FROM stdin;
\.


--
-- TOC entry 5001 (class 0 OID 17333)
-- Dependencies: 302
-- Data for Name: action_reply; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.action_reply (id, action_id, parent_reply_id, content, owner_id, created_at, updated_at) FROM stdin;
2	477	\N	1111	13	2025-05-14 02:33:29.994408	2025-05-14 02:33:29.99441
4	771	\N	原厂设备几乎瘫痪，代表这几年的维保运营是失败的，所以建议对方无论发包给任何第三方都要求有原厂的授权来确保系统质量	5	2025-05-27 11:43:35.545658	2025-05-27 11:43:35.54566
8	785	\N	请及时更新确定是否继续，如果不继续请改为失败或搁置	5	2025-06-03 03:59:08.841445	2025-06-03 03:59:08.841447
9	804	\N	确定丢失要更新状态到失败	5	2025-06-03 04:03:59.117956	2025-06-03 04:03:59.117958
10	788	\N	请确认项目目前的最新的情况，确认阶段是否需要调整	13	2025-06-03 09:27:31.537783	2025-06-03 09:27:31.537785
11	816	\N	你的焦点应该集中在用户对原产产品维护的要求，转而接触云思这些维护单位成功率是很小的	5	2025-06-05 03:20:55.070885	2025-06-05 03:20:55.070888
12	842	\N	同意	7	2025-06-10 02:20:57.088734	2025-06-10 02:20:57.088737
13	978	\N	客户后续还有50套防爆对讲机需求，预计在7/8完成采购。	2	2025-07-01 05:35:24.904457	2025-07-01 05:35:24.904459
14	1096	\N	目前有接触到城欣嘛	13	2025-07-29 02:29:18.460742	2025-07-29 02:29:18.460744
15	1460	\N	客户要求明年的维保，维保清单要重新做，分两部分，设备维保费和设备维修单价；	20	2025-09-09 10:11:16.31762	2025-09-09 10:11:16.317622
\.


--
-- TOC entry 5003 (class 0 OID 17339)
-- Dependencies: 304
-- Data for Name: actions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.actions (id, date, contact_id, company_id, project_id, communication, created_at, owner_id, is_shared) FROM stdin;
1128	2025-08-01	130	443	\N	通信费用8月费走流程开票。	2025-08-01 05:48:37.499516	2	t
1129	2025-08-01	132	444	\N	二厂对讲机突发有2个频道无法呼叫，与客户电话沟通去主机房查看，一台信道机告警灯红灯，告知客户关机重启后通信正常，但过段时间后又出现如此情况，约客户8月4日上门排查故障。	2025-08-01 05:52:20.890009	2	t
1130	2025-07-29	435	252	112	与国际机场股份有限公司合约部黄经理确认上周现场应标答疑现场会议，根据会议沟通纪要，确认2025-2029年浦东机场卫星厅消防用无线对讲系统最终合约价格与应标答疑现场关于合约执行增项内容纸面确认，双方最终背书完成签字，进入商务流程环节；	2025-08-01 05:59:46.507606	7	t
1131	2025-07-31	460	264	638	与中芯南方业主ERC负责人沟通提交的中芯南方无线对讲系统的维护工作，业主方认可方案，但谈及到维护所涉及到的目前正在施工的P3项目增补，由于增补部分属于新建成，所以需要考虑在上报系统维护时如何处理新增部分仍然在质保范围内却要签订有偿维护合约的问题；	2025-08-01 06:08:14.737089	7	t
1132	2025-08-01	745	549	\N	公网通信许可费用9月份到期，与客户确认续费事宜，先行报价给用户。	2025-08-01 06:42:06.843442	2	t
1133	2025-08-01	108	428	\N	公网通信费用8月到期，与客户确认续费事宜，客户要上报领导审批后再回复。	2025-08-01 06:44:42.931506	2	t
1134	2025-07-29	\N	550	683	保邦龚总介绍，他正在运作智能化分包，价格需要到位，品牌还没有定，符合最低技术参数要求即可。	2025-08-03 15:51:32.681159	17	t
1135	2025-07-31	\N	551	684	中通服深圳销售负责人王浩文介绍，本项目有他们和广州市安装集团分别中标智能化。他们包内有酒店和部分商业，广州安装保内有办公和商业部分，目前他们还没有进场，品牌也没有定，清单也还未深化，下周到公司介绍技术对接人，价格需要有优势。	2025-08-03 15:59:59.613894	17	t
1136	2025-08-01	660	171	685	筑博设计院王院长介绍，主体是他们做的设计，智能化也由她这边在负责运作，暂时还没有招标。华润的项目需要用库内品牌，不了解天馈部分有没有要求，需要找业主方去了解，如果有要求建议入库或者通过方案来绕开。	2025-08-03 16:03:06.274162	17	t
1138	2025-07-29	716	154	617	吴经理说近期在休假，上班后会着手评定品牌，虽然我们调整过，但我们的价格不是最优的。	2025-08-03 16:07:16.28171	17	t
1139	2025-07-28	\N	165	148	三局智能介绍，目前进度较慢，招标时间还不能确定，今年内是肯定会招标。	2025-08-03 16:10:01.017544	17	t
1137	2025-07-30	\N	118	679	拜访项目经理张巡万，8月10号前会定品牌，如果基站和对讲机要增加一个品牌，需要我们给出一个较有吸引力的空间（5-10万差价），他们才会去协调。目前还在与张兴评估价差。	2025-08-03 16:04:14.864435	17	t
1140	2025-08-01	616	381	93	李工介绍，我们的价格不占优势，大概率项目经理不会选我们的，建议去做项目经理工作。\r\n已约了项目经理王雪下周拜访。	2025-08-03 16:20:06.984591	17	t
1143	2025-08-04	\N	552	686	和安徽泰合的王总以及中兴高达深入交流了，我司产品在合肥机场的优势，双方就公安对讲接入，室分系统的合作，达成一致	2025-08-04 01:09:59.925799	13	f
741	2025-05-21	682	497	61	经沟通了解代理商与华虹智联商务合约已经确认，在审批流转中，与代理商确认发起批价申请	2025-05-21 06:55:21.232168	14	t
764	2025-05-21	\N	497	595	据了解本项目是由八局智能中的智能化总包，无线对讲没有品牌要求，但在参数上有要求。\r\n分包集成商浙江洲之宇介绍，他们已经中了分包，需要我方给与价格支持。\r\n目前还在侧面了解真实情况，以及改项目的话语权在谁手上。	2025-05-23 10:36:47.831488	17	t
1087	2025-07-24	682	497	\N	与瀚网总经理及售后服务负责人贺望亭沟通国家会展中心无线对讲系统维护招标事宜；包括合约中的系统维护，公网产品，人员安排等等涉及成本的各个分项，根据投标文件中的评分项制作相关资料，最终完成投标文件，24日上午至国家会展中心现场完成现场商务开标；	2025-07-25 02:58:11.925261	7	t
1146	2025-08-04	746	497	\N	贺望亭给到了一部分客户信息，本周会去拜访一下，收集具体信息之后开始跟进；客户名单如下：张江科学会堂、苏州罗氏制药、福建晋华、宜家、世博酒店、淮安荣芯半导体；	2025-08-04 03:09:49.631545	20	f
1147	2025-08-04	433	251	\N	尽量本周能给到客户我司检测报告，或者上门给客户做一次检测；帮客户完成2万元的维修费用；	2025-08-04 03:43:32.697557	20	f
1148	2025-08-04	\N	553	687	渠道与沈佳沟通，确认项目中标信息，但合同还未签订，按其反馈近期就会签订。当时招标时智能化子系统未有明确，所以他们也是投了个总价包干，待合同签订后就会启动深化设计，到时候只要总价合适就可以	2025-08-04 03:51:54.808411	14	t
1149	2025-08-04	\N	\N	528	目前配合卢洪祥调整招标图设计，按其反馈这版图纸设计确认后会作为招标图使用。与吴一涛确认项目概算，按其反馈说设计院还在统计，他这边没有得到消息说是概算已经确认	2025-08-04 03:52:54.140339	14	t
1150	2025-08-04	\N	\N	593	该项目正式挂网公开招标，于8月11号集成商投标，目前询价集成商有上安九分、上电科、中铁建河北分公司、浪潮信息、申北、永天和真赛，渠道淳泊和瀚网都有被询价，及配套报价参与对接各自集成商	2025-08-04 04:06:34.220821	14	t
1151	2025-08-04	532	215	671	该项目渠道反馈与上安九分投标部门沟通，项目未有中标	2025-08-04 04:45:44.685467	14	t
1152	2025-07-30	747	282	\N	邹飞让直接对接胡琦，具体介绍了公司方向跟相关信息，回来后会给到面对代理商跟业主的模版给到对方，后续有项目会带着一起去；	2025-08-04 05:31:58.098122	20	t
1153	2025-08-04	723	524	661	云沛报价已经给到业主方，后续继续跟进；	2025-08-04 06:34:49.706603	20	f
1154	2025-08-04	737	540	\N	客户表示本月比较忙，让下月再联系拜访；	2025-08-04 08:22:06.777806	20	t
369	2025-05-09	496	185	\N	该项目与张旭东了解他们可能放弃自己做，交由其他部门来执行。现阶段又有一家上海众铭找到合作伙伴配合报价	2025-05-09 00:00:00	14	t
380	2025-05-09	496	185	\N	该项目中标，复核项目成本，询价至瀚网。瀚网报备，跟进业务配套	2025-05-09 00:00:00	14	t
388	2025-05-09	521	202	\N	会面	2025-05-09 00:00:00	14	t
1462	2025-09-09	15	50	778	配合完成清单编制与预算	2025-09-09 13:05:30.975943	16	t
1156	2025-08-05	144	454	114	设备已发货，与客户沟通安排安装调试时间及开票工作。	2025-08-05 05:30:02.680682	2	t
1157	2025-08-06	\N	435	689	客户B123 CDP新增2个小操作房间，里面信号弱，按客户需求做了方案及报价。	2025-08-06 02:10:29.333332	2	t
1158	2025-08-07	749	359	686	和易总沟通核实了合肥航站楼项目延后的情况，合肥机场资金有些跟不上，配套的变电站和飞行区的方案是后批的，整体机场交付由2026年改到2027年，项目进度放缓；公安对讲系统放在口岸包里，公安的合作伙伴已和业主对接，我们需要和他们对接下，沟通一下方案	2025-08-07 07:13:39.545583	13	t
1161	2025-08-07	177	343	614	易总反馈客户那边了解到韩国那边提供给船东的解决方案很便宜，和易总沟通后，让易总帮忙了解韩国的解决方案的情况，了解比对后再想办法推动	2025-08-07 07:27:28.106447	13	t
1162	2025-08-07	187	352	690	和业主沟通了康桥项目二期项目交付的问题，了解到三期下半年也会启动，近期资料出来后，需要配合核算清单预算	2025-08-07 07:31:46.868483	13	t
466	2025-05-09	655	166	\N	让瀚网张兴配合在报价。\r\n由于客户清单有缺漏项和本项目分两个标段，每个标段内的具体明细不清晰，系统图内有办公/公寓/康养/商业系统图，清单有三套系统的主设备，有个清单是公用的，但具体是哪两个系统共用？由于时间不多，三局智能表示按照清单先报价，后续再答疑。	2025-05-09 00:00:00	17	t
468	2025-05-09	638	143	\N	由于本项目投标时间较紧，报价最好今天发给他。	2025-05-09 00:00:00	17	t
1163	2025-08-07	750	554	\N	瀚网这里的客户，客户表示对讲机声音太响，约了下周去看看；	2025-08-08 02:10:00.758213	20	t
1164	2025-08-05	751	555	\N	客户在一年半之前就用了公网对讲机了，现在的供应商叫：好咔； 可以尝试介入看看后续能不能替换掉；	2025-08-08 02:39:50.952004	20	t
1165	2025-08-07	435	252	\N	与浦东机场卫星厅业主采购部沟通无线对讲系统维护合约业主方合约流转细节包括公司财务信息，无犯罪受贿证明，最终合约文本等等，相关上流程原件盖章寄出等等；	2025-08-08 02:47:30.899669	7	t
1166	2025-08-06	427	435	\N	B123区域CPD隔音屋无线对讲信号覆盖方案修正并交付商务提交，与区域负责人沟通B196区域MCC的1楼2楼3楼增补天线的事宜；	2025-08-08 02:51:48.306402	7	t
1167	2025-08-05	451	259	\N	与上海中心大厦业主沟通本次上海中心大厦350兆消防用无线对讲系统光端机设备更新2025年资金预算情况，商榷如何设定2026年资金预算的计划等等；	2025-08-08 02:55:29.135565	7	t
1168	2025-08-05	752	556	\N	这家客户是物业托管给第三方的，维保是有检查的；先加微信对接人再把第三方的联系方式给到我；	2025-08-08 03:17:12.347952	20	t
1169	2025-08-05	753	557	\N	客户在开会，先加微信再沟通；	2025-08-08 03:21:49.38583	20	t
1170	2025-08-05	754	558	\N	对接人是龙湖物业的，加微信推送业主给我；	2025-08-08 03:31:59.380657	20	t
1171	2025-08-05	755	559	\N	客户反馈之前有问题一次都没来过，加微信沟通具体细节；	2025-08-08 03:35:32.03397	20	t
1172	2025-08-05	756	560	\N	客户目前确实存在维保的问题，加了微信，后续根据节奏来推进；	2025-08-08 03:40:20.077419	20	t
854	2025-06-11	184	350	590	配合徐工修改ITC的设计资料	2025-06-11 06:48:38.227061	13	t
1173	2025-08-05	682	497	\N	瀚网这里虹桥机场的客户对我们的对讲机有不满，初步沟通瀚网李冬，帮忙建立联系；	2025-08-08 06:49:47.834779	20	t
1174	2025-08-08	755	559	\N	跟客户约了下周二过去看下；	2025-08-08 07:38:46.60046	20	t
1175	2025-08-08	757	558	\N	对接人给了江森邱工的联系方式，加了微信，江森的人表示频道是有点问题的，约下周去看一下；	2025-08-08 08:16:16.026705	20	t
769	2025-05-26	666	474	\N	跟客户约周四拜访；	2025-05-27 02:34:22.197146	20	t
1176	2025-08-08	758	556	\N	约了工程部的下周二去看下；	2025-08-08 09:04:56.589529	20	t
1177	2025-08-08	750	554	\N	暂定下周三，客户让周二再确定下；	2025-08-08 09:22:54.538212	20	t
781	2025-05-30	\N	54	529	目前已和中标集成商联系上，由北京代理商（联航迅达）对接	2025-05-30 01:55:00.275259	16	t
119	2025-05-09	92	88	\N	无品牌招标，云筑网公开招标，价格高；北京雄然电子中标。	2025-05-09 00:00:00	16	t
120	2025-05-09	5	44	\N	本周与集成商沟通一期项目清单调整及初步报价。	2025-05-09 00:00:00	16	t
121	2025-05-09	5	44	\N	配合集成商做初步报价	2025-05-09 00:00:00	16	t
122	2025-05-09	143	453	\N	客户确认再购2套公网机器，节后拿货及付款。	2025-05-09 00:00:00	2	t
123	2025-05-09	160	468	\N	客户对讲机突然无法登陆，确认天线故障，客户再购5根天线。	2025-05-09 00:00:00	2	t
124	2025-05-09	119	435	\N	与客户确认预计二季度下订单，要先确认可供设备型号，一次性供货；目前等待供应链给可供型号。	2025-05-09 00:00:00	2	t
125	2025-05-09	119	435	\N	预订购防爆对讲机，数量150套，沟通目前使用型号，先询供货期，用户8月底前要收到。	2025-05-09 00:00:00	2	t
126	2025-05-09	120	435	\N	B193区域信号补强沟通报价，按报价内清单及调试费 分项下PO单。	2025-05-09 00:00:00	2	t
127	2025-05-09	148	458	\N	用户现场使用的改装车载设备的配件损坏，更换配件，安排订单。	2025-05-09 00:00:00	2	t
128	2025-05-09	154	464	\N	新订购3套干放，走订单流程	2025-05-09 00:00:00	2	t
129	2025-05-09	155	260	\N	现场故障的350M设备已拆除完成，后续先安排检测，完成后安排更换新设备	2025-05-09 00:00:00	2	t
130	2025-05-09	152	462	\N	与客户沟通10套对讲机事宜，告知在等业主流程。	2025-05-09 00:00:00	2	t
131	2025-05-09	116	435	\N	客户确认购买10套机器，已下订单，安排备货。	2025-05-09 00:00:00	2	t
132	2025-05-09	116	435	\N	客户预采购10套防爆机器，与客户沟通目前厂区内防爆机器供货情况，客户按提供的信息安排下单。	2025-05-09 00:00:00	2	t
133	2025-05-09	125	438	\N	客户2套防爆机器确认购买，已付款，安排备货写频，发货给用户。	2025-05-09 00:00:00	2	t
134	2025-05-09	125	438	\N	客户预采购2套防爆对讲机，已报价给客户。	2025-05-09 00:00:00	2	t
1384	2025-09-04	\N	341	561	集成商没中标	2025-09-04 01:52:15.885179	25	t
135	2025-05-09	144	454	\N	在巡检过程中，一台远端机已坏，一台干放功率低，建议客户更换，报价给客户，客户走审批流程。	2025-05-09 00:00:00	2	t
136	2025-05-09	117	435	\N	MDI区域采购20套P8668i防爆机器，与客户沟通目前此款机器供货周期长，可更改为GP338D+防爆机器，客户预算按P8668i申请，GP338D+每台要贵500元。更改无预算，目前可以等待P8668i机器，可以到4月中旬供货。	2025-05-09 00:00:00	2	t
137	2025-05-09	147	457	\N	基美电子的防爆天线项目与客户沟通，目前项目已开始询价阶段，已报价给客户。	2025-05-09 00:00:00	2	t
138	2025-05-09	132	444	\N	他们厂区新建K栋，目前由销售部门在跟进，项目已经总包中标，最终使用ERC部门，销售让协助与ERC部门沟通，如此项目上会，建议使用和源品牌。	2025-05-09 00:00:00	2	t
257	2025-05-09	363	307	\N	年前代理商配合深化确认完成，预计4-5月份左右开始进场穿线，计划3月份让代理商跟进谈判对方合约商务事宜。	2025-05-09 00:00:00	15	t
139	2025-05-09	152	462	\N	和源PNR2000对讲机询价，报价；此批对讲机用于上海松江站，原有站点物业使用，目前现场对讲机移交给消防站点微站使用，需要增加一批机器。	2025-05-09 00:00:00	2	t
140	2025-05-09	160	468	\N	3月份到期的公网机器许可，与客户确认继续使用，月初开票。	2025-05-09 00:00:00	2	t
141	2025-05-09	120	435	\N	写频线订单完成	2025-05-09 00:00:00	2	t
142	2025-05-09	121	435	\N	40套对讲机客户确认，签订合同	2025-05-09 00:00:00	2	t
143	2025-05-09	136	263	\N	沟通确认签订新一年度的维保合同，我司先准备合同盖章，待客户盖章。	2025-05-09 00:00:00	2	t
144	2025-05-09	136	263	\N	沟通新一年度的维保合同，解答维保合同内明细组成及相关情况。	2025-05-09 00:00:00	2	t
145	2025-05-09	120	435	\N	写频线订单客户已确认下单，签订合同	2025-05-09 00:00:00	2	t
146	2025-05-09	149	459	\N	签订‘上海金融交易广场400M无线对讲系统优化项目 ’的合同。	2025-05-09 00:00:00	2	t
147	2025-05-09	156	260	\N	上海中心里面用的对讲机各型号产品维修部件明细报价。	2025-05-09 00:00:00	2	t
148	2025-05-09	121	435	\N	预采购40套对讲机，与客户沟通目前P8668i防爆供货周期长，建议换GP338D+防爆设备。近期客户安排下单。	2025-05-09 00:00:00	2	t
149	2025-05-09	115	435	\N	因ariba系统内目录缺少GP338D+防爆机器产品，先客户需要采购机器，与采购员沟通新增此型号设备，等审核完成后通知用户下单。	2025-05-09 00:00:00	2	t
150	2025-05-09	120	435	\N	协助基地对讲机写频，客户预采购写频线，客户安排下单。	2025-05-09 00:00:00	2	t
151	2025-05-09	200	365	\N	针对新提供的招标文件，调整好清单报价给到王文，待其确认。项目是采用800M定制化产品，和赵沟通好产品需求，初步对产品成本进行评估报价，待客户明确回复采用我司产品后，再进行定制化处理	2025-05-09 00:00:00	13	t
152	2025-05-09	210	375	\N	汤总他们主是是做无线电监测设备的，他们有些行业的合作伙伴有相关的业务需求，可以尝试合作。	2025-05-09 00:00:00	13	t
153	2025-05-09	176	341	\N	沟通德赛西威项目的情况，给其建议和指导，协助其配合客户投标	2025-05-09 00:00:00	13	t
154	2025-05-09	196	360	\N	和付工沟通货运楼招标文件中的问题，原清单的缺失的设备，付工建议我们先列出来，他们和商务沟通投标策略	2025-05-09 00:00:00	13	t
155	2025-05-09	179	347	\N	和尤总沟通货运楼投标参与的集成商情况，商务投标的策略	2025-05-09 00:00:00	13	t
156	2025-05-09	179	347	\N	和尤总沟通目前合肥机场的最新情况，尤总已推动业主在会议上明确提出系统方案确定过程中需要现场提供设备，搭建平台进行测试，也通知到集成商，尤总了解到集成商的中标价格和竞争对手的报价，和尤总商量好报价策略，和尤总调整报价发给总包，看总包反应	2025-05-09 00:00:00	13	t
157	2025-05-09	174	339	\N	和孟总他们沟通深化方案的问题，有几栋楼本次建设是毛坯，和业主沟通协商后，从本次清单中去掉，采用简单的临时系统，核对好深化的清单给集成商进行确认	2025-05-09 00:00:00	13	t
258	2025-05-09	405	330	\N	烈龙价格跳水，价格竞争优势不足。	2025-05-09 00:00:00	15	t
885	2025-06-13	722	525	\N	此人是业主方，管IT的，客户表示一期跟二期的项目已经在收尾阶段了，维保这块是可以聊的，加了微信后续继续沟通；	2025-06-16 01:10:49.085126	20	t
158	2025-05-09	183	350	\N	和吴老师沟通浦东机场四期的最新情况，现在浦东机场四期项目招标在小木桥路进行，公开招标，甚至不可以推荐品牌，看不清楚后面如何操作。吴老师建议待前面的安防标招好了后，看指挥部是如何操作的，我们的对讲系统招标计划在今年年底和明年年初。	2025-05-09 00:00:00	13	t
159	2025-05-09	250	399	\N	西安泰信大厦项目资金有问题，项目搁置。和邹总介绍我们公司的产品优势，寻找合作点	2025-05-09 00:00:00	13	t
160	2025-05-09	251	400	\N	项目已完成设计，北京顾问放在天馈品牌，悦泰前期参与询价，拜访悦泰采购经理，介绍公司的情况和产品优势，了解项目具体情况	2025-05-09 00:00:00	13	t
161	2025-05-09	201	366	\N	拜访陕西无线电张总，了解西安咸阳机场项目系统试用期的情况，后续安排系统最终联调和软件升级。针对张总他们化工业务的情况进行了深入的沟通和交流，介绍我们行业产品的优势，寻求行业项目的合作。	2025-05-09 00:00:00	13	t
162	2025-05-09	237	392	\N	拜访马经理，了解他们西安分司的情况，他们刚成立的新公司，目前是在做集团的老业务，还没有对讲系统，后面会留意，有项目可以加强合作	2025-05-09 00:00:00	13	t
163	2025-05-09	171	337	\N	拜访沟通今天其公司业务情况，今年他们外资的化工项目特别少，近期中了一个沙特中国塑料原产品项目设计标，交流了项目的基本情况，他和业主关系还不错，回头可以帮我们组织一起和业主交流下	2025-05-09 00:00:00	13	t
164	2025-05-09	209	374	\N	和庹总交流我们在隧道方面的解决方案，让其去了解他们接触 的太仓的隧道的项目情况，帮助从公安那边挖掘下设计院的信息，我们可以对接下	2025-05-09 00:00:00	13	t
165	2025-05-09	231	384	\N	拜访孙月红，了解他们今年的设计项目情况，项目不多，主要是华润的项目，还有之前的项目收尾，商定4月组织下给他们培训一下我们的解决方案和产品，特别是消防的那部分	2025-05-09 00:00:00	13	t
924	2025-06-23	\N	289	309	中标客户转移杨俊杰，他已经完成签约批价。	2025-06-23 07:48:24.125901	15	t
840	2025-06-05	398	323	180	目前系统预算在50万左右，询价了先景、威仕普。目前需要确认绑定品牌，我们优化方案和价格后靠近预算范围。预计下半年进场。	2025-06-09 06:44:32.710314	15	t
166	2025-05-09	231	384	\N	拜访孙总，之前的负责孙方正已离职，现在孙月红负责设计团队，了解他们今年的业务情况，目前的主要是华润和中海的项目，可以合作，约定4月组织给他们团队培训一下	2025-05-09 00:00:00	13	t
167	2025-05-09	204	369	\N	拜访孙总和叶工，和其沟通交通无锡奥体的项目情况，交换意见，了解他们近期的业务情况，嘉兴湖畔项目EPC总指定了分包直接做，拿到联系方式给安排李华伟进行跟进；玉佛寺项目有些搁置，估计 下半年会动	2025-05-09 00:00:00	13	t
168	2025-05-09	182	350	\N	计划四月份开始弱电设计，到时候找陈工配合，了解相关需求	2025-05-09 00:00:00	13	t
169	2025-05-09	207	372	\N	和曹沟通芯恩项目投标情况，他们两家投标均超过业主的预算，业主叫停，内容沟通，如何处理，等待消息	2025-05-09 00:00:00	13	t
170	2025-05-09	209	374	\N	组织技术和庹总会议，沟通浦东机场T3边防系统建设的的想法和建议，给庹总介绍我们的方案和产品特点，提供一些资料供庹总他们参考。推动边防系统产品的合作	2025-05-09 00:00:00	13	t
171	2025-05-09	174	339	\N	和邹飞一起和总包技术、商务沟通康二项目技术方案产品选型问题，图纸深化问题，以及价格问题。经过前期的优化设计，目前价格方面还未达成一致，现场讨论几个区域还需要再调整一下，然后再进行最终的商务谈判。现在已同意同步走产品品牌报审流程	2025-05-09 00:00:00	13	t
172	2025-05-09	174	339	\N	和邹飞一起和总包技术、商务沟通康二项目技术方案产品选型问题，图纸深化问题，以及价格问题。经过前期的优化设计，目前价格方面还未达成一致，现场讨论几个区域还需要再调整一下，然后再进行最终的商务谈判。现在已同意同步走产品品牌报审流程	2025-05-09 00:00:00	13	t
173	2025-05-09	208	373	\N	朱总从仪电出来，和领导一起去了临港集团，给朱总介绍我们公司现在的情况和产品，为以后合作做铺垫	2025-05-09 00:00:00	13	t
174	2025-05-09	207	372	\N	配合竞拓和 业主沟通一期和二期的整合方案	2025-05-09 00:00:00	13	t
175	2025-05-09	192	359	\N	了解合肥机场最新的现场情况，现场已开始做桥架，精装这两个月也会进厂了，整体进度也挺快的，但京航安这边不知道在搞什么，也没有什么实质性的动作。和尤总沟通后，尤总这几天会和业主也沟通下，然后再去了解下京航安的想法	2025-05-09 00:00:00	13	t
176	2025-05-09	239	331	\N	集成商询价，了解项目情况后，安排成都代理商邹娟配合跟进	2025-05-09 00:00:00	13	t
177	2025-05-09	212	377	\N	和应寅沟通他们在浦东机场参与的情况。他们现在已进厂，作为机电总包，现在主要是在预埋管线，他们也想参与后面的弱电包，现在开始介入弱电前期工作，可能后面业主会让他们帮忙调研弱电品牌，他们提前在和有意向的厂商沟通。应寅认为他们拿不到弱电包，大概率是和其他单位合作，弱电调研后续应该是配合华东院一起调研，提前了解起来	2025-05-09 00:00:00	13	t
178	2025-05-09	177	343	\N	和易总了解了他们船泊业务的情况以及他们的船舶业务是如何做的，沟通大家的合作模式，大家的接下来的合作推动计划，\r\n1、针对之前做的船舶项目，做一套更为详细雨的解决方案PPT出来，他们后面好向客户介绍，要附上几个类似的案例；\r\n2、方案出来后和易总他们交流下，易总可以推给他们这边的客户先，然后可以根据项目一起交流，也可以先他们熟悉约广东的船舶设计院进行一下交流和推广；\r\n3、关于产品方面我们后续需要注意的，IP的防护等级一般要满足IP67以上；如果想要长期做要考虑，做船上专用的认证，一船国外的船是做挪威船级社的认证；\r\n4、希望给他们一个船舶行业的授权代理证；\r\n	2025-05-09 00:00:00	13	t
179	2025-05-09	193	359	\N	李小将是成都民航电子广州区域的负责人，通过成都总部介绍认识，了解到目前深圳和广州机场都在扩建，佛山也在建设一个新机场。深圳和广州机场受华为的影响 ，通信系统用的华为LTE系统，扩建部分也没有窄带通信。佛山机场，目前进入初设阶段，通信系统还没有明确LTE还是窄带，民航专家倾向宽带LTE,和李沟通后，近期跟据李的要求，整理一份适合机场宽带共存的PPT介绍和他们交流，他们再向业主汇报	2025-05-09 00:00:00	13	t
986	2025-07-02	102	420	\N	通信费用确认，完成合同及开票。	2025-07-03 09:42:07.646042	2	t
180	2025-05-09	273	416	\N	和分销淳泊以及大鹏鸟核对项目清单，协调批价工作，大鹏鸟的已拿到中标通知，预计3月中下旬批价	2025-05-09 00:00:00	13	t
181	2025-05-09	174	339	\N	和总包沟通深化设计问题，因为项目保密，图纸发不出，须到现场驻深化，协调邹飞安排人驻厂深化设计	2025-05-09 00:00:00	13	t
182	2025-05-09	209	374	\N	庹总苏州公安有个隧道项目，有涉及的公安对讲系统，和庹总交流客户的基本需求，提供给其我们的建议方案和预算，让其跟进	2025-05-09 00:00:00	13	t
183	2025-05-09	200	365	\N	沟通太原机场停车楼项目的方案和产品问题，需要澄清的问题梳理和沟通	2025-05-09 00:00:00	13	t
184	2025-05-09	174	339	\N	和邹飞一起见总包沟通康二项目的价格问题，总价还是碰不拢，业主出面协调，同意按最新的需求进一步优化设计后，再进行一轮商务谈判，双方向中间靠拢一下	2025-05-09 00:00:00	13	t
185	2025-05-09	273	416	\N	和邹飞拜访大鹏鸟的魏总，针对区域的市场合作模式进行了沟通和探讨，通过芯联微项目的配合，魏总也对双方后续业务合作给予了肯定，后续也会更加关注一些区域资源上有价值的项目机会和我们在前期展开合作。芯联微项目目前他们和总包还在议价，基本给他做，现在就软件的价格相差太大，无法达成一致，对方希望软件是给予更大的支持	2025-05-09 00:00:00	13	t
186	2025-05-09	272	416	\N	此项目没钱，业主和总包还磋商砍预算和系统，目前没有进展	2025-05-09 00:00:00	13	t
187	2025-05-09	175	340	\N	和邹飞一起拜访李总，针对李总他们公司的情况进行了解，沟通和探讨后续在成都区域的合作，李总也很认可我们的的模式，也提出自己在电厂的一些资源，认可电厂这几年在西南区域发展不错，他们也在向行业转型，大家可以找一些行业项目展开合作。太保项目年前一直停着，预计3月启动，订货预计在3月底或4月初	2025-05-09 00:00:00	13	t
188	2025-05-09	175	340	\N	大渡河项目，他们和用户是老关系，根据用户的预算他们推了我们的基础产品，预计下半年启动	2025-05-09 00:00:00	13	t
189	2025-05-09	164	334	\N	成都十一院介绍北京建筑设计研究院成都分院的专家，了解成都分院的情况，带邹娟认识，后面会引荐对接智能化部门的相关负责人	2025-05-09 00:00:00	13	t
846	2025-06-10	151	461	\N	新一年度的通信费用客户确认续费，做一份合同给用户。	2025-06-10 05:44:38.171206	2	t
190	2025-05-09	263	407	\N	拜访熊总，汇报去年合作的业务情况，了解他们今年院的动向，同时沟通今年四川区域市场活动的计划以及智能化标准的推动情况，加强合作	2025-05-09 00:00:00	13	t
191	2025-05-09	261	407	\N	拜访李佳莉，西南院成立了国际事业部，李现在负责国际项目的智能化设计，介绍我们公司的情况以及国外业务的情况，寻找国外业务合作的机会	2025-05-09 00:00:00	13	t
192	2025-05-09	264	407	\N	和邹娟一起拜访余工，产品和技术交流，沟通中交建设的商办项目方案	2025-05-09 00:00:00	13	t
193	2025-05-09	266	411	\N	和邹娟一起拜访中铁二院的程工，介绍公司情况，了解他们院里的基本情况以及涉及的业务情况，相关业务有机场、地铁、交通枢纽，后续计划推动技术交流，寻找业务合作机会，他们所目前了解到一直在和中瑞特合作	2025-05-09 00:00:00	13	t
194	2025-05-09	209	374	\N	带杨俊杰一起拜访庹总，了解庹部他们公司的业务和产品，寻找合作点。庹总他们主要做边防和公安，维德上海的核心代理商。上海东站和浦东机场的边防大家达成合作意向，共同推进；同时他们的公安客户有隧道项目，也可以推我们的产品，互利共赢	2025-05-09 00:00:00	13	t
195	2025-05-09	254	401	\N	业主签头让十一想办法建一套临时对讲系统供FAB里面施工指挥和后期设备进厂使用，带代理商去现场勘察、沟通方案和需求	2025-05-09 00:00:00	13	t
196	2025-05-09	183	350	\N	和吴老师沟通项目进展和图纸问题，业主方大领导更换为东航，建筑布局有调整，调整好的图纸预计3月可以好，到时候我们再配深化设计调整。预计我们系统的品牌调研工作在下半年展开，吴老师目前的建议推荐品牌延用卫星厅的，或者推荐上海地标里的几家	2025-05-09 00:00:00	13	t
426	2025-05-09	585	99	\N	品牌确认已经报送业主，目前在配合采购前深化。	2025-05-09 00:00:00	17	t
197	2025-05-09	169	335	\N	和京航安和合肥兴合沟通合肥机场采购谈判事宜，项目延后，京航安近期忙其他项目投标，表示过段时间再进行约谈，希望我们给出最大的支持，价格和付款	2025-05-09 00:00:00	13	t
198	2025-05-09	195	359	\N	余到上海出差，和他聚了一下，了解他们公司今年组织结构的变化和业务的分布情况，他们成立了国际事业部，他后续主要负责国际机场和港口业务，这次到上海出差，主要就是和华东院联合投一个沙特的港口项目，待后续中标后沟通如何配合的事宜	2025-05-09 00:00:00	13	t
199	2025-05-09	253	401	\N	和施君沟通康二项目的设计优化问题，同意调整公寓部分的点位，F3部分的调整方案需和业主进一步确认	2025-05-09 00:00:00	13	t
200	2025-05-09	174	339	\N	和代理商一起与康二总包沟通优化后项目方案和价格，双方价格达不成一致，还需进一步商谈	2025-05-09 00:00:00	13	t
201	2025-05-09	194	359	\N	和叶老师沟通南昌机场的进展和情况，配合其完成GTC的设计	2025-05-09 00:00:00	13	t
202	2025-05-09	253	401	\N	重庆芯联微内部清查结束，确定你重庆赛迪中标	2025-05-09 00:00:00	13	t
203	2025-05-09	273	416	\N	和重庆大鹏鸟沟通重庆芯联微项目的中标情况，协调成都福淳配合	2025-05-09 00:00:00	13	t
204	2025-05-09	176	341	\N	沟通福田TOD的项目进展，集成商招标清单有变化，协调其和设计院、总包沟通清单变更问题。	2025-05-09 00:00:00	13	t
205	2025-05-09	187	352	\N	向业主汇报目前和集成商沟通的情况，价格相差太大，暂时僵持着，安排技术人员去现场复核图纸设计，看看优化空间	2025-05-09 00:00:00	13	t
206	2025-05-09	272	416	\N	大鹏鸟谭超洋反馈，总包这边现在有些问题，预算给的很低，分包可能会放弃	2025-05-09 00:00:00	13	t
207	2025-05-09	176	341	\N	邹娟配合的总包未中标	2025-05-09 00:00:00	13	t
929	2025-06-25	\N	77	209	和设计院张彦沟通，用户那边明确要增加车台，信道机和对讲机指定用摩托罗拉品牌，进行方案的报价调整 	2025-06-25 04:42:56.981942	13	t
208	2025-05-09	235	390	\N	和集成商沟通协商中兴高达部分产品单独的付款方式，重新调整合同和价进行协商	2025-05-09 00:00:00	13	t
209	2025-05-09	179	347	\N	京航安已进厂，有了业主和设计院多方的压力，京航安开始愿意和代理商合肥兴和商谈价格，但目前要求的价格很悬殊，双方还是僵持着	2025-05-09 00:00:00	13	t
210	2025-05-09	206	371	\N	内部已确定邹飞中标，邹飞已在做进厂前的准备工作，合同预计10月底 或11月初确定	2025-05-09 00:00:00	13	t
211	2025-05-09	249	398	\N	代理商已和集成商在谈判，第三方产品集成商打算自行采购，预计10月下旬签约	2025-05-09 00:00:00	13	t
212	2025-05-09	233	387	\N	项目资金有些问题，项目延后到2025年启动	2025-05-09 00:00:00	13	t
213	2025-05-09	175	340	\N	代理商反馈资料报审已基本没有问题，10月推动商务谈判，10月份计划和分销商一起去成都，推动和发展其为新的渠道商	2025-05-09 00:00:00	13	t
214	2025-05-09	170	336	\N	邹飞支持北京朗易通低价中标	2025-05-09 00:00:00	13	t
215	2025-05-09	263	407	\N	代理商反馈交子业主在缩减各系统相关预算，各系统品牌要求采用业主原来库里的品牌，相关方案和预算待业主确定后再做调整	2025-05-09 00:00:00	13	t
216	2025-05-09	242	243	\N	和孙晓文沟通设计方案问题，配合其调整设计方案和清单	2025-05-09 00:00:00	13	t
217	2025-05-09	187	352	\N	项目已开始招标，了解相关集成商参与，安排杨俊杰对接跟进	2025-05-09 00:00:00	13	t
218	2025-05-09	233	387	\N	项目没有品牌，协调邹娟配合集成报价，说服集成采用和源产品投标	2025-05-09 00:00:00	13	t
219	2025-05-09	235	390	\N	沟通线缆型号调整，价格分摊问题	2025-05-09 00:00:00	13	t
220	2025-05-09	264	407	\N	西南院的EPC项目，代理商福淳配合西南院核准图纸问题，出具相应清单和推荐相关品牌	2025-05-09 00:00:00	13	t
221	2025-05-09	175	340	\N	协调分销商提供相关报审资料	2025-05-09 00:00:00	13	t
892	2025-06-18	722	525	\N	联系对方设备的问题可以送修，客户表示OK并且近期会送来，等检测了再说后续的事；	2025-06-19 03:12:56.785768	20	t
1	2025-05-09	38	11	\N	该部分对讲机已启动批价流程	2025-05-09 00:00:00	16	t
2	2025-05-09	70	6	\N	该公司已中标，目前正在询价。和源品牌在天馈品牌范围内，与项目负责人沟通建议主机更换品牌。	2025-05-09 00:00:00	16	t
3	2025-05-09	60	10	\N	项目目前正处于前期方案清单配置中，土建已在施工中，预计三季度进行智能化招标，项目计划明年一季度结束。	2025-05-09 00:00:00	16	t
1616	2025-10-09	77	21	289	配合，浙江华是科技	2025-10-09 07:05:18.023317	16	t
86	2025-05-09	58	9	\N	配合完成方案配置报价	2025-05-09 00:00:00	16	t
4	2025-05-09	52	92	\N	沟通了该项目的推进情况，目前该项目已从原落地合肥变更为福州；同时沟通了目前其负责的贵州项目。	2025-05-09 00:00:00	16	t
5	2025-05-09	40	8	\N	目前该项目的43#楼正在招标中，已有至少2家公司与我们进行了联系；项目投标截止时间为5月6日。	2025-05-09 00:00:00	16	t
6	2025-05-09	88	85	\N	沟通项目实施情况，协助经销商沟通了合同回款事宜。	2025-05-09 00:00:00	16	t
7	2025-05-09	88	85	\N	沟通了该地块系统调整问题，经沟通增加了软件平台管理系统；后续需协助进行批价审价。	2025-05-09 00:00:00	16	t
8	2025-05-09	60	10	\N	该部分对讲机已返回工厂调整功率。	2025-05-09 00:00:00	16	t
9	2025-05-09	38	11	\N	沟通了前期项目落实推进的情况及目前跟踪项目的情况。	2025-05-09 00:00:00	16	t
10	2025-05-09	25	165	\N	拜访了项目部吴总，沟通了后续项目实施中的问题；包括软件部署等问题。	2025-05-09 00:00:00	16	t
11	2025-05-09	61	82	\N	配合集成商完成招标清单报价	2025-05-09 00:00:00	16	t
12	2025-05-09	81	12	\N	配合集成商完成询价工作	2025-05-09 00:00:00	16	t
13	2025-05-09	77	21	\N	指导代理商技术进行项目图纸深化。	2025-05-09 00:00:00	16	t
14	2025-05-09	20	30	\N	沟通项目进展，目前刚刚进场施工，主要集中在桥架管线，系统品牌基本计划在5月中旬确定。目前苏州2家产品商已和他们有所接触；苏州中瀚（孙建忠）已报出非常低的价格；但瀚远目前没有采纳中瀚。	2025-05-09 00:00:00	16	t
15	2025-05-09	29	63	\N	拜访了邦耀公司的总经理，沟通了苏州当前的项目机会，特别商讨了苏州桑田岛实验室的项目合作，基本达成一致意见：通过技术方案能否实现功能（进行软件功能展示）将苏州中瀚排除出局或迫使其提高实现成本；因为目前主机品牌是摩托。海能达、建伍，因建伍无法实现巡更功能，我们希望争取拿到摩托代理授权；邦耀拿到海能达的授权；从而形成优势。	2025-05-09 00:00:00	16	t
16	2025-05-09	97	21	\N	约见拜访项目机电总包方项目经理（总），沟通项目合作事宜。目前海能达通过南京广电公司在参与该项目，现在争取除350M公安系统外的系统。	2025-05-09 00:00:00	16	t
17	2025-05-09	77	21	\N	督促支付该项目软件订单款项	2025-05-09 00:00:00	16	t
18	2025-05-09	81	12	\N	沟通项目目前推进情况，配合准备相关资料；项目负责人透露目前已有海能达代理商通过相关人员介绍在接触项目部。	2025-05-09 00:00:00	16	t
19	2025-05-09	77	21	\N	督促代理商完成软件项目的订单签署机付款。	2025-05-09 00:00:00	16	t
20	2025-05-09	77	21	\N	与相关集成商沟通，项目目前具体情况	2025-05-09 00:00:00	16	t
21	2025-05-09	10	89	\N	与设计工程师沟通推荐品牌事宜，目前推荐品牌如下：\r\n信道机和对讲机：摩托罗拉，海能达，和源通信；\r\n信号中继（近、远端直放站）及天馈（天线、功分耦合器）分布：福玛通信、淳泊、和源通信；\r\n线缆：中天、亨鑫、德通；	2025-05-09 00:00:00	16	t
22	2025-05-09	40	8	\N	沟通项目系统技术文件的细节要求	2025-05-09 00:00:00	16	t
23	2025-05-09	54	20	\N	沟通系统设计的技术问题，后续会有项目合作	2025-05-09 00:00:00	16	t
24	2025-05-09	77	21	\N	指导、配合代理商完成项目的方案设计及清单配置。	2025-05-09 00:00:00	16	t
25	2025-05-09	59	89	\N	介绍公司相关产品及系统架构，后期会有项目设计需配合。	2025-05-09 00:00:00	16	t
1076	2025-07-22	151	461	\N	通信费用合同签订完成，开票。	2025-07-22 02:45:17.069665	2	t
26	2025-05-09	60	10	\N	经过多方不懈努力，多轮沟通目前基本确定该项目中普通对讲机将采用和源对讲机。	2025-05-09 00:00:00	16	t
27	2025-05-09	77	21	\N	启动并与公司完成了项目软件的直接订单工作	2025-05-09 00:00:00	16	t
28	2025-05-09	77	21	\N	与集成商做了初步沟通	2025-05-09 00:00:00	16	t
29	2025-05-09	77	21	\N	补充了相关品牌报审资料	2025-05-09 00:00:00	16	t
30	2025-05-09	77	21	\N	完成批价流程	2025-05-09 00:00:00	16	t
31	2025-05-09	77	21	\N	完成批价流程	2025-05-09 00:00:00	16	t
32	2025-05-09	97	21	\N	配合中间人推动品牌入围事宜，提交了相关入围资料。目前总包方委托了："上海延和信息技术有限公司"在针对本项目初步配置清单进行询价工作。	2025-05-09 00:00:00	16	t
33	2025-05-09	77	21	\N	完成批价申请	2025-05-09 00:00:00	16	t
34	2025-05-09	97	21	\N	因项目出现了公安350MHz系统的产品供应商海能达（公安指定），项目出现了不小变数；陈总拜访了中铁十四局项目部上级相关领导，沟通了项目后续推动事宜。	2025-05-09 00:00:00	16	t
35	2025-05-09	97	21	\N	与陈总沟通了无锡奥体项目先行申请批价事宜，基本双方达成一致意见。	2025-05-09 00:00:00	16	t
36	2025-05-09	77	21	\N	完成申请批价工作；	2025-05-09 00:00:00	16	t
37	2025-05-09	40	8	\N	沟通了该项目目前正在进行的43号地块的招投标准备工作，后续我们参与的修改技术文件如总包方反馈，顾问将通知和配合我们。	2025-05-09 00:00:00	16	t
38	2025-05-09	81	12	\N	沟通项目目前进展，据了解后续他们还会参与过江管廊建设，双方沟通了管廊初步解决方案。并且介绍了目前入围隧道项目的厂家短名单：和源、威升，衡盈；	2025-05-09 00:00:00	16	t
39	2025-05-09	44	30	\N	前期项目品牌已入围，目前项目采用投标中标后上报品牌，业主确认方式进行；目前项目具体负责人未确定，待后续公司确认后（大约4月中旬），会将相关信息告知我们。该项目即为：“苏州工业园区银科产业投资有限公司桑田科学岛科创中心（DK20230518地块）项目”	2025-05-09 00:00:00	16	t
40	2025-05-09	93	81	\N	前期项目品牌已入围，目前项目采用投标中标后上报品牌，业主确认方式进行；后续正在跟进中。	2025-05-09 00:00:00	16	t
41	2025-05-09	96	76	\N	更新部分项目信息数据	2025-05-09 00:00:00	16	t
42	2025-05-09	25	165	\N	沟通项目后续实施进展，	2025-05-09 00:00:00	16	t
43	2025-05-09	77	21	\N	代理商已提交批价	2025-05-09 00:00:00	16	t
44	2025-05-09	69	79	\N	项目因投资资金缩减，智能化系统减少投资，无线对讲系统由原来专网系统取消，改为后期物业自配。	2025-05-09 00:00:00	16	t
45	2025-05-09	72	13	\N	目前该项目集成商已中标，主机品牌已确定范围，天馈系统未确定品牌，正在与中标方商议。	2025-05-09 00:00:00	16	t
46	2025-05-09	10	89	\N	完成图纸修改，采用光纤架构，增加软件平台；	2025-05-09 00:00:00	16	t
47	2025-05-09	14	89	\N	沟通后续交流事宜	2025-05-09 00:00:00	16	t
1625	2025-10-13	857	623	\N	定本周四去看现场；	2025-10-13 01:39:52.508959	20	t
48	2025-05-09	96	76	\N	请戴经理对部分项目进行数据更新	2025-05-09 00:00:00	16	t
49	2025-05-09	5	44	\N	第二轮报价，后续分包方会参与采购和商务谈判。	2025-05-09 00:00:00	16	t
50	2025-05-09	77	21	\N	目前代理商已与集成商签订了合同，签约价为20.2248万元；代理商本周已启动批价申请流程。	2025-05-09 00:00:00	16	t
51	2025-05-09	96	76	\N	对筛选出的数据进行核实	2025-05-09 00:00:00	16	t
1056	2025-07-18	\N	537	643	配合集成商编写述标文档	2025-07-18 02:10:58.885549	16	t
52	2025-05-09	10	89	\N	配合设计方修改系统方案，由原室外大功率天线覆盖方式，改为室内小功率天线覆盖方式；采用全光纤近远端架构，增加管理平台。	2025-05-09 00:00:00	16	t
53	2025-05-09	31	80	\N	根据中标方给出的招标清单，进行了第一轮报价。	2025-05-09 00:00:00	16	t
54	2025-05-09	81	12	\N	项目部拜访了郭总，沟通了项目目前进展情况，及后续招标事宜：建议了后期采购招标的品牌。	2025-05-09 00:00:00	16	t
55	2025-05-09	40	8	\N	本周通过微信沟通了一下雄安国贸中心的品牌调整事宜，建议增加我们可控的品牌。	2025-05-09 00:00:00	16	t
56	2025-05-09	38	11	\N	沟通了目前合作的项目推进情况，（1）首钢1612产业园一标段及二标段的供货、实施及产品付款计划；（2）中芯国际龙舟二期项目的情况；（3）顺义会展项目的情况，因资金问题，项目整体进度推迟，沟通了后续供货事宜。	2025-05-09 00:00:00	16	t
57	2025-05-09	72	13	\N	介绍了公司情况，对公司近年研发的信道机、软件平台、馈电型室分等产品做了系统性介绍，沟通了近期参与的项目；讨论了后期双方合作的机会及后续双方团队的技术交流事宜。	2025-05-09 00:00:00	16	t
58	2025-05-09	40	8	\N	与田工详细介绍了公司的新产品及新技术，包括：云平台、基站、一体化分合路平台、MA12天线等产品；初步沟通了下次两公司之间大范围技术交流活动的意向。近期田工参与的项目情况，落实了雄安与中海苏州项目配合参与事宜。	2025-05-09 00:00:00	16	t
59	2025-05-09	73	55	\N	与目前项目意向性中标方项目负责人会面，沟通了后续配合事宜及产品品牌、选型事宜。	2025-05-09 00:00:00	16	t
60	2025-05-09	25	165	\N	拜访项目负责人，了解了项目最新进展。其中784地块已安装完毕（独立系统），774地块计划3月底前需完成设备安装（系统主机房）；779地块计划6月底完成。沟通了后续项目配合事宜。	2025-05-09 00:00:00	16	t
61	2025-05-09	8	60	\N	处于暂停状态，业主在走内部流程	2025-05-09 00:00:00	16	t
62	2025-05-09	69	79	\N	该项目因业主方投资资金压缩，计划减少后续系统建设项目（弱电智能化），目前还未最后确定最终方案。预计2025年3月底可确定招标方案。	2025-05-09 00:00:00	16	t
63	2025-05-09	68	20	\N	土建单位招标2024年11月完成，目前智能化暂未招标。	2025-05-09 00:00:00	16	t
64	2025-05-09	71	50	\N	项目大楼主体2024年12月封顶，智能化暂未招标。	2025-05-09 00:00:00	16	t
65	2025-05-09	68	20	\N	项目主体施工已进场，弱电分包未定。项目计划2027年1季度完工。	2025-05-09 00:00:00	16	t
66	2025-05-09	65	62	\N	了解今年在参与的设计项目情况，目前主要是南京的道路改造项目，暂未涉及到隧道项目。专委会筹建工作也在推进中，可能会在二季度召开会议。	2025-05-09 00:00:00	16	t
899	2025-06-20	677	486	\N	与产品设计人员沟通PPT的细节，修改取卡机的图片，修改终端和发卡机的扩展功能描述，修改部分软件功能的描述；下周会把定位产品PPT介绍和南方无线对讲系统维护方案一起发给业主，和业主进一步沟通；	2025-06-20 02:11:48.339981	7	t
904	2025-06-19	426	435	\N	与IOBC区域负责人沟通下周MCF承包商区域无线对讲系统施工交底事宜，沟通下半年区域需求及预算事宜；	2025-06-20 02:29:29.96523	7	t
67	2025-05-09	55	25	\N	介绍了公司及产品，庞工表示：目前项目还在设计阶段，让我们可以多和设计院沟通，他们近阶段还没有确定品牌。品牌确定需要多部门参与讨论。	2025-05-09 00:00:00	16	t
68	2025-05-09	22	44	\N	项目进入品牌资料报审阶段，已提供和源相关产品资料；计划二季度采购。	2025-05-09 00:00:00	16	t
69	2025-05-09	81	12	\N	与项目负责人做了初步沟通，已拿到项目招标图纸及清单。项目计划2025年2季度末进入设备采购阶段。	2025-05-09 00:00:00	16	t
70	2025-05-09	10	89	\N	介绍了公司产品，沟通了项目初步设计中的问题，商讨了后续设计修改的思路。	2025-05-09 00:00:00	16	t
71	2025-05-09	77	21	\N	梳理沟通了2025年跟踪项目的清单，确定了1季度落地项目批价的事宜。	2025-05-09 00:00:00	16	t
72	2025-05-09	28	69	\N	根据项目一期采用的设备型号，更新了配置清单。	2025-05-09 00:00:00	16	t
73	2025-05-09	31	80	\N	根据沟通情况及系统图对配置清单做了修改调整	2025-05-09 00:00:00	16	t
74	2025-05-09	28	69	\N	天津会展项目，本次只是北区厨房区域改造，整个体量为1-4号厨房区域，也就是北区展厅的连廊区域部分。该区域的信号是沿用原系统的信号，接入原有系统，清单已根据一期使用的数字产品进行了修改。\r\n目前项目还没有交到代理商手中，只是和郭总商量后，觉得体量较小及后期需花费的精力综合考虑，计划将该项目交到天津代理商进行跟踪实施。	2025-05-09 00:00:00	16	t
75	2025-05-09	31	80	\N	今年与集成商后续执行负责人进行了沟通，该项目目前计划部分系统会整体打包进行专项分包，但目前未定哪些系统会分包给分包单位。\r\n目前主要存在的问题是150MHz频段的部分产品成本，需要供应链尽快核算。如信道机、双工器、远端机、天线等。	2025-05-09 00:00:00	16	t
76	2025-05-09	31	80	\N	根据春节前与中标方该项目市场负责人见面沟通情况，目前项目中标公式已结束，处于双方合同商谈阶段；项目部正在组建中，计划现场项目部与2月中旬进场。	2025-05-09 00:00:00	16	t
77	2025-05-09	28	69	\N	配合集成商完成总包方要求的项目招标前的方案完善及预算	2025-05-09 00:00:00	16	t
78	2025-05-09	31	80	\N	目前已进入签约商谈	2025-05-09 00:00:00	16	t
79	2025-05-09	77	21	\N	目前已确定敦力为中标供货方	2025-05-09 00:00:00	16	t
80	2025-05-09	97	21	\N	报价已提交合作伙伴	2025-05-09 00:00:00	16	t
81	2025-05-09	97	21	\N	方案已提交合作伙伴	2025-05-09 00:00:00	16	t
82	2025-05-09	77	21	\N	目前集成商已完成与业主签约，年后进场施工。	2025-05-09 00:00:00	16	t
83	2025-05-09	77	21	\N	配合集成商未中标。	2025-05-09 00:00:00	16	t
84	2025-05-09	77	21	\N	中标集成商已落实，目前集成商正在准备与业主商务谈判中。	2025-05-09 00:00:00	16	t
85	2025-05-09	66	70	\N	完成初步方案配置	2025-05-09 00:00:00	16	t
87	2025-05-09	77	21	\N	与项目关系人对项目进行了沟通，初步配置了项目清单。	2025-05-09 00:00:00	16	t
88	2025-05-09	97	21	\N	与项目关系人进行了2轮沟通，目前可以确定后期在国内采购，需要在项目地提供实施服务及申请当地频率。	2025-05-09 00:00:00	16	t
89	2025-05-09	77	21	\N	本周进行了新一轮沟通，目前侨讯的价格优势比较明显，我们正在努力沟通工作中，主要是技术层面。	2025-05-09 00:00:00	16	t
90	2025-05-09	77	21	\N	本周拿到了项目的系统图，设计方：上海同济院（项目负责人：王翔）；从系统图架构看，设计院设计较为简单。	2025-05-09 00:00:00	16	t
91	2025-05-09	12	83	\N	配合集成商完成投标清单报价	2025-05-09 00:00:00	16	t
92	2025-05-09	77	21	\N	与参与该项目的集成商初步沟通	2025-05-09 00:00:00	16	t
93	2025-05-09	77	21	\N	目前项目已进入招投标阶段中	2025-05-09 00:00:00	16	t
94	2025-05-09	21	75	\N	集成商未中标	2025-05-09 00:00:00	16	t
95	2025-05-09	77	21	\N	集成商未中标	2025-05-09 00:00:00	16	t
96	2025-05-09	77	21	\N	集成商放弃后期参与	2025-05-09 00:00:00	16	t
97	2025-05-09	77	21	\N	配合集成商投标	2025-05-09 00:00:00	16	t
98	2025-05-09	62	77	\N	因业主资金问题，项目搁置。	2025-05-09 00:00:00	16	t
99	2025-05-09	77	21	\N	配合集成商完成投标工作	2025-05-09 00:00:00	16	t
222	2025-05-09	181	349	\N	EPC项目，于总他们和总包关系比较好，尝试推和源的产品，配合提交资料，于总去推动加入和源的品牌	2025-05-09 00:00:00	13	t
100	2025-05-09	22	44	\N	经与集成总包单位确认，一期上报入围品牌，主机及终端：海能达、和源通信、712；天馈：和源通信、联航迅达、侨讯；目前最大竞争对手 ，海能达+侨讯（分包施工单位推荐 ）	2025-05-09 00:00:00	16	t
101	2025-05-09	12	83	\N	参与该项目投标报价	2025-05-09 00:00:00	16	t
102	2025-05-09	85	64	\N	调整一轮新报价	2025-05-09 00:00:00	16	t
103	2025-05-09	11	9	\N	经进一步沟通，他们已放弃该项目继续跟进。	2025-05-09 00:00:00	16	t
104	2025-05-09	21	75	\N	本项目该公司未中标；已与新中标单位取得联系。	2025-05-09 00:00:00	16	t
105	2025-05-09	63	29	\N	未中标	2025-05-09 00:00:00	16	t
106	2025-05-09	88	85	\N	已完成设备供应商招标工作，确定中标单位。	2025-05-09 00:00:00	16	t
107	2025-05-09	38	11	\N	已向总包方提交会展解决方案的PPT介绍	2025-05-09 00:00:00	16	t
108	2025-05-09	77	21	\N	配合集成商做好招标前配置清单及技术文件	2025-05-09 00:00:00	16	t
109	2025-05-09	85	64	\N	拜访项目中标方项目经理及采购部经理，沟通项目目前情况。该项目目前处于品牌报审阶段；中标方前期是由苏州两家当地品牌供应商配合的；经沟通目前已同意我方对该项目参与后续报价。	2025-05-09 00:00:00	16	t
110	2025-05-09	38	11	\N	经销商与目前进行 项目实施的集成商进行初步接触，了解项目后续施工范围。 	2025-05-09 00:00:00	16	t
111	2025-05-09	38	11	\N	经销商与目前负责该项目的总包方进行初步沟通，介绍公司在会展项目上的案例等情况。	2025-05-09 00:00:00	16	t
112	2025-05-09	99	34	\N	配合集成商完成初步方案设计	2025-05-09 00:00:00	16	t
113	2025-05-09	33	43	\N	代理商敦力（南京）科技有限公司 配合集成商完成了初步设计和清单报价。	2025-05-09 00:00:00	16	t
114	2025-05-09	33	43	\N	配合集成商做初步设计	2025-05-09 00:00:00	16	t
115	2025-05-09	39	41	\N	配合集成商做初步设计	2025-05-09 00:00:00	16	t
116	2025-05-09	30	51	\N	配合参与项目投标	2025-05-09 00:00:00	16	t
117	2025-05-09	22	44	\N	与技术总沟通推荐品牌事宜，主机对讲机：摩托罗拉、海能达、和源；天馈：和源、淳泊、联航迅达；	2025-05-09 00:00:00	16	t
118	2025-05-09	60	10	\N	沟通项目合同落地事宜。	2025-05-09 00:00:00	16	t
945	2025-06-25	\N	251	\N	跟客户约定下周三拜访；	2025-06-25 09:09:45.004799	20	t
223	2025-05-09	400	325	\N	预计5月签约合同，推动现场采购下单，博物馆有部分天线取消，价格层面一直在谈判让我们给与支持，虽然品牌用了我们但是价格相差中标成本价格有15个点的区间。	2025-05-09 00:00:00	15	t
224	2025-05-09	396	323	\N	配合对方设计金华双龙凯悦酒店方案和品牌植入，后续跟进招标情况后续参与。	2025-05-09 00:00:00	15	t
225	2025-05-09	372	311	\N	龙旗总部大楼对方中标，预计5月左右进场，对方投标用了科立讯，目前沟通商务价格情况。	2025-05-09 00:00:00	15	t
226	2025-05-09	362	226	\N	目前人工智能岛项目预计11月份进场穿线，深化配合完成图纸报审。手上配合参与张家浜项目投标。	2025-05-09 00:00:00	15	t
227	2025-05-09	367	310	\N	目前浦兴社区嘉里巨峰中心对方中标，预计7月份左右进场，目前品牌内和源烈龙中元进行商务谈判，代理商配合跟进中。预计5月份确认品牌报审。	2025-05-09 00:00:00	15	t
228	2025-05-09	375	311	\N	代理商配合云赛投标，品牌和源入围，已知云赛、朗捷通、霍尼、延华参与投标，安排代理商配合接触。	2025-05-09 00:00:00	15	t
229	2025-05-09	388	316	\N	对方以小区为主，但是认识的业主资源较多，下周介绍鲁能业主杭州国际中心项目沟通。	2025-05-09 00:00:00	15	t
230	2025-05-09	395	322	\N	对方主要做生物医药项目，原来对我们系统不了解，后续跟进组织技术交流。	2025-05-09 00:00:00	15	t
231	2025-05-09	415	165	\N	目前智能化预算报1.2亿，业主预算给了5800万，方案后续可能调整，后续跟进情况。	2025-05-09 00:00:00	15	t
232	2025-05-09	311	283	\N	代理商瑞康带我们现场沟通客户负责人，对方选用了程联品牌，要求我们给他们深化下配置重新报价，后续跟进商务情况。	2025-05-09 00:00:00	15	t
233	2025-05-09	309	280	\N	配合采购做品牌入库资料审核，预计下个月招标，目前了解下来原来一期的品牌和广州品牌，共计三家入围。后续拜访业主沟通定标打分细节，能否操作。	2025-05-09 00:00:00	15	t
234	2025-05-09	367	310	\N	代理商带我们拜访源和浦兴社区对方中标，品牌入围和源烈龙中原，预计6月份中标。后续跟进客户价格谈判。	2025-05-09 00:00:00	15	t
235	2025-05-09	363	307	\N	预计6月份进场穿线，目前代理商推动配合报审品牌，后续跟进商务流程和报审结果。	2025-05-09 00:00:00	15	t
236	2025-05-09	312	285	\N	商业部分开始配合设计方案，业主联系人拿到跟进业主这边，促成合作，预计下半年招标。	2025-05-09 00:00:00	15	t
237	2025-05-09	394	321	\N	拜访介绍和源产品，目前手上商业项目较少，有个交控集团金融大楼项目在设计，省院在负责，无线对讲系统这块不确定当时有没有设计，后续跟进省院。	2025-05-09 00:00:00	15	t
238	2025-05-09	308	279	\N	介绍和源产品，对方主要以商业住宅居多，原来品牌库只规定了对讲机品牌。后续跟进入库品牌事宜。	2025-05-09 00:00:00	15	t
239	2025-05-09	399	324	\N	主要设计石化项目，目前遇到我们系统不多，加之认识不足。潜在项目还是有的，后续组织技术交流。	2025-05-09 00:00:00	15	t
240	2025-05-09	310	124	\N	沟通杭州西站南广场共7个标段品牌，目前1标不在内。后续二标沟通帮忙植入品牌，预计6月份左右招标。后续跟进确认植入情况。	2025-05-09 00:00:00	15	t
241	2025-05-09	332	205	\N	据淳泊反馈凯通中标结果刚公示，代理商配合集成商深化。预计进场在下半年。后续安排确认进场时间和商务事宜。	2025-05-09 00:00:00	15	t
242	2025-05-09	306	278	\N	这个项目暂时停工搁置未招标，目前手上有个绍兴安塔拉酒店在设计，后续跟进配合。	2025-05-09 00:00:00	15	t
243	2025-05-09	301	276	\N	代理商带我们拜访现场，对方刚进场预计穿线在7月份左右，目前里面有苏州威升报价竞争，二标主设备已经锁定和源，后续安排代理商跟进金鼎采购负责人沟通商务情况。	2025-05-09 00:00:00	15	t
244	2025-05-09	311	283	\N	目前宝通中标后价格太低准备退场，上海众铭接手还不确定是否实施，配合报价后续跟进现场分包情况。	2025-05-09 00:00:00	15	t
245	2025-05-09	309	280	\N	经过拜访介绍和源，后续进入业主品牌库，配合业主出预算清单。前期没有设计对讲属于后补，由业主直接招标，预计在4月份左右招标。	2025-05-09 00:00:00	15	t
246	2025-05-09	398	323	\N	目前嘉兴二院投标结果公示4家，由于院方内部问题，最终结果还没出。代理商配合投标客户安排定期跟进消息。	2025-05-09 00:00:00	15	t
247	2025-05-09	397	323	\N	目前刚开始设计图纸方案，配合省院刘总设计方案植入。预计下半年12月左右招标。手上还有较多项目，后续需要加强与此人关系。	2025-05-09 00:00:00	15	t
248	2025-05-09	400	325	\N	目前配合深化图纸完成交底，报审资料完成。预计在3月中旬现场会提交采购单给到公司，后续采购及时跟进商务谈判。	2025-05-09 00:00:00	15	t
249	2025-05-09	401	326	\N	拜访机电经理郑总，介绍和源产品。目前他们业务轻资产较多，重资产属于自己投资控制项目，原来用公网比较多。后续他们建立品牌库继续跟进和源品牌入库。	2025-05-09 00:00:00	15	t
250	2025-05-09	310	124	\N	北广场项目配合万安设计院设计施工图，沟通设计方案计划植入和源馈电天线。预计5月份确认施工图，招标时间预计在26年初。后续持续跟进设计院和业主方案采用情况。	2025-05-09 00:00:00	15	t
251	2025-05-09	282	267	\N	徐州德基目前由于资金问题停工。手上的最新接入项目杭州国际广场、苏州湾洲际酒店、浙江农夫山泉酒店，安吉鸬鸟希尔顿后续到节点配合设计植入。	2025-05-09 00:00:00	15	t
252	2025-05-09	286	270	\N	顾问反馈衢州希尔顿项目为EPC，业主需要造价确认，主设备价格还没定价。预计在5-6月份结束定价，设备进场。目前手上漳州希尔顿、阿克苏希尔顿刚接的项目。	2025-05-09 00:00:00	15	t
253	2025-05-09	312	285	\N	目前公寓部分方案已经配合设计完成，商业和酒店预计年中开始设计。年前与业主做过品牌介绍，后续3月份跟进业主品牌和方案合作。	2025-05-09 00:00:00	15	t
254	2025-05-09	290	273	\N	一期我们21年建设的系统，目前属于二期扩建新增区域，代理商前期配合客户投标，已经中标。同代理商跟总包沟通介绍了和源防爆天线产品，锁定和源。代理商在配合深化图纸，预计2月底3月初可谈判商务进场。	2025-05-09 00:00:00	15	t
255	2025-05-09	380	314	\N	据代理商反馈年前因为总包合同一直没有进场，目前现场在做管道预埋，已经在配合深化报验工作，预计6月份启动穿线。安排代理商定期跟进现场进度及时确认商务合同。	2025-05-09 00:00:00	15	t
256	2025-05-09	385	314	\N	现场年前报验已经通过，深化已经配合，预计4-5月份左右进场开始穿线。定期安排代理商跟进确认合约和进度。	2025-05-09 00:00:00	15	t
259	2025-05-09	456	422	\N	与业主方负责人沟通中芯国际今年常规射频直放站更新事宜，听取业主方想法和意见；	2025-05-09 00:00:00	7	t
260	2025-05-09	449	258	\N	与振华重工采购部门领导沟通申请企业供应商资质的事宜，并且寻求和源对讲机进入振华产品库的可能性	2025-05-09 00:00:00	7	t
261	2025-05-09	451	259	\N	与业主沟通消防用350兆系统设备检测后替换方案与执行预算；另外业主方提出能否以节能减排，降低环境危害方面做系统更新功能提升的改造方案；	2025-05-09 00:00:00	7	t
262	2025-05-09	446	255	\N	上海咸力环境设备有限公司是一家外贸公司，经营外贸产品，主要涉及绿色环境净水/电子产品等业务，与其总经理熟悉，目前有类似无人机，GPS产品，电脑产品，通信产品销往东南亚的需求，与对方沟通并了解需求，尝试提供中国市场产品和有可能的无线对讲产品；	2025-05-09 00:00:00	7	t
263	2025-05-09	429	435	\N	与科思创E188区域负责人沟通，了解刚刚建设完成E188区域无线对讲系统的情况，了解区域后续可能出现的产品，区域覆盖的需求；	2025-05-09 00:00:00	7	t
264	2025-05-09	439	470	\N	与中芯国际深圳ERC负责人沟通和录音相关技术问题，业主方希望录音可以在现场两个不同的区域调取记录文件；	2025-05-09 00:00:00	7	t
265	2025-05-09	426	435	\N	与科思创IOBC区域负责人沟通2025年区域设备数字化事宜，了解系统使用情况，IOBC区域目前的设备数字化比例为57%，希望推动下半年进一步推进系统设备数字化工作；	2025-05-09 00:00:00	7	t
266	2025-05-09	439	470	\N	与业主方沟通关于系统录音功能的需求，为深圳中芯国际已建成无线对讲系统提供录音功能方案和预算，业主已认可并且本周五会向深圳中芯内部提出采购需求，下周会安排商务对方案进行产品清单报价；	2025-05-09 00:00:00	7	t
267	2025-05-09	439	470	\N	与深圳中芯国际ERC负责人沟通改造方案与2025系统维护测试两个方案的最终确认，对方根据方案报价向采购部门正式提出采购申请，预算通过后制作PO单；	2025-05-09 00:00:00	7	t
268	2025-05-09	439	470	\N	提供方案和三个区域的大致点位图给业主方，并且说明方案的执行和需要注意的地方，业主方根据方案上报需求	2025-05-09 00:00:00	7	t
269	2025-05-09	458	470	\N	与ERC负责人联系沟通2025年深圳中芯国际无线对讲系统定期系统排查合约事宜；	2025-05-09 00:00:00	7	t
847	2025-06-10	143	453	\N	7月份通信费到期，客户确认续费，开票给用户。	2025-06-10 05:45:32.452996	2	t
270	2025-05-09	451	259	\N	与上海中心大厦业主方沟通上海中心大厦350兆消防用无线对讲系统市消防总队和浦东支队出具的报告，根据报告内容推进物业管理公司整改，希望能够跨过维护合约框架单独立项实施	2025-05-09 00:00:00	7	t
271	2025-05-09	439	470	\N	根据业主的需求提供了FAB6二层三层的初步天馈布点点位，协助业主负责人完善改造方案申报的资料；	2025-05-09 00:00:00	7	t
272	2025-05-09	427	435	\N	沟通B193区域的实施方案，业主提出在是否能在B193一楼CCR控制室增加一副天线，复核设计图纸进行确认，方案其他业主已认可；	2025-05-09 00:00:00	7	t
273	2025-05-09	439	470	\N	与业主方工程师沟通改造方案，并且根据业主要求修改了方案中系统图部分，协助业主工程师向上级提出改造需求和方案，业主方需提供CUB/FAB二层/FAB三层图纸；	2025-05-09 00:00:00	7	t
274	2025-05-09	427	435	\N	设计师已经完成B193区域的信号覆盖的方案和清单，商务在填写好清单价格后发给客户确认；	2025-05-09 00:00:00	7	t
275	2025-05-09	439	470	\N	业主方咨询由于FAB二楼三楼安装天车造成原无线对讲天馈系统破坏恢复的方案，进行初步的沟通；	2025-05-09 00:00:00	7	t
276	2025-05-09	439	470	\N	测试	2025-05-09 00:00:00	7	t
277	2025-05-09	434	252	\N	根据上周现场会议沟通的意见，对于浦东机场卫星厅350兆无线对讲系统维护合约的技术规格书进行修正，修正内容包括定义室外设备的检测方法和内容，检测设备需要第三方报告，设备维修包含在合约内，维护合约去除设备更新的内容，明年独立立项设备更新等等；	2025-05-09 00:00:00	7	t
278	2025-05-09	434	252	\N	至浦东机场卫星厅现场与业主沟通2025年无线对讲系统续约事宜，目前主要沟通的是业主希望能够在新的合约中包含设备维修更换的工作内容，但是这部分的价值需要预估并且存在预估执行的风险，需要与业主沟通并确定一个双方认可的模式；陪同浦东机场T3项目销售与设计师向机场业主介绍和源350系统结构及相关软件；	2025-05-09 00:00:00	7	t
305	2025-05-09	427	435	\N	与区域负责人沟通1月份区域定向测试时B193区域两个茶水间信号断续情况，并提供方案与负责人沟通	2025-05-09 00:00:00	7	t
279	2025-05-09	439	470	\N	与ERC负责人就FAB区域新安装天车系统对无线对讲天馈的影响进行沟通，并且根据该区域图纸清单对涉及的天线器件等等进行了预估；	2025-05-09 00:00:00	7	t
280	2025-05-09	439	470	\N	与ERC负责工程师沟通测试报告与改造方案里的技术点，相关产品做了远程功能介绍，深圳中芯用防爆对讲机的需求；	2025-05-09 00:00:00	7	t
282	2025-05-09	429	435	\N	E188区域已完成项目的施工阶段，与业主方沟通下周系统接入的详细事宜，确定接入时间，并且协调技术对接入系统影响的区域，时长等事宜进行多方沟通；与业主沟通确认了施工材料的增补，移交给商务人员确认PO并且本周完成发货；	2025-05-09 00:00:00	7	t
283	2025-05-09	460	264	\N	和供应商根据上海厂和南方厂FAB区域的平面图后，向业主提出了方案和方案相关的终端形式，与业主分析了目前方案和终端的利弊，业主已接收提出的方案和终端的形式，业主方表示将在中芯南方内部进行方案讨论，后续继续跟踪；	2025-05-09 00:00:00	7	t
284	2025-05-09	460	264	\N	与供应商根据与业主确认的中芯南方/中芯上海厂的FAB三个区域的平面图，提出可行的硬件方案，选择高精度UWB及有源定位终端的方案，确定可提供的两种终端维护模式与业主下周进一步沟通；	2025-05-09 00:00:00	7	t
285	2025-05-09	460	264	\N	在中芯南方现场召开会议，与业主沟通高精度智能人员定位方案，本次沟通完全针对中芯南方与上海厂三个互通的fab区域的建筑结构，连廊通道互相关系等等，根据区域的入口/人员值守工况等等一一讨论定位的需求和终端的形式并且明确了软件功能的要求，会后会再和供应商沟通提出的有源终端的工作形式和呈现形式，然后再与业主沟通；	2025-05-09 00:00:00	7	t
286	2025-05-09	429	435	\N	与188区域负责人沟通了防爆天线的密封问题和威图控制箱的质量文件需求的事宜，并且把业主需要增加采购线缆的事宜告知商务，推进商务采购流程；	2025-05-09 00:00:00	7	t
288	2025-05-09	460	264	\N	与业主方沟通中芯南方无线对讲系统改造PO单内UPS代采购事宜，由于甲方采购部门的原因，需要进一步沟通如何处理，并约定4月9日至上海中芯南方现场会议；	2025-05-09 00:00:00	7	t
289	2025-05-09	423	249	\N	与设计院认识的工程师添加了联系方式，初步沟通了船舶用呼叫系统目前在船舶设计院这边的情况，初步约定了后续沟通交流的事情；	2025-05-09 00:00:00	7	t
290	2025-05-09	460	264	\N	与供应商沟通定位需求芯片厂的实际场景，根据芯片厂FAB区域的特殊流程，防护服防护装备消杀通道等等，筛选可行性，与业主方进一步商讨；	2025-05-09 00:00:00	7	t
291	2025-05-09	460	264	\N	与业主进一步确定以FAB区域为定位人员统计项目目标区域，结合进入FAB的人员工作流程（进入区域闸机/穿特定的防护服/通过特定消毒区域/指定离开通道）等特定场景特定流程特定区域来商榷定位基站和终端的形式；根据与业主沟通的信息与供应商联系，约定下周一供应商至公司沟通；	2025-05-09 00:00:00	7	t
293	2025-05-09	434	252	\N	与上海浦东机场卫星厅弱电部门合约签订负责人沟通2025年浦东机场卫星厅350M无线对讲系统维护合约签订的事宜，提供资料给业主，业主提供了项目立项及合约指定签订的项目建议书；	2025-05-09 00:00:00	7	t
294	2025-05-09	460	264	\N	与中芯南方业主沟通现场需求的区域对于定位基站和定位终端的形式，初步排除RFID的形式，但是业主仍然希望后续更换电池/充电/终端管理能够减少管理成本，我将继续与供应商沟通终端的形式	2025-05-09 00:00:00	7	t
295	2025-05-09	460	264	\N	中芯南方业主方在初步方案上会后进一步调整需求，目前希望定位的终端最好能以无源的形式来减少后期对于终端更换电池等维护工作；与供应商沟通后进一步商榷提出有源终端（尽量避免现场维护工作量）和无源终端（还未确定形式）两种方案，本周完善方案下周与业主沟通；	2025-05-09 00:00:00	7	t
296	2025-05-09	427	435	\N	由于原先B193区域只是增加了2个天线做了两层办公室的信号增补，业主希望这次对B193做个全面的覆盖，业主需要提供B193的建筑平面图，然后安排设计师做方案；	2025-05-09 00:00:00	7	t
297	2025-05-09	460	264	\N	根据最新要求沟通了调整终端的形式，与供应商沟通定制方案及可选择终端的方式及执行预算；	2025-05-09 00:00:00	7	t
298	2025-05-09	460	264	\N	与中芯南方业主现场沟通会议，根据新的AOA的方案，联络了相关部门讨论终端的形式，并且对执行预算进行沟通；	2025-05-09 00:00:00	7	t
299	2025-05-09	427	435	\N	与PCS区域负责人沟通B193区域茶水间信号增补的事宜，提供了茶水间信号增补方案，客户提出了对B193区域做整体室内信号覆盖的需求	2025-05-09 00:00:00	7	t
300	2025-05-09	460	264	\N	根据与业主方沟通UWB方案硬件预算较高的想法后，沟通调整预算的第二个方案，把方案提供给业主，下周与用户根据方案进行进一步沟通；	2025-05-09 00:00:00	7	t
302	2025-05-09	460	264	\N	中心南方P2P3项目改造项目与业主方确认最后合约签订事项，业主方发出PO最后确认单，安排商务完成提交给业主；	2025-05-09 00:00:00	7	t
303	2025-05-09	460	264	\N	与业主沟通商榷相关预算的问题，主要集中在一些量级的硬件的实施预算的优化，比如定位工牌的需求量可能在5000-10000张，基站的数量级可能上百；	2025-05-09 00:00:00	7	t
304	2025-05-09	460	264	\N	提供初步的UWB方案的软件及硬件清单，并且根据沟通的结果提供预算，协助业主提出需求所需要的各种信息；	2025-05-09 00:00:00	7	t
465	2025-05-09	607	123	\N	本次沟通针对的工业园项目还没有到投标节点。	2025-05-09 00:00:00	17	t
306	2025-05-09	460	264	\N	与业主方沟通厂区现场具体建筑确定方案内基站的安装距离，安装方式和数量；	2025-05-09 00:00:00	7	t
307	2025-05-09	460	264	\N	与业主沟通2月18日现场会议沟通方案后的想法，并把针对UWB方式的方案提供给客户，客户也增加了希望定位工牌能融入南方海康门禁系统等需求；	2025-05-09 00:00:00	7	t
308	2025-05-09	460	264	\N	在中芯南方与业主交流蓝牙信标及UWB电子围栏 功能的方案，并且根据与业主沟通的结果会提供进一步针对UWB围栏功能（特定区域两个入口进出人员统计）的方案	2025-05-09 00:00:00	7	t
309	2025-05-09	436	252	\N	与浦东机场卫星厅机电负责人沟通2025年浦东机场卫星厅无线对讲系统维护合约续约事宜，根据业主需求提供部分材料，确定大致今年续约谈判的年限和预算；	2025-05-09 00:00:00	7	t
312	2025-05-09	449	258	\N	2月12日与业主方负责人沟通和源股份进入振华供应商库事宜，目前资料提交完成，流程进入最后审核阶段，目前缺少企业ISO14001、45001管理体系认证证书，正想办法解决；	2025-05-09 00:00:00	7	t
313	2025-05-09	460	264	\N	2025年2月11日至2025年2月14日与中芯南方业主沟通蓝牙信标及UWB高精度定位实现区域电子围栏 访客卡定位方案的可能性；	2025-05-09 00:00:00	7	t
314	2025-05-09	460	264	\N	2025年1月30日与设计师至上海中芯南方与业主方沟通交流 介绍和源系统监控/定位/巡更/智能电池管理等功能	2025-05-09 00:00:00	7	t
397	2025-05-09	609	125	\N	交流蓝牙信标巡检方案，方经理介绍业主希望打卡能有声音反馈，不然信息不闭环，不知道能不能打上，从而给工作造成不便。	2025-05-09 00:00:00	17	t
315	2025-05-09	495	183	\N	张家浜业务招标，目前询价仅壹杰和九分及九分分包单位，与梅小好沟通复核情况。经了解基本确认壹杰中标C1B-02地块，而九分会中标C1C-01地块，但九分即使中标还是通过另外一家采购，关系基本都是另外一家在处理	2025-05-09 00:00:00	14	t
316	2025-05-09	488	276	\N	九星城一标段，推动品牌资料报验，确保品牌不要再有变化，同时安排渠道跟进深化设计。与渠道沟通了解二标段品牌报验已经确认，商务在同步进行，预计5月份会提前预估三个标段所需产品数量，统一申请价格进行批价。	2025-05-09 00:00:00	14	t
317	2025-05-09	531	214	\N	与张辉沟通了解目前长芯海神项目启动，我们系统仍就在消防包内，但此项目牵涉保密，所以公司委派北京总部的人在总体负责设计，至于用户方面他也没有直接接触，所以没有联系方式。另外业务提及广州有个日月新半导体业务，智能化设计还没启动，后续看用户是否需要无线对讲系统	2025-05-09 00:00:00	14	t
318	2025-05-09	541	217	\N	拜访卢荣祥，有个太仓隧道业务主要他在负责设计，我们通过维德的关系了解其业务，在沟通过程中了解该项目已经有过一般初步设计，只是这次正好牵涉到公安提出基站需求，可以通过此机会去看如何调整。通过沟通该院智能化设计人员在5人左右，但和隧道有关的业务现在基本都是他在负责，同时他提到还有个嘉兴隧道和上海真如隧道贯通业务。目前先配合太仓隧道业务，计划后续组局加强关系，并洽谈合作，推进其他业务合作，同时组织交流	2025-05-09 00:00:00	14	t
319	2025-05-09	562	233	\N	渠道报备，云思参与此业务投标，品牌虽然未入围，但可以使用同档次，云思咨询价格合适后，还是会考虑知名品牌	2025-05-09 00:00:00	14	t
320	2025-05-09	534	215	\N	拜访龚俊瑜和滕思宇，赠送茶叶慰问客户。跟进浦东东站地下标段业务，目前了解浦东东站地下标段近期上安内部会初步确认系统供应商，按龚总给与价格进行调整，先稳定上安，后续继续跟进了解目前上安这边的情况。同时龚俊瑜告知E2商务区最终价格和邹飞那边已经确认，由于他们合同还没下来，让我们提前配合	2025-05-09 00:00:00	14	t
848	2025-06-10	102	420	\N	7月份通信费用到期，客户确认续费，费用会在7月份报上去，发票7月份开。	2025-06-10 05:46:19.356301	2	t
849	2025-06-10	130	443	\N	客户预订购2块公网机器电池，先报价。	2025-06-10 05:47:00.560701	2	t
321	2025-05-09	542	219	\N	拜访王佳斌，中午便餐。了解行业情况，经沟通，他们内部分为多个分院，每个分院在外地有很多分公司，主要市场竞争是隧道院、城建院，他们所处的是地下环境院，主要业务聚焦在市政道路，隧道及地下空间，像他们一院、二院、三院、四院主要以与水有关的业务为主。在其沟通过程中介绍了台州临海的一条隧道，据说总包临海广电中标，给予了联系人，跟进看是否有机会。同时与其商量5月份约个时间和他们部分弱电团队组织技术交流和中午聚餐，按现有的弱电人员预计在5人。浦东东站隧道业务现在情况不是很了解，让我们跟踪铁四院去了解了解情况	2025-05-09 00:00:00	14	t
322	2025-05-09	485	176	\N	通过莫忠海组局认识华润置地华东区机电设计总监巫和昕，与郭总一同晚宴邀请。了解华润置地业务分为三级管理，由总部至大区至城市公司，城市公司业务主要以地产为主，商业项目一般会从大区调配一个负责人，一般业务都会以总部集采名单为主，但大区经理可以通过合理理由去改变原定品牌，目前无线对讲系统也不再集采范围，大区可以通过组织审核，提供品牌入围。正好郭总通过麦驰设计在参与华润宝山大杨镇W12地块。计划后续至巫和昕办公室拜访，商议如何推进招标品牌入围及合作	2025-05-09 00:00:00	14	t
323	2025-05-09	528	211	\N	跟踪渠道，确认商务合同已经确认，发起渠道业务批价确认	2025-05-09 00:00:00	14	t
324	2025-05-09	508	288	\N	跟踪渠道，御桥12C-18项目确认商务合同已经确认，发起渠道业务批价确认	2025-05-09 00:00:00	14	t
325	2025-05-09	567	239	\N	跟踪渠道，确认商务合同已经确认，发起渠道业务批价确认	2025-05-09 00:00:00	14	t
326	2025-05-09	480	350	\N	拜访殷平，现在华东院内部也在不断变化，其中原先机电一院、机电三院各自抽调一个团队去建筑所，机电二院成立智能化团队，由蔡曾宜负责。现阶段他们主要在配合建筑一所再投设计标	2025-05-09 00:00:00	14	t
327	2025-05-09	482	350	\N	拜访张晓波，组织华东院技术交流&商务活动，拓展关系	2025-05-09 00:00:00	14	t
328	2025-05-09	546	223	\N	拜访闻锋，沟通上海党校，目前还在方案阔粗，用户希望搭建上层平台，所以找了3家，华为、联通及仪电鑫森，待方案阔粗好了之后才会启动智能化设计。至于915项目，经沟通确认，仪电鑫森已经报了和源的品牌，但因为项目特殊性，所以进度比较慢	2025-05-09 00:00:00	14	t
329	2025-05-09	512	196	\N	与采购周心一及项目经理确认最终方案及价格，渠道配合提供最终报价，待采购确认后，发起合约商务流程	2025-05-09 00:00:00	14	t
330	2025-05-09	533	215	\N	拜访丁愉豪，经了解无线对讲中标价格不含税为270万，这个价格是四建安装中标价格，等于智能化分包的话四建安装还要收取管理费。按现在九分内部想法是各系统有关技术要求及价格确认，然后再内部讨论，调整报价后跟进九分龚俊瑜，拜访梁栋之，表示给予支持，稳定九分关系	2025-05-09 00:00:00	14	t
842	2025-06-09	\N	423	602	保障完成，开票收款。	2025-06-09 08:16:25.092238	2	t
331	2025-05-09	476	350	\N	拜访韩翌，目前他们调整到建筑一所，主要在忙着配合建筑一所参与投标，结构上调整意味着以后建筑一所业务一旦拿下，智能化业务基本都会在他和殷平手上负责，除非忙不过来后才有可能会转移到其他部门。至于工业博览会项目，因为进度原因还是比较慢，现在在等精装图出来后才会启动智能化施工图，业主方面现在还没具体负责人，侧边了解是原先国展业主负责人	2025-05-09 00:00:00	14	t
332	2025-05-09	478	350	\N	与毛晶轶沟通，了解有关业主及品牌情况。按毛晶轶反馈目前业主那边不用太过担心，基本都会听他的，让我们先去和黄辰贇沟通，给予黄辰贇一版品牌建议，待黄辰贇确认后他这边会去看是否合理	2025-05-09 00:00:00	14	t
333	2025-05-09	495	183	\N	与梅小好沟通反馈有集成商挂靠九分资质，通过初步复核品牌的确可控，但参与集成商通过九分关系了解到并没有参考招标品牌，用的是浙江尧起，将次情况让梅小好复核集成商信息，判断用户除了品牌招标在可控范围内以外，是否有能力可以掌控集成商。项目预计二季度招标，潜在参与集成商：信业、中建电子、益邦及万安都有可能参与，待项目正式招标，了解参与集成商具体情况	2025-05-09 00:00:00	14	t
354	2025-05-09	478	350	\N	了解上实北外滩项目91号地块项目，目前其主要负责塔楼办公区域的设计，整体方案还在讨论，这块由于和黄辰贇负责不同区域，各自有各自的设计思路，但用户方面通过WSP了解现阶段更多是毛晶轶在负责对接，攻克毛晶轶关系，计划通过他接触到现在业主负责人	2025-05-09 00:00:00	14	t
334	2025-05-09	538	215	\N	该项目分为联检及酒店两个部分，其中联检目前上安九分参与建工平台投标，预计5-6月份完成投标，并与总包建工合同签订，酒店预计本月底启动投标，预计合同签订时间与联检相差不会太多。现场反馈项目实施进度较急，联检及酒店需要提前协助，把天馈有关隐蔽工程提前完成。现阶段深化方案基本确认，价格与上安采购有过初步沟通和确认，代理商在跟进并提前配合执行	2025-05-09 00:00:00	14	t
335	2025-05-09	536	215	\N	浦东东站地下及空铁联运基本确认上安九分负责智能化实施及设备采购，项目现场张东伟负责，与张东伟初步建立沟通，今年他们主要计划是项目整体实施方案深化，与业主确认，具体进场实施要到明年	2025-05-09 00:00:00	14	t
336	2025-05-09	497	186	\N	与代理商一同拜访奔逸总经理徐良健，沟通浦江永久实验室，判断代理商与集成商商务合作关系。目前项目建筑结构部分还未封顶，现场仅在做管线预埋，设备进场预计在今年三季度，整体交付要到明年。商务方面给与总价控制范围，基本双方合作没有太大问题	2025-05-09 00:00:00	14	t
337	2025-05-09	502	188	\N	协同代理商拜访电科智能，经了解电科智能中标，主要与烈龙竞争，通过替换和源对讲机从而获取价格优势，基本项目已经确定，只是目前电科还在等与总包合同签订，预计商务启动时间5月份	2025-05-09 00:00:00	14	t
338	2025-05-09	513	196	\N	与代理商一同参与张江二厂项目方案会议，经讨论确认实施方案，后续由代理商推进与华虹智联商务合约进程	2025-05-09 00:00:00	14	t
339	2025-05-09	502	188	\N	与代理商一同拜访电科智能，协调原虹桥香格里拉酒店项目，并通过此机会认识电科智能项目领导，介绍新增业务，渠道负责跟进	2025-05-09 00:00:00	14	t
340	2025-05-09	513	196	\N	同代理商瀚网参与张江华虹宏力二厂项目会议，与业主汇报方案，经汇报后根据用户要求调整方案介绍，下周用户建设部门组织使用部门一同参与，计划通过方案汇报尽快锁定品牌，帮助渠道在商务谈判中与凌越竞争处于有利位置	2025-05-09 00:00:00	14	t
341	2025-05-09	545	223	\N	与刘威和设计负责人邓清、瞿迪组织项目交流，经交流后设计院理清项目方案设计思路，经讨论后调整方案。该项目分为多个地块，上海院作为主设，确定系统架构和设计方向	2025-05-09 00:00:00	14	t
342	2025-05-09	537	215	\N	为帮助代理商瀚网与实际项目分包商奔逸商务方面能够有序推进，拜访上安九分分派的项目经理曲文博，与他沟通了解项目目前准备做管线预埋，预计到我们系统进场穿线时间预估在8，9月份，现阶段需要先把深化方案落实。经了解分包奔逸在和上安九分签订分包合同，其中无线对讲系统复核选用和源品牌，同时瀚网在推进奔逸项目现场提交品牌送审，价格方面通过上安了解到给予分包价格	2025-05-09 00:00:00	14	t
343	2025-05-09	542	219	\N	该项目设计已经完成，经了解在提交过程中有关品牌提交过短名单，复核品牌入围，但最终还需看用户是否采纳，但市政院目前还没直接对接用户，后续了解项目招标计划及是否能够接触到用户。在拜访过程中挖掘新增济南隧道业务，推动业务合作	2025-05-09 00:00:00	14	t
344	2025-05-09	504	192	\N	渠道报备，配合东大参与项目报价。经沟通了解东大在配合甲方做招标前概算	2025-05-09 00:00:00	14	t
345	2025-05-09	506	192	\N	渠道报备，配合东大参与项目报价，主要竞争：锐河、英智源、畅博	2025-05-09 00:00:00	14	t
346	2025-05-09	516	199	\N	与薛总了解目前他们还在与甲方合同签订过程中，预计本月能过把合同落实，现场已经派驻项目经理，但实际进场预计需要到今年9月份，弱电有可能会到明年才启动，今年只是做准备工作。商务方面他们还没确定具体智能化分包单位，由于项目体量较大，最终定夺都是在集团内部，他们分公司没有权利直接去定，后续跟进了解智能化分包单位，同时了解到该项目为单价合同。	2025-05-09 00:00:00	14	t
347	2025-05-09	525	208	\N	拜访业主设计部彭俊，了解投标情况。目前还未最终出结果，侧边了解主要在云思和云赛之间相互竞争。通过集成商跟踪情况，云赛是事业7部在负责，直接事业部亲自负责投标，选用沅抗品牌。计划待结果出来后再看业主是否能帮忙，目前云赛事业部也没直接联系人，但业主方面他也比较谨慎，主要是内部也存在相互竞争，主要是技术与合约部门	2025-05-09 00:00:00	14	t
348	2025-05-09	535	215	\N	同代理商一同拜访焦峰，关系维护，经了解焦峰现在主要负责供应商有关项目管理。并与采购负责人龚俊瑜了解到后续他们会参与宁波丽思卡尔顿酒店，这部分他们把握较大，需要配合好报价	2025-05-09 00:00:00	14	t
349	2025-05-09	472	174	\N	经上安介绍，与海康威视上海区域交通行业销售负责人杨敬鹏交流，通过其引荐通号信息上海负责人，跟进了解浦东东站地上部分。经了解杨敬鹏主要负责海康威视交通行业板块，主要以铁路，地铁，码头、机场等，目前他们也在跟进浦东东站项目。	2025-05-09 00:00:00	14	t
350	2025-05-09	569	241	\N	拜访通号信息关鹏，经了解浦东东站地上部分由他负责，他们原先主要以铁路，轨道交通项目为主，与海能达，中瑞特都有过了解和接触。有关项目沟通他这边对整个项目站房内比较熟悉，并且按他对项目的了解整个项目后续运维是由铁路来负责，所以整个项目最后系统接口要统一，会存在统一调度的可能性。目前配合他们浦东东站地下部分报价，他们也在跟进四建安装想要把地下部分也一并拿下。有关通号本身后续业务流程上需要提前确认好，一旦到北京总部内部招标很多东西再去改变几乎没有可能	2025-05-09 00:00:00	14	t
351	2025-05-09	495	183	\N	该项目与梅小好联系，沟通项目情况，得到反馈他与业主已经推动品牌围标，无线对讲品牌为和源，瀚网，福玛。项目预计2个月内招标，有关方案建议回复现阶段无法修改调整	2025-05-09 00:00:00	14	t
352	2025-05-09	507	288	\N	与福玛陈刘祥沟通确认张江创新药基地B03C-02项目益邦分包给予名鹭，在配合名鹭进行商务报价。项目时间节点预计与03K时间上差不多，现阶段做管线预埋，设备进场时间预估在5，6月份	2025-05-09 00:00:00	14	t
353	2025-05-09	483	350	\N	南大项目与业主沟通情况汇报给予周天文，现阶段主要等待智能化成本概算出来后，就会启动招标，具体品牌方面还是以业主建议为主。另外天合光能项目智能化还早，现阶段还在讨论机电，等机电招标工作完成后才会启动智能化。另外他负责的长江存储目前还在方案阶段，没有任何消息，同时告知他们在投一个青浦的文旅项目，待设计中标确认是他负责后推进业务跟进	2025-05-09 00:00:00	14	t
355	2025-05-09	559	231	\N	上海圆信挂靠中邮件，中标九星城三标段，现阶段刚刚进场，准备系统方案深化确认同时主要做管线预埋，经沟通了解他们与弘谊白银龙属于深度合作，白银龙在圆信有股份，所以杨冰峰意思项目可以用和源，但出货渠道需要通过弘谊，而弘谊现在主要是和瑞康业务合作。所以计划安排瑞康跟进方案深化，确认采购清单，推进品牌报验	2025-05-09 00:00:00	14	t
356	2025-05-09	488	276	\N	拜访九星城一标段中标单位江苏金鼎，与项目经理沟通了解整体进度与三标段一致，预计无线对讲启动时间在下半年。项目经理反馈他们投标选用威升品牌，通过对金鼎了解，包括二标段反馈，应该是中瀚孙建中和杨顺凯在以威升名义参与。项目经理透露主要还是在于商务成本，这部分主要负责是朱焱。项目现在二标段付言新已经推动蓝极星申报品牌，经顾问复核他们已经确认，但业主方面还在等待一、三标段情况，业主是希望品牌统一化，但如果出现不统一，会看各标段情况来左右，所以计划除二标段以外，先拿下三标段，这样在一标段中可以处于有利位置	2025-05-09 00:00:00	14	t
357	2025-05-09	536	215	\N	该项目用户预算给予仅60万，配合调整优化方案，项目设计虽为华东院负责，但实际都是上安在负责把控，与上安商议推进品牌植入工作。另外上安帮忙引荐海康威视，经了解海康威视与浦东东站地上标段通号有过接触，尝试引荐	2025-05-09 00:00:00	14	t
358	2025-05-09	523	373	\N	与张小宁反馈成本部清单与设计方案不符，会导致概算价格有出入，说服后张小宁让我们根据方案出配置清单给予他后，他来看如何处理。现阶段按张小宁透露的情况是他们集团内部在做智能化成本概算，待概算确认后就会启动招标，预计时间4月份。他也是在等成本概算，同时他表示近期因为市场环境，集团对于预算把控比较严格，预算都比较偏低，项目本身有部分已经整体售卖，所以系统规划上他们可能会取消消防系统建设，至于品牌推荐方面也是等概算后再跟进	2025-05-09 00:00:00	14	t
851	2025-06-10	134	444	\N	与客户沟通安排本季度维保工作，6月11日完成本季度维保。	2025-06-10 06:06:21.032327	2	t
946	2025-06-25	693	341	242	配合的总包未中标	2025-06-25 09:21:26.476019	13	t
1629	2025-10-17	\N	\N	830	声美华设计	2025-10-17 10:59:41.556623	25	t
359	2025-05-09	496	185	\N	渠道反馈宝通因价格因素放弃福瑞项目，但透露应该还是回到大总包十一科技。与十一科技施君联系了解情况，但他表示也不太清楚，项目介入不深，计划通过他接触到用户，但他并不认识，只是给了一个微信，下周计划尝试加下，看看能否接触到用户	2025-05-09 00:00:00	14	t
360	2025-05-09	566	238	\N	经沟通了解用户对无线对讲系统不是特别了解，仅要求手持对讲机要摩托罗拉品牌，系统招标分配在自控包间内，由苏州汉威中标，代理商为配合苏州汉威提供系统方案，组织用户交流，介绍和源企业的同时，介绍方案和产品。项目分为一期、二期，本次先建设一期，初步明确用户基本需求，配合汉威提供系统方案给予用户确认。项目现场要求今年四季度完工，预计二季度就会启动项目实施工作	2025-05-09 00:00:00	14	t
361	2025-05-09	474	350	\N	拜访陈允强，沟通深圳中信金融中心项目。该项目华东院为设计总负责，智能化设计由广东设计院负责，目前广东设计院完成后交由华东院负责审核，同时通过品牌表上信息了解WSP为机电顾问，给予陈允强品牌修改建议，看能否做出调整，把基站及对讲机品牌添加进去	2025-05-09 00:00:00	14	t
362	2025-05-09	481	350	\N	拜访张航，经沟通了解近期机电准备招标，弱电智能化预计今年三季度招标。目前对讲系统方案基本确认，进入品牌讨论，现阶段基站品牌经了解加入了和源，传输部分还在确认。另外跟进D5D项目，目前设计还没有具体推进计划	2025-05-09 00:00:00	14	t
363	2025-05-09	536	215	\N	该项目地下及空铁联运部分经沟通上安九分计划承接智能化分包，目前在复核整体成本，无线对讲经透露差距230万，复核方案调整报价策略给予上安，后续跟进确认智能化分包信息	2025-05-09 00:00:00	14	t
364	2025-05-09	476	350	\N	拜访韩韩翌，了解工博会项目情况。经沟通智能化设计还没有任何进度要求，现阶段因建筑设计报审没通过，所以修改设计后重新报建设	2025-05-09 00:00:00	14	t
365	2025-05-09	529	213	\N	拜访朱丹，经沟通了解项目总体设计华东院负责，但智能化专项设计分包给朱丹负责。和朱丹沟通了解原先因资金问题没有考虑无线对讲系统，计划用公网系统取代，但华东院提及上海地方规范，所以现在还在讨论确认是否需要做。项目设计进度方面现在朱丹正配合按业态逐步出点位图，目前对讲系统因没有确认，还未设计进去。项目分为多个地块，同济院和华东院各负责一部分，华东院负责的为部分商业，酒店及酒店式公寓，其中商业可能还需要接入到同济设计的部分，关于界面划分还在沟通讨论。	2025-05-09 00:00:00	14	t
366	2025-05-09	563	234	\N	拜访庄彦，中午便餐，了解张江创新药项目情况，目前03K地块上报品牌为和源，但03C还没有看到品牌报验情况。项目两边实施进度差不多，届时帮忙关注03C的品牌情况。另外沟通了解今年新增业务目前还没有，主要受制于政策及招商影响	2025-05-09 00:00:00	14	t
367	2025-05-09	536	215	\N	该项目通过陈华林了解到四建安装给予上安九分有关无线对讲系统的成本价格，与梁晓君沟通目前他们在核实项目成本，在确定是否会去做智能化分包。关于目前价格情况也与梅小好进行沟通，希望借此引荐用户给予认识，但梅小好反馈业主现在处于敏感期，他与业主有过沟通不是特别方便，但他反馈品牌变更可能性不大	2025-05-09 00:00:00	14	t
368	2025-05-09	566	238	\N	与业主了解，目前汉威提交系统品牌，为摩托罗拉+和源，计划邀约业主，和业主交流	2025-05-09 00:00:00	14	t
370	2025-05-09	556	229	\N	该项目经沟通了解目前在做精装样板间确认，待确认后启动桥架管线工作，预计项目要到年中才会启动设备采购。目前商务方面出了我们以外，烈龙也在参与报价，由于项目为合作伙伴梅小好与业主有商务合作，烈龙品牌不在范围内，所以只是来压制我们价格	2025-05-09 00:00:00	14	t
371	2025-05-09	517	199	\N	拜访建工四建安装投标部赵展鹏，经沟通由于年前刚宣布中标结果，原定中铁由于个别资质原因由他们中标，现阶段他们可能与甲方合同还未最终签订，由于他们原先主要以机电业务为主，智能化可能会分包，具体需要与他们经营部负责人沟通了解。同时上安九分询价，经了解他们可能会作为智能化分包，按上安九分反馈目前建工四建给予的无线对讲系统预算和当时我们投标报价对比差了230万，让我们先按清单复核，调整优惠一版价格。计划后续通过赵展鹏引荐，了解项目中标情况。\r\n	2025-05-09 00:00:00	14	t
372	2025-05-09	519	201	\N	该项目与黄攀联系后了解智能化还未正式招标，近期吉托一直在忙于智能化招标前准备工作，预计3，4月份就会启动招标，待智能化招标完成，就马上要启动设备进场	2025-05-09 00:00:00	14	t
373	2025-05-09	528	211	\N	该项目与冯一沟通了解项目现场具备实施条件，计划3月份天馈部分可以进场实施。商务方面具体由卢宁负责，需要冯一组织安排与卢宁洽谈商务合约。现阶段安排渠道复核深化方案，提交冯一沟通确认	2025-05-09 00:00:00	14	t
374	2025-05-09	495	183	\N	介绍梅小好与林文冠认识，促进艾亿作为渠道发展与我们保持合作。跟进业务情况，新增浙江横店喜来登业业务，与梅小好沟通了解他通过关系把品牌变更为和源，瀚网及福玛	2025-05-09 00:00:00	14	t
375	2025-05-09	496	185	\N	拜访宝通张旭东，经了解项目实际跟踪为弘谊，项目负责人与王丽亚关系较熟悉，王丽亚跟进后和瑞康报备。核实项目情况，现阶段宝通在复核成本，整体智能化仅几百万，中标价格偏低，无线对讲系统实施预算仅35万。与合作伙伴沟通，因需要防爆产品，第三方产品调整为科立讯，控制项目成本。项目实施要求今年5，6月份系统交付，商务方面预计4月份会确认。但现在宝通还在因为整体价格因素，在考虑是否与总包十一科技继续执行下去	2025-05-09 00:00:00	14	t
377	2025-05-09	510	195	\N	拜访华虹半导体消防机电负责人王炜，沟通张江半导体二厂扩建项目。现阶段华虹计通中标，但凌越品牌在内，希望通过与业主合作，确保把凌越品牌屏蔽在外。王炜反馈现阶段具体选用是大总包十一科技负责，但他们作为用户会审核确认，相对比较谨慎，但考虑原先系统为我们建设，这块还是会帮去帮助让华虹计通尽可能选用和源品牌	2025-05-09 00:00:00	14	t
378	2025-05-09	564	237	\N	与声美华技术团队交流。了解前期业务情况，宁波中心丽思卡尔顿由于精装还未确认，点位图一直在修改，待点位图确认后，推进设计方案植入，品牌方面有了初步沟通。宜宾中心重新启动，品牌已经提交。计划通过声美华了解业主信息，安排福淳跟进，把对讲机品牌也做植入。	2025-05-09 00:00:00	14	t
855	2025-06-11	250	399	512	西安瑞林达已配合集成商完成深化设计和交流，在进行商务谈判，顺利的话7月可以签约	2025-06-11 07:08:45.293722	13	t
379	2025-05-09	547	223	\N	拜访徐楷程，沟通上海党校项目。现阶段他们提交扩粗方案，业主在抱概算，等概算下来后再根据概算情况，确定设计方案，具体时间节点目前还没有准确计划，后续计划通过上海院与用户接触，推进方案和品牌植入。另外徐楷程告知云赛有介入此项目，到时候找机会引荐，提前对接	2025-05-09 00:00:00	14	t
381	2025-05-09	509	194	\N	该项目通过WSP了解到恒能电子中标，与采购经理复核相关情况，并根据恒能中标业务流程，需重新报一版价格，采购给予指导价格70万，复核后几乎不可能，与采购建议需要先复核方案，否则无法执行下去，并通过采购了解他们主要合作对象为常森，同时另外一个苏州HKL项目，他们也刚刚拿下，项目进度会比E地块快一点，但这个项目没有品牌要求，根据他们合作单位情况预判应该是常森在参与。计划两个项目商务一同推进，并与常森洽谈，拓展区域合作	2025-05-09 00:00:00	14	t
382	2025-05-09	536	215	\N	上安梁晓君反馈地上、地下会分开招标，之前机房设备考虑地上，因为地下概算问题，但现在又需改为到地下部分，重新梳理清单。并通过资源了解甲方信息，邀约拜访铁四院也了解项目情况	2025-05-09 00:00:00	14	t
383	2025-05-09	543	219	\N	该项目市政院王微微反馈招标代理咨询他们有关该项目招标品牌要求，给予王微微提供系统招标品牌，信道机及对讲机品牌：摩托罗拉、海能达、和源通信。天馈传输及信号中继：和源通信、瀚网、福玛通信	2025-05-09 00:00:00	14	t
384	2025-05-09	539	215	\N	渠道反馈上安九分华南分公司在参与鹏峰项目投标，配合参与报价，品牌入围，竞争品牌为中诺天诚、英智源及宇洪，主设备品牌未入围	2025-05-09 00:00:00	14	t
385	2025-05-09	495	183	\N	该项目渠道报备，配合上电科参与项目投标，没有品牌要求，采用全和源产品提供参考价格	2025-05-09 00:00:00	14	t
386	2025-05-09	558	230	\N	机房中标单位永通反馈他们与甲方合同预计10月份落实，同步会与渠道瑞康完成商务确认。乐园中标单位现阶段瑞康采用让利方式已经确认商务框架，预计本月会启动确认合同签订。而酒店中标单位天馈部分已经确认，但直放站因为中标价格差异较大还在那有所搁置	2025-05-09 00:00:00	14	t
387	2025-05-09	508	288	\N	该项目渠道福玛反馈蓝极星借用上安九分资质中标，目前复核成本，配套方案深化，按目前掌握的情况，项目计划于明年3，4月份完成系统调试，预计今年就会落实商务采购	2025-05-09 00:00:00	14	t
389	2025-05-09	521	202	\N	签约批价	2025-05-09 00:00:00	14	t
390	2025-05-09	629	135	\N	林总介绍，他们想要去参与香港科技大学项目二期的总包，让我们方配合评估成本。\r\n华南理工黄主任确认，本项目的施工图还没有出来，保证品牌和参数会配合推荐。	2025-05-09 00:00:00	17	t
835	2025-06-09	\N	\N	16	客户告知，设备更换已上会，流程完成后到采购部，进行3方比价。	2025-06-09 03:39:13.889355	2	t
391	2025-05-09	621	381	\N	唐经理介绍，本项目我们的没有机会参与后续的竞价了，因为没有品牌限定，再者我们的价格较高，根据系统的评估策略，我们就难以参与，不然他们的系统会给出质疑。\r\n后续的项目要尽早的配合好售前，或者项目经理一确认下来就要马上做他们的工作，内部竞价流程对我方不利。	2025-05-09 00:00:00	17	t
392	2025-05-09	624	381	\N	东翼-1项目已经配合售前过配置清单，目前有：达实、金证、智宇、英飞拓、万安、北电正光已询价。\r\n本项目有可能最后采取抽签形式，暂时没有办法准确评估哪一家比较稳妥中标。	2025-05-09 00:00:00	17	t
393	2025-05-09	590	107	\N	秦经理介绍，老板暂时叫停了我们系统，觉得报价高。项目目前在走管线，约了秦经理后续拜访，与技术当面核对配置，了解秦经理是否有个人述求。	2025-05-09 00:00:00	17	t
394	2025-05-09	627	131	\N	徐总反馈，之前跟我们没有配合，他们的项目里面有部分是无线对讲系统，但不多，当前更多的业主会选择把无线系统留给物业自建。\r\n他先了解我们的资料，约了下周再到公司拜访，过一遍他们需要配合的项目。	2025-05-09 00:00:00	17	t
395	2025-05-09	636	141	\N	张总说我们需要跟瑞斯通比价，竞品（科立讯、海能达、瑞斯通）希望我们尽力配合价格。\r\n当前已经报了一版常规价格给采购，接下来还要找张总争取议价机会。	2025-05-09 00:00:00	17	t
396	2025-05-09	629	135	\N	林总介绍了负责本项目的项目经理对接，胡经理说他这边已经根据我们给的资料了解过了我们品牌，他们现在一个一个系统在过，暂时还没有过到无线对讲系统，等到了再通知我们参与线上竞价。\r\n项目经理在本环节占有选择权，需要进一步做深项目经理的工作。	2025-05-09 00:00:00	17	t
398	2025-05-09	620	381	\N	帅总要求尽快梳理出本项目的配置，要求尽量精准，本项目对成本比较关注。具体招标时间还没有定下来。\r\n目前已经梳理出来了配置和成本清单。	2025-05-09 00:00:00	17	t
399	2025-05-09	585	99	\N	张经理给出指导价格，我方配合做了调整。代理商已经提交企业资料，对方审核没有问题，下周可以签合同。\r\n其余的项目暂时都没有进展。	2025-05-09 00:00:00	17	t
400	2025-05-09	652	162	\N	何总介绍，深铁置业让他们配合出设计规范，这个工作大概会在5-6月启动，到时候需要将我们上海做的无线对讲行业规范梳理出核心关键，给到他们。\r\n河套项目还在做土建设计，智能化还远。	2025-05-09 00:00:00	17	t
401	2025-05-09	578	94	\N	王经理，介绍项目上近期出了安全问题，所有人员都在做安全管理规范学习，需要改下周到公司去找关键人做品牌入库工作。	2025-05-09 00:00:00	17	t
402	2025-05-09	609	125	\N	和方经理重新核对招标技术文档，他介绍地下室的摄像头是内置蓝牙的，业主出于成本考虑，也避免重复建设。提到蓝牙巡检能否使用摄像头里的蓝牙信号，以及蓝牙打卡的时候，能否在对讲机上有打上卡的提示音。我们最好出具一份关于蓝牙信标巡检的技术方案。\r\n目前已经让刘威在配合整理。	2025-05-09 00:00:00	17	t
403	2025-05-09	602	119	\N	焦总介绍，本项目分四个单位配合设计，分别是华阳、华东、浙江院、北京院。他们这边到时候让我们配合，最好去找剩下的三个院沟通，大家也希望尽量做到统一，避免后续的扯皮。	2025-05-09 00:00:00	17	t
404	2025-05-09	648	155	\N	柯经理表示，公司的项目分内、外两部分，内部项目首先考虑会用集采，外部项目他们销售有话语权。答应后续可以帮忙找招商蛇口负责本次集采的联系人，以及后续他的外部项目可以跟我们配合。	2025-05-09 00:00:00	17	t
405	2025-05-09	629	135	\N	林经理介绍，已经将我们品牌补录进罗湖妇幼的招标名单，等通知到线上招标。	2025-05-09 00:00:00	17	t
406	2025-05-09	649	155	\N	孟经理介绍，公司集采工作计划5月份会启动，他们作为前导部门会参与需求评估和品牌推荐工作。公司近期在进行人事调整，目前还没有明确下来，不宜去其他部门沟通。	2025-05-09 00:00:00	17	t
407	2025-05-09	609	125	\N	方总反馈，业主方不同意把软件部分在技术参数里体现出来，所以需要想方法变通一下。调整后的频段以及对讲机含蓝牙功能基本没有问题。	2025-05-09 00:00:00	17	t
408	2025-05-09	602	119	\N	焦总同意先举行技术交流，再推动整个部门的深入合作，希望后续能达成紧密合作。我们需要把后续工作上如何配合，以及做过的案例以及方案，我们的优势在技术交流的时候表达清楚。他来牵头组织，到时电气部门也会参与。	2025-05-09 00:00:00	17	t
409	2025-05-09	629	135	\N	配合梳理清单，以及报价。接下来等通知在平台邀标。没有回复报价的情况，到时候招标会给一个上限价格。	2025-05-09 00:00:00	17	t
410	2025-05-09	578	94	\N	王经理介绍，他们有自己的品牌库，要对接设计院建议先做品牌入库工作，避免浪费时间。了解了入库流程以及关键人联系方式，建议下周再联系拜访。	2025-05-09 00:00:00	17	t
411	2025-05-09	620	381	\N	本项目招标授权资料提报。本项目的中标概率较大。	2025-05-09 00:00:00	17	t
412	2025-05-09	616	381	\N	李工介绍本项已经中标，当时用的是昊天配合投标，和源报价合适可以配合变更，目前还没到品牌确认阶段。预计最快第三季度会涉及到我们系统的采购。	2025-05-09 00:00:00	17	t
413	2025-05-09	629	135	\N	林总介绍当前有罗湖妇幼项目，之前已经询过两轮价格，如果价格合适就直接使用。\r\n新皇岗口岸联检大楼项目，他们也会去参与，跟进这个项目的时间比较长，而且比较深，如果没有意外，他们的优势比较大。	2025-05-09 00:00:00	17	t
414	2025-05-09	620	381	\N	本项目计划最快六月份可以采购。	2025-05-09 00:00:00	17	t
415	2025-05-09	620	381	\N	帅总介绍本项目下周投标，需要下周一前出厂家授权文件。中继台和对讲机有品牌要求，我们配合天馈部分。	2025-05-09 00:00:00	17	t
416	2025-05-09	609	125	\N	方工介绍，项目调整为5月招标。上周已经把含有我们调整后的初版技术文档提交给代建方，最快节后回来会有结果。	2025-05-09 00:00:00	17	t
417	2025-05-09	650	157	\N	邹经理介绍，虽然我们配合投标，但他们的中标价格比较低，本周会进行品牌报审前询价沟通。\r\n已通知宇洪，本项目涉及竞品：海能达、上海曙腾。	2025-05-09 00:00:00	17	t
418	2025-05-09	624	381	\N	徐介绍本项目他这边在跟进，业主方深铁置业需要找技术运营部做品牌推荐工作，招采部不一定能说的上话，下周帮忙推介对接人。\r\n推荐新皇岗口岸、C塔、深铁物流项目，让其参与投标。徐表示新皇岗口岸和C塔项目，目前有其他同事在跟进，由于公司的销售太多，他需要回去查系统了解具体对接人，到时候跟我们同步。深铁物流可以配合去跟进。	2025-05-09 00:00:00	17	t
419	2025-05-09	657	89	\N	宋洋洋希望能参与进来，因与业主关系，并且在跟中标集成商：中通服和达实都有对接。我跟张兴协调，可以让他们参与标包一。\r\n王总介绍，他们会去参与新皇岗口岸联建大楼项目投标，投标找我们配合。\r\n	2025-05-09 00:00:00	17	t
420	2025-05-09	632	138	\N	刘总介绍，项目还没有到品牌推荐阶段，介绍顾问公司柏诚让我方先去对接，做好品牌预选工作。\r\n华泰证券总部大厦项目，目前在做智能化施工图，到无线对讲系统让我们跟黄工对接。	2025-05-09 00:00:00	17	t
421	2025-05-09	609	125	\N	已配合技术文档编写。由于技术文档是他同事在负责，他需要跟他同事同步技术文档修改和补充事宜。	2025-05-09 00:00:00	17	t
422	2025-05-09	640	146	\N	李总表示新皇岗口岸联检大厦项目他们这边在跟进，到时候投标他们会拿其他单位来投，天威不会出面。投标的时候介绍我们来配合售前做标书。\r\n由于项目较大，他们的把握说不准。运营商基本都会去参与。	2025-05-09 00:00:00	17	t
423	2025-05-09	585	99	\N	目前在配合方案配置。	2025-05-09 00:00:00	17	t
424	2025-05-09	661	171	\N	他们目前只是做简单的弱电工程-管网设计。智能化目前还没有确定是给他们来配合，业主可能会另招智能化设计单位。	2025-05-09 00:00:00	17	t
425	2025-05-09	655	166	\N	云筑网已挂标，与天津平安泰达项目共同招标。天津项目对讲品牌：摩托罗拉、建伍、威泰克斯。天馈：雷克、特易迅、德利亨通。光明项目无品牌要求。天津项目由于他们三局投标的时候业主有品牌要求，所以可以放品牌。我总结，后续和中建合作，可以通过业主或三局销售做品牌植入工作。\r\n邹总说报名结束时候可以通知我们有哪些单位参与。我们最大的潜在竞争对手是英智源。	2025-05-09 00:00:00	17	t
427	2025-05-09	601	119	\N	项目尚在前期，要求先了解资料，后面找机会再约时间沟通配置和方案。\r\n部门总工焦总不在，部门技术交流需要下回再约了。	2025-05-09 00:00:00	17	t
428	2025-05-09	640	146	\N	李总介绍，他们也在关注新皇岗口岸项目的进展，大概率会去参与投标，到时候会跟我们配合。	2025-05-09 00:00:00	17	t
429	2025-05-09	636	141	\N	张总介绍，长沙橘洲酒店需要尽快配合当地的技术深化图纸，以及到时候推荐同档次的品牌内部比价，避免把价格做低了。\r\n介绍张总给深铁物流设计方以及业主方认识，张总对本项目也比较感兴趣。\r\n希望通过引进第三方与该项目和业主方认识，大家可以对齐信息，了解项目真实进展，如后面我方引入的集成商中标，对我方利润把控有利。	2025-05-09 00:00:00	17	t
430	2025-05-09	585	99	\N	采购经理张焱反馈，我们系统较小，加上技术也跟我们对过了参数，没什么问题就提报我们品牌了。预计最快本月底签采购合同。	2025-05-09 00:00:00	17	t
431	2025-05-09	609	125	\N	方工介绍，技术文档目前正在编写，本周会把无线对讲系统的部分发给我们，不合理或者没有贴合我们优势的都可以修改，但要跟他们同步修改的地方，说明原因，以免业主方提出质疑。	2025-05-09 00:00:00	17	t
432	2025-05-09	600	118	\N	黄主任表示香港科技大学二期的施工图还没有开始设计，还需要再等等，还有个广东理工学院之前听说在做土建设计，看是否有无线对讲需求。广州大学宿舍项目近期在看成本，很有可能会去掉无线对讲系统。	2025-05-09 00:00:00	17	t
433	2025-05-09	631	138	\N	梁工介绍，他目前已经调到项目上工作，无线对讲系统配合要再等等，最快下个月，最晚要到五月系统图出来，我们就可以配合方案。	2025-05-09 00:00:00	17	t
863	2025-06-12	\N	50	264	经与设计方、项目管理方确认，因电信公司赠送公网对讲机，该系统取消。	2025-06-12 03:47:21.094736	16	t
694	2025-05-13	\N	89	555	配合设计方完成方案与清单编制	2025-05-16 07:21:25.27626	16	t
434	2025-05-09	609	125	\N	方经理介绍，本项目最快4月招标，我们的品牌和技术参数已经报上去给业主，工务署招标的时候应该不会有品牌要求，只有技术参数。\r\n接下来要了解会有哪些集成商参与投标，方经理答应会帮忙了解。以及项目咨询方：华昊咨询 刘经理也会帮忙了解参与集成商名单。	2025-05-09 00:00:00	17	t
435	2025-05-09	645	152	\N	项目的天线数量做了调整，李工将昊天的价格跟我同步了，昊天报的价格24.8万，我方4.8折报价27.1万。后续会进入议价阶段。	2025-05-09 00:00:00	17	t
436	2025-05-09	620	381	\N	最快下周设备的数量清单核对无误后就可以下单采购。	2025-05-09 00:00:00	17	t
437	2025-05-09	642	147	\N	项目对接的是前端销售，品牌已经植入成功，清单也已经出来，最快这个月底投标。	2025-05-09 00:00:00	17	t
438	2025-05-09	634	139	\N	由于上回陈工表示对专网无线对讲系统配置有些疑问，本次带张兴与陈工认识和技术交流，并且预约下回的售前部门技术交流。	2025-05-09 00:00:00	17	t
439	2025-05-09	645	152	\N	与张兴一同现场搭建简易天线回路（对讲机-耦合器-天线）测试。测试效果符合分包理想，目前他们需要考虑天线的缩减数量。	2025-05-09 00:00:00	17	t
440	2025-05-09	605	104	\N	与郭总一同跟省院第三机电所技术交流，之前与他们所有两个项目在合作，分别是琶洲算谷与罗山科技园。\r\n黄总对专网无线对讲比较熟悉，希望通过此次技术交流让其他同事能深入了解，并且植入和源是行业翘楚的印象，为后续合作奠定基础。	2025-05-09 00:00:00	17	t
441	2025-05-09	657	89	\N	王经理介绍，他们跟业主确认过，避免系统出现不兼容和售后扯皮，二期的品牌选择需要跟一期的同样。\r\n据了解一期是达实中的标，找达实项目陈经理确认过了，他们当时用的汉界配合投标，目前在找帅总帮忙协调更换品牌。	2025-05-09 00:00:00	17	t
442	2025-05-09	620	381	\N	让帅总帮忙协调佛山平安中心更换品牌。并且了解鹏峰项目负责人。	2025-05-09 00:00:00	17	t
443	2025-05-09	643	149	\N	李总之前是在海能达负责轨交部门，现在也是专门做地铁这块的项目，是海能达的代理商。\r\n李总介绍，本项目他跟进的是业主，和业主保持长期合作。深圳地铁的项目需要设备型号核准证才能参与，并且业内在推三频段合一的天线（350/400/800M），如果我们满足可以尝试合作。	2025-05-09 00:00:00	17	t
444	2025-05-09	637	142	\N	目前物流园项目已经确认由广东省建筑设计院中标。与智能化负责人肖经理沟通确定了，3月6日下周三上午进行技术交流，会让设计方一同参与，让我们尽快准备技术交流使用的物流园区相关方案，以及着重介绍专网对讲系统除对讲以外的功能，公司希望从本系统看到更多的价值。	2025-05-09 00:00:00	17	t
445	2025-05-09	632	138	\N	刘总介绍，西丽枢纽项目是配合中铁四院在做设计，下个月开始做施工图，到时候会推荐我们来配合。\r\n如果3月6日有空也可以过来跟他们部门做个技术交流，部门有十多个人，都比较分散。下周一再确认是具体时间。	2025-05-09 00:00:00	17	t
806	2025-06-03	\N	359	607	配合设计院叶工出具方案和清单 	2025-06-03 10:53:59.985855	13	t
836	2025-06-06	\N	54	523	下周准备签约	2025-06-09 05:35:11.854237	16	t
837	2025-06-05	\N	12	62	调整方案及报价	2025-06-09 05:36:50.171108	16	t
446	2025-05-09	597	117	\N	张工介绍，腾讯音乐大厦项目是由他这边在做设计，由于腾讯需要采用他库内的品牌，需要我们去找腾讯做入库工作，本项目他们是配合总包方卓越地产，介绍了卓越地产本项目的负责人郭立立。如果下周我们的团队来深圳，欢迎过来做技术交流。\r\n已经和郭立立沟通，他介绍腾讯入库需要找招采部的产品经理，他这边对接的是项目上的人。	2025-05-09 00:00:00	17	t
447	2025-05-09	638	143	\N	与樊总确认下周参与渠道会议，以及沟通后续合作政策。他表示前面两个项目他都在积极沟通中，遇到需要我们配合的地方会让我配合。	2025-05-09 00:00:00	17	t
448	2025-05-09	654	164	\N	钟经理介绍，本项目主体还在挖基坑，进展不会很快。后续会招智能化分包。\r\n后续邀约拜访，了解项目的其他负责人，保证信息非单一来源。\r\n	2025-05-09 00:00:00	17	t
449	2025-05-09	607	123	\N	王经理表示已经将和源品牌推荐进入本项目，引荐了成本部总监朱泽林，以及政府部门总经理黄燕竹。黄总介绍有个周六福的项目近期在投标，可以让我们配合报一份价格，如果价格合适，在没有开标前她可以更换品牌。目前根据清单报价10.8万元。找成本部朱经理在沟通，有几个品牌参与，以及我们的报价是否有优势。	2025-05-09 00:00:00	17	t
450	2025-05-09	638	143	\N	通知樊总参与3月7日深圳举办的渠道会议。\r\n樊总介绍，深圳机场教育基地项目由达实中标，当前已经在与达实在沟通项目的品牌变更和后续采购时间节点。（达实当时投标不是用和源去配合，樊总支持的是另外一家公司用和源投标）	2025-05-09 00:00:00	17	t
451	2025-05-09	655	166	\N	邹总介绍，鹏峰项目由于和业主针对成本谈判没有谈妥（业主压价太低），所以三局选择主动退出。\r\n目前还没有选择哪家单位中标，等中标后再让代理商去找集成商对接，是否还有机会争取进一步配合。	2025-05-09 00:00:00	17	t
452	2025-05-09	655	166	\N	预计2月底3月初挂云筑网招标，采购需求已经提交给供应链部门。招标流程，第一轮重点技术参数核对，第二轮比价格，基本价低者中标。可以中标后再沟通优化系统事宜。	2025-05-09 00:00:00	17	t
453	2025-05-09	620	381	\N	已确定3月份正式签采购合同，下周和张兴一同拜访项目经理，沟通具体的采购详情。	2025-05-09 00:00:00	17	t
454	2025-05-09	611	127	\N	项目尚未到对应节点，由于是军用机场，图纸不能外发，等有施工图出清单了再让我们配合。\r\n本项目是纵横单线直接跟业主对接的项目，他们有话语权，拒绝让我方介入业主方，因全盘考虑需要。	2025-05-09 00:00:00	17	t
455	2025-05-09	661	171	\N	周工介绍中集项目是由王琦院长刚让他接手，还没有进行初稿设计，当前确定会有专网分布系统，他们对这无线对讲系统不是很熟悉，到时候让我们配合做方案。	2025-05-09 00:00:00	17	t
456	2025-05-09	630	136	\N	黄经理介绍，针对年前的询价，当时给到他的报价补充了遗漏项，他需要重新跟各厂家重新询价，但有的厂家尚未回复报价。黄经理说第一轮报价英智源和科立讯价格较优。（竞品：英智源、海能达、科立讯）\r\n通过多次拜访，了解黄经理的立场，找到其公司内部本项目的关键人（经过前几次的拜访，我提议将售前和销售介绍认识，他表示拒绝），为一下步公关做准备。从整体成本（产品质量和铺设施工、商务账期）角度出发对比竞品，打破绝对价格思维，拉小成本差距。争取跟关键人利益绑定。	2025-05-09 00:00:00	17	t
457	2025-05-09	645	152	\N	李工介绍，朱总认同了年前重新做的点位新增方案，为了保障新增方点位方案合理性，他建议最好能现场搭建天线测试。接下来需要跟业主方上会沟通，需要我们将新增点位说明给到他们，或者到时候配合到会说明。\r\n已经与李工利益绑定，朱总的述求是价格合理以及我们配合点位优化。本项目是以单价成本核算，信号覆盖度验收。所以希望在能看见天线的地方：裙楼和地下室多新增点位。但在实际施工中，在地面上的建筑原来一层一个点位，改为两层放一个点位。	2025-05-09 00:00:00	17	t
458	2025-05-09	609	125	\N	方工介绍：年前业主方要求他们修改施工图，后续到我们这块的时候会让我们配合重新修改方案。\r\n本项目因整体预算不足，方工要求修改过三轮价格。保障项目整体可控为前提，为了保留软件，采取第三方产品降价策略。已联系上业主方项目经理，对方以本事务不在范围内，让去对接设计院为由，不再沟通。后续工作还是需要由方工出面，让其介绍对接业主方的人员。	2025-05-09 00:00:00	17	t
459	2025-05-09	656	89	\N	李经理介绍，本项目已经中标，但我方之前的报价没有优势。（竞品：汉界、烈龙、武汉中元）给了指导价格，如果同意指导价格，他们会再跟我们谈判一轮。目前已经让张兴报了一轮价格，尚未有结果。\r\n本项目的汉界和武汉中元价格较低，已经找到了中通服本项目经理，想通过做王经理的公关工作，项目上以整体价格（品牌优势、产品质量、售后等）角度对比竞品，拉小价格差距。长期合作上争取与其的利益绑定。	2025-05-09 00:00:00	17	t
460	2025-05-09	631	138	\N	梁工介绍，今年3-4月会常驻项目上，目前C塔项目的进度没有那么快，之前我们配合的设计方案已经提交给业主，业主当时对无线对讲的需求还不明确，施工图最快今年5月前要出来，到时候还需要我们配合。\r\n已经争取到了梁工的领导刘汉伟副总的长期合作，业主方尚未接洽上，但刘汉伟答应后续会介绍业主方严经理，到时一起打配合，争取让我们给业主方介绍方案。	2025-05-09 00:00:00	17	t
461	2025-05-09	652	162	\N	何所长介绍，本项目 深圳壹创国际负责总包设计，华艺负责智能化设计。本项目属于地铁，地铁项目可能不会定品牌，最好跟总包或者智能化分包配合。\r\n我尽快找到业主方设计对接联系人，了解是否有品牌限定，以及本阶段是否有机会参与。以及本项目有哪些智能化总包参与，配合最有机会的一方，配合将我方系统作为控标项，做到参数或者品牌植入。	2025-05-09 00:00:00	17	t
462	2025-05-09	580	95	\N	李主任介绍，祐富百胜宝总部项目土建总包刚定，无线对讲的需求还没有，可以先提供类似工业园区的方案作为参考。\r\n在业主方还没有明确需求前，可以引导业主对无线对讲系统的功能，以及我方品牌价值植入。所以需要从业主方和设计院两条线切入，推动品牌植入工作。	2025-05-09 00:00:00	17	t
463	2025-05-09	609	125	\N	方工介绍：年前业主方要求他们修改施工图，后续到我们这块的时候会让我们配合重新修改方案。\r\n本项目因整体预算不足，方工要求修改过三轮价格。保障项目整体可控为前提，为了保留软件，采取第三方产品降价策略。已联系上业主方项目经理，对方以本事务不在范围内，让去对接设计院为由，不再沟通。后续工作还是需要由方工出面，让其介绍对接业主方的人员。	2025-05-09 00:00:00	17	t
464	2025-05-09	604	120	\N	变更销售跟进为为：周裔锦	2025-05-09 00:00:00	17	t
467	2025-05-09	631	138	\N	由于业主对专网通信系统建设尚不明确，要求采用光纤方案。目前还没有做系统图，给了图纸让我们配合出方案。	2025-05-09 00:00:00	17	t
469	2025-05-09	656	89	\N	已根据清单报价358968元。	2025-05-09 00:00:00	17	t
807	2025-06-04	40	8	609	目前北京集成商未中标，代理商淳泊跟踪的另一家集成商已中标，本月将进入批价流程	2025-06-04 01:35:26.089004	16	t
471	2025-05-11	\N	423	120	沟通增加记录1\r\n	2025-05-11 04:05:43.01168	5	t
472	2025-05-11	\N	\N	510	和刘林沟能项目进展，同意让我们配合，可配合系统图和技术规格书	2025-05-11 14:32:10.60599	13	t
808	2025-06-04	\N	165	610	配合完成清单预算	2025-06-04 01:46:46.246819	16	t
820	2025-06-05	115	435	\N	科思创系统内第三方常够产品按原价格再次报价，对客户采购要求做出响应。\r\nE188项目调试费用开票开具，同时尾款质保收据开具，交付给对方财务。	2025-06-05 07:42:06.919687	2	t
475	2025-05-12	451	259	\N	根据上周与业主沟通的上海中心大厦项目无线对讲系统评估报告的情况，完成评估报告并且与业主沟通进行了修正，确定提交报告的内容和形式，周二业主会召开物业管理部门的牵头会议，要求物业部门提供系统评估报告，然后和源将评估报告提交给物业部门，本次评估报告的内容不再局限于消防用350兆无线对讲系统的设备维修更换，扩展至400兆物业用无线对讲系统/光纤直放站数字化/智能平台化管理等等	2025-05-13 02:00:31.509212	7	t
476	2025-05-12	460	264	74	根据中芯南方业主需求上会依据最后确定的高精度定位需求（地图场景/定位终端）等细节与供应商沟通，落实到最终方案，并且提供相似案例编制进最终方案	2025-05-13 03:00:00.849406	7	t
477	2025-05-13	662	471	510	和刘林沟通清单量的问题，按其要求，调整好系统图和清单	2025-05-13 04:31:14.041424	13	t
478	2025-05-08	664	472	\N	已加业主微信，保持沟通，争取后面约见面； 	2025-05-14 01:40:00.848001	20	t
479	2025-05-12	664	472	\N	跟客户聊天，得知客户不是上海的，是南京的，先开始聊起来，争取后续约拜访；	2025-05-14 01:40:52.348701	20	t
480	2025-05-08	665	473	\N	客户表示现在很多地方信号都不好，机房什么的，所以对讲机不大用了，都用手机比较多，最近比较忙，过两周可以约，已加微信；	2025-05-14 01:49:17.6147	20	t
481	2025-05-08	666	474	\N	客户反馈室外的信号不好，1256都不好，34是好的；去年有联系过，但是搁浅了；客户希望我司上门查看下；	2025-05-14 01:52:34.610821	20	t
482	2025-05-12	\N	474	\N	总包还是希望我们能派人上门检查一下，但是内部沟通下来，因之前建议过对接人远程，但是对方表示酒店有活动不能开展检测，所以搁浅了； 另，质保是今年6月到期的，故此需内部开会再决定是否要上门帮客户检测；	2025-05-14 01:52:59.92157	20	t
483	2025-05-13	\N	474	\N	今天部门沟通下来，因6月客户的质保就要到期了，届时总包会撤场，到时可以联系下业主方；故此不用浪费公司成本进行跨城出差；已经建议了总包先行远程视频进行处理；	2025-05-14 01:53:29.359874	20	t
484	2025-05-14	250	399	512	西安的客户询价，和瑞林达邹总的报备的信息一致，协调邹总进行配合集成商深化和报价	2025-05-14 01:58:17.205169	13	t
485	2025-05-08	\N	475	\N	客户反馈没啥太大问题，去年换了个天线，加了微信，后续保持沟通；	2025-05-14 01:59:36.606931	20	t
486	2025-05-08	667	475	\N	客户反馈没啥太大问题，去年换了个天线，加了微信，后续保持沟通；	2025-05-14 02:00:59.812846	20	t
490	2025-05-08	669	478	\N	客户联系方式一直是关机，需要寻找其他方式进入；	2025-05-14 02:35:11.685867	20	t
491	2025-05-08	670	479	\N	客户表示此项目已结束，也没有维保什么的，先加微信后续保持沟通；	2025-05-14 02:39:10.998634	20	t
492	2025-05-08	\N	480	\N	对接人反馈当出现问题的时候，没有可视化；溯源能力太差了；可以关注官网；声称因为标的关系不让加人，后续可以再电话沟通；	2025-05-14 02:43:03.93067	20	t
493	2025-05-08	672	481	\N	对接人表示没什么大问题，先加微信，后续保持沟通；	2025-05-14 02:50:28.91361	20	t
494	2025-05-08	673	482	\N	客户表示没什么问题，先加微信，争取后续约拜访；	2025-05-14 02:54:25.714166	20	t
495	2025-05-14	664	472	\N	跟客户约下周，下周一定具体时间；这个客户比较喜欢喝酒应酬，到时候再深度聊聊；	2025-05-14 07:23:12.55788	20	t
496	2025-05-14	672	481	\N	跟客户约了周五下午拜访，已拿到合同，做好准备再去；	2025-05-14 07:24:27.392536	20	t
497	2025-05-14	673	482	\N	约客户，客户表示这两天不在上海，下周一再定具体时间；	2025-05-14 07:25:03.629672	20	t
500	2025-05-14	\N	427	\N	新一年度的通信费用即将到期，客户费用确认，直接开票。	2025-05-14 08:04:04.707693	2	t
501	2025-05-08	119	435	42	客户本月会再将现场有故障的机器筛选出来，不能用的机器会购买新的，在原150套的基础上增补；提前给用户做好频率文件。	2025-05-14 08:07:56.406864	2	t
507	2025-05-14	457	470	13	深圳中芯国际ERC工程改造负责人沟通，根据之前提供的改造方案和初步报价，ERC部门已经将需求上会并发给采购部门，采购部门会向供应商进行询价，目前询价工作已开展，如和源收到询价会告知业主需求部门这边然后对方案和报价需求进行进一步沟通；	2025-05-15 02:39:50.432359	7	t
508	2025-05-09	675	483	\N	已把我司产品样品给到对方，需要下周把我司参与项目详细化的公司介绍给到客户，以及营业执照跟产品信息等；\r\n目前有另一家公网的产品在竞争，会把我们两家的产品一起给到需求方；	2025-05-15 02:42:15.881194	20	t
509	2025-05-15	451	259	\N	业主方面5月13日下午进行了业主与物业管理部门的会议，业主要求物业管理部门提交2025年上半年系统运维评估报告，次日物业部门向和源商务提出相应要求，目前评估报告已与业主方沟通定制完成，我已把报告交给商务人员，会在5月15日下午交给物业管理部门；	2025-05-15 02:44:31.422297	7	t
809	2025-06-04	\N	518	611	完成初步估算	2025-06-04 02:53:37.895807	16	t
816	2025-06-04	670	479	\N	拜访上海银行傅颖毅：客户表示之前脱保的原因，除了价格跟服务等外在原因，最关键的是业主方现在选定的是云思做这一块，这个项目现在已经不属于中电科来管了，建议我可以从云思那边入手；现在跟我们的项目是中山医院的，李华伟来对接的；加了中电科也是负责核价后端的一个人，宋丹，后续如果有问题可以随时联系。 云思有个汇添富基金大楼的项目，焦通在负责，约了下周拜访，准备到时候一起摸一下情况；	2025-06-05 01:37:22.522635	20	t
821	2025-06-05	673	482	\N	因原对接人鲍磊态度不大好，直接冲；来了一个保卫处的人，此人表示对讲机是坏了几台，但是不知道什么原因一直没报修；鲍磊这里也没有反馈过，但是实际是在使用当中的；因绕了一圈，在博物馆外围的保安处看到了MOTO的对讲机，说明客户这里是在用的； 我过去说到是消防的系统跟对讲机，博物馆的人比较重视这句话，我思考是否可以从消防入手，如果在鲍磊不配合的情况下；对接人还表示管设备的老师今天不在，但是我的名片收掉了，号称会转交给相关的老师。后续可能再跑一趟。而且我们的质保还在期内，需要从另外个维度思考下。	2025-06-06 02:15:12.389961	20	t
830	2025-06-04	609	125	43	无线对讲系统调整不大，业主传达如果还能进行成本压缩的，需要适当压缩。\r\n业主之前考虑过两种巡更方案，分别是蓝牙和RFID，之前已经跟业主介绍过蓝牙方案，业主也比较认可。\r\n接下来，还需要招标技术文档编写，做好把控。	2025-06-08 14:09:44.032377	17	t
838	2025-06-03	\N	10	3	沟通了项目目前进展情况，预计本月业主会发起招标	2025-06-09 05:39:34.355378	16	t
843	2025-06-10	451	259	\N	为推动350兆400兆无线对讲系统的设备更新及升级改造，与业主方沟通定于本周周五现场专项会议，上海中心大厦业主工程部负责人和世邦魏理物业公司总经理参会，物业公司弱电负责人介绍无线对讲系统维护工作，和源通信负责人介绍系统状况及设备更新情况系统升级改造方案等等；	2025-06-10 02:02:02.015411	7	t
869	2025-06-12	451	259	\N	与上海中心业主沟通周五上午在上海中心针对上海中心大厦无线对讲系统专题会议的沟通细节，确认了推动议题的方向和阐述设备更新升级的必要性等等细节；	2025-06-12 05:54:15.901096	7	t
844	2025-06-10	155	260	\N	与上海中心大厦物业管理有限公司确认本周五现场专项会议，向上海中心大厦业主与世邦魏理物业公司领导汇报无线对讲系统的维护及设备更新功能提升等事宜，与物业弱电管理部门负责人沟通会议详细汇报内容，并与物业公司总经理确认；	2025-06-10 02:05:45.45074	7	t
852	2025-06-10	680	477	\N	今天跟时雪峰一起上门海昌，做排查故障，结果如下：海豚馆上次检查是不好的，原来是光路故障，今天处理之后就好了。 珊瑚馆，显示功率低；奥特曼馆，是光路故障；办公楼，远端机功率低，导致室外天线覆盖信号弱。。停车楼，属于光路故障。 火山冰川馆，光弱。 跟业主方沟通了以后，回来会做一份维保的报价给到对方； 同时业主拿出了5台对讲机，要求一起报个维修的价格，明日处理；	2025-06-10 15:29:14.91021	20	t
867	2025-06-11	460	264	\N	与业主方沟通中芯南方无线对讲系统的系统维护的工作，业主肯定了维护工作的必要性，将在下周上半周前提供一份针对中芯南方系统的维护方案给到业主方；	2025-06-12 05:47:02.351695	7	t
872	2025-06-10	363	307	566	目前代理商瑞康推动品牌资料报验提交和源品牌确认，预7月底8月份开始设备进场，后续跟进合同签约批价。	2025-06-13 02:50:05.506867	15	t
561	2025-05-16	508	288	518	本周与付言新沟通，目前烈龙价格还在不断放水，但付言新与蓝极星负责人宋治军多年合作关系，商务上还是有一定把握，现在商议策略，产品价格就参考九星城业务，稳定客户关系，提前发起批价，他这边承诺宋治军价格与九星城一致后，推进项目现场品牌报验，锁定和源品牌	2025-05-16 03:17:51.826921	14	t
573	2025-05-16	563	234	524	拜访庄彦，国信安今年新增业务较少，明显放缓，仅了解到一个，但还没确定具体启动时间，谁来负责。国信安内部分为企划部（设计），房产部（工程）和招采。企划部主要负责业务前期设计对口，制定方案及技术要求，会给予招采品牌推荐，最终到集团招采来确认招标品牌。目前手上跟踪业务，张江人工智能岛预计要到今年年底才会启动，现场在做管线预埋，预估要幕墙安装完成才会正式启动，幕墙计划10月份完工。至于张江创新药分为四个地块，庄彦负责的03C、K地块，分别是派汇及铭鹭中标，预计三季度就要启动实施工作。而04A、C地块超哥负责，原定通过庄彦引荐，但超哥临时有事不在，下次找机会拜访	2025-05-16 03:59:14.234162	14	t
583	2025-05-16	677	486	\N	与合作供应商产品技术负责人沟通上海中芯南方FAB区域上海厂和南方厂的平面图纸，根据业主提供的平面图纸融入目前确定的方案，争取下周把方案进一步修正，尽可能匹配中芯南方现场的使用场景，然后与业主进一步沟通，推动业主上会提出需求；	2025-05-16 04:08:10.579528	7	t
588	2025-05-15	423	249	\N	与沪东中华造船设计院人员沟通中船长兴造船基地二期(EPC)项目，获知该项目在沪东内部的名称是长兴二期建设项目，目前由沪东中华造船本部管理部进行岸线基础建设；	2025-05-16 04:14:40.333683	7	t
810	2025-06-04	\N	519	609	该集成商已中标本项目，目前已与代理商进行沟通。	2025-06-04 02:57:08.957916	16	t
817	2025-06-05	174	339	100	康桥二期项目和总包的最终采购清单和报价已洽谈好，代理商已弄好合同，发给总包进行确认，走签约流程	2025-06-05 06:06:04.664847	13	t
822	2025-06-06	\N	298	102	张江创新药项目与代理商一同拜访，该项目分为两个地块，目前现场都在做管线预埋，系统品牌提交甲方都已确认，03C地块目前代理商配套深化方案确认，预计项目无线对讲启动实施在8月份左右	2025-06-06 02:21:24.166669	14	t
824	2025-06-06	497	186	108	该项目同代理商了解，现阶段还在确认实施方案，现场方面还在做管线预埋，预计8，9月份启动无线对讲实施工作，按此施工进度预估8月份会落实商务情况	2025-06-06 02:31:44.756868	14	t
831	2025-06-04	717	142	55	肖经理表示上级已经过会，专网无线对讲系统确定建设，希望我们配合设计院做好成本把控。\r\n设计方蓝工介绍，业主方比较在意供应商跟设计院私下沟通，如果下回要开会，最好通过业主方通知设计院。\r\n	2025-06-08 14:21:28.539889	17	t
833	2025-06-03	636	141	31	配合项目上做好品牌报审资料，审批通过了再签合同，避免临时出现其他变数。	2025-06-08 14:31:00.564088	17	t
775	2025-05-28	\N	21	573	目前经与集成商确认，天线采用MA10	2025-05-28 06:27:37.366924	16	t
839	2025-06-09	681	215	32	该项目与上安九分龚俊瑜就目前清单初步确认最终价格，通过了解上安九分内部也基本确认，有关品牌及供应商提交到项目部，项目实际负责人为蒯乃骏。与蒯乃骏沟通了解现阶段他们与四建安装合同还未签订，现场在与甲方地下部分负责人李继栋汇报智能化各子系统品牌，和源初步确认，进一步计划就是各子系统进行方案汇报，最终先把品牌给予确认，同时沟通过程中了解，无线对讲系统确定地上、地下为同一个品牌，至于航空模块部分因为牵涉机场，所以后续可能还需要待机场相关负责人确认后还需要进行汇报。现场实施确认为明年年中以后，今年至多完成方案深化，确认采购清单。目前所存在的风险即为机房核心设备是否能够保留在上安，因从系统原先规划及招标上核心设备在地上部分，如果这样就可能需要通号明确是否也选用和源品牌，不一定以上安建议为主	2025-06-09 05:49:22.926652	14	t
845	2025-06-10	720	521	\N	与新美阁展会负责人沟通2025年开办展会需要向管理局申请临时频率的技术咨询事宜，对于不同类型终端产品是否需要进行临时频率申请沟通讨论；	2025-06-10 02:16:18.681064	7	t
861	2025-06-12	715	518	611	根据沟通对设计方案及项目预算报价进行了调整	2025-06-12 03:42:32.376173	16	t
862	2025-06-12	68	20	295	经沟通，项目因资金问题暂停了。	2025-06-12 03:44:22.312229	16	t
864	2025-06-12	37	40	239	因资金问题，项目暂停。	2025-06-12 03:48:35.178476	16	t
865	2025-06-10	55	25	105	经沟通，该项目除酒店区域，工区区域预计7月进入招标。	2025-06-12 03:52:06.85392	16	t
868	2025-06-10	677	486	\N	与第三方技术负责人确认人员定位方案业主方最新提出的对于终端产品方案阐述的细节等信息，修改版尽快完成以便与业主进一步沟通；	2025-06-12 05:49:22.949555	7	t
870	2025-06-12	457	470	\N	业主方负责人联系表示他5月份已经向采购部门提出了系统改造的询价的需求，但是我们确认这边未收到采购的询价邮件，业主会联系相关采购人员；	2025-06-12 05:58:10.95488	7	t
873	2025-06-13	398	323	180	目前方案已经确认，对讲机业主选用了中兴。最终价格和商务已经初步和EPC总包确认，预计8月份进场。	2025-06-13 02:52:04.484488	15	t
651	2025-05-14	93	81	549	等待主设备标段确定品牌	2025-05-16 06:36:35.148158	16	t
667	2025-05-13	85	64	146	目前项目已进入穿线施工，设备品牌暂未确定。该项目为（DK20230133地块）	2025-05-16 06:54:06.176394	16	t
658	2025-05-15	20	30	\N	目前还没开始	2025-05-16 06:42:59.429515	16	t
811	2025-06-04	421	445	122	与客户沟通本年上半年度维保工作安排，安排在6月6日上午。\r\n另与客户沟通一台远端机设备事宜，电话采购，采购告知订单已在核签，预计下周完成下单。	2025-06-04 06:25:47.394649	2	t
812	2025-06-04	132	444	\N	与客户沟通本季度维保工作安排，安排在6月6日下午。	2025-06-04 06:28:37.089436	2	t
818	2025-06-05	200	365	2	太原机场云时代打算分包山西戎安天下科技有限公司，和山西戎安天下科技有限公司张经理沟通方案和清单 	2025-06-05 06:20:06.506927	13	t
825	2025-06-05	667	475	\N	客户表示现在业主无需维保的原因是因为我们的设备质量太好了，也没出过问题，所以取消了维保；这个真实原因还是等下周见面了再探寻；	2025-06-06 02:53:41.78925	20	t
826	2025-06-04	680	477	\N	下周二跟时雪峰这里去海昌检测，已跟业主定好时间沟通好；用一天的时间搞定所有检查；（我的想法是：帮客户先做检测，然后拿出报告再摸清楚客户的预算情况等；）	2025-06-06 02:54:45.610356	20	t
832	2025-06-03	718	381	202	他还在争取，把采购订单拆分成线缆跟对讲两部分，这样就能绕过内部竞价，目前还在沟通中。	2025-06-08 14:27:43.439941	17	t
853	2025-06-11	693	341	535	邹娟配合的深圳达实成都分公司已中标，近期邹娟会去拜访客户，了解项目节点	2025-06-11 06:45:59.955565	13	t
704	2025-05-13	59	89	563	配合完成项目方案与清单初步设计	2025-05-16 07:40:21.224562	16	t
705	2025-05-13	70	6	523	沟通产品样品报验事宜	2025-05-16 07:41:53.45574	16	t
706	2025-05-14	\N	7	531	沟通新老产品型号等相关事宜，落实后续项目事宜	2025-05-16 07:43:08.325258	16	t
707	2025-05-15	\N	7	531	出具老产品停产证明事宜	2025-05-16 07:43:55.814769	16	t
708	2025-05-12	\N	12	62	沟通了下一步项目推动事宜	2025-05-16 07:46:42.715642	16	t
709	2025-05-15	77	21	62	与350M设备厂商沟通商谈350M直放站选型配合事宜。	2025-05-16 07:47:49.026152	16	t
710	2025-05-14	\N	60	194	沟通了项目目前进展，项目刚刚重新准备启动	2025-05-16 07:51:12.95617	16	t
711	2025-05-15	77	21	63	指导、协调代理商完成施工图深化。	2025-05-16 08:03:48.819745	16	t
712	2025-05-16	20	30	65	该项目（地块项目编号DK20230517/20230518地块）目前还未开始确定各系统品牌,	2025-05-16 08:37:58.174834	16	t
714	2025-05-16	672	481	\N	客户表示之前的维修一直得不到很及时的报修跟反馈，比较慢，担心导致消防的检查，会有罚款。我表示从今天起不会再有这种事发生，可以直接找我，肯定会及时的。\r\n并且愿意下次引荐领导见面，不过主要负责的人还是他。看了客户在5楼的机房，比较热，提出可以适当的做降温等处理，否则会有设备损耗的隐患；\r\n聊到维保已经过期了，不过内部讨论下来，还是等接触到他领导了再问；\r\n \r\n\r\n	2025-05-16 09:22:29.74442	20	t
715	2025-05-16	182	350	307	华东院开始智能化设计，配合陈工进行前期图纸和方案设计	2025-05-16 09:25:12.203834	13	t
716	2025-05-16	675	483	\N	徐家汇政府的朋友表示：我们的对讲机距离不够，从政府门口到了宜山路地铁站就没信号了，大约1公里不到； 已经帮我在问街道这里的需求了，看看是否符合；	2025-05-16 09:35:21.640588	20	t
717	2025-05-12	\N	141	31	我方报价同比优于对方，张坤成当面答应了，等20号老板出差回来后，他会跟老板当面汇报，基本没有太大问题。	2025-05-18 15:40:11.955764	17	t
718	2025-05-13	\N	148	7	采购李经理介绍，本项目今年估计还有30-40万（面价）需求。\r\n李冬表示，本项目由于当时为了中标，降低了其他产品的价格，以及客户付款要7个月。所以需要我方申请价格支持。	2025-05-18 15:43:49.725688	17	t
719	2025-05-14	\N	\N	514	刘明勇，明确了会用我方品牌去参与投标，到时候会跟我方拿唯一授权等投标资料。	2025-05-18 15:45:38.770186	17	t
720	2025-05-13	654	164	165	城信科技采购林经理表示，后续会把项目经理、采购部负责人马总，以及销售拉群，对接后续的工作。\r\n张兴说本周还有其他集成商在询价，听说集成商还没有定。\r\n宋洋洋表示也要参与，他说跟工务署有相应关系，他来对接可以争取一个表较好的价格。\r\n本项目是中建科工降低30%价格中的标，智宇张总介绍，他们找中建科工谈过，价格给的很低，几乎没有利润，所以没有接。本项目的参数和品牌已经被我方锁定，集成商想要推翻有一定的困难。\r\n	2025-05-18 15:47:00.469616	17	t
721	2025-05-13	\N	490	580	霍尼韦尔集成林总介绍，本周项目经理出差了，需要约下周当面过方案，以及清单。	2025-05-18 15:48:04.378692	17	t
722	2025-05-14	\N	89	202	一标段。拜访达实项目时经理，他介绍对方用中元在报价，除线缆外的整体报价在30多万。我让张兴把整体清单的价格控制在28万内，和源价格根据达实库内采购价保持，将其他产品降价。时经理对我方价格比较满意，最快下周需要给业主报审品牌，所以下周会给我们答复。\r\n侧面了解到，李小飞在用中元、汉界运作本项目。\r\n	2025-05-18 15:49:18.798907	17	t
797	2025-05-28	577	93	604	项目是由他们这边负责做的设计，目前已经启动土建的有1和2地块，建筑面积有17万平方米，施工图最快7月可以开始。	2025-06-02 15:17:26.645926	17	t
723	2025-05-15	600	118	188	华南理工建筑设计院智能化黄主任，黄主任介绍，本项目整体进度没有那么快，建议我方不要太着急，施工图还没有进展，如果外界有关于本项目的总包询价，都是基于之前的土建设计做的。	2025-05-18 15:50:30.656239	17	t
724	2025-05-14	\N	103	235	项目建设到一半。\r\n与裴小印拜访三局智能二分公司文经理，他介绍下一步要跟业主过智能化系统，业主方倾向首选本地品牌。\r\n与裴小印拜访业主方胡经理，他表示后续会到我方的案例上考察，品牌是由他来拍板，但是也会走流程过会。\r\n接下来会督促裴小印做好业主的拜访，以及品牌植入工作。\r\n	2025-05-18 15:52:26.950092	17	t
725	2025-05-15	\N	111	53	拜访广州鑫宇视通曾帅，他介绍本项目的初版方案的价格已经报给业主了，暂时没有反馈。但对比市面上我方价格太高，希望后续落地过程中可以有一定的折扣。	2025-05-18 15:53:29.061075	17	t
726	2025-05-16	590	107	8	拜访鼎信科技采购秦经理，以及技术总监史总，本项目是跟南方电网合作的一个园区，由于他们也是业主方，所以怎么定方案的品牌，都由他们自己说了算。\r\n史总说他在广东省应急中心有些关系，据说今年有个110亿的应急项目会下来，他先去了解有多少无线对讲的产品，如果我们有机会，后续会加强跟我们的沟通。	2025-05-18 15:54:44.474206	17	t
727	2025-05-16	\N	99	581	采购张经理介绍，已经投标，暂时还没有反馈结果。	2025-05-18 15:56:07.747437	17	t
728	2025-05-14	\N	165	148	近期招标，需要我方帮忙把控，限制其他代理商参与。裴小印介绍，他已和业主方沟通好，非和源品牌不让参与投标。	2025-05-18 15:58:24.005026	17	t
730	2025-05-15	679	256	\N	之前的马建强已经退休，现任是潘继峰，客户现在每年2万多的维护费用，100多台机器。 这个钱是交给政府的，无线电管理局。 目前公网对讲机大概有几十台。客户反馈有的时候进行展会的时候，叫不到，会有干扰。通过中继台，有延时，1秒左右。现在全部都是数字的。马总之前的部门现在没有在用公网的机器，是别的部门在用。 客户现在MOTO的对讲机基本不用，已经积灰，系统表示没出过问题，质量还不错；跟客户介绍了公司产品册，如果有需求可以直接问我，保持联系。	2025-05-19 02:15:24.102634	20	t
731	2025-05-19	\N	477	\N	张工给了一个新的联系人，俞工，约定了明天去看现场；	2025-05-19 09:31:02.588149	20	t
732	2025-05-20	182	350	307	和陈工沟通方案的问题，进行相应调整，将调整的系统方案和预算给到陈工	2025-05-20 08:19:44.790037	13	t
1178	2025-08-07	\N	164	165	目前已经确定智能化分包是诚信科技，跟售前约定下周拜访，同意介绍项目经理以及销售负责人。\r\n主要判断本项目的品牌选择和成本是哪个部门以及谁是关键人，跟关键人了解他们的述求。	2025-08-10 13:58:54.109973	17	t
1179	2025-08-08	\N	381	692	配合达实投标，售前介绍本项目没有品牌限定，建筑面积10万平方米，技术参数符合的话用我们的品牌投标，我方已根据图纸深化数量。	2025-08-10 14:06:38.916579	17	t
1298	2025-08-21	636	141	653	当前项目在沟通一些细节问题，还没有确定下来。	2025-08-24 15:27:25.25001	17	t
734	2025-05-20	680	477	\N	对接人的职位是：信息部经理，谈了两轮，第二轮的时候带了他们的运营经理周杰周经理一起来，周经理表示：早些年我们给到海昌的维护，第一版报价是6万整，第二版是4万多。这是2023年的维保报价，当时跟公司表示过太贵了，但是还是此价格，故此才选了现在的弱电维护；现在的弱电维护很有可能还是我们的代理商（这是俞工透露的）； 但是现在的弱电维护呢没办法完全解决客户目前的问题； 客户现在的问题是：园区部分场馆的远端机信号不大好，需要维修。 但是现在的弱电维护并没有办法解决； 对讲机的问题倒是小问题，更换下配件即可，现在远端机是大问题； 周经理表示因现在已经是年中，如果要更换供应商也要等到12月份了，到时候明年的预算就出来了；当然前提是我们的价格要合适，不能太贵； 后续有什么新增也可以继续找我们；  我个人认为这家还是可以挖掘的，比较有价值，后期可以带着技术再上一次门。	2025-05-20 11:36:45.093581	20	t
735	2025-05-21	241	243	593	施国平响应用户需求，寻找到我们进行方案配套，具体项目情况及细节需要进一步沟通，初步沟通端午后拜访	2025-05-21 05:45:15.439254	14	t
736	2025-05-19	507	288	518	与付言新沟通确认清单明细，发起业务批价申请，推进渠道批价确认	2025-05-21 06:22:31.061746	14	t
738	2025-05-19	508	288	187	与付言新沟通确认清单明细，发起业务批价申请，推进渠道批价确认	2025-05-21 06:23:33.694554	14	t
739	2025-05-20	681	215	32	配合项目经理提交和源品牌报验资料，并提供系统方案介绍，给予用户确认，从而锁定和源品牌	2025-05-21 06:28:29.038273	14	t
740	2025-05-21	\N	229	133	拜访项目现场滕顺，经沟通了解项目计划8-9月份启动设备安装，7月份就开始穿线，今年要求整体交付，因用户住宅预售良好，推进代理商与挂靠银欣客户商务洽谈，预计6月份商务会有结果	2025-05-21 06:31:23.107205	14	t
742	2025-05-20	478	350	64	与毛晶轶复核WSP沟通情况，的确待综合机电招标完成后会启动智能化品牌确定工作，但按毛晶轶意思他有把握能推动品牌的确认工作，后续还需要进一步跟进各个负责人，推动招标品牌植入锁定工作	2025-05-21 08:16:52.403056	14	t
487	2025-05-08	\N	251	\N	客户刚刚开了7000块的发票，加了微信，后续保持沟通；	2025-05-14 02:05:20.314574	20	t
744	2025-05-21	683	478	\N	现名上海浦东丽晶酒店，原来的须工联系不上，直接上门；经前台引荐，接触到了工程部的负责人，工程部经理，方俊斌，方工；对方表示因是2017年的故障排查报告，目前并不知晓是否还在使用； 对讲机是没有在用了； 先加了微信，后续继续跟进； 我会尝试接触到关键决策人，努力把供应商的关系重新建立起来，这是我的销售思路；	2025-05-21 10:13:57.193796	20	t
745	2025-05-20	\N	423	513	维保完成，签订合同，开票。	2025-05-21 13:15:25.123719	2	t
746	2025-05-21	119	435	42	沟通客户目前订单流程，预计6月中旬出PO单。	2025-05-21 13:17:20.180731	2	t
748	2025-05-22	665	473	\N	上汽陈琦拜访，此人是业主负责人，跟着董老师一起去的，客户反馈从监控室到A栋大楼的信号不好，经常叫不到；这个问题从去年到现在了，去年帮客户上过一次门，维修过信道机，后面好了；目前是保安在使用，物业并没有在用了；现在这个问题的话，本次见面客户表示如果是免费的可以来；  因本次是跟董老师一起上门的，客户没多表示什么，我打算后期再维护下，单人上一次门，约客户喝个咖啡聊聊；因保安表示了MOTO的机器不好用，下次上门的时候我准备带着我们和源自己的对讲机上门给客户演示；尽量跟业主建立起关系，才能更有助于后面的合作；	2025-05-22 09:43:43.310615	20	t
749	2025-05-22	460	264	125	与业主就P3改造项目合约签订后的部分实施进度现场工作等进行沟通，初步沟通本次改造后对整个系统的监控平台进行评估和建议方案，由于中芯南方P1P2P3属于不同时期的建设项目，所以设备软件都有版本和硬件上的差异（利用浦东机场卫星厅软件升级可对中芯南方P1硬件进行升级）；	2025-05-23 01:34:08.941607	7	t
750	2025-05-21	677	486	\N	与国鑫音达沈总沟通上周确定平面图纸，最终使用终端后的初步方案，对方案的一些细节进行修正，本周五沈总会给到第二版；	2025-05-23 01:38:29.552679	7	t
751	2025-05-22	423	249	\N	与沪东中华造船厂人员沟通目前船厂在无线对讲系统上的使用情况，由于船厂在无线对讲系统上使用并不广泛，所以对于系统本身并不熟悉，初步介绍了无线对讲系统及产品，并希望通过有效途径把系统概念传递到相应的设计平台	2025-05-23 01:48:22.13646	7	t
752	2025-05-20	457	470	13	中芯国际深圳有限公司ECR需求负责人对改造方案/录音方案进行询价确认，并表示如果收到采购部的询价需提前与他沟通并确定报价方案	2025-05-23 01:53:20.530155	7	t
753	2025-05-23	451	259	\N	本周上海中心大厦业主参加海口绿色建筑和建筑节能大会，但是业主表示已经收到我们提交给物业部门的系统评估及建议报告，等业主回来后见面沟通后续推动方法	2025-05-23 01:56:11.989974	7	t
754	2025-05-21	115	435	42	确认科思创本次较大数量采购防爆对讲机事宜，确认大致数量190+，PO单预计在6月10日至6月15日发给和源，然后与张总确认上述甲方信息，确保供货方为此批供货提供足够的货量及及时的供货时间；	2025-05-23 02:00:35.068948	7	t
755	2025-05-23	508	288	187	与一标段江苏金鼎现场项目经理许华沟通，了解福玛与他们还在配合调整深化方案，主要是制图方面的细节问题需要改进。按许华透露情况，品牌设备资料已经提交，等待审批回复，待图纸完成后也需要尽快提交审批确认。现场实施进度，桥架材料他们与甲方已经落实，在抓紧备货，待材料到位后就会立即安装，有关无线对讲预计7月份就会启动材料进场，按此情况预测许华会在6月份发起采购计划	2025-05-23 03:34:21.987252	14	t
756	2025-05-22	685	494	157	拜访徐畅慧，与徐畅慧中午便餐，加强商务关系，商议项目合作。目前5，6号地块智能化后续会同时招标，现阶段先把方案和设计公司落实确认，后续按徐畅慧透露信息，可能会让卓展作为顾问，届时再看招标文件如何植入，有关招标品牌方面，徐畅慧有意向合作，会帮助植入招标品牌。至于潜在集成商，他提及到益邦，但可能也只是做其中一个地块	2025-05-23 04:20:43.21811	14	t
757	2025-05-22	\N	119	580	项目经理史存鑫表示，目前他手头上还有其他项目没有结束，最快下个月到罗山科技园项目。由于之前项目投标是没有品牌要求，所以后续价格可能不会太高。	2025-05-23 10:07:55.375205	17	t
758	2025-05-21	\N	125	43	设计方工介绍，本项目业主由于要压缩成本，施工图还要重新修改，以及我们的系统方案都要重新做过。本来5月份的招标要推到7月份，业主要求他们6月中旬提交施工图。	2025-05-23 10:10:56.926926	17	t
759	2025-05-23	628	135	33	项目经理胡总介绍，项目的施工进度有点慢，预定本月的招标比较要推到6月进行。\r\n副总林嘉豪介绍，近期没有参与其他的新项目。	2025-05-23 10:14:26.864389	17	t
760	2025-05-19	654	164	165	钟总介绍，他目前对于该项目没有决策权和管理权，预计他会到广西项目去帮忙。本项目目前在基坑状态，后续智能化有可能会分成两个标段来招，城信会是一个，因为他们的报价低，另外一个还没有浮现出来，有消息了到时候会通知我这边。	2025-05-23 10:18:44.134171	17	t
761	2025-05-22	621	381	202	项目经理表示中元把价格降到了我们的水平，而且公司领导也找了他来打招呼用中元（给他们领导打招呼的人是宇洪），他会两边都不得罪，品牌都会上报。\r\n采购唐经理表示到时候会帮我们，只要在价格上同等或者优于对手就可以。	2025-05-23 10:25:02.804629	17	t
762	2025-05-23	\N	141	31	张坤成说本周老板没有回来，但这个事情不会有太大变化。	2025-05-23 10:27:51.361454	17	t
763	2025-05-19	593	112	72	本项目是中山大学租用粤芯的地方来做科研，前期无线对讲方案是由粤芯来指导完成的，需要等中山大学的款项到位才能采购，目前在等最后的申请批流程。	2025-05-23 10:30:54.943802	17	t
765	2025-05-20	632	138	218	刘总介绍，近期已经跟业主方的刘总提过我们的品牌，刘总建议前期要跟前端的项目上的阎经理按照流程走通先，到时候如遇到问题，或者品牌的流程走到他这边他会帮忙。	2025-05-23 10:40:02.742936	17	t
766	2025-05-21	620	381	594	配合投标项目，没有品牌要求。	2025-05-23 10:42:46.664156	17	t
767	2025-05-22	\N	162	25	当前金证已经中标。投标前信元说用我们品牌配合金证投标，后来了解到信元觉得我们价格高，就用自己品牌报价给集成商配合投标。\r\n当前已经跟金证售前和采购在协商，改回我们品牌。	2025-05-25 12:17:47.300177	17	t
876	2025-06-12	\N	151	620	售前李总介绍，终端品牌：海能达、建伍、摩托罗拉，天馈没有品牌限制。本项目下周二投标，目前知道参与本项目投标集成商：万安，中国电信海南分公司。	2025-06-15 13:18:20.573356	17	t
488	2025-05-12	\N	251	\N	客户需要我司盖章上半年维保小结，约了明日下午上门拜访；	2025-05-14 02:05:49.735842	20	t
768	2025-05-23	664	472	\N	1.松江站客户拜访：对接人许涛，职位是工程部部长； 上面有1个项目经理，邵志超； 身边是一个安保经理，张淏；  不过邵志超是95后，年纪太小，平时很多事情都要咨询许涛的意见，实际掌权的还是许涛；  我们的系统在物业办公室对面的机房里，许涛表示只有对讲机只有4个频道，不太够用，看看是不是可以增添； 另外，此3人的关系比较要好，平时都会拖家带口的进行下班后聚餐或者同事间的娱乐活动； 当天跟3人一起吃了顿饭，这个项目的同事关系都是比较和谐的，企业性质属于半国企，国资委旗下的半商业性交通枢纽；大头是万科。 项目部也是有指标的，不仅仅是花钱也有赚钱部分；并且现在也在找人，说明是有预算的； 3人在吃饭状态会聊很多，家常跟工作都有 ；\r\n此项目目前属于刚启动状态， 我个人感觉可以进行一个长期维护，通过跟物业这里建立关系，应该是能够得到单子的后续。 	2025-05-26 06:20:22.631368	20	t
792	2025-05-29	115	435	\N	双方框架协议在6月30日到期，客户采购部因第三方摩托罗拉产品金额达到需要公开招标，客户告知会在协议结束后进行公开招标第三方产品价格，告知对方我司第三方产品价格内包含产品的写频等服务项。	2025-05-30 06:29:08.062688	2	t
794	2025-05-30	546	223	603	拜访闻锋，了解到该项目在方案扩粗阶段，用于项目申报审批概算，待概确认后才会启动智能化招标设计	2025-05-30 07:21:53.035658	14	t
795	2025-05-28	\N	148	599	目前与代理商沟通好了，在走批价流程。	2025-06-02 14:28:38.950518	17	t
796	2025-05-27	634	139	25	陈经理已让我方配合重新报价，价格对标信元。有优势的话可以争取变更。	2025-06-02 15:03:59.202079	17	t
798	2025-05-28	\N	381	202	项目时经理表示本周会上报品牌，让我们找采购那边关注询价动向。	2025-06-02 15:18:24.228702	17	t
799	2025-05-29	\N	93	577	集成商中通服介绍项目六月份开标，目前竞争激烈，如果还有降价空间希望我们能全力支持，节后开始议标。\r\n已答复对方，如果能中标，我们会有一定的议价空间，到采购阶段我们会给与支持。	2025-06-02 15:20:51.291259	17	t
800	2025-05-30	\N	171	595	已和八局项目经理公经理联系，节后上班到现场拜访，希望通过介绍本系统的重要性，以及了解他个人是否有诉求，争取到他的支持。	2025-06-02 15:27:12.968792	17	t
802	2025-05-27	\N	164	165	宋洋洋介绍已经和中间人约好工务署方的人，争取到7-8月份拜访（项目进展不快），工务署方能答应做到，集成商上报品牌的时候，如果不是和源的就打会去重报。	2025-06-02 15:36:34.250961	17	t
803	2025-05-26	\N	147	161	万睿销售介绍，本项目六月份招标，技术参数和品牌都已经按我方要求写入招标文件。	2025-06-02 15:38:25.700838	17	t
1180	2025-08-05	628	135	33	智能化项目经理胡程序介绍，目前比价是大系统，无线对讲最快下周开始，要看各部门的进度。 近期没有涉及到无线对讲的新项目。	2025-08-10 14:28:27.191039	17	t
1181	2025-08-05	577	93	604	本项目还在做系统设计，不会采用过于成本过高的系统，由于预算有限，到施工图节点让我们配合参数，到时整体的方案会由他们上海团队来牵头做。 	2025-08-10 14:31:16.861044	17	t
1182	2025-08-07	\N	546	679	智能化分包项目经理张巡万介绍，已经跟业主介绍我方品牌和优势，以及终端和天馈使用同一品牌的优势，接下来要看业主是否有意向，如果业主出现松动就让我们配合出个说明给设计院，争取到设计院再组织业主、总包方、设计院、监理方过会。周五跟张经理确认，业主方还是没有松动的意向。	2025-08-10 14:43:26.626132	17	t
1183	2025-08-07	\N	128	584	集成商采购林燕娜介绍，属于EPC项目，智能化分包当前还没有确定招标时间，根据建设进度有可能会明年初才招标。\r\n当前宋洋洋根据设计院了解到该项目，表示到时候也能有机会参与。	2025-08-10 14:57:08.946704	17	t
1184	2025-08-04	630	136	196	黄经理介绍，前几次我方报价不占优势，预计明年6月才进场（我估计前几次询价是为了测算成本）。以及尚未找到该项目的影响品牌的关键人，跟黄经理提过对接售前深化清单以及销售能否争取统一终端和天馈品牌，都没有得到肯定回复。\r\n下回跟张兴一同拜访，再争取跟售前认识。	2025-08-10 15:10:25.084332	17	t
1321	2025-08-26	758	556	\N	问客户要图纸，更改清单跟检测报告；	2025-08-26 09:04:03.647915	20	t
771	2025-05-27	671	480	\N	国家会展中心：跟客户聊了半小时电话：客户对接人房保飞表示，之前我们的标，价格太高，导致于未中； 比如说：近端机，别家报7800~8000；我们报21000；维保费，标准是3年120几万；我们报价100零几万；别家报价70几万；   现在这件事房交给下面的人去做，上面的领导虽然是有决策权的，但是不想管这件事；我理解下来，房这边表达的意思是他能做主的；我们之前做的设备，好多是坏的；设备坏了满场馆找；信号不好得找；现在的新的可以直接看到；客户需要成熟的技术去替代； 然后新的维保商不仅仅是无线对讲，还有广播的；现在的广播是迪士普的；代理商价格挺贵的；京东慧采；1个广播主机卖30000；必须要有出厂合约证书跟广播的资质；例如：功放（远端）、喇叭、号角；客户举例了迪士普-时序器；\r\n 客户表示在6月底前维保招标；可以关注网站，勘察时间；并举例了我们之前的问题：陪标的标书是有雷同的；3份都一样；这点非常重要；因为现在审标都是电子投标；还要查IP地址；外网IP是三防的；  需要有下载记录，但是我们之前的操作可能是就下载了1份，然后就把这1份直接发给陪标的2家了；  \r\n另外，房问我们天津的国家会展中心，展馆是否有经验；如果有的话，对我们来说是好事；  虽然这种案例 超过3年了，但是可以在计分的时候写进去，项目能写都写进去；因为现在比较卷；主要还是看经验资质； 客户对我们的资质什么的还是认可的，只是价格这些；\r\n后续我准备继续打电话，因为客户今天能跟我聊半小时，说明愿意跟我讲一些； 所以继续联络，能够争取到拜访为止；	2025-05-27 09:46:07.174897	20	t
772	2025-05-27	460	264	125	与中芯南方业主沟通6月份业主整个ERC机房搬迁接近完成后需要配套的机柜清洁及设备整理的工作，对27日FAB区域信号问题紧急排查的结果进行分析沟通，对于系统的日常维护提出了建议，后续以方案形式提供给业主；P3改造工程的进程进行了沟通；人员定位的需求将在6月份ERC工作完成后继续推进沟通和讨论；	2025-05-28 05:14:07.667502	7	t
773	2025-05-28	677	486	\N	与来访的沈总对中芯南方人员定位需求制定的方案进行沟通，提出了业主方面对于FAB平面图上人员行动路线和入口出口的偏差进行修改的要求，产品介绍部分聚焦在方案中用到的产品，剔除选项产品，把定位卡片的机柜产品介绍加入到方案中，增加第三部分相似案例的介绍等等，节后会对修正后的方案进行再次沟通；	2025-05-28 05:19:40.325998	7	t
774	2025-05-26	451	259	\N	业主已收到物业部门各个弱电专业提供的系统评估报告；业主提供了最新相关上海中心大厦核心领导班子替换的信息，新的领导班子将于6月初正式进入上海中心大厦管理岗位，上海中心的各项建设运营将在新的领导班子下继续进行，业主弱点负责人表示，近期观察然后推进后续工作；	2025-05-28 05:25:56.723764	7	t
776	2025-05-26	\N	30	65	目前沟通情况，项目进度推迟，品牌确定时间目前计划改到6月下旬	2025-05-28 08:32:34.426157	16	t
777	2025-05-27	93	81	549	目前在等待主设备中标集成商确定品牌	2025-05-28 08:35:04.672176	16	t
779	2025-05-28	40	8	542	配合具体设计单位完成初步预算	2025-05-28 08:40:55.148254	16	t
780	2025-05-29	666	474	\N	苏州四季酒店：对接人王鑫是最终客户四季酒店的总包方，职位是BMS维修销售（楼宇自控）；沟通下来，江森这里其实还是想掌控所有权的，不愿意轻易放手； 江森跟酒店的合同是6月底到期；我们的维保是今年9月，所以明天需要内部开个会沟通下，看看后续怎样操作会比较好； 因王鑫提出的要求：1.需要把坏掉的合路器更换掉，这样他们才能继续正常对讲机的工作；2.我们的维保方案可以出报价了；3.到期了大概率还是继续对酒店的操控的； 需要想办法接触到业主方； 因之前内部的沟通，可能王鑫跟方玲表示出的意思是9月底会撤场，但是今天过去他表现出来的并不是这样；他还是想要通过他们作为中转，再到业主这里。  这个人属于偏技术的销售，较内敛，需要长时间接触以培养信任感；平时应酬有但是对于喝酒不是很热衷，更想要做的其实是偏内勤的工作，我感觉后续会继续培养跟他的信任，另外一面等9月到了看他的情况；今天聊下来，个人感觉不是到了9月就撤场这么简单的，因为这个项目时间很久了，从2018年到现在，其实江森这里也是蛮疲惫的，因为平时他们也有别的项目要跑，无锡南京这种，具体的还需要继续聊，看情况。	2025-05-29 16:29:58.879765	20	t
783	2025-05-30	\N	25	105	以配合设计方完成图纸清单及预算	2025-05-30 02:18:26.42508	16	t
784	2025-05-30	\N	10	3	完成预算清单	2025-05-30 02:38:38.667367	16	t
786	2025-05-30	711	517	\N	沟通船舶 UHF（Ultra High Frequency，超高频）通信系统的组成，了解系统的功能，应用，图纸等相关信息；	2025-05-30 04:41:35.218694	7	t
787	2025-05-30	423	249	\N	了解沪东船舶设计院对于船舶用无线对讲系统的设计和应用，介绍了和源通信的企业和业务，了解船厂在UHF和VHF通信方面的应用和功能，希望后面能够进一步沟通，对标和源无线对讲的设计理念和产品，希望能够找到可能性做进一步的企业的技术交流	2025-05-30 04:45:46.595733	7	t
788	2025-05-30	\N	205	198	据代理商反馈客户选用亦朗，价格含施工在我们折扣的23-25折。	2025-05-30 06:12:53.701387	15	t
789	2025-05-28	712	221	41	拜访周晶，通过沟通了解项目基本内定他们，但具体实施需要等到明年，目前还在报方案及概算，至于品牌及供应商选定对外全部由采购林瑾负责。通过其引荐，与林瑾沟通了解，原先他们主要与烈龙合作较多，此业务既然找到我们，会考虑选用我们，但更多还是在价格成本	2025-05-30 06:17:03.472185	14	t
790	2025-05-27	713	350	587	拜访叶海茂，与其沟通了解此业务还在方案扩粗阶段，在审批概算，项目为老凤祥自用办公楼，位于徐汇漕河泾。待项目扩粗完成后才会启动智能化招标图设计，项目预计明年才会启动智能化招标，现在打桩还未启动，整体交付计划2030年交付	2025-05-30 06:25:57.476297	14	t
791	2025-05-27	713	350	587	拜访叶海茂，与其沟通了解此业务还在方案扩粗阶段，在审批概算，项目为老凤祥自用办公楼，位于徐汇漕河泾。待项目扩粗完成后才会启动智能化招标图设计，项目预计明年才会启动智能化招标，现在打桩还未启动，整体交付计划2030年交付	2025-05-30 06:25:58.425031	14	t
1206	2025-08-14	460	264	638	业主方已根据之前提供的维保方案提出申请，并且根据和源建议准备提出专用备品备件的需求，修正方案和备品备件的方案及清单，接下来将由现场ERC人员向中芯南方采购部门提出需求；	2025-08-15 02:02:13.53203	7	t
804	2025-05-29	611	127	269	项目运作方厦门纵横集团綦总表示，项目已经丢了，之前他们在配合业主方做项目前期筹备，以及初步设计。丢失原因是部队高层提出指定智能化总包。 \r\n他们近期中标了翔安机场维修机库智能化项目，让我们发一份机场的方案给到他们，了解是否需要建设无线对讲系统。\r\n	2025-06-02 15:47:10.857085	17	t
819	2025-06-05	177	343	614	和广州希耐特船舶科技易总沟通项目基本需求，协调代理商张兴进行设计配合	2025-06-05 07:15:44.173954	13	t
828	2025-06-05	716	154	617	吴经理，由于项目刚中标，清单尚在梳理中，发来图纸希望我们能帮忙深化。已让张兴配合。	2025-06-08 13:49:42.094515	17	t
829	2025-06-06	634	139	25	陈工透露，信元整体报价在30万出头，我方45折报价可以做到15.5万，整体成本可以优化到29.5万多。初次报价33万，第二轮价格沟通会适当降价。\r\n陈工介绍，本项目竞争激烈，是降价20%中标，所以公司利润较低。	2025-06-08 13:56:43.14765	17	t
834	2025-06-09	144	454	\N	上半年度的维保完成，与客户沟通开半年度的发票。	2025-06-09 03:33:59.221781	2	t
850	2025-06-10	155	260	\N	与客户确认本周四、五安排本月巡检工作，周五参加现场专项会议	2025-06-10 06:03:53.489021	2	t
857	2025-06-11	\N	410	209	项目在投标答疑澄清，和付沟通阿联酋的频率以及认证相关问题，配合总包提供了备品备件清单 	2025-06-11 07:59:43.12474	13	t
858	2025-06-11	174	339	100	和代理商一起参加项目会议沟通现场计划和安排，协调分销和公司订货和供货问题	2025-06-11 08:02:52.060514	13	t
866	2025-06-11	427	435	\N	与科思创技术负责人员沟通对讲机产品采购2025-2026年的框架协议的价格，服务内容等等，根据实际报价情况，决定提供P8668i产品的替代款，并提交替代产品的相关资料；	2025-06-12 05:38:02.024241	7	t
871	2025-06-11	667	475	\N	汇添富基金拜访，对接人带了他领导一起来，尹超，是云思的控制中心解决方案经理； 表示了汇添富基金应该是业主这里不需要维保了； 介绍了公司产品，对接人问了如果是摩托的系统，我司的对讲机是否可以使用，回答是可以兼容的；并且提了战略合作协议的模式，表示可以引荐采购这里去做进一步的沟通，后续继续保持联系；	2025-06-12 08:19:08.911768	20	t
874	2025-06-12	\N	323	622	目前挂靠中通服当地分包中标，预计9月份进场。人员找到，后续安排代理商配合深化对接跟进进度和商务。	2025-06-13 07:11:06.981823	15	t
785	2025-05-30	\N	21	318	据最新消息，该项目已取消无线对讲系统	2025-05-30 02:40:34.09064	16	t
793	2025-05-30	\N	282	593	此业务邹飞报备，有配合集成商在提交品牌建议	2025-05-30 07:09:24.461993	14	t
877	2025-06-10	\N	165	619	本项目是中建三局代建，智能化由三局智能二公司文工负责，文工已由原来的广州琶洲算谷调到本项目，目前项目已经在挖基坑。本次询价做预算，接下来让我们配合深化，到深化节点介绍代建方和业主方关键人跟进。	2025-06-15 13:43:31.087012	17	t
878	2025-06-12	636	141	31	集成商采购李小芹提出对手降价到10万，已和张坤成沟通，他表示目前确实对手在降价，我们品牌尚未上报成功。建议我们再次报价，如果我们报价差异不到，略高于对手3-5千，他都可以帮忙跟老板解释。\r\n瀚网成本接近10万，且了解到长沙之前有频段申报手续费（办理人员收取），需要去核实是否存在收费。最迟下周二报给集成商最新报价。\r\n	2025-06-15 14:00:17.948526	17	t
879	2025-06-10	\N	93	577	顾问公司李工介绍，他不知道哪家集成商去投标，因为没有集成商找他们了解情况。	2025-06-15 14:01:31.670353	17	t
912	2025-06-17	\N	532	628	协助代理商瀚网张国栋，拜访智信世创项目负责人颜江及技术和采购，沟通介绍项目方案，目前讨论后分配代理商跟进配套，智信世创表态投标会选用和源品牌参与	2025-06-20 05:48:09.72987	14	t
913	2025-06-18	241	243	593	拜访施国平，了解到该项目进入智能化概算审核，并且提交了系统品牌给与甲方下属研究院，按施国平说法品牌不太会变化，用户会以他们建议为主，并且通过渠道及外部消息了解，有一家集成商在积极跟进，通过施国平了解是申北智能化公司，施国平给予了联系人，计划后续跟进，项目预计7-8月份招标	2025-06-20 05:57:15.599738	14	t
914	2025-06-20	536	215	630	渠道报备，配合参与项目投标报价。项目为总价包干，整个项目有40万方	2025-06-20 06:13:41.292374	14	t
948	2025-06-23	460	264	74	向业主方提交高精度智能人员定位方案和中芯南方无线对讲系统维护方案和专用备品备件方案；与业主针对三份方案进行细节沟通；	2025-06-26 02:28:18.476071	7	t
949	2025-06-24	460	264	74	业主方提出针对高精度人员定位方案制定不同种类的技术方案对比表，在收到业主需求后与厂家技术负责人进行对比表编制，完成后25日发给业主方，业主方表示查阅后如有问题继续沟通；	2025-06-26 02:30:47.788275	7	t
950	2025-06-25	460	264	\N	业主方提出南方正在建设的ERC应急管理系统希望把应急管理系统的重要信息以文本形式传送到对讲机终端，以语音形式或者文本在对讲机上显示，与应急管理系统的技术人员进行了技术沟通和需求讨论；	2025-06-26 02:35:49.425357	7	t
980	2025-06-30	\N	251	\N	与盛一起在现场，和源对讲机售后问题测试，现场2台故障机器呼叫测试，一台更换频道无声音，不能确定频道；一台PTT键时有按下去无反应，导致客户反馈有时候无法呼叫，换一台正常机器测试后能正常呼叫；2台设备带回公司检测。	2025-07-01 06:07:09.982223	2	t
489	2025-05-13	\N	251	\N	上门送半年小结，同时跟客户聊了聊，客户反馈码头信号不是很好，暂定此客户没什么需要深挖的必要，可以放一放；	2025-05-14 02:06:23.930478	20	t
1062	2025-07-17	671	480	\N	国展对讲机招标历经3天的内部沟通以及外部沟通，一开始网站负责人驳回了我司的招标申请，后续沟通了房，房给了招标人的电话，沟通了之后对方批复了我司的申请，顺利拿到了招标文件，后续进行招标资料的进度；	2025-07-18 08:45:31.930437	20	t
1207	2025-08-15	759	564	\N	对方目前给振华供货设备，现包含对讲系统，询价一批摩托罗拉产品报价。	2025-08-15 02:17:58.098158	2	t
875	2025-06-11	695	319	623	项目原来做了系统，现在要改造代理商航博配合出改造方案，对讲机沿用原来的海能达，防爆天馈采用和源产品。后续辅助配合代理商与业主交流方案和造价预算问题。	2025-06-13 07:17:21.105904	15	t
856	2025-06-11	693	341	613	协调福淳配合完成图纸和方案，和邹娟一起和EPC总包单位北京中泰科沟通交流方案，业主内部还需进一步讨论确认是否需要窄带和宽带两套对讲机系统。	2025-06-11 07:53:07.623404	13	t
1086	2025-07-24	435	252	112	至上海浦东国际机场办公区现场提交浦东机场卫星厅消防用无线对讲系统维护标书，现场对合约服务内容，分项报价进行商谈，确认最终合约价格，分项报价包含的工作和合约设计维修更换的设备明细一一确认，最终完成现场答辩，双方签字确认，进入合约签订商务流程；	2025-07-25 02:36:46.000711	7	t
1107	2025-07-30	104	422	16	正式询价邮件收到，已报价给用户。	2025-07-30 06:02:36.298735	2	t
1108	2025-07-30	435	252	112	二次报价确认，报价文件发给用户。	2025-07-30 06:24:07.164409	2	t
880	2025-06-13	\N	142	55	目前我方品牌已入围业主品牌库，库内品牌有：海能达、摩托罗拉、海格通信、科立讯、北峰、和源通信。\r\n设计院让我们配合初步询价，上会跟业主方横向比对成本，以及了解各家品牌产品是否齐全。当前已分别找了家单位盖章报价（除海格外）。	2025-06-15 14:21:03.110599	17	t
881	2025-06-11	\N	\N	514	海能达刘明勇介绍，项目最快到6月底有结果，目前在和甲方协商（因之前在做招标文件过程有出入导致）。	2025-06-15 14:27:41.323235	17	t
882	2025-06-12	\N	138	218	集成商英飞拓确认到时候会去参与投标，业主方深投控虽然之前给过两个项目他们，但本项目会拆分成几个标，他们应该可以拿一个。	2025-06-15 14:29:15.534121	17	t
883	2025-06-11	\N	118	188	洪昇宋洋洋介绍，本项目分两家设计院分别设计，华南理工做核心大楼，省院负责宿舍楼等区域。目前已让我们配合根据系统图做系统架构。华南理工设计院黄志伟介绍，他们负责的部分进展没有那么快，目前给不了确切的参与节点。	2025-06-15 14:31:29.602051	17	t
884	2025-06-09	616	381	93	李工介绍，投标结果还没有出来，近期没有新项目。	2025-06-15 14:33:43.179696	17	t
915	2025-06-19	729	147	632	李经理表示，他和业主方高层关系好，愿意带我们品牌进去，并且让我们配合投标。本项目大概率是他们拿下。\r\n我在深铁物流枢纽项目，之前介绍李应跟业主方和设计方认识，此项目李应正在攻克广铁高层。	2025-06-22 13:32:19.885285	17	t
916	2025-06-22	659	169	268	宋洋洋表示，没有找到华发本项目对应的负责人，听说本项目已经将智能化分包出去。\r\n目前已了解到宇洪弱电线缆已经进场，现场了解到是宇洪马总在对接。由于之前找马总沟通过无线对讲事宜，她对我们业务不感兴趣。已让裴小印去沟通。下周持续了解进展。	2025-06-22 13:36:56.620515	17	t
917	2025-06-19	\N	101	90	广东省电信规划设计院北方区域技术于工，让我方配合审核原有技术参数，以及升级系统架构，目前已让张兴按照定位天线配置架构，将项目参数和整体预算做高。	2025-06-22 14:10:15.950351	17	t
922	2025-06-23	\N	280	70	一轮定标，最终投标价格未中标，价格高出。	2025-06-23 07:37:59.577242	15	t
951	2025-06-24	429	435	\N	与D600&E188区域负责人沟通今年E188区域新建无线对讲系统的使用情况，沟通了冷库区域由于封闭建筑结构的影响造成冷库里有弱信号区的问题，并且确定安排本次去科思创的人员对冷库区域进行现场勘察，如有必要对冷库区域增加相应的天线来解决；	2025-06-26 02:41:19.550268	7	t
952	2025-06-23	426	435	\N	与IOBC区域负责人沟通MCF区域的安装调试开通的安排，本周去科思创的项目负责人会至MCF区域与施工负责人对接进行施工交底；	2025-06-26 02:44:48.512702	7	t
981	2025-07-01	144	454	114	目前市政产品替换经过审价环节，10W的干放设备审完价格偏低，需要与公司确认此款设备生产是否可行，需要给用户一个情况说明及最优价格。	2025-07-01 06:47:46.784144	2	t
982	2025-07-01	136	263	\N	现场新换的2台2W的干放有一台功率偏低，与客户沟通将公司新生产的干放更换故障的设备，安排7月3日现场更换安装测试。	2025-07-01 07:04:01.915448	2	t
1019	2025-07-09	135	446	\N	文安鲁能的10套公网设备通信费到期，通知用户，确认续费使用，签订合同，开票。	2025-07-09 08:00:14.183549	2	t
1039	2025-07-07	\N	103	662	洪昇介绍品牌已经成功植入，当前在配合集成商准备投标，近期会有询价，需要帮忙保护。	2025-07-13 14:18:21.325766	17	t
1040	2025-07-08	620	381	48	下周投标，他们无论成本还是客户关系，把握都比较大。据了解上海金桥，以及当地的运营商有可能会去参与投标。	2025-07-13 14:24:18.145161	17	t
1041	2025-07-11	\N	\N	514	项目运作方海能达渠道经理刘明勇介绍，本来是6月底要定下来的，但由于项目较大，关注方较多，目前还没有定下来，但也不会太久了。	2025-07-13 14:29:15.478005	17	t
1042	2025-07-09	\N	533	632	深圳万睿销售经理介绍业主方设计对接人黄工拜访，介绍我方品牌和优势，事后补发了对应的案例资料，让其了解。争取下一步将品牌植入，以及配合技术方案编写。	2025-07-13 14:44:05.195483	17	t
1043	2025-07-10	632	138	663	深圳院智能化刘总介绍，本周刚定下来由他们出设计，通知让我们密切配合。 	2025-07-13 14:49:13.970248	17	t
1044	2025-07-10	632	138	218	目前还在施工图设计，后续的技术文档会让我们配合编写，或者我们编写一份给他们直接附上去也行。\r\n目前本项目顾问方栢诚庄工已经同意将我们品牌放入推荐名单中，业主方阎祖涵对我方品牌较为认可。	2025-07-13 14:57:44.222856	17	t
1063	2025-07-20	739	411	667	和刘工沟通昆明机场的情况，提供我们公司机场相关的解决方案和产品介绍给到刘工，近期安排见面沟通	2025-07-20 01:49:27.318534	13	t
1109	2025-05-30	666	474	\N	内部开会沟通苏州四季酒店这个客户，客户提出的合路器的问题，开会总结，节后给到客户我司备用机器，远程教客户自行切换；然后客户把坏掉的机器寄回来；	2025-07-30 07:39:59.213261	20	t
918	2025-06-18	\N	534	633	石国飞介绍，本项目是他原来的手下在负责，下回到广州他来组局，让我们认识，直接对接跟进。	2025-06-22 14:25:24.454625	17	t
919	2025-06-20	592	111	53	曾帅表示，之前的方案和报价给过去，业主觉得我们的成本过高。如果需要调整他们会尽快通知我们，智能化近期就会定下来。	2025-06-22 14:31:50.588018	17	t
920	2025-06-19	620	381	579	帅总介绍，项目上已经定下来我们品牌，按照施工进度，需要到三季度才能采购。	2025-06-22 14:34:09.354346	17	t
921	2025-06-16	\N	165	148	裴小印介绍，本项目招标时间还没有定，应该是下个月了，希望我们配合把控好报价和授权。	2025-06-22 14:44:09.700118	17	t
923	2025-06-23	\N	310	552	项目品牌和源烈龙中元，中标客户指定了越波老吴来做，老吴给出的拿货价格偏低，最终老吴选用了中元来做。	2025-06-23 07:46:41.75598	15	t
953	2025-06-26	671	480	\N	国家会展中心表示大领导刚出差了，这个月应该发不了招标文件了，估计要下个月了；	2025-06-26 08:19:05.173627	20	t
983	2025-07-02	182	350	307	项目计划三季度招标，和华东院陈工沟通招标技术规格方面的要求，配合其完成招标技术规格初稿	2025-07-02 06:08:21.060374	13	t
1208	2025-08-15	745	549	\N	客户确认续费，开票给用户。	2025-08-15 02:46:52.820762	2	t
1020	2025-07-09	\N	435	\N	邹伟奇：按客户要求2个不同频道之间互通使用，在公司写频测试。测试完成后将客户机器写频交给客户现场测试使用。	2025-07-09 08:05:05.738481	2	t
1021	2025-07-09	738	541	655	给合作伙伴张鹏介绍我司产品和解决方案在机场的应用和优势，达成合作意向。张鹏愿意分享他这边的相关资源，特别是在新疆那拉提和新疆伊利机机场项目，可以尝试合作，计划7月底或8月初去新疆，张鹏帮忙组织和机场业主之间的交流	2025-07-09 08:53:10.426571	13	t
1045	2025-07-09	\N	164	165	智能化分包方城信威胁，如我方价格较高，后续会跟业主方、总包方做工作换了我们品牌。虽然有品牌和技术参数把控，但仍需要加强业主方的工作，预计7月宋洋洋会到深圳，届时一同拜访业主方，了解业主方的把控支持力度。	2025-07-13 15:20:02.688946	17	t
1046	2025-07-13	\N	138	251	负责基建的江副校长介绍，虽然校区建筑面积有8万多平方，但因预算不足，决定不建设无线分布对讲系统。	2025-07-13 15:23:33.266865	17	t
1064	2025-07-18	\N	147	161	销售蔡经理介绍，目前在配合业主做招标技术文档核对，无线对讲系统没有什么问题，主要在关注是大的系统。本来预计7月招标，按照现在的进度，应该会安排到8月初。	2025-07-20 14:33:48.159111	17	t
1065	2025-07-18	\N	164	165	宋洋洋从工务署确认，目前尚未确定是城信分包智能化。推测一是城信仍是在做成本分析，二是可能确定了城信，但还尚未上报。已让宋洋洋确认到深圳拜访工务署对接人的时间。下周联系中建科工钟经理，了解具体进度。	2025-07-20 14:38:39.21314	17	t
1066	2025-07-20	578	94	52	采购王经理介绍，目前项目还在土建阶段，需要找基建公司总经理做品牌入库。之前跟基建总经理联系过，一直没有约上。王经理让下回他去基建公司办事的时候我一同过去。	2025-07-20 15:02:25.533939	17	t
1088	2025-07-25	\N	\N	32	渠道瑞康报备，经沟通了解其与通号之前有过业务合作，认识通号总部招采人员，通过招采人员和我同样接触到现场负责人，邀约共同拜访，商务宴请，加强客户关系，同时沟通引导方案，推进和源品牌锁定。目前通号在发起询价，初步复核成本，希望我们价格给予优惠，今年计划内部平台进行竞标，因地上标段没有限定品牌，虽然我们想通过地下来推进品牌一致，但目前从用户，到设计还没有明确，现在还在与瑞康商议如何锁定入围名单，防止恶性竞争。	2025-07-25 05:56:21.166653	14	t
1110	2025-06-13	666	474	\N	设备回来，合路器是正常的，那就说明不是这个问题；先帮王鑫解决这个问题；下周一统一内部解决此问题；王总选择第3种方式进行报价（即自己解决，我司进行远程技术指导等，不过客户问关于设备维修这一块的报价是如何的）；	2025-07-30 08:53:25.986087	20	t
1111	2025-06-30	666	474	\N	跟客户说合路器寄回的事，客户最近没在苏州，让过段时间再联系；	2025-07-30 09:13:57.033885	20	t
1112	2025-07-07	722	525	\N	客户询问我司是否有备用机器可以顶一顶，因客户的机器年份太久，没有备用的，后期再回复客户；	2025-07-30 09:18:23.620639	20	t
1113	2025-07-07	680	477	\N	海昌的MOTO维修报告已出来，明日给到客户，一并把后续的价目表等沟通下；	2025-07-30 09:19:40.33152	20	t
1114	2025-07-08	680	477	\N	客户这确定可出报价了，但是客户表示设备跟人工需要分开来报，只需要人工的； 后期这个模式如何报价，内部再讨论下再决定；	2025-07-30 09:20:27.605737	20	t
1115	2025-07-08	722	525	\N	客户提出了两个问：1.导出日志确定一下是否需要软件辅助？因客户目前的系统是没有软件的； 2.新的型号的设备是否能兼容旧的系统？	2025-07-30 09:21:27.792086	20	t
886	2025-06-18	724	376	\N	和唐总沟通今年上海新建地铁项目的情况，今年主要是崇明线、21号线、嘉定市域快线。目前上海地铁里专网通信，主要是公安和消防。公安是华为和中兴的LTE，消防是中兴的主机为主，直放站主要是陈明杰在弄，用的应该是畅博的设备，覆盖是沿用的泄露电缆的方式	2025-06-18 06:34:55.779241	13	t
955	2025-06-26	722	525	\N	青岛芯恩表示区域信号不好，想锁定一下是不是近端机对远端机没有信号；9个房间信号有一半是不好的，客户无法判断是近端机还是远端机的问题；之前已经建议客户导出日志但是客户不愿意做；建议客户可以 ① 先把设备寄回来进行检测，后续再看；② 因客户已过维保，建议客户可以续签维保； 客户表示可以考虑； ③ 客户可以购买备件进行更换； 把客户往签维保方向引导，明日在线会议沟通；	2025-06-26 09:58:48.985675	20	t
984	2025-07-02	115	435	\N	按新的框架协议更新ariba内的目录清单，与客户确认，完成更新。\r\n完成供货的机器开票确认。\r\n	2025-07-03 09:37:02.619938	2	t
985	2025-07-03	136	263	\N	现场新设备更换完成，故障设备测试功率偏低，新设备功率测试正常，楼层信号正常。	2025-07-03 09:40:44.668063	2	t
1022	2025-07-10	171	337	656	此项目沃利张总他们负责项目的初设，只设计的框架和相关预算，配合张总提供相关的资料，后期会推荐业主孙建亮认识	2025-07-10 04:20:36.417766	13	t
1047	2025-07-14	435	252	112	与上海国际机场股份有限公司合约部沟通2025-2029年浦东机场卫星厅无线对讲系统维护合约方面的细节，收到单一来源采购文件，安排商务完成相应应标文件；	2025-07-14 01:23:12.111268	7	t
1067	2025-07-21	435	252	112	维保的响应文件已确认，文件制作完成且已装订，等待响应谈判。	2025-07-21 01:16:06.008997	2	t
1068	2025-07-21	144	454	114	客户合同确认，流程走完安排备货	2025-07-21 01:21:56.150087	2	t
1089	2025-07-25	\N	484	516	经了解此业务中标几率较大为上海博电，渠道有过接触，与渠道一同拜访，推进集成商投标选用和源品牌，项目计划8月4号招标，项目整体进度为明年下半年交付，但今年会启动管线预埋及布线工作，建筑结构已经完成	2025-07-25 05:58:41.483139	14	t
1090	2025-07-25	741	193	\N	拜访环卫科负责人陆坚，介绍和源，了解上海福瑞业务。通过陆坚了解中标集成商存在自动化有关无线对讲品牌已经上报，并且通过，选用科立讯品牌，与陆坚沟通科立讯仅终端产品，关于系统部分，科立讯并不生产，而陆坚与存在自动化沟通后得到反馈系统部分选用程联，推进陆坚尝试用防爆产品及相关认证去否定存在自动化所选用的程联。同时通过陆坚了解无线对讲还没开始实施，但近期就会启动设备进场，需要进一步跟踪	2025-07-25 06:02:27.486041	14	t
1091	2025-07-25	\N	188	528	经设计院介绍，接触上电科市政部门负责人，拜访后了解其主要以区里市政业务为主，原先更多是以高速收费口称重及平台业务为主，对讲系统遇到的不多，目前他们的确在参与前期，现阶段主要是等项目概算，待概算确认后在启动完成初设和深化设计，在进行招标，按目前项目进度要求今年底要完工。他们与普陀区政府相关负责人有一定关系基础，但还不能确定后期招标形式	2025-07-25 06:06:53.655267	14	t
1738	2025-11-03	\N	\N	853	申请授权参与投标。	2025-11-03 06:18:00.766631	3	t
1116	2025-07-30	672	481	\N	对接人表示他上面的领导离职了，新来的还没定，约拜访；	2025-07-30 09:26:06.549713	20	t
1117	2025-07-16	671	480	\N	国展招标的公告已出，不过这次是对讲机跟广播一起的，注册好网站之后于今日下班前通过审核了，不过招标文件还需要对方工作人员流程之后才能获得；	2025-07-30 09:27:08.752399	20	t
1118	2025-07-21	671	480	\N	国家会展中心对讲机系统投标事宜，整理之前的合同，跟网站的投标资料，与瑞康一起商量，徐总主讲，最后决定我司不参与投标，全权交给瑞康进行投标，瑞康需要的所有资料我司皆会给予帮助；	2025-07-30 09:36:33.880395	20	t
1119	2025-07-22	671	480	\N	国家会展中心对讲机系统投标事宜，跟翰网协商，给到一定的资料，以及沟通标书等内容；	2025-07-30 09:37:15.091445	20	t
1120	2025-07-22	680	477	\N	海昌的方案给到翰网，大致的范围给到，需等对方确定了一致报给业主；	2025-07-30 09:37:54.949388	20	t
1121	2025-07-23	671	480	\N	帮助国展进行招标文件的投放事宜；翰网在上传文件的时候遇到问题， 网站要求.*JMYCTB的格式，询问招投标的人之后得知需在网站下载相关的载件再导入以后才能进行格式的转换；	2025-07-30 09:40:56.867312	20	t
1122	2025-07-24	671	480	\N	国展投标现场联系，翰网是价格最低的，就看最后结果了；	2025-07-30 09:41:33.38895	20	t
1123	2025-07-24	680	477	\N	瀚网给了海昌的人工，一年两次大检测按5000/次，其他常规测试/应急维护2000/次，5 次即10000元；20000元一年，这个价格还需内部沟通了再决定；	2025-07-30 09:45:06.969167	20	t
887	2025-06-18	725	527	\N	民航介绍桂总他们在参数沙特过境口岸项目，拜访桂总， 了解他们公司的业务情况，介绍我们公司的解决方案和产品，为后续合作做铺垫	2025-06-18 06:41:49.589164	13	t
925	2025-06-24	\N	423	106	与审价公司沟通审价后价格，确认价格及审价费用，按流程申请费用。\r\n审价公司需要盖章的资料确认，盖章后交赛车场公司，等赛车场公司盖章完成后开票。	2025-06-24 04:55:42.737902	2	t
956	2025-06-27	731	536	645	过与冀方萌沟通了解中国电子第十分公司招标，第一轮投标为6月底7月初，共计三轮，项目为电子十一院四所设计，原先设计负责人离职，按招标系统图看有参考我们设计框架，但招标清单却是网络接入天线的方式，此情况与冀方萌沟通后得到反馈，他们内部沟通确认先投标待中标后再深化调整	2025-06-27 03:12:29.829504	14	t
987	2025-07-02	148	458	\N	祥明1套M220设备确认订货，完成合同签订，通知客户付款。	2025-07-03 09:43:21.891564	2	t
1023	2025-07-10	672	481	\N	跟客户提出再次拜访，客户最近在休假，过两周再问；	2025-07-10 07:21:28.678903	20	t
1048	2025-07-14	155	260	56	与上海中心物业部总经理弱电负责人及采购确认本次350兆远端机更新方案，采购数量为6台，总金额12万，维修设备数量为5台，交给商务对接后续事宜；	2025-07-14 05:34:39.933502	7	t
1069	2025-07-21	155	260	56	6套350M远端机确认订单，安排签订合同及备货。	2025-07-21 01:25:19.654441	2	t
1070	2025-07-18	\N	160	138	李小飞介绍，本项目的合同还没有签下来，具体数量和采购计划，他这边不好确定，跟之前给我们的数量上肯定会有所调整，最好等他签完合同后再确认后续事项。	2025-07-21 01:30:25.071575	17	t
1071	2025-07-21	\N	\N	636	黄周迪：合同已确认，安排签订。	2025-07-21 01:35:02.699993	2	t
1092	2025-07-23	\N	30	65	与集成商商务沟通了项目采购的情况，目前现场业主意见还有分歧，商务采购还未开始启动，但3家报价我们目前最高，后续还要调整报价。	2025-07-25 08:24:04.971067	16	t
1093	2025-07-22	81	12	62	拜访了中标方项目总，目前项目进度整体偏慢。项目超概严重，目前正在走重新批价流程。预计9月份会启动采购招投标工作。	2025-07-25 08:42:31.575919	16	t
1124	2025-07-31	742	544	\N	因缘分加到的客户，此人之前在华为工作过，说看到过我们 Evertac 的LOGO，是帮华为的一个车平台做过服务的，约了拜访，不过最近这个人在闹离婚，等过掉这段时间再说；	2025-07-31 03:21:37.249915	20	t
888	2025-06-18	662	471	510	和刘林沟通项目情况，项目近期会招强电，弱电招标的时间还没有确定	2025-06-18 07:02:46.642295	13	t
927	2025-06-25	\N	382	535	邹娟对接了集成商的商务和项目经理，成都分公司给出回复，后期采购应该会放在深圳总部采购，后续时间到了，会把她推荐到确定的采购经理那边	2025-06-25 04:03:45.474059	13	t
928	2025-06-25	\N	522	613	和代理商确定好方案和报价，代理商已将方案和报价调整好发给总包，进行确认	2025-06-25 04:40:59.45628	13	t
376	2025-05-09	\N	214	\N	拜访世源科技高源，了解舜宇项目情况。原先没有无线对讲系统，后来做了增加，但智能化设计高源没有负责参与，经他反馈大概率在机电包中。现在机电总包中电四局中标，通过高源接触舜宇业主负责人俞晖，简单沟通了解无线对讲系统在汉威那边采购，计划后续拜访俞晖，复核项目是否有品牌要求，推进业务合作。	2025-05-09 00:00:00	14	t
957	2025-06-27	732	214	646	与高银沟通了解建设方为华为，由盛进王哲在负责弱电，有关无线对讲系统用户没有指定要求，同时高银透露华为项目大多都为单价开口合同。另外郭小会透露华为项目主要有三家集采单位，其中一家为深圳万睿	2025-06-27 03:20:26.547644	14	t
988	2025-07-03	101	419	\N	新一年度通信费用确认，完成开票。\r\n客户现场一台设备故障，测试后为电池问题，与客户沟通购买新电池事宜。	2025-07-03 09:46:02.289073	2	t
989	2025-07-02	130	443	\N	客户确认购买新电池，完成合同订单，安排备货。	2025-07-03 09:47:27.644547	2	t
990	2025-06-30	\N	423	106	与业主沟通审价公司的审价盖章报告要下周完成，完成后即可开票。	2025-07-03 09:56:05.371315	2	t
1024	2025-07-10	723	524	\N	客户最近刚从杭州四季回来，业主这里要求出新一年的维保价格，需要合同清单才能出报价；	2025-07-10 07:40:56.855056	20	t
1049	2025-07-14	435	252	112	服务方案，采购文件及相应初步的响应文件资料制作，发给用户确认。	2025-07-14 08:29:05.68284	2	t
1072	2025-07-21	150	460	\N	客户通信费用8月到期，与客户沟通续费事宜，确认续费使用，开票。	2025-07-21 03:14:03.35348	2	t
1094	2025-07-25	31	80	145	与项目负责人王总进行了沟通，目前项目刚刚进入管线阶段，进度远远滞后于原计划。目前预计最快9月份启动该系统招采工作。	2025-07-25 08:45:41.805045	16	t
1125	2025-07-31	734	435	\N	现场一批对讲机需要重新刷频，给客户按型号制作频率模板	2025-07-31 05:34:23.985106	2	t
933	2025-06-25	84	59	319	项目资金有问题，停工了	2025-06-25 05:05:47.513718	13	t
889	2025-06-18	693	341	437	邹娟配合的集成商未中标，找不到相关的信息了	2025-06-18 07:05:42.389743	13	t
1771	2025-11-06	179	347	694	沟通后续与集成商合事宜	2025-11-10 01:27:39.481722	16	t
1772	2025-11-07	\N	21	691	已投标，暂未出结果。	2025-11-10 01:29:12.852201	16	t
958	2025-06-26	650	157	131	采购介绍，经过三轮询价，最终定了曙腾，主要是价格因素。宇洪最后一轮的报价46折，曙腾价格是我们32折的水平。	2025-06-29 14:23:42.238935	17	t
959	2025-06-24	592	111	53	深圳市泰英通信工程本周通过洪昇和张兴同步在询价，曾帅介绍近期会开始投标，让我们配合，保护好价格。	2025-06-29 14:30:37.57703	17	t
960	2025-06-25	716	154	617	核对技术参数，我们的价额不是最有优势，还需要调整，调整幅度等他通知。	2025-06-29 14:34:50.542265	17	t
962	2025-06-25	\N	112	72	最晚三季度末，中山大学的资金会申请下来，计划年底竣工。	2025-06-29 14:42:11.536986	17	t
963	2025-06-26	\N	148	599	本次采购是星河两个项目一起采购，东湾项目是其中之一，项目经理介绍，业主出于成本考虑，已经内部过会取消了无线对讲系统。虽然瀚网已经跟星河智善采购合同已经签署，但没有发货，但对方采购还是坚持要求取消合同。约了下周拜访，沟通如何处理本合同。 	2025-06-29 14:52:35.793358	17	t
965	2025-06-23	601	119	576	谌工介绍，之前给的资料已经了解，近期都在跟业主沟通系统图，施工图暂时还没有那么快，有了的具体需求会让我们配合。	2025-06-29 15:02:30.691528	17	t
991	2025-07-05	714	359	640	T3光端机机的娈更方案已提交给指挥部，预计7月份批复的变更单发给总包	2025-07-05 08:37:58.524641	13	t
1025	2025-07-10	155	260	56	客户沟通确认，原350M故障远端机设备内3台维修，采购4台新的远端机使用，客户目前内部走流程。做好安装楼层评估。	2025-07-11 02:18:51.902802	2	t
1026	2025-07-11	\N	\N	636	黄周迪：审价公司审价完成，价格已到业主，业主按审价价格做合同，上会报批，完成后签订合同。	2025-07-11 02:20:41.632703	2	t
1027	2025-07-11	\N	435	\N	邹伟奇：现场2个频道测试不同，目前2个频道属于2个机柜内系统，暂时无法互通，找技术人员沟通支持，能否以其他方法实现。	2025-07-11 02:23:17.156172	2	t
1050	2025-07-16	148	458	\N	客户1套M220设备订单已付款，通知供应链备货，备货完成后发货。	2025-07-16 05:41:07.38875	2	t
1051	2025-07-14	130	443	\N	客户电池订单完成备货，安排发货，收货后与客户确认开票事宜。	2025-07-16 05:42:01.762353	2	t
1052	2025-07-15	421	445	122	订单备货完成，已发货，和客户沟通安排7-18现场安装调试。	2025-07-16 05:43:17.232988	2	t
1053	2025-07-16	155	260	\N	故障的350M设备与客户沟通安排7-22返回客户，将区分可用设备，安排7.23-25现场安装测试及本月巡检。	2025-07-16 05:45:46.279713	2	t
1073	2025-07-21	287	271	4	对方这边后面不参与投标，杨俊杰这边再跟进对应客户。	2025-07-21 03:16:45.789203	15	t
1095	2025-07-24	\N	103	678	配合广东省建筑设计院做系统图设计，由于预算有限，要求常规方案即可。张兴配合做点位图和系统图及清单。\r\n下一步深入确定需求，引导提升方案以及辅助做系统方案稿。	2025-07-27 14:54:42.130164	17	t
1096	2025-07-25	\N	545	165	和宋洋洋朋友丁总拜访项目经理戴松涛，宋洋洋没有过来。\r\n戴经理介绍，目前整体形式由于项目当时招标预算有限，整体比预算下浮32%，再加上分包又多一个环节，所以智能化分包是预算不足，比较难控制利润。再加上城信当初是协助了总包中建科工拿下本项目，所以城信比较有话语权，我们不降价是很大概率我们拦不住他们去修改品牌或者参数，作为项目上的负责人，较难不给公司高层领导的面子。	2025-07-27 15:12:31.240377	17	t
1126	2025-07-31	666	474	\N	回去的合路器对接人已经换上，最近台风天下雨，还没呢来得及测试，让下周再问；	2025-07-31 07:59:21.179956	20	t
1127	2025-07-31	664	472	\N	一直保持跟客户的联系，客户前段时间在闹离婚，劝说客户尽量别离，工作方面也别擅自行动，维持原状，这样才能进行下一步；	2025-07-31 08:55:02.764999	20	t
964	2025-06-25	\N	112	138	李小飞介绍，本项目需要特价申请，原因是招标无品牌限制，竞争激烈。再有是需要给客户费用，所以需要价格支持，希望能申请给到4折的价格到宇洪。	2025-06-29 14:55:58.601309	17	t
930	2025-06-25	200	365	2	此项目已确定由云时代分包出去。组织云时代、分包，刘威、王刚针对系统方案，特别是软件部署方案进行会议沟通商确，现场无法提供服务器，只能增加工作站	2025-06-25 04:48:37.20506	13	t
931	2025-06-25	204	369	245	慧腾是同济院 的设计 分包，负责此项目智能化专项设计，项目较早，前期规划设计 ，计划2028年完工	2025-06-25 05:00:45.288938	13	t
932	2025-06-25	\N	\N	311	郑州合作伙伴配合的集成商未中标，找不相关的信息	2025-06-25 05:03:19.440071	13	t
966	2025-06-23	602	119	647	焦总介绍，本项目的智能化已经内定给他部门来做，答应后续的品牌和参数由我们来配合，只要留出部门的团建费用即可。	2025-06-29 15:11:26.230023	17	t
967	2025-06-27	\N	147	161	销售蔡经理介绍，前段时间本项目业主想要将住宅打包出售，但没有成功，于是耽误了原计划的招标进度。由于没有出售成功，当前已经重新启动智能化招标流程，预计要在7月招标。	2025-06-29 15:17:39.244962	17	t
993	2025-07-06	\N	\N	24	该项目与邹飞沟通了解他与柚彤王亮有关无线对讲商务框架已经谈妥，项目预计7月中旬启动招标，按此进度预估7-8月份甲方与上安九分智能化合同落地，随后上安九分与智能化分包柚彤完成智能化合同，预计最迟今年四季度柚彤就会发起商务采购流程，并完成设备采购供应商确认。至于现场进度方面，经邹飞反馈柚彤已经进场开始实施，目前主要做管线预埋	2025-07-06 07:09:29.049607	14	t
1015	2025-07-07	737	540	\N	国展洲际联系，谢建明，客户现在还在职洲际酒店，表示目前系统良好，约了拜访，说最近比较忙，让下个月再去；	2025-07-07 09:24:41.961183	20	t
994	2025-07-06	\N	\N	32	该项目本周提供设计方案给予通号赵永杰，目前通号给予的反馈基本确认选用我们和源，现阶段地上、地下由于建设管理方、设计及系统集成单位都是2家，方案框架目前还没人牵线负责，地上、地下方案深化方向。按通号给与反馈情况，他们计划是年底发起设备采购流程，但实施进度目前了解地上土建才刚刚开始，智能化施工及设备进场为明年春节以后，大概率在明年二季度	2025-07-06 07:18:35.874066	14	t
995	2025-07-06	512	196	517	该项目代理商销售张国栋反馈他与华虹智联项目经理联系，由于甲方预算缩减，所以智能化合同重新变更，现在基本上差不多了，现场马上就要启动设备进场施工。项目经理已经提交设备采购计划，商务审核后会发起供应商询价流程，预计顺利的话8月份能够完成商务比价，并启动合约签订，与代理商确认待比价完成后就发起批价工作	2025-07-06 07:31:05.370548	14	t
1409	2025-09-04	\N	\N	91	项目进行报价阶段，线上报价。	2025-09-04 05:43:54.110811	2	t
1028	2025-07-04	211	496	\N	跟瑞康的李总沟通了后续的合作方向，李总表示可以，跟他下面的贺经理对接就可以；	2025-07-11 03:24:34.14195	20	t
1029	2025-07-11	551	226	24	分析业务成本，提供价格指导，安排渠道了解项目招投标计划，项目实施进度，跟踪价格反馈	2025-07-11 04:03:22.279626	14	t
1030	2025-07-11	\N	497	634	渠道报备，配合投标报价，给予指导价格。目前已知配合集成商包括云思、电信、信业，项目挂网公开招标，于7月底投标，分为两轮，先是技术标，再是商务标。	2025-07-11 04:07:33.725864	14	t
1031	2025-07-11	503	190	66	代理商反馈配合材料报验，与华东院余杰反馈，余杰透露方案审批通过，接下来就是品牌报验\r\n配合电信提供品牌报验资料	2025-07-11 04:11:59.621747	14	t
1054	2025-07-16	134	444	\N	客户今年配件预算已下来，需要采购一些配件，确认能订货后报价给用户。	2025-07-16 08:09:00.375724	2	t
1074	2025-07-22	140	450	\N	与客户沟通今年通信费用到期续费事宜，客户确认续费使用，开票。	2025-07-22 02:42:52.554168	2	t
1075	2025-07-22	139	449	\N	与客户沟通今年通信费用到期续费事宜，客户确认续费使用，开票。	2025-07-22 02:44:04.105143	2	t
1077	2025-07-22	130	443	\N	与客户沟通今年通信费用到期续费事宜，客户确认续费使用，8月开票。	2025-07-22 02:48:40.350343	2	t
1097	2025-07-23	\N	546	679	基站和对讲有品牌要求：建伍、摩托、海能达。智能化分包广东睿为建设有限公司，项目经理张巡万介绍，已经进场，预计本季度会采购，需要深化清单，给实在的价格，约定下周跟张兴一起到项目上进一步洽谈。	2025-07-27 15:41:08.714606	17	t
1098	2025-07-22	602	119	647	最快在第四季度才有可能需要初步配合，当前在建筑图设计。	2025-07-27 15:46:08.037348	17	t
1099	2025-07-22	601	119	576	业主还没有定出初步需求，到时候会需要我们根据系统图先给一版方案，根据这版方案拿给业主交流。最快下个月中左右让我们配合。当前大家的注意力还在其他系统上。	2025-07-27 15:51:42.203374	17	t
1100	2025-07-24	\N	112	668	裴小印介绍，广州市第三建筑有限公司已经中标智能化，他们公司同事之前已经配合集成商把品牌推荐成功，目前在做深化设计。	2025-07-27 16:00:24.610832	17	t
827	2025-06-06	\N	282	30	批价已结束	2025-06-06 07:19:09.11507	16	t
893	2025-06-19	\N	\N	42	用户确认，最终采购数量80套，已收到客户订单。	2025-06-19 03:51:04.117075	2	t
894	2025-06-19	115	435	\N	框架协议确认，约定后续付款账期90天，告知后续供货的对讲机型号有更改，给用户新的设备型号及报价。	2025-06-19 04:13:44.159311	2	t
934	2025-06-25	265	408	35	设计院刚把相关设计方案提交给业主，业主那边反馈很慢，目前还没有回复	2025-06-25 06:16:13.576925	13	t
969	2025-06-27	20	30	65	现场看了进度，目前处于管线施工阶段，进度比原先推进要慢。无线对讲系统品牌目前未确定。	2025-06-30 02:07:22.560498	16	t
970	2025-06-25	40	8	542	和顾问沟通了项目目前推进情况，反馈信息是：酒店和枢纽自建专网，办公地库采用公网。	2025-06-30 02:09:50.681473	16	t
996	2025-07-06	495	183	133	本项目目前接触现场项目经理，馈线已经有供应商供货至现场，按此情况至少公司定了一家，具体哪家还未了解，将次情况与梅小好商议，梅小好与业主沟通了解到施工单位的确线缆有到货情况，但其余设备没有，不过业主反馈施工单位申报品牌为海能达，并和业主说和源价格太高，给予业主建议让施工单位提供全套系统设备资料，并主动与施工单位决策人联系，但决策人不愿接触。按之前与项目经理沟通情况现场预计三季度天馈部分需要实施，同时对施工单位了解大概率竞争对手为曙腾，现在只能通过业主在品牌资料上制约施工单位，从而让我们重新回到商务谈判上	2025-07-06 07:38:12.262419	14	t
997	2025-07-06	534	215	101	该项目分为联检办公及酒店，分两次招标，但基本都内定上安，项目实施进度基本一致，但招标进度上存在差异，联检已经启动招标，上安也已中标，现场随即发起采购申请，代理商跟进采购负责人龚俊瑜，价格上经了解基本确认，而酒店部分预计待上安中标并签订合同，采购发起申请时间在8-9月份	2025-07-06 07:46:59.252768	14	t
998	2025-07-06	534	215	101	该项目分为联检办公及酒店，分两次招标，但基本都内定上安，项目实施进度基本一致，但招标进度上存在差异，联检已经启动招标，上安也已中标，现场随即发起采购申请，代理商跟进采购负责人龚俊瑜，价格上经了解基本确认，而酒店部分预计待上安中标并签订合同，采购发起申请时间在8-9月份	2025-07-06 07:47:00.956282	14	t
999	2025-07-06	\N	\N	134	该项目代理商瀚网反馈，他们在跟进仪电鑫森负责人，经了解，项目预计今年底会启动，现阶段他们刚进场，还在深化方案确认，有关品牌方面基本不会存在变化就会选用和源品牌	2025-07-06 07:49:54.580238	14	t
1000	2025-07-06	\N	\N	88	拜访季浩，了解到永天合同还在签订过程，由于他负责现场，关于无线对讲中标价格合约部了解，他并不知道，永天正式进场预计在10月份。现阶段通过代理商及李华伟反馈永天商务还在核价，主要与烈龙竞争，预算给予的比较低	2025-07-06 07:55:37.450489	14	t
1001	2025-07-06	\N	190	66	与代理商一同拜访现场，经了解实际中标单位挂靠上海电信，负责人为电信出来的。目前项目现场一栋楼刚封顶，施工单位开始做管线预埋，另外一栋还未封顶，无线对讲预估在四季度才会启动实施，项目整体交付在明年6月份。现阶段施工单位已提供方案资料审批，本月推进施工单位把品牌给予报审，计划提前先锁定系统品牌	2025-07-06 07:58:41.494269	14	t
1002	2025-07-06	\N	307	167	该项目仪电鑫森现场负责人反馈他们目前只是参与项目例会，还未正式进场，后续跟进了解进场时间及施工计划，推动深化方案确认，品牌资料报验	2025-07-06 08:01:18.356035	14	t
1003	2025-07-06	\N	248	60	拜访卓展李霄云，经了解云赛目前刚提交图纸资料，品牌还未送样。由于云赛为项目经理承包制，他们投标时选用沅抗支持，报的科立讯品牌，我们协助代理商共同跟进，给予超低优惠价格，但云赛负责人表示他们原先与沅抗一直合作，况且沅抗现在价格还是比我们低了8万多，所以他已经决定选用沅抗。将次情况反馈给予李霄云，看是否能够通过品牌报验去制约云赛，至于用户那边，因为云赛和IT部门老大关系较好，所以通过用户再去制约云赛可能性不大	2025-07-06 08:06:52.005317	14	t
1004	2025-07-06	681	215	85	该项目与浦东东站地下一同招标，四建安装中标，整体智能化打包给予上安九分，现场负责人统一为蒯乃骏，现阶段东站地下枢纽部分已经汇报方案及品牌，至于空铁联运问题应该不大，但需要等机场负责人落实后，再与机场一同汇报一次方案	2025-07-06 08:08:38.459082	14	t
1209	2025-08-15	103	421	\N	介绍美术馆客户，想了解公网对讲机通信，安排带2台机器现场测试使用看一下。	2025-08-15 03:26:59.255857	2	t
1005	2025-07-06	736	214	\N	拜访王粤，介绍和源企业，了解海神项目情况。目前得到反馈无线对讲设计定稿，在核算工程量，仍旧会在消防包内，品牌沿用一期海葵，由于在消防包内，业主由消防负责人跟进。与王粤沟通原先方案及中标选用供应商存在的风险情况，并提供相应企业资料，让其与用户沟通，看是否可以组织一次用户方案交流，从而扭转项目局面	2025-07-06 08:12:25.788855	14	t
1006	2025-07-06	\N	\N	593	拜访申北集团采购负责人，经了解他们的确早期参与，原先公司主要与曙腾合作，所以当时有过品牌推荐，虽然我们借用其他资源将曙腾品牌剔除在外，但担心申北仍旧以曙腾后续参与投标，所以通过代理商与申北沟通，申北表示项目现在进入小木桥公开招标，智能化预算虽然2600万，但已经变得不可控，所以他们希望我们尽量给予支持，经沟通后他们也愿意用和源品牌去参与	2025-07-06 08:15:32.635357	14	t
1007	2025-07-06	541	217	\N	拜访卢洪祥，了解城建院组织架构及业务情况。同时跟进太仓隧道项目，项目为隧道股份及中亿丰联合体投标，地面土建总承包为中亿丰，地下隧道部分为隧道股份，后续他这边会跟进帮助我们了解相关负责人，尝试帮助我们推进与总包及智能化分包的沟通。同时他提到真如地下车库现在方案汇报阶段，正式施工图设计还未启动，待后续招标时看如何帮助我们引入可控。	2025-07-06 08:18:50.355451	14	t
968	2025-06-27	\N	251	\N	戴彬拜访，客户表示8.9月份会有一笔2万元的费用可以用，不过名目必须是维修费。复盘了下目前的设备，客户的对讲机大概有一半已经丢失，剩下的可以用这个名目进行申请，具体的下周内部会议讨论如何操作。 并且客户要求下周一下午我司最好有工程师到场勘测一下现场对讲机设备，已经内部沟通过，下周一会与方玲一起到场，后续推进此事。	2025-06-30 01:54:31.046985	20	t
1032	2025-07-11	\N	186	108	了解在配合现场材料报验，由于监理监管比较严格，同时徐良健告知华融与上安合同还未签订，需要等材料报验通过，上安与分包合同签订后才会启动商务缓解	2025-07-11 04:17:22.511675	14	t
1033	2025-07-11	512	196	517	该项目周心一发起询价，三家入围参与投标，瑞康、常森及诺斯杰，预计本月底完成华虹智联内部招标，并签订合同。通过张国栋了解华虹智联与甲方合同重新签订，现场朱进发起设备采购订单	2025-07-11 04:19:32.280498	14	t
1034	2025-07-11	282	267	658	目前信诚百年帮我们品牌推荐和源品牌，方案是浙江省院在设计，目前是二期，方案还没开始配合设计。	2025-07-11 04:23:14.374694	15	t
895	2025-06-19	120	435	\N	有一批对讲机需要重新刷机，给用户制作对讲机频率模板，指导写频。	2025-06-19 05:21:09.440842	2	t
935	2025-06-25	195	359	641	组织刘威和设计院线上会议，沟通利比亚班加西机场新建项目的情况、需求和方案	2025-06-25 06:45:32.216262	13	t
971	2025-06-26	\N	535	643	目前配合合肥代理商四峰电子参与集成商投标报价	2025-06-30 02:12:28.556931	16	t
972	2025-06-28	\N	535	643	配合集成商江苏宜安建筑有限公司参与投标报价	2025-06-30 02:14:17.747842	16	t
973	2025-06-25	\N	493	592	湖畔酒店品牌无要求，竞争对手价格在18万长期合作单位，我们报价分析测算下来最低21万，对方已经采购英思普品牌。	2025-06-30 02:43:16.297577	15	t
974	2025-06-26	81	12	62	目前对项目做了进一步沟通，项目整体进度偏慢，无线对讲系统采购暂时还未开始。	2025-06-30 02:44:55.257277	16	t
1008	2025-07-04	636	141	653	张总介绍，他们是本项目唯一指定合作伙伴，这个项目只能由他们来做。当前我们无线对讲品牌只要在库内（中继台：摩托罗拉、海能达、和源；天馈：和源、京信通信、福玛通信），如果价格差距不大，首选推荐我们。	2025-07-06 12:42:07.148965	17	t
1009	2025-07-03	\N	539	652	集成商网真信息售前张经理介绍， 本项目近期会招投标，没有品牌限制，但也不是什么品牌都可以参与。最终客户会综合考虑，性价比高的会是首选。	2025-07-06 12:47:38.150103	17	t
1010	2025-07-02	\N	103	654	中建四局为总承包，暂时没有确定无线对讲品牌和智能化招标时间，留意配合，近期有询价。	2025-07-06 12:58:15.135248	17	t
1011	2025-07-01	628	135	33	胡总介绍，近期项目比较忙，核心在大的系统里，无线对讲需要到7月中下旬会进行比价流程，以及近期会走内部深化流程，到时还需要我们积极配合。	2025-07-06 13:10:38.920271	17	t
1035	2025-07-08	155	260	\N	参与上海中心大厦消防无线对讲系统专题会议，上海中心大厦世邦魏理仕物业管理有限公司总经理出席，沟通2025年2026年消防无线对讲系统设备更新事宜，确认批次更换的设备数量，更换时间，合约金额等等，会议结束安排商务对接，完成商务流程系统签订合约；	2025-07-11 06:55:00.131194	7	t
1055	2025-07-17	183	350	109	组织刘威和华东院 会议，沟通浦东机四期目前的最新情况和相关的时间节点，此项目分成三个标段招标，两个酒店、航站楼和南北交通枢纽、停车楼分开招标，计划明年3~4月份招，8月份我们完成深化图纸和招标文件的初稿给到华东院 	2025-07-17 03:36:53.44201	13	t
1101	2025-07-25	\N	381	579	达实介绍，业主由于预算不足，有可能会使用公网方案的。项目经理已跟业主普及专网的优点，争取机会让我们厂家跟业主当面交流，立体介绍建设专网的优势，公网的劣势。	2025-07-27 16:09:59.660199	17	t
896	2025-06-19	133	444	\N	与客户沟通一厂的本季度维保工作安排，安排6-23日。	2025-06-19 05:46:04.257531	2	t
897	2025-06-17	\N	454	\N	市政现场2台有故障的设备与客户再次沟通及报价。	2025-06-19 05:47:05.220405	2	t
898	2025-06-18	\N	423	\N	黄周迪-本月度通信巡检完成。主、备系统设备正常，通信、场强正常。\r\n发现新做的B看台远端机光路不正常，现场勘查，B看台的光路不通，原有的连接断开，重新接入另一光口，但光弱。B看台还未验收完成，故障情况告知用户，由用户找施工方安排维修。	2025-06-19 05:59:17.907067	2	t
936	2025-06-25	\N	\N	636	新一年度的无线对讲维保情况沟通，维保方案、赛车保障方案制作，维保及赛事保障报价给用户。\r\n建议上赛场根据现有系统会对信号偏弱区域进行信号补忙。	2025-06-25 07:03:51.934028	2	t
937	2025-06-25	148	458	\N	客户近期有项目需订1套IC-M220改装设备，确认此型号设备还可以订货，与客户沟通设备价格及交货期。	2025-06-25 07:22:34.647296	2	t
975	2025-06-25	\N	538	\N	中国电建华东勘测设计院介绍和源，对方主要做公建类，原来我们系统很少设计。余杭人才大厦目前系统没有设计，手上有个墨脱酒店后续配合。后续单独邀请晚餐进一步沟通维护关系	2025-06-30 03:34:12.752527	15	t
1012	2025-07-02	\N	490	580	项目史经理介绍，他目前还在广州收尾项目，暂未到深圳办公。最快本月底到深圳项目。	2025-07-06 13:18:02.560291	17	t
1210	2025-08-15	767	571	705	River帮忙组织他们工程部带我们去现场和业主方沟通交流项目情况，了解项目相关需求	2025-08-15 03:46:43.537402	13	t
1013	2025-07-03	716	154	617	吴经理建议代理商，线缆不用报价，公司会另外沟通。我们天馈报价与其他品牌有10个点差距，我们降下来后（降价后报价2.4万元），他来帮我们内部沟通。	2025-07-06 13:23:19.80843	17	t
1036	2025-07-11	360	226	69	目前对方已经进场，近期走公招流程确认最终结果。安排代理商配合初步深化。对方还在跟进闵行儿童医院项目。	2025-07-11 07:17:46.840588	15	t
1078	2025-07-21	434	252	112	与机场机电部负责人沟通2025-2029年卫星厅无线对讲系统维护合约的分项报价，根据业主方给的建议修正分项报价，修改应标文件中分项报价部分；	2025-07-23 01:22:12.677123	7	t
1079	2025-07-22	435	252	112	与机场合约部沟通浦东机场卫星厅消防用无线对讲系统的报价组成，根据业主方要求提供2022-2025年浦东机场卫星厅无线对讲系统设备维修及软件平台升级工作的明细，提供新的合约报价依据，并且对分项报价的依据进行阐述，为最后的商谈谈判做准备工作；	2025-07-23 01:24:31.20919	7	t
1080	2025-07-21	740	260	56	与上海中心大厦物业公司工程部总经理沟通上海中心大厦350兆消防用无线对讲系统设备维修/更新以及与消防单位的相关的联系沟通，推动6套远端机的合约签订事宜；	2025-07-23 01:28:47.53978	7	t
1102	2025-07-28	441	263	\N	与浦东文华酒店IT部门负责人沟通中秋节礼品采购（项目支持）事宜，安排人员对接周二进行；	2025-07-28 03:30:57.910582	7	t
900	2025-06-17	451	259	\N	现场无线对讲专题会议后与业主方面沟通在目前物业公司年度维修费用无法支撑全部故障设备替换新设备的情况下，如何处理的几种方法与可能性，并确定先由业主推动物业公司提供想法和我们沟通如何解决；	2025-06-20 02:15:45.4308	7	t
902	2025-06-17	427	435	\N	与业主方关于2025年7月后供给科思创产品框架协议的调整，包括产品的种类，新型号的引入及产品报价等等事宜，并且安排商务人员对接业主方采购，协调相关事宜；	2025-06-20 02:21:11.428981	7	t
903	2025-06-18	726	530	\N	与长宁区消防协会负责人沟通来福士广场350消防无线对讲系统维护事宜/长宁来福士广场事宜/浦东消防支队临港芯片厂推动消防用无线对讲事宜/松江南站项目收款事宜/与协会业务合作等事宜；	2025-06-20 02:28:02.897489	7	t
941	2025-06-25	680	477	\N	海昌这里跟客户确定需要维修的部分，客户只表达了电池都不好，需要MOTO这里检测再出报价；需要内部沟通如何处理；	2025-06-25 07:59:19.894558	20	t
1014	2025-06-19	730	332	\N	今日联络了吴鹏，对方是信息技术部的主管，此项目去年7月截止的，目前还没有什么问题，加了微信，后续继续沟通。	2025-07-07 05:07:49.831451	20	t
976	2025-06-30	\N	251	\N	跟方玲一起上门给客户检测，检测下来现场2台对讲机有问题，是需要维修的；同时信道机的灯也有问题，这个可以到时候跟对讲机一起放在维修里；后续继续跟进；	2025-06-30 09:25:57.04339	20	t
1037	2025-07-09	460	264	74	与业主沟通高精度智能人员定位需求现场建模演示的事宜，确认演示场地大小，演示需要的硬件软件条件等等，业主同步提出了无源定位产品的咨询和区域定位和轨迹回溯等等技术沟通；	2025-07-11 07:23:19.592778	7	t
1057	2025-07-18	362	226	69	壹杰标段需要与3号地块互联，代理商配合深化沟通。现场预计12月份左右进场穿线，目前在做桥架管子。	2025-07-18 03:08:15.631237	15	t
1058	2025-07-17	317	289	212	目前配合深化，集成商中标价格较低，代理商配合深化优化，资料已经报验。预计10月份左右进场穿线。	2025-07-18 03:10:02.415526	15	t
1104	2025-07-25	673	482	\N	跟董老师一起上门拜访的，对接人鲍磊表示，如果是维保的事情可以直接跟对方采购直接对接，因他是公司的人，这种事情由我们来提出比较好；引荐人可以通过李华伟介绍；博物馆这里确实是还在使用中的，鲍磊他们还在驻场中，后期还有拓展项目； 而且对讲机也存在维修损耗的情况，后期方向就是跑到对方北蔡公司去对接采购这样； 	2025-07-28 09:09:39.819394	20	t
905	2025-06-20	727	531	\N	根据销售部负责人郭小会临港芯片厂推动消防用无线对讲系统的需求，与原杨浦消防人员许秀峰目前在浦东住建委建立联系，沟通业务推广的可能性；	2025-06-20 03:51:53.862115	7	t
939	2025-06-23	722	525	\N	客户设备亮红灯，重启后仍旧存在问题；让客户确定下SN号再做后续处理；	2025-06-25 07:51:44.744035	20	t
942	2025-06-25	680	477	\N	海昌给到了检测报告，对方需要对讲机的维修价格，届时跟维保一起给到；	2025-06-25 07:59:47.949995	20	t
943	2025-06-16	666	474	\N	苏州四季酒店，询问对接人是否已更换了设备，对方回复还未； 表示如有任何问题都可以联系我； 并且关于报价这块对方还未询问，等出来了再给；	2025-06-25 08:32:18.946707	20	t
977	2025-07-01	734	435	\N	现场新购的对讲机需要刷频，给用户制作新的频率模板，及解答频率写频问题。	2025-07-01 05:09:13.377696	2	t
978	2025-07-01	\N	\N	42	kevin：与客户确认今日安排发货，给客户制作频率文件；\r\n与采购沟通收到货后即可开票。	2025-07-01 05:17:50.075268	2	t
1082	2025-07-23	155	260	\N	与客户沟通安排7月巡检事宜，7-24/25本月巡检，且将5台旧的350M远端机及跨频段合路安装完成。	2025-07-23 09:28:37.367114	2	t
1083	2025-07-23	\N	\N	106	发票已开具完成，赛车场公司流程已完成，收到审价文件电子版，现等他们财务付款。\r\n安排本月度巡检-7月28日	2025-07-23 09:30:29.445347	2	t
1105	2025-07-28	680	477	\N	今日跟瀚网的确定了几套方案，根据客户实际需求来报价；本周把该方案出出来；	2025-07-28 09:30:16.8898	20	t
1059	2025-07-18	693	341	613	业主会议又将无线对讲系统划分的非民航包里，北京中电力不做了，有本地的一个消防分包接手，邹娟已对接报价，业主没有钱，对讲机系统原来的100万的预算后来只批了15万，总包尝试和业主商量增加预算。	2025-07-18 04:36:33.169682	13	t
1103	2025-07-28	438	423	\N	与上海F1赛车场负责人奚晗之沟通主系统轮询主机采用一台8200型号替换现5300型号的事宜，提供工程师对于瞬时呼叫现象的技术分析，通过更换主机型号来测试是否是因为信道机型号不同造成，并在更换型号后利用9月份赛事进行使用验证；	2025-07-28 03:35:31.103662	7	t
906	2025-06-19	488	276	\N	与代理商福玛一同出差至常州，拜访江苏金鼎采购负责人朱焱，沟通九星城一标段商务。目前九星城一标段完成内部批价，商务方面协助代理商推进，由于中标价格极低，现阶段江苏金鼎仍旧在一一核算成本，有关和源品牌及产品对方清楚价格已经没有空间，现在主要是第三方产品上，关于这块代理商自行做衡量及与江苏金鼎沟通，预计商务落地还需要一段时间沟通博弈。	2025-06-20 04:59:16.343037	14	t
907	2025-06-19	488	276	\N	与代理商福玛一同出差至常州，拜访江苏金鼎采购负责人朱焱，沟通九星城一标段商务。目前九星城一标段完成内部批价，商务方面协助代理商推进，由于中标价格极低，现阶段江苏金鼎仍旧在一一核算成本，有关和源品牌及产品对方清楚价格已经没有空间，现在主要是第三方产品上，关于这块代理商自行做衡量及与江苏金鼎沟通，预计商务落地还需要一段时间沟通博弈。	2025-06-20 04:59:16.4678	14	t
908	2025-06-20	542	219	260	拜访市政院城交地下环境院弱电负责人王佳斌，沟通了解浦东东站地道工程，目前他们这边没有任何信息，只是回复可能土建大总包中标，按行业过往情况后续智能化会有弱电分包。市政院在隧道行业很少参与品牌推荐，只是提供招标设计方案，如果业主需要会参与项目中标后方案交底及深化确认，可以拿到智能化相关负责人信息。至于台州临海隧道近期没有任何音讯，计划还是尝试推进与弱电分包浙江机电沟通，找到项目具体负责人，再做进一步打算。另外有关前期业务，近期不多，且都是市政道路，没有涉及到隧道及管廊业务	2025-06-20 05:05:12.513279	14	t
909	2025-06-20	728	241	\N	拜访张鸿，目前浦东东站地上部分通号成立项目组，项目负责人夏志栋，属于上海通号，由他统管整个项目，关于无线对讲分派赵永杰和张鸿，属于北京通号。和夏志栋，张鸿初次会面，介绍和源，讲解东站项目技术方案，初步配套设计方案。商务方面初步了解，待通号有关方案落实后，金额超过50万会到北京总部进行招标。目前整个东站主要确认整体系统方案，包含地上及地下，由于甲方地上及地下是2个负责人，中标单位又为两家，从业务落地上上安九分基本确认品牌，现阶段是如何争取通号也认同品牌，一种是把系统核心引导放在上安来负责采购，但存在问题上安清单不完善，且中标价较低。另外就是说服通号认可和源品牌，而且现在在引导采用全和源产品，可是系统方案上400M调度可能会地上，地下分开建设，采用IP互联方式	2025-06-20 05:12:18.987829	14	t
910	2025-06-20	398	323	629	目前配合设计院设计馈电方案植入，后续跟进品牌和后续招标节点。造价公司预算已经配合出具。	2025-06-20 05:18:32.77971	15	t
944	2025-06-13	723	524	\N	李总表示现在杭州四季酒店的餐饮部在用公网的对讲机了，是小米的；   跟客户提了3种合作模式，李总选择第3种，进行远程技术指导，客户这出人，进行实地操作；我司提供培训等； 再跟最终用户去谈；客户提出的问题：①.关于系统我司是否能进行培训？②.我们公司在杭州有多少用户？这决定了客户是否跟我们进行此模式的合作；③.如果合作的话，分成模式，结算模式是怎样的？	2025-06-25 09:02:09.323942	20	t
979	2025-07-01	735	422	\N	中芯东方（临港）的P2区域要建无线对讲系统，面积与P1相同，P1是曙腾做的，现P2需要做预算做报告。	2025-07-01 05:53:01.828444	2	t
1016	2025-07-08	144	454	114	用户确认审价完成，等待合同流程审批，完成后准备签约	2025-07-08 01:44:21.604875	2	t
1017	2025-07-08	421	445	122	用户内部订单核签流程已完成，下发订单，签订合同。	2025-07-08 01:46:51.171879	2	t
1018	2025-07-07	\N	\N	636	目前进入审价阶段，与审价公司沟通价格，按上年度标准审价。	2025-07-08 02:13:55.955264	2	t
1061	2025-07-18	184	350	590	ITC的400M系统取消，只预留350M的消防接入设备，消防信号引自航站楼，配合徐工调整设计 	2025-07-18 05:10:36.869566	13	t
1084	2025-07-22	673	482	\N	客户让周四周五挑一天过去；	2025-07-24 07:50:06.765137	20	t
1085	2025-07-24	722	525	\N	客户表示近端机的问题还需要解决，总包的问题会在8月~9月之间定下来，到时候也不是竞拓，会让定下来的总包联系我的；会把维保跟所有弱电一起做进去；	2025-07-24 08:24:17.308926	20	t
1106	2025-07-28	666	474	\N	苏州四季酒店合路器已经回去，江森对于我们的报价感觉还可以，后续会报给业主，继续跟进；	2025-07-28 09:31:15.070131	20	t
1186	2025-08-06	760	564	\N	通过振华业主介绍，至上海真砂隆福机械有限公司与公司总经理副总经理沟通业务合作，通过会议沟通了振华产品需求合作模式，介绍了和源企业历史及无线对讲系统，推广和源产品（信道机和对讲机），对方总经理通过介绍和企业彩页介绍产品介绍了解和源业务和产品；	2025-08-11 01:40:19.794991	7	t
1187	2025-08-11	323	291	210	该项目分为3个地块，分别是104、105和106，其中104是欣钶中标，105和106是益邦中标，由于项目规划较早，用户预算有限，整个项目最后招标仅400兆常规对讲系统。目前王丽亚报备，跟踪欣钶中标，现阶段在配合欣钶确认深化方案，商务预计8月底9月头上启动，由于招标限价比较低，推进采用全和源产品替代摩托设备。至于益邦，主要负责人周晓飞，沟通后反馈他们投标选用招标品牌外的尚岛，关于这部分要和业主沟通，计划了解是否有品牌报验等环节从而让益邦改换为和源品牌	2025-08-11 01:54:24.256029	14	f
1188	2025-08-11	495	183	133	协助合作伙伴梅小好，拜访华兴项目中标单位采购负责人，通过梅小好与华兴业主关系，扭转局面，重新建立商务谈判，目前因现场进度比较着急，按采购说法天馈部分已经下单采购其他品牌，关于这部分与梅小好商议，通过业主了解是否采购及安装，业主是否同意。目前梅小好在与采购洽谈商务细节，如无意外预计本月底商务能够正常落地	2025-08-11 02:36:55.067458	14	t
1211	2025-08-15	763	566	706	项目设计负责人为徐珣，郭总与徐珣直接对接，整个项目仅做消防350M，接入至卫星厅，考虑后续T4建设，整个方案选用数字产品，但直放站概算偏低，先以数字直放站产品报价，待后续中标后根据实际情况再看如何调整。按周文乾所述，他们提前拿到招标设计资料进行复核，商议给予品牌建议，让其帮助推进	2025-08-15 04:05:55.971876	14	t
1254	2025-08-20	20	30	65	与工程总监，沟通了一下项目推进情况及采购推进。目前反馈信息是上报的设备品牌业主均未批复，公司内部ERP系统显示采购状态为未采购。	2025-08-20 02:12:47.67578	16	t
1255	2025-08-20	\N	535	675	清单中部分产品进入签约批价	2025-08-20 02:15:28.823659	16	t
1299	2025-08-24	\N	\N	733	霍尼韦尔销售经理陈政介绍，他目前与一个集成商在运作本项目，有无线对讲系统，需要我们帮忙深化以及报价。需要进一步了解他们对接的是哪一方，评估成功率。以及是否能影响到业主方，修改方案以及控制品牌。	2025-08-24 15:50:15.525615	17	t
1189	2025-08-11	748	435	689	将B196区域信号弱的区域增补进入本方案内，一起合并报价。	2025-08-11 05:57:57.886859	2	t
1212	2025-08-15	144	454	\N	因壁挂干放要打孔安装，工作日不能打孔，市政要求周末安装，安排8-16周六到现场安装调试，调试完成后出具报告。	2025-08-15 04:20:40.714951	2	t
1256	2025-08-21	767	571	705	客户预算很有限，要求按最基本的配制，安排福玛小陈配合设计方案和清单，给到客户	2025-08-21 06:08:33.569834	13	t
1257	2025-08-21	195	359	641	会议沟通业主反馈，业主明确要求建设TETRA系统，组织摩托TETRA团队，林峰，刘玉涛以及赵总，刘威会议讨论系统方案设计 和配合事宜	2025-08-21 06:10:57.539208	13	t
1258	2025-08-21	\N	382	535	和邹娟一起云见达实成都项目的负责人郑超，介绍和源公司的情况和模式，可以加强在前端业务的的合作，关于德赛西威，大家针对方案进行了沟通，组织福淳技术和达实对方案进行讨论和确认，邹娟继续推动商务工作	2025-08-21 06:14:03.230656	13	t
1259	2025-08-21	\N	526	715	江苏仁凯信息科技有限公司正在跟进此项目，中标的设计单位为：中国能源建设集团黑龙江省电力设计院有限公司，本次大型电厂的相关需求集成商在配合设计院，暂未拿到相关要求。	2025-08-21 06:15:47.458418	22	t
1300	2025-08-18	\N	\N	730	保利库内供应商（系统集成商）高攀介绍，他和业主方海南保利副总关系不错，但这里面有品牌库限定，高总答应出面帮忙了解是否有其他途径绕过品牌库操作。	2025-08-24 15:51:20.647649	17	t
1301	2025-08-20	\N	\N	732	集成商青岛九渊通自动化售前孙松林介绍，本项前一期使用的是科立讯的产品，当前由他们来做二期施工，但由于对无线对讲系统不了解，需要我们帮忙配合设计和咨询。当前已经让孙经理去了解，一期建设的产品技术参数、产品型号以及是否建设有通信管理平台，以及二期业主的建设需求。	2025-08-24 15:52:29.652053	17	t
1303	2025-08-22	\N	118	679	智能化分包项目经理张巡万介绍，按照上回报价（信道机和对讲机报海能达），已确定报审我方品牌。	2025-08-24 15:54:22.317899	17	t
1304	2025-08-21	\N	139	25	金证售前王工，项目9月最快可以采购进场，需要我方配合深化清单以及报价。根据最新清单参数要求，本项目使用馈电产品，且需要数字近远端机，45折成本58万。	2025-08-24 15:56:17.23449	17	t
1305	2025-08-22	717	142	55	最快8月底或者9月初开始招标。设计院确认按照我方给的技术参数招标。当前确认了万睿参与投标。	2025-08-24 15:58:24.518585	17	t
1322	2025-08-26	666	474	\N	客户最近没回苏州，报价已经给到业主方，后续继续跟进；；	2025-08-26 09:05:08.99535	20	t
1323	2025-08-26	723	524	\N	客户已经把报价给到酒店，后续会再跟客户吃个饭，继续追踪；	2025-08-26 09:09:12.323703	20	t
1324	2025-08-26	796	590	\N	客户表示有些地方还是有问题的，加了微信后续上门拜访；	2025-08-26 10:03:18.899339	20	t
1354	2025-08-28	\N	534	750	广州市设计集团叶总工介绍，本项目由他们做土建设计，智能化设计由分给上海西门子，答应帮忙找到西门子本项目的对接人。下周找到设计方对接人需要找上海同事帮忙一同做好前期植入工作。	2025-08-31 14:36:11.676815	17	t
1355	2025-08-29	\N	112	751	宇洪裴小印介绍，品牌：宇洪、和源、摩托罗拉。品牌由他们掌控，首选和源。当前配合集成商投标，需要我方配合控好价格和授权。	2025-08-31 15:00:27.581692	17	t
1356	2025-08-26	\N	142	55	肖总介绍项目预定在9月中旬招标，达实作为本次的顾问，目前了解到有联通、电信、万安、万睿参与投标。	2025-08-31 15:01:18.875091	17	t
1357	2025-08-29	\N	118	679	张兴已配合智能化分包深化清单，且根据清单在和瀚网沟通合同条款，等条款核商议好后马上签约采购天线跟线缆。	2025-08-31 15:02:19.743715	17	t
1358	2025-08-28	\N	162	25	中标集成商售前王工介绍，目前在跟业主沟通，是否能变更方案，如果按照招标方案，我们会亏本较多，大概率会把本系统推掉，我们的报价已修改提报过去，等部门领导了解后看给什么意见。下周去拜访业主方技术潘昊，了解参数变更意愿，如无可能就找集成商商量落地方案。	2025-08-31 15:03:25.821335	17	t
1359	2025-08-29	\N	\N	732	已与集成商青岛九渊通自动化项目经理孙松林商议，让代理商技术到现场，和他们现场人员一同勘察，以及配置方案。我已跟宋洋洋沟通，下周抽空安排技术到现场配合。	2025-08-31 15:09:43.884361	17	t
1376	2025-09-01	722	525	\N	青岛芯恩本月会定下总包的消息，届时联系总包进行定价即可；	2025-09-01 05:46:29.995958	20	t
1385	2025-09-01	430	435	766	客户确认需要我司人员检测现场设备及故障情况，下订单，安排人员9月2-3日现场故障排查。	2025-09-04 02:03:29.832454	2	t
1386	2025-09-04	\N	492	462	24年11月29日配合给程工（技术）技术方案，报价清单（和源通信），程工25年6月离职；25年6月再次联系上采购部刘经理给到（科立讯、淳泊）报价，因品牌库 里是（摩托罗拉、海能达、秋日、上海率延、建伍、利美特同等及以上品牌），目前接触的是总包的采购，弱电智能化这块还没确定是外包还是自己做	2025-09-04 02:22:01.274476	25	t
1387	2025-09-02	\N	\N	767	洁净室正在建，地下一层及地上一层，每层3000平方，现需做对讲通信系统，前期给客户做预算。\r\n已按客户给的初步平面图做了一份预估清单给用户，植入和源信道机及对讲机。	2025-09-04 02:22:50.638059	2	t
1388	2025-08-26	144	454	114	现场更换设备后进行联调，主机房分路器有故障，导致整个系统底噪过高，部分区域出现呼不出情况，暂用备机替换使用一段时间。\r\n三季度巡检完成。	2025-09-04 02:39:31.982318	2	t
1389	2025-08-27	\N	\N	636	8月巡检完成，现场主备系统的第一台主机对换使用，现场测试正常，轮巡正常，通信正常，录音及监控正常。	2025-09-04 02:49:22.176629	2	t
1390	2025-09-02	141	451	\N	新一年度通信费即将到期，与客户确认续费使用，安排订单及开票。	2025-09-04 02:50:54.836057	2	t
1391	2025-09-03	135	446	\N	北京凯宾斯基的公网许可到期，客户确认本次续费10个，安排签订合同及开票	2025-09-04 02:52:15.390328	2	t
1392	2025-09-04	159	467	\N	公网通信许可即将到期，与客户沟通确认续费，安排订单及开票。	2025-09-04 02:53:24.818272	2	t
1393	2025-09-01	111	431	\N	本月有20台公网通信许可要到期，通知用户，客户要申请费用，等申请完成后开票。	2025-09-04 02:54:42.152549	2	t
1191	2025-08-11	757	558	\N	江森说他们是晚上10点开始上班的，给了业主这里的联系方式，周四或者周五过去一趟；	2025-08-11 08:21:30.797581	20	t
1192	2025-08-11	753	557	\N	联系客户，之前的远端机问题已解决；发给客户资料看看，后续继续追踪；	2025-08-11 08:30:25.655417	20	t
1213	2025-08-15	495	183	24	该项目与梅小好初步确认合作方式，目前壹杰负责标段，有关样板层需要提前供货，协调渠道分销瑞康与合作伙伴艾亿，先满足项目现场要求，随后尽快落实艾亿成为代理商	2025-08-15 05:47:31.236938	14	t
1260	2025-08-20	77	21	693	指导代理商配合图纸系统设计工作	2025-08-21 07:03:37.564679	16	t
1261	2025-08-20	758	556	\N	跟贺一起上门，物业领导表示信号不好的地方必须要解决；客户B2停车场信号盲区，楼顶葡萄园信号不好，帮客户做了两遍信号排查；因业主的建设方签了7年的合同，我们直接报价给建设方即可；今天让贺出报告，然后我这里出报价，给到建设方；	2025-08-21 07:20:33.249353	20	t
1262	2025-08-21	747	282	\N	今天联系胡琦，表示这周会把名单给到，等给到了理顺情况就开始联系；	2025-08-21 07:22:23.701437	20	t
1263	2025-08-21	758	556	\N	客户要求在9月10号之前必须解决问题；	2025-08-21 07:31:41.011721	20	t
1264	2025-08-21	750	554	\N	内部开会，确定明天去的时候统一口径，以及需要帮客户解决的细节部分；	2025-08-21 07:47:02.843392	20	t
1265	2025-08-21	758	556	\N	物业领导表示：价格不要亚花花，不能高于合同价，这个对于我们跟代理商都是利好消息；	2025-08-21 07:58:54.477309	20	t
1306	2025-08-22	750	554	\N	跟赵总，董老师，还有小何一起去的，当场帮客户升级了信道机，关于对讲机的音量问题，赵总回来会做软件方面的调整，大概一个月左右；\r\n1.帮客户现场升级了信道机，解决了客户的信号延迟问题。                           2.承诺客户，对讲机声音太响，会在1个月之内帮客户解决，客户表示如果能解决，会继续用我们对讲机。    不过此决定赵总表示需要通过倪总同意才能执行；                                          	2025-08-25 01:34:30.328186	20	t
1307	2025-08-22	757	558	\N	约宜家现场检测，客户表示下周五，时间还需商榷；	2025-08-25 01:44:25.472551	20	t
1325	2025-08-27	794	481	\N	 现任新对接的人表示可能要增加10～50台对讲机，以及2026年的维保，不过是要拿钱的，让回来报价。 客户监控室用的是消防那套，400M物业的合同还需斟酌是否该问邹飞要；	2025-08-28 01:54:28.060758	20	t
1326	2025-08-25	435	252	112	浦东机场卫星厅项目合约已完成流转，合约正本件业主方已寄到和源，周一与业主关于合约附件4附件5附件6附件7附件8附件9进行一一核对回应，确认相关信息后于周三完成和源方面盖章，合约完成盖章后回寄给机场业主；	2025-08-28 02:20:16.808888	7	t
1327	2025-08-26	460	264	638	中芯南方无线对讲系统维护及相关备品备件需求已进入采购环节，周二与业主方沟通了维护报价中的分项报价，对每一项分项报价进行说明并且补充至报价方案内，针对备品备件的内容也进行了相关说明，阐述这些设备对于系统正常运行的重要性；最后以正式邮件的形式发给业主方；	2025-08-28 02:49:34.892686	7	t
1328	2025-08-27	771	20	693	介绍会展类项目的解决方案，就本项目的系统设计提出思路，沟通项目情况及后续配合事宜。	2025-08-28 03:38:46.277545	16	t
1329	2025-08-27	753	557	\N	客户这里需要整体改造的清单跟报价， 跟客户解释了现有的系统无法满足客户监控的需求，需要更换核心设备才能达到；后续继续追踪；	2025-08-28 03:40:58.140271	20	t
1330	2025-08-26	800	594	\N	拜访，介绍公司情况；沟通后续合作事宜	2025-08-28 03:44:36.698303	16	t
1331	2025-08-28	801	595	\N	拜访，沟通后续合作事宜	2025-08-28 03:47:54.62779	16	t
1360	2025-09-01	389	317	601	具浙江航博反馈由于品牌无要求，李总推荐选用和源品牌投标，一期是汉界品牌，近期会有投标价结果，中标后近期就要进场。现在增补扩建客户对于价格比较在意。考虑到设备数量具有规模，要求代理商李总以拿下来为主。	2025-09-01 01:16:26.084525	15	t
1361	2025-09-01	796	590	\N	客户改时间到周三；	2025-09-01 01:25:25.09561	20	t
1362	2025-09-01	\N	596	65	预约本周四拜访	2025-09-01 01:38:49.603086	16	t
1363	2025-08-27	789	584	\N	与长鑫用户沟通了解海神项目北京首安中标，通过其介绍，认识北京首安负责人于冲，与于冲初步介绍和源企业。计划与孔令冲加强关系，了解项目情况，如何有效切入到北京首安，同步与于冲接触，推进海神项目配套工作	2025-09-01 01:47:45.444463	14	t
1377	2025-09-01	775	574	710	前期的预算清单已经给出，但是无线对讲系统的设计存在不合理的地方，待谢总与甲方沟通完再统一修改	2025-09-01 07:25:23.467576	22	t
1378	2025-09-01	802	309	558	针对部分技术条款有异议，对清单进行了修改，目前还在沟通。	2025-09-01 07:53:40.729677	36	t
1394	2025-09-04	\N	\N	94	客户系统检测已开始询价，系统内报价给用户	2025-09-04 03:14:40.476463	2	t
1395	2025-09-02	794	481	\N	跟着业主方找到B1夹层的400M设备，客户让先报100台我们的对讲机，流程必须2个月内走完；回来报价；	2025-09-04 03:23:35.076297	20	t
1396	2025-09-03	796	590	\N	跟淳泊的小陈一起上门，因初步跟业主沟通提到维保的事情，业主让报价了，所以现场帮客户做了个检测； 客户现在主要是保安在使用对讲机，消控室：反馈3号港跟4号港的信号不好；保安反馈3号港，B2部分通道，信号盲区，叫不通；现场测试下来，1号港是有问题的，3号港没问题。3个直放站，有2个输出不达标。回来先做维保的报价，再结合测试报告给到业主；因10月份业主马上要大型比赛了；	2025-09-04 03:30:43.914508	20	t
1397	2025-09-04	\N	470	768	此项目进行报价	2025-09-04 03:35:42.841261	2	t
1410	2025-09-04	\N	\N	91	项目进行报价阶段，线上报价。	2025-09-04 05:45:17.438889	2	t
1418	2025-09-05	\N	600	728	跟冯技术沟通，他们前期在做配合，暂时还不确定是否是他们做	2025-09-05 04:50:40.09879	25	f
1419	2025-09-05	\N	600	728	跟冯技术沟通，他们前期在做配合，暂时还不确定是否是他们做	2025-09-05 04:50:41.470488	25	f
1420	2025-09-05	\N	388	612	9月4日去广元跟中建五局机电负责人陈经理见面，酒店有品牌库，跟他介绍了和源产品室分部分，项目9月底开标，保持联系	2025-09-05 04:59:26.338702	25	t
1421	2025-09-05	\N	388	612	9月4日去广元跟中建五局机电负责人陈经理见面，酒店有品牌库，跟他介绍了和源产品室分部分，项目9月底开标，保持联系	2025-09-05 04:59:27.662869	25	t
1434	2025-09-05	380	314	163	代理商配合深化完成，商务价格确认合约再走流程。推动近期批价确认掉。	2025-09-05 06:19:39.167842	15	t
1194	2025-08-12	449	258	\N	与振华重工采购部分的负责人沟通了与上海真砂隆福机械有限公司上周见面沟通合作的事情，目前振华去代理商的工作指导可以以目前这种业务模式合作执行，并且能够极大的解决供应商资金压力的问题；	2025-08-13 05:38:58.904839	7	t
1195	2025-08-12	459	470	\N	中芯国际集成电路制造（深圳）有限公司的ERC负责人联系说明了今年无线对讲系统改造目前停滞的原因和继续推动的计划，提出无线对讲系统运行和对讲机使用对于精密仪器的电磁干扰影响的问题，稍后会根据技术提供的材料向负责人提供相应的说明，并希望能找到相关法规和标准；	2025-08-13 05:43:28.083668	7	t
1214	2025-08-12	68	20	693	沟通系统架构及系统功能	2025-08-18 00:59:56.253082	16	t
1215	2025-08-14	771	20	693	与具体项目负责人对接，配合后续设计工作。	2025-08-18 01:03:41.110555	16	t
1217	2025-08-13	\N	165	21	协调公司售后服务部门，配合集成商处理现场系统发生的问题（信道频道互相干扰，初步判断是设备隔离部分发生问题）	2025-08-18 01:08:46.203134	16	t
1218	2025-08-18	772	535	675	项目增补，部分已确定。	2025-08-18 01:15:54.153399	16	t
1219	2025-08-15	750	554	\N	协调客户、赵总、董老师3方时间，最终定于8月22号下周五上午去；	2025-08-18 01:25:47.167228	20	t
1220	2025-08-15	5	44	127	配合代理商推动二期合同商务谈判	2025-08-18 01:30:43.173784	16	t
1221	2025-08-15	757	558	\N	分别见了2个人，1个是安保处负责人，邵辰；对接人表示聚荟办公楼A楼，1楼跟4楼没有办法接通，断断续续的，甚至听不到。。客户的使用频率是高的；我们的工程师之前来过2次左右，刚调好是好的，不过弱电间调试好了2周左右，又有问题了。\r\n\r\n第2个是商场这里工程部的负责人，方健康，对接人表示写字楼到消控室信号不好，消控室叫出去没反应，写字楼回来是有声音的，不过第一次呼叫都没反应，需要上门排查一下。\r\n\r\n之后江森这里的邱工表示情况可以直接对接，但是这个人是上晚班的，具体情况需要今天公司内部开会讨论后再决定下一步；	2025-08-18 01:38:04.122031	20	t
1222	2025-08-18	758	556	\N	协调瀚网客户建设方的时间，定于本周三上门帮客户做全面排查；	2025-08-18 01:42:15.434582	20	t
1223	2025-08-14	\N	7	531	与代理商沟通项目推进情况	2025-08-18 01:47:20.420589	16	t
1224	2025-08-18	\N	\N	710	与集成商接触后了解项目的基本情况，现正配合力均做设计，并出具预算清单。	2025-08-18 01:52:15.09871	22	t
1225	2025-08-18	385	314	696	招标参与集成商代理商瑞康配合同方、圆信。品牌围标，我通过卓展顾问沟通了解还是上海炙意几率较大。后续安排代理商跟进上海炙意配合。	2025-08-18 01:55:07.238177	15	t
1226	2025-08-12	403	328	556	带代理商技术同客户沟通二期方案，目前需要调整为物业和消防系统同一期全部考虑覆盖的方案来做，配合出具最新资料。价格成本增加较大，客户要求我们给出优惠支持价格。	2025-08-18 01:58:01.615379	15	t
1266	2025-08-21	695	319	623	目前李波的代理人帮忙入围三家品牌，预算基本框定。配合李波安排处理三个品牌入围资质资料。预计下个月进行招标。	2025-08-22 01:41:40.341499	15	t
1228	2025-08-11	778	30	65	提交报价，沟通了项目情况，初步沟通了付款方式等信息；后续等通知。	2025-08-18 02:01:08.138594	16	t
1229	2025-08-18	775	574	710	南京力均智能科技有限公司报备此项目	2025-08-18 02:03:29.213538	22	t
1230	2025-08-15	81	12	62	沟通了项目情况，目前有较多同行厂家在拜访或电话咨询该项目。	2025-08-18 02:03:40.877178	16	t
1233	2025-08-18	780	578	\N	拜访介绍和源产品，对方主要合作品牌为凌越荣驰，在宁波属于前三名的大客户年体量在4-5个亿智能化项目。对方还是以投标部门选定品牌为主，采购只负责合约。后续安排代理商组织技术交流和关系搭建。	2025-08-18 02:06:42.384853	15	t
1234	2025-08-15	\N	537	643	沟通项目招投标工作的进展，目前提供了质保期和售后服务电话。	2025-08-18 02:06:51.702355	16	t
1235	2025-08-15	781	577	\N	拜访介绍和源产品，对方主要合作品牌为凌越曙腾，在宁波属于前三名的大客户年体量在2-3个亿智能化项目。对方选定品牌以采购为主前期投标就要询价。后续安排代理商组织技术交流和关系搭建。	2025-08-18 02:07:59.914287	15	t
1236	2025-08-13	38	11	529	沟通了目前项目推进情况，合同暂未签订。	2025-08-18 02:09:02.805177	16	t
1267	2025-08-20	785	581	\N	拜访设计经理江兵介绍和源，目前已经在和对方逐步开始形成合作，手上实验室项目近期会参与配合设计。	2025-08-22 01:52:41.702595	15	t
1268	2025-08-18	788	583	\N	渠道报备，瀚网配合集成商江苏荣达参与桃源里-酒店-91#楼项目投标，品牌入围，主要竞争：汉界。项目前期设计经了解为李华伟负责，跟进顾问迈进。	2025-08-22 02:32:54.117974	14	t
1269	2025-08-22	787	582	\N	聚峰中心：该项目经沟通确认源和提交中元品牌，结合渠道反馈与集成商源和了解的情况，基本可以确认失效，源和因价格因素，设备含施工报价63万，选择跃波吴宏亮，采用中元品牌，依据此价格分析和源产品需要25折才能符合报价要求。\r\n上实北外滩91号地块（480米）：目前还停留在图纸设计审核阶段，现在用户确定酒管公司，WSP目前手上图纸还停留在6月份这一版。有关招标概算，由利比负责，应该根据之前图纸出过一版概算。至于有关智能化招标及系统品牌情况，现在还不确定\r\n新增业务：苏州会展中心，刚刚中标，还不确定设计负责范围，后续跟进了解。	2025-08-22 02:37:39.525716	14	t
1308	2025-08-25	792	233	701	提供南交酒店无线对讲设计方案。计划跟进北交酒店设计配套，同时了解云思在本项目中参与深度，项目设计及招标进度计划，推进业务合作	2025-08-25 02:19:38.417747	14	t
1309	2025-08-19	\N	553	105	配合集成商完成招标清单预算工作	2025-08-25 02:24:00.338421	16	t
1332	2025-08-26	802	309	558	进场明年，目前在做样板间，需要把整个系统资料全部报验，品牌目前需要确定，和技术确认清单。烈龙竞争，价格压力较大，目前还在和客户沟通。	2025-08-28 07:14:35.842073	36	t
1333	2025-08-28	\N	\N	200	配合集成商未中标	2025-08-28 07:37:24.482556	36	t
1443	2025-09-03	\N	\N	710	根据交流，对清单方案进行了修改调整。	2025-09-07 07:35:40.635207	16	t
1237	2025-08-18	134	444	695	三个厂区的新一年度做三方各报价给用户，待用户上报审批。	2025-08-18 03:13:39.96595	2	t
1270	2025-08-19	786	582	\N	黄浦区南延伸段WS3单元xh130E街坊：反馈用户由于招商问题，所以商业先建，办公搁置。集成商恒能电子还未提交系统品牌报验，主要竞争仍旧是烈龙，渠道瀚网在跟进\r\n嘉华上海P18项目：确认中标单位仍旧是霄远，但实际背后实施是安保的黄斌勇，安排跟进后没有得到反馈。WSP透露智能化多个系统已申报品牌，但无线对讲系统还没提交。与WSP复核项目进度，的确项目进度缓慢，但应该已经进场在做了。此项目品牌围标，瀚网及福玛。\r\n嘉里金陵路项目64、65地块：反馈永天合同已经签订，项目进场后现场负责人在和甲方及WSP沟通协商更换品牌，但嘉里及WSP基本不会同意，会要求其仍就在招标品牌范围内选择。至于其他地块综合机电近期招标，智能化招标图还未确认，预计最快也要年底或者明年招标。项目主要瀚网跟进，配合永天参与报价，李华伟在协助	2025-08-22 02:40:22.082522	14	t
1271	2025-08-20	789	584	\N	与保密项目海神建设方长鑫负责消防的孔令冲沟通了解，由于无线对讲系统内有消防应急通信，所以无线对讲发包在消防包内已经招标，中标单位北京首安，孔总已经将我的联系方式给予了项目负责人，目前还未建立联系，计划下周再主动跟进对接中标集成商。另外瀚网李冬联系，他通过海能达的关系也接触了用户负责运维人员，经运维引荐给予了用户其他人员及设计世源科技，在沟通过程中提及到我们，所以想是否可以相互配合参与此项目	2025-08-22 02:50:37.571513	14	t
1273	2025-08-21	435	252	\N	浦东机场卫星厅2025年-2029年系统维护项目合约修正最终版双方线上审核会议，完成所有条款及相关信息确认，进入合约盖章阶段；	2025-08-22 03:02:15.439122	7	t
1274	2025-08-22	427	435	\N	根据业主方提出CPD区域出现通信故障的现象，协调商务及工程师8月25日根据科思创下发的技术服务PO单至现场；	2025-08-22 03:04:03.635317	7	t
1275	2025-08-21	752	556	725	与现场检测人员沟通，对现场检测项与检测数据进行规整，对瀚网工程师的检测报告进行审核修改，对缺省数据进行补充，修正最终测试报告，提供给销售人员；	2025-08-22 03:09:56.541894	7	t
1276	2025-08-19	500	282	\N	陪同销售人员至上海淳泊与淳泊总经理和项目部负责人沟通淳泊项目售后服务业务，和源销售人员与淳泊项目部将针对项目进行逐个信息对接由销售人员对项目开展业务追踪；	2025-08-22 03:13:06.027011	7	t
1277	2025-08-21	726	530	\N	与消协负责人沟通虹口来福士广场350兆无线对讲系统现场测试完成后续工作，消协负责人表示虹口支队负责人前几周休假，他会尽快联系确认报告是否正式下发，拟下周一追踪结果；	2025-08-22 03:16:04.209095	7	t
1278	2025-08-20	790	350	\N	复地金豫福佑地块-南里：该项目华东院负责设计，经审图意见增加消防通信系统，给予设计参考。经沟通了解此项目还在初设阶段，至于后续智能化招标是否也由他们负责还不确定	2025-08-22 03:34:19.199207	14	t
1279	2025-08-21	782	553	687	渠道配合提供初步深化方案，沟通招标方案存在问题。沈佳反馈他们基于我们目前提供方案与用户汇报确认，待确认后才会启动后续工作	2025-08-22 03:39:33.537209	14	t
1280	2025-08-22	682	497	88	64和65地块主要与烈龙竞争，渠道瀚网跟进永天参与商务询价，预计永天在确认供应商及品牌。与渠道商议报价策略，基于目前烈龙对外渠道价格预测，给予成本预估及出价指导意见	2025-08-22 03:40:53.577576	14	t
1281	2025-08-21	495	183	133	通过了解天馈设备集成商问大展采购，将此情况反馈用户，用户要求集成商须采购和源产品。集成商与梅小好沟通提供天线样品，安排渠道瑞康跟进配合。协助合作伙伴与集成商推进商务合约	2025-08-22 03:42:15.301442	14	t
1282	2025-08-21	762	565	210	了解他们与甲方合同刚刚签订，近期正好他在忙于其他项目投标，另外本项目因为甲方付款因素还需和甲方沟通确认主设备供货时间，按他预测在11月份，但天馈设备仍旧在9月份会启动实施，至于商务方面他计划在9月初来落实	2025-08-22 03:43:26.277748	14	t
1283	2025-08-21	523	373	210	有关2个标段中标集成商目前推进情况与业主反馈，主要现在益邦还是选择其他品牌，业主近期休假，待回来后会找益邦负责人沟通，到时候在去找益邦沟通项目，看如何切进去	2025-08-22 03:44:53.448674	14	t
1284	2025-08-22	508	288	521	与代理商复核配套集成商上安九分、卡乐科技都未中标，实际中标单位仅知道温州当地企业，具体信息不了解	2025-08-22 03:47:02.965026	14	t
1285	2025-08-21	775	574	710	根据前期提供的图纸，并与力均的谢总进行沟通了具体的需求，并对设计院提供的相关图纸进行修改，并出具详细的配置清单	2025-08-22 03:50:03.40638	22	t
1286	2025-08-22	791	379	664	客户签约别家，价格太低，没有优势	2025-08-22 03:59:41.652503	36	t
1287	2025-08-22	\N	543	666	昆山高新区前进路南侧、江浦路西侧商住用房新建项目已中标，正在合同谈判中	2025-08-22 04:11:45.670836	22	t
1288	2025-08-22	\N	299	285	111	2025-08-22 04:25:51.905343	3	t
1289	2025-08-22	\N	309	558	再一次更新了报价给集成商。	2025-08-22 04:37:38.731752	3	t
1310	2025-08-25	747	282	\N	胡琦给了3个名单，太平桥132地块；安徽芜湖长飞半导体；马术中心； 其中安徽已经联络过；下午问了要设备清单跟了解具体情况再致电客户；	2025-08-25 05:48:20.885026	20	t
1311	2025-08-25	794	481	\N	原来的物业经理已离职，新来的已建立联系，约了本周拜访；	2025-08-25 05:53:14.819319	20	t
1334	2025-08-28	362	226	537	洽谈商务条款，对方中标价较低，在优化价格。预计10月左右敲定合约。	2025-08-28 08:01:14.397892	36	t
1364	2025-08-27	294	350	32	将整个系统深化方案框架与两家智能化总包沟通情况反馈给予黄辰贇，确保方案深化地上、地下，从智能化总包、设计院保持一致。另外了解航空模块情况，核实上安给予信息，得到回复图纸的确调整，主要根据机场空管局要求增加800M系统，但不影响原先我们设计内容，800M系统独立，不与消防等合设，且这部分仍旧由上安负责采购实施	2025-09-01 01:53:24.663261	14	t
1365	2025-08-26	804	215	670	目前项目还在项目立项，方案汇报阶段，现阶段主要申报项目概算	2025-09-01 02:02:15.479811	14	t
1366	2025-08-26	545	223	150	拜访瞿迪，与上海院团队聚餐，加强客户关系，沟通上海东站站前区A3-01地块，仅了解到有关品牌及招标，按目前院里计划如用户没有提及这部分内容由上海院负责，他们不会主动负责。同时按瞿迪反馈情况，即使交由他们负责，估计他还是会参考上海地标规范，我们，烈龙及正禄都会在内	2025-09-01 02:05:29.681152	14	t
1367	2025-08-27	763	566	706	招标设计方案基本定稿，在最后阶段复核，他将我给予的品牌建议给到设计院，但还没有得到具体回复，按他预测项目预计10月份招标	2025-09-01 02:09:03.920319	14	t
1435	2025-09-05	144	454	\N	针对上周五市政通信发生故障，给客户故障分析报告及设备检测报告，建议更换故障设备并进行报价。	2025-09-05 08:23:51.670853	2	t
1238	2025-08-18	782	553	687	集成商反馈他们合同已经签订，目前还未正式进场，只是在前期方案深化阶段，桥架管线由他们负责，具体进场时间还不确定，现阶段主要以技术配套为主，现场情况还未了解	2025-08-18 04:09:03.243497	14	t
1240	2025-08-18	783	572	24	该项目与邹飞沟通了解他们与柚彤深化方案配套已完成，在等待确认，同时柚彤给予反馈项目正式启动内部招标。邹飞计划待深化方案确认后，会第一时间与柚彤王亮沟通，推进商务合作	2025-08-18 07:26:22.442802	14	t
1241	2025-08-18	784	579	80	该项目现场还在做管线桥架预埋，由于精装还未进场，所以实施速度较慢，预计9月底完成桥架管线工作，接下来就计划就向用户提交深化方案，等业主确认后就会启动设备采购。有关品牌报审待设备采购时才会启动	2025-08-18 07:47:36.969169	14	t
1242	2025-08-18	551	226	135	壹杰现场要求提供部分天馈，所以采购徐骏启动采购询价，要求价格下浮20%，预测项目成本，商议报价策略，协助代理商与壹杰商务洽谈	2025-08-18 07:54:39.708419	14	t
1243	2025-08-18	744	548	\N	跟客户约了周四见面聊聊；	2025-08-18 08:22:53.800359	20	t
1244	2025-08-18	144	454	\N	设备已安装调试完。\r\n本季度维保安排在8月25-26，测试完所有数据后将调试报告及巡检报个给用户。	2025-08-18 08:25:16.428824	2	t
1245	2025-08-18	108	428	\N	本年度通信费用确认续费，现款结算，开票，后台续费。	2025-08-18 08:26:21.957464	2	t
1246	2025-08-18	159	467	\N	本年度通信费下个月到期，客户确认续费，9月开票。	2025-08-18 08:27:13.389186	2	t
1247	2025-08-18	155	260	\N	与客户沟通安排8月维保相关事宜，以及现场光路维修。	2025-08-18 08:33:00.663757	2	t
1248	2025-08-18	682	497	517	李冬反馈由于项目现场仅发起线缆采购，所以根据华虹智联流程上仅有线缆合同，现在他们与项目经理沟通，推进项目经理整体下单，待项目经理整体下单后再与采购接洽商务合约	2025-08-18 09:01:51.12228	14	t
1290	2025-08-22	97	21	600	目前还没有进展	2025-08-22 06:23:18.786241	16	t
1291	2025-08-22	364	309	558	目前烈龙和我们在竞争，客户计划月底品牌确认报审，与代理商沟通后给出最终价格。下周安排代理商一同与对方集成商商务碰面沟通。	2025-08-22 09:08:35.504548	15	t
1292	2025-08-19	551	226	537	安排代理商配合深化确认清单，对方样板层供货配合完成。对方中标价格较低，需要我们优惠20%的幅度，通过项目经理确认对方实际中标价格，价格重新核算。预计9-10月份进场穿线。委托项目经理尽快发起采购单确认合约。	2025-08-22 09:12:26.673976	15	t
1312	2025-08-25	795	556	\N	建设方让周四或者周五去，周三跟客户定时间，这两天把报价做出来；	2025-08-25 09:04:35.743639	20	t
1335	2025-08-29	195	359	641	和摩托罗拉林峰团队沟通计讨论利比亚项目的方案，明确双方的分工，准备相关的资料	2025-08-29 02:02:50.061271	13	t
1337	2025-08-28	757	558	\N	跟江森的人对接上了，江森的人表示3个月之后会撤场，现场帮客户写字楼4楼远端机的功率调低了点，然后现场告警功能就消失了，后续跟业主继续保持联系；	2025-08-29 02:11:59.649459	20	t
1338	2025-08-28	429	435	\N	与E188区域项目建设负责人和该区域技术工程师召开E188冷库内无线对讲信号的事宜，沟通不同对讲机型号在冷库内使用效果不同的原因，制定预解决方案，下周会先落实现场检测PO，通过PO复核问题，如需要出具冷库增加天线的方案；	2025-08-29 02:18:18.878672	7	t
1368	2025-08-27	495	183	133	合作伙伴梅小好反馈集成商与他合同签订。确认合同签订内容，协调分销瑞康配合梅小好，推进渠道批价确认	2025-09-01 02:10:13.626336	14	t
1369	2025-08-27	507	288	700	推进渠道批价确认	2025-09-01 02:12:12.032494	14	t
1370	2025-08-28	542	219	260	拜访市政院地下环境院，技术交流，并了解浦东东站地道业务情况，没有得到有效价值信息，让王佳斌通过其他专业负责人了解项目情况，后续继续跟进	2025-09-01 02:16:33.185401	14	t
1379	2025-09-02	460	264	638	与业主方沟通了P3增补项目临近收尾结算的事宜，特别是防爆UPS移位的事情，系统维护确认最终的报价和相关分项的细节；	2025-09-03 02:18:19.630165	7	t
1380	2025-09-01	429	435	54	与188区域建设方沟通现场冷库区域对讲机使用的问题，并且确认周三工程师会按PO单至现场检查新老对讲机的设置及冷库具体位置的情况；	2025-09-03 02:23:04.534458	7	t
1381	2025-09-01	430	435	\N	与MDI区域负责人开会沟通有反馈MCC信号不佳的情况，根据PO单安排工程师周二现场排查；	2025-09-03 02:25:57.483624	7	t
1398	2025-09-01	539	215	\N	项目梳理，通过渠道了解配套投标鹏峰项目、广州聚龙湾项目启动区1、2、3地块情况。经反馈鹏峰项目由于甲方资金因素一直搁置，放弃参与。广州聚龙湾项目启动区1、2、3地块未有中标，仅了解到四建安装中标，但没有相关联系人。	2025-09-04 03:46:01.74268	14	t
1399	2025-09-01	507	288	630	项目梳理，与渠道确认上安九分未有中标，中标单位为厦门万安，通过各个渠道传递中标信息，是否有过业务对接	2025-09-04 03:47:58.170437	14	t
1400	2025-09-01	536	215	\N	项目梳理，与渠道确认浦东机场南区地下交通枢纽及配套工程，上安九分未有中标，中标单位不详	2025-09-04 03:50:57.934554	14	t
1401	2025-09-01	536	215	769	渠道反馈该项目上安基本确认中标，预计顺利的话9月份上安与总包中铁建智能化分包合同能够签订，但由于中铁建合同范围中有一条债务抵房条款，所以还不确定项目中标后是否会存在双包。项目本身没有限定品牌要求，只能等上安正式中标进场后再跟进了解具体情况	2025-09-04 03:55:25.959013	14	t
1402	2025-09-04	682	497	517	跟踪项目商务进度，渠道张国栋反馈与项目经理沟通重新提交整体采购单，内部流程已经审批至采购环节，采购与渠道李冬有过价格确认，但商务合同始终没有进一步推进，安排渠道及时跟进，计划本月完成项目批价	2025-09-04 03:59:47.779667	14	t
1412	2025-09-04	\N	\N	771	目前配合安徽多普多信息科技有限公司进行前期设计及品牌植入。	2025-09-04 07:16:22.550126	23	t
1413	2025-09-04	754	558	\N	客户这提出信号不好是否350M跟400M能兼容 ，以及是否需要增补咨询技术意见以及瀚网的，3方沟通；	2025-09-04 09:19:18.012577	20	t
1414	2025-09-04	747	282	\N	你胡琦沟通昨日马术中心的项目情况，同时催付海军那边的客户名单；	2025-09-04 09:30:40.225646	20	t
1424	2025-09-05	\N	601	438	8月11日 去雅安跟技术、采购见面，目前他们是二标段，9月1日配合报价和源，还有一标段还没定（后端的主设备），总包是中铁四局，华西，9月3日跟西南院张工联系一标段还没确定是哪家集成商	2025-09-05 05:18:47.092021	25	t
1198	2025-08-13	750	554	\N	联系人陈吉是机场集团项目工程部主管，中间有一家上海电器科学研究所（集团）有限公司，当初是电器科学研究所购买的，使用方是机场集团； 现客户提出了以下几点问题：\r\n1.我们的对讲机声音太响，是否能够调节？（因客户的办公场所是圆环形，封闭性较高，整体也很安静，有一次领导在3楼开会，保洁在1楼呼叫，被3楼的领导听见了，领导不满意，表示不能有太大的声音，所以现在我们的对讲机都是停用的状态 ）\r\n2.对讲机在呼叫时会占用，第1个人跟第2个人可以说，但是到了第3个人就会有延时有7～8秒。（推测是否是中继台的关系）\r\n3.后期有增补的话，价格是否能便宜？但是不能超过2000元一台，否则客户这里部门流程算资产，非常复杂，需要上报。（这个前提是帮客户解决了现有的声音的问题的前提下，客户会有这个需求）\r\n4.数字台死机，1个月的频次左右，后续又死了一次，重启中继就好了。（这个问题倒还好）\r\n      \r\n我给客户提出的解决方案：1.回公司研究是否可以通过软件来解决这个声音的问题；\r\n2.如果不能解决，客户可以考虑我们的 PNR 2100；\r\n3.最坏的情况，如若客户要整体更换对讲机的话，不管是摩托还是我们自有的都还是可以找我们买（当然这句话是说给客户听的，还是会把客户往我们自有品牌引导）\r\n	2025-08-14 04:14:59.045643	20	t
1199	2025-08-13	758	556	\N	跟瀚网贺望亭一起上的门，客户的B2层跟5楼信号是有问题的，对讲机叫不通， 海歌厅也没信号。 这个问题存在半年了，没人处理。\r\n经现场排查，客户的远端机有问题，可能需要返修或者报废处理，客户提出如果返修的话需要提供备用机，这个问题需公司内部讨论；\r\n我给客户提出的解决方案：1.我们会上一次门，做一个全面检测； 2.检测报告出来之后，再给客户报2个价格，1个是单台远端机的维修或者更新费用，还有1个是整年的维保费用（因此客户以脱保）；\r\n客户的内部构造比较复杂，是业主运营-维保方-建设方-瀚网这样的形成；不过已经加了客户可以拍板的工程部负责人俞工的微信，后续报价也是跟他联系；\r\n因此客户对讲机的使用频率比较高，基本上天天要开会的，此次信号不好也是客户的领导提出的，所以我认为此客户比较重要，可以作为主攻的方向之一；\r\n	2025-08-14 04:40:10.248386	20	t
1200	2025-08-13	755	559	\N	跟瀚网的贺望亭一起上门，客户反馈下雨天信号极其差，对讲机返修了2次之后直接报废了，一年大概有十几次的维修率。不过台风天信号是稳定的，约定客户下一次下雨的时候直接过来看下； 另外，客户是酒店，要求要戴耳麦的，但是客户嫌摩托的耳机太贵，自行购买了杂牌耳机，用废了十几副了，因MOTO的原装耳机大约200元一副，杂牌的只要50元一副；对于此问题，建议客户可以先行购买一副原装的试一下，如果效果可以的话可以再买别的，总比不断的浪费钱的好；\r\n另，初步聊下来，此人上面还有个领导，下次方向即是让对接人介绍领导聊，看看是不是有把客户MOTO对讲机换成我们的品牌的；可以继续追踪；\r\n	2025-08-14 04:54:52.681357	20	t
1201	2025-08-13	757	558	\N	江森这里来电要购买一台MOTO的对讲机，需要入网跟报价；因此人是晚上22点上班的，准备过两天晚上去一次，明天拜访的是办公楼安保主管，双管齐下，看看效果如何，以及真正拍板的人；	2025-08-14 05:18:21.700386	20	t
1202	2025-08-14	748	435	689	订单确认，安排备货	2025-08-14 09:28:00.361174	2	t
1348	2025-08-29	695	319	623	李波告知本周安排业主陪标品牌瀚网公司参观，入围资料确认。目前可控的2家已经全部入围，第三家嘉兴本地的一家公司，安排李波跟中间人能否以资料防爆天线资质卡一下对方。	2025-08-29 03:31:16.096402	15	t
1250	2025-08-19	\N	\N	721	已投标	2025-08-19 03:30:38.710287	24	t
1293	2025-08-22	\N	388	164	四川欣邦公司询的市场价格太低，我们做不了	2025-08-22 13:25:59.574026	25	t
1313	2025-08-26	\N	317	601	目前配合集成商做投标前最后工作！	2025-08-26 02:38:05.72165	23	t
1314	2025-08-26	\N	323	526	目前已跟业主对接上！	2025-08-26 02:53:18.069088	23	t
1339	2025-08-29	187	352	690	和冯总沟通交流三期的方案，建议把通过这次机会把一期署腾的光端机换掉，一期2剥离器7近24远，先将预算做进去。三期业主和EPC总包目前的想法是以保密项目的理由向发改委申请，三期延续二期中标结果，不进行重新投标。	2025-08-29 02:23:04.309651	13	t
1340	2025-08-29	253	401	690	和福玛小陈会议，沟通三期设计方案思路，此项目是保密项目，图纸只能在现场看，安排小陈去现场和设计院对接设计图纸，出具预算清单	2025-08-29 02:25:50.079415	13	t
1341	2025-08-29	767	571	705	river已将两种 方案和预算提交给业主，业主需要上会讨论会给予回复	2025-08-29 02:29:09.413674	13	t
1342	2025-08-27	\N	226	537	现场预计9-10月份进场，通过采购和项目经理打听得知对方中标价低于我们的报价，需要优化价格和配置，同代理商与采购沟通具体商务细节。	2025-08-29 02:30:02.672737	15	t
1343	2025-08-29	177	343	614	拿到韩国的解决方案，和赵沟通方案存在问题，整理后给到易总，由易总反馈给设计方和船东，和易总想办法组织一下设计院和船东的交流	2025-08-29 02:50:52.367473	13	t
1344	2025-08-29	184	350	590	和徐工沟通讨论ITC的方案细节以及产品选型问题，她之边会帮我们把关，此项目上电科已提前介入，已同步给到杨俊杰进行对接上电科。\r\n近期徐工她们在参与宁波机场的设计标，南通机场也要启动	2025-08-29 03:00:14.995399	13	t
1346	2025-08-29	479	350	307	和王总沟通了此项目的情说，此项目有些乱，有个代建公司负责，但又没有懂弱电的负责人，业主那边也没有直接的对接人，他们以将设计和相关的招标文件给到代建方，目前那边也没有很好的反馈。他会想办法了解下有意向的总包，拿到联系人后让我们对接	2025-08-29 03:08:04.949532	13	t
1347	2025-08-29	184	350	219	能源中心预计10月招标，是上安在参与，已交通信息同步给杨俊杰，安排其跟进上安	2025-08-29 03:11:39.784285	13	t
1349	2025-08-29	\N	289	746	项目是一个绿地公园，代理商目前配合集成商方案设计预算，交代代理商方案设计植入全套和源新产品。	2025-08-29 03:34:37.532396	15	t
1350	2025-08-26	\N	165	559	原来设计院是同济，现在浙江省院接手设计，品牌推荐还不明确是否由他们来出口。后续拜访省院了解业主信息跟进甲方。	2025-08-29 03:37:38.492656	15	t
1351	2025-08-27	386	315	550	打听到目前集成商奥乐、上海大数据中心在参与前期，招标预计年底左右。后续安排代理商跟进拜访参与的集成商。	2025-08-29 03:46:40.319618	15	t
1203	2025-08-15	459	470	\N	与业主沟通关于对讲系统对于芯片企业精密仪器的电磁干扰问题，通过内部技术工程师的信息传递，向业主说明电磁干扰的产生和预防的措施；	2025-08-15 01:41:12.937204	7	t
1251	2025-08-19	500	282	\N	徐总陪同一起上门拜访，邹飞这里表示可以接受代理商合作模式，本周会让胡琦出列表给到我，联系起来；	2025-08-19 08:09:45.369945	20	t
1252	2025-08-19	758	556	\N	跟客户定明日具体时间，贺表示全面检测需要一整天，另，询问是否需要带备机给客户；跟徐总商讨下来，先不给，先帮客户做检测，再出报价，看客户的态度再做决定是否给备件；	2025-08-19 08:42:20.195572	20	t
1294	2025-08-24	\N	58	728	配合集成商报价，近期去拜访	2025-08-24 03:10:13.328582	25	t
1295	2025-08-24	\N	58	728	配合集成商报价，近期去拜访	2025-08-24 03:10:14.706625	25	t
1296	2025-08-24	\N	587	729	了解到项目已第二轮投标，以最低价中标	2025-08-24 03:31:40.433809	25	t
1297	2025-08-24	\N	587	729	了解到项目已第二轮投标，以最低价中标	2025-08-24 03:31:41.624997	25	t
1315	2025-08-26	\N	323	527	目前已查到具体的中标单位、与2025年8月25日已见面交流，预计9月20日开始进行询价详谈！	2025-08-26 03:03:31.615702	23	t
1317	2025-08-26	753	557	\N	客户提出需要改造厂区信号，能在监控平台上检测信号，原有的系统需要改成我们的，下午跟技术开会之后再回复客户；	2025-08-26 03:23:03.965719	20	t
1318	2025-08-26	685	494	742	经业主引荐，配套挂靠同济设计的负责人王其，安排代理商技术协助配合前期方案设计	2025-08-26 04:36:09.974785	14	t
1320	2025-08-26	681	215	32	沟通深化方案，将整个系统进行机房合设，建立一套400M运维系统，主动协调通号、上安确认方案可行性。目前上安、通号已认同相关方案，并且和铁四院也已确认，后续和华东院沟通，确保设计、实施一致性，把我们方案统一递交给到用户确认。另外蒯乃骏侧边与通号沟通，得到回复地上、地下会品牌一致性，用和源品牌，蒯乃骏将此信息也传递给到东方枢纽机电负责人李继东	2025-08-26 05:15:35.353709	14	t
1352	2025-08-29	\N	\N	727	该项目新建有错误	2025-08-29 06:43:16.346711	25	t
1353	2025-08-29	796	590	\N	跟客户约了下周二跟胡琦一起去；	2025-08-29 08:18:42.819948	20	t
1371	2025-09-01	551	226	537	项目目前在中标后的深化，后期由杨俊杰配合跟进，项目转移给杨俊杰负责后续批价落地。	2025-09-01 02:52:30.641492	15	t
1372	2025-09-01	688	496	537	项目转移杨俊杰配合，目前进度中标后再配合深化，预计近期批价。由杨俊杰负责。	2025-09-01 02:54:47.718483	15	t
1373	2025-09-01	396	323	764	项目目前启动总包设计招标，省院是机电设计单位，弱电设计目前还没确认。后续通过设计院接触业主。	2025-09-01 03:12:27.632513	15	t
1374	2025-09-01	311	283	545	项目失败，签约科立讯。	2025-09-01 03:43:23.94976	36	t
1375	2025-09-01	794	481	\N	内部搞清楚了客户现有的系统，350M消防是在1楼消控室的；400M物业是在B1夹层的，约了明天去看B1的设备；	2025-09-01 05:10:25.813169	20	t
1382	2025-09-03	265	408	639	项目没有钱，智化预算砍的很多，用户最终选择移动公网对讲，取消专网对讲	2025-09-03 08:22:43.148276	13	t
1383	2025-09-03	265	408	35	上个月院方人事变动，大领导更换，近期刚重新向业主方进行了汇报	2025-09-03 08:24:53.982072	13	t
1403	2025-09-02	476	350	67	拜访韩翌，沟通了解工博会项目目前由于主负责人上海市委秘书长换人，所以方案有所调整，精装与建筑图纸始终未有最终确认，所以现阶段仍旧停留在初设阶段，需要等建筑精装图纸确认后才会启动智能化招标图。项目概算方面未有变化，按每平米800元估算。甲方之前管理单位退出，由上海城投负责，但城投那边没有具体专业人员，等后续招标图设计启动在根据情况做具体安排。另外韩翌提到浦东东站站前区他们新接了一个会展类项目，现在还在方案汇报阶段，后续设计启动推进技术配套	2025-09-04 04:05:58.261816	14	t
1404	2025-09-02	184	350	706	该项目核实品牌方面上电科按我们提交品牌给予徐珣，徐珣会以此品牌提交，项目预计10月份招标，上电科主要配合总包建工四建，甲方对于四建及上电科在原有项目上都比较满意，所以他们中标几率较大。至于能源中心，仅了解弱电当时有过暂估价，但会单独招标，具体招标节点不是特别了解，且徐珣咨询过他们院内负责人，说是参考机场招标要求，所以没有过多介入，不过了解到用户负责人为唐建树，后续计划邀约拜访	2025-09-04 04:23:55.284808	14	t
1405	2025-09-02	789	584	\N	与长鑫用户聚餐，初步建立合作意愿，项目没有限定品牌要求，所以还是需要通过用户把关，让我们与中标单位北京首安能够建立对等的商务沟通环节。另外核实代理商李冬反馈情况，了解到他接触的是运营人员，且一期海葵项目系统搭建的情况不是很好，给予孔令冲后续有关无线对讲系统在资料报验时需要注意哪些侧重点，给予文档资料参考信息。目前最大困境时孔总反馈北京首安无线对讲中标价格仅为60多万，用的科立讯品牌，就看孔总能否卡住北京首安	2025-09-04 04:28:10.800297	14	t
1406	2025-09-03	792	233	701	拜访陆丽春，了解南交和北交酒店情况，反馈他们与华东院吴文芳有关设计意见达成一致，以他们为主，主要业务负责人王杰飞，与王杰飞、陆丽春达成项目合作共识，目前南交配套提交给到陆丽春，北交图纸还在整理，据说今年9月份会提交一版设计资料。另外云思内部今年除华南区域以外没有新增业务，谢国平在参与一些项目前期设计	2025-09-04 04:33:19.917237	14	t
1407	2025-09-03	798	592	744	拜访朱明华，了解本项目在做招标概算，正式招标预计在11月份，和其沟通项目没有限定品牌要求，但整体参数完全是海能达，且要求与原先系统互联。朱明华反馈他除了咨询我们以外，还找了海能达，海能达引荐武汉当地合作伙伴华宜中通，沈飞有在对接，目前还在思考如何破局。且和朱明华沟通过程中他们也有海外业务，在马来西亚有个自建数据中心，经其介绍认识扬州分公司负责人，但里面没有无线对讲系统需求，看后续是否有合适业务合作	2025-09-04 04:36:40.361125	14	t
1408	2025-09-04	342	298	102	该项目与渠道福玛确认，有关张江创新药基地其中一个地块B03K-03，他们与派汇网络最终价格确认，再走商务合同签订流程，确认实施清单，发起设备采购。另一个地块B03C-02，进度方面慢一些，预计本月底下月集成商铭鹭才会启动设备采购流程	2025-09-04 04:39:34.313469	14	t
1415	2025-09-05	\N	587	729	9月3日联系集成商说取消无线对讲这块了，联系到业主确认目前取消，后期再看是否再加	2025-09-05 03:47:04.757982	25	t
1416	2025-09-05	\N	586	728	跟李经理售前技术见面，项目目前还没开始招标，后续保持联系	2025-09-05 04:48:18.58046	25	f
1417	2025-09-05	\N	586	728	跟李经理售前技术见面，项目目前还没开始招标，后续保持联系	2025-09-05 04:48:19.912423	25	f
1425	2025-09-05	\N	601	438	8月11日 去雅安跟技术、采购见面，目前他们是二标段，9月1日配合报价和源，还有一标段还没定（后端的主设备），总包是中铁四局，华西，9月3日跟西南院张工联系一标段还没确定是哪家集成商	2025-09-05 05:18:48.380872	25	t
1426	2025-09-05	\N	\N	436	联系上分包一个标段的，约9月中旬见面	2025-09-05 05:21:06.479922	25	t
1427	2025-09-05	\N	\N	436	联系上分包一个标段的，约9月中旬见面	2025-09-05 05:21:07.778127	25	t
1430	2025-09-05	810	603	772	拜访了李总，介绍我司在机场相关的案例和解决方案，确认温州机机场项目是他们负责智能化设计	2025-09-05 05:41:11.683566	13	t
1431	2025-09-05	809	602	772	拜访威汉的苏总，介绍我司的产品和解决方案优势，机场项目的成功案例以及合作模式，通过苏总了解温州机场的目前对讲系统的情况，大家在后期合作事宜达成一致，近期会针对此项目合作，签定的合作意向书，明确在此项目中双方合作的权宜	2025-09-05 05:45:10.531363	13	t
1432	2025-09-05	259	405	773	拜访业主张总，介绍江苏中业的卢总，此项目江苏中业参与前期的设计和后期投标，江苏中业拿到图纸相关的资料，安排福玛的小陈对接，配套设计 	2025-09-05 05:50:03.617678	13	t
1433	2025-09-05	\N	355	773	和江苏中业的卢总沟通项目设计方案和产品选型，此项目预算有限，方案参考之前地块的方案，基本配制，推荐和源全套产品	2025-09-05 05:51:58.499009	13	t
1436	2025-09-05	794	481	\N	1.客户这里表示是否可以报价1000元以内一台PNR2000； 这个价格以内的话采购100台是可以的； 还需要倪总来决定；\r\n2.客户这里还让报消防跟物业的维保； 说维保一签即3年，是否比1年的能优惠； \r\n如果能同意的话，下周让我带着3个报价直接上门了就；	2025-09-05 11:42:48.571192	20	f
1437	2025-09-05	795	556	\N	下周二上门报价；	2025-09-05 11:54:37.421894	20	t
1438	2025-09-05	65	62	\N	沟通后续项目合作机会，了解目前在参与推进的项目。	2025-09-07 06:19:07.824043	16	t
1439	2025-09-05	811	608	\N	陪同代理商陈总拜访谷总，沟通后续在南京交通领域如何推动和源产品进入项目合作。	2025-09-07 06:28:52.29353	16	t
1440	2025-09-02	812	609	\N	陪同倪总拜访客户，介绍公司情况，沟通后续双方项目合作事宜。	2025-09-07 06:33:59.554579	16	t
1441	2025-09-04	813	610	\N	拜访张总，介绍公司及产品情况，商谈后续项目合作事宜。	2025-09-07 06:51:54.667133	16	t
1442	2025-09-07	803	596	\N	拜访秦工，沟通项目技术实现，主要明确了设计方案及实现功能不能调整，现在选用的摩托产品在集群情况下是无法完成巡更功能的。沟通了项目的进展，现在进度要比预期晚。最终产品选择还是需要与集成商沟通商定。	2025-09-07 06:57:10.072879	16	t
1444	2025-09-02	\N	147	161	万睿销售蔡炽介绍，本项目推迟到10月招标，由于甲方内部资金问题推迟招标。	2025-09-07 15:18:35.394126	17	t
1445	2025-09-04	\N	\N	776	深圳电信工程政企部林嘉豪介绍，智能化近期已经中标，无线对讲传输系统没有品牌限定，前期投标是根据总体成本去投的，接下来需要我方配合技术部做深化和成本优化。	2025-09-07 15:30:51.258517	17	t
1446	2025-09-05	\N	490	777	建筑面积23万平米，霍尼韦尔销售经理介绍，本项目前期配合集成商投标，他们跟集成商中国二十二冶关系不错，他们进场没多久，下周会到项目现场拜访，帮忙介绍认识。	2025-09-07 15:37:38.437401	17	t
1447	2025-09-04	\N	118	679	集成商已跟瀚网签采购天线和耦合器合同，嫌线缆较贵另外采购。设备类的采购要分第二次合同，集成商还想做设备优化，将数量尽量减少，压缩成本。	2025-09-07 15:41:33.099834	17	t
1448	2025-09-05	429	435	\N	与科思创项目区域负责人沟通D600冷库区域信号问题，分析对讲机使用功率的问题，确认下周给出方案；	2025-09-08 05:24:48.395895	7	t
1449	2025-09-05	451	259	\N	与上海中心大厦业主沟通本次350兆消防用无线对讲系统设备更新的进展，下周6套远端机将现场安装完成，沟通2026年对于系统设备更新的预算和计划，对于整套系统功能提升和和源新技术新设备进行了介绍；	2025-09-08 05:30:27.840515	7	t
1450	2025-09-08	426	435	\N	与区域负责人沟通了B458,B391区域可能存在的问题，区域负责人根据我们沟通的去与生产负责人确认出具故障响应PO单，收到PO单后安排工程师至现场检修；	2025-09-08 05:37:18.913168	7	t
1451	2025-09-05	439	470	768	与ERC负责工程师沟通了本次深圳中芯国际的询价内容和分项报价，核实了我们的报价与ERC部门申请的预算是否匹配等问题；	2025-09-08 05:39:21.299925	7	t
1453	2025-09-09	755	559	\N	对接人领导休假回来了，暂定下周二上门拜访；	2025-09-09 02:12:24.339068	20	t
1454	2025-09-08	814	282	\N	付海军给到一批名单，先自己过一遍，明日跟付沟通后再联系客户；	2025-09-09 02:15:16.001694	20	f
1455	2025-09-09	795	556	\N	方案报价检测报告赢给到集成商，同时也告知业主，把报价部分隐藏了给到业主，后续继续跟进；	2025-09-09 02:18:08.759841	20	t
1456	2025-09-05	750	554	\N	询问客户上次去了之后的情况，以及内部这里音量调整的进度； 客户这里反馈信道机后继没啥问题，内部项目这里表示大约15号左右会有结果；催进度；	2025-09-09 02:25:23.21299	20	t
1457	2025-09-09	814	282	\N	付海军让周四去趟淳泊对客户名单；	2025-09-09 02:41:22.352143	20	f
1458	2025-09-09	433	251	665	跟客户约了本周四上门拜访，需要把检测报告给到客户；报刊架客户问到2026年的维保价格是否跟今年一样，请示两位领导后一起答复客户；	2025-09-09 05:38:26.582408	20	t
1459	2025-09-09	433	251	\N	跟客户约了本周四上门拜访，需要把检测报告给到客户；包括客户问到2026年的维保价格是否跟今年一样，因现在需要做明年的预算了，请示两位领导后一起答复客户；	2025-09-09 05:39:29.098661	20	t
1460	2025-09-09	433	251	\N	跟客户约了本周四上门拜访，需要把检测报告给到客户；包括客户问到2026年的维保价格是否跟今年一样，因现在要做 明年的预算了，请示两位领导后一起答复客户；	2025-09-09 05:40:42.986198	20	f
1461	2025-09-09	753	557	\N	客户目前是想要达到监控的功能，但是之前瀚网做的设备不具备此功能；客户预算有是有，不过达不到整体改造的数字；目前在技术的帮助下逐步解答客户的问题，看看是否能在客户预算内帮客户解决；	2025-09-09 06:55:53.379364	20	t
1463	2025-09-11	131	444	695	三个厂区进行三方报价盖章，出维保方案。\r\n杨震-SL2M对讲机询价，报价。	2025-09-11 08:11:41.26004	2	t
1464	2025-09-08	119	435	779	7月客户已购买80套设备，目前因项目再增加20套，确认订单。	2025-09-11 08:15:29.572382	2	t
1465	2025-09-10	\N	260	56	订单已完成交货，现场安装调试已完成，出具调试报告。	2025-09-11 08:19:50.329317	2	t
1466	2025-09-11	\N	423	780	客户确认此场赛事需要通信保障。	2025-09-11 08:25:18.199058	2	t
1467	2025-09-08	799	91	\N	拜访集成商，沟通无锡奥体中心项目公安350MHz项目	2025-09-11 11:38:00.604421	16	t
1468	2025-09-09	816	612	\N	沟通现有项目进展情况，沟通其他在建项目合作机会	2025-09-11 11:49:46.379576	16	t
1470	2025-09-09	88	85	\N	沟通现有项目进展情况，沟通后续项目合作机会\r\n	2025-09-11 11:52:41.549181	16	t
1471	2025-09-10	776	7	\N	沟通雄安新区国贸中心项目跟进情况，后续配合分工。	2025-09-11 11:55:13.847862	16	t
1472	2025-09-11	11	9	\N	沟通近期市场和项目合作机会	2025-09-11 11:56:51.428231	16	t
1473	2025-09-11	38	11	\N	沟通最近跟踪项目机会，下周一之前整理出来。商谈了雄安国贸中心项目的情况，后续配合。	2025-09-11 11:59:11.532957	16	t
1474	2025-09-10	40	8	542	沟通了项目的目前状况，枢纽采用350MHz专网和公专网结合模式，目前品牌基本已定，天馈和源入围，后续项目会分为5个包发布（包括酒店部分）。目前已知报名参与集成商约40家。	2025-09-11 12:04:05.454618	16	t
1475	2025-09-09	\N	\N	542	与业主辛工通了电话，表示目前属于敏感期不易见面，后续项目开标后再约。	2025-09-11 12:06:38.128467	16	t
1476	2025-09-10	\N	78	597	沟通了项目的目前状况，酒店采用专网模式建设，体量不大。目前品牌基本已定，天馈和源入围，后续项目会做为一个独立标段发表。目前已知报名参与集成商约40家。	2025-09-11 12:09:00.444518	16	t
1477	2025-09-11	429	435	\N	与D600&E188区域负责人开会讨论D685,D634,D635冷库区域点位增补事宜，根据现场反馈和区域重点修正点位，确认位置和图纸，更新方案和清单，业主根据新的清单下PO单；	2025-09-12 01:26:31.921757	7	t
1479	2025-09-12	419	248	\N	拜访卓展弱电团队，与赵铁军、庄妍华及李霄云沟通。\r\n今年新增业务较少，目前集中在酒店行业，跟着酒管公司参与全国各地新建酒店投标及设计。目前弱电团队人员10人，部门规划从原来两个团队合并至一个团队，专业上也不在区分，强弱电合并，但实际设计配套时还是会有所区分，团队负责由强电人员管理。\r\n	2025-09-12 03:13:19.235481	14	t
1480	2025-09-12	500	282	24	与邹飞沟通，他与王亮了解张家浜C1C-01地块项目，业主浦开在走招投标流程，预计9月中下旬完成招标。但项目现场进度置前于项目招标，预计9月底10月份天馈就会启动实施。实际商务方面需要等到业主招标完成确定上安中标，上安中标签订合同发起采购流程，才与王亮合同签订，按此流程预测实际商务启动最晚11月份	2025-09-12 03:20:13.075262	14	t
1481	2025-09-12	682	497	24	与李冬沟通，他与壹杰采购徐骏沟通张家浜绿地C1B-02地块，徐骏透露公司期望价格在60万以内，按目前清单报价与壹杰期望值差距较大。计划一边保持与壹杰沟通，评估方案和成本，再看价格如何调整，另一边将此情况反馈给予梅小好，与其商议业主环节是否能够要求壹杰按照招标内容实施采购	2025-09-12 03:25:42.331031	14	t
1482	2025-09-11	418	248	60	与李霄云确认云赛后续并未提交系统品牌资料进行报验审批，同时业主彭俊离职，接手的为企业内部负责工厂生产的人在接手管理。目前现场进度也并不了解，通过与渠道及集成商之前沟通，应该是找了沅抗郭鹏采购了系统设备	2025-09-12 03:29:18.513604	14	t
1483	2025-09-11	762	565	210	渠道反馈，南大104-02地块，跟踪欣钶负责人李伟，他已经提交了采购计划，但欣钶总经理近期一直忙于未来得及审批，答复下周会当面盯着确认，预计顺利的话下周至9月底合约能够正常推进，与代理商确认一旦欣钶发起合同流程就进行价格审批	2025-09-12 03:32:28.834285	14	t
1484	2025-09-11	682	497	517	渠道反馈，跟踪华虹智联采购周心一，有关采购合同流程提交审批，但公司流程迟迟没有批复。本周如还没有答复，渠道计划至华虹智联公司拜访，当面了解其中情况，并通过现场督促公司采购尽快落实	2025-09-12 03:35:28.561014	14	t
1485	2025-09-10	536	215	593	该项目投标结果公布，上安宣布第一候选人中标。侧边了解最后业主要求让利，他们打了比较大的折扣，要求我们系统进行让利	2025-09-12 03:44:16.338821	14	t
1486	2025-09-10	507	288	516	渠道反馈，该项目集成商在投标过程中最后与业主议价，集成商要求我们价格给予调整，考虑到原商业办公采用竟品，且正禄也在找机会跟进，所以计划价格上重新复核给予一版优惠报价	2025-09-12 03:46:56.412717	14	t
1487	2025-09-11	736	214	\N	与王粤沟通，有关海神项目，与业主消防负责人孔令冲沟通情况反馈给予王粤，并且通过王粤介绍中标集成商北京首安项目现场负责人。计划下周邀约拜访	2025-09-12 03:49:21.878647	14	t
1488	2025-09-11	786	582	\N	与金晓俊沟通，有关嘉华P18项目，目前无线对讲系统中标集成商还未提交报验资料，之前与业主设计部门有过确认，从嘉华内部管理流程，设计不直接对接项目现场，项目现场由工程部负责对接，而中标集成商负责人黄斌勇与他们关系较好，目前与黄斌勇联系，对方回复项目不着急，并没有让我们过多参与介入。但按金晓俊表露意思，港资项目如果顾问不确认进场是不符合流程的，只能进一步观望同时继续保持与黄斌勇沟通联系。\r\n另外嘉里金陵中路64、65地块，中标集成商永天提交和源品牌资料，目前金晓俊和业主季浩刚拿到，在进行审批，但根据代理商反馈的情况，永天商务决策人主要是老板娘，但近期老板娘不在国内，所以最终情况如何不好判断，只能持续保持跟进	2025-09-12 03:55:03.90799	14	t
1489	2025-09-09	784	579	80	渠道反馈，该项目集成商按业主要求需要进行一轮专项方案汇报，待方案汇报完成确认后，就会启动采购询价流程，预计在10月底11月份	2025-09-12 03:57:29.213956	14	t
1490	2025-09-10	478	350	64	与毛晶轶沟通，了解酒店考虑后续存在变化，设计还未完确定稿，但办公部分已经设计完成，预测智能化招标可能在今年年底或者明年初。至于招标技术要求和品牌虽然WSP负责，但业主会交由华东院复核，这块毛晶轶拿到后会找我们确认，有关品牌植入，会说服用户按我们的方式去推进	2025-09-12 04:02:32.743911	14	t
1491	2025-09-12	433	251	665	客户这里表示，两个项目的正式流程都在12月，客户这里建议分项列表，可以用增补协议的方式来进行，这样也不用再公开招投标了，价格也不变。这样是最好的。	2025-09-12 04:08:18.343899	20	f
1492	2025-09-09	478	350	699	与毛晶轶沟通，了解整个智能化招标图他按我们的设计完成，只要业主不提出，基本不会存在变化，至于招标技术要求和品牌现在还不确定是否他们负责，不过可以确认的是此项目业主仍旧是东方枢纽，负责浦东东站的同一波人	2025-09-12 04:11:06.746809	14	t
1493	2025-09-09	477	350	207	与李源沟通，了解用户取消无线对讲系统	2025-09-12 04:34:46.976284	14	t
1494	2025-09-09	477	350	159	与李源沟通，了解他们只是负责常规弱电，智能化由业主找了当地一家小企业，基本确认设计实施都是他们来做，没有好的机会切入进去	2025-09-12 04:37:15.309051	14	t
1495	2025-09-09	294	350	673	与黄辰贇沟通，了解此项目目前还在做招标前准备，招标代理复核参数，至于招标品牌还未完全定稿，曙腾印象中黄辰贇反馈是招标代理提供的，最终如何去推动还在观望，至于中标单位大概率是浙江省邮电，但没有具体联系方式	2025-09-12 04:53:17.279961	14	t
1496	2025-09-09	728	241	32	与张鸿沟通，推进深化方案配套，待配套完成他们提交给予确认，确认后会启动内部招标审核会议，届时需要跟进确保招标在可控范围，与原定时间有所延后，整个流程预计在2个月，估计招标会在年底前启动	2025-09-12 04:56:13.539	14	t
1497	2025-09-10	397	323	782	发现项目阶段，属于公建类场馆，省院刘译泽负责设计智能化，预计年前方案启动初设。已经沟通对接上后续跟进阶段配合设计。	2025-09-12 05:05:49.555282	15	t
1498	2025-09-11	398	323	712	配合省院设计方案预算全套和源，提供三个品牌植入。预计年底前进行招标，业主采用邀标形式。	2025-09-12 05:07:47.24488	15	t
1499	2025-09-11	817	58	\N	对方负责智能化设计，原来接触的正禄和朔通合作过，介绍了和源产品和目前的配合流程。	2025-09-12 05:15:20.424697	15	t
1500	2025-09-12	814	282	\N	上门跟付海军对客户名单，上海国际财富中心、华泰金融大厦、南通科创中心周浦体育中心、前滩纽约大学、上海华邑酒店、上海瑞华酒店、中海油大厦、董家渡金融城、上海虹桥龙湖霞菲公馆、上海人民银行征信中心；（无联系人）\r\n仁恒河滨城三期、嘉定中兴泰富万达广场、嘉定印象城购物中心、上海歌斐中心商场、上海领展企业广场（有联系人，但是不确定是否还在职，需要联系）\r\n要求无联系人的可以给我相关合同，好继续对接；\r\n	2025-09-12 05:16:10.780851	20	f
1502	2025-09-12	493	181	\N	与舒辉沟通，了解深圳乐高情况，是否有团队人员至上海考察及咨询，回复他这边建设口快没有接触过深圳团队，其帮我们从其他部门有过侧边了解，也没有相关人员信息	2025-09-12 05:29:43.210065	14	t
1503	2025-09-12	\N	196	517	合同审批流程采购已经提交，了解到流程目前在公司总经理那边，后续还有项目登记，预计流程还需一周左右。计划下周跟进采购，了解流程情况，推进商务签订。项目现场反馈预计国庆后需要供货。	2025-09-12 06:28:20.119534	36	t
1504	2025-09-10	818	613	658	拜访业主介绍和源产品，目前机电在招标，弱电设计二期还没开始，省院的设计师后续接触配合方案。顾问已经对接上后续规格书参数功能同步配合植入。	2025-09-12 06:32:39.45229	15	t
1505	2025-09-11	\N	381	594	达实技术部许工介绍，当前进场时间和深化还没有确定。	2025-09-14 14:51:12.82949	17	t
1506	2025-09-08	\N	\N	204	裴小印让我方配合协调其他代理商不要报价，提前提醒避免再次出现冲突。	2025-09-14 14:55:55.410446	17	t
1507	2025-09-12	577	93	577	目前已经确定是厦门万安总部中标，裴小印已经通过当地同事确认。下一步确定深化时间以及采购时间。	2025-09-14 14:59:16.804888	17	t
1508	2025-09-15	814	282	\N	催付合同跟来福士400M系统图；	2025-09-15 10:07:42.367372	20	f
1509	2025-09-15	429	435	\N	根据E188生产的需求，修正9月12日的方案与清单，设计人员完成方案与清单的修正审核后，提交给E188生产负责人对两个方案进行确认，然后形成PO单	2025-09-16 01:20:48.657488	7	t
1511	2025-09-16	\N	433	748	项目前期规划阶段，已和集成商约时间沟通项目植入细节。	2025-09-16 04:46:51.014386	3	t
1512	2025-09-16	\N	497	747	目前，我司已与顾问公司签订品牌入围协议，在该协议方案里，消防部分指定了唯一品牌及货源。为维护市场秩序与品牌价值，确保项目顺利推进，烦请厂家协助进行品牌价格保护。后续若涉及此项目的相关报价，请统一按与我司协商后执行，以保障各方利益，促进合作圆满完成。 	2025-09-16 05:17:40.395989	3	f
1514	2025-09-16	795	556	\N	客户暂定周四，明日再确定；	2025-09-16 09:38:07.435647	20	t
1515	2025-09-16	820	615	\N	客户本月到保，确实最近在考虑质保单位的事，约了明天上门拜访；	2025-09-16 09:39:36.584803	20	f
1516	2025-09-18	131	444	\N	三厂的对讲机PR流程已完成，进入采购议价阶段，进行二次报价。	2025-09-18 02:19:10.834094	2	t
1517	2025-09-18	119	435	\N	新购买的机器版本升级，按用户需求重新制作频率模板。	2025-09-18 02:30:40.667887	2	t
1518	2025-09-18	115	435	788	此项目为E188项目区域的冷库信号增补，按用户需求出具方案，按E188项目产品价格进行报价。	2025-09-18 02:32:39.072516	2	t
1519	2025-09-17	\N	423	780	赛前进行巡检测试，测试主、备系统设备正常，通信正常。	2025-09-18 02:34:21.271397	2	t
1520	2025-09-12	\N	65	781	系统产品投标报价	2025-09-18 03:20:05.031665	16	t
1521	2025-09-12	77	21	781	配合集成商中通服产品报价	2025-09-18 03:22:15.802468	16	t
1522	2025-09-16	77	21	781	配合集成商中亿丰产品报价	2025-09-18 03:22:53.680166	16	t
1524	2025-09-17	794	481	\N	客户表示400M物业的先放一放，350M消防的需要先解决；让我司出一个维修的方案跟报告；最好在国庆前我们能派人去检测一下；	2025-09-18 13:13:52.599296	20	t
1525	2025-09-17	820	615	\N	原联系人已离职，对接了现工程部经理跟弱电负责人，对接人表示现在使用公网的对讲机是因为之前有问题一直没解决好，所以后面就渐渐不用了；询问如果解决问题的话是否会沿用，对方让出个解决方案跟维保报价；	2025-09-18 13:28:32.388769	20	t
1526	2025-09-18	795	556	\N	见了银江，对方认可我们的报价，会在我们的报价上再加人工；不过对于报告需要整改，弱化B2，强化葡萄园；再加上对讲机电池的报价一起报；	2025-09-18 13:34:18.278719	20	t
1527	2025-09-18	183	350	109	配合华东院整理好T3、交通中心的招标清单和技术规格书给到吴老师	2025-09-18 14:21:17.572321	13	t
1528	2025-09-18	\N	350	796	配合华东院进行项目拆分，提供相关招标清单和技术文件	2025-09-18 14:57:03.144117	13	t
1523	2025-09-16	\N	288	781	配合集成商上海银欣高新技术发展股份有限公司产品报价	2025-09-18 03:24:49.733817	16	t
1599	2025-09-29	\N	215	820	渠道报备，配合上安九分华南分公司参与项目投标。品牌入围，主要竞争为烈龙、锐河。	2025-09-29 04:25:29.258002	14	t
1510	2025-09-15	438	423	\N	与久事赛事负责人沟通9月19日-9月21日和10月6日-10月8日两场赛事的赛事保障事宜，对中秋节这场赛事的通信保障提出了人员的要求，并协调安排；	2025-09-16 01:26:05.404912	7	t
1529	2025-09-19	\N	304	37	该项目集成商万安中标，目前询价阶段，因前期植入与顾问签有品牌入围协议，烦请厂家协助进行品牌价格保护。后续若涉及此项目的相关报价，请统一按与我司协商后执行，以保障各方利益，促进合作圆满完成。	2025-09-19 02:28:15.116467	3	t
1530	2025-09-18	823	181	\N	拜访罗工，引荐售后服务徐昊，了解项目交付使用情况，及后续运维如何考虑，同步侧边了解深圳乐高情况，前期深圳项目建设预期早于上海，但后面由于资金问题，整体建设速度晚于上海，所以现在深圳会借鉴上海的情况。同时通过建设舒辉了解到，北京宝冶退出，五矿带资进场作为大总包，深圳弱电负责人为马骥，与郭总汇报沟通了解他们已经衔接	2025-09-19 03:22:39.650522	14	t
1531	2025-09-19	541	217	\N	与卢洪祥聚餐，了解项目情况。目前弱电团队共计3人，各自负责业务，但隧道项目集中在卢洪祥手上。其手上目前主要有4条隧道，上海真如、嘉兴、绍兴及太仓。其中上海真如项目提交概算审批，等待确认后会挂网招标，项目为EPC，通过代理商跟踪上电科的子部门了解，他们中标几率较大。项目预计今年底会启动招标。而太仓隧道没有任何进展，仅了解到大总包中标，但智能化公司还没浮现出来，嘉兴项目还在早期设计阶段，等图纸设计启动会介入跟踪配合	2025-09-19 03:25:57.954038	14	t
1533	2025-09-17	563	234	\N	拜访庄彦，汇报了解张江创新药和张江人工智能岛进度，了解今年是否有新增业务，目前由于上海政府要求及市场环境，新增项目都偏小型改造	2025-09-19 03:42:54.292324	14	t
1534	2025-09-17	785	581	797	代理商配合设计院设计，植入和源方案，目前品牌还没确认是否由他们来推荐。	2025-09-19 03:44:49.047756	15	t
1535	2025-09-17	824	234	\N	通过庄彦引荐，认识国信安设计另一个负责人王良超，介绍和源企业及行业情况，与超哥了解创新药A地块中2个项目情况。其中九谷中标的，品牌确认使用为和源，但项目要到年底才建筑结构封顶，智能化明年启动，而另外一个还需要了解中标单位信息，项目进度晚于九谷中标的地块。至于周浦医疗园，中标单位奂源报的海能达品牌，让超哥了解具体招标品牌范围，并沟通海能达不做系统传输部分，后续进一步跟进	2025-09-19 03:46:13.857545	14	t
1536	2025-09-17	824	234	\N	通过庄彦引荐，认识国信安设计另一个负责人王良超，介绍和源企业及行业情况，与超哥了解创新药A地块中2个项目情况。其中九谷中标的，品牌确认使用为和源，但项目要到年底才建筑结构封顶，智能化明年启动，而另外一个还需要了解中标单位信息，项目进度晚于九谷中标的地块。至于周浦医疗园，中标单位奂源报的海能达品牌，让超哥了解具体招标品牌范围，并沟通海能达不做系统传输部分，后续进一步跟进	2025-09-19 03:46:16.854013	14	t
1537	2025-09-15	682	497	\N	推动渠道批价沟通确认，提交张江人工智能岛、招商船厂业务和松江海螺水泥批价	2025-09-19 03:50:48.390098	14	t
1538	2025-09-19	389	317	601	李波反馈合同经过沟通已经确认没有问题，预计近期就要进场。批价确认流程已经提交。	2025-09-19 03:56:29.065806	15	t
1539	2025-09-19	750	554	\N	跟客户约了下周二上门调整对讲机音量的事情；	2025-09-19 06:09:55.256456	20	t
1540	2025-09-19	814	282	\N	催付合同金额等细节，催回复这两天展会，最晚下周一给到；	2025-09-19 08:23:27.421519	20	f
1541	2025-09-19	794	481	\N	跟客户约了下周四去现场测试设备，董老师跟时雪峰一起；	2025-09-19 09:08:56.129085	20	t
1543	2025-09-18	825	618	\N	信息咨询，对公司情况做初步介绍，并商定19日周五下午3:00进行技术交流线上会议。	2025-09-20 11:40:31.350041	16	t
1544	2025-09-19	825	618	\N	组织技术及客户的供应链、技术团队参与进行1:20分钟视频会议，对公司的情况、产品、芯片厂区建设技术解决进行了交流。	2025-09-20 11:41:22.744057	16	t
1545	2025-09-19	826	619	542	询价	2025-09-20 11:54:28.028277	16	t
1546	2025-09-19	827	620	542	询价	2025-09-20 11:55:23.756797	16	t
1547	2025-09-16	803	596	65	沟通了：项目目前选型中的技术问题，无法解决系统功能实现。	2025-09-20 12:08:44.528553	16	t
1548	2025-09-16	828	30	65	和项目经理详细介绍了我们产品在这个项目上的优势，以及业主对系统功能一定要实现的态度。	2025-09-20 12:10:38.000975	16	t
1549	2025-09-16	5	44	63	现场协助代理商、集成商解决产品报验资料事宜。	2025-09-20 12:12:45.441137	16	t
1550	2025-09-18	21	75	794	要求根据提供的资料，进行方案设计	2025-09-20 12:18:05.82715	16	t
1551	2025-09-18	77	21	794	开始进行初步方案设计	2025-09-20 12:19:00.400716	16	t
1553	2025-09-15	71	50	774	咨询、沟通蚂蚁项目的情况	2025-09-20 12:21:59.76487	16	t
1554	2025-09-18	77	21	774	配合对图纸进行方案初步设计	2025-09-20 12:22:40.885878	16	t
1555	2025-09-17	\N	162	800	庄工介绍了承建方中信建设工程部余工，已和余工约好下周拜访，介绍我品牌优势和案例，进一步了解预算和需求。	2025-09-21 16:20:21.491159	17	t
1556	2025-09-22	332	205	798	项目品牌入围和源，代理商配合凯通投标。后续跟进项目投标情况。	2025-09-22 03:43:00.180157	15	t
823	2025-06-06	\N	288	78	该项目经了解品牌已经确认，商务由于总包与智能化分包电科合同还没签署，电科作为国企供应商采购流程无法发起，按目前回复电科与总包合同最迟本月底会落实，一旦落实后第一时间会启动商务谈判和确认，预测最迟下月会完成供应商确定	2025-06-06 02:28:32.063395	14	t
1190	2025-08-11	\N	288	700	渠道反馈，该项目上安九分中标，推进深化方案确认，改用全和源产品，商务已经启动洽谈，计划8月份提交批价确认	2025-08-11 07:58:43.086187	14	t
841	2025-06-09	\N	288	102	该项目通过付海军拜访现场负责人刑梁易，按刑梁易反馈的情况，品牌已经提交并确认为和源，下一步计划就是把图纸方案进行深化，现场执行还在做管线预埋，预计三季度末无线对讲会启动设备采购及实施工作	2025-06-09 07:07:55.805552	14	t
1081	2025-07-23	\N	288	101	该项目联检部分经了解集成商发起询价流程，渠道在配合投标走流程。酒店部分集成商还在招标过程，预计8-9月份才会启动商务流程。	2025-07-23 09:09:15.167575	14	t
1316	2025-08-26	\N	288	697	目前集成商已中标，正在配合集成商出方案及清单！	2025-08-26 03:08:16.322514	23	t
1557	2025-09-22	796	590	\N	客户十一期间的活动需要保障，沟通淳泊上门修复直放站；以便于后期聊维保；	2025-09-22 08:57:53.899042	20	f
1558	2025-09-24	214	219	273	设计院介绍总包负责人对接，了解项目的情况，项目湖南建工总承包，广州联通拿到分包后又分包给广州德莹，无品牌要求，先沟通方案	2025-09-24 03:38:12.604973	13	t
1600	2025-09-29	250	399	512	西安瑞林达客户那边没有搞定，项目丢掉了	2025-09-29 05:09:10.958598	13	t
1559	2025-09-24	767	571	705	组织业主、代理商小陈开方案沟通会议，业主预算有限，计划采用最简单的方式先进行报批，基站+室外天线的方式，协调代理商出具相关方案	2025-09-24 03:42:38.528945	13	t
1560	2025-09-24	714	359	640	光端机的变更的方案机场已批复，批复函已发给民航二所，待二所和四川中航建落实变更后，和我们签定合两同变更补充协议	2025-09-24 03:45:23.847157	13	t
1561	2025-09-24	177	343	614	易总反馈这个项目也是通过中间人在跟进的，反馈有些不及时，和易总商量，节后安排和中间人见面沟通下。	2025-09-24 03:48:23.737521	13	t
1562	2025-09-24	750	554	\N	跟小何，董师傅，时雪峰一起上门，当场帮客户解决了音量问题；客户表示很满意，并且后续有增补的话也会直接找我们；推荐了PNR2100；	2025-09-24 07:37:57.437086	20	t
1563	2025-09-24	820	615	\N	客户 10月的大型活动，要求淳泊这里先把现有的问题修复，已经上过门帮客户换了直放站，跟对讲机的使用，能确保客户10月活动的正常进行；	2025-09-24 07:47:13.599761	20	t
1564	2025-09-24	680	477	\N	约客户拜访，客户表示国庆期间比较忙，节后再来；	2025-09-24 07:49:12.359723	20	t
1565	2025-09-24	830	622	\N	客户两年前就换了公网的对讲机，因当时只剩8台了，即时购买了； 不过不排除之前系统还能用起来的可能性，先加了微信先聊起来；	2025-09-24 08:47:13.394175	20	t
1566	2025-09-24	831	624	\N	对接人已调到别的印象城，给了现任胡工的联系方式；	2025-09-24 09:40:00.55635	20	t
1567	2025-09-24	832	625	\N	对接人暂时不负责这块，给了相关联系人的手机号，再联系；	2025-09-24 09:42:44.053552	20	t
1568	2025-09-24	833	626	\N	原对接人已离职，给了现负责人顾春荣手机号，已加微信，后续保持沟通；	2025-09-24 09:56:45.922771	20	t
1569	2025-09-24	795	556	\N	根据银江的要求修改了方案跟报告，报价加上了对讲机的电池部分，后续保持跟进；	2025-09-24 10:03:28.857333	20	t
1570	2025-09-22	834	564	\N	客户了解无线对讲系统在项目建设过程中的作用和系统在超大空间里的优势等；	2025-09-25 01:37:13.247162	7	t
1571	2025-09-24	834	564	\N	客户提供具体项目的信息，根据信息提供和源机场案例，进一步沟通交流中为客户分析在大型项目的建设期无线对讲系统的作用；	2025-09-25 01:39:42.630226	7	t
1572	2025-09-18	821	616	\N	与中芯国际（北京）ERC负责人沟通他们的需求，业主表示北京中芯希望能够建立一套全新的无线对讲系统，要求与上海中芯南方的系统达到一样的级别和标准；	2025-09-25 01:45:23.726896	7	t
1573	2025-09-24	821	616	\N	提供和源为中芯南方建设无线对讲系统的方案介绍，提供部分和源产品的产品彩页技术参数等等，并且沟通了部分系统延申功能；	2025-09-25 01:49:37.859652	7	t
1574	2025-09-23	439	470	768	与业主ERC负责人确认了已完成响应中芯深圳的报价邮件，沟通确认了本次合约的主体为和源股份（原本在中芯深圳里面的主体为和源工程），避免后期因开票类型出现问题，讨论项目大概的执行时间端；	2025-09-25 01:56:11.914439	7	t
1575	2025-09-19	439	470	768	与业主方ERC负责人初步沟通了今年系统检测的大致时间和检测内容；	2025-09-25 02:00:24.4723	7	t
1577	2025-09-22	434	252	112	与机场业主沟通了新的四年无线对讲系统维护合约的签订后启动的事宜，包含新的履约保证金的支付与上一个合约周期履约保证金退回等；	2025-09-25 02:05:11.535986	7	t
1578	2025-09-18	835	629	\N	至上海金山乐高乐园与HSS部门负责人建立联系，并了解了目前无线对讲系统的交付情况和现场使用情况；	2025-09-25 02:14:01.871329	7	t
1579	2025-09-19	427	435	\N	与科思创区域负责人沟通了B193区域与B123区域故障现象，区域出PO单，约定周一9月22日工程师至现场排查故障，并且与现场协调沟通故障排查脚手架搭建事宜；	2025-09-25 02:30:45.899842	7	t
1580	2025-09-25	426	435	\N	与区域负责人沟通了IOBC区域的故障状况，由区域出PO，节后安排工程师至现场排查；	2025-09-25 02:34:55.309817	7	t
1581	2025-09-25	\N	497	801	邀请厂家销售参与该项目的交流活动，推进品牌报审。	2025-09-25 02:51:23.998464	3	t
1582	2025-09-25	\N	423	780	赛事保障完成，系统正常，通信正常。	2025-09-25 03:28:12.885804	2	t
1584	2025-09-22	429	435	788	客户确认方案及订单，安排备货及发货。	2025-09-25 03:30:04.615332	2	t
1585	2025-09-24	836	630	\N	客户国金项目上对讲机需要采购一批电池，报价给用户，确认订单购买，安排备货及发货。	2025-09-25 03:43:10.784642	2	t
1586	2025-09-25	837	631	809	渠道报备，配合参与投标	2025-09-25 05:31:52.697562	14	t
1587	2025-09-25	838	592	807	渠道报备，配合参与投标	2025-09-25 06:19:56.541767	14	t
1588	2025-09-26	739	411	667	项目启动了，铁二院准备初步方案，计划10月份去昆明进行一次汇报，我们刚拿到图纸，和设计院以及刘威沟通好图纸问题和需求，10月14号前先配合设计院出图	2025-09-26 04:20:08.098763	13	t
1589	2025-09-25	794	481	\N	跟董师傅、时雪峰一起上门，帮客户的消防 350M 系统做检测，客户要求国庆前给到维修的价格；	2025-09-26 04:58:53.251878	20	t
1590	2025-09-26	841	624	\N	 此人是管理物业的部门经理，约了下周去看现场；	2025-09-26 09:32:15.900461	20	t
1591	2025-09-28	\N	497	812	瀚网配合擎天参与项目报价，该项目大总包中建科技中标，擎天配合参与智能化报价，有关对讲机系统品牌入围，并根据招标要求为原系统兼容	2025-09-28 00:32:10.266604	14	t
1594	2025-09-28	\N	497	816	配合集成商投标，全系列和源产品	2025-09-28 03:58:44.346381	3	t
1595	2025-09-28	\N	535	289	配合：安徽讯飞、中电兴发、航天科工	2025-09-28 09:16:20.847211	16	t
1596	2025-09-28	77	21	289	配合集成商：中电兴发、达尔、讯飞、安泰、中科软	2025-09-28 09:17:19.509947	16	t
1597	2025-09-26	593	112	818	终端品牌：海能达、摩托罗拉、建伍；天馈品牌：海能达、和源、烈龙、锐河。\r\n已让裴小印对接中建电子配合投标，因他们的线缆也在品牌表内，有销售同事跟她提起过这个项目。洪昇介绍他们也在跟进这个项目，暂无集成商找他们询价。	2025-09-28 15:11:10.479219	17	t
1598	2025-09-25	\N	124	819	品牌：创飞腾、超诺、和源。\r\n裴小印配合万安参与投标。	2025-09-28 15:13:34.262986	17	t
1253	2025-08-19	\N	340	723	成都天皓的李总报备，目前配合总包提供和源产品和相关参数用于后期招标使用，项目参考一期的要求，采用基本的配制	2025-08-19 15:07:52.069875	13	t
1608	2025-10-09	40	8	822	配合完成技术参数植入	2025-10-09 01:48:23.378985	16	t
1576	2025-09-16	438	423	\N	与赛车业主负责人沟通了中秋节赛事保障事宜，由于本次赛事赛车场业主首次自主赛事，所以业主非常重视，确认了赛事保障人员及相关事宜；	2025-09-25 02:02:32.922137	7	t
1601	2025-09-29	237	392	821	项目已中标询价，安排福淳对接配合图纸深化，洽谈商务	2025-09-29 05:27:23.599257	13	t
1602	2025-09-23	\N	635	408	项目开始招标，配合集成商开授权。	2025-09-29 07:16:55.183282	36	t
1603	2025-09-25	\N	309	558	配合集成商提交资料给顾问公司，目前所需资料已全部提交。他们开始走流程批B。	2025-09-30 01:20:47.168918	36	t
1605	2025-09-30	\N	607	436	项目有变动，品牌控不了	2025-09-30 03:02:09.041419	25	t
1606	2025-09-29	841	624	\N	跟新的对接人见面了，此人是现任商管经理，管理印象城物业部的，不过对于内部的东西也不是最清楚； 给客户演示了我们的对讲机，对方表示后续如果需要采购的话会联系我的；	2025-10-09 01:21:00.218357	20	t
1607	2025-09-30	664	472	\N	参加了物业跟中铁二局的内部参会，客户介绍了中铁二局的领导，苏总；中铁后续会撤场，不过跟物业的关系还是蛮好的，能在参会中看得出来；现任对接人如果还在职的情况下尽量多认识相关的决策人；	2025-10-09 01:31:25.342545	20	t
1609	2025-10-09	\N	194	817	配合集成商未中标，五家排第三，正在了解中标公司	2025-10-09 02:56:45.294848	36	t
1610	2025-10-09	833	626	\N	客户暂定下周三拜访，周二再跟客户确定下；	2025-10-09 06:07:33.928139	20	t
1611	2025-10-09	796	590	\N	询问客户国庆期间的活动是否正常，对接人表示国庆活动期间对讲机出现串台的情况，下周需要去看一下；	2025-10-09 06:11:54.449034	20	t
1612	2025-10-09	\N	91	781	上海达尔因通信设备有限公司配合投标，目前中邮建技术有限公司预中标，后续分销淳泊继续跟进。	2025-10-09 06:26:03.465851	16	t
1613	2025-10-09	680	477	\N	客户定下周二去谈具体的细节；	2025-10-09 06:29:57.294667	20	t
1614	2025-10-09	857	623	\N	据淳泊的讲，这家客户使用的是摩托罗拉的系统，之前咨询过维修；加了客户微信聊天，客户住陆家嘴的，不定时会去嘉定，下周再问客户时间；	2025-10-09 06:36:34.86707	20	t
1615	2025-10-09	849	638	823	配合合作伙伴完成初步清单及方案	2025-10-09 06:46:30.701746	16	t
1617	2025-10-09	857	623	\N	这家客户现在变动比较大，物业也即将撤场，目前是云思在管着，约了下周去看一下现场；	2025-10-09 08:40:33.621019	20	t
1618	2025-10-10	795	556	\N	跟物业老大约了下下周去拜访，银江这里同步催进度；届时一起把商讨好的报价拿去跟甲方商谈；	2025-10-10 07:35:27.225908	20	t
1619	2025-10-11	425	435	808	科思创3个负责人区域故障排查\r\n1、吴天杰区域B158，节前已排查完成，现场信号修复\r\n2、黄代梅区域D391 /D202 /D191：安排10-13日现场检测故障\r\n2、王金元区域，安排10-14现场检测故障	2025-10-11 06:46:45.664956	2	t
1620	2025-10-11	148	458	826	客户确认12套设备，安排合同签订。	2025-10-11 06:54:02.989842	2	t
1621	2025-10-11	859	644	\N	和张琛沟通了目前他们总队关于消防业务这块的想法。今年消防内部的的事情比较多，没有时间关心业务口块，目前的消防通信系统这块交给他负责，但他今年一直在外面出差。有事情时还是尽量找朱鸣君帮忙。详细介绍了浦东机场四期的消防对讲系统的情况以及我们的想法，建议我们可以尝试说服业主给他们和浦东支队发联系单，进行一次会议沟通。	2025-10-11 08:26:34.385011	13	t
1622	2025-10-12	860	645	\N	孙总从麦驰出来后，重订组建团队负责深圳瑞迪兴设计院的设计业务，聚集于企业总部大楼和产业园项目。深圳中集总部他们刚中了设计标，业主招采收集智能化品牌，对讲系统推荐了相关品牌给到孙总，后续设计可深度参与，有相关对接人后安排深圳销售跟进； 孙总他们在参与深铁置业集团的弱电标准的编写，和孙总沟通好，我们可以参与，加一些我们的产品元素进去	2025-10-12 01:29:26.542756	13	t
1623	2025-10-12	182	350	307	和陈工经及王总沟通项目的最新情况，项目已按我们提交的方案和要求提给代甲方，那边还没有反馈，王总给了现场代甲方的负责人见锟，可以尝试约见，推动一下	2025-10-12 01:32:19.983164	13	t
1624	2025-10-11	833	626	\N	通过对接人找到了现在工程部的负责人刘总，这个人是从项目那会就在职的，年龄比较大；也表示，之前使用的科立讯也是寿命到期了需要更换，具体数量需要根据我们的报价还有客户上报到业主方看；当场推荐了我们自己的对讲机，今天内部讨论下，确定是否能兼容，后续再跟客户报价；	2025-10-13 01:19:58.861918	20	t
782	2025-05-30	696	11	529	代理商已在和相关中标集成商对接	2025-05-30 02:02:21.38321	16	t
1159	2025-08-07	702	347	107	和尤总沟通合肥机场二期新建项目和总包以及业主沟通的情况，上次核价后给到京杭安一直没有反馈，业主反馈项目要延期的2027年，最近京杭安那没有动静	2025-08-07 07:17:49.279489	13	t
1160	2025-08-07	\N	347	99	总包通知机场业主突然要取消此部分无线对讲机系统，理由是资金吃紧，物流中心反应他们目前通信还好，大部区域可以正常通信；尤总和总包一起和业主物流中心的负责人沟通交流后，说明利弊，业主决定上会沟通是否保留对讲机系统	2025-08-07 07:23:53.153507	13	t
890	2025-06-19	702	347	99	民航电子已中标，协调代理商和刘威配合总包深化设计，现在急封板的区域供货的问题，已协调代理商配合解决	2025-06-19 02:14:04.298411	13	t
926	2025-06-25	702	347	99	深化方案已完成提交给总包进行核对，产品样品已送到客户那边了	2025-06-25 03:55:44.304267	13	t
992	2025-07-05	702	347	107	和尤总沟通好策略，尤总调整好价格给到京杭安。京航安要求你和源产品控制在200万内，和尤总商定先按280万报，京航安愿意谈，就约其大领导一起北京或现场商谈。	2025-07-05 08:46:15.072141	13	t
1216	2025-08-11	702	347	694	采用中策大数据，查找项目业主方负责人及联系方式，与项目跟进代理商沟通信息。	2025-08-18 01:05:53.020077	16	t
1345	2025-08-29	702	347	99	合肥机场配套用房经过沟通和交流，业主和总包同同意先将末端的天线和耦合器安装了，项目完工后，如果信号不好，再装光端机，若信号还可以，就不再安装光端机了。已和合肥尤总商量，这个配套用房量比较小，先按45折采购，后面航站楼项目谈下来，再给他申请折扣支持，尤总已按45折将天线和器件向我司下单	2025-08-29 03:04:39.684366	13	t
1142	2025-07-31	\N	109	205	宋洋洋介绍，由于建设进度较慢，今年内智能化来不及招标，目前在跟业主方对接，品牌入围问题不大。	2025-08-03 16:26:21.354987	17	t
1141	2025-07-31	\N	109	205	宋洋洋介绍，由于建设进度较慢，今年不会招标，目前在跟业主方对接，品牌入围问题不大。	2025-08-03 16:24:47.484467	17	t
1155	2025-07-31	\N	109	205	宋洋洋介绍，本项目目前对接上业主，品牌植入没有问题，今年来不及招标，工程进度较慢。	2025-08-05 01:58:48.683932	17	t
1604	2025-09-30	\N	341	532	国庆后联系，谈具体采购清单	2025-09-30 02:59:52.248235	25	t
1630	2025-10-17	\N	341	532	联系张总了解到他们已经进场开始布线	2025-10-17 11:02:18.463464	25	t
1302	2025-08-24	699	109	731	品牌：和源、洪昇、科立讯。集成商：广州长辉信息采购朱文鹃介绍，目前智能化定向邀标，他们跟业主方保持有合作。宋洋洋介绍，品牌是他做的植入，希望我们能在价格上给到支持。\r\n下周一找集成商和宋洋洋确认，宋洋洋如果没有使用我方品牌投标，我会让宇洪或者我直接找集成商参与报价。\r\n	2025-08-24 15:53:19.92105	17	t
911	2025-06-19	695	319	623	配合代理商提供资质案例证明给到业主，目前方案和整体预算基本确认下来，安排航博后续跟进商务价格和后面的采购流程，搞定关键人。	2025-06-20 05:25:08.955111	15	t
1501	2025-09-09	695	319	559	拜访省院黄震对方品牌推荐给了三局，通过设计院找到业主信息，下周安排代理商李总一同拜访。项目预计分为5个标段，三局为机电大总包。	2025-09-12 05:18:02.601813	15	t
1532	2025-09-16	695	319	559	青山湖业主沟通会客厅项目预计10-11月份左右公开招标，目前品牌已经推荐上去三个品牌，等预算确认下来复核品牌情况。	2025-09-19 03:35:35.103668	15	t
1592	2025-09-28	695	319	622	李波反馈项目后面品牌无要求，价格竞争较低，客户选用了其他品牌。	2025-09-28 03:27:08.965763	15	t
805	2025-06-03	693	341	606	和邹娟沟通项目具体情况，指导其配合总包策略	2025-06-03 10:22:57.153676	13	t
947	2025-06-25	693	341	440	业主没有钱，取消专网，采用公网的方式	2025-06-25 09:23:39.856236	13	t
860	2025-06-12	693	341	618	集成商中标，之前是其他家的产品，现在福淳在和客户沟通，推动换成我们的产品，配合邹娟提供相关所需要证明文件	2025-06-12 02:31:55.613266	13	t
1060	2025-07-18	693	341	164	总包和业主在商定认价，目前还没有确定，项目有些拖延	2025-07-18 04:43:00.264918	13	t
1422	2025-09-05	\N	341	606	总包目前还没定是分包还是自己做，保持联系	2025-09-05 05:05:43.022213	25	t
1423	2025-09-05	\N	341	606	总包目前还没定是分包还是自己做，保持联系	2025-09-05 05:05:44.287577	25	t
1239	2025-08-18	693	341	613	业主那边这个系统的预算太低，无法执行，取消了无线对讲机系统	2025-08-18 06:00:55.711085	13	t
1428	2025-09-05	\N	341	532	在跟总包协调，预估9月底开始进场	2025-09-05 05:24:45.230806	25	t
1429	2025-09-05	\N	341	532	在跟总包协调，预估9月底开始进场	2025-09-05 05:24:46.53547	25	t
281	2025-05-09	438	423	\N	与业主方详细沟通了2025年F1世界方程式锦标赛产品采购和赛事通信保障事宜，由于本次赛事业主方主体由赛车场转变为赛事公司，所以在本次大赛的产品采购和前后三场赛事的通信保障由赛车场业主进行先背书先执行然后再签订相关合约，与业主方加快产品采购和赛事保障签订的流程，尽快在项目执行后完成签约收款的事宜；	2025-05-09 00:00:00	7	t
287	2025-05-09	438	423	\N	与业主方2025年F1国际方程式锦标赛负责人沟通确认本次对讲机采购的现场工作安排事宜，现场人员通信保障安排事宜，下周的赛前赛中赛后的现场工作事宜，由于对讲机采购合约后置提供确认材料给甲方以便尽快推进合约签订付款事宜；	2025-05-09 00:00:00	7	t
292	2025-05-09	438	423	\N	与业主方沟通商榷，由于业主方在2025年一级方程式国际锦标赛前无法提供正式的对讲机采购合同，业主方提供采购需求单/指定采购邮件给和源，和源在赛前提供对讲机产品；	2025-05-09 00:00:00	7	t
301	2025-05-09	438	423	\N	今日与业主方沟通确认60套SL2M的对讲机采购取消审价公司审价的方式，改为采用三方比价的方式，安排商务重新报价给业主，这样能够加快合约流程的速度，争取在2025年F1方程式锦标赛前完成合约签订；	2025-05-09 00:00:00	7	t
310	2025-05-09	438	423	\N	2月10日与业主方沟通赛车场2025F1国际方程式锦标赛对讲机采购事宜；	2025-05-09 00:00:00	7	t
311	2025-05-09	437	423	\N	2025年2月13日与业主方经办人沟通确认合约采购的招标模式，安排报价及审价事宜；	2025-05-09 00:00:00	7	t
901	2025-06-19	438	423	\N	与业主沟通2025年F1方程式锦标赛无线对讲系统终端采购合约赛事公司第三方审价公司事宜，并在赛事公司已经将申报价格提交给审价公司后，安排商务人员与审价公司取得联系，与审价公司沟通购买的产品硬件软件服务的组成，并报价给审价公司；	2025-06-20 02:18:38.528506	7	t
1193	2025-08-13	438	423	\N	与公司技术部门负责人赵祎博一起至上海国际赛车场与业主方弱电负责人沟通如何解决在今年赛事中出现的短暂对讲机无法按下的故障现象的技术方案，通过对现象的判断方案的解读，决定按照第一方案8月的月度系统巡查，把主系统和备用系统的一号信道机进行呼唤，并且在九月的赛事中对系统是否会再出现这个现象进行验证，如果现象是由智能信道共享软件引起我们再确认第二方案卸除智能信道共享软件功能的执行，目前第二方案会因为卸除智能信道共享会影响系统录音功能无法执行；	2025-08-13 05:34:59.785442	7	t
1478	2025-09-09	438	423	\N	与久事赛事负责人沟通赛车场无线对讲系统智能信道共享功能卸用对于系统稳定的优点 并且讨论如何在常规系统下主备系统的切换，后续需将此想法落到纸面方案 业主方将进行内部讨论；	2025-09-12 01:37:55.801348	7	t
1626	2025-10-14	684	477	\N	跟客户决策人谈判，客户部对于2万的价格是满意的，不过需要增加以下部分才能上报给采购； 后续进行签合同；\r\n1.我们2万的人工包含哪部分？\r\n2.维修费用另外做个附件。\r\n3.人员多久到场？\r\n4.备品备件，需要另外作为附件附在后面；\r\n时间节点：本周末前给到客户，客户内部流程本月底前完成；	2025-10-16 03:12:58.374146	20	t
1627	2025-10-17	\N	264	638	与采购沟通，维保及备品件将要发包询价。	2025-10-17 02:59:51.147381	2	t
1628	2025-10-16	425	435	829	新做的(D191 D202)这2个区域室内无信号覆盖，现场场强测试，室内信号弱，现提出室内做信号覆盖。	2025-10-17 03:04:07.518016	2	t
1631	2025-10-17	\N	341	606	10月底11月初出最终清单和方案	2025-10-17 11:03:46.727619	25	t
1632	2025-10-17	\N	340	612	分包还没定标	2025-10-17 11:04:40.812914	25	t
1633	2025-10-18	739	411	667	配合铁二院刘工出针对航站楼区域进行布点，和摩托罗拉林峰沟通他们跟进此项目的情况，商讨合作方案。原系统的摩托罗拉的TETRA系统	2025-10-18 06:44:27.853582	13	t
1634	2025-10-18	237	392	821	和福淳核对项目清单，沟通项目批价问题，确定清单，走批价流程	2025-10-18 07:22:13.465712	13	t
1635	2025-10-14	\N	139	25	集成商技术部经理何宇红介绍，本系统由于投标成本（27万），与招标参数成本（64.6万）相差较大，本系统尚未签约，还在跟业主沟通是否能调整成本。\r\n韦祖伟跟现场业主工程部了解到，对讲系统尚未签约，他这边还不能报价。\r\n	2025-10-19 15:33:02.668369	17	t
1636	2025-10-17	\N	563	165	集成商城信项目部曾经理，李工表示，由于对馈电方案了解不深，希望我方下周组织线上技术交流，重点介绍馈电方案及相关产品原理，为接下来项目安装做基础，后续跟业主好做汇报表现的更专业，以及今后他们公司有自己控的项目，可以把我方系统作为控标系统。曾、李经理介绍希望我方能在原有报价基础上给予一定的价格支持，并且配合深化系统。\r\n采购林经理催促我方能尽快给予价格支持，根据现场进度（现场看大多在正负零，有一栋副楼建到4层）项目需要2026年后签采购合同，2027年或2028年竣工。\r\n丁杰答应跟业主方沟通，业主戴总能否在他这个环节守住技术变更，最晚23号给予答复。\r\n	2025-10-19 15:34:22.587777	17	t
1637	2025-10-17	\N	563	165	集成商城信项目部曾经理，李工表示，由于对馈电方案了解不深，希望我方下周组织线上技术交流，重点介绍馈电方案及相关产品原理，为接下来项目安装做基础，后续跟业主好做汇报表现的更专业，以及今后他们公司有自己控的项目，可以把我方系统作为控标系统。曾、李经理介绍希望我方能在原有报价基础上给予一定的价格支持，并且配合深化系统。\r\n采购林经理催促我方能尽快给予价格支持，根据现场进度（现场看大多在正负零，有一栋副楼建到4层）项目需要2026年后签采购合同，2027年或2028年竣工。\r\n丁杰答应跟业主方沟通，业主戴总能否在他这个环节守住技术变更，最晚23号给予答复。\r\n	2025-10-19 15:34:49.422504	17	t
1638	2025-10-16	\N	138	218	顾问公司柏诚智能化庄工，上次业主方要求推荐了品牌，已推荐了我方品牌，终端：和源、摩托罗拉、建伍、海能达。天馈：和源、信元、瀚网、英智源。考虑到跟设计院方案需要保持一致，并且业主方也认同我司的方案，答应后续招标参数由我方配合编写。	2025-10-19 15:48:55.382696	17	t
1639	2025-10-15	\N	\N	832	深圳建筑设计院智能化刘汉伟介绍，涉及到建设多个新站点，本项目跟西丽综合交通枢纽工程同属于中铁四院设计，约好下周一起拜访中铁四院，建议提前准备铁路站点的相关案例。	2025-10-19 15:54:18.910264	17	t
1640	2025-10-17	\N	497	90	南区统计已有6家集成商投标询价：深圳金证、中建电子、深圳智宇、深圳城信、广州韩电智能、履安科技。	2025-10-19 16:08:22.897639	17	t
1641	2025-10-17	\N	148	7	甲方不同意瀚网回复的条件——“乙方发货前办理9个月银行承兑”，并要求瀚网尽快出示弃标函。\r\n瀚网以本次集采尚未供货，没有形成交易，所签协议不能生效。	2025-10-19 16:09:34.73817	17	t
1642	2025-10-13	762	565	210	通过与李伟、渠道分销邹飞及合作伙伴祁桢沟通，了解南大104-02地块欣轲启动商务签约流程，与祁桢、邹飞确认此项目合作模式，一旦商务合同确认，发起渠道批价。计划本周跟进了解商务签约流程进度情况，尽可能在本月完成渠道批价	2025-10-20 00:29:49.272022	14	t
1643	2025-10-13	500	282	24	与邹飞沟通，了解到目前正式系统由于存在部分问题还在拉扯。按他预估商务会在11月份落实，他与王亮已经提前布局，希望我们原厂及合作品牌商接到询价后给予价格保护。\r\n与梁晓君沟通，了解到目前他们与甲方浦开有关合同签订还在流程中，按此预估差不多到11月份能够完成，等合同签订后他们才会发起下包流程，因此预计顺利的话尽可能在今年底发起并完成渠道批价	2025-10-20 00:35:30.750667	14	t
1644	2025-10-13	862	484	516	项目配合博电采购陈娴静复核清单报价，经沟通了解，主要是为配合销售孙涛了解他们智能化分包成本，从而便于他们与上安洽谈价格。但与梁晓君沟通，确认他们已经中标，目前由于造价公司有关清单价格还没核对好，所以还没正式发中标通知书。待造价公司核对确认好价格后由上安盖章，并再反馈给到造价公司后才会正式签订合同。后续计划安排渠道跟进商务报价反馈，推进项目深化方案配套及确认，复核项目实施计划	2025-10-20 00:45:48.140582	14	t
1645	2025-10-16	682	497	517	渠道李冬反馈华虹智联采购周心一回复有关商务合同迟迟审批没有通过的主要原因在于项目部吴昊在审批时留言内容为考虑资金拖欠导致项目配套服务不及时的风险，让他们彭总拒批。目前按与周心一沟通后的结果，针对当时招标询价另外两家给予二次报价机会，让我们原厂保护好出货渠道，重新提交流程看审批情况	2025-10-20 00:51:10.443003	14	t
1646	2025-10-13	782	553	687	了解到土建还未完成，项目整体进度偏慢，目前他们人员还没正式进场，只是在配合用户复核系统深化方案，预计项目正式启动商务环节至少在明年	2025-10-20 00:54:33.284187	14	t
1647	2025-10-13	681	215	32	与上安沟通了解，目前他们与四建安装由于价格问题还在沟通协商过程中，所以合同迟迟未有签订，不过应该谈的差不多了。现场方面他们还未有正式进场，有关方案提交给到华东院，待黄辰贇审批回复。计划跟进上安、华东院先确认深化方案审批情况，在根据项目项目情况，确保品牌及方案锁定同时推进采购流程	2025-10-20 01:05:34.890117	14	t
1648	2025-10-13	784	579	80	与海峡创新刘潇沟通了解有关深化方案与业主、设计有过沟通，还在确认过程中，后续会有回复意见，大致意思以满足功能要求为主。目前地下室桥架仅做了样板区，地面部分还在做管线桥架，预计11月份桥架能够完成。另外由于精装还未进场，所以前端点位还无法安装，需要与精装先确认。现场计划等桥架完成后就会启动馈线铺设，按此进度预计在11月底12月	2025-10-20 01:14:22.790454	14	t
1649	2025-10-20	682	497	801	渠道配合首安深化方案配套，提供系统品牌材料。拜访刘天瑞，初步沟通，了解到他们中标价格偏低，近期项目现场一直要求他们汇报各子系统品牌，与业主确认所选材料，刘天瑞给了商务指导价格，希望我们控制在100万内，因为这样便于后续走流程。目前根据深化方案后统计的初步清单报价远远高于首安给予的指导价格，针对这部分计划跟进业主，能否通过与业主合作来锁定品牌，确保我们和首安的业务合作	2025-10-20 01:20:12.397843	14	t
1650	2025-10-20	425	435	829	与客户沟通需要2个建筑的平面图纸，让技术进行方案设计审核及修改。	2025-10-20 03:14:28.028964	2	t
1651	2025-10-20	\N	215	651	该项目与上安华南分公司钟锐江沟通，了解到中标单位中建四局，没有直接对接人	2025-10-20 06:30:37.488698	14	t
1652	2025-10-20	\N	\N	528	与城建院卢洪祥沟通，了解到目前在整个招标设计增加品牌和型号，业主未必同意的点在于项目招标会有外部审核，怕招到投诉，所以现阶段只能通过技术进行控标，虽然他已和上电科负责市政部门的彭总打过招呼，但为了以防万一，还是要时刻保持警惕和跟进	2025-10-20 07:40:09.00074	14	t
1654	2025-10-20	\N	\N	11	该项目张国栋反馈该项目众频中标，因价格因素，且没有品牌限定，选用沅抗品牌	2025-10-20 08:55:28.903454	14	t
1655	2025-10-20	\N	232	45	渠道反馈，客户未中标，中标单位信息不详	2025-10-20 08:58:51.41571	14	t
1656	2025-10-22	425	435	829	新做的方案发给用户，并澄清一些现场问题。	2025-10-22 02:06:35.794713	2	t
1657	2025-10-21	\N	264	638	完成线上维保及备品件报价。	2025-10-22 02:07:36.192924	2	t
1658	2025-10-22	\N	\N	91	客户订单确认，已下单，CRM合同建立	2025-10-22 02:10:56.868264	2	t
1659	2025-10-21	457	470	94	订单确认，已下单，CRM建立合同	2025-10-22 02:23:31.250215	2	t
1660	2025-10-22	119	435	839	客户本月再增加17套对讲机采购，确认订单。	2025-10-22 03:39:20.832504	2	t
1661	2025-10-23	777	576	711	上门拜访，提交产品资料，沟通项目现状。	2025-10-23 05:20:33.808446	34	t
1662	2025-10-24	\N	\N	180	目前接到通知配合智能化单位已中标	2025-10-24 06:55:04.455602	23	t
1663	2025-10-24	\N	\N	824	已配合智能化单位投标	2025-10-24 06:56:51.716861	23	t
1664	2025-10-24	714	359	607	设计变更，增补流程已通过，收到甲方的通知单，给到四川中航建，沟通合同增补协议	2025-10-24 07:15:22.295065	13	t
1665	2025-10-24	235	390	640	和财务沟通合同增补协议的内容，整理后给到中航建，待中航建审核通过后，进行签约	2025-10-24 07:27:11.149953	13	t
1666	2025-10-24	\N	\N	801	和杨俊杰一起约了集成商负责人刘总见面沟通，集成商中标价格倒挂，苏州中瀚也报了价格，就价格而言，我们优势不大，技术方面一直再配合，下周约现场项目经理，力求从方案上突破。	2025-10-24 08:25:01.067967	3	t
1667	2025-10-21	\N	148	7	甲方要求瀚网尽快出示弃标函。瀚网不愿配合出示弃标函。\r\n虽然集采整体利润较薄，裴小印考虑能建立长期合作，愿意来承接本次集采，已跟裴小印一同拜访采购总监，采购总监同意宇洪作为后续的供应商。\r\n由于没有瀚网的弃标函，甲方审计通过新供应商变更提议较为困难。\r\n催促瀚网尽快回复邮件，以邮件形式说明合作无法开展，让甲方审计以此评估。\r\n	2025-10-26 14:26:29.138284	17	t
1668	2025-10-23	\N	563	165	组织集成商城信项目部曾经理、李工、采购等人技术交流，经过本次交流，项目上的人员对我方案和产品较为认可，缓和了我方大幅降价的要求。由于本月需要提报品牌，采购希望我方能给个优惠价格配合。	2025-10-26 14:46:47.384518	17	t
1669	2025-10-24	\N	546	679	集成商项目经理张总介绍，由于业主资金问题，项目进度还要往后延迟，最快11-12月才能进行后续设备的采购安装。	2025-10-26 14:47:50.925407	17	t
1670	2025-10-22	\N	142	55	招标信息已挂网， 11月7日投标截止，11月20日左右公布中标结果。肖总已同步潜在中标单位：电信工程，华海（华为系）。目前已经跟两家投标负责人已经联系，并且对方同意我方配合投标，约好下周拜访，深入了解对方的应标策略。\r\n已询价集成商：麦驰物联、万睿、达实、中建电子、范进配合的集成商。\r\n	2025-10-26 14:49:37.019359	17	t
1671	2025-10-27	\N	\N	842	现场沟通厂区总经理，要求将工段覆盖的方案升级到整个厂区覆盖，30个频道，整个区域赵祎博做了测试，返回制定报价预算和方案	2025-10-27 00:34:54.794171	6	t
1672	2025-10-27	868	659	102	该项目与渠道确认，现场实施进度推迟，预计前端天馈设备实施要到11月中旬，商务方面采购还未正式与渠道洽谈。但考虑本项目品牌已经提交申报，并审批确认，且集成商铭鹭与渠道有着良好合作关系，所以提前发起批价确认	2025-10-27 03:00:21.469005	14	t
1673	2025-10-24	400	325	840	配合中国联合设计，设计集成商微风在后面操刀，客户找到代理商李波配合设计，后面参与施工标。计划植入和源控标点。	2025-10-27 03:37:22.916023	15	t
1674	2025-10-27	312	285	841	配合德恳包工设计植入和源品牌，预计年初招标，项目后面招标是他们业主自己内部在操作，不对外招标。	2025-10-27 03:38:48.384083	15	t
1675	2025-10-22	400	325	833	他们前期介入设计方案，找到我们配合设计植入控标点参数，帮助他们后面技术标拿分，然后后面落地按照实际优化来做。	2025-10-27 03:41:49.489958	15	t
1676	2025-10-23	778	30	65	经与集成商采购沟通，目前项目采购品牌已确定摩托罗拉+中瀚。	2025-10-27 04:30:23.514997	16	t
1677	2025-10-24	828	30	65	经与项目现场项目经理确认，无线对讲品牌供应商已确定，为苏州中瀚。	2025-10-27 04:31:53.851299	16	t
1678	2025-10-24	85	64	146	经沟通本标段需要与主系统品牌保持一致。	2025-10-27 04:33:46.855302	16	t
1679	2025-10-27	93	81	549	经沟通本标段需要主系统品牌保持一致	2025-10-27 04:35:38.690047	16	t
1680	2025-10-27	\N	488	553	经与该标段项目经理（张文晶）联系，项目品牌需与主系统标段品牌保持一致。	2025-10-27 04:39:11.571743	16	t
1681	2025-10-21	77	21	691	配合集成商南京聚立投标	2025-10-27 04:40:51.264135	16	t
1682	2025-10-22	77	21	691	配合中江智建（幕墙）公司投标报价	2025-10-27 04:42:04.374213	16	t
1683	2025-10-23	\N	\N	691	配合中建电子投标报价	2025-10-27 04:45:26.425184	16	t
1684	2025-10-23	77	21	691	配合冠林电子投标报价	2025-10-27 04:46:01.120626	16	t
1685	2025-10-23	\N	21	691	配合江苏三棱电子投标报价	2025-10-27 04:46:35.070927	16	t
1686	2025-10-27	77	21	691	配合泽利投标报价	2025-10-27 04:47:14.385552	16	t
1687	2025-10-27	\N	\N	691	配合江苏德安投标报价	2025-10-27 04:47:52.170384	16	t
1688	2025-10-24	77	21	843	代理商配合集成商设计系统方案	2025-10-27 04:51:46.657051	16	t
1689	2025-10-27	762	565	210	该项目与渠道确认，现场实施预计前端天馈设备实施要到11月中下旬，商务方面采购起草合同流程。考虑本项目与集成商锁定系统品牌，所以提前发起批价确认	2025-10-27 04:54:47.380635	14	t
1690	2025-10-27	500	282	835	该项目与邹飞沟通了解，项目为大展李发超报备，反馈配合集成商中标，现阶段在提供样品机资料进行报验，具体情况还需进一步了解	2025-10-27 05:50:17.668178	14	t
1691	2025-10-28	551	226	24	与壹杰采购徐骏沟通得到反馈项目已经中标，但合同还未签订，深化方案之前有过提交，在做优化存在难度，具体还需等到我们系统启动前再进一步沟通，有关报价及采购期望偏差较大如何协调，确保商务能够有效落地。现场预计11月底启动天馈实施	2025-10-28 01:59:55.754151	14	t
1692	2025-10-28	682	497	108	与渠道李冬沟通，了解到他与奔逸徐良建在沟通推进商务合同签订，预计11月份可以完成落地	2025-10-28 02:21:56.965693	14	t
1693	2025-10-28	681	215	32	配合上安蒯乃骏提供品牌材料报验，按蒯乃骏所诉本次为正式申报确认系统品牌	2025-10-28 02:39:59.800452	14	t
1694	2025-10-28	789	584	801	与首安项目负责人刘天瑞沟通，侧边了解到苏州中瀚也有找到他们，有关价格及品牌资料给到首安，但首安关于品牌资料通过业主关系得知还未提交	2025-10-28 02:52:57.539713	14	t
1695	2025-10-28	728	241	32	张鸿近期回北京考试，按他反馈待他回上海后计划组织设计院、业主复核系统方案，以此来定方案和品牌。同时商务方面计划直接写定品牌，从而他们内部招标时以价格谈判方式，来锁定合作	2025-10-28 03:12:45.342162	14	t
1696	2025-10-28	873	190	66	了解有关方案和品牌审批都已通过，但现场进度缓慢，目前至多做4-8层前端天馈实施工作，B栋建筑还未确认，所以智能化也没启动，整体竣工为明年10月底，推进他提前发起采购流程，等待通知	2025-10-28 03:41:15.670311	14	t
1697	2025-10-28	\N	147	646	该项目与万睿范由闲沟通，了解为二期需接入原先一期，目前他们在做管线预埋，计划春节前部分区域天馈设备启动实施，商务由华东区刘兴鹏负责	2025-10-28 04:07:57.025653	14	t
1698	2025-10-28	867	215	593	渠道反馈目前合同还在签订过程中，主要和中建八局商谈总包管理费。项目计划明年春节前完成大部分天馈设备实施，现阶段配合项目方案深化	2025-10-28 05:36:52.915634	14	t
1699	2025-10-28	115	435	829	进行议价。\r\nD514区域检测后进行方案设计。	2025-10-28 08:19:24.518795	2	t
1700	2025-10-28	\N	\N	108	上安与下包华融合同签订，项目目前深化方案有过确认，品牌已经提交送审，目前在推进商务合约签订，预计11月能够落地	2025-10-28 09:04:43.023089	36	t
1701	2025-10-28	\N	\N	801	配合首安技术曹晓芸方案进行深化，等首安和业主，设计确认，另外按项目要求需要首安提供系统品牌材料，但通过杨俊杰了解业主还没拿到相关资料。估计按方案深化后我们报价远超首安预期的100万以内，且之前首安沟通过程中得知苏州中瀚也找到他们，估计价格因素，还需进一步跟进	2025-10-28 09:09:49.725768	36	t
1703	2025-10-28	\N	\N	80	与海峡创新刘潇沟通，了解有关方案基本确认，根据现有方案提供深化清单，等他确认后就会开始发起采购流程。项目现场桥架除一层及地下室以外大部分已经完成，精装计划也在11月份进场，按他计划明年春节前把前端天馈设备都安装完成。预计商务流程11-12月能够签订。	2025-10-28 09:14:52.555375	36	t
1704	2025-10-29	892	678	\N	和陈经理沟通国外项目的情况，提供相关产品的报价	2025-10-29 13:42:44.628145	13	t
1705	2025-10-29	171	337	656	SABIC项目总包招标结果还没有确定，待总包确定后再约业主进一步沟通	2025-10-29 14:51:00.604395	13	t
1706	2025-10-31	403	328	562	目前代理商深化配合完成，现场预计12月左右进场穿线，计划推动采购合约流程。	2025-10-31 02:08:37.27822	15	t
1707	2025-10-30	380	314	149	据代理商反馈目前深化方案已经确认，现场预计12月左右进场穿线，品牌资料已经报验。后续安排代理商推动合同流程尽快落地批价。	2025-10-31 02:11:11.60707	15	t
1708	2025-10-29	400	325	840	目前方案设计预算给到对方，3套系统馈电产品。后续跟进方案预算有没有问题，品牌是否由对方来推荐，打听业主信息。	2025-10-31 02:13:23.652919	15	t
1709	2025-10-31	500	282	90	邹飞配合了中建电子进行投标	2025-10-31 07:51:48.021348	13	t
1710	2025-10-28	632	138	19	深圳建筑设计院总院刘汉伟介绍，中铁四局对接的人不是一直在深圳，之前因为项目启动来这边办公一段时间，他们总部在武汉，根据全国项目需要，他们会不定期的出差，等下回项目需要对方过来深圳项目上，才能过去拜访。	2025-11-02 15:00:25.440739	17	t
1711	2025-10-29	\N	142	55	拜访华海智汇销售经理催鑫，催经理告知我方报价过高（174万），无线对讲预算200万。本次投标竞争会比较激烈，大家基本都是按照招标预算金额下浮20-30个点去投，中标后一定会根据实际情况跟我方谈价格。\r\n拜访电信工程龙岗分公司销售经理刘总，刘总跟华海的情况一样，对我方价格表示过高，也是根据招标预算金额去做下浮，中标后再跟我方协商价格，既然我方的方案和参数锁死，后续坚定选择我方配合。\r\n	2025-11-02 15:01:40.235626	17	t
1712	2025-10-30	\N	381	594	达实项目经理陈总介绍，目前刚进场，按照业主方原来的计划明年6月竣工，但实际肯定会延误，无线对讲系统最快也是年前做线缆采购计划，设备要到明年才能安排。	2025-11-02 15:05:12.916108	17	t
1713	2025-10-31	\N	495	595	配合投标集成商浙江州之宇胡工介绍，本项目还没有投标结果，参与投标的集成商较多，竞争比较激烈，一直没有定下来。	2025-11-02 15:06:01.885187	17	t
1714	2025-10-31	900	582	847	与柏诚一组团队聚餐，了解到他们新增此业务，目前在做方案汇报，项目设计由中衡王啸负责，现阶段根据中衡出的方案设计做一版初步概算。计划通过WSP了解设计，业主具体负责人，衔接业务配套设计	2025-11-03 01:01:29.068973	14	t
1715	2025-10-31	787	582	64	与WSP一组成员聚餐，了解到此项目智能化进度还早，近期没有太多讯息	2025-11-03 01:06:03.055074	14	t
1716	2025-10-23	542	219	160	拜访王佳斌，了解到此业务情况不是特别了解，他们完成设计后就没有在进一步有过对接	2025-11-03 01:12:39.948387	14	t
1717	2025-10-23	542	219	260	拜访王佳斌，他通过项目电气负责人了解到弱电还未招标，按电气专业负责人回复弱电不在机电包内，会单独招一个信息标，通号几率会比较大	2025-11-03 01:15:55.431894	14	t
1718	2025-11-03	542	219	\N	拜访王佳斌，了解前期业务情况，关于深圳湾超级总部基地片区市政交通基础设施项目，目前还在方案修改，他们仅负责图纸设计，招标由工务署负责	2025-11-03 01:17:16.974157	14	t
1719	2025-10-29	77	21	691	配合旭鸿科技、冠林电子两家集成商投标	2025-11-03 01:26:14.481547	16	t
1720	2025-10-30	77	21	691	配合集成商南京聚立、江苏三棱、泽利投标	2025-11-03 01:27:38.688469	16	t
1721	2025-10-30	531	214	801	与张辉团队聚餐，将海神业务与业主沟通情况回馈给到张辉，按业主意思他会让首安组织苏州中瀚做技术交流，在交流过程中由设计院提出问题后业主回应，相互配合看是否能够有机会屏蔽掉苏州中瀚	2025-11-03 01:28:17.727022	14	t
1722	2025-10-31	77	21	691	配合集成商中建电子、熊猫投标	2025-11-03 01:28:28.079824	16	t
1723	2025-10-23	902	214	\N	与张辉，葛明阳聚餐时了解到葛明阳新增两个业务，济南歌尔股份及上海中微，济南歌尔已经开始设计，但好像没有对讲机系统，需要进一步跟进确认，上海中微还在初期，后续继续跟进	2025-11-03 01:30:58.521531	14	t
1724	2025-10-31	77	21	289	配合的集成商安徽安泰科技中标，下周去安泰公司拜访。	2025-11-03 01:31:32.940181	16	t
1773	2025-11-10	920	696	33	电信中的是智能化总包，智讯智能做智能化分包。陈楚负责技术对接，张兴配合深化设计。	2025-11-10 01:56:28.619854	17	t
1822	2025-11-10	593	112	148	裴小印介绍，三局那边通知要明年才能招标。	2025-11-10 10:13:49.974651	17	t
1726	2025-10-29	572	244	\N	与江勤平聚餐，目前其主要在嘉定光通信项目上做最后收尾工作，今年新增业务机会不多，但有几个还在跟进投标，预计明年一季度会有结果，到时候中标后推进跟进。同时了解到无锡华虹计划建二期，推进后续配套设计	2025-11-03 01:36:56.798574	14	t
1727	2025-10-31	\N	686	781	目前配合的集成商中邮建常州分公司已中标该项目。	2025-11-03 01:38:00.463926	16	t
1728	2025-11-03	77	21	643	代理商敦力公司配合的宜安公司已中标。	2025-11-03 01:40:57.602107	16	t
1729	2025-10-28	77	21	105	配合科大讯飞报价	2025-11-03 01:45:34.064773	16	t
1730	2025-10-28	\N	553	105	配合北明软件投标报价	2025-11-03 01:47:19.581435	16	t
1731	2025-10-28	772	535	105	配合科大讯飞投标报价	2025-11-03 01:48:34.496504	16	t
1732	2025-10-29	508	288	105	配合济南合作伙伴给集成商瑞源控股投标报价	2025-11-03 01:52:06.345735	16	t
1733	2025-10-28	\N	\N	105	李华伟配合集成商浙大中控报价	2025-11-03 01:53:05.223549	16	t
1734	2025-11-03	77	21	105	配合集成商莱斯集团中电科28所投标报价	2025-11-03 01:54:15.868672	16	t
1735	2025-11-03	904	687	849	渠道报备，据了解中邮建中标，但智能化不会自己做，所以现阶段在对外询价分包，郡申参与，配合报价	2025-11-03 02:29:40.597049	14	t
1736	2025-10-27	241	243	\N	拜访施国平，确认上安中标电气装备园项目，另外了解到其手上还在负责上海集成电路设计产业园2b-6项目，但智能化设计具体由福祁负责，进入到招标前准备工作，计划跟进张江业主刘亚楼，推进品牌植入。另外其手上还有一个8-1项目，计划推进项目设计配套	2025-11-03 02:52:38.779954	14	t
1737	2025-11-03	287	271	850	代理商配合集成商报价预算，经过沟通品牌帮忙推荐了围标品牌上去，后续确认品牌是否采纳和招标时间	2025-11-03 03:38:20.770086	15	t
1739	2025-11-03	906	217	855	配合董飞，提供系统清单报价	2025-11-03 07:47:18.8512	14	t
1740	2025-11-03	\N	\N	565	中标单位上海九谷，业主张江国信安。项目进度缓慢，打桩阶段，智能化至少明年才进场，待进场后配合确认深化方案。	2025-11-03 08:22:53.51299	36	t
1741	2025-11-03	\N	\N	687	配合北明沈佳提供一版深化方案，目前沈佳回复项目现场进度缓慢，目前还在土建，还没有进场施工。现阶段主要是沈佳他们在与甲方汇报智能化各个系统，与业主确认。后续跟进了解项目实施进度，采购计划，确认方案情况	2025-11-03 08:25:50.574376	36	t
1742	2025-11-04	\N	689	856	上午合作伙伴茂名佳胜销售陈总去现场拉通电话会议，跟茂名热电厂技术部汇报我司的产品和和源在无线对讲通信领域的实力，目前客户初步认可我们的品牌，初步提出按4-6个信道配置，搭配20台对讲机的采购方案。	2025-11-04 09:06:42.138411	42	t
1743	2025-11-04	908	691	\N	和李冬拜访邓总，了解邓总公司的规模、业务模式和业务情况，介绍我们公司的市场、业务模式，产品优势，挖掘合作机会，了解小梅沙广场项目品牌以及投标的相关情况	2025-11-04 12:41:32.485359	13	t
1744	2025-11-04	909	692	\N	拜访肖总，了解他们近期的业务情况，以及他们与深圳乐高后勤楼部分的情况，后勤楼部分中冶给的价格和他们的报价相差太大，肖总他们放弃了，后续他们想参加乐园和酒店的智能化招标，目前还在找工作进入	2025-11-04 12:47:16.987209	13	t
1745	2025-11-05	425	435	829	D514区域方案已完成，清单报价发给用户确认。	2025-11-05 06:28:46.198878	2	t
1746	2025-11-03	131	444	695	客户确认维保订单，合同签订完成。	2025-11-05 06:32:58.726169	2	t
1747	2025-11-05	431	435	858	TDI C2生产区域出现过几次叫不通情况，与客户沟通下故障排查订单，去现场排查故障	2025-11-05 06:42:12.507507	2	t
1748	2025-11-07	\N	539	652	中通服低价中标，没有品牌要求。	2025-11-07 06:28:25.55476	17	t
1749	2025-11-07	660	171	685	产品需要从华润库内选，只用普通系统。	2025-11-07 06:36:23.974937	17	t
1750	2025-11-07	912	533	783	阎祖涵从C塔项目调到本项目，负责工程技术。	2025-11-07 06:48:06.345697	17	t
1751	2025-11-07	585	99	750	项目已中标，业主还没有确定是否建设无线对讲系统。	2025-11-07 07:05:26.341759	17	t
1752	2025-11-04	480	350	\N	与华东院建筑一所殷平等人聚餐，沟通了解近期他们配合建筑共同参与项目投标，中标上海北外滩294米超高层项目，由青山集团建设投资，另外还有上海横沔酒店。目前这两个业务刚刚中标，现阶段主要方案汇报为主，计划后续跟进了解是否由殷平负责，华东院是否为智能化专项	2025-11-08 08:34:02.073996	14	t
1753	2025-11-04	481	350	214	了解到此项目近期的确计划招标，现在在做招标前概算，业主有询价至摩托罗拉，摩托罗拉交由李冬在配合报价，有关品牌按张航所述会参考聚峰中心，也就是和源入围，与烈龙、中元竞争。张航会参与项目全过程，计划待项目招标后，透过张航了解集成商信息，给予渠道跟进	2025-11-08 08:41:20.757256	14	t
1754	2025-11-04	476	350	860	目前项目初设招标图完成，并提供概算清单，后续待精装图完成后确认是否需要调整	2025-11-08 08:43:05.878936	14	t
1755	2025-11-04	476	350	\N	与韩翌沟通，了解他们中了雅江集团业主营地，项目共计6个地块，目前他们只是拿了其中1个，为公寓楼，办公由上勘院负责设计，项目为雅江集团在西藏为雅鲁藏布江工程配套设施	2025-11-08 08:50:29.339231	14	t
1756	2025-11-04	476	350	861	该项目华东院韩翌负责智能化设计，目前项目初设招标图完成，并提供概算清单，后续待精装图完成后确认是否需要调整。另外目前有一稿品牌，和源入围，传输另外包括佰沃、德恒达，与韩翌商议尝试品牌变更	2025-11-08 08:57:13.27709	14	t
1757	2025-11-05	763	566	706	渠道报备，该项目招标，配合上电科参与项目投标报价，与上电科周闻乾沟通了解由于配合大总包一起参与，所以即使中标，明年也只是做管线预埋，实际要到2028年完工，预计设备供货在2027年	2025-11-08 09:13:01.518035	14	t
1758	2025-11-06	913	579	80	渠道反馈，海峡创新技术刘潇反馈他需要将深化方案和清单提交业主审核确认，待确认后现场项目经理才会根据现场进度提交采购计划，而业主近期忙于样板层确认，还未有到我们这个环节。而现场项目经理反馈天馈实施计划明年春节以后，今年至多做点管线预埋，要等到精装进场后根据精装的进度确认施工计划	2025-11-08 09:24:30.528745	14	t
1759	2025-11-06	914	693	516	渠道反馈，该项目与上安九分樊正刚确认他们双包签给博电，但博电内部在是否会分包还无法确定。现阶段箐峰郑峰找到我，说是我们系统直接由他来负责采购，同时与现场刘洋沟通了解桥架已全部完成，目前着急客房层64-76层需要先实施。与梁晓君确认刚发中标通知书，合同还未签订	2025-11-08 09:27:06.719735	14	t
1774	2025-11-10	609	125	43	业主最终没有采用我方配合设计院方案招标。目前达实和中建电子分别中标。达实BAH部门售前吴登峰13510282298负责技术对接。	2025-11-10 02:21:30.072134	17	t
1823	2025-11-11	\N	533	783	重复	2025-11-11 04:03:26.409641	17	t
1760	2025-11-05	570	204	\N	久钮俞春磊沟通，了解他们在参与金水湾酒店改造项目。按他所述此项目总包中标，智能化大概率交给他们来做，目前他们在复核成本，因只有询价清单，资料不齐全，所以无法判别有没有品牌限定，待他们确认参与此项目智能化后按久钮的业务流程，还需三方比价	2025-11-08 09:38:25.483727	14	t
1761	2025-11-07	\N	125	43	中建电子和达实分别中标。	2025-11-09 14:18:00.722354	17	t
1762	2025-11-05	894	563	165	陪同郭总一同拜访城信现场项目人员，现场李工介绍，项目的品牌推荐推迟到11月，原计划在10月底进行。施工图暂时还没到节点，施工图出来后会发我方配合深化。李工并且表达，采购什么价格，他们不关心，只要在施工配合上没有问题，按照他们的节奏来，他们就不会给我们找麻烦。从目前现场人员的态度来看，基本可以确定他们无法变更我们方案和参数。	2025-11-09 14:39:54.068502	17	t
1763	2025-11-04	632	138	218	柏诚智能化庄工已让我方配合图纸和方案，并让我方跟进总院进度。深圳建筑总院刘汉伟和梁工确认，无线对讲系统暂定预算200万，近期业主让他们做了一版全光图纸和方案，暂未出成本。梁工介绍，业主让他们出全光方案是想要跟之前我们配合的方案做对比，成本和功能。刘汉伟答应会在下次上会提出两套方案的成本、功能、优劣对比。	2025-11-09 14:41:37.661079	17	t
1764	2025-11-07	917	695	90	业主方电气负责人宋忠平介绍，近期已退休，如果需要到现场找童卫民。方案和参数以及品牌已定，去找业主方做工作，意义不大。\r\n下一步工作应该放在中标集成商，做好对应的公关工作。	2025-11-09 14:58:29.988535	17	t
1766	2025-11-04	\N	599	765	迈众诚肖攀介绍，他跟土建总包对后勤楼的图纸、施工方案、以及施工金额都有异议，图纸混乱，到目前还没有梳理出一个确定的方案，业主提出10万的施工费，但肖总根据工程量预估60万打底。\r\n会参与后续的核心项目智能化招标，他这边配合的合正人员已经离职。目前在找核心高层沟通合作。	2025-11-09 15:15:25.279795	17	t
1767	2025-11-06	920	696	33	目前张兴在配合分包集成商陈工做深化。	2025-11-09 15:47:36.713772	17	t
1768	2025-11-09	\N	\N	730	海南保利库内集成商肖总帮忙我方做品牌入库推荐，我方目前在准备入库所需资料。	2025-11-09 15:51:59.569305	17	t
1769	2025-11-07	921	490	580	已进场，项目在出正负零。	2025-11-09 15:57:03.485171	17	t
1770	2025-11-06	624	381	50	达实徐经理介绍，他在跟进本项目，与业主方高层关系紧密，之前成功拿下过类似项目，中标概率大。	2025-11-09 16:05:02.711024	17	t
1765	2025-11-05	\N	698	632	庄工介绍，他这边在负责智能化的设计，暂未到施工图阶段，后续让我们配合方案和品牌选择。	2025-11-09 15:04:59.886732	17	t
1775	2025-11-10	\N	381	594	售前许文相 18902437618，张兴在对接项目经理陈晓宜18188623919。当前售前介绍项目还没有开始深化。	2025-11-10 02:34:02.572653	17	t
1776	2025-11-10	593	112	72	中山大学的资金尚未到位，裴小印的项目。	2025-11-10 06:19:43.575761	17	t
1777	2025-11-10	655	166	582	三局智能中的智能化，但之前的联系人蒋创15927220726已调离项目。目前没有有效联系人。	2025-11-10 06:23:31.947475	17	t
1778	2025-11-10	119	435	863	大修前再增补35套P8668i防爆机器，前期80套机器陆续使用，发现有电池出现无法正常使用情况，与客户沟通将电池寄回更换。	2025-11-10 06:32:55.276802	2	t
1779	2025-11-10	688	496	648	代理商反馈配合客户未中标，中标单位范敬在配合。	2025-11-10 06:43:57.75218	15	t
1780	2025-11-10	425	435	864	D514区域的方案及报价给到用户，用户确认此区域的信号补盲方案，下单采购设备。	2025-11-10 06:57:02.254488	2	t
1781	2025-11-10	\N	103	678	广东省院张学强18928875787负责本项目，配合图纸和预算，当前尚在设计阶段，招标日期还不明确。	2025-11-10 07:42:14.834532	17	t
1782	2025-11-10	\N	165	619	三局智能文工17600296441介绍，项目进展较慢，还没有出正负零。智能化的施工图还没有出来。	2025-11-10 07:45:14.88743	17	t
1783	2025-11-10	607	123	283	王总介绍，他们推荐了我方品牌，目前还没确定招标日期。他们集成部门有可能会去参与投标。	2025-11-10 07:52:19.089675	17	t
1785	2025-11-10	\N	162	800	代建方中信建设余工13823665013让我方配合设计院做好无线对讲系统设计，本项目资金有限，只考虑传统对讲系统。	2025-11-10 08:09:13.743739	17	t
1786	2025-11-10	601	119	576	谌工介绍，项目总包刚进场，基础还没有做，计划28年竣工，还没有到施工图阶段。	2025-11-10 08:17:27.152428	17	t
1787	2025-11-10	602	119	647	三季度预计四季度可以配合施工图设计，目前项目推迟，最快要年后才需要我们配合。	2025-11-10 08:23:33.221211	17	t
1788	2025-11-10	848	534	633	项目因资金问题暂时搁置。	2025-11-10 08:28:26.134239	17	t
1789	2025-11-10	600	118	190	深圳特发已中标，没有品牌限定。	2025-11-10 08:31:48.389858	17	t
1790	2025-11-10	652	162	191	项目分南北片区，华艺负责北片区的设计，深圳总院负责南区设计，当前属于早期，还在做建筑设计阶段。	2025-11-10 08:36:05.846328	17	t
1791	2025-11-10	660	171	249	王院长介绍，他们没有中智能化设计标。郭总介绍，之前配合深铁置业做标准的上海设计院在做本项目智能化设计。	2025-11-10 08:40:31.963036	17	t
1792	2025-11-10	580	95	253	整个项目较大，他们只负责两栋楼的设计。智能化设计，业主会重新找一家设计院来单独做。	2025-11-10 08:42:58.914318	17	t
1793	2025-11-10	658	168	267	采购陈经理介绍，项目进度较慢，还在还在主体土建阶段，智能化还没有招标。如果到现场，可以介绍业主认识。	2025-11-10 08:46:56.000781	17	t
1794	2025-11-10	600	118	188	本项目分两家设计院设计：华南理工做核心大楼，省院负责宿舍楼等区域。\r\n目前已让我们配合根据系统图做系统架构。\r\n华南理工负责的部分进展没有那么快，目前给不了确切的参与节点。	2025-11-10 08:51:02.512373	17	t
1795	2025-11-10	591	109	583	宋洋洋跟进的项目，没有反馈进度。	2025-11-10 08:51:42.664911	17	t
1796	2025-11-10	591	109	20	宋洋洋跟进的项目，没有反馈确切进度。	2025-11-10 08:52:25.694699	17	t
1797	2025-11-10	593	112	819	裴小印介绍，当前还没有反馈中标结果。	2025-11-10 08:55:07.485353	17	t
1798	2025-11-10	943	147	161	项目推迟到11月招标，无线对讲系统按照我方品牌和参数来写，提报品牌：和源、摩托罗拉、海能达。	2025-11-10 09:02:14.320988	17	t
1799	2025-11-10	591	109	731	尚无中标结果。	2025-11-10 09:03:37.908805	17	t
1800	2025-11-10	944	128	584	集成商采购林燕娜表示，项目因资金问题进度缓慢，智能化分包当前还没有确定招标时间。\r\n宋洋洋从设计院了解到该项目，想要参与进来。	2025-11-10 09:08:29.511944	17	t
1801	2025-11-10	945	381	692	已提交我方报价配合，中标还没有公告。	2025-11-10 09:12:57.390565	17	t
1802	2025-11-10	699	109	662	宋洋洋介绍，尚无中标结果。	2025-11-10 09:14:14.986208	17	t
1803	2025-11-10	591	109	205	宋洋洋单独跟进，暂无招标具体节点日期。	2025-11-10 09:15:56.141052	17	t
1804	2025-11-10	592	111	53	曾帅介绍，广东南方通信建设中了智能化标，暂时还没有人来找配合，过段时间会让业主给联系人。	2025-11-10 09:21:23.516183	17	t
1805	2025-11-10	584	98	170	采购林经理介绍，项目因资金问题，暂无具体的招标节点。	2025-11-10 09:23:01.664972	17	t
1806	2025-11-10	946	710	235	胡总介绍，公司倾向选择本地品牌。\r\n一同裴小印拜访胡总，并且由她一直在维护。\r\n由于项目进度较慢，三局智能的文工已抽调到双碳项目支援。	2025-11-10 09:30:37.361174	17	t
1807	2025-11-10	593	112	818	裴小印介绍，截止当前还没有中标结果。	2025-11-10 09:33:24.666502	17	t
1808	2025-11-10	945	381	48	当时用了我方报价配合投标，目前没有中标结果。	2025-11-10 09:34:30.242581	17	t
1809	2025-11-10	844	141	653	目前还没有中标结果，业主给的预算太低，最后不一定再继续谈判下去。	2025-11-10 09:36:40.673595	17	t
1810	2025-11-10	585	99	574	暂无中标消息。	2025-11-10 09:41:55.188948	17	t
1812	2025-11-10	689	497	139	项目分包是中冶黄光榆13729225566，我和张兴分别对接沟通过该项目，黄较难沟通。虽然我方品牌在里面，如果到了对应节点，对方有可能会来重新沟通。	2025-11-10 09:48:46.726929	17	t
1813	2025-11-10	629	135	776	暂时没有到我方配合阶段，深化应该在年后，到时候会让商务找我们询价。	2025-11-10 09:53:41.24122	17	t
1814	2025-11-10	633	139	25	金证还没有跟业主签合同，无线对讲系统项目招标预算20多万，根据招标参数的成本要64万。\r\n已经让设计院和顾问公司配合锁住参数。\r\n韦祖伟让业主方工程部锁住参数，只等金证签约后谈价格。\r\n	2025-11-10 09:59:09.472713	17	t
1816	2025-11-10	682	497	577	万安中标没多久，还没有让配合深化，采购节点还没有确认。	2025-11-10 10:01:24.444541	17	t
1817	2025-11-06	911	611	777	霍尼韦尔介绍了集成商技术薛工。\r\n电话联系了薛工，对方比较冷漠，让后续有需求再联系我方。\r\n	2025-11-10 10:04:52.25921	17	t
1818	2025-11-10	593	112	147	销售在跟进项目，项目还存在，具体采购时间未定。	2025-11-10 10:06:11.196861	17	t
1819	2025-11-10	593	112	668	采购日期未定，清单到时会补过来。	2025-11-10 10:07:24.1399	17	t
1820	2025-11-10	716	154	617	我们的价格已经报给项目组了，目前还没有收到采购通知。	2025-11-10 10:08:51.120371	17	t
1821	2025-11-10	947	546	679	张总介绍，看本月的施工进度，如果开的话月底可以采购，不行就等下一个月，他们也想赶在年底前做进度80%结算。	2025-11-10 10:12:04.906832	17	t
1824	2025-11-11	\N	142	55	华海 催鑫15919461583；深圳电信龙岗分公司销售 18938076197 容海燕	2025-11-11 07:44:12.588791	17	t
1825	2025-11-11	689	497	170	前期张兴配合客户做的设计方案，暂无信息反馈。	2025-11-11 07:48:03.550853	17	t
1826	2025-11-11	689	497	584	张兴配合做的方案，暂无反馈。	2025-11-11 07:49:16.60396	17	t
1827	2025-11-11	943	147	161	项目由万睿蔡总工在操作。	2025-11-11 07:51:22.930855	17	t
1828	2025-11-11	602	119	47	分四个设计院进行设计：华阳、华东、浙江、北京院。智能化放在浙江院跟北京院。	2025-11-11 08:09:27.06587	17	t
1829	2025-11-11	908	691	853	李冬在配合远脉投标。	2025-11-11 08:26:58.145941	17	t
1830	2025-11-12	\N	635	408	客户中标，采购预计明年，后续和采购对接	2025-11-12 05:22:57.373872	36	t
1831	2025-11-13	425	435	829	用户订单方案，完成订单PO，安排供应链备货。	2025-11-13 01:58:01.382166	2	t
1832	2025-11-13	119	435	863	客户因大修项目需要，再增加10套对讲机，共45套。	2025-11-13 02:12:21.52118	2	t
1833	2025-11-13	134	444	859	客户订单完成签约，写频供货，安排开票。	2025-11-13 02:13:41.786848	2	t
1834	2025-11-13	431	435	858	故障排查完成，现场因单呼占用通道导致组呼不能通信，现场与客户沟通建议不要使用单呼。	2025-11-13 03:01:28.766114	2	t
1835	2025-11-10	429	435	788	现场安装调试已完成，测试信号正常，完成调试报告。	2025-11-13 03:04:04.170911	2	t
1836	2025-11-12	148	458	826	客户先支付6套设备费用，安排6套设备备货。	2025-11-13 03:05:38.017033	2	t
1837	2025-11-13	421	445	\N	与客户沟通安排11-17下半年度巡检。	2025-11-13 03:10:33.046915	2	t
1838	2025-11-13	132	444	695	第四季度巡检与客户确认安排11-17日。	2025-11-13 03:11:41.561961	2	t
1839	2025-11-13	\N	711	649	通过业主了解到设计院相关负责人，近期开始方案涉及，对接上对方进行方案配合，后续接触业主了解品牌后面怎么推荐方式。	2025-11-13 07:16:30.446208	15	t
1840	2025-11-13	\N	712	867	通过航博代理商反馈项目信息，找到设计院中联，项目3年前搁置，目前图纸方案也是他们原来自己随便设计的常规系统，现在不确定还能否修改，后续跟进。	2025-11-13 07:23:14.414028	15	t
1841	2025-11-13	391	319	527	同李总一起拜访对方采购，目前他们已经进场，预计1月份左右开始穿线。由于价格跟对方以往合作的存在较大差异，跟对方介绍了和源产品和公司情况，对方表示不要差异太大，让我们进行初步深化和价格申请。安排李总及时沟通反馈商务情况。	2025-11-13 07:30:10.031131	15	t
1843	2025-11-12	545	223	150	拜访瞿迪，沟通站前区A3-01地块，10月份业主有过一版品牌表中，瞿迪看到有和源，应该是参考了东站本体招标品牌，没有分层，为摩托，和源及中兴高达。瞿迪意思按院里要求他们不参与招标技术要求和品牌推荐，只是提供图纸设计，项目据说弱电与机电一同招标。需确认招标品牌，复核招标计划。A1A-01和A4B-01目前在施工图审图阶段。需跟进确认招标方案，了解招标品牌和招标计划。其余新增为浦开在张家浜的住宅业务，目前他在品牌推荐中更趋向于按地方规范进行推荐	2025-11-14 05:05:11.905036	14	t
1844	2025-11-12	546	223	59	拜访闻锋，沟通社会主义学院项目，总包建工中标，智能化分包会给予仪电鑫森，项目土建即将启动，近期用户运营会与仪电鑫森有关智能化进行沟通。北京西路项目，机电招标，弱电图纸还在修改，但闻锋并不负责品牌推荐。静安图书馆二期:之前在方案可研阶段，近期没有任何消息，业主有引荐一家智能化公司，闻锋让其配合做概算	2025-11-14 05:06:27.588224	14	t
1845	2025-11-13	576	248	24	拜访庄妍华，答谢御桥项目，并沟通张家浜绿地，了解到目前2个地块还未有收到集成商提供的有关系统任何资料。今年卓展新增项目不多，主要集中在改造和酒店行业	2025-11-14 05:08:54.126567	14	t
1846	2025-11-13	728	241	\N	与渠道一同参与通号组织的有关浦东东站地上标段与华东院技术方案确认会，目前初步对有关方案进行确认，后续通号计划一种等待地上标段确认品牌后，直接以统一品牌为理由内部发起竞价谈判，或者内部挂网招标，配合做招标文件，控制中标结果，预计时间在今年底至明年初会启动	2025-11-14 05:11:27.217769	14	t
1847	2025-11-11	536	215	813	渠道反馈，配合上安参与项目报价。目前项目技术标已经投标，商务标即将启动	2025-11-14 05:12:56.785705	14	t
1848	2025-11-14	904	687	868	该项目郡申配合总包参与项目报价，最低价中标，目前在议价过程中，提供技术及价格支持	2025-11-14 05:19:58.721462	14	t
1849	2025-11-14	211	496	869	该项目集成商中标，项目为二期扩建，需新增天馈设备采购	2025-11-14 05:27:02.813925	14	t
1850	2025-11-14	176	341	535	和邹娟他们协商好和李冬他们之间的合作以及供货方式，核对好清单 ，计划下周提交相关的批价流程 	2025-11-14 14:17:54.900657	13	t
1851	2025-11-14	183	350	109	浦东机场目前吴老师他们已配合指挥部他们进行了一轮的品牌调研工作，调研的品牌，有和源通信、烈龙，锐河、凌越，主是以参加上海的地标单位，目前反馈我们案例优势比较明显，据说最终确定品牌还是机场的大领导周荣来决定。已确定将消防对讲、有限电视、综合布线以及广播四个系统划为一个包，1.2亿左右，会对总包进行一定的资质筛选入围，指挥部对招标还是有把控能力的。据说上海泰豪朱兆基在运作此项目，后期计划提前接触	2025-11-14 14:26:22.050566	13	t
\.


--
-- TOC entry 5005 (class 0 OID 17345)
-- Dependencies: 306
-- Data for Name: affiliations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.affiliations (id, owner_id, viewer_id, created_at) FROM stdin;
140	2	9	1753157501.2701292
141	17	9	1753157501.276043
142	10	9	1753157501.280365
143	14	9	1753157501.2841847
144	18	9	1753157501.2875166
145	19	9	1753157501.2929728
146	15	9	1753157501.2967057
147	16	9	1753157501.3002625
148	13	9	1753157501.3051386
149	12	9	1753157501.3090558
150	20	9	1753157501.3147852
151	7	9	1753157501.3182645
46	7	29	1746925351.10497
53	20	7	1747007541.1512697
54	2	7	1747007541.1616883
55	11	10	1747007577.8188853
56	12	10	1747007577.8229327
67	6	4	1747008131.4079785
69	14	4	1747008131.4163432
70	13	4	1747008131.420363
71	16	4	1747008131.4241817
72	7	4	1747008131.4281096
73	15	4	1747008131.4321363
74	17	4	1747008131.4366107
75	29	4	1747008131.4403765
76	19	4	1747008131.4462335
77	22	4	1747008131.4514062
78	20	4	1747008131.4556158
79	3	4	1747008131.460326
80	2	4	1747008131.4641833
81	25	4	1747008131.4679577
82	24	4	1747008131.471684
83	23	4	1747008131.475264
153	34	24	1754976932.6843207
154	35	3	1754977506.0181937
155	36	3	1754977506.0211976
157	19	13	1754977543.1016376
158	14	13	1754977543.1046145
159	16	13	1754977543.1077185
160	17	13	1754977543.1110663
161	18	13	1754977543.1137123
162	15	13	1754977543.116351
163	22	13	1754977543.1192968
164	3	13	1754977543.1227314
165	25	13	1754977543.1254315
166	24	13	1754977543.128695
167	23	13	1754977543.133321
168	35	13	1754977543.136311
169	36	13	1754977543.1390874
209	22	18	1760700015.7196038
210	3	18	1760700015.7287743
211	25	18	1760700015.7349005
212	24	18	1760700015.7415795
213	23	18	1760700015.7479882
214	35	18	1760700015.754381
215	36	18	1760700015.7610073
216	37	18	1760700015.7677274
217	38	18	1760700015.774043
