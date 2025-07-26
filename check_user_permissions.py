#!/usr/bin/env python3
"""
检查当前用户的权限配置和可见客户数量
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/nijie/Documents/PMA')

# 设置必要的环境变量
os.environ['DATABASE_URL'] = 'sqlite:///app.db'
os.environ['SECRET_KEY'] = 'dev-secret-key'

try:
    from app import create_app, db
    from app.models.customer import Company
    from app.models.user import User
    from app.utils.access_control import get_viewable_data
    from sqlalchemy import func
    
    def check_user_permissions():
        """检查用户权限和可见客户数量"""
        app = create_app()
        
        with app.app_context():
            print("=" * 60)
            print("用户权限和客户数据分析")
            print("=" * 60)
            
            # 1. 检查数据库中总的客户数量
            total_companies = Company.query.filter(Company.is_deleted == False).count()
            print(f"\n1. 数据库客户统计:")
            print(f"   总客户数量（未删除）: {total_companies}")
            
            # 2. 查看所有用户的角色分布
            print(f"\n2. 用户角色分布:")
            user_roles = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
            for role, count in user_roles:
                print(f"   {role or '无角色'}: {count}个用户")
            
            # 3. 选择几个代表性用户进行测试
            test_users = []
            
            # 查找管理员
            admin = User.query.filter(User.role == 'admin').first()
            if admin:
                test_users.append(admin)
            
            # 查找销售总监
            sales_director = User.query.filter(User.role == 'sales_director').first()
            if sales_director:
                test_users.append(sales_director)
            
            # 查找普通销售
            sales_user = User.query.filter(User.role == 'sales').first()
            if sales_user:
                test_users.append(sales_user)
            
            # 查找渠道经理
            channel_manager = User.query.filter(User.role == 'channel_manager').first()
            if channel_manager:
                test_users.append(channel_manager)
            
            # 查找其他用户
            other_user = User.query.filter(~User.role.in_(['admin', 'sales_director', 'sales', 'channel_manager'])).first()
            if other_user:
                test_users.append(other_user)
            
            print(f"\n3. 用户权限分析:")
            for user in test_users:
                print(f"\n   用户: {user.username} (ID: {user.id})")
                print(f"   角色: {user.role or '未设置'}")
                print(f"   公司: {user.company_name or '未设置'}")
                print(f"   部门: {user.department or '未设置'}")
                
                try:
                    # 检查用户权限
                    has_customer_permission = user.has_permission('customer', 'view')
                    permission_level = user.get_permission_level('customer')
                    print(f"   客户查看权限: {has_customer_permission}")
                    print(f"   权限级别: {permission_level}")
                    
                    # 使用权限控制函数获取可见客户
                    viewable_query = get_viewable_data(Company, user)
                    viewable_count = viewable_query.count()
                    print(f"   可见客户数量: {viewable_count}")
                    
                    if viewable_count == 65:
                        print(f"   *** 这个用户看到的是65个客户 ***")
                        
                        # 检查这65个客户的归属分布
                        companies = viewable_query.all()
                        owner_distribution = {}
                        for company in companies:
                            owner_id = company.owner_id
                            if owner_id not in owner_distribution:
                                owner_distribution[owner_id] = 0
                            owner_distribution[owner_id] += 1
                        
                        print(f"   归属用户分布:")
                        for owner_id, count in sorted(owner_distribution.items(), key=lambda x: x[1], reverse=True):
                            owner_user = User.query.get(owner_id) if owner_id else None
                            owner_name = owner_user.username if owner_user else "未知"
                            print(f"     Owner {owner_id} ({owner_name}): {count}个客户")
                    
                    # 如果是非管理员用户且可见数量较少，分析原因
                    if user.role != 'admin' and viewable_count < total_companies:
                        print(f"   权限限制分析:")
                        if permission_level == 'personal':
                            print(f"     - 个人级权限：只能看到自己的客户和授权给自己的客户")
                            own_companies = Company.query.filter(
                                Company.is_deleted == False,
                                Company.owner_id == user.id
                            ).count()
                            print(f"     - 自己的客户数量: {own_companies}")
                            
                            # 检查归属关系
                            from app.models.user import Affiliation
                            affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
                            if affiliations:
                                print(f"     - 数据归属授权: {len(affiliations)}个")
                                for aff in affiliations:
                                    owner_user = User.query.get(aff.owner_id)
                                    owner_name = owner_user.username if owner_user else "未知"
                                    authorized_companies = Company.query.filter(
                                        Company.is_deleted == False,
                                        Company.owner_id == aff.owner_id
                                    ).count()
                                    print(f"       - 来自 {owner_name} (ID:{aff.owner_id}): {authorized_companies}个客户")
                        
                        elif permission_level == 'department':
                            print(f"     - 部门级权限：可以看到同部门同公司的所有客户")
                            if user.department and user.company_name:
                                dept_users = User.query.filter(
                                    User.department == user.department,
                                    User.company_name == user.company_name
                                ).all()
                                dept_user_ids = [u.id for u in dept_users]
                                dept_companies = Company.query.filter(
                                    Company.is_deleted == False,
                                    Company.owner_id.in_(dept_user_ids)
                                ).count()
                                print(f"       - 部门用户数: {len(dept_users)}")
                                print(f"       - 部门客户数: {dept_companies}")
                        
                        elif permission_level == 'company':
                            print(f"     - 企业级权限：可以看到同公司的所有客户")
                            if user.company_name:
                                company_users = User.query.filter_by(company_name=user.company_name).all()
                                company_user_ids = [u.id for u in company_users]
                                company_companies = Company.query.filter(
                                    Company.is_deleted == False,
                                    Company.owner_id.in_(company_user_ids)
                                ).count()
                                print(f"       - 公司用户数: {len(company_users)}")
                                print(f"       - 公司客户数: {company_companies}")
                
                except Exception as e:
                    print(f"   权限检查出错: {str(e)}")
            
            # 4. 检查客户归属分布
            print(f"\n4. 客户归属分布分析:")
            owner_stats = Company.query.filter(Company.is_deleted == False)\
                .with_entities(Company.owner_id, func.count(Company.id))\
                .group_by(Company.owner_id)\
                .order_by(func.count(Company.id).desc())\
                .all()
            
            print(f"   客户归属统计 (按数量排序):")
            for owner_id, count in owner_stats[:10]:  # 显示前10个
                owner_user = User.query.get(owner_id) if owner_id else None
                owner_name = owner_user.username if owner_user else "未知用户"
                owner_role = owner_user.role if owner_user else "未知角色"
                print(f"     Owner {owner_id} ({owner_name}, {owner_role}): {count}个客户")
            
            print(f"\n5. 可能的原因分析:")
            print(f"   如果统计数量从几百个变为65个，可能的原因包括：")
            print(f"   1. 最近启用了权限控制系统，之前可能显示所有客户")
            print(f"   2. 当前用户的权限级别被限制为个人级或部门级")
            print(f"   3. 客户数据的归属关系发生了变化")
            print(f"   4. 有大量客户被标记为已删除")
            
            # 检查已删除的客户
            deleted_count = Company.query.filter(Company.is_deleted == True).count()
            print(f"   已删除的客户数量: {deleted_count}")
            
            print(f"\n" + "=" * 60)
            print("分析完成")
            print("=" * 60)
    
    if __name__ == '__main__':
        check_user_permissions()

except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的项目目录中运行此脚本")
except Exception as e:
    print(f"运行错误: {e}")