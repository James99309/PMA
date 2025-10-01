#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to test project owner options generation for admin
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

def debug_owner_options():
    app = create_app()
    
    with app.app_context():
        # 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("❌ 找不到admin用户")
            return
            
        print(f"✅ 找到admin用户: {admin_user.username}, ID: {admin_user.id}, 角色: {admin_user.role}")
        
        # 模拟 _get_project_owner_options 函数的逻辑
        print(f"\n🔍 模拟项目拥有者选项生成逻辑:")
        
        # 1. 获取所有项目的拥有者ID（不经过访问控制）
        all_owner_ids_query = Project.query.filter(Project.owner_id.isnot(None))\
            .with_entities(Project.owner_id.distinct())
        all_unique_owner_ids = {row[0] for row in all_owner_ids_query.all()}
        print(f"  - 数据库中所有项目的拥有者ID数量: {len(all_unique_owner_ids)}")
        print(f"  - 拥有者ID列表: {sorted(all_unique_owner_ids)}")
        
        # 2. 获取admin可见项目的拥有者ID（经过访问控制）
        viewable_owner_ids_query = get_viewable_data(Project, admin_user)\
            .filter(Project.owner_id.isnot(None))\
            .with_entities(Project.owner_id.distinct())
        viewable_unique_owner_ids = {row[0] for row in viewable_owner_ids_query.all()}
        print(f"  - admin可见项目的拥有者ID数量: {len(viewable_unique_owner_ids)}")
        print(f"  - admin可见拥有者ID列表: {sorted(viewable_unique_owner_ids)}")
        
        # 3. 分析差异
        missing_owner_ids = all_unique_owner_ids - viewable_unique_owner_ids
        if missing_owner_ids:
            print(f"⚠️  admin看不到的拥有者ID: {sorted(missing_owner_ids)}")
            
            # 分析这些拥有者的角色
            missing_owners = User.query.filter(User.id.in_(missing_owner_ids)).all()
            print(f"\n📊 看不到的项目拥有者分析:")
            for owner in missing_owners:
                projects_count = Project.query.filter_by(owner_id=owner.id).count()
                print(f"  - {owner.username} ({owner.real_name}): 角色={owner.role}, 项目数={projects_count}")
        else:
            print(f"✅ admin可以看到所有项目拥有者")
            
        # 4. 检查具体的访问控制逻辑
        print(f"\n🔧 访问控制详细分析:")
        print(f"  - admin角色: {admin_user.role}")
        print(f"  - admin有项目查看权限: {admin_user.has_permission('project', 'view')}")
        print(f"  - admin权限级别: {admin_user.get_permission_level('project')}")
        
        # 5. 检查项目表是否有is_deleted字段
        print(f"\n🗂️ 数据库结构检查:")
        has_is_deleted = hasattr(Project, 'is_deleted')
        print(f"  - Project模型有is_deleted字段: {has_is_deleted}")
        if has_is_deleted:
            deleted_projects = Project.query.filter_by(is_deleted=True).count()
            print(f"  - 已删除的项目数量: {deleted_projects}")

if __name__ == "__main__":
    debug_owner_options()