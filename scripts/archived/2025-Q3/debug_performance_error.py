#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试绩效看板 NoneType 错误
"""

import sys
import os
import traceback

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.user import User
from app.models.performance import PerformanceTarget, PerformanceStatistics
from app.utils.permissions import get_accessible_users

def debug_performance_error():
    app = create_app()
    
    with app.app_context():
        try:
            # 模拟登录用户
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                print("❌ 找不到admin用户")
                return
                
            print(f"✅ admin用户: {admin_user.username}")
            
            # 模拟绩效看板的逻辑
            from datetime import datetime
            from flask import request
            
            current_year = datetime.now().year
            
            # 获取可访问的用户列表（基于权限）
            print("🔍 获取可访问用户...")
            accessible_users = get_accessible_users(admin_user, 'performance_management')
            print(f"可访问用户数: {len(accessible_users)}")
            
            # 获取有绩效目标设置的用户列表
            print("🔍 获取有绩效目标的用户...")
            users_with_targets = db.session.query(User).join(
                PerformanceTarget, User.id == PerformanceTarget.user_id
            ).filter(
                User.id.in_([u.id for u in accessible_users])
            ).distinct().all()
            print(f"有绩效目标的用户数: {len(users_with_targets)}")
            
            # 获取有绩效数据的年份列表
            print("🔍 获取可用年份...")
            available_years = db.session.query(PerformanceTarget.year).filter(
                PerformanceTarget.user_id.in_([u.id for u in accessible_users])
            ).distinct().order_by(PerformanceTarget.year.desc()).all()
            available_years = [year[0] for year in available_years]
            print(f"可用年份: {available_years}")
            
            # 确保年份数据存在，如果当年没有数据但其他年份有数据，使用最近的年份
            if current_year not in available_years and available_years:
                # 优先使用当年，如果当年没有数据则使用最近的年份
                if datetime.now().year in available_years:
                    current_year = datetime.now().year
                else:
                    current_year = available_years[0]  # 使用最近的年份
            elif not available_years:
                # 如果没有任何年份数据，使用当年
                current_year = datetime.now().year
            
            print(f"选择的年份: {current_year}")
            
            # 选择用户（默认admin用户）
            selected_user_id = admin_user.id
            selected_user = admin_user
            
            print(f"选择的用户: {selected_user.username} (ID: {selected_user_id})")
            
            # 获取年度统计数据
            print("🔍 获取年度统计数据...")
            from app.services.performance_service import PerformanceService
            yearly_stats = PerformanceService.get_yearly_statistics(selected_user_id, current_year)
            print(f"年度统计数据: {len(yearly_stats) if yearly_stats else 0} 条记录")
            
            # 获取年度目标数据
            print("🔍 获取年度目标数据...")
            yearly_targets = {}
            for month in range(1, 13):
                target = PerformanceTarget.query.filter_by(
                    user_id=selected_user_id, year=current_year, month=month
                ).first()
                yearly_targets[month] = target
            
            target_count = len([t for t in yearly_targets.values() if t])
            print(f"年度目标数据: {target_count} 个月有目标")
            
            # 测试数据转换函数
            print("🔍 测试数据转换函数...")
            from app.utils.dictionary_helpers import prepare_stats_card_amount
            from app.utils.i18n import get_current_language
            
            current_language = get_current_language()
            print(f"当前语言: {current_language}")
            
            # 测试转换函数
            test_result = prepare_stats_card_amount(100000, current_language)
            print(f"测试转换结果: {test_result}")
            print(f"转换结果类型: {type(test_result)}")
            
            # 检查是否有数据导致NoneType错误
            for month in range(1, 13):
                stats = yearly_stats[month - 1] if yearly_stats and len(yearly_stats) > month - 1 else None
                target = yearly_targets.get(month)
                
                if stats:
                    print(f"\\n📊 处理 {month}月 数据...")
                    implant_actual_cny = float(stats.implant_amount_actual or 0)
                    sales_actual_cny = float(stats.sales_amount_actual or 0)
                    
                    print(f"  原始值: implant={implant_actual_cny}, sales={sales_actual_cny}")
                    
                    try:
                        # 测试转换函数
                        implant_converted = prepare_stats_card_amount(implant_actual_cny, current_language)
                        sales_converted = prepare_stats_card_amount(sales_actual_cny, current_language)
                        
                        print(f"  转换后: implant={implant_converted}, sales={sales_converted}")
                        
                        if implant_converted is None or sales_converted is None:
                            print(f"  ❌ 发现 None 值!")
                            
                    except Exception as convert_error:
                        print(f"  ❌ 转换异常: {convert_error}")
                        print(f"  异常堆栈: {traceback.format_exc()}")
            
            print("✅ 绩效看板调试完成")
            
        except Exception as e:
            print(f"❌ 调试过程出错: {e}")
            print(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_performance_error()