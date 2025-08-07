# 🚨 紧急修复指南 - 解决共享字段不存在错误

## 问题描述

当前遇到的错误：
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column projects.shared_with_users does not exist
```

**原因**: 代码已经更新为使用新的共享字段，但数据库结构还没有相应更新。

## 🔧 解决方案

### 方案1: 立即应用数据库迁移（推荐）

#### 步骤1: 执行数据库迁移

```bash
# 在项目根目录执行
python3 apply_sharing_migration.py
```

这个脚本会：
- ✅ 为projects表添加 `shared_with_users` 和 `share_enabled` 字段
- ✅ 为companies表添加 `share_enabled` 字段
- ✅ 关闭所有客户的项目自动共享功能（解决zhouyj权限异常）
- ✅ 创建性能优化索引
- ✅ 初始化现有数据

#### 步骤2: 恢复模型定义

迁移成功后，需要取消注释项目模型中的字段定义：

编辑 `app/models/project.py`:
```python
# 将这些注释的行恢复
shared_with_users = Column(JSON, default=list, nullable=True)  # 共享给的用户ID列表
share_enabled = Column(Boolean, default=False, nullable=False)  # 是否启用共享
```

#### 步骤3: 重启应用

```bash
# 重启Flask应用
flask run
# 或重启生产服务
```

### 方案2: 手动执行SQL（如果Python脚本无法运行）

直接在数据库中执行以下SQL：

```sql
-- 连接到数据库并执行
BEGIN;

-- 添加项目共享字段
ALTER TABLE projects ADD COLUMN shared_with_users JSON DEFAULT '[]';
ALTER TABLE projects ADD COLUMN share_enabled BOOLEAN DEFAULT false;

-- 添加客户共享启用字段
ALTER TABLE companies ADD COLUMN share_enabled BOOLEAN DEFAULT false;

-- 初始化数据
UPDATE projects SET shared_with_users = '[]' WHERE shared_with_users IS NULL;
UPDATE projects SET share_enabled = false WHERE share_enabled IS NULL;
UPDATE companies SET share_enabled = false WHERE share_enabled IS NULL;

-- 关闭客户项目自动共享（解决zhouyj问题）
UPDATE companies SET share_related_projects = false WHERE share_related_projects = true;

-- 创建索引
CREATE INDEX idx_projects_shared_users ON projects USING gin (shared_with_users);
CREATE INDEX idx_projects_share_enabled ON projects (share_enabled);
CREATE INDEX idx_companies_share_enabled ON companies (share_enabled);

COMMIT;
```

### 方案3: 临时回滚代码（应急方案）

如果无法立即执行数据库迁移，可以临时回滚部分代码更改：

1. **保持模型字段注释状态**（已完成）
2. **临时禁用共享功能调用**

编辑 `app/views/project.py`，临时注释掉共享更新：
```python
# 临时注释掉，待迁移完成后恢复
# from app.utils.sharing import SharingService
# SharingService.update_sharing_from_request(project, current_user, 'project')
```

## 🎯 推荐执行顺序

### 立即执行（解决当前错误）:
1. ✅ **已完成**: 模型字段已注释，兼容性处理已添加
2. 🔄 **执行**: `python3 apply_sharing_migration.py`
3. 🔄 **恢复**: 取消注释模型字段定义
4. 🔄 **重启**: 重启应用服务
5. ✅ **验证**: 确认错误已解决

### 验证修复结果:
1. **访问项目页面** - 应该不再出现字段不存在错误
2. **检查zhouyj权限** - 应该只能看到自己的项目
3. **测试项目编辑** - 共享设置界面应该正常显示

## 📊 迁移前后对比

### 迁移前:
- ❌ zhouyj可以看到23个其他用户的项目（通过客户共享）
- ❌ 项目没有直接共享功能
- ❌ 客户共享会自动包含所有相关项目

### 迁移后:
- ✅ zhouyj只能看到自己的项目
- ✅ 项目支持精确的用户共享
- ✅ 客户共享和项目共享独立控制
- ✅ 更安全的权限控制

## ⚠️ 注意事项

1. **备份数据库**: 执行迁移前建议备份数据库
2. **测试环境**: 如果可能，先在测试环境验证
3. **权限检查**: 确保数据库用户有DDL权限
4. **应用重启**: 迁移后必须重启应用以重新加载模型

## 🆘 如果遇到问题

### 迁移失败:
1. 检查数据库连接配置
2. 确认用户权限足够
3. 查看具体错误信息
4. 考虑手动执行SQL

### 应用仍然报错:
1. 确认模型字段已取消注释
2. 检查应用是否重启
3. 清理Python缓存: `find . -name "*.pyc" -delete`

### 权限仍然异常:
1. 检查数据库中zhouyj相关的客户共享设置
2. 验证 `share_related_projects` 字段是否为false
3. 重新登录测试用户权限

## ✅ 成功标志

迁移成功后，应该看到：
- ✅ 应用正常启动，无字段错误
- ✅ zhouyj只能访问自己的项目
- ✅ 项目编辑页面显示共享设置
- ✅ 客户共享功能继续正常工作

---

**立即执行**: `python3 apply_sharing_migration.py` 解决当前错误！