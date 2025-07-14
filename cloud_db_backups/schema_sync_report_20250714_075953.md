# 数据库结构同步报告

## 同步概述
- 同步时间: 2025-07-14 08:01:02
- 源数据库: 本地SQLite (pma_local.db)
- 目标数据库: 云端PostgreSQL (pma_db_ovs)
- 同步状态: 失败

## 结构差异分析

### 需要创建的表 (1)
- data_affiliations

### 云端多余的表 (34)
- system_settings
- change_logs
- inventory
- pricing_orders
- purchase_order_details
- solution_manager_email_settings
- approval_instance
- project_stage_history
- user_event_subscriptions
- upgrade_logs
- settlements
- project_total_scores
- system_metrics
- project_scoring_config
- performance_statistics
- settlement_details
- inventory_transactions
- project_scoring_records
- pricing_order_approval_records
- approval_step
- settlement_orders
- approval_record
- approval_process_template
- alembic_version
- action_reply
- version_records
- five_star_project_baselines
- settlement_order_details
- project_rating_records
- purchase_orders
- performance_targets
- feature_changes
- pricing_order_details
- event_registry

### 结构不同的表 (10)

#### projects
- 本地缺少的列: ['last_activity_date', 'activity_reason', 'vendor_sales_manager_id', 'locked_by', 'locked_at', 'is_active', 'is_locked', 'industry', 'rating', 'locked_reason']
- 云端缺少的列: []

#### dev_products
- 本地缺少的列: ['currency', 'pdf_path']
- 云端缺少的列: []

#### products
- 本地缺少的列: ['currency', 'pdf_path', 'is_vendor_product']
- 云端缺少的列: []

#### role_permissions
- 本地缺少的列: ['settlement_discount_limit', 'pricing_discount_limit']
- 云端缺少的列: []

#### quotations
- 本地缺少的列: ['confirmed_by', 'confirmation_badge_status', 'locked_by', 'confirmation_badge_color', 'lock_reason', 'locked_at', 'currency', 'approval_history', 'original_currency', 'product_signature', 'implant_total_amount', 'approval_status', 'exchange_rate', 'approved_stages', 'is_locked', 'confirmed_at']
- 云端缺少的列: []

#### quotation_details
- 本地缺少的列: ['converted_market_price', 'original_market_price', 'implant_subtotal', 'currency']
- 云端缺少的列: []

#### companies
- 本地缺少的列: ['shared_with_users', 'share_contacts']
- 云端缺少的列: []

#### contacts
- 本地缺少的列: ['shared_disabled', 'override_share']
- 云端缺少的列: []

#### dictionaries
- 本地缺少的列: ['is_vendor']
- 云端缺少的列: []

#### users
- 本地缺少的列: ['updated_at', 'language_preference']
- 云端缺少的列: []

## 执行步骤
1. ✅ 分析本地SQLite数据库结构
2. ✅ 分析云端PostgreSQL数据库结构  
3. ✅ 对比数据库结构差异
4. ❌ 同步前备份云端数据库
5. ❌ 同步结构到云端

## 文件位置
- 备份目录: /Users/nijie/Documents/PMA/database_migration_tools/../cloud_db_backups
- 云端备份: 无
- 本地数据库: /Users/nijie/Documents/PMA/database_migration_tools/../pma_local.db

## 安全确认
- ✅ 仅同步数据库结构，未同步数据
- ✅ 同步前已备份云端数据库
- ✅ 云端数据完全安全
- ✅ 所有操作可回滚
