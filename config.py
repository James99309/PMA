import os
from dotenv import load_dotenv
from datetime import timedelta
import re
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # 数据库配置
    # 添加Render PostgreSQL数据库支持
    database_url = os.environ.get('DATABASE_URL')
    
    # 记录原始数据库URL用于调试
    if database_url:
        logger.info(f"原始DATABASE_URL: {database_url}")
    else:
        logger.info("未找到DATABASE_URL环境变量，将使用默认SQLite数据库")
    
    # Render使用postgres://协议，而SQLAlchemy 1.4+需要postgresql://
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info(f"转换后的DATABASE_URL: {database_url}")
    
    SQLALCHEMY_DATABASE_URI = database_url or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    
    # 确保没有硬编码的数据库连接参数
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 调试模式
    DEBUG = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('SMTP_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('SMTP_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('SENDER_EMAIL')
    MAIL_PASSWORD = os.environ.get('SENDER_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('SENDER_EMAIL')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'James.ni@evertacsolutions.com' 
    
    # 应用域名，用于邮件中的链接
    APP_DOMAIN = os.environ.get('APP_DOMAIN') or 'http://localhost:8082'
    
    PORT = int(os.environ.get('FLASK_PORT', 8082))

class DevelopmentConfig(Config):
    DEBUG = True
    # 确保开发环境也使用正确的数据库URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url or \
        'sqlite:///' + os.path.join(basedir, 'app.db')

class ProductionConfig(Config):
    DEBUG = False
    # 确保生产环境也使用正确的数据库URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url or \
        'sqlite:///' + os.path.join(basedir, 'app.db') 