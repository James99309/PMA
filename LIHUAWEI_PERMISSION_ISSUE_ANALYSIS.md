# lihuawei用户权限异常问题分析报告

## 问题概述
用户lihuawei (ID: 15, 角色: sales_manager) 能够访问其他账户的客户信息和项目信息，存在数据安全风险。

## 问题根源

### 1. 用户基本信息
- **用户名**: lihuawei
- **用户ID**: 15
- **角色**: "sales_manager"
- **归属关系**: 无 (0个)
- **作为厂商负责人的项目**: 50个
- **作为拥有者的项目**: 50个
- **作为拥有者的客户**: 65个

### 2. 权限扩展的根本原因

在 `app/utils/access_control.py` 第410-471行中，`sales_manager`角色被赋予了过度的权限：

```python
# 销售角色：查看自己的客户 + 通过归属关系可见的客户 + 被共享的客户 + 厂商负责人项目相关的客户
if user_role in ['sales', 'sales_manager']:
    # ... 省略部分代码 ...
    
    # 获取厂商负责人相关的项目涉及的客户
    from app.models.project import Project
    vendor_projects = Project.query.filter(Project.vendor_sales_manager_id == user.id).all()
    vendor_company_names = set()
    for project in vendor_projects:
        if project.end_user:
            vendor_company_names.add(project.end_user)
        if project.contractor:
            vendor_company_names.add(project.contractor)
        if project.system_integrator:
            vendor_company_names.add(project.system_integrator)
        if project.dealer:
            vendor_company_names.add(project.dealer)
    
    vendor_company_ids = []
    if vendor_company_names:
        vendor_companies = Company.query.filter(Company.company_name.in_(vendor_company_names)).all()
        vendor_company_ids = [c.id for c in vendor_companies]
```

### 3. 具体权限扩展内容

lihuawei通过以下方式获得了过度权限：

1. **厂商负责人项目权限**: 50个项目中涉及的所有客户公司
   - end_user (最终用户)
   - contractor (承建商)  
   - system_integrator (系统集成商)
   - dealer (经销商)

2. **联系人相关公司权限**: 通过创建的联系人访问相关公司

3. **共享公司权限**: 被其他用户共享的公司

4. **厂商用户权限**: 如果被标记为厂商用户，可访问所有经销商类型公司

## 数据影响评估

### 理论访问范围
- **总项目数**: 435个
- **lihuawei理论可访问项目**: 100个 (自己50个 + 厂商负责人50个)
- **总客户数**: 476个  
- **lihuawei理论可访问客户**: 远超65个（通过项目关联扩展）

### 安全风险
1. **数据泄露**: 可访问不属于自己的敏感客户信息
2. **业务竞争**: 可能获取其他销售的客户资源
3. **合规问题**: 违反最小权限原则
4. **审计风险**: 权限分配不当可能导致审计问题

## 修复建议

### 方案1: 限制厂商负责人权限范围（推荐）
```python
# 修改 access_control.py 中的逻辑
if user_role in ['sales', 'sales_manager']:
    # 移除或限制厂商负责人项目相关的客户访问权限
    # 只保留：自己的客户 + 归属关系客户 + 明确共享的客户
```

### 方案2: 角色权限细分
- 将 `sales_manager` 和 `sales` 角色的权限分开处理
- 销售经理不应自动获得厂商负责人项目的客户访问权限

### 方案3: 增加权限审核机制
- 添加权限申请和审批流程
- 厂商负责人项目的客户访问需要额外授权

## 立即行动建议

### 1. 紧急措施
- 立即审查所有 `sales_manager` 角色用户的权限
- 检查是否有其他用户存在相同问题
- 考虑临时限制过度权限

### 2. 代码修复
- 修改 `access_control.py` 中的权限逻辑
- 添加更精细的权限控制
- 增加权限变更的日志记录

### 3. 数据审计
- 审计历史数据访问记录
- 检查是否有未授权的数据访问行为
- 建立权限变更的审计轨迹

## 技术实现细节

### 当前问题代码位置
- 文件: `app/utils/access_control.py`
- 行数: 410-471行
- 函数: `get_viewable_data()`
- 条件: `if user_role in ['sales', 'sales_manager']:`

### 修复示例代码
```python
# 建议的修复逻辑
if user_role == 'sales':
    # 销售人员权限：较为限制
    # 只能访问自己的客户 + 归属关系客户
elif user_role == 'sales_manager':
    # 销售经理权限：适度扩展
    # 可以访问自己的客户 + 归属关系客户 + 明确授权的客户
    # 但不自动获得厂商负责人项目的所有相关客户
```

## 结论

lihuawei用户权限异常的根本原因是系统给予了 `sales_manager` 角色过度的权限，特别是通过厂商负责人身份访问大量不相关的客户数据。这种权限设计违反了最小权限原则，存在严重的数据安全风险。

建议立即进行权限整改，并建立更严格的权限审核机制。 