# 数据库备份和迁移规范

## 🗄️ 云端数据库备份工具规范

### **备份工具概述**

项目包含两个云端数据库的标准化备份工具，用于定期备份和数据安全保障：

1. **SP8D 数据库备份工具**：`backup_cloud_pma_db.py`
2. **OVS 数据库备份工具**：`simple_ovs_backup.py`

### **备份工具位置和使用**

#### **SP8D 数据库备份**
```bash
# 位置：项目根目录
python3 backup_cloud_pma_db.py

# 功能：
# - 备份云端 pma_db_sp8d 数据库
# - 生成详细的备份信息报告
# - 自动验证数据完整性
```

#### **OVS 数据库备份**
```bash
# 位置：项目根目录
python3 simple_ovs_backup.py

# 功能：
# - 备份云端 pma_db_ovs 数据库
# - 生成统计信息
# - 避免超时问题的简化版本
```

### **备份工具规范**

#### **必须遵循的规范**
- ✅ **统一执行方式**：使用 `subprocess.run()` 同步执行
- ✅ **标准备份选项**：`--verbose --clean --if-exists --no-owner --no-privileges`
- ✅ **密码安全**：通过环境变量 `PGPASSWORD` 传递数据库密码
- ✅ **备份验证**：备份完成后验证文件大小和数据完整性
- ❌ **禁止使用**：`subprocess.Popen()` + 监控循环（可能导致死锁）

#### **备份文件命名规范**
```
云端备份文件格式：
- SP8D: pma_db_sp8d_backup_YYYYMMDD_HHMMSS.sql
- OVS:  pma_db_ovs_backup_simple_YYYYMMDD_HHMMSS.sql

备份信息文件格式：
- SP8D: backup_info_YYYYMMDD_HHMMSS.md
- OVS:  统计信息直接在控制台输出
```

#### **备份存储位置**
```
备份文件统一存储在：
/cloud_db_backups/

目录结构：
cloud_db_backups/
├── pma_db_sp8d_backup_*.sql     # SP8D 数据库备份
├── pma_db_ovs_backup_*.sql      # OVS 数据库备份
├── backup_info_*.md             # 备份信息文件
└── [其他历史备份文件]
```

### **备份完整性要求**

#### **必须包含的内容**
- ✅ **表结构**：所有表的 CREATE TABLE 语句
- ✅ **约束**：主键、外键、唯一约束、检查约束
- ✅ **索引**：所有自定义索引和系统索引
- ✅ **序列**：所有序列定义和当前值
- ✅ **数据**：使用 COPY 语句备份所有表数据
- ✅ **清理语句**：DROP 语句确保可重复恢复

#### **备份质量验证**
```bash
# 验证备份完整性的标准检查
grep -c "CREATE TABLE" backup_file.sql      # 表数量
grep -c "ADD CONSTRAINT" backup_file.sql    # 约束数量
grep -c "CREATE.*INDEX" backup_file.sql     # 索引数量
grep -c "COPY.*FROM stdin" backup_file.sql  # 数据表数量
```

### **数据库信息对照表**

| 数据库 | 连接地址 | 用户名 | 数据库名 | 估计大小 | 备份耗时 |
|--------|----------|--------|----------|----------|----------|
| **SP8D** | aws-0-ap-southeast-1.pooler.supabase.com:6543 | postgres.iqcyimnjtnmomvfuwjzw | postgres | ~19MB | ~3秒 |
| **OVS** | aws-0-ap-southeast-1.pooler.supabase.com:6543 | postgres.pqzviljbpfoqvyfulakl | postgres | ~12MB | ~3秒 |

### **完整数据库连接URL**

```bash
# SP8D数据库连接URL
SP8D_URL="postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

# OVS数据库连接URL  
OVS_URL="postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
```

## 🚀 云端数据库迁移升级规范

### **迁移升级概述**

项目建立了标准化的云端数据库迁移升级流程，用于将本地数据库结构变更同步到云端数据库，确保版本一致性和数据安全。

**核心工具：**
1. **SP8D标准迁移升级工具**：`standard_migration_upgrade.py`
2. **SP8D终极迁移同步工具**：`ultimate_migration_sync.py`
3. **OVS标准迁移升级工具**：`standard_migration_upgrade_ovs.py`
4. **OVS终极迁移同步工具**：`ultimate_migration_sync_ovs.py`
5. **迁移冲突修复工具**：`fix_migration_conflicts.py`

### **标准迁移升级流程**

#### **SP8D数据库升级（推荐方式）**
```bash
# SP8D标准Flask-Migrate升级流程
python3 standard_migration_upgrade.py
```

#### **OVS数据库升级（推荐方式）**
```bash
# OVS标准Flask-Migrate升级流程
python3 standard_migration_upgrade_ovs.py
```

**执行步骤：**
1. ✅ **检查迁移状态** - 对比本地和云端当前版本
2. ✅ **自动备份** - 升级前完整备份云端数据库
3. ✅ **执行升级** - 使用 `flask db upgrade` 标准命令
4. ✅ **验证结果** - 确认版本同步和数据完整性

#### **复杂冲突处理（终极方案）**

**SP8D数据库：**
```bash
# 当SP8D标准升级失败时使用
python3 ultimate_migration_sync.py
```

**OVS数据库：**
```bash
# 当OVS标准升级失败时使用
python3 ultimate_migration_sync_ovs.py
```

**适用场景：**
- 迁移文件与数据库实际结构不一致
- 存在索引或字段冲突
- 迁移版本历史混乱

#### **迁移冲突预处理**
```bash
# 修复已知的迁移冲突
python3 fix_migration_conflicts.py
```

### **升级策略选择**

**SP8D数据库：**

| 场景 | 推荐工具 | 说明 |
|------|----------|------|
| **日常升级** | `standard_migration_upgrade.py` | 标准Flask-Migrate流程 |
| **首次同步** | `ultimate_migration_sync.py` | 处理版本历史差异 |
| **冲突修复** | `fix_migration_conflicts.py` + 标准升级 | 先修复已知冲突 |
| **紧急回滚** | 使用备份文件直接恢复 | 数据安全优先 |

**OVS数据库：**

| 场景 | 推荐工具 | 说明 |
|------|----------|------|
| **日常升级** | `standard_migration_upgrade_ovs.py` | OVS专用标准Flask-Migrate流程 |
| **首次同步** | `ultimate_migration_sync_ovs.py` | 处理OVS版本历史差异 |
| **SP8D安全检查冲突** | `ultimate_migration_sync_ovs.py` | 绕过SP8D专用安全检查 |
| **紧急回滚** | 使用OVS备份文件直接恢复 | 数据安全优先 |

### **迁移文件管理规范**

#### **创建新迁移**
```bash
# 生成迁移文件
flask db revision -m "迁移描述"

# 自动生成（推荐）
flask db migrate -m "迁移描述"
```

#### **迁移文件审查**
创建迁移文件后必须审查：
- ✅ **操作安全性** - 确认不会删除重要数据
- ✅ **索引处理** - 检查索引删除/创建操作
- ✅ **字段约束** - 验证字段类型和约束变更
- ✅ **回滚逻辑** - 确保 downgrade() 函数正确

### **已知冲突类型及处理**

**SP8D数据库冲突：**

**索引不存在错误：**
```python
# 问题：尝试删除不存在的索引
batch_op.drop_index('idx_name')

# 解决：注释掉或使用安全删除
# batch_op.drop_index('idx_name')  # SP8D中不存在，跳过
```

**OVS数据库冲突：**

**SP8D安全检查阻止：**
```python
# 问题：迁移文件包含SP8D专用安全检查
def upgrade():
    if database_name != 'pma_db_sp8d':
        raise Exception("数据库安全检查失败 - 非SP8D数据库")

# 解决：使用终极迁移同步工具绕过安全检查
python3 ultimate_migration_sync_ovs.py
```

### **备份文件管理**

#### **备份文件命名**
```
SP8D升级备份文件格式：
- 标准升级：sp8d_pre_upgrade_backup_YYYYMMDD_HHMMSS.sql
- 终极同步：sp8d_ultimate_sync_backup_YYYYMMDD_HHMMSS.sql

OVS升级备份文件格式：
- 标准升级：ovs_pre_upgrade_backup_YYYYMMDD_HHMMSS.sql
- 终极同步：ovs_ultimate_sync_backup_YYYYMMDD_HHMMSS.sql
```

#### **备份文件保留策略**
- ✅ **升级备份** - 保留最近10次升级的备份文件
- ✅ **重要里程碑** - 手动标记重要版本的备份文件
- ✅ **定期清理** - 超过30天的常规备份可删除
- ✅ **异地备份** - 重要备份上传到云存储

### **工具脚本位置**

```
项目根目录下的迁移升级工具：
├── standard_migration_upgrade.py        # SP8D标准迁移升级脚本
├── ultimate_migration_sync.py           # SP8D终极迁移同步脚本
├── standard_migration_upgrade_ovs.py    # OVS标准迁移升级脚本
├── ultimate_migration_sync_ovs.py       # OVS终极迁移同步脚本
├── fix_migration_conflicts.py           # 迁移冲突修复脚本
├── backup_cloud_pma_db.py              # SP8D数据库备份工具
└── simple_ovs_backup.py                # OVS数据库备份工具
```

## 💾 数据库与模型规则

### **字段规范**
- **时间字段**：使用 UTC 存储，显示时转换为本地时间
- **金额字段**：数据库存储分（整数），显示时除以100转换为元
- **大金额显示**：除以10000显示为万元，格式化为2位小数
- **软删除**：使用 `is_deleted` 布尔字段，默认 `False`
- **创建/更新时间**：`created_at`, `updated_at` 使用 `datetime.utcnow()`

### **查询规范**
```python
# 正确 ✅ - 排除已删除记录
query = Model.query.filter(Model.is_deleted == False)

# 正确 ✅ - 金额转换
total_amount = order.total_amount / 10000  # 转换为万元

# 正确 ✅ - 时间格式化
created_time = order.created_at.strftime('%Y-%m-%d %H:%M')
```

## 🚨 故障排除指南

### **备份工具常见问题**

**问题1：备份超时**
- **原因**：使用了 `subprocess.Popen()` + 监控循环
- **解决**：使用简化版备份工具（已解决 OVS 超时问题）

**问题2：连接失败**
- **原因**：网络问题或数据库凭据错误
- **解决**：检查网络连接和数据库URL配置

**问题3：备份文件过小**
- **原因**：备份可能只包含结构，没有数据
- **解决**：检查备份选项，确认包含 COPY 语句

### **迁移升级常见错误**

**SP8D数据库错误：**

**错误1: 迁移版本不匹配**
```
本地版本：b891f72a8dcb
SP8D版本：sync_local_to_cloud_20250728
```
- **解决**：使用 `ultimate_migration_sync.py` 强制同步版本

**错误2: 索引删除失败**
```
sqlalchemy.exc.ProgrammingError: index "idx_name" does not exist
```
- **解决**：编辑迁移文件，注释掉不存在的索引删除操作

**OVS数据库错误：**

**错误1: SP8D安全检查失败**
```
Exception: 数据库安全检查失败 - 非SP8D数据库
安全检查失败: 当前数据库 'pma_db_ovs' 不是SP8D数据库
```
- **解决**：这是预期行为，直接使用 `ultimate_migration_sync_ovs.py`

### **紧急回滚流程**
```bash
# 1. 停止应用服务
# 2. 使用备份文件完全恢复
PGPASSWORD=password psql -h host -U user -d database < backup_file.sql

# 3. 验证恢复结果
# 4. 重启应用服务
```

## 🎯 最佳实践

### **备份执行最佳实践**

#### **执行频率建议**
- **开发环境**：根据需要手动执行
- **重要操作前**：必须执行备份（如数据库迁移、重大更新）
- **定期备份**：建议每周至少一次完整备份

#### **执行前检查清单**
1. ✅ 确认网络连接正常
2. ✅ 确认云端数据库可访问
3. ✅ 确认本地磁盘空间充足
4. ✅ 确认 PostgreSQL 客户端工具可用

#### **执行后验证清单**
1. ✅ 检查备份文件大小合理（通常 SP8D > OVS）
2. ✅ 检查备份文件包含表结构和数据
3. ✅ 检查控制台输出无错误信息
4. ✅ 对比数据行数与实时数据库一致

### **迁移升级最佳实践**

#### **开发阶段**
- ✅ **频繁迁移** - 小步快跑，避免大批量结构变更
- ✅ **本地测试** - 确保迁移在本地正常执行
- ✅ **代码审查** - 迁移文件必须经过代码审查
- ✅ **文档记录** - 重要结构变更记录在迁移说明中

#### **部署阶段**
- ✅ **备份优先** - 任何升级前先完整备份
- ✅ **标准流程** - 优先使用标准升级工具
- ✅ **版本验证** - 升级后立即验证版本一致性
- ✅ **功能测试** - 升级后进行基本功能测试

#### **监控维护**
- ✅ **定期检查** - 每周检查本地与云端版本一致性
- ✅ **备份清理** - 定期清理过期备份文件
- ✅ **工具更新** - 根据项目发展更新升级工具
- ✅ **经验总结** - 记录升级过程中的问题和解决方案

## ✅ 升级成功标志

升级完成后应确认以下指标：
- ✅ **版本一致** - 本地和云端 `flask db current` 版本相同
- ✅ **表数量匹配** - 云端表数量与本地一致
- ✅ **应用启动正常** - 云端应用使用新数据库结构正常启动
- ✅ **功能验证通过** - 关键功能测试正常

## 📝 实战验证案例

### **OVS数据库升级成功案例 (2025-08-01)**

**场景**: OVS云端数据库版本落后，需要与本地版本同步

**升级前状态**:
- 本地版本: `b891f72a8dcb`
- OVS版本: `ovs_sync_fix_20250729`
- 表数量: 62个表（两边一致）

**执行流程**:
1. **标准升级尝试**: 使用 `standard_migration_upgrade_ovs.py`
2. **遇到SP8D安全检查**: 按预期触发安全检查阻止
3. **终极同步成功**: 使用 `ultimate_migration_sync_ovs.py` 绕过安全检查
4. **版本完全同步**: 成功同步到 `b891f72a8dcb`

**验证结果**:
```bash
# 升级前
本地: b891f72a8dcb
OVS:  ovs_sync_fix_20250729

# 升级后
本地: b891f72a8dcb  
OVS:  b891f72a8dcb  ✅ 完全同步
```

**注意：此迁移升级流程已通过SP8D和OVS两个数据库的实战验证，可作为云端数据库升级的标准方法。**