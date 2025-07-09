# 云端sp8d数据库备份信息

## 备份详情
- **备份时间**: 2025-07-07 21:46:52
- **数据库**: pma_db_sp8d (云端)
- **连接地址**: dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com
- **备份文件**: cloud_sp8d_backup_20250707_214343.sql
- **文件大小**: 2.99 MB (3,133,698 bytes)
- **备份方式**: pg_dump (完整备份，包含结构和数据)

## 备份状态
✅ 备份成功完成

## 备份选项
- 格式: Plain SQL
- 包含清理语句: 是
- 包含权限: 否
- 包含所有者: 否

## 使用说明
1. 恢复到本地PostgreSQL:
   ```bash
   psql -d your_local_database < cloud_sp8d_backup_20250707_214343.sql
   ```

2. 查看备份内容:
   ```bash
   head -n 50 cloud_sp8d_backup_20250707_214343.sql
   ```

## 注意事项
- 此备份仅用于本地开发和测试
- 不会修改云端数据库的任何数据或结构
- 备份文件包含完整的数据库结构和数据
