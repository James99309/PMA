#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端数据库中是否存在重复的项目客户关联"""
import sys
import os

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
from sqlalchemy.orm import sessionmaker

# 云端数据库连接字符串
CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def check_duplicates():
    """检查重复的项目客户关联"""

    print("=" * 100)
    print("云端数据库 - 检查重复的项目客户关联")
    print("=" * 100)

    engine = create_engine(CLOUD_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 查找重复的关联（同一个项目、同一个客户、同一个类型出现多次）
        print("\n🔍 查找重复的关联记录...")
        print("-" * 100)

        query = text("""
            SELECT
                project_id,
                company_id,
                customer_type,
                COUNT(*) as duplicate_count,
                array_agg(id ORDER BY created_at) as association_ids,
                array_agg(created_at ORDER BY created_at) as created_times
            FROM project_customer_associations
            GROUP BY project_id, company_id, customer_type
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC, project_id
        """)

        duplicates = session.execute(query).fetchall()

        if not duplicates:
            print("\n✅ 未发现重复记录！")
            return

        print(f"\n⚠️  发现 {len(duplicates)} 组重复记录:\n")

        # 客户类型标签
        type_labels = {
            'end_user': '直接用户',
            'design_issues': '设计院及顾问',
            'contractor': '总承包单位',
            'system_integrator': '系统集成商',
            'dealer': '经销商'
        }

        total_duplicate_records = 0

        for i, dup in enumerate(duplicates, 1):
            # 获取项目和客户名称
            detail_query = text("""
                SELECT
                    p.project_name,
                    c.company_name
                FROM projects p
                JOIN companies c ON c.id = :company_id
                WHERE p.id = :project_id
            """)

            result = session.execute(detail_query, {
                'project_id': dup.project_id,
                'company_id': dup.company_id
            }).fetchone()

            duplicate_count = dup.duplicate_count
            total_duplicate_records += (duplicate_count - 1)  # 减1因为保留一个

            print(f"【重复组 {i}】")
            print(f"  项目: {result.project_name if result else 'Unknown'} (ID: {dup.project_id})")
            print(f"  客户: {result.company_name if result else 'Unknown'} (ID: {dup.company_id})")
            print(f"  类型: {type_labels.get(dup.customer_type, dup.customer_type)}")
            print(f"  重复次数: {duplicate_count} 条")
            print(f"  关联ID: {dup.association_ids}")
            print(f"  创建时间: {dup.created_times}")
            print(f"  建议保留: ID {dup.association_ids[0]} (最早创建)")
            print(f"  建议删除: {dup.association_ids[1:]} ({duplicate_count - 1} 条)")
            print()

        # 统计信息
        print("=" * 100)
        print("📊 重复统计")
        print("=" * 100)
        print(f"  重复组数: {len(duplicates)}")
        print(f"  需要删除的重复记录: {total_duplicate_records} 条")
        print(f"  关联表当前总记录: {session.execute(text('SELECT COUNT(*) FROM project_customer_associations')).scalar()}")
        print(f"  删除后预期记录: {session.execute(text('SELECT COUNT(*) FROM project_customer_associations')).scalar() - total_duplicate_records}")

        # 生成删除脚本
        print("\n" + "=" * 100)
        print("🔧 修复方案")
        print("=" * 100)

        print("\n选项1: SQL删除脚本（保留最早创建的记录）")
        print("-" * 100)
        print("DELETE FROM project_customer_associations WHERE id IN (")

        delete_ids = []
        for dup in duplicates:
            # 保留第一个（最早创建），删除其他
            delete_ids.extend(dup.association_ids[1:])

        for i, aid in enumerate(delete_ids):
            if i < len(delete_ids) - 1:
                print(f"    {aid},")
            else:
                print(f"    {aid}")

        print(");")

        print("\n选项2: 使用Python脚本自动清理")
        print("-" * 100)
        print("运行: python3 scripts/temp/fix_duplicate_associations.py --execute")

        # 分析重复原因
        print("\n" + "=" * 100)
        print("🔍 重复原因分析")
        print("=" * 100)

        # 检查是否是迁移导致的
        migration_related = 0
        for dup in duplicates:
            for created_time in dup.created_times:
                if '2025-10-15' in str(created_time):
                    migration_related += 1
                    break

        print(f"  可能由迁移导致的重复组: {migration_related}/{len(duplicates)}")

        if migration_related > 0:
            print("\n⚠️  分析: 迁移脚本在创建新记录前检查了是否存在，但可能存在以下情况:")
            print("  1. 迁移前已存在该关联（通过项目详情页面手动添加）")
            print("  2. 项目表字段也有相同客户名称")
            print("  3. 迁移脚本误判为需要创建")
            print("\n建议: 清理重复记录后，项目表字段可以考虑逐步废弃")

    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        engine.dispose()

    print("\n" + "=" * 100)
    print("检查完成")
    print("=" * 100)

if __name__ == '__main__':
    check_duplicates()
