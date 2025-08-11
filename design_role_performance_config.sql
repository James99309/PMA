-- 角色绩效配置系统 - 数据模型设计
-- 设计思路：支持角色级别的灵活绩效配置，每个角色可配置不同的绩效项目和计算方法

-- 1. 绩效指标定义表（系统级配置）
CREATE TABLE performance_metrics_definition (
    id SERIAL PRIMARY KEY,
    metric_code VARCHAR(50) UNIQUE NOT NULL,           -- 指标代码，如 'sales_amount', 'customer_count'
    metric_name VARCHAR(100) NOT NULL,                 -- 指标名称，如 '销售金额', '客户数量'  
    metric_category VARCHAR(50) DEFAULT 'custom',      -- 指标分类：financial(财务), customer(客户), project(项目), custom(自定义)
    data_type VARCHAR(20) NOT NULL,                    -- 数据类型：amount(金额), count(数量), percentage(百分比), score(评分)
    default_unit VARCHAR(20),                          -- 默认单位：元, 万元, 个, %
    description TEXT,                                  -- 指标说明
    available_sources JSONB,                          -- 可用数据源配置 {"sources": [{"table": "quotations", "field": "total_amount"}, ...]}
    is_system_metric BOOLEAN DEFAULT FALSE,           -- 是否系统内置指标
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 角色绩效配置主表
CREATE TABLE role_performance_config (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) NOT NULL,                         -- 角色代码，如 'sales_director', 'product_manager'
    config_name VARCHAR(100),                          -- 配置名称，如 '销售总监绩效方案'
    description TEXT,                                  -- 配置说明
    is_active BOOLEAN DEFAULT TRUE,                    -- 是否启用
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role)                                       -- 每个角色只能有一套配置
);

-- 3. 角色绩效项目配置表（每个角色的具体绩效项目）
CREATE TABLE role_performance_items (
    id SERIAL PRIMARY KEY,
    role_config_id INTEGER REFERENCES role_performance_config(id) ON DELETE CASCADE,
    metric_id INTEGER REFERENCES performance_metrics_definition(id),
    
    -- 项目基本配置
    item_name VARCHAR(100) NOT NULL,                   -- 项目名称（可自定义，覆盖默认名称）
    item_code VARCHAR(50) NOT NULL,                    -- 项目代码
    sort_order INTEGER DEFAULT 0,                      -- 显示顺序
    is_enabled BOOLEAN DEFAULT TRUE,                   -- 是否启用此项目
    
    -- 统计范围配置
    stat_scope VARCHAR(20) NOT NULL DEFAULT 'personal', -- 统计范围：personal(个人), department(部门), company(企业), system(系统)
    stat_scope_description TEXT,                       -- 统计范围说明
    
    -- 计算方法配置
    calculation_method VARCHAR(20) DEFAULT 'sum',      -- 计算方法：sum(求和), avg(平均), count(计数), custom(自定义公式)
    calculation_formula TEXT,                          -- 自定义计算公式，如 'sales_amount * 0.8 + bonus_amount'
    data_source_config JSONB,                         -- 数据源配置：{"table": "quotations", "fields": ["total_amount"], "conditions": "status='approved'"}
    
    -- 合格标准配置
    qualification_rate DECIMAL(5,2),                  -- 合格率（百分比）
    excellent_threshold DECIMAL(15,2),                -- 优秀阈值
    good_threshold DECIMAL(15,2),                     -- 良好阈值
    qualified_threshold DECIMAL(15,2),                -- 合格阈值
    
    -- 显示配置
    display_unit VARCHAR(20),                          -- 显示单位
    decimal_places INTEGER DEFAULT 2,                 -- 小数位数
    color_config JSONB,                               -- 颜色配置：{"excellent": "#28a745", "good": "#17a2b8", "qualified": "#ffc107", "unqualified": "#dc3545"}
    
    -- 权重配置（用于综合评分）
    weight DECIMAL(5,2) DEFAULT 1.0,                  -- 权重
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_config_id, item_code)                 -- 同一角色配置下项目代码不能重复
);

-- 4. 绩效计算公式模板表（预定义常用公式）
CREATE TABLE performance_formula_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,               -- 模板名称，如 '销售金额统计', '客户增长率'
    template_category VARCHAR(50),                     -- 模板分类
    formula_expression TEXT NOT NULL,                  -- 公式表达式
    description TEXT,                                  -- 公式说明
    variables_definition JSONB,                       -- 变量定义：{"variables": [{"name": "sales_amount", "description": "销售金额", "type": "amount"}]}
    example_usage TEXT,                               -- 使用示例
    is_system_template BOOLEAN DEFAULT FALSE,         -- 是否系统模板
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 角色绩效数据访问权限表（控制不同角色能看到哪些用户的数据）
CREATE TABLE role_performance_access (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    access_scope VARCHAR(20) NOT NULL,                -- 访问范围：personal, department, company, system
    access_conditions JSONB,                          -- 访问条件，如部门限制、公司限制等
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role, access_scope)
);

-- 初始化系统内置指标
INSERT INTO performance_metrics_definition (metric_code, metric_name, metric_category, data_type, default_unit, description, is_system_metric) VALUES
('sales_amount', '销售金额', 'financial', 'amount', '万元', '已审批批价单的销售总额', true),
('implant_amount', '植入金额', 'financial', 'amount', '万元', '报价单中产品的市场价值总额', true),
('customer_count', '新增客户数', 'customer', 'count', '个', '新增客户公司数量', true),
('project_count', '新增项目数', 'project', 'count', '个', '新增项目数量', true),
('five_star_projects', '五星项目数', 'project', 'count', '个', '五星级项目数量', true),
('quotation_count', '报价单数', 'business', 'count', '个', '创建的报价单数量', true),
('approval_efficiency', '审批效率', 'business', 'percentage', '%', '审批通过率', true);

-- 初始化公式模板
INSERT INTO performance_formula_templates (template_name, template_category, formula_expression, description, variables_definition, is_system_template) VALUES
('销售金额统计', 'financial', 'SUM(pricing_orders.pricing_total_amount) WHERE status = ''approved''', '统计已审批批价单的销售总额', '{"variables": [{"name": "pricing_total_amount", "description": "批价单总额", "type": "amount"}]}', true),
('植入金额统计', 'financial', 'SUM(quotation_details.quantity * quotation_details.market_price)', '统计报价单明细的植入总额', '{"variables": [{"name": "quantity", "description": "数量"}, {"name": "market_price", "description": "市场价格"}]}', true),
('客户增长率', 'customer', '(当月新增客户数 - 上月新增客户数) / 上月新增客户数 * 100', '计算客户增长百分比', '{"variables": [{"name": "current_count", "description": "当月客户数"}, {"name": "previous_count", "description": "上月客户数"}]}', true),
('综合业绩评分', 'comprehensive', 'sales_amount * 0.4 + implant_amount * 0.3 + customer_count * 100 * 0.3', '综合业绩加权评分', '{"variables": [{"name": "sales_amount", "description": "销售金额"}, {"name": "implant_amount", "description": "植入金额"}, {"name": "customer_count", "description": "客户数量"}]}', true);

-- 创建索引
CREATE INDEX idx_role_performance_config_role ON role_performance_config(role);
CREATE INDEX idx_role_performance_items_role_config ON role_performance_items(role_config_id);
CREATE INDEX idx_role_performance_items_metric ON role_performance_items(metric_id);
CREATE INDEX idx_performance_metrics_code ON performance_metrics_definition(metric_code);
CREATE INDEX idx_performance_access_role ON role_performance_access(role);

-- 添加注释
COMMENT ON TABLE performance_metrics_definition IS '绩效指标定义表 - 定义系统中所有可用的绩效指标';
COMMENT ON TABLE role_performance_config IS '角色绩效配置主表 - 每个角色的绩效配置方案';
COMMENT ON TABLE role_performance_items IS '角色绩效项目表 - 每个角色具体的绩效考核项目';
COMMENT ON TABLE performance_formula_templates IS '绩效计算公式模板表 - 预定义的常用计算公式';
COMMENT ON TABLE role_performance_access IS '角色绩效数据访问权限表 - 控制不同角色的数据访问范围';