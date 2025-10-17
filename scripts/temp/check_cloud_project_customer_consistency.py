#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端数据库中项目表字段与关联表的一致性，并提供迁移方案"""
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
import json

# 云端数据库连接字符串
CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def check_consistency():
    """检查项目字段与关联表的一致性"""

    print("=" * 100)
    print("云端数据库 - 项目客户字段与关联表一致性检查")
    print("=" * 100)

    # 创建数据库连接
    engine = create_engine(CLOUD_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. 统计项目表中的客户字段数据
        print("\n📊 第一步：统计项目表中的客户字段数据")
        print("-" * 100)

        query = text("""
            SELECT
                COUNT(*) as total_projects,
                COUNT(end_user) as has_end_user,
                COUNT(design_issues) as has_design_issues,
                COUNT(contractor) as has_contractor,
                COUNT(system_integrator) as has_system_integrator,
                COUNT(dealer) as has_dealer,
                COUNT(CASE WHEN end_user IS NOT NULL OR
                            design_issues IS NOT NULL OR
                            contractor IS NOT NULL OR
                            system_integrator IS NOT NULL OR
                            dealer IS NOT NULL THEN 1 END) as has_any_customer_field
            FROM projects
        """)

        result = session.execute(query).fetchone()

        print(f"  项目总数: {result.total_projects}")
        print(f"  有直接用户(end_user)字段: {result.has_end_user}")
        print(f"  有设计院(design_issues)字段: {result.has_design_issues}")
        print(f"  有总承包(contractor)字段: {result.has_contractor}")
        print(f"  有系统集成商(system_integrator)字段: {result.has_system_integrator}")
        print(f"  有经销商(dealer)字段: {result.has_dealer}")
        print(f"  至少有一个客户字段: {result.has_any_customer_field}")

        # 2. 统计关联表数据
        print("\n📊 第二步：统计项目客户关联表数据")
        print("-" * 100)

        query = text("""
            SELECT
                COUNT(*) as total_associations,
                COUNT(DISTINCT project_id) as projects_with_associations,
                COUNT(DISTINCT company_id) as companies_in_associations,
                customer_type,
                COUNT(*) as count_by_type
            FROM project_customer_associations
            GROUP BY customer_type
            ORDER BY count_by_type DESC
        """)

        results = session.execute(query).fetchall()

        total_assoc = session.execute(text("SELECT COUNT(*) FROM project_customer_associations")).scalar()
        distinct_projects = session.execute(text("SELECT COUNT(DISTINCT project_id) FROM project_customer_associations")).scalar()

        print(f"  关联关系总数: {total_assoc}")
        print(f"  有关联的项目数: {distinct_projects}")
        print(f"\n  按客户类型分布:")
        for row in results:
            print(f"    - {row.customer_type}: {row.count_by_type}个关联")

        # 3. 检查不一致的数据
        print("\n🔍 第三步：检查不一致的数据（项目字段有值但关联表无记录）")
        print("-" * 100)

        # 客户类型映射
        field_to_type_map = {
            'end_user': 'end_user',
            'design_issues': 'design_issues',
            'contractor': 'contractor',
            'system_integrator': 'system_integrator',
            'dealer': 'dealer'
        }

        all_missing = []
        field_stats = {}

        for field_name, customer_type in field_to_type_map.items():
            # 查找项目字段有值但关联表中没有对应记录的情况
            query = text(f"""
                SELECT
                    p.id as project_id,
                    p.project_name,
                    p.{field_name} as customer_name,
                    c.id as company_id
                FROM projects p
                LEFT JOIN companies c ON c.company_name = p.{field_name} AND c.is_deleted = false
                WHERE p.{field_name} IS NOT NULL
                  AND p.{field_name} != ''
                  AND NOT EXISTS (
                      SELECT 1
                      FROM project_customer_associations pca
                      WHERE pca.project_id = p.id
                        AND pca.company_id = c.id
                        AND pca.customer_type = :customer_type
                  )
                  AND c.id IS NOT NULL
                LIMIT 100
            """)

            results = session.execute(query, {'customer_type': customer_type}).fetchall()

            # 统计此字段缺失的总数
            count_query = text(f"""
                SELECT COUNT(*)
                FROM projects p
                LEFT JOIN companies c ON c.company_name = p.{field_name} AND c.is_deleted = false
                WHERE p.{field_name} IS NOT NULL
                  AND p.{field_name} != ''
                  AND NOT EXISTS (
                      SELECT 1
                      FROM project_customer_associations pca
                      WHERE pca.project_id = p.id
                        AND pca.company_id = c.id
                        AND pca.customer_type = :customer_type
                  )
                  AND c.id IS NOT NULL
            """)

            total_missing = session.execute(count_query, {'customer_type': customer_type}).scalar()
            field_stats[field_name] = {
                'customer_type': customer_type,
                'total_missing': total_missing,
                'samples': results
            }

        # 显示统计
        total_missing_all = sum(stat['total_missing'] for stat in field_stats.values())

        if total_missing_all > 0:
            print(f"\n⚠️  发现 {total_missing_all} 个不一致的关联需要迁移:")
            print()

            for field_name, stat in field_stats.items():
                if stat['total_missing'] > 0:
                    print(f"  【{field_name}】字段: {stat['total_missing']} 个缺失")
                    if stat['samples']:
                        print(f"    示例 (前5个):")
                        for i, row in enumerate(stat['samples'][:5], 1):
                            print(f"      {i}. 项目: {row.project_name} (ID: {row.project_id})")
                            print(f"         客户: {row.customer_name} (公司ID: {row.company_id})")
                        if stat['total_missing'] > 5:
                            print(f"      ... 还有 {stat['total_missing'] - 5} 个")
                    print()
        else:
            print("\n✅ 所有项目字段数据已正确迁移到关联表！")

        # 4. 检查关联表中存在但项目字段为空的情况
        print("\n🔍 第四步：检查关联表有记录但项目字段为空的情况")
        print("-" * 100)

        reverse_check_query = text("""
            SELECT
                pca.id as association_id,
                pca.project_id,
                p.project_name,
                pca.customer_type,
                c.company_name,
                CASE pca.customer_type
                    WHEN 'end_user' THEN p.end_user
                    WHEN 'design_issues' THEN p.design_issues
                    WHEN 'contractor' THEN p.contractor
                    WHEN 'system_integrator' THEN p.system_integrator
                    WHEN 'dealer' THEN p.dealer
                END as project_field_value
            FROM project_customer_associations pca
            JOIN projects p ON p.id = pca.project_id
            JOIN companies c ON c.id = pca.company_id
            WHERE (
                (pca.customer_type = 'end_user' AND (p.end_user IS NULL OR p.end_user = '')) OR
                (pca.customer_type = 'design_issues' AND (p.design_issues IS NULL OR p.design_issues = '')) OR
                (pca.customer_type = 'contractor' AND (p.contractor IS NULL OR p.contractor = '')) OR
                (pca.customer_type = 'system_integrator' AND (p.system_integrator IS NULL OR p.system_integrator = '')) OR
                (pca.customer_type = 'dealer' AND (p.dealer IS NULL OR p.dealer = ''))
            )
            LIMIT 20
        """)

        reverse_results = session.execute(reverse_check_query).fetchall()

        if reverse_results:
            print(f"\n⚠️  发现 {len(reverse_results)} 个关联表记录但项目字段为空的情况:")
            print("  （这是正常的，因为新功能使用关联表，旧字段可以为空）")
            for i, row in enumerate(reverse_results[:10], 1):
                print(f"    {i}. 项目: {row.project_name}")
                print(f"       关联类型: {row.customer_type}, 客户: {row.company_name}")
                print(f"       项目字段值: {row.project_field_value or '(空)'}")
        else:
            print("\n✅ 未发现此类情况")

        # 5. 生成迁移报告
        print("\n" + "=" * 100)
        print("📋 迁移建议")
        print("=" * 100)

        if total_missing_all > 0:
            print(f"""
建议执行数据迁移：
  1. 需要迁移的关联数: {total_missing_all}
  2. 迁移脚本: migrate_cloud_project_customers.py
  3. 迁移操作:
     - 读取项目表中的客户字段
     - 匹配客户名称到companies表
     - 创建对应的project_customer_associations记录
  4. 迁移后验证:
     - 重新运行本检查脚本
     - 确认不一致数量为0
            """)

            # 保存详细报告
            report = {
                'total_missing': total_missing_all,
                'field_stats': {
                    field: {
                        'customer_type': stat['customer_type'],
                        'total_missing': stat['total_missing']
                    }
                    for field, stat in field_stats.items()
                }
            }

            report_path = os.path.join(get_project_root(), 'scripts/temp/cloud_project_customer_migration_report.json')
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"\n详细报告已保存到: {report_path}")
        else:
            print("\n✅ 数据已完全一致，无需迁移！")

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
    check_consistency()
