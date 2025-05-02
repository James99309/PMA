# RENDER环境数据库修复
import os
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 修复数据库URL
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
    os.environ['DATABASE_URL'] = fixed_url
    logger.info(f"已修复DATABASE_URL: {fixed_url}")

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run() 