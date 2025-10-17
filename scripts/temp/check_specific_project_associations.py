#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查特定项目的客户关联详情"""
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

def check_project_associations(project_id=None, project_name_like=None):
    """检查特定项目的客户关联"""

    print("=" * 100)
    print("云端数据库 - 检查特定项目的客户关联")
    print("=" * 100)

    engine = create_engine(CLOUD_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    type_labels = {
        'end_user': '直接用户',
        'design_issues': '设计院及顾问',
        'contractor': '总承包单位',
        'system_integrator': '系统集成商',
        'dealer': '经销商'
    }

    try:
        # 如果没有指定项目ID，列出最近的项目
        if not project_id and not project_name_like:
            print("\n📋 列出最近创建的10个有关联的项目:")
            print("-" * 100)

            query = text("""
                SELECT
                    p.id,
                    p.project_name,
                    p.created_at,
                    COUNT(pca.id) as association_count
                FROM projects p
                JOIN project_customer_associations pca ON pca.project_id = p.id
                GROUP BY p.id, p.project_name, p.created_at
                ORDER BY p.created_at DESC
                LIMIT 10
            """)

            projects = session.execute(query).fetchall()

            for i, proj in enumerate(projects, 1):
                print(f"{i}. [{proj.id}] {proj.project_name} ({proj.association_count}个关联)")

            print("\n使用方式:")
            print("  python3 scripts/temp/check_specific_project_associations.py <project_id>")
            print("  或")
            print("  python3 scripts/temp/check_specific_project_associations.py --name '项目名称'")
            return

        # 查找项目
        if project_id:
            query = text("SELECT id, project_name FROM projects WHERE id = :pid")
            project = session.execute(query, {'pid': project_id}).fetchone()
        else:
            query = text("SELECT id, project_name FROM projects WHERE project_name ILIKE :name LIMIT 1")
            project = session.execute(query, {'name': f'%{project_name_like}%'}).fetchone()

        if not project:
            print(f"\n❌ 未找到项目 (ID={project_id}, 名称包含='{project_name_like}')")
            return

        print(f"\n📊 项目: {project.project_name} (ID: {project.id})")
        print("=" * 100)

        # 查询关联表中的客户
        print("\n1️⃣  关联表中的客户关联:")
        print("-" * 100)

        query = text("""
            SELECT
                pca.id,
                pca.customer_type,
                c.id as company_id,
                c.company_name,
                pca.created_at,
                pca.created_by
            FROM project_customer_associations pca
            JOIN companies c ON c.id = pca.company_id
            WHERE pca.project_id = :pid
            ORDER BY pca.customer_type, c.company_name
        """)

        associations = session.execute(query, {'pid': project.id}).fetchall()

        if associations:
            for i, assoc in enumerate(associations, 1):
                print(f"  [{i}] {type_labels.get(assoc.customer_type, assoc.customer_type)}")
                print(f"      客户: {assoc.company_name} (ID: {assoc.company_id})")
                print(f"      关联ID: {assoc.id}")
                print(f"      创建时间: {assoc.created_at}")
                print(f"      创建人ID: {assoc.created_by}")
                print()
        else:
            print("  无关联记录")

        # 查询项目表中的客户字段
        print("\n2️⃣  项目表字段中的客户信息:")
        print("-" * 100)

        query = text("""
            SELECT
                end_user,
                design_issues,
                contractor,
                system_integrator,
                dealer
            FROM projects
            WHERE id = :pid
        """)

        fields = session.execute(query, {'pid': project.id}).fetchone()

        field_map = {
            'end_user': '直接用户',
            'design_issues': '设计院及顾问',
            'contractor': '总承包单位',
            'system_integrator': '系统集成商',
            'dealer': '经销商'
        }

        has_fields = False
        for field, label in field_map.items():
            value = getattr(fields, field)
            if value:
                print(f"  {label}: {value}")
                has_fields = True

        if not has_fields:
            print("  无客户字段")

        # 对比分析
        print("\n3️⃣  对比分析:")
        print("-" * 100)

        # 统计每种类型的数量
        from collections import defaultdict
        assoc_by_type = defaultdict(list)

        for assoc in associations:
            assoc_by_type[assoc.customer_type].append(assoc.company_name)

        # 检查是否有重复
        for ctype, companies in assoc_by_type.items():
            if len(companies) > len(set(companies)):
                print(f"  ⚠️  {type_labels.get(ctype, ctype)}: 发现重复客户!")
                from collections import Counter
                counts = Counter(companies)
                for company, count in counts.items():
                    if count > 1:
                        print(f"      - {company} 出现 {count} 次")
            else:
                print(f"  ✅ {type_labels.get(ctype, ctype)}: 无重复 ({len(companies)}个客户)")

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
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--name' and len(sys.argv) > 2:
            check_project_associations(project_name_like=sys.argv[2])
        else:
            try:
                pid = int(sys.argv[1])
                check_project_associations(project_id=pid)
            except ValueError:
                print("错误: 项目ID必须是数字")
    else:
        check_project_associations()
