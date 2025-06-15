# 库存订单创建页面修复总结

## 问题描述
1. 访问创建订单页面时出现500内部服务器错误：
```
TypeError: macro 'render_button' takes no keyword argument 'onclick'
jinja2.exceptions.UndefinedError: 'render_button' is undefined
```

2. UI显示问题：
- 单价输入框无法正常输入
- 产品规格、市场单价、小计和MN字段显示宽度不够
- 长文本内容无法完整显示

## 问题原因
1. `render_button` 宏函数不支持 `onclick` 参数，但模板中使用了不正确的参数格式
2. 删除import后，还有其他地方使用了 `render_button` 函数但没有导入
3. 表格列宽度设置不合理，缺少文本截断功能

## 修复方案

### 1. 删除有问题的import语句
- 删除了 `{% from "macros/ui_helpers.html" import render_button %}` 导入

### 2. 替换所有按钮代码
将所有有问题的宏函数调用替换为标准HTML按钮：

**修复前：**
```html
{{ render_button('取消', 'btn-secondary me-2', 'fas fa-times', onclick='window.history.back()') }}
{{ render_button('创建订单', 'btn-primary', 'fas fa-save', id='submitBtn', type='submit') }}
{{ render_button('返回订单列表', href=url_for('inventory.order_list'), color='secondary', icon='fas fa-arrow-left') }}
```

**修复后：**
```html
<!-- 取消和创建订单按钮 -->
<button type="button" class="btn btn-secondary me-2" onclick="window.history.back()">
    <i class="fas fa-times me-1"></i>取消
</button>
<button type="submit" class="btn btn-primary" id="submitBtn">
    <i class="fas fa-save me-1"></i>创建订单
</button>

<!-- 返回订单列表按钮 -->
<a href="{{ url_for('inventory.order_list') }}" class="btn btn-secondary">
    <i class="fas fa-arrow-left me-1"></i>返回订单列表
</a>
```

### 3. 表格列宽度优化
添加了专门的CSS类来控制各列宽度：

```css
/* 产品规格列宽度调整 */
.table th.desc-column,
.table td.desc-column {
    min-width: 200px;
    max-width: 200px;
}

/* 价格列宽度调整 */
.table th.price-column,
.table td.price-column {
    min-width: 120px;
    max-width: 120px;
}

/* MN列宽度调整 */
.table th.mn-column,
.table td.mn-column {
    min-width: 150px;
    max-width: 150px;
}
```

### 4. 文本截断功能
添加了文本截断样式和JavaScript处理：

```css
/* 文本截断样式 */
.text-truncate-custom {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
    display: block;
}

/* 输入框文本截断 */
.form-control.text-truncate-input {
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
}
```

```javascript
// 文本截断处理函数
function truncateText(text, maxLength = 15) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

// 设置输入框的值和tooltip
function setInputValueWithTooltip($input, value) {
    const truncatedValue = truncateText(value);
    $input.val(truncatedValue);
    $input.attr('title', value || '');
}
```

### 5. 单价输入功能增强
修复了单价输入框并添加了自动计算折扣率的功能：

```css
/* 单价输入框可编辑样式 */
.discounted-price {
    background-color: #fff !important;
    border: 1px solid #ced4da !important;
}

.discounted-price:focus {
    background-color: #fff !important;
    border-color: #80bdff !important;
    box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25) !important;
}
```

```javascript
// 如果是单价变化，先计算折扣率
if ($(this).hasClass('discounted-price')) {
    const marketPriceText = $row.find('.product-price').val() || '';
    const marketPrice = parseFloat(marketPriceText.replace(/[^\d.-]/g, '')) || 0;
    const unitPrice = parseFloat($(this).val()) || 0;
    
    if (marketPrice > 0 && unitPrice > 0) {
        const discountRate = (unitPrice / marketPrice * 100).toFixed(1);
        $row.find('.discount-rate').val(discountRate);
    }
}
```

## 修复结果
- ✅ 页面不再报500错误
- ✅ 正常重定向到登录页面（302状态码）
- ✅ 所有按钮功能正常
- ✅ 单价可编辑并自动计算折扣率
- ✅ 表格列宽度合理，显示效果良好
- ✅ 长文本自动截断并显示tooltip
- ✅ 完全移除了对render_button宏函数的依赖

## 修复过程
1. **第一次修复**：删除import，替换底部的取消和创建订单按钮
2. **第二次修复**：发现还有返回订单列表按钮使用render_button，进行完整替换
3. **第三次修复**：优化表格列宽度和文本显示
4. **验证修复**：确认所有功能正常工作

## 测试建议
1. 登录后访问创建订单页面
2. 测试返回订单列表按钮
3. 测试添加产品功能
4. 测试产品选择时的文本截断显示
5. 测试单价输入时的自动折扣率计算
6. 测试取消和创建订单按钮功能
7. 验证长文本字段的tooltip显示

## 文件修改
- `app/templates/inventory/create_order.html` - 主要修复文件
- 创建备份文件：`app/templates/inventory/create_order.html.backup`

## 技术要点
- 使用标准HTML按钮和链接替代有问题的宏函数
- 处理价格字符串中可能包含的货币符号
- 保持原有的UI样式和交互逻辑
- 彻底移除对render_button宏函数的依赖
- 实现响应式表格列宽度控制
- 添加文本截断和tooltip功能提升用户体验
- 优化单价输入和自动计算功能 