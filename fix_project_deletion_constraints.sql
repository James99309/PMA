
-- 项目删除外键约束修复脚本
-- 修复 actions 和 approval_instance 表的外键约束

-- 1. 修复 actions.project_id 外键约束
-- 删除现有约束
ALTER TABLE actions DROP CONSTRAINT IF EXISTS actions_project_id_fkey;

-- 重新创建带CASCADE的约束
ALTER TABLE actions 
ADD CONSTRAINT actions_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- 2. 注意：approval_instance.object_id 不能直接设置CASCADE
-- 因为它可能引用不同类型的对象（project, quotation等）
-- 所以需要在应用层面处理这个约束

-- 3. 可选：修复其他可能需要CASCADE的约束
-- project_stage_history
ALTER TABLE project_stage_history DROP CONSTRAINT IF EXISTS project_stage_history_project_id_fkey;
ALTER TABLE project_stage_history 
ADD CONSTRAINT project_stage_history_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- project_members (如果存在)
ALTER TABLE project_members DROP CONSTRAINT IF EXISTS project_members_project_id_fkey;
ALTER TABLE project_members 
ADD CONSTRAINT project_members_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- quotations (报价单可以选择CASCADE或保留现有约束)
-- ALTER TABLE quotations DROP CONSTRAINT IF EXISTS quotations_project_id_fkey;
-- ALTER TABLE quotations 
-- ADD CONSTRAINT quotations_project_id_fkey 
-- FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

COMMIT;
