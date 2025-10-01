#!/usr/bin/env python3
"""
检查应用程序实际使用的数据库
"""

import os
import sys
sys.path.append('/Users/nijie/Documents/PMA')

from config import DATABASE_URL, Config
from app import create_app
from app.models.user import User
from app.models.customer import Company
from app.models.role_permissions import RolePermission

def check_actual_database():
    print(f"=== 应用程序数据库配置检查 ===")
    print(f"DATABASE_URL: {DATABASE_URL}")
    print(f"Config.SQLALCHEMY_DATABASE_URI: {Config.SQLALCHEMY_DATABASE_URI}")
    
    # 创建应用实例
    app = create_app()
    
    with app.app_context():
        try:
            # 检查用户数据
            users = User.query.all()
            print(f"\n用户总数: {len(users)}")
            for user in users:
                print(f"  {user.id}: {user.username} ({user.real_name}) - {user.role}")
            
            # 检查公司数据
            companies = Company.query.filter(Company.is_deleted == False).all()
            print(f"\n公司总数: {len(companies)}")
            for company in companies[:5]:  # 只显示前5个
                print(f"  {company.id}: {company.company_name} ({company.company_type}) - 所有者:{company.owner_id}")
            
            # 检查权限配置
            permissions = RolePermission.query.filter_by(role='user').all()
            print(f"\nuser角色权限:")
            for perm in permissions:
                print(f"  {perm.module}: view={perm.can_view}, create={perm.can_create}")
                
        except Exception as e:
            print(f"数据库连接或查询错误: {e}")

if __name__ == '__main__':
    check_actual_database()