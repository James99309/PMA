#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库结构恢复脚本

该脚本用于在Render环境中应用本地导出的数据库结构。
"""

import os
import sys
import subprocess
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Render数据库恢复')

def main():
    """主函数"""
    # 检查是否在Render环境
    if os.environ.get('RENDER') != 'true':
        logger.warning("该脚本应该在Render环境中运行")
    
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("未找到DATABASE_URL环境变量")
        return 1
    
    # 转换URL格式
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    # 从数据库URL中提取连接信息
    url_parts = db_url.replace('postgresql://', '').split('/')
    conn_parts = url_parts[0].split('@')
    
    user_pass = conn_parts[0].split(':')
    host_port = conn_parts[1].split(':')
    
    username = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else '5432'
    dbname = url_parts[1].split('?')[0]  # 移除可能的查询参数
    
    # 设置PGPASSWORD环境变量
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    
    # 应用迁移SQL
    schema_file = 'db_schema.sql'
    if not os.path.exists(schema_file):
        logger.error(f"未找到结构文件 {schema_file}")
        return 1
    
    logger.info(f"开始应用数据库结构...")
    
    try:
        # 使用psql应用结构
        cmd = [
            'psql',
            '-h', host,
            '-p', port,
            '-U', username,
            '-d', dbname,
            '-f', schema_file
        ]
        
        logger.info(f"运行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env, check=True)
        
        if result.returncode == 0:
            logger.info("成功应用数据库结构")
            return 0
        else:
            logger.error("应用数据库结构失败")
            return 1
            
    except Exception as e:
        logger.error(f"应用数据库结构时出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
