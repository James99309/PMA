#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接查询SP8D数据库：
1. 孙方正属于哪个客户公司
2. 深圳市瑞迪兴智能设计研究院下有哪些联系人
"""
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

# 设置SP8D数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

from app import create_app, db
from app.models.customer import Company, Contact
from app.models.user import User
from sqlalchemy import or_

app = create_app()

with app.app_context():
    print("=" * 80)
    print("SP8D数据库查询：孙方正联系人和瑞迪兴公司信息")
    print("=" * 80)

    # ========================================================================
    # 1. 查找"孙方正"联系人
    # ========================================================================
    print("\n【1】查找'孙方正'联系人")
    print("-" * 80)

    sunfangzheng_contacts = Contact.query.filter(
        Contact.name.ilike('%孙方正%')
    ).all()

    if sunfangzheng_contacts:
        print(f"✅ 找到 {len(sunfangzheng_contacts)} 个'孙方正'联系人:\n")
        for idx, contact in enumerate(sunfangzheng_contacts, 1):
            company = Company.query.get(contact.company_id) if contact.company_id else None
            owner = User.query.get(contact.owner_id) if contact.owner_id else None

            print(f"【联系人 {idx}】")
            print(f"  联系人ID: {contact.id}")
            print(f"  姓名: {contact.name}")
            print(f"  职位: {contact.position if contact.position else '未设置'}")
            print(f"  电话: {contact.phone if contact.phone else '未设置'}")
            print(f"  邮箱: {contact.email if contact.email else '未设置'}")
            print(f"  所属公司ID: {contact.company_id}")
            print(f"  所属公司名称: {company.company_name if company else '❌ 公司不存在或已删除'}")
            if company:
                print(f"  公司是否删除: {'是 ❌' if company.is_deleted else '否 ✅'}")
            print(f"  联系人拥有者ID: {contact.owner_id}")
            print(f"  联系人拥有者: {owner.real_name or owner.username if owner else '无'}")
            print(f"  创建时间: {contact.created_at}")
            print()
    else:
        print("❌ 未找到名为'孙方正'的联系人\n")

    # ========================================================================
    # 2. 查找"深圳市瑞迪兴智能设计研究院"公司
    # ========================================================================
    print("=" * 80)
    print("【2】查找'深圳市瑞迪兴智能设计研究院'公司")
    print("-" * 80)

    ruidixing_companies = Company.query.filter(
        or_(
            Company.company_name.ilike('%深圳市瑞迪兴智能设计研究院%'),
            Company.company_name.ilike('%瑞迪兴%'),
            Company.company_name.ilike('%ruidixing%')
        )
    ).all()

    if ruidixing_companies:
        print(f"✅ 找到 {len(ruidixing_companies)} 个相关公司:\n")
        for idx, company in enumerate(ruidixing_companies, 1):
            owner = User.query.get(company.owner_id) if company.owner_id else None

            print(f"【公司 {idx}】")
            print(f"  公司ID: {company.id}")
            print(f"  公司名称: {company.company_name}")
            print(f"  是否删除: {'是 ❌' if company.is_deleted else '否 ✅'}")
            print(f"  公司类型: {company.company_type}")
            print(f"  公司拥有者ID: {company.owner_id}")
            print(f"  公司拥有者: {owner.real_name or owner.username if owner else '无'}")
            print(f"  创建时间: {company.created_at}")

            # 查询该公司下的所有联系人 (Contact模型没有is_deleted字段)
            contacts = Contact.query.filter_by(
                company_id=company.id
            ).all()

            print(f"\n  该公司下的联系人 ({len(contacts)} 个):")
            if contacts:
                for contact in contacts:
                    contact_owner = User.query.get(contact.owner_id) if contact.owner_id else None
                    sun_marker = "👤 " if '孙方正' in contact.name else "   "
                    print(f"    {sun_marker}ID:{contact.id} | {contact.name} | 拥有者:{contact_owner.real_name or contact_owner.username if contact_owner else '无'}")
            else:
                print(f"    (无联系人)")
            print()
    else:
        print("❌ 未找到'瑞迪兴'相关的公司\n")

    # ========================================================================
    # 3. 查找包含"瑞迪兴"的项目
    # ========================================================================
    print("=" * 80)
    print("【3】查找包含'瑞迪兴'的项目")
    print("-" * 80)

    from app.models.project import Project
    from app.models.project_customer_association import ProjectCustomerAssociation

    projects = Project.query.filter(
        Project.project_name.ilike('%瑞迪兴%')
    ).all()

    if projects:
        print(f"✅ 找到 {len(projects)} 个相关项目:\n")
        for idx, project in enumerate(projects, 1):
            owner = User.query.get(project.owner_id) if project.owner_id else None

            print(f"【项目 {idx}】")
            print(f"  项目ID: {project.id}")
            print(f"  项目名称: {project.project_name}")
            print(f"  项目拥有者: {owner.real_name or owner.username if owner else '无'}")
            print(f"  创建时间: {project.created_at}")

            # 查询该项目关联的客户公司
            associations = ProjectCustomerAssociation.query.filter_by(
                project_id=project.id
            ).all()

            print(f"\n  该项目关联的客户公司 ({len(associations)} 个):")
            if associations:
                for assoc in associations:
                    company = Company.query.get(assoc.company_id)
                    if company:
                        print(f"    公司ID:{company.id} | {company.company_name} | 类型:{assoc.customer_type}")
            else:
                print(f"    ❌ 该项目未关联任何客户公司")
            print()
    else:
        print("❌ 未找到包含'瑞迪兴'的项目\n")

    # ========================================================================
    # 4. 诊断总结
    # ========================================================================
    print("=" * 80)
    print("【4】诊断总结")
    print("=" * 80)

    if sunfangzheng_contacts and ruidixing_companies:
        sun_contact = sunfangzheng_contacts[0]
        sun_company_id = sun_contact.company_id

        # 检查孙方正所属公司是否在瑞迪兴公司列表中
        ruidixing_ids = [c.id for c in ruidixing_companies if not c.is_deleted]

        if sun_company_id in ruidixing_ids:
            print("✅ 孙方正确实属于瑞迪兴相关公司")

            # 检查项目是否关联了该公司
            if projects:
                project = projects[0]
                associations = ProjectCustomerAssociation.query.filter_by(
                    project_id=project.id
                ).all()
                associated_company_ids = [a.company_id for a in associations]

                if sun_company_id in associated_company_ids:
                    print("✅ 该公司已关联到项目")
                    print("\n⚠️  问题可能是：")
                    print("   1. 权限过滤：gxh没有查看该联系人的权限")
                    print("   2. 联系人已删除")
                else:
                    print("❌ 该公司未关联到项目")
                    print("\n🎯 问题根源：孙方正所属公司未通过 project_customer_associations 关联到项目")
                    print("\n解决方案：在项目详情页点击'添加客户'，添加该公司到项目")
        else:
            print("❌ 孙方正不属于瑞迪兴相关公司")
            sun_company = Company.query.get(sun_company_id)
            print(f"\n孙方正实际所属公司：{sun_company.company_name if sun_company else '未知'}")

    print("\n" + "=" * 80)
    print("查询完成")
    print("=" * 80)
