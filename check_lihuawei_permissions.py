#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查lihuawei用户的权限设置和数据访问权限
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User, Affiliation
from app.models.customer import Company
from app.models.project import Project
from app.utils.access_control import get_viewable_data

def check_lihuawei_permissions():
    """检查lihuawei用户的权限设置和数据访问权限"""
    app = create_app()
    
    with app.app_context():
        print("🔍 检查lihuawei用户的权限设置和数据访问权限...")
        
        # 查找lihuawei用户
        lihuawei = User.query.filter_by(username='lihuawei').first()
        
        if not lihuawei:
            print("❌ 没有找到lihuawei用户")
            return
        
        print(f"👤 用户信息:")
        print(f"   用户名: {lihuawei.username}")
        print(f"   真实姓名: {lihuawei.real_name}")
        print(f"   角色: {lihuawei.role}")
        print(f"   用户ID: {lihuawei.id}")
        print(f"   所属部门: {lihuawei.department}")
        
        # 检查归属关系（lihuawei作为查看者）
        print(f"\n🔗 lihuawei的归属关系（作为查看者）:")
        affiliations_as_viewer = Affiliation.query.filter_by(viewer_id=lihuawei.id).all()
        
        if affiliations_as_viewer:
            print(f"   发现 {len(affiliations_as_viewer)} 个归属关系:")
            for aff in affiliations_as_viewer:
                owner = db.session.get(User, aff.owner_id)
                print(f"   - 可以查看 {owner.real_name or owner.username} ({owner.role}) 的数据")
        else:
            print("   ❌ 没有找到归属关系")
        
        # 检查归属关系（lihuawei作为数据拥有者）
        print(f"\n🔗 lihuawei的归属关系（作为数据拥有者）:")
        affiliations_as_owner = Affiliation.query.filter_by(owner_id=lihuawei.id).all()
        
        if affiliations_as_owner:
            print(f"   发现 {len(affiliations_as_owner)} 个归属关系:")
            for aff in affiliations_as_owner:
                viewer = db.session.get(User, aff.viewer_id)
                print(f"   - {viewer.real_name or viewer.username} ({viewer.role}) 可以查看lihuawei的数据")
        else:
            print("   ❌ 没有人可以通过归属关系查看lihuawei的数据")
        
        # 检查客户数据访问权限
        print(f"\n🏢 客户数据访问权限:")
        viewable_companies = get_viewable_data(Company, lihuawei).all()
        print(f"   可以访问 {len(viewable_companies)} 个客户")
        
        # 统计拥有者分布
        owner_stats = {}
        for company in viewable_companies:
            owner = db.session.get(User, company.owner_id) if company.owner_id else None
            owner_name = owner.real_name or owner.username if owner else 'Unknown'
            owner_stats[owner_name] = owner_stats.get(owner_name, 0) + 1
        
        print(f"   客户拥有者分布:")
        for owner_name, count in sorted(owner_stats.items()):
            print(f"   - {owner_name}: {count} 个客户")
        
        # 检查项目数据访问权限
        print(f"\n📋 项目数据访问权限:")
        viewable_projects = get_viewable_data(Project, lihuawei).all()
        print(f"   可以访问 {len(viewable_projects)} 个项目")
        
        # 统计项目拥有者分布
        project_owner_stats = {}
        for project in viewable_projects:
            owner = db.session.get(User, project.owner_id) if project.owner_id else None
            owner_name = owner.real_name or owner.username if owner else 'Unknown'
            project_owner_stats[owner_name] = project_owner_stats.get(owner_name, 0) + 1
        
        print(f"   项目拥有者分布:")
        for owner_name, count in sorted(project_owner_stats.items()):
            print(f"   - {owner_name}: {count} 个项目")
        
        # 分析权限异常
        print(f"\n⚠️  权限异常分析:")
        
        # 检查不是lihuawei创建的数据
        other_owners_companies = sum(count for name, count in owner_stats.items() if name != '李华伟')
        other_owners_projects = sum(count for name, count in project_owner_stats.items() if name != '李华伟')
        
        print(f"   lihuawei自己创建的客户: {owner_stats.get('李华伟', 0)} 个")
        print(f"   lihuawei可访问的其他人客户: {other_owners_companies} 个")
        print(f"   lihuawei自己创建的项目: {project_owner_stats.get('李华伟', 0)} 个")
        print(f"   lihuawei可访问的其他人项目: {other_owners_projects} 个")
        
        if other_owners_companies > 0 or other_owners_projects > 0:
            print(f"   🚨 发现权限异常：lihuawei可以访问其他人创建的数据！")
            print(f"   建议检查access_control.py中sales_manager角色的权限逻辑")
        else:
            print(f"   ✅ 权限正常：lihuawei只能访问自己创建的数据")

if __name__ == '__main__':
    check_lihuawei_permissions() 