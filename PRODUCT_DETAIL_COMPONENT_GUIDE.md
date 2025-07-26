# 通用产品明细管理组件使用指南

## 概述

通用产品明细管理组件是一个高度可配置的产品明细管理解决方案，支持报价单、采购单、销售单等多种业务场景。

## 核心组件

### 1. ProductDetailManager (JavaScript)
主要的产品明细管理类，负责整体的交互逻辑和数据管理。

### 2. ProductSelector (JavaScript)  
产品选择器组件，提供四级联动的产品选择功能。

### 3. render_product_detail_table (Jinja2 宏)
用于渲染产品明细表格的模板宏。

## 快速开始

### 1. 在模板中引入组件

```html
{% from "macros/product_detail_manager.html" import render_product_detail_table, init_product_detail_scripts %}

<!-- 在页面内容中使用 -->
{{ render_product_detail_table(config, existing_data) }}

<!-- 在页面底部初始化脚本 -->
{{ init_product_detail_scripts() }}
```

### 2. 配置组件

```python
# 在视图中准备配置
product_config = {
    "table_id": "myProductTable",
    "add_button_id": "addMyProduct", 
    "grand_total_id": "myGrandTotal",
    
    # API端点配置
    "api_endpoints": {
        "categories": url_for('api.get_product_categories'),
        "productsByCategory": url_for('api.get_products_by_category'),
        "productModels": url_for('api.get_product_models'),
        "productSpecs": url_for('api.get_product_specs'),
        "productSearch": url_for('api.search_products')
    },
    
    # 计算规则
    "calculation_rules": {
        "discount_type": "percentage",  # 或 "fixed"
        "currency": "CNY",
        "decimal_places": 2,
        "auto_calculate": true
    },
    
    # 列配置
    "columns": [
        {
            "key": "product_name",
            "label": "产品名称",
            "type": "product-selector",
            "required": true,
            "width": "200px"
        },
        # ... 更多列配置
    ],
    
    # 字段映射
    "field_mapping": {
        "product_name": "product_name",
        "quantity": "quantity",
        "unit_price": "unit_price",
        # ... 更多字段映射
    },
    
    # 验证规则
    "validators": {
        "quantity": "val => val > 0",
        "unit_price": "val => val >= 0"
    },
    
    # 事件回调
    "callbacks": {
        "onProductSelect": "handleProductSelect",
        "onCalculate": "handleCalculate"
    }
}
```

### 3. 在JavaScript中处理事件

```javascript
// 产品选择回调
function handleProductSelect(data) {
    const { product, row } = data;
    console.log('选择了产品:', product);
    
    // 自定义业务逻辑
    if (product.special_field) {
        // 处理特殊字段
    }
}

// 计算回调
function handleCalculate(data) {
    const { row, rowData } = data;
    
    // 自定义计算逻辑
    // 比如税费、运费等
}

// 访问管理器实例
const manager = window.productDetailManager;

// 获取所有数据
const allData = manager.getAllData();

// 设置数据
manager.setAllData(dataArray);

// 验证数据
const errors = manager.validateAll();
```

## 预设配置

### 报价单配置

```javascript
const quotationConfig = {
    "discount_type": "percentage",
    "currency": "CNY",
    "columns": [
        // 包含产品名称、型号、规格、品牌、单位、数量、市场价、折扣率、单价、小计
    ],
    "callbacks": {
        "onProductSelect": "handleQuotationProductSelect"
    }
};
```

### 采购单配置

```javascript  
const purchaseConfig = {
    "discount_type": "fixed",
    "currency": "USD", 
    "columns": [
        // 包含产品名称、供应商、采购数量、采购单价、折扣金额、税费、小计
    ],
    "callbacks": {
        "onProductSelect": "handlePurchaseProductSelect"
    }
};
```

## API要求

组件需要以下API端点支持：

### 1. 获取产品类别
```
GET /api/products/categories
返回: ["类别1", "类别2", ...]
```

### 2. 按类别获取产品
```
GET /api/products/by-category?category=类别名
返回: [
    {
        "id": 1,
        "product_name": "产品名",
        "model": "型号",
        "specification": "规格",
        "brand": "品牌",
        "unit": "单位",
        "retail_price": 100.00,
        "currency": "CNY",
        "product_mn": "MN123"
    },
    ...
]
```

### 3. 获取产品型号
```
GET /api/products/models?category=类别&product_name=产品名
返回: 产品对象数组（按型号分组）
```

### 4. 获取产品规格
```
GET /api/products/specs?category=类别&product_name=产品名&model=型号
返回: 产品对象数组（最终可选择的规格）
```

### 5. 产品搜索
```
GET /api/products/search?term=搜索词
返回: 匹配的产品对象数组
```

## 列类型说明

### product-selector
产品选择器，支持四级联动选择。

### text
普通文本输入框。

### number
数字输入框，支持step设置。

### currency
货币输入框，自动格式化显示。

### percentage
百分比输入框，通常用于折扣率。

### actions
操作列，包含删除按钮等。

## 事件系统

### 可监听的事件

- **ready**: 组件初始化完成
- **rowAdd**: 添加新行
- **rowRemove**: 删除行
- **rowUpdate**: 行数据更新
- **productSelect**: 选择产品
- **calculate**: 重新计算
- **grandTotalUpdate**: 总计更新
- **fieldChange**: 字段值变化
- **error**: 发生错误

### 事件监听示例

```javascript
const manager = window.productDetailManager;

manager.on('productSelect', function(data) {
    console.log('产品选择事件:', data);
});

manager.on('calculate', function(data) {
    console.log('计算事件:', data);
});
```

## 自定义样式

组件提供了丰富的CSS类名用于自定义样式：

```css
/* 容器样式 */
.product-detail-container { }

/* 表格样式 */
.product-detail-container .table { }

/* 输入框样式 */
.product-detail-container .form-control { }

/* 货币输入框 */
.product-detail-container .currency-input { }

/* 总计区域 */
.product-detail-container .grand-total-container { }

/* 错误状态 */
.product-detail-container .is-invalid { }

/* 只读模式 */
.product-detail-container.readonly { }
```

## 最佳实践

### 1. 配置管理
将配置对象抽取到单独的配置文件中，便于维护。

### 2. 错误处理
实现全局的错误处理函数，统一处理组件错误。

### 3. 数据验证
在服务端也要进行数据验证，不能仅依赖前端验证。

### 4. 性能优化
对于大量数据的场景，考虑实现虚拟滚动或分页加载。

### 5. 可访问性
为表单元素添加适当的标签和ARIA属性。

## 故障排除

### 常见问题

1. **组件未初始化**
   - 检查是否正确引入了JavaScript文件
   - 确认DOM结构是否正确

2. **API调用失败**
   - 检查API端点配置是否正确
   - 确认服务端API是否正常工作

3. **数据格式错误**
   - 检查服务端返回的数据格式是否符合要求
   - 确认字段映射配置是否正确

4. **计算结果不正确**
   - 检查计算规则配置
   - 确认验证规则是否过于严格

### 调试技巧

```javascript
// 启用详细日志
window.productDetailManager.config.debug = true;

// 检查当前数据
console.log(window.productDetailManager.getAllData());

// 检查配置
console.log(window.productDetailManager.config);

// 手动触发计算
window.productDetailManager.updateGrandTotal();
```

## 版本兼容性

- 支持现代浏览器（Chrome 60+, Firefox 55+, Safari 11+, Edge 79+）
- 需要ES6+支持
- 依赖Bootstrap 5+样式框架
- 依赖Font Awesome图标库

## 更新日志

### v1.0.0 (2025-01-XX)
- 初始版本发布
- 支持基础的产品明细管理功能
- 四级联动产品选择器
- 可配置的计算规则
- 事件系统支持