

# ==================== 数据库配置 ====================
import os
from dotenv import load_dotenv
from datetime import timedelta
import logging
from urllib.parse import urlparse

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

def get_database_url():
    """动态获取数据库URL"""
    # 优先从环境变量获取DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        logger.info("✅ 从环境变量获取到DATABASE_URL")
        # 修复postgres://为postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            logger.info("🔧 已将postgres://替换为postgresql://")
        return database_url
    
    # 如果没有环境变量，检查是否有本地数据库配置
    local_db_url = os.environ.get('LOCAL_DATABASE_URL')
    if local_db_url:
        logger.info("✅ 使用本地数据库配置")
        return local_db_url
    
    # 默认本地PostgreSQL配置
    default_local_url = 'postgresql://nijie@localhost:5432/pma_local'
    logger.info("⚠️ 使用默认本地数据库配置")
    return default_local_url

# 获取数据库URL
DATABASE_URL = get_database_url()

class Config:
    """基础配置类 - 支持动态数据库配置"""
    
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'local-development-secret-key-pma-2025'
    
    # 🔧 动态数据库配置
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 环境检测
    IS_CLOUD_ENV = 'render.com' in DATABASE_URL or 'dpg-' in DATABASE_URL
    IS_LOCAL_ENV = not IS_CLOUD_ENV
    
    # 根据环境调整配置
    if IS_CLOUD_ENV:
        DEBUG = False
        TESTING = False
        ENVIRONMENT = 'production'
        APP_VERSION = '1.2.2-CLOUD'
        APP_NAME = 'PMA项目管理系统 (云端版)'
        CLOUD_PROVIDER = 'render'
        
        # 云端会话配置
        SESSION_COOKIE_SECURE = True
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = 'Lax'
        
        # 云端PostgreSQL连接池配置
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'pool_timeout': 30,
            'connect_args': {
                'sslmode': 'require',
                'connect_timeout': 30,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5,
                'application_name': 'PMA_Cloud_App'
            }
        }
        
        # 云端域名配置
        APP_DOMAIN = os.environ.get('APP_DOMAIN', 'https://your-app.onrender.com')
        PORT = int(os.environ.get('PORT', 10000))
        
    else:
        DEBUG = True
        TESTING = False
        ENVIRONMENT = 'local'
        APP_VERSION = '1.2.2-LOCAL'
        APP_NAME = 'PMA项目管理系统 (本地版)'
        CLOUD_PROVIDER = 'local'
        
        # 本地会话配置
        SESSION_COOKIE_SECURE = False
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = 'Lax'
        
        # 本地PostgreSQL连接池配置
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 5,
            'max_overflow': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'pool_timeout': 30,
            'connect_args': {
                'sslmode': 'disable',
                'connect_timeout': 10,
                'application_name': 'PMA_Local_App'
            }
        }
        
        # 本地域名配置
        APP_DOMAIN = 'http://localhost:5005'
        PORT = 5005
    
    # 模板配置
    TEMPLATES_AUTO_RELOAD = True
    
    # JWT配置
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # 邮件配置
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'james98980566@gmail.com'
    MAIL_PASSWORD = 'cihkheuuyvnkrtrj'
    MAIL_DEFAULT_SENDER = 'james98980566@gmail.com'
    ADMIN_EMAIL = 'James.ni@evertacsolutions.com'
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 日志配置
    LOG_LEVEL = 'INFO' if IS_CLOUD_ENV else 'DEBUG'
    LOG_TO_STDOUT = IS_CLOUD_ENV
    
    # 备份服务配置
    BACKUP_ENABLED = True
    BACKUP_SCHEDULE = '00:00'
    BACKUP_RETENTION_DAYS = 30
    BACKUP_LOCATION = os.path.join(basedir, 'backups')

# 🔒 安全别名配置
LocalConfig = Config
DevelopmentConfig = Config
ProductionConfig = Config
TestingConfig = Config
CloudConfig = Config

def get_config():
    """获取配置"""
    return Config

def verify_database_connection():
    """验证数据库连接"""
    try:
        if Config.IS_CLOUD_ENV:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            logger.info("✅ 云端数据库连接验证成功")
            return True
        else:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            logger.info("✅ 本地数据库连接验证成功")
            return True
    except Exception as e:
        logger.error(f"❌ 数据库连接验证失败: {e}")
        return False

def get_database_info():
    """获取数据库信息"""
    parsed = urlparse(DATABASE_URL)
    return {
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path.lstrip('/'),
        'username': parsed.username,
        'is_cloud': Config.IS_CLOUD_ENV,
        'is_local': Config.IS_LOCAL_ENV
    }

# 启动时显示数据库配置信息
db_info = get_database_info()
logger.info("=" * 60)
logger.info("🗄️  数据库配置信息")
logger.info("=" * 60)
logger.info(f"环境类型: {'云端' if db_info['is_cloud'] else '本地'}")
logger.info(f"数据库主机: {db_info['host']}")
logger.info(f"数据库端口: {db_info['port']}")
logger.info(f"数据库名称: {db_info['database']}")
logger.info(f"用户名: {db_info['username']}")
logger.info("=" * 60)


