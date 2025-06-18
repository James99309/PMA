-- 安全的数据库结构同步 DDL
-- 生成时间: 2025-06-18 23:00:11
-- 这些操作是安全的，不会删除或破坏现有数据

-- ============================================
-- 1. 添加新列（安全操作）
-- ============================================

-- 为 dictionaries 表添加 is_vendor 列
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS is_vendor boolean DEFAULT false;

-- 为 role_permissions 表添加折扣限制列
ALTER TABLE role_permissions ADD COLUMN IF NOT EXISTS pricing_discount_limit double precision;
ALTER TABLE role_permissions ADD COLUMN IF NOT EXISTS settlement_discount_limit double precision;

-- 为 users 表添加语言偏好列
ALTER TABLE users ADD COLUMN IF NOT EXISTS language_preference character varying(10);

-- ============================================
-- 2. 设置默认值（安全操作）
-- ============================================

-- 为 approval_process_template 表设置默认值
ALTER TABLE approval_process_template ALTER COLUMN required_fields SET DEFAULT '[]'::jsonb;
ALTER TABLE approval_process_template ALTER COLUMN lock_object_on_start SET DEFAULT true;
ALTER TABLE approval_process_template ALTER COLUMN lock_reason SET DEFAULT '审批流程进行中，暂时锁定编辑'::character varying;

-- 为 approval_step 表设置默认值
ALTER TABLE approval_step ALTER COLUMN editable_fields SET DEFAULT '[]'::json;
ALTER TABLE approval_step ALTER COLUMN cc_users SET DEFAULT '[]'::json;
ALTER TABLE approval_step ALTER COLUMN cc_enabled SET DEFAULT false;

-- 为 pricing_orders 表设置默认值
ALTER TABLE pricing_orders ALTER COLUMN is_direct_contract SET DEFAULT false;
ALTER TABLE pricing_orders ALTER COLUMN is_factory_pickup SET DEFAULT false;

-- 为 project_scoring_config 表设置默认值
ALTER TABLE project_scoring_config ALTER COLUMN score_value SET DEFAULT 0.0;
ALTER TABLE project_scoring_config ALTER COLUMN is_active SET DEFAULT true;
ALTER TABLE project_scoring_config ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE project_scoring_config ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

-- 为 project_scoring_records 表设置默认值
ALTER TABLE project_scoring_records ALTER COLUMN score_value SET DEFAULT 0.0;
ALTER TABLE project_scoring_records ALTER COLUMN auto_calculated SET DEFAULT true;
ALTER TABLE project_scoring_records ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE project_scoring_records ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

-- 为 project_total_scores 表设置默认值
ALTER TABLE project_total_scores ALTER COLUMN information_score SET DEFAULT 0.0;
ALTER TABLE project_total_scores ALTER COLUMN quotation_score SET DEFAULT 0.0;
ALTER TABLE project_total_scores ALTER COLUMN stage_score SET DEFAULT 0.0;
ALTER TABLE project_total_scores ALTER COLUMN manual_score SET DEFAULT 0.0;
ALTER TABLE project_total_scores ALTER COLUMN total_score SET DEFAULT 0.0;
ALTER TABLE project_total_scores ALTER COLUMN star_rating SET DEFAULT 0;
ALTER TABLE project_total_scores ALTER COLUMN last_calculated SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE project_total_scores ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE project_total_scores ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

-- 为 projects 表设置默认值
ALTER TABLE projects ALTER COLUMN updated_at SET DEFAULT now();
ALTER TABLE projects ALTER COLUMN is_locked SET DEFAULT false;
ALTER TABLE projects ALTER COLUMN is_active SET DEFAULT true;
ALTER TABLE projects ALTER COLUMN last_activity_date SET DEFAULT now();

-- 为 quotation_details 表设置默认值
ALTER TABLE quotation_details ALTER COLUMN implant_subtotal SET DEFAULT 0.00;

-- 为 quotations 表设置默认值
ALTER TABLE quotations ALTER COLUMN approval_status SET DEFAULT 'pending'::character varying;
ALTER TABLE quotations ALTER COLUMN approved_stages SET DEFAULT '[]'::json;
ALTER TABLE quotations ALTER COLUMN approval_history SET DEFAULT '[]'::json;
ALTER TABLE quotations ALTER COLUMN is_locked SET DEFAULT false;
ALTER TABLE quotations ALTER COLUMN confirmation_badge_status SET DEFAULT 'none'::character varying;
ALTER TABLE quotations ALTER COLUMN confirmation_badge_color SET DEFAULT NULL::character varying;
ALTER TABLE quotations ALTER COLUMN product_signature SET DEFAULT NULL::character varying;
ALTER TABLE quotations ALTER COLUMN implant_total_amount SET DEFAULT 0.00; 