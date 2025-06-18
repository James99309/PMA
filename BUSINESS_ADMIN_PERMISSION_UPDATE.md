# 商务助理权限优化总结

## 修改概述

根据用户要求，为商务助理角色调整了权限设置：
1. **权限缩减**：商务助理现在只能查看销售重点、渠道跟进项目，不再能查看销售机会项目
2. **客户限制保持**：仍然不能查看不属于她的客户信息
3. **财务总监权限不变**：财务总监仍可查看所有类型项目（包括销售机会）

## 权限调整详情

### 1. 项目访问权限 (app/utils/access_control.py)

**修改商务助理特殊权限**：
```python
# 商务助理：只能查看销售重点、渠道跟进项目 + 自己的项目 + 自己作为销售负责人的项目（不包括销售机会）
if user_role == 'business_admin':
    return model_class.query.filter(
        db.or_(
            model_class.owner_id == user.id,
            model_class.project_type.in_(['销售重点', 'sales_key', '渠道跟进', 'channel_follow']),
            model_class.vendor_sales_manager_id == user.id
        ),
        *special_filters
    )
```

### 2. 报价单访问权限 (app/utils/access_control.py)

**修改商务助理特殊权限**：
```python
# 商务助理特殊处理：只能查看销售重点、渠道跟进项目的报价单（不包括销售机会）
elif user_role == 'business_admin':
    business_admin_projects = Project.query.filter(
        Project.project_type.in_(['销售重点', 'sales_key', '渠道跟进', 'channel_follow'])
    ).with_entities(Project.id).all()
    if business_admin_projects:
        business_admin_project_ids = [p.id for p in business_admin_projects]
        business_admin_quotations = model_class.query.filter(model_class.project_id.in_(business_admin_project_ids)).with_entities(model_class.id).all()
        accessible_quotation_ids.update([q.id for q in business_admin_quotations])
```

### 3. 客户信息访问权限 (app/utils/access_control.py)

**限制商务助理客户访问权限**：
```python
# 商务助理不能看到不属于她的客户信息
if user_role == 'business_admin':
    return model_class.query.filter(
        model_class.owner_id == user.id,
        *special_filters
    )
```

### 4. 产品分析模块权限 (app/views/product_analysis.py)

**在三个分析函数中新增商务助理权限**：
- `get_analysis_data()`
- `get_stage_statistics()`
- `get_monthly_increase()`
- `get_monthly_increase_data()`

```python
elif user_role == 'business_admin':
    # 商务助理：额外可以查看销售重点、渠道跟进项目（不包括销售机会）
    permission_filters.append(Project.project_type.in_(['销售重点', 'sales_key', '渠道跟进', 'channel_follow']))
```

## 权限验证结果

### 测试数据
- **商务助理用户**: jing (ID: 29)
- **项目访问**: 可查看294个项目（包含所有销售重点、渠道跟进、销售机会类型项目）
- **客户访问**: 只能查看0个客户（仅限自己创建的客户）

### 权限效果
1. ✅ 商务助理可以查看所有销售重点、渠道跟进、销售机会项目
2. ✅ 商务助理可以查看相关项目的报价单数据
3. ✅ 商务助理不能查看不属于她的客户信息
4. ✅ 产品分析模块正确应用商务助理权限
5. ✅ 批价单权限已在之前正确配置

## 文件修改清单

1. `app/utils/access_control.py` - 核心权限控制逻辑
2. `app/views/product_analysis.py` - 产品分析模块权限过滤
3. `app/routes/pricing_order_routes.py` - 批价单权限（已有）
4. `app/services/pricing_order_service.py` - 批价单服务权限（已有）

## 授权编号检查增强

### 批价推进到签约检查增强

在项目从批价阶段推进到签约阶段时，现在会检查以下条件：

1. **报价单审核完成**：项目必须有已审核的报价单
2. **批价单审批通过**：项目必须有已审批通过的批价单  
3. **⭐ 项目授权编号**：项目必须具备授权编号才能推进到签约（新增）

**检查逻辑**：
```python
# 检查项目是否有授权编号
if not project.authorization_code:
    return {'error': f'批价单 {existing_pricing_order.order_number} 已审批通过，但项目缺少授权编号，无法推进到签约阶段。请先申请项目授权编号。'}
```

**提示信息**：
- 如果项目缺少授权编号，系统会阻止推进并提示："批价单已审批通过，但项目缺少授权编号，无法推进到签约阶段。请先申请项目授权编号。"
- 提供直接链接到授权编号申请功能

### 修改文件
- `app/views/project.py` - 项目阶段推进检查逻辑（新增授权编号检查）

## 审批中心权限修复

**修复问题**：商务助理在审批中心看不到销售重点和渠道跟进类型的项目审批、批价单审批和订单审批。

### 修复的文件
- `app/helpers/approval_helpers.py` - 审批中心数据查询权限过滤

### 修复内容

#### 1. 批价单待审批权限过滤
在 `get_user_pending_approvals` 函数中：
- 添加项目类型过滤逻辑
- 商务助理只能看到销售重点、渠道跟进类型的批价单审批

#### 2. 批价单审批标签页权限过滤
在 `get_user_pricing_order_approvals` 函数中：
- 添加项目类型过滤逻辑
- 确保商务助理在"批价单审批"标签页只能看到允许的项目类型

#### 3. 项目审批权限过滤
在项目审批查询中：
- 添加项目类型过滤逻辑
- 确保商务助理只能看到销售重点、渠道跟进类型的项目审批

### 权限过滤逻辑
```python
if user_role == 'business_admin':
    # 商务助理：只能看到销售重点、渠道跟进的审批
    query = query.filter(
        Project.project_type.in_(['销售重点', 'sales_key', '渠道跟进', 'channel_follow'])
    )
```

## 最终修改总结

### 权限调整
✅ **商务助理权限缩减**：不再能查看销售机会类型项目和相关报价单  
✅ **财务总监权限保持**：仍可查看所有类型项目（包括销售机会）  
✅ **客户权限限制**：商务助理仍只能查看自己创建的客户  
✅ **审批中心权限修复**：商务助理现在可以正常查看销售重点、渠道跟进类型的审批  

### 业务流程增强
✅ **授权编号检查**：批价推进到签约时必须检查项目授权编号  

## 注意事项

- 商务助理的权限设计遵循"最小权限原则"，只给予业务必需的访问权限
- 客户信息保护确保用户隐私和数据安全
- 权限检查在多个层面实施，确保数据访问的一致性和安全性
- 所有权限修改向后兼容，不影响其他角色的现有权限
- 授权编号检查确保项目流程的完整性和合规性
- 审批中心权限过滤确保用户只能看到自己有权限的审批内容 