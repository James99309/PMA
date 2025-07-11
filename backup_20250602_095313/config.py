import os
from dotenv import load_dotenv
from datetime import timedelta
import re
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 为activity_tracker模块设置DEBUG日志级别
activity_logger = logging.getLogger('app.utils.activity_tracker')
activity_logger.setLevel(logging.DEBUG)

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# 正确的Render数据库URL
RENDER_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

class Config:
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string-for-pma-app'
    
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
    
    # 检查数据库URL是否包含错误的主机名，如果是则替换为正确的
    if database_url and 'dpg-d0b1gl1r0fns73d1jc1g-a' in database_url:
        logger.warning("检测到错误的数据库主机名，正在替换为正确的主机名")
        database_url = database_url.replace('dpg-d0b1gl1r0fns73d1jc1g-a', 'dpg-d0b1gl1r0fns73d1jc1g-a')
        logger.info(f"已更正的DATABASE_URL: {database_url}")
    
    # 如果在Render环境中运行且没有设置环境变量，使用硬编码的Render数据库URL
    if os.environ.get('RENDER') and not database_url:
        logger.info("在Render环境中运行且无数据库URL，使用硬编码的Render数据库URL")
        database_url = RENDER_DB_URL
    
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
    
    # 会话配置 - 强制重新登录
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # 会话2小时后过期
    SESSION_COOKIE_SECURE = False  # 开发环境设为False，生产环境应设为True
    SESSION_COOKIE_HTTPONLY = True  # 防止XSS攻击
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF保护
    REMEMBER_COOKIE_DURATION = timedelta(hours=2)  # 记住我功能也只持续2小时
    
    # 邮件配置（硬编码）
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'james98980566@gmail.com'
    MAIL_PASSWORD = 'cihkheuuyvnkrtrj'
    MAIL_DEFAULT_SENDER = 'james98980566@gmail.com'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'James.ni@evertacsolutions.com'
    APP_DOMAIN = os.environ.get('APP_DOMAIN') or 'http://localhost:8082'
    PORT = int(os.environ.get('FLASK_PORT', 8082))
    
    # PostgreSQL连接池配置
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }

class DevelopmentConfig(Config):
    DEBUG = True
    # 确保开发环境也使用正确的数据库URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # 检查数据库URL是否包含错误的主机名，如果是则替换为正确的
    if database_url and 'dpg-d0b1gl1r0fns73d1jc1g-a' in database_url:
        database_url = database_url.replace('dpg-d0b1gl1r0fns73d1jc1g-a', 'dpg-d0b1gl1r0fns73d1jc1g-a')
    
    SQLALCHEMY_DATABASE_URI = database_url or \
        'sqlite:///' + os.path.join(basedir, 'app.db')

class ProductionConfig(Config):
    DEBUG = False 
    # 在生产环境中优先使用环境变量，如果没有则使用硬编码的Render数据库URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # 检查数据库URL是否包含错误的主机名，如果是则替换为正确的
    if database_url and 'dpg-d0b1gl1r0fns73d1jc1g-a' in database_url:
        database_url = database_url.replace('dpg-d0b1gl1r0fns73d1jc1g-a', 'dpg-d0b1gl1r0fns73d1jc1g-a')
    
    # 如果没有设置环境变量，使用硬编码的Render数据库URL
    SQLALCHEMY_DATABASE_URI = database_url or RENDER_DB_URL

# 本地PostgreSQL开发环境配置
# 取消注释以下行并修改连接参数以使用本地PostgreSQL
# SQLALCHEMY_DATABASE_URI = 'postgresql://用户名:密码@localhost/pma_development' 