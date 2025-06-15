# RENDER环境数据库配置
import os
import sys
import logging

# 添加日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_url():
    """修复和设置数据库URL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        logger.info("✅ 从环境变量获取到DATABASE_URL")
        
        # 替换postgres://为postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            logger.info("🔧 已将postgres://替换为postgresql://")
        
        # 更新环境变量
        os.environ['DATABASE_URL'] = database_url
        logger.info("✅ DATABASE_URL已设置")
    else:
        logger.info("⚠️ 未找到DATABASE_URL环境变量")
        logger.info("💡 系统将使用config.py中的默认配置")
    
    # 同时设置SQLALCHEMY_DATABASE_URI以确保一致性
    if 'DATABASE_URL' in os.environ:
        os.environ['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

# 在创建应用前修复数据库URL
fix_database_url()

# 导入应用
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run() 