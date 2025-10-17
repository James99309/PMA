#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查当前云端数据库中项目客户关联的问题"""
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

def check_current_issues():
    """检查当前数据库中的关联问题"""

    print("=" * 100)
    print("云端数据库 - 项目客户关联问题检查")
    print("=" * 100)

    engine = create_engine(CLOUD_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 问题1: 同一客户名称在同一项目中有多个角色
        print("\n🔍 问题1: 同一客户在同一项目中有多个不同角色")
        print("-" * 100)

        query = text("""
            WITH customer_roles AS (
                SELECT
                    pca.project_id,
                    c.company_name,
                    c.id as company_id,
                    pca.customer_type,
                    pca.id as assoc_id,
                    pca.created_at
                FROM project_customer_associations pca
                JOIN companies c ON c.id = pca.company_id
            )
            SELECT
                cr1.project_id,
                p.project_name,
                cr1.company_name,
                array_agg(DISTINCT cr1.company_id) as company_ids,
                array_agg(cr1.customer_type || '(' || cr1.assoc_id || ')' ORDER BY cr1.created_at) as roles_and_ids,
                COUNT(*) as role_count
            FROM customer_roles cr1
            JOIN projects p ON p.id = cr1.project_id
            GROUP BY cr1.project_id, p.project_name, cr1.company_name
            HAVING COUNT(DISTINCT cr1.customer_type) > 1
            ORDER BY COUNT(*) DESC, cr1.project_id
        """)

        multi_role_issues = session.execute(query).fetchall()

        if multi_role_issues:
            print(f"\n发现 {len(multi_role_issues)} 个项目存在客户多角色问题:\n")

            for i, issue in enumerate(multi_role_issues, 1):
                print(f"【问题 {i}】")
                print(f"  项目: {issue.project_name} (ID: {issue.project_id})")
                print(f"  客户: {issue.company_name}")
                print(f"  公司ID: {issue.company_ids}")
                print(f"  角色数: {issue.role_count}")
                print(f"  角色详情: {issue.roles_and_ids}")
                print()
        else:
            print("✅ 未发现多角色问题")

        # 问题2: 重名公司检查
        print("\n🔍 问题2: 数据库中的重名公司")
        print("-" * 100)

        query = text("""
            SELECT
                company_name,
                array_agg(id ORDER BY id) as company_ids,
                COUNT(*) as duplicate_count
            FROM companies
            WHERE is_deleted = false
            GROUP BY company_name
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 20
        """)

        duplicate_companies = session.execute(query).fetchall()

        if duplicate_companies:
            print(f"\n发现 {len(duplicate_companies)} 个重名公司（显示前20个）:\n")

            for i, dup in enumerate(duplicate_companies, 1):
                print(f"【重名 {i}】")
                print(f"  公司名: {dup.company_name}")
                print(f"  公司ID: {dup.company_ids}")
                print(f"  重复次数: {dup.duplicate_count}")
                print()
        else:
            print("✅ 未发现重名公司")

        # 问题3: 完全重复的关联（相同项目+相同公司+相同类型）
        print("\n🔍 问题3: 完全重复的关联记录")
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
            ORDER BY COUNT(*) DESC
        """)

        exact_duplicates = session.execute(query).fetchall()

        if exact_duplicates:
            print(f"\n发现 {len(exact_duplicates)} 组完全重复的关联:\n")

            for i, dup in enumerate(exact_duplicates, 1):
                # 获取详情
                detail_query = text("""
                    SELECT p.project_name, c.company_name
                    FROM projects p
                    JOIN companies c ON c.id = :company_id
                    WHERE p.id = :project_id
                """)

                result = session.execute(detail_query, {
                    'project_id': dup.project_id,
                    'company_id': dup.company_id
                }).fetchone()

                print(f"【重复 {i}】")
                print(f"  项目: {result.project_name if result else 'Unknown'} (ID: {dup.project_id})")
                print(f"  客户: {result.company_name if result else 'Unknown'} (ID: {dup.company_id})")
                print(f"  类型: {dup.customer_type}")
                print(f"  重复次数: {dup.duplicate_count}")
                print(f"  关联ID: {dup.association_ids}")
                print(f"  创建时间: {dup.created_times}")
                print()
        else:
            print("✅ 未发现完全重复的关联")

        # 统计总结
        print("\n" + "=" * 100)
        print("📊 总结")
        print("=" * 100)

        total_associations = session.execute(text(
            "SELECT COUNT(*) FROM project_customer_associations"
        )).scalar()

        total_projects = session.execute(text(
            "SELECT COUNT(*) FROM projects WHERE is_deleted = false"
        )).scalar()

        print(f"\n  总关联数: {total_associations}")
        print(f"  总项目数: {total_projects}")
        print(f"  多角色问题: {len(multi_role_issues)} 项")
        print(f"  重名公司: {len(duplicate_companies)} 组")
        print(f"  完全重复: {len(exact_duplicates)} 组")

        return {
            'multi_role_issues': multi_role_issues,
            'duplicate_companies': duplicate_companies,
            'exact_duplicates': exact_duplicates
        }

    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()
        engine.dispose()

    print("\n" + "=" * 100)
    print("检查完成")
    print("=" * 100)

if __name__ == '__main__':
    check_current_issues()
