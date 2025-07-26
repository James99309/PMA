#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查项目筛选器用户选项获取问题的专门调试脚本
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.project import Project
from app.models.user import User
from sqlalchemy import distinct
from app.utils.access_control import get_viewable_data

def debug_project_filter_options():
    """调试项目筛选器获取不到用户选项的问题"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("调试项目筛选器用户选项获取问题")
        print("=" * 80)
        
        # 1. 基础数据检查
        print("\n1. 基础数据检查：")
        print("-" * 40)
        
        total_users = User.query.count()
        total_projects = Project.query.count()
        projects_with_owner = Project.query.filter(Project.owner_id.isnot(None)).count()
        projects_with_vendor_manager = Project.query.filter(Project.vendor_sales_manager_id.isnot(None)).count()
        
        print(f"总用户数: {total_users}")
        print(f"总项目数: {total_projects}")
        print(f"有owner_id的项目: {projects_with_owner}")
        print(f"有vendor_sales_manager_id的项目: {projects_with_vendor_manager}")
        
        # 2. User.is_active属性检查
        print("\n\n2. User.is_active属性检查：")
        print("-" * 40)
        
        # 检查不同查询方式的结果
        try:
            # 方式1: 直接使用属性（会触发@property）
            users_by_property = []
            all_users = User.query.limit(20).all()  # 限制数量避免过多输出
            for user in all_users:
                if user.is_active:
                    users_by_property.append(user)
            
            # 方式2: 使用数据库字段
            users_by_field = User.query.filter(User._is_active == True).all()
            
            # 方式3: 使用filter_by（会使用属性）
            try:
                users_by_filter_by = User.query.filter_by(is_active=True).all()
            except Exception as e:
                users_by_filter_by = []
                print(f"  filter_by(is_active=True) 查询失败: {e}")
            
            print(f"通过属性检查的活跃用户: {len(users_by_property)}")
            print(f"通过字段_is_active=True的用户: {len(users_by_field)}")
            print(f"通过filter_by的用户: {len(users_by_filter_by)}")
            
            # 显示前5个用户的详细状态
            print("\n用户状态详情（前5个）:")
            for user in all_users[:5]:
                db_active = getattr(user, '_is_active', None)
                prop_active = user.is_active
                print(f"  ID: {user.id}, 用户: {user.username}, _is_active: {db_active}, is_active属性: {prop_active}, 角色: {user.role}")
                
        except Exception as e:
            print(f"User.is_active检查出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 3. 获取一个测试用户（管理员）
        print("\n\n3. 获取测试用户：")
        print("-" * 40)
        
        # 找一个管理员用户或者活跃用户
        test_user = User.query.filter_by(role='admin').first()
        if not test_user:
            # 如果没有管理员，找第一个活跃用户
            for user in User.query.all():
                if user.is_active:
                    test_user = user
                    break
        
        if test_user:
            print(f"测试用户: {test_user.username} (ID: {test_user.id}, 角色: {test_user.role})")
            print(f"  is_active属性: {test_user.is_active}")
            print(f"  _is_active字段: {getattr(test_user, '_is_active', None)}")
        else:
            print("警告: 没有找到合适的测试用户!")
            return
        
        # 4. 模拟 _get_project_owner_options 函数
        print("\n\n4. 模拟项目拥有者选项获取：")
        print("-" * 40)
        
        try:
            print("步骤1: 调用get_viewable_data获取可见项目")
            viewable_projects_query = get_viewable_data(Project, test_user)
            viewable_projects_count = viewable_projects_query.count()
            print(f"  可见项目数: {viewable_projects_count}")
            
            print("步骤2: 筛选有owner_id的项目")
            projects_with_owner_query = viewable_projects_query.filter(Project.owner_id.isnot(None))
            projects_with_owner_count = projects_with_owner_query.count()
            print(f"  有owner_id的可见项目数: {projects_with_owner_count}")
            
            print("步骤3: 获取不同的owner_id")
            unique_owner_ids_query = projects_with_owner_query.with_entities(Project.owner_id.distinct())
            unique_owner_ids = {row[0] for row in unique_owner_ids_query.all()}
            print(f"  不同的owner_id集合: {unique_owner_ids}")
            print(f"  不同的owner_id数量: {len(unique_owner_ids)}")
            
            if unique_owner_ids:
                print("步骤4: 查询对应的用户")
                # 先查询所有相关用户，不管is_active状态
                all_owner_users = User.query.filter(User.id.in_(unique_owner_ids)).all()
                print(f"  找到的用户总数: {len(all_owner_users)}")
                
                # 显示所有用户的状态
                print("  所有拥有者用户状态：")
                active_owners = []
                for user in all_owner_users:
                    is_active_prop = user.is_active
                    is_active_field = getattr(user, '_is_active', None)
                    print(f"    ID: {user.id}, 用户: {user.username}, 真实姓名: {user.real_name}")
                    print(f"      _is_active字段: {is_active_field}, is_active属性: {is_active_prop}, 角色: {user.role}")
                    if is_active_prop:
                        active_owners.append(user)
                
                print(f"\n  活跃的拥有者用户数: {len(active_owners)}")
                
                # 尝试不同的查询方式
                print("步骤5: 尝试不同的活跃用户查询方式")
                
                # 方式A: 使用属性查询（这个可能有问题）
                try:
                    users_method_a = User.query.filter(
                        User.id.in_(unique_owner_ids),
                        User.is_active == True
                    ).all()
                    print(f"  方式A (User.is_active == True): {len(users_method_a)} 个用户")
                except Exception as e:
                    print(f"  方式A 失败: {e}")
                    users_method_a = []
                
                # 方式B: 使用字段查询
                try:
                    users_method_b = User.query.filter(
                        User.id.in_(unique_owner_ids),
                        User._is_active == True
                    ).all()
                    print(f"  方式B (User._is_active == True): {len(users_method_b)} 个用户")
                except Exception as e:
                    print(f"  方式B 失败: {e}")
                    users_method_b = []
                
                # 方式C: 手动筛选
                users_method_c = [user for user in all_owner_users if user.is_active]
                print(f"  方式C (手动筛选is_active属性): {len(users_method_c)} 个用户")
                
                # 生成选项
                if users_method_c:
                    options = [
                        {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
                        for user in users_method_c
                    ]
                    print(f"\n  最终生成的拥有者选项: {options}")
                else:
                    print(f"\n  警告: 没有活跃的拥有者用户，无法生成选项!")
            
        except Exception as e:
            print(f"模拟项目拥有者选项获取失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 5. 模拟厂商负责人选项获取
        print("\n\n5. 模拟厂商负责人选项获取：")
        print("-" * 40)
        
        try:
            print("步骤1: 获取有vendor_sales_manager_id的可见项目")
            projects_with_vendor_query = get_viewable_data(Project, test_user).filter(
                Project.vendor_sales_manager_id.isnot(None)
            )
            projects_with_vendor_count = projects_with_vendor_query.count()
            print(f"  有vendor_sales_manager_id的可见项目数: {projects_with_vendor_count}")
            
            if projects_with_vendor_count > 0:
                print("步骤2: 获取不同的vendor_sales_manager_id")
                unique_manager_ids_query = projects_with_vendor_query.with_entities(
                    Project.vendor_sales_manager_id.distinct()
                )
                unique_manager_ids = {row[0] for row in unique_manager_ids_query.all()}
                print(f"  不同的vendor_sales_manager_id集合: {unique_manager_ids}")
                print(f"  不同的vendor_sales_manager_id数量: {len(unique_manager_ids)}")
                
                if unique_manager_ids:
                    # 查询对应的用户
                    all_manager_users = User.query.filter(User.id.in_(unique_manager_ids)).all()
                    print(f"  找到的负责人用户总数: {len(all_manager_users)}")
                    
                    active_managers = [user for user in all_manager_users if user.is_active]
                    print(f"  活跃的负责人用户数: {len(active_managers)}")
                    
                    if active_managers:
                        options = [
                            {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
                            for user in active_managers
                        ]
                        print(f"  厂商负责人选项: {options}")
                    else:
                        print("  警告: 没有活跃的厂商负责人用户!")
            else:
                print("  没有找到任何有厂商负责人的项目")
                
        except Exception as e:
            print(f"模拟厂商负责人选项获取失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 6. 检查权限访问控制
        print("\n\n6. 检查get_viewable_data函数：")
        print("-" * 40)
        
        try:
            # 测试get_viewable_data是否正常工作
            all_projects_count = Project.query.count()
            viewable_projects_count = get_viewable_data(Project, test_user).count()
            
            print(f"数据库中总项目数: {all_projects_count}")
            print(f"用户可见项目数: {viewable_projects_count}")
            
            if viewable_projects_count == 0 and all_projects_count > 0:
                print("  警告: 用户无法查看任何项目，可能是权限问题!")
                print(f"  用户角色: {test_user.role}")
                print(f"  用户ID: {test_user.id}")
                
                # 检查是否有管理员权限
                if test_user.role == 'admin':
                    print("  用户是管理员，应该能看到所有项目")
                    
        except Exception as e:
            print(f"检查get_viewable_data函数失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("调试完成！")
        print("\n总结:")
        print("1. 检查User表中是否有活跃用户")
        print("2. 检查Project表中是否有owner_id和vendor_sales_manager_id数据")
        print("3. 检查User.is_active属性和数据库字段的一致性")
        print("4. 检查get_viewable_data函数是否正常工作")
        print("5. 检查SQL查询中的User.is_active条件是否有效")

if __name__ == '__main__':
    debug_project_filter_options()