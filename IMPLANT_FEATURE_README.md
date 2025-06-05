# 报价单植入小计和植入总额合计功能

## 功能概述

为PMA项目管理系统的报价单模块新增了植入小计和植入总额合计功能，用于统计和源通信品牌产品的金额。

## 功能特性

### 1. 植入小计（产品明细级别）
- **字段名称**: `implant_subtotal`
- **计算规则**: 当产品品牌是"和源通信"时，植入小计 = 零售价格（市场价） × 产品数量
- **非和源通信产品**: 植入小计 = 0
- **数据类型**: DECIMAL(12,2)
- **前端显示**: 该字段不在前端显示，仅用于后台计算

### 2. 植入总额合计（报价单级别）
- **字段名称**: `implant_total_amount`
- **计算规则**: 该报价单下所有产品明细的植入小计之和
- **数据类型**: DECIMAL(12,2)
- **前端显示**: 在报价单详情页面的基本信息表格中显示

## 数据库变更

### 新增字段

#### quotation_details 表
```sql
ALTER TABLE quotation_details 
ADD COLUMN implant_subtotal DECIMAL(12,2) DEFAULT 0.00;
```

#### quotations 表
```sql
ALTER TABLE quotations 
ADD COLUMN implant_total_amount DECIMAL(12,2) DEFAULT 0.00;
```

### 索引优化
```sql
CREATE INDEX idx_quotation_details_implant_subtotal ON quotation_details(implant_subtotal);
CREATE INDEX idx_quotations_implant_total_amount ON quotations(implant_total_amount);
```

## 代码实现

### 模型层 (app/models/quotation.py)

#### QuotationDetail 模型新增
- `implant_subtotal` 字段
- `calculate_prices()` 方法增强，自动计算植入小计
- `formatted_implant_subtotal` 属性，返回格式化的植入小计

#### Quotation 模型新增
- `implant_total_amount` 字段
- `calculate_implant_total_amount()` 方法，计算植入总额合计
- `formatted_implant_total_amount` 属性，返回格式化的植入总额合计

### 事件监听器
- 产品明细变化时自动更新报价单的植入总额合计
- 与现有的产品签名更新机制集成

### 视图层 (app/views/quotation.py)
- 报价单创建、编辑、复制时自动计算植入小计
- 保存时自动更新植入总额合计

### 模板层 (app/templates/quotation/detail.html)
- 在报价单详情页面显示植入总额合计
- 位置：基本信息表格中，报价总额下方

## 使用示例

### 计算逻辑示例
```python
# 产品明细1：和源通信产品
detail1 = QuotationDetail(
    product_name="智能光纤远端直放站",
    brand="和源通信",
    market_price=22500.00,
    quantity=2
)
detail1.calculate_prices()
# detail1.implant_subtotal = 22500.00 * 2 = 45000.00

# 产品明细2：非和源通信产品
detail2 = QuotationDetail(
    product_name="其他产品",
    brand="其他品牌",
    market_price=10000.00,
    quantity=3
)
detail2.calculate_prices()
# detail2.implant_subtotal = 0.00

# 报价单植入总额合计
quotation.calculate_implant_total_amount()
# quotation.implant_total_amount = 45000.00 + 0.00 = 45000.00
```

## 数据迁移

### 迁移脚本
执行 `migrations/add_implant_fields.sql` 完成数据库结构升级和历史数据更新。

### 迁移结果
- 成功更新 3,102 个产品明细记录
- 成功更新 254 个报价单记录
- 和源通信产品占比：92.1%
- 总植入金额：151,122,090.00 元

## 测试验证

### 测试脚本
运行 `test_implant_calculation.py` 验证功能正确性：

```bash
python test_implant_calculation.py
```

### 测试结果
- ✅ 和源通信产品植入小计计算正确
- ✅ 非和源通信产品植入小计为0
- ✅ 报价单植入总额合计计算正确
- ✅ 数据库迁移成功

## 注意事项

1. **品牌匹配**: 植入小计的计算严格基于品牌字段是否等于"和源通信"
2. **价格基准**: 使用市场价（零售价格）而非折扣后的单价进行计算
3. **自动更新**: 产品明细变化时会自动触发植入总额合计的重新计算
4. **前端隐藏**: 植入小计字段不在前端表格中显示，仅用于后台统计
5. **权限控制**: 植入总额合计的显示遵循现有的权限控制机制

## 维护建议

1. 定期检查和源通信品牌名称的一致性
2. 监控植入金额占比的变化趋势
3. 如需修改品牌匹配规则，需要同时更新计算逻辑和历史数据 