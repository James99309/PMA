#!/bin/bash
# GitHub备份脚本
# 将备份文件推送到私有GitHub仓库

BACKUP_REPO="your-username/pma-backups"  # 替换为您的GitHub仓库
BACKUP_DIR="./github_backups"

# 创建备份目录
mkdir -p $BACKUP_DIR
cd $BACKUP_DIR

# 如果是第一次，克隆仓库
if [ ! -d ".git" ]; then
    git clone https://github.com/$BACKUP_REPO.git .
fi

# 创建数据库备份
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="cloud_backup_$TIMESTAMP.sql"

pg_dump \
    --host=dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com \
    --port=5432 \
    --username=pma_db_sp8d_user \
    --no-password \
    --format=plain \
    --clean \
    --create \
    --encoding=UTF8 \
    pma_db_sp8d > $BACKUP_FILE

# 压缩备份文件
gzip $BACKUP_FILE

# 提交到GitHub
git add .
git commit -m "Auto backup: $TIMESTAMP"
git push origin main

echo "✅ 备份已推送到GitHub: $BACKUP_FILE.gz"
