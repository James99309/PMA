#!/bin/bash
# 快速OVS数据库备份脚本

# 设置变量
export PGPASSWORD='nyjrIc-gubcu4-rukhoc'
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cloud_db_backups/ovs_backup_${TIMESTAMP}.sql"

echo "开始OVS数据库备份..."
echo "备份文件: $BACKUP_FILE"

# 执行备份
/opt/homebrew/opt/postgresql@17/bin/pg_dump \
  -h aws-0-ap-southeast-1.pooler.supabase.com \
  -p 6543 \
  -U postgres.pqzviljbpfoqvyfulakl \
  -d postgres \
  --verbose \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  -f "$BACKUP_FILE"

# 检查结果
if [ $? -eq 0 ]; then
    echo "✅ 备份成功！"
    ls -lh "$BACKUP_FILE"
else
    echo "❌ 备份失败"
    exit 1
fi
