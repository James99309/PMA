#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查gxh的content_filters内容过滤配置"""
import sys, os
import json

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
from app.models.user import User, Permission
from app.models.customer import Company

app = create_app()

with app.app_context():
    print("=" * 80)
    print("检查gxh的content_filters内容过滤配置")
    print("=" * 80)

    # 1. 查询gxh用户
    gxh_user = User.query.filter_by(username='gxh').first()
    print(f"\n【gxh用户】")
    print(f"ID: {gxh_user.id}")
    print(f"姓名: {gxh_user.name}")

    # 2. 查询gxh在customer模块的权限配置
    customer_permission = Permission.query.filter_by(
        user_id=gxh_user.id,
        module='customer'
    ).first()

    if not customer_permission:
        print("\n❌ 未找到gxh的customer权限配置")
        sys.exit(1)

    print(f"\n【customer模块权限配置】")
    print(f"权限级别: {customer_permission.permission_level}")
    print(f"查看权限: {customer_permission.can_view}")
    print(f"创建权限: {customer_permission.can_create}")
    print(f"编辑权限: {customer_permission.can_edit}")
    print(f"删除权限: {customer_permission.can_delete}")

    print(f"\n【内容过滤器 (content_filters)】")
    if customer_permission.content_filters:
        print(f"内容过滤器: {json.dumps(customer_permission.content_filters, ensure_ascii=False, indent=2)}")

        # 检查行业过滤
        if 'industry' in customer_permission.content_filters:
            allowed_industries = customer_permission.content_filters['industry']
            print(f"\n✅ 发现行业过滤器！")
            print(f"允许查看的行业: {allowed_industries}")

        # 检查地区过滤
        if 'region' in customer_permission.content_filters:
            allowed_regions = customer_permission.content_filters['region']
            print(f"\n✅ 发现地区过滤器！")
            print(f"允许查看的地区: {allowed_regions}")
    else:
        print("无内容过滤器")

    # 3. 查询目标客户信息
    customer = Company.query.filter(
        Company.company_name.like('%上海博望电子科技有限公司%'),
        Company.is_deleted == False
    ).first()

    print(f"\n【目标客户信息】")
    print(f"客户ID: {customer.id}")
    print(f"客户名称: {customer.company_name}")
    print(f"客户行业: {customer.industry}")
    print(f"客户地区: {customer.region}")

    # 4. 检查目标客户是否符合内容过滤器
    if customer_permission.content_filters:
        print(f"\n【内容过滤器匹配检查】")

        is_pass = True
        reasons = []

        # 检查行业过滤
        if 'industry' in customer_permission.content_filters and customer_permission.content_filters['industry']:
            allowed_industries = customer_permission.content_filters['industry']
            if customer.industry in allowed_industries:
                reasons.append(f"✅ 行业匹配: {customer.industry} 在允许列表中")
            else:
                reasons.append(f"❌ 行业不匹配: {customer.industry} 不在允许列表 {allowed_industries} 中")
                is_pass = False

        # 检查地区过滤
        if 'region' in customer_permission.content_filters and customer_permission.content_filters['region']:
            allowed_regions = customer_permission.content_filters['region']
            if customer.region in allowed_regions:
                reasons.append(f"✅ 地区匹配: {customer.region} 在允许列表中")
            else:
                reasons.append(f"❌ 地区不匹配: {customer.region} 不在允许列表 {allowed_regions} 中")
                is_pass = False

        for reason in reasons:
            print(f"  {reason}")

        print(f"\n【最终判断】目标客户是否通过内容过滤器: {'是 ✅' if is_pass else '否 ❌'}")

        if not is_pass:
            print("\n" + "="*80)
            print("🎯 问题确认：目标客户被内容过滤器过滤掉了！")
            print("="*80)
            print("\n解决方案：")
            print("1. 【推荐】调整gxh的内容过滤器配置，添加目标客户的行业/地区")
            print(f"   - 当前允许的行业: {customer_permission.content_filters.get('industry', '无限制')}")
            print(f"   - 当前允许的地区: {customer_permission.content_filters.get('region', '无限制')}")
            print(f"   - 目标客户行业: {customer.industry}")
            print(f"   - 目标客户地区: {customer.region}")
            print("\n2. 或者清空gxh的内容过滤器，允许查看所有行业/地区的客户")
            print("\n3. 或者修改目标客户的行业/地区信息，使其符合过滤器要求")
        else:
            print("\n✅ 目标客户通过了内容过滤器检查")
            print("问题可能在其他地方，需要进一步诊断")

    print("\n" + "=" * 80)
