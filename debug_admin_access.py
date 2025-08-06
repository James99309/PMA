#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to test admin access control for projects
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

def test_admin_project_access():
    app = create_app()
    
    with app.app_context():
        # 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("❌ 找不到admin用户")
            return
            
        print(f"✅ 找到admin用户: {admin_user.username}, ID: {admin_user.id}, 角色: {admin_user.role}")
        
        # 测试权限检查
        has_project_view = admin_user.has_permission('project', 'view')
        permission_level = admin_user.get_permission_level('project')
        
        print(f"📋 权限检查结果:")
        print(f"  - 有项目查看权限: {has_project_view}")
        print(f"  - 权限级别: {permission_level}")
        
        # 测试访问控制函数
        print(f"\n🔍 访问控制测试:")
        
        # 获取所有项目（不经过访问控制）
        all_projects = Project.query.count()
        print(f"  - 数据库中总项目数: {all_projects}")
        
        # 获取通过访问控制的项目
        viewable_query = get_viewable_data(Project, admin_user)
        viewable_count = viewable_query.count()
        print(f"  - 通过访问控制的项目数: {viewable_count}")
        
        # 分析差异
        if viewable_count < all_projects:
            print(f"⚠️  发现问题：admin用户看不到 {all_projects - viewable_count} 个项目")
            
            # 获取看不到的项目
            all_project_ids = [p.id for p in Project.query.all()]
            viewable_project_ids = [p.id for p in viewable_query.all()]
            invisible_project_ids = set(all_project_ids) - set(viewable_project_ids)
            
            print(f"🔎 看不到的项目ID: {list(invisible_project_ids)[:10]}...")  # 只显示前10个
            
            # 分析这些项目的特征
            if invisible_project_ids:
                invisible_projects = Project.query.filter(Project.id.in_(list(invisible_project_ids)[:5])).all()
                print(f"\n📊 看不到的项目特征分析（前5个）:")
                for project in invisible_projects:
                    owner_info = f"{project.owner.username} ({project.owner.role})" if project.owner else "None"
                    sales_manager_info = f"{project.vendor_sales_manager.username} ({project.vendor_sales_manager.role})" if project.vendor_sales_manager else "None"
                    print(f"  - ID {project.id}: {project.project_name}")
                    print(f"    拥有者: {owner_info}")
                    print(f"    销售经理: {sales_manager_info}")
        else:
            print(f"✅ admin用户可以看到所有项目")

if __name__ == "__main__":
    test_admin_project_access()