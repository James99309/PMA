#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据库连接
为应用程序提供连接Render PostgreSQL数据库的工具函数
"""

import os
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# 全局变量
db = SQLAlchemy()

def parse_db_url(url):
    """解析数据库URL，提取连接参数"""
    parsed = urlparse(url)
    
    db_info = {
        'dbname': parsed.path.strip('/'),
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'sslmode': 'require',
        'sslrootcert': 'none'
    }
    
    return db_info

def get_db_url():
    """获取数据库URL，优先使用环境变量"""
    render_db_url = os.environ.get('RENDER_DB_URL')
    
    if render_db_url:
        # 确保URL包含SSL参数
        if '?' not in render_db_url:
            render_db_url += '?sslmode=require&sslrootcert=none'
        elif 'sslmode=' not in render_db_url:
            render_db_url += '&sslmode=require&sslrootcert=none'
            
        return render_db_url
    
    # 开发环境回退到SQLite
    return 'sqlite:///app.db'

def get_engine():
    """创建数据库引擎"""
    db_url = get_db_url()
    
    if db_url.startswith('postgresql'):
        # PostgreSQL引擎
        engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True
        )
    else:
        # SQLite引擎
        engine = create_engine(db_url)
    
    return engine

def get_db_session():
    """创建数据库会话"""
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(session_factory)

def init_app(app):
    """初始化Flask应用的数据库连接"""
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 添加其他PostgreSQL相关配置
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
    
    db.init_app(app)
    
    return db

def test_connection():
    """测试数据库连接"""
    engine = get_engine()
    try:
        connection = engine.connect()
        connection.close()
        print("数据库连接测试成功!")
        return True
    except Exception as e:
        print(f"数据库连接测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 如果直接运行此脚本，执行连接测试
    test_connection()

# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据库连接
为应用程序提供连接Render PostgreSQL数据库的工具函数
"""

import os
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# 全局变量
db = SQLAlchemy()

def parse_db_url(url):
    """解析数据库URL，提取连接参数"""
    parsed = urlparse(url)
    
    db_info = {
        'dbname': parsed.path.strip('/'),
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'sslmode': 'require',
        'sslrootcert': 'none'
    }
    
    return db_info

def get_db_url():
    """获取数据库URL，优先使用环境变量"""
    render_db_url = os.environ.get('RENDER_DB_URL')
    
    if render_db_url:
        # 确保URL包含SSL参数
        if '?' not in render_db_url:
            render_db_url += '?sslmode=require&sslrootcert=none'
        elif 'sslmode=' not in render_db_url:
            render_db_url += '&sslmode=require&sslrootcert=none'
            
        return render_db_url
    
    # 开发环境回退到SQLite
    return 'sqlite:///app.db'

def get_engine():
    """创建数据库引擎"""
    db_url = get_db_url()
    
    if db_url.startswith('postgresql'):
        # PostgreSQL引擎
        engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True
        )
    else:
        # SQLite引擎
        engine = create_engine(db_url)
    
    return engine

def get_db_session():
    """创建数据库会话"""
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(session_factory)

def init_app(app):
    """初始化Flask应用的数据库连接"""
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 添加其他PostgreSQL相关配置
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
    
    db.init_app(app)
    
    return db

def test_connection():
    """测试数据库连接"""
    engine = get_engine()
    try:
        connection = engine.connect()
        connection.close()
        print("数据库连接测试成功!")
        return True
    except Exception as e:
        print(f"数据库连接测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 如果直接运行此脚本，执行连接测试
    test_connection()

 
 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据库连接
为应用程序提供连接Render PostgreSQL数据库的工具函数
"""

import os
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# 全局变量
db = SQLAlchemy()

def parse_db_url(url):
    """解析数据库URL，提取连接参数"""
    parsed = urlparse(url)
    
    db_info = {
        'dbname': parsed.path.strip('/'),
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'sslmode': 'require',
        'sslrootcert': 'none'
    }
    
    return db_info

def get_db_url():
    """获取数据库URL，优先使用环境变量"""
    render_db_url = os.environ.get('RENDER_DB_URL')
    
    if render_db_url:
        # 确保URL包含SSL参数
        if '?' not in render_db_url:
            render_db_url += '?sslmode=require&sslrootcert=none'
        elif 'sslmode=' not in render_db_url:
            render_db_url += '&sslmode=require&sslrootcert=none'
            
        return render_db_url
    
    # 开发环境回退到SQLite
    return 'sqlite:///app.db'

def get_engine():
    """创建数据库引擎"""
    db_url = get_db_url()
    
    if db_url.startswith('postgresql'):
        # PostgreSQL引擎
        engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True
        )
    else:
        # SQLite引擎
        engine = create_engine(db_url)
    
    return engine

def get_db_session():
    """创建数据库会话"""
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(session_factory)

def init_app(app):
    """初始化Flask应用的数据库连接"""
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 添加其他PostgreSQL相关配置
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
    
    db.init_app(app)
    
    return db

def test_connection():
    """测试数据库连接"""
    engine = get_engine()
    try:
        connection = engine.connect()
        connection.close()
        print("数据库连接测试成功!")
        return True
    except Exception as e:
        print(f"数据库连接测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 如果直接运行此脚本，执行连接测试
    test_connection()

# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据库连接
为应用程序提供连接Render PostgreSQL数据库的工具函数
"""

import os
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# 全局变量
db = SQLAlchemy()

def parse_db_url(url):
    """解析数据库URL，提取连接参数"""
    parsed = urlparse(url)
    
    db_info = {
        'dbname': parsed.path.strip('/'),
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'sslmode': 'require',
        'sslrootcert': 'none'
    }
    
    return db_info

def get_db_url():
    """获取数据库URL，优先使用环境变量"""
    render_db_url = os.environ.get('RENDER_DB_URL')
    
    if render_db_url:
        # 确保URL包含SSL参数
        if '?' not in render_db_url:
            render_db_url += '?sslmode=require&sslrootcert=none'
        elif 'sslmode=' not in render_db_url:
            render_db_url += '&sslmode=require&sslrootcert=none'
            
        return render_db_url
    
    # 开发环境回退到SQLite
    return 'sqlite:///app.db'

def get_engine():
    """创建数据库引擎"""
    db_url = get_db_url()
    
    if db_url.startswith('postgresql'):
        # PostgreSQL引擎
        engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True
        )
    else:
        # SQLite引擎
        engine = create_engine(db_url)
    
    return engine

def get_db_session():
    """创建数据库会话"""
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(session_factory)

def init_app(app):
    """初始化Flask应用的数据库连接"""
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 添加其他PostgreSQL相关配置
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
    
    db.init_app(app)
    
    return db

def test_connection():
    """测试数据库连接"""
    engine = get_engine()
    try:
        connection = engine.connect()
        connection.close()
        print("数据库连接测试成功!")
        return True
    except Exception as e:
        print(f"数据库连接测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 如果直接运行此脚本，执行连接测试
    test_connection()

 
 