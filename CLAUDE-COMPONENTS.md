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

### **详情列表组件 - render_detail_list()**

用于在详情页面中显示关联数据列表（如订单明细、关联产品等），采用客户端JavaScript渲染。

#### **组件位置和引入**
- **模板宏**: `app/templates/macros/ui_helpers.html:render_detail_list()`
- **在页面中引入**:
```html
{% from 'macros/ui_helpers.html' import render_detail_list %}
```

#### **基本使用**

```html
{{ render_detail_list(
    container_id='productRelationsList',
    title='关联产品配置',
    icon='fa-link',
    api_url=url_for('product_management.get_product_relations', product_id=product.id),
    columns=[
        {'key': 'product_name', 'label': _('产品名称'), 'width': '25%'},
        {'key': 'product_model', 'label': _('型号'), 'width': '20%'},
        {'key': 'product_mn', 'label': _('MN编号'), 'width': '20%'},
        {'key': 'relation_type_label', 'label': _('配置类型'), 'width': '15%', 'align': 'center', 'type': 'badge', 'render': 'render_relation_type_badge'},
        {'key': 'default_quantity', 'label': _('配置数量'), 'width': '10%', 'align': 'center'}
    ],
    actions=[
        {'type': 'delete', 'label': _('删除'), 'confirm': _('确认删除此关联产品？')}
    ],
    add_button_html=render_button(
        text=_('添加关联产品'),
        color='primary',
        size='sm',
        onclick='openAddModal()',
        type='button'
    ) if has_permission else '',
    empty_message=_('暂无数据'),
    show_actions=has_permission
) }}
```

#### **参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|-----|------|
| `container_id` | string | ✅ | 容器唯一ID |
| `title` | string | ✅ | 列表标题 |
| `icon` | string | ❌ | 标题图标（如 'fa-link'） |
| `api_url` | string | ✅ | 数据API地址 |
| `columns` | array | ✅ | 列配置数组 |
| `actions` | array | ❌ | 操作按钮配置 |
| `add_button_html` | string | ❌ | 添加按钮HTML |
| `empty_message` | string | ❌ | 空数据提示 |
| `show_actions` | boolean | ❌ | 是否显示操作列 |

#### **列配置详解**

```python
columns = [
    {
        'key': 'field_name',        # 数据字段名（必填）
        'label': '列标题',           # 显示标题（必填）
        'width': '20%',             # 列宽度（可选）
        'align': 'center',          # 对齐方式: left/center/right（可选，默认left）
        'type': 'badge',            # 数据类型: text/badge/link/number（可选）
        'render': 'render_xxx_badge' # 徽章渲染宏名（type='badge'时使用）
    }
]
```

#### **支持的数据类型**

**1. text（默认）**
```python
{'key': 'product_name', 'label': '产品名称', 'type': 'text'}
```

**2. badge（徽章）**
```python
# 使用自定义徽章宏
{'key': 'status', 'label': '状态', 'type': 'badge', 'render': 'render_order_status_badge'}

# 使用默认徽章（需要API返回 field_class 字段）
{'key': 'type_label', 'label': '类型', 'type': 'badge'}
# API需返回: {'type_label': '文本', 'type_label_class': 'badge-class-name'}
```

**3. link（链接）**
```python
{'key': 'order_number', 'label': '订单号', 'type': 'link', 'url_template': '/order/{id}'}
```

**4. number（数字）**
```python
{'key': 'amount', 'label': '金额', 'type': 'number', 'align': 'right'}
```

#### **操作按钮配置**

```python
actions = [
    {
        'type': 'edit',                    # 操作类型: edit/delete/custom
        'label': '编辑',                   # 按钮文本
        'onclick': 'editItem({id})'       # 点击事件（{id}会被替换为实际ID）
    },
    {
        'type': 'delete',
        'label': '删除',
        'confirm': '确认删除此项？'        # 删除确认提示
    }
]
```

#### **API数据格式要求**

后端API应返回以下格式：

```python
{
    'success': True,
    'data': [
        {
            'id': 1,                              # 必需：记录ID
            'product_name': '产品A',              # 各列数据
            'product_model': 'MODEL-001',
            'relation_type_label': '必选',        # 徽章显示文本
            'relation_type_label_class': 'badge relation-type-required rounded-pill',  # 徽章CSS类
            'default_quantity': 1
        },
        # ...更多记录
    ],
    'total': 10  # 可选：总记录数
}
```

#### **JavaScript刷新方法**

组件会自动注册刷新函数，可在外部调用：

```javascript
// 刷新列表数据
if (typeof window.refresh_productRelationsList === 'function') {
    window.refresh_productRelationsList();
}
```

刷新函数命名规则：`refresh_${container_id}`

#### **删除操作处理**

当配置了删除操作时，组件会自动调用：

```javascript
// 自动生成的删除函数
function delete_productRelationsList(itemId) {
    // 1. 显示确认对话框
    // 2. 调用删除API: /api/{module}/{id}
    // 3. 刷新列表
}
```

可通过在路由中实现对应的DELETE接口来处理删除请求。

#### **使用示例**

**完整示例：产品详情页的关联产品列表**

```html
<!-- 模板代码 -->
{% from 'macros/ui_helpers.html' import render_detail_list, render_button %}

<div class="row mb-4">
    <div class="col-md-12">
        {{ render_detail_list(
            container_id='productRelationsList',
            title='关联产品配置',
            icon='fa-link',
            api_url=url_for('product_management.get_product_relations', product_id=product.id),
            columns=[
                {'key': 'product_name', 'label': _('产品名称'), 'width': '25%'},
                {'key': 'product_model', 'label': _('型号'), 'width': '20%'},
                {'key': 'product_mn', 'label': _('MN编号'), 'width': '20%'},
                {'key': 'relation_type_label', 'label': _('配置类型'), 'width': '15%', 'align': 'center', 'type': 'badge', 'render': 'render_relation_type_badge'},
                {'key': 'default_quantity', 'label': _('配置数量'), 'width': '10%', 'align': 'center'}
            ],
            actions=[
                {'type': 'delete', 'label': _('删除'), 'confirm': _('确认删除此关联产品？')}
            ],
            add_button_html=render_button(
                text=_('添加关联产品'),
                color='primary',
                size='sm',
                onclick='openAddRelationModal()',
                type='button'
            ) if current_user.role in ['admin', 'product_manager'] else '',
            empty_message=_('暂无关联产品配置'),
            show_actions=current_user.role in ['admin', 'product_manager']
        ) }}
    </div>
</div>
```

```python
# 后端API代码
@product_management_bp.route('/api/product/<int:product_id>/relations', methods=['GET'])
@login_required
@permission_required('product', 'view')
def get_product_relations(product_id):
    try:
        relations = ProductRelation.query.filter_by(
            main_product_id=product_id,
            is_active=True
        ).all()

        relations_data = []
        for relation in relations:
            relations_data.append({
                'id': relation.id,
                'related_product_id': relation.related_product_id,
                'product_name': relation.related_product.product_name,
                'product_model': relation.related_product.model,
                'product_mn': relation.related_product.product_mn,
                'relation_type': relation.relation_type,
                'relation_type_label': ProductRelation.get_relation_type_label(relation.relation_type),
                'relation_type_label_class': 'badge relation-type-required rounded-pill',  # 自定义CSS类
                'default_quantity': relation.default_quantity
            })

        return jsonify({'success': True, 'data': relations_data, 'total': len(relations_data)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
```

#### **注意事项**

1. **客户端渲染** - 组件使用JavaScript渲染，不支持服务器端渲染
2. **徽章渲染** - 如使用自定义徽章宏，需确保宏已在ui_helpers.html中定义并注册
3. **权限控制** - 操作按钮和添加按钮应根据权限动态显示
4. **容器ID唯一** - 同一页面的多个列表必须使用不同的container_id
5. **API格式** - 必须返回`{success, data, total}`格式的JSON

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

---

### **自定义内容对话框 - render_custom_dialog()**

用于需要自定义复杂内容的对话框（如选择器、表单、多步骤操作等），提供与确认对话框相同的视觉风格，但支持灵活的内容区域。

#### **组件位置和引入**
- **模板宏**: `app/templates/macros/ui_helpers.html:render_custom_dialog()`
- **在页面中引入**:
```jinja2
{% from 'macros/ui_helpers.html' import render_custom_dialog %}

<!-- 使用caller块定义对话框内容 -->
{% call render_custom_dialog('myDialogId', '对话框标题', icon='fas fa-cog', size='xl') %}
    <!-- 自定义内容区域 -->
    <div class="row">
        <div class="col-md-12">
            <p>这里可以放置任意HTML内容</p>
        </div>
    </div>

    <!-- 底部操作按钮 -->
    <div class="custom-dialog-actions">
        {{ render_button('保存', type='button', color='primary', onclick='saveData()') }}
        {{ render_button('取消', type='button', color='secondary', onclick='closeCustomDialog("myDialogId")') }}
    </div>
{% endcall %}
```

#### **设计特性**
- ✅ **统一风格** - 与确认对话框相同的视觉设计（灰色背景 #f8f9fa，12px圆角，白色底部）
- ✅ **灵活尺寸** - 支持多种尺寸：sm(400px), md(600px), lg(800px), xl(1000px), full(95%)
- ✅ **自定义内容** - 通过caller块支持任意复杂的HTML内容
- ✅ **毛玻璃效果** - 背景模糊遮罩层
- ✅ **动画效果** - 淡入淡出和缩放动画
- ✅ **响应式设计** - 移动端自动适应

#### **参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| `dialog_id` | string | ✅ | - | 对话框唯一ID |
| `title` | string | ✅ | - | 对话框标题 |
| `icon` | string | ❌ | '' | 标题图标类名（如 'fas fa-link'） |
| `size` | string | ❌ | 'lg' | 对话框尺寸：'sm', 'md', 'lg', 'xl', 'full' |
| `show_close` | boolean | ❌ | true | 是否显示右上角关闭按钮 |

#### **JavaScript API**

**1. 显示对话框**
```javascript
/**
 * 显示自定义对话框
 * @param {string} dialogId - 对话框ID（必须与模板中定义的ID一致）
 */
showCustomDialog('myDialogId');
```

**2. 关闭对话框**
```javascript
/**
 * 关闭自定义对话框
 * @param {string} dialogId - 对话框ID
 */
closeCustomDialog('myDialogId');
```

**3. 扩展关闭行为**
```javascript
// 覆盖关闭函数以添加清理逻辑
const originalCloseCustomDialog = window.closeCustomDialog;
window.closeCustomDialog = function(dialogId) {
    if (dialogId === 'myDialogId') {
        // 执行清理操作
        clearFormData();
    }
    originalCloseCustomDialog(dialogId);
};
```

#### **对话框尺寸规格**

| 尺寸代码 | 宽度 | 适用场景 |
|---------|------|---------|
| `sm` | 400px | 简单表单、单一输入 |
| `md` | 600px | 中等表单、双列布局 |
| `lg` | 800px | 复杂表单、列表选择（默认） |
| `xl` | 1000px | 大型选择器、树状结构 |
| `full` | 95% | 复杂多栏布局、大数据表格 |

**移动端**: 所有尺寸在移动设备上自动调整为95%宽度

#### **使用示例**

**示例1：产品选择器对话框**

```jinja2
{% from 'macros/ui_helpers.html' import render_custom_dialog, render_button %}
{% from 'macros/product_tree_selector.html' import render_product_tree_selector %}

<!-- 对话框定义 -->
{% call render_custom_dialog('addRelationModal', _('添加关联产品'), icon='fas fa-link', size='xl') %}
    <!-- 产品树选择器 -->
    <div class="row">
        <div class="col-md-12">
            {{ render_product_tree_selector(
                container_id='relationProductSelector',
                api_url=url_for('product_management.get_product_tree'),
                selected_product_ids=[],
                show_badges=True,
                show_icons=False,
                exclude_product_ids=[product.id]
            ) }}
        </div>
    </div>

    <!-- 配置选项 -->
    <div class="row mt-3">
        <div class="col-md-6">
            <label class="form-label fw-bold">{{ _('配置类型') }}</label>
            <select class="form-select" id="relationType" name="relationType">
                <option value="required">{{ _('必选') }}</option>
                <option value="recommended">{{ _('推荐') }}</option>
            </select>
        </div>
    </div>

    <!-- 底部操作按钮 -->
    <div class="custom-dialog-actions">
        {{ render_button(
            text=_('保存'),
            type='button',
            color='primary',
            onclick='saveRelationProducts()'
        ) }}
        {{ render_button(
            text=_('取消'),
            type='button',
            color='secondary',
            onclick='closeCustomDialog("addRelationModal")'
        ) }}
    </div>
{% endcall %}
```

**JavaScript代码**:
```javascript
// 打开对话框
function openAddRelationModal() {
    // 初始化表单数据
    document.getElementById('relationType').value = 'required';

    // 显示对话框
    showCustomDialog('addRelationModal');
}

// 保存操作
function saveRelationProducts() {
    const selectedProducts = getSelectedProducts();
    const relationType = document.getElementById('relationType').value;

    // 执行保存API调用
    fetch('/api/save-relations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            products: selectedProducts,
            relation_type: relationType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeCustomDialog('addRelationModal');
            // 刷新列表
            if (typeof window.refresh_productRelationsList === 'function') {
                window.refresh_productRelationsList();
            }
        } else {
            alert(data.message);
        }
    });
}
```

**示例2：多步骤表单对话框**

```jinja2
{% call render_custom_dialog('multiStepForm', _('批量导入'), icon='fas fa-file-upload', size='lg') %}
    <!-- 步骤指示器 -->
    <div class="wizard-steps mb-4">
        <div class="step active" data-step="1">1. 上传文件</div>
        <div class="step" data-step="2">2. 数据验证</div>
        <div class="step" data-step="3">3. 确认导入</div>
    </div>

    <!-- 步骤内容 -->
    <div id="step1" class="wizard-content">
        <input type="file" class="form-control" id="uploadFile">
    </div>
    <div id="step2" class="wizard-content" style="display:none;">
        <div id="validationResults"></div>
    </div>
    <div id="step3" class="wizard-content" style="display:none;">
        <div id="importSummary"></div>
    </div>

    <!-- 底部按钮 -->
    <div class="custom-dialog-actions">
        <div id="stepButtons">
            {{ render_button('下一步', type='button', color='primary', onclick='nextStep()', attrs='id="nextBtn"') }}
            {{ render_button('上一步', type='button', color='secondary', onclick='prevStep()', attrs='id="prevBtn" style="display:none;"') }}
            {{ render_button('取消', type='button', color='secondary', onclick='closeCustomDialog("multiStepForm")') }}
        </div>
    </div>
{% endcall %}
```

#### **底部按钮区域样式**

对话框底部按钮区域使用 `.custom-dialog-actions` 类：

```html
<div class="custom-dialog-actions">
    <!-- 按钮从右到左依次排列 -->
    {{ render_button('主要操作', color='primary', ...) }}
    {{ render_button('次要操作', color='secondary', ...) }}
</div>
```

**样式特性**:
- ✅ 白色背景 (#ffffff)
- ✅ 右对齐按钮布局
- ✅ 按钮间距12px
- ✅ 与确认对话框风格一致

#### **与确认对话框的区别**

| 特性 | 确认对话框 | 自定义对话框 |
|-----|----------|------------|
| **用途** | 简单的确认/取消操作 | 复杂的表单、选择器、多步骤流程 |
| **内容** | 固定的标题+消息+按钮 | 自定义HTML内容（通过caller块） |
| **尺寸** | 固定400px | 可配置多种尺寸 |
| **API** | `showConfirmDialog()` | `showCustomDialog()` |
| **按钮** | 自动生成确认/取消按钮 | 需手动定义按钮 |
| **回调** | 通过参数传递 | 通过onclick事件 |

#### **使用规范**

1. **选择正确的组件**:
   - 简单确认操作 → 使用 `render_confirm_dialog()`
   - 复杂内容表单 → 使用 `render_custom_dialog()`

2. **唯一ID要求**: 每个对话框必须有唯一的dialog_id

3. **尺寸选择**:
   - 优先使用 `lg` 或 `xl` 确保内容不拥挤
   - 仅在内容确实简单时使用 `sm` 或 `md`

4. **按钮布局**:
   - 主要操作按钮放在左侧
   - 取消按钮放在右侧
   - 统一使用 `.custom-dialog-actions` 容器

5. **关闭清理**:
   - 关闭对话框时执行必要的清理操作
   - 重置表单状态
   - 移除临时数据

6. **移动端友好**:
   - 确保内容在小屏幕上可读
   - 避免过深的嵌套滚动

#### **常见使用场景**

- ✅ 产品/用户选择器（树状结构）
- ✅ 多字段表单输入
- ✅ 数据预览和编辑
- ✅ 多步骤向导流程
- ✅ 批量操作配置
- ✅ 文件上传和预览

#### **实际应用页面**

- `app/templates/product/detail.html` - 产品关联配置选择器
- 更多应用待补充...

---

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

## 🤝 共享功能组件规范

### **共享组件系统概述**

项目提供**统一的共享功能组件系统**，支持项目、客户等数据的用户共享功能。系统采用树状用户选择器，支持公司、部门、用户的层级结构显示和批量选择。

### **核心组件**

#### **主要组件宏**
- `render_sharing_section()` - 完整的共享设置区域
- `render_tree_user_selector()` - 树状用户选择器
- `SharingMixin` - 数据模型共享功能混入类
- `SharingService` - 共享服务类

#### **支持文件**
- `app/utils/sharing.py` - 共享功能后端服务
- `app/templates/macros/ui_helpers.html` - 共享组件模板
- CSS 样式集成在组件内部

### **使用方法**

#### **1. 数据模型配置**

**数据库字段要求**：
```python
# 模型中必须包含以下字段
class YourModel(db.Model, SharingMixin):
    # ... 其他字段
    share_enabled = db.Column(db.Boolean, default=False)      # 是否启用共享
    shared_with_users = db.Column(db.JSON, default=[])       # 共享用户ID列表
```

**混入类使用**：
```python
from app.utils.sharing import SharingMixin

class Project(db.Model, SharingMixin):
    # 自动获得以下属性和方法：
    # - shared_user_ids (属性)
    # - is_shared (属性)  
    # - is_shared_with_user(user_id)
    # - add_shared_user(user_id)
    # - remove_shared_user(user_id)
    # - set_shared_users(user_ids)
```

#### **2. 后端路由配置**

**基本配置**：
```python
from app.utils.sharing import SharingService, get_shareable_users_tree

@blueprint.route('/detail/<int:id>')
@login_required
@permission_required('module', 'view')
def detail(id):
    item = Model.query.get_or_404(id)
    
    # 权限检查
    can_edit_sharing = SharingService.can_edit_sharing_settings(
        current_user, item, 'model_type'
    )
    
    # 获取可共享用户树（仅在可以编辑时）
    shareable_users_tree = []
    if can_edit_sharing:
        shareable_users_tree = get_shareable_users_tree(current_user, 'model_type')
    
    return render_template('template.html',
                         item=item,
                         can_edit_sharing=can_edit_sharing,
                         shareable_users_tree=shareable_users_tree)
```

**共享更新路由**：
```python
@blueprint.route('/update_sharing/<int:id>', methods=['POST'])
@login_required
@permission_required('module', 'edit')
def update_sharing(id):
    item = Model.query.get_or_404(id)
    
    # 使用统一服务更新共享设置
    if SharingService.update_sharing_from_request(item, current_user, 'model_type'):
        try:
            db.session.commit()
            flash('共享设置保存成功', 'success')
        except Exception as e:
            db.session.rollback()
            flash('保存失败，请重试', 'danger')
    else:
        flash('没有权限或保存失败', 'danger')
    
    return redirect(url_for('module.detail', id=id))
```

#### **3. 模板中使用**

**导入组件**：
```html
{% from 'macros/ui_helpers.html' import render_sharing_section %}
```

**基本使用**：
```html
<!-- 在详情页面中添加共享设置区域 -->
{{ render_sharing_section(
    model_obj=project,                    # 数据对象
    model_type='project',                 # 模型类型
    current_user=current_user,            # 当前用户
    can_edit_sharing=can_edit_sharing,    # 编辑权限
    shareable_users_tree=shareable_users_tree  # 可共享用户树
) }}
```

**带自定义参数**：
```html
{{ render_sharing_section(
    model_obj=company,
    model_type='customer',
    current_user=current_user,
    action_url=url_for('customer.update_company_sharing', company_id=company.id),
    collapsed=False,                      # 默认展开
    can_edit_sharing=can_edit_sharing,
    shareable_users_tree=shareable_users_tree
) }}
```

### **组件参数说明**

#### **render_sharing_section() 参数**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `model_obj` | Model对象 | ✅ | 要共享的数据对象 |
| `model_type` | String | ✅ | 模型类型标识 ('project', 'customer') |
| `current_user` | User对象 | ✅ | 当前登录用户 |
| `action_url` | String | ❌ | 提交URL（默认当前页面） |
| `collapsed` | Boolean | ❌ | 是否默认收起 (默认True) |
| `can_edit_sharing` | Boolean | ❌ | 是否可编辑 (默认True) |
| `shareable_users_tree` | Array | ❌ | 可共享用户树数据 |

#### **get_shareable_users_tree() 返回格式**
```python
[
    {
        'id': 'company_1',
        'name': '公司A',
        'type': 'company',
        'selectable': True,
        'children': [
            {
                'id': 'dept_1',
                'name': '销售部',
                'type': 'department', 
                'selectable': True,
                'children': [
                    {
                        'id': 'user_1',
                        'name': '张三',
                        'type': 'user',
                        'user_id': 1,
                        'selectable': True
                    }
                ]
            },
            {
                'id': 'user_2',
                'name': '李四',     # 公司直属用户
                'type': 'user',
                'user_id': 2,
                'selectable': True
            }
        ]
    }
]
```

### **权限控制规范**

#### **权限等级**
1. **管理员权限**: `admin`, `product_manager`, `solution_manager`, `finance_director`
2. **拥有者权限**: 数据的 `owner_id` 等于当前用户ID
3. **特定权限**: 
   - 项目：`vendor_sales_manager_id` 等于当前用户ID
   - 客户：归属关系权限、商务助理部门权限

#### **权限检查方法**
```python
# 检查是否可以编辑共享设置
can_edit = SharingService.can_edit_sharing_settings(user, data_obj, model_type)

# 检查是否可以查看共享数据
can_view = SharingPermissionHelper.can_view_shared_data(user, data_obj)
```

### **用户筛选规则**

#### **管理员用户**
- 可以共享给系统内所有活跃用户
- 不受公司和部门限制

#### **普通用户**
- 只能共享给同公司用户
- 项目/报价单类型：优先业务相关用户（销售、产品、管理等角色）
- 其他类型：同公司所有用户

#### **用户活跃状态判断**
```python
# 活跃用户条件（二选一）
User.role == 'admin'        # 管理员总是活跃
User._is_active == True     # 其他用户根据状态字段
```

### **树状选择器特性**

#### **层级结构**
- **层级0**: 🏛️ 公司 (`padding-left: 8px`)
- **层级1**: 🏢 部门 和 👤 公司直属用户 (`padding-left: 28px`)
- **层级2**: 👤 部门下用户 (`padding-left: 48px`)

#### **交互功能**
- ✅ **级联选择**: 选中父级时自动选中所有子级
- ✅ **状态显示**: 支持全选、半选、未选三种状态
- ✅ **展开收起**: 支持点击展开/收起子级
- ✅ **服务器端状态**: 页面加载时根据保存的数据正确显示状态
- ✅ **排除当前用户**: 自动排除操作者本身

#### **状态映射规则**
- **全选中**: 父级下所有用户都被选中 → 父级显示为选中 (`checked=true`)
- **半选中**: 父级下部分用户被选中 → 父级显示为半选 (`indeterminate=true`) 
- **未选中**: 父级下无用户被选中 → 父级显示为未选 (`checked=false`)

### **AJAX 数据处理**

#### **表单数据格式**
```javascript
// JavaScript 获取选中用户ID
const selectedUserIds = getSelectedUserIds('userTree_123');
// 返回: ['12', '29', '35']

// 表单提交数据
shared_with_users: ['12', '29', '35']  // 数组格式
// 或
shared_with_users: '12,29,35'          // 逗号分隔字符串（自动解析）
```

#### **后端数据处理**
```python
# SharingService.update_sharing_from_request() 自动处理
# 支持数组格式: ['12', '29', '35']  
# 支持逗号分隔: ['12,29,35'] -> ['12', '29', '35']
```

### **样式定制**

#### **主要CSS类**
```css
/* 树状选择器容器 */
.tree-user-selector {
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    max-height: 300px;
    overflow-y: auto;
}

/* 层级缩进 */
.company-node .tree-node-content { padding-left: 8px; }
.department-node .tree-node-content { padding-left: 28px; }
.user-node .tree-node-content { padding-left: 48px; }
.company-direct-user .tree-node-content { padding-left: 28px; }

/* 文本大小 */
.tree-text { font-size: 0.875rem; }
```

### **最佳实践**

#### **1. 数据模型设计**
```python
class YourModel(db.Model, SharingMixin):
    # 必需字段
    share_enabled = db.Column(db.Boolean, default=False)
    shared_with_users = db.Column(db.JSON, default=lambda: [])  # 使用lambda避免可变默认值
    
    # 可选：拥有者字段（推荐）
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
```

#### **2. 路由设计模式**
```python
# 详情页面路由
@blueprint.route('/<int:id>')
def detail(id):
    # 获取数据 + 权限检查 + 获取可共享用户

# 共享设置更新路由  
@blueprint.route('/<int:id>/update_sharing', methods=['POST'])
def update_sharing(id):
    # 权限检查 + 数据更新 + 重定向
```

#### **3. 权限集成**
- 在数据查询中集成共享权限检查
- 使用 `SharingService.get_shared_data_query()` 获取共享数据
- 在访问控制中检查直接共享权限

#### **4. 用户体验优化**
- 共享设置默认收起（`collapsed=True`）
- 无编辑权限时隐藏组件
- 提供清晰的权限提示信息
- 保存后给予明确反馈

#### **5. 性能考虑**
- 只在需要时获取 `shareable_users_tree`
- 使用JOIN查询减少数据库访问
- 合理使用缓存（如用户树结构）

### **错误处理和调试**

#### **常见问题**
1. **状态不同步**: 检查 `SharingMixin` 是否正确继承
2. **权限错误**: 验证 `can_edit_sharing_settings()` 逻辑
3. **树状结构异常**: 检查 `get_shareable_users_tree()` 数据格式
4. **保存失败**: 检查表单字段名称和数据类型

#### **调试方法**
```python
# 后端调试
logger.info(f"共享用户ID: {model.shared_user_ids}")
logger.info(f"编辑权限: {can_edit_sharing}")

# 前端调试（浏览器控制台）
console.log('选中用户:', getSelectedUserIds('userTree_123'));
```

### **版本兼容性**

#### **当前版本**: v2.0
- ✅ 支持树状用户选择器
- ✅ 服务器端状态渲染 
- ✅ 层级权限控制
- ✅ 公司直属用户层级修复
- ✅ 级联选择和状态同步

#### **升级指南**
从旧版本升级时：
1. 将 `SharingMixin` 添加到模型类
2. 更新模板使用 `render_sharing_section()`
3. 使用 `SharingService` 替换自定义权限逻辑
4. 测试树状选择器功能和权限控制

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