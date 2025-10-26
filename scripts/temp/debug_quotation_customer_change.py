#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调查报价单 QU202405-022 的客户关联变更问题"""
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

sys.path.insert(0, get_project_root())

from app import create_app, db
from app.models import Quotation, Company, Project, Contact, User
from sqlalchemy import text
from datetime import datetime

def investigate_quotation_customer():
    """调查报价单客户关联变更"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
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
        print(f"  创建人: {quotation.created_by.username if quotation.created_by else 'N/A'}")

        # 2. 当前关联的客户
        print(f"\n🏢 当前关联客户:")
        if quotation.customer_id:
            company = Company.query.get(quotation.customer_id)
            if company:
                print(f"  客户ID: {company.id}")
                print(f"  客户名称: {company.name}")
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
                print(f"  项目名称: {project.name}")
                print(f"  项目客户ID: {project.company_id}")
                if project.company:
                    print(f"  项目客户名称: {project.company.name}")
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
                    print(f"  联系人所属客户: {contact.company.name}")
        else:
            print(f"  ⚠️ 无关联联系人")

        # 5. 检查是否有审计日志（如果表存在）
        print(f"\n📝 检查审计日志:")
        try:
            # 检查是否有 audit_log 表
            result = db.session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'audit_log'
            """))

            if result.fetchone():
                # 查询与此报价单相关的审计日志
                logs = db.session.execute(text("""
                    SELECT
                        created_at,
                        user_id,
                        action,
                        changes
                    FROM audit_log
                    WHERE table_name = 'quotation'
                    AND record_id = :quotation_id
                    ORDER BY created_at DESC
                    LIMIT 20
                """), {'quotation_id': quotation.id}).fetchall()

                if logs:
                    print(f"  找到 {len(logs)} 条审计日志:")
                    for log in logs:
                        print(f"\n  时间: {log[0]}")
                        print(f"  操作: {log[2]}")
                        if log[3]:
                            print(f"  变更: {log[3][:200]}...")
                else:
                    print("  ⚠️ 未找到相关审计日志")
            else:
                print("  ⚠️ 系统中无审计日志表")
        except Exception as e:
            print(f"  ⚠️ 查询审计日志失败: {str(e)}")

        # 6. 检查可能的数据合并记录
        print(f"\n🔄 检查智能合并记录:")
        try:
            # 检查是否有 merge_log 或类似的表
            result = db.session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE '%merge%'
            """))

            merge_tables = result.fetchall()
            if merge_tables:
                print(f"  找到合并相关表: {[t[0] for t in merge_tables]}")

                # 查询与当前客户相关的合并记录
                if quotation.customer_id:
                    for table in merge_tables:
                        table_name = table[0]
                        try:
                            merge_logs = db.session.execute(text(f"""
                                SELECT * FROM {table_name}
                                WHERE target_id = :customer_id
                                   OR source_ids::text LIKE '%' || :customer_id || '%'
                                ORDER BY created_at DESC
                                LIMIT 5
                            """), {'customer_id': quotation.customer_id}).fetchall()

                            if merge_logs:
                                print(f"\n  {table_name} 中找到相关记录:")
                                for log in merge_logs:
                                    print(f"    {log}")
                        except Exception as e:
                            print(f"  查询 {table_name} 失败: {str(e)}")
            else:
                print("  ⚠️ 未找到合并相关表")
        except Exception as e:
            print(f"  ⚠️ 查询合并记录失败: {str(e)}")

        # 7. 查询所有名称包含 "SK海力士" 的客户
        print(f"\n🔍 查询所有 SK海力士 相关客户:")
        sk_companies = Company.query.filter(
            Company.name.ilike('%SK海力士%'),
            Company.is_deleted == False
        ).all()

        print(f"  找到 {len(sk_companies)} 个相关客户:")
        for company in sk_companies:
            print(f"\n  客户ID: {company.id}")
            print(f"  客户名称: {company.name}")
            print(f"  创建时间: {company.created_at}")
            print(f"  更新时间: {company.updated_at}")

            # 查询每个客户的报价单数量
            quotation_count = Quotation.query.filter_by(
                company_id=company.id,
                is_deleted=False
            ).count()
            print(f"  关联报价单数: {quotation_count}")

        # 8. 检查归属关系是否影响
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
                    print(f"\n  父公司: {parent.name if parent else 'N/A'} (ID: {aff.parent_company_id})")
                    print(f"  子公司: {child.name if child else 'N/A'} (ID: {aff.child_company_id})")
                    print(f"  创建时间: {aff.created_at}")
            else:
                print("  ⚠️ 无归属关系")

        print("\n" + "=" * 80)
        print("调查完成")
        print("=" * 80)

if __name__ == '__main__':
    investigate_quotation_customer()
