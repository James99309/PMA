#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
客户统计计算逻辑检查脚本

分析客户模块的统计计算逻辑，检查为什么显示65个客户而实际权限范围内只有53个
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.customer import Company
from app.utils.access_control import get_viewable_data
from flask import request
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_customer_statistics_calculation():
    """分析客户统计计算逻辑的差异"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=" * 80)
            print("客户统计计算逻辑分析报告")
            print("=" * 80)
            
            # 获取fangl用户
            fangl = User.query.filter_by(username='fangl').first()
            if not fangl:
                print("❌ 找不到用户 'fangl'")
                return
            
            print(f"👤 分析用户: {fangl.username} ({fangl.real_name})")
            print()
            
            # 1. 模拟客户列表页面的统计计算逻辑
            print("🧮 1. 模拟客户列表页面统计计算")
            print("-" * 50)
            
            # 这里模拟 app/views/customer.py 中 list_companies 函数的统计逻辑
            # 基础查询 - 使用 get_viewable_data
            stats_query = get_viewable_data(Company, fangl)
            print(f"基础查询（get_viewable_data）返回数量: {stats_query.count()}")
            
            # 检查各项统计计算
            total_stat = stats_query.count()
            active_stat = stats_query.filter(Company.status == 'active').count()
            user_stat = stats_query.filter(Company.company_type == 'user').count()
            designer_stat = stats_query.filter(Company.company_type == 'designer').count()
            integrator_stat = stats_query.filter(Company.company_type == 'integrator').count()
            dealer_stat = stats_query.filter(Company.company_type == 'dealer').count()
            
            print(f"📊 统计结果:")
            print(f"  总计: {total_stat}")
            print(f"  活跃: {active_stat}")
            print(f"  终端用户: {user_stat}")
            print(f"  设计院: {designer_stat}")
            print(f"  集成商: {integrator_stat}")
            print(f"  经销商: {dealer_stat}")
            print()
            
            # 2. 检查下拉筛选器的数据来源
            print("📋 2. 检查下拉筛选器数据来源")
            print("-" * 50)
            
            # 模拟获取筛选器选项的逻辑
            all_viewable_companies = get_viewable_data(Company, fangl).all()
            print(f"all_viewable_companies 数量: {len(all_viewable_companies)}")
            
            # 获取用户列表用于拥有者筛选
            all_users = User.query.filter(User._is_active == True).order_by(User.real_name, User.username).all()
            unique_owner_ids = {c.owner_id for c in all_viewable_companies if c.owner_id}
            available_owners = [user for user in all_users if user.id in unique_owner_ids]
            
            print(f"活跃用户总数: {len(all_users)}")
            print(f"可见客户的拥有者ID数量: {len(unique_owner_ids)}")
            print(f"可用拥有者数量: {len(available_owners)}")
            print(f"可用拥有者: {[f'{user.real_name}({user.username})' for user in available_owners]}")
            print()
            
            # 3. 检查是否有缓存或其他数据源
            print("🔍 3. 检查可能的数据不一致来源")
            print("-" * 50)
            
            # 检查是否有其他查询方式
            direct_query = Company.query.filter(
                Company.owner_id == fangl.id,
                Company.is_deleted == False
            ).count()
            print(f"直接查询用户拥有的客户数: {direct_query}")
            
            # 检查归属关系
            from app.models.user import Affiliation
            affiliations = Affiliation.query.filter_by(viewer_id=fangl.id).all()
            print(f"归属关系数量: {len(affiliations)}")
            
            if affiliations:
                affiliation_owner_ids = [aff.owner_id for aff in affiliations]
                affiliation_companies = Company.query.filter(
                    Company.owner_id.in_(affiliation_owner_ids),
                    Company.is_deleted == False
                ).count()
                print(f"归属关系客户数: {affiliation_companies}")
            else:
                affiliation_companies = 0
                print(f"归属关系客户数: 0")
            
            total_expected = direct_query + affiliation_companies
            print(f"预期总数: {total_expected}")
            print()
            
            # 4. 检查是否有JavaScript/AJAX统计
            print("🌐 4. 检查前端AJAX统计的可能性")
            print("-" * 50)
            
            print("检查是否有客户列表的AJAX端点...")
            # 在这里我们需要查看是否有额外的AJAX端点提供统计数据
            
            print("可能的数据不一致原因:")
            print("1. 前端缓存了旧的统计数据")
            print("2. 有其他AJAX端点提供统计，使用了不同的查询逻辑")
            print("3. JavaScript客户端计算统计数据")
            print("4. 页面模板中有硬编码的统计数据")
            print("5. 浏览器会话中缓存了数据")
            print()
            
            # 5. 分析差异
            print("📈 5. 差异分析")
            print("-" * 50)
            
            reported_count = 65  # 用户看到的数量
            actual_count = total_stat  # 实际权限范围内的数量
            difference = reported_count - actual_count
            
            print(f"用户看到的数量: {reported_count}")
            print(f"实际权限范围数量: {actual_count}")
            print(f"差异: {difference}")
            
            if difference > 0:
                print(f"⚠️  用户看到的数量比实际权限范围多 {difference} 个")
                print("可能原因:")
                print("  - 前端缓存了包含更多数据的统计")
                print("  - 有其他数据源提供了额外的客户数据")
                print("  - 权限检查在某个环节被绕过")
                print("  - 统计计算使用了不同的过滤条件")
            elif difference < 0:
                print(f"⚠️  用户看到的数量比实际权限范围少 {abs(difference)} 个")
                print("可能原因:")
                print("  - 前端额外过滤了一些数据")
                print("  - 统计计算有错误")
            else:
                print("✅ 用户看到的数量与实际权限范围一致")
            print()
            
            # 6. 建议的排查步骤
            print("🔧 6. 建议的排查步骤")
            print("-" * 50)
            
            print("1. 检查客户列表页面的HTML源码，查看统计数据来源")
            print("2. 检查是否有AJAX端点提供统计数据")
            print("3. 清除浏览器缓存和会话数据")
            print("4. 检查JavaScript代码中的统计计算逻辑")
            print("5. 验证模板中的统计变量赋值")
            print("6. 检查是否有多个权限检查函数被调用")
            print()
            
            # 7. 详细检查客户记录
            print("📝 7. 详细客户记录分析")
            print("-" * 50)
            
            viewable_companies = get_viewable_data(Company, fangl).all()
            
            print("可见客户详情（前10个）:")
            for i, company in enumerate(viewable_companies[:10]):
                print(f"  {i+1}. {company.company_name} (ID: {company.id}, 拥有者: {company.owner_id}, 状态: {company.status})")
            
            if len(viewable_companies) > 10:
                print(f"  ... 还有 {len(viewable_companies) - 10} 个客户")
            
            print()
            print("✅ 分析完成")
            
        except Exception as e:
            print(f"❌ 分析过程中发生错误: {str(e)}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    analyze_customer_statistics_calculation()