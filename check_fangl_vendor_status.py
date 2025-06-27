#!/usr/bin/env python3
"""
检查fangl用户是否被误判为厂商用户

Created: 2025-06-27
Author: Assistant
Purpose: 调试fangl用户权限问题
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from flask import Flask
from app import create_app, db
from app.models.user import User

def check_vendor_status():
    """检查fangl用户的厂商状态"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # 找到fangl用户
            fangl = User.query.filter_by(username='fangl').first()
            if not fangl:
                print("❌ 未找到fangl用户")
                return
            
            print(f"=== fangl厂商状态检查 ===")
            print(f"用户: {fangl.username}")
            print(f"角色: '{fangl.role}'")
            print(f"公司: {fangl.company_name}")
            
            # 检查是否有is_vendor_user方法
            if hasattr(fangl, 'is_vendor_user'):
                vendor_status = fangl.is_vendor_user()
                print(f"is_vendor_user(): {vendor_status}")
            else:
                print("❌ 用户对象没有is_vendor_user方法")
            
            # 检查用户对象的所有属性
            print(f"\n=== 用户对象属性 ===")
            for attr in dir(fangl):
                if not attr.startswith('_') and not callable(getattr(fangl, attr)):
                    value = getattr(fangl, attr)
                    print(f"{attr}: {value}")
                    
        except Exception as e:
            print(f"检查过程发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_vendor_status() 