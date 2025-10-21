#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OVS数据库迁移状态检查脚本
检查云端OVS数据库的迁移历史，对比本地迁移文件，识别未应用的迁移
"""
import sys, os
import re
from datetime import datetime
from pathlib import Path

# 路径修正 - 支持从任何位置运行
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
import psycopg2

# OVS数据库连接信息
OVS_URL = "postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"


def get_ovs_migration_version():
    """获取OVS数据库当前的迁移版本"""
    print("=" * 80)
    print("☁️  检查OVS数据库迁移版本")
    print("=" * 80)

    try:
        engine = create_engine(OVS_URL)
        with engine.connect() as conn:
            # 检查alembic_version表是否存在
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'alembic_version'
                )
            """))
            table_exists = result.scalar()

            if not table_exists:
                print("⚠️  alembic_version表不存在")
                print("   OVS数据库可能从未执行过迁移")
                engine.dispose()
                return None

            # 获取当前版本
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()

            if version:
                print(f"✅ 当前迁移版本: {version}")
            else:
                print("⚠️  alembic_version表为空")
                version = None

        engine.dispose()
        return version

    except Exception as e:
        print(f"❌ 获取OVS迁移版本失败: {e}")
        return None


def get_local_migrations():
    """获取本地所有迁移文件信息"""
    print("\n" + "=" * 80)
    print("📂 检查本地迁移文件")
    print("=" * 80)

    project_root = get_project_root()
    migrations_dir = Path(project_root) / 'migrations' / 'versions'

    if not migrations_dir.exists():
        print(f"❌ 迁移目录不存在: {migrations_dir}")
        return []

    # 获取所有迁移文件
    migration_files = list(migrations_dir.glob('*.py'))
    migration_files = [f for f in migration_files if not f.name.startswith('__')]

    migrations = []
    for file_path in migration_files:
        # 提取迁移版本号（文件名前12个字符）
        filename = file_path.name
        if len(filename) >= 12:
            revision = filename[:12]
        else:
            revision = filename.replace('.py', '')

        # 提取迁移描述
        description = filename[13:].replace('.py', '').replace('_', ' ')

        # 获取文件修改时间
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

        migrations.append({
            'revision': revision,
            'description': description,
            'filename': filename,
            'mtime': mtime
        })

    # 按修改时间排序
    migrations.sort(key=lambda x: x['mtime'])

    print(f"✅ 找到 {len(migrations)} 个迁移文件")
    return migrations


def analyze_migration_status(ovs_version, local_migrations):
    """分析迁移状态"""
    print("\n" + "=" * 80)
    print("🔍 迁移状态分析")
    print("=" * 80)

    if not local_migrations:
        print("❌ 没有找到本地迁移文件")
        return

    # 找到OVS当前版本在本地迁移列表中的位置
    ovs_index = None
    if ovs_version:
        for i, migration in enumerate(local_migrations):
            if migration['revision'] == ovs_version:
                ovs_index = i
                break

    if ovs_version is None:
        print("\n⚠️  OVS数据库从未执行过迁移")
        print(f"   需要应用所有 {len(local_migrations)} 个迁移")
        unapplied = local_migrations
    elif ovs_index is None:
        print(f"\n⚠️  OVS当前版本 {ovs_version} 在本地迁移文件中未找到")
        print("   可能的原因:")
        print("   1. OVS应用了本地没有的迁移（已删除的迁移文件）")
        print("   2. 迁移文件重命名或修改")
        print("   3. OVS和本地使用了不同的迁移分支")
        unapplied = local_migrations
    else:
        print(f"\n✅ OVS当前版本: {ovs_version}")
        print(f"   对应迁移: {local_migrations[ovs_index]['description']}")
        print(f"   迁移时间: {local_migrations[ovs_index]['mtime'].strftime('%Y-%m-%d %H:%M:%S')}")

        # 计算未应用的迁移
        unapplied = local_migrations[ovs_index + 1:] if ovs_index < len(local_migrations) - 1 else []

    # 打印未应用的迁移
    if unapplied:
        print(f"\n📋 需要应用的迁移 ({len(unapplied)}个):")
        print("-" * 80)
        for i, migration in enumerate(unapplied, 1):
            print(f"{i}. {migration['revision']} - {migration['description']}")
            print(f"   时间: {migration['mtime'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   文件: {migration['filename']}")
            print()
    else:
        print("\n✅ OVS数据库已应用所有本地迁移，无需更新")

    return unapplied


def generate_migration_plan(unapplied_migrations):
    """生成迁移计划"""
    if not unapplied_migrations:
        return

    print("=" * 80)
    print("💡 建议的迁移方案")
    print("=" * 80)

    # 分析迁移复杂度
    has_merge = any('merge' in m['description'].lower() for m in unapplied_migrations)
    recent_count = len([m for m in unapplied_migrations if (datetime.now() - m['mtime']).days <= 7])

    print(f"\n迁移统计:")
    print(f"   - 总数: {len(unapplied_migrations)} 个")
    print(f"   - 最近7天: {recent_count} 个")
    if has_merge:
        print(f"   ⚠️  包含合并迁移")

    print(f"\n推荐方案:")

    if len(unapplied_migrations) <= 5 and not has_merge:
        print("\n✅ 方案A：Flask-Migrate标准升级（推荐）")
        print("   条件: 迁移数量少且无合并迁移")
        print("   步骤:")
        print("   1. 先备份OVS数据库: python3 simple_ovs_backup.py")
        print("   2. 创建标准迁移工具: standard_migration_upgrade_ovs.py")
        print("   3. 执行标准升级: python3 standard_migration_upgrade_ovs.py")
        print("   4. 验证结果")
    elif has_merge:
        print("\n⚠️  方案B：谨慎处理（包含合并迁移）")
        print("   条件: 检测到迁移合并")
        print("   步骤:")
        print("   1. 先备份OVS数据库")
        print("   2. 检查迁移依赖关系")
        print("   3. 使用Flask-Migrate逐个应用")
        print("   4. 每个迁移后验证")
    else:
        print("\n⚠️  方案C：分批迁移")
        print("   条件: 迁移数量较多")
        print("   步骤:")
        print("   1. 先备份OVS数据库")
        print("   2. 按时间分批应用迁移")
        print("   3. 每批后验证Schema")
        print("   4. 如遇错误及时回滚")

    print("\n通用注意事项:")
    print("   ✓ 执行前务必备份数据库")
    print("   ✓ 在非业务高峰期执行")
    print("   ✓ 准备回滚方案")
    print("   ✓ 记录每步操作日志")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🔍 OVS数据库迁移状态检查")
    print("=" * 80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 获取OVS当前迁移版本
    ovs_version = get_ovs_migration_version()

    # 获取本地迁移文件
    local_migrations = get_local_migrations()

    if not local_migrations:
        print("\n❌ 检查终止：未找到本地迁移文件")
        return

    # 分析迁移状态
    unapplied = analyze_migration_status(ovs_version, local_migrations)

    # 生成迁移计划
    if unapplied:
        generate_migration_plan(unapplied)

    print("\n" + "=" * 80)
    print("✅ 迁移状态检查完成")
    print("=" * 80)
    print(f"\n下一步:")
    if unapplied:
        print("   1. 运行 python3 simple_ovs_backup.py 备份数据库")
        print("   2. 根据上述方案执行迁移")
        print("   3. 运行 python3 scripts/temp/compare_local_ovs_schemas.py 验证结果")
    else:
        print("   无需迁移，OVS数据库已是最新状态")


if __name__ == '__main__':
    main()
