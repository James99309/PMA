# 组件和UI规范

## 📄 页面结构标准化规范

项目中所有页面必须遵循统一的页面结构模式，以确保用户体验的一致性和代码的可维护性。

### **1. 主要功能页面结构**
适用于：列表页面、详情页面、编辑页面、重要功能页面

```html
{% extends "base.html" %}
{% from 'macros/ui_helpers.html' import render_button, render_confirm_cancel %}

{% block title %}{{ _('页面标题') }}{% endblock %}

{% block content %}
<div class="container-fluid page-with-fixed-nav">
    <!-- 标准化页面头部区域：标题与操作按钮在同一行 -->
    <div class="page-header-with-actions mb-4">
        <div class="row align-items-center">
            <div class="col-auto">
                <h1 class="page-title mb-0">{{ _('页面标题') }}</h1>
            </div>
            <div class="col text-end">
                <!-- 操作按钮组 -->
                <div class="btn-toolbar justify-content-end" role="toolbar">
                    {{ render_button(_('返回'), href=url_for('module.list'), color='secondary') }}
                    {{ render_button(_('主要操作'), href=url_for('module.action'), color='primary') }}
                </div>
            </div>
        </div>
    </div>

    <!-- 页面主体内容 -->
    <div class="row">
        <div class="col-md-12">
            <!-- 页面内容 -->
        </div>
    </div>
</div>
{% endblock %}
```

### **2. 简单表单页面结构**
适用于：添加/编辑联系人、简单配置页面、轻量级功能页面

```html
{% extends "base.html" %}
{% from 'macros/ui_helpers.html' import render_button, render_confirm_cancel %}

{% block title %}{{ _('页面标题') }}{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h4>{{ _('页面标题') }}</h4>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        
                        <!-- 表单字段 -->
                        
                        <!-- 标准化表单提交按钮 -->
                        <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                            {{ render_confirm_cancel(
                                confirm_text=_('保存'),
                                cancel_text=_('取消'),
                                cancel_href=url_for('module.list'),
                                confirm_type='submit'
                            ) }}
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## 🔘 按钮组件使用规范

### **1. 页面头部操作按钮**
- **必须使用**：`render_button()` 组件
- **容器要求**：`btn-toolbar justify-content-end`

```html
<div class="btn-toolbar justify-content-end" role="toolbar">
    {{ render_button(
        text=_('返回列表'),
        href=url_for('module.list'),
        color='secondary',
        icon='fas fa-arrow-left'
    ) }}
    {{ render_button(
        text=_('编辑'),
        href=url_for('module.edit', id=item.id),
        color='primary',
        icon='fas fa-edit'
    ) }}
</div>
```

### **2. 表单提交按钮**
- **必须使用**：`render_confirm_cancel()` 组件
- **容器要求**：`d-grid gap-2 d-md-flex justify-content-md-end`

```html
<div class="d-grid gap-2 d-md-flex justify-content-md-end">
    {{ render_confirm_cancel(
        confirm_text=_('保存'),
        cancel_text=_('取消'),
        cancel_href=url_for('module.list'),
        confirm_color='primary',
        cancel_color='secondary',
        confirm_type='submit'  # 或 'button' 用于 JavaScript 处理
    ) }}
</div>
```

## 🔍 筛选搜索组件

### **统一配置格式**
- **必须使用**：`render_filter_search_form(filter_config)`

```python
filter_config = {
    'action_url': url_for('blueprint.route'),
    'form_id': 'uniqueFormId',
    'reset_url': url_for('blueprint.route'),
    
    'search_field': {
        'name': 'search',
        'label': '搜索',
        'placeholder': '具体搜索提示',
        'value': search,
        'col_width': 4
    },
    
    'filter_fields': [
        {
            'name': 'field_name',
            'label': '中文标签',
            'all_option_text': '全部选项',
            'current_value': current_value,
            'col_width': 3,
            'options': [
                {'value': 'key', 'label': '中文显示', 'translate': True}
            ]
        }
    ],
    
    'search_button_text': '搜索',
    'reset_button_text': '重置'
}
```

### **JavaScript 初始化**

#### **传统模式（页面刷新）**
```javascript
const configName = {
    form_id: 'formId',
    search_field_id: 'search',
    realtime_search: false,
    auto_submit: true,              // 启用自动筛选
    dynamic_reset_button: true,     // 启用动态重置按钮（必须）
    adaptive_width: true,           // 启用自适应宽度（默认开启）
    adaptive_button_layout: true,   // 启用自适应按钮布局（默认开启）
    search_delay: 300,
    filter_fields: [
        { name: 'field1' },
        { name: 'field2' }
    ]
};

setupFilterSearch(configName);
```

#### **AJAX模式（推荐）**
```javascript
const configName = {
    form_id: 'formId',
    search_field_id: 'search',
    auto_submit: true,
    ajax_mode: true,                      // 启用AJAX模式
    ajax_endpoint: '/api/module/filter',  // AJAX筛选端点
    ajax_target: '#tableBody',            // 更新目标元素选择器
    ajax_columns: 8,                      // 表格列数（用于加载状态显示）
    dynamic_reset_button: true,
    adaptive_width: true,
    adaptive_button_layout: true,
    filter_fields: [
        { name: 'field1' },
        { name: 'field2' }
    ]
};

// 设置全局配置供重置按钮使用
window.filterSearchConfig = configName;
setupFilterSearch(configName);
```

## 🗂️ 通用列表组件系统

### **系统架构**
通用列表组件系统为所有列表页面提供标准化的UI和交互功能，包括：
- **统计卡片** - 页面顶部的数据统计展示
- **筛选搜索** - 与现有筛选组件集成
- **数据表格** - 标准化的表格渲染
- **AJAX支持** - 无页面刷新的数据加载

### **使用方法**

#### **完整列表页面（推荐）**
使用 `render_data_list()` 宏渲染完整的列表页面：

```python
# 后端路由配置
list_config = {
    'module_name': 'order',
    'title': '订单列表',
    'ajax_mode': True,  # 启用AJAX模式
    
    # 统计卡片配置
    'stats': {
        'cards': [
            {
                'id': 'total',
                'title': '全部订单',
                'icon': 'fas fa-list-alt',
                'value': total_count,
                'amount': total_amount,
                'unit': '单',
                'amount_unit': '万元',
                'color': 'primary',
                'clickable': True,
                'click_params': {}  # 点击时清空筛选
            }
        ]
    },
    
    # 筛选配置（复用现有筛选组件）
    'filter': filter_config,
    
    # 表格配置
    'table': {
        'ajax_target': 'orderTableBody',
        'title': '订单列表',
        'icon': 'fas fa-table',
        'columns': [
            {
                'key': 'order_number',
                'label': '订单号',
                'type': 'link',
                'url_template': '/inventory/order/{id}',
                'width': '140px'
            },
            {
                'key': 'total_amount',
                'label': '总金额',
                'type': 'number',
                'format': 'wan',  # 万元格式
                'align': 'end',
                'width': '100px'
            },
            {
                'key': 'status',
                'label': '审批状态',
                'type': 'badge',
                'render': 'render_order_status_badge',  # 使用现有徽章宏
                'width': '100px'
            }
        ]
    }
}
```

### **配置规范**

#### **统计卡片配置**
```python
stats_config = {
    'cards': [
        {
            'id': 'card_id',           # 卡片ID（必需）
            'title': '卡片标题',        # 显示标题（必需）
            'icon': 'fas fa-icon',     # 图标类名（必需）
            'value': 100,              # 主要数值（必需）
            'unit': '单位',            # 数值单位（必需）
            'amount': 50000,           # 金额数值（可选）
            'amount_unit': '万元',      # 金额单位（可选）
            'color': 'primary',        # 颜色主题（必需）
            'clickable': True,         # 是否可点击（可选）
            'click_params': {          # 点击筛选参数（可选）
                'status': 'pending'
            }
        }
    ]
}
```

#### **数据类型和格式**
- **text**: 普通文本（默认）
- **badge**: 徽章显示
- **link**: 链接显示
- **number**: 数字显示
  - `format: 'currency'` - 货币格式 ¥1,234.56
  - `format: 'wan'` - 万元格式 12.34万
- **date**: 日期显示
  - `format: '%Y-%m-%d %H:%M'` - 自定义日期格式

## 📢 提示信息组件规范

### **统一提示组件 - showTopNotification()**

项目采用**统一的顶部通知组件**来处理所有提示信息，提供一致的用户体验。

#### **组件位置和引入**
- **模板宏**: `app/templates/macros/ui_helpers.html:render_top_notification()`
- **在页面中引入**:
```html
<!-- 在页面顶部添加提示容器 -->
{{ render_top_notification() }}
```

#### **JavaScript 使用方法**
```javascript
/**
 * 统一提示函数
 * @param {string} message - 主要消息内容
 * @param {string} type - 提示类型: 'success', 'error', 'warning', 'info'
 * @param {number} duration - 自动隐藏延迟（毫秒），默认3000，设为0则不自动隐藏
 * @param {string} containerId - 容器ID，默认'topNotification'
 * @param {Array} conditions - 条件检查列表（可选）
 */
showTopNotification(message, type, duration, containerId, conditions)

// 基本用法示例
showTopNotification('操作成功完成', 'success');
showTopNotification('请检查输入信息', 'warning', 5000);
showTopNotification('服务器连接失败', 'error', 0); // 不自动隐藏

// 带条件检查的用法
showTopNotification('验证结果', 'warning', 0, 'topNotification', [
    {text: '用户名格式正确', passed: true},
    {text: '密码长度不足', passed: false}
]);
```

#### **支持的提示类型**
| 类型 | 描述 | 颜色方案 | 图标 |
|------|------|---------|------|
| `success` | 成功操作 | 绿色渐变 + 左边框 | fa-check-circle |
| `error` | 错误信息 | 红色渐变 + 左边框 | fa-exclamation-circle |
| `warning` | 警告提示 | 黄色渐变 + 左边框 | fa-exclamation-triangle |
| `info` | 一般信息 | 蓝色渐变 + 左边框 | fa-info-circle |

#### **高级功能**

**1. 条件检查显示**
```javascript
const validationResult = {
    conditions: [
        {text: '文件格式正确', passed: true},
        {text: '文件大小超限', passed: false},
        {text: '权限验证通过', passed: true}
    ]
};

showTopNotification('文件上传验证', 'warning', 0, 'topNotification', validationResult.conditions);
```

**2. 向后兼容支持**
为了兼容现有代码，提供了`showStandardAlert`的别名：
```javascript
// 旧的调用方式仍然有效
showStandardAlert('success', '操作成功', [], null, 3000);

// 会自动转换为
showTopNotification('操作成功', 'success', 3000, 'topNotification', []);
```

#### **设计特性**
- ✅ **固定顶部位置** - 不影响页面布局
- ✅ **渐变背景设计** - 视觉层次丰富
- ✅ **左边框强调** - 清晰的状态指示
- ✅ **条件检查列表** - 支持复杂验证反馈
- ✅ **响应式设计** - 移动端友好
- ✅ **滑动动画** - 流畅的显示/隐藏效果
- ✅ **自动隐藏** - 可配置的自动消失时间

#### **使用规范**
1. **必须使用统一组件** - 禁止直接编写提示框HTML
2. **消息内容** - 支持HTML标签和换行（\n会转换为<br>）
3. **时长建议**:
   - 成功提示：2-3秒
   - 警告信息：5-8秒或不自动隐藏
   - 错误信息：不自动隐藏（设为0）
   - 一般信息：3-5秒

#### **禁用的组件**
❌ **已移除**: `showStandardAlert()` - 请使用 `showTopNotification()`  
❌ **已移除**: `render_animated_alert_script()` - 功能已合并

## 💬 确认对话框组件规范

### **标准确认对话框 - render_confirm_dialog()**

项目使用**统一的确认对话框组件**处理所有需要用户确认的操作，提供一致的视觉设计和交互体验。

#### **组件位置和引入**
- **模板宏**: `app/templates/macros/ui_helpers.html:render_confirm_dialog()`
- **在页面中引入**:
```html
<!-- 在页面底部添加对话框容器 -->
{{ render_confirm_dialog('uniqueDialogId') }}
```

#### **设计特性**
- ✅ **标准大小** - 固定400px宽度（移动端95%宽度）
- ✅ **圆弧形角** - 12px圆角设计
- ✅ **淡灰色背景** - #f8f9fa主体背景，#ffffff按钮区域背景
- ✅ **底部右侧按钮** - 使用统一按钮组件，右对齐布局
- ✅ **左对齐消息** - 消息内容左对齐显示
- ✅ **毛玻璃效果** - 背景模糊遮罩层
- ✅ **动画效果** - 淡入淡出和缩放动画
- ✅ **响应式设计** - 移动端自适应布局

#### **JavaScript 使用方法**

**1. 基本确认对话框**
```javascript
/**
 * 显示标准确认对话框
 * @param {Object} options - 配置选项
 * @param {string} options.title - 对话框标题
 * @param {string} options.message - 对话框消息内容（支持HTML和\n换行）
 * @param {string} options.type - 对话框类型: 'danger', 'warning', 'info', 'success'
 * @param {string} options.confirmText - 确认按钮文本，默认'确认'
 * @param {string} options.cancelText - 取消按钮文本，默认'取消'
 * @param {Function} options.onConfirm - 确认回调函数
 * @param {Function} options.onCancel - 取消回调函数
 * @param {string} options.dialogId - 对话框ID，必须与页面中的ID一致
 */
showConfirmDialog({
    title: '确认操作',
    message: '确定要执行此操作吗？',
    type: 'danger',
    dialogId: 'myConfirmDialog',
    onConfirm: function() {
        // 确认操作的代码
        console.log('用户确认了操作');
    },
    onCancel: function() {
        // 取消操作的代码（可选）
        console.log('用户取消了操作');
    }
});
```

**2. 删除确认对话框（预设）**
```javascript
/**
 * 删除确认对话框 - 常用的预设
 * @param {Object} options - 配置选项
 */
showDeleteConfirm({
    title: '确认删除报销单',
    message: '确定要删除这个报销单吗？此操作不可恢复。\n\n报销单号：EX-2024-001',
    dialogId: 'deleteDialog',
    onConfirm: function() {
        // 执行删除操作
        fetch('/api/delete', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showTopNotification('删除成功', 'success');
                } else {
                    showTopNotification(data.message, 'error');
                }
            });
    }
});
```

#### **支持的对话框类型**
| 类型 | 描述 | 图标颜色 | 图标 | 默认按钮颜色 |
|------|------|---------|------|-------------|
| `danger` | 危险操作 | 红色 #dc3545 | fa-exclamation-triangle | btn-danger |
| `warning` | 警告提示 | 黄色 #ffc107 | fa-exclamation-circle | btn-warning |
| `info` | 信息确认 | 蓝色 #17a2b8 | fa-info-circle | btn-primary |
| `success` | 成功确认 | 绿色 #28a745 | fa-check-circle | btn-primary |

#### **实际使用示例**

**示例1：删除操作确认**
```html
<!-- 模板中添加对话框容器 -->
{{ render_confirm_dialog('expenseDeleteDialog') }}

<!-- 删除按钮 -->
{{ render_button('删除', None, color='danger', type='button', attrs='onclick="deleteExpense(' ~ expense.id ~ ')"') }}
```

```javascript
// JavaScript删除函数
function deleteExpense(expenseId) {
    showDeleteConfirm({
        title: '确认删除报销单',
        message: `确定要删除这个报销单吗？此操作不可恢复。\n\n报销单号：${expenseNumber}`,
        dialogId: 'expenseDeleteDialog',
        onConfirm: function() {
            // 执行删除API调用
            fetch(`/expense/${expenseId}/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showTopNotification(data.message, 'success');
                    setTimeout(() => window.location.href = data.redirect_url, 1500);
                } else {
                    showTopNotification(data.message, 'error');
                }
            })
            .catch(error => {
                showTopNotification('删除失败，请重试', 'error');
            });
        }
    });
}
```

#### **高级功能**

**1. 手动控制对话框**
```javascript
// 手动隐藏对话框
hideConfirmDialog('dialogId');

// 支持ESC键关闭
// 支持点击遮罩层关闭
// 自动管理事件监听器
```

**2. 多行消息支持**
```javascript
showConfirmDialog({
    title: '批量操作确认',
    message: '即将执行以下操作：\n\n• 删除3个报销单\n• 更新2个项目状态\n• 发送5封通知邮件\n\n确定继续吗？',
    type: 'warning'
});
```

#### **使用规范**
1. **必须使用统一组件** - 禁止直接编写对话框HTML或使用Bootstrap模态框
2. **唯一ID要求** - 每个页面的对话框必须有唯一的dialogId
3. **消息内容** - 支持HTML标签，`\n`会自动转换为`<br>`
4. **回调函数** - onConfirm和onCancel都是可选的
5. **类型选择**:
   - 删除操作：使用`danger`类型
   - 重要操作：使用`warning`类型
   - 一般确认：使用`info`类型
   - 成功确认：使用`success`类型

#### **与其他组件集成**
- ✅ **配合顶部通知** - 操作结果使用`showTopNotification()`显示
- ✅ **配合按钮组件** - 触发按钮使用`render_button()`
- ✅ **响应式布局** - 移动端自动调整为全屏友好布局
- ✅ **无障碍支持** - 键盘导航和屏幕阅读器友好

#### **禁用的组件**
❌ **禁止使用**: Bootstrap模态框 - 请使用标准确认对话框  
❌ **禁止使用**: 原生alert/confirm - 用户体验不一致  
❌ **禁止使用**: 自定义对话框HTML - 违反组件化原则

## 🏷️ 徽章组件规则

### **设计原则**
- **统一风格**：所有徽章使用自定义样式，不使用Bootstrap默认徽章
- **视觉一致性**：胶囊形状、半透明背景、带边框设计
- **低对比度**：使用CSS变量控制透明度，确保不喧宾夺主

### **必须使用的通用徽章组件**

| 组件名称 | 用途 | 使用示例 |
|---------|-----|---------|
| `render_order_status_badge` | 订单状态 | `{{ render_order_status_badge(order.status) }}` |
| `render_inventory_status_badge` | 库存状态 | `{{ render_inventory_status_badge(order.inventory_status) }}` |
| `render_settlement_status_badge` | 结算状态 | `{{ render_settlement_status_badge(settlement.status) }}` |
| `render_project_stage` | 项目阶段 | `{{ render_project_stage(project.current_stage) }}` |
| `render_quotation_number` | 报价单编号 | `{{ render_quotation_number(quotation.number) }}` |
| `render_owner` | 拥有人/用户 | `{{ render_owner(user_object) }}` |
| `render_product_type_badge` | 产品类型 | `{{ render_product_type_badge(product.type) }}` |
| `render_product_status_badge` | 产品状态 | `{{ render_product_status_badge(product.status) }}` |
| `render_customer_status_badge` | 客户状态 | `{{ render_customer_status_badge(customer.status) }}` |

### **使用规范**
1. **禁止直接编写徽章HTML**：必须使用已定义的宏
2. **禁止使用Bootstrap徽章类**：如 `bg-primary`、`bg-success` 等
3. **新徽章类型**：需在 `ui_helpers.html` 中创建专门的宏
4. **颜色映射**：在宏内部定义，不在模板中硬编码
5. **国际化支持**：徽章文本必须支持中英文切换

### **拥有人徽章组件详细规则 (render_owner)**

**样式效果**：
- **厂商用户**：蓝色渐变 + 胶囊造型徽章 (`badge-user vendor rounded-pill`)
- **普通用户**：灰色渐变 + 方形造型徽章 (`badge-user regular`)
- **字符串参数**：灰色渐变 + 方形造型徽章 (`badge-user regular`)

**正确使用方式**：
```python
# 后端查询 - 获取完整User对象
query = db.session.query(
    SomeModel.id,
    User,  # 完整的User对象，不是User.username等字段
    # ... 其他字段
).join(User, SomeModel.user_id == User.id)

# 数据格式化 - 传递完整User对象
formatted_row = SimpleNamespace(
    id=row[0],
    owner=row[1],  # 传递完整的User对象
    # ... 其他字段
)
```

```html
<!-- 模板使用 - 传入完整User对象 -->
<td>{{ render_owner(row.owner) }}</td>
```

## 📏 CSS 类名标准

### **必需的 CSS 类**
- `page-with-fixed-nav` - 主要功能页面的根容器
- `page-header-with-actions` - 页面头部区域
- `page-title` - 页面标题
- `btn-toolbar justify-content-end` - 操作按钮容器
- `d-grid gap-2 d-md-flex justify-content-md-end` - 表单按钮容器

### **徽章组件CSS类命名规范**
- **订单相关**：`order-status-{status}`
- **库存相关**：`inventory-status-{status}`
- **结算相关**：`settlement-status-{status}`
- **项目相关**：`project-stage-{stage}`
- **产品相关**：`product-type-{type}`、`product-status-{status}`
- **用户相关**：`badge-user vendor`、`badge-user regular`
- **通用状态**：`badge-muted`（未设置/无数据）

## 🎨 前端交互规则

### **动态元素控制**
- **重置按钮**：默认隐藏（`display: none`），JavaScript 控制显示
- **加载状态**：统一使用 `.loading` 类
- **自动筛选**：下拉框变化时自动提交，搜索框需点击搜索按钮

### **自适应功能**

#### **自适应宽度功能**
- **自动开启**：`adaptive_width: true`（默认启用）
- **响应式调整**：根据标签文本长度和内容长度自动调整宽度
- **最小宽度**：120px（移动端自动100%宽度）
- **最大宽度**：300px（可通过CSS自定义）
- **语言切换**：自动检测语言变化并重新调整宽度

#### **自适应按钮布局功能**
- **自动开启**：`adaptive_button_layout: true`（默认启用）
- **智能排列**：空间充足时按钮在右侧，空间不足时换行到下方
- **响应式切换**：自动检测可用空间并调整布局
- **桌面端策略**：优先保持按钮在筛选器同一行的右侧
- **移动端策略**：自动换行到下方并右对齐

### **用户体验**
- **响应时间**：操作反馈在 200ms 内显示
- **加载提示**：超过 1 秒的操作必须显示加载状态
- **错误处理**：所有 AJAX 请求必须有错误处理

## 📁 文件结构规范

### **模板组织**
```
app/templates/
├── macros/
│   ├── ui_helpers.html      # UI 组件宏
│   └── filter_search.html   # 筛选搜索组件
├── inventory/
│   ├── order_list.html      # 订单列表
│   ├── settlement_list.html # 结算明细列表
│   └── settlement_order_list.html # 结算单列表
```

### **静态资源**
```
app/static/
├── css/
│   └── style.css           # 主样式文件
├── js/
│   ├── filter-search.js    # 筛选搜索 JS
│   └── data-list.js        # 通用列表组件 JS
```

### **组件文件结构**
```
通用列表组件系统
├── app/templates/macros/ui_helpers.html  # 列表UI宏
│   ├── render_data_list()               # 完整列表页面
│   ├── render_stats_cards()             # 统计卡片
│   ├── render_data_table()              # 数据表格
│   └── render_table_cell()              # 表格单元格
├── app/static/css/style.css             # 列表样式
│   ├── .data-list-container             # 列表容器样式
│   ├── .stats-card-*                    # 统计卡片样式
│   └── .data-list-table                 # 表格样式
└── app/static/js/data-list.js           # 列表交互功能
    ├── setupDataList()                  # 初始化函数
    ├── updateStatsFromAjax()             # 统计更新
    └── 与 filter-search.js 集成
```

## 🎯 最佳实践

### **页面结构选择指南**

| 页面类型 | 结构模式 | 示例页面 |
|---------|----------|----------|
| **数据列表页面** | 主要功能页面结构 | customer/list.html |
| **数据详情页面** | 主要功能页面结构 | customer/view.html |
| **数据编辑页面** | 主要功能页面结构 | customer/edit.html |
| **重要功能页面** | 主要功能页面结构 | customer/add.html, project/detail.html |
| **添加联系人** | 简单表单页面结构 | customer/add_contact.html |
| **编辑联系人** | 简单表单页面结构 | customer/edit_contact.html |
| **系统配置页面** | 简单表单页面结构 | admin/settings.html |

### **通用列表组件最佳实践**
1. **优先使用 `render_data_list()` 完整组件**
2. **统计卡片数量建议不超过4个（移动端友好）**
3. **表格列数建议不超过8列（避免横向滚动）**
4. **AJAX模式下必须实现统计数据同步更新**
5. **使用语义化的卡片ID和颜色主题**
6. **为所有数值字段配置合适的格式化**
7. **移动端测试响应式布局**