#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调查云端报价单 QU202405-022 的客户关联变更问题"""
import sys, os

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)

# 加载云端数据库配置
from dotenv import load_dotenv
dotenv_path = os.path.join(project_root, '.env.sp8d.backup')
if os.path.exists(dotenv_path):
    print(f"✅ 加载云端数据库配置: {dotenv_path}")
    load_dotenv(dotenv_path, override=True)
else:
    print(f"⚠️ 未找到云端配置文件: {dotenv_path}")
    sys.exit(1)

from app import create_app, db
from app.models import Quotation, Company, Project, Contact, User
from sqlalchemy import text
from datetime import datetime

def investigate_quotation_customer():
    """调查报价单客户关联变更"""
    app = create_app()

    with app.app_context():
        # 验证数据库连接
        print("=" * 80)
        print("验证数据库连接")
        print("=" * 80)
        try:
            result = db.session.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"✅ 已连接到数据库: {db_name}")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return

        print("\n" + "=" * 80)
        print("报价单 QU202405-022 客户关联调查")
        print("=" * 80)

        # 1. 查询报价单基本信息
        quotation = Quotation.query.filter_by(
            quotation_number='QU202405-022'
        ).first()

        if not quotation:
            print("\n❌ 未找到报价单 QU202405-022")
            return

        print(f"\n📋 报价单基本信息:")
        print(f"  ID: {quotation.id}")
        print(f"  报价单号: {quotation.quotation_number}")
        print(f"  创建时间: {quotation.created_at}")
        print(f"  更新时间: {quotation.updated_at}")
        print(f"  创建人: {quotation.owner.username if quotation.owner else 'N/A'}")

        # 2. 当前关联的客户
        print(f"\n🏢 当前关联客户:")
        if quotation.customer_id:
            company = Company.query.get(quotation.customer_id)
            if company:
                print(f"  客户ID: {company.id}")
                print(f"  客户名称: {company.company_name}")
                print(f"  客户创建时间: {company.created_at}")
                print(f"  客户更新时间: {company.updated_at}")
                print(f"  客户所有者: {company.owner.username if company.owner else 'N/A'}")
        else:
            print(f"  ⚠️ 无关联客户")

        # 3. 关联的项目
        print(f"\n📊 关联项目:")
        if quotation.project_id:
            project = Project.query.get(quotation.project_id)
            if project:
                print(f"  项目ID: {project.id}")
                print(f"  项目名称: {project.project_name}")
                print(f"  项目创建时间: {project.created_at if hasattr(project, 'created_at') else 'N/A'}")
                print(f"  项目更新时间: {project.updated_at if hasattr(project, 'updated_at') else 'N/A'}")

                # 查询项目关联的客户（通过关联表）
                try:
                    from sqlalchemy import text as sql_text
                    result = db.session.execute(sql_text("""
                        SELECT company_id FROM project_customer_associations
                        WHERE project_id = :project_id
                    """), {"project_id": project.id})
                    company_ids = [row[0] for row in result.fetchall()]
                    if company_ids:
                        print(f"  项目关联的客户IDs: {company_ids}")
                        if quotation.customer_id not in company_ids:
                            print(f"  ⚠️ 报价单客户ID {quotation.customer_id} 不在项目关联客户列表中")
                except Exception as e:
                    print(f"  ⚠️ 查询项目客户关联失败: {e}")
        else:
            print(f"  ⚠️ 无关联项目")

        # 4. 关联的联系人
        print(f"\n👤 关联联系人:")
        if quotation.contact_id:
            contact = Contact.query.get(quotation.contact_id)
            if contact:
                print(f"  联系人ID: {contact.id}")
                print(f"  联系人姓名: {contact.name}")
                print(f"  联系人所属客户ID: {contact.company_id}")
                if contact.company:
                    print(f"  联系人所属客户: {contact.company.company_name}")
                    print(f"  ⚠️ 注意: 报价单客户ID={quotation.customer_id}, 联系人客户ID={contact.company_id}")
                    if quotation.customer_id != contact.company_id:
                        print(f"  ❌ 报价单客户与联系人客户不一致!")
        else:
            print(f"  ⚠️ 无关联联系人")

        # 5. 查询所有名称包含 "SK海力士" 的客户
        print(f"\n🔍 查询所有 SK海力士 相关客户:")
        sk_companies = Company.query.filter(
            Company.company_name.ilike('%SK海力士%'),
            Company.is_deleted == False
        ).all()

        print(f"  找到 {len(sk_companies)} 个相关客户:")
        for company in sk_companies:
            print(f"\n  [客户 {company.id}]")
            print(f"    名称: {company.company_name}")
            print(f"    创建时间: {company.created_at}")
            print(f"    更新时间: {company.updated_at}")
            print(f"    所有者: {company.owner.username if company.owner else 'N/A'}")

            # 查询每个客户的报价单数量
            quotation_count = Quotation.query.filter_by(
                customer_id=company.id
            ).count()
            print(f"    关联报价单数: {quotation_count}")

            # 如果是当前报价单的客户，标记出来
            if company.id == quotation.customer_id:
                print(f"    ✅ 这是当前报价单的关联客户")

        # 6. 检查客户合并记录
        print(f"\n🔄 检查客户合并记录:")
        if quotation.customer_id:
            # 查询与当前客户相关的合并记录
            merge_query = text("""
                SELECT
                    id,
                    target_id,
                    source_ids,
                    merged_by,
                    created_at,
                    details
                FROM company_merge_log
                WHERE target_id = :customer_id
                   OR source_ids::jsonb @> :customer_id_json
                ORDER BY created_at DESC
                LIMIT 10
            """)

            try:
                import json
                customer_id_json = json.dumps(quotation.customer_id)
                merge_logs = db.session.execute(
                    merge_query,
                    {'customer_id': quotation.customer_id, 'customer_id_json': customer_id_json}
                ).fetchall()

                if merge_logs:
                    print(f"  找到 {len(merge_logs)} 条合并记录:")
                    for log in merge_logs:
                        print(f"\n  [合并记录 {log[0]}]")
                        print(f"    目标客户ID: {log[1]}")
                        print(f"    源客户IDs: {log[2]}")
                        print(f"    合并人ID: {log[3]}")
                        print(f"    合并时间: {log[4]}")
                        if log[5]:
                            details = json.loads(log[5]) if isinstance(log[5], str) else log[5]
                            print(f"    详情: {details}")

                        # 检查这次合并是否影响了我们的报价单
                        target_company = Company.query.get(log[1])
                        if target_company:
                            print(f"    目标客户名称: {target_company.company_name}")
                else:
                    print("  ⚠️ 未找到相关合并记录")
            except Exception as e:
                print(f"  ⚠️ 查询合并记录失败: {str(e)}")

        # 7. 检查归属关系
        print(f"\n🔗 检查归属关系:")
        if quotation.customer:
            from app.models import Affiliation
            affiliations = Affiliation.query.filter(
                (Affiliation.parent_company_id == quotation.customer_id) |
                (Affiliation.child_company_id == quotation.customer_id)
            ).all()

            if affiliations:
                print(f"  找到 {len(affiliations)} 条归属关系:")
                for aff in affiliations:
                    parent = Company.query.get(aff.parent_company_id)
                    child = Company.query.get(aff.child_company_id)
                    print(f"\n  父公司: {parent.company_name if parent else 'N/A'} (ID: {aff.parent_company_id})")
                    print(f"  子公司: {child.company_name if child else 'N/A'} (ID: {aff.child_company_id})")
                    print(f"  创建时间: {aff.created_at}")
            else:
                print("  ⚠️ 无归属关系")

        # 8. 检查报价单的修改历史（通过updated_at判断）
        print(f"\n📝 报价单修改时间线:")
        print(f"  创建时间: {quotation.created_at}")
        print(f"  最后更新: {quotation.updated_at}")

        time_diff = quotation.updated_at - quotation.created_at
        if time_diff.total_seconds() > 60:  # 如果更新时间比创建时间晚超过1分钟
            print(f"  ⚠️ 报价单在创建后被修改过 (时差: {time_diff})")

        print("\n" + "=" * 80)
        print("调查完成")
        print("=" * 80)

if __name__ == '__main__':
    investigate_quotation_customer()
