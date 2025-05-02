#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Render数据库连接调试工具

用于分析和修复数据库连接问题，特别是针对"postgres"主机名无法解析的错误。
在Render环境中运行，帮助识别连接问题的根源。
"""

import os
import sys
import logging
import re
from urllib.parse import urlparse

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def inspect_database_config():
    """
    检查数据库配置并尝试修复连接问题
    """
    # 检查环境变量
    database_url = os.environ.get('DATABASE_URL')
    
    logger.info("=== 数据库配置诊断 ===")
    
    if not database_url:
        logger.error("未找到DATABASE_URL环境变量!")
        return
    
    logger.info(f"原始DATABASE_URL: {database_url}")
    
    # 解析URL
    parsed_url = urlparse(database_url)
    logger.info(f"协议: {parsed_url.scheme}")
    logger.info(f"主机名: {parsed_url.hostname}")
    logger.info(f"端口: {parsed_url.port}")
    logger.info(f"用户名: {parsed_url.username}")
    logger.info(f"数据库名: {parsed_url.path.lstrip('/')}")
    
    # 检查协议并修复
    if parsed_url.scheme == 'postgres':
        fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info(f"已修复的URL: {fixed_url}")
        
        # 修改环境变量
        os.environ['DATABASE_URL'] = fixed_url
        logger.info("已更新环境变量DATABASE_URL")
    
    # 检查是否存在硬编码的postgres主机
    app_init_path = os.path.join(os.path.dirname(__file__), 'app', '__init__.py')
    extensions_path = os.path.join(os.path.dirname(__file__), 'app', 'extensions.py')
    
    if os.path.exists(app_init_path):
        logger.info(f"正在检查 {app_init_path}")
        with open(app_init_path, 'r') as f:
            content = f.read()
            if 'postgres' in content:
                logger.warning(f"app/__init__.py 中可能包含硬编码的postgres主机名")
                matches = re.findall(r'[\'"]postgres[\'"]', content)
                if matches:
                    logger.error(f"发现硬编码的postgres主机名: {matches}")
    
    if os.path.exists(extensions_path):
        logger.info(f"正在检查 {extensions_path}")
        with open(extensions_path, 'r') as f:
            content = f.read()
            if 'postgres' in content:
                logger.warning(f"app/extensions.py 中可能包含硬编码的postgres主机名")
                matches = re.findall(r'[\'"]postgres[\'"]', content)
                if matches:
                    logger.error(f"发现硬编码的postgres主机名: {matches}")
    
    # 检查配置文件
    config_path = os.path.join(os.path.dirname(__file__), 'config.py')
    if os.path.exists(config_path):
        logger.info(f"正在检查 {config_path}")
        with open(config_path, 'r') as f:
            content = f.read()
            if 'postgres' in content and not 'postgres://' in content:
                logger.warning(f"config.py 中可能包含硬编码的postgres主机名")
                matches = re.findall(r'[\'"]postgres[\'"]', content)
                if matches:
                    logger.error(f"发现硬编码的postgres主机名: {matches}")
    
    logger.info("数据库配置诊断完成")

def search_postgres_references():
    """搜索项目中任何硬编码的postgres引用"""
    import glob
    import os
    
    logger.info("=== 搜索项目中的postgres引用 ===")
    
    # 搜索Python文件
    py_files = glob.glob('**/*.py', recursive=True)
    
    for file_path in py_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'postgres' in content and not ('postgres://' in content or 'postgresql://' in content):
                    matches = re.findall(r'[\'"]postgres[\'"]', content)
                    if matches:
                        logger.warning(f"在 {file_path} 中发现疑似硬编码的postgres引用: {matches}")
                        # 显示相关上下文
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'postgres' in line:
                                context_start = max(0, i-2)
                                context_end = min(len(lines), i+3)
                                logger.info(f"上下文 ({file_path}, 行 {i+1}):")
                                for j in range(context_start, context_end):
                                    logger.info(f"    {j+1}: {lines[j]}")
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {str(e)}")
    
    logger.info("搜索完成")

def test_database_connection():
    """测试数据库连接"""
    # 尝试创建一个SQLAlchemy引擎并连接
    try:
        from sqlalchemy import create_engine, text
        
        # 获取数据库URL
        database_url = os.environ.get('DATABASE_URL', '')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        if not database_url:
            logger.error("没有数据库URL，无法测试连接")
            return
        
        logger.info(f"尝试连接到数据库: {database_url}")
        engine = create_engine(database_url)
        
        # 尝试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            for row in result:
                logger.info(f"连接成功，结果: {row}")
        
        logger.info("数据库连接测试成功!")
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")

if __name__ == "__main__":
    logger.info("开始数据库调试")
    inspect_database_config()
    search_postgres_references()
    test_database_connection()
    logger.info("调试完成") 