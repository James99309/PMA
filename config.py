import os
from dotenv import load_dotenv
from datetime import timedelta
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# 云端Render数据库URL
CLOUD_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

class Config:
    """基础配置类 - 兼容原有配置"""
    
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cloud-production-secret-key-pma-2025'
    
    # 数据库配置 - 云端PostgreSQL
    database_url = os.environ.get('DATABASE_URL') or CLOUD_DB_URL
    
    # 确保使用正确的PostgreSQL协议
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("已转换数据库URL协议为postgresql://")
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 生产环境配置
    DEBUG = False
    TESTING = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 会话配置 - 生产环境安全设置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # 8小时会话
    SESSION_COOKIE_SECURE = True  # 生产环境启用HTTPS
    SESSION_COOKIE_HTTPONLY = True  # 防止XSS攻击
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF保护
    REMEMBER_COOKIE_DURATION = timedelta(days=7)  # 记住我功能7天
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'james98980566@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'cihkheuuyvnkrtrj'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'james98980566@gmail.com'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'James.ni@evertacsolutions.com'
    
    # 应用域名配置
    APP_DOMAIN = os.environ.get('APP_DOMAIN') or 'https://pma-system.onrender.com'
    PORT = int(os.environ.get('PORT', 10000))  # Render默认端口
    
    # PostgreSQL连接池配置 - 云端优化
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,  # 云端资源有限，减少连接池大小
        'max_overflow': 10,
        'pool_recycle': 1800,  # 30分钟回收连接
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'connect_args': {
            # 根据数据库URL动态设置SSL模式
            'sslmode': 'require' if 'render.com' in database_url else 'disable',
            'connect_timeout': 10,
            'application_name': 'PMA_Cloud_App'
        }
    }
    
    # 应用版本信息
    APP_VERSION = '1.2.1'
    APP_NAME = 'PMA项目管理系统'
    ENVIRONMENT = 'production'
    
    # 云端特定配置
    CLOUD_PROVIDER = 'render'
    DEPLOYMENT_DATE = '2025-05-30'
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF令牌1小时有效
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB最大文件大小
    UPLOAD_FOLDER = '/tmp/uploads'  # 云端临时目录
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_TO_STDOUT = True

class CloudConfig(Config):
    """云端部署配置类"""
    pass

class DevelopmentConfig(Config):
    """开发环境配置（基于云端数据库）"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # 开发环境可以使用HTTP
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # 生产环境额外的安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PREFERRED_URL_SCHEME = 'https'
    
    # 更严格的会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)
    
    # 生产环境日志配置
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    
    # 测试环境使用内存数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig
}

def get_config():
    """根据环境变量获取配置"""
    env = os.environ.get('FLASK_ENV', 'production')
    return config.get(env, config['default'])

# 验证云端数据库连接
def verify_cloud_database():
    """验证云端数据库连接"""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(CLOUD_DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"云端数据库连接成功: {version}")
            return True
    except Exception as e:
        logger.error(f"云端数据库连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试云端数据库连接
    print("测试云端数据库连接...")
    if verify_cloud_database():
        print("✓ 云端数据库连接正常")
    else:
        print("✗ 云端数据库连接失败") 