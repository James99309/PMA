# PMA系统云端数据库升级指南

## 🔄 Render.com 自动部署流程

### 代码推送后的自动流程：
1. **Git推送触发**: 推送到main分支触发Render自动部署
2. **环境构建**: Render构建新的应用环境
3. **依赖安装**: 安装requirements.txt中的依赖
4. **应用启动**: 运行run.py启动应用

### ⚠️ 关键问题：Render不会自动执行数据库迁移

## 🛠️ 手动数据库升级步骤

### 方法1: 通过Render Web Terminal（推荐）

1. **登录Render控制台**
   - 访问: https://dashboard.render.com
   - 找到你的PMA应用服务

2. **打开Web Terminal**
   - 在服务页面点击 "Shell" 或 "Terminal"
   - 等待终端连接

3. **执行数据库迁移命令**
   ```bash
   # 检查当前迁移状态
   flask db current
   
   # 查看待处理的迁移
   flask db history
   
   # 执行数据库升级
   flask db upgrade
   
   # 验证升级结果
   flask db current
   ```

### 方法2: 本地连接云端数据库

1. **设置环境变量**
   ```bash
   export DATABASE_URL="postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
   ```

2. **执行迁移**
   ```bash
   flask db upgrade
   ```

### 方法3: 直接SQL执行（紧急情况）

如果Flask迁移失败：

```bash
# 连接数据库
psql $DATABASE_URL

# 执行修复脚本
\i cloud_database_fix.sql

# 手动更新迁移版本表
INSERT INTO alembic_version VALUES ('c1308c08d0c9');
```

## 📋 升级验证清单

### 升级后必须验证：

1. **迁移版本检查**
   ```bash
   flask db current
   # 应该显示: c1308c08d0c9
   ```

2. **数据完整性验证**
   ```sql
   SELECT COUNT(*) FROM approval_record WHERE step_id IS NULL;
   # 应该返回: 0
   ```

3. **应用功能测试**
   - 登录系统正常
   - 项目列表加载正常
   - 筛选功能工作正常

## 🚨 常见问题解决

### 问题1: 迁移失败 - step_id约束错误
```bash
# 先修复数据
UPDATE approval_record SET step_id = 11 WHERE step_id IS NULL;
# 然后重新执行迁移
flask db upgrade
```

### 问题2: 连接超时
```bash
# 增加连接超时时间
export SQLALCHEMY_ENGINE_OPTIONS='{"connect_args": {"connect_timeout": 30}}'
flask db upgrade
```

## ⏱️ 升级时间预估

- **小型迁移**: 2-5分钟
- **数据修复**: 1-3分钟  
- **验证测试**: 2-5分钟
- **总计**: 5-15分钟

## 📞 紧急联系

如遇到问题：
- **技术负责人**: 倪捷
- **邮箱**: James.ni@evertacsolutions.com 