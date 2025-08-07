#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试绩效看板模板渲染问题
"""

import sys
import os
import traceback

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.user import User
from flask import render_template_string, render_template

def test_performance_template():
    app = create_app()
    
    with app.app_context():
        # 模拟登录用户
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("❌ 找不到admin用户")
            return
            
        print(f"✅ admin用户: {admin_user.username}")
        
        with app.test_request_context('/performance/'):
            from flask_login import login_user
            login_user(admin_user)
            
            # 测试简单的模板渲染
            try:
                simple_template = """
                <h1>测试页面</h1>
                {% set is_english = False %}
                {% if _ %}
                    {% set is_english = (_('搜索') == 'Search') %}
                {% endif %}
                <p>语言检测: {{ 'English' if is_english else '中文' }}</p>
                <p>翻译测试: {{ _('搜索') if _ else '翻译函数不可用' }}</p>
                """
                
                result = render_template_string(simple_template)
                print("✅ 简单模板渲染成功")
                print("模板输出:", result)
                
            except Exception as e:
                print(f"❌ 简单模板渲染失败: {e}")
                print(f"错误堆栈: {traceback.format_exc()}")
            
            # 测试实际的绩效看板模板
            try:
                print("\n开始测试实际绩效看板模板...")
                
                # 准备最小化的模板变量
                template_vars = {
                    'selected_user': admin_user,
                    'accessible_users': [admin_user],
                    'users_with_targets': [admin_user],
                    'available_years': [2025],
                    'current_year': 2025,
                    'current_month': 8,
                    'current_tab': 'overview',
                    'chart_data': {'months': [], 'implant_actual': [], 'sales_actual': []},
                    'total_actual': {'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0},
                    'total_target': {'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0},
                    'achievement_rates': {'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0},
                    'monthly_rates': {},
                    'industry_summary': {},
                    'monthly_industry_stats': {},
                    'display_currency': 'CNY',
                    'yearly_stats': [],
                    'yearly_targets': {},
                    'monthly_converted_amounts': {},
                    'list_config': None
                }
                
                result = render_template('performance/index.html', **template_vars)
                print("✅ 绩效看板模板渲染成功")
                
            except Exception as e:
                print(f"❌ 绩效看板模板渲染失败: {e}")
                print(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    test_performance_template()