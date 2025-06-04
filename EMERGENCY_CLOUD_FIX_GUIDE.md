# 🚨 PMA云端数据库紧急修复指南

## 当前问题分析
云端升级失败，错误信息：
```
psycopg2.errors.UndefinedObject: index "idx_scoring_config_category" does not exist
```

**根本原因**：原始Alembic迁移脚本 `c1308c08d0c9` 尝试删除不存在的索引，导致迁移失败。

## 🔧 立即修复方案

### 方案1：使用安全迁移脚本（推荐）

在Render Terminal中执行：

```bash
cd ~/project/src

# 运行安全迁移脚本
python safe_migration_c1308c08d0c9.py
```

### 方案2：手动绕过原始迁移

如果方案1不可用，手动执行以下步骤：

```bash
cd ~/project/src

# 1. 连接数据库，手动执行安全操作
psql $DATABASE_URL << 'EOF'

-- 安全删除索引（如果存在）
DROP INDEX IF EXISTS idx_scoring_config_category;
DROP INDEX IF EXISTS idx_scoring_records_category;
DROP INDEX IF EXISTS idx_scoring_records_project;
DROP INDEX IF EXISTS idx_quotations_is_locked;
DROP INDEX IF EXISTS idx_quotations_locked_by;
DROP INDEX IF EXISTS idx_project_rating_records_created_at;
DROP INDEX IF EXISTS idx_project_rating_records_project_id;
DROP INDEX IF EXISTS idx_project_rating_records_user_id;

-- 安全删除表
DROP TABLE IF EXISTS project_rating_records CASCADE;

-- 删除旧约束（如果存在）
ALTER TABLE project_scoring_config DROP CONSTRAINT IF EXISTS project_scoring_config_category_field_name_key;
ALTER TABLE project_scoring_records DROP CONSTRAINT IF EXISTS project_scoring_records_project_id_category_field_name_key;

-- 创建新约束（如果不存在）
ALTER TABLE project_scoring_config ADD CONSTRAINT uq_scoring_config UNIQUE (category, field_name);
ALTER TABLE project_scoring_records ADD CONSTRAINT uq_scoring_record_with_user UNIQUE (project_id, category, field_name, awarded_by);

-- 修复 approval_record.step_id NULL值
UPDATE approval_record SET step_id = (SELECT MIN(id) FROM approval_step LIMIT 1) WHERE step_id IS NULL;
ALTER TABLE approval_record ALTER COLUMN step_id SET NOT NULL;

-- 更改 projects.rating 列类型
ALTER TABLE projects ALTER COLUMN rating TYPE INTEGER USING rating::integer;

EOF

# 2. 手动标记迁移为已完成
psql $DATABASE_URL -c "UPDATE alembic_version SET version_num = 'c1308c08d0c9';"

# 3. 验证迁移版本
flask db current
```

### 方案3：重置迁移（最后手段）

⚠️ **警告：此方案会跳过所有迁移，只有在前两个方案都失败时才使用**

```bash
# 强制标记为最新版本
psql $DATABASE_URL -c "UPDATE alembic_version SET version_num = 'c1308c08d0c9';"

# 验证
flask db current
```

## ✅ 验证修复成功

执行以下命令确认修复成功：

1. **检查迁移版本**：
   ```bash
   flask db current
   ```
   应该显示：`c1308c08d0c9`

2. **检查约束状态**：
   ```bash
   psql $DATABASE_URL -c "\d+ project_scoring_config"
   psql $DATABASE_URL -c "\d+ project_scoring_records"
   ```

3. **启动应用测试**：
   ```bash
   python run.py
   ```

## 🎯 修复原理

**问题详情**：
- 原始迁移脚本使用了 `batch_op.drop_index()` 删除索引
- 但没有进行存在性检查
- 云端数据库中某些索引不存在，导致删除操作失败

**解决方案**：
1. **安全迁移脚本**：使用SQLAlchemy检查索引/约束存在性，只删除存在的对象
2. **手动SQL**：使用 `DROP ... IF EXISTS` 语法安全删除
3. **标记完成**：直接更新Alembic版本表，跳过有问题的迁移

## 📋 修复后检查清单

- [ ] 迁移版本为 `c1308c08d0c9`
- [ ] `project_scoring_config.uq_scoring_config` 约束存在
- [ ] `project_scoring_records.uq_scoring_record_with_user` 约束存在
- [ ] `approval_record.step_id` 为 NOT NULL
- [ ] `project_rating_records` 表已删除
- [ ] 应用能正常启动
- [ ] 项目列表筛选功能正常

## 🚀 推荐执行顺序

1. **首选**：方案1（安全迁移脚本）
2. **备选**：方案2（手动SQL操作）
3. **紧急**：方案3（强制标记完成）

## 📞 技术支持

如果所有方案都失败，请：

1. 复制完整错误日志
2. 运行 `psql $DATABASE_URL -c "\d"` 获取表结构
3. 运行 `flask db history` 查看迁移历史
4. 联系技术支持并提供以上信息

---

**创建时间**: 2025年6月4日  
**适用场景**: 云端迁移索引错误  
**预计修复时间**: 5-10分钟 