# 项目审批按钮修复总结

## 问题描述
项目"抖动"(ID=628) 被拒绝后，无法看到"重新提交"按钮。

## 根本原因
**权限检查不匹配**：
- **视图层** (`views/project.py:1172-1173`): `can_submit_approval` 包含三类用户
  - 管理员 (admin)
  - 项目所有者 (owner_id)
  - 厂商销售经理 (vendor_sales_manager_id)

- **模板层** (`approval_flow.html`): 旧版只检查 `is_creator`
  - 只允许项目所有者看到按钮
  - **缺陷**: 即使视图层允许，厂商销售经理和管理员也看不到按钮

## 具体案例
```
项目ID: 628
项目名称: 抖动
owner_id: 23 (项目所有者)
vendor_sales_manager_id: 15 (厂商销售经理)

当前登录用户ID: 15 (厂商销售经理)
```

**问题**: 用户15是厂商销售经理，按业务逻辑应该能提交审批，但因为不是项目所有者(23)，旧版宏的 `{% if is_creator %}` 条件失败，整个审批操作区域不渲染。

## 修复方案

### 1. 宏系统增强 (`approval_flow.html`)

#### 修改 `render_approval_operation_section` 宏
```jinja2
{# 旧版签名 #}
{% macro render_approval_operation_section(object_type, object_id, object_status="draft",
    current_user_id=None, creator_id=None, title="审批操作", options={}) %}
    {% set is_creator = current_user_id == creator_id %}
    {% if is_creator %}  <!-- 只检查是否为创建人 -->

{# 新版签名 #}
{% macro render_approval_operation_section(object_type, object_id, object_status="draft",
    current_user_id=None, creator_id=None, title="审批操作", options={}, can_submit=None) %}
    {% set is_creator = current_user_id == creator_id %}
    {% set has_permission = can_submit if can_submit is not none else is_creator %}
    {% if has_permission %}  <!-- 使用增强的权限检查 -->
```

**关键逻辑**:
```jinja2
{% set has_permission = can_submit if can_submit is not none else is_creator %}
```
- 如果传入 `can_submit` 参数，使用该值
- 如果未传入，回退到原有的 `is_creator` 检查（向后兼容）

#### 修改 `render_complete_approval_section` 宏
```jinja2
{# 旧版 #}
{% macro render_complete_approval_section(object_type, object_id, object_status="draft",
    current_user_id=None, creator_id=None, container_id="approvalFlowSection", options={}) %}
    {{ render_approval_operation_section(..., options) }}

{# 新版 #}
{% macro render_complete_approval_section(object_type, object_id, object_status="draft",
    current_user_id=None, creator_id=None, container_id="approvalFlowSection", options={}, can_submit=None) %}
    {{ render_approval_operation_section(..., options, can_submit) }}
```

### 2. 模板调用更新 (`project/detail.html`)

```jinja2
{{ render_complete_approval_section(
    'project',
    project.id,
    project.status|default('draft'),
    current_user.id,
    project.owner_id,
    'projectApprovalFlowSection',
    {
        'operation_title': '项目审批操作',
        'flow_title': '项目审批流程',
        'description': '项目创建完成，可以提交审批流程。',
        'warning': '提交后将进入审批流程，无法直接修改项目信息。'
    },
    can_submit_approval  # 新增参数 - 从视图层传递权限判断结果
) }}
```

## 修复效果

### 修复前
| 用户类型 | owner_id=23 | 管理员 | 厂商销售经理(15) |
|---------|-------------|--------|-----------------|
| 视图层权限 | ✅ | ✅ | ✅ |
| 看到按钮 | ✅ | ❌ | ❌ |

### 修复后
| 用户类型 | owner_id=23 | 管理员 | 厂商销售经理(15) |
|---------|-------------|--------|-----------------|
| 视图层权限 | ✅ | ✅ | ✅ |
| 看到按钮 | ✅ | ✅ | ✅ |

## 测试步骤

### 1. 刷新页面
访问: `http://localhost:5000/project/view/628`

使用用户ID 15 (厂商销售经理) 登录

### 2. 检查调试信息
页面顶部应显示:
```
🔍 调试信息
项目ID: 628
项目状态: rejected
当前用户ID: 15
项目owner_id: 23
是否匹配: ❌ 不是创建人
```

### 3. 查看审批操作区域
应该看到一个卡片：
```
┌─────────────────────────────────────┐
│ ⚙️ 项目审批操作                      │
├─────────────────────────────────────┤
│ 审批流程被拒绝，您可以重新提交。       │
│ 重新提交将重置审批历史，重新开始      │
│ 审批流程。                 [重新提交] │
└─────────────────────────────────────┘
```

### 4. 查看控制台输出
打开浏览器Console (F12)，应看到:
```
🔍 [DEBUG] ========== 审批组件初始化调试 ==========
🔍 [DEBUG] 项目ID: 628
🔍 [DEBUG] 项目状态: rejected
🔍 [DEBUG] 当前用户ID: 15
🔍 [DEBUG] 项目owner_id: 23
🔍 [DEBUG] can_submit_approval: true  <-- 关键！应为 true
🔍 [DEBUG] 审批组件容器存在: true
🔍 [DEBUG] 容器HTML长度: [较大的数字]

🔍 [DEBUG] ========== 检查审批按钮 ==========
🔍 [DEBUG] 找到的按钮数量: 1  <-- 关键！应为 1 而非 0
🔍 [DEBUG] 按钮 1: 重新提交 | 可见: true
```

### 5. 点击重新提交按钮
应该弹出确认对话框，确认后应能正常重新提交审批。

## 调试代码清理

待测试通过后，需要删除以下调试代码:

### `project/detail.html`

1. **删除可见调试信息** (lines 395-402):
```html
<!-- 删除这个 alert 框 -->
<div class="alert alert-warning" style="margin: 20px 0;">
    <h5>🔍 调试信息</h5>
    ...
</div>
```

2. **删除Console调试日志** (lines 904-950):
```javascript
// 删除这些 console.log 语句
console.log('✅ [FILE LOADED] project/detail.html JavaScript 已加载 - Line 900');
console.log('🔍 [DEBUG] ========== 审批组件初始化调试 ==========');
// ... 等等所有带 [DEBUG] 的日志
```

3. **保留核心初始化代码**:
```javascript
// 保留这部分
document.addEventListener('DOMContentLoaded', function() {
    const projectApprovalFlow = new ApprovalFlow('project', {{ project.id }}, {
        containerId: 'projectApprovalFlowSection',
        containerSelector: '#projectApprovalFlowSectionContainer',
        apiBasePath: '/project/api/approval',
        autoLoad: true,
        enableInteraction: true
    });
    window.projectApprovalFlowInstance = projectApprovalFlow;
    projectApprovalFlow.init();
});
```

## 受影响的文件

1. **app/templates/macros/approval_flow.html**
   - 修改 `render_approval_operation_section` 宏签名
   - 修改 `render_complete_approval_section` 宏签名
   - 增强权限检查逻辑

2. **app/templates/project/detail.html**
   - 调用宏时传递 `can_submit_approval` 参数
   - 添加临时调试代码（待清理）

## 向后兼容性

✅ **完全兼容**: 现有使用该宏的页面无需修改

- 报销单详情 (`expense/expense_detail.html`)
- 订单详情 (`inventory/order_detail.html`)

这些页面如果不传 `can_submit` 参数，宏会自动使用 `is_creator` 检查（原有逻辑）。

## 数据库验证

```sql
-- 验证项目数据
SELECT id, project_name, owner_id, vendor_sales_manager_id, status
FROM projects
WHERE id = 628;
-- 结果: owner_id=23, vendor_sales_manager_id=15, status='rejected'

-- 验证审批实例已正确关闭
SELECT id, object_type, object_id, status, ended_at
FROM approval_instance
WHERE object_type = 'project' AND object_id = 628
ORDER BY created_at DESC;
-- 结果: status='REJECTED', ended_at不为NULL（已正确关闭）
```

## 总结

**核心修复**: 打通视图层和模板层的权限逻辑，确保 `can_submit_approval` 的判断结果能正确传递到宏系统，使管理员、项目所有者、厂商销售经理三类用户都能看到审批操作按钮。

**技术亮点**: 使用可选参数和回退机制，确保向后兼容，无需修改现有使用该宏的其他页面。

---

**创建时间**: 2025-11-24
**问题项目**: 抖动 (ID=628)
**修复状态**: ✅ 代码已修复，等待测试验证
