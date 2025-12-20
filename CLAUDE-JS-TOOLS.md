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
| customer-form.js | 客户表单公共逻辑 | 客户新建/编辑表单（国家地区、行业、类型等） | 2 | ✅ 已文档化 |
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
| tw-list-manager.js | Tailwind列表管理器 | Tailwind列表页的排序、无限滚动 | 2 | ✅ 已文档化 |
| approval-field-control.js | 审批字段控制工具 | 审批编辑模式下的字段启用/禁用控制 | 2 | ✅ 已文档化 |
| quotation-modal.js | 报价单模态框表单模块 | 报价单创建/编辑模态框 | 2 | ✅ 已文档化 |
| spec-editor.js | 规格编辑管理器 | 产品/研发产品的规格编辑功能 | 2 | ✅ 已文档化 |
| spec-dictionary-manager.js | 规格字典管理器 | 规格字典和指标的完整CRUD管理 | 1 | ✅ 已文档化 🆕 |

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

### 📝 表单工具类

#### customer-form.js

**基本信息**

- **文件路径**: `app/static/js/customer-form.js`
- **版本**: 1.0.0
- **创建日期**: 2025-12-06
- **文件大小**: 374 行

**功能描述**

客户表单公共逻辑模块，用于客户新建和编辑表单。封装了国家/地区、行业、企业类型、来源等下拉框的数据加载和填充逻辑，以及表单提交（创建/更新）功能。

**使用场景**

- 新建客户模态框
- 编辑客户模态框
- 任何需要客户表单的页面

**已使用页面**

1. `app/templates/customer/tw_view.html` - 客户详情页（编辑客户模态框）
2. `app/templates/customer/tw_list.html` - 客户列表页（新建客户模态框）

**API 文档**

```javascript
// 模块命名空间
window.CustomerForm = {
    init: initForm,              // 初始化表单
    submit: submitForm,          // 提交表单
    reset: resetForm,            // 重置表单
    loadCompanyData: loadCompanyData,    // 加载客户数据
    populateFormData: populateFormData,  // 填充表单数据
    populateCountry: populateCountrySelect,  // 填充国家下拉框
    populateRegion: populateRegionSelect,    // 填充地区下拉框
    populateSelect: populateSelect,          // 填充通用下拉框
    isInitialized: function() { return isInitialized; },
    API: API  // API端点常量
};
```

**参数说明**

**init(config)**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| config.countryId | string | ❌ | 'country' | 国家select的ID |
| config.regionId | string | ❌ | 'region' | 地区select的ID |
| config.industryId | string | ❌ | 'industry' | 行业select的ID |
| config.companyTypeId | string | ❌ | 'company_type' | 企业类型select的ID |
| config.sourceId | string | ❌ | 'source' | 来源select的ID |
| config.placeholders | object | ❌ | {...} | 各下拉框的占位文本 |

**submit(formId, mode, companyId, callbacks)**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| formId | string | ✅ | - | 表单ID |
| mode | string | ✅ | - | 模式：'create' 或 'update' |
| companyId | number | 条件 | null | 公司ID（update模式必填） |
| callbacks.onSuccess | function | ❌ | null | 成功回调 |
| callbacks.onError | function | ❌ | null | 失败回调 |
| callbacks.i18n | object | ❌ | {...} | 国际化文本 |

**使用示例**

```html
<!-- 引入模块 -->
<script src="{{ url_for('static', filename='js/customer-form.js') }}"></script>

<!-- 新建客户模态框使用示例 -->
<script>
(function() {
    const i18n = {
        country: '请选择国家',
        region: '请选择省/州',
        industry: '请选择行业',
        companyType: '请选择企业类型',
        source: '请选择来源',
        creating: '创建中...',
        create: '创建',
        saveError: '保存失败，请重试'
    };

    let isFormInitialized = false;

    // 打开新建客户模态框
    window.openAddCustomerModal = async function() {
        if (!isFormInitialized) {
            const result = await CustomerForm.init({ placeholders: i18n });
            if (!result) return;

            document.getElementById('customerFormModal-form').onsubmit = async function(e) {
                e.preventDefault();
                await CustomerForm.submit('customerFormModal-form', 'create', null, {
                    i18n: i18n,
                    onSuccess: function(result) {
                        closeFormModal('customerFormModal');
                        window.location.href = '/customer/' + result.data.id + '/view';
                    }
                });
            };
            isFormInitialized = true;
        }

        CustomerForm.reset('customerFormModal-form', { placeholders: i18n });
        openFormModal('customerFormModal');
    };
})();
</script>

<!-- 编辑客户模态框使用示例 -->
<script>
(function() {
    const companyId = 123;

    window.openCustomerEditModal = async function() {
        await CustomerForm.init({ placeholders: i18n });

        const customerData = await CustomerForm.loadCompanyData(companyId);
        if (!customerData) return;

        CustomerForm.populateFormData(customerData, { placeholders: i18n });
        openFormModal('customerFormModal');
    };
})();
</script>
```

**依赖关系**

- **API依赖**:
  - `/customer/api/countries-regions` - 获取国家地区数据
  - `/customer/api/company/options` - 获取表单选项（行业、类型、来源）
  - `/customer/api/company/create` - 创建客户
  - `/customer/api/company/<id>/update` - 更新客户
  - `/customer/api/company/<id>` - 获取客户数据

- **前端依赖**: 无（纯JavaScript模块）

- **CSS依赖**: 无

**重构记录**

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2025-12-06 | 1.0.0 | 从 tw_view.html 和 tw_list.html 提取公共逻辑，消除约 330 行重复代码 |

---

#### quotation-modal.js

**基本信息**

- **文件路径**: `app/static/js/quotation-modal.js`
- **版本**: 1.0.0
- **创建日期**: 2025-12-12
- **文件大小**: 约 600 行

**功能描述**

报价单模态框表单模块，用于新建和编辑报价单的模态框通用逻辑。封装了项目搜索、客户/联系人级联加载、产品明细表格、表单提交等功能。支持预设项目（如从项目详情页打开时自动填充项目信息）。

**使用场景**

- 报价单列表页新建报价单
- 项目详情页快速创建报价单（预设项目）
- 任何需要报价单创建/编辑模态框的页面

**已使用页面**

1. `app/templates/quotation/tw_list.html` - 报价单列表页
2. `app/templates/project/tw_project_detail.html` - 项目详情页

**核心功能**

- ✅ 项目搜索与选择（支持关键词搜索）
- ✅ 客户级联加载（根据项目加载关联客户）
- ✅ 联系人级联加载（根据客户加载联系人）
- ✅ 产品明细表格（支持添加/删除/编辑产品）
- ✅ 自动计算总金额
- ✅ 表单验证
- ✅ 支持预设项目（项目详情页场景）
- ✅ 可配置的国际化文本
- ✅ 可配置的 API 端点
- ✅ 自定义成功回调

**API 文档**

```javascript
// 模块命名空间
window.QuotationModal = {
    init: init,                      // 初始化模块
    initProductTable: initProductTable,  // 初始化产品表格
    initProductSelector: initProductSelector,  // 初始化产品选择器
    searchProjects: searchProjects,  // 项目搜索
    selectProject: selectProject,    // 选择项目
    clearProject: clearProject,      // 清除项目选择
    loadProjectCustomers: loadProjectCustomers,  // 加载项目客户
    loadCustomerContacts: loadCustomerContacts,  // 加载客户联系人
    reset: reset,                    // 重置表单
    setPresetProject: setPresetProject,  // 设置预设项目
    collectFormData: collectFormData,    // 收集表单数据
    validate: validate,              // 验证表单
    submit: submit,                  // 提交表单
    getConfig: getConfig             // 获取配置
};

// 全局函数
window.openAddQuotationModal = function(options) { ... };
```

**参数说明**

**init(options)**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| options.i18n | Object | ❌ | {...} | 国际化文本配置 |
| options.urls | Object | ❌ | {...} | API URL 配置 |
| options.presetProjectId | number | ❌ | null | 预设项目ID |
| options.presetProjectName | string | ❌ | null | 预设项目名称 |
| options.onSuccess | function | ❌ | null | 成功回调函数 |

**i18n 配置项**

| 键 | 默认值 | 说明 |
|---|--------|------|
| loading | '加载中...' | 加载状态文本 |
| pleaseSelectProject | '-- 请先选择项目 --' | 客户下拉框默认提示 |
| pleaseSelectCustomer | '请选择客户' | 客户选择提示 |
| noCustomersFound | '该项目暂无关联客户' | 无客户提示 |
| pleaseSelectContact | '请选择联系人' | 联系人选择提示 |
| noContactsFound | '该客户暂无联系人' | 无联系人提示 |
| creating | '创建中...' | 创建按钮加载文本 |
| create | '创建' | 创建按钮文本 |
| saving | '保存中...' | 保存按钮加载文本 |
| save | '保存' | 保存按钮文本 |
| saveError | '保存失败，请重试' | 保存失败提示 |
| loadError | '加载数据失败，请重试' | 加载失败提示 |
| projectRequired | '请选择关联项目' | 项目必填验证 |
| customerRequired | '请选择客户' | 客户必填验证 |
| productRequired | '请至少添加一个产品' | 产品必填验证 |
| manualInput | '手动输入' | 产品选择器手动输入选项 |
| tempIndicator | '临时' | 临时产品标识 |
| noProjectsFound | '未找到匹配的项目' | 项目搜索无结果 |
| newQuotation | '新建报价单' | 模态框标题 |

**urls 配置项**

| 键 | 默认值 | 说明 |
|---|--------|------|
| createQuotation | '/quotation/create' | 创建报价单 API |
| searchProjects | '/quotation/search_projects' | 项目搜索 API |
| getProjectCustomers | '/quotation/get_project_customers' | 获取项目客户 API |
| getCustomerContacts | '/quotation/get_customer_contacts' | 获取客户联系人 API |

**openAddQuotationModal(options)**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| options.presetProjectId | number | ❌ | null | 预设项目ID |
| options.presetProjectName | string | ❌ | null | 预设项目名称 |

**使用示例**

**1. 报价单列表页使用**

```html
<!-- 引入依赖 -->
<script src="{{ url_for('static', filename='js/product-selector.js') }}"></script>
<script src="{{ url_for('static', filename='js/product-config-modal.js') }}"></script>
<script src="{{ url_for('static', filename='js/quotation-modal.js') }}"></script>

<!-- 初始化模块 -->
<script>
(function() {
    QuotationModal.init({
        i18n: {
            loading: '{{ _("加载中...") }}',
            pleaseSelectProject: '{{ _("-- 请先选择项目 --") }}',
            pleaseSelectCustomer: '{{ _("请选择客户") }}',
            noCustomersFound: '{{ _("该项目暂无关联客户") }}',
            pleaseSelectContact: '{{ _("请选择联系人") }}',
            noContactsFound: '{{ _("该客户暂无联系人") }}',
            creating: '{{ _("创建中...") }}',
            create: '{{ _("创建") }}',
            saving: '{{ _("保存中...") }}',
            save: '{{ _("保存") }}',
            saveError: '{{ _("保存失败，请重试") }}',
            loadError: '{{ _("加载数据失败，请重试") }}',
            projectRequired: '{{ _("请选择关联项目") }}',
            customerRequired: '{{ _("请选择客户") }}',
            productRequired: '{{ _("请至少添加一个产品") }}',
            manualInput: '{{ _("手动输入") }}',
            tempIndicator: '{{ _("临时") }}',
            noProjectsFound: '{{ _("未找到匹配的项目") }}',
            newQuotation: '{{ _("新建报价单") }}'
        },
        urls: {
            createQuotation: '{{ url_for("quotation.create_quotation") }}',
            searchProjects: '/quotation/search_projects',
            getProjectCustomers: '/quotation/get_project_customers',
            getCustomerContacts: '/quotation/get_customer_contacts'
        }
    });
})();
</script>

<!-- 创建按钮 -->
<button type="button" onclick="openAddQuotationModal()">创建报价单</button>
```

**2. 项目详情页使用（预设项目）**

```html
<!-- 初始化模块并预设项目 -->
<script>
(function() {
    QuotationModal.init({
        i18n: { ... },
        urls: { ... },
        // 预设项目信息
        presetProjectId: {{ project.id }},
        presetProjectName: '{{ project.project_name|e }}'
    });
})();
</script>

<!-- 创建按钮（传递预设项目参数） -->
<button type="button" onclick="openAddQuotationModal({ presetProjectId: {{ project.id }}, presetProjectName: '{{ project.project_name|e }}' })">
    添加报价单
</button>
```

**3. 自定义成功回调**

```javascript
QuotationModal.init({
    i18n: { ... },
    urls: { ... },
    onSuccess: function(result) {
        // 自定义成功处理，例如刷新列表而不跳转
        showTopNotification('success', '报价单创建成功！');
        loadQuotationList();  // 刷新报价单列表
    }
});
```

**元素ID约定**

模态框使用以下固定的元素ID（带Modal后缀以避免冲突）：

| 元素ID | 说明 |
|--------|------|
| projectSearchModal | 项目搜索输入框 |
| projectDropdownModal | 项目搜索下拉框 |
| projectResultsModal | 项目搜索结果容器 |
| project_id_modal | 项目ID隐藏字段 |
| clearProjectBtnModal | 清除项目按钮 |
| customer_id_modal | 客户下拉框 |
| contact_id_modal | 联系人下拉框 |
| currency_modal | 货币下拉框 |
| quotationProductTable | 产品明细表格 |
| quotationProductTableBody | 产品表格tbody |
| grandTotalModal | 总金额显示 |
| quotationFormModal-form | 表单元素 |
| quotationFormModal-submit-btn | 提交按钮 |

**依赖关系**

- **API依赖**:
  - `/quotation/create` - 创建报价单
  - `/quotation/search_projects` - 搜索项目
  - `/quotation/get_project_customers/{id}` - 获取项目客户
  - `/quotation/get_customer_contacts/{id}` - 获取客户联系人

- **前端依赖**:
  - `tw_form_modal` 组件 - 提供 `openFormModal`/`closeFormModal` 函数
  - `tw_editable_table` 组件 - 提供产品明细表格功能
  - `ProductSelector` 类 - 提供产品四级选择功能
  - CSRF token meta 标签

- **模板依赖**:
  - `quotation/partials/_quotation_modal_fields.html` - 模态框表单字段

**重构记录**

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2025-12-12 | 1.0.0 | 从 tw_list.html 提取约 400 行内联 JavaScript 为可复用模块 |

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

---

#### tw-list-manager.js

**基本信息**
- **文件路径**: `app/static/js/tw-list-manager.js`
- **功能描述**: Tailwind列表页面通用管理器，提供排序和无限滚动功能
- **依赖库**: 无外部依赖
- **创建日期**: 2025-12-07

**已使用页面**
1. `project/tw_list.html` - 项目管理列表页
2. `customer/tw_list.html` - 客户管理列表页

**API文档**

```javascript
/**
 * Tailwind 列表管理器构造函数
 *
 * @param {Object} config - 配置对象
 * @param {string} config.tableId - 表格ID
 * @param {string} config.formId - 筛选表单ID
 * @param {string} config.ajaxEndpoint - AJAX加载端点
 * @param {number} [config.pageSize=30] - 每页数量
 * @param {number} [config.initialCount=0] - 初始数据数量
 * @param {string} [config.sortField='updated_at'] - 默认排序字段
 * @param {string} [config.sortOrder='desc'] - 默认排序方向
 * @param {boolean} [config.infiniteScroll=true] - 是否启用无限滚动
 * @param {Object} [config.messages] - 自定义消息文本
 */
const listManager = new TwListManager(config);
listManager.init();
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| tableId | string | ✅ | - | 表格ID（如'projectTable'） |
| formId | string | ✅ | - | 筛选表单ID（如'filterForm'） |
| ajaxEndpoint | string | ✅ | - | AJAX加载端点URL |
| pageSize | number | ❌ | 30 | 每页加载数量 |
| initialCount | number | ❌ | 0 | 初始已加载的数据数量 |
| sortField | string | ❌ | 'updated_at' | 默认排序字段 |
| sortOrder | string | ❌ | 'desc' | 默认排序方向 |
| infiniteScroll | boolean | ❌ | true | 是否启用无限滚动 |
| messages | object | ❌ | {} | 自定义消息文本（支持国际化） |

**DOM元素要求**

表格组件需要包含以下ID格式的元素（以tableId='projectTable'为例）：

| 元素ID | 作用 | 说明 |
|--------|------|------|
| projectTableBody | 表格内容容器 | tbody元素，用于插入新行 |
| projectTableLoadingMore | 加载中指示器 | 显示"加载中..."状态 |
| projectTableNoMore | 无更多数据提示 | 显示"没有更多数据" |
| projectTableSentinel | 滚动触发器 | IntersectionObserver监听元素 |

**使用示例**

```html
<!-- 引入脚本 -->
<script src="{{ url_for('static', filename='js/tw-list-manager.js') }}"></script>

<script>
(function() {
    // 初始化列表管理器
    const listManager = new TwListManager({
        tableId: 'projectTable',
        formId: 'filterForm',
        ajaxEndpoint: '{{ url_for("project.project_list_ajax") }}',
        pageSize: 30,
        initialCount: {{ projects|length }},
        sortField: '{{ request.args.get("sort", "updated_at") }}',
        sortOrder: '{{ request.args.get("order", "desc") }}',
        messages: {
            loadingMore: '{{ _("加载中...") }}',
            noMoreData: '{{ _("没有更多数据") }}',
            loadError: '{{ _("加载数据失败") }}'
        }
    });
    listManager.init();

    // 暴露排序函数供表格组件调用
    window.sortTable = function(field) {
        listManager.sortBy(field);
    };
})();
</script>
```

**主要方法**

| 方法 | 说明 |
|------|------|
| init() | 初始化管理器，设置排序和无限滚动 |
| sortBy(field) | 按指定字段排序，触发页面跳转 |
| loadMore() | 加载更多数据 |
| reset() | 重置列表，清空数据重新加载 |
| refresh() | 刷新列表，重新加载所有已加载的数据 |

**AJAX响应格式**

服务器端需要返回以下格式的JSON响应：

```json
{
    "success": true,
    "html": "<tr>...</tr>",
    "has_more": true,
    "offset": 60,
    "count": 30
}
```

**相关工具**

| 工具 | 说明 |
|------|------|
| query_filters.py | 后端筛选参数提取工具 |
| list_config_builder.py | 后端列表配置构建器 |
| tw_data_table.html | Tailwind数据表格组件 |
| tw_filter_bar.html | Tailwind筛选栏组件 |

**维护日志**

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2025-12-07 | 1.0.0 | 初始版本，从项目管理和客户管理提取公共逻辑 |

---

---

### 🔐 审批流程工具类

#### approval-field-control.js

**基本信息**

- **文件路径**: `app/static/js/approval-field-control.js`
- **版本**: 1.0.0
- **创建日期**: 2025-12-11
- **文件大小**: 约350行
- **依赖**: 无外部依赖

**功能描述**

通用审批字段控制工具，通过模板属性 `data-field-code` 自动控制字段的启用/禁用状态。用于审批流程中限制用户只能编辑特定字段，替代每个模块硬编码字段映射的方式。

**使用场景**

- 报销单审批编辑模式
- 项目审批编辑模式
- 报价单审批编辑模式
- 任何需要在审批流程中控制字段编辑权限的场景

**已使用页面**

1. `app/templates/expense/tw_expense_detail.html` - 报销单详情页
2. `app/templates/expense/tw_list.html` - 报销单列表页

**核心功能**

- ✅ 通过 `data-field-code` 属性自动识别字段
- ✅ 支持多种控件类型（input, select, textarea, button）
- ✅ 支持搜索框组（search, value, clear 角色）
- ✅ 支持文件上传和删除预览按钮
- ✅ 自动禁用操作按钮（添加行、删除行）
- ✅ 可编辑字段高亮显示（琥珀色背景）
- ✅ 不可编辑字段灰色背景 + 禁用状态
- ✅ 支持明细行动态控制

**模板属性说明**

| 属性 | 说明 | 示例 |
|------|------|------|
| `data-field-code` | 字段代码，与审批模板配置一致 | `data-field-code="title"` |
| `data-field-role` | 控件角色（可选） | `data-field-role="search"` |

**控件角色 (data-field-role)**

| 角色 | 说明 | 处理方式 |
|------|------|---------|
| `search` | 搜索输入框 | 启用/禁用 + 样式 |
| `value` | 隐藏值字段 | 不做样式处理 |
| `clear` | 清除按钮 | 隐藏或禁用 |
| `upload` | 文件上传 | 启用/禁用 + 样式 |
| `delete-preview` | 删除预览按钮 | 隐藏或禁用 |

**特殊字段代码**

| 代码 | 说明 |
|------|------|
| `__add_row__` | 添加行按钮（审批模式下始终禁用） |
| `__delete_row__` | 删除行按钮（审批模式下始终禁用） |
| `__no_customer_mode__` | 不关联客户复选框 |

**API文档**

```javascript
/**
 * 应用字段控制
 * @param {HTMLElement|string} container - 容器元素或选择器
 * @param {Array<string>} editableFields - 可编辑字段代码列表
 * @param {Object} options - 可选配置
 * @returns {Object} - { success: boolean, stats: object }
 */
ApprovalFieldControl.apply(container, editableFields, options)

/**
 * 应用明细行控制（用于动态添加的行）
 * @param {HTMLElement} row - 明细行元素
 * @param {Array<string>} editableFields - 可编辑字段代码列表
 * @param {Object} options - 可选配置
 */
ApprovalFieldControl.applyToRow(row, editableFields, options)

/**
 * 重置字段状态（恢复为可编辑）
 * @param {HTMLElement|string} container - 容器元素或选择器
 */
ApprovalFieldControl.reset(container)
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| container | HTMLElement/string | ✅ | - | 容器元素或CSS选择器 |
| editableFields | Array<string> | ✅ | [] | 可编辑字段代码列表 |
| options.editableClasses | Array | ❌ | ['bg-amber-50', 'dark:bg-amber-900/20'] | 可编辑样式 |
| options.disabledClasses | Array | ❌ | ['bg-slate-100', 'dark:bg-slate-700', 'cursor-not-allowed', 'opacity-60'] | 不可编辑样式 |
| options.buttonDisabledClasses | Array | ❌ | ['opacity-50', 'cursor-not-allowed'] | 按钮禁用样式 |
| options.hideClearButtons | boolean | ❌ | true | 是否隐藏禁用的清除按钮 |
| options.hideDeleteButtons | boolean | ❌ | true | 是否隐藏禁用的删除按钮 |
| options.disableActionButtons | boolean | ❌ | true | 是否禁用操作按钮 |
| options.debug | boolean | ❌ | false | 是否开启调试日志 |

**模板使用示例**

```html
<!-- 1. 普通控件 -->
<input type="text" name="title" data-field-code="title">
<select name="currency" data-field-code="main_currency">
<textarea name="description" data-field-code="main_description"></textarea>

<!-- 2. 搜索框组（使用 data-field-role 区分） -->
<input type="text" data-field-code="customer_id" data-field-role="search">
<input type="hidden" data-field-code="customer_id" data-field-role="value">
<button data-field-code="customer_id" data-field-role="clear">清除</button>

<!-- 3. 文件上传 -->
<label data-field-code="invoice_images" data-field-role="upload">
    <input type="file" name="invoice_files">
</label>

<!-- 4. 操作按钮（审批模式下始终禁用） -->
<button data-field-code="__add_row__">添加明细</button>
<button data-field-code="__delete_row__">删除</button>
```

**JavaScript调用示例**

```javascript
// 1. 引入工具
<script src="{{ url_for('static', filename='js/approval-field-control.js') }}"></script>

// 2. 应用字段控制
const editableFields = ['exchange_rate', 'invoice_amount'];  // 从审批模板获取
const form = document.getElementById('myForm');

ApprovalFieldControl.apply(form, editableFields, { debug: true });

// 3. 为动态添加的明细行应用控制
function addDetailRow() {
    const row = createNewRow();
    tbody.appendChild(row);

    // 如果在审批编辑模式，应用字段控制
    if (approvalEditMode) {
        ApprovalFieldControl.applyToRow(row, editableFields);
    }
}

// 4. 重置（退出审批模式时）
ApprovalFieldControl.reset(form);
```

**在 expense-modal.js 中的集成**

```javascript
// 应用审批编辑模式的字段限制
applyApprovalEditRestrictions: function() {
    const form = document.getElementById(config.modalId + '-form');
    if (form && typeof ApprovalFieldControl !== 'undefined') {
        ApprovalFieldControl.apply(form, this.editableFields, { debug: true });
    }
},

// 应用明细行字段限制
applyDetailRowRestrictions: function(row) {
    if (typeof ApprovalFieldControl !== 'undefined') {
        ApprovalFieldControl.applyToRow(row, this.editableFields, { debug: true });
    }
}
```

**样式效果**

| 状态 | 样式 | 说明 |
|------|------|------|
| 可编辑 | `bg-amber-50 dark:bg-amber-900/20` | 琥珀色背景高亮 |
| 不可编辑 | `bg-slate-100 dark:bg-slate-700 cursor-not-allowed opacity-60` | 灰色背景 + 禁用 |
| 按钮禁用 | `opacity-50 cursor-not-allowed` | 半透明 + 禁用光标 |

**代码量对比**

| 项目 | 旧实现 | 新实现 |
|------|--------|--------|
| expense-modal.js 字段控制 | ~200行 | ~15行调用 |
| 通用工具 | 0 | ~350行(一次性) |
| 新模块接入 | ~200行/模块 | ~15行/模块 |

**字段代码对照表（报销单）**

**主表字段**

| 字段代码 | 控件 | 说明 |
|---------|------|------|
| title | expense_title | 报销主题 |
| main_currency | expense_currency | 主表货币 |
| main_description | expense_description | 主表描述 |
| customer_id | 搜索框组 | 关联客户 |
| contact_id | expense_contact_id | 联系人 |
| project_id | 搜索框组 | 关联项目 |

**明细字段**

| 字段代码 | 控件name | 说明 |
|---------|---------|------|
| expense_date | expense_date | 日期 |
| expense_category | expense_category | 科目 |
| description | detail_description | 描述 |
| document_count | document_count | 单据数 |
| currency | detail_currency | 货币 |
| invoice_amount | invoice_amount | 金额 |
| exchange_rate | exchange_rate | 汇率 |
| invoice_images | 文件上传 | 发票 |

**扩展到其他模块**

要在新模块（如项目、报价单）中使用此工具：

1. **修改模板**：为所有需要控制的控件添加 `data-field-code` 属性
2. **引入工具**：在页面中引入 `approval-field-control.js`
3. **调用方法**：在审批编辑模式下调用 `ApprovalFieldControl.apply()`

**维护日志**

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2025-12-11 | 1.0.0 | 初始版本，从报销单审批编辑功能重构而来 |

---

#### spec-editor.js

**基本信息**

- **文件路径**: `app/static/js/spec-editor.js`
- **版本**: 1.0.0
- **创建日期**: 2025-12-13
- **文件大小**: 约708行
- **依赖**: 无外部依赖

**功能描述**

通用规格编辑管理器，用于产品和研发产品详情页的规格编辑功能。封装了编辑模式切换、新增规格行、编辑确认/取消、指标选项加载、数据保存等完整功能，支持配置化的API端点和国际化文本。

**使用场景**

- 产品库详情页规格编辑
- 研发产品详情页规格编辑
- 任何需要编辑产品规格列表的页面

**已使用页面**

1. `app/templates/product_management/tw_product_detail.html` - 研发产品详情页
2. `app/templates/product/tw_product_detail.html` - 产品库详情页

**核心功能**

- ✅ 编辑模式切换（显示/隐藏编辑控件）
- ✅ 新增规格行（从规格字典选择）
- ✅ 确认/取消新增行
- ✅ 编辑/确认/取消现有规格
- ✅ 删除未保存的新规格行
- ✅ 指标选项动态加载（带缓存）
- ✅ 应用按钮状态控制（有未确认编辑时禁用）
- ✅ 保存变更到服务器
- ✅ 可配置的API端点
- ✅ 可配置的国际化文本
- ✅ 可配置的成功回调

**API文档**

```javascript
/**
 * 规格编辑管理器
 * @param {Object} options - 配置选项
 */
const specEditor = new SpecEditor(options);
specEditor.init();
```

**配置选项说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| productId | number | ✅ | - | 产品ID |
| apiEndpoint | string | ✅ | - | 保存规格的API端点 |
| containerId | string | ❌ | 'productSpecsContainer' | 规格容器ID |
| listId | string | ❌ | 'productSpecsList' | 规格列表ID |
| buttons | object | ❌ | {} | 按钮ID配置 |
| buttons.edit | string | ❌ | 'editSpecsBtn' | 编辑按钮ID |
| buttons.apply | string | ❌ | 'applySpecsBtn' | 应用按钮ID |
| buttons.cancel | string | ❌ | 'cancelSpecsBtn' | 取消按钮ID |
| buttons.add | string | ❌ | 'addSpecBtn' | 添加按钮ID |
| i18n | object | ❌ | {...} | 国际化文本 |
| csrfToken | string | ❌ | '' | CSRF令牌 |
| onSaveSuccess | function | ❌ | null | 保存成功回调 |

**i18n 配置项**

| 键 | 默认值 | 说明 |
|---|--------|------|
| selectSpec | '请选择规格' | 规格下拉框默认选项 |
| selectOption | '请选择指标' | 指标下拉框默认选项 |
| loading | '加载中...' | 加载状态文本 |
| confirm | '确认' | 确认按钮文本 |
| cancel | '取消' | 取消按钮文本 |
| edit | '编辑' | 编辑按钮文本 |
| delete | '删除' | 删除按钮文本 |
| applyDisabledTitle | '请先确认所有编辑中的规格' | 应用按钮禁用提示 |
| saveSuccess | '规格保存成功' | 保存成功提示 |
| saveFailed | '规格保存失败' | 保存失败提示 |

**主要方法**

| 方法 | 说明 |
|------|------|
| init() | 初始化编辑器，设置事件委托 |
| toggleEditMode() | 切换编辑模式 |
| cancelEditMode() | 取消编辑模式，恢复原始数据 |
| applyChanges() | 应用更改，保存到服务器 |
| addNewSpecRow() | 添加新规格行 |
| confirmNewSpecRow(row) | 确认新规格行 |
| cancelNewSpecRow(row) | 取消新规格行 |
| deleteNewSpec(row) | 删除未保存的新规格行 |
| toggleSpecEdit(btn) | 切换现有规格的编辑状态 |
| loadSpecOptions(specId, selectEl, specName) | 加载指标选项 |
| updateApplyButtonState() | 更新应用按钮状态 |

**使用示例**

```html
<!-- 1. 引入脚本 -->
<script src="{{ url_for('static', filename='js/spec-editor.js') }}"></script>

<!-- 2. 规格卡片HTML结构 -->
<div id="productSpecsContainer" class="card">
    <div class="card-header flex justify-between items-center">
        <span>产品规格</span>
        <div class="flex items-center gap-2">
            <!-- 添加按钮（编辑模式显示） -->
            <button id="addSpecBtn" onclick="addNewSpecRow()" class="hidden">
                添加
            </button>
            <!-- 编辑/应用/取消按钮 -->
            <button id="editSpecsBtn" onclick="toggleSpecEditMode()">编辑</button>
            <button id="applySpecsBtn" onclick="applySpecChanges()" class="hidden">应用</button>
            <button id="cancelSpecsBtn" onclick="cancelSpecEditMode()" class="hidden">取消</button>
        </div>
    </div>
    <div id="productSpecsList">
        <!-- 规格列表 -->
        <div class="spec-row" data-spec-id="1">
            <span class="spec-name">颜色</span>
            <span class="spec-value">红色</span>
            <span class="spec-unit">-</span>
            <div class="spec-edit-controls hidden">
                <select class="option-select">...</select>
                <button onclick="toggleSpecEdit(this)">确认</button>
            </div>
        </div>
    </div>
</div>

<!-- 3. 初始化编辑器 -->
<script>
(function() {
    const specI18n = {
        selectSpec: '{{ _("请选择规格") }}',
        selectOption: '{{ _("请选择指标") }}',
        loading: '{{ _("加载中...") }}',
        confirm: '{{ _("确认") }}',
        cancel: '{{ _("取消") }}',
        edit: '{{ _("编辑") }}',
        delete: '{{ _("删除") }}',
        applyDisabledTitle: '{{ _("请先确认所有编辑中的规格") }}',
        saveSuccess: '{{ _("规格保存成功") }}',
        saveFailed: '{{ _("规格保存失败") }}'
    };

    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    const productId = {{ dev_product.id }};

    // 使用可复用的规格编辑器
    const specEditor = new SpecEditor({
        productId: productId,
        apiEndpoint: `/product-management/api/rd-products/${productId}/specs`,
        containerId: 'productSpecsContainer',
        listId: 'productSpecsList',
        buttons: {
            edit: 'editSpecsBtn',
            apply: 'applySpecsBtn',
            cancel: 'cancelSpecsBtn',
            add: 'addSpecBtn'
        },
        i18n: specI18n,
        csrfToken: csrfToken,
        onSaveSuccess: function() {
            window.location.reload();
        }
    });
    specEditor.init();

    // 暴露全局函数供模板调用
    window.toggleSpecEditMode = () => specEditor.toggleEditMode();
    window.cancelSpecEditMode = () => specEditor.cancelEditMode();
    window.applySpecChanges = () => specEditor.applyChanges();
    window.addNewSpecRow = () => specEditor.addNewSpecRow();
    window.toggleSpecEdit = (btn) => specEditor.toggleSpecEdit(btn);
    window.confirmNewSpecRow = (btn) => {
        const row = btn.closest('.spec-row');
        specEditor.confirmNewSpecRow(row);
    };
    window.cancelNewSpecRow = (btn) => {
        const row = btn.closest('.spec-row');
        specEditor.cancelNewSpecRow(row);
    };
    window.deleteNewSpec = (btn) => {
        const row = btn.closest('.spec-row');
        specEditor.deleteNewSpec(row);
    };
})();
</script>
```

**规格行HTML结构要求**

```html
<!-- 新增规格行模板 -->
<div class="spec-row new-row" data-spec-id="" data-confirmed="false">
    <!-- 规格选择下拉框 -->
    <select class="spec-select" onchange="specEditor.onSpecSelect(this)">
        <option value="">请选择规格</option>
        <option value="1" data-name="颜色">颜色</option>
    </select>

    <!-- 指标选择下拉框 -->
    <select class="option-select">
        <option value="">请选择指标</option>
    </select>

    <!-- 单位显示 -->
    <span class="spec-unit">-</span>

    <!-- 操作按钮 -->
    <button onclick="confirmNewSpecRow(this)">确认</button>
    <button onclick="cancelNewSpecRow(this)">取消</button>
</div>

<!-- 已确认规格行 -->
<div class="spec-row" data-spec-id="1" data-confirmed="true">
    <span class="spec-name">颜色</span>
    <span class="spec-value">红色</span>
    <span class="spec-unit">-</span>

    <!-- 编辑模式控件（默认隐藏） -->
    <div class="spec-edit-controls hidden">
        <select class="option-select">...</select>
        <button onclick="toggleSpecEdit(this)">编辑/确认</button>
        <button class="delete-btn" onclick="deleteNewSpec(this)">删除</button>
    </div>
</div>
```

**后端API要求**

```python
# 保存规格API
@app.route('/api/products/<int:product_id>/specs', methods=['POST'])
def save_specs(product_id):
    """
    请求格式:
    {
        "specs": [
            {
                "spec_field_id": 1,           # 规格字段ID
                "spec_field_option_id": 10,   # 指标选项ID
                "spec_name": "颜色",           # 规格名称
                "value": "红色",               # 指标值
                "unit": "-"                   # 单位
            }
        ]
    }

    返回格式:
    {
        "success": true,
        "message": "保存成功"
    }
    """
```

**与规格选项管理模态框集成**

```javascript
// 打开规格选项管理模态框时传递回调
window.openSpecOptionsModal = function(specId, specName, options = {}) {
    // 传递回调函数，关闭模态框后刷新指标选项
    if (specEditor.currentEditingSelect) {
        options.onClose = function() {
            specEditor.loadSpecOptions(
                specId,
                specEditor.currentEditingSelect,
                specName,
                true  // forceReload = true
            );
        };
    }
    // 打开模态框...
};
```

**状态管理**

| 状态 | 说明 |
|------|------|
| 查看模式 | 只显示规格值，隐藏编辑控件 |
| 编辑模式 | 显示编辑按钮和添加按钮 |
| 行编辑中 | 该行处于编辑状态，需确认或取消 |
| 新行未确认 | 新增的规格行尚未确认 |
| 有未确认编辑 | 存在未确认的编辑，应用按钮禁用 |

**依赖关系**

- **API依赖**:
  - 保存规格API: `${apiEndpoint}` (POST)
  - 获取指标选项API: `/product-management/api/spec-fields/${specId}/options`

- **前端依赖**:
  - CSRF token meta 标签
  - showTopNotification 函数（可选，用于提示）

- **组件依赖**:
  - tw_spec_options_modal 组件（可选，用于管理规格选项）

**重构记录**

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2025-12-13 | 1.0.0 | 从 tw_product_detail.html 提取约 600 行内联代码为可复用模块 |

---

---

#### spec-dictionary-manager.js

**基本信息**

- **文件路径**: `app/static/js/spec-dictionary-manager.js`
- **模板路径**: `app/templates/components/tw_spec_dictionary_modal.html`
- **功能描述**: 规格字典和指标的完整CRUD管理模态框
- **依赖库**: 无外部依赖，仅需 CSRF token
- **创建日期**: 2025-12-14

**已使用页面**

1. 可嵌入任何需要管理规格字典的页面

**功能特性**

- 左右分栏布局：左侧规格列表，右侧详情和指标管理
- 规格搜索过滤
- 规格CRUD（创建、读取、更新、删除）
- 指标CRUD（创建、读取、更新、删除）
- 智能编码预览和自动生成
- 状态切换（启用/停用）
- 深色模式支持
- 国际化支持

**API文档**

```javascript
// 显示规格字典管理模态框
SpecDictionaryManager.show();

// 隐藏模态框
SpecDictionaryManager.hide();

// 选择指定规格
SpecDictionaryManager.selectSpec(specId);

// 过滤规格列表
SpecDictionaryManager.filterSpecs(keyword);

// 显示添加规格表单
SpecDictionaryManager.showAddSpecForm();

// 显示编辑规格表单
SpecDictionaryManager.showEditSpecForm();

// 显示添加指标表单
SpecDictionaryManager.showAddOptionForm();

// 显示编辑指标表单
SpecDictionaryManager.showEditOptionForm(optionId);

// 切换指标状态
SpecDictionaryManager.toggleOptionStatus(optionId);

// 预览编码（输入指标值时自动调用）
SpecDictionaryManager.previewCode(value);
```

**使用示例**

```jinja2
{# 1. 在模板中引入模态框组件 #}
{% from 'components/tw_spec_dictionary_modal.html' import tw_spec_dictionary_modal, tw_spec_dictionary_script %}

{# 2. 在页面中渲染模态框 #}
{{ tw_spec_dictionary_modal() }}

{# 3. 在页面底部引入脚本 #}
{{ tw_spec_dictionary_script() }}
```

```html
<!-- 4. 添加打开按钮 -->
<button type="button" onclick="SpecDictionaryManager.show()"
        class="btn btn-primary">
    <span class="material-symbols-outlined">library_books</span>
    规格字典管理
</button>
```

**后端API依赖**

| API端点 | 方法 | 说明 |
|---------|------|------|
| `/api/spec-dictionary` | GET | 获取规格列表 |
| `/api/spec-dictionary` | POST | 创建规格 |
| `/api/spec-dictionary/:id` | PUT | 更新规格 |
| `/api/spec-dictionary/:id` | DELETE | 删除规格 |
| `/api/spec-dictionary/:id/toggle` | PUT | 切换规格状态 |
| `/api/spec-dictionary/:id/options` | GET | 获取指标列表 |
| `/api/spec-dictionary/:id/options` | POST | 创建指标 |
| `/api/spec-dictionary/:id/preview-code` | POST | 预览编码 |
| `/api/spec-dictionary/options/:id` | PUT | 更新指标 |
| `/api/spec-dictionary/options/:id` | DELETE | 删除指标 |
| `/api/spec-dictionary/options/:id/toggle` | PUT | 切换指标状态 |

**组件结构**

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 规格字典管理                                                    [×]     │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────────────────────────────────────────┐  │
│  │ 左侧规格列表 │   │ 右侧：规格详情 & 指标管理                       │  │
│  │ [搜索框]    │   │ ─────────────────────────────────────────────── │  │
│  │ [+添加]     │   │ 规格名称 | 单位 | 状态 | 创建时间               │  │
│  │             │   │ [编辑规格] [删除规格]                           │  │
│  │ ○ 规格1     │   │                                                 │  │
│  │ ○ 规格2     │   │ ─── 指标列表 ──────────────────── [+ 添加] ─   │  │
│  │ ○ 规格3     │   │ ┌─────────┬────────┬────────┬──────────────┐   │  │
│  │             │   │ │ 指标值  │ 编码   │ 状态   │ 操作         │   │  │
│  └─────────────┘   │ └─────────┴────────┴────────┴──────────────┘   │  │
│                    └─────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│  共 N 条指标记录                                              [关闭]    │
└─────────────────────────────────────────────────────────────────────────┘
```

**子模态框**

1. **specFormModal** - 添加/编辑规格表单
2. **optionFormModal** - 添加/编辑指标表单（带智能编码预览）
3. **specDeleteModal** - 删除确认弹窗

**重构记录**

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2025-12-14 | 1.0.0 | 创建规格字典管理模态框组件，复用现有后端API |

---

**版本**: 2.6.0
**最后更新**: 2025-12-14
**维护者**: Claude AI
