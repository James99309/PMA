-- ================================================
-- 分支条件独立数据表创建脚本
-- ================================================

-- 创建分支条件表
CREATE TABLE approval_branch_condition (
    -- 主键和关联
    id VARCHAR(50) PRIMARY KEY,                    -- 条件唯一ID (格式: cond_xxxxxxxx)
    step_id INTEGER NOT NULL,                      -- 关联的审批步骤ID
    condition_order INTEGER DEFAULT 0,            -- 条件在步骤中的排序（0开始）
    
    -- 条件配置
    operator VARCHAR(50) NOT NULL,                 -- 操作符：equals, not_equals, in, contains等
    field_value VARCHAR(255) NOT NULL,             -- 条件值：sales_focus, business_opportunity等
    
    -- 审批人配置
    approver_id INTEGER,                           -- 审批人ID（如果是具体用户）
    approver_type VARCHAR(50) DEFAULT 'user',     -- 审批人类型：user, next_level, next_branch
    action VARCHAR(100),                           -- 执行动作：authorization, payment_processing等
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    CONSTRAINT fk_branch_condition_step 
        FOREIGN KEY (step_id) 
        REFERENCES approval_step(id) 
        ON DELETE CASCADE,
        
    CONSTRAINT fk_branch_condition_approver 
        FOREIGN KEY (approver_id) 
        REFERENCES users(id) 
        ON DELETE SET NULL,
        
    -- 业务约束
    CONSTRAINT chk_operator_valid 
        CHECK (operator IN (
            'equals', 'not_equals', 'contains', 'not_contains',
            'greater_than', 'less_than', 'in', 'not_in',
            'starts_with', 'ends_with', 'is_null', 'is_not_null'
        )),
        
    CONSTRAINT chk_approver_type_valid 
        CHECK (approver_type IN ('user', 'next_level', 'next_branch')),
        
    CONSTRAINT chk_condition_order_positive 
        CHECK (condition_order >= 0),
        
    -- 唯一性约束（防止同一步骤下的完全重复条件）
    CONSTRAINT uk_step_operator_value 
        UNIQUE (step_id, operator, field_value)
);

-- ================================================
-- 索引创建
-- ================================================

-- 基本查询索引
CREATE INDEX idx_branch_condition_step_id 
    ON approval_branch_condition(step_id);

-- 排序查询索引
CREATE INDEX idx_branch_condition_order 
    ON approval_branch_condition(step_id, condition_order);

-- 审批人查询索引
CREATE INDEX idx_branch_condition_approver 
    ON approval_branch_condition(approver_id);

-- 条件值查询索引（用于重复检测）
CREATE INDEX idx_branch_condition_value 
    ON approval_branch_condition(field_value, operator);

-- ================================================
-- 触发器：自动更新 updated_at
-- ================================================
CREATE OR REPLACE FUNCTION update_branch_condition_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_branch_condition_updated_at
    BEFORE UPDATE ON approval_branch_condition
    FOR EACH ROW
    EXECUTE FUNCTION update_branch_condition_updated_at();

-- ================================================
-- 验证脚本
-- ================================================

-- 查看表结构
\d approval_branch_condition;

-- 验证约束
SELECT 
    conname as constraint_name,
    contype as constraint_type,
    consrc as constraint_definition
FROM pg_constraint 
WHERE conrelid = 'approval_branch_condition'::regclass
ORDER BY contype, conname;

-- 验证索引
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'approval_branch_condition'
ORDER BY indexname;

-- ================================================
-- 测试数据（可选）
-- ================================================

-- 插入测试数据示例
/*
INSERT INTO approval_branch_condition (
    id, step_id, condition_order,
    operator, field_value,
    approver_id, approver_type, action
) VALUES 
(
    'cond_test001', 53, 0,
    'equals', 'sales_focus',
    6, 'user', 'pricing_settlement_approval'
);
*/

COMMENT ON TABLE approval_branch_condition IS '审批分支条件表 - 存储审批步骤的分支决策条件';
COMMENT ON COLUMN approval_branch_condition.id IS '条件唯一标识符';
COMMENT ON COLUMN approval_branch_condition.step_id IS '关联的审批步骤ID';
COMMENT ON COLUMN approval_branch_condition.condition_order IS '条件在步骤中的排序位置';
COMMENT ON COLUMN approval_branch_condition.operator IS '条件操作符（等于、包含等）';
COMMENT ON COLUMN approval_branch_condition.field_value IS '条件匹配的字段值';
COMMENT ON COLUMN approval_branch_condition.approver_id IS '满足条件时的审批人用户ID';
COMMENT ON COLUMN approval_branch_condition.approver_type IS '审批人类型（用户/上级/下一分支）';
COMMENT ON COLUMN approval_branch_condition.action IS '满足条件时执行的业务动作';