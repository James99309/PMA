#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库SSL证书下载工具
用于下载和配置Render PostgreSQL的SSL证书
"""

import os
import sys
import logging
import argparse
import requests
import tempfile
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('证书下载器')

# Render PostgreSQL CA证书URL
# 注意：之前的URL不再可用，替换为新的URL
# 从文档中看，render现在不再提供单独的CA证书下载，而是通过SSL连接自动处理
# 作为临时解决方案，我们将创建一个自签名证书，以便测试SSL连接
RENDER_CA_CERT_URL = None  # 置空URL，将采用自签名证书方式

def download_cert(output_dir=None):
    """下载或创建SSL证书"""
    if not output_dir:
        # 使用系统证书目录或当前目录
        if sys.platform == 'darwin':  # macOS
            output_dir = '/usr/local/etc/ssl'
        elif sys.platform == 'linux':
            output_dir = '/etc/ssl/certs'
        else:
            output_dir = os.getcwd()
    
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 输出证书路径
    cert_path = os.path.join(output_dir, 'render-ca.crt')
    
    try:
        # 由于无法直接下载Render证书，我们创建一个自签名证书
        logger.info(f"创建自签名SSL证书用于测试...")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建自签名证书
            subprocess.run([
                'openssl', 'req', '-new', '-x509', '-days', '365', '-nodes',
                '-out', cert_path,
                '-keyout', os.path.join(temp_dir, 'render-ca.key'),
                '-subj', '/CN=render-postgres/O=Render/C=US'
            ], check=True)
        
        logger.info(f"自签名证书已创建: {cert_path}")
        logger.info(f"注意：这是一个自签名证书，仅用于测试。在生产环境中，您应使用Render提供的正确SSL设置。")
        return cert_path
    except Exception as e:
        logger.error(f"创建SSL证书失败: {str(e)}")
        logger.info(f"解决方案：在连接字符串中添加 '?ssl=true' 或 '?sslmode=require'，让Render自动处理SSL连接")
        return None

def configure_postgresql_client(cert_path):
    """配置PostgreSQL客户端使用证书"""
    # 获取PostgreSQL配置目录
    try:
        if sys.platform == 'darwin':  # macOS
            pg_config_paths = [
                '/usr/local/var/postgresql',
                '/usr/local/pgsql/data',
                '/opt/homebrew/var/postgres',
                os.path.expanduser('~/.postgresql')
            ]
        else:  # Linux
            pg_config_paths = [
                '/etc/postgresql',
                '/var/lib/pgsql/data',
                os.path.expanduser('~/.postgresql')
            ]
        
        # 查找或创建配置文件
        pg_config_path = None
        for path in pg_config_paths:
            if os.path.exists(path):
                pg_config_path = path
                break
        
        if not pg_config_path:
            pg_config_path = os.path.expanduser('~/.postgresql')
            os.makedirs(pg_config_path, exist_ok=True)
        
        # 设置环境变量
        ssl_env_var = f"PGSSLROOTCERT={cert_path}"
        logger.info(f"推荐设置环境变量: {ssl_env_var}")
        
        # 检查是否可以将环境变量添加到配置文件
        shell_configs = [
            (os.path.expanduser('~/.bashrc'), 'bash'),
            (os.path.expanduser('~/.zshrc'), 'zsh'),
            (os.path.expanduser('~/.profile'), 'profile')
        ]
        
        for config_file, shell_name in shell_configs:
            if os.path.exists(config_file):
                logger.info(f"可以将环境变量添加到 {config_file}")
                logger.info(f"运行: echo 'export {ssl_env_var}' >> {config_file}")
        
        return True
    except Exception as e:
        logger.error(f"配置PostgreSQL客户端失败: {str(e)}")
        return False

def test_connection(database_url, cert_path):
    """测试使用证书连接数据库"""
    try:
        logger.info("测试使用证书连接...")
        
        # 创建临时环境用于测试
        env = os.environ.copy()
        env['PGSSLROOTCERT'] = cert_path
        env['PGSSLMODE'] = 'verify-ca'
        
        # 从URL提取连接信息
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        host = parsed.hostname
        port = parsed.port or 5432
        user = parsed.username
        database = parsed.path.lstrip('/')
        
        # 构建psql命令行
        cmd = f"psql -h {host} -p {port} -U {user} -d {database} -c 'SELECT version();'"
        
        logger.info(f"执行测试命令: {cmd}")
        
        # 使用临时文件存储密码，避免命令行可见
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp:
            temp_path = temp.name
            password = parsed.password
            if password:
                temp.write(password)
                temp.flush()
                env['PGPASSFILE'] = temp_path
        
        # 执行psql命令
        process = subprocess.run(
            cmd, 
            shell=True, 
            env=env, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 删除临时密码文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        
        # 检查结果
        if process.returncode == 0:
            logger.info("连接测试成功!")
            logger.info(process.stdout)
            return True
        else:
            logger.error("连接测试失败!")
            logger.error(process.stderr)
            return False
    except Exception as e:
        logger.error(f"测试连接失败: {str(e)}")
        return False

def generate_connection_examples(database_url, cert_path):
    """生成使用证书的连接示例"""
    logger.info("\n=== 连接示例 ===")
    
    # SQLAlchemy连接示例
    logger.info("SQLAlchemy连接:")
    logger.info(f"""
from sqlalchemy import create_engine

# 方法1: 设置环境变量
import os
os.environ['PGSSLROOTCERT'] = '{cert_path}'

# 创建引擎 - 方法1：使用证书
engine = create_engine(
    '{database_url}?sslmode=verify-ca',
    connect_args={{
        'sslrootcert': '{cert_path}'
    }}
)

# 方法2: 更简单的方式，不需要证书文件
engine_simple = create_engine('{database_url}?ssl=true')
    """.strip())
    
    # psycopg2连接示例
    logger.info("\npsycopg2连接:")
    logger.info(f"""
import psycopg2

# 方法1：使用证书进行连接
conn = psycopg2.connect(
    '{database_url}',
    sslmode='verify-ca',
    sslrootcert='{cert_path}'
)

# 方法2：更简单的方式，不需要证书文件
conn_simple = psycopg2.connect('{database_url}?ssl=true')
    """.strip())
    
    # 命令行连接示例
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432
    user = parsed.username
    database = parsed.path.lstrip('/')
    
    logger.info("\n命令行连接:")
    logger.info(f"""
# 方法1：设置环境变量并使用证书
export PGSSLROOTCERT='{cert_path}'
export PGSSLMODE='verify-ca'

# 连接数据库
psql -h {host} -p {port} -U {user} -d {database}

# 方法2：更简单的方式，不需要证书文件
psql "postgresql://{user}:PASSWORD@{host}:{port}/{database}?ssl=true"
    """.strip())

def main():
    parser = argparse.ArgumentParser(description='Render数据库SSL证书下载工具')
    parser.add_argument('--db-url', help='数据库URL，用于测试连接')
    parser.add_argument('--output-dir', help='保存证书的目录')
    args = parser.parse_args()
    
    # 下载证书
    cert_path = download_cert(args.output_dir)
    if not cert_path:
        logger.info("提示：无法下载或创建证书，但您仍然可以使用'?ssl=true'参数连接到Render数据库")
        logger.info("示例：postgresql://user:password@host:port/database?ssl=true")
        sys.exit(1)
    
    # 配置PostgreSQL客户端
    configure_postgresql_client(cert_path)
    
    # 如果提供了数据库URL，测试连接
    if args.db_url:
        from urllib.parse import urlparse
        parsed = urlparse(args.db_url)
        masked_url = args.db_url
        if parsed.password:
            masked_url = args.db_url.replace(parsed.password, '********')
        logger.info(f"使用URL测试连接: {masked_url}")
        
        test_connection(args.db_url, cert_path)
        
        # 生成连接示例
        generate_connection_examples(args.db_url, cert_path)
    
    logger.info("\n证书配置完成!")
    logger.info(f"证书路径: {cert_path}")
    logger.info("推荐连接方式: 在连接字符串中添加 '?ssl=true' 参数，例如:")
    logger.info("postgresql://user:password@host:port/database?ssl=true")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render数据库SSL证书下载工具
用于下载和配置Render PostgreSQL的SSL证书
"""

import os
import sys
import logging
import argparse
import requests
import tempfile
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('证书下载器')

# Render PostgreSQL CA证书URL
# 注意：之前的URL不再可用，替换为新的URL
# 从文档中看，render现在不再提供单独的CA证书下载，而是通过SSL连接自动处理
# 作为临时解决方案，我们将创建一个自签名证书，以便测试SSL连接
RENDER_CA_CERT_URL = None  # 置空URL，将采用自签名证书方式

def download_cert(output_dir=None):
    """下载或创建SSL证书"""
    if not output_dir:
        # 使用系统证书目录或当前目录
        if sys.platform == 'darwin':  # macOS
            output_dir = '/usr/local/etc/ssl'
        elif sys.platform == 'linux':
            output_dir = '/etc/ssl/certs'
        else:
            output_dir = os.getcwd()
    
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 输出证书路径
    cert_path = os.path.join(output_dir, 'render-ca.crt')
    
    try:
        # 由于无法直接下载Render证书，我们创建一个自签名证书
        logger.info(f"创建自签名SSL证书用于测试...")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建自签名证书
            subprocess.run([
                'openssl', 'req', '-new', '-x509', '-days', '365', '-nodes',
                '-out', cert_path,
                '-keyout', os.path.join(temp_dir, 'render-ca.key'),
                '-subj', '/CN=render-postgres/O=Render/C=US'
            ], check=True)
        
        logger.info(f"自签名证书已创建: {cert_path}")
        logger.info(f"注意：这是一个自签名证书，仅用于测试。在生产环境中，您应使用Render提供的正确SSL设置。")
        return cert_path
    except Exception as e:
        logger.error(f"创建SSL证书失败: {str(e)}")
        logger.info(f"解决方案：在连接字符串中添加 '?ssl=true' 或 '?sslmode=require'，让Render自动处理SSL连接")
        return None

def configure_postgresql_client(cert_path):
    """配置PostgreSQL客户端使用证书"""
    # 获取PostgreSQL配置目录
    try:
        if sys.platform == 'darwin':  # macOS
            pg_config_paths = [
                '/usr/local/var/postgresql',
                '/usr/local/pgsql/data',
                '/opt/homebrew/var/postgres',
                os.path.expanduser('~/.postgresql')
            ]
        else:  # Linux
            pg_config_paths = [
                '/etc/postgresql',
                '/var/lib/pgsql/data',
                os.path.expanduser('~/.postgresql')
            ]
        
        # 查找或创建配置文件
        pg_config_path = None
        for path in pg_config_paths:
            if os.path.exists(path):
                pg_config_path = path
                break
        
        if not pg_config_path:
            pg_config_path = os.path.expanduser('~/.postgresql')
            os.makedirs(pg_config_path, exist_ok=True)
        
        # 设置环境变量
        ssl_env_var = f"PGSSLROOTCERT={cert_path}"
        logger.info(f"推荐设置环境变量: {ssl_env_var}")
        
        # 检查是否可以将环境变量添加到配置文件
        shell_configs = [
            (os.path.expanduser('~/.bashrc'), 'bash'),
            (os.path.expanduser('~/.zshrc'), 'zsh'),
            (os.path.expanduser('~/.profile'), 'profile')
        ]
        
        for config_file, shell_name in shell_configs:
            if os.path.exists(config_file):
                logger.info(f"可以将环境变量添加到 {config_file}")
                logger.info(f"运行: echo 'export {ssl_env_var}' >> {config_file}")
        
        return True
    except Exception as e:
        logger.error(f"配置PostgreSQL客户端失败: {str(e)}")
        return False

def test_connection(database_url, cert_path):
    """测试使用证书连接数据库"""
    try:
        logger.info("测试使用证书连接...")
        
        # 创建临时环境用于测试
        env = os.environ.copy()
        env['PGSSLROOTCERT'] = cert_path
        env['PGSSLMODE'] = 'verify-ca'
        
        # 从URL提取连接信息
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        host = parsed.hostname
        port = parsed.port or 5432
        user = parsed.username
        database = parsed.path.lstrip('/')
        
        # 构建psql命令行
        cmd = f"psql -h {host} -p {port} -U {user} -d {database} -c 'SELECT version();'"
        
        logger.info(f"执行测试命令: {cmd}")
        
        # 使用临时文件存储密码，避免命令行可见
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp:
            temp_path = temp.name
            password = parsed.password
            if password:
                temp.write(password)
                temp.flush()
                env['PGPASSFILE'] = temp_path
        
        # 执行psql命令
        process = subprocess.run(
            cmd, 
            shell=True, 
            env=env, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 删除临时密码文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        
        # 检查结果
        if process.returncode == 0:
            logger.info("连接测试成功!")
            logger.info(process.stdout)
            return True
        else:
            logger.error("连接测试失败!")
            logger.error(process.stderr)
            return False
    except Exception as e:
        logger.error(f"测试连接失败: {str(e)}")
        return False

def generate_connection_examples(database_url, cert_path):
    """生成使用证书的连接示例"""
    logger.info("\n=== 连接示例 ===")
    
    # SQLAlchemy连接示例
    logger.info("SQLAlchemy连接:")
    logger.info(f"""
from sqlalchemy import create_engine

# 方法1: 设置环境变量
import os
os.environ['PGSSLROOTCERT'] = '{cert_path}'

# 创建引擎 - 方法1：使用证书
engine = create_engine(
    '{database_url}?sslmode=verify-ca',
    connect_args={{
        'sslrootcert': '{cert_path}'
    }}
)

# 方法2: 更简单的方式，不需要证书文件
engine_simple = create_engine('{database_url}?ssl=true')
    """.strip())
    
    # psycopg2连接示例
    logger.info("\npsycopg2连接:")
    logger.info(f"""
import psycopg2

# 方法1：使用证书进行连接
conn = psycopg2.connect(
    '{database_url}',
    sslmode='verify-ca',
    sslrootcert='{cert_path}'
)

# 方法2：更简单的方式，不需要证书文件
conn_simple = psycopg2.connect('{database_url}?ssl=true')
    """.strip())
    
    # 命令行连接示例
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432
    user = parsed.username
    database = parsed.path.lstrip('/')
    
    logger.info("\n命令行连接:")
    logger.info(f"""
# 方法1：设置环境变量并使用证书
export PGSSLROOTCERT='{cert_path}'
export PGSSLMODE='verify-ca'

# 连接数据库
psql -h {host} -p {port} -U {user} -d {database}

# 方法2：更简单的方式，不需要证书文件
psql "postgresql://{user}:PASSWORD@{host}:{port}/{database}?ssl=true"
    """.strip())

def main():
    parser = argparse.ArgumentParser(description='Render数据库SSL证书下载工具')
    parser.add_argument('--db-url', help='数据库URL，用于测试连接')
    parser.add_argument('--output-dir', help='保存证书的目录')
    args = parser.parse_args()
    
    # 下载证书
    cert_path = download_cert(args.output_dir)
    if not cert_path:
        logger.info("提示：无法下载或创建证书，但您仍然可以使用'?ssl=true'参数连接到Render数据库")
        logger.info("示例：postgresql://user:password@host:port/database?ssl=true")
        sys.exit(1)
    
    # 配置PostgreSQL客户端
    configure_postgresql_client(cert_path)
    
    # 如果提供了数据库URL，测试连接
    if args.db_url:
        from urllib.parse import urlparse
        parsed = urlparse(args.db_url)
        masked_url = args.db_url
        if parsed.password:
            masked_url = args.db_url.replace(parsed.password, '********')
        logger.info(f"使用URL测试连接: {masked_url}")
        
        test_connection(args.db_url, cert_path)
        
        # 生成连接示例
        generate_connection_examples(args.db_url, cert_path)
    
    logger.info("\n证书配置完成!")
    logger.info(f"证书路径: {cert_path}")
    logger.info("推荐连接方式: 在连接字符串中添加 '?ssl=true' 参数，例如:")
    logger.info("postgresql://user:password@host:port/database?ssl=true")

if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
Render数据库SSL证书下载工具
用于下载和配置Render PostgreSQL的SSL证书
"""

import os
import sys
import logging
import argparse
import requests
import tempfile
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('证书下载器')

# Render PostgreSQL CA证书URL
# 注意：之前的URL不再可用，替换为新的URL
# 从文档中看，render现在不再提供单独的CA证书下载，而是通过SSL连接自动处理
# 作为临时解决方案，我们将创建一个自签名证书，以便测试SSL连接
RENDER_CA_CERT_URL = None  # 置空URL，将采用自签名证书方式

def download_cert(output_dir=None):
    """下载或创建SSL证书"""
    if not output_dir:
        # 使用系统证书目录或当前目录
        if sys.platform == 'darwin':  # macOS
            output_dir = '/usr/local/etc/ssl'
        elif sys.platform == 'linux':
            output_dir = '/etc/ssl/certs'
        else:
            output_dir = os.getcwd()
    
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 输出证书路径
    cert_path = os.path.join(output_dir, 'render-ca.crt')
    
    try:
        # 由于无法直接下载Render证书，我们创建一个自签名证书
        logger.info(f"创建自签名SSL证书用于测试...")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建自签名证书
            subprocess.run([
                'openssl', 'req', '-new', '-x509', '-days', '365', '-nodes',
                '-out', cert_path,
                '-keyout', os.path.join(temp_dir, 'render-ca.key'),
                '-subj', '/CN=render-postgres/O=Render/C=US'
            ], check=True)
        
        logger.info(f"自签名证书已创建: {cert_path}")
        logger.info(f"注意：这是一个自签名证书，仅用于测试。在生产环境中，您应使用Render提供的正确SSL设置。")
        return cert_path
    except Exception as e:
        logger.error(f"创建SSL证书失败: {str(e)}")
        logger.info(f"解决方案：在连接字符串中添加 '?ssl=true' 或 '?sslmode=require'，让Render自动处理SSL连接")
        return None

def configure_postgresql_client(cert_path):
    """配置PostgreSQL客户端使用证书"""
    # 获取PostgreSQL配置目录
    try:
        if sys.platform == 'darwin':  # macOS
            pg_config_paths = [
                '/usr/local/var/postgresql',
                '/usr/local/pgsql/data',
                '/opt/homebrew/var/postgres',
                os.path.expanduser('~/.postgresql')
            ]
        else:  # Linux
            pg_config_paths = [
                '/etc/postgresql',
                '/var/lib/pgsql/data',
                os.path.expanduser('~/.postgresql')
            ]
        
        # 查找或创建配置文件
        pg_config_path = None
        for path in pg_config_paths:
            if os.path.exists(path):
                pg_config_path = path
                break
        
        if not pg_config_path:
            pg_config_path = os.path.expanduser('~/.postgresql')
            os.makedirs(pg_config_path, exist_ok=True)
        
        # 设置环境变量
        ssl_env_var = f"PGSSLROOTCERT={cert_path}"
        logger.info(f"推荐设置环境变量: {ssl_env_var}")
        
        # 检查是否可以将环境变量添加到配置文件
        shell_configs = [
            (os.path.expanduser('~/.bashrc'), 'bash'),
            (os.path.expanduser('~/.zshrc'), 'zsh'),
            (os.path.expanduser('~/.profile'), 'profile')
        ]
        
        for config_file, shell_name in shell_configs:
            if os.path.exists(config_file):
                logger.info(f"可以将环境变量添加到 {config_file}")
                logger.info(f"运行: echo 'export {ssl_env_var}' >> {config_file}")
        
        return True
    except Exception as e:
        logger.error(f"配置PostgreSQL客户端失败: {str(e)}")
        return False

def test_connection(database_url, cert_path):
    """测试使用证书连接数据库"""
    try:
        logger.info("测试使用证书连接...")
        
        # 创建临时环境用于测试
        env = os.environ.copy()
        env['PGSSLROOTCERT'] = cert_path
        env['PGSSLMODE'] = 'verify-ca'
        
        # 从URL提取连接信息
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        host = parsed.hostname
        port = parsed.port or 5432
        user = parsed.username
        database = parsed.path.lstrip('/')
        
        # 构建psql命令行
        cmd = f"psql -h {host} -p {port} -U {user} -d {database} -c 'SELECT version();'"
        
        logger.info(f"执行测试命令: {cmd}")
        
        # 使用临时文件存储密码，避免命令行可见
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp:
            temp_path = temp.name
            password = parsed.password
            if password:
                temp.write(password)
                temp.flush()
                env['PGPASSFILE'] = temp_path
        
        # 执行psql命令
        process = subprocess.run(
            cmd, 
            shell=True, 
            env=env, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 删除临时密码文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        
        # 检查结果
        if process.returncode == 0:
            logger.info("连接测试成功!")
            logger.info(process.stdout)
            return True
        else:
            logger.error("连接测试失败!")
            logger.error(process.stderr)
            return False
    except Exception as e:
        logger.error(f"测试连接失败: {str(e)}")
        return False

def generate_connection_examples(database_url, cert_path):
    """生成使用证书的连接示例"""
    logger.info("\n=== 连接示例 ===")
    
    # SQLAlchemy连接示例
    logger.info("SQLAlchemy连接:")
    logger.info(f"""
from sqlalchemy import create_engine

# 方法1: 设置环境变量
import os
os.environ['PGSSLROOTCERT'] = '{cert_path}'

# 创建引擎 - 方法1：使用证书
engine = create_engine(
    '{database_url}?sslmode=verify-ca',
    connect_args={{
        'sslrootcert': '{cert_path}'
    }}
)

# 方法2: 更简单的方式，不需要证书文件
engine_simple = create_engine('{database_url}?ssl=true')
    """.strip())
    
    # psycopg2连接示例
    logger.info("\npsycopg2连接:")
    logger.info(f"""
import psycopg2

# 方法1：使用证书进行连接
conn = psycopg2.connect(
    '{database_url}',
    sslmode='verify-ca',
    sslrootcert='{cert_path}'
)

# 方法2：更简单的方式，不需要证书文件
conn_simple = psycopg2.connect('{database_url}?ssl=true')
    """.strip())
    
    # 命令行连接示例
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432
    user = parsed.username
    database = parsed.path.lstrip('/')
    
    logger.info("\n命令行连接:")
    logger.info(f"""
# 方法1：设置环境变量并使用证书
export PGSSLROOTCERT='{cert_path}'
export PGSSLMODE='verify-ca'

# 连接数据库
psql -h {host} -p {port} -U {user} -d {database}

# 方法2：更简单的方式，不需要证书文件
psql "postgresql://{user}:PASSWORD@{host}:{port}/{database}?ssl=true"
    """.strip())

def main():
    parser = argparse.ArgumentParser(description='Render数据库SSL证书下载工具')
    parser.add_argument('--db-url', help='数据库URL，用于测试连接')
    parser.add_argument('--output-dir', help='保存证书的目录')
    args = parser.parse_args()
    
    # 下载证书
    cert_path = download_cert(args.output_dir)
    if not cert_path:
        logger.info("提示：无法下载或创建证书，但您仍然可以使用'?ssl=true'参数连接到Render数据库")
        logger.info("示例：postgresql://user:password@host:port/database?ssl=true")
        sys.exit(1)
    
    # 配置PostgreSQL客户端
    configure_postgresql_client(cert_path)
    
    # 如果提供了数据库URL，测试连接
    if args.db_url:
        from urllib.parse import urlparse
        parsed = urlparse(args.db_url)
        masked_url = args.db_url
        if parsed.password:
            masked_url = args.db_url.replace(parsed.password, '********')
        logger.info(f"使用URL测试连接: {masked_url}")
        
        test_connection(args.db_url, cert_path)
        
        # 生成连接示例
        generate_connection_examples(args.db_url, cert_path)
    
    logger.info("\n证书配置完成!")
    logger.info(f"证书路径: {cert_path}")
    logger.info("推荐连接方式: 在连接字符串中添加 '?ssl=true' 参数，例如:")
    logger.info("postgresql://user:password@host:port/database?ssl=true")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render数据库SSL证书下载工具
用于下载和配置Render PostgreSQL的SSL证书
"""

import os
import sys
import logging
import argparse
import requests
import tempfile
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('证书下载器')

# Render PostgreSQL CA证书URL
# 注意：之前的URL不再可用，替换为新的URL
# 从文档中看，render现在不再提供单独的CA证书下载，而是通过SSL连接自动处理
# 作为临时解决方案，我们将创建一个自签名证书，以便测试SSL连接
RENDER_CA_CERT_URL = None  # 置空URL，将采用自签名证书方式

def download_cert(output_dir=None):
    """下载或创建SSL证书"""
    if not output_dir:
        # 使用系统证书目录或当前目录
        if sys.platform == 'darwin':  # macOS
            output_dir = '/usr/local/etc/ssl'
        elif sys.platform == 'linux':
            output_dir = '/etc/ssl/certs'
        else:
            output_dir = os.getcwd()
    
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 输出证书路径
    cert_path = os.path.join(output_dir, 'render-ca.crt')
    
    try:
        # 由于无法直接下载Render证书，我们创建一个自签名证书
        logger.info(f"创建自签名SSL证书用于测试...")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建自签名证书
            subprocess.run([
                'openssl', 'req', '-new', '-x509', '-days', '365', '-nodes',
                '-out', cert_path,
                '-keyout', os.path.join(temp_dir, 'render-ca.key'),
                '-subj', '/CN=render-postgres/O=Render/C=US'
            ], check=True)
        
        logger.info(f"自签名证书已创建: {cert_path}")
        logger.info(f"注意：这是一个自签名证书，仅用于测试。在生产环境中，您应使用Render提供的正确SSL设置。")
        return cert_path
    except Exception as e:
        logger.error(f"创建SSL证书失败: {str(e)}")
        logger.info(f"解决方案：在连接字符串中添加 '?ssl=true' 或 '?sslmode=require'，让Render自动处理SSL连接")
        return None

def configure_postgresql_client(cert_path):
    """配置PostgreSQL客户端使用证书"""
    # 获取PostgreSQL配置目录
    try:
        if sys.platform == 'darwin':  # macOS
            pg_config_paths = [
                '/usr/local/var/postgresql',
                '/usr/local/pgsql/data',
                '/opt/homebrew/var/postgres',
                os.path.expanduser('~/.postgresql')
            ]
        else:  # Linux
            pg_config_paths = [
                '/etc/postgresql',
                '/var/lib/pgsql/data',
                os.path.expanduser('~/.postgresql')
            ]
        
        # 查找或创建配置文件
        pg_config_path = None
        for path in pg_config_paths:
            if os.path.exists(path):
                pg_config_path = path
                break
        
        if not pg_config_path:
            pg_config_path = os.path.expanduser('~/.postgresql')
            os.makedirs(pg_config_path, exist_ok=True)
        
        # 设置环境变量
        ssl_env_var = f"PGSSLROOTCERT={cert_path}"
        logger.info(f"推荐设置环境变量: {ssl_env_var}")
        
        # 检查是否可以将环境变量添加到配置文件
        shell_configs = [
            (os.path.expanduser('~/.bashrc'), 'bash'),
            (os.path.expanduser('~/.zshrc'), 'zsh'),
            (os.path.expanduser('~/.profile'), 'profile')
        ]
        
        for config_file, shell_name in shell_configs:
            if os.path.exists(config_file):
                logger.info(f"可以将环境变量添加到 {config_file}")
                logger.info(f"运行: echo 'export {ssl_env_var}' >> {config_file}")
        
        return True
    except Exception as e:
        logger.error(f"配置PostgreSQL客户端失败: {str(e)}")
        return False

def test_connection(database_url, cert_path):
    """测试使用证书连接数据库"""
    try:
        logger.info("测试使用证书连接...")
        
        # 创建临时环境用于测试
        env = os.environ.copy()
        env['PGSSLROOTCERT'] = cert_path
        env['PGSSLMODE'] = 'verify-ca'
        
        # 从URL提取连接信息
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        host = parsed.hostname
        port = parsed.port or 5432
        user = parsed.username
        database = parsed.path.lstrip('/')
        
        # 构建psql命令行
        cmd = f"psql -h {host} -p {port} -U {user} -d {database} -c 'SELECT version();'"
        
        logger.info(f"执行测试命令: {cmd}")
        
        # 使用临时文件存储密码，避免命令行可见
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp:
            temp_path = temp.name
            password = parsed.password
            if password:
                temp.write(password)
                temp.flush()
                env['PGPASSFILE'] = temp_path
        
        # 执行psql命令
        process = subprocess.run(
            cmd, 
            shell=True, 
            env=env, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 删除临时密码文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        
        # 检查结果
        if process.returncode == 0:
            logger.info("连接测试成功!")
            logger.info(process.stdout)
            return True
        else:
            logger.error("连接测试失败!")
            logger.error(process.stderr)
            return False
    except Exception as e:
        logger.error(f"测试连接失败: {str(e)}")
        return False

def generate_connection_examples(database_url, cert_path):
    """生成使用证书的连接示例"""
    logger.info("\n=== 连接示例 ===")
    
    # SQLAlchemy连接示例
    logger.info("SQLAlchemy连接:")
    logger.info(f"""
from sqlalchemy import create_engine

# 方法1: 设置环境变量
import os
os.environ['PGSSLROOTCERT'] = '{cert_path}'

# 创建引擎 - 方法1：使用证书
engine = create_engine(
    '{database_url}?sslmode=verify-ca',
    connect_args={{
        'sslrootcert': '{cert_path}'
    }}
)

# 方法2: 更简单的方式，不需要证书文件
engine_simple = create_engine('{database_url}?ssl=true')
    """.strip())
    
    # psycopg2连接示例
    logger.info("\npsycopg2连接:")
    logger.info(f"""
import psycopg2

# 方法1：使用证书进行连接
conn = psycopg2.connect(
    '{database_url}',
    sslmode='verify-ca',
    sslrootcert='{cert_path}'
)

# 方法2：更简单的方式，不需要证书文件
conn_simple = psycopg2.connect('{database_url}?ssl=true')
    """.strip())
    
    # 命令行连接示例
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432
    user = parsed.username
    database = parsed.path.lstrip('/')
    
    logger.info("\n命令行连接:")
    logger.info(f"""
# 方法1：设置环境变量并使用证书
export PGSSLROOTCERT='{cert_path}'
export PGSSLMODE='verify-ca'

# 连接数据库
psql -h {host} -p {port} -U {user} -d {database}

# 方法2：更简单的方式，不需要证书文件
psql "postgresql://{user}:PASSWORD@{host}:{port}/{database}?ssl=true"
    """.strip())

def main():
    parser = argparse.ArgumentParser(description='Render数据库SSL证书下载工具')
    parser.add_argument('--db-url', help='数据库URL，用于测试连接')
    parser.add_argument('--output-dir', help='保存证书的目录')
    args = parser.parse_args()
    
    # 下载证书
    cert_path = download_cert(args.output_dir)
    if not cert_path:
        logger.info("提示：无法下载或创建证书，但您仍然可以使用'?ssl=true'参数连接到Render数据库")
        logger.info("示例：postgresql://user:password@host:port/database?ssl=true")
        sys.exit(1)
    
    # 配置PostgreSQL客户端
    configure_postgresql_client(cert_path)
    
    # 如果提供了数据库URL，测试连接
    if args.db_url:
        from urllib.parse import urlparse
        parsed = urlparse(args.db_url)
        masked_url = args.db_url
        if parsed.password:
            masked_url = args.db_url.replace(parsed.password, '********')
        logger.info(f"使用URL测试连接: {masked_url}")
        
        test_connection(args.db_url, cert_path)
        
        # 生成连接示例
        generate_connection_examples(args.db_url, cert_path)
    
    logger.info("\n证书配置完成!")
    logger.info(f"证书路径: {cert_path}")
    logger.info("推荐连接方式: 在连接字符串中添加 '?ssl=true' 参数，例如:")
    logger.info("postgresql://user:password@host:port/database?ssl=true")

if __name__ == "__main__":
    main() 
 
 