# 🚀 PMA云端数据库升级指南

## 📋 升级概述

本次升级将云端数据库结构同步到本地版本，主要包括：

- ✅ **projects.rating** 列类型从 `NUMERIC(2,1)` 改为 `INTEGER`
- ✅ **quotations** 表添加确认相关字段
- ✅ **project_rating_records** 表结构更新和约束修复  
- ✅ 清理无效的索引和约束
- ✅ 更新 Alembic 迁移版本到 `c1308c08d0c9`

## 🔧 执行升级

### 方案1：自动化升级（推荐）

在Render Terminal中执行：

```bash
cd ~/project/src

# 上传升级脚本到云端（如果还没有）
# 确保 cloud_db_final_upgrade.sql 和 execute_cloud_upgrade.py 文件存在

# 执行自动化升级
python execute_cloud_upgrade.py
```

### 方案2：手动SQL升级

如果自动化脚本不可用：

```bash
cd ~/project/src

# 直接执行SQL脚本
psql $DATABASE_URL -f cloud_db_final_upgrade.sql
```

### 方案3：分步手动升级

```bash
# 连接到云端数据库
psql $DATABASE_URL

-- 1. 修改 projects.rating 列类型
ALTER TABLE projects ALTER COLUMN rating TYPE INTEGER USING rating::integer;

-- 2. 清理 project_stage_history 表
DROP INDEX IF EXISTS ix_project_stage_history_user_id;
ALTER TABLE project_stage_history DROP COLUMN IF EXISTS user_id;

-- 3. 更新 quotations 表
ALTER TABLE quotations DROP COLUMN IF EXISTS approval_required_fields;
ALTER TABLE quotations DROP COLUMN IF EXISTS approval_comments;
ALTER TABLE quotations DROP COLUMN IF EXISTS approved_at;
ALTER TABLE quotations DROP COLUMN IF EXISTS approved_by;

ALTER TABLE quotations ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS confirmation_badge_color VARCHAR(20) DEFAULT NULL;
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS product_signature VARCHAR(64) DEFAULT NULL;
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS confirmed_by INTEGER;
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS confirmation_badge_status VARCHAR(20) DEFAULT 'none';

-- 4. 修复 project_rating_records 表
ALTER TABLE project_rating_records DROP COLUMN IF EXISTS comment;
ALTER TABLE project_rating_records ALTER COLUMN rating TYPE INTEGER USING rating::integer;

-- 5. 更新迁移版本
UPDATE alembic_version SET version_num = 'c1308c08d0c9';

-- 退出数据库
\q
```

## ✅ 验证升级结果

升级完成后，运行以下命令验证：

```bash
# 检查迁移版本
psql $DATABASE_URL -c "SELECT version_num FROM alembic_version;"

# 检查关键表结构
psql $DATABASE_URL -c "\d+ projects" | grep rating
psql $DATABASE_URL -c "\d+ quotations" | grep confirmed
psql $DATABASE_URL -c "\d+ project_rating_records" | grep rating

# 启动应用测试
python run.py
```

## 📊 预期结果

升级成功后，你应该看到：

1. **迁移版本**: `c1308c08d0c9`
2. **projects.rating**: `integer` 类型
3. **quotations** 表包含以下新列:
   - `confirmed_at`
   - `confirmation_badge_color` 
   - `product_signature`
   - `confirmed_by`
   - `confirmation_badge_status`
4. **project_rating_records.rating**: `integer` 类型
5. **应用启动无错误**

## 🚨 如果遇到问题

### 问题1：权限错误
```bash
# 确保使用正确的数据库URL
echo $DATABASE_URL
```

### 问题2：列已存在错误
```bash
# 脚本包含 IF NOT EXISTS 检查，应该不会出现此问题
# 如果仍有错误，可以手动删除相关列后重新执行
```

### 问题3：约束冲突
```bash
# 先删除冲突的约束
psql $DATABASE_URL -c "ALTER TABLE project_rating_records DROP CONSTRAINT IF EXISTS uq_project_rating_project_user;"
# 然后重新执行升级脚本
```

### 问题4：应用启动失败
```bash
# 检查数据库连接
psql $DATABASE_URL -c "SELECT 1;"

# 检查关键表是否存在
psql $DATABASE_URL -c "\dt"

# 查看详细错误日志
python run.py 2>&1 | head -50
```

## 📞 联系支持

如果升级过程中遇到任何问题，请提供：

1. 错误信息的完整日志
2. 当前迁移版本：`SELECT version_num FROM alembic_version;`
3. 表结构状态：`\d+ projects` 和 `\d+ quotations` 的输出

---

## 🎯 升级检查清单

- [ ] 备份重要数据（如果需要）
- [ ] 上传升级脚本到云端
- [ ] 执行升级命令
- [ ] 验证迁移版本
- [ ] 检查关键表结构
- [ ] 测试应用启动
- [ ] 验证核心功能正常

**升级完成！** 🎉 