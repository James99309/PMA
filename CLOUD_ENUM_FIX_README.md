# 云端审批状态枚举修复指南

## 🎯 问题诊断

**错误信息**：
```
ERROR:app:获取审批实例失败: (psycopg2.errors.InvalidTextRepresentation) 
invalid input value for enum approvalstatus: "RECALLED"
```

**问题分析**：
- 代码中定义了 `ApprovalStatus.RECALLED = "recalled"`
- 本地数据库枚举包含：`['PENDING', 'APPROVED', 'REJECTED', 'RECALLED']` 
- 云端数据库枚举可能缺少 `RECALLED` 值

## 🚀 修复方案

### 方案一：使用修复脚本 (推荐)

#### 1. 上传修复脚本到云端
```bash
scp fix_approval_status_enum.py user@server:/path/to/pma/
```

#### 2. 在云端执行修复
```bash
cd /path/to/pma
python fix_approval_status_enum.py
```

#### 3. 重启应用服务
```bash
sudo systemctl restart pma-app
# 或根据实际部署方式重启
```

### 方案二：直接SQL修复

#### 1. 连接云端数据库
```bash
psql -h [host] -U [username] -d [database]
```

#### 2. 检查当前枚举值
```sql
SELECT enumlabel 
FROM pg_enum e
JOIN pg_type t ON e.enumtypid = t.oid 
WHERE t.typname = 'approvalstatus'
ORDER BY e.enumsortorder;
```

#### 3. 添加缺失的枚举值
```sql
-- 如果RECALLED不存在，执行以下命令
ALTER TYPE approvalstatus ADD VALUE 'RECALLED';

-- 验证添加结果
SELECT enumlabel 
FROM pg_enum e
JOIN pg_type t ON e.enumtypid = t.oid 
WHERE t.typname = 'approvalstatus'
ORDER BY e.enumsortorder;
```

### 方案三：数据库迁移

#### 1. 创建迁移文件
```python
# 在 migrations/versions/ 目录下创建迁移文件
def upgrade():
    # 添加枚举值需要在事务外执行
    op.execute("ALTER TYPE approvalstatus ADD VALUE 'RECALLED'")

def downgrade():
    # 注意：PostgreSQL不支持删除枚举值
    pass
```

#### 2. 执行迁移
```bash
flask db upgrade
```

## ✅ 验证步骤

### 1. 检查枚举值
```sql
SELECT enumlabel FROM pg_enum e
JOIN pg_type t ON e.enumtypid = t.oid 
WHERE t.typname = 'approvalstatus';
```

**期望结果**：
```
 enumlabel 
-----------
 PENDING
 APPROVED
 REJECTED
 RECALLED
```

### 2. 测试应用功能
- 访问报销页面 `/expense/2`
- 测试图片上传功能
- 检查审批流程是否正常

### 3. 查看错误日志
```bash
tail -f /path/to/logs/app.log
# 确认没有更多的枚举错误
```

## 🛡️ 预防措施

### 1. 环境一致性检查
定期对比本地和云端的数据库结构：
```bash
# 导出枚举定义
pg_dump -h [host] -U [username] -d [database] --schema-only | grep -A5 -B5 approvalstatus
```

### 2. 迁移脚本改进
确保所有枚举变更都通过迁移脚本管理：
```python
def upgrade():
    # 检查枚举值是否存在
    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT COUNT(*) FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid 
        WHERE t.typname = 'approvalstatus' AND e.enumlabel = 'RECALLED'
    """))
    
    if result.fetchone()[0] == 0:
        op.execute("ALTER TYPE approvalstatus ADD VALUE 'RECALLED'")
```

### 3. 部署流程优化
- 部署前运行枚举检查脚本
- 自动化数据库结构对比
- 添加健康检查端点

## 🔧 故障排查

### 问题：修复脚本执行失败
**可能原因**：
- 数据库连接问题
- 权限不足
- 事务冲突

**解决方法**：
1. 检查数据库连接字符串
2. 确认用户有 ALTER TYPE 权限
3. 确保没有活跃的事务

### 问题：枚举值添加后仍然报错
**可能原因**：
- 应用缓存了旧的枚举定义
- 需要重启应用服务
- 代码和数据库不匹配

**解决方法**：
1. 重启应用服务
2. 清理应用缓存
3. 验证代码中的枚举定义

### 问题：数据库权限不足
**错误信息**：`permission denied for type approvalstatus`

**解决方法**：
```sql
-- 给用户授予类型权限
GRANT USAGE ON TYPE approvalstatus TO [username];
-- 或使用超级用户执行
```

## 📋 检查清单

- [ ] 确认云端数据库连接正常
- [ ] 备份数据库（如果是生产环境）
- [ ] 检查当前枚举值
- [ ] 执行修复操作
- [ ] 验证枚举值已添加
- [ ] 重启应用服务
- [ ] 测试报销功能
- [ ] 检查应用日志
- [ ] 验证审批流程正常

## 📞 技术支持

如果修复过程中遇到问题：

1. **收集信息**：
   - 错误日志完整信息
   - 数据库版本和配置
   - 当前枚举值列表

2. **常见解决方案**：
   - 重启数据库服务
   - 检查网络连接
   - 验证权限设置

3. **联系支持**：
   - 提供详细的错误信息
   - 包含修复尝试的日志
   - 说明云端环境配置

---

**最后更新**: 2025-08-08  
**适用版本**: PMA v1.3.5+  
**数据库**: PostgreSQL