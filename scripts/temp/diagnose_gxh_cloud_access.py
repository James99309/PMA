#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断gxh账户在云端SP8D数据库无法查看上海博望电子科技有限公司客户的原因"""
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

# 设置云端SP8D数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

from app import create_app, db
from app.models.user import User, Affiliation, Permission
from app.models.customer import Company, Contact
from sqlalchemy import or_, and_

app = create_app()

with app.app_context():
    print("=" * 80)
    print("诊断gxh账户在云端SP8D数据库的权限问题")
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
        viewer_id=gxh_user.id
    ).all()
    print(f"gxh可查看的归属关系数量: {len(subordinates)}")
    if subordinates:
        print("gxh可查看的数据所有者:")
        for aff in subordinates:
            print(f"  - {aff.owner.name} ({aff.owner.username})")

    # 4. 检查gxh是否有联系人关联到该客户
    print("\n【4. 联系人关系检查】")
    gxh_contacts = Contact.query.filter_by(
        owner_id=gxh_user.id,
        company_id=customer.id
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
            reasons.append(f"❌ company级权限：创建人公司({customer.owner.company_name if customer.owner else 'N/A'})与gxh公司({gxh_user.company_name})不同")
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
    owner_ids = [aff.owner_id for aff in subordinates]
    if customer.owner_id in owner_ids:
        should_see = True
        reasons.append(f"✅ 归属关系：创建人{customer.owner.name}的数据已授权给gxh查看")
    else:
        reasons.append(f"❌ 归属关系：创建人{customer.owner.name if customer.owner else 'N/A'}的数据未授权给gxh查看")

    # 联系人级别访问
    if len(gxh_contacts) > 0:
        should_see = True
        reasons.append(f"✅ 联系人访问：gxh在该客户下有{len(gxh_contacts)}个联系人")
    else:
        reasons.append("❌ 联系人访问：gxh在该客户下没有联系人")

    print("\n权限检查结果:")
    for reason in reasons:
        print(f"  {reason}")

    print(f"\n【最终判断】gxh应该能看到该客户: {'是 ✅' if should_see else '否 ❌'}")

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
    print(f"实际能否查看该客户: {'是 ✅' if can_see_customer else '否 ❌'}")

    if not can_see_customer:
        print("\n" + "="*80)
        print("❌ 问题确认：gxh确实无法查看该客户")
        print("="*80)
        print("\n可能的解决方案：")
        print("1. 【推荐】将客户直接共享给gxh")
        print("   - 在客户详情页点击'共享'按钮，添加gxh")
        print("\n2. 建立归属关系")
        print(f"   - 在归属关系管理中，添加：创建人({customer.owner.name})的数据授权给gxh查看")
        print("\n3. 让gxh在该客户下创建联系人")
        print("   - gxh创建该客户的联系人后，会自动获得客户查看权限")
        print("\n4. 调整创建人公司信息")
        if customer.owner:
            print(f"   - 将创建人{customer.owner.name}的公司改为: {gxh_user.company_name}")

        # 显示一些可能相关的客户
        print("\n【相关信息】gxh可查看的前5个客户示例:")
        for i, c in enumerate(viewable_companies[:5], 1):
            print(f"{i}. {c.company_name} (ID:{c.id}, 创建人:{c.owner.name if c.owner else 'N/A'})")
    else:
        print("\n✅ gxh能查看该客户，可能是筛选或搜索条件导致显示问题")

    print("\n" + "=" * 80)
