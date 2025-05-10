# 项目统计面板账户切换功能

## 功能概述

项目统计面板新增账户切换功能，支持按不同账户查看项目统计数据和趋势分析。主要功能包括：

1. 在统计面板顶部添加账户下拉选择器
2. 自动加载并显示所有有数据的账户列表
3. 切换账户时实时更新统计数据和趋势图表
4. 支持"全部账户"视图查看综合统计数据

## 实现变更

### 1. 数据库结构变更

在 `project_stage_history` 表中添加 `account_id` 字段，用于记录每条历史变更记录所属的账户。

```sql
ALTER TABLE project_stage_history ADD COLUMN account_id INTEGER;
CREATE INDEX ix_project_stage_history_account_id ON project_stage_history (account_id);
```

### 2. 后端API变更

- 统计数据API新增 `account_id` 参数支持
- 趋势数据API新增 `account_id` 参数支持
- 新增 `/projectpm/statistics/api/available_accounts` 接口，用于获取可用账户列表

### 3. 前端实现变更

- 统计面板顶部添加账户选择下拉菜单
- 实现账户列表加载和选择功能
- 添加账户切换事件，触发数据重新加载
- 数据请求时自动附加账户参数

## 使用方法

### 1. 数据库迁移

在部署前需要执行数据库迁移脚本，添加 `account_id` 字段：

```bash
python run_migration.py
```

### 2. 填充历史数据的账户信息

由于历史数据中没有账户信息，建议使用以下方法补充：

```sql
-- 按项目创建者设置account_id
UPDATE project_stage_history 
SET account_id = (
    SELECT created_by 
    FROM projects 
    WHERE projects.id = project_stage_history.project_id
);
```

或者使用Python脚本补充：

```python
from app import app, db
from app.models.projectpm_stage_history import ProjectStageHistory
from app.models.project import Project

with app.app_context():
    # 查询所有历史记录
    records = ProjectStageHistory.query.all()
    updated = 0
    
    for record in records:
        if record.account_id is None:
            # 获取项目创建者ID
            project = Project.query.get(record.project_id)
            if project and project.created_by:
                record.account_id = project.created_by
                updated += 1
    
    if updated > 0:
        db.session.commit()
        print(f"更新了 {updated} 条历史记录的账户信息")
```

### 3. 使用账户切换功能

1. 点击统计面板顶部的"全部账户"下拉菜单
2. 选择需要查看的特定账户
3. 统计数据和趋势图表会自动更新为所选账户的数据

默认情况下，系统会显示"全部账户"的统计数据。

## 测试案例

### 1. 账户列表加载

- 打开项目统计面板，验证账户下拉列表是否正确加载
- 确认列表中包含"全部账户"选项和所有有数据的账户

### 2. 账户切换

- 选择特定账户，验证统计数据是否更新
- 检查趋势图表是否显示所选账户的趋势数据
- 切换回"全部账户"，验证是否显示综合数据

### 3. 边界情况

- 当没有账户数据时，验证下拉菜单是否显示"无可用账户数据"
- 切换到没有数据的账户时，验证是否显示"无历史数据"提示

## 注意事项

1. 账户数据来源于阶段历史记录的 `account_id` 字段，确保添加新项目或变更阶段时正确设置该字段
2. 页面刷新后恢复到"全部账户"状态
3. 为保护数据隐私，用户只能查看自己有权限查看的项目数据，即使切换了账户 