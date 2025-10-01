#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建测试用户脚本
"""
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash
import time

def create_test_users():
    """创建测试用户"""
    print("开始创建测试用户...")
    
    # 先检查是否已有测试用户
    test_users = User.query.filter(User.username.like('test%')).all()
    if test_users:
        print(f"已存在 {len(test_users)} 个测试用户:")
        for user in test_users:
            print(f"  ID: {user.id}, 用户名: {user.username}, 姓名: {user.real_name}")
        return test_users
    
    # 创建测试用户
    users_to_create = [
        {
            'username': 'test1',
            'real_name': '测试用户1',
            'email': 'test1@example.com',
            'role': 'user',
            'is_active': True,
            'department': '测试部门',
            'company_name': '测试公司',
            'is_department_manager': False
        },
        {
            'username': 'test2',
            'real_name': '测试用户2',
            'email': 'test2@example.com',
            'role': 'user',
            'is_active': True,
            'department': '测试部门',
            'company_name': '测试公司',
            'is_department_manager': False
        },
        {
            'username': 'test_manager',
            'real_name': '测试部门经理',
            'email': 'test_manager@example.com',
            'role': 'admin',
            'is_active': True,
            'department': '测试部门',
            'company_name': '测试公司',
            'is_department_manager': True
        }
    ]
    
    created_users = []
    for user_data in users_to_create:
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if existing_user:
            print(f"用户 {user_data['username']} 已存在，跳过")
            created_users.append(existing_user)
            continue
        
        # 创建新用户
        user = User(
            username=user_data['username'],
            password_hash=generate_password_hash('password123'),
            real_name=user_data['real_name'],
            email=user_data['email'],
            role=user_data['role'],
            is_active=user_data['is_active'],
            department=user_data['department'],
            company_name=user_data['company_name'],
            is_department_manager=user_data['is_department_manager'],
            created_at=time.time()
        )
        db.session.add(user)
        db.session.flush()  # 获取生成的ID
        created_users.append(user)
        print(f"创建用户: ID={user.id}, 用户名={user.username}, 姓名={user.real_name}")
    
    db.session.commit()
    print(f"成功创建 {len(created_users)} 个测试用户")
    return created_users

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_test_users() 