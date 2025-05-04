#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 直接连接脚本
使用最简单的参数连接到Render PostgreSQL
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def parse_db_url(url):
    """解析数据库URL"""
    parsed = urlparse(url)
    
    db_info = {
        'dbname': parsed.path.strip('/'),
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port or 5432,
    }
    
    print(f"数据库信息:")
    print(f"  主机: {db_info['host']}")
    print(f"  端口: {db_info['port']}")
    print(f"  数据库: {db_info['dbname']}")
    print(f"  用户: {db_info['user']}")
    
    return db_info

def try_connect_options(db_info):
    """尝试不同的连接参数组合"""
    options = [
        {'sslmode': 'require'},
        {'sslmode': 'prefer'},
        {'sslmode': 'allow'},
        {'sslmode': 'disable'},
        {'sslmode': 'require', 'sslrootcert': 'none'},
        {'sslmode': 'verify-ca', 'sslrootcert': 'none'},
    ]
    
    for option in options:
        print("\n尝试使用以下参数连接:")
        for k, v in option.items():
            print(f"  {k}: {v}")
            
        try:
            conn_params = {**db_info, **option}
            conn = psycopg2.connect(**conn_params)
            
            # 测试连接
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"连接成功! PostgreSQL版本: {version}")
            
            # 测试查询表
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = cursor.fetchall()
            if tables:
                table_names = [t[0] for t in tables]
                print(f"数据库中的表: {', '.join(table_names[:5])}...")
                print(f"总共发现 {len(table_names)} 个表")
            else:
                print("数据库中没有表")
            
            # 关闭连接
            cursor.close()
            conn.close()
            
            # 存储成功的连接参数
            with open("successful_connection.txt", "w") as f:
                f.write(f"成功的连接参数:\n")
                for k, v in option.items():
                    f.write(f"{k}={v}\n")
            
            return True
        except Exception as e:
            print(f"连接失败: {str(e)}")
    
    return False

def try_alternate_host(db_info):
    """尝试使用不同的主机格式"""
    original_host = db_info['host']
    alternate_hosts = []
    
    # 生成可能的备选主机名
    if '.render.com' in original_host:
        # 常见的Render格式变体
        if not original_host.endswith('.oregon-postgres.render.com'):
            base_name = original_host.split('.')[0]
            alternate_hosts.append(f"{base_name}.oregon-postgres.render.com")
            alternate_hosts.append(f"{base_name}.postgres.render.com")
    
    success = False
    for host in alternate_hosts:
        print(f"\n尝试使用替代主机名: {host}")
        db_info_copy = db_info.copy()
        db_info_copy['host'] = host
        
        if try_connect_options(db_info_copy):
            success = True
            break
    
    return success

def main():
    # 获取数据库URL
    db_url = os.environ.get('RENDER_DB_URL') or sys.argv[1] if len(sys.argv) > 1 else None
    
    if not db_url:
        print("请提供数据库URL作为参数或设置RENDER_DB_URL环境变量")
        return 1
    
    # 解析数据库URL
    db_info = parse_db_url(db_url)
    
    # 尝试基本连接
    print("\n--- 尝试基本连接 ---")
    if try_connect_options(db_info):
        print("\n成功连接到数据库!")
        return 0
    
    # 尝试替代主机名
    print("\n--- 尝试替代主机名 ---")
    if try_alternate_host(db_info):
        print("\n成功连接到数据库!")
        return 0
    
    print("\n所有连接尝试均失败，无法连接到Render PostgreSQL")
    return 1

if __name__ == "__main__":
    sys.exit(main()) 