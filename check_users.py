#!/usr/bin/env python3
"""
检查用户表，特别是NIJIE用户
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User

def check_users():
    """检查用户表"""
    
    app = create_app()
    
    with app.app_context():
        print("=== 用户表检查 ===\n")
        
        # 1. 查找所有用户
        all_users = User.query.all()
        print(f"总用户数: {len(all_users)}")
        
        # 2. 查找包含"nijie"的用户（不区分大小写）
        nijie_users = User.query.filter(User.username.ilike('%nijie%')).all()
        print(f"\n包含'nijie'的用户 ({len(nijie_users)}个):")
        for user in nijie_users:
            print(f"  - 用户ID: {user.id}")
            print(f"    用户名: '{user.username}'")
            print(f"    真实姓名: '{user.real_name or '未设置'}'")
            print(f"    角色: {user.role}")
            print(f"    是否激活: {user.is_active}")
        
        # 3. 查找用户ID为6的用户
        user_6 = User.query.get(6)
        if user_6:
            print(f"\n✅ 用户ID 6:")
            print(f"   用户名: '{user_6.username}'")
            print(f"   真实姓名: '{user_6.real_name or '未设置'}'")
            print(f"   角色: {user_6.role}")
            print(f"   是否激活: {user_6.is_active}")
        else:
            print(f"\n❌ 未找到用户ID 6")
        
        # 4. 尝试不同的查询方式
        print(f"\n=== 不同查询方式测试 ===")
        
        # 精确匹配
        exact_nijie = User.query.filter_by(username='NIJIE').first()
        print(f"精确匹配'NIJIE': {'找到' if exact_nijie else '未找到'}")
        
        exact_nijie_lower = User.query.filter_by(username='nijie').first()
        print(f"精确匹配'nijie': {'找到' if exact_nijie_lower else '未找到'}")
        
        # 不区分大小写匹配
        ilike_nijie = User.query.filter(User.username.ilike('nijie')).first()
        print(f"不区分大小写匹配'nijie': {'找到' if ilike_nijie else '未找到'}")
        
        # 显示所有用户的用户名
        print(f"\n=== 所有用户列表 ===")
        for user in all_users:
            print(f"ID: {user.id}, 用户名: '{user.username}', 姓名: '{user.real_name or '未设置'}'")

if __name__ == "__main__":
    check_users() 