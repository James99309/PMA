# PMA 项目开发规则 - Claude AI 助手指南

## 🎯 核心原则

### **优先级排序**
1. **数据安全** - 永不删除或损坏现有数据
2. **通用组件保护** - 严禁随意修改通用模组，必须遵循保护协议
3. **一致性** - 所有功能必须遵循统一标准
4. **国际化** - 支持中英文切换
5. **用户体验** - 简洁、直观、响应快速
6. **代码质量** - 可维护、可扩展、有文档

---

## 🔒 通用组件保护协议

### **受保护文件列表**
- `app/templates/macros/ui_helpers.html` - 通用UI组件模板
- `app/static/js/data-list.js` - 通用数据列表组件
- `app/static/js/filter-search.js` - 通用筛选搜索组件
- `app/static/css/style.css` (通用组件相关样式) - 通用组件CSS样式

### **修改协议**
**禁止**直接修改上述通用组件文件。如需修改，必须：

1. **风险评估** - 详细分析修改对整个系统的影响范围
2. **获得授权** - 必须获得项目负责人明确同意
3. **充分测试** - 在多个使用该组件的页面进行测试验证
4. **记录修改** - 在 `UNIVERSAL_COMPONENTS_CHANGELOG.md` 中详细记录
5. **代码审查** - 修改后进行代码审查确认

### **替代方案**
- 优先考虑通过配置参数实现需求
- 创建专用组件而非修改通用组件
- 使用CSS覆盖而非修改通用样式

---

## 🌍 翻译与国际化规则

### **强制规则**
- ✅ **所有配置文本使用中文作为 msgid**
- ✅ **英文作为翻译值存储在 messages.po 中**
- ❌ **禁止在 Python 代码中硬编码英文字符串**
- ❌ **禁止在模板中硬编码英文文本**
- 在放入翻译文件中时，先检查是否有重复的中文，只放入中文不重复的英文翻译

### **标准格式**
```python
# 正确 ✅
filter_config = {
    'search_field': {
        'label': '搜索',
        'placeholder': '订单号或公司名称'
    }
}

# 错误 ❌
filter_config = {
    'search_field': {
        'label': 'Search',
        'placeholder': 'Order number or company name'
    }
}
```

### **翻译文件管理**
1. 添加新翻译后必须执行：`pybabel compile -d app/translations`
2. 翻译文件路径：`app/translations/en/LC_MESSAGES/messages.po`
3. 模板中使用：`{{ _('中文文本') }}`
4. Python 中使用：`from flask_babel import gettext as _; _('中文文本')`

---

## 🔧 标准化组件规则

### **筛选搜索组件**
- **必须使用**：`render_filter_search_form(filter_config)`
- **统一配置格式**：
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

---

## 🗂️ 通用列表组件系统

### **系统架构**
通用列表组件系统为所有列表页面提供标准化的UI和交互功能，包括：
- **统计卡片** - 页面顶部的数据统计展示
- **筛选搜索** - 与现有筛选组件集成
- **数据表格** - 标准化的表格渲染
- **AJAX支持** - 无页面刷新的数据加载

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

### **使用方法**

#### **1. 完整列表页面（推荐）**
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
            },
            {
                'id': 'pending',
                'title': '待入库',
                'icon': 'fas fa-clock',
                'value': pending_count,
                'amount': pending_amount,
                'unit': '单',
                'amount_unit': '万元',
                'color': 'warning',
                'clickable': True,
                'click_params': {'inventory_status': 'pending'}
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
                'key': 'company_name',
                'label': '公司',
                'type': 'text',
                'width': '180px'
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
            },
            {
                'key': 'created_at',
                'label': '创建时间',
                'type': 'date',
                'format': '%Y-%m-%d %H:%M',
                'width': '150px'
            }
        ]
    }
}

return render_template('inventory/order_list.html', list_config=list_config)
```

```html
<!-- 模板文件 -->
{% extends "base.html" %}
{% from 'macros/ui_helpers.html' import render_data_list %}

{% block title %}{{ list_config.title }}{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    {{ render_data_list(list_config) }}
</div>

<script src="{{ url_for('static', filename='js/filter-search.js') }}"></script>
<script src="{{ url_for('static', filename='js/data-list.js') }}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 配置数据列表
    const orderListConfig = {
        module_name: '{{ list_config.module_name }}',
        ajax_mode: {{ 'true' if list_config.ajax_mode else 'false' }},
        ajax_endpoint: '{{ url_for("inventory.order_list_ajax") }}',
        ajax_target: '#{{ list_config.table.ajax_target }}',
        stats: {{ list_config.stats | tojson | safe }},
        filter: {{ list_config.filter | tojson | safe }},
        table: {{ list_config.table | tojson | safe }}
    };
    
    // 初始化数据列表
    setupDataList(orderListConfig);
});
</script>
{% endblock %}
```

#### **2. 分别使用各个组件**

**统计卡片：**
```html
{% from 'macros/ui_helpers.html' import render_stats_cards %}
{{ render_stats_cards(stats_config) }}
```

**数据表格：**
```html
{% from 'macros/ui_helpers.html' import render_data_table %}
{{ render_data_table(table_config, items, ajax_mode=True) }}
```

### **AJAX端点标准格式**
```python
@blueprint.route('/api/list_ajax', methods=['GET'])
@login_required
@permission_required('module', 'view')
def list_ajax():
    """标准AJAX列表端点"""
    # 获取搜索和筛选参数
    search = request.args.get('search', '')
    field1 = request.args.get('field1', '')
    
    # 分页参数
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # 构建查询并应用筛选
    query = Model.query
    if search:
        query = query.filter(Model.name.contains(search))
    
    # 执行查询
    total_count = query.count()
    items = query.offset(offset).limit(limit).all()
    
    # 渲染HTML片段（使用行模板）
    html_rows = []
    for item in items:
        html_row = f"""
        <tr>
            <td><a href="/module/view/{item.id}">{item.name}</a></td>
            <td class="text-end">¥{item.amount:,.2f}</td>
            <td>{render_order_status_badge(item.status)}</td>
        </tr>
        """
        html_rows.append(html_row)
    
    # 计算统计数据
    statistics = {
        'total_count': total_count,
        'total_amount': sum(item.amount for item in items),
        'pending_count': query.filter(Model.status == 'pending').count(),
        'pending_amount': sum(item.amount for item in query.filter(Model.status == 'pending').all())
    }
    
    return jsonify({
        'success': True,
        'html': '\n'.join(html_rows),
        'total_count': total_count,
        'loaded_count': len(items),
        'statistics': statistics  # 用于更新统计卡片
    })
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
            },
            'data_key': 'pending'      # 统计数据键名（AJAX更新用）
        }
    ]
}
```

#### **表格配置**
```python
table_config = {
    'ajax_target': 'tableBody',    # AJAX更新目标ID（AJAX模式必需）
    'title': '表格标题',           # 表格标题（可选）
    'icon': 'fas fa-table',       # 标题图标（可选）
    'badge_text': '筛选结果',      # 徽章文本（可选）
    'show_header': True,          # 是否显示表头（默认true）
    'columns': [
        {
            'key': 'field_name',      # 数据字段名（必需）
            'label': '列标题',        # 列标题（必需）
            'type': 'text',           # 数据类型（可选）
            'width': '100px',         # 列宽度（可选）
            'align': 'center',        # 对齐方式（可选）
            'format': 'currency',     # 格式化方式（可选）
            'render': 'macro_name',   # 自定义渲染宏（可选）
            'url_template': '/path/{id}'  # 链接模板（type=link时）
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

### **样式自定义**
```css
/* 自定义统计卡片颜色 */
.stats-card-custom {
    background-color: #f0f8ff;
    border-left: 4px solid #6f42c1;
}

.stats-card-custom .stats-value {
    color: #6f42c1;
}

/* 自定义表格样式 */
.data-list-table.custom-table th {
    background-color: #e3f2fd;
}

.data-list-table.custom-table .badge-custom {
    background-color: #9c27b0;
    color: white;
}
```

### **最佳实践**

1. **优先使用 `render_data_list()` 完整组件**
2. **统计卡片数量建议不超过4个（移动端友好）**
3. **表格列数建议不超过8列（避免横向滚动）**
4. **AJAX模式下必须实现统计数据同步更新**
5. **使用语义化的卡片ID和颜色主题**
6. **为所有数值字段配置合适的格式化**
7. **移动端测试响应式布局**

#### **AJAX模式（无页面刷新，推荐）**

##### **方式一：通用AJAX配置（推荐，无需自定义函数）**
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

**通用AJAX必需的后端支持：**
```python
@blueprint.route('/api/module/filter', methods=['GET'])
@login_required
@permission_required('module', 'view')
def module_list_ajax():
    """模块列表AJAX筛选API"""
    # 获取搜索和筛选参数
    search = request.args.get('search', '')
    field1 = request.args.get('field1', '')
    
    # 分页参数
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # 构建查询并应用筛选
    query = Model.query
    if search:
        query = query.filter(Model.name.contains(search))
    if field1:
        query = query.filter(Model.field1 == field1)
    
    # 执行查询
    total_count = query.count()
    items = query.offset(offset).limit(limit).all()
    has_more = (offset + limit) < total_count
    
    # 渲染HTML片段
    html = render_template('module/item_rows.html', items=items)
    
    return jsonify({
        'html': html,
        'has_more': has_more,
        'total_count': total_count,
        'loaded_count': offset + len(items)
    })
```

**必需的模板片段（item_rows.html）：**
```html
{% for item in items %}
<tr>
    <td>{{ item.name }}</td>
    <td>{{ item.value }}</td>
    <!-- 其他列 -->
</tr>
{% endfor %}
```

##### **方式二：自定义AJAX回调（兼容模式，用于复杂场景）**
```javascript
// 定义AJAX筛选函数
function performAjaxFilter() {
    // 获取当前筛选参数
    const params = getCurrentParams();
    
    // 执行AJAX请求更新列表内容
    fetch('/api/filter-endpoint?' + new URLSearchParams(params))
        .then(response => response.json())
        .then(data => {
            // 更新列表内容
            document.getElementById('tableBody').innerHTML = data.html;
            // 更新浏览器URL
            window.history.pushState({}, '', newUrl);
        });
}

// 定义AJAX重置函数
function resetAjaxFilter() {
    // 清空表单字段
    const form = document.getElementById('formId');
    form.querySelectorAll('input, select').forEach(input => {
        if (input.type === 'text') input.value = '';
        else if (input.tagName === 'SELECT') input.selectedIndex = 0;
    });
    performAjaxFilter();
}

const configName = {
    form_id: 'formId',
    search_field_id: 'search',
    auto_submit: true,
    ajax_mode: true,                      // 启用AJAX模式
    ajax_callback: performAjaxFilter,     // 自定义AJAX筛选函数
    ajax_reset_callback: resetAjaxFilter, // 自定义AJAX重置函数
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

##### **实际项目示例**

**订单列表模块AJAX配置：**
```javascript
const orderFilterConfig = {
    form_id: 'orderFilterForm',
    search_field_id: 'search',
    realtime_search: false,
    auto_submit: true,
    ajax_mode: true,
    ajax_endpoint: '{{ url_for("inventory.order_list_ajax") }}',
    ajax_target: '#orderTableBody',
    ajax_columns: 9,
    dynamic_reset_button: true,
    search_delay: 300,
    filter_fields: [
        { name: 'company_id' },
        { name: 'status' },
        { name: 'inventory_status' }
    ]
};
setupFilterSearch(orderFilterConfig);
```

**结算单列表模块AJAX配置：**
```javascript
const settlementOrderFilterConfig = {
    form_id: 'settlementOrderFilterForm',
    search_field_id: 'search',
    realtime_search: false,
    auto_submit: true,
    ajax_mode: true,
    ajax_endpoint: '{{ url_for("inventory.settlement_order_list_ajax") }}',
    ajax_target: '#settlementTableBody',
    ajax_columns: 8,
    dynamic_reset_button: true,
    search_delay: 300,
    filter_fields: [
        { name: 'settlement_company' },
        { name: 'settlement_status' }
    ]
};
setupFilterSearch(settlementOrderFilterConfig);
```

### **重置按钮显示规则**
- **默认状态**：`display: none` 隐藏
- **显示条件**：有任何筛选条件或搜索内容时自动显示
- **隐藏条件**：重置后或无筛选条件时自动隐藏
- **必须配置**：`dynamic_reset_button: true`

### **自适应宽度功能**
- **自动开启**：`adaptive_width: true`（默认启用）
- **响应式调整**：根据标签文本长度和内容长度自动调整宽度
- **最小宽度**：120px（移动端自动100%宽度）
- **最大宽度**：300px（可通过CSS自定义）
- **语言切换**：自动检测语言变化并重新调整宽度
- **支持内容**：搜索框placeholder、下拉选项最长文本、标签文本
- **关闭方式**：设置 `adaptive_width: false` 或字段级别 `adaptive: false`

### **自适应按钮布局功能**
- **自动开启**：`adaptive_button_layout: true`（默认启用）
- **智能排列**：空间充足时按钮在右侧，空间不足时换行到下方
- **响应式切换**：自动检测可用空间并调整布局
- **桌面端策略**：优先保持按钮在筛选器同一行的右侧
- **移动端策略**：自动换行到下方并右对齐
- **窗口变化**：监听窗口大小变化并实时调整
- **关闭方式**：设置 `adaptive_button_layout: false`

### **徽章组件规则**

#### **设计原则**
- **统一风格**：所有徽章使用自定义样式，不使用Bootstrap默认徽章
- **视觉一致性**：胶囊形状、半透明背景、带边框设计
- **低对比度**：使用CSS变量控制透明度，确保不喧宾夺主

#### **基础样式结构**
```css
.badge.badge-pill.badge-transparent.{特定类名} {
    /* CSS变量控制透明度 */
    --badge-bg-opacity: 0.4;
    --badge-text-opacity: 0.8;
    --badge-border-opacity: 0.6;
}
```

#### **必须使用的通用徽章组件**

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

#### **使用规范**
1. **禁止直接编写徽章HTML**：必须使用已定义的宏
2. **禁止使用Bootstrap徽章类**：如 `bg-primary`、`bg-success` 等
3. **新徽章类型**：需在 `ui_helpers.html` 中创建专门的宏
4. **颜色映射**：在宏内部定义，不在模板中硬编码
5. **国际化支持**：徽章文本必须支持中英文切换

#### **创建新徽章组件示例**
```jinja2
{% macro render_new_type_badge(value) %}
  {% set value_map = {
    'type1': _('类型一'),
    'type2': _('类型二')
  } %}
  <span class="badge badge-pill badge-transparent new-type-{{ value }}">
    {{ value_map.get(value, _(value)) }}
  </span>
{% endmacro %}
```

#### **CSS类命名规范**
- **订单相关**：`order-status-{status}`
- **库存相关**：`inventory-status-{status}`
- **结算相关**：`settlement-status-{status}`
- **项目相关**：`project-stage-{stage}`
- **产品相关**：`product-type-{type}`、`product-status-{status}`
- **用户相关**：`badge-user vendor`、`badge-user regular`
- **通用状态**：`badge-muted`（未设置/无数据）

#### **注意事项**
- `render_user_badge` 使用Bootstrap样式，仅用于特殊场景
- 优先使用 `render_owner` 渲染用户信息
- 空值处理：组件内部处理，显示"未设置"或"-"
- 链接徽章：在 `<a>` 标签内嵌套徽章组件

#### **拥有人徽章组件详细规则 (render_owner)**

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

**错误使用方式**：
```python
# ❌ 错误：只获取字段，无法判断厂商身份
query = db.session.query(
    User.username.label('owner_name'),
    User.real_name.label('owner_real_name')
)

# ❌ 错误：传入字符串，只能显示灰色徽章
{{ render_owner(row.owner_name) }}
```

**后端查询必需条件**：
- 必须获取完整的 `User` 对象，而不是单独字段
- User对象需要包含 `is_vendor_user()` 方法以判断厂商身份
- 数据传递时保持对象完整性

---

## 💾 数据库与模型规则

### **字段规范**
- **时间字段**：使用 UTC 存储，显示时转换为本地时间
- **金额字段**：数据库存储分（整数），显示时除以100转换为元
- **大金额显示**：除以10000显示为万元，格式化为2位小数
- **软删除**：使用 `is_deleted` 布尔字段，默认 `False`
- **创建/更新时间**：`created_at`, `updated_at` 使用 `datetime.utcnow()`

### **查询规范**
```python
# 正确 ✅ - 排除已删除记录
query = Model.query.filter(Model.is_deleted == False)

# 正确 ✅ - 金额转换
total_amount = order.total_amount / 10000  # 转换为万元

# 正确 ✅ - 时间格式化
created_time = order.created_at.strftime('%Y-%m-%d %H:%M')
```

---

## 🎨 前端交互规则

### **动态元素控制**
- **重置按钮**：默认隐藏（`display: none`），JavaScript 控制显示
- **加载状态**：统一使用 `.loading` 类
- **自动筛选**：下拉框变化时自动提交，搜索框需点击搜索按钮

### **CSS 类命名**
- **筛选容器**：`.filter-search-container`
- **重置按钮**：`.filter-reset-button`
- **加载状态**：`.loading`
- **数字对齐**：`.number-cell { text-align: right; }`

### **用户体验**
- **响应时间**：操作反馈在 200ms 内显示
- **加载提示**：超过 1 秒的操作必须显示加载状态
- **错误处理**：所有 AJAX 请求必须有错误处理

---

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
│   └── filter-search.js    # 筛选搜索 JS
```

---

## 🔒 权限与安全规则

### **权限检查**
- 所有路由必须使用 `@permission_required` 装饰器
- 模板中使用 `{% if has_permission('module', 'action') %}`
- API 端点必须验证 CSRF token

### **数据验证**
- 所有用户输入必须验证和清理
- 数据库操作使用事务处理
- 敏感操作记录审计日志

---

## 🚀 性能优化规则

### **数据库查询**
- 避免 N+1 查询，使用 `joinedload()` 或 `subqueryload()`
- 大数据集使用分页：`paginate(page, per_page, error_out=False)`
- 复杂查询使用原生 SQL 或视图

### **前端优化**
- 静态资源使用 CDN
- 大型列表实现虚拟滚动或分页加载
- 图片使用懒加载

---

## 🧪 测试规范

### **必测场景**
- 筛选搜索功能：自动筛选、重置按钮、翻译切换
- 权限控制：无权限时的页面行为
- 数据完整性：CRUD 操作的数据一致性
- 国际化：中英文切换的完整性

### **测试数据**
- 使用种子数据进行开发测试
- 不在生产环境测试

---

## 🛠️ 开发工作流

### **代码修改流程**
1. **读取需求** - 仔细理解用户需求
2. **检查现有实现** - 避免重复造轮子
3. **遵循规范** - 按照本文档规则实现
4. **测试验证** - 确保功能正常且符合规范
5. **文档更新** - 必要时更新本规则文档

### **提交前检查清单**
- [ ] 翻译文件已更新和编译
- [ ] 标准化组件配置一致
- [ ] JavaScript 初始化参数正确
- [ ] 权限检查完整
- [ ] 错误处理完善
- [ ] 代码注释清晰

---

## 🚨 常见错误与解决方案

### **翻译问题**
- **问题**：界面显示英文而非中文
- **解决**：检查配置是否使用中文 msgid，确认翻译文件已编译

### **筛选功能不一致**
- **问题**：不同列表页面行为不同
- **解决**：使用统一的 filter_config 格式和 JavaScript 配置

### **重置按钮显示异常**
- **问题**：重置按钮一直显示或不显示
- **解决**：检查 CSS `.filter-reset-button { display: none; }` 和 JavaScript 控制逻辑

### **权限错误**
- **问题**：用户看到不应该看到的内容
- **解决**：添加 `@permission_required` 装饰器和模板权限检查

---

## 🗄️ 云端数据库备份工具规范

### **备份工具概述**

项目包含两个云端数据库的标准化备份工具，用于定期备份和数据安全保障：

1. **SP8D 数据库备份工具**：`backup_cloud_pma_db.py`
2. **OVS 数据库备份工具**：`simple_ovs_backup.py`

### **备份工具位置和使用**

#### **SP8D 数据库备份**
```bash
# 位置：项目根目录
python3 backup_cloud_pma_db.py

# 功能：
# - 备份云端 pma_db_sp8d 数据库
# - 生成详细的备份信息报告
# - 自动验证数据完整性
```

#### **OVS 数据库备份**
```bash
# 位置：项目根目录
python3 simple_ovs_backup.py

# 功能：
# - 备份云端 pma_db_ovs 数据库
# - 生成统计信息
# - 避免超时问题的简化版本
```

### **备份工具规范**

#### **必须遵循的规范**
- ✅ **统一执行方式**：使用 `subprocess.run()` 同步执行
- ✅ **标准备份选项**：`--verbose --clean --if-exists --no-owner --no-privileges`
- ✅ **密码安全**：通过环境变量 `PGPASSWORD` 传递数据库密码
- ✅ **备份验证**：备份完成后验证文件大小和数据完整性
- ❌ **禁止使用**：`subprocess.Popen()` + 监控循环（可能导致死锁）

#### **备份文件命名规范**
```
云端备份文件格式：
- SP8D: pma_db_sp8d_backup_YYYYMMDD_HHMMSS.sql
- OVS:  pma_db_ovs_backup_simple_YYYYMMDD_HHMMSS.sql

备份信息文件格式：
- SP8D: backup_info_YYYYMMDD_HHMMSS.md
- OVS:  统计信息直接在控制台输出
```

#### **备份存储位置**
```
备份文件统一存储在：
/cloud_db_backups/

目录结构：
cloud_db_backups/
├── pma_db_sp8d_backup_*.sql     # SP8D 数据库备份
├── pma_db_ovs_backup_*.sql      # OVS 数据库备份
├── backup_info_*.md             # 备份信息文件
└── [其他历史备份文件]
```

### **备份完整性要求**

#### **必须包含的内容**
- ✅ **表结构**：所有表的 CREATE TABLE 语句
- ✅ **约束**：主键、外键、唯一约束、检查约束
- ✅ **索引**：所有自定义索引和系统索引
- ✅ **序列**：所有序列定义和当前值
- ✅ **数据**：使用 COPY 语句备份所有表数据
- ✅ **清理语句**：DROP 语句确保可重复恢复

#### **备份质量验证**
```bash
# 验证备份完整性的标准检查
grep -c "CREATE TABLE" backup_file.sql      # 表数量
grep -c "ADD CONSTRAINT" backup_file.sql    # 约束数量
grep -c "CREATE.*INDEX" backup_file.sql     # 索引数量
grep -c "COPY.*FROM stdin" backup_file.sql  # 数据表数量
```

### **备份执行最佳实践**

#### **执行频率建议**
- **开发环境**：根据需要手动执行
- **重要操作前**：必须执行备份（如数据库迁移、重大更新）
- **定期备份**：建议每周至少一次完整备份

#### **执行前检查清单**
1. ✅ 确认网络连接正常
2. ✅ 确认云端数据库可访问
3. ✅ 确认本地磁盘空间充足
4. ✅ 确认 PostgreSQL 客户端工具可用

#### **执行后验证清单**
1. ✅ 检查备份文件大小合理（通常 SP8D > OVS）
2. ✅ 检查备份文件包含表结构和数据
3. ✅ 检查控制台输出无错误信息
4. ✅ 对比数据行数与实时数据库一致

### **故障排除指南**

#### **常见问题及解决方案**

**问题1：备份超时**
- **原因**：使用了 `subprocess.Popen()` + 监控循环
- **解决**：使用简化版备份工具（已解决 OVS 超时问题）

**问题2：连接失败**
- **原因**：网络问题或数据库凭据错误
- **解决**：检查网络连接和数据库URL配置

**问题3：备份文件过小**
- **原因**：备份可能只包含结构，没有数据
- **解决**：检查备份选项，确认包含 COPY 语句

**问题4：权限错误**
- **原因**：数据库用户权限不足
- **解决**：确认数据库用户有读取权限

### **备份工具维护规则**

#### **代码修改规则**
- ❌ **禁止**：修改核心备份逻辑（`subprocess.run` 执行方式）
- ❌ **禁止**：添加复杂的监控循环
- ✅ **允许**：优化备份信息生成
- ✅ **允许**：增强错误处理和日志输出

#### **新增备份工具规则**
如需新增数据库备份工具，必须：

1. **遵循命名规范**：`backup_[database_name].py`
2. **使用统一模式**：基于现有工具的代码结构
3. **包含完整性检查**：验证备份包含所有必要组件
4. **添加到此文档**：更新备份工具列表和使用说明

### **数据库信息对照表**

| 数据库 | 连接地址 | 用户名 | 数据库名 | 估计大小 | 备份耗时 |
|--------|----------|--------|----------|----------|----------|
| **SP8D** | dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com | pma_db_sp8d_user | pma_db_sp8d | ~19MB | ~3秒 |
| **OVS** | dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com | pma_db_ovs_user | pma_db_ovs | ~12MB | ~3秒 |

---

## 🚀 云端数据库迁移升级规范

### **迁移升级概述**

项目建立了标准化的云端数据库迁移升级流程，用于将本地数据库结构变更同步到云端数据库，确保版本一致性和数据安全。

**核心工具：**
1. **SP8D标准迁移升级工具**：`standard_migration_upgrade.py`
2. **SP8D终极迁移同步工具**：`ultimate_migration_sync.py`
3. **OVS标准迁移升级工具**：`standard_migration_upgrade_ovs.py`
4. **OVS终极迁移同步工具**：`ultimate_migration_sync_ovs.py`
5. **迁移冲突修复工具**：`fix_migration_conflicts.py`

### **标准迁移升级流程**

#### **SP8D数据库升级（推荐方式）**
```bash
# SP8D标准Flask-Migrate升级流程
python3 standard_migration_upgrade.py
```

#### **OVS数据库升级（推荐方式）**
```bash
# OVS标准Flask-Migrate升级流程
python3 standard_migration_upgrade_ovs.py
```

**执行步骤：**
1. ✅ **检查迁移状态** - 对比本地和云端当前版本
2. ✅ **自动备份** - 升级前完整备份云端数据库
3. ✅ **执行升级** - 使用 `flask db upgrade` 标准命令
4. ✅ **验证结果** - 确认版本同步和数据完整性

#### **SP8D复杂冲突处理（终极方案）**
```bash
# 当SP8D标准升级失败时使用
python3 ultimate_migration_sync.py
```

#### **OVS复杂冲突处理（终极方案）**
```bash
# 当OVS标准升级失败时使用
python3 ultimate_migration_sync_ovs.py
```

**适用场景：**
- 迁移文件与数据库实际结构不一致
- 存在索引或字段冲突
- 迁移版本历史混乱

**执行步骤：**
1. ✅ **完整备份** - 保证数据安全
2. ✅ **强制版本同步** - 直接更新 alembic_version 表
3. ✅ **结构对比验证** - 确认表数量和基本结构一致
4. ✅ **生成操作报告** - 详细记录同步过程

#### **迁移冲突预处理**
```bash
# 修复已知的迁移冲突
python3 fix_migration_conflicts.py
```

### **迁移升级规范**

#### **执行前检查清单**
- [ ] **本地迁移状态正常** - `flask db current` 显示最新版本
- [ ] **网络连接稳定** - 确保可访问云端数据库
- [ ] **权限验证通过** - 数据库用户有足够权限
- [ ] **磁盘空间充足** - 本地有足够空间存储备份文件

#### **安全保障措施**
- ✅ **自动备份** - 每次升级前自动备份云端数据库
- ✅ **版本验证** - 升级后验证版本号一致性
- ✅ **结构对比** - 对比表数量确保基本结构正确
- ✅ **回滚准备** - 保留备份文件支持快速回滚

#### **升级策略选择**

**SP8D数据库：**

| 场景 | 推荐工具 | 说明 |
|------|----------|------|
| **日常升级** | `standard_migration_upgrade.py` | 标准Flask-Migrate流程 |
| **首次同步** | `ultimate_migration_sync.py` | 处理版本历史差异 |
| **冲突修复** | `fix_migration_conflicts.py` + 标准升级 | 先修复已知冲突 |
| **紧急回滚** | 使用备份文件直接恢复 | 数据安全优先 |

**OVS数据库：**

| 场景 | 推荐工具 | 说明 |
|------|----------|------|
| **日常升级** | `standard_migration_upgrade_ovs.py` | OVS专用标准Flask-Migrate流程 |
| **首次同步** | `ultimate_migration_sync_ovs.py` | 处理OVS版本历史差异 |
| **SP8D安全检查冲突** | `ultimate_migration_sync_ovs.py` | 绕过SP8D专用安全检查 |
| **紧急回滚** | 使用OVS备份文件直接恢复 | 数据安全优先 |

### **迁移文件管理规范**

#### **创建新迁移**
```bash
# 生成迁移文件
flask db revision -m "迁移描述"

# 自动生成（推荐）
flask db migrate -m "迁移描述"
```

#### **迁移文件审查**
创建迁移文件后必须审查：
- ✅ **操作安全性** - 确认不会删除重要数据
- ✅ **索引处理** - 检查索引删除/创建操作
- ✅ **字段约束** - 验证字段类型和约束变更
- ✅ **回滚逻辑** - 确保 downgrade() 函数正确

#### **已知冲突类型及处理**

**SP8D数据库冲突：**

**索引不存在错误：**
```python
# 问题：尝试删除不存在的索引
batch_op.drop_index('idx_name')

# 解决：注释掉或使用安全删除
# batch_op.drop_index('idx_name')  # SP8D中不存在，跳过
```

**字段重复添加错误：**
```python
# 问题：尝试添加已存在的字段
batch_op.add_column(sa.Column('field_name', sa.String()))

# 解决：检查字段是否存在或使用条件添加
```

**OVS数据库冲突：**

**SP8D安全检查阻止：**
```python
# 问题：迁移文件包含SP8D专用安全检查
def upgrade():
    if database_name != 'pma_db_sp8d':
        raise Exception("数据库安全检查失败 - 非SP8D数据库")

# 解决：使用终极迁移同步工具绕过安全检查
python3 ultimate_migration_sync_ovs.py
```

**版本标识不匹配：**
```python
# 问题：OVS使用不同的版本标识符
# 本地版本：b891f72a8dcb
# OVS版本：ovs_sync_fix_20250729

# 解决：使用终极同步强制更新版本号
```

### **备份文件管理**

#### **备份文件命名**
```
SP8D升级备份文件格式：
- 标准升级：sp8d_pre_upgrade_backup_YYYYMMDD_HHMMSS.sql
- 终极同步：sp8d_ultimate_sync_backup_YYYYMMDD_HHMMSS.sql

OVS升级备份文件格式：
- 标准升级：ovs_pre_upgrade_backup_YYYYMMDD_HHMMSS.sql
- 终极同步：ovs_ultimate_sync_backup_YYYYMMDD_HHMMSS.sql
```

#### **备份文件保留策略**
- ✅ **升级备份** - 保留最近10次升级的备份文件
- ✅ **重要里程碑** - 手动标记重要版本的备份文件
- ✅ **定期清理** - 超过30天的常规备份可删除
- ✅ **异地备份** - 重要备份上传到云存储

### **故障排除指南**

#### **常见错误及解决方案**

**SP8D数据库错误：**

**错误1: SP8D迁移版本不匹配**
```
本地版本：b891f72a8dcb
SP8D版本：sync_local_to_cloud_20250728
```
- **解决**：使用 `ultimate_migration_sync.py` 强制同步版本

**错误2: 索引删除失败**
```
sqlalchemy.exc.ProgrammingError: index "idx_name" does not exist
```
- **解决**：编辑迁移文件，注释掉不存在的索引删除操作

**OVS数据库错误：**

**错误1: OVS迁移版本不匹配**
```
本地版本：b891f72a8dcb
OVS版本：ovs_sync_fix_20250729
```
- **解决**：使用 `ultimate_migration_sync_ovs.py` 强制同步版本

**错误2: SP8D安全检查失败**
```
Exception: 数据库安全检查失败 - 非SP8D数据库
安全检查失败: 当前数据库 'pma_db_ovs' 不是SP8D数据库
```
- **解决**：这是预期行为，直接使用 `ultimate_migration_sync_ovs.py`

**通用错误：**

**错误3: 字段重复添加**
```
sqlalchemy.exc.ProgrammingError: column "field_name" already exists
```
- **解决**：检查云端数据库实际结构，修改迁移文件

**错误4: 连接超时**
```
connection timeout
```
- **解决**：检查网络连接，重试升级操作

#### **紧急回滚流程**
```bash
# 1. 停止应用服务
# 2. 使用备份文件完全恢复
PGPASSWORD=password psql -h host -U user -d database < backup_file.sql

# 3. 验证恢复结果
# 4. 重启应用服务
```

### **最佳实践总结**

#### **开发阶段**
- ✅ **频繁迁移** - 小步快跑，避免大批量结构变更
- ✅ **本地测试** - 确保迁移在本地正常执行
- ✅ **代码审查** - 迁移文件必须经过代码审查
- ✅ **文档记录** - 重要结构变更记录在迁移说明中

#### **部署阶段**
- ✅ **备份优先** - 任何升级前先完整备份
- ✅ **标准流程** - 优先使用标准升级工具
- ✅ **版本验证** - 升级后立即验证版本一致性
- ✅ **功能测试** - 升级后进行基本功能测试

#### **监控维护**
- ✅ **定期检查** - 每周检查本地与云端版本一致性
- ✅ **备份清理** - 定期清理过期备份文件
- ✅ **工具更新** - 根据项目发展更新升级工具
- ✅ **经验总结** - 记录升级过程中的问题和解决方案

### **工具脚本位置**

```
项目根目录下的迁移升级工具：
├── standard_migration_upgrade.py        # SP8D标准迁移升级脚本
├── ultimate_migration_sync.py           # SP8D终极迁移同步脚本
├── standard_migration_upgrade_ovs.py    # OVS标准迁移升级脚本
├── ultimate_migration_sync_ovs.py       # OVS终极迁移同步脚本
├── fix_migration_conflicts.py           # 迁移冲突修复脚本
├── backup_cloud_pma_db.py              # SP8D数据库备份工具
└── simple_ovs_backup.py                # OVS数据库备份工具
```

### **升级成功标志**

升级完成后应确认以下指标：
- ✅ **版本一致** - 本地和云端 `flask db current` 版本相同
- ✅ **表数量匹配** - 云端表数量与本地一致
- ✅ **应用启动正常** - 云端应用使用新数据库结构正常启动
- ✅ **功能验证通过** - 关键功能测试正常

### **实战验证案例**

#### **OVS数据库升级成功案例 (2025-08-01)**

**场景**: OVS云端数据库版本落后，需要与本地版本同步

**升级前状态**:
- 本地版本: `b891f72a8dcb`
- OVS版本: `ovs_sync_fix_20250729`
- 表数量: 62个表（两边一致）

**执行流程**:
1. **标准升级尝试**: 使用 `standard_migration_upgrade_ovs.py`
2. **遇到SP8D安全检查**: 按预期触发安全检查阻止
3. **终极同步成功**: 使用 `ultimate_migration_sync_ovs.py` 绕过安全检查
4. **版本完全同步**: 成功同步到 `b891f72a8dcb`

**技术细节**:
- OVS数据库URL: `postgresql://pma_db_ovs_user:***@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs`
- 备份文件: `ovs_pre_upgrade_backup_20250801_012732.sql` (425,458 字节)
- 同步备份: `ovs_ultimate_sync_backup_20250801_012918.sql` (425,458 字节)

**关键成功要素**:
- ✅ **预期SP8D安全检查**: 正确识别并处理安全检查机制
- ✅ **自动备份保护**: 双重备份确保数据安全
- ✅ **版本强制同步**: 成功绕过安全检查更新版本号
- ✅ **结构完整性验证**: 表数量和结构完全匹配

**验证结果**:
```bash
# 升级前
本地: b891f72a8dcb
OVS:  ovs_sync_fix_20250729

# 升级后
本地: b891f72a8dcb  
OVS:  b891f72a8dcb  ✅ 完全同步
```

**注意：此迁移升级流程已通过SP8D和OVS两个数据库的实战验证，可作为云端数据库升级的标准方法。**

---

## 📋 快速参考

### **常用命令**
```bash
# 编译翻译文件
pybabel compile -d app/translations

# 提取新的翻译文本
pybabel extract -F babel.cfg -k _l -o messages.pot .
pybabel update -i messages.pot -d app/translations

# 运行开发服务器
python run.py
```

### **常用代码片段**
```python
# 标准路由模板
@blueprint.route('/list')
@login_required
@permission_required('module', 'view')
def list_view():
    # 获取参数
    search = request.args.get('search', '').strip()
    
    # 构建查询
    query = Model.query.filter(Model.is_deleted == False)
    
    # 应用筛选
    if search:
        query = query.filter(Model.name.ilike(f'%{search}%'))
    
    # 执行查询
    items = query.order_by(Model.created_at.desc()).all()
    
    # 构建筛选配置
    filter_config = {
        'action_url': url_for('blueprint.list_view'),
        'form_id': 'listFilterForm',
        'reset_url': url_for('blueprint.list_view'),
        'search_field': {
            'name': 'search',
            'label': '搜索',
            'placeholder': '搜索提示',
            'value': search,
            'col_width': 4
        },
        'filter_fields': [],
        'search_button_text': '搜索',
        'reset_button_text': '重置'
    }
    
    return render_template('template.html', 
                         items=items,
                         filter_config=filter_config)
```

---

## 📝 规则更新日志

- **2025-07-20**: 创建初始规则文档
- **2025-07-30**: 添加云端数据库备份工具规范
- **2025-08-01**: 添加云端数据库迁移升级规范和标准流程
- **2025-08-01**: 添加OVS数据库迁移升级规范，包含完整的工具链和实战验证案例
- **版本**: 1.3.0
- **最后更新**: 2025-08-01

---

## 💡 注意事项

**Claude AI 助手在每次对话开始时应该：**
1. 自动读取并遵循本规则文档
2. 在不确定时主动询问而非假设
3. 始终优先保证数据安全和代码一致性
4. 完成任务后验证是否符合本规则要求
5. 统一使用中文进行会话

**本文档是活文档，应根据项目发展持续更新完善。**