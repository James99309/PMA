#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复应用程序配置脚本
确保应用正确连接到Render PostgreSQL数据库
"""

import os
import sys
import re
import logging
import shutil
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_app_config.log')
    ]
)
logger = logging.getLogger('应用配置修复')

def backup_file(file_path):
    """备份文件"""
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = f"{file_path}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        logger.info(f"已备份文件 {file_path} 到 {backup_path}")
        return backup_path
    return None

def update_config_file():
    """更新配置文件"""
    config_path = 'config.py'
    
    # 备份文件
    backup_file(config_path)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有RENDER_DB_URL配置
        if 'RENDER_DB_URL' in content and 'SQLALCHEMY_DATABASE_URI' in content:
            logger.info("配置文件已包含Render数据库配置")
            
            # 检查是否需要更新SSL配置
            if 'sslmode=require' not in content or 'sslrootcert=none' not in content:
                logger.info("需要更新SSL配置")
                
                # 查找SQLALCHEMY_DATABASE_URI配置行
                uri_pattern = r'(SQLALCHEMY_DATABASE_URI\s*=\s*.*)'
                uri_matches = re.findall(uri_pattern, content)
                
                if uri_matches:
                    # 替换配置
                    for match in uri_matches:
                        if 'postgresql:' in match and 'RENDER_DB_URL' in match:
                            # 修复PostgreSQL连接字符串
                            fixed_line = match
                            # 确保包含SSL参数
                            if 'sslmode=require' not in match:
                                if '?' in match:
                                    fixed_line = fixed_line.replace('")', '&sslmode=require&sslrootcert=none")')
                                else:
                                    fixed_line = fixed_line.replace('")', '?sslmode=require&sslrootcert=none")')
                            # 替换原始行
                            content = content.replace(match, fixed_line)
                            logger.info(f"已修复SQLALCHEMY_DATABASE_URI配置: {fixed_line}")
                
                # 写回文件
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("配置文件已更新")
            else:
                logger.info("SSL配置已存在，无需更新")
        else:
            # 添加Render数据库配置
            logger.info("添加Render数据库配置")
            
            # 检查是否已有Config类定义
            config_class_pattern = r'class\s+Config\s*\(.*\)\s*:'
            if re.search(config_class_pattern, content):
                # 查找Config类中的SQLALCHEMY_DATABASE_URI定义
                uri_pattern = r'(SQLALCHEMY_DATABASE_URI\s*=\s*.*)'
                uri_matches = re.findall(uri_pattern, content)
                
                if uri_matches:
                    # 替换为从环境变量获取
                    new_uri_line = "    SQLALCHEMY_DATABASE_URI = os.environ.get('RENDER_DB_URL', 'sqlite:///app.db')"
                    content = content.replace(uri_matches[0], new_uri_line)
                    
                    # 添加SSL连接池配置
                    pool_config = """
    # PostgreSQL连接池配置
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
"""
                    # 在Config类中添加配置
                    content = content.replace('class Config', f'class Config{pool_config}')
                    
                else:
                    # 在Config类中添加
                    config_pattern = r'(class\s+Config\s*\(.*\)\s*:)'
                    new_config = r'\1\n    SQLALCHEMY_DATABASE_URI = os.environ.get(\'RENDER_DB_URL\', \'sqlite:///app.db\')\n    # PostgreSQL连接池配置\n    if SQLALCHEMY_DATABASE_URI.startswith(\'postgresql\'):\n        SQLALCHEMY_ENGINE_OPTIONS = {\n            \'pool_size\': 10,\n            \'max_overflow\': 20,\n            \'pool_recycle\': 3600,\n            \'pool_pre_ping\': True\n        }'
                    content = re.sub(config_pattern, new_config, content)
            else:
                # 添加新的Config类
                config_class = """
class Config:
    # 从环境变量获取数据库URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('RENDER_DB_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL连接池配置
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
"""
                # 确保导入os模块
                if 'import os' not in content:
                    content = "import os\n" + content
                
                # 添加配置类
                content += config_class
            
            # 写回文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("配置文件已更新，添加了Render数据库配置")
            
        return True
    except Exception as e:
        logger.error(f"更新配置文件失败: {str(e)}")
        return False

def create_render_db_connection():
    """创建Render数据库连接模块"""
    file_path = 'render_db_connection.py'
    
    # 如果文件已存在，备份它
    if os.path.exists(file_path):
        backup_file(file_path)
    
    # 创建新的连接模块
    content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Render PostgreSQL 数据库连接
为应用程序提供连接Render PostgreSQL数据库的工具函数
\"\"\"

import os
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# 全局变量
db = SQLAlchemy()

def parse_db_url(url):
    \"\"\"解析数据库URL，提取连接参数\"\"\"
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
    \"\"\"获取数据库URL，优先使用环境变量\"\"\"
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
    \"\"\"创建数据库引擎\"\"\"
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
    \"\"\"创建数据库会话\"\"\"
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(session_factory)

def init_app(app):
    \"\"\"初始化Flask应用的数据库连接\"\"\"
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
    \"\"\"测试数据库连接\"\"\"
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
"""
    
    # 写入文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建Render数据库连接模块: {file_path}")
        return True
    except Exception as e:
        logger.error(f"创建Render数据库连接模块失败: {str(e)}")
        return False

def update_app_init():
    """更新app/__init__.py文件"""
    file_path = 'app/__init__.py'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查导入db语句
        if 'from flask_sqlalchemy import SQLAlchemy' in content:
            # 替换为导入自定义db
            logger.info("更新数据库导入语句")
            content = content.replace(
                'from flask_sqlalchemy import SQLAlchemy', 
                '# 使用自定义数据库连接模块\nfrom render_db_connection import db, init_app as init_db'
            )
            
            # 删除原始db定义
            if 'db = SQLAlchemy()' in content:
                content = content.replace('db = SQLAlchemy()', '# db已从render_db_connection导入')
            
            # 更新初始化方法
            init_pattern = r'(def\s+create_app\([^)]*\):.*?)(db\.init_app\(app\))'
            if re.search(init_pattern, content, re.DOTALL):
                content = re.sub(
                    init_pattern, 
                    r'\1init_db(app)',
                    content,
                    flags=re.DOTALL
                )
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("已更新app/__init__.py文件")
            return True
        else:
            logger.info("未找到SQLAlchemy导入语句，文件可能已更新")
            return True
    except Exception as e:
        logger.error(f"更新app/__init__.py失败: {str(e)}")
        return False

def update_run_py():
    """更新run.py文件"""
    file_path = 'run.py'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含数据库初始化代码
        if 'from app import create_app' in content:
            # 添加数据库初始化和检查
            if 'from render_db_connection import' not in content:
                # 替换导入语句
                content = content.replace(
                    'from app import create_app',
                    'from app import create_app\nfrom render_db_connection import test_connection'
                )
                
                # 添加连接测试
                if 'if __name__ == \'__main__\':' in content:
                    # 在主函数前添加连接测试
                    main_pattern = r'(if\s+__name__\s*==\s*[\'\"]__main__[\'\"].*?)'
                    content = re.sub(
                        main_pattern,
                        r'\1\n    # 测试数据库连接\n    test_connection()\n',
                        content,
                        flags=re.DOTALL
                    )
                
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("已更新run.py文件")
            else:
                logger.info("run.py文件已包含数据库连接代码")
            return True
        else:
            logger.warning("未找到app导入语句，无法更新run.py")
            return False
    except Exception as e:
        logger.error(f"更新run.py失败: {str(e)}")
        return False

def update_requirements():
    """更新requirements.txt文件"""
    file_path = 'requirements.txt'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        # 读取现有需求
        requirements = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                requirements = [line.strip() for line in f.readlines()]
        
        # 检查是否已包含psycopg2
        has_psycopg2 = any(req.startswith('psycopg2') for req in requirements)
        
        if not has_psycopg2:
            # 添加PostgreSQL驱动
            requirements.append('psycopg2-binary==2.9.9')
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(requirements) + '\n')
            logger.info("已更新requirements.txt文件，添加了psycopg2-binary")
        else:
            logger.info("requirements.txt已包含PostgreSQL驱动")
        
        return True
    except Exception as e:
        logger.error(f"更新requirements.txt失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始修复应用程序配置...")
    
    # 1. 更新配置文件
    if update_config_file():
        logger.info("配置文件更新成功")
    else:
        logger.error("配置文件更新失败")
    
    # 2. 创建Render数据库连接模块
    if create_render_db_connection():
        logger.info("Render数据库连接模块创建成功")
    else:
        logger.error("Render数据库连接模块创建失败")
    
    # 3. 更新app/__init__.py
    if update_app_init():
        logger.info("app/__init__.py更新成功")
    else:
        logger.error("app/__init__.py更新失败")
    
    # 4. 更新run.py
    if update_run_py():
        logger.info("run.py更新成功")
    else:
        logger.error("run.py更新失败")
    
    # 5. 更新requirements.txt
    if update_requirements():
        logger.info("requirements.txt更新成功")
    else:
        logger.error("requirements.txt更新失败")
    
    logger.info("应用程序配置修复完成")
    print("\n修复完成后的操作步骤:")
    print("1. 设置环境变量: export RENDER_DB_URL=\"postgresql://用户名:密码@主机/数据库名?sslmode=require&sslrootcert=none\"")
    print("2. 安装依赖: pip install -r requirements.txt")
    print("3. 测试数据库连接: python render_db_connection.py")
    print("4. 启动应用: python run.py")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
修复应用程序配置脚本
确保应用正确连接到Render PostgreSQL数据库
"""

import os
import sys
import re
import logging
import shutil
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_app_config.log')
    ]
)
logger = logging.getLogger('应用配置修复')

def backup_file(file_path):
    """备份文件"""
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = f"{file_path}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        logger.info(f"已备份文件 {file_path} 到 {backup_path}")
        return backup_path
    return None

def update_config_file():
    """更新配置文件"""
    config_path = 'config.py'
    
    # 备份文件
    backup_file(config_path)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有RENDER_DB_URL配置
        if 'RENDER_DB_URL' in content and 'SQLALCHEMY_DATABASE_URI' in content:
            logger.info("配置文件已包含Render数据库配置")
            
            # 检查是否需要更新SSL配置
            if 'sslmode=require' not in content or 'sslrootcert=none' not in content:
                logger.info("需要更新SSL配置")
                
                # 查找SQLALCHEMY_DATABASE_URI配置行
                uri_pattern = r'(SQLALCHEMY_DATABASE_URI\s*=\s*.*)'
                uri_matches = re.findall(uri_pattern, content)
                
                if uri_matches:
                    # 替换配置
                    for match in uri_matches:
                        if 'postgresql:' in match and 'RENDER_DB_URL' in match:
                            # 修复PostgreSQL连接字符串
                            fixed_line = match
                            # 确保包含SSL参数
                            if 'sslmode=require' not in match:
                                if '?' in match:
                                    fixed_line = fixed_line.replace('")', '&sslmode=require&sslrootcert=none")')
                                else:
                                    fixed_line = fixed_line.replace('")', '?sslmode=require&sslrootcert=none")')
                            # 替换原始行
                            content = content.replace(match, fixed_line)
                            logger.info(f"已修复SQLALCHEMY_DATABASE_URI配置: {fixed_line}")
                
                # 写回文件
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("配置文件已更新")
            else:
                logger.info("SSL配置已存在，无需更新")
        else:
            # 添加Render数据库配置
            logger.info("添加Render数据库配置")
            
            # 检查是否已有Config类定义
            config_class_pattern = r'class\s+Config\s*\(.*\)\s*:'
            if re.search(config_class_pattern, content):
                # 查找Config类中的SQLALCHEMY_DATABASE_URI定义
                uri_pattern = r'(SQLALCHEMY_DATABASE_URI\s*=\s*.*)'
                uri_matches = re.findall(uri_pattern, content)
                
                if uri_matches:
                    # 替换为从环境变量获取
                    new_uri_line = "    SQLALCHEMY_DATABASE_URI = os.environ.get('RENDER_DB_URL', 'sqlite:///app.db')"
                    content = content.replace(uri_matches[0], new_uri_line)
                    
                    # 添加SSL连接池配置
                    pool_config = """
    # PostgreSQL连接池配置
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
"""
                    # 在Config类中添加配置
                    content = content.replace('class Config', f'class Config{pool_config}')
                    
                else:
                    # 在Config类中添加
                    config_pattern = r'(class\s+Config\s*\(.*\)\s*:)'
                    new_config = r'\1\n    SQLALCHEMY_DATABASE_URI = os.environ.get(\'RENDER_DB_URL\', \'sqlite:///app.db\')\n    # PostgreSQL连接池配置\n    if SQLALCHEMY_DATABASE_URI.startswith(\'postgresql\'):\n        SQLALCHEMY_ENGINE_OPTIONS = {\n            \'pool_size\': 10,\n            \'max_overflow\': 20,\n            \'pool_recycle\': 3600,\n            \'pool_pre_ping\': True\n        }'
                    content = re.sub(config_pattern, new_config, content)
            else:
                # 添加新的Config类
                config_class = """
class Config:
    # 从环境变量获取数据库URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('RENDER_DB_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL连接池配置
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
"""
                # 确保导入os模块
                if 'import os' not in content:
                    content = "import os\n" + content
                
                # 添加配置类
                content += config_class
            
            # 写回文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("配置文件已更新，添加了Render数据库配置")
            
        return True
    except Exception as e:
        logger.error(f"更新配置文件失败: {str(e)}")
        return False

def create_render_db_connection():
    """创建Render数据库连接模块"""
    file_path = 'render_db_connection.py'
    
    # 如果文件已存在，备份它
    if os.path.exists(file_path):
        backup_file(file_path)
    
    # 创建新的连接模块
    content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Render PostgreSQL 数据库连接
为应用程序提供连接Render PostgreSQL数据库的工具函数
\"\"\"

import os
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# 全局变量
db = SQLAlchemy()

def parse_db_url(url):
    \"\"\"解析数据库URL，提取连接参数\"\"\"
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
    \"\"\"获取数据库URL，优先使用环境变量\"\"\"
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
    \"\"\"创建数据库引擎\"\"\"
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
    \"\"\"创建数据库会话\"\"\"
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(session_factory)

def init_app(app):
    \"\"\"初始化Flask应用的数据库连接\"\"\"
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
    \"\"\"测试数据库连接\"\"\"
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
"""
    
    # 写入文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建Render数据库连接模块: {file_path}")
        return True
    except Exception as e:
        logger.error(f"创建Render数据库连接模块失败: {str(e)}")
        return False

def update_app_init():
    """更新app/__init__.py文件"""
    file_path = 'app/__init__.py'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查导入db语句
        if 'from flask_sqlalchemy import SQLAlchemy' in content:
            # 替换为导入自定义db
            logger.info("更新数据库导入语句")
            content = content.replace(
                'from flask_sqlalchemy import SQLAlchemy', 
                '# 使用自定义数据库连接模块\nfrom render_db_connection import db, init_app as init_db'
            )
            
            # 删除原始db定义
            if 'db = SQLAlchemy()' in content:
                content = content.replace('db = SQLAlchemy()', '# db已从render_db_connection导入')
            
            # 更新初始化方法
            init_pattern = r'(def\s+create_app\([^)]*\):.*?)(db\.init_app\(app\))'
            if re.search(init_pattern, content, re.DOTALL):
                content = re.sub(
                    init_pattern, 
                    r'\1init_db(app)',
                    content,
                    flags=re.DOTALL
                )
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("已更新app/__init__.py文件")
            return True
        else:
            logger.info("未找到SQLAlchemy导入语句，文件可能已更新")
            return True
    except Exception as e:
        logger.error(f"更新app/__init__.py失败: {str(e)}")
        return False

def update_run_py():
    """更新run.py文件"""
    file_path = 'run.py'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含数据库初始化代码
        if 'from app import create_app' in content:
            # 添加数据库初始化和检查
            if 'from render_db_connection import' not in content:
                # 替换导入语句
                content = content.replace(
                    'from app import create_app',
                    'from app import create_app\nfrom render_db_connection import test_connection'
                )
                
                # 添加连接测试
                if 'if __name__ == \'__main__\':' in content:
                    # 在主函数前添加连接测试
                    main_pattern = r'(if\s+__name__\s*==\s*[\'\"]__main__[\'\"].*?)'
                    content = re.sub(
                        main_pattern,
                        r'\1\n    # 测试数据库连接\n    test_connection()\n',
                        content,
                        flags=re.DOTALL
                    )
                
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("已更新run.py文件")
            else:
                logger.info("run.py文件已包含数据库连接代码")
            return True
        else:
            logger.warning("未找到app导入语句，无法更新run.py")
            return False
    except Exception as e:
        logger.error(f"更新run.py失败: {str(e)}")
        return False

def update_requirements():
    """更新requirements.txt文件"""
    file_path = 'requirements.txt'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        # 读取现有需求
        requirements = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                requirements = [line.strip() for line in f.readlines()]
        
        # 检查是否已包含psycopg2
        has_psycopg2 = any(req.startswith('psycopg2') for req in requirements)
        
        if not has_psycopg2:
            # 添加PostgreSQL驱动
            requirements.append('psycopg2-binary==2.9.9')
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(requirements) + '\n')
            logger.info("已更新requirements.txt文件，添加了psycopg2-binary")
        else:
            logger.info("requirements.txt已包含PostgreSQL驱动")
        
        return True
    except Exception as e:
        logger.error(f"更新requirements.txt失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始修复应用程序配置...")
    
    # 1. 更新配置文件
    if update_config_file():
        logger.info("配置文件更新成功")
    else:
        logger.error("配置文件更新失败")
    
    # 2. 创建Render数据库连接模块
    if create_render_db_connection():
        logger.info("Render数据库连接模块创建成功")
    else:
        logger.error("Render数据库连接模块创建失败")
    
    # 3. 更新app/__init__.py
    if update_app_init():
        logger.info("app/__init__.py更新成功")
    else:
        logger.error("app/__init__.py更新失败")
    
    # 4. 更新run.py
    if update_run_py():
        logger.info("run.py更新成功")
    else:
        logger.error("run.py更新失败")
    
    # 5. 更新requirements.txt
    if update_requirements():
        logger.info("requirements.txt更新成功")
    else:
        logger.error("requirements.txt更新失败")
    
    logger.info("应用程序配置修复完成")
    print("\n修复完成后的操作步骤:")
    print("1. 设置环境变量: export RENDER_DB_URL=\"postgresql://用户名:密码@主机/数据库名?sslmode=require&sslrootcert=none\"")
    print("2. 安装依赖: pip install -r requirements.txt")
    print("3. 测试数据库连接: python render_db_connection.py")
    print("4. 启动应用: python run.py")

if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
修复应用程序配置脚本
确保应用正确连接到Render PostgreSQL数据库
"""

import os
import sys
import re
import logging
import shutil
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_app_config.log')
    ]
)
logger = logging.getLogger('应用配置修复')

def backup_file(file_path):
    """备份文件"""
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = f"{file_path}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        logger.info(f"已备份文件 {file_path} 到 {backup_path}")
        return backup_path
    return None

def update_config_file():
    """更新配置文件"""
    config_path = 'config.py'
    
    # 备份文件
    backup_file(config_path)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有RENDER_DB_URL配置
        if 'RENDER_DB_URL' in content and 'SQLALCHEMY_DATABASE_URI' in content:
            logger.info("配置文件已包含Render数据库配置")
            
            # 检查是否需要更新SSL配置
            if 'sslmode=require' not in content or 'sslrootcert=none' not in content:
                logger.info("需要更新SSL配置")
                
                # 查找SQLALCHEMY_DATABASE_URI配置行
                uri_pattern = r'(SQLALCHEMY_DATABASE_URI\s*=\s*.*)'
                uri_matches = re.findall(uri_pattern, content)
                
                if uri_matches:
                    # 替换配置
                    for match in uri_matches:
                        if 'postgresql:' in match and 'RENDER_DB_URL' in match:
                            # 修复PostgreSQL连接字符串
                            fixed_line = match
                            # 确保包含SSL参数
                            if 'sslmode=require' not in match:
                                if '?' in match:
                                    fixed_line = fixed_line.replace('")', '&sslmode=require&sslrootcert=none")')
                                else:
                                    fixed_line = fixed_line.replace('")', '?sslmode=require&sslrootcert=none")')
                            # 替换原始行
                            content = content.replace(match, fixed_line)
                            logger.info(f"已修复SQLALCHEMY_DATABASE_URI配置: {fixed_line}")
                
                # 写回文件
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("配置文件已更新")
            else:
                logger.info("SSL配置已存在，无需更新")
        else:
            # 添加Render数据库配置
            logger.info("添加Render数据库配置")
            
            # 检查是否已有Config类定义
            config_class_pattern = r'class\s+Config\s*\(.*\)\s*:'
            if re.search(config_class_pattern, content):
                # 查找Config类中的SQLALCHEMY_DATABASE_URI定义
                uri_pattern = r'(SQLALCHEMY_DATABASE_URI\s*=\s*.*)'
                uri_matches = re.findall(uri_pattern, content)
                
                if uri_matches:
                    # 替换为从环境变量获取
                    new_uri_line = "    SQLALCHEMY_DATABASE_URI = os.environ.get('RENDER_DB_URL', 'sqlite:///app.db')"
                    content = content.replace(uri_matches[0], new_uri_line)
                    
                    # 添加SSL连接池配置
                    pool_config = """
    # PostgreSQL连接池配置
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
"""
                    # 在Config类中添加配置
                    content = content.replace('class Config', f'class Config{pool_config}')
                    
                else:
                    # 在Config类中添加
                    config_pattern = r'(class\s+Config\s*\(.*\)\s*:)'
                    new_config = r'\1\n    SQLALCHEMY_DATABASE_URI = os.environ.get(\'RENDER_DB_URL\', \'sqlite:///app.db\')\n    # PostgreSQL连接池配置\n    if SQLALCHEMY_DATABASE_URI.startswith(\'postgresql\'):\n        SQLALCHEMY_ENGINE_OPTIONS = {\n            \'pool_size\': 10,\n            \'max_overflow\': 20,\n            \'pool_recycle\': 3600,\n            \'pool_pre_ping\': True\n        }'
                    content = re.sub(config_pattern, new_config, content)
            else:
                # 添加新的Config类
                config_class = """
class Config:
    # 从环境变量获取数据库URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('RENDER_DB_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL连接池配置
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
"""
                # 确保导入os模块
                if 'import os' not in content:
                    content = "import os\n" + content
                
                # 添加配置类
                content += config_class
            
            # 写回文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("配置文件已更新，添加了Render数据库配置")
            
        return True
    except Exception as e:
        logger.error(f"更新配置文件失败: {str(e)}")
        return False

def create_render_db_connection():
    """创建Render数据库连接模块"""
    file_path = 'render_db_connection.py'
    
    # 如果文件已存在，备份它
    if os.path.exists(file_path):
        backup_file(file_path)
    
    # 创建新的连接模块
    content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Render PostgreSQL 数据库连接
为应用程序提供连接Render PostgreSQL数据库的工具函数
\"\"\"

import os
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# 全局变量
db = SQLAlchemy()

def parse_db_url(url):
    \"\"\"解析数据库URL，提取连接参数\"\"\"
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
    \"\"\"获取数据库URL，优先使用环境变量\"\"\"
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
    \"\"\"创建数据库引擎\"\"\"
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
    \"\"\"创建数据库会话\"\"\"
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(session_factory)

def init_app(app):
    \"\"\"初始化Flask应用的数据库连接\"\"\"
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
    \"\"\"测试数据库连接\"\"\"
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
"""
    
    # 写入文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建Render数据库连接模块: {file_path}")
        return True
    except Exception as e:
        logger.error(f"创建Render数据库连接模块失败: {str(e)}")
        return False

def update_app_init():
    """更新app/__init__.py文件"""
    file_path = 'app/__init__.py'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查导入db语句
        if 'from flask_sqlalchemy import SQLAlchemy' in content:
            # 替换为导入自定义db
            logger.info("更新数据库导入语句")
            content = content.replace(
                'from flask_sqlalchemy import SQLAlchemy', 
                '# 使用自定义数据库连接模块\nfrom render_db_connection import db, init_app as init_db'
            )
            
            # 删除原始db定义
            if 'db = SQLAlchemy()' in content:
                content = content.replace('db = SQLAlchemy()', '# db已从render_db_connection导入')
            
            # 更新初始化方法
            init_pattern = r'(def\s+create_app\([^)]*\):.*?)(db\.init_app\(app\))'
            if re.search(init_pattern, content, re.DOTALL):
                content = re.sub(
                    init_pattern, 
                    r'\1init_db(app)',
                    content,
                    flags=re.DOTALL
                )
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("已更新app/__init__.py文件")
            return True
        else:
            logger.info("未找到SQLAlchemy导入语句，文件可能已更新")
            return True
    except Exception as e:
        logger.error(f"更新app/__init__.py失败: {str(e)}")
        return False

def update_run_py():
    """更新run.py文件"""
    file_path = 'run.py'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含数据库初始化代码
        if 'from app import create_app' in content:
            # 添加数据库初始化和检查
            if 'from render_db_connection import' not in content:
                # 替换导入语句
                content = content.replace(
                    'from app import create_app',
                    'from app import create_app\nfrom render_db_connection import test_connection'
                )
                
                # 添加连接测试
                if 'if __name__ == \'__main__\':' in content:
                    # 在主函数前添加连接测试
                    main_pattern = r'(if\s+__name__\s*==\s*[\'\"]__main__[\'\"].*?)'
                    content = re.sub(
                        main_pattern,
                        r'\1\n    # 测试数据库连接\n    test_connection()\n',
                        content,
                        flags=re.DOTALL
                    )
                
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("已更新run.py文件")
            else:
                logger.info("run.py文件已包含数据库连接代码")
            return True
        else:
            logger.warning("未找到app导入语句，无法更新run.py")
            return False
    except Exception as e:
        logger.error(f"更新run.py失败: {str(e)}")
        return False

def update_requirements():
    """更新requirements.txt文件"""
    file_path = 'requirements.txt'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        # 读取现有需求
        requirements = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                requirements = [line.strip() for line in f.readlines()]
        
        # 检查是否已包含psycopg2
        has_psycopg2 = any(req.startswith('psycopg2') for req in requirements)
        
        if not has_psycopg2:
            # 添加PostgreSQL驱动
            requirements.append('psycopg2-binary==2.9.9')
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(requirements) + '\n')
            logger.info("已更新requirements.txt文件，添加了psycopg2-binary")
        else:
            logger.info("requirements.txt已包含PostgreSQL驱动")
        
        return True
    except Exception as e:
        logger.error(f"更新requirements.txt失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始修复应用程序配置...")
    
    # 1. 更新配置文件
    if update_config_file():
        logger.info("配置文件更新成功")
    else:
        logger.error("配置文件更新失败")
    
    # 2. 创建Render数据库连接模块
    if create_render_db_connection():
        logger.info("Render数据库连接模块创建成功")
    else:
        logger.error("Render数据库连接模块创建失败")
    
    # 3. 更新app/__init__.py
    if update_app_init():
        logger.info("app/__init__.py更新成功")
    else:
        logger.error("app/__init__.py更新失败")
    
    # 4. 更新run.py
    if update_run_py():
        logger.info("run.py更新成功")
    else:
        logger.error("run.py更新失败")
    
    # 5. 更新requirements.txt
    if update_requirements():
        logger.info("requirements.txt更新成功")
    else:
        logger.error("requirements.txt更新失败")
    
    logger.info("应用程序配置修复完成")
    print("\n修复完成后的操作步骤:")
    print("1. 设置环境变量: export RENDER_DB_URL=\"postgresql://用户名:密码@主机/数据库名?sslmode=require&sslrootcert=none\"")
    print("2. 安装依赖: pip install -r requirements.txt")
    print("3. 测试数据库连接: python render_db_connection.py")
    print("4. 启动应用: python run.py")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
修复应用程序配置脚本
确保应用正确连接到Render PostgreSQL数据库
"""

import os
import sys
import re
import logging
import shutil
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_app_config.log')
    ]
)
logger = logging.getLogger('应用配置修复')

def backup_file(file_path):
    """备份文件"""
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = f"{file_path}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        logger.info(f"已备份文件 {file_path} 到 {backup_path}")
        return backup_path
    return None

def update_config_file():
    """更新配置文件"""
    config_path = 'config.py'
    
    # 备份文件
    backup_file(config_path)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有RENDER_DB_URL配置
        if 'RENDER_DB_URL' in content and 'SQLALCHEMY_DATABASE_URI' in content:
            logger.info("配置文件已包含Render数据库配置")
            
            # 检查是否需要更新SSL配置
            if 'sslmode=require' not in content or 'sslrootcert=none' not in content:
                logger.info("需要更新SSL配置")
                
                # 查找SQLALCHEMY_DATABASE_URI配置行
                uri_pattern = r'(SQLALCHEMY_DATABASE_URI\s*=\s*.*)'
                uri_matches = re.findall(uri_pattern, content)
                
                if uri_matches:
                    # 替换配置
                    for match in uri_matches:
                        if 'postgresql:' in match and 'RENDER_DB_URL' in match:
                            # 修复PostgreSQL连接字符串
                            fixed_line = match
                            # 确保包含SSL参数
                            if 'sslmode=require' not in match:
                                if '?' in match:
                                    fixed_line = fixed_line.replace('")', '&sslmode=require&sslrootcert=none")')
                                else:
                                    fixed_line = fixed_line.replace('")', '?sslmode=require&sslrootcert=none")')
                            # 替换原始行
                            content = content.replace(match, fixed_line)
                            logger.info(f"已修复SQLALCHEMY_DATABASE_URI配置: {fixed_line}")
                
                # 写回文件
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("配置文件已更新")
            else:
                logger.info("SSL配置已存在，无需更新")
        else:
            # 添加Render数据库配置
            logger.info("添加Render数据库配置")
            
            # 检查是否已有Config类定义
            config_class_pattern = r'class\s+Config\s*\(.*\)\s*:'
            if re.search(config_class_pattern, content):
                # 查找Config类中的SQLALCHEMY_DATABASE_URI定义
                uri_pattern = r'(SQLALCHEMY_DATABASE_URI\s*=\s*.*)'
                uri_matches = re.findall(uri_pattern, content)
                
                if uri_matches:
                    # 替换为从环境变量获取
                    new_uri_line = "    SQLALCHEMY_DATABASE_URI = os.environ.get('RENDER_DB_URL', 'sqlite:///app.db')"
                    content = content.replace(uri_matches[0], new_uri_line)
                    
                    # 添加SSL连接池配置
                    pool_config = """
    # PostgreSQL连接池配置
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
"""
                    # 在Config类中添加配置
                    content = content.replace('class Config', f'class Config{pool_config}')
                    
                else:
                    # 在Config类中添加
                    config_pattern = r'(class\s+Config\s*\(.*\)\s*:)'
                    new_config = r'\1\n    SQLALCHEMY_DATABASE_URI = os.environ.get(\'RENDER_DB_URL\', \'sqlite:///app.db\')\n    # PostgreSQL连接池配置\n    if SQLALCHEMY_DATABASE_URI.startswith(\'postgresql\'):\n        SQLALCHEMY_ENGINE_OPTIONS = {\n            \'pool_size\': 10,\n            \'max_overflow\': 20,\n            \'pool_recycle\': 3600,\n            \'pool_pre_ping\': True\n        }'
                    content = re.sub(config_pattern, new_config, content)
            else:
                # 添加新的Config类
                config_class = """
class Config:
    # 从环境变量获取数据库URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('RENDER_DB_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL连接池配置
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
"""
                # 确保导入os模块
                if 'import os' not in content:
                    content = "import os\n" + content
                
                # 添加配置类
                content += config_class
            
            # 写回文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("配置文件已更新，添加了Render数据库配置")
            
        return True
    except Exception as e:
        logger.error(f"更新配置文件失败: {str(e)}")
        return False

def create_render_db_connection():
    """创建Render数据库连接模块"""
    file_path = 'render_db_connection.py'
    
    # 如果文件已存在，备份它
    if os.path.exists(file_path):
        backup_file(file_path)
    
    # 创建新的连接模块
    content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Render PostgreSQL 数据库连接
为应用程序提供连接Render PostgreSQL数据库的工具函数
\"\"\"

import os
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# 全局变量
db = SQLAlchemy()

def parse_db_url(url):
    \"\"\"解析数据库URL，提取连接参数\"\"\"
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
    \"\"\"获取数据库URL，优先使用环境变量\"\"\"
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
    \"\"\"创建数据库引擎\"\"\"
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
    \"\"\"创建数据库会话\"\"\"
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(session_factory)

def init_app(app):
    \"\"\"初始化Flask应用的数据库连接\"\"\"
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
    \"\"\"测试数据库连接\"\"\"
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
"""
    
    # 写入文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建Render数据库连接模块: {file_path}")
        return True
    except Exception as e:
        logger.error(f"创建Render数据库连接模块失败: {str(e)}")
        return False

def update_app_init():
    """更新app/__init__.py文件"""
    file_path = 'app/__init__.py'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查导入db语句
        if 'from flask_sqlalchemy import SQLAlchemy' in content:
            # 替换为导入自定义db
            logger.info("更新数据库导入语句")
            content = content.replace(
                'from flask_sqlalchemy import SQLAlchemy', 
                '# 使用自定义数据库连接模块\nfrom render_db_connection import db, init_app as init_db'
            )
            
            # 删除原始db定义
            if 'db = SQLAlchemy()' in content:
                content = content.replace('db = SQLAlchemy()', '# db已从render_db_connection导入')
            
            # 更新初始化方法
            init_pattern = r'(def\s+create_app\([^)]*\):.*?)(db\.init_app\(app\))'
            if re.search(init_pattern, content, re.DOTALL):
                content = re.sub(
                    init_pattern, 
                    r'\1init_db(app)',
                    content,
                    flags=re.DOTALL
                )
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("已更新app/__init__.py文件")
            return True
        else:
            logger.info("未找到SQLAlchemy导入语句，文件可能已更新")
            return True
    except Exception as e:
        logger.error(f"更新app/__init__.py失败: {str(e)}")
        return False

def update_run_py():
    """更新run.py文件"""
    file_path = 'run.py'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含数据库初始化代码
        if 'from app import create_app' in content:
            # 添加数据库初始化和检查
            if 'from render_db_connection import' not in content:
                # 替换导入语句
                content = content.replace(
                    'from app import create_app',
                    'from app import create_app\nfrom render_db_connection import test_connection'
                )
                
                # 添加连接测试
                if 'if __name__ == \'__main__\':' in content:
                    # 在主函数前添加连接测试
                    main_pattern = r'(if\s+__name__\s*==\s*[\'\"]__main__[\'\"].*?)'
                    content = re.sub(
                        main_pattern,
                        r'\1\n    # 测试数据库连接\n    test_connection()\n',
                        content,
                        flags=re.DOTALL
                    )
                
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("已更新run.py文件")
            else:
                logger.info("run.py文件已包含数据库连接代码")
            return True
        else:
            logger.warning("未找到app导入语句，无法更新run.py")
            return False
    except Exception as e:
        logger.error(f"更新run.py失败: {str(e)}")
        return False

def update_requirements():
    """更新requirements.txt文件"""
    file_path = 'requirements.txt'
    
    # 备份文件
    backup_file(file_path)
    
    try:
        # 读取现有需求
        requirements = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                requirements = [line.strip() for line in f.readlines()]
        
        # 检查是否已包含psycopg2
        has_psycopg2 = any(req.startswith('psycopg2') for req in requirements)
        
        if not has_psycopg2:
            # 添加PostgreSQL驱动
            requirements.append('psycopg2-binary==2.9.9')
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(requirements) + '\n')
            logger.info("已更新requirements.txt文件，添加了psycopg2-binary")
        else:
            logger.info("requirements.txt已包含PostgreSQL驱动")
        
        return True
    except Exception as e:
        logger.error(f"更新requirements.txt失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始修复应用程序配置...")
    
    # 1. 更新配置文件
    if update_config_file():
        logger.info("配置文件更新成功")
    else:
        logger.error("配置文件更新失败")
    
    # 2. 创建Render数据库连接模块
    if create_render_db_connection():
        logger.info("Render数据库连接模块创建成功")
    else:
        logger.error("Render数据库连接模块创建失败")
    
    # 3. 更新app/__init__.py
    if update_app_init():
        logger.info("app/__init__.py更新成功")
    else:
        logger.error("app/__init__.py更新失败")
    
    # 4. 更新run.py
    if update_run_py():
        logger.info("run.py更新成功")
    else:
        logger.error("run.py更新失败")
    
    # 5. 更新requirements.txt
    if update_requirements():
        logger.info("requirements.txt更新成功")
    else:
        logger.error("requirements.txt更新失败")
    
    logger.info("应用程序配置修复完成")
    print("\n修复完成后的操作步骤:")
    print("1. 设置环境变量: export RENDER_DB_URL=\"postgresql://用户名:密码@主机/数据库名?sslmode=require&sslrootcert=none\"")
    print("2. 安装依赖: pip install -r requirements.txt")
    print("3. 测试数据库连接: python render_db_connection.py")
    print("4. 启动应用: python run.py")

if __name__ == "__main__":
    main() 
 
 