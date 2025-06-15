#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PMA项目管理系统 - 本地运行脚本
"""

import os
import sys
import logging
import argparse
from app import create_app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='PMA项目管理系统')
        parser.add_argument('--port', type=int, help='指定运行端口')
        args = parser.parse_args()
        
        # 强制使用本地数据库配置
        os.environ['FLASK_ENV'] = 'local'
        # 清除可能影响本地配置的环境变量
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        logger.info("🔧 配置为使用本地数据库")
        
        # 导入本地配置
        from config import LocalConfig
        app = create_app(LocalConfig)
        
        # 获取端口（优先使用命令行参数，然后使用默认值）
        if args.port:
            port = args.port
        else:
            port = 5000  # 默认端口5000
        
        logger.info(f"PMA系统启动中...")
        logger.info(f"环境: {os.environ.get('FLASK_ENV', 'local')}")
        logger.info(f"端口: {port}")
        logger.info(f"版本: {app.config.get('APP_VERSION', '1.2.1')}")
        logger.info(f"访问地址: http://localhost:{port}")
        logger.info(f"本地网络地址: http://0.0.0.0:{port}")
        logger.info(f"💾 数据库: 本地PostgreSQL")
        
        # 启动应用
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
