#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库SSL连接测试工具
用于测试各种SSL连接参数配置
"""

import os
import sys
import logging
import argparse
import traceback
from sqlalchemy import create_engine, text
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('db_ssl_test.log')
    ]
)
logger = logging.getLogger('SSL连接测试')

# SSL模式列表
SSL_MODES = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']

# 简化SSL选项 - 无需证书方式
SIMPLE_SSL_OPTIONS = ['true', 'no-verify']

def mask_password(database_url):
    """隐藏URL中的密码"""
    if not database_url:
        return None
        
    parsed = urlparse(database_url)
    if parsed.password:
        masked_url = database_url.replace(parsed.password, '********')
        return masked_url
    return database_url

def test_ssl_mode(database_url, ssl_mode):
    """测试指定的SSL模式"""
    try:
        # 解析URL
        parsed = urlparse(database_url)
        
        # 构建基础URL (不包含查询参数)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # 添加SSL模式参数
        test_url = f"{base_url}?sslmode={ssl_mode}"
        
        logger.info(f"测试SSL模式: {ssl_mode}")
        
        # 创建引擎并连接
        engine = create_engine(
            test_url,
            connect_args={
                'connect_timeout': 30,  # 增加连接超时时间
                'application_name': f'PMA迁移工具-SSL测试-{ssl_mode}'
            }
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功 [{ssl_mode}]: {version}")
            
        return True
    except Exception as e:
        logger.error(f"连接失败 [{ssl_mode}]: {str(e)}")
        return False

def test_simple_ssl(database_url, ssl_option='true'):
    """测试简化的SSL连接方式 - 无需证书"""
    try:
        # 解析URL
        parsed = urlparse(database_url)
        
        # 构建基础URL (不包含查询参数)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # 添加SSL参数
        test_url = f"{base_url}?ssl={ssl_option}"
        
        logger.info(f"测试简化SSL选项: ssl={ssl_option}")
        
        # 创建引擎并连接
        engine = create_engine(
            test_url,
            connect_args={
                'connect_timeout': 30,  # 增加连接超时时间
                'application_name': f'PMA迁移工具-简化SSL测试-{ssl_option}'
            }
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功 [ssl={ssl_option}]: {version}")
            
        return True
    except Exception as e:
        logger.error(f"连接失败 [ssl={ssl_option}]: {str(e)}")
        return False

def run_detailed_tests(database_url):
    """运行更详细的连接测试"""
    # 先测试常规连接
    regular_url = database_url
    logger.info(f"测试原始URL连接...")
    
    try:
        engine = create_engine(regular_url, connect_args={'connect_timeout': 30})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("原始URL连接成功")
    except Exception as e:
        logger.warning(f"原始URL连接失败: {str(e)}")
        logger.info("尝试使用简化SSL选项...")
        
        # 尝试使用简化的SSL选项
        simple_results = {}
        for option in SIMPLE_SSL_OPTIONS:
            simple_results[option] = test_simple_ssl(database_url, option)
            
        # 显示简化选项结果
        logger.info("\n=== 简化SSL选项测试结果 ===")
        for option, success in simple_results.items():
            logger.info(f"SSL选项 ssl={option}: {'成功' if success else '失败'}")
        
        # 如果简化选项成功，提供推荐
        if any(simple_results.values()):
            recommended_option = next((opt for opt, success in simple_results.items() if success), None)
            if recommended_option:
                logger.info(f"\n推荐使用简化的SSL选项: ssl={recommended_option}")
                parsed = urlparse(database_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                recommended_url = f"{base_url}?ssl={recommended_option}"
                logger.info(f"推荐使用的数据库URL: {mask_password(recommended_url)}")
                return f"ssl={recommended_option}"  # 返回推荐的简化选项
    
    # 测试各种SSL模式
    logger.info("\n继续测试标准SSL模式...")
    results = {}
    for mode in SSL_MODES:
        results[mode] = test_ssl_mode(database_url, mode)
    
    # 显示结果摘要
    logger.info("\n=== SSL连接测试结果 ===")
    for mode, success in results.items():
        logger.info(f"SSL模式 {mode}: {'成功' if success else '失败'}")
    
    # 建议最佳设置
    working_modes = [mode for mode, success in results.items() if success]
    if working_modes:
        recommended = max(working_modes, key=lambda x: SSL_MODES.index(x))
        logger.info(f"\n推荐SSL模式: {recommended} (安全性最高的可用模式)")
        
        # 构建完整URL
        parsed = urlparse(database_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        recommended_url = f"{base_url}?sslmode={recommended}"
        logger.info(f"推荐使用的数据库URL: {mask_password(recommended_url)}")
        return recommended
    else:
        logger.error("所有SSL模式测试均失败，请检查网络连接和数据库配置")
        return None

def main():
    parser = argparse.ArgumentParser(description='Render数据库SSL连接测试工具')
    parser.add_argument('--db-url', required=True, help='数据库URL')
    parser.add_argument('--ssl-mode', choices=SSL_MODES, help='指定要测试的SSL模式')
    parser.add_argument('--ssl', choices=SIMPLE_SSL_OPTIONS, help='指定要测试的简化SSL选项')
    args = parser.parse_args()
    
    # 获取数据库URL
    database_url = args.db_url
    masked_url = mask_password(database_url)
    
    logger.info(f"测试数据库URL: {masked_url}")
    
    # 如果指定了SSL模式，只测试该模式
    if args.ssl_mode:
        test_ssl_mode(database_url, args.ssl_mode)
    elif args.ssl:
        test_simple_ssl(database_url, args.ssl)
    else:
        # 否则运行完整测试
        run_detailed_tests(database_url)
    
    logger.info("SSL连接测试完成")
    
if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render数据库SSL连接测试工具
用于测试各种SSL连接参数配置
"""

import os
import sys
import logging
import argparse
import traceback
from sqlalchemy import create_engine, text
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('db_ssl_test.log')
    ]
)
logger = logging.getLogger('SSL连接测试')

# SSL模式列表
SSL_MODES = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']

# 简化SSL选项 - 无需证书方式
SIMPLE_SSL_OPTIONS = ['true', 'no-verify']

def mask_password(database_url):
    """隐藏URL中的密码"""
    if not database_url:
        return None
        
    parsed = urlparse(database_url)
    if parsed.password:
        masked_url = database_url.replace(parsed.password, '********')
        return masked_url
    return database_url

def test_ssl_mode(database_url, ssl_mode):
    """测试指定的SSL模式"""
    try:
        # 解析URL
        parsed = urlparse(database_url)
        
        # 构建基础URL (不包含查询参数)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # 添加SSL模式参数
        test_url = f"{base_url}?sslmode={ssl_mode}"
        
        logger.info(f"测试SSL模式: {ssl_mode}")
        
        # 创建引擎并连接
        engine = create_engine(
            test_url,
            connect_args={
                'connect_timeout': 30,  # 增加连接超时时间
                'application_name': f'PMA迁移工具-SSL测试-{ssl_mode}'
            }
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功 [{ssl_mode}]: {version}")
            
        return True
    except Exception as e:
        logger.error(f"连接失败 [{ssl_mode}]: {str(e)}")
        return False

def test_simple_ssl(database_url, ssl_option='true'):
    """测试简化的SSL连接方式 - 无需证书"""
    try:
        # 解析URL
        parsed = urlparse(database_url)
        
        # 构建基础URL (不包含查询参数)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # 添加SSL参数
        test_url = f"{base_url}?ssl={ssl_option}"
        
        logger.info(f"测试简化SSL选项: ssl={ssl_option}")
        
        # 创建引擎并连接
        engine = create_engine(
            test_url,
            connect_args={
                'connect_timeout': 30,  # 增加连接超时时间
                'application_name': f'PMA迁移工具-简化SSL测试-{ssl_option}'
            }
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功 [ssl={ssl_option}]: {version}")
            
        return True
    except Exception as e:
        logger.error(f"连接失败 [ssl={ssl_option}]: {str(e)}")
        return False

def run_detailed_tests(database_url):
    """运行更详细的连接测试"""
    # 先测试常规连接
    regular_url = database_url
    logger.info(f"测试原始URL连接...")
    
    try:
        engine = create_engine(regular_url, connect_args={'connect_timeout': 30})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("原始URL连接成功")
    except Exception as e:
        logger.warning(f"原始URL连接失败: {str(e)}")
        logger.info("尝试使用简化SSL选项...")
        
        # 尝试使用简化的SSL选项
        simple_results = {}
        for option in SIMPLE_SSL_OPTIONS:
            simple_results[option] = test_simple_ssl(database_url, option)
            
        # 显示简化选项结果
        logger.info("\n=== 简化SSL选项测试结果 ===")
        for option, success in simple_results.items():
            logger.info(f"SSL选项 ssl={option}: {'成功' if success else '失败'}")
        
        # 如果简化选项成功，提供推荐
        if any(simple_results.values()):
            recommended_option = next((opt for opt, success in simple_results.items() if success), None)
            if recommended_option:
                logger.info(f"\n推荐使用简化的SSL选项: ssl={recommended_option}")
                parsed = urlparse(database_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                recommended_url = f"{base_url}?ssl={recommended_option}"
                logger.info(f"推荐使用的数据库URL: {mask_password(recommended_url)}")
                return f"ssl={recommended_option}"  # 返回推荐的简化选项
    
    # 测试各种SSL模式
    logger.info("\n继续测试标准SSL模式...")
    results = {}
    for mode in SSL_MODES:
        results[mode] = test_ssl_mode(database_url, mode)
    
    # 显示结果摘要
    logger.info("\n=== SSL连接测试结果 ===")
    for mode, success in results.items():
        logger.info(f"SSL模式 {mode}: {'成功' if success else '失败'}")
    
    # 建议最佳设置
    working_modes = [mode for mode, success in results.items() if success]
    if working_modes:
        recommended = max(working_modes, key=lambda x: SSL_MODES.index(x))
        logger.info(f"\n推荐SSL模式: {recommended} (安全性最高的可用模式)")
        
        # 构建完整URL
        parsed = urlparse(database_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        recommended_url = f"{base_url}?sslmode={recommended}"
        logger.info(f"推荐使用的数据库URL: {mask_password(recommended_url)}")
        return recommended
    else:
        logger.error("所有SSL模式测试均失败，请检查网络连接和数据库配置")
        return None

def main():
    parser = argparse.ArgumentParser(description='Render数据库SSL连接测试工具')
    parser.add_argument('--db-url', required=True, help='数据库URL')
    parser.add_argument('--ssl-mode', choices=SSL_MODES, help='指定要测试的SSL模式')
    parser.add_argument('--ssl', choices=SIMPLE_SSL_OPTIONS, help='指定要测试的简化SSL选项')
    args = parser.parse_args()
    
    # 获取数据库URL
    database_url = args.db_url
    masked_url = mask_password(database_url)
    
    logger.info(f"测试数据库URL: {masked_url}")
    
    # 如果指定了SSL模式，只测试该模式
    if args.ssl_mode:
        test_ssl_mode(database_url, args.ssl_mode)
    elif args.ssl:
        test_simple_ssl(database_url, args.ssl)
    else:
        # 否则运行完整测试
        run_detailed_tests(database_url)
    
    logger.info("SSL连接测试完成")
    
if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
Render数据库SSL连接测试工具
用于测试各种SSL连接参数配置
"""

import os
import sys
import logging
import argparse
import traceback
from sqlalchemy import create_engine, text
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('db_ssl_test.log')
    ]
)
logger = logging.getLogger('SSL连接测试')

# SSL模式列表
SSL_MODES = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']

# 简化SSL选项 - 无需证书方式
SIMPLE_SSL_OPTIONS = ['true', 'no-verify']

def mask_password(database_url):
    """隐藏URL中的密码"""
    if not database_url:
        return None
        
    parsed = urlparse(database_url)
    if parsed.password:
        masked_url = database_url.replace(parsed.password, '********')
        return masked_url
    return database_url

def test_ssl_mode(database_url, ssl_mode):
    """测试指定的SSL模式"""
    try:
        # 解析URL
        parsed = urlparse(database_url)
        
        # 构建基础URL (不包含查询参数)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # 添加SSL模式参数
        test_url = f"{base_url}?sslmode={ssl_mode}"
        
        logger.info(f"测试SSL模式: {ssl_mode}")
        
        # 创建引擎并连接
        engine = create_engine(
            test_url,
            connect_args={
                'connect_timeout': 30,  # 增加连接超时时间
                'application_name': f'PMA迁移工具-SSL测试-{ssl_mode}'
            }
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功 [{ssl_mode}]: {version}")
            
        return True
    except Exception as e:
        logger.error(f"连接失败 [{ssl_mode}]: {str(e)}")
        return False

def test_simple_ssl(database_url, ssl_option='true'):
    """测试简化的SSL连接方式 - 无需证书"""
    try:
        # 解析URL
        parsed = urlparse(database_url)
        
        # 构建基础URL (不包含查询参数)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # 添加SSL参数
        test_url = f"{base_url}?ssl={ssl_option}"
        
        logger.info(f"测试简化SSL选项: ssl={ssl_option}")
        
        # 创建引擎并连接
        engine = create_engine(
            test_url,
            connect_args={
                'connect_timeout': 30,  # 增加连接超时时间
                'application_name': f'PMA迁移工具-简化SSL测试-{ssl_option}'
            }
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功 [ssl={ssl_option}]: {version}")
            
        return True
    except Exception as e:
        logger.error(f"连接失败 [ssl={ssl_option}]: {str(e)}")
        return False

def run_detailed_tests(database_url):
    """运行更详细的连接测试"""
    # 先测试常规连接
    regular_url = database_url
    logger.info(f"测试原始URL连接...")
    
    try:
        engine = create_engine(regular_url, connect_args={'connect_timeout': 30})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("原始URL连接成功")
    except Exception as e:
        logger.warning(f"原始URL连接失败: {str(e)}")
        logger.info("尝试使用简化SSL选项...")
        
        # 尝试使用简化的SSL选项
        simple_results = {}
        for option in SIMPLE_SSL_OPTIONS:
            simple_results[option] = test_simple_ssl(database_url, option)
            
        # 显示简化选项结果
        logger.info("\n=== 简化SSL选项测试结果 ===")
        for option, success in simple_results.items():
            logger.info(f"SSL选项 ssl={option}: {'成功' if success else '失败'}")
        
        # 如果简化选项成功，提供推荐
        if any(simple_results.values()):
            recommended_option = next((opt for opt, success in simple_results.items() if success), None)
            if recommended_option:
                logger.info(f"\n推荐使用简化的SSL选项: ssl={recommended_option}")
                parsed = urlparse(database_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                recommended_url = f"{base_url}?ssl={recommended_option}"
                logger.info(f"推荐使用的数据库URL: {mask_password(recommended_url)}")
                return f"ssl={recommended_option}"  # 返回推荐的简化选项
    
    # 测试各种SSL模式
    logger.info("\n继续测试标准SSL模式...")
    results = {}
    for mode in SSL_MODES:
        results[mode] = test_ssl_mode(database_url, mode)
    
    # 显示结果摘要
    logger.info("\n=== SSL连接测试结果 ===")
    for mode, success in results.items():
        logger.info(f"SSL模式 {mode}: {'成功' if success else '失败'}")
    
    # 建议最佳设置
    working_modes = [mode for mode, success in results.items() if success]
    if working_modes:
        recommended = max(working_modes, key=lambda x: SSL_MODES.index(x))
        logger.info(f"\n推荐SSL模式: {recommended} (安全性最高的可用模式)")
        
        # 构建完整URL
        parsed = urlparse(database_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        recommended_url = f"{base_url}?sslmode={recommended}"
        logger.info(f"推荐使用的数据库URL: {mask_password(recommended_url)}")
        return recommended
    else:
        logger.error("所有SSL模式测试均失败，请检查网络连接和数据库配置")
        return None

def main():
    parser = argparse.ArgumentParser(description='Render数据库SSL连接测试工具')
    parser.add_argument('--db-url', required=True, help='数据库URL')
    parser.add_argument('--ssl-mode', choices=SSL_MODES, help='指定要测试的SSL模式')
    parser.add_argument('--ssl', choices=SIMPLE_SSL_OPTIONS, help='指定要测试的简化SSL选项')
    args = parser.parse_args()
    
    # 获取数据库URL
    database_url = args.db_url
    masked_url = mask_password(database_url)
    
    logger.info(f"测试数据库URL: {masked_url}")
    
    # 如果指定了SSL模式，只测试该模式
    if args.ssl_mode:
        test_ssl_mode(database_url, args.ssl_mode)
    elif args.ssl:
        test_simple_ssl(database_url, args.ssl)
    else:
        # 否则运行完整测试
        run_detailed_tests(database_url)
    
    logger.info("SSL连接测试完成")
    
if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render数据库SSL连接测试工具
用于测试各种SSL连接参数配置
"""

import os
import sys
import logging
import argparse
import traceback
from sqlalchemy import create_engine, text
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('db_ssl_test.log')
    ]
)
logger = logging.getLogger('SSL连接测试')

# SSL模式列表
SSL_MODES = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']

# 简化SSL选项 - 无需证书方式
SIMPLE_SSL_OPTIONS = ['true', 'no-verify']

def mask_password(database_url):
    """隐藏URL中的密码"""
    if not database_url:
        return None
        
    parsed = urlparse(database_url)
    if parsed.password:
        masked_url = database_url.replace(parsed.password, '********')
        return masked_url
    return database_url

def test_ssl_mode(database_url, ssl_mode):
    """测试指定的SSL模式"""
    try:
        # 解析URL
        parsed = urlparse(database_url)
        
        # 构建基础URL (不包含查询参数)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # 添加SSL模式参数
        test_url = f"{base_url}?sslmode={ssl_mode}"
        
        logger.info(f"测试SSL模式: {ssl_mode}")
        
        # 创建引擎并连接
        engine = create_engine(
            test_url,
            connect_args={
                'connect_timeout': 30,  # 增加连接超时时间
                'application_name': f'PMA迁移工具-SSL测试-{ssl_mode}'
            }
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功 [{ssl_mode}]: {version}")
            
        return True
    except Exception as e:
        logger.error(f"连接失败 [{ssl_mode}]: {str(e)}")
        return False

def test_simple_ssl(database_url, ssl_option='true'):
    """测试简化的SSL连接方式 - 无需证书"""
    try:
        # 解析URL
        parsed = urlparse(database_url)
        
        # 构建基础URL (不包含查询参数)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # 添加SSL参数
        test_url = f"{base_url}?ssl={ssl_option}"
        
        logger.info(f"测试简化SSL选项: ssl={ssl_option}")
        
        # 创建引擎并连接
        engine = create_engine(
            test_url,
            connect_args={
                'connect_timeout': 30,  # 增加连接超时时间
                'application_name': f'PMA迁移工具-简化SSL测试-{ssl_option}'
            }
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"连接成功 [ssl={ssl_option}]: {version}")
            
        return True
    except Exception as e:
        logger.error(f"连接失败 [ssl={ssl_option}]: {str(e)}")
        return False

def run_detailed_tests(database_url):
    """运行更详细的连接测试"""
    # 先测试常规连接
    regular_url = database_url
    logger.info(f"测试原始URL连接...")
    
    try:
        engine = create_engine(regular_url, connect_args={'connect_timeout': 30})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("原始URL连接成功")
    except Exception as e:
        logger.warning(f"原始URL连接失败: {str(e)}")
        logger.info("尝试使用简化SSL选项...")
        
        # 尝试使用简化的SSL选项
        simple_results = {}
        for option in SIMPLE_SSL_OPTIONS:
            simple_results[option] = test_simple_ssl(database_url, option)
            
        # 显示简化选项结果
        logger.info("\n=== 简化SSL选项测试结果 ===")
        for option, success in simple_results.items():
            logger.info(f"SSL选项 ssl={option}: {'成功' if success else '失败'}")
        
        # 如果简化选项成功，提供推荐
        if any(simple_results.values()):
            recommended_option = next((opt for opt, success in simple_results.items() if success), None)
            if recommended_option:
                logger.info(f"\n推荐使用简化的SSL选项: ssl={recommended_option}")
                parsed = urlparse(database_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                recommended_url = f"{base_url}?ssl={recommended_option}"
                logger.info(f"推荐使用的数据库URL: {mask_password(recommended_url)}")
                return f"ssl={recommended_option}"  # 返回推荐的简化选项
    
    # 测试各种SSL模式
    logger.info("\n继续测试标准SSL模式...")
    results = {}
    for mode in SSL_MODES:
        results[mode] = test_ssl_mode(database_url, mode)
    
    # 显示结果摘要
    logger.info("\n=== SSL连接测试结果 ===")
    for mode, success in results.items():
        logger.info(f"SSL模式 {mode}: {'成功' if success else '失败'}")
    
    # 建议最佳设置
    working_modes = [mode for mode, success in results.items() if success]
    if working_modes:
        recommended = max(working_modes, key=lambda x: SSL_MODES.index(x))
        logger.info(f"\n推荐SSL模式: {recommended} (安全性最高的可用模式)")
        
        # 构建完整URL
        parsed = urlparse(database_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        recommended_url = f"{base_url}?sslmode={recommended}"
        logger.info(f"推荐使用的数据库URL: {mask_password(recommended_url)}")
        return recommended
    else:
        logger.error("所有SSL模式测试均失败，请检查网络连接和数据库配置")
        return None

def main():
    parser = argparse.ArgumentParser(description='Render数据库SSL连接测试工具')
    parser.add_argument('--db-url', required=True, help='数据库URL')
    parser.add_argument('--ssl-mode', choices=SSL_MODES, help='指定要测试的SSL模式')
    parser.add_argument('--ssl', choices=SIMPLE_SSL_OPTIONS, help='指定要测试的简化SSL选项')
    args = parser.parse_args()
    
    # 获取数据库URL
    database_url = args.db_url
    masked_url = mask_password(database_url)
    
    logger.info(f"测试数据库URL: {masked_url}")
    
    # 如果指定了SSL模式，只测试该模式
    if args.ssl_mode:
        test_ssl_mode(database_url, args.ssl_mode)
    elif args.ssl:
        test_simple_ssl(database_url, args.ssl)
    else:
        # 否则运行完整测试
        run_detailed_tests(database_url)
    
    logger.info("SSL连接测试完成")
    
if __name__ == "__main__":
    main() 
 
 