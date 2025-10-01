# 数据库同步完整解决方案指南

## 问题背景

本地数据库和云端数据库不一致，云端在迁移中没有成功将本地修改后的字段都同步到云端。

## 解决方案概览

我们提供了多个工具来解决这个问题：

### 1. 完整同步工具（推荐）
```bash
# 新建的完整解决方案
python3 complete_db_sync_solution.py --check  # 检查差异
python3 complete_db_sync_solution.py --sync   # 执行同步
```

### 2. 现有同步工具
```bash
# 已存在的工具
python3 sync_db_to_render.py --export-only    # 导出模式
python3 sync_db_to_render.py --apply          # 自动应用
```

## 详细使用步骤

### 步骤1: 检查差异

首先检查本地和云端数据库的差异：

```bash
cd /Users/nijie/Documents/PMA

# 方法1: 使用新工具（推荐）
python3 complete_db_sync_solution.py --check

# 方法2: 使用现有工具
python3 sync_db_to_render.py --export-only
```

### 步骤2: 设置环境变量

确保设置了正确的数据库连接信息：

```bash
# 本地数据库URL（默认）
export DATABASE_URL="postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

# 云端数据库URL（需要设置）
export RENDER_DATABASE_URL="你的云端数据库URL"
```

### 步骤3: 执行同步

#### 安全同步（推荐）
```bash
# 自动备份并同步
python3 complete_db_sync_solution.py --sync
```

#### 快速同步
```bash
# 不备份，直接同步
python3 complete_db_sync_solution.py --sync --no-backup --force
```

#### 指定表同步
```bash
# 只同步特定表
python3 complete_db_sync_solution.py --sync --tables "projects,companies"
```

### 步骤4: 验证同步结果

```bash
# 再次检查差异
python3 complete_db_sync_solution.py --check
```

## 命令选项说明

### complete_db_sync_solution.py 选项

- `--check`: 仅检查差异，不执行同步
- `--sync`: 执行完整同步
- `--backup`: 仅备份云端数据库
- `--force`: 强制执行（跳过确认）
- `--tables`: 指定要同步的表（逗号分隔）
- `--no-backup`: 同步时不备份数据库

### 使用示例

```bash
# 1. 检查所有表的差异
python3 complete_db_sync_solution.py --check

# 2. 仅备份云端数据库
python3 complete_db_sync_solution.py --backup

# 3. 检查特定表的差异
python3 complete_db_sync_solution.py --check --tables "projects,companies"

# 4. 安全同步（含备份）
python3 complete_db_sync_solution.py --sync

# 5. 强制同步（不确认，不备份）
python3 complete_db_sync_solution.py --sync --force --no-backup

# 6. 同步特定表
python3 complete_db_sync_solution.py --sync --tables "projects"
```

## 故障排除

### 常见问题

#### 1. 连接失败
```
错误: 数据库连接失败
解决: 检查DATABASE_URL和RENDER_DATABASE_URL环境变量
```

#### 2. 权限问题
```
错误: 权限不足
解决: 确保数据库用户有足够权限执行DDL操作
```

#### 3. 备份失败
```
错误: 备份失败
解决: 检查pg_dump是否安装，或使用--no-backup跳过备份
```

### 手动修复方案

如果自动工具失败，可以手动执行修复：

#### 1. 手动添加rating字段（紧急修复）
```sql
-- 连接到云端数据库执行
ALTER TABLE projects 
ADD COLUMN rating INTEGER NULL 
CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5));

COMMENT ON COLUMN projects.rating IS '项目评分(1-5星)，NULL表示未评分';
```

#### 2. 使用现有修复脚本
```bash
python3 cloud_database_fix.py
```

#### 3. 运行迁移脚本
```bash
python3 migrations/add_project_rating_field.py
```

## 安全注意事项

1. **始终备份**: 同步前自动备份云端数据库
2. **预览模式**: 先查看将要执行的SQL
3. **事务回滚**: 出错时自动回滚
4. **分步执行**: 可以分表或分批处理

## 验证步骤

同步完成后，验证以下内容：

### 1. 检查特定字段
```sql
-- 检查projects表的rating字段
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'projects' AND column_name = 'rating';
```

### 2. 测试应用启动
```bash
python3 run.py --port 8080
```

### 3. 检查差异报告
查看生成的差异报告文件：
- `db_differences_YYYYMMDD_HHMMSS.json`
- `migration_YYYYMMDD_HHMMSS.sql`

## 生成的文件说明

### 备份文件
- `db_backups/render_backup_YYYYMMDD_HHMMSS.sql`: 云端数据库备份

### 差异报告
- `db_differences_YYYYMMDD_HHMMSS.json`: 详细差异报告
- `db_sync.log`: 同步操作日志

### 迁移文件
- `migration_YYYYMMDD_HHMMSS.sql`: 生成的迁移SQL
- `local_schema_YYYYMMDD_HHMMSS.sql`: 本地数据库结构导出

## 定期维护建议

1. **定期检查**: 每周检查一次数据库差异
2. **自动化**: 可以将检查集成到CI/CD流程
3. **监控**: 设置监控告警，发现差异时通知
4. **文档**: 记录每次同步的操作和结果

## 联系支持

如果遇到问题，请：
1. 查看`db_sync.log`日志文件
2. 检查生成的差异报告
3. 提供详细的错误信息和环境配置

---

**更新日期**: 2025-06-02  
**版本**: 1.0  
**状态**: ✅ 测试通过 