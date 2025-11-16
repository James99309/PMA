# 权限装饰器冲突修复方案

## 问题描述
多个模块的删除/编辑函数同时使用了：
1. `@permission_required` 装饰器（模块级权限检查）- 先执行
2. `can_edit_data()` 函数（数据归属检查）- 后执行

**问题**：装饰器会在数据归属检查之前拦截用户，导致创建者无法操作自己的数据。

**根本原因**：`@permission_required` 装饰器不包含数据归属逻辑，只检查模块权限。

## 已修复的模块

### 1. Product（产品）- `/app/routes/product.py:2014`
- **函数**: `delete_product()`
- **修复**: 移除 `@permission_required('product', 'delete')` 装饰器
- **检查方式**: 使用 `can_delete_product()` 统一权限检查

### 2. Expense（报销单）- `/app/views/expense.py:1945`
- **函数**: `delete_expense()`
- **修复**: 移除 `@permission_required('expense', 'delete')` 装饰器
- **检查方式**: 使用 `can_edit_data()` 统一权限检查

## 需要修复的核心模块（优先级高）

### 3. Customer（客户）- 删除函数

#### 3.1 `/app/views/customer.py:1506` - `delete_company()`
```python
# 当前代码
@permission_required('customer', 'delete')  # ❌ 移除
def delete_company(company_id):
    # 检查删除权限
    if not can_edit_data(company, current_user):  # ✅ 保留
```

#### 3.2 `/app/views/customer.py:2836` - `batch_delete_companies()`
```python
# 当前代码
@permission_required('customer', 'delete')  # ❌ 移除
def batch_delete_companies():
    # 每个客户都检查
    if not can_edit_data(company, current_user):  # ✅ 保留
```

#### 3.3 `/app/views/customer.py:1287` - `api_delete_confirm()`
```python
@permission_required('customer', 'delete')  # ❌ 移除
def api_delete_confirm(company_id):
    # 检查权限
    if not can_edit_data(company, current_user):  # ✅ 保留
```

#### 3.4 `/app/views/customer.py:1314` - `api_batch_delete_confirm()`
```python
@permission_required('customer', 'delete')  # ❌ 移除
def api_batch_delete_confirm():
    # 每个客户都检查
    if not can_edit_data(company, current_user):  # ✅ 保留
```

### 4. Customer（客户）- 编辑函数

#### 4.1 `/app/views/customer.py:1242` - `edit_company()`
```python
@permission_required('customer', 'edit')  # ❌ 移除
def edit_company(company_id):
    # 检查编辑权限
    if not can_edit_data(company, current_user):  # ✅ 保留
```

### 5. Project（项目）- 删除函数

#### 5.1 `/app/views/project.py:1532` - `delete_project()`
```python
@permission_required('project', 'delete')  # ❌ 移除
def delete_project(project_id):
    # 检查删除权限
    if not can_edit_data(project, current_user):  # ✅ 保留
```

#### 5.2 `/app/views/project.py:1985` - `batch_delete_projects()`
```python
@permission_required('project', 'delete')  # ❌ 移除
def batch_delete_projects():
    # 每个项目都检查
    if not can_edit_data(project, current_user):  # ✅ 保留
```

### 6. Quotation（报价）- 删除函数

#### 6.1 `/app/views/quotation.py:2030` - `delete_quotation()`
```python
@permission_required('quotation', 'delete')  # ❌ 移除
def delete_quotation(id):
    # 检查删除权限
    if not can_edit_data(quotation, current_user):  # ✅ 保留
```

#### 6.2 `/app/views/quotation.py:2087` - `batch_delete_quotations()`
```python
@permission_required('quotation', 'delete')  # ❌ 移除
def batch_delete_quotations():
    # 每个报价都检查
    if not can_edit_data(quotation, current_user):  # ✅ 保留
```

### 7. Quotation（报价）- 编辑函数

#### 7.1 `/app/views/quotation.py:1449` - `edit_quotation()`
```python
@permission_required('quotation', 'edit')  # ❌ 移除
def edit_quotation(id):
    # 检查编辑权限
    if not can_edit_data(quotation, current_user):  # ✅ 保留
```

## 需要审查的其他函数（优先级中）

### Customer（客户）- 查看相关
- `/app/views/customer.py:1053` - `view_company()` - 需检查是否必要
- `/app/views/customer.py:1817` - `api_companies_by_type()` - API函数
- `/app/views/customer.py:1857` - `search_company_api()` - 搜索API
- `/app/views/customer.py:3639` - `get_merge_preview()` - 合并预览
- `/app/views/customer.py:3778` - `execute_merge()` - 执行合并

### Expense（报销单）- 编辑相关
- `/app/views/expense.py:1284` - `edit_expense()` - 编辑主函数
- `/app/views/expense.py:2267` - `upload_invoice_image()` - 上传发票
- `/app/views/expense.py:2618` - `delete_invoice_image()` - 删除发票图片
- `/app/views/expense.py:2742` - `submit_approval()` - 提交审批
- `/app/views/expense.py:2828` - `recall_approval()` - 召回审批
- `/app/views/expense.py:2884` - `resubmit_approval()` - 重新提交

### Project（项目）- 编辑相关
- `/app/views/project.py:1379` - `get_edit_project_data()` - 获取编辑数据
- `/app/views/project.py:3741` - `start_project_approval()` - 启动审批
- `/app/views/project.py:3967` - `submit_project_approval_standard()` - 提交审批
- `/app/views/project.py:4283` - `generate_authorization_code()` - 生成授权码

## 修复原则

### 何时移除 @permission_required 装饰器
✅ **应该移除** - 如果函数满足以下条件：
1. 函数内部已有 `can_edit_data()` 或类似的数据归属检查
2. 函数处理的是用户可能拥有的数据（客户、项目、报价、产品、报销单等）
3. 创建者应该有权操作自己创建的数据

❌ **不应移除** - 如果函数满足以下条件：
1. 函数处理的是系统级配置（不属于任何用户）
2. 函数是纯API/工具函数，不涉及数据归属
3. 函数仅用于模块权限检查，不需要数据级权限

### 修复模板
```python
# 修复前
@blueprint.route('/delete/<int:id>', methods=['POST'])
@login_required
@permission_required('module', 'delete')  # ❌ 移除此行
def delete_item(id):
    item = Model.query.get_or_404(id)

    # 检查删除权限
    if not can_edit_data(item, current_user):
        return error_response()

    # 执行删除...

# 修复后
@blueprint.route('/delete/<int:id>', methods=['POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以删除自己的数据
def delete_item(id):
    item = Model.query.get_or_404(id)

    # 使用统一的数据权限检查（包含数据归属逻辑）
    if not can_edit_data(item, current_user):
        return error_response()

    # 执行删除...
```

## 执行步骤

### 阶段1：核心删除函数（立即执行）
1. Customer: 4个删除函数
2. Project: 2个删除函数
3. Quotation: 2个删除函数

### 阶段2：核心编辑函数（尽快执行）
1. Customer: 1个编辑函数
2. Quotation: 1个编辑函数

### 阶段3：审查其他函数（逐步执行）
1. 审查 Expense 的 6 个编辑相关函数
2. 审查 Project 的 4 个编辑相关函数
3. 审查 Customer 的 5 个查看相关函数
4. 审查其他模块

## 测试验证

修复后需要测试：
1. **创建者权限**：用户能删除/编辑自己创建的数据（即使没有模块delete/edit权限）
2. **模块权限**：有模块权限的用户能删除/编辑他人数据（根据数据范围）
3. **无权限保护**：无关用户不能操作他人数据
4. **管理员权限**：管理员能操作所有数据

## 风险评估

### 低风险
- 移除装饰器后，`can_edit_data()` 仍然提供完整的权限检查
- `can_edit_data()` 已经包含了角色、数据范围、数据归属等所有逻辑
- 这个修复实际上是**修复bug**而非削弱权限

### 注意事项
- 确保每个移除装饰器的函数都有 `can_edit_data()` 或等效检查
- 审查时要确认权限检查的位置（在业务逻辑之前）
- 保留 `@login_required` 装饰器（基础认证必需）
