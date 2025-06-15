# PMA 数据库自动备份系统

## 概述

云端备份数据库文件列表及自动备份系统实现完成。系统支持定时自动备份、手动备份、多种备份类型和云存储集成。

## 云端备份文件清单

### 当前备份文件（按时间排序）

```
./cloud_backup_20250613_151838.sql               (2.47 MB) - 完整数据库备份
./cloud_backup_affiliations_20250613_160733.sql (856 KB)  - 归属关系数据备份  
./cloud_backup_dictionaries_20250613_153355.sql (854 KB)  - 字典数据备份
./cloud_backup_file_records_20250613_162849.sql (66 KB)   - 文件记录备份
./cloud_backup_file_records_20250613_162908.sql (66 KB)   - 文件记录备份
./cloud_backup_products_images_20250613_162559.sql (66 KB) - 产品图片记录备份
./render_backup_20250602_210908.sql              (1.92 MB) - Render平台备份
```

### 其他云端相关文件

```
./cloud_database_fix.sql                         - 数据库修复脚本
./cloud_db_final_upgrade_fixed.sql              - 最终升级脚本（已修复）
./cloud_db_final_upgrade.sql                    - 最终升级脚本
./cloud_db_upgrade_20250605_002155.sql          - 数据库升级脚本
./cloud_schema_20250613_151838.sql              - 云端模式定义
./cloud_schema_export_20250605_101744.sql       - 云端模式导出
./cloud_schema_final_20250613_151838.sql        - 最终云端模式
./cloud_schema.sql                              - 云端模式
./cloud_scoring_config.sql                      - 云端评分配置
```

## 自动备份系统功能

### ✅ 已实现功能

1. **定时自动备份**
   - 每天凌晨12点执行完整备份
   - 每6小时执行增量备份
   - 每周日凌晨2点清理过期备份

2. **多种备份类型**
   - 完整备份（`full`）：包含数据和结构
   - 增量备份（`incremental`）：仅最近24小时的数据变更
   - 结构备份（`schema_only`）：仅数据库结构
   - 数据备份（`data_only`）：仅数据内容

3. **备份管理功能**
   - 自动创建备份目录
   - 文件名时间戳标记
   - 备份文件大小统计
   - 过期文件自动清理
   - 备份状态监控

4. **Web管理界面**
   - 备份状态概览
   - 手动创建备份
   - 备份文件列表
   - 文件下载功能
   - 过期清理操作

5. **云存储支持**
   - AWS S3 集成
   - 阿里云 OSS 集成
   - 自动上传备份文件

## 使用方法

### 1. 通过Web界面管理

访问 `/backup` 路径：
- 查看备份状态和统计信息
- 手动创建各种类型的备份
- 下载现有备份文件
- 清理过期备份文件

### 2. 配置备份参数

在 `config.py` 中配置：

```python
# 备份服务配置
BACKUP_ENABLED = True                # 启用备份功能
BACKUP_SCHEDULE = '00:00'           # 每天凌晨12点备份
BACKUP_RETENTION_DAYS = 30          # 保留30天的备份
BACKUP_LOCATION = './backups'       # 备份文件存储位置

# 云存储配置（可选）
CLOUD_STORAGE_CONFIG = {
    'enabled': False,               # 是否启用云存储
    'type': 'aws_s3',              # 云存储类型
    'aws_s3': {
        'access_key': 'YOUR_KEY',
        'secret_key': 'YOUR_SECRET',
        'region': 'us-east-1',
        'bucket_name': 'your-bucket'
    }
}
```

### 3. 手动创建备份

```python
from app.services.database_backup import get_backup_service

backup_service = get_backup_service()

# 创建完整备份
backup_path = backup_service.create_backup('full')

# 创建增量备份
backup_path = backup_service.create_incremental_backup()

# 获取备份状态
status = backup_service.get_backup_status()
```

### 4. 命令行测试

运行测试脚本验证备份功能：

```bash
python test_backup_system.py
```

## 备份策略

### 推荐备份方案

1. **日常备份**
   - 每天完整备份：保证数据完整性
   - 每6小时增量备份：减少数据丢失风险

2. **备份保留**
   - 本地保留30天：满足短期恢复需求
   - 云存储长期保存：重要数据永久保护

3. **定期验证**
   - 每周检查备份文件完整性
   - 每月进行恢复测试

## 数据恢复

### 从备份恢复数据库

```bash
# 恢复完整备份
psql -h hostname -U username -d database_name -f backup_file.sql

# 或使用pg_restore（如果是自定义格式）
pg_restore -h hostname -U username -d database_name backup_file
```

## 监控和告警

### 备份状态监控

系统自动记录：
- 备份创建时间
- 备份文件大小
- 备份成功/失败状态
- 备份文件数量统计

### 日志记录

所有备份操作都会记录到应用日志：
- 备份开始/完成时间
- 备份文件路径和大小
- 错误信息和异常处理

## 云存储集成

### AWS S3 配置

1. 创建 S3 存储桶
2. 配置 IAM 用户权限
3. 设置环境变量：
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_S3_BUCKET=your_bucket_name
   ```

### 阿里云 OSS 配置

1. 创建 OSS 存储桶
2. 获取访问密钥
3. 设置环境变量：
   ```bash
   export OSS_ACCESS_KEY_ID=your_access_key
   export OSS_ACCESS_KEY_SECRET=your_secret_key
   export OSS_ENDPOINT=your_endpoint
   export OSS_BUCKET_NAME=your_bucket_name
   ```

## 安全考虑

### 备份文件保护

1. **访问控制**
   - 仅系统管理员可访问备份功能
   - 备份文件存储在安全目录
   - 下载操作记录用户日志

2. **数据加密**
   - 建议在云存储中启用加密
   - 传输过程使用 HTTPS/TLS

3. **权限管理**
   - 定期轮换云存储访问密钥
   - 最小权限原则配置

## 故障排除

### 常见问题

1. **备份创建失败**
   - 检查数据库连接
   - 验证 pg_dump 命令可用性
   - 确认备份目录写权限

2. **云存储上传失败**
   - 验证访问密钥配置
   - 检查网络连接
   - 确认存储桶权限

3. **磁盘空间不足**
   - 调整备份保留天数
   - 启用云存储自动上传
   - 手动清理过期文件

### 日志分析

查看备份相关日志：
```bash
# 应用日志
tail -f app.log | grep backup

# 系统日志
journalctl -u your-app-service | grep backup
```

## 系统要求

### 软件依赖

- PostgreSQL 客户端工具（pg_dump）
- Python 3.8+
- psycopg2-binary
- boto3（AWS S3 支持）
- oss2（阿里云 OSS 支持）
- schedule（定时任务）

### 硬件要求

- 足够的磁盘空间（建议至少数据库大小的 3 倍）
- 稳定的网络连接（云存储）
- 适当的内存（大型数据库备份）

## 性能优化

### 备份性能

1. **并行备份**
   - 使用 pg_dump 的并行选项
   - 分表备份大型数据库

2. **压缩优化**
   - 启用 gzip 压缩
   - 调整压缩级别

3. **网络优化**
   - 云存储上传使用多线程
   - 错峰执行大型备份

## 版本历史

- **v1.0** (2025-06-13): 基础备份功能实现
- **v1.1** (2025-06-13): 增加 Web 管理界面
- **v1.2** (2025-06-13): 集成云存储支持

## 支持和维护

如有问题或建议，请联系系统管理员或查看系统日志获取详细错误信息。

定期检查备份系统状态，确保数据安全可靠。 