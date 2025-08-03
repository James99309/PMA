-- 为报销单模块创建性能优化索引
-- 执行时间：2025-08-03

-- 1. 报销单主表索引
-- 复合索引：删除状态 + 创建时间（用于基础查询和排序）
CREATE INDEX IF NOT EXISTS idx_expense_deleted_created 
ON expense(is_deleted, created_at DESC);

-- 复合索引：删除状态 + 状态 + 创建时间（用于状态筛选）
CREATE INDEX IF NOT EXISTS idx_expense_deleted_status_created 
ON expense(is_deleted, status, created_at DESC);

-- 复合索引：删除状态 + 客户ID + 创建时间（用于客户筛选）
CREATE INDEX IF NOT EXISTS idx_expense_deleted_customer_created 
ON expense(is_deleted, customer_id, created_at DESC);

-- 复合索引：删除状态 + 拥有者ID + 创建时间（用于申请人筛选）
CREATE INDEX IF NOT EXISTS idx_expense_deleted_owner_created 
ON expense(is_deleted, owner_id, created_at DESC);

-- 2. 报销明细表索引
-- 外键索引：报销单ID（用于明细数量统计）
CREATE INDEX IF NOT EXISTS idx_expense_detail_expense_id 
ON expense_detail(expense_id);

-- 3. 关联表索引
-- 公司表：删除状态 + 名称（用于搜索）
CREATE INDEX IF NOT EXISTS idx_company_deleted_name 
ON company(is_deleted, company_name);

-- 项目表：名称（用于搜索）
CREATE INDEX IF NOT EXISTS idx_project_name 
ON project(project_name);

-- 用户表：活跃状态 + 真实姓名（用于筛选选项）
CREATE INDEX IF NOT EXISTS idx_user_active_realname 
ON "user"(is_active, real_name);

-- 4. 搜索相关索引（使用GIN索引支持ILIKE操作）
-- 如果数据库支持，为文本搜索创建GIN索引
-- CREATE INDEX IF NOT EXISTS idx_expense_number_gin 
-- ON expense USING gin(expense_number gin_trgm_ops);

-- CREATE INDEX IF NOT EXISTS idx_expense_title_gin 
-- ON expense USING gin(title gin_trgm_ops);

-- CREATE INDEX IF NOT EXISTS idx_company_name_gin 
-- ON company USING gin(company_name gin_trgm_ops);