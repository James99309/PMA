#!/usr/bin/env python3
"""
调试customer_sales角色的权限逻辑是否被正确调用

Created: 2025-06-27
Author: Assistant
Purpose: 调试fangl用户客户权限问题
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from flask import Flask
from app import create_app, db
from app.models.user import User, Affiliation
from app.models.customer import Company
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_customer_permissions():
    """调试客户权限逻辑"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # 找到fangl用户
            fangl = User.query.filter_by(username='fangl').first()
            if not fangl:
                print("❌ 未找到fangl用户")
                return
            
            print(f"=== 调试fangl客户权限逻辑 ===")
            print(f"用户: {fangl.username}")
            print(f"角色: '{fangl.role}'")
            print(f"角色(去空格): '{fangl.role.strip() if fangl.role else ''}'")
            print(f"部门: {fangl.department}")
            print(f"公司: {fangl.company_name}")
            
            # 检查同部门用户
            print(f"\n=== 同部门用户检查 ===")
            if fangl.department and fangl.company_name:
                dept_users = User.query.filter(
                    User.department == fangl.department,
                    User.company_name == fangl.company_name
                ).all()
                
                print(f"同部门用户数量: {len(dept_users)}")
                for user in dept_users:
                    print(f"  用户ID: {user.id}, 用户名: {user.username}, 部门: {user.department}")
                
                # 构建权限用户ID列表
                viewable_user_ids = [fangl.id]
                viewable_user_ids.extend([u.id for u in dept_users])
                viewable_user_ids = list(set(viewable_user_ids))
                
                print(f"\n应该可见的用户ID列表: {viewable_user_ids}")
                
                # 直接查询这些用户创建的客户
                companies_by_dept_users = Company.query.filter(
                    Company.owner_id.in_(viewable_user_ids)
                ).all()
                
                print(f"\n按部门逻辑应该可见的客户数量: {len(companies_by_dept_users)}")
                
                dept_stats = {}
                for company in companies_by_dept_users:
                    owner = User.query.get(company.owner_id) if company.owner_id else None
                    dept = owner.department if owner else '未知'
                    dept_stats[dept] = dept_stats.get(dept, 0) + 1
                
                print("按创建者部门统计:")
                for dept, count in dept_stats.items():
                    print(f"  {dept}: {count}个客户")
            
            # 现在用access_control模块测试
            print(f"\n=== 使用access_control模块测试 ===")
            from app.utils.access_control import get_viewable_data
            
            # 增加详细日志
            import logging
            logging.getLogger('app.utils.access_control').setLevel(logging.DEBUG)
            
            viewable_companies = get_viewable_data(Company, fangl)
            actual_count = viewable_companies.count()
            
            print(f"access_control返回的客户数量: {actual_count}")
            
            # 分析前5个结果
            sample_companies = viewable_companies.limit(5).all()
            print(f"\n前5个客户详情:")
            
            for company in sample_companies:
                owner = User.query.get(company.owner_id) if company.owner_id else None
                print(f"  客户ID: {company.id}")
                print(f"    客户名称: {company.company_name}")
                print(f"    创建者: {owner.username if owner else 'N/A'} ({owner.department if owner else 'N/A'})")
                print()
                
        except Exception as e:
            logger.error(f"调试过程发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    debug_customer_permissions() 