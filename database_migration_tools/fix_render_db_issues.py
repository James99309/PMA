#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库SSL连接问题修复工具
用于快速诊断和修复Render PostgreSQL数据库SSL连接问题
"""

import os
import sys
import logging
import argparse
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render数据库修复工具')

def parse_database_url(database_url):
    """解析数据库URL并返回各个组件"""
    # 确保URL以postgresql://开头
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("将 'postgres://' 替换为 'postgresql://'")
    
    # 解析URL
    parsed = urlparse(database_url)
    
    # 提取查询参数
    query_params = parse_qs(parsed.query)
    
    return {
        'scheme': parsed.scheme,
        'username': parsed.username,
        'password': parsed.password,
        'hostname': parsed.hostname,
        'port': parsed.port,
        'path': parsed.path.lstrip('/'),
        'query_params': query_params
    }

def build_database_url(components):
    """根据组件重建数据库URL"""
    netloc = ''
    if components['username']:
        netloc = components['username']
        if components['password']:
            netloc += ':' + components['password']
        netloc += '@'
    
    netloc += components['hostname']
    if components['port']:
        netloc += ':' + str(components['port'])
    
    # 创建查询字符串
    query_string = urlencode(components['query_params'], doseq=True)
    
    # 构建URL
    url = urlunparse((
        components['scheme'],
        netloc,
        '/' + components['path'],
        '',
        query_string,
        ''
    ))
    
    return url

def mask_password(database_url):
    """隐藏URL中的密码"""
    if not database_url:
        return None
        
    parsed = urlparse(database_url)
    if parsed.password:
        masked_url = database_url.replace(parsed.password, '********')
        return masked_url
    return database_url

def fix_ssl_issues(database_url):
    """修复SSL相关问题"""
    logger.info(f"分析数据库URL: {mask_password(database_url)}")
    
    # 解析URL
    components = parse_database_url(database_url)
    
    # 检查是否已有SSL参数
    query_params = components['query_params']
    ssl_params = {'ssl', 'sslmode', 'sslrootcert', 'sslcert', 'sslkey'}
    
    has_ssl_param = any(param in query_params for param in ssl_params)
    
    # 如果没有SSL参数，添加最简单的SSL参数
    if not has_ssl_param:
        logger.info("未找到SSL参数，添加简单的SSL配置")
        # 使用sslmode=require代替ssl=true，因为后者在某些版本可能不起作用
        query_params['sslmode'] = ['require']
        components['query_params'] = query_params
        
        # 重建URL
        fixed_url = build_database_url(components)
        logger.info(f"已修复的URL: {mask_password(fixed_url)}")
        return fixed_url
    
    # 如果有sslmode参数但值不够安全，建议更严格的模式
    if 'sslmode' in query_params:
        sslmode = query_params['sslmode'][0]
        if sslmode in ['disable', 'allow', 'prefer']:
            logger.info(f"发现不安全的sslmode: {sslmode}，推荐使用 'require' 或更高安全级别")
            query_params['sslmode'] = ['require']
            components['query_params'] = query_params
            
            # 重建URL
            fixed_url = build_database_url(components)
            logger.info(f"已修复的URL: {mask_password(fixed_url)}")
            return fixed_url
    
    # 如果URL已包含适当的SSL参数，不需要修改
    logger.info("URL已包含适当的SSL参数，无需修改")
    return database_url

def fix_connection_issues(database_url):
    """修复连接相关问题"""
    logger.info("检查连接问题...")
    
    # 解析URL
    components = parse_database_url(database_url)
    
    # 确保scheme是postgresql
    if components['scheme'] != 'postgresql':
        logger.info(f"不正确的scheme: {components['scheme']}，修改为 'postgresql'")
        components['scheme'] = 'postgresql'
    
    # 检查主机名格式
    hostname = components['hostname']
    render_pattern = r'[\w-]+\.[\w-]+\.render\.com'
    if hostname and not re.match(render_pattern, hostname):
        logger.warning(f"主机名 {hostname} 不符合 Render 标准格式 (*.render.com)")
    
    # 检查端口是否合理
    port = components['port']
    if port and port != 5432:
        logger.info(f"注意: 使用非标准PostgreSQL端口: {port} (标准端口为5432)")
    
    # 重建URL
    fixed_url = build_database_url(components)
    
    # 如果URL被修改，返回新URL
    if fixed_url != database_url:
        logger.info(f"修复连接问题后的URL: {mask_password(fixed_url)}")
        return fixed_url
    
    logger.info("未发现需要修复的连接问题")
    return database_url

def update_env_file(database_url):
    """尝试更新.env文件中的数据库URL"""
    env_file = '.env'
    if not os.path.isfile(env_file):
        logger.info(f"未找到 {env_file} 文件，无法自动更新环境变量")
        return False
    
    # 读取当前.env文件内容
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # 查找并替换DATABASE_URL
    db_url_pattern = re.compile(r'^(DATABASE_URL|RENDER_DB_URL|DB_URL)=(.*)$')
    updated = False
    
    for i, line in enumerate(lines):
        match = db_url_pattern.match(line.strip())
        if match:
            var_name = match.group(1)
            old_url = match.group(2)
            
            # 移除引号
            if (old_url.startswith('"') and old_url.endswith('"')) or \
               (old_url.startswith("'") and old_url.endswith("'")):
                old_url = old_url[1:-1]
            
            # 确保我们只替换整个URL，而不是部分匹配
            logger.info(f"在.env中找到数据库URL变量: {var_name}")
            logger.info(f"原始URL: {mask_password(old_url)}")
            logger.info(f"新URL: {mask_password(database_url)}")
            
            # 注释原行并添加新行
            lines[i] = f"# {line.strip()} (由Render数据库修复工具自动更新)\n"
            lines.insert(i + 1, f"{var_name}=\"{database_url}\"\n")
            
            updated = True
            break
    
    if updated:
        # 备份原文件
        backup_file = f"{env_file}.bak"
        with open(backup_file, 'w') as f:
            f.writelines(lines)
        
        # 写入新文件
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        logger.info(f"已更新 {env_file} 文件，原文件已备份为 {backup_file}")
        return True
    else:
        logger.info(f"在 {env_file} 中未找到数据库URL变量")
        return False

def test_ssl_connection(database_url):
    """测试SSL连接"""
    try:
        from sqlalchemy import create_engine, text
        
        logger.info("测试数据库连接...")
        engine = create_engine(database_url, connect_args={'connect_timeout': 30})
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功! PostgreSQL版本: {version}")
        
        return True
    except ImportError:
        logger.warning("未安装SQLAlchemy，无法进行连接测试")
        logger.info("请运行: pip install sqlalchemy psycopg2-binary")
        return None
    except Exception as e:
        logger.error(f"连接测试失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Render数据库SSL连接问题修复工具')
    parser.add_argument('--db-url', help='数据库URL')
    parser.add_argument('--update-env', action='store_true', help='更新.env文件中的数据库URL')
    parser.add_argument('--test', action='store_true', help='测试连接')
    args = parser.parse_args()
    
    # 获取数据库URL
    database_url = args.db_url
    
    # 如果未提供URL，尝试从环境变量获取
    if not database_url:
        for env_var in ['DATABASE_URL', 'RENDER_DB_URL', 'DB_URL']:
            if env_var in os.environ:
                database_url = os.environ[env_var]
                logger.info(f"从环境变量 {env_var} 获取数据库URL")
                break
    
    # 如果仍未找到URL，提示用户输入
    if not database_url:
        logger.info("未提供数据库URL，也未在环境变量中找到")
        print()
        database_url = input("请输入Render数据库URL: ")
        print()
    
    # 修复SSL问题
    fixed_url = fix_ssl_issues(database_url)
    
    # 修复连接问题
    fixed_url = fix_connection_issues(fixed_url)
    
    # 如果URL已被修复
    if fixed_url != database_url:
        logger.info("已修复数据库URL")
        logger.info(f"原始URL: {mask_password(database_url)}")
        logger.info(f"修复后URL: {mask_password(fixed_url)}")
        
        # 更新.env文件
        if args.update_env:
            update_env_file(fixed_url)
    else:
        logger.info("数据库URL不需要修复")
    
    # 测试连接
    if args.test:
        success = test_ssl_connection(fixed_url)
        if success:
            logger.info("SSL连接测试成功!")
            logger.info(f"您可以安全地使用以下URL连接到Render数据库:")
            logger.info(f"{mask_password(fixed_url)}")
        elif success is False:  # 区分失败和未测试
            logger.error("SSL连接测试失败，请参考上述错误信息进行排查")
    
    # 输出总结
    print("\n=== 摘要 ===")
    print(f"推荐使用的数据库URL:")
    print(f"{mask_password(fixed_url)}")
    print()
    print("建议的应用程序配置:")
    print(f"DATABASE_URL=\"{fixed_url}\"")
    print()
    print("使用方法:")
    print("1. 在.env文件或环境变量中设置上述URL")
    print("2. 确保你的应用支持SSL连接")
    print("3. 如果使用ORM框架，确保传递了正确的SSL参数")
    
if __name__ == "__main__":
    main() 