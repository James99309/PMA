#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 gxh 账户的"深圳市瑞迪兴智能设计研究院"项目的客户联系人情况
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

from app import create_app, db
from app.models.user import User
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.action import Action
from app.models.project_customer_association import ProjectCustomerAssociation

app = create_app()

with app.app_context():
    print("=" * 80)
    print("检查 GXH 账户的深圳瑞迪兴项目")
    print("=" * 80)

    # 1. 查询 gxh 用户
    gxh = User.query.filter_by(username='gxh').first()
    if not gxh:
        print("❌ 未找到 gxh 账户")
        sys.exit(1)

    print(f"\n✅ 找到用户: {gxh.username} ({gxh.real_name}) - {gxh.role}")

    # 2. 查询包含"瑞迪兴"的项目
    print("\n" + "=" * 80)
    print("查找包含'瑞迪兴'的项目")
    print("=" * 80)

    projects = Project.query.filter(
        Project.project_name.ilike('%瑞迪兴%')
    ).all()

    if not projects:
        print("❌ 未找到包含'瑞迪兴'的项目")
        sys.exit(1)

    print(f"\n找到 {len(projects)} 个相关项目:")
    for proj in projects:
        owner = User.query.get(proj.owner_id) if proj.owner_id else None
        owner_name = f"{owner.real_name or owner.username}" if owner else "无"
        print(f"\n项目ID: {proj.id}")
        print(f"  - 项目名称: {proj.project_name}")
        print(f"  - 拥有者: {owner_name}")
        print(f"  - 创建时间: {proj.created_at}")

    # 3. 重点检查 gxh 的项目或所有相关项目
    target_project = None
    for proj in projects:
        if proj.owner_id == gxh.id or '深圳市瑞迪兴智能设计研究院' in proj.project_name:
            target_project = proj
            break

    if not target_project:
        print("\n⚠️  未找到 gxh 拥有的或完全匹配的瑞迪兴项目，使用第一个找到的项目")
        target_project = projects[0]

    print("\n" + "=" * 80)
    print(f"检查项目: {target_project.project_name} (ID: {target_project.id})")
    print("=" * 80)

    # 4. 检查项目关联的客户
    print("\n📋 项目关联的客户 (通过 ProjectCustomerAssociation):")
    print("-" * 80)

    associations = ProjectCustomerAssociation.query.filter_by(
        project_id=target_project.id
    ).all()

    if associations:
        print(f"找到 {len(associations)} 个客户关联:")
        for assoc in associations:
            company = Company.query.get(assoc.company_id)
            if company:
                print(f"\n✅ 客户: {company.company_name} (ID: {company.id})")
                print(f"   - 拥有者: {User.query.get(company.owner_id).real_name if company.owner_id else '无'}")
                print(f"   - 是否主客户: {'是' if assoc.is_primary else '否'}")

                # 检查该客户下的所有联系人
                contacts = Contact.query.filter_by(
                    company_id=company.id,
                    is_deleted=False
                ).all()

                print(f"   - 联系人数量: {len(contacts)}")
                if contacts:
                    print(f"   - 联系人列表:")
                    for contact in contacts:
                        owner = User.query.get(contact.owner_id) if contact.owner_id else None
                        owner_name = f"{owner.real_name or owner.username}" if owner else "无"
                        sun_flag = "👤" if contact.name == "孙方正" else "  "
                        print(f"      {sun_flag} {contact.name} - 拥有者: {owner_name} (联系人ID: {contact.id})")
    else:
        print("❌ 该项目没有关联的客户")

    # 5. 检查项目的直接客户字段（旧版本可能使用）
    if hasattr(target_project, 'customer_name') and target_project.customer_name:
        print(f"\n📝 项目直接客户字段: {target_project.customer_name}")

    # 6. 检查行动记录中提到"孙方正"的记录
    print("\n" + "=" * 80)
    print("检查行动记录中的'孙方正'")
    print("=" * 80)

    actions_with_sun = Action.query.filter(
        Action.project_id == target_project.id,
        Action.communication.ilike('%孙方正%')
    ).all()

    if actions_with_sun:
        print(f"\n找到 {len(actions_with_sun)} 条提到'孙方正'的行动记录:")
        for action in actions_with_sun:
            print(f"\n行动ID: {action.id}")
            print(f"  - 日期: {action.date}")
            print(f"  - 拥有者: {User.query.get(action.owner_id).real_name if action.owner_id else '无'}")
            print(f"  - 关联联系人ID: {action.contact_id}")

            if action.contact_id:
                contact = Contact.query.get(action.contact_id)
                if contact:
                    print(f"  - 关联联系人: {contact.name}")
                    print(f"  - 联系人所属公司ID: {contact.company_id}")
                    if contact.company_id:
                        company = Company.query.get(contact.company_id)
                        if company:
                            print(f"  - 联系人所属公司: {company.company_name}")
                else:
                    print(f"  - ⚠️  联系人ID {action.contact_id} 不存在或已删除")

            print(f"  - 沟通内容: {action.communication[:100]}..." if len(action.communication) > 100 else f"  - 沟通内容: {action.communication}")

    # 7. 直接查询名为"孙方正"的联系人
    print("\n" + "=" * 80)
    print("直接查询'孙方正'联系人")
    print("=" * 80)

    sun_contacts = Contact.query.filter(
        Contact.name.ilike('%孙方正%'),
        Contact.is_deleted == False
    ).all()

    if sun_contacts:
        print(f"\n找到 {len(sun_contacts)} 个'孙方正'联系人:")
        for contact in sun_contacts:
            owner = User.query.get(contact.owner_id) if contact.owner_id else None
            owner_name = f"{owner.real_name or owner.username}" if owner else "无"
            company = Company.query.get(contact.company_id) if contact.company_id else None
            company_name = company.company_name if company else "无"

            print(f"\n联系人ID: {contact.id}")
            print(f"  - 姓名: {contact.name}")
            print(f"  - 所属公司: {company_name} (ID: {contact.company_id})")
            print(f"  - 拥有者: {owner_name} (ID: {contact.owner_id})")
            print(f"  - 创建时间: {contact.created_at}")

            # 检查该联系人是否在项目关联的客户下
            if company and company.id in [assoc.company_id for assoc in associations]:
                print(f"  - ✅ 该联系人所属公司已关联到项目")
            else:
                print(f"  - ❌ 该联系人所属公司未关联到项目")
    else:
        print("\n❌ 未找到'孙方正'联系人")

    # 8. 检查 gxh 的权限
    print("\n" + "=" * 80)
    print("检查 gxh 的客户权限")
    print("=" * 80)

    print(f"\ngxh 的客户权限级别: {gxh.get_permission_level('customer')}")
    print(f"gxh 是否有客户查看权限: {gxh.has_permission('customer', 'view')}")

    # 9. 总结
    print("\n" + "=" * 80)
    print("问题诊断总结")
    print("=" * 80)

    if sun_contacts:
        sun_contact = sun_contacts[0]
        if sun_contact.company_id in [assoc.company_id for assoc in associations]:
            print("\n✅ 孙方正联系人存在，且所属公司已关联到项目")
            print("   可能的问题:")
            print("   1. 前端显示问题")
            print("   2. 权限过滤问题（检查 gxh 是否有查看该联系人的权限）")
            print("   3. 联系人的 owner_id 与 gxh 无关联")
        else:
            print("\n❌ 孙方正联系人存在，但所属公司未关联到项目")
            print("   需要将孙方正所属的公司关联到项目")
    else:
        print("\n❌ 孙方正联系人不存在")
        print("   需要创建该联系人记录")

    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)
