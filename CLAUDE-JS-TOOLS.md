# JavaScript 可复用工具索引

> **⚠️ 重要规则**: 实现任何JavaScript功能前，必须先查阅此索引！避免重复造轮子。

---

## 📖 文档说明

本文档记录项目中所有可复用的JavaScript工具、组件和函数库，帮助开发者快速定位和复用现有代码。

### **使用指南**

1. **实现功能前** - 先在"快速索引表"中搜索关键词
2. **找到工具后** - 查看详细文档了解API和使用方法
3. **创建新工具后** - 立即更新此文档（强制要求）

---

## 🔍 快速索引表

| 工具文件 | 功能描述 | 使用场景 | 已用页面数 | 状态 |
|---------|---------|---------|-----------|------|
| sortable-list.js | 通用拖拽排序组件 | 任何需要列表拖拽排序的页面 | 2 | ✅ 已文档化 |
| vendor-sales-manager-selector.js | 厂商销售负责人选择器 | 项目创建/编辑需要选择厂商销售负责人 | 2 | ✅ 已文档化 |
| customer-search.js | 客户搜索组件 | 需要搜索和选择客户 | 5+ | 📋 待补充文档 |
| product-selector.js | 产品四级选择器 | 需要选择产品（类别→名称→型号→规格） | 8+ | 📋 待补充文档 |
| customer_account_selector.js | 客户账户选择器 | 需要选择客户关联的账户 | 3+ | 📋 待补充文档 |
| filter-search.js | 筛选搜索组件 | 列表页面的筛选和搜索功能 | 20+ | 📋 待补充文档 |
| data-list.js | 通用数据列表组件 | 数据列表展示和交互 | 15+ | 📋 待补充文档 |
| approval_flow.js | 审批流程工具 | 审批流程展示和操作 | 10+ | 📋 待补充文档 |
| country_region_selector.js | 国家地区选择器 | 需要选择国家和地区 | 5+ | 📋 待补充文档 |
| area_selector.js | 省市区选择器 | 需要选择省市区三级联动 | 8+ | 📋 待补充文档 |
| product-detail-manager.js | 产品明细管理 | 管理产品明细列表（增删改） | 3+ | 📋 待补充文档 |
| expense-detail-manager.js | 费用明细管理 | 管理费用明细列表（增删改） | 2+ | 📋 待补充文档 |
| project-search.js | 项目搜索组件 | 需要搜索和选择项目 | 4+ | 📋 待补充文档 |
| select-with-quick-add.js | 通用选择器快速添加组件 | 为任何下拉选择器提供快速添加新选项功能 | 3 | ✅ 已文档化 |
| spec-analyzer.js | 规格差异分析与高亮工具 | 比较同名产品的规格差异并高亮显示 | 2 | ✅ 已文档化 |

> **说明**:
> - ✅ 已文档化 - 有完整的API文档和使用示例
> - 📋 待补充文档 - 工具已存在但文档待完善
> - 🆕 新创建 - 最近新增的工具

---

## 📚 工具详细文档

### 🔄 通用功能类

#### sortable-list.js

**基本信息**
- **文件路径**: `app/static/js/sortable-list.js`
- **功能描述**: 基于SortableJS实现的通用拖拽排序工具，支持AJAX自动保存、视觉反馈和错误处理
- **依赖库**: SortableJS 1.14.0+, showTopNotification()
- **创建日期**: 2025-11-15

**已使用页面**
1. `/product-code/categories` - 产品分类管理（分类排序）
2. `/product-code/category/<id>/subcategories` - 产品名称管理（名称排序）

**API文档**

```javascript
/**
 * 初始化表格拖拽排序功能
 *
 * @param {string} tbodyId - 表格tbody元素的ID
 * @param {string} updateUrl - 更新排序的API端点URL
 * @param {Object} options - 可选配置参数
 * @param {string} [options.handle=null] - 拖拽手柄的CSS选择器，null表示整行可拖
 * @param {number} [options.animation=150] - 拖拽动画时长(毫秒)
 * @param {Function} [options.onSuccess=null] - 保存成功回调函数
 * @param {Function} [options.onError=null] - 保存失败回调函数
 * @param {Function} [options.extractId=null] - 自定义提取行ID的函数
 * @param {boolean} [options.autoReload=true] - 保存失败时是否自动刷新
 * @param {boolean} [options.updateRowNumbers=true] - 拖动后是否自动更新序号列
 * @returns {Sortable|null} Sortable实例或null
 */
function initSortableList(tbodyId, updateUrl, options = {})
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| tbodyId | string | ✅ | - | 表格tbody元素的ID |
| updateUrl | string | ✅ | - | 保存排序的API端点 |
| options.handle | string | ❌ | null | 拖拽手柄选择器（如'.drag-handle'），null表示整行可拖 |
| options.animation | number | ❌ | 150 | 拖拽动画时长（毫秒） |
| options.onSuccess | function | ❌ | null | 保存成功回调 |
| options.onError | function | ❌ | null | 保存失败回调 |
| options.extractId | function | ❌ | (row) => row.dataset.id | 提取行ID的函数 |
| options.autoReload | boolean | ❌ | true | 失败时是否自动刷新页面 |
| options.updateRowNumbers | boolean | ❌ | true | 拖动后是否自动更新序号列（假设序号在第一个td中） |

**使用示例**

```html
<!-- 1. 引入依赖库 -->
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.14.0/Sortable.min.js"></script>
<script src="{{ url_for('static', filename='js/sortable-list.js') }}"></script>

<!-- 2. HTML表格结构 -->
<table class="table">
    <thead>
        <tr>
            <th>序号</th>
            <th>名称</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody id="myTableBody">
        <tr data-id="1">
            <td>
                <i class="fas fa-grip-vertical drag-handle"></i>
                1
            </td>
            <td>项目A</td>
            <td>...</td>
        </tr>
        <tr data-id="2">
            <td>
                <i class="fas fa-grip-vertical drag-handle"></i>
                2
            </td>
            <td>项目B</td>
            <td>...</td>
        </tr>
    </tbody>
</table>

<!-- 3. 初始化拖拽排序 -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 基础用法（使用拖拽手柄）
    initSortableList('myTableBody', '/api/update-order', {
        handle: '.drag-handle'
    });

    // 高级用法（自定义回调）
    initSortableList('myTableBody', '/api/update-order', {
        handle: '.drag-handle',
        animation: 200,
        onSuccess: function(result) {
            console.log('排序保存成功', result);
        },
        onError: function(error) {
            console.error('排序保存失败', error);
        },
        autoReload: false  // 失败时不自动刷新
    });
});
</script>
```

**后端API要求**

```python
@app.route('/api/update-order', methods=['POST'])
def update_order():
    """
    接收格式:
    {
        "items": [
            {"id": 1, "order": 1},
            {"id": 2, "order": 2},
            {"id": 3, "order": 3}
        ]
    }

    返回格式:
    {
        "success": true,
        "message": "排序更新成功"
    }
    """
    data = request.get_json()
    items = data.get('items', [])

    for item in items:
        # 更新数据库中的display_order字段
        obj = Model.query.get(item['id'])
        if obj:
            obj.display_order = item['order']

    db.session.commit()
    return jsonify({'success': True, 'message': '排序更新成功'})
```

**CSS样式配置**

```css
/* style.css 中已包含以下样式，无需额外添加 */

/* 拖拽手柄 */
.drag-handle {
    cursor: grab;
    color: #6c757d;
}
.drag-handle:hover {
    color: #0d6efd;
}
.drag-handle:active {
    cursor: grabbing;
}

/* 拖拽时的虚影 */
.sortable-ghost {
    opacity: 0.4;
    background-color: #e9ecef !important;
    border: 2px dashed #0d6efd;
}

/* 正在拖拽的元素 */
.sortable-drag {
    opacity: 0.8;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

**注意事项**

1. ⚠️ 表格每行必须有 `data-id` 属性，值为记录的ID
2. ⚠️ 后端API必须返回 `{success: true/false, message: '...'}` 格式
3. ⚠️ 需要在数据模型中添加 `display_order` 字段
4. ✅ 支持移动端触摸拖拽
5. ✅ 保存失败会自动回滚（刷新页面）

**扩展场景**

未来可用于：
- 审批步骤排序
- 产品规格字段排序
- 菜单项排序
- 任何需要列表排序的场景

---

### 🎯 数据选择器类

#### vendor-sales-manager-selector.js

**基本信息**

- **文件路径**: `app/static/js/vendor-sales-manager-selector.js`
- **版本**: 1.0.0
- **创建日期**: 2025-10-21
- **文件大小**: 134 行

**功能描述**

加载和显示厂商销售负责人列表，支持按部门优先级排序（销售部 → 服务部 → 其他部门），并支持编辑模式预选和自动选择当前用户。

**使用场景**

任何需要选择厂商销售负责人的表单页面，特别是：
- 项目创建页面（自动选择当前厂商用户）
- 项目编辑页面（预选已有负责人）
- 未来可能的订单、报价等页面

**已使用页面**

1. `app/templates/project/add.html` - 项目创建页面
2. `app/templates/project/edit.html` - 项目编辑页面

**核心功能**

- ✅ 调用 `/api/users/hierarchical?vendor_only=true` 获取厂商用户
- ✅ 按部门优先级排序：销售部(1) → 服务部(2) → 其他(3)
- ✅ 同优先级内按中文拼音排序
- ✅ 支持编辑模式预选指定用户
- ✅ 支持创建模式自动选择当前用户
- ✅ 显示格式：`姓名 (部门)`

**API 文档**

```javascript
/**
 * 加载厂商销售负责人到下拉选择器
 * @param {string} selectElementId - 选择器元素ID
 * @param {Object} options - 配置选项
 * @returns {Promise<void>}
 */
loadVendorSalesManagers(selectElementId, options)
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| selectElementId | string | ✅ | - | 下拉选择器的DOM元素ID |
| options | object | ❌ | {} | 配置选项对象 |
| options.selectedUserId | number | ❌ | null | 编辑模式：预选的用户ID |
| options.autoSelectCurrentUser | boolean | ❌ | false | 是否自动选择当前登录用户 |
| options.currentUserId | number | ❌ | null | 当前登录用户ID |
| options.currentUserIsVendor | boolean | ❌ | false | 当前用户是否为厂商 |
| options.emptyText | string | ❌ | '请选择厂商销售负责人' | 默认提示文本 |

**使用示例**

**引入工具**
```html
<!-- 在页面底部引入 -->
<script src="{{ url_for('static', filename='js/vendor-sales-manager-selector.js') }}"></script>
```

**创建模式（自动选择当前厂商用户）**
```html
<select id="vendor_sales_manager_id" name="vendor_sales_manager_id" class="form-select">
    <option value="">请选择厂商销售负责人</option>
</select>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // 加载厂商销售负责人列表
    loadVendorSalesManagers('vendor_sales_manager_id', {
        autoSelectCurrentUser: true,
        currentUserId: {{ current_user.id }},
        currentUserIsVendor: {{ 'true' if current_user.is_vendor_user() else 'false' }},
        emptyText: '请选择厂商销售'
    });
});
</script>
```

**编辑模式（预选已有负责人）**
```html
<select id="vendor_sales_manager_id" name="vendor_sales_manager_id" class="form-select">
    <option value="">{{ _("请选择厂商销售负责人") }}</option>
</select>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // 加载厂商销售负责人列表并预选
    loadVendorSalesManagers('vendor_sales_manager_id', {
        {% if project and project.vendor_sales_manager_id %}
        selectedUserId: {{ project.vendor_sales_manager_id }},
        {% endif %}
        emptyText: '{{ _("请选择厂商销售负责人") }}'
    });
});
</script>
```

**技术实现细节**

1. **数据获取**: 调用 `/api/users/hierarchical?vendor_only=true` API
2. **数据收集**: 从所有公司中提取所有用户到扁平列表
3. **排序算法**:
   ```javascript
   // 部门优先级
   getDepartmentPriority(department) {
       if (department === '销售部') return 1;
       if (department === '服务部') return 2;
       return 3;  // 其他部门
   }

   // 先按优先级，再按中文拼音
   users.sort((a, b) => {
       const priorityDiff = getDepartmentPriority(a.dept) - getDepartmentPriority(b.dept);
       if (priorityDiff !== 0) return priorityDiff;
       return (a.real_name || a.name).localeCompare(b.real_name || b.name, 'zh-CN');
   });
   ```
4. **显示格式**: `${displayName} (${department})`

**依赖关系**

- **API依赖**: `/api/users/hierarchical` (需要支持 `vendor_only` 参数)
- **前端依赖**: 无（纯JavaScript实现）
- **CSS依赖**: Bootstrap 5 的 `.form-select` 样式

**重构说明**

- **重构日期**: 2025-10-21
- **原因**: 消除 `project/add.html` 和 `project/edit.html` 中的重复代码
- **代码减少**: 165行重复代码 → 134行公共工具 + 14行调用代码
- **净减少**: 17行代码，消除所有重复

**维护日志**

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2025-10-21 | 1.0.0 | 初始版本，从项目创建/编辑页面重构而来 |

---

### 🔍 搜索组件类

#### customer-search.js

**基本信息**

- **文件路径**: `app/static/js/customer-search.js`
- **状态**: 📋 待补充详细文档

**功能描述**

通用客户搜索组件，支持关键词搜索、权限过滤、显示公司名称和联系人等信息。

**已使用页面**

- `app/templates/pricing_order/edit_pricing_order.html`
- `app/templates/macros/customer_search.html` (通过宏引入)
- 其他待统计...

**后续任务**: 补充完整的API文档和使用示例

---

#### project-search.js

**基本信息**

- **文件路径**: `app/static/js/project-search.js`
- **状态**: 📋 待补充详细文档

**功能描述**

项目搜索组件，支持项目名称、项目编号等搜索。

**后续任务**: 补充完整的API文档和使用示例

---

### 🎨 UI组件类

#### product-selector.js

**基本信息**

- **文件路径**: `app/static/js/product-selector.js`
- **状态**: 📋 待补充详细文档

**功能描述**

产品四级联动选择器：类别 → 产品名称 → 型号 → 规格。

**核心功能**

- 四级联动选择
- 缓存机制（默认5分钟）
- 支持自定义API端点
- 支持回调函数

**后续任务**: 补充完整的API文档和使用示例

---

#### filter-search.js

**基本信息**

- **文件路径**: `app/static/js/filter-search.js`
- **状态**: 📋 待补充详细文档

**功能描述**

通用筛选搜索组件，配合 `render_filter_search_form()` 模板宏使用。

**已使用场景**

几乎所有列表页面（20+页面）

**后续任务**: 补充完整的API文档和使用示例

---

#### data-list.js

**基本信息**

- **文件路径**: `app/static/js/data-list.js`
- **状态**: 📋 待补充详细文档

**功能描述**

通用数据列表组件，配合 `render_data_list()` 模板宏使用。

**核心功能**

- 列表初始化
- AJAX刷新
- 统计数据更新
- 与 filter-search.js 集成

**后续任务**: 补充完整的API文档和使用示例

---

### 📋 业务工具类

#### approval_flow.js

**基本信息**

- **文件路径**: `app/static/js/approval_flow.js`
- **状态**: 📋 待补充详细文档

**功能描述**

审批流程展示和操作工具。

**后续任务**: 补充完整的API文档和使用示例

---

#### product-detail-manager.js

**基本信息**

- **文件路径**: `app/static/js/product-detail-manager.js`
- **状态**: 📋 待补充详细文档

**功能描述**

管理产品明细列表（增删改查）。

**后续任务**: 补充完整的API文档和使用示例

---

#### expense-detail-manager.js

**基本信息**

- **文件路径**: `app/static/js/expense-detail-manager.js`
- **状态**: 📋 待补充详细文档

**功能描述**

管理费用明细列表（增删改查）。

**后续任务**: 补充完整的API文档和使用示例

---

### 🌍 地区工具类

#### country_region_selector.js

**基本信息**

- **文件路径**: `app/static/js/country_region_selector.js`
- **状态**: 📋 待补充详细文档

**功能描述**

国家和地区二级联动选择器。

**后续任务**: 补充完整的API文档和使用示例

---

#### area_selector.js

**基本信息**

- **文件路径**: `app/static/js/area_selector.js`
- **状态**: 📋 待补充详细文档

**功能描述**

省市区三级联动选择器。

**后续任务**: 补充完整的API文档和使用示例

---

## 🛠️ 工具创建指南

### **何时应该创建可复用工具？**

满足以下**任一条件**即应创建可复用工具：

1. ✅ **重复代码**: 相同或相似逻辑在2个及以上页面中出现
2. ✅ **代码量大**: 单个功能逻辑超过50行且具有通用性
3. ✅ **复用潜力**: 未来可能在其他页面使用的功能
4. ✅ **业务通用**: 跨模块的通用业务逻辑（如选择器、搜索等）

### **工具创建步骤**

1. **命名规范**: 使用语义化的kebab-case命名
   - ✅ 好的命名: `vendor-sales-manager-selector.js`
   - ❌ 不好的命名: `tool1.js`, `helper.js`, `util.js`

2. **文件位置**: `app/static/js/`

3. **代码结构**:
   ```javascript
   /**
    * 工具功能描述
    *
    * @author Claude AI (或开发者名称)
    * @version 1.0.0
    */

   // 使用函数式编程或类（视情况而定）
   function toolFunction(param1, options = {}) {
       // 实现...
   }

   // 或
   class ToolClass {
       constructor(config) {
           // 初始化...
       }
   }
   ```

4. **立即更新文档**: 在 `CLAUDE-JS-TOOLS.md` 中添加完整文档

### **文档更新模板**

每次创建新工具后，按以下模板更新本文档：

```markdown
#### 工具名称.js

**基本信息**

- **文件路径**: `app/static/js/xxx.js`
- **版本**: 1.0.0
- **创建日期**: YYYY-MM-DD
- **文件大小**: XXX 行

**功能描述**

一段话描述工具的核心功能。

**使用场景**

列出工具适用的具体场景。

**已使用页面**

1. `路径/文件名.html` - 页面说明
2. ...

**API 文档**

```javascript
functionName(param1, param2, options)
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| ... | ... | ... | ... | ... |

**使用示例**

```html
<!-- 引入 -->
<script src="{{ url_for('static', filename='js/xxx.js') }}"></script>

<!-- 使用 -->
<script>
// 示例代码
</script>
```

**依赖关系**

- API依赖: ...
- 前端依赖: ...
- CSS依赖: ...

**维护日志**

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| ... | ... | ... |
```

---

## 📋 待办事项

### **文档完善计划**

- [ ] 补充 `customer-search.js` 详细文档
- [ ] 补充 `product-selector.js` 详细文档
- [ ] 补充 `filter-search.js` 详细文档
- [ ] 补充 `data-list.js` 详细文档
- [ ] 补充 `approval_flow.js` 详细文档
- [ ] 补充其余工具的基本信息
- [ ] 统计所有工具的使用页面数量

### **代码重构计划**

- [ ] 检查现有页面是否有重复的JavaScript代码
- [ ] 评估是否有新的工具提炼机会
- [ ] 优化现有工具的API设计

---

## 📖 相关文档

- **CLAUDE-COMPONENTS.md** - 模板组件（Jinja2宏）使用规范
- **CLAUDE.md** - 项目核心开发规范
- **CLAUDE-CODE-QUALITY.md** - 代码质量与重构规范

---

## 🆕 快速操作工具

### select-with-quick-add.js

**基本信息**

- **文件路径**: `app/static/js/select-with-quick-add.js`
- **版本**: 2.0.0
- **创建日期**: 2025-11-08
- **文件大小**: 约700行
- **替代**: indicator-quick-add.js (已删除)

**功能描述**

通用选择器快速添加组件，为任何下拉选择器提供即时添加新选项的能力。基于配置驱动设计，支持多种数据源（产品指标、产品名称、销售区域等）。

**使用场景**

- 产品创建/编辑时快速添加规格指标
- 产品创建/编辑时快速添加产品名称（子分类）
- 产品创建/编辑时快速添加销售区域
- 任何需要为下拉选择器动态添加新选项的场景

**已使用页面**

1. `app/templates/product/create.html` - 产品创建/编辑页面（统一页面）
2. `app/templates/product_management/new_product.html` - 研发产品新建页面（通过create.html）
3. `app/templates/product_management/edit_product.html` - 研发产品编辑页面（通过create.html）

**核心功能**

- ✅ 配置驱动架构，支持多种数据源
- ✅ 预设配置：产品指标、产品名称、销售区域
- ✅ 显示统一的快速添加模态框（Bootstrap 5风格）
- ✅ 自动加载并显示已有项目列表（徽章样式）
- ✅ 提交到对应的后端API
- ✅ 自动刷新目标下拉选择器
- ✅ 自动选中新添加的项目
- ✅ 自动生成唯一编码（A-Z → 0-9）
- ✅ 权限检查支持
- ✅ Toast通知提示添加结果
- ✅ 完整的错误处理
- ✅ 向后兼容IndicatorQuickAdd API

**API文档**

```javascript
// 1. 注册新配置（扩展到其他数据源）
SelectWithQuickAdd.register(type, config)

// 2. 显示快速添加模态框
SelectWithQuickAdd.showModal(type, context)

// 3. 提交新项目（通常由模态框内的保存按钮调用）
SelectWithQuickAdd.submit()

// 4. 向后兼容的指标API（已弃用，建议使用showModal）
IndicatorQuickAdd.showQuickAddModal(specName, specFieldId, rowElement)
```

**预设配置类型**

| 类型 | 说明 | API端点 | 已用页面 |
|-----|------|---------|---------|
| `indicator` | 产品规格指标 | `/product-management/api/spec-field-options/add` | 产品创建/编辑 |
| `subcategory` | 产品名称（子分类） | `/product-code/api/subcategories/quick-add` | 产品创建 |
| `region` | 销售区域 | `/product-code/api/regions/quick-add` | 产品创建 |

**showModal参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| type | string | ✅ | - | 配置类型（indicator/subcategory/region） |
| context | object | ✅ | - | 上下文信息 |
| context.targetSelect | HTMLElement | 条件 | null | 目标下拉选择器（subcategory/region必需） |
| context.targetRow | HTMLElement | 条件 | null | 目标行元素（indicator必需） |
| context.specName | string | 条件 | null | 规格名称（indicator必需） |
| context.specFieldId | string/number | ❌ | null | 规格字段ID（indicator可选） |
| context.displayName | string | ❌ | null | 模态框标题显示名称 |

**使用示例**

```html
<!-- 1. 引入模态框宏 -->
{% from 'macros/ui_modals.html' import render_select_quick_add_modal %}

<!-- 2. 在页面底部渲染模态框 -->
{{ render_select_quick_add_modal() }}

<!-- 3. 引入JS工具 -->
<script src="{{ url_for('static', filename='js/select-with-quick-add.js') }}"></script>

<!-- 4. 示例1: 产品名称下拉框添加快速添加选项 -->
<select class="form-select" id="subcategory_id" name="subcategory_id">
    <option value="">-- 请先选择分类 --</option>
    <!-- 动态加载的选项 -->
    {% if has_permission('product_code', 'edit') %}
    <option value="__ADD_NEW_SUBCATEGORY__" style="color: #0d6efd; font-weight: 500;">
        ➕ 添加新产品名称
    </option>
    {% endif %}
</select>

<script>
// 监听产品名称选择变化
document.getElementById('subcategory_id').addEventListener('change', function() {
    if (this.value === '__ADD_NEW_SUBCATEGORY__') {
        this.value = ''; // 恢复到之前的选择
        SelectWithQuickAdd.showModal('subcategory', {
            targetSelect: this
        });
    }
});
</script>

<!-- 5. 示例2: 销售区域快速添加 -->
<select class="form-select" id="region_id" name="region_id">
    <option value="">-- 请选择销售区域 --</option>
    <!-- 选项列表 -->
    {% if has_permission('product_code', 'edit') %}
    <option value="__ADD_NEW_REGION__" style="color: #0d6efd; font-weight: 500;">
        ➕ 添加新区域
    </option>
    {% endif %}
</select>

<script>
// 监听区域选择变化
document.getElementById('region_id').addEventListener('change', function() {
    if (this.value === '__ADD_NEW_REGION__') {
        this.value = '';
        SelectWithQuickAdd.showModal('region', {
            targetSelect: this
        });
    }
});
</script>

<!-- 6. 示例3: 产品指标快速添加（向后兼容） -->
<button type="button"
        onclick="IndicatorQuickAdd.showQuickAddModal('颜色', '123', this.closest('tr'))">
    <i class="fas fa-plus"></i> 快速添加
</button>
```

**模态框UI预览**

```
┌─────────────────────────────────────────────────┐
│ ⊕ 快速添加指标                           ✕      │ ← 蓝色header
├─────────────────────────────────────────────────┤
│ ℹ️ 添加新的指标值到当前规格。新指标将立即可用。   │
│ 当前规格: 颜色                                  │
│                                                 │
│ 指标名称 *                                      │
│ ┌─────────────────────────────────────────┐   │
│ │ 请输入指标名称...                        │   │
│ └─────────────────────────────────────────┘   │
│                                                 │
│ 指标说明 (可选)                                 │
│ ┌─────────────────────────────────────────┐   │
│ │                                         │   │
│ └─────────────────────────────────────────┘   │
│                                                 │
│ 🪄 系统将自动为指标分配唯一编码                  │
├─────────────────────────────────────────────────┤
│                            [取消] [✓ 保存并选择] │
└─────────────────────────────────────────────────┘
```

**后端API依赖**

**API 1: 产品指标快速添加**
```
POST /product-management/api/spec-field-options/add
请求: { subcategory_id, spec_name, field_id?, value, description? }
响应: { success, message, new_item: {id, value, code, description} }
```

**API 2: 产品名称快速添加**
```
POST /product-code/api/subcategories/quick-add
请求: { category_id, value, description? }
响应: { success, message, new_item: {id, name, code_letter, description} }
```

**API 3: 销售区域快速添加**
```
POST /product-code/api/regions/quick-add
请求: { value, description? }
响应: { success, message, new_item: {id, name, code_letter, description} }
```

**API 4-5: 获取已有项目列表**
```
GET /product-code/api/subcategories?category_id={id}
GET /product-code/api/regions
响应: { success, items: [{id, name, code, is_active}] }
```

**前端依赖**

- **Bootstrap 5**: 模态框组件 (`bootstrap.Modal`)
- **模板宏**: `macros/ui_modals.html::render_select_quick_add_modal()`
- **UI组件**: `macros/ui_helpers.html::render_button()`
- **Toast容器**: 用于成功提示（可选，降级为console）
- **权限系统**: `has_permission('product_code', 'edit')` 控制显示

**工作流程**

1. 用户在下拉框中选择"➕ 添加新XXX"特殊选项
2. JavaScript监听change事件，检测特殊值
3. 调用 `SelectWithQuickAdd.showModal(type, context)` 显示模态框
4. 自动加载并显示已有项目列表（徽章样式）
5. 用户输入名称和描述
6. 点击"保存并选择"触发 `submit()`
7. 调用对应的后端API创建新项目
8. API自动生成唯一编码（A-Z → 0-9）
9. 成功后关闭模态框
10. 刷新目标下拉选择器，添加新选项
11. 自动选中新添加的项目
12. 显示Toast成功提示

**注意事项**

- ✅ 自动初始化，无需手动调用 `init()`
- ✅ 支持Enter键快速提交
- ✅ 模态框关闭时自动重置表单
- ✅ 配置驱动，易于扩展到其他数据源
- ✅ 向后兼容 IndicatorQuickAdd API
- ✅ 权限控制：只有有 `product_code.edit` 权限的用户能看到快速添加选项
- ⚠️ 需要确保页面有CSRF token字段
- ⚠️ 产品名称快速添加需要先选择产品分类
- ⚠️ 产品指标快速添加需要先选择产品名称（子分类）

**扩展示例：添加新的数据源**

```javascript
// 注册新的配置类型：品牌快速添加
SelectWithQuickAdd.register('brand', {
    modalId: 'selectQuickAddModal',
    apiEndpoint: '/product-code/api/brands/quick-add',
    valueFieldLabel: '品牌名称',
    descriptionFieldLabel: '品牌描述',

    getExistingItemsUrl: function(context) {
        return '/product-code/api/brands';
    },

    refreshTarget: function(context, newItem) {
        if (!context.targetSelect) return;
        const option = document.createElement('option');
        option.value = newItem.id;
        option.textContent = newItem.name;
        context.targetSelect.appendChild(option);
        context.targetSelect.value = newItem.id;
        context.targetSelect.dispatchEvent(new Event('change'));
    }
});

// 使用
SelectWithQuickAdd.showModal('brand', {
    targetSelect: document.getElementById('brand_select')
});
```

**维护日志**

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2025-11-08 | 2.0.0 | 重构为通用组件，支持产品指标、产品名称、销售区域快速添加 |
| 2025-11-01 | 1.0.0 | ~~初始版本（indicator-quick-add.js，已删除）~~ |

---

## 🔍 规格分析工具

### spec-analyzer.js

**基本信息**

- **文件路径**: `app/static/js/spec-analyzer.js`
- **版本**: 1.0.0
- **创建日期**: 2025-11-28
- **文件大小**: 约200行
- **依赖**: 无外部依赖

**功能描述**

规格差异分析与高亮工具，用于分析同名产品的规格差异并以**黑色加粗+下划线**样式高亮显示差异部分。支持两种数据格式：字符串格式（如 ProductConfigModal 中的规格描述）和 JSON 快照格式（如报价单产品选择中的编码定义快照）。

**使用场景**

- 产品配置模态框中，当存在多个同名产品（如必选互斥、可选互斥、推荐配置）时，高亮显示规格差异
- 报价单产品选择三级菜单中，高亮同名产品的规格差异
- 任何需要比较并高亮产品规格差异的场景

**已使用页面**

1. `app/templates/macros/product_detail_manager.html` - 产品配置模态框（通过 product-config-modal.js 调用）
2. `app/static/js/product-selector.js` - 报价单产品选择三级菜单（第三级产品列表差异高亮）

**核心功能**

- ✅ 解析规格描述字符串为 key-value 对象
- ✅ 按产品名称自动分组
- ✅ 比较同组产品的规格差异
- ✅ 生成带高亮标签的 HTML
- ✅ 支持字符串格式和 JSON 快照格式
- ✅ 纯静态方法设计，无需实例化

**API文档**

```javascript
// ========== 字符串格式解析 ==========

/**
 * 解析规格描述字符串为 key-value 对象
 * @param {string} specStr - 规格字符串，如 "频率范围: 120 MHz, 接口类型: N"
 * @returns {Object} - { "频率范围": "120 MHz", "接口类型": "N" }
 */
SpecAnalyzer.parseSpecString(specStr)

/**
 * 分析同组产品的规格差异（字符串格式）
 * @param {Array} items - 同名产品列表
 * @param {string} specKey - 规格字段名 ('specification' 或 'product_desc')
 * @returns {Set} - 有差异的规格key集合
 */
SpecAnalyzer.findDiffKeys(items, specKey = 'specification')

/**
 * 为配置列表计算差异信息（按产品名称分组）
 * @param {Array} configs - 配置列表
 * @param {string} specKey - 规格字段名
 * @returns {Map} - configId -> diffKeys 的映射
 */
SpecAnalyzer.calculateDiffMap(configs, specKey = 'specification')

/**
 * 生成带差异高亮的规格HTML（字符串格式）
 * @param {string} specStr - 规格字符串
 * @param {Set} diffKeys - 有差异的key集合
 * @returns {string} - 带高亮标签的HTML
 */
SpecAnalyzer.highlightSpecString(specStr, diffKeys)

// ========== JSON快照格式解析 ==========

/**
 * 解析编码定义快照
 * @param {string|Object} rawSnapshot - JSON字符串或对象
 * @returns {Array} - [{field_name, value, code}, ...]
 */
SpecAnalyzer.parseSnapshot(rawSnapshot)

/**
 * 分析同组产品的规格差异（JSON快照格式）
 * @param {Array} items - 同名产品列表
 * @returns {Array} - [{position, fieldName, isDiff, values}, ...]
 */
SpecAnalyzer.findDiffPositions(items)

/**
 * 生成带差异高亮的规格HTML（JSON快照格式）
 * @param {Object} snapshot - 产品的编码快照
 * @param {Array} diffPositions - findDiffPositions 的返回结果
 * @returns {string} - 带高亮标签的HTML
 */
SpecAnalyzer.highlightSnapshot(snapshot, diffPositions)

// ========== 通用分组 ==========

/**
 * 按名称分组产品
 * @param {Array} items - 产品/配置列表
 * @param {string} nameKey - 名称字段名
 * @returns {Object} - { "产品名称": [item1, item2, ...], ... }
 */
SpecAnalyzer.groupByName(items, nameKey = 'product_name')
```

**参数说明**

| 方法 | 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| findDiffKeys | items | Array | ✅ | - | 同名产品列表 |
| findDiffKeys | specKey | string | ❌ | 'specification' | 规格字段名 |
| calculateDiffMap | configs | Array | ✅ | - | 配置列表（可含不同名产品） |
| highlightSpecString | specStr | string | ✅ | - | 规格字符串 |
| highlightSpecString | diffKeys | Set | ✅ | - | 有差异的key集合 |

**CSS样式**

```css
/* 在 product-config-nested.css 中定义 */
.spec-diff-highlight {
    color: #000;                /* 黑色文字 */
    font-weight: bold;          /* 加粗 */
}
```

**高亮规则**：只高亮指标值（value），规格名称（key）保持不变
- 示例：`信道端口数: **2**`（只有"2"加粗黑色）

**使用示例**

```javascript
// 示例1: 必选互斥组 - 同组产品比较
const group = {
    group_id: 1,
    products: [
        { related_product_id: 101, product_name: '信号剥离器', specification: '频率范围: 120 MHz, 接口类型: N' },
        { related_product_id: 102, product_name: '信号剥离器', specification: '频率范围: 240 MHz, 接口类型: SMA' }
    ]
};

// 计算差异keys
const diffKeys = SpecAnalyzer.findDiffKeys(group.products);
// diffKeys = Set { '频率范围', '接口类型' }

// 生成高亮HTML
group.products.forEach(product => {
    const highlightedSpec = SpecAnalyzer.highlightSpecString(product.specification, diffKeys);
    // highlightedSpec = '<span class="spec-diff-highlight">频率范围: 120 MHz</span>, <span class="spec-diff-highlight">接口类型: N</span>'
});

// 示例2: 推荐配置 - 不同名产品混合（按名称分组计算）
const configs = [
    { id: 1, product_name: '电源适配器', specification: '输出功率: 12W' },
    { id: 2, product_name: '电源适配器', specification: '输出功率: 24W' },
    { id: 3, product_name: '天线', specification: '增益: 3dBi' }
];

// 按名称分组计算差异
const diffMap = SpecAnalyzer.calculateDiffMap(configs);
// diffMap = Map { 1 => Set{'输出功率'}, 2 => Set{'输出功率'} }
// 注意: id=3 的天线没有同名产品，所以不在 diffMap 中

// 渲染时使用
configs.forEach(config => {
    const diffKeys = diffMap.get(config.id) || new Set();
    const html = SpecAnalyzer.highlightSpecString(config.specification, diffKeys);
});
```

**在 product-config-modal.js 中的集成示例**

```javascript
// 渲染必选互斥组时
renderRequiredMutualGroups(groups, options) {
    Object.values(groups).forEach(group => {
        // 计算差异keys
        const diffKeys = window.SpecAnalyzer
            ? window.SpecAnalyzer.findDiffKeys(group.products)
            : new Set();

        group.products.forEach(product => {
            // 传递diffKeys到内容创建函数
            this.createConfigItemContent(product, {
                badgeType: 'relation-type-required-mutual',
                badgeText: '必选互斥',
                diffKeys: diffKeys  // 传递差异keys
            });
        });
    });
}

// createConfigItemContent 中使用
createConfigItemContent(config, options) {
    const row3 = document.createElement('div');
    const specText = config.specification || '-';

    // 如果有差异keys，使用高亮显示
    if (options.diffKeys && options.diffKeys.size > 0 && window.SpecAnalyzer) {
        row3.innerHTML = window.SpecAnalyzer.highlightSpecString(specText, options.diffKeys);
    } else {
        row3.textContent = specText;
    }
}
```

**复用说明**

此工具设计为可复用模块，未来可直接用于：

1. **报价单产品选择三级菜单** - 使用 JSON 快照格式的 `findDiffPositions()` 和 `highlightSnapshot()` 方法
2. **产品对比页面** - 使用字符串格式的比较方法
3. **任何需要高亮产品规格差异的场景**

**代码量统计**

| 场景 | 代码量 | 说明 |
|-----|--------|------|
| 首次集成 | ~135行 | spec-analyzer.js (90行) + CSS (15行) + 调用代码 (30行) |
| 复用（报价单） | ~16行 | 仅需调用代码，工具已存在 |
| 节省比例 | 90%↓ | 复用时节省约 90% 代码量 |

**维护日志**

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2025-11-28 | 1.0.0 | 初始版本，支持字符串格式和JSON快照格式 |

---

**版本**: 2.1.0
**最后更新**: 2025-11-28
**维护者**: Claude AI
