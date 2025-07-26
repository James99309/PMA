#!/usr/bin/env python3
"""
调试客户列表统计卡片数据不一致问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Company, User
from app.utils.access_control import get_viewable_data
from flask_login import login_user

app = create_app()

def debug_customer_stats():
    """调试客户统计数据"""
    with app.app_context():
        print("=" * 60)
        print("调试客户列表统计卡片数据不一致问题")
        print("=" * 60)
        
        # 查找 lihuawei 用户
        lihuawei_user = User.query.filter_by(username='lihuawei').first()
        admin_users = User.query.filter_by(role='admin').all()
        
        print(f"\n1. 用户信息:")
        if lihuawei_user:
            print(f"   - lihuawei 用户: ID={lihuawei_user.id}, 角色={lihuawei_user.role}")
        else:
            print("   - 未找到 lihuawei 用户")
        
        print(f"   - 管理员用户数量: {len(admin_users)}")
        for admin in admin_users:
            print(f"     * {admin.username} (ID: {admin.id})")
        
        print(f"\n2. 全部客户统计:")
        all_companies = Company.query.filter(Company.is_deleted == False).all()
        print(f"   - 全部客户总数: {len(all_companies)}")
        
        # 按owner_id分组统计
        owner_stats = {}
        for company in all_companies:
            owner_id = company.owner_id or 'None'
            if owner_id not in owner_stats:
                owner_stats[owner_id] = 0
            owner_stats[owner_id] += 1
        
        print(f"   - 按拥有者分组统计:")
        for owner_id, count in sorted(owner_stats.items()):
            if owner_id == 'None':
                print(f"     * 无拥有者: {count} 家")
            else:
                user = User.query.get(owner_id)
                username = user.username if user else f"未知用户(ID:{owner_id})"
                print(f"     * {username}: {count} 家")
        
        print(f"\n3. 测试管理员权限查询:")
        if admin_users:
            test_admin = admin_users[0]  # 使用第一个管理员
            print(f"   使用管理员: {test_admin.username} (ID: {test_admin.id})")
            
            # 模拟登录上下文
            with app.test_request_context():
                # 使用 get_viewable_data 查询
                viewable_query = get_viewable_data(Company, test_admin)
                viewable_companies = viewable_query.all()
                
                print(f"   - get_viewable_data 返回数量: {len(viewable_companies)}")
                
                # 模拟统计计算（类似后端代码）
                stats_query = get_viewable_data(Company, test_admin)
                
                total_count = stats_query.count()
                active_count = stats_query.filter(Company.status == 'active').count()
                user_count = stats_query.filter(Company.company_type == 'user').count()
                designer_count = stats_query.filter(Company.company_type == 'designer').count()
                integrator_count = stats_query.filter(Company.company_type == 'integrator').count()
                dealer_count = stats_query.filter(Company.company_type == 'dealer').count()
                
                print(f"   - 统计结果:")
                print(f"     * 总数: {total_count}")
                print(f"     * 活跃: {active_count}")
                print(f"     * 用户: {user_count}")
                print(f"     * 设计师: {designer_count}")
                print(f"     * 集成商: {integrator_count}")
                print(f"     * 经销商: {dealer_count}")
                
                # 检查是否有owner_id筛选被意外应用
                print(f"\n4. 检查意外的owner_id筛选:")
                if lihuawei_user:
                    lihuawei_companies = stats_query.filter(Company.owner_id == lihuawei_user.id).all()
                    print(f"   - lihuawei拥有的客户数: {len(lihuawei_companies)}")
                    
                    # 检查查询是否被意外限制到lihuawei的数据
                    if total_count == len(lihuawei_companies):
                        print(f"   ⚠️  警告: 管理员查询结果数量等于lihuawei拥有的客户数！")
                        print(f"   这可能表示get_viewable_data函数存在问题")
                        
                        # 检查原始SQL查询
                        print(f"\n5. 检查SQL查询:")
                        print(f"   原始查询: {stats_query}")
                        print(f"   查询过滤条件: {stats_query.whereclause}")
        
        print(f"\n6. 检查数据库中的实际分布:")
        company_types = db.session.query(Company.company_type, db.func.count(Company.id)).filter(
            Company.is_deleted == False
        ).group_by(Company.company_type).all()
        
        print(f"   - 按类型分布:")
        for company_type, count in company_types:
            print(f"     * {company_type or '无类型'}: {count} 家")
        
        statuses = db.session.query(Company.status, db.func.count(Company.id)).filter(
            Company.is_deleted == False
        ).group_by(Company.status).all()
        
        print(f"   - 按状态分布:")
        for status, count in statuses:
            print(f"     * {status or '无状态'}: {count} 家")

if __name__ == '__main__':
    debug_customer_stats()