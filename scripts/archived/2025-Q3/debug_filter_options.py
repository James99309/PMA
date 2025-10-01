#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to test project owner filter options generation
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.user import User
from app.models.project import Project
from app.utils.access_control import get_viewable_data

def debug_filter_options():
    app = create_app()
    
    with app.app_context():
        # 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("❌ 找不到admin用户")
            return
            
        print(f"✅ 找到admin用户: {admin_user.username}, ID: {admin_user.id}")
        
        # 1. 获取所有项目及其拥有者（不经过访问控制）
        print(f"\n📊 所有项目拥有者分析:")
        all_projects = Project.query.filter(Project.owner_id.isnot(None)).all()
        all_owners = {}
        for project in all_projects:
            if project.owner_id not in all_owners:
                all_owners[project.owner_id] = {
                    'username': project.owner.username,
                    'real_name': project.owner.real_name,
                    'role': project.owner.role,
                    'projects': []
                }
            all_owners[project.owner_id]['projects'].append(project.id)
            
        print(f"  - 总拥有者数量: {len(all_owners)}")
        for owner_id, info in sorted(all_owners.items()):
            print(f"  - {info['username']} ({info['real_name']}): 角色={info['role']}, 项目数={len(info['projects'])}")
        
        # 2. 获取admin可见项目的拥有者（经过访问控制）
        print(f"\n🔍 admin可见项目拥有者分析:")
        
        # 模拟 _get_project_owner_options 的逻辑
        unique_owner_ids_query = get_viewable_data(Project, admin_user)\
            .filter(Project.owner_id.isnot(None))\
            .with_entities(Project.owner_id.distinct())
        
        unique_owner_ids = {row[0] for row in unique_owner_ids_query.all()}
        print(f"  - admin可见项目的拥有者ID数量: {len(unique_owner_ids)}")
        
        visible_owners = {}
        for owner_id in unique_owner_ids:
            if owner_id in all_owners:
                visible_owners[owner_id] = all_owners[owner_id]
        
        for owner_id, info in sorted(visible_owners.items()):
            print(f"  - {info['username']} ({info['real_name']}): 角色={info['role']}, 项目数={len(info['projects'])}")
        
        # 3. 分析差异
        missing_owner_ids = set(all_owners.keys()) - unique_owner_ids
        if missing_owner_ids:
            print(f"\n⚠️  admin看不到的拥有者:")
            for owner_id in sorted(missing_owner_ids):
                info = all_owners[owner_id]
                print(f"  - {info['username']} ({info['real_name']}): 角色={info['role']}, 项目数={len(info['projects'])}")
                
                # 查看这些拥有者的具体项目
                missing_projects = Project.query.filter_by(owner_id=owner_id).limit(3).all()
                print(f"    项目样例: {[p.project_name[:20]+'...' if len(p.project_name) > 20 else p.project_name for p in missing_projects]}")
        else:
            print(f"✅ admin可以看到所有项目拥有者")
            
        # 4. 获取实际生成的筛选选项
        print(f"\n🎯 实际生成的筛选选项:")
        available_users = User.query.filter(
            User.id.in_(unique_owner_ids),
            User._is_active == True
        ).order_by(User.real_name, User.username).all()
        
        print(f"  - 筛选选项数量: {len(available_users)}")
        for user in available_users:
            projects_count = len(all_owners.get(user.id, {}).get('projects', []))
            print(f"  - {user.username} ({user.real_name or '无'}): 角色={user.role}, 项目数={projects_count}")
            
        # 5. 检查非厂商角色是否在筛选选项中
        non_vendor_roles = ['dealer', 'customer_sales', 'admin', 'ceo', 'business_admin', 'finance_supervisor']
        print(f"\n🏢 非厂商角色在筛选选项中的情况:")
        for user in available_users:
            if user.role in non_vendor_roles:
                projects_count = len(all_owners.get(user.id, {}).get('projects', []))
                print(f"  ✅ {user.username} ({user.role}): {projects_count}个项目")
                
        # 检查是否有非厂商角色的拥有者被排除
        excluded_non_vendor = []
        for owner_id in missing_owner_ids:
            info = all_owners[owner_id]
            if info['role'] in non_vendor_roles:
                excluded_non_vendor.append(info)
                
        if excluded_non_vendor:
            print(f"  ❌ 被排除的非厂商角色拥有者:")
            for info in excluded_non_vendor:
                print(f"    - {info['username']} ({info['role']}): {len(info['projects'])}个项目")
        else:
            print(f"  ✅ 所有非厂商角色拥有者都在筛选选项中")

if __name__ == "__main__":
    debug_filter_options()