# 报价单折扣率和单价显示问题修复

## 问题描述
报价单在调整了折扣率和单价后，保存后在详情页汇总折扣率还是100不变，进入编辑后也没有将修改后的内容出现在单价位置。

## 问题分析
经过代码检查发现两个主要问题：

### 1. 详情页汇总折扣率缺失
- 详情页面没有显示汇总折扣率字段
- 用户无法看到整体的折扣情况

### 2. 编辑页面数据显示错误
- 编辑页面的HTML模板中，折扣率字段硬编码为`value="100.0"`
- 单价字段没有显示数据库中的实际值
- JavaScript初始化时会重新计算价格，覆盖了数据库中的正确值

## 修复方案

### 1. 详情页面添加汇总折扣率显示

#### 文件：`app/templates/quotation/detail.html`
在报价总额后面添加汇总折扣率显示：

```html
<tr>
    <th class="bg-light">汇总折扣率</th>
    <td class="fw-bold">
        {% set total_market_value = 0 %}
        {% set total_discounted_value = 0 %}
        {% for detail in quotation.details %}
            {% set total_market_value = total_market_value + (detail.market_price * detail.quantity) %}
            {% set total_discounted_value = total_discounted_value + detail.total_price %}
        {% endfor %}
        {% if total_market_value > 0 %}
            {% set overall_discount_rate = (total_discounted_value / total_market_value * 100) %}
            {{ "%.1f"|format(overall_discount_rate) }}%
        {% else %}
            100.0%
        {% endif %}
    </td>
</tr>
```

**说明**：
- 计算所有产品的总市场价值和总折扣后价值
- 通过比例计算整体折扣率
- 显示保留1位小数的折扣率百分比

### 2. 编辑页面数据显示修复

#### 文件：`app/templates/quotation/edit.html`

**问题1修复**：折扣率字段显示正确值
```html
<!-- 修改前 -->
<input type="number" class="form-control discount-rate" name="discount_rate[]" value="100.0" min="0" step="0.1" max="1000" required>

<!-- 修改后 -->
<input type="number" class="form-control discount-rate" name="discount_rate[]" value="{{ '%.1f'|format(item.discount * 100) }}" min="0" step="0.1" max="1000" required>
```

**问题2修复**：单价字段显示正确值
```html
<!-- 修改前 -->
<input type="text" class="form-control discounted-price" name="discounted_price[]" placeholder="输入单价">

<!-- 修改后 -->
<input type="text" class="form-control discounted-price" name="discounted_price[]" value="{{ '%.2f'|format(item.unit_price) }}" placeholder="输入单价">
```

**问题3修复**：防止JavaScript重新计算覆盖数据库值
```javascript
// 修改前：初始化时会重新计算价格
calculateRowPrices($newRow);

// 修改后：初始化时保持数据库中的原始值
// 初始化时不重新计算价格，保持数据库中的原始值
// calculateRowPrices($newRow);
```

## 修复效果

### 1. 详情页面改进
- ✅ 新增汇总折扣率显示，用户可以看到整体折扣情况
- ✅ 折扣率计算准确，反映实际的价格折扣

### 2. 编辑页面改进
- ✅ 折扣率字段正确显示数据库中保存的实际折扣率
- ✅ 单价字段正确显示数据库中保存的实际单价
- ✅ 编辑时数据加载正确，不会被JavaScript重新计算覆盖
- ✅ 用户修改折扣率或单价时，相互计算逻辑正常工作

## 技术说明

### 数据流程
1. **保存时**：后端正确计算并保存 `discount`（小数形式）和 `unit_price`
2. **详情页显示**：直接显示数据库中的值，并计算汇总折扣率
3. **编辑页加载**：使用模板语法显示数据库中的实际值
4. **编辑页交互**：JavaScript负责用户交互时的实时计算

### 数据格式
- **数据库存储**：`discount` 字段存储小数形式（如0.85表示85%折扣）
- **前端显示**：转换为百分比形式显示（如85.0%）
- **计算逻辑**：确保前后端计算一致性

## 测试验证
1. 创建新报价单，设置不同的折扣率和单价
2. 保存后查看详情页的汇总折扣率是否正确
3. 进入编辑页面，确认折扣率和单价显示正确的数据库值
4. 修改折扣率，确认单价自动更新
5. 修改单价，确认折扣率自动更新

## 注意事项
- 修复保持了原有的功能逻辑不变
- 汇总折扣率计算考虑了数量因素
- 编辑页面的用户交互体验保持一致
- 数据保存逻辑没有修改，只修复了显示问题 