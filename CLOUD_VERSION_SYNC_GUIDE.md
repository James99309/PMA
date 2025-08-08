# 云端版本同步指南

## 🎯 问题描述

云端部署环境显示版本与本地开发环境不一致的问题：
- **本地版本**: v1.3.5
- **云端版本**: v1.0.1 
- **问题**: 云端数据库的版本记录与实际应用版本不匹配

## 🔍 问题根因分析

### 1. 版本管理机制
- **应用版本**: 存储在 `app_version.json` 文件中
- **数据库版本**: 存储在 `version_records` 表中
- **显示逻辑**: 版本管理页面优先显示数据库中的当前版本

### 2. 云端部署差异
- 云端数据库可能使用了较旧的初始化数据
- 应用代码已更新但数据库版本记录未同步
- 版本管理表可能缺少最新的版本记录

### 3. 文件对比分析
```
本地 app_version.json: v1.3.5 (2025-08-08)
云端 database: v1.0.1 (2025-06-22)
```

## 🚀 解决方案

### 方案一：自动同步脚本 (推荐)

#### 1. 上传同步脚本到云端
将 `sync_cloud_version.py` 脚本上传到云端服务器。

#### 2. 云端执行同步
```bash
# 在云端服务器上执行
cd /path/to/pma
python sync_cloud_version.py
```

#### 3. 重启应用服务
```bash
# 重启Flask应用
sudo systemctl restart pma-app
# 或者使用其他重启命令，根据实际部署方式
```

### 方案二：手动数据库更新

#### 1. 连接云端数据库
```sql
-- 查看当前版本状态
SELECT * FROM version_records WHERE is_current = true;

-- 查看所有版本记录
SELECT id, version_number, release_date, is_current 
FROM version_records 
ORDER BY release_date DESC;
```

#### 2. 更新版本记录
```sql
-- 设置所有版本为非当前版本
UPDATE version_records SET is_current = false;

-- 检查是否存在1.3.5版本
SELECT * FROM version_records WHERE version_number = '1.3.5';

-- 如果不存在，插入新版本记录
INSERT INTO version_records (
    version_number, 
    version_name, 
    description, 
    is_current, 
    environment, 
    release_date,
    created_at,
    updated_at
) VALUES (
    '1.3.5',
    'PMA项目管理系统 v1.3.5',
    '云端版本同步更新，包含最新的功能改进和界面优化',
    true,
    'production',
    NOW(),
    NOW(),
    NOW()
);

-- 如果存在，设置为当前版本
UPDATE version_records 
SET is_current = true, updated_at = NOW() 
WHERE version_number = '1.3.5';
```

#### 3. 创建升级日志
```sql
-- 获取新版本的ID
SELECT id FROM version_records WHERE version_number = '1.3.5';

-- 插入升级日志（假设版本ID为新获取的ID）
INSERT INTO upgrade_logs (
    version_id,
    from_version,
    to_version,
    upgrade_date,
    upgrade_type,
    status,
    operator_name,
    environment,
    upgrade_notes
) VALUES (
    (SELECT id FROM version_records WHERE version_number = '1.3.5'),
    '1.0.1',
    '1.3.5',
    NOW(),
    'deployment_sync',
    'success',
    '云端同步系统',
    'production',
    '云端版本同步：修复版本显示不一致问题'
);
```

### 方案三：重新部署 (最彻底)

#### 1. 备份云端数据
```bash
# 备份数据库
pg_dump -h [host] -U [username] -d [database] > backup_before_sync.sql
```

#### 2. 更新部署包
- 确保 `app_version.json` 包含正确版本
- 包含最新的数据库迁移脚本
- 包含版本同步脚本

#### 3. 执行部署
```bash
# 上传最新代码
# 运行数据库迁移
# 执行版本同步
python sync_cloud_version.py
```

## 🔧 同步脚本功能详解

### sync_cloud_version.py 主要功能

1. **版本检测**: 读取 `app_version.json` 获取实际版本
2. **数据库同步**: 更新 `version_records` 表的当前版本
3. **升级记录**: 创建升级日志记录版本变更
4. **智能描述**: 自动生成升级说明文档
5. **结果验证**: 验证同步后的版本状态

### 脚本执行流程

```
1. 读取 app_version.json → 获取目标版本
2. 查询数据库当前版本 → 对比版本差异  
3. 创建/更新版本记录 → 设置当前版本
4. 生成升级说明 → 创建升级日志
5. 验证同步结果 → 确认版本一致
```

### 日志输出示例

```
============================================================
🚀 开始云端版本同步
============================================================
读取到版本信息: 1.3.5
目标同步版本: 1.3.5
当前数据库版本: 1.0.1
创建新版本记录: 1.3.5
✅ 版本同步成功: 1.0.1 → 1.3.5
✅ 升级日志已记录
✅ 当前数据库版本: 1.3.5
============================================================
✅ 云端版本同步完成
============================================================
```

## 📋 验证步骤

### 1. 版本管理页面验证
- 访问 `/admin/version` 
- 确认显示版本为 v1.3.5
- 验证发布日期正确
- 检查版本信息完整

### 2. 数据库验证
```sql
-- 验证当前版本
SELECT version_number, release_date, is_current 
FROM version_records 
WHERE is_current = true;

-- 验证升级日志
SELECT from_version, to_version, upgrade_date, status 
FROM upgrade_logs 
ORDER BY upgrade_date DESC 
LIMIT 5;
```

### 3. 应用功能验证
- 仪表盘版本号显示
- 版本详情页面访问
- 升级信息正常加载
- 所有模块功能正常

## ⚠️ 注意事项

### 1. 执行前备份
- **必须**备份云端数据库
- 记录当前版本状态
- 保存重要配置信息

### 2. 执行时机
- 选择业务低峰期执行
- 确保有足够维护时间
- 准备回滚方案

### 3. 权限要求
- 数据库写入权限
- 文件访问权限
- 应用重启权限

### 4. 环境变量
确保云端环境变量配置正确：
- `DATABASE_URL`: 数据库连接
- `FLASK_ENV`: 环境标识
- `APP_VERSION`: 应用版本（可选）

## 🔄 回滚方案

如果同步出现问题，可按以下步骤回滚：

### 1. 恢复数据库
```bash
psql -h [host] -U [username] -d [database] < backup_before_sync.sql
```

### 2. 手动设置版本
```sql
UPDATE version_records SET is_current = false;
UPDATE version_records SET is_current = true WHERE version_number = '1.0.1';
```

### 3. 重启应用
```bash
sudo systemctl restart pma-app
```

## 📞 技术支持

如果在版本同步过程中遇到问题：

1. **检查日志**: 查看 `sync_cloud_version.log` 文件
2. **数据库状态**: 验证数据库连接和权限
3. **环境变量**: 确认所有必需的环境变量设置
4. **文件权限**: 检查应用文件访问权限

## 🎯 预防措施

### 1. 版本发布流程
- 部署前更新 `app_version.json`
- 包含版本同步脚本
- 执行自动化测试
- 验证版本一致性

### 2. 监控机制
- 添加版本一致性检查
- 设置版本差异告警
- 定期版本状态审核
- 自动化健康检查

### 3. 文档维护
- 记录每次版本变更
- 更新部署文档
- 维护回滚程序
- 培训运维团队

---

**最后更新**: 2025-08-08  
**版本**: v1.0  
**适用环境**: PMA项目管理系统云端部署