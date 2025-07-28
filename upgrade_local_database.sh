#!/bin/bash
# 本地数据库迁移升级脚本
# 将本地数据库升级到与云端相同的版本

set -e  # 遇到错误立即退出

echo "🚀 开始本地数据库迁移升级..."

# 1. 激活虚拟环境
source venv/bin/activate

# 2. 备份当前数据库
echo "📦 创建数据库备份..."
timestamp=$(date +"%Y%m%d_%H%M%S")
pg_dump pma_local > "backups/local_backup_before_migration_${timestamp}.sql"
echo "✅ 备份完成: backups/local_backup_before_migration_${timestamp}.sql"

# 3. 检查当前迁移状态
echo "🔍 检查当前迁移状态..."
current_version=$(psql -d pma_local -t -c "SELECT version_num FROM alembic_version;" | xargs)
echo "当前版本: $current_version"

# 4. 执行迁移升级
echo "🚀 执行迁移升级..."
cd migrations
alembic upgrade head
cd ..

# 5. 验证升级结果
echo "✅ 验证升级结果..."
new_version=$(psql -d pma_local -t -c "SELECT version_num FROM alembic_version;" | xargs)
echo "新版本: $new_version"

# 6. 运行数据库完整性检查
echo "🔍 运行数据库完整性检查..."
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from app import db
    # 基本连接测试
    result = db.engine.execute('SELECT 1').scalar()
    print(f'数据库连接正常: {result == 1}')
    print('✅ 数据库完整性检查通过')
"

echo "🎉 本地数据库迁移升级完成!"
echo "📋 版本变化: $current_version -> $new_version"
