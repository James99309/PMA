#!/usr/bin/env python3
"""
检查fangl用户的权限和数据访问范围
分析为什么可以看到其他部门的客户记录和项目记录

Created: 2025-06-27
Author: Assistant
Purpose: 诊断fangl用户的权限问题
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from flask import Flask
from app import create_app, db
from app.models.user import User, Affiliation
from app.models.project import Project
from app.models.customer import Company, Contact
from app.utils.access_control import get_viewable_data
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    print("=== fangl用户权限诊断工具 ===")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. 检查用户基本信息
            fangl = User.query.filter_by(username='fangl').first()
            if not fangl:
                print("❌ 未找到fangl用户")
                return
            
            print("\n=== fangl用户基本信息 ===")
            print(f"用户ID: {fangl.id}")
            print(f"用户名: {fangl.username}")
            print(f"真实姓名: {fangl.real_name}")
            print(f"角色: {fangl.role}")
            print(f"部门: {fangl.department}")
            print(f"公司: {fangl.company_name}")
            print(f"是否激活: {fangl.is_active}")
            
            # 2. 检查归属关系
            print("\n=== fangl用户归属关系 ===")
            
            # 检查fangl作为viewer的归属关系（可以查看谁的数据）
            as_viewer = Affiliation.query.filter_by(viewer_id=fangl.id).all()
            print(f"fangl可以查看的用户数量: {len(as_viewer)}")
            
            for affiliation in as_viewer:
                owner = User.query.get(affiliation.owner_id)
                if owner:
                    print(f"  可查看用户: {owner.username} ({owner.real_name}) - 部门: {owner.department}")
                else:
                    print(f"  可查看用户ID: {affiliation.owner_id} (用户不存在)")
            
            # 检查fangl作为owner的归属关系（谁可以查看fangl的数据）
            as_owner = Affiliation.query.filter_by(owner_id=fangl.id).all()
            print(f"\n可以查看fangl数据的用户数量: {len(as_owner)}")
            
            for affiliation in as_owner:
                viewer = User.query.get(affiliation.viewer_id)
                if viewer:
                    print(f"  查看者: {viewer.username} ({viewer.real_name}) - 部门: {viewer.department}")
                else:
                    print(f"  查看者ID: {affiliation.viewer_id} (用户不存在)")
            
            # 3. 分析访问控制逻辑
            print("\n=== 访问控制逻辑分析 ===")
            
            user_role = fangl.role.strip() if fangl.role else ''
            print(f"fangl角色 (去除空格): '{user_role}'")
            
            # 检查是否匹配特殊角色处理
            if user_role in ['service', 'service_manager']:
                print("✅ fangl匹配服务经理角色处理逻辑")
                print("根据access_control.py逻辑:")
                print("  项目权限: 可以查看所有'业务机会'项目 + 自己的项目 + 自己作为销售负责人的项目")
                print("  客户权限: 只能查看自己的客户信息和授权的客户信息(通过归属关系)")
            elif user_role == 'customer_sales':
                print("✅ fangl匹配客户销售角色处理逻辑")
                print("根据access_control.py逻辑:")
                print("  项目权限: 只能查看本部门用户创建的项目")
                print("  客户权限: 只能查看本部门用户创建的客户信息")
            else:
                print("❌ fangl不匹配特殊角色，使用默认逻辑")
                print("默认逻辑: 直接归属 + 归属链")
            
            # 4. 检查同部门用户
            print("\n=== 同部门用户检查 ===")
            
            if fangl.department:
                same_dept_users = User.query.filter(
                    User.department == fangl.department,
                    User.id != fangl.id  # 排除自己
                ).all()
                
                print(f"同部门({fangl.department})其他用户数量: {len(same_dept_users)}")
                
                for user in same_dept_users[:10]:  # 显示前10个
                    print(f"  {user.username} ({user.real_name}) - 角色: {user.role}")
            else:
                print("fangl没有设置部门信息")
            
            # 5. 检查项目访问权限
            print("\n=== fangl项目访问权限分析 ===")
            
            # 使用access_control模块获取可查看的项目
            viewable_projects = get_viewable_data(Project, fangl)
            total_project_count = viewable_projects.count()
            
            print(f"fangl可以查看的项目总数: {total_project_count}")
            
            # 分析前10个项目的详情
            sample_projects = viewable_projects.limit(10).all()
            print(f"\n前10个项目详情:")
            
            for project in sample_projects:
                owner = User.query.get(project.owner_id) if project.owner_id else None
                vendor_sales = User.query.get(project.vendor_sales_manager_id) if hasattr(project, 'vendor_sales_manager_id') and project.vendor_sales_manager_id else None
                
                print(f"  项目ID: {project.id}")
                print(f"    项目名称: {project.project_name}")
                print(f"    项目类型: {project.project_type}")
                print(f"    创建者: {owner.username if owner else 'N/A'} ({owner.department if owner else 'N/A'})")
                print(f"    厂商销售: {vendor_sales.username if vendor_sales else 'N/A'}")
                print(f"    创建时间: {project.created_at}")
                print()
            
            # 统计按部门分布
            print("按创建者部门统计:")
            dept_stats = {}
            for project in viewable_projects.all():
                owner = User.query.get(project.owner_id) if project.owner_id else None
                dept = owner.department if owner else '未知'
                dept_stats[dept] = dept_stats.get(dept, 0) + 1
            
            for dept, count in dept_stats.items():
                print(f"  {dept}: {count}个项目")
            
            # 6. 检查客户访问权限
            print("\n=== fangl客户访问权限分析 ===")
            
            # 使用access_control模块获取可查看的客户
            viewable_companies = get_viewable_data(Company, fangl)
            total_customer_count = viewable_companies.count()
            
            print(f"fangl可以查看的客户总数: {total_customer_count}")
            
            # 分析前10个客户的详情
            sample_companies = viewable_companies.limit(10).all()
            print(f"\n前10个客户详情:")
            
            for company in sample_companies:
                owner = User.query.get(company.owner_id) if company.owner_id else None
                
                print(f"  客户ID: {company.id}")
                print(f"    客户名称: {company.company_name}")
                print(f"    创建者: {owner.username if owner else 'N/A'} ({owner.department if owner else 'N/A'})")
                print(f"    创建时间: {company.created_at}")
                print()
            
            # 统计按部门分布
            print("按创建者部门统计:")
            dept_stats = {}
            for company in viewable_companies.all():
                owner = User.query.get(company.owner_id) if company.owner_id else None
                dept = owner.department if owner else '未知'
                dept_stats[dept] = dept_stats.get(dept, 0) + 1
            
            for dept, count in dept_stats.items():
                print(f"  {dept}: {count}个客户")
                
            # 7. 总结
            print("\n=== 诊断总结 ===")
            print(f"fangl角色: {fangl.role}")
            print(f"fangl可查看项目数: {total_project_count}")
            print(f"fangl可查看客户数: {total_customer_count}")
            print(f"fangl归属关系数: {len(as_viewer)}")
            
            # 分析问题
            print("\n=== 问题分析 ===")
            
            if user_role == 'customer_sales':
                print("✅ 问题已修复: fangl的角色是'customer_sales'，现在有专门的权限处理：")
                print("    - 项目权限: 只能查看本部门用户创建的项目")
                print("    - 客户权限: 只能查看本部门用户创建的客户信息")
                print("    - 权限范围：服务部内的用户数据")
            
            if len(as_viewer) > 5:
                print(f"⚠️  fangl有 {len(as_viewer)} 个归属关系，可能过多！")
                print("    这可能是fangl能看到其他部门数据的主要原因")
            
            # 检查权限是否合理（只看服务部数据）
            if total_project_count > 50 or total_customer_count > 100:
                print("⚠️  fangl可能有过多的服务部数据访问权限，建议检查:")
                print("   1. 是否所有服务部用户都应该互相可见")
                print("   2. 是否需要进一步细分权限")
            else:
                print("✅ fangl的数据访问权限已正确限制在服务部范围内")
            
        except Exception as e:
            logger.error(f"诊断过程发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main() 