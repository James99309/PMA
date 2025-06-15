#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PMA项目管理系统 - 本地数据库运行脚本
"""

import os
import sys
import logging
import argparse
from app import create_app

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数 - 使用本地数据库"""
    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='PMA项目管理系统 - 本地数据库版本')
        parser.add_argument('--port', type=int, default=5000, help='指定运行端口')
        args = parser.parse_args()
        
        # 强制设置为本地环境
        os.environ['FLASK_ENV'] = 'local'
        os.environ['DATABASE_URL'] = 'postgresql://nijie@localhost:5432/pma_local'
        
        logger.info("🔧 配置本地数据库环境...")
        
        # 使用本地配置创建应用实例
        from config import LocalConfig
        app = create_app(LocalConfig)
        
        # 验证数据库连接
        with app.app_context():
            try:
                from app import db
                # 测试数据库连接
                with db.engine.connect() as conn:
                    conn.execute(db.text('SELECT 1'))
                    logger.info("✅ 本地数据库连接成功")
                    
                    # 显示数据库信息
                    result = conn.execute(db.text("SELECT current_database(), current_user"))
                    db_info = result.fetchone()
                logger.info(f"📊 数据库: {db_info[0]}, 用户: {db_info[1]}")
                
            except Exception as e:
                logger.error(f"❌ 数据库连接失败: {str(e)}")
                logger.error("请确保:")
                logger.error("1. PostgreSQL服务已启动")
                logger.error("2. 数据库 'pma_local' 已创建")
                logger.error("3. 用户 'nijie' 有访问权限")
                sys.exit(1)
        
        port = args.port
        
        logger.info("🚀 PMA系统启动中...")
        logger.info(f"🌍 环境: 本地开发环境")
        logger.info(f"🔌 端口: {port}")
        logger.info(f"📦 版本: {app.config.get('APP_VERSION', '1.2.2')}")
        logger.info(f"🔗 访问地址: http://localhost:{port}")
        logger.info(f"💾 数据库: pma_local (本地PostgreSQL)")
        
        # 启动应用
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 