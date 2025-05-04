# RENDER环境数据库修复
import os
import sys
import logging

# 添加日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 正确的Render数据库URL
CORRECT_RENDER_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

# 旧的错误主机名
OLD_HOST = 'dpg-d0b1gl1r0fns73d1jc1g-a'

# 正确的新主机名
NEW_HOST = 'dpg-d0b1gl1r0fns73d1jc1g-a'

# 处理数据库URL
def fix_database_url():
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        logger.info(f"获取到的原始DATABASE_URL: {database_url.replace(database_url.split('@')[0], '***')}")
        
        # 替换postgres://为postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            logger.info("已将postgres://替换为postgresql://")
        
        # 检查是否包含错误的主机名
        if OLD_HOST in database_url:
            database_url = database_url.replace(OLD_HOST, NEW_HOST)
            logger.info(f"已替换错误的主机名 {OLD_HOST} 为 {NEW_HOST}")
        
        # 更新环境变量
        os.environ['DATABASE_URL'] = database_url
        logger.info(f"最终DATABASE_URL已设置 (隐藏敏感信息)")
    else:
        # 如果没有环境变量，使用正确的硬编码URL
        logger.info(f"未找到DATABASE_URL环境变量，使用硬编码的正确URL")
        os.environ['DATABASE_URL'] = CORRECT_RENDER_DB_URL
    
    # 同时设置SQLALCHEMY_DATABASE_URI以确保一致性
    os.environ['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

# 在创建应用前修复数据库URL
fix_database_url()

# 导入应用
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run() 
    if database_url:
        logger.info(f"获取到的原始DATABASE_URL: {database_url.replace(database_url.split('@')[0], '***')}")
        
        # 替换postgres://为postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            logger.info("已将postgres://替换为postgresql://")
        
        # 检查是否包含错误的主机名
        if OLD_HOST in database_url:
            database_url = database_url.replace(OLD_HOST, NEW_HOST)
            logger.info(f"已替换错误的主机名 {OLD_HOST} 为 {NEW_HOST}")
        
        # 更新环境变量
        os.environ['DATABASE_URL'] = database_url
        logger.info(f"最终DATABASE_URL已设置 (隐藏敏感信息)")
    else:
        # 如果没有环境变量，使用正确的硬编码URL
        logger.info(f"未找到DATABASE_URL环境变量，使用硬编码的正确URL")
        os.environ['DATABASE_URL'] = CORRECT_RENDER_DB_URL
    
    # 同时设置SQLALCHEMY_DATABASE_URI以确保一致性
    os.environ['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

# 在创建应用前修复数据库URL
fix_database_url()

# 导入应用
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run() 