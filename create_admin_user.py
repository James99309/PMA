#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员账户
用于在新数据库环境中确保至少有一个超级管理员账户
"""

import os
import sys
import logging
import argparse
from sqlalchemy import create_engine, text, MetaData, Table
from werkzeug.security import generate_password_hash
from datetime import datetime
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('创建管理员')

def fix_database_url(database_url):
    """修正数据库URL格式"""
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # 添加SSL参数
    if '?' not in database_url:
        database_url += '?sslmode=require'
    elif 'sslmode=' not in database_url:
        database_url += '&sslmode=require'
        
    return database_url

def connect_to_db(database_url):
    """连接到数据库"""
    try:
        logger.info("连接到数据库...")
        # 添加连接参数
        engine = create_engine(
            database_url,
            connect_args={
                'connect_timeout': 30,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            },
            pool_size=3,
            max_overflow=5
        )
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        logger.info("成功连接到数据库")
        return engine
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        return None

def check_admin_exists(engine, username='admin'):
    """检查管理员账户是否已存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, role FROM users WHERE username = :username"),
                {"username": username}
            )
            user = result.fetchone()
            if user:
                logger.info(f"管理员账户已存在: ID={user[0]}, 用户名={user[1]}, 角色={user[2]}")
                return True
        return False
    except Exception as e:
        logger.error(f"检查管理员账户失败: {str(e)}")
        return False

def create_admin_user(engine, username='admin', password='admin123', role='admin'):
    """创建管理员账户"""
    try:
        # 生成密码哈希
        password_hash = generate_password_hash(password)
        now = datetime.now()
        
        # 插入用户
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO users (username, password_hash, email, role, is_active, created_at, updated_at) 
                VALUES (:username, :password_hash, :email, :role, :is_active, :created_at, :updated_at)
                """),
                {
                    "username": username,
                    "password_hash": password_hash,
                    "email": f"{username}@example.com",
                    "role": role,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now
                }
            )
        
        logger.info(f"管理员账户创建成功: 用户名={username}, 角色={role}")
        return True
    except Exception as e:
        logger.error(f"创建管理员账户失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='创建管理员账户')
    parser.add_argument('--db-url', required=True, help='数据库URL')
    parser.add_argument('--username', default='admin', help='管理员用户名，默认为admin')
    parser.add_argument('--password', default='admin123', help='管理员密码，默认为admin123')
    parser.add_argument('--role', default='admin', help='管理员角色，默认为admin')
    args = parser.parse_args()
    
    logger.info("=== 开始创建管理员账户 ===")
    
    # 修正数据库URL格式
    db_url = fix_database_url(args.db_url)
    
    # 连接数据库
    engine = connect_to_db(db_url)
    if not engine:
        logger.error("无法连接到数据库，终止操作")
        return 1
    
    # 检查管理员是否存在
    if check_admin_exists(engine, args.username):
        logger.info("管理员账户已存在，无需创建")
        return 0
    
    # 创建管理员账户
    if create_admin_user(engine, args.username, args.password, args.role):
        logger.info("=== 管理员账户创建成功 ===")
        return 0
    else:
        logger.error("=== 管理员账户创建失败 ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
创建管理员账户
用于在新数据库环境中确保至少有一个超级管理员账户
"""

import os
import sys
import logging
import argparse
from sqlalchemy import create_engine, text, MetaData, Table
from werkzeug.security import generate_password_hash
from datetime import datetime
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('创建管理员')

def fix_database_url(database_url):
    """修正数据库URL格式"""
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # 添加SSL参数
    if '?' not in database_url:
        database_url += '?sslmode=require'
    elif 'sslmode=' not in database_url:
        database_url += '&sslmode=require'
        
    return database_url

def connect_to_db(database_url):
    """连接到数据库"""
    try:
        logger.info("连接到数据库...")
        # 添加连接参数
        engine = create_engine(
            database_url,
            connect_args={
                'connect_timeout': 30,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            },
            pool_size=3,
            max_overflow=5
        )
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        logger.info("成功连接到数据库")
        return engine
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        return None

def check_admin_exists(engine, username='admin'):
    """检查管理员账户是否已存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, role FROM users WHERE username = :username"),
                {"username": username}
            )
            user = result.fetchone()
            if user:
                logger.info(f"管理员账户已存在: ID={user[0]}, 用户名={user[1]}, 角色={user[2]}")
                return True
        return False
    except Exception as e:
        logger.error(f"检查管理员账户失败: {str(e)}")
        return False

def create_admin_user(engine, username='admin', password='admin123', role='admin'):
    """创建管理员账户"""
    try:
        # 生成密码哈希
        password_hash = generate_password_hash(password)
        now = datetime.now()
        
        # 插入用户
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO users (username, password_hash, email, role, is_active, created_at, updated_at) 
                VALUES (:username, :password_hash, :email, :role, :is_active, :created_at, :updated_at)
                """),
                {
                    "username": username,
                    "password_hash": password_hash,
                    "email": f"{username}@example.com",
                    "role": role,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now
                }
            )
        
        logger.info(f"管理员账户创建成功: 用户名={username}, 角色={role}")
        return True
    except Exception as e:
        logger.error(f"创建管理员账户失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='创建管理员账户')
    parser.add_argument('--db-url', required=True, help='数据库URL')
    parser.add_argument('--username', default='admin', help='管理员用户名，默认为admin')
    parser.add_argument('--password', default='admin123', help='管理员密码，默认为admin123')
    parser.add_argument('--role', default='admin', help='管理员角色，默认为admin')
    args = parser.parse_args()
    
    logger.info("=== 开始创建管理员账户 ===")
    
    # 修正数据库URL格式
    db_url = fix_database_url(args.db_url)
    
    # 连接数据库
    engine = connect_to_db(db_url)
    if not engine:
        logger.error("无法连接到数据库，终止操作")
        return 1
    
    # 检查管理员是否存在
    if check_admin_exists(engine, args.username):
        logger.info("管理员账户已存在，无需创建")
        return 0
    
    # 创建管理员账户
    if create_admin_user(engine, args.username, args.password, args.role):
        logger.info("=== 管理员账户创建成功 ===")
        return 0
    else:
        logger.error("=== 管理员账户创建失败 ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
创建管理员账户
用于在新数据库环境中确保至少有一个超级管理员账户
"""

import os
import sys
import logging
import argparse
from sqlalchemy import create_engine, text, MetaData, Table
from werkzeug.security import generate_password_hash
from datetime import datetime
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('创建管理员')

def fix_database_url(database_url):
    """修正数据库URL格式"""
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # 添加SSL参数
    if '?' not in database_url:
        database_url += '?sslmode=require'
    elif 'sslmode=' not in database_url:
        database_url += '&sslmode=require'
        
    return database_url

def connect_to_db(database_url):
    """连接到数据库"""
    try:
        logger.info("连接到数据库...")
        # 添加连接参数
        engine = create_engine(
            database_url,
            connect_args={
                'connect_timeout': 30,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            },
            pool_size=3,
            max_overflow=5
        )
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        logger.info("成功连接到数据库")
        return engine
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        return None

def check_admin_exists(engine, username='admin'):
    """检查管理员账户是否已存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, role FROM users WHERE username = :username"),
                {"username": username}
            )
            user = result.fetchone()
            if user:
                logger.info(f"管理员账户已存在: ID={user[0]}, 用户名={user[1]}, 角色={user[2]}")
                return True
        return False
    except Exception as e:
        logger.error(f"检查管理员账户失败: {str(e)}")
        return False

def create_admin_user(engine, username='admin', password='admin123', role='admin'):
    """创建管理员账户"""
    try:
        # 生成密码哈希
        password_hash = generate_password_hash(password)
        now = datetime.now()
        
        # 插入用户
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO users (username, password_hash, email, role, is_active, created_at, updated_at) 
                VALUES (:username, :password_hash, :email, :role, :is_active, :created_at, :updated_at)
                """),
                {
                    "username": username,
                    "password_hash": password_hash,
                    "email": f"{username}@example.com",
                    "role": role,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now
                }
            )
        
        logger.info(f"管理员账户创建成功: 用户名={username}, 角色={role}")
        return True
    except Exception as e:
        logger.error(f"创建管理员账户失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='创建管理员账户')
    parser.add_argument('--db-url', required=True, help='数据库URL')
    parser.add_argument('--username', default='admin', help='管理员用户名，默认为admin')
    parser.add_argument('--password', default='admin123', help='管理员密码，默认为admin123')
    parser.add_argument('--role', default='admin', help='管理员角色，默认为admin')
    args = parser.parse_args()
    
    logger.info("=== 开始创建管理员账户 ===")
    
    # 修正数据库URL格式
    db_url = fix_database_url(args.db_url)
    
    # 连接数据库
    engine = connect_to_db(db_url)
    if not engine:
        logger.error("无法连接到数据库，终止操作")
        return 1
    
    # 检查管理员是否存在
    if check_admin_exists(engine, args.username):
        logger.info("管理员账户已存在，无需创建")
        return 0
    
    # 创建管理员账户
    if create_admin_user(engine, args.username, args.password, args.role):
        logger.info("=== 管理员账户创建成功 ===")
        return 0
    else:
        logger.error("=== 管理员账户创建失败 ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
创建管理员账户
用于在新数据库环境中确保至少有一个超级管理员账户
"""

import os
import sys
import logging
import argparse
from sqlalchemy import create_engine, text, MetaData, Table
from werkzeug.security import generate_password_hash
from datetime import datetime
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('创建管理员')

def fix_database_url(database_url):
    """修正数据库URL格式"""
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # 添加SSL参数
    if '?' not in database_url:
        database_url += '?sslmode=require'
    elif 'sslmode=' not in database_url:
        database_url += '&sslmode=require'
        
    return database_url

def connect_to_db(database_url):
    """连接到数据库"""
    try:
        logger.info("连接到数据库...")
        # 添加连接参数
        engine = create_engine(
            database_url,
            connect_args={
                'connect_timeout': 30,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            },
            pool_size=3,
            max_overflow=5
        )
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        logger.info("成功连接到数据库")
        return engine
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        return None

def check_admin_exists(engine, username='admin'):
    """检查管理员账户是否已存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, role FROM users WHERE username = :username"),
                {"username": username}
            )
            user = result.fetchone()
            if user:
                logger.info(f"管理员账户已存在: ID={user[0]}, 用户名={user[1]}, 角色={user[2]}")
                return True
        return False
    except Exception as e:
        logger.error(f"检查管理员账户失败: {str(e)}")
        return False

def create_admin_user(engine, username='admin', password='admin123', role='admin'):
    """创建管理员账户"""
    try:
        # 生成密码哈希
        password_hash = generate_password_hash(password)
        now = datetime.now()
        
        # 插入用户
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO users (username, password_hash, email, role, is_active, created_at, updated_at) 
                VALUES (:username, :password_hash, :email, :role, :is_active, :created_at, :updated_at)
                """),
                {
                    "username": username,
                    "password_hash": password_hash,
                    "email": f"{username}@example.com",
                    "role": role,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now
                }
            )
        
        logger.info(f"管理员账户创建成功: 用户名={username}, 角色={role}")
        return True
    except Exception as e:
        logger.error(f"创建管理员账户失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='创建管理员账户')
    parser.add_argument('--db-url', required=True, help='数据库URL')
    parser.add_argument('--username', default='admin', help='管理员用户名，默认为admin')
    parser.add_argument('--password', default='admin123', help='管理员密码，默认为admin123')
    parser.add_argument('--role', default='admin', help='管理员角色，默认为admin')
    args = parser.parse_args()
    
    logger.info("=== 开始创建管理员账户 ===")
    
    # 修正数据库URL格式
    db_url = fix_database_url(args.db_url)
    
    # 连接数据库
    engine = connect_to_db(db_url)
    if not engine:
        logger.error("无法连接到数据库，终止操作")
        return 1
    
    # 检查管理员是否存在
    if check_admin_exists(engine, args.username):
        logger.info("管理员账户已存在，无需创建")
        return 0
    
    # 创建管理员账户
    if create_admin_user(engine, args.username, args.password, args.role):
        logger.info("=== 管理员账户创建成功 ===")
        return 0
    else:
        logger.error("=== 管理员账户创建失败 ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 