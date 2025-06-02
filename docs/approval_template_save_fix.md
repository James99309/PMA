# 审批模板保存功能修复总结

## 问题描述

用户在保存审批流程模板时遇到以下错误：

```
TypeError: update_approval_template() got an unexpected keyword argument 'lock_object_on_start'
```

## 问题分析

错误原因是在 `app/views/approval_config.py` 中调用 `update_approval_template()` 和 `create_approval_template()` 函数时，传递了这些函数定义中不存在的参数：

1. `lock_object_on_start` - 是否在发起审批后锁定对象
2. `lock_reason` - 锁定原因
3. `editable_fields` - 在审批步骤中可编辑的字段列表
4. `cc_users` - 抄送用户ID列表
5. `cc_enabled` - 是否启用抄送

## 修复内容

### 1. 修复 `create_approval_template()` 函数

**文件**: `app/helpers/approval_helpers.py`

**修改前**:
```python
def create_approval_template(name, object_type, creator_id=None, required_fields=None):
```

**修改后**:
```python
def create_approval_template(name, object_type, creator_id=None, required_fields=None, lock_object_on_start=None, lock_reason=None):
```

**新增功能**:
- 添加 `lock_object_on_start` 参数，默认值为 `True`
- 添加 `lock_reason` 参数，默认值为 `'审批流程进行中，暂时锁定编辑'`

### 2. 修复 `update_approval_template()` 函数

**文件**: `app/helpers/approval_helpers.py`

**修改前**:
```python
def update_approval_template(template_id, name=None, object_type=None, is_active=None, required_fields=None):
```

**修改后**:
```python
def update_approval_template(template_id, name=None, object_type=None, is_active=None, required_fields=None, lock_object_on_start=None, lock_reason=None):
```

**新增功能**:
- 添加 `lock_object_on_start` 参数处理
- 添加 `lock_reason` 参数处理

### 3. 修复 `add_approval_step()` 函数

**文件**: `app/helpers/approval_helpers.py`

**修改前**:
```python
def add_approval_step(template_id, step_name, approver_id, send_email=True):
```

**修改后**:
```python
def add_approval_step(template_id, step_name, approver_id, send_email=True, editable_fields=None, cc_users=None, cc_enabled=False):
```

**新增功能**:
- 添加 `editable_fields` 参数，默认为空列表
- 添加 `cc_users` 参数，默认为空列表
- 添加 `cc_enabled` 参数，默认为 `False`

### 4. 修复 `update_approval_step()` 函数

**文件**: `app/helpers/approval_helpers.py`

**修改前**:
```python
def update_approval_step(step_id, step_name=None, approver_id=None, send_email=None):
```

**修改后**:
```python
def update_approval_step(step_id, step_name=None, approver_id=None, send_email=None, editable_fields=None, cc_users=None, cc_enabled=None):
```

**新增功能**:
- 添加 `editable_fields` 参数处理
- 添加 `cc_users` 参数处理
- 添加 `cc_enabled` 参数处理

### 5. 添加缺失的 `get_all_approvals()` 函数

**文件**: `app/helpers/approval_helpers.py`

**新增函数**:
```python
def get_all_approvals(object_type=None, status=None, page=1, per_page=20):
    """获取所有审批记录（仅供admin使用）"""
```

这个函数是为了支持admin账户查看所有审批记录的功能。

## 测试验证

创建了测试脚本验证修复效果：

1. **创建模板测试**: 验证带有新参数的模板创建功能
2. **更新模板测试**: 验证带有新参数的模板更新功能
3. **数据完整性测试**: 验证所有参数都能正确保存和读取

测试结果：
```
✅ 创建成功: ID=16, 名称=测试模板保存功能
  - 锁定设置: True
  - 锁定原因: 测试锁定原因
  - 必填字段: ['project_name', 'project_budget']

✅ 更新成功: ID=16, 名称=更新后的测试模板
  - 对象类型: quotation
  - 锁定设置: False
  - 锁定原因: 更新后的锁定原因
  - 必填字段: ['quotation_amount', 'customer_name']
```

## 影响范围

### 修复的功能
1. ✅ 审批模板创建功能
2. ✅ 审批模板编辑功能
3. ✅ 审批步骤添加功能
4. ✅ 审批步骤编辑功能
5. ✅ Admin账户查看所有审批记录功能

### 兼容性
- ✅ 向后兼容：所有新参数都有默认值
- ✅ 现有功能不受影响
- ✅ 数据库结构无需修改（字段已存在）

## 总结

此次修复解决了审批流程模板保存时的 `TypeError` 错误，确保了：

1. **功能完整性**: 所有审批模板和步骤的增强功能都能正常使用
2. **参数一致性**: 函数定义与调用处的参数完全匹配
3. **向后兼容性**: 不影响现有功能的正常运行
4. **代码健壮性**: 添加了适当的默认值和错误处理

用户现在可以正常保存和编辑审批流程模板，包括设置对象锁定、可编辑字段、抄送用户等高级功能。 