#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
客户管理权限控制分析脚本

用于检查和分析：
1. get_viewable_data(Company, current_user) 方法的实现
2. 数据过滤规则（权限级别、软删除、状态过滤）
3. 当前用户的权限级别和数据访问范围
4. 65个客户是否是正确的权限范围内的数量
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.customer import Company
from app.utils.access_control import get_viewable_data
from flask_login import current_user
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_customer_access_control():
    """分析客户管理中的权限控制逻辑"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=" * 80)
            print("客户管理权限控制分析报告")
            print("=" * 80)
            
            # 获取当前登录的用户（假设是fangl用户）
            fangl = User.query.filter_by(username='fangl').first()
            if not fangl:
                print("❌ 找不到用户 'fangl'")
                return
            
            print(f"📋 分析用户: {fangl.username} ({fangl.real_name})")
            print(f"🏷️  用户角色: {fangl.role}")
            print(f"🏢 所属公司: {fangl.company_name}")
            print(f"🏬 所属部门: {fangl.department}")
            print(f"🆔 用户ID: {fangl.id}")
            print()
            
            # 1. 检查用户在客户模块的权限
            print("🔐 1. 客户模块权限检查")
            print("-" * 40)
            
            has_customer_view_permission = fangl.has_permission('customer', 'view')
            print(f"客户查看权限: {'✅ 有' if has_customer_view_permission else '❌ 无'}")
            
            if has_customer_view_permission:
                permission_level = fangl.get_permission_level('customer')
                print(f"权限级别: {permission_level}")
                print(f"权限级别说明:")
                print(f"  - system: 系统级权限，可查看所有客户")
                print(f"  - company: 企业级权限，可查看企业下所有客户")
                print(f"  - department: 部门级权限，可查看部门下所有客户")
                print(f"  - personal: 个人级权限，只能查看自己和归属关系的客户")
            else:
                print("❌ 用户没有客户查看权限，将返回空查询")
                return
            print()
            
            # 2. 分析 get_viewable_data 的实际过滤逻辑
            print("🔍 2. get_viewable_data 过滤逻辑分析")
            print("-" * 40)
            
            # 获取原始查询
            viewable_query = get_viewable_data(Company, fangl)
            print(f"构建的查询对象: {type(viewable_query)}")
            
            # 3. 检查数据库中的总客户数量
            print("\n📊 3. 数据库客户数据统计")
            print("-" * 40)
            
            total_companies = Company.query.count()
            print(f"数据库总客户数: {total_companies}")
            
            active_companies = Company.query.filter(Company.is_deleted == False).count()
            print(f"未删除客户数: {active_companies}")
            
            deleted_companies = Company.query.filter(Company.is_deleted == True).count()
            print(f"已删除客户数: {deleted_companies}")
            
            # 4. 分析权限过滤后的结果
            print("\n🎯 4. 权限过滤结果分析")
            print("-" * 40)
            
            viewable_companies = viewable_query.all()
            viewable_count = len(viewable_companies)
            print(f"用户可见客户总数: {viewable_count}")
            
            # 按拥有者分组统计
            owner_stats = {}
            for company in viewable_companies:
                owner_id = company.owner_id
                if owner_id not in owner_stats:
                    owner = User.query.get(owner_id)
                    owner_name = owner.real_name if owner and owner.real_name else (owner.username if owner else f"用户ID:{owner_id}")
                    owner_stats[owner_id] = {
                        'name': owner_name,
                        'count': 0,
                        'companies': []
                    }
                owner_stats[owner_id]['count'] += 1
                owner_stats[owner_id]['companies'].append(company.company_name)
            
            print(f"\n按拥有者统计:")
            for owner_id, stats in owner_stats.items():
                print(f"  {stats['name']}: {stats['count']} 个客户")
                if stats['count'] <= 5:  # 只显示5个以下的详细列表
                    for company_name in stats['companies']:
                        print(f"    - {company_name}")
                elif stats['count'] <= 10:
                    print(f"    包含: {', '.join(stats['companies'][:3])} ... 等")
                
            # 5. 检查软删除过滤
            print(f"\n🗑️  5. 软删除过滤检查")
            print("-" * 40)
            
            deleted_in_viewable = [c for c in viewable_companies if c.is_deleted]
            print(f"可见客户中已删除的数量: {len(deleted_in_viewable)}")
            if deleted_in_viewable:
                print("⚠️  警告：发现已删除的客户在可见列表中")
                for company in deleted_in_viewable:
                    print(f"  - {company.company_name} (ID: {company.id})")
            else:
                print("✅ 已正确过滤已删除的客户")
            
            # 6. 检查状态过滤
            print(f"\n📊 6. 客户状态分布")
            print("-" * 40)
            
            status_stats = {}
            for company in viewable_companies:
                status = company.status or '未设置'
                status_stats[status] = status_stats.get(status, 0) + 1
            
            for status, count in status_stats.items():
                print(f"  {status}: {count} 个")
            
            # 7. 权限级别具体分析
            print(f"\n🔬 7. 权限级别具体分析")
            print("-" * 40)
            
            if permission_level == 'system':
                print("✅ 系统级权限：应该能看到所有未删除的客户")
                expected_count = active_companies
                print(f"预期可见数量: {expected_count}")
                if viewable_count == expected_count:
                    print("✅ 权限控制正常")
                else:
                    print(f"⚠️  实际可见数量({viewable_count})与预期({expected_count})不符")
                    
            elif permission_level == 'company' and fangl.company_name:
                print(f"🏢 企业级权限：应该能看到 '{fangl.company_name}' 企业下所有用户的客户")
                
                # 获取同企业用户
                company_users = User.query.filter_by(company_name=fangl.company_name).all()
                company_user_ids = [u.id for u in company_users]
                print(f"同企业用户数: {len(company_users)}")
                print(f"同企业用户: {[u.username for u in company_users]}")
                
                # 计算应该可见的客户数量
                expected_companies = Company.query.filter(
                    Company.owner_id.in_(company_user_ids),
                    Company.is_deleted == False
                ).all()
                expected_count = len(expected_companies)
                print(f"预期可见数量: {expected_count}")
                
                if viewable_count == expected_count:
                    print("✅ 企业级权限控制正常")
                else:
                    print(f"⚠️  实际可见数量({viewable_count})与预期({expected_count})不符")
                    
            elif permission_level == 'department' and fangl.department and fangl.company_name:
                print(f"🏬 部门级权限：应该能看到 '{fangl.company_name}' 企业 '{fangl.department}' 部门下所有用户的客户")
                
                # 获取同部门用户
                dept_users = User.query.filter(
                    User.department == fangl.department,
                    User.company_name == fangl.company_name
                ).all()
                dept_user_ids = [u.id for u in dept_users]
                print(f"同部门用户数: {len(dept_users)}")
                print(f"同部门用户: {[u.username for u in dept_users]}")
                
                # 计算应该可见的客户数量
                expected_companies = Company.query.filter(
                    Company.owner_id.in_(dept_user_ids),
                    Company.is_deleted == False
                ).all()
                expected_count = len(expected_companies)
                print(f"预期可见数量: {expected_count}")
                
                if viewable_count == expected_count:
                    print("✅ 部门级权限控制正常")
                else:
                    print(f"⚠️  实际可见数量({viewable_count})与预期({expected_count})不符")
                    
            else:
                print("🔒 个人级权限：只能看到自己和归属关系的客户")
                
                # 个人拥有的客户
                personal_companies = Company.query.filter(
                    Company.owner_id == fangl.id,
                    Company.is_deleted == False
                ).count()
                print(f"个人拥有的客户: {personal_companies}")
                
                # 归属关系客户
                from app.models.user import Affiliation
                affiliations = Affiliation.query.filter_by(viewer_id=fangl.id).all()
                affiliation_owner_ids = [aff.owner_id for aff in affiliations]
                print(f"归属关系用户: {len(affiliation_owner_ids)}")
                
                if affiliation_owner_ids:
                    affiliation_companies = Company.query.filter(
                        Company.owner_id.in_(affiliation_owner_ids),
                        Company.is_deleted == False
                    ).count()
                    print(f"归属关系客户: {affiliation_companies}")
                else:
                    affiliation_companies = 0
                    print(f"归属关系客户: 0")
                
                # 部门负责人权限
                is_dept_manager = getattr(fangl, 'is_department_manager', False)
                dept_manager_companies = 0
                if is_dept_manager and fangl.department:
                    dept_users = User.query.filter_by(department=fangl.department).all()
                    dept_user_ids = [u.id for u in dept_users]
                    dept_manager_companies = Company.query.filter(
                        Company.owner_id.in_(dept_user_ids),
                        Company.is_deleted == False
                    ).count()
                    print(f"部门负责人权限客户: {dept_manager_companies}")
                
                # 商务助理特殊权限
                user_role = fangl.role.strip() if fangl.role else ''
                business_admin_companies = 0
                if user_role == 'business_admin' and fangl.department and fangl.company_name:
                    ba_dept_users = User.query.filter(
                        User.department == fangl.department,
                        User.company_name == fangl.company_name
                    ).all()
                    ba_dept_user_ids = [u.id for u in ba_dept_users]
                    business_admin_companies = Company.query.filter(
                        Company.owner_id.in_(ba_dept_user_ids),
                        Company.is_deleted == False
                    ).count()
                    print(f"商务助理部门权限客户: {business_admin_companies}")
                
                expected_count = personal_companies + affiliation_companies + dept_manager_companies + business_admin_companies
                print(f"预期可见数量: {expected_count}")
                
                if viewable_count == expected_count:
                    print("✅ 个人级权限控制正常")
                else:
                    print(f"⚠️  实际可见数量({viewable_count})与预期({expected_count})不符")
            
            # 8. 结论
            print(f"\n📝 8. 分析结论")
            print("-" * 40)
            
            print(f"✅ 用户 {fangl.username} 在客户模块有 {permission_level} 级权限")
            print(f"✅ 权限过滤后可见客户数量: {viewable_count}")
            print(f"✅ 已正确过滤软删除数据: {'是' if len(deleted_in_viewable) == 0 else '否'}")
            
            if viewable_count == 65:
                print(f"✅ 确认65个客户是当前用户权限范围内的正确数量")
            else:
                print(f"⚠️  当前实际可见客户数量为 {viewable_count}，不是65个")
                print(f"需要进一步检查统计计算逻辑是否有问题")
            
        except Exception as e:
            print(f"❌ 分析过程中发生错误: {str(e)}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    analyze_customer_access_control()