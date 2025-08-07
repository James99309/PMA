#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试绩效看板视图错误
"""

import sys
import os
import traceback

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.user import User
from app.views.performance import performance_bp
from flask import request

def debug_performance_view():
    app = create_app()
    
    with app.app_context():
        try:
            # 模拟登录用户
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                print("❌ 找不到admin用户")
                return
                
            print(f"✅ admin用户: {admin_user.username}")
            
            # 模拟请求绩效看板首页
            with app.test_request_context('/performance/'):
                from flask_login import login_user
                login_user(admin_user)
                
                # 设置当前用户
                from flask import g
                g.user = admin_user
                
                try:
                    from app.views.performance import index
                    result = index()
                    print("✅ 绩效看板视图调用成功")
                    print(f"返回类型: {type(result)}")
                    
                    # 如果是模板响应，检查模板变量
                    if hasattr(result, 'get_data'):
                        print("📄 这是一个模板响应")
                    else:
                        print("📄 这是一个重定向或其他响应")
                        
                except Exception as view_error:
                    print(f"❌ 绩效看板视图调用失败: {view_error}")
                    print(f"错误堆栈: {traceback.format_exc()}")
            
        except Exception as e:
            print(f"❌ 调试过程出错: {e}")
            print(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_performance_view()