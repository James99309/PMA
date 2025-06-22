# 云端数据库备份信息 - pma_db_sp8d

- **备份时间**: 2025-06-22 18:56:58
- **源数据库**: Render PostgreSQL (Singapore)
- **数据库名**: pma_db_sp8d
- **数据库标识**: SP8D (原版本数据库)
- **备份文件**: pma_db_sp8d_backup_20250622_185655.sql
- **文件大小**: 2689.48 KB
- **备份格式**: SQL (plain text)
- **备份选项**: --clean --no-owner --no-privileges

## 数据库连接信息

- **主机**: dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com
- **用户**: pma_db_sp8d_user
- **数据库**: pma_db_sp8d

## 备份命令

```bash
pg_dump --verbose --clean --no-owner --no-privileges --format=plain --file cloud_db_backups/pma_db_sp8d_backup_20250622_185655.sql postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d
```

## 备份日志

```
pg_dump: 最后的内置 OID 是 16383
pg_dump: 读扩展
pg_dump: 识别扩展成员
pg_dump: 读取模式
pg_dump: 读取用户定义表
pg_dump: 读取用户定义函数
pg_dump: 读取用户定义类型
pg_dump: 读取过程语言
pg_dump: 读取用户定义聚集函数
pg_dump: 读取用户定义操作符
pg_dump: 读取用户定义的访问方法
pg_dump: 读取用户定义操作符集
pg_dump: 读取用户定义操作符
pg_dump: 读取用户定义的文本搜索解析器
pg_dump: 读取用户定义的文本搜索模板
pg_dump: 读取用户定义的文本搜索字典
pg_dump: 读取用户定义的文本搜索配置
pg_dump: 读取用户定义外部数据封装器
pg_dump: 读取用户定义的外部服务器
pg_dump: 正在读取缺省权限
pg_dump: 读取用户定义的校对函数
pg_dump: 读取用户定义的字符集转换
pg_dump: 读取类型转换
pg_dump: 读取转换
pg_dump: 读取表继承信息
pg_dump: 读取事件触发器
pg_dump: 查找扩展表
pg_dump: 正在查找关系继承
pg_dump: 正在读取感兴趣表的列信息
pg_dump: finding table default expressions
pg_dump: finding table check constraints
pg_dump: 在子表里标记继承字段
pg_dump: reading partitioning data
pg_dump: 读取索引
pg_dump: 在分区表中标记索引
pg_dump: 读取扩展统计信息
pg_dump: 读取约束
pg_dump: 读取触发器
pg_dump: 读取重写规则
pg_dump: 读取策略
pg_dump: reading row-level security policies
pg_dump: 读取发布
pg_dump: reading publication membership of tables
pg_dump: reading publication membership of schemas
pg_dump: 读取订阅
pg_dump: 正在读取大对象
pg_dump: 读取从属数据
pg_dump: 正在保存encoding = UTF8
pg_dump: 正在保存standard_conforming_strings = on
pg_dump: 正在保存search_path = 
pg_dump: 删除 FK CONSTRAINT user_event_subscriptions user_event_subscriptions_user_id_fkey
pg_dump: 删除 FK CONSTRAINT user_event_subscriptions user_event_subscriptions_target_user_id_fkey
pg_dump: 删除 FK CONSTRAINT user_event_subscriptions user_event_subscriptions_event_id_fkey
pg_dump: 删除 FK CONSTRAINT upgrade_logs upgrade_logs_version_id_fkey
pg_dump: 删除 FK CONSTRAINT upgrade_logs upgrade_logs_operator_id_fkey
pg_dump: 删除 FK CONSTRAINT system_metrics system_metrics_version_id_fkey
pg_dump: 删除 FK CONSTRAINT solution_manager_email_settings solution_manager_email_settings_user_id_fkey
pg_dump: 删除 FK CONSTRAINT settlements settlements_created_by_id_fkey
pg_dump: 删除 FK CONSTRAINT settlements settlements_company_id_fkey
pg_dump: 删除 FK CONSTRAINT settlements settlements_approved_by_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_orders settlement_orders_quotation_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_orders settlement_orders_project_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_orders settlement_orders_pricing_order_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_orders settlement_orders_distributor_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_orders settlement_orders_dealer_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_orders settlement_orders_created_by_fkey
pg_dump: 删除 FK CONSTRAINT settlement_orders settlement_orders_approved_by_fkey
pg_dump: 删除 FK CONSTRAINT settlement_order_details settlement_order_details_settlement_order_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_order_details settlement_order_details_settlement_company_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_order_details settlement_order_details_pricing_order_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_order_details settlement_order_details_pricing_detail_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_details settlement_details_settlement_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_details settlement_details_product_id_fkey
pg_dump: 删除 FK CONSTRAINT settlement_details settlement_details_inventory_id_fkey
pg_dump: 删除 FK CONSTRAINT quotations quotations_project_id_fkey
pg_dump: 删除 FK CONSTRAINT quotations quotations_owner_id_fkey
pg_dump: 删除 FK CONSTRAINT quotations quotations_locked_by_fkey
pg_dump: 删除 FK CONSTRAINT quotations quotations_contact_id_fkey
pg_dump: 删除 FK CONSTRAINT quotations quotations_confirmed_by_fkey
pg_dump: 删除 FK CONSTRAINT quotation_details quotation_details_quotation_id_fkey
pg_dump: 删除 FK CONSTRAINT purchase_orders purchase_orders_created_by_id_fkey
pg_dump: 删除 FK CONSTRAINT purchase_orders purchase_orders_company_id_fkey
pg_dump: 删除 FK CONSTRAINT purchase_orders purchase_orders_approved_by_id_fkey
pg_dump: 删除 FK CONSTRAINT purchase_order_details purchase_order_details_product_id_fkey
pg_dump: 删除 FK CONSTRAINT purchase_order_details purchase_order_details_order_id_fkey
pg_dump: 删除 FK CONSTRAINT projects projects_vendor_sales_manager_id_fkey
pg_dump: 删除 FK CONSTRAINT projects projects_owner_id_fkey
pg_dump: 删除 FK CONSTRAINT projects projects_locked_by_fkey
pg_dump: 删除 FK CONSTRAINT project_total_scores project_total_scores_project_id_fkey
pg_dump: 删除 FK CONSTRAINT project_stage_history project_stage_history_project_id_fkey
pg_dump: 删除 FK CONSTRAINT project_scoring_records project_scoring_records_project_id_fkey
pg_dump: 删除 FK CONSTRAINT project_scoring_records project_scoring_records_awarded_by_fkey
pg_dump: 删除 FK CONSTRAINT project_rating_records project_rating_records_user_id_fkey
pg_dump: 删除 FK CONSTRAINT project_rating_records project_rating_records_project_id_fkey
pg_dump: 删除 FK CONSTRAINT project_members project_members_user_id_fkey
pg_dump: 删除 FK CONSTRAINT project_members project_members_project_id_fkey
pg_dump: 删除 FK CONSTRAINT products products_owner_id_fkey
pg_dump: 删除 FK CONSTRAINT product_subcategories product_subcategories_category_id_fkey
pg_dump: 删除 FK CONSTRAINT product_codes product_codes_subcategory_id_fkey
pg_dump: 删除 FK CONSTRAINT product_codes product_codes_product_id_fkey
pg_dump: 删除 FK CONSTRAINT product_codes product_codes_created_by_fkey
pg_dump: 删除 FK CONSTRAINT product_codes product_codes_category_id_fkey
pg_dump: 删除 FK CONSTRAINT product_code_fields product_code_fields_subcategory_id_fkey
pg_dump: 删除 FK CONSTRAINT product_code_field_values product_code_field_values_product_code_id_fkey
pg_dump: 删除 FK CONSTRAINT product_code_field_values product_code_field_values_option_id_fkey
pg_dump: 删除 FK CONSTRAINT product_code_field_values product_code_field_values_field_id_fkey
pg_dump: 删除 FK CONSTRAINT product_code_field_options product_code_field_options_field_id_fkey
pg_dump: 删除 FK CONSTRAINT pricing_orders pricing_orders_quotation_id_fkey
pg_dump: 删除 FK CONSTRAINT pricing_orders pricing_orders_project_id_fkey
pg_dump: 删除 FK CONSTRAINT pricing_orders pricing_orders_distributor_id_fkey
pg_dump: 删除 FK CONSTRAINT pricing_orders pricing_orders_dealer_id_fkey
pg_dump: 删除 FK CONSTRAINT pricing_orders pricing_orders_created_by_fkey
pg_dump: 删除 FK CONSTRAINT pricing_orders pricing_orders_approved_by_fkey
pg_dump: 删除 FK CONSTRAINT pricing_order_details pricing_order_details_pricing_order_id_fkey
pg_dump: 删除 FK CONSTRAINT pricing_order_approval_records pricing_order_approval_records_pricing_order_id_fkey
pg_dump: 删除 FK CONSTRAINT pricing_order_approval_records pricing_order_approval_records_approver_id_fkey
pg_dump: 删除 FK CONSTRAINT permissions permissions_user_id_fkey
pg_dump: 删除 FK CONSTRAINT inventory_transactions inventory_transactions_inventory_id_fkey
pg_dump: 删除 FK CONSTRAINT inventory_transactions inventory_transactions_created_by_id_fkey
pg_dump: 删除 FK CONSTRAINT inventory inventory_product_id_fkey
pg_dump: 删除 FK CONSTRAINT inventory inventory_created_by_id_fkey
pg_dump: 删除 FK CONSTRAINT inventory inventory_company_id_fkey
pg_dump: 删除 FK CONSTRAINT project_rating_records fk_project_rating_user_id
pg_dump: 删除 FK CONSTRAINT project_rating_records fk_project_rating_project_id
pg_dump: 删除 FK CONSTRAINT feature_changes feature_changes_version_id_fkey
pg_dump: 删除 FK CONSTRAINT feature_changes feature_changes_developer_id_fkey
pg_dump: 删除 FK CONSTRAINT dev_products dev_products_subcategory_id_fkey
pg_dump: 删除 FK CONSTRAINT dev_products dev_products_region_id_fkey
pg_dump: 删除 FK CONSTRAINT dev_products dev_products_owner_id_fkey
pg_dump: 删除 FK CONSTRAINT dev_products dev_products_created_by_fkey
pg_dump: 删除 FK CONSTRAINT dev_products dev_products_category_id_fkey
pg_dump: 删除 FK CONSTRAINT dev_product_specs dev_product_specs_dev_product_id_fkey
pg_dump: 删除 FK CONSTRAINT contacts contacts_owner_id_fkey
pg_dump: 删除 FK CONSTRAINT contacts contacts_company_id_fkey
pg_dump: 删除 FK CONSTRAINT companies companies_owner_id_fkey
pg_dump: 删除 FK CONSTRAINT change_logs change_logs_user_id_fkey
pg_dump: 删除 FK CONSTRAINT approval_step approval_step_process_id_fkey
pg_dump: 删除 FK CONSTRAINT approval_step approval_step_approver_user_id_fkey
pg_dump: 删除 FK CONSTRAINT approval_record approval_record_step_id_fkey
pg_dump: 删除 FK CONSTRAINT approval_record approval_record_instance_id_fkey
pg_dump: 删除 FK CONSTRAINT approval_record approval_record_approver_id_fkey
pg_dump: 删除 FK CONSTRAINT approval_process_template approval_process_template_created_by_fkey
pg_dump: 删除 FK CONSTRAINT approval_instance approval_instance_process_id_fkey
pg_dump: 删除 FK CONSTRAINT approval_instance approval_instance_created_by_fkey
pg_dump: 删除 FK CONSTRAINT affiliations affiliations_viewer_id_fkey
pg_dump: 删除 FK CONSTRAINT affiliations affiliations_owner_id_fkey
pg_dump: 删除 FK CONSTRAINT actions actions_project_id_fkey
pg_dump: 删除 FK CONSTRAINT actions actions_owner_id_fkey
pg_dump: 删除 FK CONSTRAINT actions actions_contact_id_fkey
pg_dump: 删除 FK CONSTRAINT actions actions_company_id_fkey
pg_dump: 删除 FK CONSTRAINT action_reply action_reply_parent_reply_id_fkey
pg_dump: 删除 FK CONSTRAINT action_reply action_reply_owner_id_fkey
pg_dump: 删除 FK CONSTRAINT action_reply action_reply_action_id_fkey
pg_dump: 删除 INDEX ix_system_settings_key
pg_dump: 删除 INDEX ix_projects_project_name
pg_dump: 删除 INDEX ix_projects_authorization_code
pg_dump: 删除 INDEX ix_project_stage_history_project_id
pg_dump: 删除 CONSTRAINT version_records version_records_version_number_key
pg_dump: 删除 CONSTRAINT version_records version_records_pkey
pg_dump: 删除 CONSTRAINT users users_wechat_openid_key
pg_dump: 删除 CONSTRAINT users users_username_key
pg_dump: 删除 CONSTRAINT users users_pkey
pg_dump: 删除 CONSTRAINT users users_email_key
pg_dump: 删除 CONSTRAINT user_event_subscriptions user_event_subscriptions_pkey
pg_dump: 删除 CONSTRAINT user_event_subscriptions uq_user_target_event
pg_dump: 删除 CONSTRAINT product_subcategories uq_subcategory_code_letter
pg_dump: 删除 CONSTRAINT solution_manager_email_settings uq_solution_manager_email_user
pg_dump: 删除 CONSTRAINT project_scoring_records uq_scoring_record_with_user
pg_dump: 删除 CONSTRAINT project_scoring_records uq_scoring_record
pg_dump: 删除 CONSTRAINT project_scoring_config uq_scoring_config
pg_dump: 删除 CONSTRAINT project_rating_records uq_project_user_rating
pg_dump: 删除 CONSTRAINT upgrade_logs upgrade_logs_pkey
pg_dump: 删除 CONSTRAINT inventory unique_company_product_inventory
pg_dump: 删除 CONSTRAINT permissions uix_user_module
pg_dump: 删除 CONSTRAINT dictionaries uix_type_key
pg_dump: 删除 CONSTRAINT role_permissions uix_role_module
pg_dump: 删除 CONSTRAINT affiliations uix_owner_viewer
pg_dump: 删除 CONSTRAINT system_settings system_settings_pkey
pg_dump: 删除 CONSTRAINT system_metrics system_metrics_pkey
pg_dump: 删除 CONSTRAINT solution_manager_email_settings solution_manager_email_settings_pkey
pg_dump: 删除 CONSTRAINT settlements settlements_settlement_number_key
pg_dump: 删除 CONSTRAINT settlements settlements_pkey
pg_dump: 删除 CONSTRAINT settlement_orders settlement_orders_pkey
pg_dump: 删除 CONSTRAINT settlement_orders settlement_orders_order_number_key
pg_dump: 删除 CONSTRAINT settlement_order_details settlement_order_details_pkey
pg_dump: 删除 CONSTRAINT settlement_details settlement_details_pkey
pg_dump: 删除 CONSTRAINT role_permissions role_permissions_pkey
pg_dump: 删除 CONSTRAINT quotations quotations_quotation_number_key
pg_dump: 删除 CONSTRAINT quotations quotations_pkey
pg_dump: 删除 CONSTRAINT quotation_details quotation_details_pkey
pg_dump: 删除 CONSTRAINT purchase_orders purchase_orders_pkey
pg_dump: 删除 CONSTRAINT purchase_orders purchase_orders_order_number_key
pg_dump: 删除 CONSTRAINT purchase_order_details purchase_order_details_pkey
pg_dump: 删除 CONSTRAINT projects projects_pkey
pg_dump: 删除 CONSTRAINT project_total_scores project_total_scores_project_id_key
pg_dump: 删除 CONSTRAINT project_total_scores project_total_scores_pkey
pg_dump: 删除 CONSTRAINT project_stage_history project_stage_history_pkey
pg_dump: 删除 CONSTRAINT project_scoring_records project_scoring_records_pkey
pg_dump: 删除 CONSTRAINT project_scoring_config project_scoring_config_pkey
pg_dump: 删除 CONSTRAINT project_rating_records project_rating_records_pkey
pg_dump: 删除 CONSTRAINT project_members project_members_pkey
pg_dump: 删除 CONSTRAINT products products_product_mn_key
pg_dump: 删除 CONSTRAINT products products_pkey
pg_dump: 删除 CONSTRAINT product_subcategories product_subcategories_pkey
pg_dump: 删除 CONSTRAINT product_regions product_regions_pkey
pg_dump: 删除 CONSTRAINT product_codes product_codes_pkey
pg_dump: 删除 CONSTRAINT product_codes product_codes_full_code_key
pg_dump: 删除 CONSTRAINT product_code_fields product_code_fields_pkey
pg_dump: 删除 CONSTRAINT product_code_field_values product_code_field_values_pkey
pg_dump: 删除 CONSTRAINT product_code_field_options product_code_field_options_pkey
pg_dump: 删除 CONSTRAINT product_categories product_categories_pkey
pg_dump: 删除 CONSTRAINT product_categories product_categories_code_letter_key
pg_dump: 删除 CONSTRAINT pricing_orders pricing_orders_pkey
pg_dump: 删除 CONSTRAINT pricing_orders pricing_orders_order_number_key
pg_dump: 删除 CONSTRAINT pricing_order_details pricing_order_details_pkey
pg_dump: 删除 CONSTRAINT pricing_order_approval_records pricing_order_approval_records_pkey
pg_dump: 删除 CONSTRAINT permissions permissions_pkey
pg_dump: 删除 CONSTRAINT inventory_transactions inventory_transactions_pkey
pg_dump: 删除 CONSTRAINT inventory inventory_pkey
pg_dump: 删除 CONSTRAINT feature_changes feature_changes_pkey
pg_dump: 删除 CONSTRAINT event_registry event_registry_pkey
pg_dump: 删除 CONSTRAINT event_registry event_registry_event_key_key
pg_dump: 删除 CONSTRAINT dictionaries dictionaries_pkey
pg_dump: 删除 CONSTRAINT dev_products dev_products_pkey
pg_dump: 删除 CONSTRAINT dev_product_specs dev_product_specs_pkey
pg_dump: 删除 CONSTRAINT contacts contacts_pkey
pg_dump: 删除 CONSTRAINT companies companies_pkey
pg_dump: 删除 CONSTRAINT companies companies_company_code_key
pg_dump: 删除 CONSTRAINT change_logs change_logs_pkey
pg_dump: 删除 CONSTRAINT approval_step approval_step_pkey
pg_dump: 删除 CONSTRAINT approval_record approval_record_pkey
pg_dump: 删除 CONSTRAINT approval_process_template approval_process_template_pkey
pg_dump: 删除 CONSTRAINT approval_instance approval_instance_pkey
pg_dump: 删除 CONSTRAINT alembic_version alembic_version_pkc
pg_dump: 删除 CONSTRAINT affiliations affiliations_pkey
pg_dump: 删除 CONSTRAINT actions actions_pkey
pg_dump: 删除 CONSTRAINT action_reply action_reply_pkey
pg_dump: 删除 DEFAULT version_records id
pg_dump: 删除 DEFAULT users id
pg_dump: 删除 DEFAULT user_event_subscriptions id
pg_dump: 删除 DEFAULT upgrade_logs id
pg_dump: 删除 DEFAULT system_settings id
pg_dump: 删除 DEFAULT system_metrics id
pg_dump: 删除 DEFAULT solution_manager_email_settings id
pg_dump: 删除 DEFAULT settlements id
pg_dump: 删除 DEFAULT settlement_orders id
pg_dump: 删除 DEFAULT settlement_order_details id
pg_dump: 删除 DEFAULT settlement_details id
pg_dump: 删除 DEFAULT role_permissions id
pg_dump: 删除 DEFAULT quotations id
pg_dump: 删除 DEFAULT quotation_details id
pg_dump: 删除 DEFAULT purchase_orders id
pg_dump: 删除 DEFAULT purchase_order_details id
pg_dump: 删除 DEFAULT projects id
pg_dump: 删除 DEFAULT project_total_scores id
pg_dump: 删除 DEFAULT project_stage_history id
pg_dump: 删除 DEFAULT project_scoring_records id
pg_dump: 删除 DEFAULT project_scoring_config id
pg_dump: 删除 DEFAULT project_rating_records id
pg_dump: 删除 DEFAULT project_members id
pg_dump: 删除 DEFAULT products id
pg_dump: 删除 DEFAULT product_subcategories id
pg_dump: 删除 DEFAULT product_regions id
pg_dump: 删除 DEFAULT product_codes id
pg_dump: 删除 DEFAULT product_code_fields id
pg_dump: 删除 DEFAULT product_code_field_values id
pg_dump: 删除 DEFAULT product_code_field_options id
pg_dump: 删除 DEFAULT product_categories id
pg_dump: 删除 DEFAULT pricing_orders id
pg_dump: 删除 DEFAULT pricing_order_details id
pg_dump: 删除 DEFAULT pricing_order_approval_records id
pg_dump: 删除 DEFAULT permissions id
pg_dump: 删除 DEFAULT inventory_transactions id
pg_dump: 删除 DEFAULT inventory id
pg_dump: 删除 DEFAULT feature_changes id
pg_dump: 删除 DEFAULT event_registry id
pg_dump: 删除 DEFAULT dictionaries id
pg_dump: 删除 DEFAULT dev_products id
pg_dump: 删除 DEFAULT dev_product_specs id
pg_dump: 删除 DEFAULT contacts id
pg_dump: 删除 DEFAULT companies id
pg_dump: 删除 DEFAULT change_logs id
pg_dump: 删除 DEFAULT approval_step id
pg_dump: 删除 DEFAULT approval_record id
pg_dump: 删除 DEFAULT approval_process_template id
pg_dump: 删除 DEFAULT approval_instance id
pg_dump: 删除 DEFAULT affiliations id
pg_dump: 删除 DEFAULT actions id
pg_dump: 删除 DEFAULT action_reply id
pg_dump: 删除 SEQUENCE version_records_id_seq
pg_dump: 删除 TABLE version_records
pg_dump: 删除 SEQUENCE users_id_seq
pg_dump: 删除 TABLE users
pg_dump: 删除 SEQUENCE user_event_subscriptions_id_seq
pg_dump: 删除 TABLE user_event_subscriptions
pg_dump: 删除 SEQUENCE upgrade_logs_id_seq
pg_dump: 删除 TABLE upgrade_logs
pg_dump: 删除 SEQUENCE system_settings_id_seq
pg_dump: 删除 TABLE system_settings
pg_dump: 删除 SEQUENCE system_metrics_id_seq
pg_dump: 删除 TABLE system_metrics
pg_dump: 删除 SEQUENCE solution_manager_email_settings_id_seq
pg_dump: 删除 TABLE solution_manager_email_settings
pg_dump: 删除 SEQUENCE settlements_id_seq
pg_dump: 删除 TABLE settlements
pg_dump: 删除 SEQUENCE settlement_orders_id_seq
pg_dump: 删除 TABLE settlement_orders
pg_dump: 删除 SEQUENCE settlement_order_details_id_seq
pg_dump: 删除 TABLE settlement_order_details
pg_dump: 删除 SEQUENCE settlement_details_id_seq
pg_dump: 删除 TABLE settlement_details
pg_dump: 删除 SEQUENCE role_permissions_id_seq
pg_dump: 删除 TABLE role_permissions
pg_dump: 删除 SEQUENCE quotations_id_seq
pg_dump: 删除 TABLE quotations
pg_dump: 删除 SEQUENCE quotation_details_id_seq
pg_dump: 删除 TABLE quotation_details
pg_dump: 删除 SEQUENCE purchase_orders_id_seq
pg_dump: 删除 TABLE purchase_orders
pg_dump: 删除 SEQUENCE purchase_order_details_id_seq
pg_dump: 删除 TABLE purchase_order_details
pg_dump: 删除 SEQUENCE projects_id_seq
pg_dump: 删除 TABLE projects
pg_dump: 删除 SEQUENCE project_total_scores_id_seq
pg_dump: 删除 TABLE project_total_scores
pg_dump: 删除 SEQUENCE project_stage_history_id_seq
pg_dump: 删除 TABLE project_stage_history
pg_dump: 删除 SEQUENCE project_scoring_records_id_seq
pg_dump: 删除 TABLE project_scoring_records
pg_dump: 删除 SEQUENCE project_scoring_config_id_seq
pg_dump: 删除 TABLE project_scoring_config
pg_dump: 删除 SEQUENCE project_rating_records_id_seq
pg_dump: 删除 TABLE project_rating_records
pg_dump: 删除 SEQUENCE project_members_id_seq
pg_dump: 删除 TABLE project_members
pg_dump: 删除 SEQUENCE products_id_seq
pg_dump: 删除 TABLE products
pg_dump: 删除 SEQUENCE product_subcategories_id_seq
pg_dump: 删除 TABLE product_subcategories
pg_dump: 删除 SEQUENCE product_regions_id_seq
pg_dump: 删除 TABLE product_regions
pg_dump: 删除 SEQUENCE product_codes_id_seq
pg_dump: 删除 TABLE product_codes
pg_dump: 删除 SEQUENCE product_code_fields_id_seq
pg_dump: 删除 TABLE product_code_fields
pg_dump: 删除 SEQUENCE product_code_field_values_id_seq
pg_dump: 删除 TABLE product_code_field_values
pg_dump: 删除 SEQUENCE product_code_field_options_id_seq
pg_dump: 删除 TABLE product_code_field_options
pg_dump: 删除 SEQUENCE product_categories_id_seq
pg_dump: 删除 TABLE product_categories
pg_dump: 删除 SEQUENCE pricing_orders_id_seq
pg_dump: 删除 TABLE pricing_orders
pg_dump: 删除 SEQUENCE pricing_order_details_id_seq
pg_dump: 删除 TABLE pricing_order_details
pg_dump: 删除 SEQUENCE pricing_order_approval_records_id_seq
pg_dump: 删除 TABLE pricing_order_approval_records
pg_dump: 删除 SEQUENCE permissions_id_seq
pg_dump: 删除 TABLE permissions
pg_dump: 删除 SEQUENCE inventory_transactions_id_seq
pg_dump: 删除 TABLE inventory_transactions
pg_dump: 删除 SEQUENCE inventory_id_seq
pg_dump: 删除 TABLE inventory
pg_dump: 删除 SEQUENCE feature_changes_id_seq
pg_dump: 删除 TABLE feature_changes
pg_dump: 删除 SEQUENCE event_registry_id_seq
pg_dump: 删除 TABLE event_registry
pg_dump: 删除 SEQUENCE dictionaries_id_seq
pg_dump: 删除 TABLE dictionaries
pg_dump: 删除 SEQUENCE dev_products_id_seq
pg_dump: 删除 TABLE dev_products
pg_dump: 删除 SEQUENCE dev_product_specs_id_seq
pg_dump: 删除 TABLE dev_product_specs
pg_dump: 删除 SEQUENCE contacts_id_seq
pg_dump: 删除 TABLE contacts
pg_dump: 删除 SEQUENCE companies_id_seq
pg_dump: 删除 TABLE companies
pg_dump: 删除 SEQUENCE change_logs_id_seq
pg_dump: 删除 TABLE change_logs
pg_dump: 删除 SEQUENCE approval_step_id_seq
pg_dump: 删除 TABLE approval_step
pg_dump: 删除 SEQUENCE approval_record_id_seq
pg_dump: 删除 TABLE approval_record
pg_dump: 删除 SEQUENCE approval_process_template_id_seq
pg_dump: 删除 TABLE approval_process_template
pg_dump: 删除 SEQUENCE approval_instance_id_seq
pg_dump: 删除 TABLE approval_instance
pg_dump: 删除 TABLE alembic_version
pg_dump: 删除 SEQUENCE affiliations_id_seq
pg_dump: 删除 TABLE affiliations
pg_dump: 删除 SEQUENCE actions_id_seq
pg_dump: 删除 TABLE actions
pg_dump: 删除 SEQUENCE action_reply_id_seq
pg_dump: 删除 TABLE action_reply
pg_dump: 删除 TYPE settlementorderstatus
pg_dump: 删除 TYPE pricingorderstatus
pg_dump: 删除 TYPE pricingorderapprovalflowtype
pg_dump: 删除 TYPE approvalstatus
pg_dump: 删除 TYPE approvalinstancestatus
pg_dump: 删除 TYPE approvalaction
pg_dump: 删除 TYPE approval_status
pg_dump: 删除 TYPE approval_action
pg_dump: 删除 SCHEMA public
pg_dump: 创建SCHEMA "public"
pg_dump: 创建TYPE "public.approval_action"
pg_dump: 创建TYPE "public.approval_status"
pg_dump: 创建TYPE "public.approvalaction"
pg_dump: 创建TYPE "public.approvalinstancestatus"
pg_dump: 创建TYPE "public.approvalstatus"
pg_dump: 创建TYPE "public.pricingorderapprovalflowtype"
pg_dump: 创建TYPE "public.pricingorderstatus"
pg_dump: 创建TYPE "public.settlementorderstatus"
pg_dump: 创建TABLE "public.action_reply"
pg_dump: 创建SEQUENCE "public.action_reply_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.action_reply_id_seq"
pg_dump: 创建TABLE "public.actions"
pg_dump: 创建SEQUENCE "public.actions_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.actions_id_seq"
pg_dump: 创建TABLE "public.affiliations"
pg_dump: 创建SEQUENCE "public.affiliations_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.affiliations_id_seq"
pg_dump: 创建TABLE "public.alembic_version"
pg_dump: 创建TABLE "public.approval_instance"
pg_dump: 创建COMMENT "public.COLUMN approval_instance.process_id"
pg_dump: 创建COMMENT "public.COLUMN approval_instance.object_id"
pg_dump: 创建COMMENT "public.COLUMN approval_instance.object_type"
pg_dump: 创建COMMENT "public.COLUMN approval_instance.current_step"
pg_dump: 创建COMMENT "public.COLUMN approval_instance.status"
pg_dump: 创建COMMENT "public.COLUMN approval_instance.started_at"
pg_dump: 创建COMMENT "public.COLUMN approval_instance.ended_at"
pg_dump: 创建COMMENT "public.COLUMN approval_instance.created_by"
pg_dump: 创建COMMENT "public.COLUMN approval_instance.template_snapshot"
pg_dump: 创建COMMENT "public.COLUMN approval_instance.template_version"
pg_dump: 创建SEQUENCE "public.approval_instance_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.approval_instance_id_seq"
pg_dump: 创建TABLE "public.approval_process_template"
pg_dump: 创建COMMENT "public.COLUMN approval_process_template.name"
pg_dump: 创建COMMENT "public.COLUMN approval_process_template.object_type"
pg_dump: 创建COMMENT "public.COLUMN approval_process_template.is_active"
pg_dump: 创建COMMENT "public.COLUMN approval_process_template.created_by"
pg_dump: 创建COMMENT "public.COLUMN approval_process_template.created_at"
pg_dump: 创建COMMENT "public.COLUMN approval_process_template.required_fields"
pg_dump: 创建COMMENT "public.COLUMN approval_process_template.lock_object_on_start"
pg_dump: 创建COMMENT "public.COLUMN approval_process_template.lock_reason"
pg_dump: 创建SEQUENCE "public.approval_process_template_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.approval_process_template_id_seq"
pg_dump: 创建TABLE "public.approval_record"
pg_dump: 创建COMMENT "public.COLUMN approval_record.instance_id"
pg_dump: 创建COMMENT "public.COLUMN approval_record.step_id"
pg_dump: 创建COMMENT "public.COLUMN approval_record.approver_id"
pg_dump: 创建COMMENT "public.COLUMN approval_record.action"
pg_dump: 创建COMMENT "public.COLUMN approval_record.comment"
pg_dump: 创建COMMENT "public.COLUMN approval_record."timestamp""
pg_dump: 创建SEQUENCE "public.approval_record_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.approval_record_id_seq"
pg_dump: 创建TABLE "public.approval_step"
pg_dump: 创建COMMENT "public.COLUMN approval_step.process_id"
pg_dump: 创建COMMENT "public.COLUMN approval_step.step_order"
pg_dump: 创建COMMENT "public.COLUMN approval_step.approver_user_id"
pg_dump: 创建COMMENT "public.COLUMN approval_step.step_name"
pg_dump: 创建COMMENT "public.COLUMN approval_step.send_email"
pg_dump: 创建COMMENT "public.COLUMN approval_step.action_type"
pg_dump: 创建COMMENT "public.COLUMN approval_step.action_params"
pg_dump: 创建COMMENT "public.COLUMN approval_step.editable_fields"
pg_dump: 创建COMMENT "public.COLUMN approval_step.cc_users"
pg_dump: 创建COMMENT "public.COLUMN approval_step.cc_enabled"
pg_dump: 创建SEQUENCE "public.approval_step_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.approval_step_id_seq"
pg_dump: 创建TABLE "public.change_logs"
pg_dump: 创建SEQUENCE "public.change_logs_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.change_logs_id_seq"
pg_dump: 创建TABLE "public.companies"
pg_dump: 创建SEQUENCE "public.companies_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.companies_id_seq"
pg_dump: 创建TABLE "public.contacts"
pg_dump: 创建SEQUENCE "public.contacts_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.contacts_id_seq"
pg_dump: 创建TABLE "public.dev_product_specs"
pg_dump: 创建SEQUENCE "public.dev_product_specs_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.dev_product_specs_id_seq"
pg_dump: 创建TABLE "public.dev_products"
pg_dump: 创建SEQUENCE "public.dev_products_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.dev_products_id_seq"
pg_dump: 创建TABLE "public.dictionaries"
pg_dump: 创建SEQUENCE "public.dictionaries_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.dictionaries_id_seq"
pg_dump: 创建TABLE "public.event_registry"
pg_dump: 创建COMMENT "public.COLUMN event_registry.event_key"
pg_dump: 创建COMMENT "public.COLUMN event_registry.label_zh"
pg_dump: 创建COMMENT "public.COLUMN event_registry.label_en"
pg_dump: 创建COMMENT "public.COLUMN event_registry.default_enabled"
pg_dump: 创建COMMENT "public.COLUMN event_registry.enabled"
pg_dump: 创建SEQUENCE "public.event_registry_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.event_registry_id_seq"
pg_dump: 创建TABLE "public.feature_changes"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.version_id"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.change_type"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.module_name"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.title"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.description"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.priority"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.impact_level"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.affected_files"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.git_commits"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.test_status"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.test_notes"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.developer_id"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.developer_name"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.created_at"
pg_dump: 创建COMMENT "public.COLUMN feature_changes.completed_at"
pg_dump: 创建SEQUENCE "public.feature_changes_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.feature_changes_id_seq"
pg_dump: 创建TABLE "public.inventory"
pg_dump: 创建SEQUENCE "public.inventory_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.inventory_id_seq"
pg_dump: 创建TABLE "public.inventory_transactions"
pg_dump: 创建SEQUENCE "public.inventory_transactions_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.inventory_transactions_id_seq"
pg_dump: 创建TABLE "public.permissions"
pg_dump: 创建SEQUENCE "public.permissions_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.permissions_id_seq"
pg_dump: 创建TABLE "public.pricing_order_approval_records"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_approval_records.pricing_order_id"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_approval_records.step_order"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_approval_records.step_name"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_approval_records.approver_role"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_approval_records.approver_id"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_approval_records.action"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_approval_records.comment"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_approval_records.approved_at"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_approval_records.is_fast_approval"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_approval_records.fast_approval_reason"
pg_dump: 创建SEQUENCE "public.pricing_order_approval_records_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.pricing_order_approval_records_id_seq"
pg_dump: 创建TABLE "public.pricing_order_details"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.pricing_order_id"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.product_name"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.product_model"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.product_desc"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.brand"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.unit"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.product_mn"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.market_price"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.unit_price"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.quantity"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.discount_rate"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.total_price"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.source_type"
pg_dump: 创建COMMENT "public.COLUMN pricing_order_details.source_quotation_detail_id"
pg_dump: 创建SEQUENCE "public.pricing_order_details_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.pricing_order_details_id_seq"
pg_dump: 创建TABLE "public.pricing_orders"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.order_number"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.project_id"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.quotation_id"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.dealer_id"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.distributor_id"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.is_direct_contract"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.is_factory_pickup"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.approval_flow_type"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.status"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.current_approval_step"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.pricing_total_amount"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.pricing_total_discount_rate"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.settlement_total_amount"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.settlement_total_discount_rate"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.approved_by"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.approved_at"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.created_by"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.created_at"
pg_dump: 创建COMMENT "public.COLUMN pricing_orders.updated_at"
pg_dump: 创建SEQUENCE "public.pricing_orders_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.pricing_orders_id_seq"
pg_dump: 创建TABLE "public.product_categories"
pg_dump: 创建SEQUENCE "public.product_categories_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.product_categories_id_seq"
pg_dump: 创建TABLE "public.product_code_field_options"
pg_dump: 创建SEQUENCE "public.product_code_field_options_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.product_code_field_options_id_seq"
pg_dump: 创建TABLE "public.product_code_field_values"
pg_dump: 创建SEQUENCE "public.product_code_field_values_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.product_code_field_values_id_seq"
pg_dump: 创建TABLE "public.product_code_fields"
pg_dump: 创建SEQUENCE "public.product_code_fields_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.product_code_fields_id_seq"
pg_dump: 创建TABLE "public.product_codes"
pg_dump: 创建SEQUENCE "public.product_codes_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.product_codes_id_seq"
pg_dump: 创建TABLE "public.product_regions"
pg_dump: 创建SEQUENCE "public.product_regions_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.product_regions_id_seq"
pg_dump: 创建TABLE "public.product_subcategories"
pg_dump: 创建SEQUENCE "public.product_subcategories_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.product_subcategories_id_seq"
pg_dump: 创建TABLE "public.products"
pg_dump: 创建SEQUENCE "public.products_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.products_id_seq"
pg_dump: 创建TABLE "public.project_members"
pg_dump: 创建SEQUENCE "public.project_members_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.project_members_id_seq"
pg_dump: 创建TABLE "public.project_rating_records"
pg_dump: 创建SEQUENCE "public.project_rating_records_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.project_rating_records_id_seq"
pg_dump: 创建TABLE "public.project_scoring_config"
pg_dump: 创建SEQUENCE "public.project_scoring_config_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.project_scoring_config_id_seq"
pg_dump: 创建TABLE "public.project_scoring_records"
pg_dump: 创建SEQUENCE "public.project_scoring_records_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.project_scoring_records_id_seq"
pg_dump: 创建TABLE "public.project_stage_history"
pg_dump: 创建SEQUENCE "public.project_stage_history_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.project_stage_history_id_seq"
pg_dump: 创建TABLE "public.project_total_scores"
pg_dump: 创建SEQUENCE "public.project_total_scores_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.project_total_scores_id_seq"
pg_dump: 创建TABLE "public.projects"
pg_dump: 创建SEQUENCE "public.projects_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.projects_id_seq"
pg_dump: 创建TABLE "public.purchase_order_details"
pg_dump: 创建SEQUENCE "public.purchase_order_details_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.purchase_order_details_id_seq"
pg_dump: 创建TABLE "public.purchase_orders"
pg_dump: 创建SEQUENCE "public.purchase_orders_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.purchase_orders_id_seq"
pg_dump: 创建TABLE "public.quotation_details"
pg_dump: 创建SEQUENCE "public.quotation_details_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.quotation_details_id_seq"
pg_dump: 创建TABLE "public.quotations"
pg_dump: 创建SEQUENCE "public.quotations_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.quotations_id_seq"
pg_dump: 创建TABLE "public.role_permissions"
pg_dump: 创建SEQUENCE "public.role_permissions_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.role_permissions_id_seq"
pg_dump: 创建TABLE "public.settlement_details"
pg_dump: 创建SEQUENCE "public.settlement_details_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.settlement_details_id_seq"
pg_dump: 创建TABLE "public.settlement_order_details"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.pricing_order_id"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.settlement_order_id"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.product_name"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.product_model"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.product_desc"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.brand"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.unit"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.product_mn"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.market_price"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.unit_price"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.quantity"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.discount_rate"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.total_price"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.pricing_detail_id"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.settlement_company_id"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.settlement_status"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.settlement_date"
pg_dump: 创建COMMENT "public.COLUMN settlement_order_details.settlement_notes"
pg_dump: 创建SEQUENCE "public.settlement_order_details_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.settlement_order_details_id_seq"
pg_dump: 创建TABLE "public.settlement_orders"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.order_number"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.pricing_order_id"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.project_id"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.quotation_id"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.distributor_id"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.dealer_id"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.total_amount"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.total_discount_rate"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.status"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.approved_by"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.approved_at"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.created_by"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.created_at"
pg_dump: 创建COMMENT "public.COLUMN settlement_orders.updated_at"
pg_dump: 创建SEQUENCE "public.settlement_orders_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.settlement_orders_id_seq"
pg_dump: 创建TABLE "public.settlements"
pg_dump: 创建SEQUENCE "public.settlements_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.settlements_id_seq"
pg_dump: 创建TABLE "public.solution_manager_email_settings"
pg_dump: 创建COMMENT "public.COLUMN solution_manager_email_settings.user_id"
pg_dump: 创建COMMENT "public.COLUMN solution_manager_email_settings.quotation_created"
pg_dump: 创建COMMENT "public.COLUMN solution_manager_email_settings.quotation_updated"
pg_dump: 创建COMMENT "public.COLUMN solution_manager_email_settings.project_created"
pg_dump: 创建COMMENT "public.COLUMN solution_manager_email_settings.project_stage_changed"
pg_dump: 创建SEQUENCE "public.solution_manager_email_settings_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.solution_manager_email_settings_id_seq"
pg_dump: 创建TABLE "public.system_metrics"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.version_id"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.avg_response_time"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.max_response_time"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.error_rate"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.active_users"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.total_requests"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.database_size"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.cpu_usage"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.memory_usage"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.disk_usage"
pg_dump: 创建COMMENT "public.COLUMN system_metrics.recorded_at"
pg_dump: 创建SEQUENCE "public.system_metrics_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.system_metrics_id_seq"
pg_dump: 创建TABLE "public.system_settings"
pg_dump: 创建SEQUENCE "public.system_settings_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.system_settings_id_seq"
pg_dump: 创建TABLE "public.upgrade_logs"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.version_id"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.from_version"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.to_version"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.upgrade_date"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.upgrade_type"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.status"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.upgrade_notes"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.error_message"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.duration_seconds"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.operator_id"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.operator_name"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.environment"
pg_dump: 创建COMMENT "public.COLUMN upgrade_logs.server_info"
pg_dump: 创建SEQUENCE "public.upgrade_logs_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.upgrade_logs_id_seq"
pg_dump: 创建TABLE "public.user_event_subscriptions"
pg_dump: 创建COMMENT "public.COLUMN user_event_subscriptions.user_id"
pg_dump: 创建COMMENT "public.COLUMN user_event_subscriptions.target_user_id"
pg_dump: 创建COMMENT "public.COLUMN user_event_subscriptions.event_id"
pg_dump: 创建COMMENT "public.COLUMN user_event_subscriptions.enabled"
pg_dump: 创建SEQUENCE "public.user_event_subscriptions_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.user_event_subscriptions_id_seq"
pg_dump: 创建TABLE "public.users"
pg_dump: 创建SEQUENCE "public.users_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.users_id_seq"
pg_dump: 创建TABLE "public.version_records"
pg_dump: 创建COMMENT "public.COLUMN version_records.version_number"
pg_dump: 创建COMMENT "public.COLUMN version_records.version_name"
pg_dump: 创建COMMENT "public.COLUMN version_records.release_date"
pg_dump: 创建COMMENT "public.COLUMN version_records.description"
pg_dump: 创建COMMENT "public.COLUMN version_records.is_current"
pg_dump: 创建COMMENT "public.COLUMN version_records.environment"
pg_dump: 创建COMMENT "public.COLUMN version_records.total_features"
pg_dump: 创建COMMENT "public.COLUMN version_records.total_fixes"
pg_dump: 创建COMMENT "public.COLUMN version_records.total_improvements"
pg_dump: 创建COMMENT "public.COLUMN version_records.git_commit"
pg_dump: 创建COMMENT "public.COLUMN version_records.build_number"
pg_dump: 创建COMMENT "public.COLUMN version_records.created_at"
pg_dump: 创建COMMENT "public.COLUMN version_records.updated_at"
pg_dump: 创建SEQUENCE "public.version_records_id_seq"
pg_dump: 创建SEQUENCE OWNED BY "public.version_records_id_seq"
pg_dump: 创建DEFAULT "public.action_reply id"
pg_dump: 创建DEFAULT "public.actions id"
pg_dump: 创建DEFAULT "public.affiliations id"
pg_dump: 创建DEFAULT "public.approval_instance id"
pg_dump: 创建DEFAULT "public.approval_process_template id"
pg_dump: 创建DEFAULT "public.approval_record id"
pg_dump: 创建DEFAULT "public.approval_step id"
pg_dump: 创建DEFAULT "public.change_logs id"
pg_dump: 创建DEFAULT "public.companies id"
pg_dump: 创建DEFAULT "public.contacts id"
pg_dump: 创建DEFAULT "public.dev_product_specs id"
pg_dump: 创建DEFAULT "public.dev_products id"
pg_dump: 创建DEFAULT "public.dictionaries id"
pg_dump: 创建DEFAULT "public.event_registry id"
pg_dump: 创建DEFAULT "public.feature_changes id"
pg_dump: 创建DEFAULT "public.inventory id"
pg_dump: 创建DEFAULT "public.inventory_transactions id"
pg_dump: 创建DEFAULT "public.permissions id"
pg_dump: 创建DEFAULT "public.pricing_order_approval_records id"
pg_dump: 创建DEFAULT "public.pricing_order_details id"
pg_dump: 创建DEFAULT "public.pricing_orders id"
pg_dump: 创建DEFAULT "public.product_categories id"
pg_dump: 创建DEFAULT "public.product_code_field_options id"
pg_dump: 创建DEFAULT "public.product_code_field_values id"
pg_dump: 创建DEFAULT "public.product_code_fields id"
pg_dump: 创建DEFAULT "public.product_codes id"
pg_dump: 创建DEFAULT "public.product_regions id"
pg_dump: 创建DEFAULT "public.product_subcategories id"
pg_dump: 创建DEFAULT "public.products id"
pg_dump: 创建DEFAULT "public.project_members id"
pg_dump: 创建DEFAULT "public.project_rating_records id"
pg_dump: 创建DEFAULT "public.project_scoring_config id"
pg_dump: 创建DEFAULT "public.project_scoring_records id"
pg_dump: 创建DEFAULT "public.project_stage_history id"
pg_dump: 创建DEFAULT "public.project_total_scores id"
pg_dump: 创建DEFAULT "public.projects id"
pg_dump: 创建DEFAULT "public.purchase_order_details id"
pg_dump: 创建DEFAULT "public.purchase_orders id"
pg_dump: 创建DEFAULT "public.quotation_details id"
pg_dump: 创建DEFAULT "public.quotations id"
pg_dump: 创建DEFAULT "public.role_permissions id"
pg_dump: 创建DEFAULT "public.settlement_details id"
pg_dump: 创建DEFAULT "public.settlement_order_details id"
pg_dump: 创建DEFAULT "public.settlement_orders id"
pg_dump: 创建DEFAULT "public.settlements id"
pg_dump: 创建DEFAULT "public.solution_manager_email_settings id"
pg_dump: 创建DEFAULT "public.system_metrics id"
pg_dump: 创建DEFAULT "public.system_settings id"
pg_dump: 创建DEFAULT "public.upgrade_logs id"
pg_dump: 创建DEFAULT "public.user_event_subscriptions id"
pg_dump: 创建DEFAULT "public.users id"
pg_dump: 创建DEFAULT "public.version_records id"
pg_dump: 为表"public.action_reply"处理数据
pg_dump: 正在转储表"public.action_reply"的内容
pg_dump: 为表"public.actions"处理数据
pg_dump: 正在转储表"public.actions"的内容
pg_dump: 为表"public.affiliations"处理数据
pg_dump: 正在转储表"public.affiliations"的内容
pg_dump: 为表"public.alembic_version"处理数据
pg_dump: 正在转储表"public.alembic_version"的内容
pg_dump: 为表"public.approval_instance"处理数据
pg_dump: 正在转储表"public.approval_instance"的内容
pg_dump: 为表"public.approval_process_template"处理数据
pg_dump: 正在转储表"public.approval_process_template"的内容
pg_dump: 为表"public.approval_record"处理数据
pg_dump: 正在转储表"public.approval_record"的内容
pg_dump: 为表"public.approval_step"处理数据
pg_dump: 正在转储表"public.approval_step"的内容
pg_dump: 为表"public.change_logs"处理数据
pg_dump: 正在转储表"public.change_logs"的内容
pg_dump: 为表"public.companies"处理数据
pg_dump: 正在转储表"public.companies"的内容
pg_dump: 为表"public.contacts"处理数据
pg_dump: 正在转储表"public.contacts"的内容
pg_dump: 为表"public.dev_product_specs"处理数据
pg_dump: 正在转储表"public.dev_product_specs"的内容
pg_dump: 为表"public.dev_products"处理数据
pg_dump: 正在转储表"public.dev_products"的内容
pg_dump: 为表"public.dictionaries"处理数据
pg_dump: 正在转储表"public.dictionaries"的内容
pg_dump: 为表"public.event_registry"处理数据
pg_dump: 正在转储表"public.event_registry"的内容
pg_dump: 为表"public.feature_changes"处理数据
pg_dump: 正在转储表"public.feature_changes"的内容
pg_dump: 为表"public.inventory"处理数据
pg_dump: 正在转储表"public.inventory"的内容
pg_dump: 为表"public.inventory_transactions"处理数据
pg_dump: 正在转储表"public.inventory_transactions"的内容
pg_dump: 为表"public.permissions"处理数据
pg_dump: 正在转储表"public.permissions"的内容
pg_dump: 为表"public.pricing_order_approval_records"处理数据
pg_dump: 正在转储表"public.pricing_order_approval_records"的内容
pg_dump: 为表"public.pricing_order_details"处理数据
pg_dump: 正在转储表"public.pricing_order_details"的内容
pg_dump: 为表"public.pricing_orders"处理数据
pg_dump: 正在转储表"public.pricing_orders"的内容
pg_dump: 为表"public.product_categories"处理数据
pg_dump: 正在转储表"public.product_categories"的内容
pg_dump: 为表"public.product_code_field_options"处理数据
pg_dump: 正在转储表"public.product_code_field_options"的内容
pg_dump: 为表"public.product_code_field_values"处理数据
pg_dump: 正在转储表"public.product_code_field_values"的内容
pg_dump: 为表"public.product_code_fields"处理数据
pg_dump: 正在转储表"public.product_code_fields"的内容
pg_dump: 为表"public.product_codes"处理数据
pg_dump: 正在转储表"public.product_codes"的内容
pg_dump: 为表"public.product_regions"处理数据
pg_dump: 正在转储表"public.product_regions"的内容
pg_dump: 为表"public.product_subcategories"处理数据
pg_dump: 正在转储表"public.product_subcategories"的内容
pg_dump: 为表"public.products"处理数据
pg_dump: 正在转储表"public.products"的内容
pg_dump: 为表"public.project_members"处理数据
pg_dump: 正在转储表"public.project_members"的内容
pg_dump: 为表"public.project_rating_records"处理数据
pg_dump: 正在转储表"public.project_rating_records"的内容
pg_dump: 为表"public.project_scoring_config"处理数据
pg_dump: 正在转储表"public.project_scoring_config"的内容
pg_dump: 为表"public.project_scoring_records"处理数据
pg_dump: 正在转储表"public.project_scoring_records"的内容
pg_dump: 为表"public.project_stage_history"处理数据
pg_dump: 正在转储表"public.project_stage_history"的内容
pg_dump: 为表"public.project_total_scores"处理数据
pg_dump: 正在转储表"public.project_total_scores"的内容
pg_dump: 为表"public.projects"处理数据
pg_dump: 正在转储表"public.projects"的内容
pg_dump: 为表"public.purchase_order_details"处理数据
pg_dump: 正在转储表"public.purchase_order_details"的内容
pg_dump: 为表"public.purchase_orders"处理数据
pg_dump: 正在转储表"public.purchase_orders"的内容
pg_dump: 为表"public.quotation_details"处理数据
pg_dump: 正在转储表"public.quotation_details"的内容
pg_dump: 为表"public.quotations"处理数据
pg_dump: 正在转储表"public.quotations"的内容
pg_dump: 为表"public.role_permissions"处理数据
pg_dump: 正在转储表"public.role_permissions"的内容
pg_dump: 为表"public.settlement_details"处理数据
pg_dump: 正在转储表"public.settlement_details"的内容
pg_dump: 为表"public.settlement_order_details"处理数据
pg_dump: 正在转储表"public.settlement_order_details"的内容
pg_dump: 为表"public.settlement_orders"处理数据
pg_dump: 正在转储表"public.settlement_orders"的内容
pg_dump: 为表"public.settlements"处理数据
pg_dump: 正在转储表"public.settlements"的内容
pg_dump: 为表"public.solution_manager_email_settings"处理数据
pg_dump: 正在转储表"public.solution_manager_email_settings"的内容
pg_dump: 为表"public.system_metrics"处理数据
pg_dump: 正在转储表"public.system_metrics"的内容
pg_dump: 为表"public.system_settings"处理数据
pg_dump: 正在转储表"public.system_settings"的内容
pg_dump: 为表"public.upgrade_logs"处理数据
pg_dump: 正在转储表"public.upgrade_logs"的内容
pg_dump: 为表"public.user_event_subscriptions"处理数据
pg_dump: 正在转储表"public.user_event_subscriptions"的内容
pg_dump: 为表"public.users"处理数据
pg_dump: 正在转储表"public.users"的内容
pg_dump: 为表"public.version_records"处理数据
pg_dump: 正在转储表"public.version_records"的内容
pg_dump: 执行 SEQUENCE SET action_reply_id_seq
pg_dump: 执行 SEQUENCE SET actions_id_seq
pg_dump: 执行 SEQUENCE SET affiliations_id_seq
pg_dump: 执行 SEQUENCE SET approval_instance_id_seq
pg_dump: 执行 SEQUENCE SET approval_process_template_id_seq
pg_dump: 执行 SEQUENCE SET approval_record_id_seq
pg_dump: 执行 SEQUENCE SET approval_step_id_seq
pg_dump: 执行 SEQUENCE SET change_logs_id_seq
pg_dump: 执行 SEQUENCE SET companies_id_seq
pg_dump: 执行 SEQUENCE SET contacts_id_seq
pg_dump: 执行 SEQUENCE SET dev_product_specs_id_seq
pg_dump: 执行 SEQUENCE SET dev_products_id_seq
pg_dump: 执行 SEQUENCE SET dictionaries_id_seq
pg_dump: 执行 SEQUENCE SET event_registry_id_seq
pg_dump: 执行 SEQUENCE SET feature_changes_id_seq
pg_dump: 执行 SEQUENCE SET inventory_id_seq
pg_dump: 执行 SEQUENCE SET inventory_transactions_id_seq
pg_dump: 执行 SEQUENCE SET permissions_id_seq
pg_dump: 执行 SEQUENCE SET pricing_order_approval_records_id_seq
pg_dump: 执行 SEQUENCE SET pricing_order_details_id_seq
pg_dump: 执行 SEQUENCE SET pricing_orders_id_seq
pg_dump: 执行 SEQUENCE SET product_categories_id_seq
pg_dump: 执行 SEQUENCE SET product_code_field_options_id_seq
pg_dump: 执行 SEQUENCE SET product_code_field_values_id_seq
pg_dump: 执行 SEQUENCE SET product_code_fields_id_seq
pg_dump: 执行 SEQUENCE SET product_codes_id_seq
pg_dump: 执行 SEQUENCE SET product_regions_id_seq
pg_dump: 执行 SEQUENCE SET product_subcategories_id_seq
pg_dump: 执行 SEQUENCE SET products_id_seq
pg_dump: 执行 SEQUENCE SET project_members_id_seq
pg_dump: 执行 SEQUENCE SET project_rating_records_id_seq
pg_dump: 执行 SEQUENCE SET project_scoring_config_id_seq
pg_dump: 执行 SEQUENCE SET project_scoring_records_id_seq
pg_dump: 执行 SEQUENCE SET project_stage_history_id_seq
pg_dump: 执行 SEQUENCE SET project_total_scores_id_seq
pg_dump: 执行 SEQUENCE SET projects_id_seq
pg_dump: 执行 SEQUENCE SET purchase_order_details_id_seq
pg_dump: 执行 SEQUENCE SET purchase_orders_id_seq
pg_dump: 执行 SEQUENCE SET quotation_details_id_seq
pg_dump: 执行 SEQUENCE SET quotations_id_seq
pg_dump: 执行 SEQUENCE SET role_permissions_id_seq
pg_dump: 执行 SEQUENCE SET settlement_details_id_seq
pg_dump: 执行 SEQUENCE SET settlement_order_details_id_seq
pg_dump: 执行 SEQUENCE SET settlement_orders_id_seq
pg_dump: 执行 SEQUENCE SET settlements_id_seq
pg_dump: 执行 SEQUENCE SET solution_manager_email_settings_id_seq
pg_dump: 执行 SEQUENCE SET system_metrics_id_seq
pg_dump: 执行 SEQUENCE SET system_settings_id_seq
pg_dump: 执行 SEQUENCE SET upgrade_logs_id_seq
pg_dump: 执行 SEQUENCE SET user_event_subscriptions_id_seq
pg_dump: 执行 SEQUENCE SET users_id_seq
pg_dump: 执行 SEQUENCE SET version_records_id_seq
pg_dump: 创建CONSTRAINT "public.action_reply action_reply_pkey"
pg_dump: 创建CONSTRAINT "public.actions actions_pkey"
pg_dump: 创建CONSTRAINT "public.affiliations affiliations_pkey"
pg_dump: 创建CONSTRAINT "public.alembic_version alembic_version_pkc"
pg_dump: 创建CONSTRAINT "public.approval_instance approval_instance_pkey"
pg_dump: 创建CONSTRAINT "public.approval_process_template approval_process_template_pkey"
pg_dump: 创建CONSTRAINT "public.approval_record approval_record_pkey"
pg_dump: 创建CONSTRAINT "public.approval_step approval_step_pkey"
pg_dump: 创建CONSTRAINT "public.change_logs change_logs_pkey"
pg_dump: 创建CONSTRAINT "public.companies companies_company_code_key"
pg_dump: 创建CONSTRAINT "public.companies companies_pkey"
pg_dump: 创建CONSTRAINT "public.contacts contacts_pkey"
pg_dump: 创建CONSTRAINT "public.dev_product_specs dev_product_specs_pkey"
pg_dump: 创建CONSTRAINT "public.dev_products dev_products_pkey"
pg_dump: 创建CONSTRAINT "public.dictionaries dictionaries_pkey"
pg_dump: 创建CONSTRAINT "public.event_registry event_registry_event_key_key"
pg_dump: 创建CONSTRAINT "public.event_registry event_registry_pkey"
pg_dump: 创建CONSTRAINT "public.feature_changes feature_changes_pkey"
pg_dump: 创建CONSTRAINT "public.inventory inventory_pkey"
pg_dump: 创建CONSTRAINT "public.inventory_transactions inventory_transactions_pkey"
pg_dump: 创建CONSTRAINT "public.permissions permissions_pkey"
pg_dump: 创建CONSTRAINT "public.pricing_order_approval_records pricing_order_approval_records_pkey"
pg_dump: 创建CONSTRAINT "public.pricing_order_details pricing_order_details_pkey"
pg_dump: 创建CONSTRAINT "public.pricing_orders pricing_orders_order_number_key"
pg_dump: 创建CONSTRAINT "public.pricing_orders pricing_orders_pkey"
pg_dump: 创建CONSTRAINT "public.product_categories product_categories_code_letter_key"
pg_dump: 创建CONSTRAINT "public.product_categories product_categories_pkey"
pg_dump: 创建CONSTRAINT "public.product_code_field_options product_code_field_options_pkey"
pg_dump: 创建CONSTRAINT "public.product_code_field_values product_code_field_values_pkey"
pg_dump: 创建CONSTRAINT "public.product_code_fields product_code_fields_pkey"
pg_dump: 创建CONSTRAINT "public.product_codes product_codes_full_code_key"
pg_dump: 创建CONSTRAINT "public.product_codes product_codes_pkey"
pg_dump: 创建CONSTRAINT "public.product_regions product_regions_pkey"
pg_dump: 创建CONSTRAINT "public.product_subcategories product_subcategories_pkey"
pg_dump: 创建CONSTRAINT "public.products products_pkey"
pg_dump: 创建CONSTRAINT "public.products products_product_mn_key"
pg_dump: 创建CONSTRAINT "public.project_members project_members_pkey"
pg_dump: 创建CONSTRAINT "public.project_rating_records project_rating_records_pkey"
pg_dump: 创建CONSTRAINT "public.project_scoring_config project_scoring_config_pkey"
pg_dump: 创建CONSTRAINT "public.project_scoring_records project_scoring_records_pkey"
pg_dump: 创建CONSTRAINT "public.project_stage_history project_stage_history_pkey"
pg_dump: 创建CONSTRAINT "public.project_total_scores project_total_scores_pkey"
pg_dump: 创建CONSTRAINT "public.project_total_scores project_total_scores_project_id_key"
pg_dump: 创建CONSTRAINT "public.projects projects_pkey"
pg_dump: 创建CONSTRAINT "public.purchase_order_details purchase_order_details_pkey"
pg_dump: 创建CONSTRAINT "public.purchase_orders purchase_orders_order_number_key"
pg_dump: 创建CONSTRAINT "public.purchase_orders purchase_orders_pkey"
pg_dump: 创建CONSTRAINT "public.quotation_details quotation_details_pkey"
pg_dump: 创建CONSTRAINT "public.quotations quotations_pkey"
pg_dump: 创建CONSTRAINT "public.quotations quotations_quotation_number_key"
pg_dump: 创建CONSTRAINT "public.role_permissions role_permissions_pkey"
pg_dump: 创建CONSTRAINT "public.settlement_details settlement_details_pkey"
pg_dump: 创建CONSTRAINT "public.settlement_order_details settlement_order_details_pkey"
pg_dump: 创建CONSTRAINT "public.settlement_orders settlement_orders_order_number_key"
pg_dump: 创建CONSTRAINT "public.settlement_orders settlement_orders_pkey"
pg_dump: 创建CONSTRAINT "public.settlements settlements_pkey"
pg_dump: 创建CONSTRAINT "public.settlements settlements_settlement_number_key"
pg_dump: 创建CONSTRAINT "public.solution_manager_email_settings solution_manager_email_settings_pkey"
pg_dump: 创建CONSTRAINT "public.system_metrics system_metrics_pkey"
pg_dump: 创建CONSTRAINT "public.system_settings system_settings_pkey"
pg_dump: 创建CONSTRAINT "public.affiliations uix_owner_viewer"
pg_dump: 创建CONSTRAINT "public.role_permissions uix_role_module"
pg_dump: 创建CONSTRAINT "public.dictionaries uix_type_key"
pg_dump: 创建CONSTRAINT "public.permissions uix_user_module"
pg_dump: 创建CONSTRAINT "public.inventory unique_company_product_inventory"
pg_dump: 创建CONSTRAINT "public.upgrade_logs upgrade_logs_pkey"
pg_dump: 创建CONSTRAINT "public.project_rating_records uq_project_user_rating"
pg_dump: 创建CONSTRAINT "public.project_scoring_config uq_scoring_config"
pg_dump: 创建CONSTRAINT "public.project_scoring_records uq_scoring_record"
pg_dump: 创建CONSTRAINT "public.project_scoring_records uq_scoring_record_with_user"
pg_dump: 创建CONSTRAINT "public.solution_manager_email_settings uq_solution_manager_email_user"
pg_dump: 创建CONSTRAINT "public.product_subcategories uq_subcategory_code_letter"
pg_dump: 创建CONSTRAINT "public.user_event_subscriptions uq_user_target_event"
pg_dump: 创建CONSTRAINT "public.user_event_subscriptions user_event_subscriptions_pkey"
pg_dump: 创建CONSTRAINT "public.users users_email_key"
pg_dump: 创建CONSTRAINT "public.users users_pkey"
pg_dump: 创建CONSTRAINT "public.users users_username_key"
pg_dump: 创建CONSTRAINT "public.users users_wechat_openid_key"
pg_dump: 创建CONSTRAINT "public.version_records version_records_pkey"
pg_dump: 创建CONSTRAINT "public.version_records version_records_version_number_key"
pg_dump: 创建INDEX "public.ix_project_stage_history_project_id"
pg_dump: 创建INDEX "public.ix_projects_authorization_code"
pg_dump: 创建INDEX "public.ix_projects_project_name"
pg_dump: 创建INDEX "public.ix_system_settings_key"
pg_dump: 创建FK CONSTRAINT "public.action_reply action_reply_action_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.action_reply action_reply_owner_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.action_reply action_reply_parent_reply_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.actions actions_company_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.actions actions_contact_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.actions actions_owner_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.actions actions_project_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.affiliations affiliations_owner_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.affiliations affiliations_viewer_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.approval_instance approval_instance_created_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.approval_instance approval_instance_process_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.approval_process_template approval_process_template_created_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.approval_record approval_record_approver_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.approval_record approval_record_instance_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.approval_record approval_record_step_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.approval_step approval_step_approver_user_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.approval_step approval_step_process_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.change_logs change_logs_user_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.companies companies_owner_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.contacts contacts_company_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.contacts contacts_owner_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.dev_product_specs dev_product_specs_dev_product_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.dev_products dev_products_category_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.dev_products dev_products_created_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.dev_products dev_products_owner_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.dev_products dev_products_region_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.dev_products dev_products_subcategory_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.feature_changes feature_changes_developer_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.feature_changes feature_changes_version_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.project_rating_records fk_project_rating_project_id"
pg_dump: 创建FK CONSTRAINT "public.project_rating_records fk_project_rating_user_id"
pg_dump: 创建FK CONSTRAINT "public.inventory inventory_company_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.inventory inventory_created_by_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.inventory inventory_product_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.inventory_transactions inventory_transactions_created_by_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.inventory_transactions inventory_transactions_inventory_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.permissions permissions_user_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.pricing_order_approval_records pricing_order_approval_records_approver_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.pricing_order_approval_records pricing_order_approval_records_pricing_order_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.pricing_order_details pricing_order_details_pricing_order_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.pricing_orders pricing_orders_approved_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.pricing_orders pricing_orders_created_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.pricing_orders pricing_orders_dealer_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.pricing_orders pricing_orders_distributor_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.pricing_orders pricing_orders_project_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.pricing_orders pricing_orders_quotation_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.product_code_field_options product_code_field_options_field_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.product_code_field_values product_code_field_values_field_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.product_code_field_values product_code_field_values_option_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.product_code_field_values product_code_field_values_product_code_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.product_code_fields product_code_fields_subcategory_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.product_codes product_codes_category_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.product_codes product_codes_created_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.product_codes product_codes_product_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.product_codes product_codes_subcategory_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.product_subcategories product_subcategories_category_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.products products_owner_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.project_members project_members_project_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.project_members project_members_user_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.project_rating_records project_rating_records_project_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.project_rating_records project_rating_records_user_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.project_scoring_records project_scoring_records_awarded_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.project_scoring_records project_scoring_records_project_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.project_stage_history project_stage_history_project_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.project_total_scores project_total_scores_project_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.projects projects_locked_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.projects projects_owner_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.projects projects_vendor_sales_manager_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.purchase_order_details purchase_order_details_order_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.purchase_order_details purchase_order_details_product_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.purchase_orders purchase_orders_approved_by_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.purchase_orders purchase_orders_company_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.purchase_orders purchase_orders_created_by_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.quotation_details quotation_details_quotation_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.quotations quotations_confirmed_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.quotations quotations_contact_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.quotations quotations_locked_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.quotations quotations_owner_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.quotations quotations_project_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_details settlement_details_inventory_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_details settlement_details_product_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_details settlement_details_settlement_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_order_details settlement_order_details_pricing_detail_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_order_details settlement_order_details_pricing_order_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_order_details settlement_order_details_settlement_company_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_order_details settlement_order_details_settlement_order_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_orders settlement_orders_approved_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_orders settlement_orders_created_by_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_orders settlement_orders_dealer_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_orders settlement_orders_distributor_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_orders settlement_orders_pricing_order_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_orders settlement_orders_project_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlement_orders settlement_orders_quotation_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlements settlements_approved_by_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlements settlements_company_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.settlements settlements_created_by_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.solution_manager_email_settings solution_manager_email_settings_user_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.system_metrics system_metrics_version_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.upgrade_logs upgrade_logs_operator_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.upgrade_logs upgrade_logs_version_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.user_event_subscriptions user_event_subscriptions_event_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.user_event_subscriptions user_event_subscriptions_target_user_id_fkey"
pg_dump: 创建FK CONSTRAINT "public.user_event_subscriptions user_event_subscriptions_user_id_fkey"

```
