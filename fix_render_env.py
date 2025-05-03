#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render环境变量修复脚本
用于在Render服务上直接修复数据库连接信息

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
import json
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render环境修复')

# 正确的数据库连接信息
CORRECT_DB_INFO = {
    'host': 'dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com',
    'user': 'pma_db_sp8d_user',
    'password': 'LXNGJmR6bFrNecoaWbdbdzPpltIAd40w',
    'dbname': 'pma_db_sp8d',
    'port': 5432
}

# 错误的信息
INCORRECT_HOSTS = [
    'dpg-d0a6s03uibrs73b5nelg-a',
    'dpg-d0a6s03uibrs73b5nelg-a.singapore-postgres.render.com'
]

INCORRECT_USERS = [
    'pma_db_08cz_user'
]

def get_current_env():
    """获取当前环境变量中的数据库连接信息"""
    db_url = os.environ.get('DATABASE_URL', '')
    sqlalchemy_uri = os.environ.get('SQLALCHEMY_DATABASE_URI', '')
    
    logger.info(f"当前DATABASE_URL: {db_url.replace(db_url.split('@')[0] if '@' in db_url else '', '***')}")
    logger.info(f"当前SQLALCHEMY_DATABASE_URI: {sqlalchemy_uri.replace(sqlalchemy_uri.split('@')[0] if '@' in sqlalchemy_uri else '', '***')}")
    
    return db_url, sqlalchemy_uri

def create_correct_db_url():
    """创建正确的数据库URL"""
    db_info = CORRECT_DB_INFO
    db_url = f"postgresql://{db_info['user']}:{db_info['password']}@{db_info['host']}/{db_info['dbname']}"
    return db_url

def write_env_fix_commands():
    """创建环境变量修复命令文件"""
    correct_db_url = create_correct_db_url()
    
    commands = [
        "# Render环境变量修复命令",
        "# 运行: source fix_env.sh",
        "",
        f"export DATABASE_URL='{correct_db_url}'",
        f"export SQLALCHEMY_DATABASE_URI='{correct_db_url}'",
        "export PGSSLMODE='require'",
        "export SSL_MODE='require'",
        "export RENDER='true'",
        "",
        "echo '环境变量已更新:'",
        "echo \"DATABASE_URL=${DATABASE_URL}\"",
        "echo \"SQLALCHEMY_DATABASE_URI=${SQLALCHEMY_DATABASE_URI}\"",
        "echo \"PGSSLMODE=${PGSSLMODE}\"",
        ""
    ]
    
    with open("fix_env.sh", "w") as f:
        f.write("\n".join(commands))
    
    os.chmod("fix_env.sh", 0o755)
    logger.info("已创建环境变量修复脚本 fix_env.sh")

def generate_render_config_json():
    """生成Render环境配置JSON文件"""
    correct_db_url = create_correct_db_url()
    
    env_vars = {
        "DATABASE_URL": correct_db_url,
        "SQLALCHEMY_DATABASE_URI": correct_db_url,
        "PGSSLMODE": "require",
        "SSL_MODE": "require",
        "RENDER": "true"
    }
    
    with open("render_env_config.json", "w") as f:
        json.dump({"envVars": env_vars}, f, indent=2)
    
    logger.info("已生成Render环境配置JSON文件 render_env_config.json")
    logger.info("请在Render控制台中导入此配置文件以更新环境变量")

def create_test_connection_script():
    """创建测试连接脚本"""
    test_script = """#!/usr/bin/env python3
import os
import sys
import psycopg2

# 从环境变量获取数据库URL
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("错误: 未设置DATABASE_URL环境变量")
    sys.exit(1)

# 确保URL是postgresql://开头
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

print(f"测试连接到: {db_url.split('@')[1]}")

try:
    # 尝试连接
    conn = psycopg2.connect(db_url, sslmode='require')
    cursor = conn.cursor()
    
    # 执行简单查询
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f"连接成功! 数据库版本: {version[0]}")
    
    # 查询表信息
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    tables = cursor.fetchall()
    print(f"数据库中的表:")
    for table in tables:
        print(f"- {table[0]}")
    
    cursor.close()
    conn.close()
    print("测试完成，连接正常")
    sys.exit(0)
except Exception as e:
    print(f"连接失败: {e}")
    sys.exit(1)
"""
    
    with open("test_render_db.py", "w") as f:
        f.write(test_script)
    
    os.chmod("test_render_db.py", 0o755)
    logger.info("已创建数据库连接测试脚本 test_render_db.py")

def main():
    """主函数"""
    logger.info("开始Render环境修复...")
    
    # 获取当前环境变量
    get_current_env()
    
    # 创建修复脚本
    write_env_fix_commands()
    
    # 生成Render配置
    generate_render_config_json()
    
    # 创建测试连接脚本
    create_test_connection_script()
    
    logger.info("修复文件创建完成。请执行以下步骤:")
    logger.info("1. 在Render服务的Shell中运行: source fix_env.sh")
    logger.info("2. 测试连接: python test_render_db.py")
    logger.info("3. 在Render管理面板中更新环境变量")
    logger.info("4. 重启服务")

if __name__ == "__main__":
    main() 