#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将云端数据库中项目表的客户字段迁移到关联表"""
import sys
import os

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
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# 云端数据库连接字符串
CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def migrate_project_customers(dry_run=True):
    """迁移项目客户数据到关联表

    Args:
        dry_run: 如果为True，只显示迁移计划不实际执行
    """

    print("=" * 100)
    print("云端数据库 - 项目客户字段迁移到关联表")
    print("=" * 100)
    print(f"\n模式: {'🔍 预演模式 (DRY RUN)' if dry_run else '🚀 执行模式 (EXECUTE)'}")
    print("-" * 100)

    # 创建数据库连接
    engine = create_engine(CLOUD_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 客户类型映射
    field_to_type_map = {
        'end_user': 'end_user',
        'design_issues': 'design_issues',
        'contractor': 'contractor',
        'system_integrator': 'system_integrator',
        'dealer': 'dealer'
    }

    # 中文标签
    type_labels = {
        'end_user': '直接用户',
        'design_issues': '设计院及顾问',
        'contractor': '总承包单位',
        'system_integrator': '系统集成商',
        'dealer': '经销商'
    }

    migration_stats = {
        'total_processed': 0,
        'total_created': 0,
        'total_skipped': 0,
        'total_errors': 0,
        'by_type': {},
        'details': []
    }

    try:
        for field_name, customer_type in field_to_type_map.items():
            print(f"\n处理字段: {field_name} ({type_labels[customer_type]})")
            print("-" * 100)

            # 查找需要迁移的数据
            query = text(f"""
                SELECT
                    p.id as project_id,
                    p.project_name,
                    p.{field_name} as customer_name,
                    p.created_by,
                    c.id as company_id,
                    c.company_name
                FROM projects p
                LEFT JOIN companies c ON c.company_name = p.{field_name} AND c.is_deleted = false
                WHERE p.{field_name} IS NOT NULL
                  AND p.{field_name} != ''
                  AND c.id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1
                      FROM project_customer_associations pca
                      WHERE pca.project_id = p.id
                        AND pca.company_id = c.id
                        AND pca.customer_type = :customer_type
                  )
                ORDER BY p.id
            """)

            results = session.execute(query, {'customer_type': customer_type}).fetchall()

            migration_stats['by_type'][customer_type] = {
                'total': len(results),
                'created': 0,
                'skipped': 0,
                'errors': 0
            }

            if not results:
                print(f"  ✅ 无需迁移的数据")
                continue

            print(f"  发现 {len(results)} 条需要迁移的关联")

            for i, row in enumerate(results, 1):
                migration_stats['total_processed'] += 1

                if dry_run:
                    # 预演模式：只显示将要创建的关联
                    if i <= 10:  # 只显示前10个
                        print(f"    [{i}] 将创建关联:")
                        print(f"        项目: {row.project_name} (ID: {row.project_id})")
                        print(f"        客户: {row.company_name} (ID: {row.company_id})")
                        print(f"        类型: {type_labels[customer_type]}")
                    elif i == 11:
                        print(f"    ... 还有 {len(results) - 10} 条将被创建")

                    migration_stats['by_type'][customer_type]['created'] += 1
                    migration_stats['total_created'] += 1

                    # 记录详细信息用于报告
                    migration_stats['details'].append({
                        'project_id': row.project_id,
                        'project_name': row.project_name,
                        'company_id': row.company_id,
                        'company_name': row.company_name,
                        'customer_type': customer_type
                    })
                else:
                    # 执行模式：实际创建关联
                    try:
                        # 再次检查是否已存在（防止并发创建）
                        check_query = text("""
                            SELECT id FROM project_customer_associations
                            WHERE project_id = :project_id
                              AND company_id = :company_id
                              AND customer_type = :customer_type
                        """)

                        existing = session.execute(check_query, {
                            'project_id': row.project_id,
                            'company_id': row.company_id,
                            'customer_type': customer_type
                        }).fetchone()

                        if existing:
                            migration_stats['by_type'][customer_type]['skipped'] += 1
                            migration_stats['total_skipped'] += 1
                            continue

                        # 创建关联记录
                        insert_query = text("""
                            INSERT INTO project_customer_associations
                                (project_id, company_id, customer_type, created_by, created_at, updated_at)
                            VALUES
                                (:project_id, :company_id, :customer_type, :created_by, :created_at, :updated_at)
                        """)

                        session.execute(insert_query, {
                            'project_id': row.project_id,
                            'company_id': row.company_id,
                            'customer_type': customer_type,
                            'created_by': row.created_by,
                            'created_at': datetime.now(),
                            'updated_at': datetime.now()
                        })

                        migration_stats['by_type'][customer_type]['created'] += 1
                        migration_stats['total_created'] += 1

                        if i <= 10:
                            print(f"    ✅ [{i}] 已创建关联:")
                            print(f"        项目: {row.project_name} (ID: {row.project_id})")
                            print(f"        客户: {row.company_name} (ID: {row.company_id})")
                        elif i == 11:
                            print(f"    ... 继续创建剩余 {len(results) - 10} 条 ...")

                    except Exception as e:
                        migration_stats['by_type'][customer_type]['errors'] += 1
                        migration_stats['total_errors'] += 1
                        print(f"    ❌ [{i}] 创建失败: {e}")
                        print(f"        项目ID: {row.project_id}, 客户ID: {row.company_id}")

        # 如果是执行模式，提交事务
        if not dry_run:
            print("\n" + "-" * 100)
            print("提交事务...")
            session.commit()
            print("✅ 事务已提交")

        # 打印统计报告
        print("\n" + "=" * 100)
        print("📊 迁移统计报告")
        print("=" * 100)

        print(f"\n总体统计:")
        print(f"  处理总数: {migration_stats['total_processed']}")
        print(f"  {'计划创建' if dry_run else '成功创建'}: {migration_stats['total_created']}")
        print(f"  跳过: {migration_stats['total_skipped']}")
        print(f"  错误: {migration_stats['total_errors']}")

        print(f"\n按类型统计:")
        for customer_type, stats in migration_stats['by_type'].items():
            if stats['total'] > 0:
                print(f"  【{type_labels[customer_type]}】:")
                print(f"    需要迁移: {stats['total']}")
                print(f"    {'计划创建' if dry_run else '成功创建'}: {stats['created']}")
                if stats['skipped'] > 0:
                    print(f"    跳过: {stats['skipped']}")
                if stats['errors'] > 0:
                    print(f"    错误: {stats['errors']}")

        # 保存迁移报告
        report_path = os.path.join(get_project_root(), 'scripts/temp/cloud_project_customer_migration_result.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'dry_run': dry_run,
                'stats': {
                    'total_processed': migration_stats['total_processed'],
                    'total_created': migration_stats['total_created'],
                    'total_skipped': migration_stats['total_skipped'],
                    'total_errors': migration_stats['total_errors'],
                    'by_type': migration_stats['by_type']
                },
                'sample_details': migration_stats['details'][:50] if dry_run else []  # 只保存前50个样本
            }, f, indent=2, ensure_ascii=False)

        print(f"\n详细报告已保存到: {report_path}")

        if dry_run:
            print("\n" + "=" * 100)
            print("⚠️  这是预演模式，没有实际修改数据")
            print("要执行实际迁移，请运行:")
            print("  python3 scripts/temp/migrate_cloud_project_customers.py --execute")
            print("=" * 100)
        else:
            print("\n" + "=" * 100)
            print("✅ 迁移已完成！")
            print("\n建议验证步骤:")
            print("  1. 运行一致性检查: python3 scripts/temp/check_cloud_project_customer_consistency.py")
            print("  2. 检查客户详情页面是否正常显示关联项目")
            print("  3. 检查项目详情页面是否正常显示关联客户")
            print("=" * 100)

        return migration_stats['total_errors'] == 0

    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        if not dry_run:
            print("\n回滚事务...")
            session.rollback()
            print("✅ 事务已回滚")
        return False
    finally:
        session.close()
        engine.dispose()

    print("\n" + "=" * 100)
    print("迁移流程结束")
    print("=" * 100)

if __name__ == '__main__':
    import sys

    # 检查是否有 --execute 参数
    dry_run = '--execute' not in sys.argv
    force = '--force' in sys.argv

    if not dry_run and not force:
        print("\n" + "!" * 100)
        print("⚠️  警告：即将执行实际迁移操作！")
        print("!" * 100)
        print("\n请确认:")
        print("  1. 已完成数据库备份")
        print("  2. 已在预演模式下验证迁移计划")
        print("  3. 理解此操作将创建新的关联表记录")
        print()
        response = input("确认要执行迁移吗？(输入 'YES' 确认): ")
        if response != 'YES':
            print("\n已取消迁移")
            sys.exit(0)
    elif not dry_run and force:
        print("\n" + "!" * 100)
        print("🚀 使用 --force 参数，跳过确认步骤")
        print("!" * 100)

    success = migrate_project_customers(dry_run=dry_run)
    sys.exit(0 if success else 1)
