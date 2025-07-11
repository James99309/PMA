#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PMA项目管理系统 - 云端运行脚本
"""

import os
import sys
import logging
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
        # 设置环境变量
        os.environ.setdefault('FLASK_ENV', 'production')
        
        # 创建应用实例
        app = create_app()
        
        # 获取端口（Render使用PORT环境变量）
        port = int(os.environ.get('PORT', 10000))
        
        logger.info(f"PMA系统启动中...")
        logger.info(f"环境: {os.environ.get('FLASK_ENV', 'production')}")
        logger.info(f"端口: {port}")
        logger.info(f"版本: {app.config.get('APP_VERSION', '1.2.1')}")
        
        # 启动应用
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
