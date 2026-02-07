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
        parser.add_argument('--supabase', action='store_true', help='启用Supabase云端上传测试')
        args = parser.parse_args()

        # 强制加载本地环境配置
        from dotenv import load_dotenv

        # 加载 NAS 存储配置（优先级最高）
        if os.path.exists('.env.nas'):
            load_dotenv('.env.nas', override=True)
            logger.info("🗄️ 加载 NAS 存储配置文件 .env.nas")

        # 注意：启动脚本已经导出环境变量，但我们仍需尝试从对应的.env文件加载
        # 检测数据库类型（SP8D/OVS），兼容旧变量名 SUPABASE_DB_TYPE
        pma_db_type = (os.environ.get('PMA_DB_TYPE', '') or os.environ.get('SUPABASE_DB_TYPE', '')).lower()

        if pma_db_type == 'sp8d':
            # SP8D 测试模式 - 加载 .env.sp8d.local
            if os.path.exists('.env.sp8d.local'):
                load_dotenv('.env.sp8d.local', override=True)
                logger.info("🔄 检测到SP8D测试模式，加载.env.sp8d.local配置")
        elif pma_db_type == 'ovs':
            # OVS 测试模式 - 加载 .env.ovs.local
            if os.path.exists('.env.ovs.local'):
                load_dotenv('.env.ovs.local', override=True)
                logger.info("🔄 检测到OVS测试模式，加载.env.ovs.local配置")
        elif not args.supabase:
            # 非跨系统测试模式 - 加载本地配置
            load_dotenv('.env.local', override=True)
            logger.info("🔧 强制加载本地环境配置文件 .env.local")

        # 现在检测是否在运行跨系统测试模式（此时环境变量已加载）
        is_cross_system_test = (
            os.environ.get('CROSS_SYSTEM_API_KEY') is not None or
            os.environ.get('SP8D_API_BASE_URL') is not None or
            (os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE', '')) in ['sp8d', 'ovs']
        )

        # 如果启用了Supabase测试
        if args.supabase:
            logger.info("🌐 启用Supabase云端上传测试模式")
            # 加载Supabase配置
            env_file_path = '.env.supabase.prod'
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
                            display_value = value[:20] + '...' if len(value) > 20 else value
                            logger.info(f"✅ 设置环境变量: {key}={display_value}")
            else:
                logger.warning("⚠️ Supabase配置文件 .env.supabase 不存在")

        # 仅在非跨系统测试模式下强制使用本地数据库配置
        if not is_cross_system_test:
            os.environ['FLASK_ENV'] = 'local'
            # 清除可能影响本地配置的环境变量
            if 'DATABASE_URL' in os.environ:
                del os.environ['DATABASE_URL']
            if 'CLOUD_DB_URL' in os.environ:
                del os.environ['CLOUD_DB_URL']
            if 'CLOUD_DB_ACCESS' in os.environ:
                del os.environ['CLOUD_DB_ACCESS']

            # 设置本地数据库配置
            os.environ['LOCAL_DATABASE_URL'] = 'postgresql://nijie@localhost:5432/pma_local'
            logger.info("🔧 配置为使用本地数据库")
        else:
            logger.info("✅ 使用启动脚本导出的数据库配置（跨系统API测试模式）")
        
        # 导入本地配置
        from config import LocalConfig
        app = create_app(LocalConfig)
        
        # 显示最终的环境变量状态
        if args.supabase:
            logger.info(f"🔍 最终环境变量状态:")
            logger.info(f"   SUPABASE_URL: {os.environ.get('SUPABASE_URL', 'NOT SET')}")
            logger.info(f"   FORCE_CLOUD_UPLOAD: {os.environ.get('FORCE_CLOUD_UPLOAD', 'NOT SET')}")
        
        # 获取端口（优先级：命令行参数 > 环境变量 > 默认值）
        if args.port:
            port = args.port
        else:
            # 优先读取环境变量中的 FLASK_RUN_PORT（来自启动脚本）
            env_port = os.environ.get('FLASK_RUN_PORT') or os.environ.get('PORT')
            port = int(env_port) if env_port else 5011
        
        logger.info(f"PMA系统启动中...")
        logger.info(f"环境: {os.environ.get('FLASK_ENV', 'local')}")
        logger.info(f"端口: {port}")
        logger.info(f"版本: {app.config.get('APP_VERSION', '1.2.1')}")
        logger.info(f"访问地址: http://localhost:{port}")
        logger.info(f"本地网络地址: http://0.0.0.0:{port}")
        logger.info(f"💾 数据库: 本地PostgreSQL")
        if args.supabase:
            logger.info(f"☁️ 文件上传: Supabase云端存储")
        
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
