#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to test gxh user access to non-vendor accounts
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.user import User
from app.models.project import Project
from app.models.user import Affiliation
from app.utils.access_control import get_viewable_data
from app.views.project import _get_project_owner_options, _get_vendor_manager_options

def debug_gxh_access():
    app = create_app()
    
    with app.app_context():
        # 获取gxh用户
        gxh_user = User.query.filter_by(username='gxh').first()
        
        if not gxh_user:
            print("❌ 找不到gxh用户")
            return
            
        print(f"✅ 找到gxh用户: {gxh_user.username}, ID: {gxh_user.id}, 角色: {gxh_user.role}")
        
        # 检查gxh的权限设置
        print(f"\n🔧 权限检查:")
        print(f"  - 有项目查看权限: {gxh_user.has_permission('project', 'view')}")
        print(f"  - 权限级别: {gxh_user.get_permission_level('project')}")
        print(f"  - 是部门经理: {gxh_user.is_department_manager}")
        print(f"  - 部门: {gxh_user.department}")
        
        # 获取gxh可以查看的用户（通过数据归属）
        print(f"\n📋 数据归属配置:")
        affiliations = Affiliation.query.filter_by(viewer_id=gxh_user.id).all()
        affiliated_user_ids = [aff.owner_id for aff in affiliations]
        affiliated_users = User.query.filter(User.id.in_(affiliated_user_ids)).all()
        
        print(f"  - 总归属用户数: {len(affiliated_users)}")
        non_vendor_affiliated = []
        for user in affiliated_users:
            role_type = "非厂商" if user.role in ['dealer', 'customer_sales'] else "厂商"
            print(f"    - {user.username} ({user.real_name}): {user.role} ({role_type})")
            if user.role in ['dealer', 'customer_sales']:
                non_vendor_affiliated.append(user)
        
        print(f"  - 归属的非厂商用户数: {len(non_vendor_affiliated)}")
        
        # 检查这些非厂商用户拥有的项目数
        print(f"\n📊 非厂商用户项目统计:")
        total_non_vendor_projects = 0
        for user in non_vendor_affiliated:
            project_count = Project.query.filter_by(owner_id=user.id).count()
            total_non_vendor_projects += project_count
            print(f"  - {user.username}: {project_count}个项目")
        
        print(f"  总计: {total_non_vendor_projects}个非厂商用户项目")
        
        # 测试gxh能看到多少项目
        print(f"\n🔍 访问控制测试:")
        
        # 获取所有项目（不经过访问控制）
        all_projects_count = Project.query.count()
        print(f"  - 数据库中总项目数: {all_projects_count}")
        
        # 获取gxh可见项目（经过访问控制）
        viewable_query = get_viewable_data(Project, gxh_user)
        viewable_count = viewable_query.count()
        print(f"  - gxh可见项目数: {viewable_count}")
        
        # 分析gxh可见项目的拥有者
        viewable_projects = viewable_query.all()
        owner_stats = {}
        for project in viewable_projects:
            if project.owner_id:
                owner = project.owner
                if owner.username not in owner_stats:
                    owner_stats[owner.username] = {
                        'real_name': owner.real_name,
                        'role': owner.role,
                        'count': 0
                    }
                owner_stats[owner.username]['count'] += 1
        
        print(f"\n📈 gxh可见项目按拥有者统计:")
        non_vendor_visible_count = 0
        for username, stats in sorted(owner_stats.items()):
            role_type = "非厂商" if stats['role'] in ['dealer', 'customer_sales'] else "厂商"
            print(f"  - {username} ({stats['real_name']}): {stats['count']}个项目 ({stats['role']}, {role_type})")
            if stats['role'] in ['dealer', 'customer_sales']:
                non_vendor_visible_count += stats['count']
        
        print(f"  gxh可见的非厂商用户项目: {non_vendor_visible_count}个")
        
        # 测试筛选选项生成
        print(f"\n🎯 筛选选项测试:")
        project_owner_options = _get_project_owner_options(gxh_user)
        print(f"  - 项目拥有者筛选选项数量: {len(project_owner_options)}")
        
        # 分析筛选选项中的用户角色
        option_users = []
        for option in project_owner_options:
            user = User.query.get(int(option['value']))
            if user:
                option_users.append(user)
        
        print(f"\n📋 筛选选项中的用户:")
        non_vendor_in_options = 0
        for user in option_users:
            role_type = "非厂商" if user.role in ['dealer', 'customer_sales'] else "厂商"
            print(f"  - {user.username} ({user.real_name}): {user.role} ({role_type})")
            if user.role in ['dealer', 'customer_sales']:
                non_vendor_in_options += 1
        
        print(f"  筛选选项中的非厂商用户数: {non_vendor_in_options}")
        
        # 检查是否有遗漏的非厂商用户
        expected_non_vendor = set(u.username for u in non_vendor_affiliated if Project.query.filter_by(owner_id=u.id).count() > 0)
        actual_non_vendor = set(u.username for u in option_users if u.role in ['dealer', 'customer_sales'])
        missing_non_vendor = expected_non_vendor - actual_non_vendor
        
        if missing_non_vendor:
            print(f"\n⚠️  筛选选项中缺失的非厂商用户: {list(missing_non_vendor)}")
        else:
            print(f"\n✅ 所有预期的非厂商用户都在筛选选项中")
            
        # 详细调试访问控制逻辑
        print(f"\n🔬 详细权限分析:")
        print(f"  - gxh权限级别: {gxh_user.get_permission_level('project')}")
        
        # 检查归属关系是否正确工作
        viewable_user_ids = [gxh_user.id]
        affiliations = Affiliation.query.filter_by(viewer_id=gxh_user.id).all()
        for affiliation in affiliations:
            viewable_user_ids.append(affiliation.owner_id)
        print(f"  - 通过归属关系可查看的用户ID: {viewable_user_ids}")
        
        # 检查部门经理权限
        if gxh_user.is_department_manager and gxh_user.department:
            dept_users = User.query.filter_by(department=gxh_user.department).all()
            dept_user_ids = [u.id for u in dept_users]
            print(f"  - 同部门用户ID: {dept_user_ids}")
            viewable_user_ids.extend(dept_user_ids)
        
        viewable_user_ids = list(set(viewable_user_ids))
        print(f"  - 最终可查看用户ID列表: {viewable_user_ids}")
        
        # 统计这些用户拥有的项目
        projects_by_viewable_users = Project.query.filter(Project.owner_id.in_(viewable_user_ids)).count()
        print(f"  - 基于权限逻辑应该可见的项目数: {projects_by_viewable_users}")

if __name__ == "__main__":
    debug_gxh_access()