# 项目筛选器用户选项获取问题修复报告

## 问题描述
项目列表页面的筛选器中，"拥有者"和"厂商负责人"下拉选项显示为空，用户无法通过这两个字段进行筛选。

## 问题排查过程

### 1. 数据检查
通过调试脚本 `debug_project_filter_options.py` 发现：
- 数据库中有 27 个用户，其中 9 个用户的 `_is_active=True`
- 数据库中有 448 个项目，都有 `owner_id`，343个有 `vendor_sales_manager_id`
- 数据完整性没有问题

### 2. 根本原因分析
发现关键问题：在项目视图的用户查询中，使用了 `User.is_active == True` 条件，但这个查询返回 0 个结果。

**问题根源**：
- `User.is_active` 在模型中定义为 `@property`，它不是一个数据库字段
- SQLAlchemy 无法在查询中直接使用 Python 属性进行过滤
- 实际的数据库字段名为 `_is_active`

### 3. 调试结果对比
```python
# 问题查询（返回0个结果）
User.query.filter(User.is_active == True).count()  # 0

# 正确查询（返回9个结果）  
User.query.filter(User._is_active == True).count()  # 9

# 手动筛选（返回9个结果）
[u for u in User.query.all() if u.is_active]  # 9个用户
```

## 修复方案

### 修复的文件和代码

#### 1. `/app/views/project.py` 文件修复

**文件位置**: 第2797行和第2825行

**修复前**:
```python
# _get_project_owner_options 函数
available_users = User.query.filter(
    User.id.in_(unique_owner_ids),
    User.is_active == True  # ❌ 问题代码
).order_by(User.real_name, User.username).all()

# _get_vendor_manager_options 函数  
available_managers = User.query.filter(
    User.id.in_(unique_manager_ids),
    User.is_active == True  # ❌ 问题代码
).order_by(User.real_name, User.username).all()
```

**修复后**:
```python
# _get_project_owner_options 函数
available_users = User.query.filter(
    User.id.in_(unique_owner_ids),
    User._is_active == True  # ✅ 修复后
).order_by(User.real_name, User.username).all()

# _get_vendor_manager_options 函数
available_managers = User.query.filter(
    User.id.in_(unique_manager_ids),
    User._is_active == True  # ✅ 修复后
).order_by(User.real_name, User.username).all()
```

#### 2. `/app/api/v1/affiliations.py` 文件修复

**文件位置**: 第400行

**修复前**:
```python
users = User.query.filter(
    User.is_active == True,  # ❌ 问题代码
    User.id != current_user.id
).all()
```

**修复后**:
```python
users = User.query.filter(
    User._is_active == True,  # ✅ 修复后
    User.id != current_user.id
).all()
```

## 修复验证

### 修复前测试结果
- 拥有者选项查询: **0个用户** ❌
- 厂商负责人选项查询: **0个用户** ❌

### 修复后测试结果  
- 拥有者选项查询: **9个用户** ✅
- 厂商负责人选项查询: **8个用户** ✅

### 修复后找到的用户列表
**拥有者选项**:
1. James Ni (ID: 5)
2. 倪捷 (ID: 6) 
3. 徐昊 (ID: 7)
4. 方玲 (ID: 2)
5. 李冬 (ID: 3)
6. 李华伟 (ID: 15)
7. 杨俊杰 (ID: 14)
8. 范敬 (ID: 16)
9. 郭小会 (ID: 13)

**厂商负责人选项**（8个，比拥有者少1个是因为数据中的差异）:
1. James Ni (ID: 5)
2. 倪捷 (ID: 6)
3. 徐昊 (ID: 7) 
4. 方玲 (ID: 2)
5. 李华伟 (ID: 15)
6. 杨俊杰 (ID: 14)
7. 范敬 (ID: 16)
8. 郭小会 (ID: 13)

## 影响范围

### 修复的功能
1. **项目列表筛选器** - 拥有者和厂商负责人下拉选项现在能正确显示
2. **关联数据API** - 用户选择接口能正确返回活跃用户

### 不受影响的功能
- 用户登录和认证功能（使用 `user.is_active` 属性）
- 用户权限检查（使用 `user.is_active` 属性）
- 其他业务逻辑中的用户状态判断

## 技术说明

### User模型中is_active的设计
```python
class User(db.Model):
    # 数据库字段
    _is_active = db.Column(db.Boolean, default=False, name="is_active")
    
    @property
    def is_active(self):
        """覆盖is_active属性，确保管理员账户总是激活的"""
        if self.role == 'admin':
            return True  # 管理员总是激活
        return bool(self._is_active)  # 其他用户根据字段决定
```

这种设计的好处：
- **业务逻辑**: 通过 `user.is_active` 属性获取，包含特殊规则（如管理员总是活跃）
- **数据库查询**: 通过 `User._is_active` 字段查询，性能更好

### 最佳实践
1. **数据库查询**: 使用 `User._is_active == True`
2. **业务逻辑判断**: 使用 `user.is_active` 属性
3. **批量状态检查**: 先查询后用属性判断

## 预防措施

### 代码审查检查点
1. 确认所有SQLAlchemy查询中使用的是数据库字段，而不是Python属性
2. 对于有 `@property` 装饰器的字段，查询时使用下划线前缀的实际字段名
3. 在类似场景中优先使用手动筛选或分步查询

### 建议改进
1. 考虑在User模型上添加类方法来标准化活跃用户查询
2. 在开发环境中添加查询结果检查，避免空结果问题

## 总结

这个问题是由于SQLAlchemy查询中错误使用Python属性而不是数据库字段导致的。修复后：

- ✅ 项目筛选器能正确显示用户选项
- ✅ 用户可以正常使用拥有者和厂商负责人筛选功能  
- ✅ API接口能正确返回活跃用户列表
- ✅ 不影响现有的业务逻辑

修复简单但重要，解决了用户无法使用关键筛选功能的问题。