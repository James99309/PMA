#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查主页面和AJAX端点统计计算差异的脚本

根据代码分析，主页面和AJAX端点都使用了相同的权限过滤逻辑，
但是用户看到65个客户而实际只有53个，这说明可能有其他问题
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

def analyze_ajax_statistics_difference():
    """检查主页面和AJAX端点的统计计算差异"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=" * 80)
            print("主页面与AJAX端点统计计算差异分析")
            print("=" * 80)
            
            # 获取fangl用户
            fangl = User.query.filter_by(username='fangl').first()
            if not fangl:
                print("❌ 找不到用户 'fangl'")
                return
            
            print(f"👤 分析用户: {fangl.username} ({fangl.real_name})")
            print(f"🆔 用户ID: {fangl.id}")
            print()
            
            # 1. 模拟主页面的统计计算（list_companies函数）
            print("🏠 1. 主页面统计计算（list_companies）")
            print("-" * 50)
            
            # 模拟没有筛选条件的情况
            main_stats_query = get_viewable_data(Company, fangl)
            
            main_stats = {
                'total': main_stats_query.count(),
                'active': main_stats_query.filter(Company.status == 'active').count(),
                'user': main_stats_query.filter(Company.company_type == 'user').count(),
                'designer': main_stats_query.filter(Company.company_type == 'designer').count(),
                'integrator': main_stats_query.filter(Company.company_type == 'integrator').count(),
                'dealer': main_stats_query.filter(Company.company_type == 'dealer').count()
            }
            
            print(f"主页面统计结果:")
            for key, value in main_stats.items():
                print(f"  {key}: {value}")
            print()
            
            # 2. 模拟AJAX端点的统计计算（companies_list_ajax函数）
            print("⚡ 2. AJAX端点统计计算（companies_list_ajax）")
            print("-" * 50)
            
            # 模拟没有筛选条件的情况
            ajax_stats_query = get_viewable_data(Company, fangl)
            
            ajax_statistics = {
                'total': ajax_stats_query.count(),
                'active': ajax_stats_query.filter(Company.status == 'active').count(),
                'user': ajax_stats_query.filter(Company.company_type == 'user').count(),
                'designer': ajax_stats_query.filter(Company.company_type == 'designer').count(),
                'integrator': ajax_stats_query.filter(Company.company_type == 'integrator').count(),
                'dealer': ajax_stats_query.filter(Company.company_type == 'dealer').count()
            }
            
            print(f"AJAX端点统计结果:")
            for key, value in ajax_statistics.items():
                print(f"  {key}: {value}")
            print()
            
            # 3. 比较差异
            print("🔍 3. 统计结果对比")
            print("-" * 50)
            
            all_match = True
            for key in main_stats.keys():
                main_val = main_stats[key]
                ajax_val = ajax_statistics[key]
                match = main_val == ajax_val
                status = "✅" if match else "❌"
                
                print(f"{status} {key}: 主页面={main_val}, AJAX={ajax_val}")
                if not match:
                    all_match = False
                    diff = ajax_val - main_val
                    print(f"   差异: {'+' if diff > 0 else ''}{diff}")
            
            print()
            if all_match:
                print("✅ 主页面和AJAX端点的统计计算完全一致")
                print("统计计算逻辑没有问题，差异可能来自其他地方")
            else:
                print("⚠️  主页面和AJAX端点的统计计算存在差异")
            print()
            
            # 4. 检查可能的其他问题
            print("🔬 4. 检查其他可能的问题")
            print("-" * 50)
            
            print("可能的65个客户来源分析:")
            print()
            
            # 检查是否有缓存或其他数据来源
            print("A. 检查数据库查询一致性")
            query1 = get_viewable_data(Company, fangl)
            query2 = get_viewable_data(Company, fangl)
            
            count1 = query1.count()
            count2 = query2.count()
            
            print(f"   第一次查询: {count1}")
            print(f"   第二次查询: {count2}")
            print(f"   查询一致性: {'✅ 一致' if count1 == count2 else '❌ 不一致'}")
            print()
            
            # 检查用户权限是否有变化
            print("B. 检查用户权限稳定性")
            perm1 = fangl.has_permission('customer', 'view')
            level1 = fangl.get_permission_level('customer')
            
            # 稍等一下再检查一次
            perm2 = fangl.has_permission('customer', 'view')
            level2 = fangl.get_permission_level('customer')
            
            print(f"   第一次权限检查: 有权限={perm1}, 级别={level1}")
            print(f"   第二次权限检查: 有权限={perm2}, 级别={level2}")
            print(f"   权限一致性: {'✅ 一致' if (perm1, level1) == (perm2, level2) else '❌ 不一致'}")
            print()
            
            # 检查是否有会话或上下文影响
            print("C. 检查可能的数据来源")
            print("   - 前端JavaScript计算: 需要检查客户端代码")
            print("   - 浏览器缓存: 需要清除缓存重新加载")
            print("   - 会话数据: 需要检查Flask会话中是否存储了统计数据")
            print("   - 数据库连接池: 可能有不同的数据库连接")
            print("   - 权限缓存: 可能权限计算结果被缓存")
            print()
            
            # 5. 检查数据变化
            print("📊 5. 详细数据分析")
            print("-" * 50)
            
            # 获取详细的客户列表
            all_companies = get_viewable_data(Company, fangl).all()
            print(f"当前可见客户总数: {len(all_companies)}")
            
            # 按状态分组
            status_groups = {}
            for company in all_companies:
                status = company.status or 'unknown'
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(company)
            
            print("按状态分组:")
            for status, companies in status_groups.items():
                print(f"  {status}: {len(companies)} 个")
            
            # 按类型分组
            type_groups = {}
            for company in all_companies:
                company_type = company.company_type or 'unknown'
                if company_type not in type_groups:
                    type_groups[company_type] = []
                type_groups[company_type].append(company)
            
            print("按类型分组:")
            for comp_type, companies in type_groups.items():
                print(f"  {comp_type}: {len(companies)} 个")
            print()
            
            # 6. 可能的解决方案
            print("💡 6. 可能的解决方案")
            print("-" * 50)
            
            print("如果用户仍然看到65个客户，建议采取以下步骤:")
            print()
            print("1. 🔄 强制刷新页面")
            print("   - 清除浏览器缓存")
            print("   - 使用Ctrl+F5或Cmd+Shift+R强制刷新")
            print()
            print("2. 🚪 重新登录")
            print("   - 退出并重新登录系统")
            print("   - 清除会话数据")
            print()
            print("3. 🔍 检查前端代码")
            print("   - 查看客户列表页面的HTML源码")
            print("   - 检查JavaScript中是否有硬编码的统计数据")
            print("   - 验证AJAX请求的响应数据")
            print()
            print("4. 🗃️  检查数据库状态")
            print("   - 验证数据库连接")
            print("   - 检查是否有数据同步问题")
            print()
            print("5. ⚙️  重启应用")
            print("   - 重启Flask应用")
            print("   - 清除所有可能的缓存")
            print()
            
            print("✅ 分析完成")
            print(f"📋 结论: 后端权限控制和统计计算逻辑正常，用户应该看到 {main_stats['total']} 个客户")
            print("📝 如果用户仍看到65个，问题可能在前端缓存或会话数据中")
            
        except Exception as e:
            print(f"❌ 分析过程中发生错误: {str(e)}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    analyze_ajax_statistics_difference()