# Admin账户审批中心功能增强

## 概述

为了让admin账户能够查看和管理所有的审批记录，对审批中心进行了功能增强。

## 主要修改

### 1. 后端函数修改

#### `app/helpers/approval_helpers.py`

**修改的函数：**

- `get_user_created_approvals()`: 
  - admin账户可以查看所有审批记录，不再限制为只能查看自己发起的
  - 其他用户仍然只能查看自己发起的审批记录

- `get_user_pending_approvals()`:
  - admin账户可以查看所有待审批的记录
  - 其他用户仍然只能查看待自己审批的记录

**新增的函数：**

- `get_all_approvals()`: 专门为admin账户提供的函数，用于获取所有审批记录

### 2. 前端界面修改

#### `app/templates/approval/center.html`

**新增功能：**
- 为admin账户添加了"全部审批"标签页
- 只有admin账户可以看到这个标签页
- 更新了标题显示逻辑，支持三种模式

#### `app/views/approval.py`

**修改的视图函数：**
- `center()`: 添加了对"全部审批"标签页的支持
- admin账户访问"全部审批"时，使用`get_all_approvals()`函数获取所有记录

#### `app/templates/macros/approval_macros.html`

**修改的宏：**
- `approval_table()`: 更新了空状态消息，支持"全部审批"模式

## 功能特性

### Admin账户权限

1. **我发起的标签页**：显示所有审批记录（不限发起人）
2. **待我审批的标签页**：显示所有待审批记录（不限审批人）
3. **全部审批标签页**：显示所有审批记录（仅admin可见）

### 普通用户权限

1. **我发起的标签页**：只显示自己发起的审批记录
2. **待我审批的标签页**：只显示待自己审批的记录
3. **无法看到"全部审批"标签页**

## 测试验证

通过测试脚本验证了以下功能：

- ✅ admin可以查看所有15个审批记录
- ✅ admin可以查看所有1个待审批记录
- ✅ `get_all_approvals()`函数正常工作
- ✅ 权限控制正确，admin和普通用户有不同的访问权限

## 使用说明

1. 使用admin账户登录系统
2. 点击用户头像下拉菜单中的"审批中心"
3. 可以看到三个标签页：
   - **我发起的**：显示所有审批记录
   - **待我审批的**：显示所有待审批记录
   - **全部审批**：显示所有审批记录（与"我发起的"内容相同，但语义更清晰）

## 技术实现

### 权限检查逻辑

```python
# 在helper函数中检查用户角色
if current_user.role != 'admin':
    query = query.filter(ApprovalInstance.created_by == user_id)
```

### 前端权限控制

```html
<!-- 只有admin可以看到"全部审批"标签页 -->
{% if current_user.role == 'admin' %}
<li class="nav-item">
  <a class="nav-link {{ 'active' if current_tab == 'all' else '' }}" 
     href="{{ url_for('approval.center', tab='all') }}">
    <i class="fas fa-list me-1"></i> 全部审批
  </a>
</li>
{% endif %}
```

## 安全考虑

- 权限检查在后端函数中进行，确保数据安全
- 前端界面控制只是用户体验优化，真正的权限控制在后端
- admin角色的权限检查使用`current_user.role == 'admin'`

## 兼容性

- 对现有功能无影响
- 普通用户的使用体验保持不变
- 只是为admin账户增加了额外的查看权限 