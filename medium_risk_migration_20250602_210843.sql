-- 中等风险数据库迁移
-- 生成时间: 2025-06-02 21:08:43.455193

BEGIN;

-- 添加列: approval_process_template.lock_object_on_start
ALTER TABLE approval_process_template ADD COLUMN IF NOT EXISTS lock_object_on_start BOOLEAN NULL DEFAULT true;

-- 添加列: approval_process_template.lock_reason
ALTER TABLE approval_process_template ADD COLUMN IF NOT EXISTS lock_reason VARCHAR(200) NULL DEFAULT '审批流程进行中，暂时锁定编辑'::character varying;

-- 添加列: approval_step.editable_fields
ALTER TABLE approval_step ADD COLUMN IF NOT EXISTS editable_fields JSON NULL DEFAULT '[]'::json;

-- 添加列: approval_step.cc_users
ALTER TABLE approval_step ADD COLUMN IF NOT EXISTS cc_users JSON NULL DEFAULT '[]'::json;

-- 添加列: approval_step.cc_enabled
ALTER TABLE approval_step ADD COLUMN IF NOT EXISTS cc_enabled BOOLEAN NULL DEFAULT false;

-- 添加列: approval_instance.template_snapshot
ALTER TABLE approval_instance ADD COLUMN IF NOT EXISTS template_snapshot JSON NULL ;

-- 添加列: approval_instance.template_version
ALTER TABLE approval_instance ADD COLUMN IF NOT EXISTS template_version VARCHAR(50) NULL ;

-- 添加列: quotations.approval_status
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) NULL DEFAULT 'pending'::character varying;

-- 添加列: quotations.approved_stages
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS approved_stages JSON NULL DEFAULT '[]'::json;

-- 添加列: quotations.approval_history
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS approval_history JSON NULL DEFAULT '[]'::json;

-- 添加列: quotations.is_locked
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS is_locked BOOLEAN NULL DEFAULT false;

-- 添加列: quotations.lock_reason
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS lock_reason VARCHAR(200) NULL ;

-- 添加列: quotations.locked_by
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS locked_by INTEGER NULL ;

-- 添加列: quotations.locked_at
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP NULL ;

COMMIT;
