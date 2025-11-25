#!/bin/bash
# 简化的OVS数据库备份（不包含权限和安全策略）

export PGPASSWORD='nyjrIc-gubcu4-rukhoc'
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cloud_db_backups/ovs_simple_backup_${TIMESTAMP}.sql"

echo "开始简化OVS备份（排除权限和安全策略）..."
echo "备份文件: $BACKUP_FILE"

# 使用更简单的选项
/opt/homebrew/opt/postgresql@17/bin/pg_dump \
  -h aws-0-ap-southeast-1.pooler.supabase.com \
  -p 6543 \
  -U postgres.pqzviljbpfoqvyfulakl \
  -d postgres \
  --data-only \
  --inserts \
  --no-owner \
  --no-privileges \
  -f "$BACKUP_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ 数据备份成功！"
    ls -lh "$BACKUP_FILE"
else
    echo "❌ 备份失败，尝试仅结构备份..."

    # 如果数据备份失败，尝试只备份结构
    SCHEMA_FILE="cloud_db_backups/ovs_schema_${TIMESTAMP}.sql"
    /opt/homebrew/opt/postgresql@17/bin/pg_dump \
      -h aws-0-ap-southeast-1.pooler.supabase.com \
      -p 6543 \
      -U postgres.pqzviljbpfoqvyfulakl \
      -d postgres \
      --schema-only \
      --no-owner \
      --no-privileges \
      -f "$SCHEMA_FILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "✅ 结构备份成功！"
        ls -lh "$SCHEMA_FILE"
    else
        echo "❌ 结构备份也失败"
        exit 1
    fi
fi
