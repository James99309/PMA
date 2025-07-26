#!/usr/bin/env python3
"""
检查客户统计数据的计算逻辑
分析为什么统计数量从几百个变为65个
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models.customer import Company
from app.models.user import User
from app.utils.access_control import get_viewable_data
from sqlalchemy import func

def check_customer_statistics():
    """检查客户统计数据"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("客户统计数据分析报告")
        print("=" * 60)
        
        # 1. 检查数据库中总的客户数量
        total_companies = Company.query.filter(Company.is_deleted == False).count()
        print(f"\n1. 数据库中总客户数量（未删除）: {total_companies}")
        
        deleted_companies = Company.query.filter(Company.is_deleted == True).count()
        print(f"   已删除的客户数量: {deleted_companies}")
        
        all_companies = Company.query.count()
        print(f"   数据库中所有客户记录: {all_companies}")
        
        # 2. 检查不同状态的客户数量
        active_count = Company.query.filter(
            Company.is_deleted == False,
            Company.status == 'active'
        ).count()
        print(f"\n2. 不同状态客户统计:")
        print(f"   活跃客户: {active_count}")
        
        # 按类型统计
        type_stats = {}
        for company_type in ['user', 'designer', 'integrator', 'dealer']:
            count = Company.query.filter(
                Company.is_deleted == False,
                Company.company_type == company_type
            ).count()
            type_stats[company_type] = count
            print(f"   {company_type}: {count}")
        
        # 3. 获取一些示例用户进行权限测试
        print(f"\n3. 用户权限分析:")
        
        # 查找一些不同角色的用户
        users_to_test = []
        
        # 查找管理员
        admin_user = User.query.filter(User.role == 'admin').first()
        if admin_user:
            users_to_test.append(admin_user)
        
        # 查找销售总监
        sales_director = User.query.filter(User.role == 'sales_director').first()
        if sales_director:
            users_to_test.append(sales_director)
        
        # 查找普通销售
        sales_user = User.query.filter(User.role == 'sales').first()
        if sales_user:
            users_to_test.append(sales_user)
        
        # 查找其他角色用户
        other_user = User.query.filter(~User.role.in_(['admin', 'sales_director', 'sales'])).first()
        if other_user:
            users_to_test.append(other_user)
        
        # 分析每个用户能看到的客户数量
        for user in users_to_test:
            print(f"\n   用户: {user.username} (ID: {user.id}, 角色: {user.role})")
            print(f"   公司: {user.company_name or '未设置'}")
            print(f"   部门: {user.department or '未设置'}")
            
            # 检查权限级别
            try:
                permission_level = user.get_permission_level('customer')
                has_permission = user.has_permission('customer', 'view')
                print(f"   客户模块权限级别: {permission_level}")
                print(f"   是否有查看权限: {has_permission}")
            except Exception as e:
                print(f"   权限检查出错: {str(e)}")
                continue
            
            # 使用权限控制函数获取可见客户数量
            try:
                viewable_query = get_viewable_data(Company, user)
                viewable_count = viewable_query.count()
                print(f"   可见客户数量: {viewable_count}")
                
                # 获取一些示例客户
                sample_companies = viewable_query.limit(3).all()
                if sample_companies:
                    print(f"   示例客户:")
                    for company in sample_companies:
                        print(f"     - {company.company_name} (owner_id: {company.owner_id})")
                
            except Exception as e:
                print(f"   获取可见客户出错: {str(e)}")
        
        # 4. 检查owner_id分布
        print(f"\n4. 客户归属分析:")
        
        # 统计不同owner_id的客户数量
        owner_stats = Company.query.filter(Company.is_deleted == False)\
            .with_entities(Company.owner_id, func.count(Company.id))\
            .group_by(Company.owner_id)\
            .order_by(func.count(Company.id).desc())\
            .limit(10).all()
        
        print("   客户数量最多的前10个owner_id:")
        for owner_id, count in owner_stats:
            owner_user = User.query.get(owner_id) if owner_id else None
            owner_name = owner_user.username if owner_user else "未知用户"
            print(f"     Owner {owner_id} ({owner_name}): {count}个客户")
        
        # 5. 检查是否有客户没有owner_id
        no_owner_count = Company.query.filter(
            Company.is_deleted == False,
            Company.owner_id.is_(None)
        ).count()
        print(f"\n   没有归属用户的客户数量: {no_owner_count}")
        
        # 6. 模拟客户列表视图的统计计算
        print(f"\n5. 模拟客户列表统计计算:")
        
        # 假设当前用户是销售总监或普通用户
        test_user = sales_director or sales_user or other_user
        if test_user:
            print(f"   模拟用户: {test_user.username} ({test_user.role})")
            
            try:
                # 模拟客户列表中的统计计算逻辑
                stats_query = get_viewable_data(Company, test_user)
                
                stats = {
                    'total': stats_query.count(),
                    'active': stats_query.filter(Company.status == 'active').count(),
                    'user': stats_query.filter(Company.company_type == 'user').count(),
                    'designer': stats_query.filter(Company.company_type == 'designer').count(),
                    'integrator': stats_query.filter(Company.company_type == 'integrator').count(),
                    'dealer': stats_query.filter(Company.company_type == 'dealer').count()
                }
                
                print(f"   模拟统计结果:")
                for key, value in stats.items():
                    print(f"     {key}: {value}")
                
                # 如果总数是65，检查具体是哪些客户
                if stats['total'] == 65:
                    print(f"\n   这65个可见客户的详细信息:")
                    visible_companies = stats_query.limit(65).all()
                    owner_distribution = {}
                    for company in visible_companies:
                        owner_id = company.owner_id
                        if owner_id not in owner_distribution:
                            owner_distribution[owner_id] = 0
                        owner_distribution[owner_id] += 1
                    
                    print(f"   按归属用户分布:")
                    for owner_id, count in sorted(owner_distribution.items(), key=lambda x: x[1], reverse=True):
                        owner_user = User.query.get(owner_id) if owner_id else None
                        owner_name = owner_user.username if owner_user else "未知用户"
                        print(f"     Owner {owner_id} ({owner_name}): {count}个客户")
                
            except Exception as e:
                print(f"   模拟统计计算出错: {str(e)}")
        
        print(f"\n" + "=" * 60)
        print("分析完成")
        print("=" * 60)

if __name__ == '__main__':
    check_customer_statistics()