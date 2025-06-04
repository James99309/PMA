-- 审批流程增强功能数据库迁移脚本
-- 添加对象锁定配置、可编辑字段和邮件抄送功能

-- 1. 为审批流程模板表添加对象锁定配置字段
ALTER TABLE approval_process_template 
ADD COLUMN IF NOT EXISTS lock_object_on_start BOOLEAN DEFAULT TRUE;

ALTER TABLE approval_process_template 
ADD COLUMN IF NOT EXISTS lock_reason VARCHAR(200) DEFAULT '审批流程进行中，暂时锁定编辑';

-- 2. 为审批步骤表添加可编辑字段和邮件抄送配置字段
ALTER TABLE approval_step 
ADD COLUMN IF NOT EXISTS editable_fields JSON DEFAULT '[]';

ALTER TABLE approval_step 
ADD COLUMN IF NOT EXISTS cc_users JSON DEFAULT '[]';

ALTER TABLE approval_step 
ADD COLUMN IF NOT EXISTS cc_enabled BOOLEAN DEFAULT FALSE;

-- 3. 添加字段注释
COMMENT ON COLUMN approval_process_template.lock_object_on_start IS '发起审批后是否锁定对象编辑';
COMMENT ON COLUMN approval_process_template.lock_reason IS '锁定原因说明';
COMMENT ON COLUMN approval_step.editable_fields IS '在此步骤可编辑的字段列表';
COMMENT ON COLUMN approval_step.cc_users IS '邮件抄送用户ID列表';
COMMENT ON COLUMN approval_step.cc_enabled IS '是否启用邮件抄送';

-- 4. 更新现有数据的默认值
UPDATE approval_process_template 
SET lock_object_on_start = TRUE, 
    lock_reason = '审批流程进行中，暂时锁定编辑' 
WHERE lock_object_on_start IS NULL;

UPDATE approval_step 
SET editable_fields = '[]', 
    cc_users = '[]', 
    cc_enabled = FALSE 
WHERE editable_fields IS NULL; 