#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细调试gxh的department权限过滤逻辑"""
import sys, os

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

# 设置云端SP8D数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

from app import create_app, db
from app.models.user import User, Affiliation
from app.models.customer import Company
from app.utils.access_control import get_department_user_ids

app = create_app()

with app.app_context():
    print("=" * 80)
    print("详细调试gxh的department权限过滤逻辑")
    print("=" * 80)

    # 1. 查询gxh用户
    gxh_user = User.query.filter_by(username='gxh').first()
    print(f"\n【gxh用户信息】")
    print(f"ID: {gxh_user.id}")
    print(f"姓名: {gxh_user.name}")
    print(f"公司: {gxh_user.company_name}")
    print(f"部门: {gxh_user.department}")

    # 2. 查询目标客户
    customer = Company.query.filter(
        Company.company_name.like('%上海博望电子科技有限公司%'),
        Company.is_deleted == False
    ).first()
    print(f"\n【目标客户信息】")
    print(f"ID: {customer.id}")
    print(f"名称: {customer.company_name}")
    print(f"创建人ID: {customer.owner_id}")
    print(f"创建人: {customer.owner.name if customer.owner else 'N/A'}")

    # 3. 获取部门用户ID列表
    print(f"\n【调用 get_department_user_ids() 函数】")
    dept_user_ids = get_department_user_ids(gxh_user, include_affiliations=True)
    print(f"返回的用户ID列表: {dept_user_ids}")
    print(f"用户ID数量: {len(dept_user_ids)}")

    # 4. 检查gxh自己是否在列表中
    print(f"\ngxh自己(ID:{gxh_user.id})是否在列表中: {gxh_user.id in dept_user_ids}")

    # 5. 检查客户创建人是否在列表中
    print(f"客户创建人(ID:{customer.owner_id})是否在列表中: {customer.owner_id in dept_user_ids}")

    # 6. 列出所有部门用户
    print(f"\n【同部门同公司的所有用户】")
    same_dept_users = User.query.filter(
        User.department == gxh_user.department,
        User.company_name == gxh_user.company_name
    ).all()
    print(f"数量: {len(same_dept_users)}")
    for u in same_dept_users:
        print(f"  - ID:{u.id}, 用户名:{u.username}, 姓名:{u.name}")

    # 7. 列出通过归属关系的用户
    print(f"\n【通过归属关系授权的用户】")
    affiliations = Affiliation.query.filter_by(viewer_id=gxh_user.id).all()
    print(f"数量: {len(affiliations)}")
    for aff in affiliations:
        print(f"  - ID:{aff.owner_id}, 用户名:{aff.owner.username}, 姓名:{aff.owner.name}")

    # 8. 模拟权限过滤查询
    print(f"\n【模拟department级权限过滤】")
    print(f"过滤条件: Company.owner_id.in_({dept_user_ids})")

    filtered_companies = Company.query.filter(
        Company.is_deleted == False,
        Company.owner_id.in_(dept_user_ids)
    ).all()

    print(f"过滤后的客户数量: {len(filtered_companies)}")

    # 9. 检查目标客户是否在过滤结果中
    filtered_customer_ids = [c.id for c in filtered_companies]
    is_in_filtered = customer.id in filtered_customer_ids

    print(f"\n目标客户(ID:{customer.id})是否在过滤结果中: {is_in_filtered}")

    if not is_in_filtered:
        print("\n❌ 确认问题：目标客户未通过department权限过滤")
        print("\n可能的原因：")
        print(f"1. 客户创建人ID({customer.owner_id})不在dept_user_ids列表({dept_user_ids})中")
        print(f"2. 数据库记录的department或company_name不一致")

        # 详细对比
        print(f"\n【详细对比】")
        print(f"gxh的部门: '{gxh_user.department}'")
        print(f"gxh的公司: '{gxh_user.company_name}'")
        if customer.owner:
            print(f"创建人的部门: '{customer.owner.department}'")
            print(f"创建人的公司: '{customer.owner.company_name}'")
            print(f"部门是否完全匹配: {gxh_user.department == customer.owner.department}")
            print(f"公司是否完全匹配: {gxh_user.company_name == customer.owner.company_name}")

            # 检查是否有隐藏的空格或特殊字符
            print(f"\ngxh部门字节: {gxh_user.department.encode('utf-8') if gxh_user.department else 'None'}")
            print(f"创建人部门字节: {customer.owner.department.encode('utf-8') if customer.owner.department else 'None'}")
    else:
        print("\n✅ 目标客户通过了department权限过滤")
        print("问题可能在其他过滤条件或特殊过滤器(special_filters)中")

    print("\n" + "=" * 80)
