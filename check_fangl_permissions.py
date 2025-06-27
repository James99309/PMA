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

def check_fangl_user():
    """检查fangl用户的基本信息"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # 查找fangl用户
            fangl = User.query.filter_by(username='fangl').first()
            if not fangl:
                logger.error("未找到fangl用户")
                return None
            
            logger.info("=== fangl用户基本信息 ===")
            logger.info(f"用户ID: {fangl.id}")
            logger.info(f"用户名: {fangl.username}")
            logger.info(f"真实姓名: {fangl.real_name}")
            logger.info(f"角色: {fangl.role}")
            logger.info(f"部门: {fangl.department}")
            logger.info(f"公司: {fangl.company_name}")
            logger.info(f"是否激活: {fangl.is_active}")
            
            return fangl
            
        except Exception as e:
            logger.error(f"检查fangl用户信息时发生错误: {str(e)}")
            return None

def check_fangl_affiliations(fangl):
    """检查fangl用户的归属关系"""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("\n=== fangl用户归属关系 ===")
            
            # 检查fangl作为viewer的归属关系（可以查看谁的数据）
            as_viewer = Affiliation.query.filter_by(viewer_id=fangl.id).all()
            logger.info(f"fangl可以查看的用户数量: {len(as_viewer)}")
            
            for affiliation in as_viewer:
                owner = User.query.get(affiliation.owner_id)
                if owner:
                    logger.info(f"  可查看用户: {owner.username} ({owner.real_name}) - 部门: {owner.department}")
                else:
                    logger.info(f"  可查看用户ID: {affiliation.owner_id} (用户不存在)")
            
            # 检查fangl作为owner的归属关系（谁可以查看fangl的数据）
            as_owner = Affiliation.query.filter_by(owner_id=fangl.id).all()
            logger.info(f"\n可以查看fangl数据的用户数量: {len(as_owner)}")
            
            for affiliation in as_owner:
                viewer = User.query.get(affiliation.viewer_id)
                if viewer:
                    logger.info(f"  查看者: {viewer.username} ({viewer.real_name}) - 部门: {viewer.department}")
                else:
                    logger.info(f"  查看者ID: {affiliation.viewer_id} (用户不存在)")
            
            return as_viewer
            
        except Exception as e:
            logger.error(f"检查fangl归属关系时发生错误: {str(e)}")
            return []

def check_fangl_project_access(fangl):
    """检查fangl可以访问的项目"""
    
    try:
        logger.info("\n=== fangl项目访问权限分析 ===")
        
        # 使用access_control模块获取可查看的项目
        viewable_projects = get_viewable_data(Project, fangl)
        total_count = viewable_projects.count()
        
        logger.info(f"fangl可以查看的项目总数: {total_count}")
        
        # 分析前10个项目的详情
        sample_projects = viewable_projects.limit(10).all()
        logger.info(f"\n前10个项目详情:")
        
        for project in sample_projects:
            owner = User.query.get(project.owner_id) if project.owner_id else None
            vendor_sales = User.query.get(project.vendor_sales_manager_id) if hasattr(project, 'vendor_sales_manager_id') and project.vendor_sales_manager_id else None
            
            logger.info(f"  项目ID: {project.id}")
            logger.info(f"    项目名称: {project.project_name}")
            logger.info(f"    项目类型: {project.project_type}")
            logger.info(f"    创建者: {owner.username if owner else 'N/A'} ({owner.department if owner else 'N/A'})")
            logger.info(f"    厂商销售: {vendor_sales.username if vendor_sales else 'N/A'}")
            logger.info(f"    创建时间: {project.created_at}")
            print()
        
        # 统计按部门分布
        logger.info("按创建者部门统计:")
        dept_stats = {}
        for project in viewable_projects.all():
            owner = User.query.get(project.owner_id) if project.owner_id else None
            dept = owner.department if owner else '未知'
            dept_stats[dept] = dept_stats.get(dept, 0) + 1
        
        for dept, count in dept_stats.items():
            logger.info(f"  {dept}: {count}个项目")
        
        return total_count
        
    except Exception as e:
        logger.error(f"检查fangl项目访问权限时发生错误: {str(e)}")
        return 0

def check_fangl_customer_access(fangl):
    """检查fangl可以访问的客户"""
    
    try:
        logger.info("\n=== fangl客户访问权限分析 ===")
        
        # 使用access_control模块获取可查看的客户
        viewable_companies = get_viewable_data(Company, fangl)
        total_count = viewable_companies.count()
        
        logger.info(f"fangl可以查看的客户总数: {total_count}")
        
        # 分析前10个客户的详情
        sample_companies = viewable_companies.limit(10).all()
        logger.info(f"\n前10个客户详情:")
        
        for company in sample_companies:
            owner = User.query.get(company.owner_id) if company.owner_id else None
            
            logger.info(f"  客户ID: {company.id}")
            logger.info(f"    客户名称: {company.company_name}")
            logger.info(f"    创建者: {owner.username if owner else 'N/A'} ({owner.department if owner else 'N/A'})")
            logger.info(f"    创建时间: {company.created_at}")
            print()
        
        # 统计按部门分布
        logger.info("按创建者部门统计:")
        dept_stats = {}
        for company in viewable_companies.all():
            owner = User.query.get(company.owner_id) if company.owner_id else None
            dept = owner.department if owner else '未知'
            dept_stats[dept] = dept_stats.get(dept, 0) + 1
        
        for dept, count in dept_stats.items():
            logger.info(f"  {dept}: {count}个客户")
        
        return total_count
        
    except Exception as e:
        logger.error(f"检查fangl客户访问权限时发生错误: {str(e)}")
        return 0

def analyze_access_control_logic(fangl):
    """分析access_control.py中对服务部角色的处理逻辑"""
    
    logger.info("\n=== 访问控制逻辑分析 ===")
    
    user_role = fangl.role.strip() if fangl.role else ''
    logger.info(f"fangl角色 (去除空格): '{user_role}'")
    
    # 检查是否匹配特殊角色处理
    if user_role in ['service', 'service_manager']:
        logger.info("✅ fangl匹配服务经理角色处理逻辑")
        logger.info("根据access_control.py逻辑:")
        logger.info("  项目权限: 可以查看所有'业务机会'项目 + 自己的项目 + 自己作为销售负责人的项目")
        logger.info("  客户权限: 只能查看自己的客户信息和授权的客户信息(通过归属关系)")
    else:
        logger.info("❌ fangl不匹配服务经理角色，使用默认逻辑")
        logger.info("默认逻辑: 直接归属 + 归属链")

def check_same_department_users(fangl):
    """检查同部门用户"""
    
    try:
        logger.info("\n=== 同部门用户检查 ===")
        
        if fangl.department:
            same_dept_users = User.query.filter(
                User.department == fangl.department,
                User.id != fangl.id  # 排除自己
            ).all()
            
            logger.info(f"同部门({fangl.department})其他用户数量: {len(same_dept_users)}")
            
            for user in same_dept_users[:10]:  # 显示前10个
                logger.info(f"  {user.username} ({user.real_name}) - 角色: {user.role}")
        else:
            logger.info("fangl没有设置部门信息")
            
    except Exception as e:
        logger.error(f"检查同部门用户时发生错误: {str(e)}")

def main():
    """主函数"""
    print("=== fangl用户权限诊断工具 ===")
    print()
    
    # 1. 检查用户基本信息
    fangl = check_fangl_user()
    if not fangl:
        print("❌ 无法获取fangl用户信息，退出")
        return
    
    # 2. 检查归属关系
    affiliations = check_fangl_affiliations(fangl)
    
    # 3. 分析访问控制逻辑
    analyze_access_control_logic(fangl)
    
    # 4. 检查同部门用户
    check_same_department_users(fangl)
    
    # 5. 检查项目访问权限
    project_count = check_fangl_project_access(fangl)
    
    # 6. 检查客户访问权限
    customer_count = check_fangl_customer_access(fangl)
    
    print("\n=== 诊断总结 ===")
    print(f"fangl可查看项目数: {project_count}")
    print(f"fangl可查看客户数: {customer_count}")
    print(f"fangl归属关系数: {len(affiliations)}")
    
    if project_count > 100 or customer_count > 50:  # 假设的阈值
        print("⚠️  fangl可能有过多的数据访问权限，建议检查:")
        print("   1. 归属关系是否正确配置")
        print("   2. 角色权限设置是否合理")
        print("   3. 是否有多余的权限授权")
    else:
        print("✅ fangl的数据访问权限看起来正常")

if __name__ == '__main__':
    main() 