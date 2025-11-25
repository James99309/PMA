--
-- PostgreSQL database dump
--

\restrict uXloyvhsyDGsdSbXS7Q5VjaiufPubSN7uGrSmFwuQLJUAJ4pBwu4XCVtY8FnESf

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.6 (Homebrew)

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
ALTER TABLE IF EXISTS ONLY storage.vector_indexes DROP CONSTRAINT IF EXISTS vector_indexes_bucket_id_fkey;
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
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS approval_record_instance_id_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_process_template DROP CONSTRAINT IF EXISTS approval_process_template_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_instance DROP CONSTRAINT IF EXISTS approval_instance_process_id_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_instance DROP CONSTRAINT IF EXISTS approval_instance_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_branch_condition DROP CONSTRAINT IF EXISTS approval_branch_condition_step_id_fkey;
ALTER TABLE IF EXISTS ONLY public.approval_branch_condition DROP CONSTRAINT IF EXISTS approval_branch_condition_approver_id_fkey;
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
DROP INDEX IF EXISTS storage.vector_indexes_name_bucket_id_idx;
DROP INDEX IF EXISTS storage.objects_bucket_id_level_idx;
DROP INDEX IF EXISTS storage.name_prefix_search;
DROP INDEX IF EXISTS storage.idx_prefixes_lower_name;
DROP INDEX IF EXISTS storage.idx_objects_lower_name;
DROP INDEX IF EXISTS storage.idx_objects_bucket_id_name;
DROP INDEX IF EXISTS storage.idx_name_bucket_level_unique;
DROP INDEX IF EXISTS storage.idx_multipart_uploads_list;
DROP INDEX IF EXISTS storage.buckets_analytics_unique_name_idx;
DROP INDEX IF EXISTS storage.bucketid_objname;
DROP INDEX IF EXISTS storage.bname;
DROP INDEX IF EXISTS realtime.subscription_subscription_id_entity_filters_key;
DROP INDEX IF EXISTS realtime.messages_inserted_at_topic_index;
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
ALTER TABLE IF EXISTS ONLY storage.vector_indexes DROP CONSTRAINT IF EXISTS vector_indexes_pkey;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads DROP CONSTRAINT IF EXISTS s3_multipart_uploads_pkey;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads_parts DROP CONSTRAINT IF EXISTS s3_multipart_uploads_parts_pkey;
ALTER TABLE IF EXISTS ONLY storage.prefixes DROP CONSTRAINT IF EXISTS prefixes_pkey;
ALTER TABLE IF EXISTS ONLY storage.objects DROP CONSTRAINT IF EXISTS objects_pkey;
ALTER TABLE IF EXISTS ONLY storage.migrations DROP CONSTRAINT IF EXISTS migrations_pkey;
ALTER TABLE IF EXISTS ONLY storage.migrations DROP CONSTRAINT IF EXISTS migrations_name_key;
ALTER TABLE IF EXISTS ONLY storage.buckets_vectors DROP CONSTRAINT IF EXISTS buckets_vectors_pkey;
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
ALTER TABLE IF EXISTS ONLY public.project_scoring_records DROP CONSTRAINT IF EXISTS uq_scoring_record;
ALTER TABLE IF EXISTS ONLY public.project_scoring_config DROP CONSTRAINT IF EXISTS uq_scoring_config;
ALTER TABLE IF EXISTS ONLY public.role_performance_items DROP CONSTRAINT IF EXISTS uq_role_item_code;
ALTER TABLE IF EXISTS ONLY public.role_performance_access DROP CONSTRAINT IF EXISTS uq_role_access_scope;
ALTER TABLE IF EXISTS ONLY public.project_rating_records DROP CONSTRAINT IF EXISTS uq_project_user_rating;
ALTER TABLE IF EXISTS ONLY public.upgrade_logs DROP CONSTRAINT IF EXISTS upgrade_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.project_customer_associations DROP CONSTRAINT IF EXISTS unique_project_company;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS unique_company_product_inventory;
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
ALTER TABLE IF EXISTS ONLY public.approval_record DROP CONSTRAINT IF EXISTS approval_record_temp_pkey;
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
ALTER TABLE IF EXISTS public.approval_process_template ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.approval_instance ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.affiliations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.actions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.action_reply ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS auth.refresh_tokens ALTER COLUMN id DROP DEFAULT;
DROP TABLE IF EXISTS storage.vector_indexes;
DROP TABLE IF EXISTS storage.s3_multipart_uploads_parts;
DROP TABLE IF EXISTS storage.s3_multipart_uploads;
DROP TABLE IF EXISTS storage.prefixes;
DROP TABLE IF EXISTS storage.objects;
DROP TABLE IF EXISTS storage.migrations;
DROP TABLE IF EXISTS storage.buckets_vectors;
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
DROP TABLE IF EXISTS public.pricing_order_approval_records_backup;
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
DROP TABLE IF EXISTS public.approval_record;
DROP SEQUENCE IF EXISTS public.approval_record_id_seq;
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
-- Name: auth; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA auth;


--
-- Name: extensions; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA extensions;


--
-- Name: graphql; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA graphql;


--
-- Name: graphql_public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA graphql_public;


--
-- Name: pgbouncer; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA pgbouncer;


--
-- Name: realtime; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA realtime;


--
-- Name: storage; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA storage;


--
-- Name: vault; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA vault;


--
-- Name: pg_graphql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_graphql WITH SCHEMA graphql;


--
-- Name: EXTENSION pg_graphql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_graphql IS 'pg_graphql: GraphQL support';


--
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA extensions;


--
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: supabase_vault; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS supabase_vault WITH SCHEMA vault;


--
-- Name: EXTENSION supabase_vault; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION supabase_vault IS 'Supabase Vault Extension';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: aal_level; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.aal_level AS ENUM (
    'aal1',
    'aal2',
    'aal3'
);


--
-- Name: code_challenge_method; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.code_challenge_method AS ENUM (
    's256',
    'plain'
);


--
-- Name: factor_status; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.factor_status AS ENUM (
    'unverified',
    'verified'
);


--
-- Name: factor_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.factor_type AS ENUM (
    'totp',
    'webauthn',
    'phone'
);


--
-- Name: oauth_authorization_status; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_authorization_status AS ENUM (
    'pending',
    'approved',
    'denied',
    'expired'
);


--
-- Name: oauth_client_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_client_type AS ENUM (
    'public',
    'confidential'
);


--
-- Name: oauth_registration_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_registration_type AS ENUM (
    'dynamic',
    'manual'
);


--
-- Name: oauth_response_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_response_type AS ENUM (
    'code'
);


--
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
    'REJECTED',
    'RECALLED'
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


--
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
-- Name: user_defined_filter; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.user_defined_filter AS (
	column_name text,
	op realtime.equality_op,
	value text
);


--
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
-- Name: wal_rls; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.wal_rls AS (
	wal jsonb,
	is_rls_enabled boolean,
	subscription_ids uuid[],
	errors text[]
);


--
-- Name: buckettype; Type: TYPE; Schema: storage; Owner: -
--

CREATE TYPE storage.buckettype AS ENUM (
    'STANDARD',
    'ANALYTICS',
    'VECTOR'
);


--
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
-- Name: FUNCTION email(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.email() IS 'Deprecated. Use auth.jwt() -> ''email'' instead.';


--
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
-- Name: FUNCTION role(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.role() IS 'Deprecated. Use auth.jwt() -> ''role'' instead.';


--
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
-- Name: FUNCTION uid(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.uid() IS 'Deprecated. Use auth.jwt() -> ''sub'' instead.';


--
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
-- Name: FUNCTION grant_pg_cron_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_cron_access() IS 'Grants access to pg_cron';


--
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
-- Name: FUNCTION grant_pg_graphql_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_graphql_access() IS 'Grants access to pg_graphql';


--
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
-- Name: FUNCTION grant_pg_net_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_net_access() IS 'Grants access to pg_net';


--
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
-- Name: FUNCTION set_graphql_placeholder(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.set_graphql_placeholder() IS 'Reintroduces placeholder function for graphql_public.graphql';


--
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
-- Name: send(jsonb, text, text, boolean); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.send(payload jsonb, event text, topic text, private boolean DEFAULT true) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
  generated_id uuid;
  final_payload jsonb;
BEGIN
  BEGIN
    -- Generate a new UUID for the id
    generated_id := gen_random_uuid();

    -- Check if payload has an 'id' key, if not, add the generated UUID
    IF payload ? 'id' THEN
      final_payload := payload;
    ELSE
      final_payload := jsonb_set(payload, '{id}', to_jsonb(generated_id));
    END IF;

    -- Set the topic configuration
    EXECUTE format('SET LOCAL realtime.topic TO %L', topic);

    -- Attempt to insert the message
    INSERT INTO realtime.messages (id, payload, event, topic, private, extension)
    VALUES (generated_id, final_payload, event, topic, private, 'broadcast');
  EXCEPTION
    WHEN OTHERS THEN
      -- Capture and notify the error
      RAISE WARNING 'ErrorSendingBroadcastMessage: %', SQLERRM;
  END;
END;
$$;


--
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
-- Name: to_regrole(text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.to_regrole(role_name text) RETURNS regrole
    LANGUAGE sql IMMUTABLE
    AS $$ select role_name::regrole $$;


--
-- Name: topic(); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.topic() RETURNS text
    LANGUAGE sql STABLE
    AS $$
select nullif(current_setting('realtime.topic', true), '')::text;
$$;


--
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
-- Name: get_level(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_level(name text) RETURNS integer
    LANGUAGE sql IMMUTABLE STRICT
    AS $$
SELECT array_length(string_to_array("name", '/'), 1);
$$;


--
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
-- Name: TABLE audit_log_entries; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.audit_log_entries IS 'Auth: Audit trail for user actions.';


--
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
-- Name: TABLE flow_state; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.flow_state IS 'stores metadata for pkce logins';


--
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
-- Name: TABLE identities; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.identities IS 'Auth: Stores identities associated to a user.';


--
-- Name: COLUMN identities.email; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.identities.email IS 'Auth: Email is a generated column that references the optional email property in the identity_data';


--
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
-- Name: TABLE instances; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.instances IS 'Auth: Manages users across multiple sites.';


--
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
-- Name: TABLE mfa_amr_claims; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_amr_claims IS 'auth: stores authenticator method reference claims for multi factor authentication';


--
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
-- Name: TABLE mfa_challenges; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_challenges IS 'auth: stores metadata about challenge requests made';


--
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
-- Name: TABLE mfa_factors; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_factors IS 'auth: stores metadata about factors';


--
-- Name: COLUMN mfa_factors.last_webauthn_challenge_data; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.mfa_factors.last_webauthn_challenge_data IS 'Stores the latest WebAuthn challenge data including attestation/assertion for customer verification';


--
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
-- Name: TABLE refresh_tokens; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.refresh_tokens IS 'Auth: Store of tokens used to refresh JWT tokens once they expire.';


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE; Schema: auth; Owner: -
--

CREATE SEQUENCE auth.refresh_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: -
--

ALTER SEQUENCE auth.refresh_tokens_id_seq OWNED BY auth.refresh_tokens.id;


--
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
-- Name: TABLE saml_providers; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.saml_providers IS 'Auth: Manages SAML Identity Provider connections.';


--
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
-- Name: TABLE saml_relay_states; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.saml_relay_states IS 'Auth: Contains SAML Relay State information for each Service Provider initiated login.';


--
-- Name: schema_migrations; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.schema_migrations (
    version character varying(255) NOT NULL
);


--
-- Name: TABLE schema_migrations; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.schema_migrations IS 'Auth: Manages updates to the auth system.';


--
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
-- Name: TABLE sessions; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sessions IS 'Auth: Stores session data associated to a user.';


--
-- Name: COLUMN sessions.not_after; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.not_after IS 'Auth: Not after is a nullable column that contains a timestamp after which the session should be regarded as expired.';


--
-- Name: COLUMN sessions.refresh_token_hmac_key; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.refresh_token_hmac_key IS 'Holds a HMAC-SHA256 key used to sign refresh tokens for this session.';


--
-- Name: COLUMN sessions.refresh_token_counter; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.refresh_token_counter IS 'Holds the ID (counter) of the last issued refresh token.';


--
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
-- Name: TABLE sso_domains; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sso_domains IS 'Auth: Manages SSO email address domain mapping to an SSO Identity Provider.';


--
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
-- Name: TABLE sso_providers; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sso_providers IS 'Auth: Manages SSO identity provider information; see saml_providers for SAML.';


--
-- Name: COLUMN sso_providers.resource_id; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sso_providers.resource_id IS 'Auth: Uniquely identifies a SSO provider according to a user-chosen resource ID (case insensitive), useful in infrastructure as code.';


--
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
-- Name: TABLE users; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.users IS 'Auth: Stores user login data within a secure schema.';


--
-- Name: COLUMN users.is_sso_user; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.users.is_sso_user IS 'Auth: Set this column to true when the account comes from SSO. These accounts can have duplicate emails.';


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
    owner_id integer,
    is_shared boolean NOT NULL
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
-- Name: approval_branch_condition; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.approval_branch_condition (
    id character varying(50) NOT NULL,
    step_id integer NOT NULL,
    condition_order integer,
    operator character varying(50) NOT NULL,
    field_value character varying(255) NOT NULL,
    approver_id integer,
    approver_type character varying(50),
    action character varying(100),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    CONSTRAINT chk_approver_type_valid CHECK (((approver_type)::text = ANY ((ARRAY['user'::character varying, 'next_level'::character varying, 'next_branch'::character varying])::text[]))),
    CONSTRAINT chk_condition_order_positive CHECK ((condition_order >= 0)),
    CONSTRAINT chk_operator_valid CHECK (((operator)::text = ANY ((ARRAY['equals'::character varying, 'not_equals'::character varying, 'contains'::character varying, 'not_contains'::character varying, 'greater_than'::character varying, 'less_than'::character varying, 'in'::character varying, 'not_in'::character varying, 'starts_with'::character varying, 'ends_with'::character varying, 'is_null'::character varying, 'is_not_null'::character varying])::text[])))
);


--
-- Name: COLUMN approval_branch_condition.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_branch_condition.id IS '条件唯一标识符';


--
-- Name: COLUMN approval_branch_condition.step_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_branch_condition.step_id IS '关联的审批步骤ID';


--
-- Name: COLUMN approval_branch_condition.condition_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_branch_condition.condition_order IS '条件在步骤中的排序位置';


--
-- Name: COLUMN approval_branch_condition.operator; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_branch_condition.operator IS '条件操作符';


--
-- Name: COLUMN approval_branch_condition.field_value; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_branch_condition.field_value IS '条件匹配的字段值';


--
-- Name: COLUMN approval_branch_condition.approver_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_branch_condition.approver_id IS '满足条件时的审批人用户ID';


--
-- Name: COLUMN approval_branch_condition.approver_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_branch_condition.approver_type IS '审批人类型';


--
-- Name: COLUMN approval_branch_condition.action; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_branch_condition.action IS '满足条件时执行的业务动作';


--
-- Name: COLUMN approval_branch_condition.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_branch_condition.created_at IS '创建时间';


--
-- Name: COLUMN approval_branch_condition.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.approval_branch_condition.updated_at IS '更新时间';


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
    lock_reason character varying(200) DEFAULT '审批流程进行中，暂时锁定编辑'::character varying,
    visual_data json
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
    step_id integer,
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
    branch_on_approve integer,
    step_type character varying(20) DEFAULT 'normal'::character varying,
    branch_condition json,
    parent_step_id integer,
    is_parallel boolean DEFAULT false,
    branch_group_id character varying(50) DEFAULT NULL::character varying,
    branch_level integer DEFAULT 0,
    branch_path character varying(100) DEFAULT NULL::character varying,
    merge_step_id integer
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
    share_contacts boolean,
    share_enabled boolean NOT NULL,
    source character varying(20)
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
-- Name: COLUMN company_assets.asset_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.asset_type IS '资产类型: logo, seal, etc.';


--
-- Name: COLUMN company_assets.asset_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.asset_name IS '资产名称';


--
-- Name: COLUMN company_assets.asset_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.asset_key IS '资产唯一标识';


--
-- Name: COLUMN company_assets.file_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_name IS '原始文件名';


--
-- Name: COLUMN company_assets.file_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_type IS '文件类型: image/png, image/svg+xml, etc.';


--
-- Name: COLUMN company_assets.file_size; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_size IS '文件大小(字节)';


--
-- Name: COLUMN company_assets.file_content; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.file_content IS 'Base64编码的文件内容';


--
-- Name: COLUMN company_assets.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.description IS '资产描述';


--
-- Name: COLUMN company_assets.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.is_active IS '是否启用';


--
-- Name: COLUMN company_assets.is_default; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.company_assets.is_default IS '是否为默认资产';


--
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
-- Name: company_assets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.company_assets_id_seq OWNED BY public.company_assets.id;


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
-- Name: COLUMN data_field_config.field_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.field_name IS '字段名';


--
-- Name: COLUMN data_field_config.display_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.display_name IS '显示名称';


--
-- Name: COLUMN data_field_config.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.description IS '字段描述';


--
-- Name: COLUMN data_field_config.data_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.data_type IS '数据类型';


--
-- Name: COLUMN data_field_config.is_nullable; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_nullable IS '是否可为空';


--
-- Name: COLUMN data_field_config.is_primary_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_primary_key IS '是否主键';


--
-- Name: COLUMN data_field_config.is_foreign_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_foreign_key IS '是否外键';


--
-- Name: COLUMN data_field_config.foreign_table; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.foreign_table IS '外键关联表';


--
-- Name: COLUMN data_field_config.foreign_field; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.foreign_field IS '外键关联字段';


--
-- Name: COLUMN data_field_config.is_numeric; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_numeric IS '是否数值字段';


--
-- Name: COLUMN data_field_config.is_monetary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_monetary IS '是否金额字段';


--
-- Name: COLUMN data_field_config.is_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_date IS '是否日期字段';


--
-- Name: COLUMN data_field_config.is_aggregatable; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_aggregatable IS '是否可聚合统计';


--
-- Name: COLUMN data_field_config.is_filterable; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_filterable IS '是否可过滤';


--
-- Name: COLUMN data_field_config.is_performance_metric; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.is_performance_metric IS '是否绩效指标';


--
-- Name: COLUMN data_field_config.performance_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.performance_category IS '绩效分类：sales/customer/project/quality';


--
-- Name: COLUMN data_field_config.calculation_priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.calculation_priority IS '计算优先级';


--
-- Name: COLUMN data_field_config.display_format; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.display_format IS '显示格式';


--
-- Name: COLUMN data_field_config.default_unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.default_unit IS '默认单位';


--
-- Name: COLUMN data_field_config.decimal_places; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.decimal_places IS '小数位数';


--
-- Name: COLUMN data_field_config.sample_values; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.sample_values IS '样本值JSON';


--
-- Name: COLUMN data_field_config.value_range; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_field_config.value_range IS '值范围JSON';


--
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
-- Name: data_field_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_field_config_id_seq OWNED BY public.data_field_config.id;


--
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
-- Name: COLUMN data_table_config.table_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.table_name IS '数据表名';


--
-- Name: COLUMN data_table_config.display_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.display_name IS '显示名称';


--
-- Name: COLUMN data_table_config.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.description IS '表描述';


--
-- Name: COLUMN data_table_config.category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.category IS '表分类：business/system/reference';


--
-- Name: COLUMN data_table_config.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.is_active IS '是否启用';


--
-- Name: COLUMN data_table_config.is_performance_source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.is_performance_source IS '是否可用作绩效数据源';


--
-- Name: COLUMN data_table_config.total_records; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.total_records IS '记录总数';


--
-- Name: COLUMN data_table_config.last_updated; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.data_table_config.last_updated IS '数据最后更新时间';


--
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
-- Name: data_table_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_table_config_id_seq OWNED BY public.data_table_config.id;


--
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
-- Name: departments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.departments_id_seq OWNED BY public.departments.id;


--
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
-- Name: dev_product_milestones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_product_milestones_id_seq OWNED BY public.dev_product_milestones.id;


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
    pdf_path character varying(255),
    currency character varying(3) DEFAULT 'CNY'::character varying NOT NULL,
    planned_duration_days integer,
    actual_duration_days integer,
    risk_level character varying(20) DEFAULT 'medium'::character varying,
    baseline_date timestamp without time zone,
    milestone_count integer DEFAULT 0,
    stage_description text,
    stage_history json,
    stage_records json
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
-- Name: expense_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expense_details_id_seq OWNED BY public.expense_details.id;


--
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
-- Name: expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expenses_id_seq OWNED BY public.expenses.id;


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
-- Name: five_star_project_baselines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.five_star_project_baselines_id_seq OWNED BY public.five_star_project_baselines.id;


--
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
-- Name: COLUMN formula_templates_extended.template_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.template_name IS '模板名称';


--
-- Name: COLUMN formula_templates_extended.template_category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.template_category IS '模板分类';


--
-- Name: COLUMN formula_templates_extended.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.description IS '模板描述';


--
-- Name: COLUMN formula_templates_extended.formula_expression; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.formula_expression IS '公式表达式';


--
-- Name: COLUMN formula_templates_extended.required_tables; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.required_tables IS '需要的数据表JSON';


--
-- Name: COLUMN formula_templates_extended.required_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.required_fields IS '需要的字段JSON';


--
-- Name: COLUMN formula_templates_extended.result_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.result_type IS '结果类型：numeric/percentage/count';


--
-- Name: COLUMN formula_templates_extended.result_unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.result_unit IS '结果单位';


--
-- Name: COLUMN formula_templates_extended.is_system_template; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.is_system_template IS '是否系统模板';


--
-- Name: COLUMN formula_templates_extended.is_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.is_active IS '是否启用';


--
-- Name: COLUMN formula_templates_extended.usage_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.usage_count IS '使用次数';


--
-- Name: COLUMN formula_templates_extended.last_used_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.formula_templates_extended.last_used_at IS '最后使用时间';


--
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
-- Name: formula_templates_extended_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.formula_templates_extended_id_seq OWNED BY public.formula_templates_extended.id;


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
-- Name: performance_formula_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_formula_templates_id_seq OWNED BY public.performance_formula_templates.id;


--
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
-- Name: performance_metrics_definition_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_metrics_definition_id_seq OWNED BY public.performance_metrics_definition.id;


--
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
-- Name: performance_statistics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_statistics_id_seq OWNED BY public.performance_statistics.id;


--
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
-- Name: performance_targets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_targets_id_seq OWNED BY public.performance_targets.id;


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
    can_delete boolean,
    permission_level character varying(20) DEFAULT 'personal'::character varying NOT NULL,
    permission_level_description text,
    pricing_discount_limit double precision,
    settlement_discount_limit double precision,
    can_change_owner boolean DEFAULT false,
    content_filters json
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
-- Name: pricing_order_approval_records_backup; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pricing_order_approval_records_backup (
    id integer,
    pricing_order_id integer,
    step_order integer,
    step_name character varying(64),
    approver_role character varying(64),
    approver_id integer,
    action character varying(16),
    comment text,
    approved_at timestamp without time zone,
    is_fast_approval boolean,
    fast_approval_reason character varying(255)
);


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
    source_quotation_detail_id integer,
    currency character varying(10) DEFAULT 'CNY'::character varying
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
-- Name: COLUMN pricing_orders.distributor_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.distributor_id IS '分销商ID';


--
-- Name: COLUMN pricing_orders.dealer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.dealer_id IS '经销商ID';


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
-- Name: COLUMN pricing_orders.is_direct_contract; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.is_direct_contract IS '厂商直签';


--
-- Name: COLUMN pricing_orders.is_factory_pickup; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pricing_orders.is_factory_pickup IS '厂家提货';


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
    pdf_path character varying(255),
    currency character varying(3) DEFAULT 'CNY'::character varying NOT NULL,
    is_vendor_product boolean DEFAULT false
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
-- Name: TABLE project_customer_associations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.project_customer_associations IS '项目客户关联表';


--
-- Name: COLUMN project_customer_associations.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.id IS '主键ID';


--
-- Name: COLUMN project_customer_associations.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.project_id IS '关联的项目ID';


--
-- Name: COLUMN project_customer_associations.company_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.company_id IS '关联的公司ID';


--
-- Name: COLUMN project_customer_associations.customer_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.customer_type IS '客户类型（end_user等）';


--
-- Name: COLUMN project_customer_associations.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.created_at IS '创建时间';


--
-- Name: COLUMN project_customer_associations.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.updated_at IS '更新时间';


--
-- Name: COLUMN project_customer_associations.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_customer_associations.created_by IS '创建者用户ID';


--
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
-- Name: project_customer_associations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_customer_associations_id_seq OWNED BY public.project_customer_associations.id;


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
    industry character varying(50),
    shared_with_users jsonb,
    share_enabled boolean NOT NULL,
    status character varying(20) NOT NULL,
    created_by integer NOT NULL
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
    implant_subtotal double precision DEFAULT 0.00,
    currency character varying(3),
    original_market_price double precision,
    converted_market_price double precision
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
    confirmation_badge_status character varying(20) DEFAULT 'none'::character varying,
    confirmation_badge_color character varying(20) DEFAULT NULL::character varying,
    confirmed_by integer,
    confirmed_at timestamp without time zone,
    product_signature character varying(64) DEFAULT NULL::character varying,
    implant_total_amount double precision DEFAULT 0.00,
    currency character varying(3) DEFAULT 'CNY'::character varying NOT NULL,
    exchange_rate numeric(10,6) DEFAULT 1.000000 NOT NULL,
    original_currency character varying(3),
    customer_id integer
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
-- Name: role_performance_access_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_performance_access_id_seq OWNED BY public.role_performance_access.id;


--
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
-- Name: role_performance_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_performance_config_id_seq OWNED BY public.role_performance_config.id;


--
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
-- Name: role_performance_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_performance_items_id_seq OWNED BY public.role_performance_items.id;


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
    can_delete boolean,
    pricing_discount_limit double precision,
    settlement_discount_limit double precision,
    permission_level character varying DEFAULT 'personal'::character varying,
    permission_level_description text,
    can_change_owner boolean DEFAULT false,
    content_filters json
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
    settlement_notes text,
    currency character varying(10) DEFAULT 'CNY'::character varying
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
    settlement_status character varying(20) DEFAULT '''pending'''::character varying,
    is_direct_contract boolean DEFAULT false,
    is_factory_pickup boolean DEFAULT false
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
-- Name: stage_attachments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stage_attachments_id_seq OWNED BY public.stage_attachments.id;


--
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
-- Name: stage_dependencies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stage_dependencies_id_seq OWNED BY public.stage_dependencies.id;


--
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
-- Name: stage_reviews_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stage_reviews_id_seq OWNED BY public.stage_reviews.id;


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
-- Name: COLUMN temp_products.product_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_name IS '产品名称';


--
-- Name: COLUMN temp_products.product_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_model IS '产品型号';


--
-- Name: COLUMN temp_products.product_desc; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_desc IS '产品描述/规格';


--
-- Name: COLUMN temp_products.brand; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.brand IS '品牌';


--
-- Name: COLUMN temp_products.unit; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.unit IS '单位';


--
-- Name: COLUMN temp_products.product_mn; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.product_mn IS '临时产品MN号，格式为TEMP-{8位随机码}';


--
-- Name: COLUMN temp_products.category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.category IS '关联的三级分类';


--
-- Name: COLUMN temp_products.category_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.category_path IS '完整分类路径，如：基站/近端设备/室内型';


--
-- Name: COLUMN temp_products.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.created_by IS '创建用户ID';


--
-- Name: COLUMN temp_products.reference_price; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.reference_price IS '参考价格（保存时的单价）';


--
-- Name: COLUMN temp_products.usage_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.usage_count IS '使用次数';


--
-- Name: COLUMN temp_products.last_used_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.last_used_at IS '最后使用时间';


--
-- Name: COLUMN temp_products.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.created_at IS '创建时间';


--
-- Name: COLUMN temp_products.updated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.updated_at IS '更新时间';


--
-- Name: COLUMN temp_products.is_deleted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.temp_products.is_deleted IS '是否已删除';


--
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
-- Name: temp_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.temp_products_id_seq OWNED BY public.temp_products.id;


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
    updated_at double precision,
    language_preference character varying(10)
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
-- Name: schema_migrations; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);


--
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
-- Name: COLUMN buckets.owner; Type: COMMENT; Schema: storage; Owner: -
--

COMMENT ON COLUMN storage.buckets.owner IS 'Field is deprecated, use owner_id instead';


--
-- Name: buckets_analytics; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.buckets_analytics (
    name text NOT NULL,
    type storage.buckettype DEFAULT 'ANALYTICS'::storage.buckettype NOT NULL,
    format text DEFAULT 'ICEBERG'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: buckets_vectors; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.buckets_vectors (
    id text NOT NULL,
    type storage.buckettype DEFAULT 'VECTOR'::storage.buckettype NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: migrations; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.migrations (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    hash character varying(40) NOT NULL,
    executed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
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
-- Name: COLUMN objects.owner; Type: COMMENT; Schema: storage; Owner: -
--

COMMENT ON COLUMN storage.objects.owner IS 'Field is deprecated, use owner_id instead';


--
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
-- Name: vector_indexes; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.vector_indexes (
    id text DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL COLLATE pg_catalog."C",
    bucket_id text NOT NULL,
    data_type text NOT NULL,
    dimension integer NOT NULL,
    distance_metric text NOT NULL,
    metadata_configuration jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: refresh_tokens id; Type: DEFAULT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('auth.refresh_tokens_id_seq'::regclass);


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
-- Name: company_assets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_assets ALTER COLUMN id SET DEFAULT nextval('public.company_assets_id_seq'::regclass);


--
-- Name: contacts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contacts ALTER COLUMN id SET DEFAULT nextval('public.contacts_id_seq'::regclass);


--
-- Name: data_field_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_field_config ALTER COLUMN id SET DEFAULT nextval('public.data_field_config_id_seq'::regclass);


--
-- Name: data_table_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_table_config ALTER COLUMN id SET DEFAULT nextval('public.data_table_config_id_seq'::regclass);


--
-- Name: departments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments ALTER COLUMN id SET DEFAULT nextval('public.departments_id_seq'::regclass);


--
-- Name: dev_product_milestones id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_product_milestones ALTER COLUMN id SET DEFAULT nextval('public.dev_product_milestones_id_seq'::regclass);


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
-- Name: expense_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense_details ALTER COLUMN id SET DEFAULT nextval('public.expense_details_id_seq'::regclass);


--
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.expenses_id_seq'::regclass);


--
-- Name: feature_changes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_changes ALTER COLUMN id SET DEFAULT nextval('public.feature_changes_id_seq'::regclass);


--
-- Name: five_star_project_baselines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.five_star_project_baselines ALTER COLUMN id SET DEFAULT nextval('public.five_star_project_baselines_id_seq'::regclass);


--
-- Name: formula_templates_extended id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formula_templates_extended ALTER COLUMN id SET DEFAULT nextval('public.formula_templates_extended_id_seq'::regclass);


--
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- Name: inventory_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_transactions ALTER COLUMN id SET DEFAULT nextval('public.inventory_transactions_id_seq'::regclass);


--
-- Name: performance_formula_templates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_formula_templates ALTER COLUMN id SET DEFAULT nextval('public.performance_formula_templates_id_seq'::regclass);


--
-- Name: performance_metrics_definition id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_metrics_definition ALTER COLUMN id SET DEFAULT nextval('public.performance_metrics_definition_id_seq'::regclass);


--
-- Name: performance_statistics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_statistics ALTER COLUMN id SET DEFAULT nextval('public.performance_statistics_id_seq'::regclass);


--
-- Name: performance_targets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_targets ALTER COLUMN id SET DEFAULT nextval('public.performance_targets_id_seq'::regclass);


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
-- Name: project_customer_associations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_customer_associations ALTER COLUMN id SET DEFAULT nextval('public.project_customer_associations_id_seq'::regclass);


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
-- Name: role_performance_access id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_access ALTER COLUMN id SET DEFAULT nextval('public.role_performance_access_id_seq'::regclass);


--
-- Name: role_performance_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_config ALTER COLUMN id SET DEFAULT nextval('public.role_performance_config_id_seq'::regclass);


--
-- Name: role_performance_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_performance_items ALTER COLUMN id SET DEFAULT nextval('public.role_performance_items_id_seq'::regclass);


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
-- Name: stage_attachments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stage_attachments ALTER COLUMN id SET DEFAULT nextval('public.stage_attachments_id_seq'::regclass);


--
-- Name: stage_dependencies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stage_dependencies ALTER COLUMN id SET DEFAULT nextval('public.stage_dependencies_id_seq'::regclass);


--
-- Name: stage_reviews id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stage_reviews ALTER COLUMN id SET DEFAULT nextval('public.stage_reviews_id_seq'::regclass);


--
-- Name: system_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_metrics ALTER COLUMN id SET DEFAULT nextval('public.system_metrics_id_seq'::regclass);


--
-- Name: system_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings ALTER COLUMN id SET DEFAULT nextval('public.system_settings_id_seq'::regclass);


--
-- Name: temp_products id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temp_products ALTER COLUMN id SET DEFAULT nextval('public.temp_products_id_seq'::regclass);


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
-- Data for Name: audit_log_entries; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.audit_log_entries (instance_id, id, payload, created_at, ip_address) FROM stdin;
\.


--
-- Data for Name: flow_state; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.flow_state (id, user_id, auth_code, code_challenge_method, code_challenge, provider_type, provider_access_token, provider_refresh_token, created_at, updated_at, authentication_method, auth_code_issued_at) FROM stdin;
\.


--
-- Data for Name: identities; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.identities (provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at, id) FROM stdin;
\.


--
-- Data for Name: instances; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.instances (id, uuid, raw_base_config, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: mfa_amr_claims; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.mfa_amr_claims (session_id, created_at, updated_at, authentication_method, id) FROM stdin;
\.


--
-- Data for Name: mfa_challenges; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.mfa_challenges (id, factor_id, created_at, verified_at, ip_address, otp_code, web_authn_session_data) FROM stdin;
\.


--
-- Data for Name: mfa_factors; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.mfa_factors (id, user_id, friendly_name, factor_type, status, created_at, updated_at, secret, phone, last_challenged_at, web_authn_credential, web_authn_aaguid, last_webauthn_challenge_data) FROM stdin;
\.


--
-- Data for Name: oauth_authorizations; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.oauth_authorizations (id, authorization_id, client_id, user_id, redirect_uri, scope, state, resource, code_challenge, code_challenge_method, response_type, status, authorization_code, created_at, expires_at, approved_at) FROM stdin;
\.


--
-- Data for Name: oauth_clients; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.oauth_clients (id, client_secret_hash, registration_type, redirect_uris, grant_types, client_name, client_uri, logo_uri, created_at, updated_at, deleted_at, client_type) FROM stdin;
\.


--
-- Data for Name: oauth_consents; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.oauth_consents (id, user_id, client_id, scopes, granted_at, revoked_at) FROM stdin;
\.


--
-- Data for Name: one_time_tokens; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.one_time_tokens (id, user_id, token_type, token_hash, relates_to, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: refresh_tokens; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.refresh_tokens (instance_id, id, token, user_id, revoked, created_at, updated_at, parent, session_id) FROM stdin;
\.


--
-- Data for Name: saml_providers; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.saml_providers (id, sso_provider_id, entity_id, metadata_xml, metadata_url, attribute_mapping, created_at, updated_at, name_id_format) FROM stdin;
\.


--
-- Data for Name: saml_relay_states; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.saml_relay_states (id, sso_provider_id, request_id, for_email, redirect_to, created_at, updated_at, flow_state_id) FROM stdin;
\.


--
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
-- Data for Name: sessions; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.sessions (id, user_id, created_at, updated_at, factor_id, aal, not_after, refreshed_at, user_agent, ip, tag, oauth_client_id, refresh_token_hmac_key, refresh_token_counter) FROM stdin;
\.


--
-- Data for Name: sso_domains; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.sso_domains (id, sso_provider_id, domain, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sso_providers; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.sso_providers (id, resource_id, created_at, updated_at, disabled) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: auth; Owner: -
--

COPY auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at, invited_at, confirmation_token, confirmation_sent_at, recovery_token, recovery_sent_at, email_change_token_new, email_change, email_change_sent_at, last_sign_in_at, raw_app_meta_data, raw_user_meta_data, is_super_admin, created_at, updated_at, phone, phone_confirmed_at, phone_change, phone_change_token, phone_change_sent_at, email_change_token_current, email_change_confirm_status, banned_until, reauthentication_token, reauthentication_sent_at, is_sso_user, deleted_at, is_anonymous) FROM stdin;
\.


--
-- Data for Name: action_reply; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.action_reply (id, action_id, parent_reply_id, content, owner_id, created_at, updated_at) FROM stdin;
1	4	\N	Ms. Cindy say they will drop the project as the end user not agree to increase the budget for whole security system.	2	2025-08-05 09:28:33.954493	2025-08-05 09:28:33.954499
2	44	\N	We had open an WeChat group with BHJ's engineering team and had include Fu Zhong in the group. \nFu Zhong will be our representative to continue liaison with the team for project design and boom list update.	2	2025-08-05 09:36:38.233996	2025-08-05 09:36:38.234002
3	36	\N	目前N地块采用全新技术方案数字远端机重新提交给EPG向下的6家系统集成商，目前还未确定是哪家中标。	12	2025-08-11 03:40:37.501837	2025-08-11 03:40:37.501842
4	39	\N	已确定朗茂中标，设计暂时未开始！G\\M 交付压力比较大，他们暂时没有时间推进J地块	12	2025-08-11 03:41:39.601367	2025-08-11 03:41:39.601373
5	96	\N	alesandro, you still hurry to find out one real opportunity to next step then we can help you.	1	2025-09-17 01:59:43.492269	2025-09-17 01:59:43.492274
6	139	\N	this good chance to create a new budget.	1	2025-10-22 00:33:26.541629	2025-10-22 00:33:26.541635
7	138	\N	I just see the quoation total is 20k usd not is 200k rm?	1	2025-10-22 01:48:47.136871	2025-10-22 01:48:47.136876
\.


--
-- Data for Name: actions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.actions (id, date, contact_id, company_id, project_id, communication, created_at, owner_id, is_shared) FROM stdin;
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
182	2025-11-18	54	42	84	Submitted the quotation with advised higher than based price advised by Mr. Fu . \r\nCommunicate with the end user and next step they will guide TA to do registration account with the company.	2025-11-18 21:00:37.882045	2	t
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
56	2025-08-08	86	70	\N	Invited Alesandro to visit this M&E consultant for GDS project. Ms. Mimi told KTP block B & E will include security & RF design, other blocks will exlude security package due to short of manpower. Told only support GDS DC in Malaysia and do not involve in Thailand or Indonesia projects due to no counterparts support in these countries. Invite their team to visit KLCC ENGINEER Exhibition.                    	2025-08-12 03:35:47.859437	3	t
57	2025-08-12	91	54	22	Discussed with Mr. Johnson regarding their design technically and our products specification/programming. \r\nMr. Johnson keen to know more about our products detail especially in programming setting side. \r\nBeside the request for data specification for Outdoor and Wall-Mount digital type ORU, they want to know possibility to do redundancy by 2 ORUs supporting same set of antennas system. \r\nReason why the outdoor system are supporting up to 70% of coverage area and not allow to mulfunction. \r\n\r\nBeside they also query about our VSWR threshold setting in ORU and request an demonstration/training of it.\r\nWe are requesting the team to summarize all their query and write us an email directly. \r\nWill discuss accordingly with our tech-support team and plan a on-line training section with the engineer. \r\nTentatively set on coming Tuesday.  	2025-08-12 05:59:26.176803	2	t
58	2025-08-12	84	69	12	Had quoted Bandway Engineering for their tender with EPG. \r\nTheir core business are Building Automation System (BAS) which include supply and install. \r\nCurrently EPG haven't send out the new revised MTO with Digital Type system to them yet thus we are still quoting with the Analog system first.  	2025-08-12 06:22:27.368622	2	t
59	2025-08-12	53	12	8	Mr. Lee had help to get the owner endorsement for MCMC's application form and letter of consent for our frequency application. \r\nNow pending the information of site coordinate. 	2025-08-12 06:44:45.07513	2	t
60	2025-08-12	83	65	22	Talk to Mr. Zanirul and his team are now handling with PNB 118 project. \r\nHe had many experiences on land / on air application of audio system with strong technical know how knowledge. \r\nHe share his challenges facing in industries that many user also tend to have device only for communication not system. \r\nHe like to know more what we can help him in proposing solution for his customer and will set face-to-face appointment with him next week.	2025-08-12 07:46:11.462575	2	t
62	2025-08-12	92	65	31	Mr. Zaimi are in charge for their TM Iskandar Puteri Data Centre (IPDC) and currently the project are in the tier-end. \r\nShared our success story in DayOne with him and he know the project very well also. \r\nThese week he are at the site and will help to find out more information what audio system they are using. \r\n\r\n	2025-08-12 08:01:16.428118	2	t
63	2025-08-13	95	37	\N	Provide RFoF DAS training to new project engineer Shahrul that will support Eric & Reena for GDS NTP expansion. Prepared brochures & equipment price list for their submission. Discussed with Reena regarding the T&C submitted by Mr. Fu was incomplete and Dayone will not accepted these NTP-F, J, K, M, N, KTP-D & incoming KTP-C, H & J. Request to provide certified instrument to check RF coverage that they can present to Dayone.             	2025-08-19 04:28:13.591394	3	t
64	2025-08-15	96	75	\N	Courtesy visit to check Penang Airport extension and recommend to meet with Zuhairi to check any design requirement for RF. And check the project progress for Amazon & Microsoft DC @ Cyberjaya. Recommend us to follow up with Suncon for any RF request due to their ELV package exclude RF in design.         	2025-08-19 04:33:21.486805	3	t
65	2025-08-12	98	30	\N	Courtesy visit to check their projects status and told participated bidding in Kulim Infineon fabrication plant & Penang Airport extension. Already start the Amazon & Microsoft DC @ Cyberjaya construction that can recommend her senior contract manager Ms. Yap to let us follow up any requirement for RF in these DC.	2025-08-19 04:37:04.310449	3	t
66	2025-08-19	94	74	\N	Quoted to Mr. Khor and follow up with him. \r\nCurrently they he had received 2 quotation, 1 from Kenwood and 1 from us Evertac. \r\nHad shared our company position as direct manufacturer representative locally and we are focusing on system solution based. \r\nThey are submitting the proposal to main contractor 中建江山. 	2025-08-19 04:37:46.312571	2	t
67	2025-08-19	54	42	34	Quoted to Mr. Khor and follow up with him. \r\nCurrently they he had received 2 quotation, 1 from Kenwood and 1 from us Evertac. \r\nHad shared our company position as direct manufacturer representative locally and we are focusing on system solution based. \r\nThey are submitting the proposal to main contractor 中建江山. 	2025-08-19 04:41:24.720992	2	t
68	2025-08-19	97	76	\N	We have introduced and presented the Evertac solution, they welcomed our solution, and will follow up with their IT department.	2025-08-19 04:44:10.988768	9	t
69	2025-08-19	99	77	\N	They currently have an opportunity for an airport expansion project in Indonesia (the name of the airport is still a secret), Mr. Joestian will try to inform and propose to end users to use the Evertac solution.	2025-08-19 04:57:09.291738	9	t
70	2025-08-19	100	78	\N	They currently have a mining project opportunity for the conveyor crossing tunnel, and also an apartment project with a blind spot in the basement, interested in trying to apply for the Evertac solution.	2025-08-19 05:07:38.645189	9	t
71	2025-08-20	91	54	22	Had answer Mr. Johson queries regarding our NetFlex's Network Monitoring System setting, Digital Wall Mount Outdoor ORU, cascade/ daisy chain of the oru, Redundancy on 2 ORU supporting 1 set of antennas, Tuning of ORU power output. \r\nToday afternoon they will have solution proposal presentation with client and we will follow up again with the team after that. 	2025-08-20 01:48:02.493853	2	t
72	2025-08-22	\N	46	13	目前和LM采购建立了联系，图纸深化和报价已经完成	2025-08-22 04:37:13.843421	12	t
73	2025-08-25	94	74	34	Mr. Wei Lee the sale and marketing manager had requested references quote from Triple Access for Motorola's Repeater and Walkie Talkie. \r\nHad confirm with Mr. Khor that they are submitted using our pricing to CCYR (Main Cont). \r\nWe also had submitted our refine proposal of RFOF DAS system and overall boom list to Mr. Khor. \r\nCurrently CCYR still in the tender stage with the owner and we will approach CCYR to gain more information. 	2025-08-25 09:36:33.092867	2	t
74	2025-08-25	70	55	32	Had discuss with Mr. Surasak regarding with our demonstration proposal. \r\nThe proposal include combination of 1 Motorola repeater and 1 Evertac Repeater together with our NetFlex dashboard software. \r\nMr. Surasak had concern the integration regarding the CP/IPSC/LCP/CAPMAX ( MOTOTRBO) sets up of the network and radios, PC‑based dispatch management application  TrboCare /Smart Ptt/WavePTX. \r\n\r\nHad explain to him what are the main differences between Motorola's dispatch software with Evertac's NetFlex.	2025-08-25 09:42:42.073234	2	t
75	2025-08-26	102	84	\N	Courtesy visit to this Data Centre specialist and present our DAS to support their design to DC RF system. They more focus to M&E package and recently participate few design bidding DC in Johor but temporary no convenient to disclose project name. Told our RF package will under their SI Willowglen for security package.	2025-08-26 06:38:15.889268	3	t
76	2025-08-18	20	30	\N	Present our RFoF DAS for and DC projects reference to Ms. Yap and highlight our roles that can suppport them for RF design, budget & technical proposal during DC bidding stage. And able to integrate Motorola in our system to assist for signal coverage. Told will request her procurement team to check any RF request in Amazon & Microsoft DC projects that we can quote & supply. 	2025-08-26 06:39:44.151988	3	t
77	2025-08-21	104	22	\N	Courtesy visit to present our RFoF DAS system and follow up Edgeconnex Data Centre @ KLCBD. Told this expansion project DC hall was pending for design review but they are submission consultant and overall design & spec request will come from from US. Told we can follow up with their team to check any design request for project NTT Global Data Centre @ Johor & Zdata Gyperscale DC @ Johor.	2025-08-26 07:43:52.466146	3	t
81	2025-08-27	54	42	34	Had bring Yusry to meet up iFlyTek Mr. Wei Lee and Mr. Khor for the project discussion. \r\nTheir company culture is preferable to liaise directly with principle/manufacturer and we had explain to the team how our business mode and operation pattern. \r\nHad emphasize again the importance of Local Type Approval and System Assurance fulfill the project requirement. \r\nAs discussed, they are foresee these project to be finalize by end user on Quoter 4 2025. \r\n	2025-08-27 01:45:14.700209	2	t
82	2025-08-27	91	54	22	Followed up their meeting with PNB118 and TM Technology last week. \r\nAt the moment , Mr. Johnson feedback client are satisfy with our products feature and their design concept. \r\nAs told TM Technology eventually will own all the devices and listing to PNB118 via contract. \r\nTheir current planning for deployment are by zone( set of ORU with the corresponds antennas system ）  meaning there will be few time shipment .\r\nAs practice they company will have final inspection / factory acceptance test for every project and we had advise it can be done at China or Singapore before shipment.	2025-08-27 01:53:47.95475	2	t
83	2025-09-02	107	93	\N	I've introduced the company, products, and the Evertac Solution system to Mr. Handoko (who is in charge of the airport electronics division) via WhatsApp. I'll follow up to get an email and an appointment to present the Evertac Solution online or offline.	2025-09-02 09:03:32.898557	9	t
84	2025-09-02	\N	90	50	Currently, I am following up with the consultant to ask about the radio frequency system there and get a layout drawing that we will try to submit the Evertac system through the consultant. I have made an appointment with them on Wednesday afternoon.	2025-09-02 09:05:59.420394	9	t
85	2025-09-02	100	78	\N	For both projects, we are still following up to request the layout.  PT. Dwi Candra Teknologi (Mr Candra) currently trying to request the layout from the end user.	2025-09-02 09:20:03.987564	9	t
86	2025-09-02	108	92	\N	Mr. Asep, as a consultant, suggested that if you want to participate in a tender package, the consultants must submit several documents to the end user, including:\r\n1. Technical specifications,\r\n2. Single Line Diagram (general, but please provide details for cables),\r\n3. Datasheets\r\n\r\nThis data will be submitted by the consultants to the end user for the project they are supporting.	2025-09-02 09:48:13.304552	9	t
87	2025-08-28	109	94	\N	Courtesy visit and checked their project status to data centre & industrial projects. Told one the DC project was Equinix Data Centre @ Johor will complete end of this year. After that 2nd phase Equinix DC @ Cyberjaya will start early 2026. They are submission consultant to these 2 projects and exclude RF package in design and advise us to follow up with maincon Shimizu.	2025-09-02 14:32:04.929909	3	t
88	2025-08-29	6	22	48	Informed that we have supplied RF system to GDS & Bridge DC that investors came from China. Their operation team familiar with RF wireless intercom and we used RFoF DAS system to fulfilled their higher demand to security communication & full signal coverage. Checked this 中联数据 ZData GP3 Hyperscale DC @ Johor and told this ZData land size around 38 acres and planning for 5 data halls around total 200 MW and 1st block structure will complete end of this year but they are submission consultant and design involed in high power systems to handle the main electrical distribution. Regarding the ELV & surveillance system that we can check with CCIE or ICT SI company call CET to clarify any RF requirement due to end-user direct award to them. 	2025-09-02 14:34:14.496956	3	t
90	2025-09-03	111	65	22	Talk to Ms. Nurshaliana the project manager for PNB 118. \r\nIntroduce our position as manufacturer to support O'Connor for the audio system and invited her to visit our exhibition. \r\nKnowing Mr. Nurshaliana not very familiar with the Distributed Antenna System and explain our structure design and redundancy can be made with her. 	2025-09-03 01:19:22.018073	2	t
91	2025-09-03	92	65	31	Understand from Mr. Zaimi currently the IPDC 2 blocks datacenter only using point-to-point communication (Motorola) and relatively coverage is accepted as area of premise not big. \r\nThey are buying from Centrix Engineering and will create opportunity to approach the company to find out more. 	2025-09-03 01:25:50.776537	2	t
92	2025-09-09	112	90	\N	He wants to help us incorporate the Evertac solution into future projects. He will assist us from the beginning in proposing the Evertac solution to the owner or end user.\r\nSimilar to Mr. Asep from PT. Meltech Consultindo requested the following:\r\n1. Technical documents\r\n2. Single line diagram (SLD)\r\n3. Indonesian government permit documents \r\n\r\nAfter receiving these documents, Mr. Endang asked us to present the entire Evertac solution. The presentation would be conducted in Malay/Indonesian only. They are ready for an online meeting every Monday or Tuesday from 10 AM to 12 AM.\r\n	2025-09-09 02:51:01.563041	9	t
93	2025-09-09	\N	90	50	Mr. Endang is waiting for the required data, namely:\r\n1. Technical documents\r\n2. Single line diagram (SLD)\r\n3. Indonesian government permit documents\r\nand our presentation.\r\n\r\nAfter that, if it's still possible, he will try to propose the Evertac solution to the Yellow Stone data center project.	2025-09-09 03:15:17.86346	9	t
94	2025-09-09	108	92	\N	Mr. Asep is still waiting for the requested documents for them to study.	2025-09-09 03:22:00.519579	9	t
95	2025-09-09	107	93	\N	Still following up to get an appointment with Mr. Handoko, because Mr. Handoko's schedule is very busy, I pushed to be able to meet him.	2025-09-09 03:28:51.62535	9	t
96	2025-09-16	113	95	\N	I met with Mr. Widodo, I introduced myself, introduced the company, product and system of Evertac Solution. For Mr. Widodo, this is a new system, quite interesting and just like other consultant friends, asked for several documents to be studied further, such as Single Line Diagram, Technical Specifications and data sheets that they will bring to the end user to try out this Evertac Solution system.	2025-09-16 09:20:10.368935	9	t
97	2025-09-03	114	34	48	Courtesy visit and follow up BDC MY02. Wu told the structure for block 1 power station almost complete and block 2 Data Hall still in progress. Already secured Block 3 Data Hall but waiting design amendment from 2 floors increased to 3 floors to comply tenant requirement. Zdata that checked with his team and informed end-user already took out the RF due to full wifi coverage.	2025-09-16 12:16:07.91216	3	t
98	2025-09-23	112	90	\N	We presented the overall Evertac solution, including data center and industrial systems. Roy assisted with the presentation. Mr. Endang asked us quite a lot of questions. They also informed us about several factory projects. I'll plan to meet with Mr. Endang again this week.	2025-09-23 09:44:44.829786	9	t
99	2025-09-23	\N	90	50	During yesterday's presentation with Mr. Endang and the team via online meeting, we asked about this data center project, Mr. Endang responded that it was not possible for Evertac Solution to enter this data center project, on the grounds that the project was already underway, it was too late to enter. Mr. Endang suggested communicating directly with the end user to offer this Evertac solution.	2025-09-23 09:51:47.85444	9	t
100	2025-09-23	107	93	\N	Mr. Hondoko responded to my WhatsApp chat, but he informed me that he no longer handles this radio frequency communication system. I'm currently inquiring about who will handle this matter. I'm still waiting for a response from Mr. Handoko.	2025-09-23 10:00:04.951466	9	t
101	2025-09-23	118	97	\N	Mr. Kuan is interested to know more about our system and products. \r\nHad invited him to our office to explain further our system design and solution that can propose to his clients. 	2025-09-23 18:12:57.536778	2	t
102	2025-09-22	120	34	48	Met their project team 焦洋 and informed that we are support CCIE in BDC MY02 and explained necessity RF system in DC. Told ZData Centre's RF package already withdraw from CCIE package and will let operation team to decide once DC operated. He will check with the end-user team in next week and try to arrange our presentation to convince the end-user. 	2025-09-24 01:24:52.596273	3	t
103	2025-09-18	85	37	\N	Reena told Eric resigned during end of Aug and temperary she will take care his roles in GDS DC and told Longmotive already provide the spectrum analyzer to check GDS DC signal strength and her site also will follow them to varify the performance. But end-user already appoint NV5 as checker.                                            	2025-09-24 01:26:21.225514	3	t
104	2025-09-19	109	94	\N	Courtesy visit to checked GDS DC progress and update Mr. Hadi that we are RF system supplier and willing to support them for RF performance T&C or any technical clarification.  	2025-09-24 01:27:23.201363	3	t
105	2025-09-24	\N	46	13	RAFA Technology Co., Ltd and Ablelink (Thailand) Company Limited sourcing for pricing. \r\nRAFA are the main contractor and Ablelink is their SI. \r\n付总say on-hold first the submission and wait for their final price to LongMotive as there are revision in pricing. 	2025-09-24 02:37:12.819049	2	t
106	2025-09-24	106	74	34	童总main procurement manager from HQ and 娜总APAC procurement manager together with the team visited Triple Access for meeting. \r\nThe main purpose of meeting is to know the relationship between Motorola and Evertac in malaysia cooperation relationship.\r\nFrom the meeting we also know that the main contractor CCYR are still revised the design on all ELV package and forecast design will only be finalized end of these year or early of next year. 	2025-09-24 02:45:26.39149	2	t
107	2025-09-23	128	105	\N	Follow up the Genting facilities team Mr. Farid's info that Genting resort having RF signal coverage problem for their operation & security team. Daniel told Genting Resort previous facilities VP used rental basis from Johor vendor Ace Sonic Communications provided POC with brand name Easytalk that parellel import from China but facing a lot signal coverage problem. We can partnership with Daniel to propose our design concept to upgrade their overall hotels & casino building.                        	2025-10-01 01:29:30.386891	3	t
109	2025-10-01	127	39	34	Had talk to 张总 the project manager and as discussed they are not officially awarded the project yet but having high chance as they are close to end user. \r\nTentatively according to 张总 the end user will finalize the design these month and PO will be issue out before end of the year. \r\n张总is based in Johor now and will plan a trip to visit him accordingly to understand more the project progress. 	2025-10-01 01:34:11.578401	2	t
110	2025-09-26	131	106	\N	Courtesy visit and checked any inquiry after exhibition. Told that they just completed one block Aims DC @ Cyberjaya and maincon is Gamuda Eng. Told this DC exclude RF in design and usually Aims DC will let the operation team to purchase the two-way radios. 	2025-10-01 01:39:16.589536	3	t
111	2025-10-01	94	74	34	Talk to Mr. Khor saying the main con are souring price through other sub-con and pushing him to bring us to main cont/end user for presentation. \r\nMr. Khor say currently the end user others ELV package still got many changes and radio system is not their priority concern yet. \r\nLet them finalize other ELV package first then they will bring up the radio package re-design concern.\r\nBasically they are having close contact with the main cont and foresee having higher chance to win the project by them. 	2025-10-01 01:40:51.109786	2	t
112	2025-09-24	132	107	\N	Recommended by BCI Peggy and Andrew told they are security locking & access control vendor. Told previous supplied security locking system to Microsoft DC through SI.	2025-10-01 01:43:04.981649	3	t
113	2025-10-01	126	42	66	Join visit with Fizwan to visit the customer for proposal radio solution. \r\nCurrently they are using LTE radio for communication and having problem in enclose space or inside the lift. \r\nExplain the differences concept of radio communication via LTE with RF. \r\nThey are interested with RF solution and the only concern is the budget. \r\nHad request them to find out how many budget will cater for these upgrading then we will propose the solution accordingly. 	2025-10-01 01:46:05.863345	2	t
114	2025-09-26	85	37	14	Checked operation team contact with Reena & Chris and told that they are difference blocks might have difference team to handle and they only had design team contact with end-user. Told still hold the T&C approval to block F that EPG still refuse to present the heatmap for signal coverage.  	2025-10-01 01:51:00.418044	3	t
115	2025-10-01	126	42	52	Currently on end user hand there are 3 quotation , Triple Access and Vertex is using our solution but stream communication using other brand. \r\nWill try approach end user to do presentation and explain the total solution we can provide to end user. 	2025-10-01 02:38:53.633797	2	t
116	2025-10-01	\N	78	59	There have been no updates so far. I've requested a meeting with PT. Citradata's sales representative, Mrs. Ajri, to schedule a meeting with the director of PT. Dwi Candra, Mr. Chandra, as she's in charge of this project. Mrs. Ajri will inform me when a meeting with Mr. Chandra is scheduled. She's currently arranging the schedule.	2025-10-01 03:10:50.596435	9	t
117	2025-10-01	\N	90	50	I've asked the consultant, Mr. Endang, for the owner's contact information. However, Mr. Endang said they aren't directly connected to the owner. They're under an architect. The main architect is from Korea, but there is a local architect, PT. Domus Arsitektur Indonesia	2025-10-01 03:13:07.223266	9	t
118	2025-10-02	137	108	\N	Had do presentation with the Digital Solution team regarding the radio system setup and our products. \r\nTheir business are more to oil and gas application and will follow up again to seek business opportunities. \r\n	2025-10-02 02:23:32.194938	2	t
121	2025-10-07	139	109	50	We have sent an email introducing the company to Mr. Moonsun Song, and also requested a schedule to meet via online meeting for further introduction and to ask for his direction in providing the SMX-01 Yellowstone Data Center project in Jakarta.	2025-10-07 10:01:31.235074	9	t
122	2025-10-07	100	78	59	I've communicated directly with the director of PT. Dwi Chandra Teknologi, Mr. Chandra. We were scheduled to meet this Tuesday, but it's been rescheduled to Wednesday, after lunch. I'll check directly with him to see what the status of this project is and what the update is.	2025-10-07 10:07:13.560252	9	t
123	2025-10-07	141	110	68	Mr. Andi is the PIC for the MEP department on another project. I'm currently asking him about the PIC for the BYD project and the Hiron Tuban project. So far, I haven't received a response from him. I'll try pushing and calling him directly.	2025-10-07 10:19:28.317007	9	t
124	2025-10-07	141	110	69	Mr. Andi is the PIC for the MEP department on another project. I'm currently asking him about the PIC for the BYD project and the Hiron Tuban project. So far, I haven't received a response from him. I'll try pushing and calling him directly.	2025-10-07 10:21:24.642018	9	t
125	2025-10-14	145	113	71	We met with Mr. Hendry, the Engineering Manager, and presented Evertac. He was interested and asked for a trial in his building, while we offered our system. We're waiting for their layout drawings.	2025-10-14 02:20:56.435563	9	t
126	2025-10-14	100	78	\N	I've met with Mr. Chandra in person regarding the Tunnel project, which is currently pending and will likely be continued next year due to budgetary constraints.\r\nMr. Chandra will introduce me to his users to give a presentation about Evertac. The schedule will be announced later.	2025-10-14 02:27:48.693778	9	t
127	2025-10-03	29	33	60	Sent the moon cake to Wong and checked BDC progress. Told that haven't receive the block 3 DC hall amendment from 2 floors to 3 floors and phase 2 still in preliminary stage that haven't start the design. 	2025-10-14 06:56:47.963162	3	t
128	2025-10-03	85	37	\N	Sent the moon cake to Reena and checked her work progress in GDS. Told that busy to take over Eric's site work that a lot incomplete documents that have to follow up. Especially EPG block F that Eric issued CCC approval does not fulfilled tender spec requirement.	2025-10-14 06:59:00.600198	3	t
129	2025-10-02	147	116	\N	Follow up their planning to build for a Data Centre and told they had reserved agricultural land (Palm Tree) more than 1000 acre in Perak and government allow them to convert partial land development to Data Centre & energy renewable plant. But this planning still in preliminary stage and haven't proceed to appoint design consultant due to their marketing team still looking for potential MNC achor tenant. 	2025-10-14 07:06:22.756681	3	t
130	2025-10-01	148	117	\N	Courtesy visit to follow up after exhibition and Ms. Aina told previous their company took a lot commercial & residential project but recently this market slow down and they will bid for Data Centre projects but still in confidential stage & not sure package include security & RF or not.	2025-10-14 07:19:00.242824	3	t
131	2025-10-07	149	118	\N	DC consultant & service provider for cooling system, fire supression & security monitoring. Told her department more in system service & support. Recently received Mid Valley inquiry for RF signal coverage problem that we can support them to propose a solution. Regarding new project bidding will under his boss control and no details info about it. 	2025-10-15 01:26:59.765953	3	t
132	2025-10-10	150	119	\N	Courtesy visit to checked their project status. Told during year 2023 completed BDC MY06 @ KIDEX (Sedenak Tech Park) 3 data halls with total capacity around 100MW but recently failed to continue & most of BDC projects secured by CCIE. Now working on Mercury data centre @ Johor with 2 blocks of data hall and this project under Woh Hup Malaysia-IJM construction joint venture.	2025-10-15 01:38:07.202195	3	t
133	2025-10-15	100	78	59	Mr. Cahandra is still scheduling an introduction to his users.\r\nStill waiting to schedule a meeting with a potential user who needs an Evertac.	2025-10-15 02:54:46.475128	9	t
134	2025-10-15	139	109	50	I have also sent an introductory message via WhatsApp, but Mr. Moonsun Song is still slow to respond, he hasn't replied to my message.	2025-10-15 02:58:07.745713	9	t
135	2025-10-16	\N	39	34	The construction had start but CCYR's only awarded 2 block accordingly to 张总and remaining 3 block is built by other main contractor. \r\nFor our radio package so far R&F owner didn't raise up or appoint who to awarded to. \r\nCCYR advise us to approach R&F owner directly and raise our concern as the coverage and deployment will include all 5blocks. 	2025-10-16 05:49:53.439483	2	t
136	2025-10-16	111	65	22	Follow up with Ms. Nurshaliana and currently the project will on-hold as 2 concern change in design. \r\n1st the owner would like change from current DMR into TETRA system \r\n2nd they would like to expand the coverage into shopping mall and residential area. \r\nCurrently Ms. Liana are accumulate the information and integrate accordingly with 2 more PIC on shopping mall and residential area. \r\nHad explain to Ms. Liana saying that our design infrastructure not only can support both system but can consider the expansion plan in future.  	2025-10-16 05:55:22.074026	2	t
137	2025-10-16	122	101	63	Join visit with TA's sale person to the end user and found they have difficulty in radio coverage in parking area and Telco signal also very poor. \r\nWe will craft out a preliminary design plan and submit commercial proposal for Mr. Jack to request budget upgrading from point-to-point into system.  	2025-10-16 05:58:43.436984	2	t
138	2025-10-21	122	101	63	Had further communicate with Mr. Chan regarding his request of proposal in upgrading the radio system. \r\nWe had share our preliminary design consist of 18indoors antenna + 1 outdoor antenna complete with 1 unit repeater for overall 3 floors of the premise with total estimated budget Rm 200K. \r\nNext he will seek budget from management and will follow up with him again . 	2025-10-21 03:26:44.723352	2	t
181	2025-11-17	170	134	\N	We conducted a visit to the office of PT. DCI Indonesia Tbk and met with Mr. Ervin Andriana Taufik, the NOC Manager, along with his team. The meeting was also attended by our distributor, PT. Citra Data.\r\n\r\nDuring the session, we introduced our company profile and delivered a general presentation about Evertac Solutions, covering key capabilities, value propositions, and implementation areas, particularly in data center environments.	2025-11-18 20:34:00.552776	9	t
139	2025-10-21	121	99	61	Meeting up with the Mr. Hisyam and Mr. Harith the team of facility engineering maintenance services to introduce our products and solutions. \r\nCurrently they are using motorola XiR P8620 model combination with 1 repeater together with Mobile Radio on vehicle and centralize on Wave PTX platform for whole team communication. \r\nOn the UMSC's HQ office they are emitted the coverage through 1 outdoor antenna only for remaining few block premise own by them for communication. \r\nNext year they are planning to have new build block and would like to extend the coverage into the building as well as planning to improve the coverage blind spot in current building that faced. \r\nWe had explain our products capability in integration with existing system and expandability for future coverage need. \r\nWill organize another meeting with the team again for solution presentation next.  \r\n 	2025-10-21 04:06:55.320996	2	t
140	2025-10-22	\N	\N	61	if you identify this opportunity is a right chance and decide to follow up, you need to set the stage to embedding.	2025-10-22 00:36:29.934386	1	t
141	2025-10-17	152	121	\N	Present our RFoF DAS provide RF signal full coverage to upgrade DC security level & communication efficiency for operation. Told Menara Aims @ KL used Motorola two-way radio and last 2 years add repeater to improved their signal coverage. 	2025-10-22 01:18:39.441842	3	t
142	2025-10-22	145	113	71	Mr. Hendry will send the floor plan this afternoon. After receiving the floor plan, we will design the Evertac solution.	2025-10-22 02:23:10.690499	9	t
143	2025-10-22	100	78	59	Mr. Candra is still arranging to meet with his end users. Mr. Candra will provide the update information soon.	2025-10-22 02:36:30.779834	9	t
144	2025-10-22	155	65	22	Communicated with Pak Jad who are specialize advise radio communication solution to TM Technology project team. \r\nWas general introduction regarding our products range and integration capability through phone. \r\n 	2025-10-22 02:51:54.046719	2	t
145	2025-10-23	156	69	\N	Discussed for ZData GP3 hyperscale DC @ Nusajaya Industrial, Johor and told that each block had 3 floors for DC halls and whole project had 5 blocks DC. They secured 1st phase Block 1 & 2 and overall design will request 6 channels with each repeater had backup unit (Total 3+3 repeaters). We will proposed Block 1 to let them apply approval with Zdata before proceed to purchase negotiation and end-user request partial completion end of this December.	2025-10-28 06:32:46.788185	3	t
146	2025-10-24	157	37	\N	Discussed with Krisnaa (Senior Technical Manager) regarding their question & pressure received from QS & operation team ask about Evertac not in theGDS project brand list. Already briefed our recent support EPG for T&C to block F, G, H & M and their upcoming site meeting with Dayone operation head Dharmendran and unlikely will complaint about our Evertac system.        	2025-10-28 06:37:12.978215	3	t
147	2025-10-22	153	121	\N	As per previous arrangement request by facility director Mr. Lim to present our RFoF DAS system to their security team to let them to liase with Aims Cyberjaya and told Cyberjaya site had 3 blocks that A & B already completed with Motorola radio & repeaters and will check with block C status and any coverage problem that we can follow up.	2025-10-28 06:46:05.239161	3	t
148	2025-10-28	140	88	50	After we tried to communicate with the end user, Mr. Moon Sunsong, but it was a bit difficult, I tried to meet with Mr. Jonan, Chief Estimate of PT Acset Indonusa Tbk, the main contractor on this project. I talked about Evertac and sought information regarding the Yellow Stone project, especially regarding radio communication in the project. Mr. Jonan recommended meeting with his team at the project site. Mr. Jonan will arrange to meet with his project team there.	2025-10-28 12:42:45.336543	9	t
149	2025-10-28	159	126	\N	I met Mr. Kent, we talked about the BYD and Hiron projects, where they are subcontractors of PT. China State Construction for both projects. I inquired about radio communications there, but Mr. Kent didn't know about them. Mr. Kent will try to ask his team on site, later his team on site will inform us about the radio communications and help us find the PIC of the main contractor, PT. China State Construction for both projects.	2025-10-28 15:00:12.122333	9	t
150	2025-10-28	145	113	71	I have coordinated again with Mr. Hendri, Mr. Hendri did give a statement that the floor plan drawing would be sent last week, but until this week we still haven't received the floor plan drawing, I confirmed that it turns out the floor plan drawing is currently being searched for by his team and is currently sorting and tidying up the floor plan drawing, we should be able to get the drawing this week.	2025-10-28 15:17:39.642933	9	t
151	2025-10-29	74	60	79	Understand from Ms.Tan that they are awarded the project and design was been approved.\r\nHad communicated with Mr. Chung too as they understand the project will have expansion plan in future. We had  explain and recommend our OMU & ORU to him which are suitable products for expansion plan later.   	2025-10-29 01:41:41.997931	2	t
152	2025-10-29	159	126	68	I met with Mr. Kent and we discussed the BYD and Hiron projects, both of which are subcontractors of PT. China State Construction for both projects. I inquired about radio communications there, but Mr. Kent was unaware of them. Mr. Kent will try to inquire with his team on site, who will then inform us about the radio communications and help us find the PIC of the main contractor, PT. China State Construction, for both projects.	2025-10-29 02:08:20.399595	9	t
153	2025-10-30	160	126	\N	The meeting with Mr. Dhimas went well and was conducted in a positive and open manner. PT Shunrong showed a cooperative attitude and willingness to assist in the introduction process to the main contractor, PT China State Construction, as an initial step toward exploring potential collaboration opportunities in the BYD Subang project.	2025-11-04 17:11:26.304667	9	t
154	2025-11-04	160	126	68	The meeting with Mr. Dhimas went well and was conducted in a positive and open manner. PT Shunrong showed a cooperative attitude and willingness to assist in the introduction process to the main contractor, PT China State Construction, as an initial step toward exploring potential collaboration opportunities in the BYD Subang project.	2025-11-04 17:13:46.423129	9	t
158	2025-11-04	145	113	71	Communication with Mr. Hendry A. Hermawan has been positive and ongoing; however, the floor layout promised has not yet been provided.\r\nFurther follow-up and confirmation are required to proceed with the technical analysis and proposal preparation for the Tzu Chi Hospital Project.	2025-11-04 18:00:54.713076	9	t
159	2025-11-03	100	78	59	Based on the communication with Mr. Candra (PT Dwi Chandra), the Kalimantan Tunnel Project is currently on hold and scheduled to be included in the 2026 budget plan.\r\nWe will continue to monitor progress and maintain regular contact in preparation for project reactivation next year.	2025-11-04 18:14:02.26025	9	t
160	2025-10-31	140	88	50	I met again with Mr Johan. The meeting with Mr. Johan (PT Acset) was productive and informative.\r\nHe provided clear guidance to coordinate directly with the Procurement Manager of SMX01 (Mr. Asep), even though his contact information is not yet available.\r\nWe will proceed to obtain the necessary contact and arrange a meeting with the SM+ procurement team as the next step in exploring potential collaboration for the SMX01 Data Center Project.	2025-11-04 18:22:21.838726	9	t
161	2025-10-30	157	37	\N	Request meeting to solve the GDS problems and promised that we will arrange our technical team to fix the repeater setting for Dayone NTP Block F and will remind EPG again regarding the installation antennas into the facilities containers to improve signal coverage. Told Dharmendran under operation HOD Gavin that handle KTP and will request follow the brand white list and change to Motorola for the following blocks. Checked Krisnaa recent project and told beside GDS and busy with KL Midtown mixed development that under JV of Hap Seng & Naza TTDI.  This is a mixed development with 5 stars hotel, offices, retail, urban park, leisure, and serviced residential, located in Kuala Lumpur's KL Metropolis, near Jalan Duta. But this security design excludes RF and will let the tenants to decide their requirement.                     	2025-11-05 01:38:20.797868	3	t
162	2025-10-30	32	37	\N	Met with Azri and checked any key person contact for YTL Data Centre operation team that we can present our RF system. Told that still work with the project team and foresee these DC will use YTL Yes Telco company owned by YTL to setup their communication system with 4G, 5G and even RF system.                     	2025-11-05 01:41:07.000597	3	t
163	2025-10-29	156	69	\N	Request to quoted Zdata with Motorola repeaters, walkie talkies & installation (Total RM 1,131K) for their submission to CCIE for budget approval.             	2025-11-05 01:44:02.593786	3	t
164	2025-11-05	122	101	63	Visited Mr. Chan together with TA's Fitzwan to do site testing for coverage and follow up on the budget cater for these project. \r\nThey only had less budget these year ~Rm30K for the upgrading. \r\nFrom site survey, we understand the center park of building having big issue of coverage and car park area. \r\nMr. Chan also share with us that others Columbia hospital also having the same issue. \r\nThey already bring up these issue to headquarter and we are pushing him create a opportunity for us to present our solution in headquarters.  	2025-11-05 02:06:54.647411	2	t
165	2025-11-05	126	42	52	Do presentation to the operating team and purchasing team about our solution. \r\nMs. Erra are happy and understand our products capability and she will organize another meeting with engineer as we request it. \r\nAs explained at the moment we are only receive the boom list thus we would assist the team in design too.  	2025-11-05 02:12:52.875261	2	t
166	2025-11-05	62	50	61	We understand that previously these client was serve by SLW and client also had close relationship with the company. \r\nHad communicate with Mr. Andrew and understand Ms. Shida are the PIC sale project engineer. \r\nWe are communicate with Ms. Shida and next will join visit with her to client site to understand more the detail and potential of these opportunities.	2025-11-05 02:17:39.338129	2	t
167	2025-11-05	55	43	\N	Approach Mr. Matthew to create more cooperation opportunities and planning to appoint the company as our direct agent and partner.\r\nUnderstand from Mr. Matthew they are more focusing on hospitality industry. \r\nPreviously they had also come across with BDC and DayOne opportunities but loss. They also would like to know more how can our products technology provide the solution needs in DC and had we had do presentation to the team. \r\n\r\n	2025-11-05 02:23:22.576406	2	t
168	2025-11-05	74	60	\N	Talk to Ms. Tan for our future cooperation opportunity as agent.  \r\nThey had clear they position as will focusing on Oil & Gas industry and show very interested with our program. \r\n	2025-11-05 02:28:13.800101	2	t
169	2025-11-05	62	50	\N	Meeting with Mr. Andrew discuss about the future cooperation opportunities as agent / partner. \r\nMr. Andrew did not specify which industry they are targeting now but they are keen to represent us as after sale service team. \r\nHe hope we could organize a proper seminar or training outside not in TA office. 	2025-11-05 02:32:37.740414	2	t
171	2025-11-10	165	130	\N	I have already communicated with Mr. Hendri. A meeting will be scheduled next week for the introduction of Evertac. He confirmed that he is not available this week. They have several industrial estates across Indonesia, which presents a good opportunity for us to get involved in their projects. We will further explore the potential opportunities that may arise.	2025-11-11 13:46:50.249473	9	t
172	2025-11-07	145	113	71	I have received the drawings related to the Tzu Chi Hospital Project from Mr. Hendry A. Hermawan. However, the files provided were not floor-by-floor layouts, but only general project drawings.\r\nI have confirmed with Mr. Hendry A. Hermawan that the drawings sent were not accurate, and have requested the correct floor layout drawings of the building. The requested file formats are PDF or AutoCAD (.dwg) so that they can be used as technical references and for further analysis.\r\n	2025-11-11 15:24:23.007366	9	t
173	2025-11-06	140	88	50	On November 6, 2025, I had a follow-up communication with Mr. Johan from PT. Acset Indonusa Tbk, the Main Contractor for the SMX01 Project.\r\nDuring the discussion, I received the project layout drawing for SMX01, which will serve as an initial technical reference for further analysis and preparation to introduce Evertac Solution to the project.\r\n\r\nHowever, I have not yet obtained the contact information of Mr. Asep, who serves as the Purchasing Manager of PT. SMX01 (SM+).	2025-11-11 15:46:20.576356	9	t
174	2025-11-11	159	126	68	I had a follow-up meeting with Mr. Kent from PT. Shunrong regarding the BYD Subang Project.\r\nDuring the meeting, Mr. Kent provided the contact of the End User, obtained from his field team:\r\n\r\nName: Ms. Noviyanti Gouw\r\nPosition: Project Specialist	2025-11-11 16:29:24.69336	9	t
175	2025-11-12	74	60	79	Ms. Tan had help us successfully spec in our OMU & ORU into the project for future expansion. \r\nNext we will organize an discussion meeting with Mr. Chung the technical person and explain how the expansion to be design. 	2025-11-12 01:22:23.114303	2	t
176	2025-11-12	163	129	53	They had request for top-up 10unit walkie-talkie and had discuss with Mr. Fu. \r\nMr. Fu agree we using our local company to quote to the user as requested by Mr. Dharmendran. \r\nPending advise how much quoted price to user by Mr. Fu. 	2025-11-12 01:25:59.348608	2	t
177	2025-11-05	6	22	48	Follow up these 5 blocks DC for Zdata Centre GP3 and told this block 1 structure almost complete but their desing only involve in high power supply & main electrical distribution. Informed that ELV, ICT, Surveillance System and our RF proposal have to direct follow up with CCIE's PM 焦洋. Highlight RF type approval to prevent China SI parallel import RF equipment that illegal and leading fines max 100K and 6 months jail for the end-user.	2025-11-12 01:32:32.875709	3	t
178	2025-11-06	114	34	\N	Checked with CCIE's PM Mr. Wu(吴锋艳) regarding any SI or key person contacts for Zdata DC beside 焦洋 but informed that his team only handle BDC MY projects and not direct related to Zdata DC and advice us tightly follow up with PM 焦洋.        	2025-11-12 01:34:04.220478	3	t
179	2025-11-07	120	34	48	Called and checked again with CCIE's PM 焦洋 to offered our RF equipment provide local ceritifed supply to his China SI. Told this block 1 having design amendment and has not award to any SI yet and we can follow up end of Nov and quote to Bandway Eng for submission. 	2025-11-12 01:35:09.448842	3	t
180	2025-11-07	169	133	\N	Courtesy visit to Ronny and checked the Zdata Centre DC project status. Told previous quoted RF to his SI and told info from his SI informed this project quoted RF equipment supply and install to China contractor and not direct quote to CCIE. But his SI has not receive any confirmation due to a lot amendment still pending.	2025-11-12 01:39:51.752208	3	t
183	2025-11-13	165	130	\N	I conducted a follow-up communication with Mr. Hendri regarding the scheduling of our upcoming meeting.\r\nHe informed that the meeting schedule is currently being finalized internally and will be confirmed within this week. The tentative plan is to hold the meeting between Thursday and Friday, and he will provide the exact time once confirmed.\r\n	2025-11-18 21:14:46.73015	9	t
185	2025-11-13	145	113	71	Following the previous communication and the request for the correct floor-by-floor layout drawings, I conducted another follow-up through WhatsApp messages and attempted to call Mr. Hendry A. Hermawan. However, he has not been able to respond, as he is still unwell and has not fully recovered. This situation has delayed the process of obtaining the correct layout drawings needed for the next phase of the project.	2025-11-18 21:51:06.895734	9	t
186	2025-11-18	166	131	68	I have contacted Ms. Noviyanti Gouw via WhatsApp to introduce myself and begin the initial communication regarding the BYD Subang Project. In the message, I provided a brief introduction and conveyed the purpose of reaching out, which is to discuss the potential implementation of Evertac Solution for the project.\r\nAt this stage, we are still waiting for her response. We hope to receive a positive reply so that we can proceed to the next step, which is scheduling a meeting or presentation to review the communication requirements and explore the integration opportunities for Evertac Solution in the project.\r\n	2025-11-18 22:05:24.724567	9	t
187	2025-11-18	33	28	48	Currently there are 3-4 company tendering the project directly to CCIE.\r\nBelieve Vertex's SI tendering through YSC and Fu Zhong receive MTO from YSC are similar MTO. \r\n	2025-11-18 22:33:17.103441	2	t
188	2025-11-18	53	12	54	DayOne had raise complain that our OMU having problem causing whole system breakdown. \r\nUnderstand that for these deployment they didn't use uplink & downlink splitter and suspect these cause our OMU can not function well as direct input power too high. \r\nThe team will further testing and investigate again. \r\n	2025-11-18 22:40:31.262714	2	t
189	2025-11-18	53	12	8	Support re-write approved frequency into the system together with TA's yusry at site.	2025-11-18 22:42:07.199614	2	t
190	2025-11-11	152	121	\N	Courtesy visit and follow up Aims DC @ Cyberjaya with their facilities director SE Lim. Told that already discussed with the security manager Mr. Sanmugevellu in charge for Cyberjaya DC and he will arrange a site visit to let us direct discuss with their operation team.               	2025-11-19 01:26:09.319923	3	t
191	2025-11-14	128	105	\N	Follow up the Genting RF signal coverage issues in the hotels & casino buildings to propose DAS design. Daniel told that their exsiting POC (Brand Easytalk) can not fulfill their requirement and received complaints from facilities team. But he has to take time build rapport and trust with the new facilities VP before propose any new RF system to Genting.    	2025-11-19 01:28:14.118734	3	t
192	2025-11-19	111	65	22	Accordingly to Ms. Liana the owner project on-hold again the project due to budget issue and re-consideration on the coverage area.  	2025-11-19 02:13:00.49358	2	t
193	2025-11-19	33	28	48	南京卓恒 and IFlyTech was also now tender directly to CCIE 	2025-11-19 02:25:54.60706	2	t
194	2025-11-14	112	90	86	We held a discussion with Mr. Endang from PT. Mitra Cipta Pranata. He explained that the Cikini Area Development Project is currently in the initial pre-Project Phase, which still provides a wide opportunity for preparing concepts and system proposals that can be adopted in the development of the area.\r\n\r\nMr. Endang expressed his willingness to support and help position Evertac Solutions as one of the potential solution providers for the project. He also shared the Master Plan, which serves as the main reference for the overall development layout, and requested Evertac to prepare a high-level system proposal based on the provided master plan.\r\n	2025-11-19 02:28:44.977189	9	t
\.


--
-- Data for Name: affiliations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.affiliations (id, owner_id, viewer_id, created_at) FROM stdin;
2	9	5	1754470674.2665598
3	3	5	1754470674.2730565
4	2	5	1754470674.2774239
5	6	5	1754470674.2812474
6	4	5	1754470674.2845933
7	7	8	1754470738.6517096
19	7	2	1761091865.8724983
20	9	2	1761091865.882079
21	12	2	1761091865.8881779
37	7	4	1761093542.1153123
38	3	4	1761093542.1215305
39	2	4	1761093542.1280484
40	9	4	1761093542.133828
41	7	3	1761095355.3929398
42	2	3	1761095355.3989418
43	12	3	1761095355.4038663
44	9	3	1761095355.4087496
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
bccffbe037d7
\.


--
-- Data for Name: approval_branch_condition; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_branch_condition (id, step_id, condition_order, operator, field_value, approver_id, approver_type, action, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: approval_instance; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_instance (id, object_id, object_type, current_step, status, started_at, ended_at, process_id, created_by, template_snapshot, template_version) FROM stdin;
4	8	project	1	APPROVED	2025-07-09 02:08:14.634093	2025-07-14 00:58:19.767314	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-07-09T02:08:14.625617", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "\\u7cfb\\u7edf\\u7ba1\\u7406\\u5458", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true}]}	v20250709_020814
3	4	project	1	APPROVED	2025-06-22 15:39:13.876777	2025-06-22 15:39:58.052442	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-22T15:39:13.874943", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "\\u7cfb\\u7edf\\u7ba1\\u7406\\u5458", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true}]}	v20250622_153913
2	3	project	1	APPROVED	2025-06-22 15:38:29.21562	2025-06-22 15:40:16.182924	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "required_fields": ["project_name", "project_type", "report_source"], "lock_object_on_start": true, "lock_reason": "\\u5ba1\\u6279\\u6d41\\u7a0b\\u8fdb\\u884c\\u4e2d\\uff0c\\u6682\\u65f6\\u9501\\u5b9a\\u7f16\\u8f91", "created_at": "2025-06-22T15:38:29.213923", "steps": [{"id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "\\u7cfb\\u7edf\\u7ba1\\u7406\\u5458", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true}]}	v20250622_153829
6	7	project	1	APPROVED	2025-07-09 03:13:45.458661	2025-07-14 00:57:51.921138	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-07-09T03:13:45.448806", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "\\u7cfb\\u7edf\\u7ba1\\u7406\\u5458", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true}]}	v20250709_031345
7	1	expense	3	APPROVED	2025-08-06 06:48:14.800669	2025-08-06 06:49:57.252071	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-08-06T06:48:14.794929", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "\\u7cfb\\u7edf\\u7ba1\\u7406\\u5458", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250806_064814
69	32	expense	7	APPROVED	2025-10-16 06:56:34.052608	2025-10-29 05:55:53.826279	5	3	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-16T06:56:34.044069", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251016_065634
68	31	expense	7	APPROVED	2025-10-16 06:14:34.305199	2025-10-29 05:56:12.459505	5	3	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-16T06:14:34.294002", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251016_061434
88	17	pricing_order	10	APPROVED	2025-10-31 02:54:02.793116	2025-11-18 04:41:51.195892	7	2	{"template_id": 7, "template_name": "\\u6279\\u4ef7\\u5355\\u6d41\\u7a0b", "object_type": "pricing_order", "created_at": "2025-10-31T02:54:02.773954", "steps": [{"step_id": 9, "step_order": 1, "step_name": "\\u6279\\u4ef7\\u5ba1\\u6838", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["settlement_total_discount_rate", "pricing_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 10, "step_order": 2, "step_name": "\\u6700\\u7ec8\\u5ba1\\u6279", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["pricing_total_discount_rate", "settlement_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251031_025402
70	21	expense	5	PENDING	2025-10-17 14:54:05.636154	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-17T14:54:05.627529", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251017_145405
90	18	pricing_order	9	PENDING	2025-11-05 03:07:11.704898	\N	7	2	{"template_id": 7, "template_name": "\\u6279\\u4ef7\\u5355\\u6d41\\u7a0b", "object_type": "pricing_order", "created_at": "2025-11-05T03:07:11.694093", "steps": [{"step_id": 9, "step_order": 1, "step_name": "\\u6279\\u4ef7\\u5ba1\\u6838", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["settlement_total_discount_rate", "pricing_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 10, "step_order": 2, "step_name": "\\u6700\\u7ec8\\u5ba1\\u6279", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["pricing_total_discount_rate", "settlement_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251105_030711
12	33	project	1	APPROVED	2025-08-19 03:19:44.67533	2025-08-19 04:07:23.557321	6	12	{"template_id": 6, "template_name": "\\u667a\\u80fd\\u6388\\u6743\\u5ba1\\u6279\\u6d41\\u7a0b", "object_type": "project", "created_at": "2025-08-19T03:19:44.660756", "steps": [{"step_id": 8, "step_order": 1, "step_name": "Admin\\u6388\\u6743\\u5ba1\\u6279", "approver_type": "auto", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250819_031944
17	13	project	1	REJECTED	2025-08-22 04:29:26.490981	2025-08-22 04:57:55.426731	6	12	{"template_id": 6, "template_name": "\\u667a\\u80fd\\u6388\\u6743\\u5ba1\\u6279\\u6d41\\u7a0b", "object_type": "project", "created_at": "2025-08-22T04:29:26.481405", "steps": [{"step_id": 8, "step_order": 1, "step_name": "Admin\\u6388\\u6743\\u5ba1\\u6279", "approver_type": "auto", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250822_042926
16	12	project	1	APPROVED	2025-08-22 04:25:37.17391	2025-09-08 04:22:37.791254	6	12	{"template_id": 6, "template_name": "\\u667a\\u80fd\\u6388\\u6743\\u5ba1\\u6279\\u6d41\\u7a0b", "object_type": "project", "created_at": "2025-08-22T04:25:37.162454", "steps": [{"step_id": 8, "step_order": 1, "step_name": "Admin\\u6388\\u6743\\u5ba1\\u6279", "approver_type": "auto", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250822_042537
15	43	project	1	APPROVED	2025-08-22 04:18:32.023782	2025-09-03 02:09:20.682821	6	1	{"template_id": 6, "template_name": "\\u667a\\u80fd\\u6388\\u6743\\u5ba1\\u6279\\u6d41\\u7a0b", "object_type": "project", "created_at": "2025-08-22T04:18:32.012702", "steps": [{"step_id": 8, "step_order": 1, "step_name": "Admin\\u6388\\u6743\\u5ba1\\u6279", "approver_type": "auto", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250822_041832
114	79	project	1	APPROVED	2025-11-12 03:45:12.350972	2025-11-18 05:47:58.230657	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-11-12T03:45:12.331397", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251112_034512
115	56	project	1	APPROVED	2025-11-12 03:46:48.799117	2025-11-18 05:48:43.166684	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-11-12T03:46:48.779006", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251112_034648
120	84	project	1	PENDING	2025-11-18 20:56:51.743174	\N	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-11-18T20:56:51.729848", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251118_205651
13	35	project	1	APPROVED	2025-08-19 03:20:05.810057	2025-09-19 05:04:24.866037	6	12	{"template_id": 6, "template_name": "\\u667a\\u80fd\\u6388\\u6743\\u5ba1\\u6279\\u6d41\\u7a0b", "object_type": "project", "created_at": "2025-08-19T03:20:05.797035", "steps": [{"step_id": 8, "step_order": 1, "step_name": "Admin\\u6388\\u6743\\u5ba1\\u6279", "approver_type": "auto", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250819_032005
48	65	project	1	APPROVED	2025-09-30 05:24:32.689613	2025-10-01 01:20:10.468452	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-09-30T05:24:32.675301", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20250930_052432
71	74	project	1	RECALLED	2025-10-21 07:54:50.60357	2025-10-21 07:55:14.283604	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-21T07:54:50.584177", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251021_075450
46	31	project	1	REJECTED	2025-09-30 05:23:54.567571	2025-10-01 01:20:39.442544	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-09-30T05:23:54.554485", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20250930_052354
47	64	project	1	APPROVED	2025-09-30 05:24:20.04466	2025-10-01 01:20:50.141855	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-09-30T05:24:20.029816", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20250930_052420
73	55	project	1	RECALLED	2025-10-21 07:59:59.114044	2025-10-21 08:04:54.398973	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-21T07:59:59.093525", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251021_075959
72	74	project	1	RECALLED	2025-10-21 07:57:16.632817	2025-10-21 08:42:10.598407	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-21T07:57:16.615808", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251021_075716
11	8	expense	7	APPROVED	2025-08-12 04:57:47.408637	2025-10-06 13:44:10.993528	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-08-12T04:57:47.404009", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250812_045747
76	76	project	1	APPROVED	2025-10-21 08:37:34.37117	2025-10-22 00:17:38.469186	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-21T08:37:34.357885", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251021_083734
75	75	project	1	APPROVED	2025-10-21 08:34:25.429252	2025-10-22 00:18:39.139523	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-21T08:34:25.415380", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251021_083425
74	55	project	1	APPROVED	2025-10-21 08:31:08.644208	2025-10-22 00:19:24.463598	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-21T08:31:08.631347", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251021_083108
26	18	expense	5	REJECTED	2025-09-19 05:54:45.693136	2025-10-01 09:06:48.276916	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-09-19T05:54:45.688203", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250919_055445
67	48	project	1	APPROVED	2025-10-14 07:20:52.276104	2025-10-15 02:29:12.825847	1	3	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-14T07:20:52.258052", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251014_072052
91	35	expense	7	APPROVED	2025-11-06 08:20:42.331237	2025-11-10 09:29:11.932651	5	7	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-06T08:20:42.323069", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251106_082042
102	43	expense	7	APPROVED	2025-11-11 09:53:59.415954	2025-11-19 02:02:08.203299	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T09:53:59.406656", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_095359
27	20	expense	1	RECALLED	2025-09-19 06:15:30.047378	2025-09-19 06:17:02.898523	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-09-19T06:15:30.042361", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250919_061530
77	74	project	1	APPROVED	2025-10-21 08:45:56.159303	2025-10-22 00:16:06.95682	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-21T08:45:56.145504", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251021_084556
31	16	expense	1	RECALLED	2025-09-19 06:19:40.646574	2025-09-19 06:20:14.801391	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-09-19T06:19:40.639730", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250919_061940
66	60	project	1	APPROVED	2025-10-14 07:20:19.261807	2025-10-15 02:30:01.073243	1	3	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-14T07:20:19.233700", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251014_072019
92	36	expense	7	PENDING	2025-11-09 02:39:41.092001	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-09T02:39:41.080379", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251109_023941
93	37	expense	7	PENDING	2025-11-09 02:46:58.788397	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-09T02:46:58.777776", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251109_024658
97	38	expense	5	PENDING	2025-11-09 05:47:14.666761	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-09T05:47:14.659817", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251109_054714
30	17	expense	7	APPROVED	2025-09-19 06:17:47.098035	2025-10-02 04:03:49.366621	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-09-19T06:17:47.093556", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250919_061747
96	39	expense	5	PENDING	2025-11-09 03:47:01.546001	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-09T03:47:01.528795", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251109_034701
94	38	expense	5	RECALLED	2025-11-09 03:25:45.383583	2025-11-09 05:44:11.866435	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-09T03:25:45.375952", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251109_032545
95	33	expense	6	PENDING	2025-11-09 03:33:11.830286	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-09T03:33:11.822245", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251109_033311
79	34	expense	7	APPROVED	2025-10-23 12:11:04.997755	2025-10-29 05:55:32.990138	5	4	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-23T12:11:04.988808", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251023_121104
98	52	expense	5	RECALLED	2025-11-11 03:27:08.078735	2025-11-11 03:29:11.241689	5	3	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T03:27:08.070907", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_032708
99	52	expense	5	REJECTED	2025-11-11 03:31:31.084767	2025-11-13 09:33:29.171791	5	3	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T03:31:31.077699", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_033131
108	49	expense	7	APPROVED	2025-11-11 09:56:36.841779	2025-11-19 02:03:13.409437	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T09:56:36.828711", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_095636
109	50	expense	7	APPROVED	2025-11-11 09:56:59.955215	2025-11-19 02:02:54.393804	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T09:56:59.947727", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_095659
82	53	project	1	RECALLED	2025-10-24 04:51:50.233485	2025-10-24 04:52:30.713142	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-24T04:51:50.215578", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251024_045150
45	52	project	1	APPROVED	2025-09-30 05:23:27.687382	2025-10-01 01:21:16.44987	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-09-30T05:23:27.671344", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20250930_052327
44	67	project	1	APPROVED	2025-09-30 05:17:10.700641	2025-10-01 01:21:40.481523	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-09-30T05:17:10.686407", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20250930_051710
43	63	project	1	APPROVED	2025-09-30 05:13:21.322061	2025-10-01 01:21:55.600531	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-09-30T05:13:21.307823", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20250930_051321
42	66	project	1	APPROVED	2025-09-30 05:11:56.048718	2025-10-01 01:22:27.383204	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-09-30T05:11:56.035177", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20250930_051156
83	53	project	1	APPROVED	2025-10-24 04:53:23.016181	2025-10-29 07:26:11.642148	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-24T04:53:22.998994", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251024_045323
81	54	project	1	APPROVED	2025-10-24 03:31:31.796265	2025-10-29 07:26:37.677159	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-24T03:31:31.775867", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251024_033131
80	78	project	1	APPROVED	2025-10-24 02:35:15.890792	2025-10-29 07:26:51.731339	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-24T02:35:15.877225", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251024_023515
100	40	expense	7	APPROVED	2025-11-11 09:53:10.973028	2025-11-19 02:01:20.58684	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T09:53:10.957273", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_095310
9	2	expense	5	PENDING	2025-08-12 04:16:29.86015	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-08-12T04:16:29.853127", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250812_041629
10	7	expense	5	PENDING	2025-08-12 04:52:06.863764	\N	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-08-12T04:52:06.858726", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250812_045206
84	80	project	1	APPROVED	2025-10-27 00:43:34.837484	2025-10-27 00:43:46.58594	1	1	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-27T00:43:34.818542", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251027_004334
8	6	expense	5	REJECTED	2025-08-12 04:13:40.313311	2025-10-03 12:15:39.976053	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-08-12T04:13:40.307183", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250812_041340
103	44	expense	7	APPROVED	2025-11-11 09:54:37.876446	2025-11-19 02:03:45.117894	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T09:54:37.868473", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_095437
85	81	project	1	APPROVED	2025-10-31 02:27:47.996198	2025-10-31 02:28:49.587276	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-31T02:27:47.969139", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251031_022747
32	16	expense	7	APPROVED	2025-09-19 06:21:36.620003	2025-10-02 04:04:21.787706	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-09-19T06:21:36.612288", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250919_062136
33	15	expense	7	APPROVED	2025-09-19 06:23:06.66289	2025-10-02 04:04:36.007293	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-09-19T06:23:06.656805", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250919_062306
107	48	expense	7	APPROVED	2025-11-11 09:56:12.790485	2025-11-19 02:07:53.717909	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T09:56:12.781352", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_095612
105	46	expense	7	APPROVED	2025-11-11 09:55:27.489246	2025-11-19 02:02:36.418176	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T09:55:27.481033", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_095527
106	47	expense	7	APPROVED	2025-11-11 09:55:48.421037	2025-11-19 02:07:31.461947	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T09:55:48.412934", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_095548
49	9	expense	7	APPROVED	2025-10-01 14:52:58.705864	2025-11-13 10:04:21.106931	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-01T14:52:58.695563", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251001_145258
34	14	expense	7	APPROVED	2025-09-19 06:24:06.758215	2025-10-02 04:04:49.069027	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-09-19T06:24:06.752037", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250919_062406
24	10	expense	7	APPROVED	2025-09-19 05:06:04.734161	2025-10-06 13:43:34.771466	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-09-19T05:06:04.729050", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250919_050604
35	13	expense	7	APPROVED	2025-09-19 06:26:38.592349	2025-10-02 04:05:01.209886	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-09-19T06:26:38.586129", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false}]}	v20250919_062638
54	24	expense	7	APPROVED	2025-10-02 08:57:11.935289	2025-10-16 04:38:23.303866	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-02T08:57:11.924266", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251002_085711
52	19	expense	7	APPROVED	2025-10-01 15:03:25.596443	2025-11-13 10:04:06.311146	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-01T15:03:25.589723", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251001_150325
55	25	expense	7	APPROVED	2025-10-02 09:25:20.573393	2025-10-16 04:38:05.860506	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-02T09:25:20.556773", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251002_092520
56	26	expense	7	APPROVED	2025-10-02 09:29:04.835575	2025-10-16 04:37:50.261863	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-02T09:29:04.824296", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251002_092904
58	28	expense	7	APPROVED	2025-10-02 09:32:59.241723	2025-10-16 04:37:18.603809	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-02T09:32:59.233927", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251002_093259
57	27	expense	7	APPROVED	2025-10-02 09:31:15.301624	2025-10-16 04:37:34.28503	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-02T09:31:15.294508", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251002_093115
60	70	project	1	APPROVED	2025-10-03 04:33:49.244977	2025-10-08 00:52:21.245421	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-03T04:33:49.226838", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251003_043349
122	20	pricing_order	9	RECALLED	2025-11-18 21:10:02.659466	2025-11-18 21:11:10.196608	7	2	{"template_id": 7, "template_name": "\\u6279\\u4ef7\\u5355\\u6d41\\u7a0b", "object_type": "pricing_order", "created_at": "2025-11-18T21:10:02.648861", "steps": [{"step_id": 9, "step_order": 1, "step_name": "\\u6279\\u4ef7\\u5ba1\\u6838", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["settlement_total_discount_rate", "pricing_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 10, "step_order": 2, "step_name": "\\u6700\\u7ec8\\u5ba1\\u6279", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["pricing_total_discount_rate", "settlement_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251118_211002
121	20	pricing_order	9	RECALLED	2025-11-18 21:09:11.11989	2025-11-18 21:09:22.968634	7	2	{"template_id": 7, "template_name": "\\u6279\\u4ef7\\u5355\\u6d41\\u7a0b", "object_type": "pricing_order", "created_at": "2025-11-18T21:09:11.110596", "steps": [{"step_id": 9, "step_order": 1, "step_name": "\\u6279\\u4ef7\\u5ba1\\u6838", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["settlement_total_discount_rate", "pricing_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 10, "step_order": 2, "step_name": "\\u6700\\u7ec8\\u5ba1\\u6279", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["pricing_total_discount_rate", "settlement_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251118_210911
123	20	pricing_order	9	PENDING	2025-11-18 21:18:16.827216	\N	7	2	{"template_id": 7, "template_name": "\\u6279\\u4ef7\\u5355\\u6d41\\u7a0b", "object_type": "pricing_order", "created_at": "2025-11-18T21:18:16.817667", "steps": [{"step_id": 9, "step_order": 1, "step_name": "\\u6279\\u4ef7\\u5ba1\\u6838", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["settlement_total_discount_rate", "pricing_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 10, "step_order": 2, "step_name": "\\u6700\\u7ec8\\u5ba1\\u6279", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["pricing_total_discount_rate", "settlement_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251118_211816
124	19	pricing_order	9	PENDING	2025-11-18 21:22:16.697413	\N	7	2	{"template_id": 7, "template_name": "\\u6279\\u4ef7\\u5355\\u6d41\\u7a0b", "object_type": "pricing_order", "created_at": "2025-11-18T21:22:16.688205", "steps": [{"step_id": 9, "step_order": 1, "step_name": "\\u6279\\u4ef7\\u5ba1\\u6838", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["settlement_total_discount_rate", "pricing_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 10, "step_order": 2, "step_name": "\\u6700\\u7ec8\\u5ba1\\u6279", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["pricing_total_discount_rate", "settlement_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251118_212216
53	23	expense	7	APPROVED	2025-10-02 08:52:03.480034	2025-10-16 04:38:39.974307	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-02T08:52:03.470267", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251002_085203
62	61	project	1	APPROVED	2025-10-07 04:32:55.915564	2025-10-08 01:54:27.09082	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-07T04:32:55.898473", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251007_043255
61	32	project	1	APPROVED	2025-10-07 04:28:19.360518	2025-10-08 07:09:20.338803	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-07T04:28:19.344871", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251007_042819
64	34	project	1	APPROVED	2025-10-10 08:02:02.269384	2025-10-11 05:35:38.623494	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-10T08:02:02.254316", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251010_080202
51	20	expense	7	APPROVED	2025-10-01 15:02:59.943246	2025-11-13 10:02:49.428748	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-01T15:02:59.936167", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251001_150259
63	22	project	1	APPROVED	2025-10-10 08:00:45.067935	2025-10-15 02:30:19.209317	1	2	{"template_id": 1, "template_name": "\\u6388\\u6743\\u5907\\u6848", "object_type": "project", "created_at": "2025-10-10T08:00:45.049071", "steps": [{"step_id": 1, "step_order": 1, "step_name": "\\u7533\\u8bf7\\u5907\\u6848 - Admin\\u6388\\u6743", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "authorization", "action_params": null, "editable_fields": [], "cc_users": [1], "cc_enabled": true, "branch_condition": null}]}	v20251010_080045
65	30	expense	7	APPROVED	2025-10-11 06:58:20.328689	2025-11-13 10:02:17.401687	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-11T06:58:20.319733", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251011_065820
59	29	expense	7	APPROVED	2025-10-02 09:36:34.302944	2025-10-16 04:36:40.680993	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-02T09:36:34.294915", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251002_093634
111	53	expense	5	RECALLED	2025-11-11 09:58:22.775371	2025-11-11 09:58:29.884921	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T09:58:22.766200", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_095822
104	45	expense	7	APPROVED	2025-11-11 09:55:01.58831	2025-11-19 02:07:10.478494	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-11T09:55:01.578693", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251111_095501
50	22	expense	7	APPROVED	2025-10-01 15:01:39.877975	2025-11-13 10:02:34.4907	5	1	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-10-01T15:01:39.870822", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251001_150139
116	42	expense	7	APPROVED	2025-11-12 23:17:55.275653	2025-11-19 02:01:48.451741	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-12T23:17:55.265793", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251112_231755
117	53	expense	6	PENDING	2025-11-18 06:09:33.305876	\N	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-18T06:09:33.297641", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251118_060933
118	54	expense	5	RECALLED	2025-11-18 06:44:07.122135	2025-11-20 10:12:55.822144	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-18T06:44:07.115843", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251118_064407
119	51	expense	5	RECALLED	2025-11-18 07:11:14.642806	2025-11-20 10:13:20.31856	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-18T07:11:14.635987", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251118_071114
125	21	pricing_order	9	PENDING	2025-11-18 21:27:49.680759	\N	7	2	{"template_id": 7, "template_name": "\\u6279\\u4ef7\\u5355\\u6d41\\u7a0b", "object_type": "pricing_order", "created_at": "2025-11-18T21:27:49.669920", "steps": [{"step_id": 9, "step_order": 1, "step_name": "\\u6279\\u4ef7\\u5ba1\\u6838", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["settlement_total_discount_rate", "pricing_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 10, "step_order": 2, "step_name": "\\u6700\\u7ec8\\u5ba1\\u6279", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": "pricing_settlement_approval", "action_params": null, "editable_fields": ["pricing_total_discount_rate", "settlement_total_discount_rate", "unit_price", "discount_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251118_212749
126	51	expense	5	RECALLED	2025-11-24 05:48:01.419636	2025-11-24 05:56:51.134651	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-24T05:48:01.411355", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251124_054801
127	51	expense	5	PENDING	2025-11-24 05:57:22.504743	\N	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-24T05:57:22.496659", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251124_055722
128	54	expense	5	PENDING	2025-11-24 05:58:03.043589	\N	5	2	{"template_id": 5, "template_name": "Expense Claim", "object_type": "expense", "created_at": "2025-11-24T05:58:03.034817", "steps": [{"step_id": 5, "step_order": 1, "step_name": "Finance Review", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": null, "action_params": null, "editable_fields": ["exchange_rate"], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 6, "step_order": 2, "step_name": "Supervisor Review", "approver_type": "user", "approver_user_id": 1, "approver_username": "admin", "approver_real_name": "james.ni", "send_email": true, "action_type": null, "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}, {"step_id": 7, "step_order": 3, "step_name": "Reimbursement Payment", "approver_type": "user", "approver_user_id": 5, "approver_username": "peizhen", "approver_real_name": "Pei Zhen", "send_email": true, "action_type": "payment_processing", "action_params": null, "editable_fields": [], "cc_users": [], "cc_enabled": false, "branch_condition": null}]}	v20251124_055803
\.


--
-- Data for Name: approval_process_template; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_process_template (id, name, object_type, is_active, created_by, created_at, required_fields, lock_object_on_start, lock_reason, visual_data) FROM stdin;
1	授权备案	project	t	1	2025-06-22 15:34:43.794919	["project_name", "project_type", "report_source"]	t	审批流程进行中，暂时锁定编辑	\N
5	Expense Claim	expense	t	1	2025-08-06 14:32:25.764934	["expense_number"]	t	审批流程进行中，暂时锁定编辑	\N
6	智能授权审批流程	project	t	1	2025-08-19 11:19:44.567936	[]	t	项目授权编号审批锁定	\N
7	批价单流程	pricing_order	t	1	2025-10-30 09:49:46.253812	[]	t	审批流程进行中，暂时锁定编辑	\N
\.


--
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
14	12	8	1	approve		2025-08-19 04:07:23.534462
16	17	8	12	recall	发起人召回审批流程。原因：状态更新	2025-08-22 04:57:55.433454
18	15	8	1	approve		2025-09-03 02:09:20.648068
19	11	5	5	approve		2025-09-05 08:41:43.30184
20	16	8	1	approve		2025-09-08 04:22:37.769639
22	13	8	1	approve		2025-09-19 05:04:24.843272
23	11	6	1	approve		2025-09-19 05:04:48.866614
28	30	5	5	approve		2025-09-19 06:23:27.548367
29	32	5	5	approve		2025-09-19 06:24:28.033474
30	33	5	5	approve		2025-09-19 06:25:19.032731
31	34	5	5	approve		2025-09-19 06:25:51.596523
32	35	5	5	approve		2025-09-19 06:29:32.17072
33	24	5	5	approve		2025-09-19 06:36:57.016696
39	48	1	1	approve		2025-10-01 01:20:10.45409
40	46	\N	2	recall	流程召回	2025-10-01 01:20:39.442554
41	47	1	1	approve		2025-10-01 01:20:50.128374
42	45	1	1	approve		2025-10-01 01:21:16.43807
43	44	1	1	approve		2025-10-01 01:21:40.469257
44	43	1	1	approve		2025-10-01 01:21:55.588446
45	42	1	1	approve		2025-10-01 01:22:27.370867
49	30	6	1	approve		2025-10-01 08:38:39.491957
50	26	5	5	reject	Pls re-attached supporting invoice for ¥1,265.00 (cannot be viewed, download also cannot - indicated a not supported file/ damaged). \r\n\r\n฿1,585.54 - wrong invoice attached	2025-10-01 09:06:48.276716
51	32	6	1	approve		2025-10-01 14:49:53.84995
52	33	6	1	approve		2025-10-01 14:50:50.484453
53	35	6	1	approve		2025-10-01 14:51:13.011583
54	34	6	1	approve		2025-10-01 14:51:21.698267
55	24	6	1	approve		2025-10-01 14:51:43.998857
56	30	7	5	approve		2025-10-02 04:03:49.366451
57	32	7	5	approve	Payment Date: 02/10/2025	2025-10-02 04:04:21.787551
58	33	7	5	approve	Payment Date: 02/10/2025	2025-10-02 04:04:36.007155
59	34	7	5	approve	Payment Date: 02/10/2025	2025-10-02 04:04:49.068891
60	35	7	5	approve	Payment Date: 02/10/2025	2025-10-02 04:05:01.209731
61	52	5	5	approve		2025-10-02 04:31:20.867827
62	51	5	5	approve		2025-10-02 04:44:36.987198
63	49	5	5	approve		2025-10-02 04:48:27.380935
64	50	5	5	approve		2025-10-02 08:38:21.243342
65	53	5	5	approve		2025-10-03 05:41:54.977621
66	54	5	5	approve		2025-10-03 05:46:35.349291
67	55	5	5	approve		2025-10-03 05:48:55.059559
68	56	5	5	approve		2025-10-03 05:52:36.969026
69	58	5	5	approve		2025-10-03 06:06:05.577949
70	59	5	5	approve		2025-10-03 06:14:06.758287
71	57	5	5	approve		2025-10-03 06:18:43.894209
73	8	5	5	reject	Other - ¥58.72\t\r\n1) pls change invoice currency to SGD\r\n\r\nLocal Transport ฿1,460.00\t\r\n1) Expenses category - pls change to travelling\r\n\r\nLocal Transport (¥54.10) \r\n1) pls change invoice currency to SGD\r\n2) Expense date change to 2025-07-31	2025-10-03 12:15:39.975932
74	24	7	5	approve	Paid 06.10.2025	2025-10-06 13:43:34.771319
75	11	7	5	approve	Paid 06.10.2025	2025-10-06 13:44:10.993368
76	60	1	1	approve		2025-10-08 00:52:21.225546
77	59	6	1	approve		2025-10-08 01:54:13.145953
78	62	1	1	approve		2025-10-08 01:54:27.080827
79	61	1	1	approve		2025-10-08 07:09:20.330506
80	58	6	1	approve		2025-10-10 04:39:54.284129
81	57	6	1	approve		2025-10-10 04:40:10.503358
82	56	6	1	approve		2025-10-10 04:40:26.807447
83	55	6	1	approve		2025-10-10 04:40:52.801818
84	54	6	1	approve		2025-10-10 04:41:12.63598
85	53	6	1	approve		2025-10-10 04:41:28.771954
86	52	6	1	approve		2025-10-10 04:41:42.750027
87	51	6	1	approve		2025-10-10 04:41:52.788577
88	50	6	1	approve		2025-10-10 04:42:07.170771
89	49	6	1	approve		2025-10-10 04:42:29.109842
90	64	1	1	approve		2025-10-11 05:35:38.604545
91	67	1	1	approve		2025-10-15 02:29:12.811109
92	66	1	1	approve		2025-10-15 02:30:01.065581
93	63	1	1	approve		2025-10-15 02:30:19.202106
95	59	7	5	approve	Paid 16/10/2025	2025-10-16 04:36:40.680507
96	58	7	5	approve	Paid 16/10/2025	2025-10-16 04:37:18.603616
97	57	7	5	approve	Paid 16/10/2025	2025-10-16 04:37:34.284806
98	56	7	5	approve	Paid 16/10/2025	2025-10-16 04:37:50.261692
99	55	7	5	approve	Paid 16/10/2025	2025-10-16 04:38:05.860317
100	54	7	5	approve	Paid 16/10/2025	2025-10-16 04:38:23.303715
101	53	7	5	approve	Paid 16/10/2025	2025-10-16 04:38:39.974106
102	68	5	5	approve		2025-10-16 06:18:47.294362
103	69	5	5	approve		2025-10-16 07:25:17.70354
104	69	6	1	approve		2025-10-17 04:00:40.728185
105	68	6	1	approve		2025-10-17 04:01:07.702739
106	77	1	1	approve		2025-10-22 00:16:06.940804
107	76	1	1	approve	your project currently stage need to comfirmed	2025-10-22 00:17:38.458113
108	75	1	1	approve	currently project stage is not right	2025-10-22 00:18:39.128332
109	74	1	1	approve	please add the customer and adjust project stage to right position.	2025-10-22 00:19:24.45443
111	65	5	5	approve		2025-10-23 12:14:04.704726
112	79	5	5	approve		2025-10-23 12:15:44.487031
113	84	1	1	approve		2025-10-27 00:43:46.571698
114	79	6	1	approve		2025-10-29 04:46:21.434968
115	65	6	1	approve		2025-10-29 04:46:37.38476
116	79	7	5	approve	Paid 29/10/2025	2025-10-29 05:55:32.989929
117	69	7	5	approve	Paid 29/10/2025	2025-10-29 05:55:53.826087
118	68	7	5	approve	Paid 29/10/2025	2025-10-29 05:56:12.459332
119	83	1	1	approve		2025-10-29 07:26:11.629386
120	81	1	1	approve		2025-10-29 07:26:37.66902
121	80	1	1	approve		2025-10-29 07:26:51.723704
122	85	1	1	approve		2025-10-31 02:28:49.577443
126	88	9	5	approve		2025-10-31 02:57:09.397788
128	91	5	5	approve		2025-11-06 08:59:30.306611
129	91	6	1	approve		2025-11-09 02:30:08.955895
130	91	7	5	approve	Credited to CIMB bank on 10/11/2025	2025-11-10 09:29:11.932439
132	102	5	5	approve		2025-11-12 06:34:56.991034
133	103	5	5	approve		2025-11-12 06:36:14.681661
134	104	5	5	approve		2025-11-12 06:37:42.674443
135	105	5	5	approve		2025-11-12 06:39:46.387903
136	107	5	5	approve		2025-11-12 06:54:12.629386
137	109	5	5	approve		2025-11-12 06:56:28.201437
140	100	5	5	approve		2025-11-12 09:59:54.561677
142	116	5	5	approve		2025-11-13 09:01:47.733723
143	99	5	5	reject	1. I noticed there’s a customer record for Trac Consulting & Engineering Sdn Bhd. Your entertainment claim for lunch with Trac Consult — is that the same company?\r\n If yes, please select this customer for your entertainment claim.\r\n2. For the roll-up banner, please submit it as a separate new claim. Invoice currency pls select RM.	2025-11-13 09:33:29.171582
144	106	5	5	approve		2025-11-13 09:36:30.853832
145	108	5	5	approve		2025-11-13 09:37:38.911437
146	65	7	5	approve	Paid on 10 Nov 2025	2025-11-13 10:02:17.401488
147	50	7	5	approve	Paid on 10 Nov 2025	2025-11-13 10:02:34.490488
148	51	7	5	approve	Paid on 10 Nov 2025	2025-11-13 10:02:49.428525
149	52	7	5	approve	Paid on 10 Nov 2025	2025-11-13 10:04:06.310967
150	49	7	5	approve	Paid on 10 Nov 2025	2025-11-13 10:04:21.106745
151	92	5	5	approve		2025-11-13 10:55:09.999687
152	93	5	5	approve		2025-11-13 10:56:30.125382
153	88	10	1	approve		2025-11-18 04:41:51.141474
154	100	6	1	approve		2025-11-18 04:43:19.384634
155	102	6	1	approve		2025-11-18 04:43:58.915357
156	103	6	1	approve		2025-11-18 04:44:39.766775
157	104	6	1	approve		2025-11-18 04:48:46.361364
158	105	6	1	approve		2025-11-18 04:49:34.234477
159	106	6	1	approve		2025-11-18 04:50:35.923649
160	116	6	1	approve		2025-11-18 04:56:35.998095
161	109	6	1	approve		2025-11-18 04:57:25.727555
162	108	6	1	approve		2025-11-18 04:58:53.441606
163	114	1	1	approve		2025-11-18 05:47:58.22031
164	115	1	1	approve		2025-11-18 05:48:43.155972
165	107	6	1	approve		2025-11-18 05:49:15.502418
166	93	6	1	approve		2025-11-18 05:49:51.438031
167	92	6	1	approve		2025-11-18 05:50:13.454064
168	121	9	2	recall	发起人召回批价单。原因：用户主动召回	2025-11-18 21:09:22.968644
169	122	9	2	recall	发起人召回批价单。原因：用户主动召回	2025-11-18 21:11:10.196616
170	100	7	5	approve	Paid 19/11/2025	2025-11-19 02:01:20.586655
171	116	7	5	approve	Paid 19/11/2025	2025-11-19 02:01:48.451577
172	102	7	5	approve	Paid 19/11/2025	2025-11-19 02:02:08.203139
173	105	7	5	approve	Paid 19/11/2025	2025-11-19 02:02:36.418002
174	109	7	5	approve	Paid 19/11/2025	2025-11-19 02:02:54.393569
175	108	7	5	approve	Paid 19/11/2025	2025-11-19 02:03:13.40928
176	103	7	5	approve	Paid 19/11/2025	2025-11-19 02:03:45.117733
177	104	7	5	approve	Paid 19/11/2025	2025-11-19 02:07:10.478316
178	106	7	5	approve	Paid 19/11/2025	2025-11-19 02:07:31.461774
179	107	7	5	approve	Paid 19/11/2025	2025-11-19 02:07:53.717723
180	117	5	5	approve	I checked with Quah about the additional check-in luggage fee. He explained that the airline did not allow him to hand-carry his luggage due to the size, so he had to purchase check-in baggage on the spot.	2025-11-20 08:04:03.51568
181	95	5	5	approve		2025-11-20 11:40:24.42704
\.


--
-- Data for Name: approval_step; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.approval_step (id, process_id, step_order, approver_user_id, step_name, send_email, action_type, action_params, editable_fields, cc_users, cc_enabled, approver_type, description, condition_config, is_conditional, branch_on_reject, skip_conditions, condition_type, branch_on_approve, step_type, branch_condition, parent_step_id, is_parallel, branch_group_id, branch_level, branch_path, merge_step_id) FROM stdin;
1	1	1	1	申请备案	t	authorization	\N	[]	[1]	t	user	\N	\N	f	\N	\N	\N	\N	normal	\N	\N	f	\N	0	\N	\N
5	5	1	5	Finance Review	t	\N	\N	["exchange_rate"]	[]	f	user	\N	\N	f	\N	\N	\N	\N	normal	\N	\N	f	\N	0	\N	\N
6	5	2	1	Supervisor Review	t	\N	\N	[]	[]	f	user	\N	\N	f	\N	\N	\N	\N	normal	\N	\N	f	\N	0	\N	\N
7	5	3	5	Reimbursement Payment	t	payment_processing	\N	[]	[]	f	user	\N	\N	f	\N	\N	\N	\N	normal	\N	\N	f	\N	0	\N	\N
8	6	1	\N	智能授权审批	t	authorization	\N	[]	[]	f	auto	根据项目类型自动分配审批人：渠道跟进→渠道经理，销售重点→营销总监，销售机会→服务经理	\N	f	\N	\N	\N	\N	normal	\N	\N	f	\N	0	\N	\N
9	7	1	5	批价审核	t	pricing_settlement_approval	\N	["settlement_total_discount_rate", "pricing_total_discount_rate", "unit_price", "discount_rate"]	[]	f	user	\N	\N	f	\N	\N	\N	\N	normal	null	\N	f	\N	0	\N	\N
10	7	2	1	最终审批	t	pricing_settlement_approval	\N	["pricing_total_discount_rate", "settlement_total_discount_rate", "unit_price", "discount_rate"]	[]	f	user	\N	\N	f	\N	\N	\N	\N	normal	null	\N	f	\N	0	\N	\N
\.


--
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
568	customer	contacts	98	CREATE	\N	\N	\N	3	roy	2025-08-19 04:35:32.627016	\N	10.210.205.21	\N	记录: Lilian Su Lee Ding
522	quotation	quotations	19	UPDATE	product_signature	bde7b7a43b04330328b919a66d551273	bff43007b7bbeb1792df3bbae2651bdf	2	quah	2025-08-15 02:22:27.254171	\N	10.210.172.229	\N	报价单: QU202508-002
523	quotation	quotations	19	UPDATE	implant_total_amount	3290.0	28544.0	2	quah	2025-08-15 02:22:27.254174	\N	10.210.172.229	\N	报价单: QU202508-002
524	quotation	quotations	19	UPDATE	updated_at	2025-08-15 02:05:11.949107	2025-08-15 02:22:27.252753	2	quah	2025-08-15 02:22:27.254175	\N	10.210.172.229	\N	报价单: QU202508-002
525	quotation	quotations	19	UPDATE	amount	31194.0	32060.899999999998	2	quah	2025-08-15 02:28:10.142649	\N	10.210.172.229	\N	报价单: QU202508-002
526	quotation	quotations	19	UPDATE	product_signature	bff43007b7bbeb1792df3bbae2651bdf	54bbd12cc6f9a9ebf905218150643f40	2	quah	2025-08-15 02:28:10.142659	\N	10.210.172.229	\N	报价单: QU202508-002
527	quotation	quotations	19	UPDATE	updated_at	2025-08-15 02:22:27.252753	2025-08-15 02:28:10.139042	2	quah	2025-08-15 02:28:10.142663	\N	10.210.172.229	\N	报价单: QU202508-002
528	user	users	13	CREATE	\N	\N	\N	1	admin	2025-08-18 05:12:16.690874	\N	10.210.172.229	\N	公司: Technics Communication & Electronics Pte Ltd
529	user	users	14	CREATE	\N	\N	\N	1	admin	2025-08-18 05:13:34.63371	\N	10.210.205.21	\N	公司: Technics Communication & Electronics Pte Ltd
530	user	users	14	UPDATE	是否激活	False	True	1	admin	2025-08-18 05:13:47.424776	\N	10.210.86.86	\N	公司: Technics Communication & Electronics Pte Ltd
531	user	users	14	UPDATE	updated_at	1755494014.46515	1755494027.40599	1	admin	2025-08-18 05:13:47.42478	\N	10.210.86.86	\N	公司: Technics Communication & Electronics Pte Ltd
532	user	users	13	UPDATE	是否激活	False	True	1	admin	2025-08-18 05:13:58.429312	\N	10.210.205.21	\N	公司: Technics Communication & Electronics Pte Ltd
533	user	users	13	UPDATE	updated_at	1755493936.41583	1755494038.39735	1	admin	2025-08-18 05:13:58.429317	\N	10.210.205.21	\N	公司: Technics Communication & Electronics Pte Ltd
534	user	users	14	UPDATE	是否激活	True	False	1	admin	2025-08-18 05:16:37.532431	\N	10.210.172.229	\N	公司: Technics Communication & Electronics Pte Ltd
535	user	users	14	UPDATE	updated_at	1755494027.40599	1755494197.51228	1	admin	2025-08-18 05:16:37.532438	\N	10.210.172.229	\N	公司: Technics Communication & Electronics Pte Ltd
536	user	users	13	UPDATE	是否激活	True	False	1	admin	2025-08-18 05:16:47.88376	\N	10.210.86.86	\N	公司: Technics Communication & Electronics Pte Ltd
537	user	users	13	UPDATE	updated_at	1755494130.2996	1755494207.86365	1	admin	2025-08-18 05:16:47.883765	\N	10.210.86.86	\N	公司: Technics Communication & Electronics Pte Ltd
538	user	users	14	UPDATE	邮箱	ryan.ong@tce.com	ryan.ong@tce.com.sg	1	admin	2025-08-18 05:17:01.397399	\N	10.210.179.122	\N	公司: Technics Communication & Electronics Pte Ltd
539	user	users	14	UPDATE	updated_at	1755494197.51228	1755494221.37623	1	admin	2025-08-18 05:17:01.397406	\N	10.210.179.122	\N	公司: Technics Communication & Electronics Pte Ltd
540	user	users	13	UPDATE	邮箱	jianming.loo@tce.com	jianming.loo@tce.com.sg	1	admin	2025-08-18 05:17:20.859227	\N	10.210.205.21	\N	公司: Technics Communication & Electronics Pte Ltd
541	user	users	13	UPDATE	updated_at	1755494207.86365	1755494240.82984	1	admin	2025-08-18 05:17:20.859232	\N	10.210.205.21	\N	公司: Technics Communication & Electronics Pte Ltd
542	user	users	8	UPDATE	is_department_manager	False	True	1	admin	2025-08-18 05:17:52.649991	\N	10.210.172.229	\N	公司: Technics Communication & Electronics Pte Ltd
543	user	users	8	UPDATE	updated_at	1754471817.15416	1755494272.62893	1	admin	2025-08-18 05:17:52.649995	\N	10.210.172.229	\N	公司: Technics Communication & Electronics Pte Ltd
544	user	users	8	UPDATE	is_department_manager	True	False	1	admin	2025-08-18 05:20:16.709773	\N	10.210.179.122	\N	公司: Technics Communication & Electronics Pte Ltd
545	user	users	8	UPDATE	updated_at	1755494272.62893	1755494416.69063	1	admin	2025-08-18 05:20:16.709777	\N	10.210.179.122	\N	公司: Technics Communication & Electronics Pte Ltd
546	project	projects	33	CREATE	\N	\N	\N	12	fuyan	2025-08-18 09:38:47.651223	\N	10.210.86.86	\N	项目: 香港新界荃湾GDS数据中心一期
547	quotation	quotations	20	CREATE	\N	\N	\N	12	fuyan	2025-08-18 09:46:25.910341	\N	10.210.23.23	\N	报价单: QU202508-003
548	quotation	quotations	21	CREATE	\N	\N	\N	12	fuyan	2025-08-18 10:06:21.420425	\N	10.210.205.21	\N	报价单: QU202508-004
549	project	projects	34	CREATE	\N	\N	\N	2	quah	2025-08-19 02:20:08.023244	\N	10.210.172.229	\N	项目:  R&F Princess Cove III
550	quotation	quotations	22	CREATE	\N	\N	\N	2	quah	2025-08-19 02:20:37.787464	\N	10.210.23.23	\N	报价单: QU202508-005
551	quotation	quotations	22	UPDATE	amount	3619.0	153809.0	2	quah	2025-08-19 02:32:55.916065	\N	10.210.167.141	\N	报价单: QU202508-005
552	quotation	quotations	22	UPDATE	product_signature	a0179ce456b21ef33a8d90796ee52d58	9386adca01062dfdb6cec9c8bc32f0b2	2	quah	2025-08-19 02:32:55.916069	\N	10.210.167.141	\N	报价单: QU202508-005
553	quotation	quotations	22	UPDATE	implant_total_amount	3290.0	153809.0	2	quah	2025-08-19 02:32:55.916072	\N	10.210.167.141	\N	报价单: QU202508-005
554	quotation	quotations	22	UPDATE	updated_at	2025-08-19 02:20:37.753261	2025-08-19 02:32:55.914865	2	quah	2025-08-19 02:32:55.916074	\N	10.210.167.141	\N	报价单: QU202508-005
555	project	projects	35	CREATE	\N	\N	\N	12	fuyan	2025-08-19 02:34:17.76572	\N	10.210.167.141	\N	项目: 香港新界荃湾GDS数据中心二期
556	quotation	quotations	23	CREATE	\N	\N	\N	12	fuyan	2025-08-19 02:36:33.942547	\N	10.210.172.229	\N	报价单: QU202508-006
557	quotation	quotations	22	UPDATE	amount	153809.0	213399.2	2	quah	2025-08-19 03:10:25.713159	\N	10.210.86.86	\N	报价单: QU202508-005
558	quotation	quotations	22	UPDATE	product_signature	9386adca01062dfdb6cec9c8bc32f0b2	dd0b5b391a240f37dbf845465ad0ed87	2	quah	2025-08-19 03:10:25.713163	\N	10.210.86.86	\N	报价单: QU202508-005
559	quotation	quotations	22	UPDATE	implant_total_amount	153809.0	189364.0	2	quah	2025-08-19 03:10:25.713166	\N	10.210.86.86	\N	报价单: QU202508-005
560	quotation	quotations	22	UPDATE	updated_at	2025-08-19 02:32:55.914865	2025-08-19 03:10:25.711296	2	quah	2025-08-19 03:10:25.713168	\N	10.210.86.86	\N	报价单: QU202508-005
561	customer	companies	74	CREATE	\N	\N	\N	2	quah	2025-08-19 03:22:56.723	\N	10.210.167.141	\N	公司: iFLYTEK
562	customer	contacts	94	CREATE	\N	\N	\N	2	quah	2025-08-19 03:24:40.79146	\N	10.210.179.122	\N	记录: Khor Su Chong 
563	customer	contacts	95	CREATE	\N	\N	\N	3	roy	2025-08-19 04:26:13.334141	\N	10.210.86.86	\N	记录: Shahrul
564	customer	companies	75	CREATE	\N	\N	\N	3	roy	2025-08-19 04:29:51.62707	\N	10.210.23.23	\N	公司: Arup Jururunding Sdn Bhd
565	customer	companies	76	CREATE	\N	\N	\N	9	alesandro	2025-08-19 04:31:03.202533	\N	10.210.179.122	\N	公司: PT. Indonesia Weda Bay Industrial Park (IWIP)
566	customer	contacts	96	CREATE	\N	\N	\N	3	roy	2025-08-19 04:32:11.450539	\N	10.210.23.23	\N	记录: Jackie Teo
567	customer	contacts	97	CREATE	\N	\N	\N	9	alesandro	2025-08-19 04:33:31.418501	\N	10.210.179.122	\N	记录: Delvin
569	customer	companies	77	CREATE	\N	\N	\N	9	alesandro	2025-08-19 04:49:17.080928	\N	10.210.23.23	\N	公司: PT. Padma Integra Mandiri
570	customer	contacts	97	UPDATE	部门		Project Devision	9	alesandro	2025-08-19 04:50:09.025987	\N	10.210.179.122	\N	记录: Delvin
571	customer	contacts	97	UPDATE	position		Project Devision	9	alesandro	2025-08-19 04:50:09.025994	\N	10.210.179.122	\N	记录: Delvin
572	customer	contacts	97	UPDATE	updated_at	2025-08-19 12:33:31.400579	2025-08-19 12:50:09.010407	9	alesandro	2025-08-19 04:50:09.025997	\N	10.210.179.122	\N	记录: Delvin
573	customer	contacts	99	CREATE	\N	\N	\N	9	alesandro	2025-08-19 04:51:57.294113	\N	10.210.86.86	\N	记录: Joestiant
574	customer	companies	78	CREATE	\N	\N	\N	9	alesandro	2025-08-19 05:00:23.415679	\N	10.210.167.141	\N	公司: PT. Dwi Candra Teknologi
575	customer	contacts	100	CREATE	\N	\N	\N	9	alesandro	2025-08-19 05:01:36.540447	\N	10.210.205.21	\N	记录: Candra
576	customer	contacts	101	CREATE	\N	\N	\N	2	quah	2025-08-19 05:09:46.273824	\N	10.210.86.86	\N	记录: Maximilian
577	customer	companies	79	CREATE	\N	\N	\N	13	jianming	2025-08-19 07:50:26.614243	\N	10.210.205.21	\N	公司: Telesources (S) Pte Ltd
578	project	projects	36	CREATE	\N	\N	\N	14	ryan	2025-08-19 07:51:05.867021	\N	10.210.23.23	\N	项目: Alexandra Hospital 
579	project	projects	37	CREATE	\N	\N	\N	13	jianming	2025-08-19 07:52:18.221963	\N	10.210.205.21	\N	项目: Vessel (One Infinity)
580	quotation	quotations	24	CREATE	\N	\N	\N	13	jianming	2025-08-19 08:31:43.597419	\N	10.210.23.23	\N	报价单: QU202508-007
581	project	projects	38	CREATE	\N	\N	\N	13	jianming	2025-08-19 08:43:19.21138	\N	10.210.179.122	\N	项目: Hendon Camp (Phase3)
582	customer	companies	80	CREATE	\N	\N	\N	13	jianming	2025-08-19 08:46:43.836341	\N	10.210.179.122	\N	公司: Ping Engineering (Singapore) Pte Ltd
583	quotation	quotations	25	CREATE	\N	\N	\N	13	jianming	2025-08-19 08:50:45.668435	\N	10.210.167.141	\N	报价单: QU202508-008
584	quotation	quotations	24	UPDATE	product_signature	0e38143cba4819a7	0ee43448b99f29fb40a81446dea39869	13	jianming	2025-08-19 08:51:55.904076	\N	10.210.179.122	\N	报价单: QU202508-007
585	quotation	quotations	24	UPDATE	updated_at	2025-08-19 08:31:43.570369	2025-08-19 08:51:55.903196	13	jianming	2025-08-19 08:51:55.904082	\N	10.210.179.122	\N	报价单: QU202508-007
586	quotation	quotations	24	UPDATE	updated_at	2025-08-19 08:51:55.903196	2025-08-19 08:52:30.322286	13	jianming	2025-08-19 08:52:30.323224	\N	10.210.167.141	\N	报价单: QU202508-007
587	project	projects	10	UPDATE	industry	other	datacenter	1	admin	2025-08-20 01:46:36.415915	\N	10.210.23.23	\N	项目: YTL Data Centre @ Kulai
588	project	projects	33	UPDATE	厂商负责人	2	1	1	admin	2025-08-20 01:47:20.449883	\N	10.210.23.23	\N	项目: 香港新界荃湾GDS数据中心一期
589	project	projects	35	UPDATE	厂商负责人	2	1	1	admin	2025-08-20 01:47:37.368956	\N	10.210.167.141	\N	项目: 香港新界荃湾GDS数据中心二期
590	project	projects	35	UPDATE	shared_with_users	[1, 2, 3, 4, 5, 9, 10, 11]	[2, 3, 4, 5, 9, 10, 11]	1	admin	2025-08-20 01:47:37.36896	\N	10.210.167.141	\N	项目: 香港新界荃湾GDS数据中心二期
591	project	projects	39	CREATE	\N	\N	\N	3	roy	2025-08-21 02:48:23.695629	\N	10.210.205.21	\N	项目: Penang Airport Extension
592	project	projects	39	DELETE	\N	\N	\N	3	roy	2025-08-21 02:49:28.950854	\N	10.210.205.21	\N	项目: Penang Airport Extension
593	customer	companies	81	CREATE	\N	\N	\N	3	roy	2025-08-21 02:51:34.335604	\N	10.210.172.229	\N	公司: Malaysia Airports Holdings Bhd (MAHB)
594	project	projects	40	CREATE	\N	\N	\N	3	roy	2025-08-21 02:52:52.325216	\N	10.210.23.23	\N	项目: Penang Airport Extension
595	customer	companies	82	CREATE	\N	\N	\N	3	roy	2025-08-21 02:56:23.323715	\N	10.210.23.23	\N	公司: Amazon Web Services Malaysia Sdn Bhd (AWS)
596	project	projects	41	CREATE	\N	\N	\N	3	roy	2025-08-21 02:58:07.367723	\N	10.210.205.21	\N	项目: Amazon Data Centre @ Cyberjaya
597	customer	companies	83	CREATE	\N	\N	\N	3	roy	2025-08-21 03:00:38.832653	\N	10.210.167.141	\N	公司: Microsoft (Malaysia) Sdn Bhd
598	project	projects	42	CREATE	\N	\N	\N	3	roy	2025-08-21 03:02:06.480778	\N	10.210.179.122	\N	项目: Microsoft Data Centre @ Cyberjaya
599	project	projects	43	CREATE	\N	\N	\N	12	fuyan	2025-08-22 04:16:16.018588	\N	10.210.167.141	\N	项目: 中联重科中联2号楼
600	project	projects	44	CREATE	\N	\N	\N	1	admin	2025-08-22 04:17:35.045282	\N	10.210.172.229	\N	项目: 测试好了
601	project	projects	44	DELETE	\N	\N	\N	1	admin	2025-08-22 04:18:02.640288	\N	10.210.172.229	\N	项目: 测试好了
602	quotation	quotations	26	CREATE	\N	\N	\N	12	fuyan	2025-08-22 04:22:11.293806	\N	10.210.23.23	\N	报价单: QU202508-009
603	project	projects	28	DELETE	\N	\N	\N	12	fuyan	2025-08-22 04:52:10.756813	\N	10.210.86.86	\N	项目: NTP-N
604	project	projects	19	UPDATE	项目名称	CTP - C - GDS DC @ Chonburi Thailand	KTP - C - GDS DC @ Chonburi Thailand	12	fuyan	2025-08-22 04:56:55.049191	\N	10.210.86.86	\N	项目: KTP - C - GDS DC @ Chonburi Thailand
605	project	projects	19	UPDATE	产品情况	qualified	controlled	12	fuyan	2025-08-22 04:56:55.049195	\N	10.210.86.86	\N	项目: KTP - C - GDS DC @ Chonburi Thailand
606	project	projects	19	UPDATE	阶段描述		目前LM中标，已经深化图纸及清单！	12	fuyan	2025-08-22 04:56:55.049198	\N	10.210.86.86	\N	项目: KTP - C - GDS DC @ Chonburi Thailand
607	project	projects	19	UPDATE	交付预测	\N	2025-10-30	12	fuyan	2025-08-22 04:56:55.0492	\N	10.210.86.86	\N	项目: KTP - C - GDS DC @ Chonburi Thailand
608	quotation	quotations	19	UPDATE	amount	32060.9	32098.4	2	quah	2025-08-25 02:03:33.224573	\N	10.210.205.21	\N	报价单: QU202508-002
609	quotation	quotations	19	UPDATE	product_signature	54bbd12cc6f9a9ebf905218150643f40	2efb54d9c14cc5e33fe6726019c19d9b	2	quah	2025-08-25 02:03:33.224577	\N	10.210.205.21	\N	报价单: QU202508-002
610	quotation	quotations	19	UPDATE	updated_at	2025-08-15 02:28:10.139042	2025-08-25 02:03:33.223278	2	quah	2025-08-25 02:03:33.22458	\N	10.210.205.21	\N	报价单: QU202508-002
611	quotation	quotations	19	UPDATE	amount	32098.4	27223.4	2	quah	2025-08-25 02:09:05.626516	\N	10.210.86.86	\N	报价单: QU202508-002
612	quotation	quotations	19	UPDATE	implant_total_amount	28544.0	23669.0	2	quah	2025-08-25 02:09:05.626521	\N	10.210.86.86	\N	报价单: QU202508-002
613	quotation	quotations	19	UPDATE	updated_at	2025-08-25 02:03:33.223278	2025-08-25 02:09:05.625404	2	quah	2025-08-25 02:09:05.626524	\N	10.210.86.86	\N	报价单: QU202508-002
614	quotation	quotations	22	UPDATE	amount	213399.2	213499.2	2	quah	2025-08-25 08:06:09.925691	\N	10.210.23.23	\N	报价单: QU202508-005
615	quotation	quotations	22	UPDATE	updated_at	2025-08-19 03:10:25.711296	2025-08-25 08:06:09.924808	2	quah	2025-08-25 08:06:09.925695	\N	10.210.23.23	\N	报价单: QU202508-005
616	quotation	quotations	22	UPDATE	amount	213499.2	213919.2	2	quah	2025-08-25 08:19:31.533389	\N	10.210.86.86	\N	报价单: QU202508-005
662	customer	companies	89	CREATE	\N	\N	\N	9	alesandro	2025-08-26 13:18:25.811476	\N	10.210.213.88	\N	公司: PT Bintai Kindenko Engineering Indonesia
617	quotation	quotations	22	UPDATE	product_signature	dd0b5b391a240f37dbf845465ad0ed87	38e346b3773508c41005e553c59dbc2f	2	quah	2025-08-25 08:19:31.533396	\N	10.210.86.86	\N	报价单: QU202508-005
618	quotation	quotations	22	UPDATE	implant_total_amount	189364.0	189744.0	2	quah	2025-08-25 08:19:31.5334	\N	10.210.86.86	\N	报价单: QU202508-005
619	quotation	quotations	22	UPDATE	updated_at	2025-08-25 08:06:09.924808	2025-08-25 08:19:31.531985	2	quah	2025-08-25 08:19:31.533404	\N	10.210.86.86	\N	报价单: QU202508-005
620	quotation	quotations	22	UPDATE	amount	213919.2	214090.2	2	quah	2025-08-25 08:20:09.588361	\N	10.210.86.86	\N	报价单: QU202508-005
621	quotation	quotations	22	UPDATE	product_signature	38e346b3773508c41005e553c59dbc2f	3fb154e953d7ee8585ae1366fdb61942	2	quah	2025-08-25 08:20:09.588366	\N	10.210.86.86	\N	报价单: QU202508-005
622	quotation	quotations	22	UPDATE	implant_total_amount	189744.0	189855.0	2	quah	2025-08-25 08:20:09.58837	\N	10.210.86.86	\N	报价单: QU202508-005
623	quotation	quotations	22	UPDATE	updated_at	2025-08-25 08:19:31.531985	2025-08-25 08:20:09.586476	2	quah	2025-08-25 08:20:09.588373	\N	10.210.86.86	\N	报价单: QU202508-005
624	quotation	quotations	22	UPDATE	amount	214090.2	160930.2	2	quah	2025-08-25 08:29:56.439385	\N	10.210.167.141	\N	报价单: QU202508-005
625	quotation	quotations	22	UPDATE	implant_total_amount	189855.0	136375.0	2	quah	2025-08-25 08:29:56.439389	\N	10.210.167.141	\N	报价单: QU202508-005
626	quotation	quotations	22	UPDATE	updated_at	2025-08-25 08:20:09.586476	2025-08-25 08:29:56.438440	2	quah	2025-08-25 08:29:56.439391	\N	10.210.167.141	\N	报价单: QU202508-005
627	quotation	quotations	22	UPDATE	amount	160930.2	264191.2418	2	quah	2025-08-25 08:43:04.161201	\N	10.210.167.141	\N	报价单: QU202508-005
628	quotation	quotations	22	UPDATE	product_signature	3fb154e953d7ee8585ae1366fdb61942	3e0ed8739bed3d0cbe912d899faa6496	2	quah	2025-08-25 08:43:04.161206	\N	10.210.167.141	\N	报价单: QU202508-005
629	quotation	quotations	22	UPDATE	implant_total_amount	136375.0	125500.0	2	quah	2025-08-25 08:43:04.161208	\N	10.210.167.141	\N	报价单: QU202508-005
630	quotation	quotations	22	UPDATE	updated_at	2025-08-25 08:29:56.438440	2025-08-25 08:43:04.160142	2	quah	2025-08-25 08:43:04.16121	\N	10.210.167.141	\N	报价单: QU202508-005
631	quotation	quotations	22	UPDATE	amount	264191.2418	168814.60640000002	2	quah	2025-08-25 08:53:29.219349	\N	10.210.179.122	\N	报价单: QU202508-005
632	quotation	quotations	22	UPDATE	updated_at	2025-08-25 08:43:04.160142	2025-08-25 08:53:29.218203	2	quah	2025-08-25 08:53:29.219355	\N	10.210.179.122	\N	报价单: QU202508-005
633	quotation	quotations	22	UPDATE	amount	168814.6064	169133.60640000002	2	quah	2025-08-25 08:58:33.420442	\N	10.210.23.23	\N	报价单: QU202508-005
634	quotation	quotations	22	UPDATE	product_signature	3e0ed8739bed3d0cbe912d899faa6496	213651fcc40dd9739b8c9593f9b11763	2	quah	2025-08-25 08:58:33.420446	\N	10.210.23.23	\N	报价单: QU202508-005
635	quotation	quotations	22	UPDATE	implant_total_amount	125500.0	125790.0	2	quah	2025-08-25 08:58:33.420449	\N	10.210.23.23	\N	报价单: QU202508-005
636	quotation	quotations	22	UPDATE	updated_at	2025-08-25 08:53:29.218203	2025-08-25 08:58:33.419238	2	quah	2025-08-25 08:58:33.420451	\N	10.210.23.23	\N	报价单: QU202508-005
637	quotation	quotations	22	UPDATE	amount	169133.6064	172004.60640000002	2	quah	2025-08-25 09:00:24.392877	\N	10.210.172.229	\N	报价单: QU202508-005
638	quotation	quotations	22	UPDATE	implant_total_amount	125790.0	128400.0	2	quah	2025-08-25 09:00:24.392882	\N	10.210.172.229	\N	报价单: QU202508-005
639	quotation	quotations	22	UPDATE	updated_at	2025-08-25 08:58:33.419238	2025-08-25 09:00:24.391850	2	quah	2025-08-25 09:00:24.392885	\N	10.210.172.229	\N	报价单: QU202508-005
640	quotation	quotations	22	UPDATE	amount	172004.6064	172004.60640000002	2	quah	2025-08-25 09:00:31.891305	\N	10.210.86.86	\N	报价单: QU202508-005
641	quotation	quotations	22	UPDATE	updated_at	2025-08-25 09:00:24.391850	2025-08-25 09:00:31.890167	2	quah	2025-08-25 09:00:31.891311	\N	10.210.86.86	\N	报价单: QU202508-005
642	quotation	quotations	22	UPDATE	amount	172004.6064	172662.60640000002	2	quah	2025-08-25 09:01:37.80668	\N	10.210.205.21	\N	报价单: QU202508-005
643	quotation	quotations	22	UPDATE	updated_at	2025-08-25 09:00:31.890167	2025-08-25 09:01:37.805465	2	quah	2025-08-25 09:01:37.806686	\N	10.210.205.21	\N	报价单: QU202508-005
644	quotation	quotations	22	UPDATE	amount	172662.6064	172662.60640000002	2	quah	2025-08-25 09:01:50.435571	\N	10.210.172.229	\N	报价单: QU202508-005
645	quotation	quotations	22	UPDATE	updated_at	2025-08-25 09:01:37.805465	2025-08-25 09:01:50.434451	2	quah	2025-08-25 09:01:50.435575	\N	10.210.172.229	\N	报价单: QU202508-005
646	quotation	quotations	22	UPDATE	amount	172662.6064	172662.60640000002	2	quah	2025-08-25 09:01:55.223747	\N	10.210.179.122	\N	报价单: QU202508-005
647	quotation	quotations	22	UPDATE	updated_at	2025-08-25 09:01:50.434451	2025-08-25 09:01:55.222690	2	quah	2025-08-25 09:01:55.223751	\N	10.210.179.122	\N	报价单: QU202508-005
648	project	projects	34	UPDATE	shared_with_users	[8, 7]	[7]	2	quah	2025-08-25 09:28:30.465361	\N	10.210.205.21	\N	项目:  R&F Princess Cove III
649	customer	companies	84	CREATE	\N	\N	\N	3	roy	2025-08-26 06:30:52.257069	\N	10.210.213.88	\N	公司: ACME Associates Global Sdn. Bhd.
650	customer	contacts	102	CREATE	\N	\N	\N	3	roy	2025-08-26 06:33:33.980212	\N	10.210.29.115	\N	记录: Chia Seng Huei
651	customer	contacts	103	CREATE	\N	\N	\N	3	roy	2025-08-26 06:35:02.19988	\N	10.210.167.155	\N	记录: Hii Sing Lung
652	project	projects	45	CREATE	\N	\N	\N	3	roy	2025-08-26 06:53:47.440021	\N	10.210.167.155	\N	项目: TM and Singtel's Nxera Data Centre
653	customer	companies	85	CREATE	\N	\N	\N	3	roy	2025-08-26 06:55:26.011019	\N	10.210.213.88	\N	公司: ST Dynamo DC Sdn Bhd
654	customer	companies	86	CREATE	\N	\N	\N	3	roy	2025-08-26 06:58:54.50636	\N	10.210.24.68	\N	公司: IJM Construction Sdn Bhd
655	project	projects	45	DELETE	\N	\N	\N	3	roy	2025-08-26 07:01:15.141934	\N	10.210.167.155	\N	项目: TM and Singtel's Nxera Data Centre
656	project	projects	46	CREATE	\N	\N	\N	3	roy	2025-08-26 07:08:24.321855	\N	10.210.213.88	\N	项目: TM & Singtel's Nxera Data Centre @ Johor
657	customer	contacts	104	CREATE	\N	\N	\N	3	roy	2025-08-26 07:31:12.160475	\N	10.210.213.88	\N	记录: Ms. Lee Yen Ling
658	customer	companies	87	CREATE	\N	\N	\N	3	roy	2025-08-26 07:52:30.907392	\N	10.210.24.68	\N	公司: NTT Global Data Centres Sdn. Bhd.
659	project	projects	47	CREATE	\N	\N	\N	3	roy	2025-08-26 07:56:03.019705	\N	10.210.29.115	\N	项目: NTT Global Data Centre @ Johor
660	project	projects	48	CREATE	\N	\N	\N	3	roy	2025-08-26 08:11:35.945131	\N	10.210.24.68	\N	项目: ZData (中联数据集团) Hyperscale GP3 DC @ Johor
661	customer	companies	88	CREATE	\N	\N	\N	9	alesandro	2025-08-26 13:14:24.212436	\N	10.210.72.189	\N	公司:  PT Acset Indonusa Tbk.
800	customer	contacts	130	CREATE	\N	\N	\N	3	roy	2025-10-01 01:32:43.77877	\N	10.210.48.171	\N	记录: Tang Pei Fen
663	customer	companies	90	CREATE	\N	\N	\N	9	alesandro	2025-08-26 13:22:10.75865	\N	10.210.24.68	\N	公司: PT.Mitra Cipta Pranata
664	project	projects	49	CREATE	\N	\N	\N	2	quah	2025-08-27 01:18:54.873658	\N	10.210.213.88	\N	项目: MY02_phase 2
665	customer	contacts	105	CREATE	\N	\N	\N	2	quah	2025-08-27 02:11:26.888556	\N	10.210.167.155	\N	记录: Azahar
666	project	projects	50	CREATE	\N	\N	\N	9	alesandro	2025-08-27 04:31:26.461922	\N	10.210.8.178	\N	项目: Yellow Stone Project
667	customer	companies	91	CREATE	\N	\N	\N	9	alesandro	2025-08-27 04:42:06.529916	\N	10.210.29.115	\N	公司: PT. Kuningan Mas Gemilang
668	project	projects	51	CREATE	\N	\N	\N	12	fuyan	2025-08-27 05:48:31.628365	\N	10.210.72.189	\N	项目: NTP-J
669	customer	contacts	47	UPDATE	邮箱	maryam@tactical.com.my	maryam@tacticom.com.my	2	quah	2025-08-28 07:15:25.725041	\N	10.210.72.189	\N	记录: Puteri Maryam
670	customer	contacts	47	UPDATE	updated_at	2025-07-11 09:57:22.626193	2025-08-28 15:15:25.705253	2	quah	2025-08-28 07:15:25.725049	\N	10.210.72.189	\N	记录: Puteri Maryam
671	customer	contacts	106	CREATE	\N	\N	\N	2	quah	2025-08-29 03:15:10.290912	\N	10.210.213.110	\N	记录: Wei Lee Tong
672	quotation	quotations	27	CREATE	\N	\N	\N	12	fuyan	2025-09-01 02:28:19.934149	\N	10.210.213.110	\N	报价单: QU202509-001
673	project	projects	16	DELETE	\N	\N	\N	12	fuyan	2025-09-01 02:47:27.210388	\N	10.210.213.110	\N	项目: KTP - B & C - GDS DC @ Kempas Tech Park
674	project	projects	16	DELETE	\N	\N	\N	12	fuyan	2025-09-01 02:47:51.363793	\N	10.210.213.110	\N	项目: KTP - B & C - GDS DC @ Kempas Tech Park
675	project	projects	16	UPDATE	项目名称	KTP - B & C - GDS DC @ Kempas Tech Park	KTP -  C - GDS DC @ Kempas Tech Park	12	fuyan	2025-09-01 02:50:49.321431	\N	10.210.213.110	\N	项目: KTP -  C - GDS DC @ Kempas Tech Park
676	project	projects	16	DELETE	\N	\N	\N	12	fuyan	2025-09-01 02:50:59.997572	\N	10.210.213.110	\N	项目: KTP -  C - GDS DC @ Kempas Tech Park
677	project	projects	19	UPDATE	项目名称	KTP - C - GDS DC @ Chonburi Thailand	KTP - C - GDS 马来西亚新山	12	fuyan	2025-09-01 02:52:04.391436	\N	10.210.48.21	\N	项目: KTP - C - GDS 马来西亚新山
678	customer	companies	92	CREATE	\N	\N	\N	9	alesandro	2025-09-02 04:59:10.502186	\N	10.210.106.188	\N	公司: PT. Meltech Consultindo Nusa
679	customer	companies	93	CREATE	\N	\N	\N	9	alesandro	2025-09-02 05:05:33.550065	\N	10.210.106.188	\N	公司: PT. Aviasi Pariwisata Indonesia (Persero)/ Injorney Airports/Angkasa Pura II
680	project	projects	50	UPDATE	阶段描述	Currently in the process of seeking information regarding radio frequency work on the project	Currently, I am following up with the consultant to ask about the radio frequency system there and get a layout drawing that we will try to submit the Evertac system through the consultant. I have made an appointment with them on Wednesday afternoon.	9	alesandro	2025-09-02 08:48:37.98678	\N	10.210.48.21	\N	项目: Yellow Stone Project
681	customer	contacts	107	CREATE	\N	\N	\N	9	alesandro	2025-09-02 08:54:39.207906	\N	10.210.57.41	\N	记录: Handoko
682	customer	contacts	107	UPDATE	部门	Electronic Airports Dep	Airports Electronic Devision	9	alesandro	2025-09-02 08:55:53.822951	\N	10.210.48.21	\N	记录: Handoko
683	customer	contacts	107	UPDATE	updated_at	2025-09-02 16:54:39.192890	2025-09-02 16:55:53.808266	9	alesandro	2025-09-02 08:55:53.822958	\N	10.210.48.21	\N	记录: Handoko
684	project	projects	50	UPDATE	阶段描述	Currently, I am following up with the consultant to ask about the radio frequency system there and get a layout drawing that we will try to submit the Evertac system through the consultant. I have made an appointment with them on Wednesday afternoon.	This project is currently under construction, and the Mainkon company is PT. Acset.	9	alesandro	2025-09-02 09:07:42.214205	\N	10.210.68.90	\N	项目: Yellow Stone Project
685	customer	contacts	108	CREATE	\N	\N	\N	9	alesandro	2025-09-02 09:25:13.187459	\N	10.210.213.110	\N	记录: Asep
686	customer	contacts	108	UPDATE	部门		Project Devision	9	alesandro	2025-09-02 09:25:49.107471	\N	10.210.68.90	\N	记录: Asep
687	customer	contacts	108	UPDATE	position		Cordinator Project	9	alesandro	2025-09-02 09:25:49.107477	\N	10.210.68.90	\N	记录: Asep
688	customer	contacts	108	UPDATE	updated_at	2025-09-02 17:25:13.226254	2025-09-02 17:25:49.090483	9	alesandro	2025-09-02 09:25:49.107481	\N	10.210.68.90	\N	记录: Asep
689	customer	companies	94	CREATE	\N	\N	\N	3	roy	2025-09-02 14:27:23.111833	\N	10.210.68.90	\N	公司: NV5 Malaysia
690	customer	contacts	109	CREATE	\N	\N	\N	3	roy	2025-09-02 14:29:01.391954	\N	10.210.57.41	\N	记录: Mohd. Abdul Hadi
691	customer	contacts	110	CREATE	\N	\N	\N	3	roy	2025-09-02 14:39:27.537838	\N	10.210.221.22	\N	记录: Ms. Atiqah
692	project	projects	52	CREATE	\N	\N	\N	2	quah	2025-09-03 00:58:28.07295	\N	10.210.48.21	\N	项目: PUTRAJAYA MARRIOTT HOTEL
693	quotation	quotations	28	CREATE	\N	\N	\N	2	quah	2025-09-03 01:05:35.32314	\N	10.210.48.21	\N	报价单: QU202509-001
694	customer	contacts	111	CREATE	\N	\N	\N	2	quah	2025-09-03 01:15:43.080534	\N	10.210.213.110	\N	记录: Nurshaliana
695	project	projects	51	DELETE	\N	\N	\N	1	admin	2025-09-08 03:53:36.547804	\N	10.210.114.122	\N	项目: NTP-J
696	quotation	quotations	14	UPDATE	amount	63959.0	123775.0	1	admin	2025-09-08 03:58:08.216997	\N	10.210.114.122	\N	报价单: QU202507-005
697	quotation	quotations	14	UPDATE	项目阶段	\N	tendering	1	admin	2025-09-08 03:58:08.217001	\N	10.210.114.122	\N	报价单: QU202507-005
698	quotation	quotations	14	UPDATE	项目类型	\N	channel_follow	1	admin	2025-09-08 03:58:08.217003	\N	10.210.114.122	\N	报价单: QU202507-005
699	quotation	quotations	14	UPDATE	product_signature	f7c2aebb5b75587f2e182d1ea20fc4b4	feeba872a43a82d6ae2dbed718b5fe21	1	admin	2025-09-08 03:58:08.217005	\N	10.210.114.122	\N	报价单: QU202507-005
700	quotation	quotations	14	UPDATE	implant_total_amount	63959.0	123775.0	1	admin	2025-09-08 03:58:08.217007	\N	10.210.114.122	\N	报价单: QU202507-005
701	quotation	quotations	14	UPDATE	updated_at	2025-07-29 01:35:37.227872	2025-09-08 03:58:08.215903	1	admin	2025-09-08 03:58:08.217009	\N	10.210.114.122	\N	报价单: QU202507-005
702	quotation	quotations	21	UPDATE	amount	68315.0	70135.0	1	admin	2025-09-08 04:11:53.837646	\N	10.210.57.17	\N	报价单: QU202508-004
703	quotation	quotations	21	UPDATE	product_signature	c419dfe704112e849937c1597b5b8d5b	fa9e8f69c084e7f58ec9d4b74ada7553	1	admin	2025-09-08 04:11:53.837651	\N	10.210.57.17	\N	报价单: QU202508-004
704	quotation	quotations	21	UPDATE	implant_total_amount	68315.0	70135.0	1	admin	2025-09-08 04:11:53.837653	\N	10.210.57.17	\N	报价单: QU202508-004
705	quotation	quotations	21	UPDATE	updated_at	2025-08-18 10:06:21.381479	2025-09-08 04:11:53.836596	1	admin	2025-09-08 04:11:53.837655	\N	10.210.57.17	\N	报价单: QU202508-004
706	quotation	quotations	12	UPDATE	amount	82335.69	86764.58	1	admin	2025-09-08 04:30:46.130257	\N	10.210.52.67	\N	报价单: QU202507-003
707	quotation	quotations	12	UPDATE	product_signature	008db7c832da69fa507ed889966fd81c	ab1c60c73b2ede1d30516a0cb1b17f78	1	admin	2025-09-08 04:30:46.130262	\N	10.210.52.67	\N	报价单: QU202507-003
708	quotation	quotations	12	UPDATE	implant_total_amount	63339.0	81350.0	1	admin	2025-09-08 04:30:46.130266	\N	10.210.52.67	\N	报价单: QU202507-003
709	quotation	quotations	12	UPDATE	updated_at	2025-07-22 07:14:37.445900	2025-09-08 04:30:46.128760	1	admin	2025-09-08 04:30:46.130269	\N	10.210.52.67	\N	报价单: QU202507-003
710	project	projects	16	DELETE	\N	\N	\N	1	admin	2025-09-08 04:31:52.691	\N	10.210.191.202	\N	项目: KTP -  C - GDS DC @ Kempas Tech Park
711	project	projects	16	DELETE	\N	\N	\N	1	admin	2025-09-08 04:32:13.808825	\N	10.210.57.17	\N	项目: KTP -  C - GDS DC @ Kempas Tech Park
712	project	projects	53	CREATE	\N	\N	\N	12	fuyan	2025-09-08 05:46:21.464229	\N	10.210.143.255	\N	项目: NTP-F-gds数据中心改造
713	quotation	quotations	29	CREATE	\N	\N	\N	12	fuyan	2025-09-08 05:48:48.042141	\N	10.210.57.17	\N	报价单: QU202509-002
714	project	projects	54	CREATE	\N	\N	\N	12	fuyan	2025-09-08 05:51:17.89574	\N	10.210.143.255	\N	项目: NTP-H GDS数据中心改造
715	quotation	quotations	30	CREATE	\N	\N	\N	12	fuyan	2025-09-08 05:51:53.248155	\N	10.210.57.17	\N	报价单: QU202509-003
716	quotation	quotations	13	UPDATE	amount	152585.3	252405.0	12	fuyan	2025-09-08 05:55:27.25333	\N	10.210.213.116	\N	报价单: QU202507-004
717	quotation	quotations	13	UPDATE	product_signature	05e4e23cd00f87c32a3c726816dd4710	0ddb5e064310dcb2ff46f63359905b8b	12	fuyan	2025-09-08 05:55:27.253336	\N	10.210.213.116	\N	报价单: QU202507-004
718	quotation	quotations	13	UPDATE	implant_total_amount	123609.0	252405.0	12	fuyan	2025-09-08 05:55:27.253341	\N	10.210.213.116	\N	报价单: QU202507-004
719	quotation	quotations	13	UPDATE	updated_at	2025-07-22 08:25:41.483086	2025-09-08 05:55:27.251674	12	fuyan	2025-09-08 05:55:27.253345	\N	10.210.213.116	\N	报价单: QU202507-004
720	customer	contacts	112	CREATE	\N	\N	\N	9	alesandro	2025-09-09 01:55:15.937584	\N	10.210.57.17	\N	记录: Mr Endang
721	quotation	quotations	11	UPDATE	amount	11748.12	14170.0	1	admin	2025-09-16 02:38:13.683852	\N	10.210.173.115	\N	报价单: QU202507-002
722	quotation	quotations	11	UPDATE	product_signature	09336c18a29e7e863e1b4fdbb8b17b69	fb19f7f4bca212a2c2dd8d6f75fad726	1	admin	2025-09-16 02:38:13.683857	\N	10.210.173.115	\N	报价单: QU202507-002
723	quotation	quotations	11	UPDATE	implant_total_amount	9579.0	12839.0	1	admin	2025-09-16 02:38:13.683859	\N	10.210.173.115	\N	报价单: QU202507-002
724	quotation	quotations	11	UPDATE	updated_at	2025-07-09 01:46:53.276624	2025-09-16 02:38:13.682609	1	admin	2025-09-16 02:38:13.683861	\N	10.210.173.115	\N	报价单: QU202507-002
725	customer	companies	95	CREATE	\N	\N	\N	9	alesandro	2025-09-16 09:13:35.926948	\N	10.210.112.165	\N	公司: PT.  Duta Pratama Engineering
726	customer	contacts	113	CREATE	\N	\N	\N	9	alesandro	2025-09-16 09:13:58.13819	\N	10.210.245.123	\N	记录: Widodo
727	customer	contacts	113	UPDATE	部门		Project Devision	9	alesandro	2025-09-16 09:14:17.843847	\N	10.210.112.165	\N	记录: Widodo
728	customer	contacts	113	UPDATE	position		Cordinator Project	9	alesandro	2025-09-16 09:14:17.843854	\N	10.210.112.165	\N	记录: Widodo
729	customer	contacts	113	UPDATE	updated_at	2025-09-16 17:13:58.119153	2025-09-16 17:14:17.827164	9	alesandro	2025-09-16 09:14:17.843859	\N	10.210.112.165	\N	记录: Widodo
730	customer	companies	95	UPDATE	备注	DUTA PRATAMA ENGINEERING A mechanical/electrical planning consulting services company that started operating in 2016. Although new, we have been trusted to handle various infrastructure projects, such as factories, office centers, hotels, apartments, shopping centers, campuses, and hospitals.\r\nIn our work, we uphold the principle that business is not only about seeking profit, but also providing added value, both to clients, shareholders, contractors, employees, and other parties related to the project.	DUTA PRATAMA ENGINEERING A mechanical/electrical planning consulting services company that started operating in 2016. Although new, we have been trusted to handle various infrastructure projects, such as factories, office centers, hotels, apartments, shopping centers, campuses, and hospitals.\r\n	9	alesandro	2025-09-16 09:21:20.016749	\N	10.210.173.115	\N	公司: PT.  Duta Pratama Engineering
731	customer	contacts	114	CREATE	\N	\N	\N	3	roy	2025-09-16 12:14:43.731927	\N	10.210.89.197	\N	记录: Mr. Wu (吴锋艳)
732	project	projects	49	DELETE	\N	\N	\N	2	quah	2025-09-17 02:10:11.514053	\N	10.210.112.165	\N	项目: MY02_phase 2
733	project	projects	55	CREATE	\N	\N	\N	12	fuyan	2025-09-17 06:47:12.74802	\N	10.210.202.188	\N	项目: BDC-泰国数据中心B1-2-3项目
734	project	projects	56	CREATE	\N	\N	\N	12	fuyan	2025-09-18 04:35:19.927756	\N	10.210.112.165	\N	项目: GDS-KTP-J数据中心项目
735	customer	companies	96	CREATE	\N	\N	\N	1	admin	2025-09-19 05:56:50.899797	\N	10.210.173.80	\N	公司: 上海建工集团
736	project	projects	57	CREATE	\N	\N	\N	1	admin	2025-09-19 05:58:27.749765	\N	10.210.173.80	\N	项目: Changi airport T5 
737	customer	contacts	115	CREATE	\N	\N	\N	1	admin	2025-09-19 06:02:34.215135	\N	10.210.238.106	\N	记录: 吴亮
738	customer	contacts	116	CREATE	\N	\N	\N	1	admin	2025-09-19 06:26:12.321745	\N	10.210.53.88	\N	记录: Alber wang
739	customer	contacts	117	CREATE	\N	\N	\N	2	quah	2025-09-19 07:58:59.268616	\N	10.210.247.233	\N	记录: Khoo Zhong Yi
740	project	projects	58	CREATE	\N	\N	\N	12	fuyan	2025-09-19 08:33:02.871045	\N	10.210.53.88	\N	项目: 泰国-GDS-CTP-C数据中心
741	quotation	quotations	13	UPDATE	amount	252405.0	225140.0	1	admin	2025-09-22 02:10:26.4052	\N	10.210.125.185	\N	报价单: QU202507-004
742	quotation	quotations	13	UPDATE	product_signature	0ddb5e064310dcb2ff46f63359905b8b	015534ec2a8c6b0967ca7c475a157606	1	admin	2025-09-22 02:10:26.405204	\N	10.210.125.185	\N	报价单: QU202507-004
743	quotation	quotations	13	UPDATE	implant_total_amount	252405.0	225140.0	1	admin	2025-09-22 02:10:26.405207	\N	10.210.125.185	\N	报价单: QU202507-004
744	quotation	quotations	13	UPDATE	updated_at	2025-09-08 05:55:27.251674	2025-09-22 02:10:26.403086	1	admin	2025-09-22 02:10:26.405209	\N	10.210.125.185	\N	报价单: QU202507-004
745	project	projects	59	CREATE	\N	\N	\N	9	alesandro	2025-09-23 10:12:43.236849	\N	10.210.78.84	\N	项目: The Tunnel at The Mining In Kalimantan 
746	customer	companies	97	CREATE	\N	\N	\N	2	quah	2025-09-23 18:05:08.945156	\N	10.210.53.213	\N	公司: Ingenium Systems Sdn Bhd
747	customer	companies	98	CREATE	\N	\N	\N	2	quah	2025-09-23 18:09:13.158143	\N	10.210.82.159	\N	公司: Foursons Engineering Sdn Bhd
748	customer	contacts	118	CREATE	\N	\N	\N	2	quah	2025-09-23 18:10:49.084011	\N	10.210.82.159	\N	记录: Kuan Meng Xian
749	customer	contacts	119	CREATE	\N	\N	\N	2	quah	2025-09-23 18:13:50.868871	\N	10.210.82.159	\N	记录: Javen Low
750	customer	contacts	120	CREATE	\N	\N	\N	3	roy	2025-09-24 01:23:55.855047	\N	10.210.225.207	\N	记录: 焦洋
751	project	projects	60	CREATE	\N	\N	\N	3	roy	2025-09-24 01:34:34.055972	\N	10.210.78.84	\N	项目: MY02 - Phase 1 Block 3 - Bridge DC @ Cyberjaya
752	customer	companies	99	CREATE	\N	\N	\N	2	quah	2025-09-24 01:56:33.479483	\N	10.210.53.213	\N	公司: UM Specialist Centre (UMSC)
753	customer	contacts	121	CREATE	\N	\N	\N	2	quah	2025-09-24 01:57:50.031364	\N	10.210.36.131	\N	记录: Muhammad Hisyam bin Taib
754	project	projects	61	CREATE	\N	\N	\N	2	quah	2025-09-24 01:59:40.447326	\N	10.210.82.159	\N	项目: Hospital (Signal coverage problem especially in car park area)
755	customer	companies	100	CREATE	\N	\N	\N	9	alesandro	2025-09-24 02:45:50.160761	\N	10.210.82.159	\N	公司: PT. Mega Akses Persada
756	quotation	quotations	22	UPDATE	amount	172662.6064	171971.60640000002	2	quah	2025-09-26 02:13:51.426672	\N	10.210.139.87	\N	报价单: QU202508-005
757	quotation	quotations	22	UPDATE	product_signature	213651fcc40dd9739b8c9593f9b11763	67f16398c5c4156625cfdbc6f17692a0	2	quah	2025-09-26 02:13:51.426677	\N	10.210.139.87	\N	报价单: QU202508-005
758	quotation	quotations	22	UPDATE	implant_total_amount	128400.0	127909.0	2	quah	2025-09-26 02:13:51.426679	\N	10.210.139.87	\N	报价单: QU202508-005
759	quotation	quotations	22	UPDATE	updated_at	2025-08-25 09:01:55.222690	2025-09-26 02:13:51.424696	2	quah	2025-09-26 02:13:51.426681	\N	10.210.139.87	\N	报价单: QU202508-005
760	project	projects	62	CREATE	\N	\N	\N	12	fuyan	2025-09-29 04:21:22.025848	\N	10.210.161.249	\N	项目: 富力公主湾三期
761	project	projects	18	UPDATE	交付预测	2025-10-15	2026-06-30	12	fuyan	2025-09-29 04:23:17.963866	\N	10.210.139.87	\N	项目: CTP - A - GDS DC @ Chonburi Thailand
762	project	projects	18	UPDATE	厂商负责人	3	12	12	fuyan	2025-09-29 04:23:17.963871	\N	10.210.139.87	\N	项目: CTP - A - GDS DC @ Chonburi Thailand
763	customer	companies	101	CREATE	\N	\N	\N	2	quah	2025-09-30 03:51:31.082705	\N	10.210.48.171	\N	公司: Columbia Asia Hospital Bukit Rimau
764	customer	contacts	122	CREATE	\N	\N	\N	2	quah	2025-09-30 03:55:20.674172	\N	10.210.161.203	\N	记录: Jack Chan
765	project	projects	63	CREATE	\N	\N	\N	2	quah	2025-09-30 04:00:26.840176	\N	10.210.48.171	\N	项目: Upgrading communication coverage for basement
766	customer	companies	102	CREATE	\N	\N	\N	2	quah	2025-09-30 04:05:15.788886	\N	10.210.191.58	\N	公司: Jinko Solar Technology Sdn Bhd
767	customer	contacts	123	CREATE	\N	\N	\N	2	quah	2025-09-30 04:06:32.560414	\N	10.210.191.58	\N	记录: Koay Kean Pin
768	project	projects	64	CREATE	\N	\N	\N	2	quah	2025-09-30 04:09:39.501456	\N	10.210.182.134	\N	项目: Implement Base Station for new plant 
769	customer	companies	103	CREATE	\N	\N	\N	2	quah	2025-09-30 04:13:19.71239	\N	10.210.182.134	\N	公司: RAG Solution Sdn Bhd
770	customer	contacts	124	CREATE	\N	\N	\N	2	quah	2025-09-30 04:14:52.357589	\N	10.210.191.58	\N	记录: Ragu
771	project	projects	65	CREATE	\N	\N	\N	2	quah	2025-09-30 04:22:53.509827	\N	10.210.139.102	\N	项目: Communication Support for event
772	customer	companies	104	CREATE	\N	\N	\N	2	quah	2025-09-30 04:25:06.641225	\N	10.210.182.134	\N	公司: INNSIDE Hotel by Meliá Kuala Lumpur Cheras
773	customer	contacts	125	CREATE	\N	\N	\N	2	quah	2025-09-30 04:26:48.153574	\N	10.210.161.203	\N	记录: Darshan Ram
774	project	projects	66	CREATE	\N	\N	\N	2	quah	2025-09-30 04:27:46.873398	\N	10.210.161.203	\N	项目: Upgrading from point-to-point into walkie-talkie system
775	project	projects	67	CREATE	\N	\N	\N	2	quah	2025-09-30 04:34:14.436219	\N	10.210.139.102	\N	项目: GDS-KTP-C数据中心项目
776	quotation	quotations	31	CREATE	\N	\N	\N	2	quah	2025-09-30 04:42:26.065453	\N	10.210.161.203	\N	报价单: QU202509-004
777	quotation	quotations	29	UPDATE	amount	23930.0	22040.0	2	quah	2025-09-30 04:56:31.476605	\N	10.210.48.171	\N	报价单: QU202509-002
778	quotation	quotations	29	UPDATE	product_signature	13d52a3973ae3599	da6669354466b81e0d7cef4bbef80ef6	2	quah	2025-09-30 04:56:31.476612	\N	10.210.48.171	\N	报价单: QU202509-002
779	quotation	quotations	29	UPDATE	implant_total_amount	23930.0	22040.0	2	quah	2025-09-30 04:56:31.476615	\N	10.210.48.171	\N	报价单: QU202509-002
780	quotation	quotations	29	UPDATE	updated_at	2025-09-08 05:48:48.022307	2025-09-30 04:56:31.475341	2	quah	2025-09-30 04:56:31.476617	\N	10.210.48.171	\N	报价单: QU202509-002
781	quotation	quotations	22	UPDATE	amount	171971.6064	171971.60640000002	2	quah	2025-09-30 05:00:41.708553	\N	10.210.182.220	\N	报价单: QU202508-005
782	quotation	quotations	22	UPDATE	updated_at	2025-09-26 02:13:51.424696	2025-09-30 05:00:41.705402	2	quah	2025-09-30 05:00:41.70856	\N	10.210.182.220	\N	报价单: QU202508-005
783	quotation	quotations	32	CREATE	\N	\N	\N	2	quah	2025-09-30 05:01:21.667377	\N	10.210.161.203	\N	报价单: QU202509-005
784	quotation	quotations	32	UPDATE	product_signature	125008580b9f31fe	a0179ce456b21ef33a8d90796ee52d58	2	quah	2025-09-30 05:01:43.326581	\N	10.210.182.134	\N	报价单: QU202509-005
785	quotation	quotations	32	UPDATE	updated_at	2025-09-30 05:01:21.643552	2025-09-30 05:01:43.325655	2	quah	2025-09-30 05:01:43.326585	\N	10.210.182.134	\N	报价单: QU202509-005
786	project	projects	63	UPDATE	项目名称	Upgrading communication coverage for basement	Columbia Hospital _Upgrading communication coverage for basement	2	quah	2025-09-30 05:05:25.384647	\N	10.210.48.171	\N	项目: Columbia Hospital _Upgrading communication coverage for basement
787	project	projects	64	UPDATE	项目名称	Implement Base Station for new plant 	Jinko Solar Tech_Implement Base Station for new plant 	2	quah	2025-09-30 05:09:37.206574	\N	10.210.161.203	\N	项目: Jinko Solar Tech_Implement Base Station for new plant 
788	project	projects	66	UPDATE	项目名称	Upgrading from point-to-point into walkie-talkie system	Innside KL Cheras_Upgrading into walkie-talkie system	2	quah	2025-09-30 05:10:34.472732	\N	10.210.182.220	\N	项目: Innside KL Cheras_Upgrading into walkie-talkie system
789	project	projects	65	UPDATE	项目名称	Communication Support for event	Event_Communication Support	2	quah	2025-09-30 05:11:06.578632	\N	10.210.161.203	\N	项目: Event_Communication Support
790	quotation	quotations	30	UPDATE	product_signature	7fec5b9702690fca	41cf054695b7db483f743461b54a6ec7	2	quah	2025-09-30 05:19:16.104858	\N	10.210.139.102	\N	报价单: QU202509-003
791	quotation	quotations	30	UPDATE	updated_at	2025-09-08 05:51:53.222699	2025-09-30 05:19:16.103965	2	quah	2025-09-30 05:19:16.104863	\N	10.210.139.102	\N	报价单: QU202509-003
792	project	projects	68	CREATE	\N	\N	\N	9	alesandro	2025-09-30 10:00:16.133666	\N	10.210.182.220	\N	项目: PT BYD Indonesia 
793	project	projects	69	CREATE	\N	\N	\N	9	alesandro	2025-09-30 10:12:02.334	\N	10.210.48.171	\N	项目: PT. hiron indonesia industry
794	project	projects	69	UPDATE	项目名称	PT. hiron indonesia industry	PT. Hiron Indonesia Industry	9	alesandro	2025-09-30 10:12:26.85259	\N	10.210.182.134	\N	项目: PT. Hiron Indonesia Industry
795	customer	contacts	126	CREATE	\N	\N	\N	2	quah	2025-10-01 01:26:39.440008	\N	10.210.48.171	\N	记录: Fizwan
796	customer	companies	105	CREATE	\N	\N	\N	3	roy	2025-10-01 01:26:59.650613	\N	10.210.48.171	\N	公司: Teknik Johan Telecommunication Sdn Bhd
797	customer	contacts	127	CREATE	\N	\N	\N	2	quah	2025-10-01 01:28:09.904066	\N	10.210.182.134	\N	记录: 张总
798	customer	contacts	128	CREATE	\N	\N	\N	3	roy	2025-10-01 01:28:23.399889	\N	10.210.139.102	\N	记录: Daniel Yong
799	customer	contacts	129	CREATE	\N	\N	\N	2	quah	2025-10-01 01:29:02.024802	\N	10.210.48.171	\N	记录: Daphne Tay
801	customer	companies	106	CREATE	\N	\N	\N	3	roy	2025-10-01 01:37:20.749859	\N	10.210.191.58	\N	公司: MCE Consulting Sdn Bhd
802	customer	contacts	131	CREATE	\N	\N	\N	3	roy	2025-10-01 01:38:35.667588	\N	10.210.182.220	\N	记录: Lee Jian Xi
803	customer	companies	107	CREATE	\N	\N	\N	3	roy	2025-10-01 01:40:56.686177	\N	10.210.161.203	\N	公司: Security Marketing Sdn. Bhd.
804	customer	contacts	132	CREATE	\N	\N	\N	3	roy	2025-10-01 01:42:30.201968	\N	10.210.161.203	\N	记录: Andrew Shu
805	project	projects	68	UPDATE	阶段描述	The structural and civil engineering projects are currently underway. The owner is a Chinese company. Maincont is also a Chinese company, PT China State Construction.	PT BYD Indonesia is building an electric car factory in the Subang Smartpolitan Industrial Estate, West Java, which will be BYD's largest manufacturing facility in Southeast Asia. This development is part of an investment of approximately US$1.3 billion (approximately Rp 21 trillion) on 108 hectares of land, with a target start-up date of early 2026.\r\n\r\nThe structural and civil engineering projects are currently underway. The owner is a Chinese company. Maincont is also a Chinese company, PT China State Construction.	9	alesandro	2025-10-01 03:17:46.657263	\N	10.210.182.134	\N	项目: PT BYD Indonesia 
806	customer	companies	108	CREATE	\N	\N	\N	2	quah	2025-10-02 02:01:51.807858	\N	10.210.161.203	\N	公司: Cekap Technical Services Sdn Bhd
807	customer	contacts	133	CREATE	\N	\N	\N	2	quah	2025-10-02 02:04:01.902934	\N	10.210.48.171	\N	记录: Mohammad Adam Bin Ismail
808	customer	contacts	134	CREATE	\N	\N	\N	2	quah	2025-10-02 02:06:35.081642	\N	10.210.182.220	\N	记录: Syuhada Suliman
809	customer	contacts	135	CREATE	\N	\N	\N	2	quah	2025-10-02 02:07:42.773063	\N	10.210.182.220	\N	记录: Nurain Zayanah Nadaruddin 
810	customer	contacts	136	CREATE	\N	\N	\N	2	quah	2025-10-02 02:09:01.926277	\N	10.210.182.134	\N	记录: Dr. Fatin Harun
811	customer	contacts	137	CREATE	\N	\N	\N	2	quah	2025-10-02 02:10:20.578284	\N	10.210.182.220	\N	记录: Alif Nazarulasmal
812	customer	contacts	138	CREATE	\N	\N	\N	2	quah	2025-10-02 02:11:23.366536	\N	10.210.191.58	\N	记录: Noor Liyana Nazarudin
813	project	projects	70	CREATE	\N	\N	\N	2	quah	2025-10-03 04:33:32.696759	\N	10.210.139.102	\N	项目: World Empire City Shopping Mall 
814	quotation	quotations	33	CREATE	\N	\N	\N	2	quah	2025-10-03 04:34:41.519157	\N	10.210.182.220	\N	报价单: QU202510-001
815	project	projects	61	UPDATE	owner_id	roy.lim	quah	3	roy.lim	2025-10-07 01:48:16.137471	项目负责人从 roy.lim 变更为 quah	10.210.182.134	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	\N
816	quotation	quotations	33	UPDATE	updated_at	2025-10-03 04:34:41.481176	2025-10-07 03:58:18.077287	2	quah	2025-10-07 03:58:18.078037	\N	10.210.191.58	\N	报价单: QU202510-001
817	quotation	quotations	33	UPDATE	amount	3938.0	175967.66000000003	2	quah	2025-10-07 04:16:35.168576	\N	10.210.48.171	\N	报价单: QU202510-001
818	quotation	quotations	33	UPDATE	product_signature	a0179ce456b21ef33a8d90796ee52d58	e7d08e4941d1bd76a5ea6c62a014d351	2	quah	2025-10-07 04:16:35.168581	\N	10.210.48.171	\N	报价单: QU202510-001
819	quotation	quotations	33	UPDATE	implant_total_amount	3290.0	107575.0	2	quah	2025-10-07 04:16:35.168585	\N	10.210.48.171	\N	报价单: QU202510-001
820	quotation	quotations	33	UPDATE	updated_at	2025-10-07 03:58:18.077287	2025-10-07 04:16:35.166337	2	quah	2025-10-07 04:16:35.168588	\N	10.210.48.171	\N	报价单: QU202510-001
821	project	projects	61	UPDATE	项目名称	Hospital (Signal coverage problem especially in car park area)	UMSC Hospital_Upgrade Signal Coverage 	2	quah	2025-10-07 04:30:55.018853	\N	10.210.139.102	\N	项目: UMSC Hospital_Upgrade Signal Coverage 
822	project	projects	61	UPDATE	阶段描述		Signal coverage problem especially in car park area	2	quah	2025-10-07 04:30:55.018858	\N	10.210.139.102	\N	项目: UMSC Hospital_Upgrade Signal Coverage 
823	project	projects	61	UPDATE	项目名称	UMSC Hospital_Upgrade Signal Coverage 	UMSC Hospital_Upgrade Signal Coverage at Car Park Area	2	quah	2025-10-07 04:32:19.690203	\N	10.210.182.134	\N	项目: UMSC Hospital_Upgrade Signal Coverage at Car Park Area
824	customer	companies	109	CREATE	\N	\N	\N	9	alesandro	2025-10-07 09:35:08.937879	\N	10.210.182.220	\N	公司: LG CNS
825	customer	contacts	139	CREATE	\N	\N	\N	9	alesandro	2025-10-07 09:37:50.237053	\N	10.210.161.203	\N	记录: Moonsun Song
826	customer	contacts	140	CREATE	\N	\N	\N	9	alesandro	2025-10-07 09:52:35.791703	\N	10.210.139.102	\N	记录: Johan
827	customer	companies	110	CREATE	\N	\N	\N	9	alesandro	2025-10-07 10:12:29.761029	\N	10.210.182.134	\N	公司: PT China State Construction Overseas Development Shanghai
828	customer	contacts	141	CREATE	\N	\N	\N	9	alesandro	2025-10-07 10:15:40.278198	\N	10.210.182.220	\N	记录: Andi
829	project	projects	31	UPDATE	项目类型	business_opportunity	sales_focus	1	admin	2025-10-08 08:32:32.755123	\N	10.210.182.220	\N	项目: TM Iskandar Puteri Data Centre (IPDC)
830	project	projects	52	UPDATE	owner_id	quah	yusry.lee	2	quah	2025-10-08 08:33:48.716702	项目负责人从 quah 变更为 yusry.lee	10.210.161.203	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36	\N
831	project	projects	19	DELETE	\N	\N	\N	1	admin	2025-10-08 08:38:09.098378	\N	10.210.48.171	\N	项目: KTP - C - GDS 马来西亚新山
832	customer	companies	111	CREATE	\N	\N	\N	2	quah	2025-10-08 09:01:48.102724	\N	10.210.161.203	\N	公司: Powerware Systems Sdn Bhd.
833	customer	contacts	142	CREATE	\N	\N	\N	2	quah	2025-10-08 09:03:04.297668	\N	10.210.191.58	\N	记录: Lee Pei Jinn
834	project	projects	19	DELETE	\N	\N	\N	1	admin	2025-10-09 00:50:30.729974	\N	10.210.161.203	\N	项目: KTP - C - GDS 马来西亚新山
835	project	projects	19	DELETE	\N	\N	\N	1	admin	2025-10-09 01:08:50.671397	\N	10.210.182.220	\N	项目: KTP - C - GDS 马来西亚新山
836	project	projects	63	UPDATE	owner_id	quah	yusry.lee	2	quah	2025-10-10 08:01:44.530504	项目负责人从 quah 变更为 yusry.lee	10.210.182.134	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36	\N
837	customer	companies	112	CREATE	\N	\N	\N	1	admin	2025-10-11 06:43:30.784239	\N	10.210.191.58	\N	公司: Malaysian Communications and Multimedia Commission
838	customer	contacts	143	CREATE	\N	\N	\N	1	admin	2025-10-11 06:44:24.809589	\N	10.210.191.58	\N	记录: Arifah Aziela Jamaludin
839	quotation	quotations	34	CREATE	\N	\N	\N	1	admin	2025-10-11 10:49:52.239166	\N	10.210.182.220	\N	报价单: QU202510-002
840	quotation	quotations	34	DELETE	\N	\N	\N	1	admin	2025-10-11 10:50:08.401742	\N	10.210.182.134	\N	报价单: QU202510-002
841	customer	companies	113	CREATE	\N	\N	\N	9	alesandro	2025-10-13 04:49:53.7444	\N	10.210.139.102	\N	公司: Tzu Chi Hospital
842	project	projects	71	CREATE	\N	\N	\N	9	alesandro	2025-10-14 02:06:17.27956	\N	10.210.182.220	\N	项目: Zhu Chi Hospital PIK
843	customer	companies	114	CREATE	\N	\N	\N	9	alesandro	2025-10-14 02:10:27.913084	\N	10.210.161.203	\N	公司: PT Teknologi Chayani Harsa (TechSolutions)
844	customer	contacts	144	CREATE	\N	\N	\N	9	alesandro	2025-10-14 02:12:43.70119	\N	10.210.161.203	\N	记录: Ilham Pratomo
845	customer	contacts	145	CREATE	\N	\N	\N	9	alesandro	2025-10-14 02:15:22.6052	\N	10.210.191.58	\N	记录: Hendry A. Hermawan
846	customer	contacts	145	UPDATE	position	Manager	Engineer Manager	9	alesandro	2025-10-14 02:16:39.170393	\N	10.210.182.134	\N	记录: Hendry A. Hermawan
847	customer	contacts	145	UPDATE	updated_at	2025-10-14 10:15:22.653686	2025-10-14 10:16:39.155519	9	alesandro	2025-10-14 02:16:39.170399	\N	10.210.182.134	\N	记录: Hendry A. Hermawan
848	customer	companies	115	CREATE	\N	\N	\N	9	alesandro	2025-10-14 02:23:17.928819	\N	10.210.182.220	\N	公司: PT. Citradata PurnaKharisma
849	customer	contacts	146	CREATE	\N	\N	\N	9	alesandro	2025-10-14 02:24:09.400838	\N	10.210.191.58	\N	记录: Ajri
850	customer	companies	116	CREATE	\N	\N	\N	3	roy	2025-10-14 07:02:24.798019	\N	10.210.139.102	\N	公司: MK Land Holdings Berhad
851	customer	contacts	147	CREATE	\N	\N	\N	3	roy	2025-10-14 07:05:33.460418	\N	10.210.191.58	\N	记录: Muhamad Hidayat bin Zabidi
852	project	projects	72	CREATE	\N	\N	\N	3	roy	2025-10-14 07:11:35.4931	\N	10.210.182.134	\N	项目: MK Land Data Centre @ Perak
853	customer	companies	117	CREATE	\N	\N	\N	3	roy	2025-10-14 07:15:27.739554	\N	10.210.191.58	\N	公司: Mega Jati Consult Sdn. Bhd.
854	customer	contacts	148	CREATE	\N	\N	\N	3	roy	2025-10-14 07:18:11.706979	\N	10.210.161.203	\N	记录: Aina Filza
855	project	projects	47	DELETE	\N	\N	\N	3	roy	2025-10-14 07:24:22.865271	\N	10.210.125.153	\N	项目: NTT Global Data Centre @ Johor
856	customer	companies	118	CREATE	\N	\N	\N	3	roy	2025-10-15 01:22:32.369151	\N	10.210.182.220	\N	公司: Thinker Engineering Sdn Bhd
857	customer	contacts	149	CREATE	\N	\N	\N	3	roy	2025-10-15 01:24:23.424505	\N	10.210.182.134	\N	记录: Ms. Amani Che Rus
858	customer	companies	119	CREATE	\N	\N	\N	3	roy	2025-10-15 01:30:34.395469	\N	10.210.161.203	\N	公司: PMX MALAYSIA SDN. BHD.
859	customer	contacts	150	CREATE	\N	\N	\N	3	roy	2025-10-15 01:32:24.396792	\N	10.210.182.220	\N	记录: Tang Lai Hing
860	project	projects	73	CREATE	\N	\N	\N	3	roy	2025-10-15 01:33:40.157246	\N	10.210.161.203	\N	项目: Mercury Data Centre @ Johor
861	project	projects	71	UPDATE	项目类型	sales_focus	channel_follow	9	alesandro	2025-10-15 03:16:55.404058	\N	10.210.48.171	\N	项目: Zhu Chi Hospital PIK
862	project	projects	71	UPDATE	industry	other	hospitality	9	alesandro	2025-10-15 03:18:08.330937	\N	10.210.182.220	\N	项目: Zhu Chi Hospital PIK
863	project	projects	59	UPDATE	项目类型	sales_focus	channel_follow	9	alesandro	2025-10-15 03:47:16.692791	\N	10.210.48.171	\N	项目: The Tunnel at The Mining In Kalimantan 
864	quotation	quotations	35	CREATE	\N	\N	\N	1	admin	2025-10-15 11:09:17.8016	\N	10.210.182.134	\N	报价单: QU202510-002
865	quotation	quotations	35	DELETE	\N	\N	\N	1	admin	2025-10-15 11:09:31.611108	\N	10.210.182.220	\N	报价单: QU202510-002
866	quotation	quotations	36	CREATE	\N	\N	\N	2	quah	2025-10-21 02:02:55.604369	\N	10.210.83.38	\N	报价单: QU202510-002
867	quotation	quotations	36	UPDATE	amount	19449.5	21394.45	2	quah	2025-10-21 02:03:52.929271	\N	10.210.245.109	\N	报价单: QU202510-002
868	quotation	quotations	36	UPDATE	updated_at	2025-10-21 02:02:55.570871	2025-10-21 02:03:52.927497	2	quah	2025-10-21 02:03:52.929275	\N	10.210.245.109	\N	报价单: QU202510-002
869	project	projects	70	UPDATE	owner_id	quah	yusry.lee	2	quah	2025-10-21 03:32:49.661252	项目负责人从 quah 变更为 yusry.lee	10.210.199.15	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	\N
870	customer	companies	120	CREATE	\N	\N	\N	2	quah	2025-10-21 06:51:20.522975	\N	10.210.199.15	\N	公司: Exquisiteness Engineering Sdn Bhd
871	customer	contacts	151	CREATE	\N	\N	\N	2	quah	2025-10-21 06:52:16.493579	\N	10.210.138.9	\N	记录: 周总
872	project	projects	10	DELETE	\N	\N	\N	3	roy	2025-10-21 07:05:10.2937	\N	10.210.199.15	\N	项目: YTL Data Centre @ Kulai
873	project	projects	10	DELETE	\N	\N	\N	3	roy	2025-10-21 07:05:44.028003	\N	10.210.211.131	\N	项目: YTL Data Centre @ Kulai
874	project	projects	10	DELETE	\N	\N	\N	3	roy	2025-10-21 07:06:20.046923	\N	10.210.83.38	\N	项目: YTL Data Centre @ Kulai
875	project	projects	10	DELETE	\N	\N	\N	3	roy	2025-10-21 07:06:38.755731	\N	10.210.211.131	\N	项目: YTL Data Centre @ Kulai
876	project	projects	40	DELETE	\N	\N	\N	3	roy	2025-10-21 07:07:33.959545	\N	10.210.211.131	\N	项目: Penang Airport Extension
877	project	projects	74	CREATE	\N	\N	\N	2	quah	2025-10-21 07:50:38.229418	\N	10.210.83.38	\N	项目: NTP - L - GDS DC @ Nusajaya Tech Park
878	project	projects	74	UPDATE	项目类型	channel_follow	sales_focus	2	quah	2025-10-21 07:51:29.581831	\N	10.210.83.38	\N	项目: NTP - L - GDS DC @ Nusajaya Tech Park
879	project	projects	74	UPDATE	项目类型	sales_focus	channel_follow	2	quah	2025-10-21 07:52:11.568633	\N	10.210.182.250	\N	项目: NTP - L - GDS DC @ Nusajaya Tech Park
880	project	projects	74	UPDATE	厂商负责人	12	2	2	quah	2025-10-21 07:52:11.568637	\N	10.210.182.250	\N	项目: NTP - L - GDS DC @ Nusajaya Tech Park
881	project	projects	74	UPDATE	厂商负责人	2	12	2	quah	2025-10-21 07:54:30.742567	\N	10.210.83.38	\N	项目: NTP - L - GDS DC @ Nusajaya Tech Park
882	project	projects	74	UPDATE	shared_with_users	[]	[3]	2	quah	2025-10-21 07:54:30.742573	\N	10.210.83.38	\N	项目: NTP - L - GDS DC @ Nusajaya Tech Park
883	project	projects	74	UPDATE	share_enabled	False	True	2	quah	2025-10-21 07:54:30.742576	\N	10.210.83.38	\N	项目: NTP - L - GDS DC @ Nusajaya Tech Park
884	project	projects	74	UPDATE	报备来源	sales	channel	2	quah	2025-10-21 07:55:38.135698	\N	10.210.245.109	\N	项目: NTP - L - GDS DC @ Nusajaya Tech Park
885	project	projects	74	UPDATE	厂商负责人	12	2	2	quah	2025-10-21 07:55:38.135704	\N	10.210.245.109	\N	项目: NTP - L - GDS DC @ Nusajaya Tech Park
886	project	projects	55	UPDATE	项目名称	BDC-泰国数据中心B1-2-3项目	BDC-泰国数据中心B1项目	2	quah	2025-10-21 07:59:43.358418	\N	10.210.211.131	\N	项目: BDC-泰国数据中心B1项目
887	project	projects	55	UPDATE	阶段描述	目前我们在初期设计这3栋数据中心，Evertac不在BDC白名单中，我需要配合一起推进白名单工作！	目前我们在初期设计这3栋数据中心(B1,B2&B3)，Evertac不在BDC白名单中，我需要配合一起推进白名单工作！	2	quah	2025-10-21 07:59:43.358422	\N	10.210.211.131	\N	项目: BDC-泰国数据中心B1项目
888	project	projects	55	UPDATE	shared_with_users	[]	[3]	2	quah	2025-10-21 07:59:43.358424	\N	10.210.211.131	\N	项目: BDC-泰国数据中心B1项目
889	project	projects	55	UPDATE	share_enabled	False	True	2	quah	2025-10-21 07:59:43.358426	\N	10.210.211.131	\N	项目: BDC-泰国数据中心B1项目
890	project	projects	75	CREATE	\N	\N	\N	2	quah	2025-10-21 08:00:46.563176	\N	10.210.199.15	\N	项目: BDC-泰国数据中心B2项目
891	project	projects	75	UPDATE	厂商负责人	12	2	2	quah	2025-10-21 08:02:34.287349	\N	10.210.199.15	\N	项目: BDC-泰国数据中心B2项目
892	project	projects	75	UPDATE	shared_with_users	[]	[3]	2	quah	2025-10-21 08:02:34.287357	\N	10.210.199.15	\N	项目: BDC-泰国数据中心B2项目
893	project	projects	75	UPDATE	share_enabled	False	True	2	quah	2025-10-21 08:02:34.287361	\N	10.210.199.15	\N	项目: BDC-泰国数据中心B2项目
894	project	projects	55	UPDATE	项目名称	BDC-泰国数据中心B1项目	泰国-BDC-Chonburi-B1数据中心	2	quah	2025-10-21 08:22:47.377342	\N	10.210.182.250	\N	项目: 泰国-BDC-Chonburi-B1数据中心
895	project	projects	75	UPDATE	项目名称	BDC-泰国数据中心B2项目	泰国-BDC-Chonburi-B2数据中心	2	quah	2025-10-21 08:23:17.272215	\N	10.210.182.250	\N	项目: 泰国-BDC-Chonburi-B2数据中心
896	project	projects	76	CREATE	\N	\N	\N	2	quah	2025-10-21 08:23:43.231576	\N	10.210.83.38	\N	项目: 泰国-BDC-Chonburi-B3数据中心
897	quotation	quotations	37	CREATE	\N	\N	\N	2	quah	2025-10-21 08:30:44.450113	\N	10.210.245.109	\N	报价单: QU202510-003
898	quotation	quotations	38	CREATE	\N	\N	\N	2	quah	2025-10-21 08:34:06.663034	\N	10.210.182.250	\N	报价单: QU202510-004
899	quotation	quotations	39	CREATE	\N	\N	\N	2	quah	2025-10-21 08:37:22.635019	\N	10.210.138.9	\N	报价单: QU202510-005
900	project	projects	54	UPDATE	项目名称	NTP-H GDS数据中心改造	GDS-NTP-H 数据中心改造	2	quah	2025-10-21 08:38:50.229537	\N	10.210.245.109	\N	项目: GDS-NTP-H 数据中心改造
901	project	projects	53	UPDATE	项目名称	NTP-F-gds数据中心改造	GDS-NTP-F数据中心改造	2	quah	2025-10-21 08:39:24.970106	\N	10.210.245.109	\N	项目: GDS-NTP-F数据中心改造
902	project	projects	74	UPDATE	项目名称	NTP - L - GDS DC @ Nusajaya Tech Park	GDS-NTP-L数据中心项目 	2	quah	2025-10-21 08:42:46.173137	\N	10.210.245.109	\N	项目: GDS-NTP-L数据中心项目 
903	project	projects	8	UPDATE	项目名称	MyO2	BDC_CyberJaya_MY02	2	quah	2025-10-21 08:44:36.493823	\N	10.210.211.131	\N	项目: BDC_CyberJaya_MY02
904	project	projects	8	UPDATE	industry		datacenter	2	quah	2025-10-21 08:44:36.493829	\N	10.210.211.131	\N	项目: BDC_CyberJaya_MY02
905	user	users	4	UPDATE	is_department_manager	True	False	1	admin	2025-10-22 00:38:28.198331	\N	10.210.211.131	\N	公司: evertacsolutions
906	user	users	4	UPDATE	updated_at	1754535169.92197	1761093508.17094	1	admin	2025-10-22 00:38:28.198338	\N	10.210.211.131	\N	公司: evertacsolutions
907	project	projects	75	UPDATE	owner_id	quah	fuyanxin	2	quah	2025-10-22 01:06:27.521621	项目负责人从 quah 变更为 fuyanxin	10.210.182.250	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	\N
908	project	projects	74	UPDATE	owner_id	quah	fuyanxin	2	quah	2025-10-22 01:07:35.09535	项目负责人从 quah 变更为 fuyanxin	10.210.245.109	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	\N
909	user	users	3	UPDATE	is_department_manager	True	False	1	admin	2025-10-22 01:08:48.33386	\N	10.210.211.131	\N	公司: evertacsolutions
910	user	users	3	UPDATE	updated_at	1752454275.95417	1761095328.31236	1	admin	2025-10-22 01:08:48.333865	\N	10.210.211.131	\N	公司: evertacsolutions
911	customer	companies	121	CREATE	\N	\N	\N	3	roy	2025-10-22 01:12:14.529554	\N	10.210.182.250	\N	公司: AIMS Data Centre Sdn. Bhd.
912	customer	contacts	152	CREATE	\N	\N	\N	3	roy	2025-10-22 01:14:39.226467	\N	10.210.83.38	\N	记录: Lim Seng Eng
913	project	projects	76	UPDATE	owner_id	quah	fuyanxin	2	quah	2025-10-22 01:24:49.849108	项目负责人从 quah 变更为 fuyanxin	10.210.138.9	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	\N
914	project	projects	76	UPDATE	阶段描述		In BDC's AML ( Approved Manufacturer List) the walkie talkie and repeater are Motorola ( SLR5000 with XiR P8600i Series) and our brand not in the list. \r\nThey contractor currently would like to remain the approved brand while integrate with our Evertac's DAS system.	2	quah	2025-10-22 01:31:32.762661	\N	10.210.182.250	\N	项目: 泰国-BDC-Chonburi-B3数据中心
915	project	projects	76	UPDATE	shared_with_users	[]	[3]	2	quah	2025-10-22 01:31:32.762666	\N	10.210.182.250	\N	项目: 泰国-BDC-Chonburi-B3数据中心
916	project	projects	76	UPDATE	share_enabled	False	True	2	quah	2025-10-22 01:31:32.762668	\N	10.210.182.250	\N	项目: 泰国-BDC-Chonburi-B3数据中心
917	customer	contacts	153	CREATE	\N	\N	\N	3	roy	2025-10-22 01:31:42.769337	\N	10.210.245.109	\N	记录: Bryan
918	project	projects	75	UPDATE	阶段描述		In BDC's AML ( Approved Manufacturer List) the walkie talkie and repeater are Motorola ( SLR5000 with XiR P8600i Series) and our brand not in the list. They contractor currently would like to remain the approved brand while integrate with our Evertac's DAS system.	2	quah	2025-10-22 01:32:39.060618	\N	10.210.245.109	\N	项目: 泰国-BDC-Chonburi-B2数据中心
919	customer	companies	122	CREATE	\N	\N	\N	3	roy	2025-10-22 01:33:26.36225	\N	10.210.245.109	\N	公司: Ekova System Sdn Bhd
920	project	projects	67	UPDATE	owner_id	quah	fuyanxin	2	quah	2025-10-22 01:37:11.84567	项目负责人从 quah 变更为 fuyanxin	10.210.245.109	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	\N
921	customer	contacts	154	CREATE	\N	\N	\N	3	roy	2025-10-22 01:37:30.291693	\N	10.210.245.109	\N	记录: Terry Ong
922	project	projects	74	UPDATE	阶段描述	Currently in tender stage	Currently in tender stage through EXQ 	2	quah	2025-10-22 01:38:17.414266	\N	10.210.182.250	\N	项目: GDS-NTP-L数据中心项目 
923	project	projects	10	DELETE	\N	\N	\N	3	roy	2025-10-22 01:38:18.75563	\N	10.210.83.38	\N	项目: YTL Data Centre @ Kulai
924	project	projects	40	DELETE	\N	\N	\N	3	roy	2025-10-22 01:38:55.157801	\N	10.210.182.250	\N	项目: Penang Airport Extension
925	project	projects	41	DELETE	\N	\N	\N	3	roy	2025-10-22 01:39:13.633715	\N	10.210.245.109	\N	项目: Amazon Data Centre @ Cyberjaya
926	project	projects	61	UPDATE	owner_id	quah	yusry.lee	2	quah	2025-10-22 01:39:43.35062	项目负责人从 quah 变更为 yusry.lee	10.210.199.15	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	\N
927	project	projects	42	DELETE	\N	\N	\N	3	roy	2025-10-22 01:39:48.422291	\N	10.210.245.109	\N	项目: Microsoft Data Centre @ Cyberjaya
928	quotation	quotations	36	UPDATE	customer_id	\N	101	1	admin	2025-10-22 01:42:50.485356	\N	10.210.83.38	\N	报价单: QU202510-002
929	quotation	quotations	36	UPDATE	contact_id	\N	122	1	admin	2025-10-22 01:42:50.485361	\N	10.210.83.38	\N	报价单: QU202510-002
930	quotation	quotations	36	UPDATE	项目阶段	discover	embed	1	admin	2025-10-22 01:42:50.485364	\N	10.210.83.38	\N	报价单: QU202510-002
931	quotation	quotations	36	UPDATE	product_signature	c94f6824c6350b40e60007b89a3d7149	d0dc40c91ae4593e74af519507cb33b8	1	admin	2025-10-22 01:42:50.485367	\N	10.210.83.38	\N	报价单: QU202510-002
932	quotation	quotations	36	UPDATE	updated_at	2025-10-21 02:03:52.927497	2025-10-22 01:42:50.483562	1	admin	2025-10-22 01:42:50.48537	\N	10.210.83.38	\N	报价单: QU202510-002
933	project	projects	77	CREATE	\N	\N	\N	3	roy	2025-10-22 01:43:00.07772	\N	10.210.182.250	\N	项目: Aims Data Centre
934	customer	contacts	155	CREATE	\N	\N	\N	2	quah	2025-10-22 02:49:33.133061	\N	10.210.138.9	\N	记录: Jaganathan
935	project	projects	78	CREATE	\N	\N	\N	2	quah	2025-10-24 01:20:55.129506	\N	10.16.211.131	\N	项目: GDS-KTP-D数据中心项目
936	project	projects	78	UPDATE	owner_id	quah	fuyanxin	2	quah	2025-10-24 02:01:41.092211	项目负责人从 quah 变更为 fuyanxin	10.210.32.97	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	\N
937	quotation	quotations	40	CREATE	\N	\N	\N	2	quah	2025-10-24 02:14:20.492692	\N	10.16.53.196	\N	报价单: QU202510-006
938	quotation	quotations	40	UPDATE	updated_at	2025-10-24 02:14:20.459133	2025-10-24 02:34:09.216533	2	quah	2025-10-24 02:34:09.217401	\N	10.210.32.97	\N	报价单: QU202510-006
939	project	projects	54	UPDATE	项目名称	GDS-NTP-H 数据中心改造	GDS-NTP-H 数据中心	2	quah	2025-10-24 02:39:09.864226	\N	10.17.26.3	\N	项目: GDS-NTP-H 数据中心
940	project	projects	53	UPDATE	项目名称	GDS-NTP-F数据中心改造	GDS-NTP-F数据中心	2	quah	2025-10-24 02:40:02.461057	\N	10.17.168.65	\N	项目: GDS-NTP-F数据中心
941	project	projects	54	UPDATE	项目名称	GDS-NTP-H 数据中心	GDS-NTP-H 数据中心项目	2	quah	2025-10-24 03:08:51.802525	\N	10.17.26.3	\N	项目: GDS-NTP-H 数据中心项目
942	quotation	quotations	30	UPDATE	customer_id	\N	28	2	quah	2025-10-24 03:30:01.570944	\N	10.17.95.192	\N	报价单: QU202509-003
943	quotation	quotations	30	UPDATE	contact_id	\N	33	2	quah	2025-10-24 03:30:01.570951	\N	10.17.95.192	\N	报价单: QU202509-003
944	quotation	quotations	30	UPDATE	amount	2640.0	56613.0	2	quah	2025-10-24 03:30:01.570955	\N	10.17.95.192	\N	报价单: QU202509-003
945	quotation	quotations	30	UPDATE	product_signature	41cf054695b7db483f743461b54a6ec7	66540d60ed4b4e7c4614661fc48ee089	2	quah	2025-10-24 03:30:01.570959	\N	10.17.95.192	\N	报价单: QU202509-003
946	quotation	quotations	30	UPDATE	implant_total_amount	2640.0	56269.0	2	quah	2025-10-24 03:30:01.570962	\N	10.17.95.192	\N	报价单: QU202509-003
947	quotation	quotations	30	UPDATE	updated_at	2025-09-30 05:19:16.103965	2025-10-24 03:30:01.568328	2	quah	2025-10-24 03:30:01.570965	\N	10.17.95.192	\N	报价单: QU202509-003
948	quotation	quotations	30	UPDATE	amount	56613.0	62274.30000000001	2	quah	2025-10-24 03:30:33.256152	\N	10.16.53.196	\N	报价单: QU202509-003
949	quotation	quotations	30	UPDATE	updated_at	2025-10-24 03:30:01.568328	2025-10-24 03:30:33.255131	2	quah	2025-10-24 03:30:33.256156	\N	10.16.53.196	\N	报价单: QU202509-003
950	quotation	quotations	11	UPDATE	customer_id	\N	28	2	quah	2025-10-24 03:45:12.843901	\N	10.17.95.192	\N	报价单: QU202507-002
951	quotation	quotations	11	UPDATE	contact_id	\N	33	2	quah	2025-10-24 03:45:12.843908	\N	10.17.95.192	\N	报价单: QU202507-002
952	quotation	quotations	11	UPDATE	amount	14170.0	24310.8	2	quah	2025-10-24 03:45:12.843912	\N	10.17.95.192	\N	报价单: QU202507-002
953	quotation	quotations	11	UPDATE	product_signature	fb19f7f4bca212a2c2dd8d6f75fad726	49e83f032c4a1067d767738afd0e242c	2	quah	2025-10-24 03:45:12.843916	\N	10.17.95.192	\N	报价单: QU202507-002
954	quotation	quotations	11	UPDATE	implant_total_amount	12839.0	12204.0	2	quah	2025-10-24 03:45:12.843919	\N	10.17.95.192	\N	报价单: QU202507-002
955	quotation	quotations	11	UPDATE	updated_at	2025-09-16 02:38:13.682609	2025-10-24 03:45:12.842079	2	quah	2025-10-24 03:45:12.843922	\N	10.17.95.192	\N	报价单: QU202507-002
956	quotation	quotations	11	UPDATE	updated_at	2025-10-24 03:45:12.842079	2025-10-24 03:46:49.703749	2	quah	2025-10-24 03:46:49.704529	\N	10.210.32.97	\N	报价单: QU202507-002
957	quotation	quotations	29	UPDATE	customer_id	\N	28	2	quah	2025-10-24 04:51:24.114564	\N	10.16.53.196	\N	报价单: QU202509-002
958	quotation	quotations	29	UPDATE	contact_id	\N	33	2	quah	2025-10-24 04:51:24.114568	\N	10.16.53.196	\N	报价单: QU202509-002
959	quotation	quotations	29	UPDATE	amount	22040.0	36777.399999999994	2	quah	2025-10-24 04:51:24.114571	\N	10.16.53.196	\N	报价单: QU202509-002
960	quotation	quotations	29	UPDATE	product_signature	da6669354466b81e0d7cef4bbef80ef6	37083ace37ddd3f25cfee8bb8a4d0d55	2	quah	2025-10-24 04:51:24.114572	\N	10.16.53.196	\N	报价单: QU202509-002
961	quotation	quotations	29	UPDATE	implant_total_amount	22040.0	33210.0	2	quah	2025-10-24 04:51:24.114574	\N	10.16.53.196	\N	报价单: QU202509-002
962	quotation	quotations	29	UPDATE	updated_at	2025-09-30 04:56:31.475341	2025-10-24 04:51:24.113128	2	quah	2025-10-24 04:51:24.114576	\N	10.16.53.196	\N	报价单: QU202509-002
963	project	projects	53	UPDATE	项目名称	GDS-NTP-F数据中心	GDS-NTP-F数据中心项目	2	quah	2025-10-24 04:52:42.233158	\N	10.17.26.3	\N	项目: GDS-NTP-F数据中心项目
964	project	projects	8	UPDATE	项目名称	BDC_CyberJaya_MY02	BDC_CyberJaya_MY02_数据中心项目	2	quah	2025-10-24 04:54:58.401027	\N	10.17.26.3	\N	项目: BDC_CyberJaya_MY02_数据中心项目
965	quotation	quotations	41	CREATE	\N	\N	\N	2	quah	2025-10-24 07:53:28.860191	\N	10.17.26.3	\N	报价单: QU202510-007
966	project	projects	79	CREATE	\N	\N	\N	2	quah	2025-10-24 08:45:21.11753	\N	10.17.26.3	\N	项目: NextDC 数据中心项目
967	quotation	quotations	42	CREATE	\N	\N	\N	2	quah	2025-10-24 08:46:31.48525	\N	10.16.53.196	\N	报价单: QU202510-008
968	project	projects	80	CREATE	\N	\N	\N	1	admin	2025-10-27 00:42:49.496719	\N	10.210.32.97	\N	项目: Tsingshan IMIP Site
969	customer	companies	123	CREATE	\N	\N	\N	7	yusry	2025-10-27 00:53:41.327135	\N	10.210.32.97	\N	公司: Tsingshan IWIP
970	customer	companies	123	DELETE	\N	\N	\N	1	admin	2025-10-27 00:54:46.334069	\N	10.16.53.196	\N	公司: Tsingshan IWIP
971	customer	companies	124	CREATE	\N	\N	\N	1	admin	2025-10-27 00:56:16.804852	\N	10.17.95.192	\N	公司: Tsingshan IWIP
972	customer	companies	124	DELETE	\N	\N	\N	1	admin	2025-10-27 01:00:48.714413	\N	10.210.32.97	\N	公司: Tsingshan IWIP
973	customer	contacts	156	CREATE	\N	\N	\N	3	roy	2025-10-27 05:30:27.33619	\N	10.17.95.192	\N	记录: Wang Jia (王佳)
974	project	projects	48	UPDATE	交付预测	\N	2025-12-15	3	roy	2025-10-28 06:30:47.054687	\N	10.17.168.65	\N	项目: ZData (中联数据集团) Hyperscale GP3 DC @ Johor
975	project	projects	48	UPDATE	shared_with_users	[]	[1, 2, 4, 7]	3	roy	2025-10-28 06:30:47.054693	\N	10.17.168.65	\N	项目: ZData (中联数据集团) Hyperscale GP3 DC @ Johor
976	project	projects	48	UPDATE	share_enabled	False	True	3	roy	2025-10-28 06:30:47.054696	\N	10.17.168.65	\N	项目: ZData (中联数据集团) Hyperscale GP3 DC @ Johor
977	customer	contacts	157	CREATE	\N	\N	\N	3	roy	2025-10-28 06:35:36.623453	\N	10.16.53.196	\N	记录: Krisnaa
978	project	projects	50	UPDATE	阶段描述	This project is currently under construction, and the Mainkon company is PT. Acset.	This project is currently under construction, and the Main Contractor company is PT. Acset Indonusa Tbk, construction time of 10 months from November 2025.	9	alesandro	2025-10-28 12:52:12.077451	\N	10.17.117.247	\N	项目: Yellow Stone Project
979	customer	companies	125	CREATE	\N	\N	\N	9	alesandro	2025-10-28 12:58:17.217806	\N	10.16.211.131	\N	公司: PT. Domus Arsitektur Indonesia
980	customer	contacts	158	CREATE	\N	\N	\N	9	alesandro	2025-10-28 13:00:53.817519	\N	10.17.95.192	\N	记录: Mohamad Salman
981	customer	companies	126	CREATE	\N	\N	\N	9	alesandro	2025-10-28 14:41:45.277344	\N	10.17.117.247	\N	公司: PT. Shunrong International
982	customer	contacts	159	CREATE	\N	\N	\N	9	alesandro	2025-10-28 14:46:14.195575	\N	10.210.32.97	\N	记录: Kent
983	customer	contacts	159	UPDATE	position	Project Devision	Senior Estimation	9	alesandro	2025-10-28 14:47:30.137726	\N	10.17.168.65	\N	记录: Kent
984	customer	contacts	159	UPDATE	updated_at	2025-10-28 22:46:14.175017	2025-10-28 22:47:30.117010	9	alesandro	2025-10-28 14:47:30.137733	\N	10.17.168.65	\N	记录: Kent
985	project	projects	81	CREATE	\N	\N	\N	2	quah	2025-10-31 02:27:20.310689	\N	10.16.55.131	\N	项目: Test price approval flow
986	quotation	quotations	43	CREATE	\N	\N	\N	2	quah	2025-10-31 02:28:10.307213	\N	10.16.55.131	\N	报价单: QU202510-009
987	customer	contacts	160	CREATE	\N	\N	\N	9	alesandro	2025-11-04 16:54:07.326282	\N	10.17.1.197	\N	记录: Argha Dhimas
988	project	projects	50	UPDATE	项目名称	Yellow Stone Project	Yellow Stone Project (SMX01)	9	alesandro	2025-11-04 17:30:34.669627	\N	10.17.114.202	\N	项目: Yellow Stone Project (SMX01)
989	customer	companies	127	CREATE	\N	\N	\N	1	admin	2025-11-09 02:55:19.473444	\N	10.17.2.6	\N	公司: UCI Corporation co.,ltd
990	customer	contacts	161	CREATE	\N	\N	\N	1	admin	2025-11-09 02:56:22.304238	\N	10.17.114.223	\N	记录: Paisith Chuchuay
991	customer	companies	128	CREATE	\N	\N	\N	2	quah	2025-11-10 06:26:44.010254	\N	10.17.93.69	\N	公司: EcoWorld HQ
992	customer	contacts	162	CREATE	\N	\N	\N	2	quah	2025-11-10 06:27:15.955173	\N	10.17.93.69	\N	记录: Ir. Low
993	customer	companies	129	CREATE	\N	\N	\N	2	quah	2025-11-10 08:23:11.091089	\N	10.17.93.69	\N	公司: DayOne DC Malaysia Sdb Bhd
994	customer	contacts	163	CREATE	\N	\N	\N	2	quah	2025-11-10 08:26:50.846247	\N	10.17.3.73	\N	记录: Dharmendran Mogan
995	customer	contacts	164	CREATE	\N	\N	\N	2	quah	2025-11-10 08:27:37.420118	\N	10.17.93.69	\N	记录: Muhammad Naim Nafi
996	customer	companies	130	CREATE	\N	\N	\N	9	alesandro	2025-11-11 13:38:27.20946	\N	10.17.114.223	\N	公司: PT Barito Pacific Tbk
997	customer	contacts	165	CREATE	\N	\N	\N	9	alesandro	2025-11-11 13:39:22.402314	\N	10.17.93.131	\N	记录: Hendri
998	customer	companies	131	CREATE	\N	\N	\N	9	alesandro	2025-11-11 16:11:42.246535	\N	10.17.93.69	\N	公司: PT BYD Motor Indonesia
999	customer	contacts	166	CREATE	\N	\N	\N	9	alesandro	2025-11-11 16:13:17.350814	\N	10.16.66.139	\N	记录: Noviyanti Gouw
1000	customer	contacts	167	CREATE	\N	\N	\N	9	alesandro	2025-11-11 16:18:31.732178	\N	10.16.66.139	\N	记录: Silviana Gunarsih Santoso
1001	customer	companies	132	CREATE	\N	\N	\N	9	alesandro	2025-11-11 16:38:37.473545	\N	10.17.238.85	\N	公司: SM+
1002	customer	contacts	168	CREATE	\N	\N	\N	9	alesandro	2025-11-11 16:40:41.793809	\N	10.17.93.69	\N	记录: antonius@smplus.com
1003	project	projects	82	CREATE	\N	\N	\N	2	quah	2025-11-12 01:18:21.921377	\N	10.17.93.131	\N	项目: Oil refinery plant_Indonesia
1004	customer	companies	133	CREATE	\N	\N	\N	3	roy	2025-11-12 01:38:19.726907	\N	10.17.1.199	\N	公司: Radius Synergy Sdn. Bhd.
1005	customer	contacts	169	CREATE	\N	\N	\N	3	roy	2025-11-12 01:39:13.109824	\N	10.16.134.198	\N	记录: Ronny Loke
1006	project	projects	79	UPDATE	项目名称	NextDC 数据中心项目	NextDC_Extension Coverage Proposal 数据中心项目	2	quah	2025-11-12 03:45:02.28064	\N	10.17.93.131	\N	项目: NextDC_Extension Coverage Proposal 数据中心项目
1007	project	projects	83	CREATE	\N	\N	\N	2	quah	2025-11-12 06:49:04.895006	\N	10.17.14.139	\N	项目: Nusajaya Industrial Park 2
1008	customer	companies	129	UPDATE	公司名称	DayOne DC Malaysia Sdb Bhd	DayOne DC Malaysia Sdn Bhd	2	quah	2025-11-12 23:20:52.953806	\N	10.17.114.223	\N	公司: DayOne DC Malaysia Sdn Bhd
1009	quotation	quotations	44	CREATE	\N	\N	\N	2	quah	2025-11-12 23:51:23.324661	\N	10.17.114.223	\N	报价单: QU202511-001
1010	quotation	quotations	44	UPDATE	amount	31887.79	35347.78999999999	2	quah	2025-11-13 00:40:33.56371	\N	10.17.93.69	\N	报价单: QU202511-001
1011	quotation	quotations	44	UPDATE	product_signature	febeaa1b368d9b8f8e916a186f43b6a3	ca4e051fdae2e0b92384bc831b882264	2	quah	2025-11-13 00:40:33.563715	\N	10.17.93.69	\N	报价单: QU202511-001
1012	quotation	quotations	44	UPDATE	implant_total_amount	16337.0	19797.0	2	quah	2025-11-13 00:40:33.563717	\N	10.17.93.69	\N	报价单: QU202511-001
1013	quotation	quotations	44	UPDATE	updated_at	2025-11-12 23:51:23.280295	2025-11-13 00:40:33.561965	2	quah	2025-11-13 00:40:33.56372	\N	10.17.93.69	\N	报价单: QU202511-001
1014	project	projects	84	CREATE	\N	\N	\N	2	quah	2025-11-17 01:42:02.509926	\N	10.17.114.223	\N	项目: Additional Walkie-talkie NTP-F
1015	quotation	quotations	45	CREATE	\N	\N	\N	2	quah	2025-11-17 01:43:11.547281	\N	10.17.2.6	\N	报价单: QU202511-002
1016	quotation	quotations	45	UPDATE	amount	3600.0	3770.0	2	quah	2025-11-17 01:46:48.747614	\N	10.17.114.223	\N	报价单: QU202511-002
1017	quotation	quotations	45	UPDATE	product_signature	4711fec56f6ae659	cc94c4325dd828788c710e9779801ae9	2	quah	2025-11-17 01:46:48.74762	\N	10.17.114.223	\N	报价单: QU202511-002
1018	quotation	quotations	45	UPDATE	updated_at	2025-11-17 01:43:11.507043	2025-11-17 01:46:48.746557	2	quah	2025-11-17 01:46:48.747624	\N	10.17.114.223	\N	报价单: QU202511-002
1019	project	projects	85	CREATE	\N	\N	\N	3	roy	2025-11-18 02:22:15.094631	\N	10.16.145.215	\N	项目: Genting World Resort
1020	customer	companies	134	CREATE	\N	\N	\N	9	alesandro	2025-11-18 20:05:12.766624	\N	10.17.93.131	\N	公司: PT. DCI Indonesia Tbk
1021	customer	contacts	170	CREATE	\N	\N	\N	9	alesandro	2025-11-18 20:08:09.958432	\N	10.17.2.6	\N	记录: Ervin Andriana Taufik
1022	customer	companies	134	UPDATE	备注		PT. DCI Indonesia Tbk (DCII) is the first Tier IV data center provider in Southeast Asia. Established in 2011, DCI offers colocation, interconnection, internet exchange, smart-hands services, and globally standardized data center operations.\r\n\r\nDCI serves major clients across cloud providers, e-commerce, banking, finance, healthcare, network services, and enterprise sectors, and is known for its high uptime and internationally recognized operational efficiency.	9	alesandro	2025-11-18 20:31:50.678846	\N	10.17.93.131	\N	公司: PT. DCI Indonesia Tbk
1023	project	projects	83	DELETE	\N	\N	\N	2	quah	2025-11-18 21:01:11.957109	\N	10.17.114.223	\N	项目: Nusajaya Industrial Park 2
1024	project	projects	86	CREATE	\N	\N	\N	9	alesandro	2025-11-18 21:01:24.313352	\N	10.17.93.131	\N	项目: Cikini Area Development Project 
1025	quotation	quotations	31	UPDATE	customer_id	\N	28	2	quah	2025-11-18 21:42:47.358268	\N	10.16.66.139	\N	报价单: QU202509-004
1026	quotation	quotations	31	UPDATE	contact_id	\N	33	2	quah	2025-11-18 21:42:47.358274	\N	10.16.66.139	\N	报价单: QU202509-004
1027	quotation	quotations	31	UPDATE	product_signature	a5e2ea95a7bdfd2f	fa9e8f69c084e7f58ec9d4b74ada7553	2	quah	2025-11-18 21:42:47.358278	\N	10.16.66.139	\N	报价单: QU202509-004
1028	quotation	quotations	31	UPDATE	updated_at	2025-09-30 04:42:26.039366	2025-11-18 21:42:47.356917	2	quah	2025-11-18 21:42:47.358281	\N	10.16.66.139	\N	报价单: QU202509-004
1029	quotation	quotations	46	CREATE	\N	\N	\N	2	quah	2025-11-18 22:14:54.344003	\N	10.17.181.56	\N	报价单: QU202511-003
1030	quotation	quotations	47	CREATE	\N	\N	\N	2	quah	2025-11-18 22:30:02.891217	\N	10.17.184.200	\N	报价单: QU202511-004
1031	quotation	quotations	45	UPDATE	amount	3770.0	6600.0	2	quah	2025-11-20 09:42:19.17508	\N	10.16.94.8	\N	报价单: QU202511-002
1032	quotation	quotations	45	UPDATE	product_signature	cc94c4325dd828788c710e9779801ae9	89b50470e31550349eb4150b7be40df0	2	quah	2025-11-20 09:42:19.175085	\N	10.16.94.8	\N	报价单: QU202511-002
1033	quotation	quotations	45	UPDATE	implant_total_amount	2900.0	5730.0	2	quah	2025-11-20 09:42:19.175088	\N	10.16.94.8	\N	报价单: QU202511-002
1034	quotation	quotations	45	UPDATE	updated_at	2025-11-17 01:46:48.746557	2025-11-20 09:42:19.173886	2	quah	2025-11-20 09:42:19.175091	\N	10.16.94.8	\N	报价单: QU202511-002
1035	user	users	15	CREATE	\N	\N	\N	1	admin	2025-11-23 01:37:29.777165	\N	10.17.99.155	\N	公司: evertacsolutions
\.


--
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.companies (id, company_code, company_name, country, region, address, industry, company_type, status, created_at, updated_at, notes, is_deleted, owner_id, shared_with_users, share_contacts, share_enabled, source) FROM stdin;
15	25F30010	MCS Management Sdn Bhd	MY	Selangor	X32, X, 9-G & 9-1, Jalan Sungai Burung 32/68, Bukit Rimau, 40460 Shah Alam, Selangor	health	designer	active	2025-06-30 06:27:31.418087	2025-07-11 17:33:46.118162		f	2	[3]	t	f	\N
38	25G10003	 Syarikat Pembenaan Yeoh Tiong Lay Sdn Bhd (YTL Construction) 	MY	Kuala Lumpur	19 - 24th Floor, Menara YTL, 205, Jalan Bukit Bintang , 55100 , Kuala Lumpur	other	contractor	active	2025-07-10 01:50:59.596652	2025-07-10 09:50:59.611157		f	3	[]	t	f	\N
40	25G16001	Stream Communication System Sdn Bhd	MY	Kuala Lumpur	12-2, Jalan Kuchai Maju 19, Kuchai Entrepreneurs Park, 58200 Kuala Lumpur, Wilayah Persekutuan Kuala Lumpur	datacenter	integrator	active	2025-07-16 15:05:46.267793	2025-07-16 15:21:29.922262		f	2	[]	t	f	\N
61	25H07002	SP Infocomm Solutions Sdn Bhd	MY	Selangor	CT-01-05, Corporate Tower, Subang Square Business Centre, 47500 Subang Jaya, Selangor	other	dealer	active	2025-08-07 15:11:35.302137	2025-08-07 15:13:51.991965		f	7	[]	t	f	\N
62	25H07003	OGX Industrial Supplies Sdn Bhd (OIS)	MY	Selangor	20, Jalan Astaka U8/84A, Taman Perindustrian Bukit Jelutong, Seksyen, U8 Shah Alam, 40150 Shah Alam, Selangor	other	dealer	active	2025-08-07 15:20:53.075649	2025-08-07 15:25:08.635927		f	7	[]	t	f	\N
63	25H07004	iOi MALLS	MY	Selangor	Management Office, Unit T2-3A-3 & Unit T2-3A-3A Level 3A, IOI City Tower Two, Lbh IRC, Ioi Resort, 62502 Putrajaya, Selangor	hospitality	user	active	2025-08-07 15:27:47.475331	2025-08-07 15:30:15.355639		f	7	[]	t	f	\N
64	25H07005	AirTrunk Malaysia Sdn Bhd	MY	Johor	Jalan Bioteknologi 3, Johor, Malaysia	datacenter	user	active	2025-08-07 15:43:10.551844	2025-08-07 15:44:45.628382		f	7	[]	t	f	\N
41	25G16002	Asalcom Sdn Bhd	MY	Kuala Lumpur	Suite 16-1, Menara Mutiara Sentral, 2, Jalan Desa Aman 1, Cheras Business Centre, 56000 Kuala Lumpur, Federal Territory of Kuala Lumpur	datacenter	integrator	active	2025-07-16 15:23:09.237429	2025-07-16 15:32:54.477481		f	2	[]	t	f	\N
17	25F30012	Engenious Solutions Sdn Bhd	MY	Selangor	Sekitar 26, No 25, Level, 1, Jalan Serendah 26/41, Seksyen 26, 40400 Shah Alam, Selangor	real_estate	contractor	active	2025-06-30 06:38:47.585461	2025-07-11 17:31:12.850498		f	2	[3]	t	f	\N
18	25F30013	Unique Arena Sdn Bhd	MY	Selangor	12, Jalan Layang - Layang 5A, Bandar Puchong Jaya, 47170 Puchong, Selangor	real_estate	integrator	active	2025-06-30 06:41:30.650289	2025-07-11 17:28:08.977939		f	2	[3]	t	f	\N
19	25F30014	Ace Sonic Communications Sdn Bhd	MY	Johor	No. 19 & 19-1, Jalan Sagu 16, Taman Daya, 81100 Johor Bahru, Johor Darul Takzim	transport	dealer	active	2025-06-30 06:44:09.482517	2025-07-11 17:25:19.715348		f	2	[3]	t	f	\N
6	25F30001	Reach Integrated Sdn Bhd	MY	Kuala Lumpur	No. 35-3, Block 1D, Jalan Wangsa Delima 12, Wangsa Link / D’wangsa, 53300 Wangsa Maju, Kuala Lumpur, Malaysia.	energy	integrator	active	2025-06-30 03:18:59.917753	2025-07-11 18:00:28.875275		f	2	[3]	t	f	\N
13	25F30008	Electcoms Berhad	MY	Selangor	12 A, Jalan 13/4, Seksyen 13, 46200 Petaling Jaya, Selangor	manufacturing	integrator	active	2025-06-30 06:16:11.805567	2025-07-11 17:37:05.79411		f	2	[3]	t	f	\N
14	25F30009	Mymeta Solution Sdn Bhd	MY	Selangor	Suite 1-12, CJ1 Centre, No. 1, Jalan Cyber Point 4, Cyber 8, 63000 Cyberjaya, Selangor Darul Ehsan. 	other	integrator	active	2025-06-30 06:22:43.998319	2025-07-18 09:52:08.08993		f	2	[3]	t	f	\N
8	25F30003	Synergy Oil & Gas Engineering Sdn Bhd	MY	Selangor	No. 31, Jalan Serendah 26/41,  Kawasan Perindustrian Hicom,  Seksyen 26, 40400 Shah Alam,  Selangor, Malaysia	other	designer	active	2025-06-30 03:35:46.277694	2025-07-14 10:29:32.040236		f	2	[3]	t	f	\N
10	25F30005	Technip FMC	MY	Kuala Lumpur	Tower, 19, TSLAW, 03, Jalan Kamuning, Imbi, 55100 Kuala Lumpur, Federal Territory of Kuala Lumpur	energy	designer	active	2025-06-30 04:24:23.119513	2025-07-11 17:52:27.402466		f	2	[3]	t	f	\N
11	25F30006	Axis Technology Resources (M) Sdn Bhd	MY	Selangor	G-23, MKH Boulevard, Jalan Bukit, Bandar Kajang, 43000 Kajang, Selangor	energy	contractor	active	2025-06-30 04:26:20.730197	2025-07-11 17:50:44.796265		f	2	[3]	t	f	\N
48	25G22005	Wire & Wireless Sdn Bhd	MY	Selangor	42, Jalan TP 7/1, Taman Perindustrian Uep, 47620 Subang Jaya, Selangor	other	integrator	active	2025-07-22 17:48:37.037535	2025-07-22 17:52:26.198536		f	2	[]	t	f	\N
9	25F30004	Tactical Communications Sdn Bhd	MY	Selangor	20, Jalan PP 20, Taman Pinggiran Putra, 43300 Seri Kembangan, Selangor	government	contractor	active	2025-06-30 03:44:33.745339	2025-07-11 17:57:22.64966		f	2	[3]	t	f	\N
36	25G10001	SIPP Power Sdn Bhd (subsidiary of YTL Corporation Bhd)	MY	Kuala Lumpur	33rd Floor, Menara YTL, 205 Jalan Bukit Bintang , 55100 , Kuala Lumpur , Malaysia	real_estate	user	active	2025-07-10 01:34:51.562963	2025-07-10 09:34:51.577917		f	3	[2, 4, 5]	t	f	\N
29	25F30024	Pembinaan Mitrajaya Sdn. Bhd.	MY	Selangor	No. 9, Block D, Pusat Perdagangan Puchong Prima, Persiaran Prima Utama, Taman Puchong Prima, 47150 Puchong, Selangor	other	contractor	active	2025-06-30 08:41:24.483104	2025-07-08 09:55:47.631153		f	3	[2, 4, 5]	t	f	\N
31	25G01001	Electrica Technology Sdn Bhd	MY	Selangor	1-3, JALAN PUTERI 3A/1, ENIGMA SQUARE, BANDAR PUTERI BANGI, 43000 KAJANG, SELANGOR.	real_estate	contractor	active	2025-07-01 01:39:40.299777	2025-07-01 09:50:31.687504		f	2	[3]	t	f	\N
23	25F30018	Binastra Corporation Bhd	MY	Kuala Lumpur	No 1 & 3, Jalan Jalil Jaya 3, Jalil Link, Bukit Jalil, 57000 Kuala Lumpur.	other	contractor	active	2025-06-30 07:16:04.787779	2025-07-08 10:02:50.577268		f	3	[2, 1]	t	f	\N
51	25G29002	Bridge Data Centres Malaysia Sdn Bhd 	MY	Selangor	MY02, Jalan Cyber Point 2, Cyber 12, 63000 Seremban Negeri Sembilan	datacenter	user	active	2025-07-29 15:35:57.187786	2025-08-19 13:09:46.27922		f	2	[]	t	f	\N
60	25H07001	RADII Teknologi Sdn Bhd	MY	Selangor	No. 327, Jalan Teluk Gadong / KS1, off, Persiaran Raja Muda Musa, 42000 Pelabuhan Klang, Selangor	other	dealer	active	2025-08-07 14:58:16.859039	2025-11-05 10:28:13.806817		f	7	[]	t	f	\N
65	25H07006	TM Technology Service Sdn Bhd 	MY	Kuala Lumpur	Level 30, TM Annexe 2, Jalan Pantai Jaya, 59200 Kuala Lumpur, Malaysia 	other	integrator	active	2025-08-07 16:37:01.866881	2025-10-22 10:49:33.139582		f	2	[]	t	f	\N
32	25G09001	Bridge Data Centres -  (Subsidiary of Chindata Group @ Beijing)	CN	北京市	Building 8, Wangjing Chengying Center, Chaoyang District, Beijing, China	other	user	active	2025-07-09 06:53:03.259073	2025-07-09 15:08:58.013676		f	3	[2, 3, 12]	t	t	\N
25	25F30020	SKA Technology Sdn Bhd	MY	Kuala Lumpur	No 26, Jalan Siput Akek, Taman Billion, 56000 Kuala Lumpur, Wilayah Persekutuan Kuala Lumpur	real_estate	integrator	active	2025-06-30 07:30:08.910648	2025-07-22 22:54:00.101942		f	3	[1, 2, 4, 5, 9, 10, 11]	t	t	\N
34	25G09003	CCIE Engineering (M) Sdn. Bhd.	MY	Kuala Lumpur	Wisma Uoa Centre, Kuala Lumpur, 50450 Kuala Lumpur.	other	contractor	active	2025-07-09 07:19:24.678782	2025-11-12 09:35:09.45416		f	3	[2, 4, 5]	t	f	\N
33	25G09002	Dynast Consult Sdn. Bhd.	MY	Selangor	20, Jln Sungai Burung AA32/AA, Bukit Rimau, 40460 Shah Alam, Selangor	other	designer	active	2025-07-09 07:12:20.248078	2025-10-14 14:56:47.973942		f	3	[2, 4, 5]	t	f	\N
22	25F30017	MEG Consult Sdn. Bhd.	MY	Kuala Lumpur	 46-1, Jln Metro Perdana Barat 2, Taman Usahawan Kepong, 52100 Kuala Lumpur.	other	designer	active	2025-06-30 06:59:16.688945	2025-11-12 09:32:32.883901		f	3	[2, 4, 5, 10, 11]	t	t	\N
27	25F30022	MCC Technique Sdn. Bhd.	MY	Selangor	12, Jalan PPU 2A, Taman Perindustrian Puchong Utama, 47100 Puchong, Selangor	real_estate	integrator	active	2025-06-30 07:43:59.217899	2025-07-08 09:57:19.26978		f	3	[2, 4, 5]	t	f	\N
16	25F30011	BHJ Security Technology Sdn Bhd	MY	Kuala Lumpur	1-31-1, Menara Bangkok Bank | Berjaya Central Park, Menara Bangkok Bank, Jln Ampang, City Centre, 50450 Kuala Lumpur, Wilayah Persekutuan Kuala Lumpur	manufacturing	contractor	active	2025-06-30 06:36:50.683932	2025-07-29 16:10:05.160632		f	2	[3]	t	f	\N
28	25F30023	FMTCS SOLUTIONS PTE. LTD	SG	Singapore	18 Boon Lay Way, #03-117 Tradehub 21, Singapore 609966   Tel No: (65) 65681543	other	dealer	active	2025-06-30 07:52:55.698312	2025-07-11 16:05:30.153078		f	2	[3]	t	f	\N
24	25F30019	Jurutera Perunding Gen Sdn. Bhd.	MY	Kuala Lumpur	Taman Cheras, 24-4-1 & 26-4-2, Jalan 2/101c, Cheras Business Centre, 56100 Kuala Lumpur	other	designer	active	2025-06-30 07:25:29.787654	2025-07-08 10:01:30.647771		f	3	[2, 4, 5]	t	f	\N
7	25F30002	Strato Solutions Sdn Bhd	MY	Selangor	C-09-06, Sunway Nexis, Kota Damansara, 47810 Petaling Jaya, Selangor	energy	integrator	active	2025-06-30 03:23:36.761819	2025-07-18 09:42:26.329867		f	2	[]	t	f	\N
20	25F30015	Digital Two Way Communications Sdn Bhd	MY	Sarawak	No.139A 1st Floor, Jalan Rock, 93200 Kuching, Sarawak.	other	integrator	active	2025-06-30 06:46:34.999153	2025-07-11 17:22:29.771241		f	2	[3]	t	f	\N
21	25F30016	Comintel Sdn Bhd	MY	Selangor	22, Jalan Nilam 2, Taman Perindustrian Teknologi Tinggi, 47500 Subang Jaya, Selangor	transport	contractor	active	2025-06-30 06:54:10.056536	2025-07-29 15:32:40.579115		f	2	[3]	t	f	\N
49	25G22006	NextDC Sdn. Bhd.	MY	Selangor	Axis Technology Centre, Level 5, Jalan 51a/225, Seksyen 51a, 46100 Petaling Jaya, Selangor	datacenter	user	active	2025-07-22 22:44:43.466513	2025-07-22 22:44:43.480828		f	3	[2, 4, 5]	t	f	\N
52	25G29003	DcD Technology Sdn Bhd 	MY	Selangor	 Level 3, CJ11, Jalan Impact, Cyberjaya, 63000 Cyberjaya, Selangor	datacenter	contractor	active	2025-07-29 15:48:09.928998	2025-07-29 15:59:37.957623		f	2	[]	t	f	\N
44	25G22001	GDS IDC SERVICES III (MALAYSIA) SDN BHD	MY	Johor	Unit 20-01 Teega Tower No 1 Jalan Laksamana Puteri Harbour Iskandar Puteri, Johor, 79250 Malaysia.	datacenter	user	active	2025-07-22 10:43:28.61806	2025-07-22 10:43:28.635674		f	3	[2, 4]	t	f	\N
26	25F30021	B-Global Tech	MY	Kuala Lumpur	Level 19, Boutique Office (B01-C), Menara 2, Jalan Bangsar, 59200 Kuala Lumpur	other	designer	active	2025-06-30 07:37:08.12148	2025-08-01 13:10:45.057373		f	3	[2, 4, 5]	t	f	\N
35	25G09004	YSC Technology Engineering Sdn. Bhd.	MY	Johor	B1-2404 Starview bay Property Management Service Centre, Teluk Bintang, Jalan Forest City 5, Pulau Satu, 81550 Gelang Patah, Johor	other	integrator	inactive	2025-07-09 07:26:57.517255	2025-07-16 15:39:36.466209		t	3	[2, 3, 4, 5, 9, 10, 11, 12]	t	t	\N
71	25H12002	PT. CITRADATA INDONUSA	ID	Jakarta	Taman Pegangsaan Indah Blok T/No. 26 Jl. Pegangsaan Dua, Kelapa Gading Jakarta 14250	other	dealer	active	2025-08-12 12:29:07.445738	2025-08-15 09:48:23.550048		f	1	[2, 3, 4, 5, 8, 9, 10, 11]	t	t	\N
47	25G22004	Longmotive (M) Sdn. Bhd.	MY	Johor	No. 9, Jalan Teknologi Perintis 1/2, Taman Teknologi Nusajaya, 79250 Iskandar Puteri, Johor.	datacenter	integrator	active	2025-07-22 15:42:11.601047	2025-07-22 15:42:11.615391		f	3	[2, 4, 12, 5]	t	t	\N
46	25G22003	GDS Data Center @ Thailand	TH	Chonburi	Amata City Chonburi Industrial Park	datacenter	user	active	2025-07-22 15:26:18.403245	2025-07-22 15:26:18.419088		f	3	[2, 4, 12, 5]	t	t	\N
39	25G10004	China Construction Yangtze River (Malaysia) Sdn. Bhd. (Subsidiary of CSCEC)	MY	Kuala Lumpur	Level 1, Suite 1-5, Vertical Corporate Tower B, Avenue 10, Bangsar South, Kuala Lumpur	other	contractor	active	2025-07-10 02:30:58.317204	2025-10-01 09:29:02.029934		f	3	[2, 12]	t	t	\N
69	25H11001	Bandway Engineering (M) Sdn Bhd	MY	Kuala Lumpur	D-1-3, MEGAN AVENUE 1 NO, 189, 50400 Kuala Lumpur	other	dealer	active	2025-08-11 13:16:15.694493	2025-11-05 09:44:02.60112		f	2	[12]	t	t	\N
53	25H04001	Timesfly Engineering Services 时代飞扬	CN	Beijing	北京市朝阳区霄云路甲26号海航大厦10层	datacenter	integrator	active	2025-08-04 16:25:47.493076	2025-08-04 16:45:28.670292		f	3	[2, 3, 12]	t	t	\N
45	25G22002	EPG Engineering System Sdn. Bhd.	MY	Kuala Lumpur	Level 41, Vista Tower,The Intermark,348 Jalan Tun Razak,50400, Kuala Lumpur, Malaysia	datacenter	integrator	active	2025-07-22 11:03:45.879688	2025-07-22 11:04:37.266505		f	3	[2, 3, 12]	t	t	\N
70	25H12001	Duriane Professionals Sdn Bhd	MY	Selangor	26-1 & 26-3, Jalan Puteri 2/4, Bandar Puteri, 47100 Puchong, Selangor	datacenter	designer	active	2025-08-12 11:20:52.625367	2025-08-12 11:35:47.867667		f	3	[]	t	f	\N
55	25H06001	Mot Smart Solutions Company Limited (Head office)	TH	Bangkok	39/14 NAWONGPRACHAPATTANA ROAD  SIKUN SUBDISTRICT, KHET DONMUEANG BANGKOK. 10210	other	dealer	active	2025-08-06 09:37:25.976557	2025-08-06 09:38:29.538311		f	2	[2, 4, 5, 8, 10, 11]	t	t	\N
72	25H12003	COMMUTRONICS ENTERPRISE CO., LTD	CN	Shanghai	台北市复兴南路二段237号10楼-6室,1 0F.-6, No. 237, Sec. 2, Fuxing S.Rd.,  Daan Dist., Taipei City 10667, Taiwan	other	dealer	active	2025-08-12 13:02:01.778949	2025-08-12 13:04:49.882041		f	1	[4, 5, 8, 10, 11]	t	t	\N
73	25H12004	C.A. Sheimer (HK) Ltd	CN	Hong Kong Special Administrative Region	Hop Hing Industrial Building, Cheung Sha Wan, Hong Kong	government	dealer	active	2025-08-12 13:10:38.731391	2025-08-12 13:11:56.000465		f	1	[4, 5, 8, 10, 11, 12]	t	t	\N
12	25F30007	YSC TECHNOLOGY ENGINEERING Sdn Bhd	MY	Johor	B1-2404 Starview bay Property Management Service Centre, Teluk Bintang, Jalan Forest City 5, Pulau Satu, 81550 Gelang Patah, Johor Darul Takzim,Malaysia	other	integrator	active	2025-06-30 06:12:43.490939	2025-08-11 10:55:33.416846		f	2	[3, 12]	t	t	\N
75	25H19002	Arup Jururunding Sdn Bhd	MY	Selangor	Level 26, 1 POWERHOUSE, No. 1, Persiaran Bandar Utama, Bandar Utama, 47800 Petaling Jaya, Selangor	datacenter	consultant	active	2025-08-19 12:29:51.610648	2025-08-19 12:33:21.491914		f	3	[]	t	f	\N
30	25F30025	Sunway Engineering Sdn. Bhd.	MY	Selangor	Level 9, Menara Sunway, Jalan Lagoon Timur, Bandar Sunway, 47500 Subang Jaya, Selangor	real_estate	contractor	active	2025-06-30 08:44:54.952054	2025-10-01 09:33:23.250348		f	3	[2, 4, 5]	t	f	\N
50	25G29001	Supreme Landmobile & Wireless Corporation Sdn. Bhd. (SLW)	MY	Selangor	No 2. Jalan Salung 33/26, Shah Alam Technology Park, Section 33, 40400 Shah Alam, Selangor Darul Ehsan, Malaysia	other	integrator	active	2025-07-29 15:12:50.816036	2025-11-05 10:32:37.747305		f	2	[8, 7]	t	t	\N
74	25H19001	iFLYTEK	MY	Kuala Lumpur	37-02, Menara EcoWorld, Bukit Bintang City Centre, 55100 Kuala Lumpur, Malaysia 	other	integrator	active	2025-08-19 11:22:56.698059	2025-08-29 11:15:10.299618		f	2	[]	t	f	\N
54	25H05001	O'Connor's Engineering Sdn Bhd	MY	Selangor	Bangunan O'Connor, 13, Jalan 51a/223, Seksyen 51a, 46100 Petaling Jaya, Selangor	other	integrator	active	2025-08-05 17:42:29.535306	2025-09-19 15:58:59.275409		f	2	[8, 7]	t	t	\N
106	25J01002	MCE Consulting Sdn Bhd	MY	Selangor	512 Blok A, L 5, Kelana Business Centre, 97 Jalan SS7/2, Kelana Jaya, Petaling Jaya, Selangor.	datacenter	consultant	active	2025-10-01 09:37:20.728941	2025-10-01 09:39:16.595863		f	3	[]	t	f	\N
42	25G16003	Triple Access Sdn Bhd	MY	Selangor	A-03-16, Kompleks Perindustrian EmHub, Seksyen 3, Persiaran Surian, Taman Sains Selangor, 47810 Petaling Jaya, Selangor	other	dealer	active	2025-07-16 16:38:28.602616	2025-10-01 09:26:39.447082		f	2	[1, 3, 4, 5, 7, 9, 10, 11]	t	t	\N
84	25H26001	ACME Associates Global Sdn. Bhd.	MY	Putrajaya	02-02, Block 13, Star Central, Lingkaran Cyber Point Timur, Cyber 12, 63000 Cyberjaya,	datacenter	contractor	active	2025-08-26 14:30:52.216151	2025-08-26 14:38:15.898191		f	3	[]	t	f	\N
88	25H26005	 PT Acset Indonusa Tbk.	ID	Jakarta	JL. Majapahit No.26 Petojo Selatan - Gambir Jakarta, Indonesia 10160	other	contractor	active	2025-08-26 21:14:24.187726	2025-10-28 20:42:45.348672		f	9	[]	t	f	\N
85	25H26002	ST Dynamo DC Sdn Bhd	MY	Kuala Lumpur	Menara TM, 1 Jalan Pantai Jaya, Off Jalan Pantai Baharu , Kuala Lumpur , Malaysia	datacenter	user	active	2025-08-26 14:55:25.986843	2025-08-26 14:55:26.016744		f	3	[]	t	f	\N
77	25H19004	PT. Padma Integra Mandiri	ID	Jakarta	Sentral Senayan II, 11th Floor Jalan Asia Afrika No.8 Central Jakarta	government	integrator	active	2025-08-19 12:49:17.062683	2025-08-19 12:57:09.298332		f	9	[]	t	f	\N
86	25H26003	IJM Construction Sdn Bhd	MY	Selangor	2nd Floor, Wisma IJM, Jalan Yong Shook Lin 46050 Petaling Jaya, Selangor Darul Ehsan	datacenter	contractor	active	2025-08-26 14:58:54.489154	2025-08-26 14:58:54.513348		f	3	[]	t	f	\N
79	25H19006	Telesources (S) Pte Ltd	MY	Johor	3014A Ubi Rd 1, #03-07 Industrial Estate, Singapore 408703	shipbuilding	dealer	active	2025-08-19 15:50:26.593538	2025-08-19 15:50:26.620631		f	13	[]	t	f	\N
80	25H19007	Ping Engineering (Singapore) Pte Ltd	MY	Johor	51 Jln Pemimpin, #03-04 Mayfair Industrial Building, Singapore 577206	other	contractor	active	2025-08-19 16:46:43.820457	2025-08-19 16:46:43.842157		f	13	[]	t	f	\N
81	25H21001	Malaysia Airports Holdings Bhd (MAHB)	MY	Selangor	Malaysia Airports Corporate Office Persiaran Korporat KLIA 64000 KLIA, Sepang Selangor, MALAYSIA	transportation	user	active	2025-08-21 10:51:34.31228	2025-08-21 10:51:34.342532		f	3	[]	t	f	\N
82	25H21002	Amazon Web Services Malaysia Sdn Bhd (AWS)	MY	Kuala Lumpur	Level 35, The Gardens North Tower, 35, Lingkaran Syed Putra, Mid Valley City , 59200 , Kuala Lumpur , Malaysia	datacenter	user	active	2025-08-21 10:56:23.257503	2025-08-21 10:56:23.331806		f	3	[]	t	f	\N
83	25H21003	Microsoft (Malaysia) Sdn Bhd	MY	Kuala Lumpur	Level 17 & 18, Menara Shell, No. 211, Jalan Tun Sambanthan, Brickfields , 50470 , Kuala Lumpur , Malaysia	datacenter	user	active	2025-08-21 11:00:38.801376	2025-08-21 11:00:38.839846		f	3	[]	t	f	\N
87	25H26004	NTT Global Data Centres Sdn. Bhd.	MY	Putrajaya	43000, Persiaran APEC, Cyberjaya, 63000 Cyberjaya, Selangor	datacenter	user	active	2025-08-26 15:52:30.889668	2025-08-26 15:52:30.912842		f	3	[]	t	f	\N
95	25I16001	PT.  Duta Pratama Engineering	ID	Jakarta	Rukan Taman Meruya Blok M 37 Kembangan Jakarta Barat 11620	other	consultant	active	2025-09-16 17:13:35.908547	2025-09-16 17:20:10.377321	DUTA PRATAMA ENGINEERING A mechanical/electrical planning consulting services company that started operating in 2016. Although new, we have been trusted to handle various infrastructure projects, such as factories, office centers, hotels, apartments, shopping centers, campuses, and hospitals.\r\n	f	9	[]	t	f	\N
90	25H26007	PT.Mitra Cipta Pranata	ID	Jakarta	Intercon Plaza Blok C no 5 Raya, Kembangan, Jl. Meruya Ilir Raya, RT.1/RW.9, Srengseng, Jakarta Barat, Kota Jakarta Barat, Daerah Khusus Ibukota Jakarta 11630	other	consultant	active	2025-08-26 21:22:10.73839	2025-09-23 17:44:44.837252		f	9	[]	t	f	\N
78	25H19005	PT. Dwi Candra Teknologi	ID	Jakarta	Ruko Puri Mansion, Jl. Lkr. Luar Barat No.25A Blok.C, RT.5/RW.1, Kembangan Sel., Kec. Kembangan, Daerah Khusus Ibukota Jakarta 11610	other	integrator	active	2025-08-19 13:00:23.399213	2025-10-14 10:27:48.701595		f	9	[]	t	f	\N
89	25H26006	PT Bintai Kindenko Engineering Indonesia	ID	Jakarta	omplek Golden Centrum, Jl. Majapahit No.26 Blok S&T, South Petojo, Gambir, Central Jakarta City, Jakarta 10160	other	general_contractor	active	2025-08-26 21:18:25.789655	2025-08-26 21:18:25.819258		f	9	[]	t	f	\N
93	25I02002	PT. Aviasi Pariwisata Indonesia (Persero)/ Injorney Airports/Angkasa Pura II	ID	Jakarta	Gedung Sarinah Lantai 14, Jl. M. H. Thamrin No. 11, Kota Jakarta Pusat, 10350	transportation	user	active	2025-09-02 13:05:33.531417	2025-09-23 18:00:04.959189	One of the companies managing airports in Indonesia	f	9	[]	t	f	\N
91	25H27001	PT. Kuningan Mas Gemilang	ID	Jakarta	SINAR MAS LAND PLAZA, TOWER II, LANTAI 32, JL. M.H. THAMRIN NO. 51	datacenter	user	active	2025-08-27 12:42:06.511837	2025-08-27 12:42:06.53655	As end user of the Yellow Stone data center project	f	9	[]	t	f	\N
99	25I24001	UM Specialist Centre (UMSC)	MY	Kuala Lumpur	UMSC Building, Lot 28, Lorong Universiti, Lembah Pantai,50603 Kuala Lumpur.	hospitality	user	active	2025-09-24 09:56:33.46215	2025-09-24 09:57:50.037312		f	2	[]	t	f	\N
92	25I02001	PT. Meltech Consultindo Nusa	ID	Jakarta	Jl. Jatinegara Timur IV No.8, RT.9/RW.3, Bali Mester, Kecamatan Jatinegara, Kota Jakarta Timur, Daerah Khusus Ibukota Jakarta 13310	other	consultant	active	2025-09-02 12:59:10.471201	2025-09-09 11:22:00.529465	One of the mechanical electrical consulting companies in Indonesia	f	9	[]	t	f	\N
105	25J01001	Teknik Johan Telecommunication Sdn Bhd	MY	Kuala Lumpur	4A Jalan Medan Ramah, Off, Jalan Kuchai Lama, Happy Garden, 58200 Kuala Lumpur, Federal Territory of Kuala Lumpur	other	dealer	active	2025-10-01 09:26:59.630547	2025-11-19 09:28:14.125487		f	3	[]	t	f	\N
97	25I23001	Ingenium Systems Sdn Bhd	MY	Selangor	SG-08-01, Level 1, Subang Square, Jalan SS 15/4G, 47500 Subang Jaya, Selangor	other	integrator	active	2025-09-24 02:05:08.923064	2025-09-24 02:12:57.54474		f	2	[]	t	f	\N
98	25I23002	Foursons Engineering Sdn Bhd	MY	Selangor	No. 7, Jalan Perindustrian PP4, Taman Perindustrian Putra Permai, 43300 Seri Kembangan, Selangor.	other	general_contractor	active	2025-09-24 02:09:13.144432	2025-09-24 02:13:50.874369		f	2	[]	t	f	\N
96	25I19001	上海建工集团	CN	Shanghai	上海市大树柏路	government	contractor	active	2025-09-19 13:56:50.877798	2025-09-19 14:02:34.22251		f	1	[]	t	f	\N
100	25I24002	PT. Mega Akses Persada	ID	Jakarta	Cyber 2 tower, 3rd Floor. Jl Rasuna Said Blok X-5 no.13 Jakarta	other	system_integrator	active	2025-09-24 10:45:50.105958	2025-09-24 10:45:50.166938		f	9	[]	t	f	\N
94	25I02003	NV5 Malaysia	MY	Kuala Lumpur	Menara 2, B01-B-13A, KL Eco City, 59200 Kuala Lumpur, Federal Territory of Kuala Lumpur	datacenter	consultant	active	2025-09-02 22:27:23.087905	2025-09-24 09:27:23.208194		f	3	[]	t	f	\N
101	25I30001	Columbia Asia Hospital Bukit Rimau	MY	Selangor	3, Persiaran Anggerik Eria Bukit Rimau, Seksyen 32, 40460 Shah Alam, Selangor	hospitality	user	active	2025-09-30 11:51:31.0656	2025-09-30 11:55:20.680516		f	2	[]	t	f	\N
102	25I30002	Jinko Solar Technology Sdn Bhd	MY	Penang	2483, Tingkat Perusahaan 4, Kawasan Perusahaan Bebas Perai, 13600 Perai, Pulau Pinang	manufacturing	user	active	2025-09-30 12:05:15.773943	2025-09-30 12:06:32.56497		f	2	[]	t	f	\N
103	25I30003	RAG Solution Sdn Bhd	MY	Kuala Lumpur	Unit A16-04, Level 16, Menara A, Persiaran MPAJ Jalan Pandan Utama, Pandan Indah, 55100 Kuala Lumpur	other	user	active	2025-09-30 12:13:19.697561	2025-09-30 12:14:52.362199		f	2	[]	t	f	\N
104	25I30004	INNSIDE Hotel by Meliá Kuala Lumpur Cheras	MY	Putrajaya	N-G01, Eko Cheras No. 693, 55100 Kuala Lumpur	hospitality	user	active	2025-09-30 12:25:06.617553	2025-09-30 12:26:48.159819		f	2	[]	t	f	\N
113	25J13001	Tzu Chi Hospital	ID	Jakarta	 Pantai Indah Kapuk, Jakarta Utara 14470	other	user	active	2025-10-13 12:49:53.719206	2025-10-14 10:15:22.613437		f	9	[]	t	f	\N
107	25J01003	Security Marketing Sdn. Bhd.	MY	Kuala Lumpur	320, Lorong Selangor, Pusat Bandar Melawati, 53100 Kuala Lumpur,	datacenter	partner	active	2025-10-01 09:40:56.659779	2025-10-01 09:43:04.989012		f	3	[]	t	f	\N
37	25G10002	TRAC Consulting & Engineering Sdn Bhd	MY	Selangor	E1-05-08, Tamarind Square, Persiaran Multimedia, Cyber 10, 63000 Cyberjaya, Selangor	other	designer	active	2025-07-10 01:44:32.414258	2025-11-05 09:41:07.010822	Security consultant & parent company is AIP Risk Consulting Pte. Ltd. @ Singapore.	f	3	[1, 2, 4, 5, 9, 10, 11]	t	t	\N
125	25J28001	PT. Domus Arsitektur Indonesia	ID	Jakarta	Jl. Terogong Raya No.20, Cilandak Barat, Jakarta Selatan.	datacenter	designer	active	2025-10-28 20:58:17.185307	2025-10-28 21:00:53.823253		f	9	[]	t	f	sales
116	25J14003	MK Land Holdings Berhad	MY	Selangor	19, Jalan PJU 8/5h, Damansara Perdana, 47820 Petaling Jaya, Selangor	real_estate	contractor	active	2025-10-14 15:02:24.775747	2025-10-14 15:06:22.764197		f	3	[]	t	f	\N
108	25J02001	Cekap Technical Services Sdn Bhd	MY	Kuala Lumpur	 Setiawangsa Business Suite, Jalan Setiawangsa 11, Taman Setiawangsa, 54200 Kuala Lumpur, Wilayah Persekutuan Kuala Lumpur	other	integrator	active	2025-10-02 10:01:51.787042	2025-10-02 10:23:32.200601		f	2	[]	t	f	\N
43	25G16004	Vertex Communication Sdn Bhd	MY	Kuala Lumpur	G-0-6, Pusat Perdagangan Kuchai,, No. 2, Jalan 1/127, Off Jalan Kuchai Lama,, 58200 Kuala Lumpur, Wilayah Persekutuan Kuala Lumpur	other	integrator	active	2025-07-16 16:43:41.112862	2025-11-05 10:23:22.583417		f	2	[8, 7]	t	t	\N
109	25J07001	LG CNS	ID	Jakarta	11F, Sang-AM IT Center, 424, Worldcup Bu-Ro, Mapo-gu, Seol	datacenter	user	active	2025-10-07 17:35:08.919534	2025-10-07 17:45:13.110191		f	9	[]	t	f	\N
110	25J07002	PT China State Construction Overseas Development Shanghai	ID	Jakarta	SOHO CAPITAL Tanjung Duren Raya, RT.2/RW.5, Tj. Duren Sel., Kec. Grogol petamburan, Kota Jakarta Barat, Daerah Khusus Ibukota Jakarta	other	contractor	active	2025-10-07 18:12:29.738626	2025-10-07 18:15:40.284168		f	9	[]	t	f	\N
117	25J14004	Mega Jati Consult Sdn. Bhd.	MY	Selangor	25-2-1, Jalan Medan Putra 3, Medan Putra Bussiness Centre, 52200 Kuala Lumpur	datacenter	consultant	active	2025-10-14 15:15:27.718747	2025-10-14 15:19:00.250164		f	3	[]	t	f	\N
111	25J08001	Powerware Systems Sdn Bhd.	MY	Selangor	12j, Jln Tandang, Seksyen 51, 46050 Petaling Jaya, Selangor	datacenter	contractor	active	2025-10-08 17:01:48.084556	2025-10-08 17:03:04.303653		f	2	[]	t	f	\N
112	25J11001	Malaysian Communications and Multimedia Commission	MY	Selangor	Ground Floor, MCMC Tower, 2, Jalan Impact, Cyber 6, 63000 Cyberjaya, Selangor, Malaysia	government	other	active	2025-10-11 14:43:30.763626	2025-10-11 14:44:24.815647	Deputy Director, Radio Spectrum Assignment Department (Mobile Services)\r\nSpectrum Planning and Assignment Division	f	1	[]	t	f	\N
122	25J22002	Ekova System Sdn Bhd	MY	Selangor	No.11A, 1, Jalan BK 5a/3a, Bandar Kinrara, 47180 Puchong,	datacenter	designer	active	2025-10-22 09:33:26.346388	2025-10-22 09:37:30.296459		f	3	[]	t	f	marketing
114	25J14001	PT Teknologi Chayani Harsa (TechSolutions)	ID	Jakarta	Neo Soho Residence, Jakarta Barat	other	dealer	active	2025-10-14 10:10:27.892236	2025-10-14 10:12:43.708234		f	9	[]	t	f	\N
118	25J15001	Thinker Engineering Sdn Bhd	MY	Selangor	Unit F-G, 3A, CBD Perdana 3, Cyberjaya, 63000 Cyberjaya, Selangor	datacenter	consultant	active	2025-10-15 09:22:32.356684	2025-10-15 09:26:59.771672		f	3	[]	t	f	\N
119	25J15002	PMX MALAYSIA SDN. BHD.	MY	Selangor	Lot 6A, Level 6, Menara PKNS PJ, Jalan Yong Shook Lin, 46050 Petaling Jaya, Selangor	datacenter	contractor	active	2025-10-15 09:30:34.382994	2025-10-15 09:38:07.210492		f	3	[]	t	f	\N
127	25K09001	UCI Corporation co.,ltd	TH	Bangkok	299/195-7 Chaengwattana Rd, Thungsonghong, Lakksi	government	partner	active	2025-11-09 10:55:19.447222	2025-11-09 10:56:22.31157	Motorola dealer in Thailand, foucs on goverment, help us to connect NBTC for apply datacenter frequency.	f	1	[2, 4]	t	t	channel
120	25J21001	Exquisiteness Engineering Sdn Bhd	MY	Johor	No. 9-01, Jalan Perjiranan 4/5, Bandar Dato Onn, 81100 JB, Johor.	datacenter	general_contractor	active	2025-10-21 14:51:20.498026	2025-10-21 14:52:16.498525		f	2	[]	t	f	\N
76	25H19003	PT. Indonesia Weda Bay Industrial Park (IWIP)	ID	Jakarta	Sopo Del Office & Lifestyle Tower A Lantai 21, Jakarta Selatan	energy	user	active	2025-08-19 12:31:03.183584	2025-08-19 12:44:10.994213	PT. Indonesia Industrial Estate (IWIP), the company is a joint venture between Tsingshan Holding Group (majority owner), Eramet, and PT Antam. The mine is an open-pit operation with significant nickel ore reserves. Their nickel mining operation is located in the Halmahera Islands region of North Maluku, Indonesia.	f	9	[7]	t	t	\N
115	25J14002	PT. Citradata PurnaKharisma	ID	Jakarta	Komp. Glodok Plaza, Jl. Pinangsia Raya blok H 28, Glodok, Taman Sari, West Jakarta City, Jakarta 11110	other	dealer	active	2025-10-14 10:23:17.912693	2025-10-14 10:24:09.405457		f	9	[8, 7]	t	t	\N
128	25K10001	EcoWorld HQ	MY	Kuala Lumpur	Unit No. 19-01, Menara EcoWorld, Bukit Bintang City Centre, No. 2, Jalan Hang Tuah, 55100 Kuala Lumpur, Wilayah Persekutuan, Malaysia	real_estate	user	active	2025-11-10 14:26:43.980187	2025-11-10 14:27:15.964092		f	2	[]	t	f	sales
126	25J28002	PT. Shunrong International	ID	Banten	PIK 2, Banten	other	other	active	2025-10-28 22:41:45.253345	2025-11-05 01:11:26.317866	One of the general contractor companies that usually does civil engineering and MEP work, and is always a vendor for PT. China State Construction.	f	9	[]	t	f	sales
130	25K11001	PT Barito Pacific Tbk	ID	Jakarta	Wisma Barito Pacific Tower A, Jl. Letjen S. Parman Kav. 62–63, Slipi, Jakarta Barat	energy	user	active	2025-11-11 21:38:27.18625	2025-11-19 05:46:51.090918	Barito Pacific is a large and diversified business group that initially operated in the forestry sector and later transformed into a conglomerate in energy and petrochemicals.\r\nIts main focus is now on energy, petrochemicals, and sustainable utilities.	f	9	[]	t	f	sales
131	25K11002	PT BYD Motor Indonesia	ID	Jakarta	Autograph Tower Thamrin Nine, Level 50, Jl. M.H. Thamrin No.10, Kebon Melati, Tanah Abang, Jakarta Pusat 10230	manufacturing	user	active	2025-11-12 00:11:42.221389	2025-11-12 00:18:31.739966		f	9	[]	t	f	sales
132	25K11003	SM+	ID	Jakarta	Jl. M.H. Thamrin No.51, RT.9/RW.4, Central Jakarta, Jakarta, 10350 ID	datacenter	user	active	2025-11-12 00:38:37.450248	2025-11-12 00:40:41.800947		f	9	[]	t	f	sales
133	25K12001	Radius Synergy Sdn. Bhd.	MY	Selangor	1F-17, Pusat Perdagangan IOI, 1, Persiaran Puchong Jaya Selatan, Bandar Puchong Jaya, 47100, Selangor	datacenter	dealer	active	2025-11-12 09:38:19.710895	2025-11-12 09:39:51.758117		f	3	[]	t	f	marketing
129	25K10002	DayOne DC Malaysia Sdn Bhd	MY	Johor	No.3 Lingkaran, Jalan Teknologi Perintis 1, Taman Teknologi Nusajaya, 79250 Iskandar Puteri, Johor Darul Ta'zim	datacenter	user	active	2025-11-10 16:23:11.070124	2025-11-10 16:27:37.425671		f	2	[]	t	f	sales
121	25J22001	AIMS Data Centre Sdn. Bhd.	MY	Kuala Lumpur	Menara AIMS, Changkat Raja Chulan, Bukit Ceylon, 50200 Kuala Lumpur	datacenter	user	active	2025-10-22 09:12:14.507797	2025-11-19 09:26:09.326138		f	3	[]	t	f	marketing
134	25K18001	PT. DCI Indonesia Tbk	ID	Jakarta	Equity Tower, Lantai 17, SCBD, Jakarta	datacenter	user	active	2025-11-19 04:05:12.742311	2025-11-19 04:34:00.562669	PT. DCI Indonesia Tbk (DCII) is the first Tier IV data center provider in Southeast Asia. Established in 2011, DCI offers colocation, interconnection, internet exchange, smart-hands services, and globally standardized data center operations.\r\n\r\nDCI serves major clients across cloud providers, e-commerce, banking, finance, healthcare, network services, and enterprise sectors, and is known for its high uptime and internationally recognized operational efficiency.	f	9	[]	t	f	channel
\.


--
-- Data for Name: company_assets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.company_assets (id, asset_type, asset_name, asset_key, file_name, file_type, file_size, file_content, description, is_active, is_default, created_at, updated_at, created_by_id) FROM stdin;
\.


--
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
48	8	Hanini Mohd Zaki	Business Development 	Business Development Enginee	0 17200 8303	hanini.zaki@synergyengineering.com	f	2025-07-11 09:59:19.349251	2025-07-11 09:59:19.349255		2	f	f
49	6	Nur Jahidah	Sale	Manager	0 17-314 5646		f	2025-07-11 10:00:28.841674	2025-07-11 10:00:28.841678		2	f	f
50	8	Alyaa		Engineer 	011 1057 302	alyaa.najihah@synergyengineering.com	f	2025-07-14 10:29:32.02487	2025-07-14 10:29:32.024888		2	f	f
51	40	Lai	Project		019 380 9008		f	2025-07-16 15:06:24.826861	2025-07-16 15:06:24.826868		2	f	f
52	41	Amelia	Project	Manager	011 5959 3513		f	2025-07-16 15:23:54.037815	2025-07-16 15:23:54.037822		2	f	f
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
95	37	Shahrul	Project Management	Project Engineer	6017-4705687		f	2025-08-19 12:26:13.313432	2025-08-19 12:26:13.31344		3	f	f
87	71	Gama Waney		Director			t	2025-08-12 12:31:23.661658	2025-08-12 12:31:23.710151		1	f	f
88	71	Mario Lukman			+62 811 195 638	mario_lukman@citradata.id	f	2025-08-12 12:33:04.469971	2025-08-12 12:33:04.469977		1	f	f
89	72	Nelson.曾国栋			+886227013743	nelson.tseng@commutronics.com.tw	f	2025-08-12 13:04:49.856726	2025-08-12 13:04:49.856732		1	f	f
90	73	Michael Ho		Sales Director	(852) 6343-3799	mho@casheimer.com.hk	f	2025-08-12 13:11:55.969563	2025-08-12 13:11:55.969568		1	f	f
91	54	Johnson		Engineer	016 684 0553		f	2025-08-12 13:45:04.675969	2025-08-12 13:45:04.675976		2	f	f
92	65	Mohd Zaimi 			013 388 1091		f	2025-08-12 15:39:30.841558	2025-08-12 15:39:30.841565		2	f	f
70	55	Surasak J. (Paul)	Project	International Project Manager	+66 (0) 86 460-0454	surasak.j@mot.co.th	f	2025-08-06 09:38:29.521504	2025-08-12 17:44:47.427545	Had share our general presentation slide and sale training slide with Mr. Surask for their in-house training. \r\nBeside requesting the NBTC guidelines what is the frequency allow use in Thailand and procedure / fee to apply it, pending the information from him now. 	2	f	f
93	71	Adrian Bany Kansil		Vice Director	0628111774415	adrian@citradata.id	f	2025-08-15 09:48:23.520572	2025-08-15 09:48:23.520578		1	f	f
94	74	Khor Su Chong 		Senior Engineer	012 983 7277	suchongkhor@iflytek.com	f	2025-08-19 11:24:40.768964	2025-08-19 11:24:40.768972		2	f	f
96	75	Jackie Teo	Electrical 	Electrical Engineer	6012-258 9039	jackie.teo@arup.com	f	2025-08-19 12:32:11.435666	2025-08-19 12:32:11.435672		3	f	f
98	30	Lilian Su Lee Ding	Contract & Procurement	Asst. Manager	6019-750 0698	liliansld@sunway.com.my	f	2025-08-19 12:35:32.611449	2025-08-19 12:35:32.611457		3	f	f
97	76	Delvin	Project Devision	Project Devision	081381070413	dh@etsingshan.com	f	2025-08-19 12:33:31.400572	2025-08-19 12:50:09.010407		9	f	f
99	77	Joestiant	Engineer	Senior Engineer	081281227172		f	2025-08-19 12:51:57.276788	2025-08-19 12:51:57.276795		9	f	f
100	78	Candra	CEO	CEO			f	2025-08-19 13:01:36.521706	2025-08-19 13:01:36.521714		9	f	f
101	51	Maximilian		Project Manager			f	2025-08-19 13:09:46.257215	2025-08-19 13:09:46.257221		2	f	f
102	84	Chia Seng Huei	Project Management	Project Manager	6014-931 9518	senghuei@acme-associates.com.my	f	2025-08-26 14:33:33.952118	2025-08-26 14:33:33.952126		3	f	f
54	42	Yusry		Presale	018 902 3933	yusrylee@tripleaccess.com.my	f	2025-07-16 16:41:27.304949	2025-09-19 14:26:12.365264		2	f	f
103	84	Hii Sing Lung	Project Management	QS Manager	6016-235 4448	singlung@acme-associates.com.my	f	2025-08-26 14:35:02.177072	2025-08-26 14:35:02.177082		3	f	f
104	22	Ms. Lee Yen Ling	Project Management	Senior Electrical Engineer	6017-690 8472	yllee@meg.com.my	f	2025-08-26 15:31:12.143426	2025-08-26 15:31:12.143435		3	f	f
105	65	Azahar	Sale		013 361 8261		f	2025-08-27 10:11:26.86907	2025-08-27 10:11:26.869077		2	f	f
47	9	Puteri Maryam	Project	Chief Executive Officer	019 383 9271	maryam@tacticom.com.my	f	2025-07-11 09:57:22.626188	2025-08-28 15:15:25.705253		2	f	f
106	74	Wei Lee Tong		Marketing Director	010 865 3050	wldong3@iflytek.com	f	2025-08-29 11:15:10.256325	2025-08-29 11:15:10.256333		2	f	f
107	93	Handoko	Airports Electronic Devision	Project Devision	082317459999		f	2025-09-02 16:54:39.192885	2025-09-02 16:55:53.808266		9	f	f
146	115	Ajri	Sales	Sales Project	0895708247100		f	2025-10-14 10:24:09.386793	2025-10-14 10:24:09.3868		9	f	f
143	112	Arifah Aziela Jamaludin	Radio Spectrum Assignment Department 	Deputy Director	014-338 4280	arifah.jamaludin@mcmc.gov.my	t	2025-10-11 14:44:24.789416	2025-10-11 14:44:24.849676		1	f	f
144	114	Ilham Pratomo	Sales 	Sales Engineer	082113042670	sales@techsolutions	f	2025-10-14 10:12:43.674794	2025-10-14 10:12:43.674801		9	f	f
108	92	Asep	Project Devision	Cordinator Project	08129727108		t	2025-09-02 17:25:13.167358	2025-09-02 17:25:49.090483		9	f	f
109	94	Mohd. Abdul Hadi	Project Management	Electrical Engineer	6013-2181 6268	abdulhadi.nadzir@nv5.com	f	2025-09-02 22:29:01.363788	2025-09-02 22:29:01.363797		3	f	f
110	22	Ms. Atiqah	Project Management	Electrical Engineer	6013-468 4785		f	2025-09-02 22:39:27.513284	2025-09-02 22:39:27.513306		3	f	f
111	65	Nurshaliana		Project Manager	012 335 0482		f	2025-09-03 09:15:43.057062	2025-09-03 09:15:43.057069		2	f	f
112	90	Mr Endang	Electronic Devision	Cordinator Project	082113353807		f	2025-09-09 09:55:15.91861	2025-09-09 09:55:15.918621		9	f	f
113	95	Widodo	Project Devision	Cordinator Project	081310094123		f	2025-09-16 17:13:58.119147	2025-09-16 17:14:17.827164		9	f	f
114	34	Mr. Wu (吴锋艳)	Project Management	Project Manager			f	2025-09-16 20:14:43.711731	2025-09-16 20:14:43.711738		3	f	f
147	116	Muhamad Hidayat bin Zabidi	Project & Technical	Technical Executive	0193915744	hidayat@mkland.com.my	f	2025-10-14 15:05:33.439733	2025-10-14 15:05:33.43974		3	f	f
115	96	吴亮	项目部	经理			t	2025-09-19 14:02:34.195856	2025-09-19 14:02:34.259231		1	f	f
148	117	Aina Filza	Electrical	Electrical Engineer	012-4582604	ainafilza.afa@gmail.com	f	2025-10-14 15:18:11.683516	2025-10-14 15:18:11.683522		3	f	f
116	42	Alber wang					t	2025-09-19 14:26:12.30087	2025-09-19 14:26:12.368794		1	f	f
117	54	Khoo Zhong Yi	Radio Communication	Telco Engineer 	012 504 9812	khoozy@oce.com.my	f	2025-09-19 15:58:59.250227	2025-09-19 15:58:59.250235		2	f	f
118	97	Kuan Meng Xian		Chief Technology Officer	017-492 9270	kuanmx@ingeniumsys.com.my	f	2025-09-24 02:10:49.069602	2025-09-24 02:10:49.069608		2	f	f
119	98	Javen Low		Project Director	016-986 1075	javen@foursons.my	f	2025-09-24 02:13:50.855168	2025-09-24 02:13:50.855176		2	f	f
120	34	焦洋	Project Management	Project Manager	6010-700 3913		f	2025-09-24 09:23:55.829954	2025-09-24 09:23:55.829961		3	f	f
121	99	Muhammad Hisyam bin Taib	Facility Engineering Maintenance Services	Assistant Manager 	012-910 9241	mhisyamt@umsc.my	f	2025-09-24 09:57:49.986777	2025-09-24 09:57:49.986784		2	f	f
122	101	Jack Chan			012-942 8933	jackchanch@gmail.com	f	2025-09-30 11:55:20.658766	2025-09-30 11:55:20.658771		2	f	f
123	102	Koay Kean Pin		Senior IT Systems Engineer	012-406 7150	kpkoay@hotmail.com	f	2025-09-30 12:06:32.546292	2025-09-30 12:06:32.546299		2	f	f
124	103	Ragu		Sales & Marketing Director	012-232 1477	ragu@ragsolutions.com.my	f	2025-09-30 12:14:52.343889	2025-09-30 12:14:52.343895		2	f	f
125	104	Darshan Ram		Chief Engineer & Security	016 949 9291	ram.darshan@melia.com	f	2025-09-30 12:26:48.126634	2025-09-30 12:26:48.12664		2	f	f
126	42	Fizwan	Sale		012 600 0139	hafidzi@tripleaccess.com.my	f	2025-10-01 09:26:39.420377	2025-10-01 09:26:39.420382		2	f	f
127	39	张总		Project Manager			f	2025-10-01 09:28:09.881258	2025-10-01 09:28:09.881265		2	f	f
128	105	Daniel Yong	Sales	Sales Director	019-766 5555	danielyong@teknikjohan.com	f	2025-10-01 09:28:23.380333	2025-10-01 09:28:23.380339		3	f	f
129	39	Daphne Tay		Procurement	017 831 2189		f	2025-10-01 09:29:02.000414	2025-10-01 09:29:02.000422		2	f	f
130	30	Tang Pei Fen	Procurement & Contracts	Senior Contract Administrator	012-544 1361	tangpf@sunway.com.my	f	2025-10-01 09:32:43.755844	2025-10-01 09:32:43.75585		3	f	f
131	106	Lee Jian Xi	Project Management	Engineer	011-1073 9575		f	2025-10-01 09:38:35.648403	2025-10-01 09:38:35.648409		3	f	f
132	107	Andrew Shu	Business Development 	Sales Manager	016-336 2836	andrew@smsb.com.my	f	2025-10-01 09:42:30.183006	2025-10-01 09:42:30.183012		3	f	f
133	108	Mohammad Adam Bin Ismail	Digital Solution	Pre-Sale engineer	017 300 3531	adam@cekaptechnical.com	f	2025-10-02 10:04:01.88133	2025-10-02 10:04:01.881336		2	f	f
134	108	Syuhada Suliman		Project Manager	013 683 8258	syuhada@cekaptechnical.com	f	2025-10-02 10:06:35.062333	2025-10-02 10:06:35.062339		2	f	f
135	108	Nurain Zayanah Nadaruddin 		Project Engineer	013 514 5389	zayanah@cekaptechnical.com	f	2025-10-02 10:07:42.748847	2025-10-02 10:07:42.748854		2	f	f
136	108	Dr. Fatin Harun		Head of Business Development 	019 415 1990	fatinharun@cekaptechnical.com	f	2025-10-02 10:09:01.906667	2025-10-02 10:09:01.906673		2	f	f
137	108	Alif Nazarulasmal		Project Engineer	012 321 3569	alif.nazarulasmal@cekaptechnical.com	f	2025-10-02 10:10:20.560126	2025-10-02 10:10:20.560133		2	f	f
138	108	Noor Liyana Nazarudin		Senior Project Executive	017 275 3448	liyana@cekaptechnical.com	f	2025-10-02 10:11:23.346943	2025-10-02 10:11:23.346949		2	f	f
149	118	Ms. Amani Che Rus	Procurement 	Executive	019-461 6334	procurement@thinker.digital	f	2025-10-15 09:24:23.411585	2025-10-15 09:24:23.41159		3	f	f
139	109	Moonsun Song	Professional | Data Center Implementation Team	Project Devision	+82 10 3387 7043	mssong@lgcns.com	t	2025-10-07 17:37:50.214434	2025-10-07 17:37:50.28934		9	f	f
140	88	Johan	Project Devision	Chief Of MEP Estimation	085649039648		f	2025-10-07 17:52:35.773723	2025-10-07 17:52:35.773728		9	f	f
141	110	Andi	Project Devision	Manager MEP Devision (PIC GOB Bali)	0817556865		f	2025-10-07 18:15:40.2582	2025-10-07 18:15:40.258208		9	f	f
142	111	Lee Pei Jinn		Assistant Procurement Manager	012-228 8012	pjlee@powerware.com.my	f	2025-10-08 17:03:04.278439	2025-10-08 17:03:04.278445		2	f	f
150	119	Tang Lai Hing	Project	Senior Solution Engineer	016-893 1755	thomas.tang@pmxmalaysia.com	f	2025-10-15 09:32:24.38419	2025-10-15 09:32:24.384197		3	f	f
151	120	周总	Project		016 858 3488		f	2025-10-21 14:52:16.474339	2025-10-21 14:52:16.474346		2	f	f
145	113	Hendry A. Hermawan	Engineer	Engineer Manager	08175065817		t	2025-10-14 10:15:22.585721	2025-10-14 10:16:39.155519		9	f	f
152	121	Lim Seng Eng	Facilities	Facilities Director	017-456 0258	sengeng_lim@yahoo.com	f	2025-10-22 09:14:39.206179	2025-10-22 09:14:39.206187		3	f	f
153	121	Bryan	Security 	Security Manager	019-9644705		f	2025-10-22 09:31:42.753708	2025-10-22 09:31:42.753724		3	f	f
154	122	Terry Ong	Project & Service	Manager	016-2901838	terry@ekovasystem.com	f	2025-10-22 09:37:30.276472	2025-10-22 09:37:30.27648	Courtesy visit to present our RFoF DAS system to evaluate any collaboration in DC project. After meeting and knowing that they are consultant and system provider for energy, battey, equipment and room condition monitoring.	3	f	f
155	65	Jaganathan	Radio Communication		013 397 6489		f	2025-10-22 10:49:33.116959	2025-10-22 10:49:33.116966		2	f	f
156	69	Wang Jia (王佳)	Project	Project Engineer	016-259 9802	wangjia@bandway.my	f	2025-10-27 13:30:27.319751	2025-10-27 13:30:27.319758		3	f	f
157	37	Krisnaa	Technical	Senior Technical Manager	014-972 9593	krisna.murtee@trac-consulting.com	f	2025-10-28 14:35:36.606853	2025-10-28 14:35:36.606861		3	f	f
158	125	Mohamad Salman	Direktur	Direktur	+6285880293290		t	2025-10-28 21:00:53.799257	2025-10-28 21:00:53.855451		9	f	f
159	126	Kent	Project Devision	Senior Estimation	+6282288472394		f	2025-10-28 22:46:14.175011	2025-10-28 22:47:30.11701		9	f	f
160	126	Argha Dhimas	Project Devision	Engineering Team	085156120744		f	2025-11-05 00:54:07.2938	2025-11-05 00:54:07.293809		9	f	f
161	127	Paisith Chuchuay		Engineer Manager	09-5206-2276	paisith@uci.co.th	t	2025-11-09 10:56:22.278895	2025-11-09 10:56:22.355137		1	f	f
162	128	Ir. Low		Project Manager			f	2025-11-10 14:27:15.92961	2025-11-10 14:27:15.929618		2	f	f
163	129	Dharmendran Mogan	DC Cluster 	Security Manager		dharmendran.mogan@dayonedc.com	f	2025-11-10 16:26:50.82664	2025-11-10 16:26:50.826647	Currently in-charge for NTP-F&H&M	2	f	f
164	129	Muhammad Naim Nafi	DC Operation	Critical Service Manager		naim.nafi@dayonedc.com	f	2025-11-10 16:27:37.403045	2025-11-10 16:27:37.403051		2	f	f
165	130	Hendri	Project Devision	Cordinator Project	+6287877976437		f	2025-11-11 21:39:22.38144	2025-11-11 21:39:22.381448		9	f	f
166	131	Noviyanti Gouw	Project Devision	Senior Project Specialist	+6287877801444	gouw_23ph@yahoo.com	f	2025-11-12 00:13:17.327726	2025-11-12 00:13:17.327733		9	f	f
167	131	Silviana Gunarsih Santoso	Project Devision	Planning Specialist		silviana.santoso@byd.com	f	2025-11-12 00:18:31.710875	2025-11-12 00:18:31.710883		9	f	f
168	132	antonius@smplus.com	Project Devision	Procurement Supervisior	081315008900	antonius@smplus.com	f	2025-11-12 00:40:41.769569	2025-11-12 00:40:41.769576		9	f	f
169	133	Ronny Loke	Sales	Director	012-2065027		f	2025-11-12 09:39:13.094199	2025-11-12 09:39:13.094205		3	f	f
170	134	Ervin Andriana Taufik	Network Opratin Center	Network Opratin Center (NOC)n Manager	+628119950452	ervin@dci-Indonesia.com	f	2025-11-19 04:08:09.934652	2025-11-19 04:08:09.934659		9	f	f
\.


--
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
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.departments (id, name, code, parent_id, manager_id, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: dev_product_milestones; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dev_product_milestones (id, product_id, stage_key, name, description, planned_start_date, planned_end_date, actual_start_date, actual_end_date, status, progress, priority, order_index, created_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: dev_product_specs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dev_product_specs (id, dev_product_id, field_name, field_value, field_code) FROM stdin;
\.


--
-- Data for Name: dev_products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dev_products (id, category_id, subcategory_id, region_id, name, model, status, unit, retail_price, description, image_path, created_at, updated_at, owner_id, created_by, mn_code, pdf_path, currency, planned_duration_days, actual_duration_days, risk_level, baseline_date, milestone_count, stage_description, stage_history, stage_records) FROM stdin;
\.


--
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
-- Data for Name: event_registry; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.event_registry (id, event_key, label_zh, label_en, default_enabled, enabled, created_at, updated_at) FROM stdin;
\.


--
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
134	41	2025-10-07	entertainment	Lunch with William	1	96.75	draft	2025-11-10 14:53:29.918756	2025-11-10 14:53:30.694933	[{"filename": "PMA-SA_BX2025111002_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111002/PMA-SA_BX2025111002_01_01.jpeg", "size": 26308}]	CNY	96.75	96.75	1.0000
51	7	2025-06-25	local_transport	grab in Jakarta hotel to pt citradata and airport	4	37.57	draft	2025-08-12 12:51:35.526254	2025-08-12 12:51:36.130346	[{"filename": "PMA-SA_BX2025081202_03_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_01.heic", "size": 70942}, {"filename": "PMA-SA_BX2025081202_03_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_02.heic", "size": 75150}, {"filename": "PMA-SA_BX2025081202_03_03.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_03.heic", "size": 75402}, {"filename": "PMA-SA_BX2025081202_03_04.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_03_04.heic", "size": 75018}]	IDR	474800.00	37.57	0.0001
52	7	2025-06-25	local_transport	grab office to airport and back to home	2	55.5	draft	2025-08-12 12:51:36.132765	2025-08-12 12:51:36.410043	[{"filename": "PMA-SA_BX2025081202_04_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_04_01.heic", "size": 77270}, {"filename": "PMA-SA_BX2025081202_04_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081202/PMA-SA_BX2025081202_04_02.heic", "size": 78051}]	CNY	55.50	55.50	1.0000
53	8	2025-08-12	entertainment	dinner for xu and his family	1	568.93	draft	2025-08-12 12:57:38.859894	2025-08-12 12:57:39.290384	[{"filename": "PMA-SA_BX2025081203_01_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081203/PMA-SA_BX2025081203_01_01.heic", "size": 1168148}]	CNY	568.93	568.93	1.0000
55	9	2025-08-12	travel_accommodation	trip air from HK to Taibei	1	223.12368	draft	2025-08-12 13:17:00.956248	2025-10-02 12:47:15.040003	[{"filename": "PMA-SA_BX2025081204_02_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081204/PMA-SA_BX2025081204_02_01.heic", "size": 141151}]	CNY	1233.00	223.12	0.1810
61	11	2025-08-13	entertainment	dinner with Pt citradata	0	103.96000000000001	draft	2025-08-15 09:56:50.557154	2025-08-15 09:56:50.557161	\N	IDR	1039600.00	103.96	0.0001
56	10	2025-06-25	travel_accommodation	trip air singapore to HK	1	148.33728	draft	2025-08-12 13:18:32.930493	2025-09-19 14:36:34.21336	[{"filename": "PMA-SA_BX2025081205_01_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081205/PMA-SA_BX2025081205_01_01.heic", "size": 252022, "uploaded_at": "2025-08-12T05:19:09.979024"}]	CNY	832.00	148.34	0.1783
64	13	2025-08-13	entertainment	Lunch Mr. Yoga	1	42.85	draft	2025-09-18 14:29:01.836695	2025-09-19 14:25:53.62875	[{"filename": "PMA-SA_BX2025091802_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091802/PMA-SA_BX2025091802_01_01.jpeg", "size": 53141}]	MYR	42.85	42.85	1.0000
58	11	2025-08-12	travel_accommodation	Hotel in Jakarta 2 nights	1	265.73	draft	2025-08-15 09:56:50.519829	2025-08-15 18:53:07.077686	[{"filename": "PMA-SA_BX2025081501_02_01.jpg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081501/PMA-SA_BX2025081501_02_01.jpg", "size": 185352}]	CNY	1476.28	265.73	0.1800
136	43	2025-10-31	entertainment	Coffee section with Andrew	1	29.8	draft	2025-11-10 15:00:46.01249	2025-11-11 17:53:54.875341	[{"filename": "PMA-SA_BX2025111004_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111004/PMA-SA_BX2025111004_01_01.jpeg", "size": 43943}]	MYR	29.80	29.80	1.0000
62	12	2025-09-18	meals	lunch	0	59	draft	2025-09-18 10:28:15.680511	2025-09-18 10:28:15.680515	\N	CNY	59.00	59.00	1.0000
63	12	2025-09-18	local_transport	lunch	0	100	draft	2025-09-18 10:29:56.248002	2025-09-18 10:29:56.248008	\N	CNY	100.00	100.00	1.0000
66	14	2025-08-06	meals	Dinner with Alesandro	1	59.85	draft	2025-09-18 14:37:50.106008	2025-09-19 14:23:52.912156	[{"filename": "PMA-SA_BX2025091803_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091803/PMA-SA_BX2025091803_01_01.jpeg", "size": 69019}]	MYR	59.85	59.85	1.0000
68	16	2025-08-26	entertainment	Lunch with Mr. Khor	1	50.6	draft	2025-09-18 14:44:04.692683	2025-09-19 14:21:32.380392	[{"filename": "PMA-SA_BX2025091805_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091805/PMA-SA_BX2025091805_01_01.jpeg", "size": 40714}]	MYR	50.60	50.60	1.0000
67	15	2025-08-21	entertainment	Lunch with Mr. Zaimi and his colleagues	1	179.1	draft	2025-09-18 14:40:06.330561	2025-09-19 14:23:03.284021	[{"filename": "PMA-SA_BX2025091804_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091804/PMA-SA_BX2025091804_01_01.jpeg", "size": 46657}]	MYR	179.10	179.10	1.0000
57	11	2025-08-12	travel_accommodation	Trip flight to Jakarta and back singapore	1	193.14	draft	2025-08-15 09:56:50.505104	2025-09-19 13:19:50.965046	[{"filename": "PMA-SA_BX2025081501_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081501/PMA-SA_BX2025081501_01_01.pdf", "size": 280275}]	CNY	1079.00	193.14	0.1790
59	11	2025-08-12	local_transport	Jakarta airport to hotel garb	1	18.18	draft	2025-08-15 09:56:50.531335	2025-09-19 13:19:50.97019	[{"filename": "PMA-SA_BX2025081501_03_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081501/PMA-SA_BX2025081501_03_01.heic", "size": 65263, "uploaded_at": "2025-09-19T05:19:50.813441"}]	IDR	181800.00	18.18	0.0001
60	11	2025-08-12	travel_accommodation	Changi airport to home	1	27.6	draft	2025-08-15 09:56:50.544434	2025-09-19 13:19:50.970193	[{"filename": "PMA-SA_BX2025081501_04_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081501/PMA-SA_BX2025081501_04_01.heic", "size": 72631, "uploaded_at": "2025-09-19T05:19:50.963674"}]	CNY	27.60	27.60	1.0000
71	18	2025-07-29	travel_accommodation	singapore to bankok	1	227.7	draft	2025-09-19 13:36:00.691455	2025-10-01 23:24:28.930237	[{"filename": "PMA-SA_BX2025091901_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091901/PMA-SA_BX2025091901_01_01.pdf", "size": 209437, "uploaded_at": "2025-10-01T15:24:28.927269"}]	CNY	1265.00	227.70	0.1800
54	9	2025-08-12	travel_accommodation	hotel in Taibei 3 night	1	484.6633584	draft	2025-08-12 13:17:00.514231	2025-10-02 12:47:15.039997	[{"filename": "PMA-SA_BX2025081204_01_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025081204/PMA-SA_BX2025081204_01_01.heic", "size": 136454}]	CNY	2678.29	484.66	0.1810
74	18	2025-07-31	travel_accommodation	Bankok to Singapore	1	189.18	draft	2025-09-19 13:36:01.885299	2025-09-19 13:49:28.101613	[{"filename": "PMA-SA_BX2025091901_03_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091901/PMA-SA_BX2025091901_03_01.pdf", "size": 209358}]	CNY	1051.00	189.18	0.1800
73	18	2025-07-31	meals	lunch in airport with patrick and quad	0	63.42	draft	2025-09-19 13:36:01.318389	2025-10-01 23:12:57.199917	\N	THB	1585.54	63.42	0.0400
76	19	2025-07-17	entertainment	dinner	1	624.68	draft	2025-09-19 14:03:42.910383	2025-10-01 23:03:19.438638	[{"filename": "PMA-SA_BX2025091902_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091902/PMA-SA_BX2025091902_01_01.jpeg", "size": 236792}]	SGD	624.68	624.68	1.0000
151	53	2025-11-04	travel_accommodation	Round Trip Flight Ticket (4-6th Nov 2025)	1	712.92	draft	2025-11-11 17:29:45.483859	2025-11-18 14:05:55.476648	[{"filename": "PMA-SA_BX2025111102_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111102/PMA-SA_BX2025111102_01_01.pdf", "size": 32309}]	MYR	712.92	712.92	1.0000
75	18	2025-07-31	local_transport	Grab in Bankok	3	58.4	draft	2025-09-19 13:49:28.103559	2025-10-01 23:12:57.203538	[{"filename": "PMA-SA_BX2025091901_05_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091901/PMA-SA_BX2025091901_05_01.jpeg", "size": 163635}, {"filename": "PMA-SA_BX2025091901_05_02.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091901/PMA-SA_BX2025091901_05_02.jpeg", "size": 159048}, {"filename": "PMA-SA_BX2025091901_05_03.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091901/PMA-SA_BX2025091901_05_03.jpeg", "size": 171577}]	THB	1460.00	58.40	0.0400
70	17	2025-08-29	entertainment	Lunch with Ms. Tan and the sale teams	1	266.95	draft	2025-09-18 14:45:29.7352	2025-09-19 14:17:01.565805	[{"filename": "PMA-SA_BX2025091806_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091806/PMA-SA_BX2025091806_01_01.jpeg", "size": 60790}]	MYR	266.95	266.95	1.0000
81	21	2025-09-09	entertainment	dinner with fu and sale team	1	208.05	draft	2025-09-19 14:35:23.578122	2025-10-17 22:54:01.467533	[{"filename": "PMA-SA_BX2025091904_02_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_02_01.jpeg", "size": 260055}]	MYR	1155.85	208.05	0.1800
69	16	2025-08-26	entertainment	Coffee section with the project teams	1	59.9	draft	2025-09-18 14:44:05.190121	2025-09-19 14:21:32.380399	[{"filename": "PMA-SA_BX2025091805_02_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091805/PMA-SA_BX2025091805_02_01.jpeg", "size": 68708}]	MYR	59.90	59.90	1.0000
152	53	2025-11-04	travel_accommodation	Additional check in luggage (KL-Thai)	1	250	draft	2025-11-11 17:29:46.136939	2025-11-18 14:05:55.476656	[{"filename": "PMA-SA_BX2025111102_02_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111102/PMA-SA_BX2025111102_02_01.jpeg", "size": 32553}]	MYR	250.00	250.00	1.0000
72	18	2025-07-30	meals	dinner with Patrick	1	88.56	draft	2025-09-19 13:36:01.08938	2025-10-01 23:24:28.932951	[{"filename": "PMA-SA_BX2025091901_02_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091901/PMA-SA_BX2025091901_02_01.jpeg", "size": 182564}]	THB	2214.00	88.56	0.0400
77	20	2025-06-04	meals	lunch with roy and quah	1	28.839557499999998	draft	2025-09-19 14:11:27.859818	2025-10-02 12:44:27.283602	[{"filename": "PMA-SA_BX2025091903_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091903/PMA-SA_BX2025091903_01_01.jpeg", "size": 136968}]	MYR	94.25	28.84	0.3060
78	20	2025-06-04	meals	dinner with team	1	90.08345599999998	draft	2025-09-19 14:11:27.868706	2025-10-02 12:44:27.283607	[{"filename": "PMA-SA_BX2025091903_02_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091903/PMA-SA_BX2025091903_02_01.jpeg", "size": 189381}]	MYR	294.40	90.08	0.3060
155	53	2025-11-06	travel_accommodation	Additional check in luggage (Thai-KL)	1	228.33	draft	2025-11-11 17:29:46.445667	2025-11-18 14:08:03.609691	[{"filename": "PMA-SA_BX2025111102_05_01.jpg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111102/PMA-SA_BX2025111102_05_01.jpg", "size": 51594}]	MYR	228.33	228.33	1.0000
80	21	2025-09-09	travel_accommodation	Hotel in KL 4 night	1	574.66	draft	2025-09-19 14:35:23.284813	2025-10-17 22:52:03.612088	[{"filename": "PMA-SA_BX2025091904_01_01.jpg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_01_01.jpg", "size": 392400}]	MYR	1886.00	574.66	0.3047
137	44	2025-10-22	entertainment	Coffee section with Mathhew and the technical team	1	54	draft	2025-11-10 15:25:09.498467	2025-11-11 17:54:34.826433	[{"filename": "PMA-SA_BX2025111005_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111005/PMA-SA_BX2025111005_01_01.jpeg", "size": 69197}]	MYR	54.00	54.00	1.0000
138	45	2025-10-13	entertainment	Coffee section with Ms. Liyana	1	15.8	draft	2025-11-10 15:30:18.73825	2025-11-11 17:54:57.3549	[{"filename": "PMA-SA_BX2025111006_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111006/PMA-SA_BX2025111006_01_01.jpeg", "size": 25081}]	MYR	15.80	15.80	1.0000
147	51	2025-10-15	travel_accommodation	Accommodation (14-15th Nov 2025)	1	278.83	draft	2025-11-10 17:08:50.203612	2025-11-18 15:10:22.002053	[{"filename": "PMA-SA_BX2025111012_03_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111012/PMA-SA_BX2025111012_03_01.png", "size": 88124}]	MYR	278.83	278.83	1.0000
158	54	2025-11-07	travel_accommodation	Milleage Claim (7-9th Nov 2025)	2	546	draft	2025-11-11 17:51:15.843102	2025-11-24 13:57:58.424381	[{"filename": "PMA-SA_BX2025111103_02_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111103/PMA-SA_BX2025111103_02_01.png", "size": 614431}, {"filename": "PMA-SA_BX2025111103_02_02.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111103/PMA-SA_BX2025111103_02_02.pdf", "size": 153976}]	MYR	546.00	546.00	1.0000
140	47	2025-10-09	entertainment	Coffee section	1	20	draft	2025-11-10 15:56:04.027027	2025-11-11 17:55:45.531304	[{"filename": "PMA-SA_BX2025111008_02_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111008/PMA-SA_BX2025111008_02_01.jpeg", "size": 24133}]	MYR	20.00	20.00	1.0000
114	33	2025-10-14	meals	Dinner with tech team and quah	1	80.55862499999999	draft	2025-10-17 12:19:11.119687	2025-11-20 19:39:41.03771	[{"filename": "PMA-SA_BX2025101701_02_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101701/PMA-SA_BX2025101701_02_01.jpeg", "size": 405597}]	MYR	262.50	80.56	0.3069
104	30	2025-10-10	travel_accommodation	flight to KL and back to singapore	2	141.79358	draft	2025-10-11 14:55:43.315096	2025-10-23 20:13:51.625624	[{"filename": "PMA-SA_BX2025101101_02_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101101/PMA-SA_BX2025101101_02_01.pdf", "size": 61800, "uploaded_at": "2025-10-11T06:58:03.832968"}, {"filename": "PMA-SA_BX2025101101_02_02.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101101/PMA-SA_BX2025101101_02_02.pdf", "size": 61500, "uploaded_at": "2025-10-11T06:58:03.971200"}]	CNY	779.00	141.79	0.1820
83	21	2025-09-13	travel_accommodation	fight to KL and back to singapore	3	523.62	draft	2025-09-19 14:35:25.004042	2025-09-24 07:55:13.433792	[{"filename": "PMA-SA_BX2025091904_02_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_02_01.pdf", "size": 61976}, {"filename": "PMA-SA_BX2025091904_02_02.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_02_02.pdf", "size": 61517}, {"filename": "PMA-SA_BX2025091904_02_03.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_02_03.pdf", "size": 209629}]	CNY	2909.00	523.62	0.1800
139	46	2025-10-15	entertainment	Lunch with Mr. Zhou	1	56.5	draft	2025-11-10 15:49:09.73741	2025-11-11 17:55:21.235302	[{"filename": "PMA-SA_BX2025111007_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111007/PMA-SA_BX2025111007_01_01.jpeg", "size": 39772}]	MYR	56.50	56.50	1.0000
109	32	2025-09-08	other	Trolley for Exhibition Usage.	1	200	draft	2025-10-16 14:55:14.285565	2025-10-16 14:56:02.49567	[{"filename": "PMA-SA_BX2025101602_02_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101602/PMA-SA_BX2025101602_02_01.pdf", "size": 904755}]	MYR	200.00	200.00	1.0000
106	31	2025-08-07	entertainment	Invited Alesandro to visit Trac consult & provide coffee to Trac team for inhouse presentation.	1	131.55	draft	2025-10-16 14:12:42.642241	2025-10-16 14:13:24.319061	[{"filename": "PMA-SA_BX2025101601_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101601/PMA-SA_BX2025101601_01_01.pdf", "size": 71842}]	MYR	131.55	131.55	1.0000
107	31	2025-08-08	entertainment	Welcome lunch for Alesandro	1	86.45	draft	2025-10-16 14:12:43.60043	2025-10-16 14:13:24.3217	[{"filename": "PMA-SA_BX2025101601_02_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101601/PMA-SA_BX2025101601_02_01.pdf", "size": 109569}]	MYR	86.45	86.45	1.0000
127	38	2025-11-06	local_transport	Taxi in Bankok	2	15.76	draft	2025-11-09 11:25:33.608986	2025-11-09 13:47:12.124881	[{"filename": "PMA-SA_BX2025110903_04_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110903/PMA-SA_BX2025110903_04_01.heic", "size": 64332}, {"filename": "PMA-SA_BX2025110903_04_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110903/PMA-SA_BX2025110903_04_02.heic", "size": 68559}]	THB	394.00	15.76	0.0400
82	21	2025-09-13	travel_accommodation	office go and back to change airport	2	54.2	draft	2025-09-19 14:35:24.104577	2025-10-17 22:52:03.616379	[{"filename": "PMA-SA_BX2025091904_03_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_03_01.jpeg", "size": 190069}, {"filename": "PMA-SA_BX2025091904_03_02.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_03_02.jpeg", "size": 191915}]	SGD	54.20	54.20	1.0000
103	30	2025-10-08	travel_accommodation	hotel 1 night	1	78.4433392	draft	2025-10-11 14:55:43.302536	2025-10-23 20:13:51.62562	[{"filename": "PMA-SA_BX2025101101_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101101/PMA-SA_BX2025101101_01_01.pdf", "size": 61066, "uploaded_at": "2025-10-11T06:58:03.705280"}]	CNY	430.96	78.44	0.1820
108	32	2025-09-08	other	Brochure Stand Rental for Engineer & Marvex KLCC Exhibition.	1	120.96	draft	2025-10-16 14:55:13.846439	2025-10-16 14:56:02.495664	[{"filename": "PMA-SA_BX2025101602_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101602/PMA-SA_BX2025101602_01_01.pdf", "size": 170719}]	MYR	120.96	120.96	1.0000
110	32	2025-09-08	other	Purchased Items for Exhibition.	1	24	draft	2025-10-16 14:55:14.522526	2025-10-16 14:56:02.495671	[{"filename": "PMA-SA_BX2025101602_03_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101602/PMA-SA_BX2025101602_03_01.pdf", "size": 134694}]	MYR	24.00	24.00	1.0000
111	32	2025-09-08	other	Purchased Items for Exhibition	1	83.5	draft	2025-10-16 14:55:14.72124	2025-10-16 14:56:02.495672	[{"filename": "PMA-SA_BX2025101602_04_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101602/PMA-SA_BX2025101602_04_01.pdf", "size": 117657}]	MYR	83.50	83.50	1.0000
112	32	2025-09-09	meals	Lunch during exhibition	1	25.3	draft	2025-10-16 14:55:14.864235	2025-10-16 14:56:02.495673	[{"filename": "PMA-SA_BX2025101602_05_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101602/PMA-SA_BX2025101602_05_01.pdf", "size": 152886}]	MYR	25.30	25.30	1.0000
105	30	2025-10-11	meals	lunch with peizhen, patrick and roy, quah	1	64.12288	draft	2025-10-11 14:55:43.329191	2025-10-23 20:13:51.625626	[{"filename": "PMA-SA_BX2025101101_03_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101101/PMA-SA_BX2025101101_03_01.png", "size": 150144, "uploaded_at": "2025-10-11T06:58:04.394812"}]	MYR	202.00	64.12	0.3174
128	38	2025-11-09	travel_accommodation	Hotel 2 night 2 room for James and Quah	1	461.87	draft	2025-11-09 11:25:34.239842	2025-11-09 13:47:12.124888	[{"filename": "PMA-SA_BX2025110903_02_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110903/PMA-SA_BX2025110903_02_01.pdf", "size": 61140}]	CNY	2565.92	461.87	0.1800
87	22	2025-09-25	travel_accommodation	Hotel in Bankok 2 night	1	328.4424	draft	2025-09-28 12:42:03.623452	2025-10-02 16:38:00.001872	[{"filename": "PMA-SA_BX2025092801_02_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025092801/PMA-SA_BX2025092801_02_01.pdf", "size": 61063}]	CNY	1815.00	328.44	0.1810
143	49	2025-10-07	entertainment	Entertainment with Mr. William	1	96.75	draft	2025-11-10 16:07:50.159819	2025-11-11 17:56:32.787322	[{"filename": "PMA-SA_BX2025111010_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111010/PMA-SA_BX2025111010_01_01.jpeg", "size": 26308}]	MYR	96.75	96.75	1.0000
144	50	2025-10-15	entertainment	Coffee section with Mr. Zhang	1	19	draft	2025-11-10 16:12:53.201652	2025-11-11 17:56:56.882544	[{"filename": "PMA-SA_BX2025111011_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111011/PMA-SA_BX2025111011_01_01.jpeg", "size": 47059}]	MYR	19.00	19.00	1.0000
89	23	2025-09-03	parking	Parking (OGA Exhibition 2025)	1	31	draft	2025-10-02 16:50:54.381496	2025-10-02 16:51:20.821818	[{"filename": "PMA-SA_BX2025100201_01_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100201/PMA-SA_BX2025100201_01_01.png", "size": 20545}]	MYR	31.00	31.00	1.0000
90	23	2025-09-04	parking	Parking (OGA Exhibition 2025)	1	26	draft	2025-10-02 16:50:54.76967	2025-10-02 16:51:20.821825	[{"filename": "PMA-SA_BX2025100201_02_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100201/PMA-SA_BX2025100201_02_01.png", "size": 20782}]	MYR	26.00	26.00	1.0000
142	48	2025-10-30	entertainment	Lunch together with Fizwan after meeting with the user	1	100.2	draft	2025-11-10 16:02:09.171488	2025-11-11 17:56:09.533957	[{"filename": "PMA-SA_BX2025111009_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111009/PMA-SA_BX2025111009_01_01.jpeg", "size": 21314}]	MYR	100.20	100.20	1.0000
85	22	2025-09-18	travel_accommodation	Flight Changi to Bankok and back	2	236.87664	draft	2025-09-28 12:42:00.944965	2025-10-02 16:38:00.001866	[{"filename": "PMA-SA_BX2025092801_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025092801/PMA-SA_BX2025092801_01_01.pdf", "size": 209345}, {"filename": "PMA-SA_BX2025092801_01_02.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025092801/PMA-SA_BX2025092801_01_02.pdf", "size": 61084}]	CNY	1309.00	236.88	0.1810
86	22	2025-09-24	local_transport	Hotel to MOT office	1	19.63156	draft	2025-09-28 12:42:03.383675	2025-10-02 16:38:00.001871	[{"filename": "PMA-SA_BX2025092801_03_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025092801/PMA-SA_BX2025092801_03_01.pdf", "size": 222777}]	THB	494.00	19.63	0.0397
99	26	2025-09-04	entertainment	Dinner with Wee Meng and the teams	1	256.75	draft	2025-10-02 17:28:31.672556	2025-10-02 17:28:45.553521	[{"filename": "PMA-SA_BX2025100204_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100204/PMA-SA_BX2025100204_01_01.jpeg", "size": 26831}]	MYR	256.75	256.75	1.0000
96	25	2025-09-09	meals	Meal with Evertac Staff	1	45.8	draft	2025-10-02 17:24:40.752117	2025-10-02 17:25:06.38532	[{"filename": "PMA-SA_BX2025100203_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100203/PMA-SA_BX2025100203_01_01.jpeg", "size": 45838}]	MYR	45.80	45.80	1.0000
97	25	2025-09-10	meals	Meal with Evertac Staff	1	27	draft	2025-10-02 17:24:41.261604	2025-10-02 17:25:06.385324	[{"filename": "PMA-SA_BX2025100203_02_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100203/PMA-SA_BX2025100203_02_01.jpeg", "size": 27483}]	MYR	27.00	27.00	1.0000
91	24	2025-09-08	parking	Parking (Engineer & Marvex Exhibition 2025)	1	46	draft	2025-10-02 16:56:13.057561	2025-10-02 16:56:47.088868	[{"filename": "PMA-SA_BX2025100202_01_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100202/PMA-SA_BX2025100202_01_01.png", "size": 10090}]	MYR	46.00	46.00	1.0000
92	24	2025-09-09	parking	Parking (Engineer & Marvex Exhibition 2025)	1	51	draft	2025-10-02 16:56:13.426476	2025-10-02 16:56:47.088874	[{"filename": "PMA-SA_BX2025100202_02_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100202/PMA-SA_BX2025100202_02_01.png", "size": 7435}]	MYR	51.00	51.00	1.0000
93	24	2025-09-10	parking	Parking (Engineer & Marvex Exhibition 2025)	1	20	draft	2025-10-02 16:56:13.559815	2025-10-02 16:56:47.088875	[{"filename": "PMA-SA_BX2025100202_03_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100202/PMA-SA_BX2025100202_03_01.png", "size": 20588}]	MYR	20.00	20.00	1.0000
94	24	2025-09-11	parking	Parking (Engineer & Marvex Exhibition 2025)	1	20	draft	2025-10-02 16:56:13.711248	2025-10-02 16:56:47.088876	[{"filename": "PMA-SA_BX2025100202_04_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100202/PMA-SA_BX2025100202_04_01.png", "size": 20136}]	MYR	20.00	20.00	1.0000
95	24	2025-09-12	parking	Parking (Engineer & Marvex Exhibition 2025)	1	20	draft	2025-10-02 16:56:13.844021	2025-10-02 16:56:47.088877	[{"filename": "PMA-SA_BX2025100202_05_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100202/PMA-SA_BX2025100202_05_01.png", "size": 21176}]	MYR	20.00	20.00	1.0000
98	25	2025-09-12	meals	Meal with Evertac Staff	1	43.4	draft	2025-10-02 17:24:41.422745	2025-10-02 17:25:06.385326	[{"filename": "PMA-SA_BX2025100203_03_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100203/PMA-SA_BX2025100203_03_01.jpeg", "size": 28125}]	MYR	43.40	43.40	1.0000
100	27	2025-09-10	entertainment	Dinner with 付总	1	152	draft	2025-10-02 17:31:02.148949	2025-10-02 17:31:02.590286	[{"filename": "PMA-SA_BX2025100205_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100205/PMA-SA_BX2025100205_01_01.jpeg", "size": 31570}]	MYR	152.00	152.00	1.0000
101	28	2025-09-10	entertainment	Lunch with Fizwan	1	43.55	draft	2025-10-02 17:32:45.181648	2025-10-02 17:32:45.599753	[{"filename": "PMA-SA_BX2025100206_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100206/PMA-SA_BX2025100206_01_01.jpeg", "size": 28337}]	MYR	43.55	43.55	1.0000
102	29	2025-09-30	entertainment	Lunch with Mr. Darshan	1	66	draft	2025-10-02 17:36:19.112803	2025-10-02 17:36:19.469023	[{"filename": "PMA-SA_BX2025100207_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025100207/PMA-SA_BX2025100207_01_01.jpeg", "size": 33887}]	MYR	66.00	66.00	1.0000
84	21	2025-09-13	local_transport	hotel to exhibition and triple access office	4	44.15	draft	2025-09-19 14:41:42.177792	2025-10-17 22:54:01.469658	[{"filename": "PMA-SA_BX2025091904_05_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_05_01.jpeg", "size": 180479}, {"filename": "PMA-SA_BX2025091904_05_02.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_05_02.jpeg", "size": 183541}, {"filename": "PMA-SA_BX2025091904_05_03.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_05_03.jpeg", "size": 171597}, {"filename": "PMA-SA_BX2025091904_05_04.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025091904/PMA-SA_BX2025091904_05_04.jpeg", "size": 177234}]	MYR	127.24	44.15	0.3470
123	38	2025-10-30	travel_accommodation	Flight to Bankok and back	1	201.78	draft	2025-11-09 11:04:19.118758	2025-11-09 11:04:19.499222	[{"filename": "PMA-SA_BX2025110903_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110903/PMA-SA_BX2025110903_01_01.pdf", "size": 211498}]	CNY	1121.00	201.78	0.1800
119	35	2025-10-24	travel_accommodation	Flight Ticket to Malaysia	1	265.64	draft	2025-11-04 16:10:36.878091	2025-11-04 16:14:29.986245	[{"filename": "PMA-SA_BX2025110401_02_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110401/PMA-SA_BX2025110401_02_01.pdf", "size": 449495}]	IDR	1027374.00	265.64	0.0003
115	34	2025-10-02	other	Mooncake festival 2025 for Malaysia	1	573.9	draft	2025-10-23 10:24:13.441046	2025-10-23 20:10:57.396846	[{"filename": "PMA-SA_BX2025102301_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025102301/PMA-SA_BX2025102301_01_01.pdf", "size": 779596}]	MYR	573.90	573.90	1.0000
116	34	2025-10-10	fuel	Petrol on customer / partner visit from time to time	1	74.05	draft	2025-10-23 10:24:14.635165	2025-10-23 20:10:57.401014	[{"filename": "PMA-SA_BX2025102301_02_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025102301/PMA-SA_BX2025102301_02_01.pdf", "size": 779596}]	MYR	74.05	74.05	1.0000
117	34	2025-10-09	entertainment	Coffee with James & Quah	1	33.05	draft	2025-10-23 10:24:15.012488	2025-10-23 20:10:57.401018	[{"filename": "PMA-SA_BX2025102301_03_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025102301/PMA-SA_BX2025102301_03_01.pdf", "size": 779596}]	MYR	33.05	33.05	1.0000
118	35	2025-10-20	travel_accommodation	Flight Ticket to Jakarta	1	491.39	draft	2025-11-04 16:10:35.317965	2025-11-04 16:10:36.874313	[{"filename": "PMA-SA_BX2025110401_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110401/PMA-SA_BX2025110401_01_01.pdf", "size": 130259}]	MYR	491.39	491.39	1.0000
125	38	2025-11-04	entertainment	dinner with partner	1	47.26	draft	2025-11-09 11:09:57.985253	2025-11-09 13:47:12.118292	[{"filename": "PMA-SA_BX2025110903_06_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110903/PMA-SA_BX2025110903_06_01.heic", "size": 63614}]	SGD	47.26	47.26	1.0000
120	35	2025-10-24	travel_accommodation	Changing Flight Ticket Date to Malaysia	2	277.75	draft	2025-11-04 16:10:37.100184	2025-11-06 16:20:29.599274	[{"filename": "PMA-SA_BX2025110401_03_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110401/PMA-SA_BX2025110401_03_01.png", "size": 48231}, {"filename": "PMA-SA_BX2025110401_03_02.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110401/PMA-SA_BX2025110401_03_02.pdf", "size": 59788, "uploaded_at": "2025-11-06T08:20:29.597121"}]	MYR	277.75	277.75	1.0000
145	51	2025-10-15	travel_accommodation	Tolls (14-15th Oct 2025)	1	79.38	draft	2025-11-10 17:06:18.934879	2025-11-24 13:57:19.676739	[{"filename": "PMA-SA_BX2025111012_01_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111012/PMA-SA_BX2025111012_01_01.png", "size": 203568}]	MYR	79.38	79.38	1.0000
124	38	2025-11-04	local_transport	Taxi to Changgi airport	1	30.4	draft	2025-11-09 11:04:19.501444	2025-11-09 11:25:33.598237	[{"filename": "PMA-SA_BX2025110903_03_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110903/PMA-SA_BX2025110903_03_01.heic", "size": 57870}]	CNY	30.40	30.40	1.0000
122	37	2025-11-02	entertainment	dinner	1	571.08	draft	2025-11-09 10:46:33.020717	2025-11-09 10:46:52.775041	[{"filename": "PMA-SA_BX2025110902_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110902/PMA-SA_BX2025110902_01_01.pdf", "size": 1957682}]	SGD	571.08	571.08	1.0000
126	38	2025-11-05	entertainment	Lunch with partner	2	35.32	draft	2025-11-09 11:09:58.167816	2025-11-09 13:47:12.118301	[{"filename": "PMA-SA_BX2025110903_05_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110903/PMA-SA_BX2025110903_05_01.heic", "size": 637124}, {"filename": "PMA-SA_BX2025110903_05_02.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110903/PMA-SA_BX2025110903_05_02.heic", "size": 54516}]	SGD	35.32	35.32	1.0000
133	40	2025-10-28	entertainment	Lunch with Ir. Low	1	162.85	draft	2025-11-10 14:34:56.279893	2025-11-11 17:53:01.009739	[{"filename": "PMA-SA_BX2025111001_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111001/PMA-SA_BX2025111001_01_01.jpeg", "size": 27591}]	MYR	162.85	162.85	1.0000
135	42	2025-10-02	entertainment	Lunch with Mr. Lee	1	93.3	draft	2025-11-10 14:56:51.376551	2025-11-13 07:17:50.625664	[{"filename": "PMA-SA_BX2025111003_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111003/PMA-SA_BX2025111003_01_01.jpeg", "size": 19508}]	MYR	93.30	93.30	1.0000
121	36	2025-11-08	meals	Dinner with Fu	1	80.288768	draft	2025-11-09 10:39:23.430536	2025-11-13 18:54:45.128758	[{"filename": "PMA-SA_BX2025110901_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110901/PMA-SA_BX2025110901_01_01.pdf", "size": 1955224}]	MYR	257.60	80.29	0.3117
129	39	2025-10-25	travel_accommodation	Flight back to singapore from Jakarta due to the schedule change	1	129.42	draft	2025-11-09 11:43:20.484708	2025-11-09 11:43:20.893388	[{"filename": "PMA-SA_BX2025110904_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110904/PMA-SA_BX2025110904_01_01.pdf", "size": 209311}]	CNY	719.00	129.42	0.1800
130	39	2025-10-25	travel_accommodation	Flight to Jakarta and back singapore,but the ticket of back flight canncel due to schedule change	1	211.91	draft	2025-11-09 11:43:20.895795	2025-11-09 11:43:21.11266	[{"filename": "PMA-SA_BX2025110904_02_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110904/PMA-SA_BX2025110904_02_01.pdf", "size": 209333}]	CNY	1158.00	211.91	0.1830
131	39	2025-10-21	travel_accommodation	Jakarta 1 night 2 room with china team for site survey	1	117.07199999999999	draft	2025-11-09 11:43:21.115022	2025-11-09 11:43:21.254896	[{"filename": "PMA-SA_BX2025110904_03_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110904/PMA-SA_BX2025110904_03_01.pdf", "size": 60497}]	CNY	650.40	117.07	0.1800
132	38	2025-11-04	other	Gift coffee for dealer	1	50.46	draft	2025-11-09 13:47:12.129333	2025-11-09 13:47:12.375198	[{"filename": "PMA-SA_BX2025110903_07_01.heic", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025110903/PMA-SA_BX2025110903_07_01.heic", "size": 756385, "uploaded_at": "2025-11-09T05:47:12.371746"}]	CNY	50.46	50.46	1.0000
156	53	2025-11-06	local_transport	Grab from airport ( From KLIA to home )	1	86.92	draft	2025-11-11 17:29:46.725706	2025-11-18 14:08:03.612447	[{"filename": "PMA-SA_BX2025111102_06_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111102/PMA-SA_BX2025111102_06_01.png", "size": 267794}]	MYR	86.92	86.92	1.0000
148	52	2025-10-03	entertainment	Lunch with Trac Consult Azri to check YTL DC	1	62	draft	2025-11-11 11:26:52.204617	2025-11-11 11:31:18.96578	[{"filename": "PMA-SA_BX2025111101_01_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111101/PMA-SA_BX2025111101_01_01.pdf", "size": 183602}]	MYR	62.00	62.00	1.0000
149	52	2025-10-30	entertainment	Lunch with Trac Consult Krisnaa to follow GDS block F site meeting	1	59.6	draft	2025-11-11 11:26:52.587628	2025-11-11 11:31:18.965788	[{"filename": "PMA-SA_BX2025111101_02_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111101/PMA-SA_BX2025111101_02_01.pdf", "size": 95767}]	MYR	59.60	59.60	1.0000
150	52	2025-10-30	office_supplies	Roll up banners for seminar	1	318	draft	2025-11-11 11:31:18.969775	2025-11-11 11:31:19.179358	[{"filename": "PMA-SA_BX2025111101_03_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111101/PMA-SA_BX2025111101_03_01.pdf", "size": 156904, "uploaded_at": "2025-11-11T03:31:19.175784"}]	CNY	318.00	318.00	1.0000
141	47	2025-10-13	entertainment	Lunch with Ms. Nurshaliana	1	32.5	draft	2025-11-10 15:56:04.405022	2025-11-11 17:55:45.531312	[{"filename": "PMA-SA_BX2025111008_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111008/PMA-SA_BX2025111008_01_01.jpeg", "size": 35938}]	MYR	32.50	32.50	1.0000
153	53	2025-11-04	travel_accommodation	Grab in thailand	1	194.51	draft	2025-11-11 17:29:46.283688	2025-11-18 14:05:55.483726	[{"filename": "PMA-SA_BX2025111102_03_01.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111102/PMA-SA_BX2025111102_03_01.pdf", "size": 143311}]	THB	1502.00	194.51	0.1295
154	53	2025-11-04	local_transport	Grab to airport ( From home to KLIA )	1	79.19	draft	2025-11-11 17:29:46.435828	2025-11-18 14:05:55.486528	[{"filename": "PMA-SA_BX2025111102_05_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111102/PMA-SA_BX2025111102_05_01.png", "size": 90480}]	MYR	79.19	79.19	1.0000
113	33	2025-10-14	meals	Coffee with tech team	2	10.096681	draft	2025-10-17 12:19:10.031935	2025-11-20 19:39:41.037704	[{"filename": "PMA-SA_BX2025101701_01_01.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101701/PMA-SA_BX2025101701_01_01.jpeg", "size": 330794}, {"filename": "PMA-SA_BX2025101701_01_02.jpeg", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025101701/PMA-SA_BX2025101701_01_02.jpeg", "size": 347184}]	MYR	32.90	10.10	0.3069
146	51	2025-10-15	travel_accommodation	Milleage Claim (14-15th Oct 2025)	2	551	draft	2025-11-10 17:06:19.952494	2025-11-24 13:57:19.680628	[{"filename": "PMA-SA_BX2025111012_02_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111012/PMA-SA_BX2025111012_02_01.png", "size": 607185}, {"filename": "PMA-SA_BX2025111012_02_02.pdf", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111012/PMA-SA_BX2025111012_02_02.pdf", "size": 251343}]	MYR	551.60	551.00	1.0000
157	54	2025-11-07	travel_accommodation	Toll (7-9th Nov 2025)	1	79.11	draft	2025-11-11 17:51:15.373746	2025-11-24 13:57:58.424375	[{"filename": "PMA-SA_BX2025111103_01_01.png", "url": "https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/invoice-images/invoice_files/PMA-SA/BX2025111103/PMA-SA_BX2025111103_01_01.png", "size": 79236}]	MYR	79.11	79.11	1.0000
\.


--
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.expenses (id, expense_number, title, description, customer_id, project_id, total_amount, status, is_locked, approved_by, approved_at, approval_notes, owner_id, created_at, updated_at, is_deleted, contact_id, currency, payment_status, payment_amount, payment_date, payment_method, payment_reference, payment_notes, paid_by) FROM stdin;
5	BX2025080803	测试非关联客-admin-2508082202	测试非关联客户	\N	\N	111	draft	f	\N	\N	\N	1	2025-08-08 22:53:41.42094	2025-08-08 22:54:01.484482	t	\N	USD	unpaid	\N	\N	\N	\N	\N	\N
1	BX2025080601	MCS Management Sdn Bhd-quah-2508060603		15	\N	250	paid	t	\N	\N	\N	2	2025-08-06 14:48:03.218555	2025-08-06 14:49:57.258183	f	39	MYR	paid	\N	2025-08-06 06:49:57.257434	\N	\N	\N	5
3	BX2025080802	TM Technology Service Sdn Bhd -admin-2508081047		65	\N	163.8	draft	f	\N	\N	\N	1	2025-08-08 18:16:47.173281	2025-08-08 19:40:09.126971	t	83	CNY	unpaid	\N	\N	\N	\N	\N	\N
15	BX2025091804	TM Technology Service Sdn Bhd -quah-2509180606	To built the relationship	65	\N	179.1	paid	t	\N	\N	\N	2	2025-09-18 14:40:06.326389	2025-10-02 12:04:36.016804	f	92	MYR	paid	\N	2025-10-02 04:04:36.016395	\N	\N	\N	5
14	BX2025091803	Dinner-quah-2509181437	Dinner with Alesandro	\N	\N	59.85	paid	t	\N	\N	\N	2	2025-09-18 14:37:50.102972	2025-10-02 12:04:49.077035	f	\N	MYR	paid	\N	2025-10-02 04:04:49.07662	\N	\N	\N	5
13	BX2025091802	Comintel Sdn Bhd-quah-2509180601	To discuss for Penang Airport opportunities	21	\N	42.85	paid	t	\N	\N	\N	2	2025-09-18 14:29:01.830894	2025-10-02 12:05:01.219038	f	57	MYR	paid	\N	2025-10-02 04:05:01.218555	\N	\N	\N	5
2	BX2025080801	Triple Access Sdn Bhd-admin-2508080034	Training New staff Alesandro and visit customer	42	\N	439.6	pending	t	\N	\N	\N	1	2025-08-08 08:36:34.344676	2025-08-12 12:16:29.88339	f	54	SGD	unpaid	\N	\N	\N	\N	\N	\N
20	BX2025091903	Malays-admin-2509191424	Malaysia sales team building	\N	\N	118.9230135	paid	t	\N	\N	\N	1	2025-09-19 14:11:27.856058	2025-11-13 18:02:51.797755	f	\N	SGD	paid	\N	2025-11-13 10:02:51.797006	\N	\N	\N	5
12	BX2025091801	lunch-quah-2509181015	lunch	\N	\N	159	draft	f	\N	\N	\N	2	2025-09-18 10:28:15.6748	2025-09-18 10:30:29.190188	t	\N	MYR	unpaid	\N	\N	\N	\N	\N	\N
23	BX2025100201	不关联（Parkin）-quah-2510020854	Parking (OGA Exhibition 2025)	\N	\N	57	paid	t	\N	\N	\N	2	2025-10-02 16:50:54.37706	2025-10-16 12:38:42.197547	f	\N	MYR	paid	\N	2025-10-16 04:38:42.196939	\N	\N	\N	5
29	BX2025100207	INNSIDE Hotel by Meliá Kuala Lumpur Cheras-quah-2510020919	Lunch with Mr. Darshan	104	\N	66	paid	t	\N	\N	\N	2	2025-10-02 17:36:19.109927	2025-10-16 12:36:42.987067	f	125	MYR	paid	\N	2025-10-16 04:36:42.983477	\N	\N	\N	5
28	BX2025100206	Triple Access Sdn Bhd-quah-2510020945	Lunch with Fizwan	42	\N	43.55	paid	t	\N	\N	\N	2	2025-10-02 17:32:45.178639	2025-10-16 12:37:21.048034	f	126	MYR	paid	\N	2025-10-16 04:37:21.047387	\N	\N	\N	5
7	BX2025081202	PT. CITRADATA INDONUSA-admin-2508120434		71	\N	581.95	pending	t	\N	\N	\N	1	2025-08-12 12:51:34.661811	2025-08-12 12:52:06.885776	f	87	SGD	unpaid	\N	\N	\N	\N	\N	\N
19	BX2025091902	上海建工集团-admin-2509190642		96	\N	624.68	paid	t	\N	\N	\N	1	2025-09-19 14:03:42.906841	2025-11-13 18:04:08.571849	f	115	SGD	paid	\N	2025-11-13 10:04:08.571053	\N	\N	\N	5
27	BX2025100205	FMTCS SOLUTIONS PTE. LTD-quah-2510020902	Dinner with 付总	28	\N	152	paid	t	\N	\N	\N	2	2025-10-02 17:31:02.1462	2025-10-16 12:37:36.522243	f	33	MYR	paid	\N	2025-10-16 04:37:36.521519	\N	\N	\N	5
9	BX2025081204	COMMUTRONICS ENTERPRISE CO., LTD-admin-2508120500		72	\N	707.7870384	paid	t	\N	\N	\N	1	2025-08-12 13:17:00.509173	2025-11-13 18:04:23.414626	f	89	SGD	paid	\N	2025-11-13 10:04:23.413996	\N	\N	\N	5
21	BX2025091904	Triple Access Sdn Bhd-admin-2509190623	GDS project sign with fu and datacenter exhibition	42	\N	1404.68	pending	t	\N	\N	\N	1	2025-09-19 14:35:23.279281	2025-10-17 22:54:07.993247	f	116	SGD	unpaid	\N	\N	\N	\N	\N	\N
31	BX2025101601	Invite-roy.lim-2510161419	Invited Alesandro to visit Trac consult & provide coffee to Trac team for inhouse presentation.	\N	\N	218	paid	t	\N	\N	\N	3	2025-10-16 14:12:42.633388	2025-10-29 13:56:14.816215	f	\N	MYR	paid	\N	2025-10-29 05:56:14.815556	\N	\N	\N	5
30	BX2025101101	Malaysian Communications and Multimedia Commission-admin-2510110643	visiting mcmc introduce evertacsolutoins company and discuss about the frequency application issue	112	12	284.3597992	paid	t	\N	\N	\N	1	2025-10-11 14:55:43.294379	2025-11-13 18:02:21.664819	f	143	SGD	paid	\N	2025-11-13 10:02:21.664173	\N	\N	\N	5
11	BX2025081501	PT. CITRADATA INDONUSA-admin-2508150150		71	\N	608.61	draft	f	\N	\N	\N	1	2025-08-15 09:56:50.496393	2025-09-19 13:19:51.003604	f	87	SGD	unpaid	\N	\N	\N	\N	\N	\N
26	BX2025100204	RADII Teknologi Sdn Bhd-quah-2510020931	Dinner with Wee Meng and the teams	60	\N	256.75	paid	t	\N	\N	\N	2	2025-10-02 17:28:31.664956	2025-10-16 12:37:52.58984	f	73	MYR	paid	\N	2025-10-16 04:37:52.589191	\N	\N	\N	5
22	BX2025092801	Mot Smart Solutions Company Limited (Head office)-admin-2509280400	With Clayton and Fu meeting with surasak dealer to make sure the next coordation in Thailand.	55	\N	584.9506	paid	t	\N	\N	\N	1	2025-09-28 12:42:00.935877	2025-11-13 18:02:36.726812	f	70	SGD	paid	\N	2025-11-13 10:02:36.726151	\N	\N	\N	5
18	BX2025091901	Mot Smart Solutions Company Limited (Head office)-admin-2509190500		55	\N	627.26	rejected	f	\N	\N	\N	1	2025-09-19 13:36:00.686857	2025-10-01 23:24:28.950186	f	70	SGD	unpaid	\N	\N	\N	\N	\N	\N
25	BX2025100203	Meal w-quah-2510021731	Meal with Evertac Staff	\N	\N	116.2	paid	t	\N	\N	\N	2	2025-10-02 17:24:40.749304	2025-10-16 12:38:08.72414	f	\N	MYR	paid	\N	2025-10-16 04:38:08.723479	\N	\N	\N	5
6	BX2025081201	Mot Smart Solutions Company Limited (Head office)-admin-2508120356	First visit to the Thai partner MOT, conduct technical training on Evertac Solutions, discuss frequency application and certification matters in Thailand, and sign the MOT memorandum.	55	\N	585.78	rejected	f	\N	\N	\N	1	2025-08-12 11:57:56.619171	2025-10-03 20:15:39.98942	f	70	SGD	unpaid	\N	\N	\N	\N	\N	\N
24	BX2025100202	Parkin-quah-2510021631	Parking (Engineer & Marvex Exhibition 2025)	\N	\N	157	paid	t	\N	\N	\N	2	2025-10-02 16:56:13.054673	2025-10-16 12:38:25.591717	f	\N	MYR	paid	\N	2025-10-16 04:38:25.591142	\N	\N	\N	5
17	BX2025091806	RADII Teknologi Sdn Bhd-quah-2509180629	To built up the relationship	60	\N	266.95	paid	t	\N	\N	\N	2	2025-09-18 14:45:29.732061	2025-10-02 12:03:49.377326	f	73	MYR	paid	\N	2025-10-02 04:03:49.376693	\N	\N	\N	5
16	BX2025091805	iFLYTEK-quah-2509180604	Lunch and meeting to discuss about the projects	74	\N	110.5	paid	t	\N	\N	\N	2	2025-09-18 14:44:04.688761	2025-10-02 12:04:21.796278	f	94	MYR	paid	\N	2025-10-02 04:04:21.795755	\N	\N	\N	5
10	BX2025081205	C.A. Sheimer (HK) Ltd-admin-2508120532		73	\N	148.33728	paid	t	\N	\N	\N	1	2025-08-12 13:18:32.927008	2025-10-06 21:43:34.786212	f	90	SGD	paid	\N	2025-10-06 13:43:34.784519	\N	\N	\N	5
8	BX2025081203	china'-admin-2508121259	china's suppler xu and his family	\N	\N	568.93	paid	t	\N	\N	\N	1	2025-08-12 12:57:38.856494	2025-10-06 21:44:11.005369	f	\N	SGD	paid	\N	2025-10-06 13:44:11.004688	\N	\N	\N	5
51	BX2025111012	Meeting at DayOne NTP-F (14-15th Oct 2025)	Meeting with DayOne Block F&H&M planning for T&C together with consultant (14-15th Oct 2025)	129	\N	909.21	pending	t	\N	\N	\N	2	2025-11-10 17:06:18.927844	2025-11-24 13:57:24.971316	f	163	MYR	unpaid	\N	\N	\N	\N	\N	\N
39	BX2025110904	PT. Indonesia Weda Bay Industrial Park (IWIP)-james.ni-2511090320	At the user request go to the Weda bay IWIP project site for survey.	76	\N	458.402	pending	t	\N	\N	\N	1	2025-11-09 11:43:20.480738	2025-11-09 11:47:03.964332	f	97	SGD	unpaid	\N	\N	\N	\N	\N	\N
50	BX2025111011	China Construction Yangtze River (Malaysia) Sdn. Bhd. (Subsidiary of CSCEC)-quah-2511100853	Courtesy visit to CCYR to follow up the current status of R&F Princess Cove III project	39	\N	19	paid	t	\N	\N	\N	2	2025-11-10 16:12:53.195926	2025-11-19 10:02:56.986644	f	127	MYR	paid	\N	2025-11-19 02:02:56.985826	\N	\N	\N	5
49	BX2025111010	SKA Technology Sdn Bhd-quah-2511100850	Understand they are awarded the NEXT DC data center project and subsequently sub out to Radii.	25	\N	96.75	paid	t	\N	\N	\N	2	2025-11-10 16:07:50.154878	2025-11-19 10:03:15.950278	f	9	MYR	paid	\N	2025-11-19 02:03:15.949561	\N	\N	\N	5
40	BX2025111001	EcoWorld HQ-quah-2511100656	Understand from Ir. Low that currently the mix development project that he handle didn't include the walkie-talkie system. \r\nHe direct us to find another department EcoWorld Quantum which the department are more focusing on datacenter project and may need our system.	128	\N	162.85	paid	t	\N	\N	\N	2	2025-11-10 14:34:56.274687	2025-11-19 10:01:23.949787	f	162	MYR	paid	\N	2025-11-19 02:01:23.948923	\N	\N	\N	5
44	BX2025111005	Vertex Communication Sdn Bhd-quah-2511100709	Presentation Evertac's Data Center technology with the technical team	43	\N	54	paid	t	\N	\N	\N	2	2025-11-10 15:25:09.494689	2025-11-19 10:03:47.460573	f	55	MYR	paid	\N	2025-11-19 02:03:47.459822	\N	\N	\N	5
45	BX2025111006	Cekap Technical Services Sdn Bhd-quah-2511100718	Courtesy visit to the company to introduce our products	108	\N	15.8	paid	t	\N	\N	\N	2	2025-11-10 15:30:18.733933	2025-11-19 10:07:13.279634	f	138	MYR	paid	\N	2025-11-19 02:07:13.278978	\N	\N	\N	5
42	BX2025111003	YSC TECHNOLOGY ENGINEERING Sdn Bhd-quah-2511100651	Lunch with Mr. Lee	12	8	93.3	paid	t	\N	\N	\N	2	2025-11-10 14:56:51.365492	2025-11-19 10:01:51.130773	f	53	MYR	paid	\N	2025-11-19 02:01:51.130118	\N	\N	\N	5
38	BX2025110903	UCI Corporation co.,ltd-james.ni-2511090319	Paisith help to apply frequency from NBTC directly and meeting with NBTC to introduce our system.	127	\N	842.85	pending	t	\N	\N	\N	1	2025-11-09 11:04:19.114414	2025-11-09 13:47:17.113048	f	161	SGD	unpaid	\N	\N	\N	\N	\N	\N
41	BX2025111002	不关联（Unders）-quah-2511100629	Understand they are awarded the project and subsequently sub out to Radii.	\N	\N	96.75	draft	f	\N	\N	\N	2	2025-11-10 14:53:29.915261	2025-11-10 16:05:07.209135	t	\N	MYR	unpaid	\N	\N	\N	\N	\N	\N
43	BX2025111004	Supreme Landmobile & Wireless Corporation Sdn. Bhd. (SLW)-quah-2511100746	Meeting to discuss appointment as Evertac's direct agent planning	50	\N	29.8	paid	t	\N	\N	\N	2	2025-11-10 15:00:46.009846	2025-11-19 10:02:10.909815	f	62	MYR	paid	\N	2025-11-19 02:02:10.909031	\N	\N	\N	5
34	BX2025102301	不关联（Govern）-Patrick.ku-2510230213	Government office (MCMC), potential customer visit and Mooncake for Malaysia customers	\N	\N	681	paid	t	\N	\N	\N	4	2025-10-23 10:24:13.436328	2025-10-29 13:55:35.4217	f	\N	MYR	paid	\N	2025-10-29 05:55:35.420617	\N	\N	\N	5
32	BX2025101602	Engine-roy.lim-2510161433	Engineer & Marvex KLCC Exhibition Expenses.	\N	\N	453.76	paid	t	\N	\N	\N	3	2025-10-16 14:55:13.842387	2025-10-29 13:55:56.20989	f	\N	MYR	paid	\N	2025-10-29 05:55:56.209233	\N	\N	\N	5
47	BX2025111008	TM Technology Service Sdn Bhd -quah-2511100704	Lunch with Ms. Nurshaliana the project manager	65	\N	52.5	paid	t	\N	\N	\N	2	2025-11-10 15:56:04.019436	2025-11-19 10:07:34.427269	f	111	MYR	paid	\N	2025-11-19 02:07:34.426608	\N	\N	\N	5
46	BX2025111007	Exquisiteness Engineering Sdn Bhd-quah-2511100709	Courtesy visit the sub-cont to follow up the project status	120	12	56.5	paid	t	\N	\N	\N	2	2025-11-10 15:49:09.730993	2025-11-19 10:02:39.130719	f	151	MYR	paid	\N	2025-11-19 02:02:39.130092	\N	\N	\N	5
48	BX2025111009	Triple Access Sdn Bhd-quah-2511100809	Lunch together after meeting and presentation at Putrajaya Marriot Hotel to the user	42	\N	100.2	paid	t	\N	\N	\N	2	2025-11-10 16:02:09.161717	2025-11-19 10:07:56.56925	f	126	MYR	paid	\N	2025-11-19 02:07:56.568572	\N	\N	\N	5
35	BX2025110401	Tsingshan IMIP Site Visit		76	\N	1034.78	paid	t	\N	\N	\N	7	2025-11-04 16:10:35.308063	2025-11-10 17:29:14.372001	f	97	MYR	paid	\N	2025-11-10 09:29:14.370561	\N	\N	\N	5
53	BX2025111102	Thailand_NBTC meeting trip ( 4-6th Nov 2025 )	Thailand_NBTC meeting trip ( 4-6th Nov 2025 )	\N	\N	1551.87	pending	t	\N	\N	\N	2	2025-11-11 17:29:45.478862	2025-11-18 14:09:35.662217	f	\N	MYR	unpaid	\N	\N	\N	\N	\N	\N
54	BX2025111103	DayOne_NTP-ABCDEF site support trip (7-9th Nov 2025)	DayOne_NTP-ABCDEF site support trip (7-9th Nov 2025)	129	\N	625.11	pending	t	\N	\N	\N	2	2025-11-11 17:51:15.369414	2025-11-24 13:58:05.434365	f	163	MYR	unpaid	\N	\N	\N	\N	\N	\N
33	BX2025101701	不关联（Visit ）-james.ni-2510170410	Visit GDS NTP—F  operator and security mananger with Tech team and quah	\N	\N	90.655306	pending	t	\N	\N	\N	1	2025-10-17 12:19:10.028072	2025-11-20 19:39:41.048994	f	\N	SGD	unpaid	\N	\N	\N	\N	\N	\N
37	BX2025110902	Family-james.ni-2511091045	Family member of CRCC(China railway) leader are coming singapore for visit and reception	\N	\N	571.08	awaiting_payment	t	\N	\N	\N	1	2025-11-09 10:46:33.016394	2025-11-18 13:49:51.446844	f	\N	SGD	awaiting	\N	\N	\N	\N	\N	\N
36	BX2025110901	FMTCS SOLUTIONS PTE. LTD-james.ni-2511090223	F Block repeater repeater, dealer with Fu	28	12	80.288768	awaiting_payment	t	\N	\N	\N	1	2025-11-09 10:39:23.419142	2025-11-18 13:50:13.464077	f	33	SGD	awaiting	\N	\N	\N	\N	\N	\N
52	BX2025111101	Lunch -roy.lim-2511111150	Lunch with Trac Consult's team.	\N	\N	439.6	rejected	f	\N	\N	\N	3	2025-11-11 11:26:52.200026	2025-11-13 17:33:31.473401	f	\N	MYR	unpaid	\N	\N	\N	\N	\N	\N
\.


--
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
12	12	fix	\N	更新仪表盘行动记录展示布局	更新仪表盘行动记录展示布局	medium	minor	\N	ca07b0c8	pending	\N	\N	开发团队	2025-08-15 04:55:14.015391	2025-08-15 04:55:14.015392
13	13	fix	\N	修复客户查看灰色逻辑问题	修复客户查看灰色逻辑问题	medium	minor	\N	dd2d2d22	pending	\N	\N	开发团队	2025-08-15 05:40:57.719561	2025-08-15 05:40:57.719563
14	14	fix	\N	再次修复归属客户是灰色的问题	再次修复归属客户是灰色的问题	medium	minor	\N	5a105cbe	pending	\N	\N	开发团队	2025-08-15 07:29:14.086467	2025-08-15 07:29:14.086468
15	15	fix	\N	修复PDF文件的预效果效果	修复PDF文件的预效果效果	medium	minor	\N	d774260d	pending	\N	\N	开发团队	2025-08-15 10:33:11.784129	2025-08-15 10:33:11.78413
16	16	feature	\N	更新发票上传的功能	更新发票上传的功能	medium	minor	\N	ccbaf653	pending	\N	\N	开发团队	2025-08-15 16:15:34.378608	2025-08-15 16:15:34.378609
17	17	feature	\N	更新翻译功能	更新翻译功能	medium	minor	\N	dbf41057	pending	\N	\N	开发团队	2025-08-16 16:06:22.830178	2025-08-16 16:06:22.830179
18	18	fix	\N	修代理商无法查看行动记录问题	修代理商无法查看行动记录问题	medium	minor	\N	8463c335	pending	\N	\N	开发团队	2025-09-15 19:30:45.562212	2025-09-15 19:30:45.562213
19	19	fix	\N	更新研发模块	更新研发模块	medium	minor	\N	6add6935	pending	\N	\N	开发团队	2025-09-15 20:39:07.841899	2025-09-15 20:39:07.8419
20	20	feature	\N	升级研发产品编码和报销通知邮件功能	升级研发产品编码和报销通知邮件功能	medium	minor	\N	23428a9b	pending	\N	\N	开发团队	2025-09-22 03:06:27.209359	2025-09-22 03:06:27.209362
21	21	fix	\N	修复四级检查逻辑	修复四级检查逻辑	medium	minor	\N	605dd6c8	pending	\N	\N	开发团队	2025-10-01 15:00:14.643842	2025-10-01 15:00:14.643843
22	22	fix	\N	修复审批流程步骤获取逻辑Bug\n\n问题描述:\n- OVS系统管理员无法看到报销单BX2025091806的审批提醒\n- current_step字段存储了step_order值而非step_id\n- 	修复审批流程步骤获取逻辑Bug\n\n问题描述:\n- OVS系统管理员无法看到报销单BX2025091806的审批提醒\n- current_step字段存储了step_order值而非step_id\n- 导致get_current_step_info()查询失败返回None\n\n根本原因:\n代码在获取下一步骤时，使用ApprovalStep.query.filter_by(id=instance.current_step)\n查询数据库，当current_step=1(step_order)时，会查到其他流程(process_id=1)的步骤，\n造成跨流程步骤混淆。\n\n修复方案:\n- 修改process_approval()和process_approval_with_project_type()\n- 从快照数据直接获取step_order，避免数据库查询造成的跨流程混淆\n- 添加数据完整性预检查，及早发现current_step异常\n\n影响范围:\n- 所有审批类型(expense, project, quotation, pricing_order)\n\n数据修复:\n- 修复OVS上11个报销单审批实例的current_step值\n- 创建projects.created_by字段迁移(已存在字段,仅同步迁移历史)\n\n文件:\n- app/helpers/approval_helpers.py: Line 4210-4227 (预检查), Line 4339-4353 (修复)\n- migrations/versions/f288f78d8527_*.py: 同步迁移历史\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>	medium	minor	\N	b4f49cd9	pending	\N	\N	开发团队	2025-10-01 08:46:59.900708	2025-10-01 08:46:59.90071
23	23	fix	\N	修复云端项目详情页"创建人"字段不显示的问题\n\n## 问题\n- 云端PMA-SA项目详情页不显示"创建人"字段\n- 本地系统显示正常\n- 数据库已有created_by字段和数据\n\n## 根本原因\nv	修复云端项目详情页"创建人"字段不显示的问题\n\n## 问题\n- 云端PMA-SA项目详情页不显示"创建人"字段\n- 本地系统显示正常\n- 数据库已有created_by字段和数据\n\n## 根本原因\nview_project函数缺少creator关系预加载，导致延迟加载在云端环境失败\n\n## 修改内容\n1. app/views/project.py: 添加creator/owner/vendor_sales_manager关系预加载\n2. migrations: 添加created_by字段迁移文件\n\n## 数据库修复\n- OVS数据库: 手动执行SQL添加created_by字段并填充数据\n- 52个项目的created_by已用owner_id填充\n\n## 预期效果\n- 云端项目详情页显示"创建人"字段\n- 性能提升（减少延迟加载查询）\n- 与列表页加载方式保持一致\n\n🤖 Generated with Claude Code\nCo-Authored-By: Claude <noreply@anthropic.com>	medium	minor	\N	f255ff95	pending	\N	\N	开发团队	2025-10-01 09:22:33.616602	2025-10-01 09:22:33.616602
24	24	fix	\N	添加货币相关辅助函数到i18n模块\n\n- 新增get_default_currency()：根据当前语言返回默认货币\n- 新增get_currency_symbol()：获取货币符号\n- 支持CNY、	添加货币相关辅助函数到i18n模块\n\n- 新增get_default_currency()：根据当前语言返回默认货币\n- 新增get_currency_symbol()：获取货币符号\n- 支持CNY、USD、SGD等多种货币	medium	minor	\N	da9ac3f9	pending	\N	\N	开发团队	2025-10-01 13:06:57.135041	2025-10-01 13:06:57.135043
25	25	fix	\N	Auto commit at Wed Oct  1 21:50:22 +08 2025	Auto commit at Wed Oct  1 21:50:22 +08 2025	medium	minor	\N	432f87b0	pending	\N	\N	开发团队	2025-10-01 13:55:29.49445	2025-10-01 13:55:29.494452
26	26	fix	\N	修复审批提交项目授权的bug	修复审批提交项目授权的bug	medium	minor	\N	a9e882b4	pending	\N	\N	开发团队	2025-10-08 00:51:41.32742	2025-10-08 00:51:41.327421
27	27	fix	\N	修复修复仪表盘的展示和权问题	修复修复仪表盘的展示和权问题	medium	minor	\N	b0636182	pending	\N	\N	开发团队	2025-10-08 01:52:39.828757	2025-10-08 01:52:39.828759
28	28	fix	\N	修复删除项目的外建约束	修复删除项目的外建约束	medium	minor	\N	a2b49343	pending	\N	\N	开发团队	2025-10-09 01:05:21.981635	2025-10-09 01:05:21.981636
29	29	fix	\N	修复厂商负责人不能提交代理商项目授权的问题	修复厂商负责人不能提交代理商项目授权的问题	medium	minor	\N	970e5c26	pending	\N	\N	开发团队	2025-10-10 03:52:14.836092	2025-10-10 03:52:14.836093
30	30	fix	\N	修复账户管理无法进入问题	修复账户管理无法进入问题	medium	minor	\N	ee81e3a9	pending	\N	\N	开发团队	2025-10-10 05:04:48.052569	2025-10-10 05:04:48.052571
31	31	fix	\N	批价单问题和结算单问题	批价单问题和结算单问题	medium	minor	\N	8b62949d	pending	\N	\N	开发团队	2025-10-13 04:46:13.548863	2025-10-13 04:46:13.548864
32	32	fix	\N	修复字段的错误和页面说明	修复字段的错误和页面说明	medium	minor	\N	6fc29e2c	pending	\N	\N	开发团队	2025-10-17 14:40:54.55902	2025-10-17 14:40:54.559021
33	33	feature	\N	修负责人选择器功能	修负责人选择器功能	medium	minor	\N	aa054c50	pending	\N	\N	开发团队	2025-10-21 22:38:21.116044	2025-10-21 22:38:21.116047
34	34	fix	\N	更新翻译	更新翻译	medium	minor	\N	095ee6ec	pending	\N	\N	开发团队	2025-10-21 23:16:15.423559	2025-10-21 23:16:15.42356
35	35	fix	\N	更新归属规则不包括的业务类型	更新归属规则不包括的业务类型	medium	minor	\N	fc4ae8ce	pending	\N	\N	开发团队	2025-10-22 00:52:55.576676	2025-10-22 00:52:55.576677
36	36	fix	\N	修复报价单和报访问问题	修复报价单和报访问问题	medium	minor	\N	33b4a27a	pending	\N	\N	开发团队	2025-10-22 01:05:25.575195	2025-10-22 01:05:25.575197
37	37	fix	\N	更新归属关系不包括报销单业务	更新归属关系不包括报销单业务	medium	minor	\N	f3201425	pending	\N	\N	开发团队	2025-10-22 01:31:15.073366	2025-10-22 01:31:15.073367
38	38	fix	\N	添加关联客户的权限报错问题	添加关联客户的权限报错问题	medium	minor	\N	c512f82a	pending	\N	\N	开发团队	2025-10-22 02:01:56.244253	2025-10-22 02:01:56.244255
39	39	fix	\N	修复客户共享后可以都看所有文具的问题	修复客户共享后可以都看所有文具的问题	medium	