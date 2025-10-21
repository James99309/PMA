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

> **说明**:
> - ✅ 已文档化 - 有完整的API文档和使用示例
> - 📋 待补充文档 - 工具已存在但文档待完善
> - 🆕 新创建 - 最近新增的工具

---

## 📚 工具详细文档

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

**版本**: 1.0.0
**最后更新**: 2025-10-21
**维护者**: Claude AI
