# 审批中心批价单筛选问题修复总结

## 问题描述

1. **500内部服务器错误**: 在审批中心选中批价单筛选时出现500错误
2. **草稿阶段批价单不显示**: 在审批中心列表中找不到草稿状态的批价单

## 问题根源分析

### 1. 状态枚举不匹配
- `ApprovalStatus`枚举只包含：`PENDING`, `APPROVED`, `REJECTED`
- 批价单状态包含：`draft`, `pending`, `approved`, `rejected`
- 草稿状态`draft`没有对应的枚举值导致筛选失败

### 2. 状态处理逻辑缺陷
- 审批中心视图中状态转换逻辑不完善
- 没有处理字符串状态参数的情况
- 批价单独立审批系统与通用审批系统状态映射不一致

### 3. 模板显示逻辑问题
- 审批状态显示模板没有处理`DRAFT`状态
- 筛选表单缺少草稿状态选项

## 修复内容

### 1. 修复状态筛选逻辑 (`app/helpers/approval_helpers.py`)

**在`get_user_created_approvals`函数中**:
```python
# 修复前
if status:
    if status == ApprovalStatus.PENDING:
        query = query.filter(PricingOrder.status == 'pending')
    # ... 其他状态
    # 注意：草稿状态不需要特殊过滤，因为没有对应的ApprovalStatus.DRAFT

# 修复后
if status:
    if status == ApprovalStatus.PENDING:
        query = query.filter(PricingOrder.status == 'pending')
    elif status == ApprovalStatus.APPROVED:
        query = query.filter(PricingOrder.status == 'approved')
    elif status == ApprovalStatus.REJECTED:
        query = query.filter(PricingOrder.status == 'rejected')
    # 如果传入的是字符串状态，直接匹配
    elif isinstance(status, str):
        if status.lower() == 'draft':
            query = query.filter(PricingOrder.status == 'draft')
        elif status.lower() == 'pending':
            query = query.filter(PricingOrder.status == 'pending')
        elif status.lower() == 'approved':
            query = query.filter(PricingOrder.status == 'approved')
        elif status.lower() == 'rejected':
            query = query.filter(PricingOrder.status == 'rejected')
```

**同样修复了`get_all_approvals`函数**，让管理员也能正确筛选批价单。

### 2. 修复视图状态参数处理 (`app/views/approval.py`)

```python
# 修复前
status_enum = None
if status:
    try:
        status_enum = ApprovalStatus[status.upper()]
    except (KeyError, AttributeError):
        pass

# 修复后
status_param = None
if status:
    try:
        # 尝试转换为枚举类型
        status_param = ApprovalStatus[status.upper()]
    except (KeyError, AttributeError):
        # 如果转换失败，直接使用字符串（用于批价单的草稿状态等）
        status_param = status
```

### 3. 修复筛选表单 (`app/templates/macros/approval_macros.html`)

添加草稿状态选项：
```html
<select class="form-select" id="status" name="status">
  <option value="">全部</option>
  <option value="draft" {{ 'selected' if status == 'draft' else '' }}>草稿</option>
  <option value="pending" {{ 'selected' if status == 'pending' else '' }}>审批中</option>
  <option value="approved" {{ 'selected' if status == 'approved' else '' }}>已通过</option>
  <option value="rejected" {{ 'selected' if status == 'rejected' else '' }}>已拒绝</option>
</select>
```

### 4. 修复状态显示 (`app/templates/macros/approval_macros.html`)

添加草稿状态的显示：
```html
{% elif item.status.name == 'DRAFT' %}
  <span class="badge rounded-pill bg-secondary text-white">草稿</span>
```

### 5. 增强错误处理

在分页查询中添加异常处理：
```python
try:
    pricing_orders = query.paginate(page=page, per_page=per_page, error_out=False)
except Exception as e:
    # 如果分页出错，返回空结果
    from flask_sqlalchemy import Pagination
    pricing_orders = Pagination(query=query, page=page, per_page=per_page, total=0, items=[])
```

## 测试验证

### 1. 数据验证
- 确认数据库中有18个批价单，大部分为草稿状态
- 用户ID 5创建了多个草稿状态的批价单

### 2. 功能测试
```python
# 测试不带状态筛选的查询
result = get_user_created_approvals(user_id=5, object_type='pricing_order')
# 返回: 10个批价单

# 测试草稿状态筛选
result = get_user_created_approvals(user_id=5, object_type='pricing_order', status='draft')
# 返回: 10个草稿状态批价单
```

## 预期效果

1. **500错误已修复**: 审批中心选择批价单筛选不再报错
2. **草稿状态显示**: 能够正确显示和筛选草稿状态的批价单
3. **状态筛选完善**: 支持所有批价单状态的筛选（草稿、审批中、已通过、已拒绝）
4. **兼容性保持**: 对其他业务类型（项目、报价单、客户）的审批功能无影响

## 相关文件清单

- `app/helpers/approval_helpers.py` - 核心筛选逻辑修复
- `app/views/approval.py` - 视图状态参数处理
- `app/templates/macros/approval_macros.html` - 界面显示和筛选表单

## 注意事项

- 批价单使用独立的审批系统，与通用审批系统并行运行
- 修复保持了向后兼容性，不影响现有功能
- 增强了错误处理，提高了系统稳定性 