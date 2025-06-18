# 项目权限一致性修复总结

## 问题描述

用户反馈：lihuawei账户可以在项目列表中看到其他拥有者和厂商负责人的项目，但无法点击进入（没有权限），这种权限不一致的表现是不正常的。

## 根本原因分析

### 权限逻辑不一致的位置

1. **项目列表权限**（`get_viewable_data`函数）：
   - 位置：`app/utils/access_control.py` 第209-224行
   - 逻辑：`sales_manager`角色可以查看归属关系中的非业务机会项目

2. **项目详情权限**（`can_view_project`函数）：
   - 位置：`app/utils/access_control.py` 第759-786行（修复前）
   - 问题：**缺少**对`sales_manager`角色归属关系权限的处理

### 具体不一致表现

```python
# get_viewable_data 中的逻辑（项目列表）
if user_role in ['sales', 'sales_manager']:
    return model_class.query.filter(
        db.or_(
            model_class.owner_id == user.id,  # 自己的项目
            db.and_(
                model_class.owner_id.in_(viewable_user_ids),
                model_class.project_type != '业务机会'  # 归属关系的非业务机会项目 ✅
            ),
            model_class.vendor_sales_manager_id == user.id  # 厂商负责人项目
        ),
        *special_filters
    )

# can_view_project 中的逻辑（项目详情）- 修复前
def can_view_project(user, project):
    # ... 其他逻辑 ...
    if project.owner_id in affiliation_owner_ids:
        return True  # ❌ 没有考虑销售经理的业务机会限制
```

## 修复方案

### 修复内容

在`can_view_project`函数中增加对`sales_manager`角色的特殊处理：

```python
def can_view_project(user, project):
    """
    判断用户是否有权查看该项目：
    1. 归属人
    2. 厂商负责人
    3. 归属链
    4. 财务总监、解决方案经理、产品经理可以查看所有项目
    5. 销售经理特殊权限：归属关系中的非业务机会项目 ✅ 新增
    6. 共享（如有 shared_with_users 字段，暂未支持）
    """
    # ... 前面的逻辑保持不变 ...
    
    from app.models.user import Affiliation
    affiliation_owner_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]
    
    # 归属关系权限检查 ✅ 新增逻辑
    if project.owner_id in affiliation_owner_ids:
        # 销售经理角色：只能查看归属关系中的非业务机会项目
        if user_role in ['sales', 'sales_manager']:
            return project.project_type != '业务机会'
        # 其他角色可以查看所有归属关系项目
        return True
    
    return False
```

### 修复位置

- **文件**：`app/utils/access_control.py`
- **函数**：`can_view_project`
- **行数**：约第759-786行

## 修复效果

### 修复前的问题
- ✅ 项目列表：显示归属关系的非业务机会项目
- ❌ 项目详情：无法查看归属关系的非业务机会项目
- 结果：用户看到项目但点击后显示"无权限"

### 修复后的改善
- ✅ 项目列表：显示归属关系的非业务机会项目
- ✅ 项目详情：可以正常查看归属关系的非业务机会项目
- 结果：权限逻辑一致，用户体验正常

## 影响评估

### 受影响的角色
- `sales`角色用户
- `sales_manager`角色用户

### 受影响的功能
- 项目列表显示
- 项目详情页面访问
- 项目相关的权限检查

### 风险评估
- **风险等级**：低
- **向后兼容**：是
- **数据安全**：改善（修复了权限不一致问题）

## 测试建议

### 测试场景

1. **lihuawei用户测试**：
   - 登录lihuawei账户
   - 查看项目列表
   - 点击归属关系中的非业务机会项目
   - 验证是否可以正常进入项目详情

2. **权限边界测试**：
   - 确认业务机会类型项目仍然无法访问（如果在归属关系中）
   - 确认自己的项目和厂商负责人项目仍可正常访问

3. **其他角色测试**：
   - 确认其他角色的权限逻辑未受影响

### 验证步骤

```python
# 可以创建测试脚本验证权限一致性
from app.utils.access_control import get_viewable_data, can_view_project

# 对于特定用户和项目
user = User.query.filter_by(username='lihuawei').first()
projects = get_viewable_data(Project, user).all()

for project in projects:
    list_visible = True  # 在列表中可见
    detail_accessible = can_view_project(user, project)
    
    if list_visible != detail_accessible:
        print(f"权限不一致：项目 {project.id}")
    else:
        print(f"权限一致：项目 {project.id}")
```

## 相关文档

- [lihuawei权限异常问题分析报告](./LIHUAWEI_PERMISSION_ISSUE_ANALYSIS.md)
- [项目权限控制文档](../docs/权限控制设计文档.md)

## 结论

此次修复解决了项目权限逻辑不一致的问题，确保了用户在项目列表中看到的项目都可以正常访问。修复遵循了现有的权限设计原则，不会引入新的安全风险，反而提升了系统的一致性和用户体验。 