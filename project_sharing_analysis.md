# 项目共享机制分析报告

## 🔍 当前项目共享机制

### 1. 现有共享机制
基于对代码和数据库的分析，**目前项目共享主要通过以下机制实现**：

#### 主要机制：客户项目共享
- **实现位置**: `app/utils/access_control.py:89-130`
- **函数**: `get_projects_through_customer_sharing_condition(user, model_class)`
- **原理**: 
  - 检查客户表中 `shared_with_users` 字段包含用户ID的记录
  - 同时该客户的 `share_related_projects = true`
  - 通过项目的客户关联字段(end_user, dealer, contractor, system_integrator, design_issues)找到相关项目
  - 允许用户查看这些项目

#### 辅助机制：
1. **归属关系 (Affiliations)**: 通过数据归属关系查看下级用户的项目
2. **厂商销售负责人**: 通过 `vendor_sales_manager_id` 字段
3. **角色特殊权限**: 特定角色(如财务总监、解决方案经理)的全局查看权限

### 2. 项目模型字段分析

**当前项目表字段**（无直接共享字段）：
```sql
- id, project_name, owner_id
- vendor_sales_manager_id  -- 厂商销售负责人
- 客户关联字段: end_user, dealer, contractor, system_integrator, design_issues
- 其他业务字段...
```

**客户表的共享字段**（用于项目共享）：
```sql
- shared_with_users: JSON数组，存储共享给的用户ID
- share_related_projects: 布尔值，是否共享相关项目
```

## 🎯 如果要添加项目直接共享机制

### 方案1: 参考客户共享模式（推荐）

需要在项目表添加以下字段：

```sql
ALTER TABLE projects ADD COLUMN shared_with_users JSON DEFAULT '[]';
ALTER TABLE projects ADD COLUMN share_enabled BOOLEAN DEFAULT false;
```

**实现步骤**：

1. **数据库迁移**：
```python
# migrations/versions/xxx_add_project_sharing.py
def upgrade():
    op.add_column('projects', sa.Column('shared_with_users', postgresql.JSON(), nullable=True, default='[]'))
    op.add_column('projects', sa.Column('share_enabled', sa.Boolean(), default=False))
```

2. **模型更新**：
```python
# app/models/project.py
from sqlalchemy.dialects.postgresql import JSON

class Project(db.Model):
    # ... 现有字段 ...
    shared_with_users = Column(JSON, default=list)  # 共享给的用户ID列表
    share_enabled = Column(Boolean, default=False)  # 是否启用共享
```

3. **权限逻辑更新**：
```python
# app/utils/access_control.py - 在get_viewable_data函数中添加
def get_projects_direct_sharing_condition(user, model_class):
    """获取直接项目共享的查询条件"""
    from sqlalchemy import cast, text
    from sqlalchemy.dialects.postgresql import JSONB
    
    return db.and_(
        model_class.share_enabled == True,
        cast(model_class.shared_with_users, JSONB).op('@>')(text(f"'{user.id}'"))
    )
```

4. **前端界面**：
```html
<!-- 在项目详情页面添加共享设置 -->
<div class="form-group">
    <label>项目共享设置</label>
    <div class="form-check">
        <input type="checkbox" id="share_enabled" name="share_enabled" {% if project.share_enabled %}checked{% endif %}>
        <label for="share_enabled">启用项目共享</label>
    </div>
    <select multiple name="shared_with_users" id="shared_with_users">
        <!-- 用户选择列表 -->
    </select>
</div>
```

### 方案2: 独立项目共享表

创建独立的项目共享关系表：

```sql
CREATE TABLE project_shares (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    shared_with_user_id INTEGER REFERENCES users(id),
    shared_by_user_id INTEGER REFERENCES users(id),
    share_type VARCHAR(20) DEFAULT 'view',  -- view, edit
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, shared_with_user_id)
);
```

## 📋 实施建议

### 推荐方案1的原因：
1. **一致性**: 与现有客户共享机制保持一致
2. **简洁性**: 直接在项目表添加字段，查询效率高
3. **维护性**: 减少表连接，降低复杂度

### 实施优先级：
1. **高优先级**: 数据库字段添加和模型更新
2. **中优先级**: 权限逻辑集成
3. **低优先级**: 前端界面开发

### 注意事项：
1. **权限检查**: 需要在 `can_edit_project_sharing()` 函数中定义谁可以设置项目共享
2. **性能优化**: JSON字段查询需要适当的索引
3. **数据迁移**: 现有项目的默认共享设置
4. **权限继承**: 考虑项目共享与客户共享的优先级关系

## 🔧 快速实现代码示例

```python
# 1. 权限检查函数
def can_edit_project_sharing(user, project):
    """检查是否可以编辑项目共享设置"""
    if user.role == 'admin':
        return True
    if project.owner_id == user.id:
        return True
    if hasattr(project, 'vendor_sales_manager_id') and project.vendor_sales_manager_id == user.id:
        return True
    return False

# 2. 权限逻辑集成（在get_viewable_data函数中）
def get_viewable_projects_with_direct_sharing(user):
    """获取包含直接共享的项目查询条件"""
    basic_conditions = [
        Project.owner_id == user.id,  # 自己的项目
        Project.vendor_sales_manager_id == user.id,  # 厂商负责人项目
    ]
    
    # 添加直接共享条件
    if hasattr(Project, 'shared_with_users'):
        from sqlalchemy import cast, text
        from sqlalchemy.dialects.postgresql import JSONB
        
        direct_share_condition = db.and_(
            Project.share_enabled == True,
            cast(Project.shared_with_users, JSONB).op('@>')(text(f"'{user.id}'"))
        )
        basic_conditions.append(direct_share_condition)
    
    return db.or_(*basic_conditions)
```

## 📊 结论

**回答你的问题**：
1. **目前项目共享确实主要通过客户共享机制实现**
2. **如果要添加项目直接共享，需要增加字段**：`shared_with_users` (JSON) 和 `share_enabled` (Boolean)
3. **推荐采用方案1，与现有架构保持一致**

这样的设计既能满足直接项目共享的需求，又能与现有的权限系统无缝集成。