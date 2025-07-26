#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查项目数据库中的拥有者和厂商负责人数据
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.project import Project
from app.models.user import User
from sqlalchemy import distinct

def check_project_user_data():
    """检查项目中的用户相关数据"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("检查项目数据库中的拥有者和厂商负责人数据")
        print("=" * 80)
        
        # 1. 检查User表中的活跃用户
        print("\n1. User表中的用户数据：")
        print("-" * 40)
        
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = User.query.filter_by(is_active=False).count()
        deleted_users = User.query.filter_by(is_deleted=True).count()
        
        print(f"总用户数: {total_users}")
        print(f"活跃用户数: {active_users}")
        print(f"非活跃用户数: {inactive_users}")
        print(f"已删除用户数: {deleted_users}")
        
        # 列出前10个活跃用户
        print("\n活跃用户列表（前10个）：")
        active_user_list = User.query.filter_by(is_active=True, is_deleted=False).limit(10).all()
        for user in active_user_list:
            print(f"  ID: {user.id}, 用户名: {user.username}, 姓名: {user.name}, 部门: {user.department}")
        
        # 2. 检查Project表的结构
        print("\n\n2. Project表的结构检查：")
        print("-" * 40)
        
        # 获取一个项目实例来检查属性
        sample_project = Project.query.first()
        if sample_project:
            print("Project表的属性：")
            for attr in dir(sample_project):
                if not attr.startswith('_') and not callable(getattr(sample_project, attr, None)):
                    try:
                        value = getattr(sample_project, attr)
                        if 'owner' in attr.lower() or 'vendor' in attr.lower() or 'manager' in attr.lower():
                            print(f"  {attr}: {value}")
                    except:
                        pass
        
        # 3. 检查Project表中owner_id的数据情况
        print("\n\n3. Project表中owner_id的数据情况：")
        print("-" * 40)
        
        total_projects = Project.query.count()
        projects_with_owner = Project.query.filter(Project.owner_id.isnot(None)).count()
        projects_without_owner = Project.query.filter(Project.owner_id.is_(None)).count()
        
        print(f"项目总数: {total_projects}")
        print(f"有owner_id的项目数: {projects_with_owner}")
        print(f"无owner_id的项目数: {projects_without_owner}")
        
        # 获取所有不同的owner_id
        distinct_owner_ids = db.session.query(distinct(Project.owner_id)).filter(
            Project.owner_id.isnot(None)
        ).all()
        
        print(f"\n不同的owner_id数量: {len(distinct_owner_ids)}")
        print("前10个owner_id及其对应的用户：")
        for owner_id_tuple in distinct_owner_ids[:10]:
            owner_id = owner_id_tuple[0]
            user = User.query.get(owner_id)
            project_count = Project.query.filter_by(owner_id=owner_id).count()
            if user:
                print(f"  owner_id: {owner_id} -> 用户: {user.name} ({user.username}), 项目数: {project_count}")
            else:
                print(f"  owner_id: {owner_id} -> 用户不存在!, 项目数: {project_count}")
        
        # 4. 检查Project表中vendor_sales_manager_id的数据情况
        print("\n\n4. Project表中vendor_sales_manager_id的数据情况：")
        print("-" * 40)
        
        # 先检查是否有这个字段
        if hasattr(Project, 'vendor_sales_manager_id'):
            projects_with_vendor_manager = Project.query.filter(
                Project.vendor_sales_manager_id.isnot(None)
            ).count()
            projects_without_vendor_manager = Project.query.filter(
                Project.vendor_sales_manager_id.is_(None)
            ).count()
            
            print(f"有vendor_sales_manager_id的项目数: {projects_with_vendor_manager}")
            print(f"无vendor_sales_manager_id的项目数: {projects_without_vendor_manager}")
            
            # 获取所有不同的vendor_sales_manager_id
            distinct_vendor_manager_ids = db.session.query(distinct(Project.vendor_sales_manager_id)).filter(
                Project.vendor_sales_manager_id.isnot(None)
            ).all()
            
            print(f"\n不同的vendor_sales_manager_id数量: {len(distinct_vendor_manager_ids)}")
            print("前10个vendor_sales_manager_id及其对应的用户：")
            for vendor_manager_id_tuple in distinct_vendor_manager_ids[:10]:
                vendor_manager_id = vendor_manager_id_tuple[0]
                user = User.query.get(vendor_manager_id)
                project_count = Project.query.filter_by(vendor_sales_manager_id=vendor_manager_id).count()
                if user:
                    print(f"  vendor_sales_manager_id: {vendor_manager_id} -> 用户: {user.name} ({user.username}), 项目数: {project_count}")
                else:
                    print(f"  vendor_sales_manager_id: {vendor_manager_id} -> 用户不存在!, 项目数: {project_count}")
        else:
            print("Project表中没有vendor_sales_manager_id字段！")
        
        # 5. 检查具体的几个项目示例
        print("\n\n5. 项目示例（前5个）：")
        print("-" * 40)
        
        sample_projects = Project.query.limit(5).all()
        for project in sample_projects:
            print(f"\n项目: {project.name} (ID: {project.id})")
            print(f"  owner_id: {project.owner_id}")
            if project.owner_id:
                owner = User.query.get(project.owner_id)
                if owner:
                    print(f"  拥有者: {owner.name} ({owner.username})")
                else:
                    print(f"  拥有者: 用户不存在!")
            
            if hasattr(project, 'vendor_sales_manager_id'):
                print(f"  vendor_sales_manager_id: {project.vendor_sales_manager_id}")
                if project.vendor_sales_manager_id:
                    vendor_manager = User.query.get(project.vendor_sales_manager_id)
                    if vendor_manager:
                        print(f"  厂商负责人: {vendor_manager.name} ({vendor_manager.username})")
                    else:
                        print(f"  厂商负责人: 用户不存在!")
        
        # 6. 检查User表的查询是否正常
        print("\n\n6. 测试User查询功能：")
        print("-" * 40)
        
        # 测试筛选活跃用户的查询
        try:
            active_users_query = User.query.filter_by(is_active=True, is_deleted=False).order_by(User.name)
            active_users_list = active_users_query.all()
            print(f"成功查询到活跃用户: {len(active_users_list)}个")
            
            # 测试构建选项列表
            user_options = []
            for user in active_users_list[:5]:  # 只显示前5个
                option = {
                    'value': str(user.id),
                    'label': f"{user.name} ({user.username})"
                }
                user_options.append(option)
                print(f"  选项: {option}")
        except Exception as e:
            print(f"查询用户时出错: {str(e)}")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    check_project_user_data()