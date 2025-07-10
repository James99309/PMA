# gxh用户访问控制问题分析报告

## 问题描述
gxh用户在项目创建时看不到自己的公司和其他公司，无法正常创建项目。

## 代码分析

### 1. 访问控制核心函数 `get_viewable_data`

位置: `/Users/nijie/Documents/PMA/app/utils/access_control.py`

该函数是整个系统数据访问控制的核心，负责根据用户权限返回可查看的数据集。

#### 对于Company模型的访问控制逻辑：

```python
# 客户特殊权限处理 - 基于权限管理系统
if model_class.__name__ in ['Company', 'Contact']:
    # 检查用户是否有客户模块的查看权限
    if not user.has_permission('customer', 'view'):
        # 如果没有客户查看权限，返回空查询
        return model_class.query.filter(False)
    
    # 基于四级权限系统的数据访问控制
    permission_level = user.get_permission_level('customer')
    
    # 为Company模型添加is_deleted过滤条件
    base_filters = []
    if model_class.__name__ == 'Company':
        base_filters.append(model_class.is_deleted == False)
    
    if permission_level == 'system':
        # 系统级权限：可以查看所有客户数据
        all_filters = base_filters + (special_filters if special_filters else [])
        return model_class.query.filter(*all_filters)
    elif permission_level == 'company' and user.company_name:
        # 企业级权限：可以查看企业下所有客户数据
        from app.models.user import User
        company_user_ids = [u.id for u in User.query.filter_by(company_name=user.company_name).all()]
        all_filters = base_filters + [model_class.owner_id.in_(company_user_ids)] + (special_filters if special_filters else [])
        return model_class.query.filter(*all_filters)
    elif permission_level == 'department' and user.department and user.company_name:
        # 部门级权限：可以查看部门下所有客户数据
        from app.models.user import User
        dept_user_ids = [u.id for u in User.query.filter(
            User.department == user.department,
            User.company_name == user.company_name
        ).all()]
        all_filters = base_filters + [model_class.owner_id.in_(dept_user_ids)] + (special_filters if special_filters else [])
        return model_class.query.filter(*all_filters)
    
    # 个人级权限或其他情况：基础权限控制
    viewable_user_ids = [user.id]
    
    # 添加归属关系授权的用户（数据归属权限）
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    for affiliation in affiliations:
        viewable_user_ids.append(affiliation.owner_id)
    
    # 部门负责人权限：可以查看本部门所有用户的数据
    if getattr(user, 'is_department_manager', False) and user.department:
        dept_users = User.query.filter_by(department=user.department).all()
        viewable_user_ids.extend([u.id for u in dept_users])
    
    # 商务助理特殊权限：具备部门所有账户的查看权限
    user_role = user.role.strip() if user.role else ''
    if user_role == 'business_admin' and user.department and user.company_name:
        dept_users = User.query.filter(
            User.department == user.department,
            User.company_name == user.company_name
        ).all()
        viewable_user_ids.extend([u.id for u in dept_users])
    
    # 去重
    viewable_user_ids = list(set(viewable_user_ids))
    
    # 基于权限管理系统的数据访问控制
    all_filters = base_filters + [model_class.owner_id.in_(viewable_user_ids)] + (special_filters if special_filters else [])
    return model_class.query.filter(*all_filters)
```

### 2. 项目创建页面的企业数据获取

位置: `/Users/nijie/Documents/PMA/app/views/project.py`

在项目创建页面中，企业数据通过以下函数获取：

```python
def get_company_data():
    company_query = get_viewable_data(Company, current_user)
    return {
        key: company_query.filter_by(company_type=key).all()
        for key in COMPANY_TYPE_LABELS.keys()
    }
```

该函数直接调用了 `get_viewable_data(Company, current_user)` 来获取用户可查看的企业数据。

### 3. 用户权限检查机制

位置: `/Users/nijie/Documents/PMA/app/models/user.py`

用户权限检查通过以下方法实现：

```python
def has_permission(self, module, action):
    # 管理员默认拥有所有权限
    if self.role == 'admin':
        return True
    
    # 获取角色权限
    from app.models.role_permissions import RolePermission
    role_permission = RolePermission.query.filter_by(role=self.role, module=module).first()
    role_has_permission = False
    if role_permission:
        if action == 'view':
            role_has_permission = role_permission.can_view
        elif action == 'create':
            role_has_permission = role_permission.can_create
        elif action == 'edit':
            role_has_permission = role_permission.can_edit
        elif action == 'delete':
            role_has_permission = role_permission.can_delete
            
    # 获取个人权限
    permission = Permission.query.filter_by(user_id=self.id, module=module).first()
    personal_has_permission = False
    if permission:
        if action == 'view':
            personal_has_permission = permission.can_view
        elif action == 'create':
            personal_has_permission = permission.can_create
        elif action == 'edit':
            personal_has_permission = permission.can_edit
        elif action == 'delete':
            personal_has_permission = permission.can_delete
    
    # 最终权限 = 角色权限 OR 个人权限
    final_permission = role_has_permission or personal_has_permission
    
    return final_permission

def get_permission_level(self, module):
    """获取用户在指定模块的权限级别"""
    try:
        from app.models.role_permissions import RolePermission
        role_permission = RolePermission.query.filter_by(role=self.role, module=module).first()
        if role_permission:
            return role_permission.permission_level
        return 'personal'  # 默认个人级权限
    except Exception as e:
        print(f"[ERROR][get_permission_level] Database error: {str(e)}")
        return 'personal'
```

## 问题根因分析

基于代码分析，gxh用户在项目创建时看不到公司列表的可能原因如下：

### 1. 权限配置问题
- **缺少customer模块查看权限**: 如果gxh用户没有customer模块的'view'权限，`get_viewable_data`函数会返回空查询(`model_class.query.filter(False)`)
- **角色权限配置错误**: 在`role_permissions`表中，gxh用户的角色可能没有正确配置customer模块的权限

### 2. 权限级别配置问题
- **权限级别设置不当**: 如果用户的权限级别为'personal'，但没有配置相应的归属关系或部门管理权限，可能导致可查看的公司数据为空
- **企业/部门信息不完整**: 如果用户的`company_name`或`department`字段为空，会影响企业级或部门级权限的判断

### 3. 数据问题
- **公司数据被标记为删除**: 如果数据库中的公司记录`is_deleted`字段为True，这些记录会被过滤掉
- **缺少归属关系**: 如果没有正确配置用户之间的归属关系(`affiliations`表)，用户可能无法查看其他用户创建的公司

### 4. 角色特殊权限问题
- **sales_director角色限制**: 从现有代码看，sales_director角色在某些模块有特殊的权限限制，可能影响数据访问
- **角色名称空格问题**: 代码中使用了`user.role.strip()`来处理角色名称，说明可能存在角色名称包含空格的情况

## 解决方案建议

### 1. 检查权限配置
```sql
-- 检查角色权限配置
SELECT * FROM role_permissions WHERE role = 'gxh用户的角色' AND module = 'customer';

-- 检查个人权限配置
SELECT * FROM permissions WHERE user_id = gxh用户ID AND module = 'customer';
```

### 2. 检查用户基本信息
```sql
-- 检查用户基本信息
SELECT id, username, real_name, role, company_name, department, is_department_manager 
FROM users WHERE username = 'gxh';
```

### 3. 检查公司数据
```sql
-- 检查公司数据
SELECT COUNT(*) FROM companies WHERE is_deleted = 0;
SELECT COUNT(*) FROM companies WHERE owner_id = gxh用户ID AND is_deleted = 0;
```

### 4. 检查归属关系
```sql
-- 检查归属关系
SELECT * FROM affiliations WHERE viewer_id = gxh用户ID;
```

### 5. 修复建议
1. **确保角色权限配置正确**: 为gxh用户的角色添加customer模块的查看权限
2. **完善用户信息**: 确保用户的company_name和department字段填写完整
3. **配置归属关系**: 如果需要，为用户配置适当的归属关系
4. **检查数据完整性**: 确保公司数据没有被错误标记为删除

## 特殊角色权限分析

从代码中可以看到，gxh用户如果是`sales_director`角色，会有一些特殊的权限控制：

```python
# 营销总监特殊处理：可以查看销售重点和渠道跟进项目
if user.role and user.role.strip() == 'sales_director' and model_class.__name__ == 'Project':
    # 获取自己的项目
    own_projects = model_class.query.filter(model_class.owner_id == user.id)
    
    # 获取销售重点和渠道跟进项目
    special_projects = model_class.query.filter(
        model_class.project_type.in_(['sales_focus', 'channel_follow', '销售重点', '渠道跟进'])
    )
    
    # 获取自己作为销售负责人的项目
    sales_manager_projects = model_class.query.filter(
        model_class.vendor_sales_manager_id == user.id
    )
    
    # 合并查询结果
    combined_query = own_projects.union(special_projects).union(sales_manager_projects)
    return combined_query.filter(*special_filters)
```

这说明`sales_director`角色在项目模块有特殊的权限控制，但在customer模块应该遵循标准的权限控制流程。

## 总结

gxh用户在项目创建时看不到公司列表的问题，主要是由于权限配置不当导致的。需要检查：

1. 用户是否有customer模块的查看权限
2. 用户的权限级别配置是否正确
3. 用户的基本信息（公司、部门）是否完整
4. 归属关系是否正确配置
5. 公司数据是否完整且未被删除

通过系统地检查这些方面，应该能够找到并解决gxh用户无法查看公司列表的问题。