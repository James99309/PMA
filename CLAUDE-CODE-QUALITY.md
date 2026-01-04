# PMA 项目代码质量与重构规范

## 📚 文档说明

本文档基于实际开发中遇到的代码质量问题和重构经验总结而成，旨在指导开发人员编写高质量、可维护的代码，避免重复造轮子和设计缺陷。

**适用对象**：
- Claude AI 助手 - 生成代码时必须遵循本规范
- 开发人员 - 编写和审查代码时的参考标准

---

## 🎯 核心原则

### **1. DRY原则 (Don't Repeat Yourself)**
- 同样的逻辑不应该在多个地方重复实现
- 发现重复代码时应立即重构
- 优先提取可复用的辅助函数

### **2. 单一职责原则**
- 每个函数应该只做一件事
- 复杂逻辑应拆分为多个小函数
- 函数名称应清晰表达其功能

### **3. 逻辑先行原则**
- 避免在if/else两个分支中重复相同的代码
- 先执行统一的处理逻辑，再根据条件分支
- 减少代码重复，提高可维护性

### **4. 适度拆分原则**
- 文件过大时应及时拆分
- 保持模块的内聚性和独立性
- 遵循合理的文件大小标准

---

## 📏 文件大小控制标准

### **Python文件**

| 级别 | 行数范围 | 处理策略 |
|------|---------|---------|
| ✅ **理想** | ≤ 1000行 | 无需处理，继续开发 |
| ⚠️ **警告** | 1000-1500行 | 开始考虑拆分，评估模块职责 |
| ⚠️ **严重警告** | 1500-2000行 | 必须计划拆分，不应继续添加新功能 |
| 🚫 **强制拆分** | ≥ 2000行 | 立即拆分，不允许继续扩展 |

**拆分建议**：
- **辅助函数模块**：将通用工具函数提取到独立文件（如 `approval_utils.py`）
- **业务逻辑分离**：按业务领域拆分（如 `approval_process.py`, `approval_actions.py`）
- **常量和配置**：提取到独立的配置文件（如 `approval_config.py`）

### **JavaScript文件**

| 级别 | 行数范围 | 处理策略 |
|------|---------|---------|
| ✅ **理想** | ≤ 800行 | 无需处理，继续开发 |
| ⚠️ **警告** | 800-1200行 | 开始考虑拆分，评估组件职责 |
| ⚠️ **严重警告** | 1200-1500行 | 必须计划拆分，不应继续添加新功能 |
| 🚫 **强制拆分** | ≥ 1500行 | 立即拆分，不允许继续扩展 |

**拆分建议**：
- **模块化设计**：使用ES6 modules拆分功能（如 `approval-flow-core.js`, `approval-flow-ui.js`）
- **组件分离**：将UI组件、数据处理、事件处理分离
- **工具函数库**：提取通用工具函数到独立文件（如 `approval-utils.js`）

### **HTML模板文件**

| 级别 | 行数范围 | 处理策略 |
|------|---------|---------|
| ✅ **理想** | ≤ 500行 | 无需处理，继续开发 |
| ⚠️ **警告** | 500-800行 | 开始考虑拆分，提取可复用组件 |
| ⚠️ **严重警告** | 800-1000行 | 必须计划拆分，不应继续添加新功能 |
| 🚫 **强制拆分** | ≥ 1000行 | 立即拆分，不允许继续扩展 |

**拆分建议**：
- **宏组件提取**：将重复的HTML片段提取为Jinja2宏（`macros/`）
- **布局继承**：使用模板继承减少重复（`base.html`, `page_base.html`）
- **局部模板**：将独立功能区域拆分为include文件

### **检查时机**

Claude AI助手在以下情况下应主动检查文件大小：
1. **新增代码时**：如果修改后文件可能超过警告阈值，提醒用户
2. **重构代码时**：主动评估是否需要拆分
3. **读取大文件时**：提醒文件已超过合理范围，建议拆分

### **Alpine.js 组件函数**

| 级别 | 行数范围 | 处理策略 |
|------|---------|---------|
| ✅ **理想** | ≤ 150行 | 无需处理，继续开发 |
| ⚠️ **警告** | 150-250行 | 开始考虑拆分，评估是否可提取 mixin |
| ⚠️ **严重警告** | 250-400行 | 必须计划拆分，不应继续添加新功能 |
| 🚫 **强制拆分** | ≥ 400行 | 立即拆分，不允许继续扩展 |

**拆分建议**：
- **Mixin 提取**：将重复的状态和方法提取为公共 mixin（如 `vendorUserSelectorMixin`）
- **外置 JS 文件**：将组件函数移到独立 JS 文件（如 `config-basic.js`）
- **辅助函数**：将复杂逻辑提取为独立辅助函数

**典型案例**：
- ❌ `salaryConfig()`: 815行 → 必须拆分
- ❌ `salaryAssignConfig()`: 657行 → 必须拆分
- ✅ `affiliationConfig()`: 116行 → 理想范围

---

## 🔧 前端组件预防规范

### **新增配置 Tab 前的检查清单**

在配置管理页面或类似多 Tab 页面新增功能前，必须完成以下检查：

#### **1. 复用检查**
- [ ] 是否可以复用 `vendorUserSelectorMixin`？（用户选择器逻辑）
- [ ] 是否可以复用 `commonStateMixin`？（loading/saving 状态）
- [ ] 是否可以复用 `render_loading_card()` 宏？
- [ ] 是否可以复用 `render_empty_state_card()` 宏？
- [ ] 是否可以复用 `getRoleDisplayName()` 函数？

#### **2. 结构检查**
- [ ] HTML 模板是否应该拆分为 `_config_xxx.html` 子模板？
- [ ] JavaScript 是否应该拆分为 `config-xxx.js` 独立文件？
- [ ] 新增代码是否超过 200 行？如果是，必须拆分

#### **3. 代码审查**
- [ ] 检查主文件行数，超过 5000 行需要立即重构
- [ ] 检查是否有复制粘贴的代码块
- [ ] 检查是否有重复的 CSS 类组合

### **Tab 模板规范**

#### ✅ 正确做法：创建独立子模板

```jinja2
{# 新增 Tab 应该创建独立文件 _config_new_feature.html #}
{% block tab_new_feature %}
<div x-data="newFeatureConfig()" ...>
  {{ render_tw_vendor_user_selector(...) }}
  {{ render_loading_card() }}
  {{ render_empty_state_card() }}
  ...
</div>
{% endblock %}
```

#### ❌ 错误做法：直接在主文件追加代码

```jinja2
{# 不要直接在主文件追加 500 行代码 #}
<div id="tab-new-feature">
  <!-- 复制粘贴加载状态 HTML -->
  <!-- 复制粘贴空状态 HTML -->
  <!-- 复制粘贴整个逻辑 -->
</div>
```

### **Alpine.js 组件规范**

#### ✅ 正确做法：使用 Mixin 组合

```javascript
function newFeatureConfig() {
    return {
        // 复用公共 mixin
        ...vendorUserSelectorMixin({ configType: 'new' }),
        ...commonStateMixin(),

        // 必须在组件中定义 getter（spread 不保留 getter）
        get filteredUsers() {
            return this.getFilteredUsers();
        },

        // 只添加该组件特有的属性
        customProperty: null,

        // 只添加该组件特有的方法
        init() {
            this.loadVendorUsers();
        }
    };
}
```

#### ❌ 错误做法：复制粘贴整个函数

```javascript
// 不要复制粘贴整个函数
function newFeatureConfig() {
    return {
        vendorUsers: [],           // ❌ 重复
        loadingUsers: true,        // ❌ 重复
        loading: false,            // ❌ 重复
        saving: false,             // ❌ 重复
        searchQuery: '',           // ❌ 重复

        get filteredUsers() {...}, // ❌ 重复
        async loadVendorUsers() {...}, // ❌ 重复
        onSearchInput() {...},     // ❌ 重复
        clearSearch() {...},       // ❌ 重复
        highlightMatch() {...},    // ❌ 重复
        getRoleDisplayName() {...} // ❌ 重复
    };
}
```

### **JavaScript Spread 与 Getter 的注意事项**

**重要**：JavaScript 的 spread 操作符（`...`）**不会保留 getter**，会立即调用并转为静态值。

```javascript
// mixin 中定义方法而非 getter
function myMixin() {
    return {
        data: [],
        // ❌ getter 会被 spread 调用并转为静态值
        // get computedData() { return this.data.filter(...); }

        // ✅ 使用方法
        getComputedData() {
            return this.data.filter(...);
        }
    };
}

// 组件中定义 getter 调用 mixin 方法
function myComponent() {
    return {
        ...myMixin(),

        // ✅ 在组件中定义 getter
        get computedData() {
            return this.getComputedData();
        }
    };
}
```

### **已有 Mixin 索引**

| Mixin 名称 | 文件位置 | 功能说明 |
|-----------|---------|---------|
| `vendorUserSelectorMixin` | `tw_index.html` 内 | 厂商用户选择器公共逻辑 |

**Mixin 提供的功能**：
- 状态：`vendorUsers`, `loadingUsers`, `selectedUserId`, `searchQuery`, `isSearching`
- 方法：`loadVendorUsers()`, `onSearchInput()`, `clearSearch()`, `highlightMatch()`, `getFilteredUsers()`

**使用 Mixin 的组件**：
- `affiliationConfig()` - configType: 'affiliation'
- `basicConfig()` - 无额外参数
- `performanceUserConfig()` - configType: 'performance', useYear: true
- `expenseUserConfig()` - configType: 'expense', useYear: true
- `salaryAssignConfig()` - useYear: true

---

## 🔍 重复代码识别标准

### **识别规则**

**触发重构的条件**（满足任一即需重构）：
1. **重复次数**：相同或高度相似的代码块在 ≥2 个地方出现
2. **重复行数**：重复代码块 ≥15 行
3. **逻辑复杂度**：即使只重复1次，但逻辑复杂（嵌套>3层、分支>5个）

### **常见重复模式**

#### **模式1：if/else分支中的重复**

❌ **错误示范**：
```python
if next_step:
    # 执行动作A
    if action_type == 'branch_decision':
        execute_branch_action(...)

    # 更新状态
    instance.current_step = next_step_id
else:
    # 执行动作A（重复）
    if action_type == 'branch_decision':
        execute_branch_action(...)

    # 完成流程
    instance.status = APPROVED
```

✅ **正确做法**：
```python
# 阶段1：先执行统一逻辑（无论是否有下一步）
if action_type == 'branch_decision':
    execute_branch_action(...)

# 阶段2：根据条件更新状态
if next_step:
    instance.current_step = next_step_id
else:
    instance.status = APPROVED
```

#### **模式2：多个函数中的重复逻辑**

❌ **错误示范**：
```python
def process_approval_a(instance_id):
    # 获取目标对象（重复）
    if instance.object_type == 'project':
        target = Project.query.get(instance.object_id)
    elif instance.object_type == 'expense':
        target = Expense.query.get(instance.object_id)
    # ...处理逻辑...

def process_approval_b(instance_id):
    # 获取目标对象（重复）
    if instance.object_type == 'project':
        target = Project.query.get(instance.object_id)
    elif instance.object_type == 'expense':
        target = Expense.query.get(instance.object_id)
    # ...处理逻辑...
```

✅ **正确做法**：
```python
def _get_target_object(instance):
    """统一获取目标对象的辅助函数"""
    if instance.object_type == 'project':
        return Project.query.get(instance.object_id)
    elif instance.object_type == 'expense':
        return Expense.query.get(instance.object_id)
    # ...

def process_approval_a(instance_id):
    target = _get_target_object(instance)
    # ...处理逻辑...

def process_approval_b(instance_id):
    target = _get_target_object(instance)
    # ...处理逻辑...
```

---

## 🛠️ 代码重构指南

### **何时应该重构**

#### **必须立即重构**（严重问题）
1. **功能性bug**：代码逻辑错误导致功能异常
2. **设计缺陷**：如本次案例中"最后一步不执行动作"的问题
3. **安全隐患**：存在潜在的数据泄露或权限绕过风险

#### **应该尽快重构**（中等问题）
1. **重复代码**：满足重复代码识别标准
2. **可读性差**：代码难以理解，需要大量注释才能看懂
3. **测试困难**：函数过于复杂，难以编写单元测试
4. **违反规范**：不符合项目编码规范

#### **可以择机重构**（低优先级）
1. **性能优化**：功能正常但性能不佳
2. **代码美化**：命名不规范、格式混乱
3. **技术债务**：使用了过时的API或库

### **重构流程**

#### **第1步：理解现有代码**
- 阅读相关代码，理解业务逻辑
- 识别问题根源（重复、设计缺陷、性能瓶颈）
- 确认影响范围（哪些模块使用了这段代码）

#### **第2步：制定重构计划**
- **Plan A（快速修复）**：最小改动，快速解决当前问题
- **Plan B（根本重构）**：彻底解决设计缺陷，提升代码质量

**选择策略**：
- 紧急bug → 先用Plan A修复，再计划Plan B
- 非紧急问题 → 直接采用Plan B
- 大型重构 → 分阶段实施，先Plan A再Plan B

#### **第3步：实施重构**

**重构前检查清单**：
- [ ] 已充分理解现有代码逻辑
- [ ] 已识别所有受影响的调用点
- [ ] 已制定回滚方案
- [ ] 已通知相关开发人员

**重构实施步骤**：
1. **创建辅助函数**（如需要）
2. **逐个修改调用点**
3. **保持功能一致性**
4. **清理无用代码**

#### **第4步：测试验证**

**测试范围**：
- [ ] 单元测试：新增/修改的函数
- [ ] 集成测试：相关业务流程的端到端测试
- [ ] 回归测试：确保未影响其他功能

**测试用例**：
- 正常场景：主要业务流程
- 边界场景：空值、极限值、异常输入
- 异常场景：错误处理、权限控制

#### **第5步：代码审查**
- 自查：使用提交前检查清单
- 同行审查：请其他开发者review
- 性能评估：对比重构前后的性能指标

---

## 📊 实战案例：审批流程重构

### **背景**

**文件**：`app/helpers/approval_helpers.py`（约7500行，超过警告阈值）

**问题**：批价单第二步审批（最后一步）不保存修改的折扣率数据

### **问题根源分析**

#### **原始代码结构**（设计缺陷）

两个审批处理函数 `process_approval()` 和 `process_approval_with_project_type()` 都存在相同的设计问题：

```python
if next_step:
    # 有下一步：只执行分支决策动作
    if current_step_action_type == 'branch_decision':
        _execute_branch_decision_action(...)  # ✅ 第一步会执行

    instance.current_step = next_step_id
else:
    # ❌ BUG: 最后一步缺少动作执行代码
    # （只有 process_approval_with_project_type 有，process_approval 缺失）

    instance.status = APPROVED
    instance.ended_at = datetime.now()
```

**问题分析**：
1. **逻辑错误**：动作执行逻辑被放在了`if next_step`分支中，导致最后一步不执行动作
2. **代码重复**：`process_approval_with_project_type`有正确实现，但`process_approval`缺失（复制粘贴时遗漏）
3. **设计缺陷**：应该先执行动作，再判断是否有下一步，而不是在两个分支中分别处理

### **解决方案对比**

#### **Plan A：快速修复**（已废弃）

**思路**：直接在`else`分支中复制粘贴动作执行代码

**优点**：
- 快速解决当前问题
- 改动最小，风险低

**缺点**：
- 没有解决根本设计缺陷
- 增加了47行重复代码
- 未来维护需要修改两处

**代码增减**：
- 新增：47行（动作执行逻辑）
- 重复代码：47行 × 2处 = 94行总重复

#### **Plan B：根本重构**（最终采用）

**思路**：采用两阶段设计，先执行动作，再更新状态

**实施步骤**：

1. **创建辅助函数**（提取重复逻辑）

```python
def _get_target_object_by_type(instance):
    """统一获取目标业务对象"""
    if instance.object_type == 'project':
        return Project.query.get(instance.object_id)
    elif instance.object_type == 'expense':
        return Expense.query.get(instance.object_id)
    elif instance.object_type == 'pricing_order':
        return PricingOrder.query.get(instance.object_id)
    return None

def _execute_current_step_action(instance, current_step, current_step_obj,
                                  current_step_action_type, record, user_id,
                                  pricing_order_data, action):
    """统一执行当前步骤的动作"""
    if action != ApprovalAction.APPROVE:
        return True

    if not current_step_action_type:
        return True

    # 分支决策步骤
    if current_step_action_type == 'branch_decision':
        _execute_branch_decision_action(instance, current_step, ...)
        return True

    # 其他动作类型
    target_object = _get_target_object_by_type(instance)
    if not target_object:
        return False

    if instance.object_type == 'pricing_order' and pricing_order_data:
        return current_step_obj.execute_action(record, target_object, pricing_order_data)
    else:
        return current_step_obj.execute_action(record, target_object)
```

2. **重构主函数**（两阶段设计）

```python
def process_approval(...):
    # ... 前置逻辑 ...

    # ============================================================
    # 阶段1：执行当前步骤的动作（统一处理，无论是否有下一步）
    # ============================================================
    _execute_current_step_action(
        instance, current_step, current_step_obj, current_step_action_type,
        record, user_id, pricing_order_data, action
    )

    # ============================================================
    # 阶段2：更新流程状态（根据是否有下一步决定继续或完成）
    # ============================================================
    if next_step:
        # 有下一步：移动到下一步
        instance.current_step = next_step_id
    else:
        # 无下一步：流程完成
        instance.status = APPROVED
        instance.ended_at = datetime.now()
        _update_business_object_approval_status(...)
        # 解锁对象...
```

### **代码增减统计**

#### **重构前**

| 函数 | 行数 | 重复代码 |
|------|------|---------|
| `process_approval` | 68行 | 动作执行逻辑缺失（bug） |
| `process_approval_with_project_type` | 68行 | 与`process_approval`高度重复 |
| **总计** | **136行** | **约47行重复** |

#### **重构后**

| 部分 | 行数 | 说明 |
|------|------|------|
| `_get_target_object_by_type` | 23行 | 新增辅助函数 |
| `_execute_current_step_action` | 56行 | 新增辅助函数 |
| `process_approval`（重构后） | 34行 | 简化50% |
| `process_approval_with_project_type`（重构后） | 34行 | 简化50% |
| **总计** | **147行** | **消除47行重复** |

#### **收益分析**

**代码质量提升**：
- ✅ 消除重复：约47行重复代码被提取到辅助函数
- ✅ 逻辑简化：主函数从68行缩减到34行（50%↓）
- ✅ 可读性强：清晰的两阶段设计，易于理解
- ✅ 易维护：未来新增动作类型只需修改辅助函数

**代码量变化**：
- 总行数：136行 → 147行（+11行，+8%）
- 但消除了47行重复，实际有效代码更少
- 新增行数主要是辅助函数，可复用价值高

**设计改进**：
- ❌ 旧设计：动作执行逻辑分散在if/else两个分支
- ✅ 新设计：先执行动作（统一），再更新状态（分支）
- 彻底解决了"最后一步不执行动作"的设计缺陷

### **测试验证结果**

**测试范围**：
- ✅ 批价单审批（两步流程）- 第一步和第二步都正确保存折扣率
- ✅ 报销单审批（多步流程）- 各步骤正常流转
- ✅ 项目报备审批（带授权）- 项目类型授权正常

**结论**：重构成功，所有测试通过，代码质量显著提升。

---

## ✅ 提交前检查清单

### **代码质量检查**

- [ ] **无重复代码**：检查是否有相同逻辑在多处重复
- [ ] **函数职责单一**：每个函数只做一件事
- [ ] **命名清晰**：变量、函数、类名能准确表达其用途
- [ ] **注释适度**：复杂逻辑有注释，简单逻辑不过度注释
- [ ] **错误处理完整**：所有可能的异常都有处理

### **文件大小检查**

- [ ] **Python文件 ≤ 1500行**：超过则需计划拆分
- [ ] **JavaScript文件 ≤ 1200行**：超过则需计划拆分
- [ ] **HTML模板 ≤ 800行**：超过则需计划拆分

### **性能检查**

- [ ] **无N+1查询**：使用`joinedload()`或`subqueryload()`
- [ ] **大数据集分页**：使用`paginate()`而非`all()`
- [ ] **缓存利用**：频繁查询的数据考虑缓存

### **安全检查**

- [ ] **权限验证**：所有路由有`@permission_required`装饰器
- [ ] **输入验证**：所有用户输入都经过验证和清理
- [ ] **SQL注入防护**：使用参数化查询，避免拼接SQL

### **测试检查**

- [ ] **核心功能已测试**：主要业务流程端到端测试通过
- [ ] **边界场景已覆盖**：空值、极限值、异常输入都有测试
- [ ] **回归测试通过**：确认未影响其他功能

---

## 📋 Claude AI 助手行为规范

### **生成代码时**

1. **主动检查重复**：
   - 生成代码前先搜索项目中是否已有类似实现
   - 如发现重复代码，建议复用而非重写

2. **遵循文件大小标准**：
   - 修改大文件时，检查文件当前行数
   - 超过警告阈值时，提醒用户并建议拆分方案

3. **优先提取辅助函数**：
   - 识别到重复逻辑时，主动建议提取辅助函数
   - 新增超过30行的代码块时，评估是否应该独立成函数

4. **采用两阶段设计**：
   - 避免在if/else两个分支中写相同代码
   - 优先考虑"先统一处理，再条件分支"的设计

### **重构代码时**

1. **制定完整计划**：
   - 使用Plan模式展示重构方案
   - 对比Plan A（快速修复）和Plan B（根本重构）
   - 等待用户确认后再实施

2. **保持功能一致**：
   - 重构时不改变外部接口
   - 保持原有功能和行为不变
   - 确保向后兼容

3. **测试驱动重构**：
   - 重构前记录现有行为
   - 重构后验证行为一致
   - 提醒用户进行全面测试

### **文档维护**

- 重大重构后，更新相关规范文档
- 记录典型问题和解决方案
- 保持文档与代码同步

---

## 📖 参考资源

### **相关规范文档**
- [CLAUDE.md](./CLAUDE.md) - 项目核心规范
- [CLAUDE-SCRIPTS.md](./CLAUDE-SCRIPTS.md) - 脚本创建与管理规范
- [CLAUDE-DATABASE.md](./CLAUDE-DATABASE.md) - 数据库规范

### **代码质量工具**
- `flake8` - Python代码风格检查
- `pylint` - Python代码质量检查
- `eslint` - JavaScript代码检查

### **推荐阅读**
- 《重构：改善既有代码的设计》- Martin Fowler
- 《代码大全》- Steve McConnell
- 《Clean Code》- Robert C. Martin

---

## 📝 更新日志

- **2026-01-01**: 添加 Alpine.js 和前端组件预防规范
  - 新增 Alpine.js 组件函数大小控制标准（150行警告、400行强制拆分）
  - 添加新增配置 Tab 前的检查清单（复用检查、结构检查、代码审查）
  - 添加 Tab 模板规范（正确/错误做法示例）
  - 添加 Alpine.js 组件规范（Mixin 使用示例）
  - 记录 JavaScript Spread 与 Getter 的技术注意事项
  - 建立已有 Mixin 索引（vendorUserSelectorMixin）
  - 基于 config_management/tw_index.html 重构经验总结

- **2025-10-12**: 创建文档，基于审批流程重构案例总结代码质量规范
  - 定义DRY原则和逻辑先行原则
  - 制定文件大小控制标准（Python 1500行、JS 1200行、HTML 800行警告阈值）
  - 建立重复代码识别标准（2次重复或15行以上）
  - 详细记录审批流程重构案例（Plan A vs Plan B）
  - 创建提交前检查清单
  - 规范Claude AI助手的代码生成和重构行为

**本文档是活文档，应根据项目发展和经验积累持续更新完善。**
