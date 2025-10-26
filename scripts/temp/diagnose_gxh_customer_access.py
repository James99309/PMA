#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断gxh账户无法查看上海博望电子科技有限公司客户的原因"""
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
from app.models.user import User, Affiliation, Permission
from app.models.customer import Company, Contact
from sqlalchemy import or_, and_

app = create_app()

with app.app_context():
    print("=" * 80)
    print("诊断gxh账户权限问题")
    print("=" * 80)

    # 1. 查询gxh用户信息
    print("\n【1. gxh用户信息】")
    gxh_user = User.query.filter_by(username='gxh').first()
    if not gxh_user:
        print("❌ 未找到gxh用户")
        sys.exit(1)

    print(f"用户ID: {gxh_user.id}")
    print(f"用户名: {gxh_user.username}")
    print(f"姓名: {gxh_user.name}")
    print(f"角色: {gxh_user.role}")
    print(f"公司名称: {gxh_user.company_name}")
    print(f"部门: {gxh_user.department}")

    # 获取权限级别
    permission = Permission.query.filter_by(
        user_id=gxh_user.id,
        module='customer'
    ).first()
    permission_level = permission.permission_level if permission else 'personal'
    print(f"客户模块权限级别: {permission_level}")
    if permission:
        print(f"  - 查看权限: {permission.can_view}")
        print(f"  - 创建权限: {permission.can_create}")
        print(f"  - 编辑权限: {permission.can_edit}")
        print(f"  - 删除权限: {permission.can_delete}")

    # 2. 查询"上海博望电子科技有限公司"客户信息
    print("\n【2. 上海博望电子科技有限公司客户信息】")
    customer = Company.query.filter(
        Company.company_name.like('%上海博望电子科技有限公司%'),
        Company.is_deleted == False
    ).first()

    if not customer:
        print("❌ 未找到该客户")
        sys.exit(1)

    print(f"客户ID: {customer.id}")
    print(f"客户名称: {customer.company_name}")
    print(f"创建人ID: {customer.owner_id}")
    if customer.owner:
        print(f"创建人: {customer.owner.name} ({customer.owner.username})")
        print(f"创建人角色: {customer.owner.role}")
        print(f"创建人公司: {customer.owner.company_name}")
        print(f"创建人部门: {customer.owner.department}")
    print(f"客户公司ID: {customer.company_id if hasattr(customer, 'company_id') else 'N/A'}")
    shared_user_ids = customer.shared_with_users if customer.shared_with_users else []
    if shared_user_ids:
        shared_users = User.query.filter(User.id.in_(shared_user_ids)).all()
        print(f"共享用户: {[u.name for u in shared_users]}")
    else:
        print(f"共享用户: 无")

    # 3. 检查归属关系
    print("\n【3. 归属关系检查】")

    # gxh的直属下属
    subordinates = Affiliation.query.filter_by(
        superior_id=gxh_user.id
    ).all()
    print(f"gxh的直属下属数量: {len(subordinates)}")
    if subordinates:
        for aff in subordinates:
            print(f"  - {aff.subordinate.name} ({aff.subordinate.username})")

    # gxh的所有下级（递归）
    def get_all_subordinates(user_id, visited=None):
        if visited is None:
            visited = set()
        if user_id in visited:
            return []
        visited.add(user_id)

        direct_subs = Affiliation.query.filter_by(
            superior_id=user_id
        ).all()

        all_subs = []
        for aff in direct_subs:
            all_subs.append(aff.subordinate)
            all_subs.extend(get_all_subordinates(aff.subordinate_id, visited))
        return all_subs

    all_subordinates = get_all_subordinates(gxh_user.id)
    print(f"gxh的所有下级数量（递归）: {len(all_subordinates)}")
    if all_subordinates:
        for sub in all_subordinates:
            print(f"  - {sub.name} ({sub.username})")

    # 4. 检查gxh是否有联系人关联到该客户
    print("\n【4. 联系人关系检查】")
    gxh_contacts = Contact.query.filter_by(
        owner_id=gxh_user.id,
        company_id=customer.id,
        is_deleted=False
    ).all()
    print(f"gxh在该客户下的联系人数量: {len(gxh_contacts)}")
    if gxh_contacts:
        for contact in gxh_contacts:
            print(f"  - {contact.name}")

    # 5. 检查共享关系
    print("\n【5. 共享关系检查】")
    is_shared = gxh_user.id in (customer.shared_with_users if customer.shared_with_users else [])
    print(f"客户是否直接共享给gxh: {is_shared}")

    # 6. 模拟get_viewable_data逻辑
    print("\n【6. 数据访问权限模拟】")
    print(f"权限级别: {permission_level}")

    should_see = False
    reasons = []

    if permission_level == 'system':
        should_see = True
        reasons.append("✅ system级权限：可查看所有客户")
    elif permission_level == 'company':
        # 同公司的所有用户创建的客户
        if customer.owner and customer.owner.company_name == gxh_user.company_name:
            should_see = True
            reasons.append(f"✅ company级权限：创建人{customer.owner.name}与gxh同公司({gxh_user.company_name})")
        else:
            reasons.append(f"❌ company级权限：创建人{customer.owner.name if customer.owner else 'N/A'}与gxh不同公司")
    elif permission_level == 'department':
        # 同部门同公司的用户创建的客户
        if customer.owner and \
           customer.owner.company_name == gxh_user.company_name and \
           customer.owner.department == gxh_user.department:
            should_see = True
            reasons.append(f"✅ department级权限：创建人{customer.owner.name}与gxh同部门同公司")
        else:
            reasons.append(f"❌ department级权限：创建人{customer.owner.name if customer.owner else 'N/A'}与gxh不同部门或不同公司")
    elif permission_level == 'personal':
        reasons.append("personal级权限，继续检查其他条件...")

    # 个人创建
    if customer.owner_id == gxh_user.id:
        should_see = True
        reasons.append("✅ 自己创建的客户")
    else:
        reasons.append(f"❌ 不是自己创建的客户（创建人：{customer.owner.name if customer.owner else 'N/A'}）")

    # 共享
    if is_shared:
        should_see = True
        reasons.append("✅ 客户直接共享给gxh")
    else:
        reasons.append("❌ 客户未直接共享给gxh")

    # 归属关系授权
    subordinate_ids = [sub.id for sub in all_subordinates]
    if customer.owner_id in subordinate_ids:
        should_see = True
        reasons.append(f"✅ 归属关系：创建人{customer.owner.name}是gxh的下级")
    else:
        reasons.append(f"❌ 归属关系：创建人{customer.owner.name if customer.owner else 'N/A'}不是gxh的下级")

    # 联系人级别访问
    if len(gxh_contacts) > 0:
        should_see = True
        reasons.append(f"✅ 联系人访问：gxh在该客户下有{len(gxh_contacts)}个联系人")
    else:
        reasons.append("❌ 联系人访问：gxh在该客户下没有联系人")

    print("\n权限检查结果:")
    for reason in reasons:
        print(f"  {reason}")

    print(f"\n【最终判断】gxh应该能看到该客户: {'是' if should_see else '否'}")

    # 7. 实际查询验证
    print("\n【7. 实际查询验证】")
    from app.utils.access_control import get_viewable_data

    viewable_companies = get_viewable_data(
        Company,
        gxh_user,
        [Company.is_deleted == False]
    ).all()

    customer_ids = [c.id for c in viewable_companies]
    can_see_customer = customer.id in customer_ids

    print(f"gxh可查看的客户总数: {len(viewable_companies)}")
    print(f"实际能否查看该客户: {'是' if can_see_customer else '否'}")

    if not can_see_customer:
        print("\n❌ 问题确认：gxh确实无法查看该客户")
        print("\n可能的解决方案：")
        print("1. 将客户直接共享给gxh")
        print("2. 建立gxh与客户创建人的归属关系")
        print("3. 让gxh在该客户下创建联系人")
        print("4. 调整gxh的权限级别")
    else:
        print("\n✅ gxh应该能看到该客户，可能是其他原因导致查询不到")

    print("\n" + "=" * 80)
