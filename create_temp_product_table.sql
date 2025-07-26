-- 创建临时产品表
-- 用于支持手动输入产品功能

CREATE TABLE temp_products (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    
    -- 基础产品信息
    product_name VARCHAR(100) NOT NULL COMMENT '产品名称',
    product_model VARCHAR(100) NOT NULL COMMENT '产品型号',
    product_desc TEXT COMMENT '产品描述/规格',
    brand VARCHAR(50) COMMENT '品牌',
    unit VARCHAR(20) DEFAULT '个' COMMENT '单位',
    
    -- 分类关联
    category VARCHAR(50) COMMENT '关联的三级分类',
    category_path VARCHAR(200) COMMENT '完整分类路径，如：基站/近端设备/室内型',
    
    -- 用户关联
    created_by INT NOT NULL COMMENT '创建用户ID',
    
    -- 使用统计
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    last_used_at TIMESTAMP NULL COMMENT '最后使用时间',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 软删除
    is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否已删除',
    
    -- 外键约束
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_temp_product_category (category),
    INDEX idx_temp_product_creator (created_by),
    INDEX idx_temp_product_model_creator (product_model, created_by),
    INDEX idx_temp_product_usage (usage_count),
    INDEX idx_temp_product_deleted (is_deleted),
    INDEX idx_temp_product_last_used (last_used_at),
    
    -- 唯一约束：同一用户不能有相同型号的活跃临时产品
    UNIQUE KEY uk_temp_product_user_model (created_by, product_model, is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='临时产品表';

-- 插入测试数据（可选）
INSERT INTO temp_products (
    product_name, product_model, product_desc, brand, unit, 
    category, category_path, created_by, usage_count
) VALUES 
(
    '自定义光纤收发器', 'CFT-1000X', '千兆单模光纤收发器，支持1310/1550nm波长', 
    '自定义品牌', '台', '基站', '基站/传输设备/光纤收发器', 1, 3
),
(
    '临时网络交换机', 'SW-2400G', '24口千兆以太网交换机，机架式安装', 
    '临时供应商', '台', '网络设备', '网络设备/交换机/千兆交换机', 1, 1
);

-- 创建视图：合并临时产品和正式产品的查询
-- 方便在产品选择器中统一显示
CREATE VIEW v_all_products AS
SELECT 
    CONCAT('regular_', id) as unified_id,
    'regular' as product_type,
    id as original_id,
    type,
    category,
    product_mn,
    product_name,
    model as product_model,
    specification as product_desc,
    brand,
    unit,
    retail_price as market_price,
    currency,
    status,
    created_at,
    0 as usage_count,
    NULL as created_by,
    is_vendor_product
FROM products 
WHERE status != 'deleted'

UNION ALL

SELECT 
    CONCAT('temp_', id) as unified_id,
    'temp' as product_type,
    id as original_id,
    'temp' as type,
    category,
    NULL as product_mn,
    product_name,
    product_model,
    product_desc,
    brand,
    unit,
    0 as market_price,
    'CNY' as currency,
    'temp' as status,
    created_at,
    usage_count,
    created_by,
    FALSE as is_vendor_product
FROM temp_products 
WHERE is_deleted = FALSE;

-- 创建函数：获取用户在特定分类下的产品（包含临时产品）
DELIMITER //

CREATE FUNCTION get_user_products_in_category(
    p_category VARCHAR(50),
    p_user_id INT
) RETURNS JSON
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE result JSON DEFAULT JSON_ARRAY();
    
    -- 获取正式产品
    SELECT JSON_ARRAYAGG(
        JSON_OBJECT(
            'id', id,
            'type', 'regular',
            'product_name', product_name,
            'product_model', model,
            'product_desc', specification,
            'brand', brand,
            'unit', unit,
            'market_price', retail_price,
            'status', status,
            'is_temp', FALSE
        )
    ) INTO @regular_products
    FROM products 
    WHERE category = p_category AND status != 'deleted';
    
    -- 获取临时产品
    SELECT JSON_ARRAYAGG(
        JSON_OBJECT(
            'id', id,
            'type', 'temp',
            'product_name', product_name,
            'product_model', product_model,
            'product_desc', product_desc,
            'brand', brand,
            'unit', unit,
            'market_price', 0,
            'status', 'temp',
            'is_temp', TRUE,
            'usage_count', usage_count
        )
    ) INTO @temp_products
    FROM temp_products 
    WHERE category = p_category 
      AND created_by = p_user_id 
      AND is_deleted = FALSE;
    
    -- 合并结果
    SET result = JSON_MERGE_PRESERVE(
        COALESCE(@regular_products, JSON_ARRAY()),
        COALESCE(@temp_products, JSON_ARRAY())
    );
    
    RETURN result;
END //

DELIMITER ;

-- 权限设置
-- 确保web应用用户有访问权限
-- GRANT SELECT, INSERT, UPDATE, DELETE ON temp_products TO 'your_web_user'@'localhost';
-- GRANT SELECT ON v_all_products TO 'your_web_user'@'localhost';
-- GRANT EXECUTE ON FUNCTION get_user_products_in_category TO 'your_web_user'@'localhost';