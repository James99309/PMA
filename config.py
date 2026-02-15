

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
# 加载 .env 文件，但不覆盖已存在的环境变量（保护启动脚本导出的配置）
load_dotenv(os.path.join(basedir, '.env'), override=False)

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

# 数据库URL将在运行时动态获取
# DATABASE_URL = get_database_url()  # 移至Config类中

class Config:
    """基础配置类 - 支持动态数据库配置"""

    # 统一版本号（所有环境共用，基于代码而非数据库）
    APP_VERSION = '1.27.59'

    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'local-development-secret-key-pma-2025'
    
    # 🔧 动态数据库配置
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 环境检测
    DATABASE_URL = get_database_url()
    IS_RENDER_ENV = 'render.com' in DATABASE_URL or 'dpg-' in DATABASE_URL
    IS_SUPABASE_ENV = 'supabase.com' in DATABASE_URL or 'supabase.co' in DATABASE_URL
    IS_CLOUD_ENV = IS_RENDER_ENV or IS_SUPABASE_ENV
    IS_LOCAL_ENV = not IS_CLOUD_ENV

    # 数据库类型检测 - 通过环境变量 PMA_DB_TYPE 或数据库URL判断
    # 兼容旧变量名 SUPABASE_DB_TYPE
    PMA_DB_TYPE = os.environ.get('PMA_DB_TYPE', '') or os.environ.get('SUPABASE_DB_TYPE', 'local')
    IS_SP8D = 'iqcyimnjtnmomvfuwjzw' in DATABASE_URL or PMA_DB_TYPE == 'sp8d'
    IS_OVS = 'pqzviljbpfoqvyfulakl' in DATABASE_URL or PMA_DB_TYPE == 'ovs'

    # ========== 系统货币配置（基于数据库类型，与语言设置解耦） ==========
    # 货币和单位由数据库类型决定，不随用户语言切换而改变
    if IS_OVS:
        # OVS 数据库 → 美元
        DEFAULT_CURRENCY = 'USD'
        CURRENCY_SYMBOL = '$'
        AMOUNT_UNIT = 'M'              # million
        AMOUNT_DIVISOR = 1000000       # 除以100万
        COUNT_UNIT = 'pcs'
    else:
        # SP8D 或本地数据库 → 人民币
        DEFAULT_CURRENCY = 'CNY'
        CURRENCY_SYMBOL = '¥'
        AMOUNT_UNIT = '万元'
        AMOUNT_DIVISOR = 10000         # 除以1万
        COUNT_UNIT = '个'

    # 根据环境调整配置
    if IS_CLOUD_ENV:
        DEBUG = False
        TESTING = False
        ENVIRONMENT = 'production'
        APP_NAME = 'PMA项目管理系统 (云端版)'
        CLOUD_PROVIDER = 'render'
        
        # 云端会话配置
        SESSION_COOKIE_SECURE = True
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = 'Lax'
        
        # 云端PostgreSQL连接池配置
        if IS_SUPABASE_ENV:
            # Supabase优化配置 - 针对远程数据库优化
            SQLALCHEMY_ENGINE_OPTIONS = {
                'pool_size': 5,  # 减少连接池大小，避免Supabase连接限制
                'max_overflow': 10,  # 减少溢出连接
                'pool_recycle': 1800,  # 30分钟回收连接，避免长连接问题
                'pool_pre_ping': True,  # 保持连接检测
                'pool_timeout': 10,  # 减少连接超时时间
                'connect_args': {
                    'sslmode': 'require',
                    'connect_timeout': 10,  # 减少连接超时
                    'application_name': 'PMA_Supabase_App',
                    'options': '-c search_path=public -c statement_timeout=30000'  # 添加语句超时30秒
                }
            }
        else:
            # Render或其他云端环境配置
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
        APP_DOMAIN = os.environ.get('APP_DOMAIN', 'https://pma.jamesgpone.win')
        # 安全的PORT配置，处理Render平台的PORT环境变量
        port_env = os.environ.get('PORT', '10000')
        if port_env == '$PORT' or not port_env.isdigit():
            PORT = 10000
        else:
            PORT = int(port_env)
        
    else:
        DEBUG = True
        TESTING = False
        ENVIRONMENT = 'local'
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
        
        # 非云端环境（本地开发、NAS部署等）
        # 优先使用 EXTERNAL_URL 环境变量（NAS部署时各环境域名不同）
        APP_DOMAIN = os.environ.get('APP_DOMAIN') or os.environ.get('EXTERNAL_URL') or 'https://pma.jamesgpone.win'
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
    # 支持从环境变量读取，便于在中国NAS环境使用国内邮件服务
    # Gmail SMTP 在中国被防火墙阻止，需要使用腾讯企业邮箱/阿里云邮件等国内服务
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'james98980566@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'cihkheuuyvnkrtrj')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME', 'james98980566@gmail.com'))
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'James.ni@evertacsolutions.com')
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
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

    # Google Maps API 配置（用于地理编码服务）
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY') or 'AIzaSyD7Ipf3-0l0XYN5rvKpT1gL-PFKVEdzZmc'

    # 旧规格系统特性开关 - 控制ProductCodeField API和UI的可用性
    # [LegacySpecSystem] 此配置用于隔离和控制旧规格系统，支持未来的完全移除
    LEGACY_SPEC_SYSTEM_ENABLED = os.getenv('LEGACY_SPEC_SYSTEM_ENABLED', 'false').lower() == 'true'

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
    database_url = get_database_url()
    parsed = urlparse(database_url)
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


