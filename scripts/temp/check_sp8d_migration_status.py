#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查SP8D数据库的迁移状态
"""
import sys, os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from sqlalchemy import create_engine, text

# SP8D数据库连接
SP8D_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def check_migration_status():
    """检查迁移状态"""
    print("=" * 80)
    print("📊 SP8D数据库迁移状态检查")
    print("=" * 80)

    engine = create_engine(SP8D_URL, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            # 1. 检查当前迁移版本
            print("\n1️⃣ 检查当前迁移版本...")
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()

            if row:
                current_version = row[0]
                print(f"   ✅ 当前版本: {current_version}")
            else:
                print(f"   ⚠️  未找到迁移版本信息")
                current_version = None

            # 2. 检查待执行的迁移文件
            print("\n2️⃣ 检查本地迁移文件...")
            migrations_dir = os.path.join(get_project_root(), 'migrations', 'versions')

            if os.path.exists(migrations_dir):
                migration_files = [f for f in os.listdir(migrations_dir)
                                 if f.endswith('.py') and not f.startswith('__')]
                migration_files.sort()

                print(f"   📁 本地迁移文件总数: {len(migration_files)}")

                if migration_files:
                    print(f"\n   最新的5个迁移文件:")
                    for f in migration_files[-5:]:
                        # 提取版本号（文件名格式：revision_description.py）
                        revision = f.split('_')[0]
                        is_current = (revision == current_version)
                        marker = "👉" if is_current else "  "
                        print(f"   {marker} {f}")

                    if current_version:
                        # 查找当前版本之后的迁移文件
                        current_found = False
                        pending_migrations = []

                        for f in migration_files:
                            revision = f.split('_')[0]
                            if current_found:
                                pending_migrations.append(f)
                            elif revision == current_version:
                                current_found = True

                        if pending_migrations:
                            print(f"\n   ⚠️  待执行的迁移 ({len(pending_migrations)} 个):")
                            for f in pending_migrations:
                                print(f"      📝 {f}")
                        else:
                            print(f"\n   ✅ 数据库已是最新版本")
                    else:
                        print(f"\n   ⚠️  无法确定待执行的迁移（未找到当前版本）")
            else:
                print(f"   ❌ 迁移目录不存在: {migrations_dir}")

            # 3. 检查数据库表结构
            print("\n3️⃣ 检查关键表结构...")

            # 检查companies表是否有source字段
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'companies'
                AND column_name IN ('source', 'company_name', 'company_type')
                ORDER BY column_name
            """))

            companies_columns = {row[0]: row[1] for row in result.fetchall()}

            if 'source' in companies_columns:
                print(f"   ✅ companies.source 字段已存在 ({companies_columns['source']})")
            else:
                print(f"   ⚠️  companies.source 字段不存在（待迁移）")

            # 检查quotations表是否有customer_id字段
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'quotations'
                AND column_name IN ('customer_id', 'quotation_number')
                ORDER BY column_name
            """))

            quotations_columns = {row[0]: row[1] for row in result.fetchall()}

            if 'customer_id' in quotations_columns:
                print(f"   ✅ quotations.customer_id 字段已存在 ({quotations_columns['customer_id']})")
            else:
                print(f"   ⚠️  quotations.customer_id 字段不存在（待迁移）")

            # 检查permissions表是否有content_filters字段
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'permissions'
                AND column_name IN ('content_filters', 'module')
                ORDER BY column_name
            """))

            permissions_columns = {row[0]: row[1] for row in result.fetchall()}

            if 'content_filters' in permissions_columns:
                print(f"   ✅ permissions.content_filters 字段已存在 ({permissions_columns['content_filters']})")
            else:
                print(f"   ⚠️  permissions.content_filters 字段不存在（待迁移）")

            print("\n" + "=" * 80)
            print("📊 状态总结")
            print("=" * 80)

            if current_version:
                print(f"✅ 当前迁移版本: {current_version}")
            else:
                print(f"⚠️  未找到迁移版本")

            missing_fields = []
            if 'source' not in companies_columns:
                missing_fields.append("companies.source")
            if 'customer_id' not in quotations_columns:
                missing_fields.append("quotations.customer_id")
            if 'content_filters' not in permissions_columns:
                missing_fields.append("permissions.content_filters")

            if missing_fields:
                print(f"⚠️  缺失字段 ({len(missing_fields)} 个):")
                for field in missing_fields:
                    print(f"   - {field}")
                print(f"\n💡 建议: 需要执行迁移来添加这些字段")
            else:
                print(f"✅ 所有新增字段已存在")

            print("\n" + "=" * 80)

    finally:
        engine.dispose()

if __name__ == '__main__':
    check_migration_status()
