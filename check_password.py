#!/usr/bin/env python3
"""
检查用户密码
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.user import User
from werkzeug.security import check_password_hash

def check_passwords():
    """检查用户密码"""
    
    app = create_app()
    
    with app.app_context():
        print("=== 用户密码检查 ===\n")
        
        # 常见密码列表
        common_passwords = ['admin123', 'admin', 'nijie123', 'nijie', '123456', 'password']
        
        # 检查admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f"admin用户存在，ID: {admin_user.id}")
            print(f"密码哈希: {admin_user.password_hash}")
            
            for pwd in common_passwords:
                if check_password_hash(admin_user.password_hash, pwd):
                    print(f"✅ admin用户密码是: {pwd}")
                    break
            else:
                print("❌ admin用户密码不在常见密码列表中")
        
        # 检查NIJIE用户
        nijie_user = User.query.filter_by(username='NIJIE').first()
        if nijie_user:
            print(f"\nNIJIE用户存在，ID: {nijie_user.id}")
            print(f"密码哈希: {nijie_user.password_hash}")
            
            for pwd in common_passwords:
                if check_password_hash(nijie_user.password_hash, pwd):
                    print(f"✅ NIJIE用户密码是: {pwd}")
                    break
            else:
                print("❌ NIJIE用户密码不在常见密码列表中")

if __name__ == "__main__":
    check_passwords() 